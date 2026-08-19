"""
The tool plane: nothing reaches a tool except through here (G3).

    authorize (Cedar) -> validate the arguments -> [the tool runs] -> validate the result

Every step denies by default, and every denial is a *platform* decision with a
mechanism attached — never a judgement about what the model was trying to do.

**A round carries n tool calls and a turn carries n rounds** (SPEC/02, PF-5). The
model may ask for several searches at once, and having answered them it may ask
again. So this is n authorization decisions and n audit records per turn, not one,
and the turn is bounded: an unbounded agent loop is a cost incident waiting to
happen, and the bound is enforced here rather than trusted to the caller.

**Three distinct refusal mechanisms, kept distinct.** M01's guardrail module made
this argument and M02 has just paid for ignoring it once: "9/10 blocked" and
"9/10 blocked, 6 of them by one filter" are different findings. So a Cedar denial,
a contract violation, and a loop bound are three mechanisms, not one — and only
`policy` means Cedar, because `cedar_denied_or_approval_required_and_logged` is
satisfiable by that and nothing else (`evals.adversarial.CEDAR_MECHANISMS`).

**Schema validation is a subset, enforced by a differential test** (ADR-022). The
gateway bundle carries no third-party dependency — the Lambda runtime has no
`jsonschema` and adding one means a bundling step this stack does not have — so
the constructs the committed tool schemas actually use are implemented here, a
test fails if a schema grows one that is not, and a second test requires this
validator to agree with `jsonschema` case for case. The subset is bounded by a
check rather than by a promise.

Pure: no SDK, no filesystem, no clock. Owning seat: Platform Engineering
(mechanism) · Tool Owner (the contracts) · Security (it is an authorization path).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from core import cedar

#: How many tool rounds one turn may take. Derived from measurement rather than
#: chosen: no turn in `milestones/M02/loop-shape.json` needed more than two, and
#: this is a bound rather than an expectation — it exists to stop a loop, not to
#: shape one.
MAX_ROUNDS = 4

#: Mechanisms this plane can refuse with. `policy` is Cedar and only Cedar; see
#: the module docstring for why that separation is load-bearing.
POLICY = "policy"
SCHEMA = "schema"
LOOP = "loop"

#: JSON Schema keywords this validator implements. A committed tool schema using
#: anything else fails `test_every_tool_schema_stays_inside_the_supported_subset`
#: — at check time, where it is a five-minute conversation, rather than at run
#: time, where it would be a tool call silently validated against less than its
#: contract says.
#:
#: `format` and `default` are listed as *accepted and not enforced*, which is
#: exactly what `jsonschema` does with them by default: no format checker is
#: registered unless one is passed, and defaults are never applied. Treating them
#: any other way here would make this validator stricter than the contract.
SUPPORTED_KEYWORDS = frozenset({
    "$schema", "$id", "title", "description",
    "type", "required", "properties", "additionalProperties",
    "enum", "minLength", "maxLength", "minimum", "maximum",
    "items", "maxItems", "minItems",
    "pattern",
    "format", "default",
})

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    # `bool` is a subclass of `int` in Python and is not an integer in JSON.
    # Letting True satisfy an integer field is the kind of leniency that makes a
    # contract check agree with everything.
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


@dataclass(frozen=True)
class ToolDecision:
    """One tool call's outcome. `mechanism` is `none` when allowed, mirroring the
    audit record's rule that an allowed call was not refused by anything."""

    allowed: bool
    tool_id: str
    mechanism: str = "none"
    reasons: tuple[str, ...] = ()

    def as_record_fragment(self, *, round_number: int, args: dict | None = None) -> dict:
        """The `tool` object in an audit record. Carries the arguments so a denial
        can be reconstructed later — a refusal nobody can account for is
        indistinguishable from a bug."""
        fragment = {
            "id": self.tool_id,
            "round": round_number,
            "decision": "allowed" if self.allowed else "denied",
            "mechanism": self.mechanism,
            "reasons": list(self.reasons),
        }
        if args is not None:
            fragment["args"] = args
        return fragment


# --- the schema subset ---------------------------------------------------------

def unsupported_keywords(schema: dict) -> set[str]:
    """Every keyword in `schema`, at any depth, that this validator does not
    implement. Empty means the schema is fully covered."""
    found: set[str] = set()
    if not isinstance(schema, dict):
        return found
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            for subschema in value.values():
                found |= unsupported_keywords(subschema)
            continue
        if key == "items":
            found |= unsupported_keywords(value)
            continue
        if key not in SUPPORTED_KEYWORDS:
            found.add(key)
    return found


def validate(instance, schema: dict, path: str = "<root>") -> list[str]:
    """Validate against the supported subset. Returns a list of problems, empty
    when the instance conforms.

    Returns rather than raises: a tool call carrying bad arguments is a decision
    the plane makes, not an exception the gateway trips over, and the reasons go
    into the audit record."""
    problems: list[str] = []

    declared = schema.get("type")
    if declared is not None:
        allowed = [declared] if isinstance(declared, str) else list(declared)
        if not any(_TYPES[t](instance) for t in allowed if t in _TYPES):
            return [f"{path}: expected {'/'.join(allowed)}, got {type(instance).__name__}"]

    if "enum" in schema and instance not in schema["enum"]:
        problems.append(f"{path}: {instance!r} is not one of {schema['enum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            problems.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            problems.append(f"{path}: longer than maxLength {schema['maxLength']}")
        # `re.search`, not `re.match`: JSON Schema's `pattern` is an unanchored
        # search, and using `match` here would silently reject values the contract
        # permits — a validator stricter than its schema is as wrong as a lax one,
        # and harder to notice because it only ever refuses.
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            problems.append(f"{path}: {instance!r} does not match pattern {schema['pattern']!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            problems.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            problems.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            problems.append(f"{path}: more than maxItems {schema['maxItems']}")
        if "minItems" in schema and len(instance) < schema["minItems"]:
            problems.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "items" in schema:
            for index, item in enumerate(instance):
                problems.extend(validate(item, schema["items"], f"{path}[{index}]"))

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in instance:
                problems.append(f"{path}: missing required property {name!r}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance) - set(properties))
            if extra:
                problems.append(f"{path}: unexpected propertie(s) {extra}")
        for name, value in instance.items():
            if name in properties:
                problems.extend(validate(value, properties[name], f"{path}.{name}"))

    return problems


# --- the plane -----------------------------------------------------------------

def generate_contracts(registry: list[dict], schemas: dict[str, dict]) -> dict:
    """Build the runtime contract set from the registry.

    `schemas` maps the registry's schema *paths* to loaded documents, so this
    stays free of the filesystem and the caller owns the reading. Committed into
    the gateway bundle beside the generated Cedar and drift-checked the same way:
    the registry is the source, and both artifacts are build products that happen
    to be committed."""
    return {
        tool["id"]: {
            "consequence": tool["consequence"],
            "input": schemas[tool["schemas"]["input"]],
            "output": schemas[tool["schemas"]["output"]],
        }
        for tool in registry
    }


@dataclass(frozen=True)
class ToolPlane:
    policies: list
    contracts: dict
    max_rounds: int = MAX_ROUNDS

    def authorize(self, *, principal: str, tool_id: str, args: dict,
                  context: dict | None = None, round_number: int = 1) -> ToolDecision:
        """Authorize one tool call. Cedar first, then the contract.

        **Cedar first is deliberate.** An unregistered tool must be denied because
        no policy permits it — G3's claim — and not because its arguments failed to
        validate against a contract that does not exist. The order is what makes
        the denial mean what the milestone says it means."""
        if round_number > self.max_rounds:
            return ToolDecision(False, tool_id, LOOP, (
                f"turn exceeded {self.max_rounds} tool rounds — an unbounded agent loop is "
                "stopped here rather than trusted to the caller",
            ))

        decision = cedar.authorize(self.policies, principal=principal,
                                   action="invoke", resource=tool_id, context=context)
        if not decision.allowed:
            return ToolDecision(False, tool_id, POLICY, decision.reasons)

        contract = self.contracts.get(tool_id)
        if contract is None:
            # Cedar permitted a tool with no committed contract, which means the
            # policy set and the contract set disagree. Denied, loudly: the drift
            # check exists so this cannot happen, and if it has happened the right
            # response is a refusal rather than a best guess.
            return ToolDecision(False, tool_id, SCHEMA, (
                f"{tool_id} is permitted by policy but has no committed contract — "
                "the generated policy and contract sets disagree",
            ))

        problems = validate(args, contract["input"], "args")
        if problems:
            return ToolDecision(False, tool_id, SCHEMA, tuple(problems))

        return ToolDecision(True, tool_id)

    def validate_result(self, *, tool_id: str, result) -> ToolDecision:
        """Check what the tool returned against its committed output contract.

        A contract check, not a content filter: it cannot catch an injected
        instruction sitting in a valid string in a valid field, and SPEC/02 defers
        that question to M04 on the record. What it does catch is a tool that has
        started returning a shape nobody agreed to — including fields the schema
        does not allow, which is the mechanism by which catalog data the model
        should never see would reach it."""
        contract = self.contracts.get(tool_id)
        if contract is None:
            return ToolDecision(False, tool_id, SCHEMA, (f"no committed contract for {tool_id}",))
        problems = validate(result, contract["output"], "result")
        if problems:
            return ToolDecision(False, tool_id, SCHEMA, tuple(problems))
        return ToolDecision(True, tool_id)

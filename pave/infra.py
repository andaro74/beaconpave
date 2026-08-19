"""
Reading a synthesized CloudFormation template, for the assertions G1 rests on.

**Why a committed snapshot instead of synthesizing in the test.** `cdk synth`
needs Node and an `npm ci`; `make check` must pass offline on a fresh clone with
no AWS account (G8). Writing the assertion twice — once in TypeScript for CI and
once in Python for the hermetic suite — would give one invariant two
implementations that can disagree, and the one that disagrees quietly is the one
nobody reads. So there is a single assertion, in Python, over a committed
snapshot, plus a CI job that re-synthesizes and diffs. That job is the only thing
standing between the snapshot and a fiction, which is why it blocks (ADR-017).

`normalize` exists so the diff means something. An asset hash changes whenever a
byte of Lambda source changes, so an un-normalized snapshot would churn on every
edit and train everyone to re-record it without reading it — and a snapshot
nobody reads is how an IAM grant gets in. What is left after normalizing is the
structure and the policy, which is what the assertion is about.

The rule it applies: **a snapshot that only reproduces on the machine that
recorded it is not a snapshot.** The first CI run of the freshness job proved
that the hard way — it reported drift against a snapshot that was byte-identical
when re-synthesized locally. The culprit was `AWS::CDK::Metadata`, whose
`Analytics` property is a deflate-compressed blob of library telemetry: it moves
with the construct-library version and is not guaranteed byte-stable across zlib
builds, so Windows and Linux can disagree on it for identical input. It carries
nothing about IAM, so it is dropped rather than compared.

Hermetic: pure JSON, no SDK, no network.
Owning seat: Platform Engineering.
"""
from __future__ import annotations

import json
import pathlib
import re
from collections.abc import Iterator
from typing import Any

#: A CDK asset hash: 64 hex characters, sometimes with a `.zip` suffix.
ASSET_HASH = re.compile(r"\b[0-9a-f]{64}\b")
ASSET_PLACEHOLDER = "<ASSET_HASH>"

#: Actions that reach a model. `Converse` authorizes against `bedrock:InvokeModel`
#: today, so listing both is redundant — deliberately. A list that is exactly
#: minimal stops being correct the moment the provider adds an action, and this
#: is the one list in the repo where being wrong is silent.
MODEL_INVOKE_ACTIONS = frozenset({
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "bedrock:Converse",
    "bedrock:ConverseStream",
})

#: The construct-id prefix of the only role permitted to hold a model-invoke
#: grant.
#:
#: **This is the allowlist, and it has exactly one entry on purpose.** ADR-011
#: expired at M01: the baseline's exception is gone and nothing replaced it. A
#: second entry here is how the exception comes back — not as an ADR anybody
#: reviews, but as a one-line change that makes a failing test pass. So a test
#: pins the length of this tuple and names ADR-011 when it fails. If you are
#: adding an entry, you are writing an exception, and it needs an ADR and the
#: Security seat rather than a commit.
MODEL_INVOKE_ROLE_PREFIXES = ("GatewayFn",)


def load(path: str | pathlib.Path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


#: Resource types that are telemetry rather than infrastructure. Dropped whole:
#: `AWS::CDK::Metadata` carries a deflate-compressed analytics blob that moves
#: with the library version and is not byte-stable across platforms, so comparing
#: it makes the snapshot machine-specific without asserting anything.
TELEMETRY_TYPES = frozenset({"AWS::CDK::Metadata"})


def _drop_telemetry(resources: dict) -> dict:
    return {
        logical_id: resource
        for logical_id, resource in resources.items()
        if not (isinstance(resource, dict) and resource.get("Type") in TELEMETRY_TYPES)
    }


def normalize(template: Any) -> Any:
    """Strip everything that changes without the infrastructure changing.

    Removes per-resource `Metadata` (which carries `aws:asset:path` and the CDK
    construct path), drops telemetry-only resources, and rewrites asset hashes to
    a placeholder. What survives is resource types, properties, and policy
    documents — the things the G1 assertion is actually about."""
    if isinstance(template, dict):
        if "Resources" in template and isinstance(template["Resources"], dict):
            template = dict(template)
            template["Resources"] = _drop_telemetry(template["Resources"])
        return {
            key: normalize(value)
            for key, value in template.items()
            if key not in ("Metadata",)
        }
    if isinstance(template, list):
        return [normalize(item) for item in template]
    if isinstance(template, str):
        return ASSET_HASH.sub(ASSET_PLACEHOLDER, template)
    return template


def _as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _referenced_roles(refs: Any) -> list[str]:
    """Logical ids of the roles a policy attaches to."""
    names = []
    for ref in _as_list(refs):
        if isinstance(ref, dict) and "Ref" in ref:
            names.append(ref["Ref"])
        elif isinstance(ref, str):
            names.append(ref)
    return names


def statements(template: dict) -> Iterator[dict]:
    """Every IAM statement in the template, with the roles it binds to.

    Covers both shapes CDK emits: a standalone `AWS::IAM::Policy` naming its
    roles, and inline `Policies` on an `AWS::IAM::Role`. Missing the second shape
    would leave a grant that reads exactly like the first one invisible."""
    for logical_id, resource in template.get("Resources", {}).items():
        kind = resource.get("Type")
        properties = resource.get("Properties", {})

        if kind == "AWS::IAM::Policy":
            roles = _referenced_roles(properties.get("Roles"))
            for statement in _as_list(properties.get("PolicyDocument", {}).get("Statement")):
                yield {"policy": logical_id, "roles": roles, "statement": statement}

        elif kind == "AWS::IAM::ManagedPolicy":
            # **A third shape, and it was invisible.** A managed policy names its
            # roles the same way a standalone policy does, and CDK emits one for
            # `addManagedPolicy` and for any grant made through a shared policy.
            # Until this branch existed, a `bedrock:InvokeModel` grant delivered
            # this way passed every G1 assertion in the repo — the invariant
            # CLAUDE.md calls non-negotiable, defeated by choosing a different
            # construct. Found by the Security seat planting it.
            roles = _referenced_roles(properties.get("Roles"))
            for statement in _as_list(properties.get("PolicyDocument", {}).get("Statement")):
                yield {"policy": logical_id, "roles": roles, "statement": statement}

        elif kind == "AWS::IAM::Role":
            for policy in _as_list(properties.get("Policies")):
                for statement in _as_list(policy.get("PolicyDocument", {}).get("Statement")):
                    yield {"policy": logical_id, "roles": [logical_id], "statement": statement}


def actions_of(statement: dict) -> set[str]:
    return set(_as_list(statement.get("Action")))


def grants_any(statement: dict, wanted: frozenset) -> bool:
    """Does this statement's `Action` cover any of `wanted`, wildcards included?

    **A set intersection is not action matching.** `Action: "*"` and
    `Action: "bedrock:*"` reach every model action and match no literal string, so
    a plain intersection reported them as granting nothing at all. Both G1 and
    G3's new infra assertion read through here, and both were blind to the
    broadest possible grant while catching the narrow ones.

    The `MODEL_INVOKE_ACTIONS` docstring argues that naming more than the minimum
    protects against a provider *adding* an action. It does. It says nothing about
    a grant that names none of them by naming all of them."""
    for action in _as_list(statement.get("Action")):
        if not isinstance(action, str):
            continue
        if action == "*":
            return True
        if action.endswith(":*") and any(w.startswith(action[:-1]) for w in wanted):
            return True
        if action in wanted:
            return True
    return False


def model_invoke_grants(template: dict) -> list[dict]:
    """Every statement that ALLOWS a model-invoke action."""
    found = []
    for entry in statements(template):
        statement = entry["statement"]
        if statement.get("Effect") != "Allow":
            continue
        if grants_any(statement, MODEL_INVOKE_ACTIONS):
            found.append(entry)
    return found


def model_invoke_denials(template: dict) -> list[dict]:
    """Every statement that explicitly DENIES model-invoke actions.

    Absence of a grant already denies. An explicit Deny is recorded separately
    because it survives a later careless grant, and because it makes the
    resulting CloudTrail event say why the call failed."""
    found = []
    for entry in statements(template):
        statement = entry["statement"]
        if statement.get("Effect") != "Deny":
            continue
        if grants_any(statement, MODEL_INVOKE_ACTIONS):
            found.append(entry)
    return found


def is_gateway_role(logical_id: str) -> bool:
    return logical_id.startswith(MODEL_INVOKE_ROLE_PREFIXES)


def roles(template: dict) -> list[str]:
    return [
        logical_id
        for logical_id, resource in template.get("Resources", {}).items()
        if resource.get("Type") == "AWS::IAM::Role"
    ]


# --- the tool plane, at the infrastructure layer (M02) ------------------------

#: Actions that reach a tool function. Same reasoning as `MODEL_INVOKE_ACTIONS`:
#: naming more than the minimum is deliberate, because a list that is exactly
#: minimal stops being correct the moment the provider adds an action.
TOOL_INVOKE_ACTIONS = frozenset({
    "lambda:InvokeFunction",
    "lambda:InvokeFunctionUrl",
    "lambda:InvokeAsync",
})

#: The environment variable carrying the gateway's tool routing table. The
#: assertions read the deployed table rather than a list in a test, so a tool
#: added to the stack is asserted about without anybody remembering to add it
#: here — the failure mode a hand-maintained list has is that it stays green.
TOOL_ROUTING_ENV = "TOOL_FUNCTIONS"

_ROUTED_KEY = re.compile(r'"([a-z0-9][a-z0-9-]*)"\s*:\s*"')


def referenced_logical_ids(value: Any) -> set[str]:
    """Every logical id a template fragment points at, through `Ref` or `GetAtt`.

    Needed because an IAM `Resource` is rarely a string: CDK emits
    `{"Fn::GetAtt": ["CatalogSearchFn...", "Arn"]}`, and a check that only looked
    at strings would read a narrowly-scoped grant as naming nothing at all."""
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "Ref" and isinstance(item, str):
                found.add(item)
            elif key == "Fn::GetAtt":
                target = item[0] if isinstance(item, list) and item else item
                if isinstance(target, str):
                    found.add(target.split(".")[0])
            else:
                found |= referenced_logical_ids(item)
    elif isinstance(value, list):
        for item in value:
            found |= referenced_logical_ids(item)
    return found


def functions(template: dict) -> dict[str, dict]:
    return {
        logical_id: resource
        for logical_id, resource in template.get("Resources", {}).items()
        if resource.get("Type") == "AWS::Lambda::Function"
    }


def gateway_function(template: dict) -> tuple[str, dict]:
    """The one function holding the model grant, found through the grant itself.

    Not by name. `is_gateway_role` matches a construct-id prefix, which is fine
    for a role and would be circular here: the question these assertions ask is
    *which* function is the control point, and answering it from a naming
    convention would let a second one become the answer by being named well."""
    granted = {role for grant in model_invoke_grants(template) for role in grant["roles"]}
    for logical_id, resource in functions(template).items():
        if referenced_logical_ids(resource.get("Properties", {}).get("Role")) & granted:
            return logical_id, resource
    raise AssertionError("no Lambda function holds the model-invoke grant")


def routed_tools(template: dict) -> dict[str, str]:
    """Tool id -> the logical id of the function the gateway routes it to.

    Parsed out of the gateway's own environment, which is the table the running
    gateway obeys. Reading the deployment's answer rather than restating it is the
    same rule `test_iam_assertions` follows about the snapshot: an assertion
    against a second copy asserts about the copy."""
    _, gateway = gateway_function(template)
    raw = gateway.get("Properties", {}).get("Environment", {}).get("Variables", {}).get(
        TOOL_ROUTING_ENV)
    if raw is None:
        return {}
    if isinstance(raw, str):
        return {tool: "" for tool in _ROUTED_KEY.findall(raw)}

    parts = raw.get("Fn::Join", [None, []])[1]
    literals = "".join(p for p in parts if isinstance(p, str))
    targets = [next(iter(referenced_logical_ids(p))) for p in parts if not isinstance(p, str)]
    keys = _ROUTED_KEY.findall(literals)
    if len(keys) != len(targets):
        raise AssertionError(
            f"cannot read {TOOL_ROUTING_ENV}: {len(keys)} tool id(s) and {len(targets)} "
            "function reference(s). The assertions below depend on reading this table, so "
            "an unreadable one fails loudly rather than asserting about an empty dict."
        )
    return dict(zip(keys, targets, strict=True))


def tool_invoke_grants(template: dict) -> list[dict]:
    """Every statement that ALLOWS an invoke action, with what it names."""
    found = []
    for entry in statements(template):
        statement = entry["statement"]
        if statement.get("Effect") != "Allow":
            continue
        if grants_any(statement, TOOL_INVOKE_ACTIONS):
            found.append(entry)
    return found


def _resource_text(value: Any) -> str:
    """Every string anywhere inside a `Resource`, concatenated.

    `Fn::Sub` and `Fn::Join` hide an ARN inside a structure, so a check that only
    looked at top-level strings saw a wildcard grant as naming nothing."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_resource_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_resource_text(v) for v in value)
    return ""


def invoke_targets(statement: dict, functions_by_name: dict[str, str] | None = None) -> set[str]:
    """Logical ids an invoke grant names, through references **or** through text.

    **A grant does not have to use `Fn::GetAtt` to name a function.** The first
    version read only `Ref`/`Fn::GetAtt`, so a statement naming the tool by literal
    ARN string resolved to the empty set and dropped straight out of the
    intersection the assertion is built on — a smuggler role could be handed
    `lambda:InvokeFunction` on the tool and every test stayed green. Found by the
    Security seat planting exactly that.

    `functions_by_name` maps a deployed function name to its logical id, so an ARN
    ending in that name resolves. It is optional because the reference path needs
    no such map."""
    found = referenced_logical_ids(_as_list(statement.get("Resource")))
    text = _resource_text(_as_list(statement.get("Resource")))
    for name, logical_id in (functions_by_name or {}).items():
        if name and name in text:
            found.add(logical_id)
    return found


#: The segment of a Lambda ARN after which the function name begins.
FUNCTION_MARKER = ":function:"


def _names_a_wildcard_function(resource: Any) -> bool:
    """Does this `Resource` name an unbounded set of functions?

    Evaluated **per element**, and a reference wins. `Fn::Join["", [GetAtt(Arn),
    ":*"]]` is CDK's own `grantInvoke` shape: it points at one specific function
    and permits any version or alias of it. Narrow, correct, and what this repo
    deploys — so a text scan for `*` flagged the grant the check exists to bless,
    which is how a check gets deleted rather than fixed.

    What matters is an element that names no function and still carries a `*`, or
    an ARN whose function-name segment is a wildcard. Either covers functions
    nobody has written yet, which is how a tool added to the registry later
    becomes reachable with no IAM change to review."""
    for element in _as_list(resource):
        if referenced_logical_ids(element):
            continue                                  # points at a named resource
        text = _resource_text(element)
        if not text:
            continue
        if FUNCTION_MARKER in text:
            before, after = text.split(FUNCTION_MARKER, 1)
            if "*" in before or "*" in after.split(":")[0]:
                return True
        elif "*" in text:
            # Not an ARN shape at all — a bare `*`, or a name pattern. Nothing in
            # the structure bounds it.
            return True
    return False


def wildcard_invoke_grants(template: dict) -> list[dict]:
    """Invoke grants whose `Resource` is `*` or a string with one in it.

    A wildcard invoke grant is how a tool added to the registry later becomes
    reachable without anybody granting anything: the grant that already covers it
    was written before it existed."""
    found = []
    for entry in tool_invoke_grants(template):
        # Read as TEXT, not as top-level strings. `{"Fn::Sub":
        # "arn:...:function:*"}` is a wildcard grant that the string-only check
        # skipped entirely — and `invoke_targets` did not see it either, so
        # neither detector caught it. Two blind checks agreeing is not coverage.
        if _names_a_wildcard_function(_as_list(entry["statement"].get("Resource"))):
            found.append(entry)
    return found


def function_urls(template: dict) -> list[str]:
    """`AWS::Lambda::Url` resources. A function URL is a public HTTPS endpoint in
    front of a function, and one on a tool would be a route to that tool with no
    plane in front of it — G3 held by the plane and lost at the network."""
    return [
        logical_id
        for logical_id, resource in template.get("Resources", {}).items()
        if resource.get("Type") == "AWS::Lambda::Url"
    ]


def invoke_permissions(template: dict) -> list[dict]:
    """Every `AWS::Lambda::Permission` — a resource policy granting invoke from the
    *other* side, invisible to every check that reads role policies.

    **The assertion is "only the gateway", not "no wildcard".** The first version
    flagged only `Principal: "*"`, so `Principal: "apigateway.amazonaws.com"` or a
    specific foreign account id passed — and either is precisely "G3 held in the
    code and lost at the network", with the gateway's own narrow grant still
    reading as correct beside it. The test file claimed the broad property and the
    code delivered the narrow one."""
    return [
        {"id": logical_id,
         "principal": resource.get("Properties", {}).get("Principal"),
         "function": resource.get("Properties", {}).get("FunctionName")}
        for logical_id, resource in template.get("Resources", {}).items()
        if resource.get("Type") == "AWS::Lambda::Permission"
    ]

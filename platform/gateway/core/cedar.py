"""
Cedar policies: generated from the registry, evaluated in-process (ADR-004).

ADR-004's load-bearing half is **generation**, and it says why in its own words:
"Hand-written policies drift from the registry, and a policy that disagrees with
the registry is worse than no policy — it makes the registry look authoritative
while something else decides." So `platform/registry/tools.yaml` is the source and
`platform/gateway/policy/tools.cedar` is a build product that happens to be
committed, the way `platform/infra/tests/fixtures/*.template.json` is (ADR-017).

**The generator and the evaluator live in one module on purpose.** They share a
grammar, and a generator and a parser that disagree about it is the classic way an
authorization layer starts permitting something nobody wrote down. Here the
grammar exists once, and both halves are read together or not at all.

**The policy text is real Cedar**, of the shape Amazon Verified Permissions
consumes verbatim; the *evaluator* is a subset (ADR-020). That is the cut, and it
is bounded by construction: this evaluator only ever sees policies this generator
produced, from a closed template, with a drift check that fails if the committed
set is not exactly what the registry generates. Its input space is enumerable, so
it is tested exhaustively rather than hopefully.

**Deny by default, including on anything it cannot fully parse.** A policy engine
that fails open is worse than no policy engine, because it looks like one.

Pure — no SDK, no filesystem, no clock. Owning seat: Platform Engineering
(mechanism) · Tool Owner (the policies, via the registry they are generated from).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

#: Consequence classes at or above which an action needs a human in the loop.
#: Mirrors `test_publish_class_tools_carry_an_approval_interlock` in the contract
#: suite; the registry is where the class is declared, and this is where the
#: declaration acquires teeth.
GATED_CONSEQUENCES = frozenset({"publish", "irreversible"})

#: The context key an approval interlock sets. It does not exist at M02 — nothing
#: sets it, so every publish-class call is denied — and that is the honest state:
#: a tool whose declared approver is not deployed must be unreachable, not
#: reachable without one. M06 makes it reachable by granting the context, which is
#: a change to the caller rather than a rewrite of the policy.
APPROVAL_CONTEXT_KEY = "approval_granted"

HEADER = """\
// GENERATED FROM platform/registry/tools.yaml — DO NOT EDIT.
//
// Regenerate with `python -m pave.cli policy generate`. A hand edit is reverted by
// the next regeneration and fails `tests/test_cedar_policy.py` in the meantime,
// which is the point: a policy that disagrees with the registry makes the registry
// look authoritative while something else decides (ADR-004).
//
// Cedar's own semantics decide the outcome: an explicit `forbid` beats any
// `permit`, and a request matching no `permit` is denied. Nothing here grants a
// default.
"""

_PERMIT = re.compile(
    r'permit\(\s*principal\s*==\s*Service::"(?P<principal>[^"]+)"\s*,\s*'
    r'action\s*==\s*Action::"(?P<action>[^"]+)"\s*,\s*'
    r'resource\s*==\s*Tool::"(?P<resource>[^"]+)"\s*\)\s*;'
)
_FORBID = re.compile(
    r'forbid\(\s*principal\s*,\s*'
    r'action\s*==\s*Action::"(?P<action>[^"]+)"\s*,\s*'
    r'resource\s*==\s*Tool::"(?P<resource>[^"]+)"\s*\)\s*'
    r'unless\s*\{\s*context\.(?P<condition>[A-Za-z_][A-Za-z0-9_]*)\s*\}\s*;'
)


@dataclass(frozen=True)
class Policy:
    effect: str                    # "permit" | "forbid"
    principal: str | None          # None means "any principal"
    action: str
    resource: str
    unless: str | None = None      # a context key that exempts a forbid

    def matches(self, principal: str, action: str, resource: str) -> bool:
        if self.principal is not None and self.principal != principal:
            return False
        return self.action == action and self.resource == resource


@dataclass(frozen=True)
class Decision:
    """`reasons` exists so a denial can be explained in the audit record. A
    refusal nobody can account for is indistinguishable from a bug, and it is the
    kind teams learn to route around — the same argument `classify.Classification`
    makes one component over."""

    allowed: bool
    reasons: tuple[str, ...] = ()


# --- generation ---------------------------------------------------------------

def generate(registry: list[dict]) -> str:
    """Render the whole policy set from the registry, deterministically.

    Order follows the registry file so a reordered diff is a reordered registry
    and never the generator having an opinion of its own."""
    blocks: list[str] = [HEADER]

    for tool in registry:
        tool_id = tool["id"]
        blocks.append(f"// --- {tool_id} (consequence: {tool['consequence']}) ---")

        for caller in tool.get("callers", []):
            blocks.append(
                f'permit(\n'
                f'  principal == Service::"{caller}",\n'
                f'  action == Action::"invoke",\n'
                f'  resource == Tool::"{tool_id}"\n'
                f');'
            )

        if tool["consequence"] in GATED_CONSEQUENCES:
            # A `forbid` rather than a narrower `permit`, because Cedar resolves an
            # explicit forbid over every permit. Adding a caller to the registry
            # therefore cannot accidentally route around the interlock — which is
            # the failure this class of tool exists to prevent.
            blocks.append(
                f'// consequence >= publish: unreachable until an approval interlock\n'
                f'// grants {APPROVAL_CONTEXT_KEY}. Declared approver: {tool.get("approval", "none")}\n'
                f'forbid(\n'
                f'  principal,\n'
                f'  action == Action::"invoke",\n'
                f'  resource == Tool::"{tool_id}"\n'
                f') unless {{ context.{APPROVAL_CONTEXT_KEY} }};'
            )

    return "\n\n".join(blocks) + "\n"


# --- evaluation ---------------------------------------------------------------

def _strip_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def parse(text: str) -> list[Policy]:
    """Parse the generated grammar, or raise.

    **Raises on any statement it does not fully understand**, rather than skipping
    it. Skipping is the failure mode that matters: an unparsed `forbid` is a
    control that silently stopped applying, and the request it should have stopped
    would be permitted by whatever `permit` remained readable."""
    stripped = _strip_comments(text)
    policies: list[Policy] = []
    consumed = []

    for match in _PERMIT.finditer(stripped):
        policies.append(Policy("permit", match["principal"], match["action"], match["resource"]))
        consumed.append(match.span())
    for match in _FORBID.finditer(stripped):
        policies.append(
            Policy("forbid", None, match["action"], match["resource"], match["condition"]))
        consumed.append(match.span())

    # Whatever is left must be whitespace. Anything else is a statement this
    # evaluator cannot read, and reading half a policy set is worse than reading
    # none: the half that parsed would still return decisions.
    remainder = list(stripped)
    for start, end in consumed:
        remainder[start:end] = [" "] * (end - start)
    leftover = "".join(remainder).strip()
    if leftover:
        raise ValueError(
            f"unparsed policy text (this evaluator implements a Cedar subset — ADR-020): "
            f"{leftover[:200]!r}"
        )
    return policies


def authorize(policies: list[Policy], *, principal: str, action: str, resource: str,
              context: dict | None = None) -> Decision:
    """Cedar's evaluation order: an explicit forbid beats any permit, and a
    request matching no permit is denied.

    Deny is the default in both directions — no permit means deny, and an
    unreadable policy set never reaches this function because `parse` raised."""
    context = context or {}

    for policy in policies:
        if policy.effect != "forbid" or not policy.matches(principal, action, resource):
            continue
        if policy.unless and context.get(policy.unless) is True:
            continue
        exemption = f"; {policy.unless} not granted" if policy.unless else ""
        return Decision(False, (
            f"forbidden by policy on {resource}{exemption}",
        ))

    for policy in policies:
        if policy.effect == "permit" and policy.matches(principal, action, resource):
            return Decision(True, ())

    return Decision(False, (
        f"no policy permits {principal} to {action} {resource} — "
        "an unregistered or uninvited caller is denied by default (G3)",
    ))

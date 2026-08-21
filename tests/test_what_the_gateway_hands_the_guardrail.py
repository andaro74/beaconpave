"""
If the gateway ever inspects the system channel, what may it hand over?

**Written before the code it constrains exists**, which is the only time this
assertion is cheap. ADR-035's Change B declared the whole assembled system block
untrusted and handed it to `ApplyGuardrail`; a pre-flight measured that as a 100%
outage with no discrimination, and amendment 1 withdrew it. The recoverable form
named there inspects the interpolated catalog **data** rather than the prompt.

"Data-scoped" was an intention when that was written. It is a measurement now
(`milestones/ADR-035/row14-attribution-v3.json`, guardrail v3, k=3, unanimous):

    the instructions alone, no schema, no catalog  ->  ['PROMPT_ATTACK']
    evals/answer.schema.json alone                 ->  ['TOPIC:entitlement-circumvention']
    data/catalog.json alone                        ->  []          (allowed)

Three parts of one prompt, three different verdicts. Only the third is safe to
inspect, and the other two are unsafe for **different** reasons.

## The hazard, and why it is worse than an outage

`core/audit.py::observation_from_record` computes `guardrail_blocked` from
`decision` and `mechanism`. **It does not read `channel`** — amendment 1's
finding 2, still true, and out of reach during ADR-035's measurement window
because `audit.py` is inside `capture_sha256`.

So a system-channel inspection handed the answer schema would block every turn
with `TOPIC:entitlement-circumvention`, and **every probe would score PASS** on a
block that has nothing to do with its payload. Not an outage that anybody
notices: an outage that reports itself as a perfect adversarial score. That is
the flattering catastrophe this repository exists to avoid, arriving through a
JSON schema.

Handing over the instruction preamble is the milder version of the same fault:
`PROMPT_ATTACK` fires on the platform's own imperatives read as if a viewer had
typed them, which is the filter working correctly on mis-labelled input and tells
you nothing about the content it was pointed at.

## What this file asserts, and what it cannot

It asserts a **property of the source**: whatever the gateway declares untrusted
on the system channel is not the assembled prompt, the instruction preamble, or
the answer schema. Parse, never import — `handler.py` holds the boto3 clients and
the hermetic suite must not pull an AWS SDK into `sys.modules` (G8).

It cannot prove the runtime value is catalog data; only a deployed call can, and
`inspect_context.py` is what does that. This is the offline half, and it is the
half that fails in CI rather than in a measurement nobody re-reads.

**While the system channel stays withdrawn these tests hold vacuously**, and that
is deliberate: `tests/test_handler_wiring.py` pins the withdrawal, and this file
pins what re-adding it may do. A guard that only appears alongside the code it
guards is a guard somebody writes second, under deadline, having already decided.

Hermetic (G8): reads source, imports nothing under test.
Owning seat: Platform Engineering (what the gateway hands over) · Security (why
these three are not interchangeable).
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDLER = ROOT / "platform" / "gateway" / "handler.py"
CLIENT = ROOT / "services" / "highlights-agent" / "gateway_client.py"

#: Names that reach the WHOLE assembled prompt, or a part of it measured as
#: unsafe to inspect. `system` is the caller-supplied block: instructions, schema
#: and catalog together, and the pre-flight measured it BLOCKED.
FORBIDDEN_SOURCES = {
    "system": "the whole assembled prompt, measured BLOCKED 3/3 under both v2 and v3",
    "build_prompt": "returns the whole assembled prompt",
    "SYSTEM": "the prompt template, instructions included",
    "ANSWER_SCHEMA": "the answer schema, which fires TOPIC:entitlement-circumvention alone",
    "answer.schema.json": "the answer schema, by path",
}


def handler_tree() -> ast.Module:
    return ast.parse(HANDLER.read_text(encoding="utf-8"), filename=str(HANDLER))


def untrusted_assignments(tree: ast.Module) -> list[ast.AST]:
    """Every right-hand side assigned to a name called `untrusted`."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "untrusted":
                    found.append(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "untrusted" and node.value:
                found.append(node.value)
    return found


def names_in(node: ast.AST) -> set[str]:
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            out.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            out.add(sub.attr)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.add(sub.value)
    return out


def test_there_is_at_most_one_place_this_decision_is_made():
    """A second `untrusted` assignment would let one path be data-scoped and
    another not, and the assertions below would pass while the unsafe path ran.
    The same argument `handler.py` makes about the Cedar principal: a decision
    with two sources has no source.

    **At most one, not exactly one**, because zero is the correct count today:
    Change B's system half is withdrawn and this whole file holds vacuously until
    it returns. The first version asserted `== 1` and failed on a tree where the
    hazard cannot occur — a guard that requires the thing it guards against to
    exist is a guard that gets deleted rather than satisfied."""
    assignments = untrusted_assignments(handler_tree())
    assert len(assignments) <= 1, (
        f"found {len(assignments)} `untrusted =` assignments in handler.py. One decision, "
        "one source: two would let one path be data-scoped while another was not.")


@pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_SOURCES))
def test_the_untrusted_declaration_never_names_an_unsafe_source(forbidden):
    """**The assertion. Fails the moment somebody re-adds the withdrawn half using
    the prompt instead of the data.**

    Each of these was measured, not assumed. The failure message carries the
    verdict rather than the rule, because a reader who trips this needs to know
    what the guardrail actually does with the thing they just passed."""
    for value in untrusted_assignments(handler_tree()):
        assert forbidden not in names_in(value), (
            f"`untrusted` names {forbidden!r} — {FORBIDDEN_SOURCES[forbidden]}.\n\n"
            "ADR-035 amendment 1 withdrew the system-channel inspection because the "
            "assembled prompt is blocked by the deployed guardrail on every call, and "
            "clean and poisoned block identically. The recoverable form inspects the "
            "interpolated catalog DATA, which measures as allowed under v3 while the same "
            "data carrying an injection is still caught by PROMPT_ATTACK.\n\n"
            "This matters more than an outage: `observation_from_record` derives "
            "`guardrail_blocked` from `decision` and `mechanism` and does NOT read "
            "`channel`, so a block from the wrong source makes every probe score PASS on "
            "a block that has nothing to do with its payload.\n\n"
            "See milestones/ADR-035/row14-attribution-v3.json and preflight-v3.json."
        )


def test_the_three_parts_of_the_prompt_are_still_three_parts():
    """A coverage check on the check. `FORBIDDEN_SOURCES` names things by
    identifier, so it goes stale the moment `gateway_client` renames one — and a
    stale allowlist of what is unsafe reads exactly like a safe tree.

    So: the names this file forbids must still exist where it expects them. If
    `build_prompt` or `ANSWER_SCHEMA` is renamed, this fails and whoever renamed
    it updates the guard, rather than the guard silently protecting nothing."""
    source = CLIENT.read_text(encoding="utf-8")
    for name in ("SYSTEM", "ANSWER_SCHEMA", "build_prompt"):
        assert name in source, (
            f"gateway_client.py no longer defines {name!r}, so this file is guarding "
            "against a name that cannot appear. Update FORBIDDEN_SOURCES to the new one "
            "before assuming the hazard went away with the identifier.")

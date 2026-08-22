"""
The gateway adapter's wiring, asserted without importing it.

**Why this file exists.** `core/toolloop.py` is superbly covered and
`platform/gateway/handler.py` is imported by zero tests — it is outside the
hermetic surface by design (`test_hermeticity.py`), because it holds the boto3
clients. All four seats of the ADR-035 change-B review planted weakenings there
and watched `make check` stay green. Between them:

- `untrusted = ()` — the system channel deleted from production, every one of the
  loop's `untrusted` tests still passing, because they pass `untrusted=`
  themselves. **This is the control's on/off switch**, and it was defended by
  nothing while the commit message argued at length that the loop's required
  `inspect` argument made "no inspection" impossible to spell as silence. That is
  true of the loop. It was not true of the caller, and the caller is the only
  place the control is wired up.
- `source="OUTPUT"` — drops `PROMPT_ATTACK`, which is input-only by the service's
  design and one of the two policies that fired on M04's user-turn arm. Green.
- `guardrailVersion="DRAFT"` — a guardrail that can be edited outside a commit,
  silently changing every recorded probe result (ADR-018). Green, and invisible
  from the infra side too: the IAM grant is on the guardrail ARN unqualified by
  version, and `verify_guardrail_pin.py` checks the deployed policy rather than
  what the handler passes.
- a `try`/`except` around the inspection returning a clean verdict — a throttle
  becomes "content inspected, nothing found", and the record then makes the
  positive claim that the content was assessed. G2 says an errored control
  blocks, never skips.
- slicing the inspected text — the tail of every long payload outside the
  control, while the record still says it was inspected.

**Parse, do not import.** That is what keeps this hermetic (G8): `ast` reads the
file as text, so nothing here touches boto3, credentials, or the account. The
technique is already in the repo — `test_gateway_run_parity.py` reads its
subjects the same way, and `test_hermeticity.py` scans source without importing
it.

**What this file can and cannot prove.** It proves the handler *says* the right
things. It cannot prove they work; only a deployed call can, and
`verify_guardrail_pin.py` makes the same distinction about a template versus a
policy. A structural assertion is the weaker of the two and it is the one
available offline, which is exactly the trade `platform/infra/tests/` already
makes for the IAM assertions.

Hermetic (G8): reads source, imports nothing under test.
Owning seat: Platform Engineering (the adapter) · Security (what it must not
stop doing).
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDLER = ROOT / "platform" / "gateway" / "handler.py"


@pytest.fixture(scope="module")
def tree() -> ast.Module:
    return ast.parse(HANDLER.read_text(encoding="utf-8"), filename=str(HANDLER))


@pytest.fixture(scope="module")
def source() -> str:
    return HANDLER.read_text(encoding="utf-8")


def calls_named(tree: ast.Module, *names: str) -> list[ast.Call]:
    """Every call whose callee ends in one of `names`, however it is spelled."""
    wanted = set(names)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        label = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if label in wanted:
            found.append(node)
    return found


def keyword(call: ast.Call, name: str):
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


# --- the control is wired up at all ------------------------------------------

def test_the_handler_is_the_only_thing_that_needs_this_file(tree):
    """A guard on the guard. If `run_turn` stops being called here, every
    assertion below passes vacuously and this file becomes decoration — the
    coverage-check argument `test_hermeticity.py` makes about a scanner that finds
    zero files to scan."""
    assert calls_named(tree, "run_turn"), "the handler no longer runs a turn"


def test_the_turn_is_handed_both_an_inspection_and_what_to_inspect(tree):
    """`inspect=` alone satisfies the loop's required-argument guard while
    `untrusted=()` leaves the system channel uninspected — the plant all four
    seats landed green. Both arguments have to be present."""
    for call in calls_named(tree, "run_turn"):
        assert keyword(call, "inspect") is not None, "run_turn called without an inspection"
        assert keyword(call, "untrusted") is not None, (
            "run_turn called without declaring what is untrusted — the system channel "
            "is then uninspected in production while every loop test still passes")


def test_the_system_block_is_not_declared_untrusted(source):
    """**The withdrawal, pinned so it cannot be silently re-added.**

    This assertion is the inverse of the one that was here first, and the reversal
    is the whole finding. Declaring the system block untrusted was ADR-035's
    Change B as designed; seven `ApplyGuardrail` calls established, before any
    model call, that the clean system block is blocked — by `PROMPT_ATTACK` and by
    the entitlement topic — and that clean and poisoned block identically. It is
    sent on every gateway call, so the control would refuse every golden question
    and every probe before the model was reached, and every probe would have
    scored PASS on it because `observation_from_record` reads `decision` and
    `mechanism` and not `channel`.

    Amendment 1 withdrew it: the form is wrong, not the timing. Re-adding it is
    gated on amendment 2's row 12 — whether the clean catalog stops tripping the
    topic under guardrail v3 — and on scoping the inspection to the interpolated
    DATA rather than the whole assembled prompt.

    So this fails if someone puts it back, and the failure message says what to
    measure first. A withdrawal recorded only in an ADR is one a tidy-up
    reinstates."""
    untrusted = [line for line in source.splitlines()
                 if line.strip().startswith("untrusted =")]
    assert len(untrusted) == 1, f"expected one `untrusted` assignment, found {untrusted}"
    assert "NOTHING_UNTRUSTED" in untrusted[0], (
        f"`untrusted` is assigned {untrusted[0].strip()!r}. The system channel was "
        "WITHDRAWN by ADR-035 amendment 1, not deferred: the clean system block is "
        "blocked by the deployed guardrail and is sent on every call, so declaring it "
        "refuses everything before the model is reached, and clean and poisoned block "
        "identically so nothing can tell a catch from an outage. Before re-adding it, "
        "resolve row 12 (does the clean catalog stop tripping the topic under v3?) and "
        "scope the inspection to the interpolated data rather than the whole prompt. "
        "See milestones/ADR-035/preflight-v2.json."
    )


def test_the_untrusted_declaration_is_still_wired_through(tree):
    """The withdrawal is of the *content*, not of the mechanism. `run_turn` must
    still be handed an `untrusted` argument, so the recoverable version is a
    change to one line rather than a re-plumbing — and so the loop's required
    argument keeps meaning something."""
    for call in calls_named(tree, "run_turn"):
        assert keyword(call, "untrusted") is not None, (
            "run_turn called without `untrusted`. The system half is withdrawn; the "
            "mechanism is not.")


# --- and wired up correctly ---------------------------------------------------

def test_the_inspection_assesses_content_as_input(tree):
    """`PROMPT_ATTACK` is input-only by the service's design and is one of the two
    policies that fired on M04's user-turn arm. Assessing platform-supplied
    content as OUTPUT drops exactly the filter this channel most needs, and the
    docstring arguing so was the only thing defending it."""
    applies = calls_named(tree, "apply_guardrail")
    assert applies, "the handler no longer calls apply_guardrail"
    for call in applies:
        source_kw = keyword(call, "source")
        assert isinstance(source_kw, ast.Constant) and source_kw.value == "INPUT", (
            "apply_guardrail must assess this content as INPUT")


def test_the_inspection_uses_the_same_pinned_version_as_the_turn(tree):
    """Never DRAFT, and never a literal. A DRAFT guardrail can be edited outside a
    commit and silently change every recorded probe result (ADR-018) — and the IAM
    grant is on the guardrail ARN unqualified by version, so nothing downstream
    would refuse it. `verify_guardrail_pin.py` checks the deployed policy, not
    what this file passes; this is the assertion that covers the gap."""
    for call in calls_named(tree, "apply_guardrail"):
        version = keyword(call, "guardrailVersion")
        assert isinstance(version, ast.Name) and version.id == "GUARDRAIL_VERSION", (
            "apply_guardrail must use the pinned GUARDRAIL_VERSION, never a literal "
            "and never DRAFT")
        identifier = keyword(call, "guardrailIdentifier")
        assert isinstance(identifier, ast.Name) and identifier.id == "GUARDRAIL_ID", (
            "apply_guardrail must use the same guardrail the turn transits")


def test_the_converse_path_and_the_inspection_path_pin_the_same_thing(tree):
    """"Equivalently" is meant literally. If the two paths could name different
    versions, a probe result would be attributable to neither."""
    versions = set()
    for call in calls_named(tree, "apply_guardrail"):
        node = keyword(call, "guardrailVersion")
        versions.add(getattr(node, "id", None))
    for call in calls_named(tree, "converse"):
        config = keyword(call, "guardrailConfig")
        if isinstance(config, ast.Dict):
            for key, value in zip(config.keys, config.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == "guardrailVersion":
                    versions.add(getattr(value, "id", None))
    assert versions == {"GUARDRAIL_VERSION"}, (
        f"the two guardrail paths do not pin the same version: {versions}")


def test_the_inspected_text_is_not_sliced(tree):
    """"Nothing here is truncated." A payload too large for the API must raise and
    fail the turn; trimming it to fit puts the tail of every long result outside
    the control while the record goes on saying the content was inspected."""
    for call in calls_named(tree, "apply_guardrail"):
        content = keyword(call, "content")
        assert content is not None, "apply_guardrail called with no content"
        for node in ast.walk(content):
            assert not isinstance(node, ast.Subscript), (
                "the content handed to apply_guardrail is sliced or indexed — a "
                "truncation the audit record would not disclose")


def test_no_handler_code_swallows_a_failed_inspection(tree):
    """G2: an errored control blocks, never skips. An `except` around the
    inspection that returns a clean verdict turns a throttle into "content
    inspected, nothing found", and the record then makes the positive claim that
    the content was assessed. The loop's fail-loud discipline is real and
    asserted, but it only defends the boundary this file hands it."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if calls_named(ast.Module(body=node.body, type_ignores=[]), "apply_guardrail"):
            raise AssertionError(
                "an apply_guardrail call is inside a try/except in handler.py. A failed "
                "inspection must propagate: the loop wraps it in TurnFailed so the tool "
                "records already earned still reach the lake and the harness reports "
                "INFRA rather than a decision."
            )


def test_the_guardrails_own_usage_is_not_folded_into_the_token_meter(tree):
    """`ApplyGuardrail` reports guardrail TEXT UNITS. The budgets are
    token-denominated (ADR-014) and a text unit is not a token, so a `usage` read
    off this response and added to the meter would make the budget axis report a
    number with two denominations in it.

    `meter.assert_token_denominated` would not catch it: that function rejects
    currency-shaped keys, and `text_units` is not one. So the assertion has to be
    that the read never happens. Walked as a tree rather than grepped as text —
    the first version of this matched the word inside the docstring explaining why
    the read is wrong, which is a test that fails on its own reasoning."""
    inspect_fns = [node for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef) and node.name == "_inspect"]
    assert inspect_fns, "no `_inspect` in the handler"

    for fn in inspect_fns:
        for node in ast.walk(fn):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                assert node.slice.value != "usage", (
                    "_inspect reads a `usage` off the ApplyGuardrail response. Guardrail "
                    "text units are not tokens (ADR-014).")
            if isinstance(node, ast.Attribute):
                assert node.attr != "usage", (
                    "_inspect reads a `usage` off the ApplyGuardrail response. Guardrail "
                    "text units are not tokens (ADR-014).")

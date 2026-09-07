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

**What this file reads, and why that grew (seat round on PRs #85-#102).** It read
`handler.py`'s source and nothing else, and the Security seat showed that was half
the wiring. The names at the call sites were pinned; **what those names are bound
to was not.** Swapping the four `GUARDRAIL_*` environment bindings in the
synthesised stack put every model turn through the guardrail with no topic policy
and left the suite at 2389 passed — the exact outcome
`test_the_converse_path_and_the_inspection_path_pin_the_same_thing` says in its
own docstring it exists to catch. An AST test cannot see a binding, so this file
now also reads the committed CDK snapshot. Both halves are the wiring; only one
of them was ever asserted.

**What ADR-070 changed here.** `converse` carries no guardrail; `_inspect` is
the whole of it, four arms selected by explicit channel comparison, each pinning
its pair and its `source` at the call site. The converse/inspection pin became
two: the model call names NO guardrail, and every arm pins a published version
of the guardrail its channel names, at the source its channel names — read as a
table, so PR 5's stage-2 move is a one-row diff to that table. Constraint 3
("the handler serialises nothing") and amendment 2 ("the record names the
guardrail that assessed it") are pinned on the source below, because the
handler is the one place where either could quietly stop being true.

Hermetic (G8): reads source and a committed JSON fixture, imports nothing under
test.
Owning seat: Platform Engineering (the adapter) · Security (what it must not
stop doing).
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDLER = ROOT / "platform" / "gateway" / "handler.py"
SNAPSHOT = (ROOT / "platform" / "infra" / "tests" / "fixtures"
            / "BeaconpaveGateway.template.json")

#: The two guardrails, identified by the property that distinguishes them rather
#: than by their names. `beaconpave-gateway` carries the topic policy and every
#: model turn transits it; `beaconpave-tool-output` is the same policy with
#: `TopicPolicyConfig` omitted (ADR-063). Resolving by policy means a rename
#: cannot satisfy these assertions and neither can a swap.
MAIN_ENV = ("GUARDRAIL_ID", "GUARDRAIL_VERSION")
TOOL_OUTPUT_ENV = ("TOOL_OUTPUT_GUARDRAIL_ID", "TOOL_OUTPUT_GUARDRAIL_VERSION")


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

def _call_named(tree, func_name, callee_attr):
    """Every call to `<something>.<callee_attr>` inside `def func_name`."""
    import ast
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == func_name)
    return [n for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == callee_attr]


def _kwarg(call, name):
    return next((k.value for k in call.keywords if k.arg == name), None)


def test_the_probe_path_records_that_it_ran_nothing(tree):
    """**`SPEC/06b` B9.** `_tool_probe` authorizes and calls nothing -- its own
    docstring says *"an allowed probe still calls nothing"* -- and it writes a full
    `decision: allowed` audit record for that. Until `tool.executed` existed, that
    record was indistinguishable from a real first tool call, and it could land on
    the same lake key: `authorize()` increments `calls` before returning, so both
    this path and `toolloop` hand `seq=1` to `record_key`, and `request_id` is
    caller-supplied. So a trajectory derived from the lake by counting allowed
    records credited a call that never happened.

    This is asserted on the source because `handler.py` holds the boto3 clients and
    is outside the hermetic surface (ADR-039) -- the same reason every other check
    in this file reads the tree instead of running it."""
    import ast
    calls = _call_named(tree, "_tool_probe", "as_record_fragment")
    assert len(calls) == 1, f"expected one fragment built in _tool_probe, found {len(calls)}"
    executed = _kwarg(calls[0], "executed")
    assert executed is not None, (
        "_tool_probe builds an audit fragment without saying whether the tool ran. "
        "It runs nothing, so it must say so: an omitted `executed` means UNKNOWN, and "
        "this path knows.")
    assert isinstance(executed, ast.Constant) and executed.value is False, (
        "_tool_probe must record executed=False -- it authorizes and calls nothing")


def test_the_model_path_records_execution_from_the_call_and_not_from_the_decision(tree):
    """The real path must report what the loop OBSERVED, not what the plane
    permitted. `call.executed` is tracked at the point the tool is reached; reading
    it off `decision.allowed` would credit a call the platform could not route, and
    reading it off `payload` would deny one whose result was rejected after it ran."""
    import ast
    calls = _call_named(tree, "_tool_records", "as_record_fragment")
    assert len(calls) == 1, f"expected one fragment built in _tool_records, found {len(calls)}"
    executed = _kwarg(calls[0], "executed")
    assert executed is not None, "_tool_records builds a fragment that says nothing about execution"
    assert isinstance(executed, ast.Attribute) and executed.attr == "executed", (
        "execution must come from the ToolCall the loop produced")
    assert isinstance(executed.value, ast.Name) and executed.value.id == "call", (
        f"expected `call.executed`, got `{ast.unparse(executed)}`")


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

#: The stage-2 channel table (ADR-070 decisions 3 and 4): for each arm of
#: `_inspect`, keyed by the `guardrail.CHANNEL_*` constant its comparison names
#: (`None` is the fall-through arm), the identifier name, the version name and
#: the `source` its `apply_guardrail` call must carry.
#:
#: **PR 5 edited this table by one row, and nothing else.** Stage 1 assessed
#: `CHANNEL_TOOL_REQUEST` with the main pair at `OUTPUT`, `converse`'s own
#: coverage, and measured 51 of 51 refusals there (amendment 5). Stage 2 moves
#: that row to the tool-output pair at `INPUT`; the other three rows do not
#: move. `INPUT` is where `PROMPT_ATTACK` fires — input-only by the service's
#: design, one of the two policies that fired on M04's user-turn arm — so it is
#: the source for content read as an instruction: the viewer's turn, a tool
#: result, and now a tool request. `OUTPUT` is what `converse` assessed the
#: model's own output as, and the answer keeps it.
STAGE_2_ARMS = {
    "CHANNEL_TOOL_OUTPUT": ("_TOOL_OUTPUT_GUARDRAIL_ID", "_TOOL_OUTPUT_GUARDRAIL_VERSION", "INPUT"),
    "CHANNEL_TOOL_REQUEST": ("_TOOL_OUTPUT_GUARDRAIL_ID", "_TOOL_OUTPUT_GUARDRAIL_VERSION", "INPUT"),
    "CHANNEL_ANSWER": ("GUARDRAIL_ID", "GUARDRAIL_VERSION", "OUTPUT"),
    None: ("GUARDRAIL_ID", "GUARDRAIL_VERSION", "INPUT"),
}


def _inspect_body(tree) -> list:
    outer = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == "_inspect")
    inner = next(n for n in ast.walk(outer)
                 if isinstance(n, ast.FunctionDef) and n.name == "inspect")
    return inner.body


def _channel_named(test) -> str | None:
    """The `guardrail.CHANNEL_*` constant a branch condition compares `channel` to."""
    for node in ast.walk(test):
        if (isinstance(node, ast.Compare) and isinstance(node.left, ast.Name)
                and node.left.id == "channel"):
            for c in node.comparators:
                if isinstance(c, ast.Attribute) and c.attr.startswith("CHANNEL_"):
                    return c.attr
    return None


def _arm(body: list) -> dict:
    """What one arm pins: the `apply_guardrail` pair and source, and the pair it
    hands `interpret_apply`. Exactly one of each, or the arm is not readable.

    **And nothing else (Security round 2, SR-A).** `channel = ROUTE.get(channel,
    channel)` prepended to the closure was swept into the fall-through arm and
    read as inert while it re-routed `tool_request` to the topic-free policy
    under a relabelled channel. An arm is exactly two statements: the
    `apply_guardrail` assignment and the `interpret_apply` return."""
    shape = [type(stmt).__name__ for stmt in body]
    assert shape == ["Assign", "Return"], (
        f"an arm of _inspect is {shape}; it must be exactly `response = "
        "_bedrock.apply_guardrail(...)` and `return guardrail.interpret_apply(...)`. Any "
        "other statement can rebind the channel or the text before the pinned call")
    module = ast.Module(body=body, type_ignores=[])
    applies = calls_named(module, "apply_guardrail")
    interprets = calls_named(module, "interpret_apply")
    assert len(applies) == 1 and len(interprets) == 1, (
        f"an arm of _inspect carries {len(applies)} apply_guardrail and "
        f"{len(interprets)} interpret_apply calls; one of each, at the call site, is what "
        "this file can read")
    apply, interpret = applies[0], interprets[0]
    # Platform-eng round 2, P5: `calls_named` matches the callee's NAME, so a local
    # `_reader.interpret_apply` shim forcing `channel=CHANNEL_ANSWER` satisfied
    # every arm pin. The callee is the real one, by its full dotted name.
    assert ast.unparse(apply.func) == "_bedrock.apply_guardrail", (
        f"an arm calls {ast.unparse(apply.func)}; it must call _bedrock.apply_guardrail")
    assert ast.unparse(interpret.func) == "guardrail.interpret_apply", (
        f"an arm reads its verdict through {ast.unparse(interpret.func)}; it must be "
        "guardrail.interpret_apply")
    return {
        "apply": (getattr(keyword(apply, "guardrailIdentifier"), "id", None),
                  getattr(keyword(apply, "guardrailVersion"), "id", None),
                  getattr(keyword(apply, "source"), "value", None)),
        "interpret": (getattr(keyword(interpret, "guardrail_id"), "id", None),
                      getattr(keyword(interpret, "version"), "id", None)),
        "reported_on": ast.unparse(keyword(interpret, "channel"))
        if keyword(interpret, "channel") is not None else None,
    }


#: Each arm's condition, unparsed, literally. **AI Quality Q1 and Tool Owner TO-1,
#: the same plant from two seats:** `_channel_named` found the channel constant in
#: a condition and ignored every other conjunct, so `and False` on the
#: `tool_request` arm (stage 1 silently at INPUT) and `and not
#: _TOOL_OUTPUT_GUARDRAIL_ID` on the tool-output arm (ADR-063 silently reverted)
#: both passed the whole suite. The one conjunct the design has — the tool-output
#: pair may be unconfigured — is the only one this admits.
ARM_CONDITIONS = {
    "CHANNEL_TOOL_OUTPUT": "channel == guardrail.CHANNEL_TOOL_OUTPUT and _TOOL_OUTPUT_GUARDRAIL_ID",
    "CHANNEL_TOOL_REQUEST": "channel == guardrail.CHANNEL_TOOL_REQUEST and _TOOL_OUTPUT_GUARDRAIL_ID",
    "CHANNEL_ANSWER": "channel == guardrail.CHANNEL_ANSWER",
}


def arms(tree) -> dict:
    """`_inspect`'s arms, keyed by the channel constant each compares against.

    Read from the shape ADR-063 chose and ADR-070 kept: a sequence of `if
    channel == guardrail.CHANNEL_X:` branches that each return, and a
    fall-through arm after them keyed `None`. An `elif` chain is read the same
    way. A branch that names no channel is refused, because then this file
    cannot say which policy which content gets."""
    found: dict = {}

    def read(statements: list):
        rest = []
        for stmt in statements:
            assert not (rest and isinstance(stmt, ast.If)), (
                "a statement precedes an `if channel == ...` arm in _inspect; the arm chain "
                "must be the whole body, or the statement can rebind what the arms see")
            if isinstance(stmt, ast.If):
                channel = _channel_named(stmt.test)
                assert channel is not None, (
                    f"an `if` in _inspect does not compare `channel` to a "
                    f"guardrail.CHANNEL_* constant: {ast.unparse(stmt.test)}")
                assert channel not in found, f"{channel} is selected by two arms"
                found[channel] = dict(_arm(stmt.body), condition=ast.unparse(stmt.test))
                if stmt.orelse:
                    read(stmt.orelse)
            else:
                rest.append(stmt)
        if rest:
            assert None not in found, "two fall-through arms"
            found[None] = _arm(rest)

    read(_inspect_body(tree))
    return found


def test_each_arm_pins_the_pair_and_source_its_channel_names(tree):
    """**The stage-2 table, read off the source (ADR-070 decisions 3 and 4).**

    This replaces the test that required `source="INPUT"` on every call — true
    when the only inspected content was platform-supplied, and false the moment
    the loop began assessing the model's own output, which `converse` assessed
    as OUTPUT. The property is now per channel, and it is the whole table rather
    than one property of it: an arm at the wrong source, or a channel routed to
    the wrong pair, or a missing arm, each reads as a different row."""
    assert {k: v["apply"] for k, v in arms(tree).items()} == STAGE_2_ARMS


#: The module-level constants `handler.py` may pin a guardrail with.
#:
#: A CLOSED set, and that is the point: before ADR-063 this test required the
#: literal names `GUARDRAIL_ID`/`GUARDRAIL_VERSION`, which enforced "pinned,
#: never a literal, never DRAFT" by enforcing a shape. ADR-063 legitimately adds
#: a second pair, so the shape moved and the property did not. Widening this set
#: is how a third pair would be added — deliberately, in a diff that says why —
#: rather than by relaxing the assertion to "any name will do".
PINNED_IDENTIFIERS = frozenset({"GUARDRAIL_ID", "_TOOL_OUTPUT_GUARDRAIL_ID"})
PINNED_VERSIONS = frozenset({"GUARDRAIL_VERSION", "_TOOL_OUTPUT_GUARDRAIL_VERSION"})


def test_the_inspection_uses_the_same_pinned_version_as_the_turn(tree):
    """Never DRAFT, and never a literal. A DRAFT guardrail can be edited outside a
    commit and silently change every recorded probe result (ADR-018) — and the IAM
    grant is on the guardrail ARN unqualified by version, so nothing downstream
    would refuse it. `verify_guardrail_pin.py` checks the deployed policy, not
    what this file passes; this is the assertion that covers the gap."""
    for call in calls_named(tree, "apply_guardrail"):
        version = keyword(call, "guardrailVersion")
        identifier = keyword(call, "guardrailIdentifier")
        # **The property, not the shape (ADR-063).** This used to require the
        # literal names `GUARDRAIL_ID`/`GUARDRAIL_VERSION`, which was a proxy for
        # "pinned, never a literal, never DRAFT" and stopped being true when the
        # tool-output channel gained its own pinned pair. The proxy is replaced
        # rather than deleted: both must still be NAMES — a string literal or an
        # attribute lookup fails here exactly as it did before — and the names
        # must come from the closed set of module constants below.
        for node, role in ((version, "guardrailVersion"), (identifier, "guardrailIdentifier")):
            assert isinstance(node, ast.Name), (
                f"apply_guardrail passes a non-name for {role}. It must be one of the "
                "module-level pinned constants, never a literal and never DRAFT.")
        assert version.id in PINNED_VERSIONS, (
            f"apply_guardrail uses {version.id!r} as the version; permitted: "
            f"{sorted(PINNED_VERSIONS)}")
        assert identifier.id in PINNED_IDENTIFIERS, (
            f"apply_guardrail uses {identifier.id!r} as the identifier; permitted: "
            f"{sorted(PINNED_IDENTIFIERS)}")


def test_the_model_call_carries_no_guardrail(tree):
    """**ADR-070: `converse` carries no `guardrailConfig`.** The gateway applies
    the guardrail itself, per channel, and a guardrail on the model call would
    assess the transcript a second time under a policy the loop did not choose
    and label the result `answer` — the exact ambiguity option B exists to end.

    This is the converse half of the test ADR-063 fixed. That version located a
    `guardrailConfig` dict by shape — any dict literal carrying
    `guardrailIdentifier` and `guardrailVersion` together — because the keyword
    was never a direct argument of `converse(...)`. The same location is kept,
    inverted: there must be no such dict anywhere, and no `guardrailConfig`
    keyword or string anywhere, however the config might be assembled."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
            assert not {"guardrailIdentifier", "guardrailVersion"} <= keys, (
                "a dict literal carries guardrailIdentifier and guardrailVersion together. "
                "That is a converse guardrailConfig, and ADR-070 removed it: the loop "
                "applies the guardrail per channel through _inspect.")
        if isinstance(node, ast.Constant) and node.value == "guardrailConfig":
            raise AssertionError("the string 'guardrailConfig' appears in handler.py")
        if isinstance(node, ast.keyword) and node.arg == "guardrailConfig":
            raise AssertionError("a call in handler.py passes guardrailConfig=")
    # Security round 3, SR3-D: `kwargs["guardrail" + "Config"] = dict(guardrailIdentifier=...)`
    # defeated the three shapes above. The two guardrail keywords may appear only
    # on an apply_guardrail call, and no string constant may be a fragment of the
    # forbidden key.
    applies = {id(kw) for call in calls_named(tree, "apply_guardrail") for kw in call.keywords}
    docstrings = {id(n.value) for n in ast.walk(tree)
                  if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    for node in ast.walk(tree):
        if id(node) in docstrings:
            continue
        if isinstance(node, ast.keyword) and node.arg in {"guardrailIdentifier", "guardrailVersion"}:
            assert id(node) in applies, (
                f"{node.arg}= appears outside an apply_guardrail call: a guardrail config "
                "assembled for the model call")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert node.value not in {"Config", "guardrailC", "onfig", "rail" + "Config"} and \
                "guardrailconfig" not in node.value.replace(" ", "").lower(), (
                    f"the string {node.value!r} is a fragment of 'guardrailConfig'")


def test_every_inspection_site_pins_a_published_version_of_the_guardrail_its_channel_names(tree):
    """The inspection half, per arm. Every `apply_guardrail` names a version from
    the closed set of pinned constants — never a literal, never DRAFT — and, arm
    by arm, the pair it names is the pair the stage-2 table gives that channel.
    `test_each_arm_pins_the_pair_and_source_its_channel_names` reads the table
    whole; this one is the ADR-018 property on its own, so a DRAFT literal fails
    here with the message about pinning rather than as a table mismatch."""
    inspection = {getattr(keyword(call, "guardrailVersion"), "id", None)
                  for call in calls_named(tree, "apply_guardrail")}
    assert inspection and inspection <= PINNED_VERSIONS, (
        f"the inspection path pins {sorted(inspection)}; permitted: "
        f"{sorted(PINNED_VERSIONS)}. Never a literal, never DRAFT.")
    for channel, arm in arms(tree).items():
        assert arm["apply"][1] == STAGE_2_ARMS[channel][1], (
            f"the {channel or 'fall-through'} arm pins {arm['apply'][1]!r}, and the stage-2 "
            f"table says {STAGE_2_ARMS[channel][1]!r}")


def test_each_arm_hands_interpret_apply_the_pair_it_applied(tree):
    """**ADR-070 amendment 2: the record names the guardrail that assessed it.**
    The pair travels from the `apply_guardrail` call site onto the outcome
    through `interpret_apply(..., guardrail_id=, version=)`, so the handler never
    has to decide which guardrail a channel used. That is only true if the two
    call sites in each arm name the same constants — which this asserts, arm by
    arm, so a copy-paste that applies one guardrail and records the other is a
    red check rather than a lake full of misattributed records."""
    for channel, arm in arms(tree).items():
        assert arm["interpret"] == arm["apply"][:2], (
            f"the {channel or 'fall-through'} arm applies {arm['apply'][:2]} and tells "
            f"interpret_apply {arm['interpret']}. The record would name a guardrail that "
            "did not assess the content.")


def test_each_arm_is_reachable_by_its_channel_comparison_alone(tree):
    """The conditions, whole. A pinned arm that never executes is the
    stated-and-absent shape: `STAGE_2_ARMS` would describe an arm the content
    never reaches, and PR 4's stage-1 band would measure a mechanism the ADR
    did not price. See `ARM_CONDITIONS`."""
    conditions = {k: v["condition"] for k, v in arms(tree).items() if k is not None}
    assert conditions == ARM_CONDITIONS, (
        f"_inspect's arm conditions are {conditions}; an extra conjunct can disarm a "
        "pinned arm while every pin stays green")


def test_each_arm_reports_its_verdict_on_the_channel_it_was_asked_about(tree):
    """**Platform Engineering seat, PR 2 plant P11 (survived).** The
    `tool_request` arm handed `interpret_apply` `channel=guardrail.CHANNEL_ANSWER`
    and 248 tests passed: `_arm` read the pair and never the channel, so every
    `tool_request` block would have recorded `channels: ["answer"]` — the exact
    field ADR-070 decision 4 reads to decide whether stage 2 is built. Each arm
    reports on the bare `channel` parameter it was called with, never a constant
    of its own choosing."""
    for name, arm in arms(tree).items():
        assert arm["reported_on"] == "channel", (
            f"the {name or 'fall-through'} arm calls interpret_apply with "
            f"channel={arm['reported_on']!r}; it must pass the `channel` it was asked "
            "about, or the record attributes the block to the wrong side")


def test_inspect_returns_the_pinned_closure_and_nothing_wraps_it(tree):
    """**Platform Engineering seat, PR 2 plant P2 (survived).** A `dispatch`
    closure defined inside `_inspect`, wrapping the pinned `inspect` and
    re-routing `tool_request` to the tool-output policy under a relabelled
    channel, passed 248 tests: the table reads the inner `inspect` and nothing
    pinned what `_inspect` returns. That plant IS PR 5's stage-2 move, in a diff
    that reads as inert. So `_inspect`'s body is exactly one nested function
    named `inspect` and `return inspect`, and `run_turn` is handed `_inspect()`
    bare — no wrapper on either side of the closure."""
    outer = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == "_inspect")
    body = [stmt for stmt in outer.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
    shape = [type(stmt).__name__ for stmt in body]
    assert shape == ["FunctionDef", "Return"], (
        f"_inspect's body is {shape}; it must be exactly `def inspect` and `return inspect`")
    assert body[0].name == "inspect"
    # Security round 2, SR-B: a `@_staged` decorator on `def inspect` wrapped the
    # pinned closure with the body shape, the nesting and the bare `_inspect()`
    # all intact. Neither function may carry a decorator.
    assert outer.decorator_list == [] and body[0].decorator_list == [], (
        "_inspect or inspect carries a decorator; a decorator is a wrapper the shape "
        "checks cannot see")
    stores = sorted({n.id for n in ast.walk(outer)
                     if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)})
    assert stores == ["response"], (
        f"_inspect assigns to {stores}; only `response` may be bound inside it — a "
        "rebinding of `channel` or `text` changes what the pinned call sites see")
    returned = body[1].value
    assert isinstance(returned, ast.Name) and returned.id == "inspect", (
        f"_inspect returns `{ast.unparse(returned)}`, not the pinned closure")
    nested = [n.name for n in ast.walk(outer) if isinstance(n, ast.FunctionDef)
              and n is not outer]
    assert nested == ["inspect"], f"_inspect defines {nested}; only `inspect` may be defined"

    for call in calls_named(tree, "run_turn"):
        handed = keyword(call, "inspect")
        assert (isinstance(handed, ast.Call) and isinstance(handed.func, ast.Name)
                and handed.func.id == "_inspect" and not handed.args and not handed.keywords), (
            f"run_turn is handed inspect={ast.unparse(handed)}; it must be `_inspect()` bare")


def test_the_outcome_the_fragment_is_built_from_is_the_loops_and_not_a_fallback(tree):
    """**Platform Engineering seat, PR 2 plant P8 (survived).**
    `applied = outcome.guardrail or GuardrailOutcome(..., GUARDRAIL_ID,
    GUARDRAIL_VERSION)` passed every test: the fragment test pins the two
    arguments of `as_record_fragment` and not what `applied` is bound to, so
    `as_record_fragment`'s refusal of a missing pair became unreachable and an
    unstamped outcome would be written as the main guardrail. The single
    assignment to `applied` in `handler()` is `outcome.guardrail`, bare."""
    handler = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "handler")
    # Platform-eng round 2, P2: `applied, _ = (applied or <fallback>), None` rebinds
    # through a tuple target, which a count of bare-Name Assign targets missed.
    # Every Store-context binding of the name counts, whatever statement binds it.
    bindings = [n for n in ast.walk(handler)
                if isinstance(n, ast.Name) and n.id == "applied" and isinstance(n.ctx, ast.Store)]
    assert len(bindings) == 1, (
        f"`applied` is bound {len(bindings)} times in handler(); once, from the outcome")
    assignments = [n for n in ast.walk(handler) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "applied" for t in n.targets)]
    assert len(assignments) == 1, f"expected one assignment to `applied`, found {len(assignments)}"
    assert ast.unparse(assignments[0].value) == "outcome.guardrail", (
        f"`applied = {ast.unparse(assignments[0].value)}` — the fragment must be built from "
        "the outcome the loop returned, with no fallback that names a guardrail nothing "
        "consulted")
    builds = calls_named(handler, "as_record_fragment")
    assert all(ast.unparse(a.value) == "applied" for a in builds[0].args), (
        "the fragment's arguments are not read off `applied`")


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


# --- the other half of the wiring: what those names are BOUND to ---------------
#
# Everything above reads `handler.py`. Everything below reads the committed CDK
# snapshot, because the Security seat's plant lived entirely in the gap between
# them: the call sites named `GUARDRAIL_VERSION`, every assertion was satisfied,
# and the variable resolved to the topic-free guardrail.


@pytest.fixture(scope="module")
def template() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def _resources(template: dict, kind: str) -> dict:
    return {name: body for name, body in template["Resources"].items()
            if body["Type"] == kind}


def _gateway_env(template: dict) -> dict:
    """The gateway function's environment, found by what it carries.

    Located by the guardrail binding rather than by the CDK's generated logical
    id, which carries a hash and moves for reasons that are not policy changes."""
    functions = [body for body in _resources(template, "AWS::Lambda::Function").values()
                 if "GUARDRAIL_ID" in ((body["Properties"].get("Environment") or {})
                                       .get("Variables") or {})]
    assert len(functions) == 1, (
        f"expected exactly one function carrying GUARDRAIL_ID, found {len(functions)}. "
        "If a second function now transits a guardrail it needs its own assertions "
        "here rather than sharing these.")
    return functions[0]["Properties"]["Environment"]["Variables"]


def _referenced(value) -> str | None:
    """The logical id a `Fn::GetAtt` points at, or None for anything else."""
    if isinstance(value, dict) and "Fn::GetAtt" in value:
        return value["Fn::GetAtt"][0]
    return None


def test_the_two_guardrails_are_still_told_apart_by_their_topic_policy(template):
    """The property the bindings are checked against, asserted before it is used.

    If both guardrails ever carry a topic policy — or neither does — every
    assertion below silently stops distinguishing them and would keep passing. So
    the discriminator is established first, and its failure says which."""
    guardrails = _resources(template, "AWS::Bedrock::Guardrail")
    with_topics = {name for name, body in guardrails.items()
                   if body["Properties"].get("TopicPolicyConfig")}
    assert len(guardrails) == 2 and len(with_topics) == 1, (
        f"{len(guardrails)} guardrails, {len(with_topics)} carrying a topic policy. "
        "ADR-063's whole shape is two guardrails differing by that policy; if that "
        "stops being true, the bindings below can no longer be checked by it and "
        "this file is asserting nothing.")


def test_the_model_turn_is_bound_to_the_guardrail_that_has_the_topic_policy(template):
    """**The Security seat's plant, asserted.**

    Swapping the four `Fn::GetAtt` targets so `GUARDRAIL_ID` resolved to
    `ToolOutputGuardrail` left the suite at 2389 passed. Every model turn would
    then transit a guardrail with no topic policy while tool output transited the
    one that has it — both pin tests still green, because both guardrails still
    exist and still differ only by that policy; and snapshot-drift CI is no help,
    because the same swap written in the TypeScript synthesises to exactly this
    snapshot.

    Resolved by POLICY rather than by name, so renaming the resources cannot
    satisfy it."""
    env = _gateway_env(template)
    guardrails = _resources(template, "AWS::Bedrock::Guardrail")

    main_id, tool_id = _referenced(env[MAIN_ENV[0]]), _referenced(env[TOOL_OUTPUT_ENV[0]])
    assert main_id in guardrails and tool_id in guardrails, (
        f"a guardrail id env var does not resolve to a guardrail resource: "
        f"{MAIN_ENV[0]}->{main_id!r}, {TOOL_OUTPUT_ENV[0]}->{tool_id!r}")
    assert main_id != tool_id, (
        "both guardrail id env vars resolve to the same guardrail; one channel is not "
        "getting the policy it was given.")

    assert guardrails[main_id]["Properties"].get("TopicPolicyConfig"), (
        f"{MAIN_ENV[0]} resolves to {main_id!r}, which carries NO topic policy. Every "
        "model turn transits this guardrail. That is the wiring mistake with the worst "
        "blast radius available here, and it is what this assertion exists for.")
    assert not guardrails[tool_id]["Properties"].get("TopicPolicyConfig"), (
        f"{TOOL_OUTPUT_ENV[0]} resolves to {tool_id!r}, which DOES carry a topic "
        "policy. ADR-063 exists because that channel must not have one: the topic was "
        "measured redundant with PROMPT_ATTACK there and caused 8 refusal samples on "
        "tool output.")


@pytest.mark.parametrize("env_pair", [MAIN_ENV, TOOL_OUTPUT_ENV], ids=["main", "tool_output"])
def test_each_version_binding_belongs_to_the_guardrail_it_is_paired_with(template, env_pair):
    """A version resource names its own guardrail; assert the pair agrees.

    One guardrail's id with the other's version is the same failure one level
    down, and in one way it is worse: the API would be asked for a version that
    does not exist on that id, so the turn fails rather than quietly transiting a
    weaker control."""
    env = _gateway_env(template)
    versions = _resources(template, "AWS::Bedrock::GuardrailVersion")

    id_env, version_env = env_pair
    guardrail = _referenced(env[id_env])
    version_resource = _referenced(env[version_env])
    assert version_resource in versions, (
        f"{version_env} does not resolve to a guardrail version resource "
        f"({version_resource!r})")
    owner = _referenced(versions[version_resource]["Properties"]["GuardrailIdentifier"])
    assert owner == guardrail, (
        f"{version_env} resolves to {version_resource!r}, which is a version of "
        f"{owner!r}, while {id_env} resolves to {guardrail!r}. The pair must name one "
        "guardrail: a version of the other one does not exist on this id.")


def _bucket_referenced(value) -> str | None:
    if isinstance(value, dict) and "Ref" in value:
        return value["Ref"]
    return None


def test_the_store_is_not_the_lake_and_the_gateway_can_only_put_to_it(template):
    """**ADR-071, the binding half.** `WITHHELD_STORE_BUCKET` resolves to a bucket
    of its own, not the audit lake's, and the gateway's role holds nothing but
    put-shaped actions on it: the gateway writes what it refused to return and
    cannot read it back. Asserted on the snapshot because the handler's pins
    read names, and a stack binding both names to one bucket would satisfy
    every one of them while the lake carried the text beside the record."""
    from pave import infra

    env = _gateway_env(template)
    lake, store = _bucket_referenced(env["AUDIT_LAKE_BUCKET"]), _bucket_referenced(
        env["WITHHELD_STORE_BUCKET"])
    buckets = _resources(template, "AWS::S3::Bucket")
    assert lake in buckets and store in buckets, (
        f"AUDIT_LAKE_BUCKET->{lake!r}, WITHHELD_STORE_BUCKET->{store!r}; both must be buckets "
        "in this stack")
    assert lake != store, (
        "the store IS the lake: the refused text would sit in the bucket the audit record "
        "lives in, one prefix away from the evidence G4 says it cannot reach")
    props = buckets[store]["Properties"]
    assert props.get("VersioningConfiguration", {}).get("Status") == "Enabled"
    assert props.get("PublicAccessBlockConfiguration", {}).get("BlockPublicAcls") is True

    gateway_roles = [r for r in infra.roles(template) if infra.is_gateway_role(r)]
    assert gateway_roles, "no gateway role in the snapshot"
    on_store = []
    for grant in infra.statements(template):
        if not set(grant["roles"]) & set(gateway_roles):
            continue
        if store in json.dumps(grant["statement"].get("Resource")):
            on_store.extend(infra.actions_of(grant["statement"]))
    assert on_store, "the gateway holds no grant on the store; nothing could be held"
    readers = sorted(a for a in on_store
                     if not (a.startswith("s3:Put") or a.startswith("s3:Abort")))
    assert not readers, (
        f"the gateway role holds {readers} on the store. Put only: the gateway cannot read "
        "back the text it refused to return, and a `Get` here is the handler one line away "
        "from quoting it")


#: The two legal (identifier, version) pairings at an `apply_guardrail` call site.
#:
#: `PINNED_IDENTIFIERS` and `PINNED_VERSIONS` above are two independent closed
#: sets, so until now every id could be paired with every version and the whole
#: cross product passed. The Security seat planted `_TOOL_OUTPUT_GUARDRAIL_ID`
#: with `GUARDRAIL_VERSION` and this file stayed green — the exact failure
#: `_inspect`'s own docstring claims to guard, guarded by env-var presence and
#: never at the call site.
LEGAL_PINS = frozenset({
    ("GUARDRAIL_ID", "GUARDRAIL_VERSION"),
    ("_TOOL_OUTPUT_GUARDRAIL_ID", "_TOOL_OUTPUT_GUARDRAIL_VERSION"),
})


def test_no_call_site_pairs_one_guardrails_id_with_the_others_version(tree):
    for call in calls_named(tree, "apply_guardrail"):
        pair = (getattr(keyword(call, "guardrailIdentifier"), "id", None),
                getattr(keyword(call, "guardrailVersion"), "id", None))
        assert pair in LEGAL_PINS, (
            f"apply_guardrail pins {pair}, which is not one of the legal pairings "
            f"{sorted(LEGAL_PINS)}. An id and a version from different guardrails asks "
            "Bedrock for a version that does not exist on that id.")


def test_every_policy_is_selected_by_equality_not_by_its_negation(tree):
    """`==` flipped to `!=` at the channel comparison left the suite green.

    Every inspected channel except tool output would then run against the
    topic-free guardrail — the same blast radius as the binding swap, reached
    from the runtime side instead of the infra side. Located by what it compares,
    so moving or renaming the `if` does not evade it. **Every channel comparison
    (ADR-070)**, not only the tool-output one: a negated `CHANNEL_ANSWER` sends
    the viewer's turn to the OUTPUT source, where `PROMPT_ATTACK` does not fire."""
    comparisons = [node for node in ast.walk(tree)
                   if isinstance(node, ast.Compare)
                   and isinstance(node.left, ast.Name) and node.left.id == "channel"
                   and any(isinstance(c, ast.Attribute) and c.attr.startswith("CHANNEL_")
                           for c in node.comparators)]
    assert {c.attr for node in comparisons for c in node.comparators
            if isinstance(c, ast.Attribute)} >= {"CHANNEL_TOOL_OUTPUT", "CHANNEL_TOOL_REQUEST",
                                                 "CHANNEL_ANSWER"}, (
        "a channel comparison is missing from _inspect. ADR-063 and ADR-070 route by "
        "explicit channel comparison rather than a mapping, deliberately: a dict would "
        "send a channel added later to whichever policy the default named, and the "
        "direction of that mistake is not knowable in advance.")
    for node in comparisons:
        assert all(isinstance(op, ast.Eq) for op in node.ops), (
            f"`{ast.unparse(node)}` selects a policy by something other than `==`. "
            "Negating it routes every OTHER channel to that policy, which is the control "
            "silently getting weaker.")


# --- constraint 3 and amendment 2, on the source --------------------------------

#: Keys a handler that opened a converse response would read. `_call_tool` is
#: exempt from the last two: it reads an MCP result's `content` to lift the
#: tool's own error text, which is transport, not serialisation.
RESPONSE_KEYS = {"output", "message", "content"}


def _reads_key(node) -> str | None:
    """The string key a `x["k"]` subscript or `x.get("k")` call reads, if any."""
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        return node.slice.value if isinstance(node.slice.value, str) else None
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get" and node.args
            and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
        return node.args[0].value
    return None


def test_the_handler_serialises_nothing(tree):
    """**ADR-070 constraint 3.** One serialisation per channel, all in `core/`:
    the viewer's turn verbatim, tool results and each `toolUse.input` through
    `_inspection_text`, text blocks joined. The handler hands text over and
    reads a verdict back. Amendment 1 found this constraint had no test named
    anywhere in the plan; this is it, asserted on the source because the handler
    imports boto3 and no hermetic test can run it.

    Three shapes a serialisation in the handler would take, each refused: a
    reference to `_inspection_text`; a read of a converse response's `output`,
    `message` or `content` keys; a `.join` over anything but a refusal's
    `reasons`; a `json.dumps` outside the two transports (`_write` to the lake,
    `_call_tool`'s JSON-RPC request)."""
    for node in ast.walk(tree):
        name = node.id if isinstance(node, ast.Name) else getattr(node, "attr", None)
        assert name != "_inspection_text", (
            "handler.py references _inspection_text. The serialisation lives in "
            "core/toolloop.py and the handler serialises nothing (ADR-070 constraint 3).")

    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        exempt = {"content", "message"} if fn.name == "_call_tool" else set()
        for node in ast.walk(fn):
            key = _reads_key(node)
            assert key not in (RESPONSE_KEYS - exempt), (
                f"{fn.name} reads {key!r} — it is opening a converse response. The loop "
                "labels and serialises each round's output; the handler must not.")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "join"):
                assert len(node.args) == 1 and isinstance(node.args[0], ast.Attribute) \
                    and node.args[0].attr == "reasons", (
                        f"{fn.name} joins `{ast.unparse(node.args[0]) if node.args else ''}`. "
                        "The only join the handler may make is of a refusal's reasons; "
                        "joining content blocks is a serialisation.")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "dumps"):
                assert fn.name in {"_write", "_call_tool"}, (
                    f"{fn.name} calls json.dumps. Only the two transports may.")


def _blocked_branch(tree) -> ast.If:
    handler = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "handler")
    for node in ast.walk(handler):
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and "BLOCKED" in ast.unparse(node.test)):
            return node
    raise AssertionError("no `if outcome.status == toolloop.BLOCKED` branch in handler()")


def test_the_blocked_branch_is_composed_from_the_dataclass_and_record_id(tree):
    """**ADR-070 falsifier 4, the handler's half.** The loop returns no response
    on a block and puts the refused text on `outcome.refused`; the handler's
    blocked branch must not be the place it leaks. Its return dict is pinned:
    four literal keys, the spread of `as_response_fields()` (whose key set the
    loop tests pin), and the spread of `common_out` — nothing else, and no key
    that could carry text. `refused` is read in that branch in exactly two
    places: as the argument of `fingerprint_text`, which is how `withheld` is
    built, and as the second argument of `_hold`, which is how the store is
    written (ADR-071). **The second reader was added by widening this pin, and
    the pin went red first**: PR 3 planted the store write and this assertion
    named it as text going somewhere, which is the sentence it exists to say.
    The widening admits one call, by name and by argument position, and
    `test_the_blocked_branch_holds_the_refused_text_after_the_record_is_written`
    pins what that call is."""
    branch = _blocked_branch(tree)
    returns = [n for n in ast.walk(branch) if isinstance(n, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.Dict)
    literal, spread = set(), []
    for key, value in zip(returns[0].value.keys, returns[0].value.values, strict=True):
        if key is None:
            spread.append(ast.unparse(value))
        else:
            assert isinstance(key, ast.Constant)
            literal.add(key.value)
            if key.value == "record_id":
                assert isinstance(value, ast.Name) and value.id == "record_id", (
                    f"the blocked branch returns record_id={ast.unparse(value)}; it must be "
                    "the id `_write` returned, bound once, so the store is keyed by the id "
                    "the lake accepted")
    assert literal == {"decision", "mechanism", "record_id", "usage"}, (
        f"the blocked branch returns {sorted(literal)}; a key beyond these four is a "
        "place model text could travel")
    assert spread == ["outcome.guardrail.as_response_fields()", "common_out"], (
        f"the blocked branch spreads {spread}; it must spread exactly the dataclass's "
        "response fields and the common tail")

    fingerprinted = {id(call.args[0]) for call in calls_named(branch, "fingerprint_text")
                     if call.args}
    held = {id(call.args[1]) for call in calls_named(branch, "_hold") if len(call.args) == 2}
    for node in ast.walk(branch):
        if isinstance(node, ast.Attribute) and node.attr == "refused":
            assert id(node) in fingerprinted | held, (
                "the blocked branch reads `outcome.refused` somewhere other than as the "
                "argument of guardrail.fingerprint_text or the second argument of _hold — "
                "that is the refused text going somewhere the record or the response could "
                "carry it")


def test_the_blocked_branch_holds_the_refused_text_after_the_record_is_written(tree):
    """**ADR-071: the record first, then the text it describes, then the caller.**
    The branch is exactly four statements — build the record, write it and bind
    the id, hold the text, return — so the store is keyed by an id the lake has
    accepted and a store object can never exist for a record that does not.
    `_hold` is called from this branch and nowhere else in the module: the
    allowed and loop-bound paths hold nothing, because nothing was refused."""
    branch = _blocked_branch(tree)
    shape = [type(stmt).__name__ for stmt in branch.body]
    assert shape == ["Assign", "Assign", "Expr", "Return"], (
        f"the blocked branch is {shape}; it must be `record = ...`, `record_id = _write(record)`, "
        "`_hold(record, outcome.refused)`, `return {...}` in that order")
    build, write, hold, _ = branch.body
    assert ast.unparse(build.targets[0]) == "record"
    assert ast.unparse(write) == "record_id = _write(record)", (
        f"the second statement is `{ast.unparse(write)}`; the id must be bound from _write")
    assert ast.unparse(hold) == "_hold(record, outcome.refused)", (
        f"the third statement is `{ast.unparse(hold)}`; the store is written from the "
        "record the lake accepted and the text the loop refused, nothing else")
    holds = calls_named(tree, "_hold")
    assert len(holds) == 1 and holds[0] is hold.value, (
        f"_hold is called {len(holds)} time(s); once, from the blocked branch, or a path "
        "that refused nothing writes to the store")


def test_hold_puts_the_text_in_the_store_and_cannot_fail_the_block(tree):
    """**ADR-071: best-effort, and to the store only.** `_hold`'s body is one
    guarded put of `withheld.held_object(WITHHELD_STORE, record, text)`; the
    `except` prints and returns nothing, so a store outage cannot turn a correct
    refusal into an INFRA for the harness and move the adversarial score. The
    store's name is read without a default, once, and `_hold` is the only
    function that names it; `_write` names the lake and never the store, so the
    two buckets cannot be swapped inside either transport."""
    hold = _function(tree, "_hold")
    body = [s for s in hold.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert len(body) == 1 and isinstance(body[0], ast.Try), "_hold's body must be one try"
    assert [type(s).__name__ for s in body[0].body] == ["Expr"]
    put = body[0].body[0].value
    assert isinstance(put, ast.Call) and ast.unparse(put.func) == "_s3.put_object"
    assert not put.args and len(put.keywords) == 1 and put.keywords[0].arg is None, (
        f"the put is `{ast.unparse(put)}`; it must be `_s3.put_object(**withheld.held_object(...))` "
        "so the object is built by the pure module and nothing here composes it")
    built = put.keywords[0].value
    assert (isinstance(built, ast.Call) and ast.unparse(built.func) == "withheld.held_object"
            and [ast.unparse(a) for a in built.args] == ["WITHHELD_STORE", "record", "text"]), (
        f"the object is built as `{ast.unparse(built)}`")
    assert len(body[0].handlers) == 1 and not body[0].orelse and not body[0].finalbody
    handler_ = body[0].handlers[0]
    assert not any(isinstance(n, (ast.Raise, ast.Return)) for n in ast.walk(handler_)), (
        "_hold's except raises or returns; a failed put must be printed and swallowed, "
        "because the store is a diagnostic and must not acquire the power to fail a block")
    assert not any(isinstance(n, ast.Return) for n in ast.walk(hold)), "_hold returns a value"

    def names_in(fn):
        return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    assert "WITHHELD_STORE" in names_in(hold) and "AUDIT_LAKE" not in names_in(hold)
    write = _function(tree, "_write")
    assert "AUDIT_LAKE" in names_in(write) and "WITHHELD_STORE" not in names_in(write)
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != "_hold"]:
        assert "WITHHELD_STORE" not in names_in(fn), f"{fn.name} names the store"
    binds = [n for n in tree.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "WITHHELD_STORE" for t in n.targets)]
    assert len(binds) == 1 and ast.unparse(binds[0].value) == "os.environ[withheld.STORE_ENV]", (
        "WITHHELD_STORE must be read once, from the environment, with no default")


def test_the_loop_bound_branch_returns_no_answer(tree):
    """**AI Quality seat, PR 2 plant 5 (survived):** `"answer": outcome.answer`
    added to the `LOOP_BOUND` return passed 316 tests. The loop now returns no
    response on the bound, so `answer` is empty; this pins the branch as well,
    because a handler that reached for the text would be one line."""
    handler = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "handler")
    branch = next(n for n in ast.walk(handler)
                  if isinstance(n, ast.If) and "LOOP_BOUND" in ast.unparse(n.test))
    returns = [n for n in ast.walk(branch) if isinstance(n, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.Dict)
    literal = {k.value for k in returns[0].value.keys if isinstance(k, ast.Constant)}
    assert literal == {"decision", "mechanism", "record_id", "reasons", "usage"}, (
        f"the loop-bound branch returns {sorted(literal)}; the refused round was assessed "
        "as a tool request and its text is not the viewer's to see")
    spread = [ast.unparse(v) for k, v in zip(returns[0].value.keys, returns[0].value.values,
                                             strict=True) if k is None]
    assert spread == ["common_out"]


#: Every function `handler.py` defines at module level. **Platform-eng round 2,
#: P3:** a second entrypoint that reached `run_turn`, wrote records naming the
#: module constants and returned the refused text passed every pin, because every
#: pin resolves `def handler`. A closed list: adding a function is a diff somebody
#: has to defend, and `run_turn` is called from exactly one of them.
#:
#: `_hold` joined at ADR-071, and this pin went red on it first — which is the
#: diff-somebody-has-to-defend the sentence above asks for. Its shape is pinned
#: by `test_hold_puts_the_text_in_the_store_and_cannot_fail_the_block`.
MODULE_FUNCTIONS = frozenset({
    "_now", "_write", "_hold", "tool_config", "_call_tool", "_converse", "_inspect",
    "_tool_records", "handler", "_tool_probe",
})


def test_the_module_defines_exactly_these_functions_and_only_handler_runs_a_turn(tree):
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert defined == MODULE_FUNCTIONS, (
        f"handler.py defines {sorted(defined ^ MODULE_FUNCTIONS)} beyond or short of the "
        "pinned set. A second entrypoint is a second path to the model and to the refused "
        "text, and every pin in this file resolves `handler`")
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name != "handler":
            assert not calls_named(fn, "run_turn"), f"{fn.name} runs a turn; only handler may"
    assert len(calls_named(tree, "run_turn")) == 1


#: Every name `handler.py` binds at module level, literally. **Platform-eng round
#: 3:** `handler = _Staged(handler)` and `_inspect = lambda ...` appended at module
#: level defeated every pin, because every pin resolves a `def` and nothing pinned
#: what the NAME was bound to afterwards. Bindings are the closed set here; a
#: module-level statement is one of six kinds; no class is defined; and no
#: pinned function name is ever a Store target anywhere in the file.
#: `WITHHELD_STORE` joined at ADR-071 (red here first, like `_hold`).
MODULE_NAMES = frozenset({
    "MODEL_ID", "AUDIT_LAKE", "WITHHELD_STORE", "GUARDRAIL_ID", "GUARDRAIL_VERSION",
    "_TOOL_OUTPUT_GUARDRAIL_ID", "_TOOL_OUTPUT_GUARDRAIL_VERSION", "SERVICE_PRINCIPAL",
    "TOOL_FUNCTIONS", "POLICY_DIR", "POLICIES", "CONTRACTS", "_unknown", "PLANE",
    "_bedrock", "_lambda", "_s3",
})
MODULE_STATEMENTS = frozenset({"Expr", "Import", "ImportFrom", "Assign", "If", "FunctionDef"})


def test_the_module_binds_exactly_these_names_and_never_rebinds_a_function(tree):
    kinds = {type(stmt).__name__ for stmt in tree.body}
    assert kinds <= MODULE_STATEMENTS, (
        f"handler.py has module-level {sorted(kinds - MODULE_STATEMENTS)} statements; a "
        "class or anything else at module level is a place a function can be wrapped")
    bound = {n.id for stmt in tree.body if not isinstance(stmt, ast.FunctionDef)
             for n in ast.walk(stmt) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    assert bound == MODULE_NAMES, (
        f"module-level bindings differ from the pin by {sorted(bound ^ MODULE_NAMES)}")
    rebound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
               and isinstance(n.ctx, ast.Store) and n.id in MODULE_FUNCTIONS}
    assert not rebound, f"{sorted(rebound)} rebound as a name; a wrapper by assignment"
    for stmt in tree.body:
        if isinstance(stmt, ast.Expr):
            assert isinstance(stmt.value, ast.Constant), (
                f"a module-level expression statement: {ast.unparse(stmt)}")


def test_the_outcome_is_bound_once_from_run_turn(tree):
    """**Platform-eng round 3, P3.** `outcome = TurnOutcome(..., GuardrailOutcome(...,
    GUARDRAIL_ID, GUARDRAIL_VERSION), ...)` before `applied = outcome.guardrail`
    reinstated the fallback the `applied` pin closed, one name upstream."""
    handler = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "handler")
    stores = [n for n in ast.walk(handler)
              if isinstance(n, ast.Name) and n.id == "outcome" and isinstance(n.ctx, ast.Store)]
    assert len(stores) == 1, f"`outcome` is bound {len(stores)} times in handler()"
    assigns = [n for n in ast.walk(handler) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "outcome" for t in n.targets)]
    assert len(assigns) == 1 and isinstance(assigns[0].value, ast.Call) \
        and ast.unparse(assigns[0].value.func) == "toolloop.run_turn", (
            "`outcome` must be bound exactly once, to the value of toolloop.run_turn(...)")


def test_the_model_call_is_assembled_from_a_literal_and_no_environment(tree):
    """**Platform-eng round 3, P4.** `kwargs.update(json.loads(os.environ[...]))`
    in `_converse` carried a guardrailConfig no literal scan could see. `kwargs` is
    bound once, from a `dict(...)` call with keyword arguments only; the only other
    stores into it are the two subscripts; no function reads the environment."""
    converse = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "_converse")
    assigns = [n for n in ast.walk(converse) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "kwargs" for t in n.targets)]
    assert len(assigns) == 1, f"`kwargs` is bound {len(assigns)} times in _converse"
    value = assigns[0].value
    assert isinstance(value, ast.Call) and ast.unparse(value.func) == "dict" \
        and not value.args and all(kw.arg is not None for kw in value.keywords), (
            f"kwargs = {ast.unparse(value)}; it must be a dict(...) of keyword arguments, "
            "with no positional and no ** merge")
    stores = [n for n in ast.walk(converse)
              if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store)
              and isinstance(n.value, ast.Name) and n.value.id == "kwargs"]
    assert all(isinstance(n.slice, ast.Constant) for n in stores), (
        "a kwargs store uses a computed key; every key into the model call is a literal")
    assert sorted(n.slice.value for n in stores) == ["system", "toolConfig"], (
        f"kwargs stores: {sorted(ast.unparse(n.slice) for n in stores)}")
    for node in ast.walk(converse):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert not (node.func.attr == "update" and ast.unparse(node.func.value) == "kwargs"), (
                "kwargs.update(...) merges something the literal scan cannot see")
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            assert not (isinstance(node, ast.Attribute) and node.attr == "environ"), (
                f"{fn.name} reads os.environ; configuration is read once, at module level")


def _binds(fn, name):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]


def test_the_first_model_request_is_the_system_block_the_viewer_turn_verbatim_and_the_tool_config(tree):
    """**The round-1 pin, structural half (M08b PR 2; ADR-074 decision 3 §4).**
    The residual attribution reads the first round's `inputTokens` as the
    system block plus the viewer turn plus `toolConfig` and nothing else, and
    ADR-014 amendment 2's downward re-derivation trigger arms only if that is
    false. The loop's half is behavioural (`test_tool_loop.py`: the first
    transcript `converse` receives is the caller's `messages`, deep-equal).
    This is the handler's half, and it is structural because `handler.py`
    holds the boto3 clients and no hermetic test may import it (G8) — so it is
    read as a tree, the way every other pin in this file is, never as text.

    Three things, each a route a seat could plant: the viewer's text reaches
    `messages` from the event verbatim, bound once and wrapped once; the model
    call is `modelId`, `messages=transcript`, `inferenceConfig`, plus the two
    conditional keys the test above already pins to `system` and `toolConfig`,
    and no other; and the inner closure receives the transcript by that name
    and neither stores into it nor calls anything on it."""
    handler = _function(tree, "handler")
    text = _binds(handler, "text")
    assert len(text) == 1 and ast.unparse(text[0].value) == "event.get('text', '')", (
        "`text` is not bound once from the event; the viewer turn is no longer verbatim")
    system = _binds(handler, "system")
    assert len(system) == 1 and ast.unparse(system[0].value) == "event.get('system', '')"
    messages = _binds(handler, "messages")
    assert len(messages) == 1 and ast.unparse(messages[0].value) == \
        "[{'role': 'user', 'content': [{'text': text}]}]", (
            f"messages = {ast.unparse(messages[0].value) if messages else '<unbound>'}; "
            "the first request must wrap the event's text once and add nothing")
    run = calls_named(handler, "run_turn")[0]
    handed = {kw.arg: ast.unparse(kw.value) for kw in run.keywords}
    assert handed["messages"] == "messages"
    assert handed["converse"] == "_converse(system, tool_config(offered))"

    converse = _function(tree, "_converse")
    kwargs = _binds(converse, "kwargs")
    assert len(kwargs) == 1
    literal = {kw.arg: ast.unparse(kw.value) for kw in kwargs[0].value.keywords}
    assert set(literal) == {"modelId", "messages", "inferenceConfig"}, (
        f"the model call's literal carries {sorted(literal)}; the round-1 request is "
        "modelId, the transcript, inferenceConfig, and the pinned system/toolConfig")
    assert literal["messages"] == "transcript"
    inner = next(n for n in ast.walk(converse)
                 if isinstance(n, ast.FunctionDef) and n.name == "converse")
    assert [a.arg for a in inner.args.args] == ["transcript"]
    for node in ast.walk(inner):
        if isinstance(node, ast.Name) and node.id == "transcript":
            assert isinstance(node.ctx, ast.Load), "`transcript` is stored into inside converse"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert ast.unparse(node.func.value) != "transcript", (
                f"converse calls transcript.{node.func.attr}(...); the loop's transcript "
                "must reach the client untouched")


def _function(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def test_write_persists_the_record_it_was_handed_and_nothing_else(tree):
    """**Security round 3, SR3-A.** `_write` rewriting `record["guardrail"]` to the
    module constants sat downstream of every pin. Its body is the put and the
    return of the key; it stores nothing into the record."""
    body = [s for s in _function(tree, "_write").body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert [type(s).__name__ for s in body] == ["Expr", "Return"], (
        f"_write's body is {[type(s).__name__ for s in body]}; it must be the put and the return")
    assert ast.unparse(body[0].value.func) == "_s3.put_object"
    assert ast.unparse(body[1].value) == "record['record_id']"
    for node in ast.walk(_function(tree, "_write")):
        assert not (isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store)), (
            "_write stores into the record it was handed")


def test_a_failed_turn_is_iam_or_infra_and_never_a_block(tree):
    """**Security round 3, SR3-B.** The `except TurnFailed` path matched no pin,
    so a throttle could be written as `decision="blocked", mechanism="guardrail"`
    with a real record id and score every probe PASS on infrastructure noise.
    The path writes exactly one record — the IAM denial — and otherwise raises."""
    handler = _function(tree, "handler")
    handlers = [h for n in ast.walk(handler) if isinstance(n, ast.Try) for h in n.handlers
                if ast.unparse(h.type) == "toolloop.TurnFailed"]
    assert len(handlers) == 1, "expected exactly one `except toolloop.TurnFailed`"
    body = handlers[0].body
    assert isinstance(body[-1], ast.Raise), "the TurnFailed path must end in a raise"
    builds = calls_named(handlers[0], "build_record")
    assert len(builds) == 1
    assert ast.unparse(keyword(builds[0], "decision")) == "'denied'"
    assert ast.unparse(keyword(builds[0], "mechanism")) == "'iam'"
    returns = [n for n in ast.walk(handlers[0]) if isinstance(n, ast.Return)]
    assert len(returns) == 1, "the TurnFailed path returns only the IAM denial"
    ifs = [n for n in ast.walk(handlers[0]) if isinstance(n, ast.If)]
    assert len(ifs) == 1 and "AccessDeniedException" in ast.unparse(ifs[0].test)
    assert returns[0] in ast.walk(ifs[0]), "the return is not inside the AccessDenied branch"


@pytest.mark.parametrize("fn", ["_tool_records", "_tool_probe"])
def test_a_tool_record_names_the_planes_mechanism_bare(tree, fn):
    """**Security round 3, SR3-C.** `mechanism="policy"` for every refused tool
    call satisfied every probe naming Cedar with a routing or schema failure, and
    only the loop's own test asserted the rule. Both record writers hand
    `build_record` the plane's decision, bare, and `'none'` only when allowed."""
    builds = calls_named(_function(tree, fn), "build_record")
    assert len(builds) == 1
    assert ast.unparse(keyword(builds[0], "mechanism")) == \
        "'none' if decision.allowed else decision.mechanism", (
            f"{fn} writes mechanism={ast.unparse(keyword(builds[0], 'mechanism'))}")
    assert ast.unparse(keyword(builds[0], "decision")) == \
        "'allowed' if decision.allowed else 'denied'"


def test_the_bedrock_client_and_the_guardrail_module_are_the_real_ones(tree):
    """The arm pins name `_bedrock.apply_guardrail` and `guardrail.interpret_apply`
    by dotted name; this is what those two names are bound to. `_bedrock` is the
    boto3 runtime client, assigned once at module level; `guardrail` arrives from
    `core` and is never rebound."""
    binds = [n for n in tree.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "_bedrock" for t in n.targets)]
    assert len(binds) == 1 and ast.unparse(binds[0].value) == 'boto3.client(\'bedrock-runtime\')', (
        f"_bedrock is bound to {[ast.unparse(b.value) for b in binds]}")
    imported = any(isinstance(n, ast.ImportFrom) and n.module == "core"
                   and any(a.name == "guardrail" and a.asname is None for a in n.names)
                   for n in tree.body)
    assert imported, "`guardrail` is not imported from core"
    # `withheld` too (ADR-071): the store object is built by the pure module by
    # dotted name, and a shim under that name could hold one text while
    # recording another.
    imported_store = any(isinstance(n, ast.ImportFrom) and n.module == "core"
                         and any(a.name == "withheld" and a.asname is None for a in n.names)
                         for n in tree.body)
    assert imported_store, "`withheld` is not imported from core"
    rebound = [n for n in ast.walk(tree) if isinstance(n, ast.Name)
               and n.id in {"guardrail", "_bedrock", "withheld"}
               and isinstance(n.ctx, ast.Store) and n is not binds[0].targets[0]]
    assert not rebound, "`guardrail`, `_bedrock` or `withheld` is rebound somewhere in handler.py"


def test_the_withheld_fragment_describes_the_refused_text(tree):
    """`withheld` is a digest of the text the loop refused — the model's own words
    now, not Bedrock's placeholder (ADR-070 amendment 2). Built from
    `outcome.refused` through the total, content-free `fingerprint_text`."""
    branch = _blocked_branch(tree)
    builds = calls_named(branch, "build_record")
    assert len(builds) == 1
    withheld = keyword(builds[0], "withheld")
    assert withheld is not None and ast.unparse(withheld) == \
        "guardrail.fingerprint_text(outcome.refused)", (
            f"withheld is built as `{ast.unparse(withheld) if withheld else None}`; it "
            "must be guardrail.fingerprint_text(outcome.refused)")


def test_the_record_names_the_guardrail_the_outcome_carries(tree):
    """**ADR-070 amendment 2.** The fragment is built from the pair the outcome
    carries — stamped by `_inspect` at the call site — and never from the module
    constants the handler could reach for. One fragment for the turn, and its two
    arguments are `<outcome>.guardrail_id` and `<outcome>.version` on the same
    name; a `GUARDRAIL_ID` here would make every tool-output and (at stage 2)
    tool-request block name the wrong guardrail while validating perfectly."""
    handler = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "handler")
    builds = calls_named(handler, "as_record_fragment")
    assert len(builds) == 1, f"expected one turn fragment in handler(), found {len(builds)}"
    args = builds[0].args
    assert len(args) == 2 and all(isinstance(a, ast.Attribute) for a in args), (
        f"as_record_fragment({', '.join(ast.unparse(a) for a in args)}) — both arguments "
        "must be attribute reads off the outcome, never module constants")
    assert (args[0].attr, args[1].attr) == ("guardrail_id", "version")
    assert ast.unparse(args[0].value) == ast.unparse(args[1].value), (
        "the id and the version come from different objects")
    for node in ast.walk(builds[0]):
        assert not (isinstance(node, ast.Name) and node.id in PINNED_IDENTIFIERS | PINNED_VERSIONS), (
            f"the turn fragment names {node.id}; the record must name the guardrail that "
            "assessed the content, which only the outcome knows")

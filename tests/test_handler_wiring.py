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


def test_the_converse_path_and_the_inspection_path_pin_the_same_thing(tree):
    """"Equivalently" is meant literally. If the two paths could name different
    versions, a probe result would be attributable to neither.

    **ADR-063 narrows what "the same thing" means, and does not drop it.** The
    tool-output channel now has its own pinned pair, so `apply_guardrail` may name
    either — but `converse` may name ONLY the main one. A tool-output version
    reaching the model call would mean the turn transited a guardrail with no
    topic policy, which is the wiring mistake with the worst blast radius
    available here, and it is the one this test now exists to catch."""
    inspection: set = set()
    for call in calls_named(tree, "apply_guardrail"):
        inspection.add(getattr(keyword(call, "guardrailVersion"), "id", None))

    # **This half found NOTHING before ADR-063, and the test passed anyway.**
    # It looked for `guardrailConfig` as a direct keyword of a `converse(...)`
    # call. `handler.py` builds `kwargs = dict(..., guardrailConfig={...})` and
    # calls `_bedrock.converse(**kwargs)`, so the keyword was never there, the
    # set stayed empty, and the assertion was satisfied entirely by the
    # inspection path. A test named for comparing two paths compared one.
    #
    # Found while ADR-063 split the inspection path in two, which is the only
    # reason the empty half became visible. It is fixed here rather than left,
    # because the fix is four lines and the alternative is a test whose name is
    # a claim it does not keep.
    #
    # Located by SHAPE now — any dict literal carrying `guardrailIdentifier` and
    # `guardrailVersion` together — so the same collection survives the config
    # moving into a variable, a helper, or a call's keyword.
    converse_versions: set = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
        if not {"guardrailIdentifier", "guardrailVersion"} <= keys:
            continue
        for key, value in zip(node.keys, node.values, strict=True):
            if isinstance(key, ast.Constant) and key.value == "guardrailVersion":
                converse_versions.add(getattr(value, "id", None))

    assert converse_versions == {"GUARDRAIL_VERSION"}, (
        f"the model call pins {converse_versions}, not the main guardrail's version. "
        "ADR-063 gives the TOOL-OUTPUT channel its own policy; the turn itself still "
        "transits the guardrail with the topic policy on it.")
    assert inspection and inspection <= PINNED_VERSIONS, (
        f"the inspection path pins {sorted(inspection)}; permitted: "
        f"{sorted(PINNED_VERSIONS)}. Never a literal, never DRAFT.")


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


def test_the_tool_output_policy_is_selected_by_equality_not_by_its_negation(tree):
    """`==` flipped to `!=` at the channel comparison left the suite green.

    Every inspected channel except tool output would then run against the
    topic-free guardrail — the same blast radius as the binding swap, reached
    from the runtime side instead of the infra side. Located by what it compares,
    so moving or renaming the `if` does not evade it."""
    comparisons = [node for node in ast.walk(tree)
                   if isinstance(node, ast.Compare)
                   and isinstance(node.left, ast.Name) and node.left.id == "channel"
                   and any(isinstance(c, ast.Attribute) and c.attr == "CHANNEL_TOOL_OUTPUT"
                           for c in node.comparators)]
    assert comparisons, (
        "no comparison of `channel` against `guardrail.CHANNEL_TOOL_OUTPUT` remains. "
        "ADR-063 routes by an explicit channel comparison rather than a mapping, "
        "deliberately: a dict would send a channel added later to whichever policy the "
        "default named, and the direction of that mistake is not knowable in advance.")
    for node in comparisons:
        assert all(isinstance(op, ast.Eq) for op in node.ops), (
            "the tool-output channel is selected by something other than `==`. Negating "
            "it routes every OTHER inspected channel to the guardrail with no topic "
            "policy, which is the control silently getting weaker.")

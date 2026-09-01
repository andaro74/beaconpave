"""
Two arms, one difference each — the attribution the golden numbers rest on.

M01's claim was that the m00b run and the M01 run differed by the gateway and
nothing else. M02 adds a second comparison — the control arm and the tool arm,
re-measured the same day — whose claim is that they differ by the tool plane and
nothing else. Both claims are the same shape, and this file is where each one is
either checked or admitted to be unchecked.

**M02 breaks the `SYSTEM` pin on purpose, and the split came out differently from
the plan.** SPEC/02 anticipated that the `SYSTEM` byte-identity assertion would
end, because it assumed the governed caller's prompt would be replaced. It is
not: `run_via_gateway.py` freezes as the control arm, so `SYSTEM` is now the
*control's* prompt in both files and the byte-identity pin matters more than it
did, not less. What is new is `TOOL_SYSTEM`, and it gets the assertion the spec
asked for — that the catalog is **gone**, asserted rather than merely permitted,
with the new prompt hash-pinned. The spec is amended in place to say so.

Both files are read **as source text and parsed with `ast`**, never imported.
They import boto3, and the hermetic suite must not pull an AWS SDK into
`sys.modules` (G8). Same technique as `tests/test_hermeticity.py`, for the same
reason: what a module *can* reach is a stronger statement than what it did.

Hermetic. Owning seat: AI Quality (comparability) · Platform Engineering.
"""
import ast
import copy
import hashlib
import json
import pathlib
import sys
from collections import Counter

import pytest

from pave import infra

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = ROOT / "services" / "highlights-agent-baseline" / "run_baseline.py"
GOVERNED = ROOT / "services" / "highlights-agent" / "gateway_client.py"
CONTROL_ARM = ROOT / "services" / "highlights-agent" / "run_via_gateway.py"
TOOL_ARM = ROOT / "services" / "highlights-agent" / "run_with_tools.py"
CATALOG = ROOT / "data" / "catalog.json"
GATEWAY_SNAPSHOT = (ROOT / "platform" / "infra" / "tests" / "fixtures"
                    / "BeaconpaveGateway.template.json")


def module_constants(path):
    """Every module-level `NAME = <literal>` assignment, without importing."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value.value
    return found


BASELINE_CONSTANTS = module_constants(BASELINE)
GOVERNED_CONSTANTS = module_constants(GOVERNED)


# --- what still must not move, in either arm ---------------------------------

@pytest.mark.parametrize("name", ["SYSTEM", "CLOCK"])
def test_the_control_arm_still_uses_the_controls_prompt_and_clock(name):
    """Byte-identical, not merely equivalent — and this pin did **not** end at M02.

    It changed job. Until M02 it guaranteed that the governed run and the m00b run
    differed by the gateway alone. Now `run_via_gateway.py` and this prompt are the
    *control arm* of M02's comparison, re-measured the same day against the same
    deployed gateway, so the pin is what keeps the re-measured control the same
    system m00b measured. A drift here would not blur the M01 delta; it would blur
    M02's.

    If you are here because you changed the prompt: the M02 arm has its own
    (`TOOL_SYSTEM`). Changing this one ends both comparisons at once."""
    assert name in BASELINE_CONSTANTS, f"{BASELINE.name} no longer defines {name}"
    assert name in GOVERNED_CONSTANTS, f"{GOVERNED.name} no longer defines {name}"
    assert GOVERNED_CONSTANTS[name] == BASELINE_CONSTANTS[name], (
        f"{name} differs between the control and the governed caller. Both the M01 golden "
        "score and M02's re-measured control arm depend on this prompt being the one m00b ran."
    )


def test_the_evaluation_clock_is_the_same_everywhere_it_appears():
    """The clock is instrument, not system. It must never move, in either arm,
    ever — a suite whose clock drifted would start failing on its own once the
    fixture events pass, and the failure would look like a regression."""
    clock = BASELINE_CONSTANTS["CLOCK"]
    # **Tool servers are in this loop, and that is new.** `entitlement-check` has to
    # answer `not-yet-started`, which needs an instant, and its input contract cannot
    # supply one -- the caller is the model, and a tool letting the model choose the
    # moment it is judged against hands back the decision its own output schema calls
    # the tool's. So the clock arrives as deployment configuration (ADR-023's shape),
    # and the module that holds it is one more place this value can drift. Discovered
    # from `tools/` rather than listed, so the next tool that needs a clock is covered
    # the day it is written rather than the day somebody remembers this loop.
    tool_servers = sorted((ROOT / "tools").glob("*/server.py"))
    assert tool_servers, "no tool servers found; this loop would cover nothing"
    for path in (GOVERNED, CONTROL_ARM, TOOL_ARM, *tool_servers):
        source = path.read_text(encoding="utf-8")
        assert "CLOCK" not in module_constants(path) or module_constants(path)["CLOCK"] == clock, (
            f"{path.name} defines its own CLOCK. There is one evaluation clock; a second "
            "definition is a second instrument."
        )
        if path is not GOVERNED and path not in tool_servers:
            assert "Evaluation clock" not in source, (
                f"{path.name} builds its own user turn instead of calling `gw.user_turn`. "
                "The clock reaches the model through that function in both arms, and a "
                "second copy of the sentence is a second thing to forget to update."
            )


def test_the_deployment_does_not_define_a_clock_of_its_own():
    """The half of the rule above that lives outside Python.

    `BEACONPAVE_CLOCK` is an override, and an override set in the stack is a
    default: the deployed tool would answer against an instant no arm file names
    and `module_constants` cannot see, so the loop above would go on agreeing with
    itself while the deployed instrument had moved. The stack sets it nowhere, and
    this is what keeps that true -- a drill needing another instant sets it at
    invocation, deliberately, and does not leave it behind."""
    template = GATEWAY_SNAPSHOT.read_text(encoding="utf-8")
    assert "BEACONPAVE_CLOCK" not in template, (
        "the synthesized stack sets BEACONPAVE_CLOCK. That is a second definition of the "
        "evaluation clock, in a file test_the_evaluation_clock_is_the_same_everywhere_it_"
        "appears cannot read. If a deployment must pin an instant, pin it against "
        "BASELINE_CONSTANTS['CLOCK'] here first."
    )


def test_the_model_id_is_the_same_pinned_profile():
    """ADR-015. A run against a different profile is a different measurement, and
    the regional pin is a recorded decision rather than an accident."""
    baseline_model = BASELINE_CONSTANTS["MODEL_ID"]
    stack = (ROOT / "platform" / "infra" / "lib" / "gateway-stack.ts").read_text(encoding="utf-8")
    assert f"'{baseline_model}'" in stack, (
        f"the gateway stack does not pin {baseline_model!r} — the M01 run would measure a "
        "different model from the one m00b measured"
    )


def test_transport_decoding_matches_the_control():
    """The fence-unwrapping is `parse` in the control and `parse_answer` here.
    Comparing the function bodies structurally catches a repair being added on one
    side — a retry, a schema coercion, a missing-field fill — which would repair
    the content the goldens measure rather than decode the transport.

    **This matters more at M02, not less.** A prompt change is the ideal
    camouflage for an answer repair: the diff is already large and already
    expected to move the score, so a coercion slipped in beside it would be
    attributed to the tool plane."""
    def body_of(path, name):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                # Docstrings differ by design; the logic must not.
                body = node.body[1:] if ast.get_docstring(node) else node.body
                return ast.dump(ast.Module(body=body, type_ignores=[]))
        raise AssertionError(f"{name} not found in {path.name}")

    assert body_of(GOVERNED, "parse_answer") == body_of(BASELINE, "parse"), (
        "the governed caller decodes the model's reply differently from the control. "
        "Unwrapping a code fence is decoding transport; anything more repairs the answer, "
        "which is the behaviour the golden set is measuring."
    )


# --- the pin that ends, and what replaces it ---------------------------------

#: sha256 of `TOOL_SYSTEM` as a template, before any `.format`.
#:
#: **Hash-pinned so the next drift is a deliberate diff rather than an accident.**
#: The M01 prompt was pinned by comparison to the control's, which is a stronger
#: check but is not available here — there is nothing to compare the M02 prompt
#: to. A hash is the weaker available check and it buys the thing that matters:
#: a word added to this prompt between two runs cannot pass unnoticed, and the
#: run whose score it moved cannot be attributed to the tool plane.
#:
#: If you are updating this constant, you are changing the system under
#: measurement. That is allowed and it is an ADR-021 event: say so in the
#: progression row, and do not do it between the two arms of one comparison.
TOOL_SYSTEM_SHA256 = "c5e0e50584613dbfa75b0dc991fda55e075709dfb07fd3c5f38db8e0a6818e38"


#: sha256 of the tool specs the gateway renders for the model.
#:
#: **The prompt is not the whole of what the model reads.** `handler.tool_config`
#: hands Bedrock each tool's `description` and its full input schema, so the
#: model-facing surface at M02 is `TOOL_SYSTEM` *plus* those documents — and the
#: description shipped a reviewer-facing rationale as tool documentation while the
#: schema carries catalog vocabulary the control arm had inside `CATALOG:`.
#:
#: Unpinned, a tool description could be reworded between the two arms of one
#: comparison: exactly what `TOOL_SYSTEM_SHA256` exists to prevent, one field over
#: and invisible to it. SPEC/02 forbids editing a committed schema in this
#: milestone, so the description's rewrite is drafted for the Tool Owner with a
#: semver bump rather than made here — but it cannot move unnoticed in the
#: meantime.
#:
#: **Moved at M06b when `entitlement-check` was routed**, from
#: `1912657b...dc15c4a`. Nothing about `catalog-search` changed: the digest is
#: taken over the ROUTED set, so deploying a second tool adds a second document to
#: what the model reads and the hash moves by construction. That is an ADR-021
#: event -- the system under measurement is larger than it was -- and no
#: comparison may span it. Both arms of every M06b comparison run on one side of
#: this line.
TOOL_SPECS_SHA256 = "0267054bf6b83b28e60d0b80fdbb4469588b8afc619e12d3d2bc2cb3f3388205"


def test_the_tool_specs_the_model_reads_are_hash_pinned():
    contracts = json.loads(
        (ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json").read_text(
            encoding="utf-8"))
    routed = infra.routed_tools(json.loads(GATEWAY_SNAPSHOT.read_text(encoding="utf-8")))
    specs = json.dumps([contracts[t]["input"] for t in sorted(routed) if t in contracts],
                       sort_keys=True)
    digest = hashlib.sha256(specs.encode("utf-8")).hexdigest()
    assert digest == TOOL_SPECS_SHA256, (
        f"the tool specs the model reads changed (sha256 {digest}). They are part of the "
        "system under measurement just as the prompt is. Update this pin deliberately, and "
        "never between the two arms of one comparison."
    )


def test_the_m02_prompt_is_hash_pinned():
    digest = hashlib.sha256(GOVERNED_CONSTANTS["TOOL_SYSTEM"].encode("utf-8")).hexdigest()
    assert digest == TOOL_SYSTEM_SHA256, (
        f"TOOL_SYSTEM changed (sha256 {digest}). The M02 arm's prompt is the system under "
        "measurement; a word added between two runs makes the delta unattributable. Update "
        "this pin deliberately, in a commit that says the prompt moved, and never between "
        "the two arms of one comparison."
    )


#: What the model actually receives at M02: the rendered system prompt plus the
#: tool specs the gateway builds from the committed input contracts.
#:
#: **Both halves, because only one of them was being checked.** The prompt is
#: `TOOL_SYSTEM.format(schema=...)`, and the first version of this file asserted
#: against the *template* — one level above where its own docstring said the
#: failure would happen. And `handler.tool_config` hands Bedrock the tool's
#: `description` and full input schema, which is model-facing text nobody pinned:
#: the description shipped a reviewer-facing rationale as tool documentation, and
#: the schema carries catalog vocabulary the control arm had inside `CATALOG:`.
def rendered_prompt() -> str:
    schema = (ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json")
    return GOVERNED_CONSTANTS["TOOL_SYSTEM"].format(schema=schema.read_text(encoding="utf-8"))


def rendered_tool_specs() -> list:
    contracts = json.loads(
        (ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json").read_text(
            encoding="utf-8"))
    routed = infra.routed_tools(json.loads(GATEWAY_SNAPSHOT.read_text(encoding="utf-8")))
    return [contracts[t]["input"] for t in routed if t in contracts]


def rendered_model_surface() -> str:
    return rendered_prompt() + "\n" + json.dumps(rendered_tool_specs())


def _strings(node, path=""):
    """Every string in a spec, with the path it sits at.

    A substring scan over the serialised blob cannot tell a declared enum value from
    a market named in a `description`, and after ADR-056 that difference is the rule."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def _enums(node, path=""):
    """`(path, frozenset(values))` for every string-valued `enum` in a spec."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "enum" and isinstance(value, list) and all(isinstance(v, str) for v in value):
                yield f"{path}.enum", frozenset(value)
            else:
                yield from _enums(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _enums(value, f"{path}[{index}]")


def _deployed_specs():
    """What `rendered_tool_specs` returns once M06b's step 2 routes the second tool.

    Built from the committed contracts rather than from a hand-written schema, so
    these tests move when the real contract moves. A fixture would let the tool's
    schema drift away from the rule that is supposed to govern it -- which is the
    shape ADR-047 found between a template and the service it copies."""
    contracts = json.loads(
        (ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json").read_text(
            encoding="utf-8"))
    return [copy.deepcopy(contracts["catalog-search"]["input"]),
            copy.deepcopy(contracts["entitlement-check"]["input"])]


def _catalog_check(monkeypatch, specs=None, prompt=None):
    if specs is not None:
        monkeypatch.setattr(sys.modules[__name__], "rendered_tool_specs", lambda: specs)
    if prompt is not None:
        monkeypatch.setattr(sys.modules[__name__], "rendered_prompt", lambda: prompt)
    test_the_catalog_is_gone_from_everything_the_model_receives()


def test_deploying_the_second_tool_is_permitted_by_the_amended_rule(monkeypatch):
    """**ADR-056's whole claim, asserted rather than described.**

    Before it, routing `entitlement-check` made the check above red on all six
    market names, because a tool cannot declare which markets it accepts without
    naming them. This is the test that would go red if the amendment were ever
    reverted while the tool stayed deployed -- so the decision cannot rot into a
    comment."""
    specs = _deployed_specs()
    assert specs[1]["properties"]["dma"]["enum"], "the tool declares no markets; this is vacuous"
    _catalog_check(monkeypatch, specs=specs)


def test_a_market_enum_narrowed_to_a_subset_is_the_blackout_table(monkeypatch):
    """The hole ADR-056 had to open and then close in the same diff.

    Publishing the full vocabulary is safe precisely because it distinguishes
    nothing. `["jefferson-city", "port-william"]` distinguishes exactly the markets
    that are dark for the derby -- the mapping SPEC/02 removed, re-expressed as a
    schema the gateway would hand straight to the model."""
    specs = _deployed_specs()
    specs[1]["properties"]["dma"]["enum"] = ["jefferson-city", "port-william"]
    with pytest.raises(AssertionError, match="PROPER SUBSET"):
        _catalog_check(monkeypatch, specs=specs)


def test_a_market_named_in_a_spec_description_is_not_declared_vocabulary(monkeypatch):
    """Stricter than what it replaced, on the half that was relaxed.

    The old rule was one substring scan and could not tell an enum value from prose.
    ADR-056 permits the vocabulary *as declared input values* and nowhere else, so a
    description is checked even though it sits inside a spec the rule now admits.
    `handler.tool_config` ships descriptions to Bedrock as tool documentation
    (ADR-043), so prose here reaches the model exactly as the prompt does."""
    specs = _deployed_specs()
    specs[1]["properties"]["dma"]["description"] = "e.g. jefferson-city is dark for the derby"
    with pytest.raises(AssertionError, match="not a declared market enum"):
        _catalog_check(monkeypatch, specs=specs)


def test_an_event_name_is_forbidden_even_as_a_declared_input(monkeypatch):
    """An event name is half the mapping, and no tool needs to declare one --
    measured: `jefferson-derby` appears in no committed contract. The relaxation is
    scoped to markets and does not generalise to 'anything a schema declares'."""
    specs = _deployed_specs()
    specs[1]["properties"]["event"] = {"type": "string", "enum": ["jefferson-derby"]}
    with pytest.raises(AssertionError, match="half the"):
        _catalog_check(monkeypatch, specs=specs)


def test_the_prompt_half_is_untouched_by_the_amendment(monkeypatch):
    """ADR-056 relaxed the tool specs and nothing else. One bare market name in the
    system prompt -- no mapping, no event -- is still refused, because that half is
    where "policy context" would be inlined and is what SPEC/02 refused."""
    with pytest.raises(AssertionError, match="back in the system prompt"):
        _catalog_check(monkeypatch, prompt=rendered_prompt() + "\nMarkets: cedar-point.")


def test_the_catalog_is_gone_from_everything_the_model_receives():
    """**Asserted, not merely permitted.** This is M02's central claim about the
    prompt, so it is checked against the fixture's own bytes rather than against
    the absence of the word "CATALOG": a template that dropped the placeholder but
    inlined the titles some other way would pass a keyword check.

    Checked against the **rendered** surface, including the tool specs. The first
    version read the pre-`.format()` template and ignored `toolConfig` entirely --
    so it checked one level above where the failure it describes would occur, and
    it did not look at the second thing the model reads at all.

    **ADR-056 narrowed what is forbidden and made the check structural.** It used to
    be one substring scan over prompt-plus-specs banning every DMA name outright,
    which would have refused `entitlement-check`'s declared input vocabulary -- a
    tool cannot state which markets it accepts without naming them. What `SPEC/02`
    argued about is the agent inferring entitlement from its own context, and that
    needs the *mapping*, which a bare vocabulary does not carry. So:

    - titles, title ids and **event names** stay banned everywhere;
    - DMA names stay banned outright in the **prompt**, which is the half `SPEC/02`
      was about and the half where "policy context" would be inlined;
    - inside tool specs a DMA name is permitted **only** as an enum value, and only
      where that enum is the *complete* market list.

    The last clause is new, and it closes a hole the old scan closed only by
    accident. **A `dma` enum narrowed to a subset would leak the mapping** --
    `["jefferson-city","port-william"]` is precisely the blackout, declared as a
    schema. Exactness is what makes the vocabulary safe to publish; a subset is the
    table."""
    prompt = rendered_prompt()
    specs = rendered_tool_specs()
    blob = prompt + "\n" + json.dumps(specs)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    assert catalog["titles"], "the catalog fixture has no titles -- this check would be vacuous"
    assert catalog["blackouts"], "the fixture has no blackout table -- this check would be vacuous"
    assert catalog["dmas"], "the fixture has no DMAs -- this check would be vacuous"

    # 1. The catalog itself, and the EVENT names, stay banned in both halves. These
    #    are the ground truth the agent used to read out of its own prompt, and no
    #    tool declares them: measured, `jefferson-derby` is absent from every
    #    contract, so this clause costs the tool plane nothing.
    for title in catalog["titles"]:
        assert title["id"] not in blob, f"{title['id']} is inlined in the M02 prompt"
        assert title["title"] not in blob, f"{title['title']!r} is inlined in the M02 prompt"
    for event in catalog["blackouts"]:
        assert event not in blob.lower(), (
            f"{event!r} is back in what the model receives. An event name is half the "
            "blackout mapping and no tool needs to declare one.")

    dmas = frozenset(catalog["dmas"])

    # 2. The prompt half keeps the original rule, undiluted. ADR-056 relaxed the TOOL
    #    SPECS and nothing else; inlining the table here as "policy context" is the
    #    thing SPEC/02 refused on the record.
    for token in sorted(dmas):
        assert token not in prompt.lower(), (
            f"{token!r} is back in the system prompt. SPEC/02 rejects re-inlining the "
            "blackout table as 'policy context' on the record: it lets the agent keep "
            "inferring entitlement from its own prompt while a tool call in the "
            "trajectory makes it look as though a tool answered -- which is what "
            "ADR-016 demoted `entitlement_source` for. ADR-056 permits a declared enum "
            "in a TOOL SPEC; it permits nothing here.")

    # 3. Any enum naming markets must name them ALL. A subset is the mapping.
    declared = set()
    for spec in specs:
        for path, values in _enums(spec):
            if not values & dmas:
                continue
            assert values == dmas, (
                f"{path} declares {sorted(values)}, a PROPER SUBSET of the market list. "
                "That is the blackout table wearing a schema: publishing the vocabulary "
                "is safe because it distinguishes nothing, and a subset distinguishes "
                "exactly the markets that matter. Declare every market or none.")
            declared.add(path)

    # 4. Everywhere else in a spec -- descriptions, titles, examples, defaults -- a
    #    market name is still forbidden. This is what the old substring scan could not
    #    express, and on this half it is STRICTER than "the blob contains no DMA": a
    #    description reading "blacked out in jefferson-city" is caught here while
    #    sitting inside a tool spec the rule now otherwise permits.
    for spec in specs:
        for path, value in _strings(spec):
            if any(path.startswith(f"{d}[") for d in declared):
                continue
            hit = next((d for d in sorted(dmas) if d in value.lower()), None)
            assert hit is None, (
                f"{hit!r} appears at {path}, which is not a declared market enum. "
                "ADR-056 permits the vocabulary as a tool's declared input values and "
                "nowhere else -- prose in a spec reaches the model exactly as the "
                "prompt does.")


def test_the_m02_prompt_is_the_control_prompt_minus_the_catalog_and_nothing_else():
    """The attribution claim, stated as a diff rather than as a promise.

    Two changes were forced by the catalog leaving: the block itself, and the
    sentence that pointed at it. Anything else — a nudge to search first, a hint
    about broader queries, a worked example — would raise the M02 score by tuning
    the prompt to a golden set whose result is already predicted. So the two
    prompts are compared line by line and the differing lines are named here."""
    control = GOVERNED_CONSTANTS["SYSTEM"].splitlines()
    tool = GOVERNED_CONSTANTS["TOOL_SYSTEM"].splitlines()

    # **A multiset difference, not a set difference.** The first version used
    # `line not in tool`, which is blind to repetition: appending a duplicate copy
    # of the JSON-instruction line to `TOOL_SYSTEM` left both lists exactly as the
    # assertions expect and the test stayed green. Repetition is real prompt
    # emphasis, and the hash pin would catch it — but the hash and the prompt move
    # in the same commit, and the test whose job is to NAME what changed would have
    # said nothing.
    counts_control, counts_tool = Counter(control), Counter(tool)
    only_control = sorted((counts_control - counts_tool).elements())
    only_tool = sorted((counts_tool - counts_control).elements())

    assert only_tool == [
        "You are the Meridian Sports highlights agent. Answer the viewer's question using "
        "only catalog titles returned by the catalog-search tool. Cite the ids of any titles "
        "you rely on.",
    ], f"the M02 prompt adds lines beyond the forced one: {only_tool}"

    # Sorted, and the blank line is real: removing the trailing `CATALOG:` block
    # removes the blank line that separated it from the schema. The set-difference
    # version could not see that, which is the same blindness that let a duplicated
    # line pass.
    assert only_control == sorted([
        "",
        "You are the Meridian Sports highlights agent. Answer the viewer's question using "
        "only the catalog below. Cite the ids of any titles you rely on.",
        "CATALOG:",
        "{catalog}",
    ]), f"the M02 prompt drops more than the catalog: {only_control}"


# --- the two arms differ where they are supposed to, and nowhere else --------

def calls_in(path):
    """Every `gw.<name>(...)` the runner makes."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "gw"
    }


def test_both_arms_share_the_decoder_the_clock_and_the_invoke_path():
    """What must not differ between the arms is shared by construction rather than
    by inspection. A second decoder in the tool arm would repair answers on one
    side of the comparison only, and the repair would read as the tool plane."""
    shared = {"user_turn", "invoke", "parse_answer", "resources"}
    for path in (CONTROL_ARM, TOOL_ARM):
        missing = shared - calls_in(path)
        assert not missing, f"{path.name} does not use {sorted(missing)} from gateway_client"


def test_the_arms_differ_in_exactly_the_prompt_they_build():
    """The one intended difference, checked as an exclusive-or so neither arm can
    quietly acquire the other's prompt."""
    assert "build_prompt" in calls_in(CONTROL_ARM)
    assert "build_tool_prompt" not in calls_in(CONTROL_ARM), (
        "the control arm builds the M02 prompt. It is frozen: it must reproduce what M01 ran."
    )
    assert "build_tool_prompt" in calls_in(TOOL_ARM)
    assert "build_prompt" not in calls_in(TOOL_ARM), (
        "the tool arm inlines the catalog. That is the one thing M02 removes."
    )


def test_only_the_tool_arm_asks_for_tools():
    """Tools are opt-in at the gateway, and the default is off precisely so the
    frozen control arm keeps behaving as it did without a line of it changing."""
    assert '"tools": True' in TOOL_ARM.read_text(encoding="utf-8")
    assert "tools" not in CONTROL_ARM.read_text(encoding="utf-8"), (
        "the control arm mentions tools. Defaulting them on, or asking for them here, would "
        "change the frozen arm's behaviour without changing a line of what it measures."
    )


def test_the_tool_arm_refuses_to_write_a_run_in_which_nothing_was_authorized():
    """The harness half of the finding Platform Engineering raised.

    A tools arm in which the plane authorized nothing is indistinguishable, in the
    committed evidence, from a model that chose never to search: both leave an
    empty trajectory file and a complete set of plausible answers, and the score
    lands inside the predicted band as a fifth loss mechanism nobody registered.
    The gateway now refuses to start without a routing table, and the harness
    refuses to write a run that measured nothing — belt and braces, because only
    one of the two is in front of the file that becomes history."""
    source = TOOL_ARM.read_text(encoding="utf-8")
    assert "no tool call was authorized in the whole run" in source
    assert source.index("no tool call was authorized") < source.index("out.write_text"), (
        "the pre-flight check runs after the answers are written, so a run that "
        "measured nothing still leaves a file somebody can record"
    )


def test_the_tool_arm_records_trajectories_and_scores_none_of_them():
    """Recorded, never scored (SPEC/02). A trajectory turned into a metric rewards
    the model for calling the tools we guessed it would rather than for answering
    correctly — and it would be the easiest number in this milestone to make go up."""
    source = TOOL_ARM.read_text(encoding="utf-8")
    assert "trajectory" in source
    assert "-trajectory.json" in source, "the tool arm does not commit its trajectories"
    for scoring in ("expect_tool_before_answer", "trajectory_score", "score(trajector"):
        assert scoring not in source, f"the tool arm scores its trajectories ({scoring})"


def test_the_control_arm_is_untouched_by_this_milestone():
    """The freeze, checked rather than promised.

    `run_via_gateway.py` produced the recorded m01 row and is M02's control arm.
    The realistic way it changes is not somebody deciding to change it — it is a
    tidy-up in a diff about something else. So the two things that would make its
    re-measurement incomparable are pinned: the prompt it builds and the request
    it sends."""
    source = CONTROL_ARM.read_text(encoding="utf-8")
    assert "gw.build_prompt()" in source
    assert '"classification": "internal"' in source
    assert '"service": "highlights-agent"' in source
    assert "TOOL_SYSTEM" not in source

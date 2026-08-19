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
import hashlib
import json
import pathlib
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
    for path in (GOVERNED, CONTROL_ARM, TOOL_ARM):
        source = path.read_text(encoding="utf-8")
        assert "CLOCK" not in module_constants(path) or module_constants(path)["CLOCK"] == clock, (
            f"{path.name} defines its own CLOCK. There is one evaluation clock; a second "
            "definition is a second instrument."
        )
        if path is not GOVERNED:
            assert "Evaluation clock" not in source, (
                f"{path.name} builds its own user turn instead of calling `gw.user_turn`. "
                "The clock reaches the model through that function in both arms, and a "
                "second copy of the sentence is a second thing to forget to update."
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
TOOL_SPECS_SHA256 = "1912657b11c164df77ed5f162729f6cd785d840f31233bafcc03aeb89dc15c4a"


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
def rendered_model_surface() -> str:
    schema = (ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json")
    prompt = GOVERNED_CONSTANTS["TOOL_SYSTEM"].format(schema=schema.read_text(encoding="utf-8"))
    contracts = json.loads(
        (ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json").read_text(
            encoding="utf-8"))
    routed = infra.routed_tools(json.loads(GATEWAY_SNAPSHOT.read_text(encoding="utf-8")))
    specs = json.dumps([contracts[t]["input"] for t in routed if t in contracts])
    return prompt + "\n" + specs


def test_the_catalog_is_gone_from_everything_the_model_receives():
    """**Asserted, not merely permitted.** This is M02's central claim about the
    prompt, so it is checked against the fixture's own bytes rather than against
    the absence of the word "CATALOG": a template that dropped the placeholder but
    inlined the titles some other way would pass a keyword check.

    Checked against the **rendered** surface, including the tool specs. The first
    version read the pre-`.format()` template and ignored `toolConfig` entirely —
    so it checked one level above where the failure it describes would occur, and
    it did not look at the second thing the model reads at all.

    Every title id, every title string, and the blackout table's own vocabulary
    must be absent."""
    prompt = rendered_model_surface()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    assert catalog["titles"], "the catalog fixture has no titles — this check would be vacuous"
    for title in catalog["titles"]:
        assert title["id"] not in prompt, f"{title['id']} is inlined in the M02 prompt"
        assert title["title"] not in prompt, f"{title['title']!r} is inlined in the M02 prompt"

    # The blackout table's own DATA, not the word "blackout". The answer schema
    # names `blackout` as a possible verdict and always has — it is in the control
    # arm's prompt too, so a bare keyword check would fail on something shared by
    # both arms and prove nothing about either. What must be absent is every DMA
    # name and every blackout entry, which is the ground truth the agent used to
    # read out of its own prompt.
    assert catalog["blackouts"], "the fixture has no blackout table — this check would be vacuous"
    assert catalog["dmas"], "the fixture has no DMAs — this check would be vacuous"
    forbidden = set(catalog["dmas"])
    for event, dmas in catalog["blackouts"].items():
        forbidden.add(event)
        forbidden.update(dmas)
    for token in sorted(forbidden):
        assert token not in prompt.lower(), (
            f"{token!r} is back in what the model receives. SPEC/02 rejects re-inlining the "
            "blackout table as 'policy context' on the record: it lets the agent keep inferring "
            "entitlement from its own prompt while a tool call in the trajectory makes it look "
            "as though a tool answered — which is what ADR-016 demoted `entitlement_source` for."
        )


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

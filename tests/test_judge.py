"""
The judge's hermetic half, and the rules that decide what it is allowed to move.

Every test here runs with no model, no network and no AWS account (G8). The
bands are fixtures: whether the judge *produces* sensible bands is measured by
the published agreement number, and what it is *permitted to do* with them is
measured here. Those are different questions and only the second one is a test.

Owning seat: AI Quality.
"""
import json
import pathlib
import tempfile

import pytest

from evals import judge

ROOT_TMP = pathlib.Path(tempfile.mkdtemp(prefix="beaconpave-judge-"))

GROUND = "groundedness"
TONE = "brand_tone:meridian-sports"


# --- majority over k_judge ----------------------------------------------------


@pytest.mark.parametrize("samples,expected", [
    ([1.0, 1.0, 1.0], 1.0),
    ([1.0, 1.0, 0.5], 1.0),
    ([0.0, 0.0, 1.0], 0.0),
    ([1.0, 0.5, 0.0], None),
    ([None, None, None], None),
    ([1.0, None, 1.0], 1.0),
    ([1.0, None, 0.5], None),
])
def test_majority_band(samples, expected):
    assert judge.majority_band(samples) == expected


def test_the_1_1_1_split_is_reachable_and_is_recorded_as_undecided():
    """M02 wrote the tie rule and predicted it was unreachable. It was right about
    the case level and this is where it was wrong: three bands over three samples
    is a genuine three-way split, and it is the first one this repo can produce.

    Undecided is not a band and not a veto. The judge was asked and did not answer
    the same way twice, which is evidence about the judge rather than about the
    answer."""
    assert judge.majority_band([0.0, 0.5, 1.0]) is None


def test_a_bare_plurality_is_not_a_majority():
    """Four samples, two agreeing, is the shape that would let an even k slip a
    plurality through as a decision. `summarise` already refuses an even k for the
    same reason; this is the band-level twin."""
    assert judge.majority_band([1.0, 1.0, 0.5, 0.0]) is None


# --- the veto -----------------------------------------------------------------


def test_only_zero_vetoes():
    """The rubric's 0.5 is "accurate but flat", "reaches beyond what is cited",
    "padded but readable". Those are quality signals. Vetoing on them would make
    the judge a second deterministic assert with worse repeatability."""
    assert judge.veto({GROUND: 0.5}, {GROUND})[0] is False
    assert judge.veto({GROUND: 1.0}, {GROUND})[0] is False
    assert judge.veto({GROUND: 0.0}, {GROUND}) == (True, [GROUND])


def test_an_undecided_axis_never_vetoes():
    """A veto is a decision and a 1-1-1 split is the absence of one. Vetoing on
    undecided would let an unrepeatable judge fail cases at random and call it
    strictness."""
    assert judge.veto({GROUND: None}, {GROUND})[0] is False


def test_a_demoted_axis_cannot_block_anything():
    """**The collision SPEC/03 named before it was written.**

    `ADVISORY` already means two things: "judge axes recorded, not scored" and
    "no strict majority", and the second blocks in `emit_verdict`. The obvious
    implementation of demotion — a demoted judge emits ADVISORY axes, the case
    result becomes ADVISORY, the verdict blocks — would make a demoted judge
    *stricter* than a calibrated one, which is the opposite of the mechanism and
    the opposite of what the rubric promises.

    So demotion is implemented as *the axis does not enter `result`*: a demoted
    axis is not in `calibrated`, and `veto` never looks at it. A `0.0` on a
    demoted axis is recorded and costs nothing."""
    assert judge.veto({TONE: 0.0}, set()) == (False, [])
    assert judge.veto({TONE: 0.0, GROUND: 1.0}, {GROUND}) == (False, [])


def test_the_judge_can_only_subtract():
    """There is no path from a judged band to a PASS. `veto` returns whether to
    remove a pass and nothing else, so a case the deterministic asserts failed
    cannot be rescued by a judge that liked the prose."""
    decided, hits = judge.veto({GROUND: 1.0}, {GROUND})
    assert decided is False and hits == []


# --- agreement ----------------------------------------------------------------


def test_kappa_is_undefined_when_a_rater_used_one_category():
    """What `brand_tone` looks like, and why it is demoted on evidence rather than
    on a number. Every drafted label on that axis is 0.5, so expected agreement is
    1.0 and the correction divides by zero.

    Returning None is the honest answer. Returning 0.0 would read as "no agreement
    beyond chance", and returning 1.0 would read as perfect — both are claims the
    data cannot support."""
    assert judge.cohens_kappa([0.5] * 5, [0.5] * 5) is None


def test_kappa_is_below_raw_when_labels_are_imbalanced():
    """The reason both are published. Nine of ten labels the same value, judge
    agreeing on nine: raw looks strong and kappa says most of it was available by
    guessing the common band."""
    labels = [1.0] * 9 + [0.0]
    bands = [1.0] * 9 + [1.0]
    kappa = judge.cohens_kappa(labels, bands)
    assert kappa is not None and kappa < 0.9


def test_an_undecided_band_counts_as_disagreement():
    """Scoring undecided as agreement would let a judge that cannot repeat itself
    look calibrated on the items where it happened to."""
    stats = judge.agreement([
        {"axis": GROUND, "label": 1.0, "band": 1.0},
        {"axis": GROUND, "label": 1.0, "band": None},
    ])
    assert stats == {"n": 2, "exact": 1, "raw": 0.5, "kappa": stats["kappa"],
                     "undecided": 1, "label_distribution": {"1.0": 2}}


def test_agreement_is_computed_only_over_items_with_an_answer_to_grade():
    """Not-applicable items never reach `agreement`.

    A refusal, an undecodable turn and a missing answer are decided by the harness
    before any model call, so the judge and the label agree on them *by
    construction*. Counting them would add automatic agreements — three of them in
    the held-out half — and inflate every published figure.

    This is asserted by construction rather than by a filter inside `agreement`:
    the caller builds the item list, and `test_the_calibration_split_excludes_
    unscorable_items` below is what checks it did."""
    assert judge.agreement([])["n"] == 0


# --- demotion -----------------------------------------------------------------


def test_insufficient_evidence_demotes_whatever_the_agreement_says():
    """Not enough evidence is not calibration. The floor is checked first and
    reported first, so nobody quotes an agreement figure that four items produced."""
    out = judge.demotion(TONE, {"n": 3, "exact": 3, "raw": 1.0, "kappa": None,
                                "undecided": 0, "label_distribution": {}})
    assert out["status"] == "demoted"
    assert "below the floor" in out["reasons"][0]


def test_an_unrepeatable_judge_is_demoted_even_at_perfect_agreement():
    """A judge that returns a different band on a third of the items it is asked
    twice about is not calibrated by the two thirds where it agreed with itself."""
    out = judge.demotion(GROUND, {"n": 10, "exact": 10, "raw": 1.0, "kappa": 1.0,
                                  "undecided": 3, "label_distribution": {}})
    assert out["status"] == "demoted"
    assert any("undecided" in r for r in out["reasons"])


def test_agreement_below_threshold_demotes():
    out = judge.demotion(GROUND, {"n": 10, "exact": 7, "raw": 0.7, "kappa": 0.5,
                                  "undecided": 0, "label_distribution": {}})
    assert out["status"] == "demoted"
    assert "below 0.75" in out["reasons"][0]


def test_a_calibrated_axis_names_no_reasons():
    out = judge.demotion(GROUND, {"n": 10, "exact": 8, "raw": 0.8, "kappa": 0.6,
                                  "undecided": 1, "label_distribution": {}})
    assert out["status"] == "calibrated" and out["reasons"] == []


def test_the_thresholds_are_the_ones_the_spec_fixed_in_advance():
    """Pinned so that a threshold cannot be re-derived after an agreement number
    exists. SPEC/03 fixed all three before the corpus was labelled; changing one
    is a two-key PR against a document that already says what it was."""
    assert judge.AGREEMENT_THRESHOLD == 0.75
    assert judge.MIN_SCORABLE_HELD_OUT == 5
    assert judge.MAX_UNDECIDED_FRACTION == 0.20


# --- the prompt ---------------------------------------------------------------


def test_the_prompt_renders_with_the_rubric_and_the_catalog_inside_it():
    """The rubric is embedded rather than referenced, which makes it model-facing
    text — a word changed there changes every band. That is why its digest is
    pinned beside the prompt's."""
    rendered = judge.render_prompt()
    assert "brand_tone:meridian-sports" in rendered
    assert "Jefferson Derby: Rovers vs Union" in rendered
    assert judge.CLOCK in rendered


def test_the_prompt_carries_no_answer_key():
    """A judge holding the golden expectations is not scoring an answer, it is
    checking a diff. None of the assert vocabulary may reach it."""
    rendered = judge.render_prompt()
    for leak in ("must_mention", "must_not_claim", "must_cite", "expect_near_threshold",
                 "entitlement_source", "cited_titles_in_fixture"):
        assert leak not in rendered, f"the judge prompt leaks {leak}"


def test_the_prompt_carries_no_worked_example_from_the_corpus():
    """A labelled example inside the prompt is calibration data leaking into the
    instrument being calibrated."""
    rendered = judge.render_prompt()
    for leak in ("cal-", "blackout-001", "grounded-019", "edge-025"):
        assert leak not in rendered, f"the judge prompt names {leak}"


def test_the_prompt_tells_the_judge_that_citing_nothing_is_not_grounded():
    """The vacuity that `cited_titles_in_fixture` had, one layer up. A judge that
    reads an empty citation list as "nothing to contradict" inherits the defect
    the deterministic tightening just closed."""
    assert "cites nothing is not grounded" in judge.render_prompt()


# --- the freeze ---------------------------------------------------------------


def test_held_out_is_refused_until_the_prompt_is_frozen():
    """The spec's central discipline, enforced rather than promised.

    Iterating the prompt against the 10 dev items is allowed for as long as it
    takes. Computing a number on the other 20 before the prompt stops moving is
    the thing that makes an agreement figure meaningless, so it raises."""
    if judge.is_frozen():
        pytest.skip("prompt is frozen; the guard's refusal path is exercised before freezing")
    with pytest.raises(SystemExit) as excinfo:
        judge.held_out_guard()
    assert "not frozen" in str(excinfo.value)


def test_freezing_pins_the_rubric_as_well_as_the_prompt():
    """Freezing only the prompt would leave the rubric free to move underneath it,
    and the rubric is half the model-facing text."""
    assert set(judge.instrument()) >= {"prompt_sha256", "rubric_sha256", "rendered_sha256"}
    if judge.FROZEN.is_file():
        marks = json.loads(judge.FROZEN.read_text(encoding="utf-8"))
        assert "rubric_sha256" in marks


def test_the_rubric_reaches_the_model_as_its_axes_and_nothing_else():
    """The cut, pinned.

    Embedding the rubric whole shipped its `## Headroom` section — *"2-3 cases in
    the golden set are authored to sit near this rubric's threshold"* — which tells
    the judge that some cases are deliberately borderline before it has read one.
    It also shipped the seat header, the M00a status note, and the reviewer-facing
    paragraph naming `cited_titles` and ADV-005.

    None of that defines a band. All of it is text a model reads.

    A test found it, which is the argument for writing `test_the_prompt_carries_no_
    answer_key` before the prompt rather than after the run."""
    axes = judge.rubric_axes()
    rendered = judge.render_prompt()

    for band_definition in ("groundedness", "completeness", "brand_tone:meridian-sports",
                            "concision", "Every factual claim traces to a cited title"):
        assert band_definition in axes

    # `cited_titles` is deliberately absent from this list: it is a field of the
    # answer the judge is shown in every user turn, so naming it in the
    # groundedness axis tells the model nothing it does not already have. The
    # assert *key* `cited_titles_in_fixture` is a different thing and is covered
    # by `test_the_prompt_carries_no_answer_key`.
    for reviewer_facing in ("Owning seat", "Two-key", "Status at M00a", "Headroom",
                            "expect_near_threshold", "ADV-005", "adversarial pass"):
        assert reviewer_facing not in rendered, (
            f"the judge prompt still carries {reviewer_facing!r}, which is written for a "
            "reviewer and is not a definition of a band"
        )


def test_the_slice_is_pinned_separately_from_the_whole_file():
    """Two digests, because they answer different questions. The whole file catches
    any change to the rubric; the slice catches a change to what the model actually
    reads. A rubric edit that moves only reviewer commentary should be visible
    without reading as an instrument change."""
    marks = judge.instrument()
    assert marks["rubric_sha256"] != marks["rubric_axes_sha256"]


def test_a_rubric_that_fails_to_slice_is_loud():
    """The failure mode least likely to be noticed from the output.

    The first version of `rubric_axes` anchored on `## Axes` unanchored, and
    matched the rubric's own sentence *about* the slice. It returned fourteen
    characters. The prompt still rendered, and a judge reading it would have
    returned perfectly well-formed bands scored against no rubric at all — the
    output of a broken instrument and a working one are the same shape.

    So the slice checks itself and exits rather than degrading."""
    from evals import judge as j

    original = j.RUBRIC
    try:
        j.RUBRIC = ROOT_TMP / "empty-rubric.md"
        j.RUBRIC.write_text("## Axes\n\nnothing\n\n## Headroom\n", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            j.rubric_axes()
        assert "is not there" in str(excinfo.value)
    finally:
        j.RUBRIC = original


def test_the_slice_carries_every_axis_the_golden_set_asks_for():
    """A slice that silently dropped one axis would leave the judge scoring an
    axis it was never given a definition for."""
    import yaml

    from evals.judge import ROOT

    cases = yaml.safe_load(
        (ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml")
        .read_text(encoding="utf-8"))
    asked = {a for c in cases for a in c.get("judge", {}).get("axes", ())}
    axes = judge.rubric_axes()
    for axis in sorted(asked):
        assert axis in axes, f"the golden set asks for {axis} and the rubric slice omits it"



# --- what the judge is shown, and what it is never asked ----------------------


@pytest.mark.parametrize("answer,expected", [
    ({"refused_by_gateway": "guardrail"}, "gateway-refusal:guardrail"),
    ({"refused_by_gateway": "policy"}, "gateway-refusal:policy"),
    ({"unparsed": "The search found one result..."}, "unparsed-turn"),
    ({"answer": None}, "no-answer-field"),
    (None, "no-answer-object"),
    ("a string", "no-answer-object"),
    ({"answer": "Yes.", "cited_titles": ["t001"]}, None),
])
def test_not_applicable_settles_every_no_answer_shape_without_a_model(answer, expected):
    """Three shapes carry nothing to grade, and all three are decided here rather
    than asked of the judge.

    SPEC/03 named two. The third — `unparsed` — was found while drafting the
    calibration labels: a turn whose reply the decoder could not read. The model
    answered, and its answer was even correct, but what the service emitted was
    undecodable and grading the blob would grade something it never produced.

    Deciding these deterministically also keeps four calibration items from
    becoming automatic agreements: a judge and a label that both say "not
    applicable" agree by construction rather than by judgement."""
    assert judge.not_applicable(answer) == expected


def test_the_user_turn_shows_the_answer_and_withholds_the_answer_key():
    """A judge holding the golden expectations is not scoring an answer, it is
    checking a diff — and it would then agree with the deterministic half by
    construction, which is the one result that could prove nothing."""
    case = {
        "id": "x", "input": "Derby on tonight?",
        "viewer": {"plan": "base", "dma": "lake-adair"},
        "asserts": [{"must_mention": "blackout"}, {"must_cite": ["t001"]}],
    }
    turn = judge.user_turn(case, {"answer": "Yes.", "cited_titles": ["t001"]}, [GROUND])
    assert "Derby on tonight?" in turn and "Yes." in turn and "t001" in turn
    assert "base" in turn and "lake-adair" in turn
    for leak in ("must_mention", "must_cite", "blackout"):
        assert leak not in turn, f"the user turn leaks {leak}"


@pytest.mark.parametrize("reported,expected_band,expected_problem", [
    ({"axes": {GROUND: {"band": 1.0}}}, 1.0, False),
    ({"axes": {GROUND: 0.5}}, 0.5, False),
    ({"axes": {GROUND: {"band": 0.75}}}, None, True),
    ({"axes": {GROUND: {"band": "1.0"}}}, None, True),
    ({"axes": {}}, None, True),
    ({}, None, True),
    (None, None, True),
])
def test_an_unreadable_band_is_never_guessed(reported, expected_band, expected_problem):
    """A judge that returned nothing usable for an axis is evidence about the
    judge. Filling it in with the middle band would erase exactly what `k_judge`
    exists to collect — and would do it in the direction that never vetoes, which
    is the flattering one."""
    bands, problems = judge.bands_from(reported, [GROUND])
    assert bands[GROUND] == expected_band
    assert bool(problems) is expected_problem


def test_an_axis_the_judge_was_not_asked_for_is_recorded_as_a_problem():
    """Dropping it silently would hide that the prompt is not being followed. A
    judge answering a question it was not asked is not obeying the one it was."""
    _, problems = judge.bands_from(
        {"axes": {GROUND: {"band": 1.0}, "invented_axis": {"band": 0.0}}}, [GROUND])
    assert problems == ["unrequested axis 'invented_axis'"]

"""
L1 tests for the deterministic runner (ADR-012).

Every fixture answer here is **hand-written**. None was captured from a model
run. Capturing them would shape the scorer around whatever the control happens
to emit, which is the same ordering hazard that made SPEC/00a insist the goldens
be authored before the control ran — and it would be worse here, because the
scorer is the instrument the control is measured with.

The answers are written against the case definitions and the answer schema, so
they say what a correct reply *should* look like, not what one did look like.

Hermetic (G8): no model, no network, committed fixtures only.
Owning seat: AI Quality (semantics) · Platform Engineering (mechanism).
"""
import json
import pathlib

import pytest
import yaml

from evals import deterministic as det

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = {c["id"]: c for c in yaml.safe_load(
    (ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml").read_text(encoding="utf-8"))}
CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))

USAGE = {"tokens_in": 1171, "tokens_out": 133, "latency_ms": 900}


@pytest.fixture
def scorer():
    return det.Scorer(root=ROOT)


def answer(**overrides):
    """A correct reply to `blackout-001`, hand-written from the case definition.

    Note the wording: this says "a blackout applies", not the more natural
    "blacked out", because `must_mention: "blackout"` is a substring check and
    "blacked out" does not contain it. The fixture is written to satisfy the case
    as authored — the case is AI Quality's and is not edited here. See the note
    in this milestone's PR: the assert is fragile in a way that could misattribute
    a phrasing mismatch to the control's blackout handling."""
    base = {
        "answer": ("A blackout applies to tonight's Jefferson Derby in Jefferson City, so it "
                   "is not available to stream there on your base plan."),
        "cited_titles": ["t001"],
        "entitlement": {"entitled": False, "reason": "blackout", "source": "entitlement-check"},
        "ai_disclosure": None,
    }
    base.update(overrides)
    return {"answer": base, "usage": dict(USAGE)}


# --- the happy path exists, so a failure below means something ------------------

def test_a_correct_answer_passes_every_assert(scorer):
    result = scorer.score_case(CASES["blackout-001"], answer(), CATALOG)
    assert result.result == det.PASS, [(a.kind, a.detail) for a in result.failures]


# --- the checks the control is expected to fail ---------------------------------

def test_a_confabulated_citation_fails_groundedness(scorer):
    """The deterministic groundedness check. A cited id absent from the catalog
    is a confabulation, and catching it needs no judge — which is the whole
    argument for this assert existing."""
    result = scorer.score_case(
        CASES["blackout-001"], answer(cited_titles=["t001", "t999"]), CATALOG)
    assert result.result == det.FAIL
    kinds = {a.kind for a in result.failures}
    assert "cited_titles_in_fixture" in kinds
    assert "t999" in next(a.detail for a in result.failures if a.kind == "cited_titles_in_fixture")


def test_entitlement_source_is_evaluated_but_never_scored(scorer):
    """ADR-016, and the reversal is the point.

    This assert used to be scored, on the reasoning that the control would emit
    `model-inference` and its constant FAIL was the gap M06 closes. The control
    instead read the enum out of the schema in its own prompt and claimed
    `entitlement-check` in 10 of 11 cases, turning the expected FAIL into an
    unearned PASS. An assert reading a self-report measures candour.

    So it must not reach the score in either direction — and it must still be
    evaluated, because the evaluation is what made the fabrication visible."""
    ent = {"entitled": False, "reason": "blackout", "source": "model-inference"}
    result = scorer.score_case(CASES["blackout-001"], answer(entitlement=ent), CATALOG)

    assert "entitlement_source" not in {a.kind for a in result.asserts}, "must not be scored"
    recorded = next(a for a in result.deferred if a.kind == "entitlement_source")
    assert not recorded.passed, "the mismatch is still detected and recorded"
    assert result.result == det.PASS, "a deferred assert cannot fail the case"


def test_a_fabricated_tool_claim_earns_no_credit(scorer):
    """The failure mode that motivated the deferral. A control claiming the tool
    it does not have must gain nothing from saying so — the case scores exactly
    as it would had the control been honest."""
    lied = {"entitled": False, "reason": "blackout", "source": "entitlement-check"}
    honest = {"entitled": False, "reason": "blackout", "source": "model-inference"}
    lying = scorer.score_case(CASES["blackout-001"], answer(entitlement=lied), CATALOG)
    truthful = scorer.score_case(CASES["blackout-001"], answer(entitlement=honest), CATALOG)
    assert lying.result == truthful.result, "claiming the tool must change nothing"
    assert len(lying.asserts) == len(truthful.asserts)


def test_latency_is_a_hang_guard_per_case_and_a_percentile_per_suite(scorer):
    """ADR-016. A single slow request is tail variance, not a defect; a stalled
    one is. The 5000ms guard catches the second without flagging the first."""
    slow = answer()
    slow["usage"]["latency_ms"] = 2400          # over the old 1800 p95 ceiling
    assert scorer.score_case(CASES["blackout-001"], slow, CATALOG).result == det.PASS

    hung = answer()
    hung["usage"]["latency_ms"] = 30_000
    result = scorer.score_case(CASES["blackout-001"], hung, CATALOG)
    assert result.result == det.FAIL
    assert "stalled" in next(a.detail for a in result.failures if a.kind == "budget")


def test_suite_p95_is_measured_across_the_population():
    """The statistic in the place where it means something."""
    answers = {f"c{i}": {"usage": {"latency_ms": ms}}
               for i, ms in enumerate([1000] * 19 + [9000])}
    assert det.suite_latency(answers, 2500).passed, "one slow call in twenty is inside a p95"
    assert not det.suite_latency({f"c{i}": {"usage": {"latency_ms": 9000}}
                                  for i in range(20)}, 2500).passed
    assert not det.suite_latency({}, 2500).passed, "no measurements is not a pass"


def test_a_wrong_entitlement_verdict_fails(scorer):
    ent = {"entitled": True, "reason": "ok", "source": "entitlement-check"}
    result = scorer.score_case(CASES["blackout-001"], answer(entitlement=ent), CATALOG)
    assert "entitlement" in {a.kind for a in result.failures}


# --- absence must block, never skip ---------------------------------------------

def test_a_missing_answer_is_infra_not_a_skip(scorer):
    """Same contract as `pave gate decide`: the harness could not establish
    anything, which pages the platform rather than the service team. A skip here
    would let a crashed agent report a clean suite."""
    result = scorer.score_case(CASES["blackout-001"], None, CATALOG)
    assert result.result == det.INFRA


def test_a_missing_usage_measurement_is_infra_not_a_passed_budget(scorer):
    """An unmeasured budget is not a satisfied budget. Treating it as passed is
    how a suite reports green over something it never checked."""
    record = answer()
    record.pop("usage")
    result = scorer.score_case(CASES["blackout-001"], record, CATALOG)
    assert result.result == det.INFRA
    assert "no usage recorded" in " ".join(a.detail for a in result.failures)


def test_an_unparseable_answer_is_infra(scorer):
    result = scorer.score_case(CASES["blackout-001"], {"usage": dict(USAGE)}, CATALOG)
    assert result.result == det.INFRA


# --- budgets are tokens, per ADR-014 ---------------------------------------------

def test_a_budget_is_enforced_on_tokens(scorer):
    record = answer()
    record["usage"]["tokens_out"] = 10_000
    result = scorer.score_case(CASES["blackout-001"], record, CATALOG)
    assert result.result == det.FAIL
    assert "tokens_out" in next(a.detail for a in result.failures if a.kind == "budget")


def test_a_budget_is_enforced_on_latency(scorer):
    record = answer()
    record["usage"]["latency_ms"] = 99_999
    result = scorer.score_case(CASES["blackout-001"], record, CATALOG)
    assert "latency_ms" in next(a.detail for a in result.failures if a.kind == "budget")


# --- schema and substring semantics ----------------------------------------------

def test_a_schema_violation_fails_before_prose_is_trusted(scorer):
    result = scorer.score_case(CASES["blackout-001"], answer(cited_titles="t001"), CATALOG)
    assert "json_schema" in {a.kind for a in result.failures}


def test_substring_asserts_are_case_insensitive(scorer):
    """`must_mention: "blackout"` must not fail on "Blackout" at the start of a
    sentence. A case-sensitive check here would fail correct answers, which the
    golden README calls the most expensive kind of broken case."""
    prose = "BLACKOUT applies: the derby is unavailable in Jefferson City tonight."
    result = scorer.score_case(CASES["blackout-001"], answer(answer=prose), CATALOG)
    assert next(a for a in result.asserts if a.kind == "must_mention").passed


# --- the judge is referenced and never read (ADR-012) -----------------------------

def test_the_runner_never_reads_the_judge_rubric(scorer, monkeypatch):
    """A judge with no published agreement number cannot produce a blocking
    score (G9). Asserting on the file read is stronger than asserting on the
    output: it fails the moment someone wires the rubric in, before any number
    it produces reaches a history entry."""
    opened = []
    original = pathlib.Path.read_text

    def spy(self, *a, **kw):
        opened.append(str(self))
        return original(self, *a, **kw)

    monkeypatch.setattr(pathlib.Path, "read_text", spy)
    scorer.score_case(CASES["blackout-001"], answer(), CATALOG)
    assert not [p for p in opened if "rubric" in p.lower()], f"rubric was read: {opened}"


def test_judge_axes_are_carried_as_advisory_not_scored(scorer):
    result = scorer.score_case(CASES["blackout-001"], answer(), CATALOG)
    assert result.advisory_axes, "the case's judge axes should be recorded"
    assert not [a for a in result.asserts if a.kind in result.advisory_axes], (
        "no judge axis may appear as a scored assert at M00b"
    )


# --- suite arithmetic ---------------------------------------------------------------

def test_tally_counts_every_outcome():
    results = [
        det.CaseResult("a", det.PASS), det.CaseResult("b", det.PASS),
        det.CaseResult("c", det.FAIL), det.CaseResult("d", det.INFRA),
    ]
    assert det.tally(results) == {
        "total": 4, "passed": 2, "failed": 1, "infra": 1, "pass_rate": 0.5}


def test_scoring_the_whole_suite_with_no_answers_is_all_infra(scorer):
    """A run that produced nothing scores 0, not a clean sheet."""
    results = scorer.score_suite(list(CASES.values()), {}, CATALOG)
    assert len(results) == 25
    assert det.tally(results) == {
        "total": 25, "passed": 0, "failed": 0, "infra": 25, "pass_rate": 0.0}

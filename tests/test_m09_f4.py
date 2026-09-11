"""
M09's F4, read at PR 4b: the goldens control run against the three clauses
SPEC/09 pre-registered, and the count kept out of them.

`milestones/M09/f4.py` reads the committed control run — 25 cases, k=3, through
the deployed gateway, after PR 4's fix — against F4:

> the goldens control run shows a ≤3-call answered sample **over 7700** that was
> under it at M08b; **or a case that passed 3-of-3 at M08b fails by majority; or a
> case that failed 0-of-3 at M08b passes by majority**

These tests pin the reading it produced, plant each clause both ways so that none
of the three is decorative, and hold the one thing this PR found the hard way: the
committed reader's own `count.falsifiers` block answers the two direction clauses
**against M08**, not against M08b, and reports them clean over a fired falsifier.

Hermetic (G8): every input is committed and no model is called. Seats, by the rule
that covers the readers and records: AI Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M09" / "f4.py"
M08B_ENTRY = ROOT / "evals" / "history" / "m08b-tools-goldens.json"
M09_JOIN = ROOT / "milestones" / "M09" / "fresh-join.json"

#: The reading, as the committed run produced it. Pinned so that a re-run, a
#: re-scored transcript or an edited answer file moves it or is red — never so
#: that the number can be updated to match a new run without saying so.
FIRED_ON = "grounded-017"
M08B_BRACKET = ["PASS", "PASS", "PASS"]
M09_BRACKET = ["PASS", "FAIL", "FAIL"]
#: The other mover, which is why the count did not notice.
COMPENSATING = "entitlement-011"
N = 10


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("m09_f4", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["m09_f4"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def reading(reader):
    """`(baseline, per-case majorities)`. `m09_brackets()` returns the count line
    beside the cases, and unpacking it as the cases dict is a `KeyError` one test
    run later — which is why the unwrapping is here rather than in each test."""
    return reader.m08b_baseline(), reader.m09_brackets()["cases"]


def _majority(samples: list[str]) -> str:
    return "PASS" if samples.count("PASS") * 2 > len(samples) else "FAIL"


# --- the three clauses, on the committed run ---------------------------------

def test_clause_1_is_clean_and_the_per_sample_claim_holds_at_7700(reader):
    """F4.1, read out of the record M08b's committed reader wrote over this run.

    The clause is narrower than *"a sample over the ceiling"* — it is one that was
    **under** it at M08b — and the unnarrowed list being empty settles it either
    way, which is why the reader prints that list first.

    The predicate is **called**, not recomputed: a test that re-derives it beside
    the reader stays green when the reader's copy is deleted."""
    join = json.loads(M09_JOIN.read_text(encoding="utf-8"))
    m08b = json.loads(
        (ROOT / "milestones" / "M08b" / "fresh-join.json").read_text(encoding="utf-8"))
    assert reader.clause_1(join, m08b) == []
    claim = join["claim"]
    assert claim["holds"] is True
    assert claim["3_call_or_fewer_samples_over"] == []
    assert claim["4_call_or_more_samples_under"] == []
    assert claim["samples_at_3_calls_or_fewer"] == 61
    assert claim["largest_3_call_or_fewer_tokens_in"] == 7280, (
        "the binding <=3-call sample moved. It is headroom-005, 6782 at M08b and 7280 "
        "here; the difference is the prompt delta measured live, and it is what F4.1 "
        "is about")
    assert claim["samples_at_4_calls_or_more"] == 8
    assert claim["smallest_4_call_or_more_tokens_in"] == 8949


def test_clause_2_fired_on_grounded_017(reader, reading):
    """**The falsifier that fired.** Pinned by name, bracket and bracket."""
    base, now = reading
    assert base[FIRED_ON] == M08B_BRACKET, "grounded-017 no longer passed 3-of-3 at M08b"
    assert now[FIRED_ON]["samples"] == M09_BRACKET
    assert now[FIRED_ON]["result"] == "FAIL"
    regressed = reader.clause_2(base, now)
    assert regressed == [FIRED_ON], (
        f"clause 2 now fires on {regressed}. F4 fired on {FIRED_ON} and the claim is "
        "FAILED on it; a different list is a different reading and must be recorded, "
        "never edited to match this one.")


def test_clause_3_is_clean_over_all_twelve_cases_that_failed_0_of_3(reader, reading):
    base, now = reading
    zero = sorted(c for c in base if all(s == "FAIL" for s in base[c]))
    assert len(zero) == 12, "the twelve 0-of-3 cases this clause reads are no longer twelve"
    assert reader.clause_3(base, now) == []


def test_every_clause_is_reachable_and_none_is_decorative(reader, reading):
    """One plant per clause, through the reader's own predicates, so a clause that
    can never fire is caught here rather than by being quietly clean for a
    milestone. The plants are on copies of what the predicates read."""
    base, now = reading
    base, now = dict(base), {k: dict(v) for k, v in now.items()}

    # clause 2, made clean: give grounded-017 a 2-of-3 M08b bracket and it is no
    # longer a 3-of-3 case, so the clause has nothing to fire on.
    assert reader.clause_2(dict(base, **{FIRED_ON: ["PASS", "PASS", "FAIL"]}), now) == []

    # clause 3, made to fire: a case that failed 0-of-3 at M08b passing here.
    bent_now = {k: dict(v) for k, v in now.items()}
    bent_now["blackout-001"]["result"] = "PASS"
    assert reader.clause_3(base, bent_now) == ["blackout-001"]

    # clause 1, made to fire: a <=3-call answered sample over the ceiling that
    # M08b's own list does not carry.
    m08b = json.loads(
        (ROOT / "milestones" / "M08b" / "fresh-join.json").read_text(encoding="utf-8"))
    join = json.loads(M09_JOIN.read_text(encoding="utf-8"))
    planted = dict(join, claim=dict(join["claim"],
                                    **{"3_call_or_fewer_samples_over": ["edge-024 s2"]}))
    assert reader.clause_1(planted, m08b) == ["edge-024 s2"]
    # and clause 1's narrowing is real: a sample M08b ALSO had over the ceiling is
    # not one this run moved, so the same plant on both sides reads clean.
    both = dict(m08b, claim=dict(m08b["claim"],
                                 **{"3_call_or_fewer_samples_over": ["edge-024 s2"]}))
    assert reader.clause_1(planted, both) == []


# --- the count is not the falsifier ------------------------------------------

def test_the_count_hit_its_prediction_while_two_cases_moved(reader, reading):
    """**The whole reason the count is a side-prediction**, measured.

    `N` landed on 10 — M08b's number and SPEC/09's predicted one — with
    `grounded-017` losing a majority and `entitlement-011` gaining one underneath
    it. A reader of the count alone reports *no change* over a fired falsifier.
    That is the compensating movement the falsifier table described before the run,
    and this asserts it happened rather than leaving it as a sentence."""
    base, now = reading
    assert now[COMPENSATING]["result"] == "PASS" and _majority(base[COMPENSATING]) == "FAIL"
    assert _majority(base[FIRED_ON]) == "PASS" and now[FIRED_ON]["result"] == "FAIL"
    moved = sorted(c for c in base if _majority(base[c]) != now[c]["result"])
    assert moved == sorted([COMPENSATING, FIRED_ON])
    # and only one of the two is a falsifier: entitlement-011 failed 2-of-3 at
    # M08b, not 0-of-3, so clause 3 does not reach it. The count sees both moves
    # and cancels them; F4 sees the one that is a falsifier.
    assert reader.clause_3(base, now) == [] and reader.clause_2(base, now) == [FIRED_ON]
    m08b_n = sum(1 for c in base.values() if _majority(c) == "PASS")
    m09_n = sum(1 for c in now.values() if c["result"] == "PASS")
    assert m08b_n == m09_n == N, (
        "the two counts no longer agree, so the compensating movement this test is "
        "about is gone and the reading must be re-taken, not re-pinned")


def test_the_count_is_printed_after_the_falsifier_and_labelled(reader, capsys):
    """A reader who stops early must not stop on the count.

    The band is a side-prediction in all three of SPEC/09's sites, and the one
    place it can still masquerade as the falsifier is the transcript a human
    actually reads."""
    reader.main()
    out = capsys.readouterr().out
    assert out.index("F4    FIRED") < out.index("SIDE-PREDICTION"), (
        "the count is printed before F4's verdict; a reader who stops at the first "
        "number stops at the one that did not fire")
    assert "SIDE-PREDICTION (not F4, not the claim)" in out
    assert "THE CLAIM IS FAILED" in out and "disclosure-103" in out, (
        "the reading does not say the claim was already failed on F1. F4 is a second "
        "falsifier, not the first, and a transcript that reports F4 alone reads as "
        "though this run decided the milestone")


def test_the_count_band_and_the_prediction_are_m09s_and_not_m08bs(reader):
    """`fresh_join.py` carries M08b's band [7, 14] and predicted 12 as module
    constants, and running it over this directory prints them. SPEC/09's band is
    [8, 12] predicted 10, and this reader is where that lives."""
    assert reader.COUNT_BAND == (8, 12) and reader.PREDICTED_N == 10
    assert reader.REFUSAL_BAND == (0, 2)
    fresh_join_band = json.loads(M09_JOIN.read_text(encoding="utf-8"))["count"]
    assert fresh_join_band["band"] == [7, 14] and fresh_join_band["predicted"] == 12, (
        "fresh_join.py's band is no longer M08b's, so the contrast this test draws is "
        "stale; the point is that the record written over M09's directory carries "
        "another milestone's band and the F4 reading must not be taken from it")


# --- the finding this PR paid for --------------------------------------------

def test_the_committed_records_direction_block_answers_against_m08_and_says_clean():
    """**The reason `f4.py` exists, asserted so nobody deletes it as duplication.**

    `milestones/M08b/fresh_join.py` writes a `count.falsifiers` block whose keys
    are literally `3_of_3_pass_at_m08_failing_by_majority` and
    `0_of_3_fail_at_m08_passing_by_majority`, and whose comparison base is a module
    constant pointing at `milestones/M08/rescore-join.json`. Run over M09's
    directory it therefore compares this run against **M08's re-reading** and
    reports both lists empty — which is true of M08 and false of M08b, because
    `grounded-017` did not pass 3-of-3 at M08.

    F4's clauses name M08b. A reader who took this block at face value would have
    published *F4 clean* over a fired falsifier, which is the vacuous pass this
    repository has met in four places. Asserting the disagreement is what stops
    the next reader repeating it."""
    record = json.loads(M09_JOIN.read_text(encoding="utf-8"))
    falsifiers = record["count"]["falsifiers"]
    assert falsifiers["3_of_3_pass_at_m08_failing_by_majority"] == [], (
        "the committed record's M08-based direction list is no longer empty, so the "
        "trap this test describes is gone; re-aim it rather than deleting it")
    m08 = json.loads(
        (ROOT / "milestones" / "M08" / "rescore-join.json").read_text(encoding="utf-8"))
    m08_bracket = {c["case"]: c.get("rescore_samples") for c in m08.get("per_case") or []}
    assert m08_bracket.get(FIRED_ON) != M08B_BRACKET, (
        f"{FIRED_ON} has the same bracket at M08 and M08b, so the two baselines no "
        "longer disagree on the case F4 fired on and this test proves nothing")
    assert record["count"]["per_case"][FIRED_ON]["result"] == "FAIL"


# --- the inputs the reading rests on ------------------------------------------

def test_the_baseline_is_the_published_entry_and_not_a_list_in_the_reader(reader):
    """The `m08b` row's **10/25** and F4's baseline are the same bytes.

    A baseline copied into the reader could disagree with the number the README
    publishes, and the disagreement would be invisible: both would be green."""
    entry = json.loads(M08B_ENTRY.read_text(encoding="utf-8"))
    assert entry["scores"]["passed"] == N and entry["scores"]["total"] == 25
    from pave import history
    assert history.README_GOLDENS["m08b"] == M08B_ENTRY.name
    base = reader.m08b_baseline()
    assert base == {c["id"]: c["samples"] for c in entry["cases"]}
    # No case id is a literal in the reader — except the seven browse-gap cases,
    # which are a NAMED CAUSE and not a baseline: they say why a case fails, never
    # whether it did. The test below holds those to ADR-074 and to the case file.
    source = READER.read_text(encoding="utf-8")
    for case_id in set(base) - set(reader.BROWSE_GAP_SEVEN):
        assert f'"{case_id}"' not in source and f"'{case_id}'" not in source, (
            f"{case_id} is a literal in f4.py. The baseline is read from the published "
            "entry precisely so that it cannot be typed in beside it and drift.")


def test_the_seven_browse_gap_cases_are_seven_real_cases(reader):
    """The one hand-held list in the reader: ADR-074 decision 2 names the seven and
    no machine-readable record does, so this is what holds it to the case set."""
    import yaml
    cases = {c["id"] for c in yaml.safe_load(
        (ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
         ).read_text(encoding="utf-8"))}
    assert len(reader.BROWSE_GAP_SEVEN) == 7
    assert set(reader.BROWSE_GAP_SEVEN) <= cases
    adr = (ROOT / "docs" / "adr" /
           "ADR-074-m08b-measures-the-ceiling-on-fresh-samples-and-the-registry-stays-m09.md"
           ).read_text(encoding="utf-8")
    for case_id in reader.BROWSE_GAP_SEVEN:
        assert f"`{case_id}`" in adr, f"{case_id} is not one of ADR-074 decision 2's seven"


def test_the_named_causes_are_read_from_records_and_not_from_prose(reader):
    causes = reader.named_causes()
    assert causes["guardrail_topic_refusal"] == ["blackout-009", "recommend-003"], (
        "M08b's refused-by-majority census is not the two cases the journal names")
    assert len(causes["tokens_out_at_unchanged_tiers"]) == 11, (
        f"M08b widened the five tokens_out cases to twelve, of which blackout-009 is "
        f"refused and carries no tokens_out verdict; the reader reads "
        f"{sorted(causes['tokens_out_at_unchanged_tiers'])}")
    assert causes["browse_gap"] == sorted(reader.BROWSE_GAP_SEVEN)


def test_the_reader_refuses_a_baseline_and_a_run_with_different_case_sets(reader, monkeypatch):
    """F4 compares case for case. A baseline missing a case would make every clause
    quietly narrower, and the narrower reading is the clean one."""
    base = reader.m08b_baseline()
    now = reader.m09_brackets()["cases"]
    reader.same_case_set(base, now)          # the control: the real pair is accepted
    base.pop("grounded-017")
    with pytest.raises(SystemExit, match="compares case for case"):
        reader.same_case_set(base, now)
    monkeypatch.setattr(reader, "m08b_baseline", lambda: base)
    with pytest.raises(SystemExit, match="compares case for case"):
        reader.main()

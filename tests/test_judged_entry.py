"""
The judged history entry: what it carries, what it must never carry, and the
one thing a demoted judge is not allowed to do.

Claim 9 is *judges are calibrated or advisory*. `tests/test_judge.py` pins the
demotion arithmetic; this file pins what demotion does to a **recorded score**,
in both directions — a calibrated axis can turn a deterministic PASS into a
judged FAIL, and a demoted one cannot block anything at all.

Hermetic. Owning seat: AI Quality.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

import pytest

from evals import judge, judged, run_evals
from evals.deterministic import CaseResult

ROOT = pathlib.Path(__file__).resolve().parents[1]
HELD_OUT_REPORT = ROOT / "milestones" / "M03" / "judge" / "held-out-report.json"


def calibration(status: str = "demoted", axis: str = "groundedness", name: str = "A") -> dict:
    return {"instrument_name": name,
            "axes": {axis: {"n": 6, "exact": 0, "raw": 0.0, "undecided": 6, "status": status}}}


def judge_dir(tmp_path: pathlib.Path, cases: dict, samples=(1, 2, 3),
              marks: dict | None = None) -> pathlib.Path:
    directory = tmp_path / "judged"
    directory.mkdir(exist_ok=True)
    for sample in samples:
        (directory / f"m00b-{sample}.json").write_text(json.dumps({
            "label": "m00b", "sample": sample, "answers_file": "x.json",
            "instrument": marks or judge.instrument(), "service": "judge-highlights",
            "cases": cases,
        }), encoding="utf-8")
    return directory


# --- what decides whether a band may veto ------------------------------------


def test_calibrated_axes_comes_from_the_published_report_not_the_run():
    """Which axes may veto is decided by an agreement number, never by the run
    being scored. Reading it from the report is what stops a judged entry and the
    figure that licenses it from disagreeing."""
    assert judged.calibrated_axes(calibration("calibrated")) == {"groundedness"}
    assert judged.calibrated_axes(calibration("demoted")) == set()


def test_the_published_m03_calibration_licenses_no_axis():
    """M03's actual state, read off the committed report rather than restated.

    Every axis demoted, so the calibrated set is empty, so `veto` consults
    nothing. This is what "advisory in full" means as arithmetic."""
    published = json.loads(HELD_OUT_REPORT.read_text(encoding="utf-8"))
    assert judged.calibrated_axes(published) == set()
    assert all(row["status"] == "demoted" for row in published["axes"].values())


# --- claim 9's artifact, both directions --------------------------------------


def test_a_calibrated_axis_turns_a_deterministic_pass_into_a_judged_fail(tmp_path):
    """The direction that must work, or "calibrated" buys nothing."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 0.0}}})
    parts = judged.entry_parts(directory, calibration("calibrated"), 3)
    assert parts["vetoes"] == {"blackout-001": ["groundedness"]}


def test_a_demoted_axis_cannot_turn_anything_into_a_fail(tmp_path):
    """The direction that must NOT work. Same judge output, same 0.0 band, one
    difference: the axis is demoted. A demoted judge that still subtracted would
    be blocking on an instrument with no published agreement — G9, and the exact
    thing claim 9 promises cannot happen."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 0.0}}})
    parts = judged.entry_parts(directory, calibration("demoted"), 3)
    assert parts["vetoes"] == {}


def test_an_undecided_band_never_vetoes_even_when_calibrated(tmp_path):
    """No strict majority is the absence of a decision, not a decision to fail."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 0.0}}},
                          samples=(1, 2, 3))
    # 0.0 / 1.0 / 0.5 — three different bands, no majority.
    for sample, band in ((1, 0.0), (2, 1.0), (3, 0.5)):
        path = directory / f"m00b-{sample}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["cases"]["blackout-001"]["axes"]["groundedness"] = band
        path.write_text(json.dumps(doc), encoding="utf-8")
    parts = judged.entry_parts(directory, calibration("calibrated"), 3)
    assert parts["bands"]["blackout-001"]["groundedness"] is None
    assert parts["vetoes"] == {}


def test_the_veto_reaches_the_recorded_score(tmp_path, monkeypatch, capsys):
    """End to end, through `run_evals.run`, on the real production path.

    This test used to build the vetoed results with its own inline comprehension
    duplicating `run_evals.py`. It never called the code it was named for: delete
    the veto application from `run_evals` entirely and it still passed. That is the
    third time this branch has recorded a test named for a defect that exercises a
    different function than the one containing it."""
    # A real committed answer that PASSES deterministically today, because a veto can
    # only turn PASS into FAIL. A synthetic answer that already failed would let this
    # test report "1 case vetoed" while nothing actually moved - which is the shape
    # of vacuity it was rewritten to escape.
    committed = json.loads((ROOT / "milestones" / "M00b" / "goldens-run.json")
                           .read_text(encoding="utf-8"))
    answers = {"blackout-001": committed["blackout-001"]}
    answers_file = tmp_path / "answers.json"
    answers_file.write_text(json.dumps(answers), encoding="utf-8")
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 0.0}}})
    calibration_file = tmp_path / "calibration.json"

    def score(status: str) -> str:
        calibration_file.write_text(json.dumps(calibration(status)), encoding="utf-8")
        run_evals.main([
            "--answers", str(answers_file), "--target", "baseline",
            "--judged", str(directory), "--calibration", str(calibration_file),
            "--k-judge", "3",
        ])
        return capsys.readouterr().out

    calibrated = score("calibrated")
    demoted = score("demoted")

    assert "1 case(s) vetoed" in calibrated, (
        "a calibrated 0.0 band did not reach the runner's own veto path")
    assert "0 case(s) vetoed" in demoted, "a demoted axis subtracted something"

    # The case is actually marked FAIL by the production path, not merely counted.
    verdict = re.search(r"^blackout-001\s+(\S+)", calibrated, re.M)
    assert verdict and verdict.group(1) == "FAIL", calibrated
    assert re.search(r"^blackout-001\s+PASS", demoted, re.M), (
        "the same judge output with the axis demoted must leave the case alone")
    assert "judge:groundedness" in calibrated, "the vetoing axis is not named in the output"


# --- what the entry must and must not carry -----------------------------------


def test_the_entry_records_which_instrument_calibrated_it(tmp_path):
    """`judge_axes` and `instrument` describe different objects and can come from
    different instruments — at M03 they do. A reader assuming otherwise would be
    wrong and would have no way to find out (ADR-027, rule 5)."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 1.0}}})
    parts = judged.entry_parts(directory, calibration(name="A"), 3)
    assert parts["instrument"]["name"] == "B", "the tree's instrument read these answers"
    assert parts["instrument"]["calibrated_by"] == "A", "instrument A produced the calibration"


def test_calibrated_by_is_recorded_even_when_it_matches(tmp_path):
    """Otherwise its absence would have to mean "the same one", and absence
    already means "not recorded"."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 1.0}}})
    parts = judged.entry_parts(directory, calibration(name="B"), 3)
    assert parts["instrument"]["calibrated_by"] == "B"


def test_an_instrument_no_freeze_record_names_is_refused(tmp_path):
    """ADR-027 rule 4. A row naming an instrument nobody can look up is a
    fingerprint of an object that does not exist."""
    invented = dict(judge.instrument(), prompt_sha256="0" * 64)
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 1.0}}},
                          marks=invented)
    with pytest.raises(SystemExit, match="no entry"):
        judged.entry_parts(directory, calibration(), 3)


def test_a_calibration_report_with_no_instrument_name_is_refused(tmp_path):
    """The axes table decides whether any band may veto. An unnamed one leaves a
    reader unable to tell which instrument licensed the veto."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 1.0}}})
    with pytest.raises(SystemExit, match="does not name the instrument"):
        judged.entry_parts(directory, {"axes": {}}, 3)


def test_a_judged_entry_carries_no_supersedes_and_a_distinguishing_filename(tmp_path, monkeypatch):
    """The two rules most likely to be broken by someone following ADR-012's
    original text: `supersedes` is the wrong verb, and the append-only guard keys
    on the filename so two entries under one tag need two names."""
    monkeypatch.setattr(run_evals, "HISTORY", tmp_path / "history")
    args = argparse.Namespace(target="baseline", arm=None, tag="m00b",
                              tokens_in=None, tokens_out=None)
    parts = {"instrument": dict(judge.instrument(), name="B", calibrated_by="A", k_judge=3,
                                deterministic=judged.deterministic_instrument()),
             "judge_axes": calibration()["axes"],
             "guardrail_refusals": {"model_eligible_calls": 3, "served": 3}}
    results = [CaseResult("blackout-001", "PASS", (), ())]
    scores = {"total": 1, "passed": 1, "failed": 0, "infra": 0, "pass_rate": 1.0}

    path = run_evals.record(results, scores, args, k=3, judged=parts)
    entry = json.loads(path.read_text(encoding="utf-8"))

    assert path.name == "m00b-judged-B-goldens.json", (
        "a judged entry must not collide with the deterministic one; the append-only "
        "guard is a filename check")
    assert "supersedes" not in entry, (
        "15/25 is not wrong — it is a correct measurement under a different instrument")
    assert entry["instrument"]["name"] == "B"
    assert entry["instrument"]["calibrated_by"] == "A"
    assert entry["judge_axes"] and entry["guardrail_refusals"]


def test_the_judged_entry_validates_against_the_committed_schema(tmp_path, monkeypatch):
    """`record` validates before writing, so this passing means the schema accepts
    a judged row — including the two fields M03 added as `required`."""
    monkeypatch.setattr(run_evals, "HISTORY", tmp_path / "history")
    args = argparse.Namespace(target="baseline", arm=None, tag="m00b",
                              tokens_in=None, tokens_out=None)
    parts = {"instrument": dict(judge.instrument(), name="B", calibrated_by="A", k_judge=3,
                                deterministic=judged.deterministic_instrument()),
             "judge_axes": calibration()["axes"],
             "guardrail_refusals": {"model_eligible_calls": 3, "served": 3}}
    run_evals.record([CaseResult("c", "PASS", (), ())],
                     {"total": 1, "passed": 1, "failed": 0, "infra": 0, "pass_rate": 1.0},
                     args, k=3, judged=parts)


def test_an_instrument_block_missing_the_user_turn_digest_is_rejected(tmp_path, monkeypatch):
    """`user_turn_sha256` is `required`. History is append-only, so a row that
    cannot say which instrument produced it is permanently ambiguous — and an
    instrument-A row records it as null rather than omitting it."""
    import jsonschema

    monkeypatch.setattr(run_evals, "HISTORY", tmp_path / "history")
    args = argparse.Namespace(target="baseline", arm=None, tag="m00b",
                              tokens_in=None, tokens_out=None)
    marks = {k: v for k, v in judge.instrument().items() if k != "user_turn_sha256"}
    parts = {"instrument": dict(marks, name="B", calibrated_by="A", k_judge=3,
                                deterministic=judged.deterministic_instrument()),
             "judge_axes": calibration()["axes"],
             "guardrail_refusals": {"model_eligible_calls": 3, "served": 3}}
    with pytest.raises(jsonschema.ValidationError):
        run_evals.record([CaseResult("c", "PASS", (), ())],
                         {"total": 1, "passed": 1, "failed": 0, "infra": 0, "pass_rate": 1.0},
                         args, k=3, judged=parts)


def test_the_entry_records_what_scored_the_deterministic_half(tmp_path):
    """The third instance of one lesson, and the most expensive.

    M03's `m00b` anchor scores 18/25 against the 15/25 the deterministic entry
    records for the same answers at the same commit. **None of that difference is
    the judge** — it vetoed nothing, because no axis is calibrated. All three
    flipped cases carried `p95_ms: 1800` at M00b and ran at 1918, 2017 and 1862 ms;
    ADR-016 moved the percentile to suite level.

    An entry whose only instrument field describes the judge would let a reader
    conclude the judge added three passes. A judge can only subtract."""
    directory = judge_dir(tmp_path, {"blackout-001": {"axes": {"groundedness": 1.0}}})
    parts = judged.entry_parts(directory, calibration(), 3)
    det = parts["instrument"]["deterministic"]
    assert det["deferred"] == ["entitlement_source"], (
        "ADR-016 stopped scoring entitlement_source; that is exactly the change this "
        "block exists to make visible")
    assert "budget" in det["scored"]
    assert det["cases_sha256"] == judge.digest(
        (ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml")
        .read_text(encoding="utf-8"))


def test_the_three_flipped_cases_are_the_deterministic_instrument_not_the_judge():
    """The 15 -> 18 decomposition, pinned hermetically.

    This used to shell out to `git show <m00b_sha>:...` and `pytest.skip` when that
    failed. The gate checks out at depth 1, so it skipped on **every CI run** and
    asserted only on a deep clone — the milestone's load-bearing arithmetic,
    verified nowhere that mattered. The m00b-era budgets are now a committed
    fixture: a byte is reachable from a shallow clone forever, and a commit is not.

    It also asserts that **exactly** three cases flipped. Checking only that the
    three named ones were over budget would let a fourth flip, from an unrelated
    cause, hide inside the same total."""
    era = json.loads((ROOT / "tests" / "fixtures" / "m00b-era-budgets.json")
                     .read_text(encoding="utf-8"))
    recorded = json.loads((ROOT / "evals" / "history" / "m00b-goldens.json")
                          .read_text(encoding="utf-8"))
    judged = json.loads((ROOT / "evals" / "history" / "m00b-judged-B-goldens.json")
                        .read_text(encoding="utf-8"))
    answers = json.loads((ROOT / "milestones" / "M00b" / "goldens-run.json")
                         .read_text(encoding="utf-8"))
    assert era["m00b_sha"] == recorded["sha"], (
        "the fixture was lifted from a different commit than the recorded entry")

    was = {c["id"]: c["result"] for c in recorded["cases"]}
    now = {c["id"]: c["result"] for c in judged["cases"]}
    flipped = sorted(cid for cid in was if was[cid] != now[cid])
    assert flipped == ["blackout-001", "blackout-006", "concise-022"], (
        f"exactly three cases flipped between the m00b entry and the judged anchor; "
        f"found {flipped}. A fourth flip has a different cause and needs its own account")

    for case_id in flipped:
        budget = era["budgets"][case_id]
        latency = answers[case_id]["usage"]["latency_ms"]
        assert budget["p95_ms"] == 1800
        assert latency > budget["p95_ms"], (
            f"{case_id} was inside its m00b-era per-case p95, so the 15 -> 18 difference "
            "is not explained by ADR-016 and needs re-deriving")
        assert was[case_id] == "FAIL" and now[case_id] == "PASS"

    # And the judge caused none of it.
    assert judged["scores"]["passed"] - recorded["scores"]["passed"] == len(flipped)
    assert judged["judge_axes"], "the judged entry records no axes table"
    assert all(row["status"] == "demoted" for row in judged["judge_axes"].values()), (
        "an axis is calibrated, so the judge could have moved cases and this "
        "decomposition no longer holds")

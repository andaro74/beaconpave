"""What the calibration report must not quietly get wrong.

`evals/judge.py` owns the arithmetic and `tests/test_judge.py` pins it. This file
pins the *assembly* — which items reach the arithmetic and which are dropped —
because every mistake available here inflates the published number rather than
deflating it, and an inflated agreement figure is the one failure claim 9 cannot
survive.

Hermetic. Owning seat: AI Quality.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from evals import run_calibration as rc

ROOT = pathlib.Path(__file__).resolve().parents[1]
HELD_OUT = ROOT / "milestones" / "M03" / "judge" / "held-out"

INSTRUMENT = {"prompt_sha256": "a" * 64, "rubric_sha256": "b" * 64,
              "rubric_axes_sha256": "c" * 64, "rendered_sha256": "d" * 64}


def write_samples(directory: pathlib.Path, label: str, cases_by_sample: dict,
                  instrument: dict | None = None) -> None:
    for sample, cases in cases_by_sample.items():
        (directory / f"{label}-{sample}.json").write_text(json.dumps({
            "label": label, "sample": sample, "answers_file": "x.json",
            "instrument": instrument or INSTRUMENT, "service": "judge-highlights",
            "cases": cases,
        }), encoding="utf-8")


# --- the drop rule, which is where a flattering number would come from --------


def test_a_refused_judge_call_is_a_disagreement_and_not_a_dropped_item():
    """The single most dangerous mistake available in this module.

    The answer exists and the judge was asked; a control would not carry the call.
    Dropping it would compute agreement over exactly the answers the guardrail
    found unobjectionable — a different question, and a far more flattering one.
    At M03 it would have turned four demoted axes into a published figure over
    five items.
    """
    rows = [
        {"item": "x", "axis": "groundedness", "label": 1.0, "band": None,
         "samples": [None, None, None]},
        {"item": "y", "axis": "groundedness", "label": 1.0, "band": 1.0,
         "samples": [1.0, 1.0, 1.0]},
    ]
    diag = rc.diagnostics(rows)
    assert diag["decided_only"]["n"] == 1, "the refused item must not be scored as decided"
    assert diag["undecided_because_controls_refused"] == 1
    assert diag["undecided_because_judge_split_bands"] == 0


def test_undecided_separates_a_blocked_call_from_a_judge_that_split_bands():
    """Same `undecided` count, two different platforms and two different seats.

    Three refusals is a finding about the gateway. Three different bands is a
    finding about the judge. A reader who cannot tell them apart will attribute
    the demotion to whichever one they already believed in.
    """
    rows = [
        {"item": "blocked", "axis": "a", "label": 1.0, "band": None,
         "samples": [None, None, 1.0]},
        {"item": "split", "axis": "a", "label": 1.0, "band": None,
         "samples": [0.0, 0.5, 1.0]},
    ]
    diag = rc.diagnostics(rows)
    assert diag["undecided_because_controls_refused"] == 1
    assert diag["undecided_because_judge_split_bands"] == 1


def test_decided_only_agreement_is_never_the_published_figure(tmp_path):
    """It is reported, and it is reported as a diagnostic.

    The guard is that it lives under `diagnostics` and nowhere near `axes`, so no
    caller can pick it up by reaching for the obvious key.
    """
    result = rc.report("held-out", HELD_OUT, 3)
    assert "decided_only" in result["diagnostics"]
    for stats in result["axes"].values():
        assert "decided_only" not in stats
        assert stats["n"] >= stats["undecided"], "undecided items must be inside n, not beside it"


# --- the two integrity checks -------------------------------------------------


def test_a_judge_that_moved_mid_run_refuses_to_be_scored(tmp_path):
    """Two instrument blocks in one directory means two judges.

    ADR-018's argument, one layer up: an agreement number computed across an
    instrument that moved describes neither instrument.
    """
    moved = {**INSTRUMENT, "prompt_sha256": "e" * 64}
    write_samples(tmp_path, "run", {1: {"c": {"axes": {"a": 1.0}}}})
    write_samples(tmp_path, "other", {1: {"c": {"axes": {"a": 1.0}}}}, instrument=moved)
    with pytest.raises(SystemExit, match="instrument block"):
        rc.report("held-out", tmp_path, 3)


def test_the_harness_and_the_seat_must_agree_on_which_items_have_no_answer():
    """A silent drop is the only way an item leaves the corpus unnoticed.

    If the harness starts calling something not-applicable that the seat labelled
    applicable, the item vanishes from the denominator and the published figure
    rises. The report refuses rather than drops.
    """
    result = rc.report("held-out", HELD_OUT, 3)
    dropped = {d["item"] for d in result["dropped_not_applicable"]}
    assert dropped, "the corpus deliberately contains no-answer items; none reached the report"
    for row in result["rows"]:
        assert row["item"] not in dropped, "an item cannot be both scored and dropped"


def test_an_even_k_is_refused():
    """`k_judge = 2` makes `undecided` mean two different things at once — no
    majority because the judge disagreed with itself, and no majority because a
    tie is arithmetically unbreakable. M02 wrote this rule with nothing riding on
    it; M03 is the first milestone where a split is reachable."""
    assert rc.main(["--judged", str(HELD_OUT), "--k", "2"]) == 2


# --- the published M03 result, pinned -----------------------------------------


def test_the_published_held_out_result_is_reproducible_offline():
    """A stranger with no AWS account re-derives every published number.

    That is the whole reason raw judge output is committed. If this test needs
    updating for a reason other than a deliberate re-run, a published number moved
    without a recorded act.
    """
    result = rc.report("held-out", HELD_OUT, 3)
    assert result["k_judge"] == 3
    assert result["correction_rate"] == {"n": 20, "corrected": 0, "rate": 0.0}
    assert result["refusals"]["model_eligible_calls"] == 48
    assert result["refusals"]["guardrail"] == 28
    assert result["refusals"]["classification"] == 3
    assert result["refusals"]["served"] == 17

    expected = {
        "brand_tone:meridian-sports": (3, 0.0, 2),
        "completeness": (5, 0.0, 3),
        "concision": (3, 0.6667, 1),
        "groundedness": (6, 0.0, 6),
    }
    assert set(result["axes"]) == set(expected)
    for axis, (n, raw, undecided) in expected.items():
        stats = result["axes"][axis]
        assert (stats["n"], stats["raw"], stats["undecided"]) == (n, raw, undecided), axis
        assert stats["status"] == "demoted", axis

    assert result["diagnostics"]["undecided_because_judge_split_bands"] == 0, (
        "every undecided held-out item was a refused call, not an unstable judge — "
        "the finding that says the instability is in the gateway and not in the judge"
    )
    assert result["diagnostics"]["decided_only"]["raw"] == 0.4


def test_no_axis_is_calibrated_and_the_reasons_are_recorded():
    """Claim 9's artifact, as measured. Not an aspiration and not a placeholder:
    if this ever flips to calibrated, it is because a real number moved."""
    result = rc.report("held-out", HELD_OUT, 3)
    calibrated = [a for a, d in result["axes"].items() if d["status"] == "calibrated"]
    assert calibrated == [], f"unexpectedly calibrated: {calibrated}"
    for axis, stats in result["axes"].items():
        assert stats["reasons"], f"{axis} is demoted with no reason recorded"

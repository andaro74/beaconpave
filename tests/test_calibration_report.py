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

from evals import judge
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


def corpus(tmp_path, items, labels):
    """Point the module at a synthetic corpus so `assemble` can be tested directly."""
    (tmp_path / "items.json").write_text(json.dumps({"salt": "t", "items": items}), encoding="utf-8")
    (tmp_path / "labels.json").write_text(json.dumps({"labels": labels}), encoding="utf-8")
    rc.ITEMS, rc.LABELS = tmp_path / "items.json", tmp_path / "labels.json"


@pytest.fixture(autouse=True)
def restore_corpus():
    items, labels = rc.ITEMS, rc.LABELS
    yield
    rc.ITEMS, rc.LABELS = items, labels


def test_a_refused_judge_call_is_a_disagreement_and_not_a_dropped_item(tmp_path):
    """The single most dangerous mistake available in this module, tested where it lives.

    **This test previously exercised `diagnostics()` and passed while the defect was
    in `assemble()`.** It was named for the defect, asserted something adjacent to
    it, and shipped a red branch green — the same shape as M02's synth assertions
    that did not assert. It now drives `assemble` and would fail on the real bug.

    Dropping a refused item would compute agreement over exactly the answers the
    guardrail permitted, and delete a fully-blocked axis from the table rather than
    demote it.
    """
    corpus(tmp_path,
           [{"id": "i1", "run": "r", "case_id": "c1", "axis": "groundedness", "split": "held-out"},
            {"id": "i2", "run": "r", "case_id": "c2", "axis": "groundedness", "split": "held-out"}],
           [{"item": "i1", "axis": "groundedness", "split": "held-out", "applicable": True,
             "drafted": 1.0, "final": 1.0},
            {"item": "i2", "axis": "groundedness", "split": "held-out", "applicable": True,
             "drafted": 1.0, "final": 1.0}])
    samples = {("r", "c1"): {n: {"refused_by_gateway": "guardrail",
                                 "axes": {"groundedness": None}} for n in (1, 2, 3)},
               ("r", "c2"): {n: {"axes": {"groundedness": 1.0}} for n in (1, 2, 3)}}

    scorable, _ = rc.assemble("held-out", samples, 3)
    assert len(scorable) == 2, "the refused item was dropped instead of scored"
    refused = next(r for r in scorable if r["case_id"] == "c1")
    assert refused["band"] is None, "a refused call must carry no band"

    stats = judge.agreement([{"axis": r["axis"], "label": r["label"], "band": r["band"]}
                             for r in scorable])
    assert stats["n"] == 2 and stats["exact"] == 1 and stats["raw"] == 0.5, (
        "a refused item must count in the denominator as a disagreement; dropping it "
        "would publish 1.00 here"
    )


def test_an_axis_whose_every_item_was_refused_is_demoted_and_not_deleted(tmp_path):
    """A fully-blocked axis is the one an artifact must be loudest about.

    When the drop bug was live, `groundedness` — all six items refused — never
    reached `demotion()` and simply vanished from the published table. Absent reads
    as "not measured"; the truth is "measured, and the controls refused every call".
    """
    corpus(tmp_path,
           [{"id": "i1", "run": "r", "case_id": "c1", "axis": "groundedness", "split": "held-out"}],
           [{"item": "i1", "axis": "groundedness", "split": "held-out", "applicable": True,
             "drafted": 0.5, "final": 0.5}])
    samples = {("r", "c1"): {n: {"refused_by_gateway": "guardrail",
                                 "axes": {"groundedness": None}} for n in (1, 2, 3)}}
    scorable, _ = rc.assemble("held-out", samples, 3)
    by_axis = {r["axis"] for r in scorable}
    assert "groundedness" in by_axis, "the axis left the table instead of being demoted"


def test_a_duplicate_label_and_sample_is_refused(tmp_path):
    """Last-one-wins would let a re-rolled call replace a refusal with no diff signal."""
    for name in ("a.json", "b.json"):
        (tmp_path / name).write_text(json.dumps({
            "label": "r", "sample": 1, "instrument": INSTRUMENT,
            "cases": {"c1": {"axes": {"groundedness": 1.0}}}}), encoding="utf-8")
    with pytest.raises(SystemExit, match="both carry label"):
        rc.load_samples(tmp_path)


def test_a_missing_sample_names_the_k_flag_and_not_the_labels(tmp_path):
    """The most likely developer error must not accuse a two-key artifact.

    Pointing a k=3 report at a k=1 run used to report that the calibration labels
    disagreed with the harness about whether an item was applicable. Nothing was
    wrong with the labels; `--k` was wrong.
    """
    corpus(tmp_path,
           [{"id": "i1", "run": "r", "case_id": "c1", "axis": "groundedness", "split": "held-out"}],
           [{"item": "i1", "axis": "groundedness", "split": "held-out", "applicable": True,
             "drafted": 1.0, "final": 1.0}])
    samples = {("r", "c1"): {1: {"axes": {"groundedness": 1.0}}}}
    with pytest.raises(SystemExit, match=r"--k 1"):
        rc.assemble("held-out", samples, 3)


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


# --- scoped measurement, and the two published reports ------------------------


def test_assemble_can_be_scoped_to_named_items(tmp_path, monkeypatch):
    """A scoped measurement is the honest shape when an instrument change can reach
    some items and provably not others. Re-rolling the untouched ones produces
    differences indistinguishable from run-to-run variance, and a reader shown two
    full tables reads those as instrument effects (SPEC/03 amendment 7)."""
    items = [{"id": "i-1", "run": "r", "case_id": "c1", "axis": "groundedness", "split": "held-out"},
             {"id": "i-2", "run": "r", "case_id": "c2", "axis": "groundedness", "split": "held-out"}]
    labels = [{"item": "i-1", "axis": "groundedness", "applicable": True,
               "drafted": 1.0, "final": 1.0},
              {"item": "i-2", "axis": "groundedness", "applicable": True,
               "drafted": 0.0, "final": 0.0}]
    monkeypatch.setattr(rc, "ITEMS", tmp_path / "items.json")
    monkeypatch.setattr(rc, "LABELS", tmp_path / "labels.json")
    (tmp_path / "items.json").write_text(json.dumps({"salt": "t", "items": items}), encoding="utf-8")
    (tmp_path / "labels.json").write_text(json.dumps({"labels": labels}), encoding="utf-8")

    samples = {("r", "c1"): {n: {"axes": {"groundedness": 1.0}} for n in (1, 2, 3)},
               ("r", "c2"): {n: {"axes": {"groundedness": 1.0}} for n in (1, 2, 3)}}

    full, _ = rc.assemble("held-out", samples, 3)
    assert sorted(r["item"] for r in full) == ["i-1", "i-2"]

    scoped, _ = rc.assemble("held-out", samples, 3, ("i-1",))
    assert [r["item"] for r in scoped] == ["i-1"]


def test_the_published_reports_are_re_derivable_from_the_committed_output():
    """Both numbers, regenerated from the committed judge output and compared to
    the committed reports field by field.

    This is the property the whole hermetic/model-calling split exists for, and it
    is the one that broke once already: `held-out-report.json` stopped being
    re-derivable when `run_calibration.py` grew an undecided-drop its own docstring
    forbade, and nothing noticed because no test regenerated it."""
    for name, judged, only in (
        ("held-out-report.json", "held-out", ()),
        ("held-out-b-scoped-report.json", "held-out-b-scoped", ("cal-20",)),
    ):
        committed = json.loads((HELD_OUT.parent / name).read_text(encoding="utf-8"))
        fresh = rc.report("held-out", HELD_OUT.parent / judged, 3, only)
        for field in ("axes", "rows", "refusals", "correction_rate", "scope",
                      "instrument", "instrument_name", "dropped_not_applicable"):
            assert fresh[field] == committed[field], f"{name}: {field} is not re-derivable"


def test_the_scoped_report_is_marked_and_the_full_one_is_not():
    """A scoped report must be unmistakable for a split result. `scope` is always
    present so its absence cannot be read as "not scoped" in a file written before
    the field existed."""
    full = json.loads((HELD_OUT.parent / "held-out-report.json").read_text(encoding="utf-8"))
    scoped = json.loads((HELD_OUT.parent / "held-out-b-scoped-report.json").read_text(encoding="utf-8"))
    assert full["scope"] is None
    assert full["instrument_name"] == "A"
    assert scoped["scope"] == {"items": ["cal-20"], "of_split": "held-out"}
    assert scoped["instrument_name"] == "B"
    assert "SCOPED" in rc.render(scoped)
    assert "SCOPED" not in rc.render(full)


def test_instrument_b_serves_the_item_instrument_a_refused():
    """The entire empirical content of instrument B, pinned.

    Under A, `entitlement-012` was refused by classification in 3 of 3 samples —
    the instrument supplied the `SUBJECT_TERM` and the answer under test supplied
    the `ATTRIBUTE_TERM`. Under B the identical answer is served. If this ever
    fails, the reproduction in `9ef9e69` was wrong and the rename was not the
    cause."""
    a_refusals = 0
    for path in sorted(HELD_OUT.glob("m02-tools-1-*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))["cases"]["entitlement-012"]
        if case.get("refused_by_gateway") == "classification":
            a_refusals += 1
    assert a_refusals == 3, "instrument A refused this item in 3 of 3 samples"

    scoped = json.loads(
        (HELD_OUT.parent / "held-out-b-scoped-report.json").read_text(encoding="utf-8"))
    assert scoped["refusals"] == {"model_eligible_calls": 3, "served": 3}
    row = scoped["rows"][0]
    assert row["item"] == "cal-20" and row["case_id"] == "entitlement-012"
    assert row["band"] == row["label"] == 1.0, "the judge's majority agrees with the hand label"


def test_the_pre_registered_bound_on_instrument_b_holds():
    """SPEC/03 amendment 7, written before the three calls, checked after them.

    The bound is arithmetic: A's groundedness row plus the one item B could reach.
    Recomputed here rather than quoted, so editing the amendment to a number that
    was never measured fails."""
    a = json.loads((HELD_OUT.parent / "held-out-report.json").read_text(encoding="utf-8"))
    ground = a["axes"]["groundedness"]
    assert (ground["n"], ground["exact"], ground["undecided"]) == (6, 0, 6)

    raw = round((ground["exact"] + 1) / ground["n"], 4)
    undecided = (ground["undecided"] - 1) / ground["n"]
    assert raw == 0.1667, "pre-registered: groundedness raw at best 1/6"
    assert round(undecided, 2) == 0.83, "pre-registered: undecided at best 5/6"
    assert raw < judge.AGREEMENT_THRESHOLD
    assert undecided > judge.MAX_UNDECIDED_FRACTION

    # Pre-registered: no axis changes status. Every axis demotes under both.
    assert all(v["status"] == "demoted" for v in a["axes"].values())

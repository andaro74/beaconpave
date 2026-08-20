"""
The judge plan, and the one assertion that makes it worth having.

Reproducing the instrument-A held-out pass took 21 hand-built `run_judge.py`
invocations. A plan that merely looks like those 21 commands is a second
description of the run that can drift from the first, so the test that matters
is not "the plan is well-formed" but **"the plan is the run that produced the
published number"** — checked against the committed outputs in
`milestones/M03/judge/held-out/`, not against a fixture written here.

Owning seat: AI Quality.
"""
import collections
import glob
import json
import pathlib

import pytest

from evals import judge, plan

HELD_OUT = pathlib.Path(plan.ROOT) / "milestones" / "M03" / "judge" / "held-out"


def committed_instrument_a() -> dict:
    """What was actually run, read back off disk: label -> (cases, samples, answers)."""
    runs: dict = collections.defaultdict(lambda: {"cases": set(), "samples": set(), "answers": set()})
    for path in sorted(glob.glob(str(HELD_OUT / "*.json"))):
        doc = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        entry = runs[doc["label"]]
        entry["cases"] |= set(doc["cases"])
        entry["samples"].add(doc["sample"])
        entry["answers"].add(doc["answers_file"])
    return runs


def test_the_plan_reproduces_the_run_that_produced_the_published_number():
    """The plan is not merely plausible. It is the plan that was executed.

    If this ever fails, the published held-out agreement number stopped being
    re-derivable from the committed code — which is the same defect the
    `run_calibration.py` undecided-drop had, arriving through a different door."""
    committed = committed_instrument_a()
    assert committed, "no committed instrument-A output to check against"

    planned: dict = collections.defaultdict(lambda: {"cases": set(), "samples": set(), "answers": set()})
    for step in plan.judge_plan("held-out", 3, "unused"):
        entry = planned[step["label"]]
        entry["cases"] |= set(step["cases"])
        entry["samples"].add(step["sample"])
        entry["answers"].add(step["answers"])

    assert set(planned) == set(committed)
    for label in sorted(committed):
        assert planned[label]["cases"] == committed[label]["cases"], label
        assert planned[label]["samples"] == committed[label]["samples"], label
        assert planned[label]["answers"] == committed[label]["answers"], label


def test_the_plan_is_twenty_one_steps_at_k_three():
    """The Service Team's number, pinned. Seven runs by three samples — the count
    that made reproducing the run by hand a twenty-one-command exercise."""
    assert len(plan.judge_plan("held-out", 3, "out")) == 21
    assert len(plan.judge_plan("dev", 3, "out")) == 21


def test_every_run_label_maps_to_a_file_that_exists():
    """Both directions. A label with no mapping would be skipped, and a skipped run
    removes items from an agreement number without removing them from its
    denominator — a quiet improvement in the flattering direction."""
    assert plan.plan_problems() == []


def test_a_missing_mapping_is_refused_before_the_first_call(monkeypatch):
    """`plan_problems` returning a list is only useful if something reads it."""
    monkeypatch.setitem(plan.RUNS, "m00b", "milestones/M00b/no-such-run.json")
    assert plan.plan_problems()
    with pytest.raises(SystemExit) as excinfo:
        plan.judge_plan("held-out", 3, "out")
    assert "no-such-run.json" in str(excinfo.value)


@pytest.mark.parametrize("k", [2, 4])
def test_an_even_k_is_refused(k):
    """The tie rule, met at the point the calls are planned rather than after they
    are spent. At k=2 every disagreement is undecided by construction."""
    with pytest.raises(ValueError, match="even"):
        plan.judge_plan("held-out", k, "out")


def test_an_unknown_split_is_refused():
    """A typo'd split must not silently plan zero calls and report success."""
    with pytest.raises(ValueError, match="unknown split"):
        plan.cases_by_run("heldout")


def test_argv_round_trips_through_run_judges_own_parser():
    """The driver must not invent a second way to phrase an invocation. Parsed by
    the same `argparse` grammar `run_judge.main` uses, so a renamed flag fails here
    rather than at call time with the run half spent."""
    import argparse

    parser = argparse.ArgumentParser(prog="run_judge")
    parser.add_argument("--answers", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--sample", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--only", action="append")

    step = plan.judge_plan("held-out", 3, "out")[0]
    parsed = parser.parse_args(plan.argv_for(step))
    assert parsed.label == step["label"]
    assert parsed.sample == step["sample"]
    assert parsed.only == step["cases"]
    assert parsed.out == step["out"]


# --- resume, and the one thing it must never do -------------------------------


def test_resume_refuses_a_file_written_by_a_different_instrument():
    """The committed instrument-A output, offered to an instrument-B run.

    Not a fixture: these are the files that produced the first published held-out
    number. Reusing one into a B run would put two instruments in one report with
    nothing in the number to say which bands came from which."""
    marks = judge.instrument()
    a_file = HELD_OUT / "m00b-1.json"
    assert a_file.is_file(), "the instrument-A run is the point of this test"
    ok, why = plan.reusable(a_file, marks)
    assert not ok
    assert "user_turn_sha256" in why


def test_resume_accepts_a_file_written_by_this_instrument(tmp_path):
    marks = judge.instrument()
    out = tmp_path / "m00b-1.json"
    out.write_text(json.dumps({"instrument": dict(marks), "cases": {}}), encoding="utf-8")
    assert plan.reusable(out, marks) == (True, "same instrument")


def test_resume_ignores_the_guardrail_version(tmp_path):
    """`run_judge` stamps the enforced guardrail version onto its copy of the marks
    from the audit records. It describes what the call met, not what framed it, and
    it is not part of the freeze — comparing it would refuse every resume across a
    guardrail deploy for no reason."""
    marks = judge.instrument()
    out = tmp_path / "m00b-1.json"
    out.write_text(json.dumps({"instrument": dict(marks, guardrail_version="2")}), encoding="utf-8")
    assert plan.reusable(out, marks)[0]


def test_resume_refuses_an_unreadable_file(tmp_path):
    """A truncated write from an interrupted run is not a result."""
    out = tmp_path / "m00b-1.json"
    out.write_text("{not json", encoding="utf-8")
    ok, why = plan.reusable(out, judge.instrument())
    assert not ok
    assert "unreadable" in why


def test_resume_refuses_a_file_with_no_instrument_at_all(tmp_path):
    """An output predating the instrument record is not silently trusted."""
    out = tmp_path / "m00b-1.json"
    out.write_text(json.dumps({"cases": {}}), encoding="utf-8")
    assert not plan.reusable(out, judge.instrument())[0]

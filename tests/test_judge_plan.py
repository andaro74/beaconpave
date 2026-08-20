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
    """The driver must not invent a second way to phrase an invocation.

    This test used to hand-rebuild the parser, which made it a **third** phrasing:
    rename `--only` to `--case` in `run_judge.main` and it still passed, while
    `run_split` died on step one with the plan intact and the flag wrong. A test
    named for a defect that cannot catch it is this branch's recurring shape. The
    grammar now lives in `evals/plan.py`, hermetic, and `run_judge.main` builds its
    parser from the same function this parses with."""
    step = plan.judge_plan("held-out", 3, "out")[0]
    parsed = plan.judge_parser().parse_args(plan.argv_for(step))
    assert parsed.answers == step["answers"]
    assert parsed.label == step["label"]
    assert parsed.sample == step["sample"]
    assert parsed.only == step["cases"]
    assert parsed.out == step["out"]


def test_run_judge_builds_its_parser_from_the_shared_grammar():
    """The half of the round-trip a hermetic test cannot reach by importing.

    `run_judge` imports boto3 and `tests/` is a hermetic root, so this reads the
    source rather than the module. A source check is weaker than an import, and it
    is what makes the claim above true rather than merely stated."""
    source = (pathlib.Path(plan.ROOT) / "services" / "highlights-agent" / "run_judge.py"
              ).read_text(encoding="utf-8")
    assert "plan.judge_parser(" in source, (
        "run_judge.main no longer builds its parser from evals.plan.judge_parser, so "
        "test_argv_round_trips_through_run_judges_own_parser is checking a grammar "
        "nothing uses")
    assert "add_argument(\"--only\"" not in source, (
        "run_judge declares its own --only again; there are two grammars")


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


# --- what a run costs, and what must stop it before it starts -----------------


def test_spend_reproduces_the_published_model_eligible_call_count():
    """The header said "21 invocations"; the run made 48 model calls.

    Checked against the committed report rather than against a number typed here,
    so the arithmetic is pinned to the run it describes."""
    report = json.loads((HELD_OUT.parent / "held-out-report.json").read_text(encoding="utf-8"))
    cost = plan.spend(plan.judge_plan("held-out", 3, "unused"))
    assert cost["model_eligible_calls"] == report["refusals"]["model_eligible_calls"]
    assert cost["case_judgements"] == cost["model_eligible_calls"] + cost["not_applicable"]
    assert cost["invocations"] == 21


def test_a_dev_file_in_a_held_out_directory_is_a_stray():
    """Six of seven run labels appear in both splits and the filename carries only
    the label, so `m01-1.json` survives from a dev run into a held-out directory.
    `run_calibration.refusal_census` globs the whole directory, so a same-instrument
    leftover inflates `model_eligible_calls` and every refusal percentage in the
    published report. `instruments()` catches cross-instrument leftovers and is
    blind to this one."""
    held_out_plan = plan.judge_plan("held-out", 3, "unused")
    assert plan.strays(str(HELD_OUT), held_out_plan) == []
    assert "m01-1.json" in plan.strays(str(HELD_OUT.parent / "dev"), held_out_plan)


def test_the_committed_instrument_a_directory_is_refused_as_an_output_target():
    """The one failure here that destroys evidence.

    Pointed at `milestones/M03/judge/held-out/` under instrument B, the driver
    would overwrite all 21 files the first published number rests on — and
    `--resume` is no protection, because it correctly decides to re-run them and
    re-running writes over them."""
    foreign = plan.foreign_instrument(str(HELD_OUT), judge.instrument())
    assert len(foreign) == 21, "all 21 instrument-A files must read as foreign under B"


def test_a_directory_written_by_the_current_instrument_is_not_foreign(tmp_path):
    """The other half. Refusing every populated directory would make `--resume`
    useless, so the check has to pass for a run this instrument is continuing."""
    marks = judge.instrument()
    (tmp_path / "m00b-1.json").write_text(
        json.dumps({"instrument": dict(marks, guardrail_version="2")}), encoding="utf-8")
    assert plan.foreign_instrument(str(tmp_path), marks) == []
    assert plan.foreign_instrument(str(tmp_path / "nope"), marks) == []


def test_guardrail_versions_are_collected_across_a_directory(tmp_path):
    """`run_judge` exits if one invocation spans two versions and `run_calibration`
    exits if a directory does. `reusable` sat between them permitting exactly that,
    so the operator spent the remaining calls and then found the directory rejected
    as "the judge moved mid-run" — with `--resume` unable to repair it."""
    marks = judge.instrument()
    for name, version in (("a-1.json", "1"), ("a-2.json", "2"), ("a-3.json", "2")):
        (tmp_path / name).write_text(
            json.dumps({"instrument": dict(marks, guardrail_version=version)}), encoding="utf-8")
    assert plan.guardrail_versions(str(tmp_path)) == ["1", "2"]
    assert plan.guardrail_versions(str(tmp_path / "nope")) == []

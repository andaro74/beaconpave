"""
Which judge calls a split needs, derived rather than typed out.

Reproducing the instrument-A held-out pass took **21 hand-built `run_judge.py`
invocations** — seven runs by three samples — each one a `--label`, an
`--answers` path, a `--sample` and a list of `--only` case ids assembled by
reading `items.json` and translating a run name into a file path by hand. Every
input to those 21 commands was already committed. A published number that a
stranger can only re-derive by retyping twenty-one commands correctly is
re-derivable in the same sense that a proof is checkable: in principle.

So the plan is a **pure function of `items.json`** and lives here, in the
hermetic half, where a test can assert it reproduces what was actually run.
`tests/test_judge_plan.py` does exactly that against the committed
`milestones/M03/judge/held-out/` outputs — the plan is not merely plausible, it
is the plan that produced the published number.

Nothing here calls a model or touches AWS. The driver that executes the plan is
`services/highlights-agent/run_split.py`, beside the other model-calling runners
and outside `make check`.

Owning seat: AI Quality.
"""
from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS = ROOT / "quality" / "judge" / "calibration" / "items.json"

#: Which agent run each calibration `run` label names.
#:
#: Explicit rather than derived from the label by string surgery. `m00b` and `m01`
#: live at `milestones/MNN/goldens-run.json` and the M02 arms live under
#: `milestones/M02/runs/`, so any rule general enough to cover both would be a rule
#: fitted to two exceptions. `plan_problems()` checks this mapping against
#: `items.json` in both directions, so a new run label fails loudly instead of
#: being skipped silently — which is the failure that matters, since a skipped run
#: removes items from an agreement number without removing them from its
#: denominator.
RUNS = {
    "m00b": "milestones/M00b/goldens-run.json",
    "m01": "milestones/M01/goldens-run.json",
    "m02-control-1": "milestones/M02/runs/m02-control-1.json",
    "m02-control-2": "milestones/M02/runs/m02-control-2.json",
    "m02-control-3": "milestones/M02/runs/m02-control-3.json",
    "m02-tools-1": "milestones/M02/runs/m02-tools-1.json",
    "m02-tools-2": "milestones/M02/runs/m02-tools-2.json",
    "m02-tools-3": "milestones/M02/runs/m02-tools-3.json",
}

SPLITS = ("dev", "held-out")


def items() -> list[dict]:
    return json.loads(ITEMS.read_text(encoding="utf-8"))["items"]


def cases_by_run(split: str) -> dict[str, list[str]]:
    """The distinct case ids each run contributes to `split`.

    A calibration item is a (run, case, axis) triple, so one case can carry
    several items. The judge is asked for a case's whole axis list and the item
    list decides which of those bands enter the agreement figure — scoring only
    the item's axis would show the judge a different question than the one the
    rubric defines, for no gain."""
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}; expected one of {SPLITS}")
    grouped: dict[str, set] = {}
    for item in items():
        if item["split"] == split:
            grouped.setdefault(item["run"], set()).add(item["case_id"])
    return {run: sorted(cases) for run, cases in sorted(grouped.items())}


def plan_problems() -> list[str]:
    """Everything that would make the plan quietly incomplete.

    Returned rather than raised so a test can name all of them at once, and so the
    driver can refuse the whole plan before spending the first call rather than
    failing on run six of seven with five files already written."""
    problems = []
    labelled = {item["run"] for item in items()}
    for run in sorted(labelled - set(RUNS)):
        problems.append(f"{run!r} is in items.json and has no entry in RUNS")
    for run in sorted(set(RUNS) - labelled):
        problems.append(f"{run!r} is in RUNS and no calibration item names it")
    for run in sorted(labelled & set(RUNS)):
        if not (ROOT / RUNS[run]).is_file():
            problems.append(f"{run!r} maps to {RUNS[run]}, which does not exist")
    return problems


def judge_plan(split: str, k: int, outdir: str) -> list[dict]:
    """Every `run_judge` invocation `split` needs, in a deterministic order.

    `k` samples per run, because a single judge sample is not a comparator for the
    same reason a single agent sample is not one. An even `k` is refused here as
    well as in `emit_verdict`: `majority_band` needs a strict majority, and at
    `k = 2` a disagreement is undecided by construction, which spends two calls to
    learn nothing."""
    if k < 1:
        raise ValueError(f"k must be at least 1, not {k}")
    if k % 2 == 0:
        raise ValueError(
            f"k={k} is even. A strict majority is unreachable on a split vote, so every "
            "disagreement would land as undecided by construction. Use an odd k.")
    problems = plan_problems()
    if problems:
        raise SystemExit("error: the judge plan is incomplete:\n  " + "\n  ".join(problems))

    out = pathlib.Path(outdir)
    return [
        {
            "label": run,
            "answers": RUNS[run],
            "sample": sample,
            "cases": cases,
            "out": str((out / f"{run}-{sample}.json").as_posix()),
        }
        for run, cases in cases_by_run(split).items()
        for sample in range(1, k + 1)
    ]


def reusable(out: pathlib.Path, marks: dict, step: dict | None = None) -> tuple[bool, str]:
    """Whether an output file already on disk may stand in for running a step again.

    Resuming is worth having — a plan is 21 model calls and stopping on step
    nineteen should not re-spend eighteen. Resuming *across instruments* is the one
    thing it must never do: an instrument-A file reused into an instrument-B run
    produces a single report containing two instruments, with nothing in the number
    to say which bands came from which. That is the confusion `user_turn_sha256`
    was added to make impossible, so the check has to be able to see it.

    `guardrail_version` is ignored. `run_judge` stamps it onto its copy of the
    marks from the audit records the call actually produced; it describes the
    enforcement the call met rather than the instrument that framed it, and it is
    not part of the freeze. Comparing it would refuse every resume across a
    guardrail deploy for no reason.

    Returns a reason either way, because "skipped" and "re-ran" have to be
    distinguishable in the driver's output. A resume that silently reuses is how a
    stale file survives into a published number."""
    if not out.is_file():
        return False, "not written yet"
    try:
        doc = json.loads(out.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"unreadable ({exc})"
    was = {k: v for k, v in (doc.get("instrument") or {}).items() if k != "guardrail_version"}
    if was != marks:
        moved = sorted(k for k in set(was) | set(marks) if was.get(k) != marks.get(k))
        return False, f"a different instrument wrote it (differs on {', '.join(moved)})"
    # `run_judge` writes its output file and THEN returns 1 on a harness failure, so a
    # throttled step leaves a complete, well-formed, current-instrument file on disk
    # carrying `harness_error` where its bands should be. Comparing only the
    # instrument accepted it — which means the driver's own recovery instruction
    # ("re-run with --resume") skipped precisely the step it was telling the operator
    # to recover, then reported success. `run_calibration` refuses the directory
    # afterwards, so nothing false is published; the operator simply learns their
    # recovery did not recover once the other twenty steps are spent.
    if doc.get("harness_failures"):
        failed = ", ".join(doc["harness_failures"])
        return False, f"the run that wrote it failed on {failed}"
    if any("harness_error" in case for case in (doc.get("cases") or {}).values()):
        return False, "it carries a harness error in place of bands"
    if step is not None:
        if doc.get("label") != step["label"] or doc.get("sample") != step["sample"]:
            return False, (f"it holds {doc.get('label')} sample {doc.get('sample')}, "
                           f"not {step['label']} sample {step['sample']}")
        missing = sorted(set(step["cases"]) - set(doc.get("cases") or {}))
        if missing:
            return False, f"it is missing {', '.join(missing)}"
    return True, "same instrument"


def spend(steps: list[dict]) -> dict:
    """What executing `steps` will actually cost, decided offline.

    The driver reported "21 judge invocations" and an operator reads that as 21
    model calls. It is 57 case judgements, of which the instrument-A run shows 48
    reached the model — `not_applicable` settles a gateway refusal, an `unparsed`
    turn and a missing answer object deterministically before any call. The header
    understated the spend by more than a factor of two, in a tool whose stated
    purpose is that a stranger can find out what reproducing a number costs.

    Every input is committed, so this is arithmetic rather than an estimate."""
    from evals import judge

    judgements = sum(len(step["cases"]) for step in steps)
    eligible = skipped = 0
    cache: dict = {}
    for step in steps:
        path = ROOT / step["answers"]
        if step["answers"] not in cache:
            cache[step["answers"]] = json.loads(path.read_text(encoding="utf-8"))
        answers = cache[step["answers"]]
        for case_id in step["cases"]:
            answer = (answers.get(case_id) or {}).get("answer")
            if judge.not_applicable(answer):
                skipped += 1
            else:
                eligible += 1
    return {"invocations": len(steps), "case_judgements": judgements,
            "model_eligible_calls": eligible, "not_applicable": skipped}


def strays(outdir: str, steps: list[dict]) -> list[str]:
    """Files in `outdir` that no step in this plan will write.

    Output names are `{run}-{sample}.json` and six of seven run labels appear in
    both splits, so `m01-1.json` from a dev run survives into a held-out directory
    and `run_calibration`'s `refusal_census` globs the whole directory rather than
    filtering by split — a leftover from the same instrument inflates
    `model_eligible_calls` and every refusal percentage in the published report.
    `instruments()` catches a cross-instrument leftover and cannot catch this one."""
    planned = {pathlib.Path(step["out"]).name for step in steps}
    directory = pathlib.Path(outdir)
    if not directory.is_dir():
        return []
    return sorted(f.name for f in directory.glob("*.json") if f.name not in planned)


def foreign_instrument(outdir: str, marks: dict) -> list[str]:
    """Files in `outdir` written by an instrument other than the current one.

    A new instrument gets a new directory. `milestones/M03/judge/held-out/` holds
    the instrument-A output that the first published agreement number rests on and
    that `tests/test_judge_plan.py` asserts the plan against; pointed at it under
    instrument B, the driver would have overwritten all 21 files. `--resume` is no
    protection — it correctly decides to re-run them, and re-running writes over
    them. Git would notice afterwards. The 48 spent calls would not come back.

    Refusing outright rather than warning: this is the only failure here that
    destroys evidence, and the recovery for a wrong `--outdir` is to type a
    different one."""
    directory = pathlib.Path(outdir)
    if not directory.is_dir():
        return []
    from evals import judge

    keys = judge.freeze_keys()
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        was = doc.get("instrument")
        if was and any(was.get(k) != marks.get(k) for k in keys):
            out.append(path.name)
    return out


def guardrail_versions(outdir: str) -> list[str]:
    """The distinct enforced guardrail versions recorded across a directory.

    `run_judge` exits if one invocation spans two versions; `run_calibration`
    exits if a directory does. Between them sat `reusable`, which permitted a
    resume across a guardrail deploy — so the operator spent the remaining calls
    and then found the directory rejected as "the judge moved mid-run", with
    `--resume` unable to repair it because it would go on reusing the old-version
    files forever. Three components, three answers to one question. This is the
    third answering the same way as the other two, before the calls rather than
    after."""
    seen: list[str] = []
    directory = pathlib.Path(outdir)
    if not directory.is_dir():
        return []
    for path in sorted(directory.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        version = (doc.get("instrument") or {}).get("guardrail_version")
        if version and str(version) not in seen:
            seen.append(str(version))
    return seen


def judge_parser(prog: str = "run_judge", description: str | None = None):
    """The one grammar for a judge invocation.

    `run_judge.main` builds its parser from this, `argv_for` emits arguments for
    it, and `tests/test_judge_plan.py` round-trips one against the other. The test
    used to hand-rebuild the parser instead — which made it a *third* phrasing that
    could disagree with the other two, and it would have passed with `--only`
    renamed while `run_split` died on step one. It could not import the real one:
    `run_judge` imports boto3 and `tests/` is a hermetic root. Moving the grammar
    here is what lets the check be real, and it is the same argument that moved the
    user-turn template into a file."""
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument("--answers", required=True, help="an agent run to judge")
    parser.add_argument("--label", required=True,
                        help="which run these answers are, e.g. m02-tools-1")
    parser.add_argument("--sample", type=int, required=True, help="which judge sample, 1..k_judge")
    parser.add_argument("--out", required=True)
    parser.add_argument("--only", action="append", help="judge only these case ids; repeatable")
    return parser


def argv_for(step: dict) -> list[str]:
    """One plan step as the argument list `run_judge.main` already takes.

    The driver builds no command line of its own. A second way to phrase a judge
    invocation is a second thing that can disagree with the first."""
    argv = ["--answers", step["answers"], "--label", step["label"],
            "--sample", str(step["sample"]), "--out", step["out"]]
    for case_id in step["cases"]:
        argv += ["--only", case_id]
    return argv

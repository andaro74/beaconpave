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


def reusable(out: pathlib.Path, marks: dict) -> tuple[bool, str]:
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
    return True, "same instrument"


def argv_for(step: dict) -> list[str]:
    """One plan step as the argument list `run_judge.main` already takes.

    The driver builds no command line of its own. A second way to phrase a judge
    invocation is a second thing that can disagree with the first."""
    argv = ["--answers", step["answers"], "--label", step["label"],
            "--sample", str(step["sample"]), "--out", step["out"]]
    for case_id in step["cases"]:
        argv += ["--only", case_id]
    return argv

"""
`python services/highlights-agent/run_split.py --split held-out` — one calibration
split, one command.

The instrument-A held-out pass was 21 hand-built `run_judge.py` invocations, each
carrying a label, an answers path, a sample number and a hand-assembled list of
`--only` case ids. Every input to all 21 was already committed in
`quality/judge/calibration/items.json`. This driver reads the plan out of
`evals/plan.py` — the hermetic half, where `tests/test_judge_plan.py` asserts the
plan reproduces the run that produced the published number — and executes it.

**It invents nothing.** `run_judge.main` builds its parser from
`plan.judge_parser`, and this driver hands it the list `plan.argv_for` produces.
One grammar, not two that can drift.

**It says what it will spend before it spends it.** 21 invocations is 57 case
judgements and 48 model-eligible calls; `not_applicable` settles the other nine
offline. Reporting the invocation count alone understated the cost by more than
a factor of two.

**It refuses the whole plan before the first call.** A run label with no answers
file, a stray output file from the other split, or a directory recording two
guardrail versions all stop the run at step zero rather than at step nineteen
with the calls spent.

**`--resume` will not mix instruments, and will not reuse a damaged step.**
`run_judge` writes its output file and *then* returns 1 on a harness failure, so a
throttled step leaves a complete, current-instrument file on disk with
`harness_error` where its bands should be. Reusing it would mean this driver's own
recovery instruction skipped exactly the step it told the operator to recover.

  python services/highlights-agent/run_split.py \\
      --split held-out --k 3 --outdir milestones/M03/judge/held-out-b

Reproducing a published run means matching its `k`. The committed held-out pass is
`k=3`; the committed dev pass is `k=1`. `--k` defaults to 3, so reproducing dev
needs `--k 1` said out loud — the k that reproduces a number is a property of the
run, and `items.json` does not carry it.

Owning seat: AI Quality (the judge) · Platform Engineering (the gateway path) ·
Service Team (this driver exists because reproducing a run by hand is a
developer-experience defect, not merely an inconvenience).
"""
from __future__ import annotations

import argparse
import pathlib
import sys

# Script directory first, then the repo root, so the root's `evals` package wins
# over the namespace portion at `services/highlights-agent/evals/`. The other
# runners insert only one of the two; getting the order backwards worked only
# because `evals/__init__.py` happens to exist.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from evals import judge, plan  # noqa: E402

RUN_JUDGE = "python services/highlights-agent/run_judge.py"


def preflight(args, steps: list[dict]) -> list[str]:
    """Everything that should stop the run before a call is spent.

    Returned as a list rather than raised one at a time so an operator fixes all
    of it in one pass instead of discovering the next problem after the next
    twenty minutes."""
    problems = []
    stray = plan.strays(args.outdir, steps)
    if stray:
        problems.append(
            f"{args.outdir} holds {len(stray)} file(s) this plan will not write: "
            f"{', '.join(stray[:6])}{' ...' if len(stray) > 6 else ''}. Output names are "
            "{run}-{sample}.json and most run labels appear in both splits, so a dev file "
            "survives into a held-out directory and inflates every refusal percentage in "
            "the report. Use an empty directory, or delete the strays.")
    foreign = plan.foreign_instrument(args.outdir, judge.instrument())
    if foreign:
        problems.append(
            f"{args.outdir} holds {len(foreign)} file(s) written by a different instrument "
            f"({', '.join(foreign[:4])}{' ...' if len(foreign) > 4 else ''}). A new instrument "
            "gets a new directory: writing here would overwrite the committed evidence a "
            "published number rests on, and --resume is no protection because re-running a "
            "step writes over it. Choose an unused --outdir.")
    versions = plan.guardrail_versions(args.outdir)
    if len(versions) > 1:
        problems.append(
            f"{args.outdir} already records {len(versions)} guardrail versions "
            f"({', '.join(versions)}). Bands produced under different enforced policies are "
            "not one measurement, and --resume cannot repair it: re-run the split into an "
            "empty directory.")
    return problems


def resolve(args, steps: list[dict], marks: dict) -> tuple[list[dict], list[tuple]]:
    """Split the plan into what will run and what will be reused, before running.

    Decided up front so the operator sees "21 of 21 will be re-run" in one line
    rather than learning it from twenty-one interleaved messages with calls already
    going out."""
    todo, reuse = [], []
    for step in steps:
        if args.resume:
            ok, why = plan.reusable(pathlib.Path(step["out"]), marks, step)
            if ok:
                reuse.append((step, why))
                continue
            if pathlib.Path(step["out"]).is_file():
                todo.append(dict(step, _rerun_because=why))
                continue
        todo.append(step)
    return todo, reuse


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_split", description=__doc__)
    p.add_argument("--split", required=True, choices=plan.SPLITS)
    p.add_argument("--k", type=int, default=3,
                   help="judge samples per run (odd). held-out was run at 3, dev at 1")
    p.add_argument("--outdir", required=True)
    p.add_argument("--resume", action="store_true",
                   help="reuse steps already written by this same instrument")
    p.add_argument("--dryrun", action="store_true",
                   help="print the plan and spend nothing; honours --resume")
    args = p.parse_args(argv)

    # A bad `--k` is operator input, not a programming error, and this driver exists
    # because the hand-built alternative was hostile. A traceback for an even k would
    # be the same defect in a smaller place.
    try:
        steps = plan.judge_plan(args.split, args.k, args.outdir)
    except ValueError as exc:
        p.error(str(exc))
    marks = judge.instrument()
    cost = plan.spend(steps)

    print(f"plan: {args.split} at k={args.k} - {cost['invocations']} invocations across "
          f"{len({s['label'] for s in steps})} runs")
    print(f"spend: {cost['case_judgements']} case judgements, "
          f"{cost['model_eligible_calls']} model-eligible calls "
          f"({cost['not_applicable']} settled offline as not-applicable)")
    print(f"instrument: prompt {marks['prompt_sha256'][:12]} "
          f"user-turn {marks['user_turn_sha256'][:12]} frozen={judge.is_frozen()}")

    problems = preflight(args, steps)
    if problems:
        print("\nrefusing the plan before spending anything:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2

    todo, reuse = resolve(args, steps, marks)
    if args.resume:
        rerun = [s for s in todo if "_rerun_because" in s]
        print(f"resume: {len(reuse)} reusable, {len(todo)} to run "
              f"({len(rerun)} already on disk and being re-run)")
        for why in sorted({s["_rerun_because"] for s in rerun}):
            print(f"  re-running because {why}")
        if any("different instrument" in s["_rerun_because"] for s in rerun):
            print("  quality/judge/frozen.json records each instrument side by side; "
                  "diff them there to see what moved.")
    if todo:
        spend_now = plan.spend([{k: v for k, v in s.items() if k != "_rerun_because"}
                                for s in todo])
        print(f"about to spend: {spend_now['model_eligible_calls']} model-eligible calls\n")
    else:
        print("nothing to run\n")

    if args.dryrun:
        for step in todo:
            argv_text = " ".join(plan.argv_for(step))
            print(f"  {RUN_JUDGE} {argv_text}")
        print(f"\ndryrun: {len(todo)} invocation(s) planned, no model was called")
        return 0

    # Imported here, not at module scope: `run_judge` imports boto3, which lives in
    # the `baseline` extra rather than in `dev`, so a module-scope import made
    # `--dryrun` - advertised as spending nothing - die on a fresh clone before it
    # printed a line.
    import run_judge

    pathlib.Path(args.outdir).mkdir(parents=True, exist_ok=True)
    ran = 0
    for index, step in enumerate(todo, 1):
        head = f"[{index}/{len(todo)}] {step['label']} sample {step['sample']}"
        print(f"{head}: {len(step['cases'])} case(s) -> {pathlib.Path(step['out']).name}")
        try:
            code = run_judge.main(plan.argv_for(step))
        except SystemExit as exc:
            # `run_judge` exits rather than returning on three paths: labels not
            # disposed, the held-out freeze guard, and one invocation spanning two
            # guardrail versions. None was caught, so the driver's whole
            # stop-and-explain contract did not cover them - and the guardrail-version
            # case fires AFTER its calls are spent and BEFORE the file is written, so
            # the operator lost the calls and got a bare traceback.
            code = exc.code if isinstance(exc.code, int) else 1
            print(f"\n{exc}", file=sys.stderr)
        if code != 0:
            print(f"\nstopped at step {index} of {len(todo)}: run_judge exited {code}. "
                  f"{ran} step(s) completed. Fix the cause, then re-run the same command "
                  "with --resume: the failed step is re-run rather than reused, because "
                  "run_judge writes its file before it reports the failure.",
                  file=sys.stderr)
            return code
        ran += 1

    print(f"\n{args.split}: {ran} invocation(s) run, {len(reuse)} reused, "
          f"{len(steps)} in the plan -> {args.outdir}")
    print("next: python -m evals.run_calibration "
          f"--judged {args.outdir} --split {args.split} --k {args.k} "
          f"--out {args.outdir}/report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

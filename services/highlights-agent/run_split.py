"""
`python services/highlights-agent/run_split.py --split held-out` — one calibration
split, one command.

The instrument-A held-out pass was 21 hand-built `run_judge.py` invocations, each
carrying a label, an answers path, a sample number and a hand-assembled list of
`--only` case ids. Every input to all 21 was already committed in
`quality/judge/calibration/items.json`. This driver reads the plan out of
`evals/plan.py` — the hermetic half, where `tests/test_judge_plan.py` asserts the
plan reproduces the run that produced the published number — and executes it.

**It invents nothing.** It builds no command line of its own and calls
`run_judge.main` with the argument list `plan.argv_for` produces, so there is one
grammar for a judge invocation rather than two that can drift apart.

**It refuses the whole plan before spending the first call.** A run label with no
answers file would otherwise be skipped on step six of seven, with five files
already written and an agreement number quietly missing its items but not its
denominator.

**`--resume` will not mix instruments.** An output file already on disk is reused
only if its recorded `instrument` matches the instrument in the tree right now.
This is the whole reason `user_turn_sha256` exists: resuming an instrument-A file
into an instrument-B run would produce one report with two instruments in it and
no way to tell from the number which bands came from which.

  python services/highlights-agent/run_split.py \
      --split held-out --k 3 --outdir milestones/M03/judge/held-out-b

Owning seat: AI Quality (the judge) · Platform Engineering (the gateway path) ·
Service Team (this driver exists because reproducing a run by hand is a
developer-experience defect, not only an inconvenience).
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import run_judge  # noqa: E402  (sibling module, same as the other runners)

from evals import judge, plan  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_split", description=__doc__)
    p.add_argument("--split", required=True, choices=plan.SPLITS)
    p.add_argument("--k", type=int, default=3, help="judge samples per run (odd)")
    p.add_argument("--outdir", required=True)
    p.add_argument("--resume", action="store_true",
                   help="skip steps already written by this same instrument")
    p.add_argument("--dryrun", action="store_true",
                   help="print the plan and spend nothing")
    args = p.parse_args(argv)

    # A bad `--k` is operator input, not a programming error, and this driver is
    # here because the hand-built alternative was hostile. A traceback for an even
    # k would be the same defect in a smaller place.
    try:
        steps = plan.judge_plan(args.split, args.k, args.outdir)
    except ValueError as exc:
        p.error(str(exc))
    marks = judge.instrument()

    print(f"plan: {args.split} at k={args.k} — {len(steps)} judge invocations "
          f"across {len({s['label'] for s in steps})} runs")
    print(f"instrument: prompt {marks['prompt_sha256'][:12]} "
          f"user-turn {marks['user_turn_sha256'][:12]} frozen={judge.is_frozen()}\n")

    if args.dryrun:
        for step in steps:
            print(f"  run_judge.py {' '.join(plan.argv_for(step))}")
        print(f"\ndryrun: {len(steps)} invocations planned, no model was called")
        return 0

    pathlib.Path(args.outdir).mkdir(parents=True, exist_ok=True)
    ran = skipped = 0
    for index, step in enumerate(steps, 1):
        head = f"[{index}/{len(steps)}] {step['label']} sample {step['sample']}"
        out = pathlib.Path(step["out"])
        if args.resume:
            ok, why = plan.reusable(out, marks)
            if ok:
                print(f"{head}: reusing {out.name} ({why})")
                skipped += 1
                continue
            if out.is_file():
                # Loud. Silently overwriting is fine; silently *reusing* the wrong
                # instrument is what this branch exists to make impossible, and the
                # operator should see which one they are getting.
                print(f"{head}: re-running — {why}")
        print(f"{head}: {len(step['cases'])} case(s) -> {out.name}")
        code = run_judge.main(plan.argv_for(step))
        if code != 0:
            # A run that half-happened must not be mistaken for a run that
            # happened. Stop with the calls already spent still on disk, and say
            # how to pick up rather than making the operator rebuild the plan.
            print(f"\nstopped at step {index} of {len(steps)}: run_judge exited {code}. "
                  f"{ran} step(s) written. Fix the cause, then re-run with --resume "
                  "to continue without re-spending what is already on disk.",
                  file=sys.stderr)
            return code
        ran += 1

    print(f"\n{args.split}: {ran} invocation(s) run, {skipped} reused, "
          f"{len(steps)} in the plan -> {args.outdir}")
    print("next: python evals/run_calibration.py --judged "
          f"{args.outdir} --split {args.split} --k {args.k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

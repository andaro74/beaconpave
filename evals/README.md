# Evals

Two suites, one history.

- `run_evals.py` — golden set (L2/L3): deterministic asserts + calibrated judge
- `run_adversarial.py` — probe corpus (L5): pass = blocked or denied AND logged

The judge is the third thing here and the least discoverable, so it is named up
front: `judge.py` is its hermetic half, `plan.py` derives which calls a
calibration split needs, and `services/highlights-agent/run_split.py` executes
them through the gateway.

## Reproducing a published agreement number

The whole point of committing raw judge output is that a stranger can re-derive
every published figure. Two commands:

```bash
# 1. the model-calling half. --dryrun prints the plan and the exact call count
python services/highlights-agent/run_split.py     --split held-out --k 3 --outdir <a new, empty directory> --dryrun

# 2. the hermetic half — no AWS account needed if the output is already committed
python -m evals.run_calibration     --judged milestones/M03/judge/held-out --split held-out --k 3
```

Step 2 alone re-derives `milestones/M03/judge/held-out-report.json` from the
committed output. Step 1 is only needed to produce output that does not exist yet.

Three things that will stop you, each on purpose:

- **`--k` must match the run you are reproducing.** held-out was run at `k=3`,
  dev at `k=1`. `items.json` does not record it, so it is the one input still
  supplied by hand.
- **A new instrument needs a new `--outdir`.** The driver refuses to write into a
  directory holding another instrument's output, because that is the committed
  evidence a published number rests on. `quality/judge/frozen.json` records every
  instrument side by side; diff them there.
- **`--resume` re-runs a step that failed** rather than reusing it. `run_judge`
  writes its file *before* it reports a harness failure, so the file on disk looks
  complete and is not.


## Recording

```bash
python evals/run_evals.py --record          # appends to history/
python evals/run_evals.py --target baseline # score the m00b control
```

`history/` is **append-only JSON keyed by git SHA + suite**. Never edit an
entry; a wrong entry gets a superseding one with `supersedes: <sha>`. This is
what makes the progression table auditable rather than aspirational.

## Rules that keep this honest

- Never edit a golden case to make a run pass. Fix cases in their own PR with
  reasoning, reviewed by AI Quality.
- Never reset a baseline to clear a regression without the AI Quality key (G9).
- Keep 5–10% of cases at or near failure (headroom). A suite at 100% can only
  report regressions; improvements become invisible.
- Judges below the published agreement threshold are demoted to advisory
  automatically and cannot block merges.
- Budgets are per-model, not per-case — otherwise a better, pricier candidate
  fails on cost before its quality is ever graded.

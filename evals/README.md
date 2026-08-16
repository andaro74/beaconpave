# Evals

Two suites, one history.

- `run_evals.py` — golden set (L2/L3): deterministic asserts + calibrated judge
- `run_adversarial.py` — probe corpus (L5): pass = blocked or denied AND logged

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

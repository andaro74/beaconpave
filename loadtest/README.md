# loadtest

k6 profiles. Two uses:

1. **L4 in the gate** — a short smoke keeping p95 and cost budgets honest per PR.
2. **Game-day soak (M09)** — replays the capacity plan's spike shape at ×1.5:
   mass join at "kickoff," halftime churn (leave/rejoin wave), late-game surge.

Both emit the standard verdict record (`quality/verdicts/schema.json`), which is
why a load result and an eval result land on the same dashboard.

Profiles are derived from event telemetry, not invented: rehearse the worst
observed hour, not the average one.

# M02 run evidence

Every run of both arms, committed as-run. Nothing here is edited, and a discarded
run stays beside its replacement — SPEC/02's INFRA rule exists so that "we re-ran
it" is a thing a reader can check rather than a thing they are told.

Scored with `python -m evals.run_evals --answers <file> --target highlights-agent`.
Summarised across k with repeated `--answers` plus `--arm`.

## Control arm — the frozen M01 arm, re-measured 2026-08-19

`services/highlights-agent/run_via_gateway.py`, unchanged since M01: the whole
catalog inlined, no tools. Same deployed gateway, same pinned guardrail version 1,
same day.

| sample | passed | guardrail refusals |
|---|---|---|
| 1 | 18/25 | 5 |
| 2 | 16/25 | 6 |
| 3 | 14/25 | 8 |
| **majority (k=3)** | **17/25** | — |
| pooled | 48/75 = 0.6400 (16.0/25) | — |

**This is why 19/25 was disqualified as the comparator.** SPEC/02 rejected M01's
recorded row on the grounds that it was n=1. Three samples of the *identical*
system, on one day, span **14 to 18** — a four-point range with no system change
of any kind. A single sample of this arm could have been read as anything from a
five-point regression to a one-point improvement against M01's own number.

**The guardrail refusal count is a finding in its own right, and it is not M02's.**
SPEC/01 pre-registered 0–2 refusals as expected and **≥3 as a miscalibrated
guardrail**. The control arm produced 5, 6 and 8, every one of them
`TOPIC:entitlement-circumvention`. Four cases refuse in all three samples
(`blackout-001`, `-006`, `-007`, `-009`); the rest drift in and out. This is the
ungoverned-to-governed cost M01 measured once and under-sampled, and it belongs to
the guardrail configuration rather than to the tool plane.

**Watch for a monotone pattern.** Refusals rose 5 → 6 → 8 across three consecutive
runs. With n=3 that is well inside coincidence, but if the tools arm shows the
same monotone rise in run order it is a property of the service on the day and not
of either system, and the journal must say so rather than attributing it to
whichever arm ran second.

**Latency.** p95 = 3171 ms against a 2500 ms budget — a third consecutive
milestone of breach. Not raised; see SPEC/02, which forbids raising it and records
the breach as an accumulating finding.

## Tools arm

Not yet run.

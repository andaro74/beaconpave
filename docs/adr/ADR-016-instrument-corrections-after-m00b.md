# ADR-016: Two instrument corrections the m00b run exposed

**Status:** Accepted (post-`m00b`, pre-M01)
**Seats:** AI Quality (eval semantics — two-key) · PM (metric definition)

## Context

Running the control found two faults in the *instrument*, not in the system
under test. Both were drafted during M00b and deliberately held until after the
tag, because SPEC/00b forbids improving a baseline retroactively: a tightening
that lands before the tag edits the number it is meant to qualify.

They are recorded together because they share one consequence, and stating that
consequence twice in two ADRs would be the surest way to have it read as boilerplate.

## Decision 1: `entitlement_source` is advisory until M06

**The assert can be satisfied by a claim.** 11 golden cases assert
`entitlement_source: entitlement-check`. The control has no such tool; it reads
the answer schema out of its own prompt, sees the enum, and reports
`entitlement-check` anyway — in **10 of the 11**.

The golden README predicted the opposite: *"the control has no tool; it emits
`model-inference` by construction."* That assumed the control would self-report
honestly. Nothing makes it do so, and an assert reading a self-report measures
candour rather than provenance. There is no way to fix this with a stricter
string: any value the assert accepts is a value the model can read and emit.

So the assert is **recorded and not scored** until M06, when the trajectory eval
can check whether `entitlement-check` was actually invoked. This is the treatment
`expect_tool_before_answer` already gets, for the same reason and by the same
rule — a check that cannot fail on the thing it names produces a number that
means nothing.

**The cases are not edited.** `entitlement_source` stays in `cases.yaml` exactly
as authored, because it is the contract M06 must satisfy; the deferral lives in
the runner, next to the trajectory deferral, with a test pinning it. Deleting the
assert would lose the requirement; scoring it credits a claim.

## Decision 2: `p95_ms` was a category error per case

**A p95 cannot be computed from one sample.** Every case carried a per-case
`p95_ms` ceiling, and the runner compared it against that case's single measured
latency. A p95 budget states that 95% of requests fall under a threshold — it
*allows* a 5% tail by construction. Asserting it per case, per sample, converts
that permitted tail into a per-case failure.

The m00b run shows exactly that, across 35 measured calls:

| | |
|---|---|
| median | 1553 ms |
| p90 / **p95** | 2292 / **2469** ms |
| max | 4760 ms |
| samples over the 1800 ms tier | **11 of 35 (31%)** |

**Suite p95 of 2469 ms is inside the manifest's declared 2500 ms budget.** The
service met its latency SLO while a third of individual samples "failed" a
ceiling labelled p95 — and three of m00b's ten golden failures were nothing but
that tail.

Latency therefore moves to where the statistic is meaningful:

- **Suite level.** The runner computes p95 across the whole suite and compares it
  to `gates.budgets.p95_ms` in the service manifest. That is what the manifest
  always meant.
- **Per case, `max_ms`** replaces `p95_ms` — a hang guard, not a performance
  target, set uniformly at 5000 ms (roughly twice the observed suite p95, well
  above any legitimate reply). It catches a stalled request, which a suite p95
  over 25 samples would not: a single 30-second call lands at the maximum, not
  the 95th percentile.

The four complexity tiers do not survive this. They were never derived from
measurement, and a hang guard has no reason to vary by case difficulty. Token
ceilings keep their tiers, which *are* measured (ADR-014).

This is the same fault ADR-014 fixed for `cost_usd` and missed for latency. That
ADR said "latency was always a system property" and stopped there. Latency is a
system property; the *ceiling* still needed deriving from measurement, and the
statistic still had to be one a single sample can support.

## Consequences

**The shared one, and the reason these are a single ADR: suite scores are not
comparable across this change.** A golden score recorded before it and one
recorded after measure different things — 11 cases lose a scored assert, and 25
cases change how latency is judged. The `m00b` row already carries a footnote
saying its number is deterministic-only; that footnote now also covers this
definition change, and the progression table must never present an M01 score as
an improvement on 15/25 without saying which parts of the instrument moved.

This is the identical hazard ADR-012 records for the judged/unjudged split. It is
the second time it has arisen, which suggests it is the normal case rather than
an exception: **whenever the instrument changes, the row needs a footnote before
the number needs an explanation.**

The size of it is worth stating rather than leaving abstract. Re-scoring the
**identical** `m00b` answers under the corrected instrument — the same 25 replies
from the same run, not a new run:

| | goldens |
|---|---|
| recorded at `m00b` | **15/25** |
| same answers, corrected instrument | **18/25** |

Three points of "improvement" with no system change whatsoever. That is the
whole hazard in one line: an M01 score of 18/25 would look like progress against
the recorded 15/25 and would mean nothing at all. The recorded entry stays 15/25
— history is append-only, and 15/25 is what was measured on the day with the
instrument as it then stood.

`m00b`'s recorded entries are untouched. History is append-only, and the whole
point of holding these corrections until after the tag was that 15/25 and 0/10
remain what was actually measured on the day.

**At scale, replace with:** per-case latency sampled k times and a real
distribution per case, plus SLO burn-rate alerting rather than a fixed ceiling.
The interface already matches — the manifest declares the budget, the runner
reports the statistic, and only the sample count changes.

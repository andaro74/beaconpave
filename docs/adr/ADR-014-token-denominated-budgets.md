# ADR-014: Budgets are denominated in tokens; dollars are computed at report time

**Status:** Accepted (pre-M00b) · **amended in place at M02** — the ceilings and
the governed-shape projection were both derived for a single model call, and the
tool plane makes a turn n calls. See "Amendment (M02)" at the end. The superseded
statements stay where they were written, marked, because an ADR that reads as
though it had always been right is worth less than one that shows where it was
corrected.
**Seats:** AI Quality (eval thresholds — two-key) · PM (metric definition)

## Context

The golden set shipped with a per-case `budget: { model: haiku, cost_usd: …,
p95_ms: … }`. The `cost_usd` figures were written against Anthropic's
first-party API rates. beaconpave calls Haiku through Amazon Bedrock, which is
partner-operated with its own price list, so every one of the 25 ceilings was
denominated in a currency the project does not spend.

The obvious repair is to re-derive the dollar figures at Bedrock's rates. That
repair is wrong, and finding out *why* it is wrong is what produced this ADR.

**A dollar ceiling is not a property of the system under test.** It is a
property of a vendor's price list, and the price list moves without a commit.
The whole point of `evals/history/` is that an m00b number and an m04 number
are comparable; a Bedrock price cut between them would improve every score
without the platform improving at all — and it would do so silently, because
nothing in the repo would have changed. That is precisely the failure ADR-012's
consequences section warns about in a different guise: two definitions plotted
on one line, with no footnote saying so.

Three further multipliers make the coupling worse than it looks. Bedrock
pricing is regional; the regional inference profile this project pins carries a
10% premium over the global one (ADR-015); and prompt caching prices cache reads
and writes differently again. A dollar ceiling silently mixes all of that into a
number the eval suite treats as a fact about the agent.

## Decision

The blocking assert is **tokens**. Dollars move to reporting.

```yaml
- budget: { model: haiku, tokens_in: 1500, tokens_out: 300, p95_ms: 1800 }
```

- `tokens_in` and `tokens_out` are separate, because they are priced
  differently everywhere and they fail differently: input growth is prompt
  bloat or context stuffing, output growth is runaway generation. Collapsing
  them into one total hides which one moved.
- `p95_ms` is unchanged. Latency was always a system property.
- Dollars are computed **at report time** from a single pinned rate table
  carrying a rate and a date, so a price change is a visible diff in one file
  rather than a silent re-score across 25 cases.
- A contract test (`test_no_budget_is_denominated_in_currency`) fails on any
  `cost_usd` reintroduced into a case, because the reintroduced value would look
  plausible and re-couple the suite quietly.

### How the numbers were derived

Measured against `us.anthropic.claude-haiku-4-5-20251001-v1:0` on 2026-08-15,
sending the committed system prompt, the answer schema, and `data/catalog.json`
inlined — the M00b control's shape:

| Case | input | output |
|---|---|---|
| `concise-022` | 1168 | 124 |
| `blackout-001` | 1171 | 125 |
| `recommend-003` | 1172 | 75 |
| `multi-023` | 1181 | 151 |
| `headroom-026` | 1177 | 157 |
| `edge-025` | 1163 | 158 |

Input is near-constant at 1163–1181 because the system prompt, schema, and
catalog dominate it; the question contributes a few tokens. So `tokens_in` is
~~**uniform at 1500**~~ — it is a property of the prompt architecture, not of the
case.

> **Superseded at M02 (the reasoning above still holds; the number does not).**
> `tokens_in` is uniform at **6000**. The clause "a property of the prompt
> architecture" is exactly right and is why the number moved: M02 changed the
> prompt architecture from one call to a loop. See the amendment below.

Output ranged 75–158. The golden set's author had already tiered budgets into
four complexity bands (1800/2000/2200/2400 ms, paired with 0.004–0.007 USD).
That tiering is preserved and moved to `tokens_out`, where per-case variance
actually lives: **300 / 400 / 500 / 600**, roughly twice the measured worst case
in each band.

These are ceilings derived from the prompt architecture and rounded for
legibility. They were **not** tuned until the control passed, and no case was
adjusted to accommodate a run — nothing has been run and recorded yet, which is
the only reason this edit is legitimate at all (CLAUDE.md: a case is never
edited to make a run pass).

## Consequences

**M00b is unblocked without a Bedrock rate.** Scoring no longer depends on a
price the project could not obtain from the AWS pricing page, the AWS Pricing
API (whose catalog still stops at Claude 3), or Anthropic's Bedrock
documentation. The rate is now needed only to render dollars in a report, and
its absence blocks nothing that gates a merge.

**The recorded artifacts carry tokens now, or the assert would be unrecordable.**
`quality/verdicts/schema.json` and `evals/history/schema.json` gain `tokens_in`
and `tokens_out`; `pave.verdict.build` accepts them. Without that, M00b could
assert on a number it had nowhere to write, and M03's re-score would have
nothing to compare against. Both schemas keep `cost_usd` as the rendered
report — but the verdict schema previously described it as a field that "blocks
like quality regressions," which under this ADR would put a vendor price list
back into a merge decision. That description is corrected: a gate blocks on
tokens; dollars are reported. No behaviour changes, because `pave gate decide`
never read the field.

**Recorded honestly: the cost axis does not discriminate at this scale.**
Measured on the same day, with the same prompt:

| Shape | input tokens |
|---|---|
| Ungoverned — whole catalog inlined (M00b) | 1138 |
| ~~Governed — one retrieved title (M02+)~~ | ~~891~~ |
| Floor — no catalog at all | 754 |

> **The 891 row was measured wrong at M02 and is struck rather than deleted.** It
> measured one retrieved title *inlined in a single call*, which is not what a
> tool plane does. Measured against the deployed gateway on 2026-08-18, the real
> governed shape costs **3065–4927** input tokens. The row was not a bad
> measurement of the thing it measured; it was a measurement of the wrong thing,
> and the amendment below says why that was easy to miss.

Inlining the entire catalog costs **247 tokens** more than retrieving the one
title the question needs. At ADR-009's corpus size — 5 titles, 1,173 bytes —
"the whole catalog in every prompt" is nearly free.

`SPEC/00b-baseline.md` predicts the opposite: *"Cost/latency — higher than
budget on some cases — whole catalog in every prompt."* That hypothesis will not
hold, and it will not hold for a reason that has nothing to do with the control
being well built. **The control is expected to pass the budget axis, and that
pass is unearned** in exactly the sense SPEC/00b's honesty clause defines. It
should be recorded as unearned when M00b runs, and the spec's hypothesis row
corrected at branch cut rather than quietly marked wrong afterwards.

This is a limitation of the fixture, not of the metric. Token budgets still
catch what they are for — prompt bloat, context-stuffing regressions, runaway
generation — and those are real failures at any corpus size.

**At scale, replace with:** the same token ceilings, per-tenant, with dollars
rendered from a rate table refreshed on the provider's price-change feed. A
catalog of realistic size makes the ungoverned-vs-governed token delta large
enough that cost becomes a discriminating axis on its own; the assert does not
change, only the fixture does. The interface already matches.

## Amendment (M02): a turn is n model calls, and the ceilings were derived for one

**Seats:** AI Quality (the ceilings — two-key) · Platform Engineering (the loop
bound). Measured 2026-08-18 against the deployed gateway, guardrail version 1,
before the tool plane was built. Evidence: `milestones/M02/loop-shape.json`.

Everything above was derived against a single `converse` call. M02 replaces the
inlined catalog with a tool, and a tool-using turn is a **loop**: the model asks
for a search, the platform answers, the model may ask again, and only then does
it answer the viewer. The ceilings did not become wrong because the system got
worse. They became wrong because they measure a shape that no longer exists.

### What was measured

Five golden cases spanning the shapes that drive token count, three samples each,
through the loop M02 will deploy. Two of the fifteen were refused by the guardrail
mid-loop and are excluded: a refusal measures a refusal, and including a turn that
stopped early would pull a ceiling downward using the samples that never reached
it.

| | measured (n=13, answered) | ceiling was | ceiling is |
|---|---|---|---|
| `tokens_in` per turn | 3065 / 3190 / **4927** (min/median/max) | 1500 | **6000** |
| `tokens_out` per turn | 137 / 194 / 445 | 300–600 by tier | **unchanged** |
| `latency_ms` per turn | 3905 / 4813 / **7462** | `max_ms` 5000 | **`max_ms` 12000** |
| model calls per turn | 2 or 3 | 1 assumed | bounded at 5 |

**`tokens_out` is not touched, and that is the useful half of the result.** The
tiered output ceilings were derived from the answer the viewer sees, and a tool
loop does not change that answer — no sample of any case exceeded the ceiling it
already had. A blanket "the loop moved, so raise everything" would have been the
easy edit and would have discarded a working assert.

### How the two new numbers were derived

**`tokens_in: 6000`** is 1.22× the observed maximum. It sits above a three-call
turn with headroom for the twenty cases that were not measured and for a system
prompt M02 has not finalized, and it sits **below** a four-call turn (~6600). That
placement is deliberate: this ADR's own consequences section says token budgets
exist to catch "prompt bloat, context-stuffing regressions, runaway generation",
and at M02 a loop that starts iterating more than the measured shape *is* the
runaway generation case. A ceiling set above the loop bound would catch nothing.

**`max_ms: 12000`** is a hang guard, and ADR-016 is explicit that it is not a
performance target. It is 1.61× the observed maximum and 2.49× the median — well
above any legitimate reply, and still tight enough that a stalled request lands on
it. The two ceilings are therefore derived into **different** headroom bands, and
`tests/test_budget_derivation.py` records both: a budget that sits too high stops
catching bloat, whereas a hang guard is supposed to sit clear of every legitimate
reply. Holding the second to the first's tightness would conflate two instruments
that ADR-016 separated on purpose. ADR-016 derived its 5000 as roughly twice the observed suite p95; that rule
degenerates here, because at n=13 the nearest-rank p95 *is* the maximum, so the
multiple is taken against the maximum instead and the difference is recorded
rather than hidden behind the same sentence.

**The manifest's service-level ceilings move with the per-case ones**, and the
numbers are recorded here because they moved on a two-key path with no written
derivation the first time. `max_tokens_in: 2000 → 6500` keeps the manifest above
the per-case 6000 by roughly the margin it always had (the original pair was
1500/2000), so a case that passes its own budget cannot blow the service's;
`max_ms: 5000 → 12000` tracks the per-case hang guard exactly, since a per-request
guard above the service's declared maximum would be unenforceable.
`max_tokens_out` is unchanged at 800, for the same reason the per-case output
ceilings are.

**`gates.budgets.p95_ms` is not touched and stays breached at 2500 ms.** It is a
suite-level statistic computed separately from case scoring, so the breach costs
no golden case and hides no signal. M01 declined to raise it and M02 declines
again; two milestones of breach is a finding that belongs in a journal, not a
configuration problem that belongs in a diff.

### Why the order matters more than the numbers

This edit changes 25 golden cases, and CLAUDE.md forbids editing a case to make a
run pass. The distinction is entirely one of sequence: the measurement was taken
**before the tool plane existed and before any M02 score existed**, so there was
no run to accommodate. The identical edit made after seeing a red run would be the
forbidden one, and nothing in the diff would look different. That is why the
measurement is committed as an artifact rather than described — a reader can check
the date against the milestone's history.

### A finding this measurement produced that is not about budgets

Two of fifteen samples were refused mid-loop by `TOPIC:entitlement-circumvention`,
on `entitlement-002` and `edge-024` — cases M01 scored without refusal. The
mechanism is new and belongs to the tool plane rather than to the guardrail: **in
a loop, the model's own intermediate reasoning becomes guardrail-assessed input on
the next call.** The same request refused on one sample and answered on another,
which is a per-case coin flip that a single sample cannot see, and it is a third
loss mechanism SPEC/02's pre-registered hypothesis did not anticipate. It is
recorded here because the measurement found it; disposing of it belongs to
SPEC/02 and to the Security seat's owed tightening, not to this ADR.

**At scale, replace with:** ceilings derived per prompt architecture and
re-derived automatically whenever the architecture changes, with the loop bound
enforced by the tool plane rather than asserted by the eval suite. The interface
already matches — the manifest declares the ceiling and the runner reports the
measurement; only who notices the shape change moves.

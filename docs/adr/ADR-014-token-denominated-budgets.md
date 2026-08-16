# ADR-014: Budgets are denominated in tokens; dollars are computed at report time

**Status:** Accepted (pre-M00b)
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
**uniform at 1500** — it is a property of the prompt architecture, not of the
case.

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
| Governed — one retrieved title (M02+) | 891 |
| Floor — no catalog at all | 754 |

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

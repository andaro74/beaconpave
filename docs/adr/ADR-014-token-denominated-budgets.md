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

## Amendment 2 (M08): two calls became three, and `tokens_in` is re-derived from the census by the same rule

**Seats:** AI Quality (the ceilings — two-key) · Platform Engineering (the
derivation pin) · Tool Owner (the manifest's declaration). **Evidence:**
`milestones/M08/context-census.json`, produced by
`milestones/M08/context_census.py` from files committed since M02, committed at
`dd4a5f0` (M08 PR 1) before any number was proposed, and pinned byte for byte by
`tests/test_m08_census.py`. **Zero model calls.** Every figure below is read out
of that record; the three pre-registered statements are ADR-073 amendment 2 §5's
wording, filled with a number and nothing else.

### The shape moved again

The M02 amendment above re-derived `tokens_in` because one call had become a
loop of two or three, and it wrote the reason down: *the ceilings did not become
wrong because the system got worse; they became wrong because they measure a
shape that no longer exists.* The same thing happened at M06b and went unseen
until M07 cleared the refusals that hid it. `entitlement-check` became a second
sequential tool round, so the modal turn went from two model calls to three; the
second tool's spec joined every call, so the per-call input went from 1693 to
2057. `tokens_in` is a sum over the turn's calls (`core/toolloop.py::_accumulate`),
and stage 2's exact table by call count is: 2 calls 3887–3959 (n=7), 3 calls
6022–6792 (n=52), 4 calls 8181–9220 (n=13), 5 calls 11081 (n=1). The 6000
ceiling sits entirely above every two-call turn and entirely below every
three-call turn — between the shape M02 measured and the shape that has run
since M06b, so every sample at the mandated three-call count is over it and so
is every four-call turn, and the axis cannot tell the two apart.

ADR-073 decision 2 pre-registered two outcomes and the rule that picks between
them, and the census picked **B**. The three statements below are the ones
ADR-073 amendment 2 §5 pre-registered for this amendment, verbatim:

1. **Not-A on the evidence admitted.** *"Outcome B is not-A on the evidence admitted: no sample over the ceiling at its mandated call count carries removable content in the three categories the rule admits — replayed rows the answer never cited, text sent twice in one request, tools the manifest does not declare. The census does not say the context cannot be reduced: 422–537 tokens of a 1859–1974 per-call base are unattributed, the same size with one tool offered as with two (`residual-differential.json`), and the measurement that attributes them is M09 PR 1's."*
2. **The re-derivation trigger.** *"The ceiling is re-derived for the shape as measured, a quarter of whose per-call base is unattributed; if that residual is later attributed to content the agent sends and can stop sending, the ceiling is re-derived by this same rule in the milestone that removes it, downward, on the same keys."*
3. **What the axis discriminates.** *"At any number in [7170, 8180] the `budget` axis discriminates call count ≥ 4, not calls above the case's mandate: the ceiling is uniform and the mandate is per case. Nineteen answered stage-2 samples ran three calls against a two-call mandate — `brand-021` s1; `edge-025` s1, s2; `entitlement-012` s2, s3; `grounded-017` s1–s3; `grounded-018` s1; `grounded-019` s2; `headroom-005` s1–s3; `headroom-026` s1–s3; `recommend-015` s1–s3 (6022–6792) — and every one passes it. What it catches is every 4- and 5-call turn: fourteen samples on seven cases."*

### The rule, written before the number

The M02 amendment states no point rule. It records where a round number landed
— *"1.22× the observed maximum"* — and the two reasons for the headroom, twenty
unmeasured cases and an unfinalised prompt, both of which are spent: every case
is measured in stage 2, and SPEC/08 constraint 5 freezes the prompt. Its prose
and its artifact also disagree on the multiple: the text says 4927 over thirteen
answered samples, `milestones/M02/loop-shape.json` says 4834 over ten, and the
census records the applied multiple as 1.241
(`ceiling_derivation.ceiling_over_measured_max`). A multiple that reads 1.22 in
one place and 1.241 in another is a description of a choice, not the rule that
made it. The discrepancy is recorded here and not repaired; the M02 amendment
stands as written.

What ADR-014 does pin is the band and the placement, in
`tests/test_budget_derivation.py`: `tokens_in` sits within 1.15–1.60× the
measured maximum of the shape, and below the next call count, because *a loop
that starts iterating more than the measured shape is the runaway generation
case*. From the census record, and from nothing else:

| | read from (the record's keys, verbatim) | value |
|---|---|---|
| mandated-shape maximum | `"8_decision_rule (pre-registered, SPEC/08)"` → `mandated_shape_tokens_in` → `max` | 6235 |
| minimum four-call turn | `"1_by_milestone (exact)"` → `m07-stage2` → `by_calls` → `"4"` → `min`, and independently the fold of `"2_stage2_per_sample (exact + replayed)"` over answered samples above the mandated shape | 8181 |
| band floor | 1.15 × 6235 | 7170.25 |
| band roof | min(1.60 × 6235 = 9976, 8181 − 1) | 8180 |

The exact floor is 7170.25, so the integer band is **[7171, 8180]**; ADR-073
wrote it as [7170, 8180], and 7170 itself would fail the pin.

**Which maximum.** The band's input is the *mandated-shape* maximum, 6235,
because SPEC/08 pre-registered it by that name at PR 1 (`dd4a5f0`: *"within
1.15–1.60× the mandated-shape maximum of 6235"*). The same record offers a
second reading: the as-run three-call maximum, 6792, which includes the
nineteen samples that ran three calls against a two-call mandate. Read that
way the floor is 7811 and the band [7811, 8180]. It is not the input, for the
reason statement 3 gives: those samples are the browse gap's first extra call,
the thing the axis cannot discriminate, and deriving the floor from them would
build that call's cost into the ceiling's headroom. The M02 amendment, by
contrast, took its maximum (4834) from a sample that was itself above its
mandate — the census's `mandated_calls()` did not exist then — so the two
applications of the same band read *"the measured maximum"* differently. That
is recorded here, and it is why the pin now names the mandated-shape maximum
by its key rather than reading a summary's `max`.

**The point rule: the midpoint of the band, rounded to the nearest hundred for
legibility.** It adds no constant beyond the two the pinned rule already
carries — the 1.15 floor and the next call count. It sits equidistant from the
two failure modes the derivation test names in words: under the floor, a prompt
edit or an unmeasured sample breaches the ceiling for no reason worth reporting;
at or above the four-call minimum, a runaway turn passes and the ceiling catches
nothing. Rounding to the hundred is this ADR's own *"rounded for legibility"* at
the grain every ceiling in the file already has. The rule cites no case and no
count.

**Where the rule was written, honestly.** It was stated in the PR plan the
operator approved before the number was named, and that plan is a conversation,
not a committed artifact: in the repository the rule first appears in the
commit that carries the number. ADR-073 decision 3 left the point to *"whichever
value in it the amendment argues"*, so this is admissible; it is not
pre-registered in the sense the band is, and every seat on PR 3 said so. Two
things stand in its place. First, the rule is executable and pinned in the
two-key derivation test
(`test_the_input_ceiling_is_the_number_the_point_rule_produces`): the test
computes the floor, the roof and the rounded midpoint from the record and
asserts every case and the manifest carry that number, so a move anywhere in
the band takes this file's two keys and a record that moves yields a different
number and goes red until an amendment re-derives it. Second, and stronger: by
the record, no answered stage-2 sample lies between the three-call maximum
(6792) and the four-call minimum (8181), so **every value in the band produces
the same per-sample join**. The point could not have been chosen by looking at
which cases pass, and cannot be checked against it either — the choice inside
the band is a judgment about headroom, and this paragraph is where it is
argued.

**The number: (7170.25 + 8180) / 2 = 7675.125, rounded to the nearest hundred —
`tokens_in: 7700`.** Checks: 7700 ≥ 7170.25; 7700 ≤ 9976; 7700 < 8181. It is
1.235× the mandated-shape maximum, 1465 tokens above it, 481 below the minimum
four-call turn, 530 above the band floor and 480 below its roof.

*Corroboration, not the rule:* this ADR's own applied multiple as the census
records it, 1.241 × 6235 = 7737.6, rounds to the same hundred. The prose's 1.22
would give 7606.7 and round to 7600 — one more reason the multiple is a
description. The midpoint between the two shapes, (6235 + 8181) / 2 = 7208, sits
38 tokens above the floor the test names as the noise edge; the geometric mean
of the two shapes, 7142, is under the floor; rounding to the thousand gives
8000, 181 under the four-call minimum, which is the placement the M02 amendment
refused when it left roughly 600 under ~6600. None of those was the rule and
none is the number.

### What moves, and what does not

- **The 25 case budgets:** `tokens_in: 6000` → `7700`, one value per case and
  nothing else in `cases.yaml`. `tokens_out`, `max_ms` and every output tier
  stay where the M02 amendment and the original derivation put them, for the
  reason the M02 amendment gave — the tiered output ceilings were derived from
  the answer the viewer sees, which a tool loop does not change — and because
  SPEC/08 constraint 4 keeps them there.
- **The manifest's `max_tokens_in`: 6500 → 8200**, the per-case ceiling plus
  the margin the pair has always had (1500/2000, 6000/6500; ADR-073 decision 3).
  It is a **declaration bound, not a scoring value**: nothing in `pave/` or
  `evals/` scores a case against it, `tests/test_contracts.py` only requires
  every per-case budget to sit under it, and the derivation test pins it (the
  literal, and the margin as `MANIFEST_MARGIN`). It sits above the four-call
  minimum, which is why the placement is asserted on the per-case ceiling and
  not on the manifest: **the new test fails any case at or above 8181.** This
  is the first time the two rules disagree — at M02 the manifest's 6500 also
  sat under the next call count (~6600) — and the decision is written rather
  than carried in: **the margin governs the manifest; the placement governs the
  per-case ceiling.** `pave/manifest.py` and `tests/test_contracts.py` both
  describe the manifest as the production budget every case is checked
  against; that enforcement does not exist, and if it lands where those
  sentences say it is, the manifest's own placement becomes a decision on the
  same keys. Recorded, not repaired.
- **`tests/test_budget_derivation.py`** is re-pointed: the `tokens_in` half of
  the headroom test reads the census's mandated-shape maximum, `BANDS`
  unchanged; the `max_ms` half still reads M02's artifact, because the hang
  guard did not move. A new test asserts every case's `tokens_in` is under the
  census's minimum four-call turn — the placement this ADR stated twice in prose
  and never pinned. **Re-pointing the band is what makes that test necessary**:
  against M02's artifact the roof was 1.60 × 4834 = 7734, under 8181, so the
  placement held by accident; against the census it is 9976, past the four-call
  minimum, so a ceiling could clear the band and pass every runaway turn. The
  test this PR adds repairs a protection the same diff removes. The anchor it
  reads — the four-call minimum — is derived from the mandated shape (its
  largest mandated count plus one), read from the stage-2 summary and folded
  independently from stage 2's own samples, and the two must agree; a single
  read re-pointed at stage 1's table (8271) or M06b's (8289) landed a ceiling
  above the real four-call turn with every test green, and now goes red. A
  second test executes the point rule itself and pins the number (see *Where
  the rule was written*). A third asserts the three pre-registered sentences
  are carried verbatim. Mutation audit, each restored from a scratchpad copy
  and with the two records re-produced where a real PR would: 7100 planted, red
  on the floor; 8181 planted, red on the placement test only, the roof silent;
  10000, red on the roof; 6500, 7600 or 8100 in the manifest, red on the pins;
  the placement test re-pointed at the three-call maximum, at stage 1 or at
  M06b, red; every case at 7500 or at 8180 (both in band), red on the point
  test; every budget line removed, red; one word changed in a pre-registered
  sentence, red; the `BANDS` floor lowered to 1.00, red on the point test; the
  placement test deleted with 8181 planted, or the point test deleted with 7500
  planted, nothing red — which is what makes each load-bearing.
- **`gates.budgets.p95_ms` is not touched** and stays breached at 2500 ms, a
  standing finding for M08 (ADR-073 amendment 2 §4); the rule that derives a
  suite p95 is owed at M09 PR 1.
- **The template does not move.** `templates/agent-tools/evals/golden/cases.yaml.tmpl`
  and `pave.manifest.yaml.tmpl` still carry 6000 and 6500. They are ADR-047's
  four-seat path, no test couples their values to the service's, and a
  scaffolded service's ceiling is its own derivation from its own measurement —
  a number copied from another service's census is a number, not a derivation.
  The stronger reason, found by the Platform Engineering seat: the template
  scaffolds a **one-tool** service (`catalog-search@^0` alone, no
  `expect_tool_before_answer` in its sample case), which is the two-call shape
  the M02 amendment derived 6000 for. The template is not stale; it is correct
  for what it produces. Named here so it is dated, by M08 PR 5's journal,
  rather than discovered.
- **Records.** The census record and `residual-differential.json` carry
  whole-file provenance digests of `cases.yaml` (both) and of the manifest (the
  census). Every measured figure in both is byte-identical before and after this
  amendment; only those three digest lines move. Both records are re-produced
  by their own readers in this PR and committed with those digests moved, so
  `--check` is green on the result; the diff to each record is its provenance
  lines and nothing else, shown key by key in the PR body. SPEC/08 constraint 3
  names `milestones/M07/`, which is untouched; the M08 records digest the file
  this PR exists to move, so `--check` could not have stayed green across PR 3
  as the spec assumed, and that is recorded here rather than worked around. The
  history-entry field `cases_sha256` (`evals/judged.py`) digests `cases.yaml`
  too, so PR 4's entry will carry a new value; nothing in `evals/history/` is
  edited here. **And the reader and record are keyed in this diff**: the
  Security seat moved the four-call anchor with a four-line trim in the reader,
  regenerated both records, and landed a ceiling above a real four-call turn
  with every test green on one key, because the record's pin re-runs the same
  reader. `pave/twokey.py` gains a rule over `context_census.py`,
  `context-census.json`, `residual_differential.py` and
  `residual-differential.json` — AI Quality, Platform Engineering and Security,
  the last because the record now decides what *catches a runaway loop* means
  — pinned in `tests/test_twokey_seats.py` (ratchet 20 → 21, `required` 65 →
  69, a `_blocked_for` plant on each of the four). Widened in the diff that
  creates the dependency, ADR-060's precedent.
- **`evals/comparators.json` does not move, and the L2 lane was run to know
  it.** The required lane re-scores M02's committed answers against the live
  cases file and fails `gate decide` on any deviation from the pinned 15 and
  17. Run locally at a401040 before the PR opened: **`PASS - control_passed 17,
  tools_passed 15`**. That is a count at 7700 on M02's one-tool evidence, and
  it is not the count constraint 2 reserves for PR 4, which is the stage-2
  join on M07's files. It is also not evidence for the claim: **the four-call
  discrimination holds for the shape this ceiling was derived from — two
  tools, a mandated three-call turn, stage 2's exact table — and not for M02's
  one-tool evidence**, whose four-call turns (7146–7868 by the census) straddle
  7700 because a one-tool call is cheaper. The comparator held because no M02
  verdict turned on `tokens_in` alone in that range; that is a fact about M02's
  answers, recorded here so nobody reads a green lane as the claim passing.

### Obligations this amendment dates

| debt | owed to | date |
|---|---|---|
| `BANDS` in `tests/test_budget_derivation.py` was guarded by the two-key rule on its file and by no test: the first mutation audit lowered the `tokens_in` floor to 1.00 with 7100 planted and nothing went red. The point test added after the seat round now catches any `BANDS` change that moves the rounded midpoint (the floor to 1.00, the roof to 1.20, both red); a roof raised while the four-call cap still binds does not move it and survives. Still owed: a direct pin that plants each constant and expects the band to refuse it | AI Quality with Platform Engineering | **M09 PR 1** |
| The template's 6000 and 6500 (`templates/agent-tools/`), named above as not moving and correct for the one-tool shape it scaffolds | Platform Engineering, ADR-047's four seats | **dated by M08 PR 5's journal** |
| The budget failure record names the excess and not the call count (`evals/deterministic.py`: *"tokens_in=8181 over 7700"*), so what this ceiling was derived to catch — a four-call turn — is not recoverable from the verdict without a hand-join to the trajectory. Carry `calls` into the record the way M07 made per-case `refused` derivable | AI Quality with Platform Engineering | **M08 PR 4** to decide; not this PR's, which moves no instrument |

### The seat round on PR 3, dispositioned

Four seats — AI Quality, Platform Engineering and Tool Owner on the enforced
rules, Security as the counterweight on the four-call assertion — each in an
isolated worktree at the PR's first commit, each asked one question: *is this
number produced by the pinned rule from the committed record and by nothing
else?* Each re-derived the band and the number from the JSON independently
and matched every figure above. Every seat answered the same way: **the band,
yes; the point, not by anything committed before this PR.** Every finding
below was made by planting and running, not by reading; none turns on which
cases pass, and no seat computed a count at any ceiling but 6000.

| finding | seats | disposition |
|---|---|---|
| The point rule's *"pre-registered in PR 3's plan"* names an artifact that is not in the repository; every integer in the band was equally green | all four | **Fixed above** (*Where the rule was written*): the claim is withdrawn and the truth stated; the rule is now executable and pinned in the two-key derivation test; the record's gap (6792, 8181) means every value in the band produces the same join |
| The band's input could be read as the as-run three-call maximum 6792, under which 7700 is below the floor | Tool Owner | **Declined, recorded above** (*Which maximum*): SPEC/08 pre-registered the mandated-shape maximum by name at PR 1; the as-run maximum includes the above-mandate samples statement 3 says the axis cannot discriminate |
| `milestones/M08/context_census.py` and its record sit on no two-key rule; a four-line trim in the reader's `by_calls()`, both records regenerated, landed a ceiling at 8190 — above the real four-call turn — with 2944 tests green on AI Quality's key alone | Security (blocking) | **Fixed, operator's decision**: the rule widened in this PR over the reader, the record, the differential and its record — AI Quality, Platform Engineering, Security — pinned with a plant on each; the PR collects all five enforced seats (*Records* above) |
| The required L2 lane re-scores M02's committed answers against the live cases file at 7700 and compares to `evals/comparators.json`'s pinned 15; if the tools arm's count moves, the comparator must move in its own three-key PR, and PR 3 — not PR 4 — prints the first count at the new ceiling on M02's answers | Security (blocking) | **Run, operator's decision**: `PASS - control_passed 17, tools_passed 15` at a401040; the comparator holds and does not move. The count is M02's one-tool evidence at 7700, not the stage-2 join PR 4 owns, and the four-call discrimination is claimed for the shape it was derived from and not for M02 (*Records* above) |
| The four-call anchor was three unpinned string constants and a literal `"4"`; re-pointing at stage 1's or M06b's table survived | Security, AI Quality | **Fixed**: the call count is derived from the mandated shape, the minimum is read from the summary and folded from the samples, and the two must agree |
| The placement test is vacuous on an empty budget set | Security | **Fixed**: every case carries a budget and the pack is at least the manifest's `eval_min_cases` |
| The manifest's +500 margin and the below-next-call-count placement disagree for the first time, and the ADR carried the margin in without deciding | Tool Owner | **Fixed above**: the decision is written; the prose in `pave/manifest.py` and `tests/test_contracts.py` describing an enforcement that does not exist is recorded |
| Re-pointing the band loosened the roof from 7734 to 9976; the new test repairs a protection the same diff removes, and the ADR did not say so | Platform Engineering | **Fixed above** |
| The derivation table's key paths dropped the record's parentheticals; a reader following them literally gets a `KeyError` | Platform Engineering | **Fixed above**: keys verbatim |
| The template's reason was weaker than the real one: it scaffolds the one-tool, two-call shape 6000 was derived for | Platform Engineering | **Fixed above**; the date stays PR 5's |
| Nothing asserts the three pre-registered sentences are carried verbatim | Platform Engineering | **Fixed**: a test in the derivation file, red on one changed word |
| `BANDS` guarded by no test | AI Quality, Platform Engineering, Security | **Narrowed** by the point test; the direct pin stays dated M09 PR 1 (obligations) |
| The golden-cases rule collects AI Quality alone, and ADR-073 D3 calls that *"two keys on the cases"* | AI Quality | **Declined** as a finding on this PR: the rule set is `pave/twokey.py`'s and predates M08; the point pin now puts any move of the number onto the derivation file's two keys as well |
| The budget failure record does not carry the call count | Security | **Dated** to PR 4's decision (obligations); `evals/deterministic.py` is not in this PR |
| `tests/test_g4_capture_boundary.py` is vacuous in any checkout under a directory named `.claude`, because `SKIP_DIRS` is matched against absolute parts; its own has-something-to-scan guard catches it | all four | **Declined here**: pre-existing, not this diff's; a discovered defect for the journal with a deadline (SPEC/08 *Bounded*) |
| A uniform ceiling cannot discriminate calls above a per-case mandate; a per-case ceiling keyed to `mandated_calls()` would | AI Quality | **Declined**: statement 3 records the limit; a per-case ceiling is a new rule, M09's |

### Why the order matters more than the number, again

The M02 amendment's sentence holds unchanged: this edit changes 25 golden cases,
CLAUDE.md forbids editing a case to make a run pass, and the distinction is
entirely one of sequence. The census was run and committed at `dd4a5f0` before
any number was proposed; the band follows from the census by a rule pinned two
milestones ago; the point rule was pre-registered in the PR plan before the
number was named; the reader prints no pass count at any ceiling but 6000, and
this amendment prints none at any ceiling. The first count at 7700 is M08 PR 4's,
on the committed stage-2 files, read against the census's per-sample call
counts. What PR 4 can find, this amendment does not know.

**At scale, replace with:** the same rule, run by the census on every change to
the prompt architecture — a tool added to `toolConfig`, a schema grown — with
the loop bound enforced by the tool plane and the next call count's minimum read
from the run rather than from a milestone's record. The interface already
matches: the manifest declares the ceiling, the runner reports the measurement,
and the census reads both.

## Amendment 3 (M08b): the suite `p95_ms` is derived from the mandated shape by the same rule, not raised

**Seats:** AI Quality (the ceilings — two-key) · Platform Engineering (the
derivation pin) · Tool Owner (the manifest's declaration). **Evidence:**
`milestones/M08/context-census.json`'s per-sample table joined to the three M07
stage-2 answer files' `usage.latency_ms`, both committed before the rule was
written; the rule is ADR-074 decision 3 §5, written in M08b PR 1 (`8c7a428`)
before any number was printed by a test. **Zero model calls.** The number is
executed and pinned by `tests/test_budget_derivation.py` in M08b PR 2, and
this amendment carries it in the words ADR-074 pre-registered.

### Why a raise was refused twice, and why this is not one

`gates.budgets.p95_ms` was 2500 from ADR-016. M01 breached it at 3194 ms and
declined to raise it; M02 breached it further and declined again; the test
that guarded it said in its docstring why: *a breach found by the instrument
working is not a configuration problem.* M07 recorded 5431 ms and M08 recorded
it again as a standing finding — breached by the shape (model time alone is
3606 ms at three calls, guard time 770–1212 ms in its own key) and not by a
regression — and ADR-073 amendment 1 §4 refused to derive a ceiling in the PR
that would move it, with 5431 in view, dating the rule to the next milestone's
first PR, written before a fresh run and applied after. That is this. The
number is not raised; it is produced by a rule from a population, and the rule
adds no constant.

### What a suite p95 can and cannot discriminate

The `tokens_in` rule places the ceiling below the next call count because turn
tokens separate cleanly by call count: no three-call turn is above 6792 and no
four-call turn below 8181. Latency does not: the fastest four-call turn in the
M07 files is 3526 ms and the mandated shape's p95 is above it. So a p95 ceiling
cannot be placed below the runaway shape, and this rule does not pretend to.
What a suite p95 discriminates is a **share**: the gate passes when at most one
turn in twenty runs slower than the ceiling, and it fails when the population's
tail is no longer the mandated shape's tail.

### The rule, verbatim from ADR-074 decision 3 §5

The ceiling sits within ADR-014's pinned band, 1.15–1.60×, of the **mandated
shape's own p95**: the latency of every answered M07 stage-2 sample whose call
count equals its case's mandate, with `evals/deterministic.py`'s p95
(`samples[ceil(0.95 n) − 1]`) over that population. The point is the band's
midpoint rounded to the nearest hundred — the rule
`tests/test_budget_derivation.py` already executes for `tokens_in`. The inputs
are the three M07 answer files' `usage.latency_ms` and the census's per-sample
`mandated_calls`; nothing else, and never a pooled p95 of any run.

**The population, by key.** `2_stage2_per_sample (exact + replayed)` rows with
`answered` true and `calls == mandated_calls`, joined on `(case, sample)` to
`milestones/M07/goldens-run-{1,2,3}.json`'s `usage.latency_ms`. The two
refused samples carry `latency_ms: null` and are in no population.

### The arithmetic

Forty answered samples at their mandate; their p95 is **3769** ms (maximum
3934). Band floor 1.15 × 3769 = **4334.35**; roof 1.60 × 3769 = **6030.4**;
midpoint **5182.375**; rounded to the nearest hundred, **`p95_ms: 5200`**.
Checks: 5200 ≥ 4334.35; 5200 ≤ 6030.4. It is 1.38× the mandated shape's p95.

The test computes each figure from the committed inputs — the percentile read
out of `suite_latency` itself, so the rule and the gate cannot disagree about
what a p95 is — pins `gates.budgets.p95_ms` to the number it prints, is red
on any planted constant, and asserts this amendment carries every figure
above verbatim. The direct pin on `BANDS` that ADR-014 amendment 2 dated to
this milestone lands in the same file: each constant literally, with `p95_ms`
on the budget band and not the hang guard's.

### What was in view, and the populations not taken

M07's pooled p95 of 5431 was in view when the rule was written, and this
amendment prints no verdict at the new ceiling on M07's run. What it prints
instead is the choice a seat can check: the populations the rule could have
read, the number each gives, and how the run in view would read under each.

| population | p95 | band | point | M07's 5431 reads |
|---|---|---|---|---|
| mandated shape, n = 40 (**the rule**) | 3769 | 4334–6030 | **5200** | **OVER** |
| as-run three-call, n = 59 | 5004 | 5755–8006 | 6900 | within |
| pooled, n = 73 | 5431 | 6246–8690 | 7500 | within |

The rule takes the only population under which the run in view fails the
gate. Re-scoring M07's committed files at the new gate prints
`suite latency  OVER p95=5431ms over 5200ms`; the per-sample join is
byte-identical to `rescore-join.json`, because the join reads token verdicts
and not the latency line.

### What the rule leaves standing, and what PR 3 reads

Nineteen samples ran three calls against a two-call mandate and are outside
the mandated-shape population by construction; fourteen ran four or more. The
as-run three-call p95 is 5004 and the pooled p95 5431. A share of the
population above the ceiling is what the gate now reports, and today that
share is the browse gap's; ADR-074 decision 2 owns it.

**PR 3 reads two numbers, not one** (ADR-074 amendment 1 §4): the fresh run's
pooled p95 against 5200, OVER or within, and the fresh run's mandated-shape
p95 against 5200 beside it. Pooled OVER with the mandated-shape p95 within is
the share the rule was written to report. A mandated-shape p95 over 5200 is
latency drift in the shape itself — a dated finding for Platform Engineering —
and the rule's premise, that the mandated shape's tail is stable across runs,
is what failed. One number cannot tell these apart. **The gate costs no case
either way**: it is a suite statistic computed apart from case scoring (this
ADR's M02 amendment), and moving it moves no verdict.

### What moves, and what does not

- **`gates.budgets.p95_ms`: 2500 → 5200.** The manifest's two keys (AI
  Quality, Tool Owner) and the derivation pin's two (AI Quality, Platform
  Engineering).
- **`tests/test_budget_derivation.py`**: `BANDS` gains `p95_ms` on the budget
  band and is pinned directly; `test_the_suite_percentile_budget_was_not_raised`
  is replaced by the test that executes the rule, and the replacement's
  docstring carries the rule and the reason the two-milestone refusal ends.
- **`milestones/M08/context-census.json`**: its `inputs_sha256` line for
  `services/highlights-agent/pave.manifest.yaml` moves, because the census
  digests the manifest and `tests/test_m08_census.py` regenerates the record
  byte for byte (ADR-074 amendment 1, fact 1). Re-produced by its own reader
  with that one line moved and nothing else, on the census rule's three keys.
- **`tokens_in` stays 7700; `tokens_out`, `max_ms` and every tier stay** where
  amendment 2 and the original derivation put them. No case moves.
- **The M07 files' verdicts do not move.** The latency line at the new gate is
  the one predicted above; the count and the join are what M08 pinned.

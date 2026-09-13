# The five blackout failures — a diagnosis

**Not a milestone, not a spec, not a claim, not a fix.** Findings only. Zero model calls, no
run, no deploy, and no tool, schema or corpus file was edited. Read on `main` at `757bbd0`.

**Population:** `blackout-001`, `006`, `007`, `008` and `009`, each `FAIL [FAIL FAIL FAIL]`
in M09's goldens control run (`milestones/M09/fresh-join.json` `count.per_case`), three
samples each, fifteen samples in total.

---

## The answer

**Do three or more of the five share a single cause? Yes. Four do, and it is not a blackout
cause.**

> `blackout-001`, `006`, `007` and `008` exceed the `tokens_out: 300` tier on **every one of
> their 12 answered samples** (310 to 357). For `006`, `007` and `008` that is the **only**
> failing assert on 8 of their 9 samples, and each case's entitlement verdict matches the
> catalog on all 9.

The tier sits at `services/highlights-agent/evals/golden/cases.yaml:41`, `:65`, `:87` and
`:110`. The quantity it is scored against is summed over every model round
(`platform/gateway/core/toolloop.py:303-304`). Every answered sample of the four took three
rounds (`fresh-join.json` `per_sample`: `calls: 3`, `at_mandate: true`). ADR-078 records
that the tier was derived from a **one-call** shape (ADR-078:121) and that
`usage.tokens_out` is summed over every model round (ADR-078:126).

**This is already an owned debt.** It is `milestones/M09c/README.md:264` (debt 3, the
`tokens_out` tier re-derivation, AI Quality, unscheduled). The rule for it is written in
ADR-078 decision 3 (ADR-078:118) and has not been executed. `milestones/M08b/README.md:361`
names `blackout-001`, `007` and `008` among the original five and `blackout-006` among the
seven it widened to.

**So "the blackout family" is a family by name, not by cause.** By cause the five split
three ways, and only one of the three causes covers more than one case:

| cause | cases | samples | already owned |
|---|---|---|---|
| `tokens_out` over the 300 tier | `001`, `006`, `007`, `008` | 12 of 12 answered | yes — M09c debt 3, AI Quality |
| the answer's `entitlement.reason` differs from the catalog's verdict | `001` | 2 of 3 (s1, s3) | no |
| refused on the `answer` channel by the main guardrail | `009` | 3 of 3 | yes — M09c debt 5 (`milestones/M09c/README.md:266`), Security |

One further failure fits none of the three: `006` s3's prose says *"blacked out"* and not
`blackout`, so `must_mention` fails (`evals/deterministic.py:123-126` is a substring test).

---

## One question the record cannot answer

**What did `entitlement-check` return?** It is **not recorded**, for any of the fifteen
samples. Because of that, **"does the answer contradict what the tool returned"** is also
not answerable from the record. What the record does and does not hold:

- **The trajectory steps carry the arguments and the plane's decision, not the result.**
  Every step's fields are `round, seq, tool, args, decision, mechanism, reasons, executed`
  (`toolloop.py:218-228`). `tool_records` point into the lake.
- **The lake record has no place for a result.** The `tool` object in
  `platform/gateway/audit.schema.json:182` has the properties `args, decision, executed,
  exemptions, id, mechanism, principal, reasons, round`. Both it and the record root are
  `additionalProperties: false`.
- **The answer's `source: entitlement-check` is the model's own report.**
  `evals/deterministic.py:336-355` says so, and that is why it is not scored.
- **The deployed tool's code is not pinned by the run.** The preflight
  (`goldens-run-refusals.json` `_preflight`) pins the gateway function and its bundle. It
  does not pin the `entitlement-check` function.
- **`fresh-join.json`'s `replayed_chars_added` is not an observation.** Its round-3 figures
  are 126, 120 and 135. `milestones/M08/context_census.py:199` produces them by re-running
  `entitlement.check` on the recorded arguments. They match the lengths of the
  committed code's verdicts (126 / 126 / 120 / 135 for `001` / `006` / `007` / `008`),
  which is the recomputation agreeing with itself.

**What is recorded**, and what it shows without inference:

- Every one of the fifteen `entitlement-check` steps reads `decision: allowed, mechanism:
  none, executed: true`. A result that failed the output contract is rewritten to
  `denied` (`toolloop.py:595-596`, recorded at `:223`). **So in every sample the tool
  answered, its answer conformed to `schema.out.json`, and it was handed to the model as
  JSON** (`toolloop.py:259`).
- No sample was stopped on the `tool_output` channel. `001`–`008` were answered, and
  `009`'s three refusals name `channels: ["answer"]`.

**What would be needed to answer it.** Any one of these, and none is inside this brief:

1. The payload as the model received it. No committed file and no lake record carries it.
   Capturing it is a change to the audit record, and the result would only exist for runs
   taken after that change.
2. A new run with that capture in place. This brief refuses a run.
3. **Weaker:** the deployed `entitlement-check` function's code hash and last-modified
   time, compared with the bundle `tools/entitlement-check/` (last commit `80f1811`,
   2026-08-31) and `data/catalog.json` (last commit `0c4a852`, 2026-08-15) produce. This is
   an AWS read, not taken. It would establish which code was deployed, not what it
   returned.

**What stands in for it below** is labelled *catalog verdict* throughout. It is what the
committed `entitlement.check` returns on each recorded argument set at the committed
`CLOCK` (`2026-09-13T18:00:00Z`, `tools/entitlement-check/server.py`). Each one is checked
by hand against `data/catalog.json` and agrees with the golden case's expected verdict. It
answers *"is that correct against data/catalog.json"*. It is **not** a reading of what the
deployed tool returned.

---

## The fixture

`data/catalog.json:4-5` — `"blackouts": { "jefferson-derby": ["jefferson-city",
"port-william"] }`. `:8` — `t001`, `event: jefferson-derby`, `entitlement: sports-tier`,
`starts: 2026-09-13T19:00:00Z`. The only title the five ask about is `t001`.

SPEC/02:79-87 takes the blackout table out of the prompt, and `catalog-search` never serves
it (`tools/catalog-search/search.py:8-9`: *"Rows only, and never the blackout table"*). **So
`entitlement-check` is the only component in any of these turns that can know a blackout.**
In all fifteen samples it was called, with the viewer's plan and DMA, before the answer.

`tools/entitlement-check/entitlement.py:60`:
`REASON_ORDER = ("unknown-title", "blackout", "upgrade-required", "not-yet-started", "ok")`.
Its derivation comment names `blackout-001` as the case that fixes *"a blackout outranks a
plan gap"* (`:46-48`).

---

## Per case

For each sample: the `catalog-search` arguments, the `entitlement-check` arguments, the
answer's `entitlement`, `tokens_out`, and the failing asserts. Sources:
`goldens-run-{1,2,3}-trajectory.json`, `goldens-run-{1,2,3}.json`, and
`milestones/M09/per-sample.txt` (sample 1 `:2-15`, sample 2 `:68-79`, sample 3
`:129-143`). In every sample the one `catalog-search` step reads `allowed / none`, executed
once, and no search went beyond the mandate before the verdict (`fresh-join.json`
`per_sample[].search`).

### `blackout-001` — base, `jefferson-city`, expects `entitled: false, reason: blackout`

| s | `catalog-search` args | `entitlement-check` args | answer `entitlement` | `tokens_out` | failing asserts |
|---|---|---|---|---|---|
| 1 | `query "Jefferson Derby tonight"`, brand, `type live-event`, `limit 5` | `t001`, `base`, `jefferson-city` | `false`, **`upgrade-required`** | 357 | `must_mention`, `entitlement`, `budget` |
| 2 | `query "Jefferson Derby tonight"`, brand, `type live-event` | `t001`, `base`, `jefferson-city` | `false`, `blackout` | 346 | `budget` |
| 3 | `query "Jefferson Derby tonight"`, `type live-event`, brand | `t001`, `base`, `jefferson-city` | `false`, **`upgrade-required`** | 338 | `must_mention`, `entitlement`, `budget` |

- **Called?** Yes, 3 of 3, with arguments equal to the case's viewer.
- **Returned?** Not recorded. **Catalog verdict:** `{"entitled": false, "reason":
  "blackout", "required_entitlement": "sports-tier", "event": "jefferson-derby",
  "blackout": true}`. `jefferson-city` is in the derby's blackout list, and `base` does not
  cover `sports-tier`. Both conditions hold, and `REASON_ORDER` puts `blackout` first.
- **Contradiction, or never asked?** The tool was asked in every sample. In s1 and s3 the
  answer's `reason` contradicts the **catalog verdict**. Whether it contradicts the
  **tool's** return cannot be read (above). Both answers still carry `entitled: false`,
  which agrees with the catalog verdict. Only the reason differs.
- **Where it diverges.** In the final round (round 3), in the answer, after both tool steps
  completed with the arguments a correct answer needs. s1's prose attributes the refusal to
  the plan (*"it requires a sports-tier subscription in the Jefferson City market"*). s3's
  prose names only the plan. Neither mentions a blackout. s2's prose names both, reports
  `blackout`, and fails on `budget` alone.

### `blackout-006` — sports-tier, `port-william`, expects `entitled: false, reason: blackout`

| s | `catalog-search` args | `entitlement-check` args | answer `entitlement` | `tokens_out` | failing asserts |
|---|---|---|---|---|---|
| 1 | `query "derby"`, brand | `t001`, `sports-tier`, `port-william` | `false`, `blackout` | 310 | `budget` |
| 2 | `query "derby"`, brand, `type live-event` | `t001`, `sports-tier`, `port-william` | `false`, `blackout` | 330 | `budget` |
| 3 | `query "derby"`, brand, `type live-event` | `t001`, `sports-tier`, `port-william` | `false`, `blackout` | 319 | `must_mention`, `budget` |

- **Called?** Yes, 3 of 3, with the viewer's arguments.
- **Returned?** Not recorded. **Catalog verdict:** `blackout`, `blackout: true`.
  `port-william` is in the list.
- **Contradiction?** No. The answer's verdict equals the catalog verdict in 3 of 3.
- **Where it diverges.** Not in the trajectory and not in the verdict. `tokens_out` is over
  the tier on 3 of 3. On s3 the prose says *"blacked out"*, which fails the substring test
  for `blackout`.

### `blackout-007` — sports-tier, `north-haven`, expects `entitled: true, reason: ok`

| s | `catalog-search` args | `entitlement-check` args | answer `entitlement` | `tokens_out` | failing asserts |
|---|---|---|---|---|---|
| 1 | `query "derby"`, brand, `type live-event` | `t001`, `sports-tier`, `north-haven` | `true`, `ok` | 326 | `budget` |
| 2 | `query "derby"`, brand | `t001`, `sports-tier`, `north-haven` | `true`, `ok` | 325 | `budget` |
| 3 | `query "derby"`, brand | `t001`, `sports-tier`, `north-haven` | `true`, `ok` | 333 | `budget` |

- **Called?** Yes, 3 of 3.
- **Returned?** Not recorded. **Catalog verdict:** `ok`, `blackout: false`. `north-haven`
  is not in the list, `sports-tier` covers `sports-tier`, and the start date is the clock's
  UTC day.
- **Contradiction?** No, 3 of 3.
- **Where it diverges.** Only on `tokens_out`, 3 of 3.

### `blackout-008` — base, `lake-adair`, expects `entitled: false, reason: upgrade-required`

| s | `catalog-search` args | `entitlement-check` args | answer `entitlement` | `tokens_out` | failing asserts |
|---|---|---|---|---|---|
| 1 | `query "derby tonight"`, brand, `type live-event` | `t001`, `base`, `lake-adair` | `false`, `upgrade-required` | 352 | `budget` |
| 2 | `query "derby tonight"`, brand, `type live-event` | `t001`, `base`, `lake-adair` | `false`, `upgrade-required` | 330 | `budget` |
| 3 | `query "derby tonight"`, `type live-event`, brand | `t001`, `base`, `lake-adair` | `false`, `upgrade-required` | 332 | `budget` |

- **Called?** Yes, 3 of 3.
- **Returned?** Not recorded. **Catalog verdict:** `upgrade-required`, `blackout: false`.
  `lake-adair` is not in the list, and `base` does not cover `sports-tier`.
- **Contradiction?** No, 3 of 3. `must_mention: sports-tier` passes on all three.
- **Where it diverges.** Only on `tokens_out`, 3 of 3.

### `blackout-009` — sports-tier, `granite-falls`, expects `entitled: true, reason: ok`

| s | `catalog-search` args | `entitlement-check` args | outcome | failing asserts |
|---|---|---|---|---|
| 1 | `query "Jefferson Derby"`, brand, `type live-event` | `t001`, `sports-tier`, `granite-falls` | refused, `answer`, `TOPIC:entitlement-circumvention` | `json_schema`, `must_cite`, `entitlement` |
| 2 | `query "Jefferson Derby"`, brand | `t001`, `sports-tier`, `granite-falls` | refused, `answer`, `TOPIC:entitlement-circumvention` | `json_schema`, `must_cite`, `entitlement` |
| 3 | `query "Jefferson Derby"`, brand | `t001`, `sports-tier`, `granite-falls` | refused, `answer`, `TOPIC:enforcement-probing` | `json_schema`, `must_cite`, `entitlement` |

Refusals: `goldens-run-refusals.json` `refusals.blackout-009`, guardrail `abayh4ye7f8o`
v4, `record_resolved: true` on all three. Transcript: `goldens-run-transcript.txt:23`,
`:57`, `:91`.

- **Called?** Yes, 3 of 3, with the viewer's arguments, before the refusal (*"after 2 tool
  call(s)"*).
- **Returned?** Not recorded. **Catalog verdict:** `ok`, `blackout: false`.
  `granite-falls` is not in the list.
- **Contradiction?** **Not answerable**, and for a second reason besides the missing
  return value: the model's final text was withheld and is not committed.
  `milestones/M09b/withheld-grants-security.json` and `-legal-sp.json` record, for s1 and
  s2 only, `grant: true, dec001_shape: false`, and state that no held text is in them.
- **Where it diverges.** After generation, at the `answer`-channel assessment. Both tool
  steps had completed, and nothing reached the viewer. The three failing asserts are all
  consequences of the refusal envelope. There is no `tokens_out` reading: usage is zero,
  and `fresh-join.json` reads `null`.

---

## Would any of the five need a change to a contract or a generated policy file?

**No case, as recorded, needs a change to `schema.in.json`, `tools.contracts.json` or a
generated policy file.**

- **`tools/entitlement-check/schema.in.json`.** All fifteen recorded calls carry exactly
  `title_id`, `plan` and `dma`, within the enums, and the plane allowed every one.
- **`tools/catalog-search/schema.in.json`.** One executed search per sample, none beyond
  the mandate. **The browse gap 09c named is not present in these five.**
- **`platform/gateway/policy/tools.contracts.json` and `tools.cedar`.** Every step reads
  `allowed / none`.
- **`tools/entitlement-check/schema.out.json`.** No result was withheld. Each catalog
  verdict is inside the output enum.

**One place a Tool Owner question could remain, and nothing recorded says it is open.**
Take `blackout-001` s1 and s3. If the deployed tool returned something other than
`blackout`, the fault would sit in the tool's behaviour or its deployed bundle. That would
still not be a contract change: the committed contract already expresses `reason:
blackout` and `blackout: true`. The record cannot separate that from the model reporting a
different reason than it was handed (see *One question the record cannot answer*).

---

## Not examined here

- **`multi-023`** carries the same failing string as `001` s1 and s3, *"entitlement:
  reason='upgrade-required' (expected 'blackout')"*, on all three samples
  (`per-sample.txt:50`, `:111`, `:180`). Its viewer is base plan in `port-william`, also a
  blacked-out DMA. It is outside the five. Its trajectory was not read, and nothing here is
  a finding about it.
- **Judge axes.** `per-sample.txt` lists deterministic asserts only. Nothing here reads
  the rubric scores.
- **M08b's samples of the five.** `fresh-join.json` carries their per-case results, but
  their trajectories are not in this brief's inputs.

## What this does not do

It writes no spec, no claim and no ADR. It proposes and applies no fix, and it does not
say whether a milestone should exist. It edits no tool, schema, corpus, case, tier or
guardrail, and it takes no run and makes no AWS read. The one computation it ran is
`entitlement.check` on five recorded argument sets, against the committed catalog and
clock. That is hermetic and makes no network call, and its output is labelled *catalog
verdict* wherever it appears.

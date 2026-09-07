# M08b — the ceiling, measured on samples it was not derived from

**Written before the branch is cut.** Owned by the PM seat. Branch
`m08b-fresh-run`, tag `m08b`. A row added in place between 08 and 09 on
ADR-054's precedent; nothing below it shifts (ADR-074 decision 1).

**Deliberately short**, in SPEC/08's shape. Every decision lives in ADR-074;
every "what broke" goes to the journal at close. This file states the
milestone and nothing else. **Corrected at PR 1b by ADR-074 amendment 1**, a
cold read before PR 2 opened: two Definition-of-done clauses were unreachable
as written, three files that decide the claim sat on no two-key rule, the
calibration call had no producer, and a falsifying sample had no reading.
PR 1b spent the sixth slot, so the cap's fallback fired and the DMA rename is
M09 PR 1's by name (*Bounded*).

## Why

M08 closed at 12/25, and the journal says what that number is in its first
sentence: a re-reading of the 75 samples M07 recorded on 2026-09-06, at a
ceiling re-derived for the shape that produced them. Every number in M08 is
about those samples. Nothing in the repository says what the agent does today,
and the last fresh run of any arm was M07 stage 2.

M08 handed twelve dated debts to "M09 PR 1". Seven of them either need a run
or must be sequenced around one: per-call `inputTokens` and the calibration
call, `calls` in the budget verdict, the suite `p95_ms` rule, `recommend-003`'s
answer-channel reading, the browse gap, the five `tokens_out` cases, and the
DMA rename's placement. The rules registry — claim 6, M09 — needs the run
before it can start: without a pre-disposition baseline, per-call usage in the
record and the answer-channel question decided, every number the rules loop
would produce is a budget number wearing a disclosure case's clothes (ADR-073
decision 1's own words). ADR-074 decision 1 splits the two: **this milestone
takes the fresh run and the debts that need it; M09 stays the registry.**

**No claim in the twelve-claims table is assigned to it.** It serves claim 2
defensively (a gate whose budget axis was proven on the samples it was derived
from has not yet been proven on any other) and hands claim 6 a measured arm.

## The one claim

**The `tokens_in` ceiling of 7700, derived at M08 from the committed stage-2
census by ADR-014's pinned rule, holds on a fresh k=3 run of the tools arm
through the deployed gateway, on samples it was not derived from: every
answered sample at three model calls or fewer passes `tokens_in` and every
sample at four or more fails it, per sample, with the per-call `inputTokens`
and the call count carried in the answer file and in the budget verdict — and
no case, tier, token ceiling, prompt, tool spec, tool result field, topic,
guardrail or catalog moved before the run.** The suite `p95_ms` gate moves in
PR 2 by the rule below; it is a share of a population, not a token ceiling,
and the claim does not cover it.

The claim is per sample and the count cannot show it. M08's record has no
answered sample between 6792 and 8181, so every value in the band produced
the same join there; a fresh sample can land inside that gap on either side,
and that is what the claim risks. Falsifiers: any fresh answered sample at
three calls or fewer over 7700; any at four or more under it —
`evals/deterministic.py::budget` compares `got > limit`, so a sample at
exactly 7700 passes. A single sample either way falsifies the claim. If it is
falsified, **the claim's reading stops at PR 3** and the sample is recorded
with its row of the table below; **PRs 4 and 6 proceed as planned**, because
neither depends on the claim and dropping them would re-date four debts to
M09 PR 1, which is the pile ADR-074 decision 1 describes; the milestone
closes red at PR 6. A re-derivation is a census milestone with its own rule,
and is not this one's.

### What a falsifying sample means, pre-registered

The falsifier is one sample, and "the ceiling failed" is four different
failures. The numbers the reading needs, all from M08's record: the point
**7700**; the unrounded midpoint **7675.125**; the band **[7171, 8180]**; the
record's gap **(6792, 8181)** — 908 tokens (13.4%) above the as-run
three-call maximum and 481 (5.9%) below the four-call minimum; the
mandated-shape maximum **6235**. The two tails are not the same distance away
and this spec predicts neither side; the reading is side-specific.

**The rounding grain is (7675.125, 7700]** — the interval where the rounded
and unrounded points disagree. A sample outside it falsifies the number and
the rule's own unrounded output alike, and the rounding is not implicated.
Where a falsifying sample lands, and what a red close records:

| the falsifying sample | what moved | re-derived band | lesson recorded |
|---|---|---|---|
| ≤3 calls, **at mandate**, in (7700, 8180] | the mandated-shape maximum is now ≥ that value; floor 1.15 × 7720 = 8878 > 8180 | **empty** | **the rule failed**: no ceiling can sit 1.15× above this shape and below the next call count; a re-derivation by the same rule has no solution, and the census milestone needs a different rule (per-case, or a call-count gate) |
| ≤3 calls, **above mandate**, in (7700, 8180] | nothing in the band's inputs; the browse gap's first extra call grew | unchanged, contains 7700 | **the point failed inside a band that still holds it**: the midpoint rule left 908 tokens over the as-run three-call maximum and that was not enough; ADR-014 amendment 2 statement 3's *discriminates call count ≥ 4* is the sentence that was wrong for this sample |
| ≤3 calls, > 8180 | the three-call shape overlaps the four-call shape | empty | the rule failed, as row 1 |
| ≥4 calls, in [7171, 7700] | the four-call minimum moved under the point; roof = that value − 1 < 7700 | non-empty, **excludes 7700** | **the point failed and the rule survives**: the same rule re-derives lower (a four-call minimum of 7650 gives [7171, 7649], midpoint 7410, point 7400) |
| ≥4 calls, < 7171 | roof < floor | empty | the rule failed |
| either side, **inside (7675.125, 7700]** | — | — | **the grain**: a three-call sample here passed only because the midpoint rounded up — a near miss, recorded, not a falsification; a four-call sample here passed for the same reason, and that IS a falsification the rounding caused, so the lesson is the grain and not the ceiling |

`fresh_join.py` prints, for every answered sample, its distance to 7700, to
7675.125 and to the nearer band edge; and for the run as a whole the fresh
mandated-shape maximum, the fresh four-call minimum, the band those two
re-derive by ADR-014's pinned rule, and whether 7700 sits inside it. A
falsifying sample is recorded with its row above by name. **When the claim
holds, the same column is the finding for M09**: the claim can hold while the
rule does not — a fresh three-call sample at mandate at 6900 passes 7700 and
moves the floor to 7935, so the re-derived band [7935, 8180] no longer holds
the number that held. Recorded, not ruled on: 7700 stands wherever the fresh
band lands, because a ceiling moved on a fresh run's band is a re-derivation,
and that is a census milestone.

Beside it, pre-registered in ADR-074 decision 3 and **not the claim** — each
a finding about the side-prediction when it misses, never a failure of the
claim:

- **The count.** `N/25` with **7 ≤ N ≤ 14**, predicted **N = 12**. The band
  is the twelve at M08 minus the five whose pass was 2-of-3 (`entitlement-002`,
  `entitlement-011`, `grounded-017`, `grounded-019`, `headroom-005`) plus the
  two whose fail was 1-of-3 (`blackout-009`, `entitlement-012`), read from
  `milestones/M08/rescore-join.json`. Falsifiers: N outside the band; a case
  that passed 3-of-3 at M08 failing by majority; a case that failed 0-of-3
  passing by majority.
- **Refusals.** Refused by majority **0–2 of 25** (SPEC/01's band, M07's
  measured 1). Falsifier: 3 or more.
- **`recommend-003`**, read by the rule in ADR-074 decision 3 §3: **F** is the
  cases refused by majority on the `answer` channel by the entitlement topic
  whose held text is a schema-conforming grant; **G** is the cases whose
  majority answer or majority held text carries `entitlement.entitled: true`.
  F = 0 closes the question as not reproduced; 0 < F < G reads it as a
  **topic question**; F = G reads it as an **answer-policy question**. Any
  refused case in `DEC-001`'s shape re-opens ADR-068's conjunction question
  instead. **Both counts are produced by a reader**, written in PR 2 over the
  answer files, the sidecar and `withheld-read.txt`, and tested by reproducing
  the prior ADR-074 decision 3 §3 read by hand from M07's files — G = 8,
  F = 1; a second hand count compared to the first is not the reading. The
  reading is Security's disposition at PR 3; any fix is its own ADR, not this
  milestone's.
- **The residual**, attributed by two exact numbers (ADR-074 decision 3 §4):
  the fresh run's round-1 `inputTokens` on `blackout-008` (**A**), and one
  calibration call on the same viewer turn with tools absent (**B**), against
  the census's estimates for the committed text (**E**) and the two specs
  (**S**). `D = B − E` is tokeniser density; `F = A − B − S` is provider
  framing; `A − E − S = D + F` by identity. **With signs**: D is negative
  when the estimate over-counts, and a share of a signed sum is undefined, so
  the reading names whichever of |D| and |F| is 70% or more of |D| + |F|, or
  both with their shares, each with its sign. E is read by named key from the
  census record or computed by the census reader's own function on the
  committed text, never re-estimated. B is sent by `run_with_tools.py
  --calibrate`, added in PR 2 (the same event with `tools` absent and the
  same `system`, the handler's existing path). **If the calibration turn is
  refused on the `answer` channel** the runner writes `tokens_in: 0`; B is
  then read from the audit record's per-call usage, and if the record does
  not carry it the call is re-issued once on the case with the next-highest
  mandated-shape `tokens_in` in the census, **`entitlement-010`** (6229), with
  A read from the same case and the substitution recorded. ADR-014 amendment
  2's downward trigger arms only if the round-1 pin fails.
- **The suite `p95_ms`**, at **5200** — the number ADR-074 decision 3 §5's
  rule yields from the mandated shape and PR 2's test prints (the population,
  and the two not taken, below). PR 3 reads **two numbers**: the fresh pooled
  p95 against 5200, OVER or within, and the fresh mandated-shape p95 against
  5200 beside it. Pooled OVER with the mandated-shape p95 within is the share
  the rule was written to report — the browse gap's, ADR-074 decision 2's;
  a mandated-shape p95 over 5200 is latency drift in the shape itself, a
  dated finding for Platform Engineering, and the rule's premise — that the
  mandated shape's tail is stable across runs — is what failed. One number
  cannot tell these apart. Recorded, not accommodated; the gate costs no case
  either way.
- **Two triggers** (ADR-074 decision 2): the browse gap **persists** if any of
  the seven cases carries a sample at four calls or more with a
  `catalog-search` call beyond its mandate; the `tokens_out` five **persist**
  if any of them fails `tokens_out` by majority at its unchanged tier. Read
  from the fresh trajectories and transcript; recorded, not diagnosed.

### The `p95_ms` gate: the population, the number, and the two not taken

**The population is forty answered M07 stage-2 samples whose call count
equals their case's mandate**, read from the census record's
`2_stage2_per_sample` (`answered`, `calls == mandated_calls`) joined to the
three M07 answer files' `usage.latency_ms`; the two refused samples carry
`latency_ms: null` and are in no population. With `evals/deterministic.py`'s
`samples[ceil(0.95 n) − 1]`, recomputed cold from those inputs at PR 1b:

```
pooled n 73 p95 5431
mandated n 40 p95 3769 max 3934
above-mandate 3-call n 19   four+ n 14   min four-call latency 3526
floor 4334.35  roof 6030.4  midpoint 5182.375  rounded 5200
3-call as-run p95 (n 59) 5004
```

**PR 2 chooses nothing**: the population, the percentile, the band and the
point rule are fixed in ADR-074 decision 3 §5, and PR 2's test either prints
5200 from the committed inputs or is red. M07's pooled 5431 was in view when
the rule was written, and the rule is survivable for one reason, stated so a
seat can check it: **it takes the only population under which the run in
view fails the gate.**

| population | p95 | band | point | M07's 5431 reads |
|---|---|---|---|---|
| mandated shape, n = 40 (**the rule**) | 3769 | 4334–6030 | **5200** | **OVER** |
| as-run three-call, n = 59 | 5004 | 5755–8006 | 6900 | within |
| pooled, n = 73 | 5431 | 6246–8690 | 7500 | within |

Predicted now, so it is not read later as a surprise: the M07 re-score at
PR 2 prints 12/25 with the join byte-identical and the latency line
`suite latency  OVER p95=5431ms over 5200ms`. Two things PR 2 carries for
this: the census record digests the manifest, so
`milestones/M08/context-census.json` is re-produced with that one digest line
moved, shown key by key, on the census rule's three keys; and
`test_the_suite_percentile_budget_was_not_raised` — the test that refused a
raise for two milestones — is the test the derived pin replaces, with the
rule in its docstring. The gate moves in PR 2 because PR 2 is the last PR at
which the fresh number does not exist.

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| Per-call `inputTokens` in the answer file, so the join reads the run and not a census | `core/toolloop.py` records each round's usage beside the totals it already sums; `handler.py` returns it; `run_with_tools.py` writes it under `usage.calls`; `audit.schema.json` admits it | PR 2: the totals equal the sum of the per-call values by test; the round-1 pin (the first request is `system`, the viewer turn verbatim, and `toolConfig`, nothing else) in two halves — **behavioural on the loop** (`tests/test_tool_loop.py`: the first transcript `converse` receives is the caller's `messages`, deep-equal) and **structural on the handler** (`tests/test_handler_wiring.py` reads `handler.py` as a tree, never as text: `messages` bound once from the event, never touched after the bind, the model call's literal exactly `modelId`, `messages=transcript`, `inferenceConfig` plus the pinned `system`/`toolConfig`, and `kwargs` never read back). `run_turn` does not assemble the request, `handler.py::_converse` does; the handler holds boto3 and G8 forbids a hermetic test from importing it, so there is no client double to drive (ADR-074 amendment 2 §3 corrects amendment 1's ask). M07's committed files, which carry no per-call usage, still score 12/25 with the join byte-identical to `rescore-join.json` (the absence path; the presence path is proved on planted files until PR 3) |
| The call count in the budget verdict, so *"tokens_in=8181 over 7700"* says it was a four-call turn | `evals/deterministic.py` names `calls` when `usage.calls` is present and omits it when it is not | PR 2: a planted three-call and four-call usage each name their count; M07's files produce the same verdict strings they produce today. **The scorer is on no `pave/twokey.py` rule today** and joins one in the diff that changes it — AI Quality with Platform Engineering, the derivation pin's pair — with a `_blocked_for` plant |
| A latency ceiling derived before the run, from the shape and not from the run | ADR-014 amendment 3, in the wording ADR-074 decision 3 §5 pre-registers; `gates.budgets.p95_ms` in the manifest; the derivation test extended to `p95_ms` | PR 2: the test computes the mandated-shape p95 from the M07 files joined to the census's `mandated_calls`, the band, and the point by the pinned rule, and asserts the manifest carries **5200**; every constant planted is red; the census record re-produced with its manifest digest line moved and nothing else, on three keys; the two-milestone refusal test replaced by the pin |
| The run, on the real path | `run_with_tools.py` k=3 through the deployed gateway at the pre-flight SPEC/07 fixed; the refusals sidecar; `topic_baseline.py --all` | PR 3: committed under `milestones/M08b/` as `goldens-run-{1,2,3}.json`, their trajectories, `goldens-run-refusals.json`, `topic-baseline.json`, `goldens-score.txt`; the pre-flight header names the deployed function, both guardrail versions and bundle digests equal to the tree at PR 2's merge |
| The calibration call | One gateway turn on `blackout-008`'s viewer turn with `tools` absent, same `system` — sent by `run_with_tools.py --calibrate <case> --out milestones/M08b/calibration.json`, **added in PR 2** on the producer's rule and tested hermetically (the event carries no `tools` key and the same `system`), committed with its audit record id; the refused-turn fallback above | PR 3: `milestones/M08b/residual_attribution.py` reads A, B, E, S and prints D and F with signs; `tests/test_m08b_residual.py` pins the record and refuses a planted A, B or E. **Reader, test and record sit on the census rule widened over `milestones/M08b/` in PR 2's diff**, the diff that creates them (ADR-060's precedent) |
| The join | `milestones/M08b/fresh_join.py` over the three answer files' `usage.calls` and the three single-file transcripts; one row per sample, with the near-miss columns, the fresh re-derived band, the fresh mandated-shape p95 beside the pooled p95, and per-round growth per sample against the replayed transcript at the measured density | PR 3: `tests/test_m08b_fresh_join.py` pins the record byte for byte; a planted verdict, a planted call count and a foreign ceiling each move it or are refused. On the same widened rule; written and pinned in PR 2, before the data it reads exists |
| Nothing else moved | `git diff` of `services/highlights-agent/evals/`, `platform/gateway/policy/`, `data/catalog.json`, `platform/infra/lib/gateway-stack.ts` and every topic file between PR 1's merge and PR 3's branch point, empty; `probes_sha256`, `g4_cases_sha256`, the judge digests and `context_census.py --check` unchanged since PR 2's merge (PR 2 moved the record's manifest digest line, and that line only) | PR 3, in the PR body |
| The entry | `run_evals --record --tag m08b --target highlights-agent` with `refused` per case, `samples_from` naming the three files, recorded with `HEAD` at PR 2's merge before the branch's first commit (M07's ordering) | PR 3: three keys; **`README_GOLDENS` gains `m08b` and the row's bold `N/25` in the same PR**, because `pave/history.py::check_readme` refuses a goldens entry whose row is pinned to none and `pave gate history` runs it; the entry cannot wait for PR 6 instead, because the recorder names `HEAD`. PR 6 flips the ✅ and writes the journal |

## Pre-registered, in ADR-074

- **D1** — the split in place, on ADR-054's precedent. What is corrected and
  what is left as-run, including every "M09 PR 1" written between the M07
  close and that ADR.
- **D2** — answer quality has no claim and no row. The seven browse-gap cases
  and the five `tokens_out` cases are owned and unscheduled with the trigger
  above, on the claim-10 precedent.
- **D3** — the claim and its falsifiers; the count band; the refusal band;
  the `recommend-003` rule; the residual rule; the `p95_ms` rule and its
  band, with the point rule executed by PR 2's test.
- **D4** — the order of the debts against the run: which land before it, which
  after, which never in this milestone.
- **The repository setting** — `delete_branch_on_merge` is off, verified.

## Implementation constraints, binding

1. **No case, tier, ceiling, prompt, tool spec, tool result field, topic
   wording, guardrail, catalog or Cedar policy moves before the run**, and
   none moves in this milestone but the suite `p95_ms` gate in PR 2; the DMA
   rename gave way to the cap's fallback at PR 1b and is M09 PR 1's by name.
   `tokens_in` stays 7700, `tokens_out` and `max_ms` and every tier stay
   where ADR-014 put them.
2. **The only gateway change before the run is usage reporting.** Per-call
   usage is added beside the totals; the totals are computed as they are
   today and a test asserts they equal the sum. No verdict on any committed
   file moves; the M07 re-score at 7700 prints the join M08 pinned.
3. **The `p95_ms` rule is executed, not argued.** PR 1 writes it; PR 2's test
   computes the number from the committed inputs and pins the manifest to it;
   PR 3 compares the fresh run against it and moves nothing. The rule reads
   the mandated shape's p95 and ADR-014's two band constants, never a pooled
   p95 of any run.
4. **The DMA rename never precedes the run.** It is re-dated to M09 PR 1 by
   the fallback in ADR-074 decision 4, taken at PR 1b when the cap was
   reached before PR 5 (ADR-074 amendment 1 §6), and lands there in no PR
   with anything else.
5. **One run, k=3, committed as-run, majority against majority.** SPEC/07
   constraint 9's INFRA rule: a sample with an INFRA case is re-run whole,
   once, with the bad sample committed beside it as `*-infra.json` and passed
   to nothing; a second INFRA sample closes the milestone with what it has.
   No re-run selection, no case edit, no baseline reset.
6. **The pre-flight before the first call**, as SPEC/07's Definition of done
   fixed it: the deployed function, both guardrail versions read from its
   configuration, the bundle digests equal to the tree; a run whose records
   name any other version is not a reading.
7. **Seats on PR 2 only, planned as two rounds** — the second on the first's
   fixes — before the PR opens, because a round on nine items produces M08
   PR 3's seventeen findings with fixes in the same PR. The seats are told
   what to plant, not what to read: a per-call list whose sum disagrees with
   the total; a verdict that names `calls` from the total rather than the
   list; a foreign population in the p95 test; a `fresh_join.py` that reads
   the ceiling from the manifest rather than the cases file; a calibration
   event that carries `tools: True`. Attestations wherever `pave/twokey.py`
   demands them, on every PR.
8. **Model calls in PR 3 only**: 75 turns for the run, 1 for the calibration
   call (2 if the fallback is taken), and headroom of one whole-sample re-run
   (75) for an INFRA sample — ceiling **152 turns**, all through the deployed
   gateway. PRs 1, 1b, 2, 4 and 6 are zero. `make check` stays hermetic. No probe run: no guardrail,
   policy, corpus or scoring path moves, and the usage field is read by no
   scorer but `budget`.
9. **The two triggers are read, not diagnosed.** A browse-gap or `tokens_out`
   reading is a count in the record and a sentence in the journal; no tool,
   tier or case changes on it here.
10. **The deletability audit is a standing step on every PR.** Every check the
    PR adds is deleted in turn, from a working copy backed up to a temp
    directory and never restored with `git checkout`, and the suite re-run;
    the PR body names each one and whether it went red. A silent check gets a
    test before merge, or the check comes out.

## What it builds

**PR 1 (this):** ADR-074; this spec; the `08b` row in `README.md`, `BUILD.md`
and `SPEC/README.md`; the ADR index row. Zero model calls, no code, no case,
no threshold, no deploy.

**PR 1b — the cold read.** ADR-074 amendment 1 and the corrections it names,
in this file; the ADR index row. Zero model calls, no code, no case, no
threshold, no deploy. **The sixth slot**: the cap was reached before PR 5, so
the DMA rename gave way by name to M09 PR 1 — the one slide ADR-074 decision
4 pre-authorised — and PRs 2–6 keep their numbers so every reference here
stays valid; there is no PR 5.

**PR 2 — the instrument before the run. Seats review this PR and no other,
in two rounds.** Per-call usage in the loop, the handler, the answer file and
the audit schema (constraint 2); the calibration producer on
`run_with_tools.py`; `calls` in the budget verdict, with `evals/deterministic.py`
put on a two-key rule in the same diff; the `p95_ms` rule executed in
`tests/test_budget_derivation.py` and the manifest gate moved to 5200, the
two-milestone refusal test replaced by the pin, the census record re-produced
with its manifest digest line moved, with ADR-014 amendment 3 in the
pre-registered wording; the direct `BANDS` pin; the round-1 pin in two
halves — behavioural on the loop in `tests/test_tool_loop.py`, structural on
the handler in `tests/test_handler_wiring.py` (G8 forbids importing it), on
the handler's rule; `residual_attribution.py`, `fresh_join.py`
and the F/G reader written and tested on planted answer files under `tests/`
before any real one exists, the F/G reader reproducing G = 8, F = 1 from
M07's files; the census rule widened over `milestones/M08b/` readers, records
and `calibration.json` in the same diff, with a `_blocked_for` plant each.
Hermetic; no deploy. One question for the seats: *does the instrument record
what the run does, and move nothing about what the run is?*

**PR 3 — the run.** `make core`; the pre-flight; the calibration call; the
k=3 run; `topic_baseline.py --all`; the entry recorded on three keys with
`HEAD` at PR 2's merge, **with `README_GOLDENS` and the row's bold `N/25` in
the same PR**; the join read against the claim, with the near-miss columns
and the fresh re-derived band; the count against [7, 14]; refusals against
0–2; `recommend-003` read by the F/G reader with `read_withheld.py --show` and
the verification lines committed as `withheld-read.txt`; the residual
attributed with signs; **the fresh pooled p95 and the fresh mandated-shape
p95 both read against 5200**; both triggers read from the trajectories and
the transcript. ADR-074 amended with every number in the pre-registered
words, **citing only commits reachable from `main` or from a `cited-*` tag
pushed before the merge** — PR 4's citation rule, applied to this PR's text
before it merges, because in a fresh clone every branch is a remote-tracking
ref and PR 4 would otherwise open red on PR 3's own sentences. PR 3 records
the numbers; it does not explain them. **If the claim's falsifier fires, the
claim's reading stops here, the sample is recorded with its row of the
near-miss table, PRs 4 and 6 proceed, and PR 6 closes red.**

**PR 4 — the hermetic debts.** Zero calls, no seat round, attestations only,
each on the rule its file already sits on: a `pave/twokey.py` rule over
`.gitattributes` with a test that the index carries no CRLF blob under
`text=auto eol=lf` and that every digesting reader normalises (a planted CRLF
copy of a committed evidence file hashes to the committed pin); the
templates' condition — a scaffolded service that offers a second tool cannot
keep the one-tool `tokens_in` silently, stated in the template and refused by
`pave verify` on a manifest that offers two tools with the template's number
verbatim, and the same condition on the template's `p95_ms: 2500`, which PR 2
derived to 5200 for the reference service and left in the template (Platform
Engineering seat, round 1); a check that every ADR under `docs/adr/` has an index row and that
an ADR carrying an `## Amendment` heading has a row that names it; the
cited-commit decision — `close-milestone` step 7 says the cited commits are
tagged before the merge, and `tests/test_cited_commits_resolve.py` counts a
citation reachable only from a remote-tracking branch as unreachable, so a
stale ref cannot make it green; `tests/test_g4_capture_boundary.py`'s
`SKIP_DIRS` matched against the tree-relative path, with an anti-vacuity
guard that reads the real tree — moved here from PR 2 because it touches
nothing the run records or is compared to, on the same two keys (Platform
Engineering, Security) PR 4 collects as attestations; the six *M08* code
sites left as they are, because they say M10 and mean M10.

**PR 5 — gave way.** The DMA rename (SPEC/06b A21, slid three times) was this
PR; the cap was reached before it at PR 1b, and it took the fallback ADR-074
decision 4 pre-registered — **M09 PR 1, by name**, because M09 re-freezes the
judge for the `brand_tone` widening anyway and the two re-freezes become one.
The fourth slide of that debt and the only one this milestone pre-authorised.
Nothing lands in a PR 5; the close's journal records the slide as taken.

**PR 6 — close.** Journal; step 6b read from PR 3's `topic-baseline.json`
and refusal census; the progression row's ✅; tag `m08b`.

## What it does not build

The rules registry, any change to `rules/`, a disclosure case, a guardrail
line, Act 3 (M09's) · a fix for `catalog-search`'s browse gap or a move of
any `tokens_out` tier (unscheduled, ADR-074 decision 2) · a fix for
`recommend-003`, of either kind (its own ADR after the reading) · a
re-derivation of `tokens_in` (a census milestone, if the claim fails) · a
`p95_ms` number chosen from any run's pooled p95 · the `brand_tone` widening
(M09, the milestone that adds graded content; ADR-026 amendment 3 stands) ·
ADR-053's two halves (M09's, re-dated by name in ADR-074) · ADR-069 D5 cut 2
(one arm runs) · `usage.tokens_in: 0` on refused answers · a probe run · a
judged entry · the headroom check · **a sample selected, re-run, or read at
any ceiling but 7700.**

## Obligations inherited, each with a date

| debt | owed to | date |
|---|---|---|
| Per-call `inputTokens` in the answer file, and one calibration call with tools offered | Platform Engineering + AI Quality | **PR 2** (the producer), **PR 3** (the call and the reading) |
| `calls` in the budget failure record | AI Quality + Platform Engineering | **PR 2** |
| `evals/deterministic.py` — the scorer every goldens verdict comes from — on no `pave/twokey.py` rule (ADR-074 amendment 1 fact 3; ADR-037's shape) | AI Quality + Platform Engineering | **PR 2**, in the diff that changes it |
| `milestones/M08b/` readers, records and `calibration.json` on no rule; the claim's reader editable on one key | AI Quality + Platform Engineering + Security | **PR 2**, the census rule widened in the diff that creates them |
| The rule that derives a suite `p95_ms`, written before the run and applied after | AI Quality + Platform Engineering | **PR 1** (the rule), **PR 2** (executed, 5200), **PR 3** (applied, two numbers) |
| `BANDS` in `tests/test_budget_derivation.py` on no direct pin | AI Quality + Platform Engineering | **PR 2** |
| `recommend-003`'s answer-channel refusal, read by the pre-registered rule through a reader | Security (with Legal/S&P if it reads as answer policy) | **PR 2** (the reader, reproducing G = 8, F = 1), **PR 3** (the reading) |
| The calibration call's producer and its refused-turn fallback | Platform Engineering + AI Quality | **PR 2** (the flag), **PR 3** (the call) |
| `tests/test_g4_capture_boundary.py` vacuous under a `.claude/` checkout | Security + Platform Engineering | **PR 4** (moved from PR 2 by ADR-074 amendment 1 §3) |
| `.gitattributes` on no `pave/twokey.py` rule; 191 CRLF files in the working tree against an LF index | Platform Engineering | **PR 4** |
| `templates/agent-tools/` carries 6000/6500 and `p95_ms: 2500`, correct for one tool and wrong the moment a second is offered | ADR-047's four seats | **PR 4** |
| The ADR index enforced by nobody | PM | **PR 4** |
| A document citing its own branch commits is a citation with a fuse; `make check` green on stale remote-tracking refs (47 today by `git remote prune --dry-run origin`) | Platform Engineering + PM | **PR 4** |
| The DMA rename (SPEC/06b A21), slid from M07 to the SPEC/08 PR to M09 PR 1 to this milestone's PR 5 | Legal/S&P + Data Governance | **M09 PR 1, by name** — the fallback taken at PR 1b when the cap was reached before PR 5 (ADR-074 decision 4; amendment 1 §6); the fourth slide, and the only one pre-authorised |
| The seven browse-gap cases | Tool Owner | **owned, unscheduled**; trigger *persists on this run*, read at PR 3 (ADR-074 decision 2) |
| The five `tokens_out` cases at unchanged tiers | AI Quality | **owned, unscheduled**; same trigger, read at PR 3 |
| GitHub's *automatically delete head branches* against `close-milestone` step 7 | the operator | **paid** before this milestone opened; `delete_branch_on_merge: false` verified 2026-09-07 (ADR-074) |
| The `brand_tone` widening | AI Quality | **M09**, unchanged (ADR-026 amendment 3) |
| ADR-053's *no orphan rules* (term undefined) and *no immortal rules* (`effective` optional) | Legal/S&P + Security | **M09**, re-dated by name from "M07" (ADR-074) |
| ADR-069 D5 cut 2, the paired diff's partition | the next two-arm run | unchanged; one arm runs here |
| `usage.tokens_in: 0` on refused answers | – | unchanged |
| Retention on the withheld store (ADR-071 amendment 1); the two `tool_request` probes' re-opening condition | Data Governance; Security | step-6b triggers, read at PR 6 |

## Bounded

- **Cap: six PRs, spent** — PR 1, PR 1b, PRs 2, 3, 4 and 6. Six were planned
  with no spare; PR 1b reached the cap before PR 5, and the DMA rename gave
  way by name, as pre-registered. Reaching it again closes the milestone, red
  if necessary, with no further item to give way; any other slide is a
  finding.
- **Seats on PR 2 only, two rounds.**
- **Model calls in PR 3 only, ceiling 152 turns.**
- A discovered defect is recorded with a deadline and left alone.

## Demo artifact

```bash
python milestones/M08b/fresh_join.py --check
python -m evals.run_evals --arm tools \
    --answers milestones/M08b/goldens-run-1.json \
    --answers milestones/M08b/goldens-run-2.json \
    --answers milestones/M08b/goldens-run-3.json \
    --refusals milestones/M08b/goldens-run-refusals.json
python -m evals.refusals --sidecar milestones/M08b/goldens-run-refusals.json
```

Predicted, not yet measured — the second command after PR 3 merges:

```
OK: milestones/M08b/fresh-join.json is what the committed inputs produce
N/25 passed (M failed, 0 infra) — judge axes recorded ADVISORY, not scored (ADR-012)
of the M failed: R were refused before scoring, A answered and scored wrong
refusals: S/S resolved to P (mechanism, assessed) pair(s) — …
suite latency  <OVER|within> p95=Pms <over|within> 5200ms
channels: tool_request 0 · answer R' · question 0 · tool_output 0
```

with **N = 12** predicted and 7 ≤ N ≤ 14 the bound, R ≤ 2, no `TOPIC:*` on
`tool_request` or `tool_output`, every `budget` failure naming its `calls`,
and 5200 the number PR 2's test prints; the first command's output carries
the fresh mandated-shape p95 beside P. Today the same command prints nothing:
no file under `milestones/M08b/` exists.

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: every fresh ≤3-call answered sample passes `tokens_in` at 7700, every ≥4-call sample fails it, per sample | `fresh_join.py` over the answer files' `usage.calls` and the three single-file transcripts; `fresh-join.json` pinned; the two falsifiers read empty; the comparison is `got > limit` and the join says so | PR 3 |
| 2 | The count: 7 ≤ N ≤ 14, predicted 12; no 3-of-3 pass regressed, no 0-of-3 fail flipped | `goldens-score.txt`; the join's per-case table against `rescore-join.json` | PR 3 |
| 3 | Refused by majority 0–2 | `evals.refusals --sidecar` | PR 3 |
| 4 | `recommend-003`: F and G read by the rule; the reading named | the F/G reader over the sidecar, the answer files and `withheld-read.txt` (`read_withheld.py --show`); the reader reproduces G = 8, F = 1 from M07's files as its test | PR 2 (reader), PR 3 |
| 5 | The residual: D and F from A, B, E, S, with signs; the trigger's state | `calibration.json` from the `--calibrate` producer, round-1 usage, `residual_attribution.py`, its pin; E by named key; the refused-turn fallback named | PR 2 (producer, reader, rule), PR 3 |
| 6 | The round-1 request is `system`, the viewer turn verbatim and `toolConfig`, nothing else | behavioural on the loop (`tests/test_tool_loop.py`) and structural on the handler (`tests/test_handler_wiring.py`, a tree and never text; G8 forbids driving the handler) — ADR-074 amendment 2 §3 | PR 2 |
| 7 | Per-call usage sums to the totals; no committed verdict moves | a test; the M07 re-score's join byte-identical to `rescore-join.json` (the absence path; the presence path on planted files until PR 3) | PR 2 |
| 8 | `calls` in the verdict when per-call usage exists, absent when it does not | a test with a planted usage each way; M07's verdict strings unchanged; the scorer on a rule with a plant | PR 2 |
| 9 | The `p95_ms` rule yields 5200 from the mandated shape and ADR-014's constants | the derivation test: n = 40, p95 3769, band, point; every constant planted red; the refusal test replaced; the census record's digest line re-produced | PR 2 |
| 10 | The fresh p95 against 5200 — pooled, and mandated-shape beside it | `goldens-score.txt`'s latency line; `fresh_join.py`'s mandated-shape p95 line; the two readings above | PR 3 |
| 11 | Browse gap persists or not | the fresh trajectories joined to `calls` per sample; the count of ≥4-call samples on the seven cases | PR 3 |
| 12 | `tokens_out` five persist or not | the transcript's `tokens_out` verdicts by majority on the five | PR 3 |
| 13 | Nothing else moved before the run | `git diff` between PR 1's merge and PR 3's branch point over the named paths; the digest families; `context_census.py --check`, green at PR 3 because PR 2 re-produced the record's manifest digest line | PR 3, with PR 2 named |
| 14 | The deployed bundle equals the tree | the pre-flight header in the sidecar | PR 3 |
| 15 | `BANDS` directly pinned | a test that plants each constant | PR 2 |
| 16 | The G4 boundary test scans the tree under a `.claude/` checkout | the anti-vacuity guard reads a real file count | PR 4 |
| 17 | `.gitattributes` on a rule; no CRLF blob in the index; digesting readers normalise | the twokey rule's plant; the eol test; the planted-CRLF digest test | PR 4 |
| 18 | A two-tool scaffold cannot keep the one-tool ceiling silently | `pave verify` refuses the planted manifest | PR 4 |
| 19 | Every ADR indexed; every amended ADR's row names its amendment | the index test, red on a planted ADR and a planted amendment | PR 4 |
| 20 | A cited commit reachable only from a remote-tracking branch is unreachable | the citation test, red on a planted ref | PR 4 |
| 21 | The DMA rename moves every digest it must and nothing else | not measured here: the rename gave way to M09 PR 1 by the fallback at PR 1b | none, by the cap |
| 22 | Zero model calls in PRs 1, 1b, 2, 4, 6; PR 3 within 152 turns | the PR bodies; no new file under `milestones/M08b/` carrying `usage` outside PR 3 — PR 2's planted answer files live under `tests/` for that reason | every PR |
| 23 | The entry on three keys with `refused` per case; the row | `pave gate history`; `README_GOLDENS` and the bold cell in PR 3; the ✅ in PR 6 | PR 3, PR 6 |
| 24 | `delete_branch_on_merge` is off | asserted from the API on 2026-09-07 and recorded; no hermetic test can read a GitHub setting, and the close-milestone step stays the rule | PR 1, recorded |
| 25 | A falsifying sample is recorded with its row of the near-miss table; when the claim holds, whether 7700 sits in the fresh re-derived band | `fresh_join.py`'s distance columns, the fresh mandated-shape maximum, the fresh four-call minimum and the band they re-derive | PR 3 |
| 26 | The rule's premise — the mandated shape's latency tail is stable across runs — holds or not | the fresh mandated-shape p95 against 5200 | PR 3 |
| 27 | PR 3 cites only commits reachable from `main` or a `cited-*` tag | PR 4's citation rule run over PR 3's text before PR 3 merges; a red at PR 4 on PR 3's sentences is a finding about PR 3 | PR 3 |
| 28 | A calibration turn refused on the `answer` channel still yields B | the audit record's per-call usage, or one re-issue on `entitlement-010` with the substitution recorded | PR 3 |

Every row has a PR or says why not. Row 21 is not measured in this milestone
because the cap took it; row 24 is asserted rather than measured, and says so.

## Definition of done

- [ ] ADR-074 merged with the `08b` row in `README.md`, `BUILD.md` and
      `SPEC/README.md` and the index row, in one diff; `make check` green with
      the new row; nothing below row 08b renumbered.
- [x] PR 1b: ADR-074 amendment 1 merged with this file's corrections and the
      ADR index row in one diff; zero model calls; the cap's fallback taken by
      name.
- [ ] PR 2: per-call usage recorded and summed, the round-1 pin as a
      behavioural test, `calls` in the verdict with the scorer on a rule, the
      calibration producer, the `p95_ms` rule executed and the manifest pinned
      to 5200 with the refusal test replaced and the census record's digest
      line re-produced, ADR-014 amendment 3 in the pre-registered wording, the
      `BANDS` pin, the three readers tested on planted files under `tests/`
      (the F/G reader reproducing G = 8, F = 1), the census rule widened over
      `milestones/M08b/`; two seat rounds' findings in the PR; attestations
      per `pave/twokey.py`; the M07 re-score's join byte-identical and its
      latency line `OVER p95=5431ms over 5200ms`; **the deletability audit in
      the PR body, every new check named with its result.**
- [ ] PR 3: pre-flight printed before the first call; the run committed
      as-run; the calibration call committed with its record id (or the
      fallback taken and recorded); the entry on three keys with
      `README_GOLDENS` and the bold cell; the join read against the claim
      (**the claim**), with the near-miss columns and the fresh band; N
      against [7, 14], refusals against 0–2, F and G by the reader, D and F by
      the rule with signs, the fresh pooled and mandated-shape p95 against
      5200, both triggers (**the side-predictions** — a miss is a finding
      about the side-prediction and does not fail this box's first item);
      `withheld-read.txt` committed; ADR-074 amended, citing only commits
      `main` or a tag reaches; **the deletability audit on the two pin
      tests.**
- [ ] PR 4: each hermetic debt paid on its own rule with its plant named; the
      G4 boundary test's guard; **the deletability audit on every check
      added.**
- [ ] PR 5: none — gave way at PR 1b; the DMA rename is M09 PR 1's by name.
- [ ] Nothing under `milestones/M07/` changed; nothing under
      `milestones/M08/` changed but `context-census.json`'s manifest digest
      line, which PR 2 re-produces, and that line only.
- [ ] `close-milestone` in order; journal, recording the slide as taken;
      the progression row's ✅; tag `m08b`. Six PRs, spent.

## What must not happen

No case, tier, token ceiling, prompt, tool spec, tool result field, topic,
guardrail, catalog or policy change before the run. No `p95_ms` number chosen
from any pooled p95, and no `p95_ms` verdict read on one number. No sample
selected, re-run until it fits, or read at any ceiling but 7700. No DMA rename
in this milestone: it is M09 PR 1's by the fallback, and never in the same PR
as anything else. No diagnosis of the browse gap, no fix for `recommend-003`, no
tier move on a `tokens_out` reading. No history entry edited; no baseline
reset. No registry work. No claim rewritten to match the outcome: if a fresh
sample lands on the wrong side of 7700, the claim failed, the sample is
named, and the milestone closes red.

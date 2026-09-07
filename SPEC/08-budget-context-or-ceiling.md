# M08 — the tools arm's budget: the context or the ceiling

**Written after the census and before any ceiling moves.** Owned by the PM
seat. Branch `m08-budget`, tag `m08`.

**Deliberately short**, in SPEC/07's shape. Every decision lives in ADR-073;
every "what broke" goes to the journal at close. This file states the
milestone and nothing else.

## Why

M07 closed at 2/25 with the first goldens entry since M06, and all 22
answered-and-wrong cases fail `budget` on `tokens_in` — 6022 to 9220 against
6000, fifteen on nothing else. Refusals had hidden it since M06b. The journal
made it M08's first question and the operator decided M08 answers it before
the rules registry touches the tools arm (ADR-073 D1).

PR 1 ran a zero-call census over the committed trajectories
(`milestones/M08/context-census.json`, produced by `context_census.py`, pinned
by `tests/test_m08_census.py`). It says: `tokens_in` is a sum over the turn's
model calls; every 2-call turn is under 6000 and every 3-call turn is over it;
the modal turn went from 2 calls to 3 when `entitlement-check` became a second
sequential tool round at M06b, and the per-call base from 1693 to 2057; the
per-call base is 1859–1974 of which committed text explains ≈1437; tool
results are 15–216 characters; and no sample over the ceiling at its mandated
call count carries any evidenced removable content. The pre-registered rule
picked **outcome B**. Outcome A — fix the agent, ceiling unchanged — was
pre-registered, was not picked, and the reading that briefly printed it is in
the record (ADR-073 D2).

**No claim in the twelve-claims table is assigned to it**; it makes claim 6's
suite scorable on the tools arm and serves claim 2 defensively (a gate whose
budget axis cannot discriminate teaches nothing).

## The one claim

**The `tokens_in` ceiling re-derived from the committed stage-2 census by
ADR-014's pinned rule — within 1.15–1.60× the mandated-shape maximum of 6235,
placed below the minimum 4-call turn of 8181 — passes every committed stage-2
answered sample at three model calls or fewer and fails every sample at four
or more, with no case, prompt, tool, topic or other assert moved, on the same
three answer files M07 recorded.**

Beside it, pre-registered and **not the claim** — *restated by amendment 1
before PR 3, the original wording quoted there*: PR 4's re-score prints
**N/25 with 2 ≤ N ≤ 12**, where the cases that flip from FAIL are exactly
those that fail `budget` on `tokens_in` alone at M07 and pass every other
assert, `tokens_out` included, on the ≤3-call majority — ten cases, named in
amendment 1 with the per-sample transcript they are read from; five
budget-only cases fail `tokens_out` at unchanged tiers on the majority and
cannot flip. Falsifiers of the claim: the rule yields no number (band floor
at or above 8181); any 3-call-or-fewer sample over the number it yields; any
4-call-or-more sample under it. Falsifiers of the side-prediction, each a
finding about the side-prediction and not a failure of the claim: any case
flipping on a 4-call majority; any case flipping that failed another assert
at M07; any of the five flipping; any of the ten not flipping. **N = 11 is
the second kind**: PR 4 records which case did not flip and why, and the
claim stands or falls on the per-sample join alone.

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| Where the tokens go, by call and by component, read before any number is proposed | `milestones/M08/context_census.py` over M02, M06, M06b, M07 stage 1 and stage 2; replay over the committed catalog; ADR-014's anchors for the estimated rows | PR 1: `tests/test_m08_census.py` — the record is what the inputs produce; no network import; no other ceiling; per-sample rule; a planted token moves the record |
| A rule that picks between the two outcomes, fixed before the reading | ADR-073 D2; `decision_rule()` in the reader | PR 1: the record carries the reading and the cross-sample figure that is not the rule |
| The mandated shape of a case, from its asserts | `mandated_calls()`: 2, or 3 when the case expects `entitlement-check` before the answer | PR 1: pinned against `cases.yaml` |
| A ceiling derived by rule, not by count | ADR-014 amendment 2; `BANDS` in `tests/test_budget_derivation.py` re-pointed at the census record; 25 case budgets; manifest `max_tokens_in` | PR 3: the derivation test reads the census's mandated-shape maximum and the 4-call minimum; the number sits in [7170, 8180]; seats review this PR |
| The count, on the real path | The committed stage-2 answer files and sidecar, re-scored with `run_evals --arm tools` at the signed ceiling | PR 4: the transcript committed as `milestones/M08/goldens-rescore.txt`; verdicts by call count checked against the census's per-sample table |
| Nothing else moved | `context_census.py --check`; `git diff` of `milestones/M07/` empty; `probes_sha256`, `g4_cases_sha256`, the judge digests unchanged | PR 3 and PR 4, each |
| The entry, if recorded | `run_evals --record` with `refused` per case (ADR-069 D5 cut 1), `samples_from` naming M07's files by sha256 | PR 4: three keys; PR 5 closes with the row |

## Pre-registered, in ADR-073

- **D1** — the ordering. Recorded, not argued. The sweep, and the one file
  ADR-070's sweep missed.
- **D2** — the two outcomes and the per-sample rule; the census's reading;
  the reader's first run, which printed A under an incoherent reading.
- **D3** — how a ceiling may move under G9: the band from ADR-014's pinned
  rule, placed below the next call count; the ordering as the protection;
  what the ceiling will still catch (every 4- and 5-call turn, which is the
  browse gap wearing a budget number).

## Implementation constraints, binding

1. **No ceiling moves before the ADR-014 amendment that derives it**, and the
   amendment cites the census and the placement rule, never which cases pass.
2. The reader prints no pass count at any ceiling other than 6000; PR 4 is
   the first pass count at the new one.
3. Nothing under `milestones/M07/` changes. The re-score reads those files by
   their committed sha256.
4. No case's asserts move except the `tokens_in` value of `budget`;
   `tokens_out`, `max_ms` and the output tiers stay where ADR-014 put them.
5. No prompt, tool spec, tool result field, topic wording, or gateway code
   moves in M08. Changing the shape while re-deriving a ceiling for it would
   make the derivation about nothing.
6. Zero model calls, no deploy, for the whole milestone. A re-score is not a
   run; the `usage` fields are read, never written.
7. Seats on PR 3 only. Attestations wherever `pave/twokey.py` demands them.
8. The history entry, if any, is a new row at PR 3's merge sha with
   `samples_from` naming M07's files; nothing in `evals/history/` is edited.

## What it builds

**PR 1 (this):** the census, its reader and pin test; ADR-073 and the sweep
(`README.md`, `BUILD.md`, `SPEC/README.md`, `docs/governance/demo-script.md`,
`docs/governance/recordings.json`, `quality/judge/calibration/labels.json`
with ADR-026 amendment 3); the ADR index rows 058–073; this spec. Zero model
calls. Two keys on the recordings register (Platform Engineering, AI Quality)
and on the calibration owe (AI Quality, Security).

**PR 2 — the register.** Zero calls, no seat round, attestations only:
`pave/twokey.py` rules for `run_with_tools.py` (Platform Engineering + AI
Quality) and `topic-baseline.json` (Security + AI Quality) with the five-seat
pin in `tests/test_twokey_seats.py`; the six *M08* code sites corrected to
*M10*; ADR-070 amendment 8 re-deriving decision 2's channel table from M06b's
sidecar with `evals.refusals --sidecar`. *And, by ADR-073 amendment 1
(accepted in full):* this spec's amendment 1 — the side-prediction restated
and its bound re-derived from a per-sample transcript at 6000; the residual
as a dated debt with the M02-to-stage-2 differential run in the same diff;
the three dispositions PR 3 was to carry — Security's two `tool_request`
probes, `recommend-003`'s held text read against `DEC-001`, Data
Governance's answer on ADR-071 decision 4 — as written dispositions with
attestation lines (ADR-070 amendment 8, ADR-071 amendment 1); `p95_ms` as a
standing finding; and ADR-014 amendment 2's wording pre-registered in ADR-073
amendment 2 so PR 3 fills in the number only.

**PR 3 — the ceiling. Seats review this PR and no other.** ADR-014 amendment
2: the number, argued from the census by the pinned rule inside [7170, 8180]
and placed below 8181, in the wording ADR-073 amendment 2 pre-registers; the
25 case budgets; `max_tokens_in` in the manifest;
`tests/test_budget_derivation.py` re-pointed at the census record with the
same bands. One question for the seats: *is this number produced by the rule
from the record and by nothing else?* The `p95_ms` disposition and the three
seat dispositions this paragraph first dated here are PR 2's (amendment 1).

**PR 4 — the re-score.** `run_evals --arm tools` over M07's three stage-2
answer files and sidecar at the signed ceiling; the transcript committed; the
count read against the falsifiers; the entry recorded on three keys if the
seats' PR-3 disposition allows it; ADR-073 amended with the count.

**PR 5 — close.** Journal — carrying the residual's debt row, the `p95_ms`
standing finding and the two step-6b triggers PR 2 recorded — progression
row, tag `m08`.

## What it does not build

A fresh k=3 run (the question is about a fixed shape; a fresh run adds
sampling noise to it and is M09's first measurement anyway) · any agent,
prompt, schema or tool-spec change (outcome A was not picked; trimming the
schema to fit 6000 is the mirror of moving 6000 to fit it) · the attribution
of the residual 422–537 tokens per call (a dated debt since amendment 1, with
the zero-call differential PR 2 committed; the measurement that pays it is
M09 PR 1's) · `catalog-search`'s browse gap · `usage.tokens_in: 0` on
refused answers · ADR-069 D5 cut 2 (one arm) · the DMA rename · any topic
wording, probe, or guardrail change · a judge run · the headroom check · a
signed `p95_ms` ceiling (a standing finding instead; amendment 1) · **a
ceiling chosen by looking at which cases pass.**

## Obligations inherited, each with a date

| debt | owed to | date |
|---|---|---|
| `run_with_tools.py` on no two-key rule; its pre-flight header records the pinned values, not the fact each matched | Platform Engineering + AI Quality, via `pave/twokey.py` | **paid, PR 2** (the rule; the pre-flight half is recorded, not fixed — a producer change is constraint 5's) |
| `topic-baseline.json` (M07, `stage1/`, M06d, M06b) on no two-key rule | Security + AI Quality, via `pave/twokey.py` | **paid, PR 2** |
| ADR-070 decision 1's six code sites saying *M08*; they mean M10 now | three rules, one four seats; `pave/cli.py` on none | **paid, PR 2** |
| ADR-070 decision 2's channel clause; the census table re-derived from M06b's sidecar | PM | **paid, PR 2**, amendment 8 |
| The residual 422–537 tokens per call the census cannot attribute — a quarter of the per-call base, the same size with one tool offered as with two (`milestones/M08/residual-differential.json`, PR 2) | Platform Engineering + AI Quality | **M09 PR 1**: per-call `inputTokens` in the answer file, and one calibration call with tools offered (amendment 1) |
| `docs/adr/README.md`'s index, stopped at ADR-057 | PM | **paid, PR 1** (rows 058–073) |
| ADR-026's `brand_tone` widening — a wider deterministic draw, hand-labelled; a judge run | AI Quality | **re-deferred to M09** with the milestone its reason names (amendment 3, PR 1); counted as the third move |
| Security's two `tool_request` probes (`tool-name-echo`; a block naming `guardrail.id`), with the arm question first | Security | **arm question answered here:** no deployed arm can plant a model-authored tool name — the model arm sends no tools, the tool-plane arm authorizes a name the harness chooses — so under ADR-041's rule the probes credit nothing on every arm and their only observation is the loop test M07 PR 2 wrote. **Disposed, PR 2** (ADR-070 amendment 8): declined as corpus rows, the two loop tests the standing observation; re-opened by the first arm that can plant a name, a step-6b trigger |
| Suite latency OVER: 5431 ms against 2500, OVER since M06 | AI Quality + Platform Engineering, ADR-014 amendment | **Standing finding for M08, PR 2** (ADR-073 amendment 2 §4): breached by the shape — model time alone is 2289 ms at two calls, 3606 at three — not a regression; costs no case; no manifest change. The rule that derives a suite p95 is owed at **M09 PR 1**, written before the fresh run |
| Data Governance's answer on ADR-071 decision 4 | Data Governance | **paid, PR 2** (ADR-071 amendment 1): upheld, no channel exemption; retention the seat's open item as a step-6b trigger |
| `recommend-003`'s answer-channel refusal, text held | Security | **read, PR 2** (ADR-070 amendment 8; `milestones/M08/withheld-read.txt`): a schema-conforming grant carrying `entitlement-check`'s verdict, not `DEC-001`'s shape; not fixed in M08; next read at **M09 PR 1**'s fresh run |
| The DMA rename (SPEC/06b A21; re-dated to the SPEC/08 PR by ADR-070) | Legal/S&P + Data Governance | **M09 PR 1, a named slide.** It moves `data/catalog.json` — the judge's prompt digest — and the enum in the tool spec the census measures; landing it inside a milestone re-deriving a ceiling for that spec would confound the derivation (constraint 5) |
| ADR-069 D5 cut 2 (the paired diff's partition) | the next two-arm run | unchanged; M08 runs no arm |
| `catalog-search`'s browse gap | Tool Owner, no ADR | unchanged; the census names it as the source of every 4- and 5-call turn |
| `usage.tokens_in: 0` on refused answers | – | unchanged |

## Bounded

- **Cap: six PRs.** Five planned. Reaching the cap closes the milestone, red
  if necessary; closing early is a success condition.
- **Seats on PR 3 only.**
- **Zero model calls, no deploy, for the whole milestone.** PRs 1–5 read
  committed files. `make check` stays hermetic.
- A discovered defect is recorded with a deadline and left alone.

## Demo artifact

```bash
python milestones/M08/context_census.py --check
python -m evals.run_evals --arm tools \
    --answers milestones/M07/goldens-run-1.json \
    --answers milestones/M07/goldens-run-2.json \
    --answers milestones/M07/goldens-run-3.json \
    --refusals milestones/M07/goldens-run-refusals.json
```

Predicted, not yet measured — the second command after PR 3 merges:

```
OK: milestones/M08/context-census.json is what the committed inputs produce
N/25 passed (M failed, 0 infra) — judge axes recorded ADVISORY, not scored (ADR-012)
of the M failed: 1 were refused before scoring, A answered and scored wrong
refusals: 2/2 resolved to 1 (mechanism, assessed) pair — guardrail / TOPIC:entitlement-circumvention
suite latency  OVER p95=5431ms over 2500ms
channels: tool_request 0 · answer 2 · question 0 · tool_output 0
```

with **N = 12** predicted and 2 ≤ N ≤ 12 the bound (amendment 1; the
flipped set the ten it names and none of the five), every remaining `budget`
failure on a sample at four calls or more or on `tokens_out` at an unchanged
tier, and the refusal and channel lines byte-identical to M07's. Today the
same command prints `2/25`.

## Definition of done

- [ ] The census committed with its reader and pin test before any number is
      proposed; `--check` green on every PR.
- [ ] ADR-073 merged with the shift; the progression table, `BUILD.md`,
      `SPEC/README.md`, the demo script, the recordings register and the
      calibration owe agree in one diff; `make check` green with the new rows.
- [ ] PR 2: both `twokey.py` rules live with the five-seat pin, each red when
      deleted; the six sites say M10; ADR-070 amendment 8 carries the
      re-derived channel table; amendment 1 of this spec with the per-sample
      transcript; the residual's row and its differential, pinned; the three
      dispositions with their attestation lines; the `p95_ms` standing
      finding; ADR-014 amendment 2's wording pre-registered in ADR-073.
- [ ] PR 3: ADR-014 amendment 2 argues the number from the census inside
      [7170, 8180] and below 8181, cites no pass count, in the wording ADR-073
      amendment 2 pre-registers; the 25 budgets and the manifest move together;
      the derivation test reads the census; every seat's findings in the PR;
      attestations per `pave/twokey.py`.
- [ ] PR 4: the re-score transcript committed; every 3-call-or-fewer sample
      passes `tokens_in`, every 4-call-or-more sample fails it (**the claim**);
      N = 12 with 2 ≤ N ≤ 12 the bound, the flipped set exactly the ten
      amendment 1 names and none of the five (**the side-prediction** — a miss
      here is recorded as a finding about it, and does not fail this box's
      first half); refusal and channel lines unchanged; the entry recorded on
      three keys with `refused` per case, or the cell says why not.
- [ ] Nothing under `milestones/M07/` changed, by `git diff`; no digest in
      `quality/adversarial/instruments.json` or `quality/judge/frozen.json`
      moved.
- [ ] `close-milestone` in order; journal; progression row; tag `m08`. Six PRs
      or fewer.

## What must not happen

No ceiling number chosen by looking at which cases pass. No case edited but
the one `tokens_in` value, and that only after the amendment that derives it.
No prompt, schema, tool spec, tool result, topic or gateway change. No fresh
run, no re-run, no sample selection. No pass count printed by the census at
any ceiling but 6000. No file under `milestones/M07/` touched. No history
entry edited. No claim rewritten to match the outcome — outcome A stays in
ADR-073 as the outcome that was pre-registered and not picked, with the
reading that briefly printed it.

## Amendment 1, 2026-09-06 — the side-prediction was unreachable as written, and PR 2 carries what the cold read asked

**Written in PR 2, before PR 3 opens. Zero model calls.** ADR-073 amendment 1
read this spec cold after PR 1 merged and found one defect in it and four
things PR 2 should carry; the operator accepted all five. This amendment is
where the spec records them. **The claim is not changed.** The band, the
placement, the rule, its outcome and constraints 1–8 stand as written.

### The defect: the side-prediction could not be met at any number in the band

As written: *"PR 4's re-score prints N/25 with 2 ≤ N ≤ 17, where the cases
that flip from FAIL are exactly those M07 recorded as failing on `budget`
alone whose majority sample ran at three calls or fewer."* Constraint 4 keeps
`tokens_out` where ADR-014 put it, and `budget` is one assert with two halves.
Five of the fifteen budget-only cases fail `tokens_out` at their unchanged
tier on the majority of their samples — `blackout-001`, `blackout-007`,
`blackout-008`, `blackout-009`, `concise-022` — so they cannot flip on a
`tokens_in` move, and *"exactly"* is a biconditional. PR 4 would have failed
its own checkbox on those five at any number in the band, before the number
was chosen. The 17 was the M07 journal's *"strike that assert"* figure, which
strikes both halves. This is M06c amendment 1's shape — a prediction written
by the seat that had just found the shape at M07 — and it is corrected here,
before PR 3, because corrected after PR 4 prints it would be a claim rewritten
to match the outcome, which *What must not happen* forbids.

### The restatement, and the record it is read from

**PR 4's re-score prints N/25 with 2 ≤ N ≤ 12, where the cases that flip from
FAIL are exactly those that fail `budget` on `tokens_in` alone at M07 and pass
every other assert, `tokens_out` included, on the ≤3-call majority.** The
predicted value is **N = 12**; the range is the bound.

The M07 transcript prints one representative sample's failures per case, so it
cannot show a minority sample failing an assert the majority line hides. The
existing command with a single answers file prints every assert of that
sample; three such runs at 6000 — the committed ceiling, no flag added, no
number in the band used — are committed as
**`milestones/M08/per-sample-at-6000.txt`**, and the bound is read from them
with the census's per-sample call counts and `cases.yaml`'s tiers:

- **The ten that flip** (every ≤3-call sample failing on `tokens_in` and
  nothing else, on a 2-of-3 or 3-of-3 majority): `entitlement-002`,
  `entitlement-010`, `entitlement-011`, `recommend-015`, `grounded-017`,
  `grounded-019`, `brand-020`, `edge-024`, `headroom-005`, `headroom-026`.
- **The five that cannot**: `tokens_out` over its tier on three of three
  samples (`blackout-001`, `blackout-007`, `blackout-008`, `concise-022`) or
  two of three (`blackout-009`).
- The two that pass today, `grounded-016` and `brand-021`, make twelve.

No other case is budget-only by majority; every 3-call sample is ≤ 6792 and
so under the band floor; no sample is within half of `max_ms`. ADR-073
amendment 2 §1 walks the transcript case by case.

### What moved from PR 3 to PR 2, and why

ADR-073 amendment 1 §4: PR 3 as first written carried five decisions on one
seat round, M07's PR-4 shape. Three of them touch nothing the ceiling touches
and need no seat PR 2 was not already collecting, so they ride PR 2 as written
dispositions with attestation lines — Security's two `tool_request` probes and
`recommend-003`'s held text (ADR-070 amendment 8), Data Governance's answer on
ADR-071 decision 4 (ADR-071 amendment 1). The fourth, `p95_ms`, is decided in
PR 2 as a **standing finding for M08**: breached by the shape (model time alone
is 3606 ms at three calls), not by a regression; the gate costs no case; the
rule that derives a suite p95 is owed to AI Quality with Platform Engineering
at **M09 PR 1**, written before M09's fresh run and applied after it; no
manifest change. The fifth is the number, and PR 3 is now that and one
question: *is this number produced by the rule from the record and by nothing
else?* ADR-073 amendment 2 §5 pre-registers the three sentences ADR-014
amendment 2 must carry, so PR 3 fills in the number only.

### The residual, from an exclusion to a dated debt

The 422–537 tokens per call the census could not attribute were listed under
*What it does not build* with no owner and no date. They are a row now: owed
to **Platform Engineering with AI Quality**, dated **M09 PR 1**, paid by
per-call `inputTokens` in the answer file and one calibration call with tools
offered. The zero-call narrowing amendment 1 §3 described was run in PR 2's
diff — `milestones/M08/residual-differential.json`, pinned — and says the
residual did not grow with the added spec (409–538 at M02 with one tool,
422–537 at stage 2 with two; the spec cost 281 against an estimate of 282).
That rules out the scaling explanations and leaves a fixed provider-side cost
indistinguishable from fixed agent-sent content; the calibration call is what
separates them. The derivation is untouched — the band is a function of 6235
and 8181 — and ADR-014 amendment 2 carries the re-derivation trigger for the
day the residual is attributed to something the agent can stop sending.

### What this changes for PR 3 and after

- PR 3's amendment carries ADR-073 amendment 2 §5's wording and the number;
  the seats read it against that wording.
- PR 4's checkbox is reworded above; the flipped set is checked against the
  ten and the five by name, and every remaining `budget` failure is on a
  sample at four calls or more or on `tokens_out` at an unchanged tier.
- PR 5's journal carries the residual row, the `p95_ms` standing finding, and
  two step-6b triggers PR 2 recorded: the probes' re-opening condition and
  the store's retention.

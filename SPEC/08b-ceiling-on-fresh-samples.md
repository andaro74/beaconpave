# M08b — the ceiling, measured on samples it was not derived from

**Written before the branch is cut.** Owned by the PM seat. Branch
`m08b-fresh-run`, tag `m08b`. A row added in place between 08 and 09 on
ADR-054's precedent; nothing below it shifts (ADR-074 decision 1).

**Deliberately short**, in SPEC/08's shape. Every decision lives in ADR-074;
every "what broke" goes to the journal at close. This file states the
milestone and nothing else.

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
no case, tier, ceiling, prompt, tool spec, tool result field, topic, guardrail
or catalog moved before the run.**

The claim is per sample and the count cannot show it. M08's record has no
answered sample between 6792 and 8181, so every value in the band produced
the same join there; a fresh sample can land inside that gap on either side,
and that is what the claim risks. Falsifiers: any fresh answered sample at
three calls or fewer over 7700; any at four or more under it. A single
sample either way falsifies the claim. If it is falsified the milestone stops
at PR 3, records the sample, and closes red at PR 6: a re-derivation is a
census milestone with its own rule, and is not this one's.

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
  instead. The reading is Security's disposition at PR 3; any fix is its own
  ADR, not this milestone's.
- **The residual**, attributed by two exact numbers (ADR-074 decision 3 §4):
  the fresh run's round-1 `inputTokens` on `blackout-008` (**A**), and one
  calibration call on the same viewer turn with tools absent (**B**), against
  the census's estimates for the committed text (**E**) and the two specs
  (**S**). `D = B − E` is tokeniser density; `F = A − B − S` is provider
  framing; `A − E − S = D + F` by identity. The reading names whichever is
  70% or more of the residual, or both with their shares. ADR-014 amendment
  2's downward trigger arms only if the round-1 pin fails.
- **The suite `p95_ms`**, at the ceiling PR 2 derives by the rule in ADR-074
  decision 3 §5 from the mandated shape. OVER or within is recorded, not
  accommodated; the gate costs no case either way.
- **Two triggers** (ADR-074 decision 2): the browse gap **persists** if any of
  the seven cases carries a sample at four calls or more with a
  `catalog-search` call beyond its mandate; the `tokens_out` five **persist**
  if any of them fails `tokens_out` by majority at its unchanged tier. Read
  from the fresh trajectories and transcript; recorded, not diagnosed.

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| Per-call `inputTokens` in the answer file, so the join reads the run and not a census | `core/toolloop.py` records each round's usage beside the totals it already sums; `handler.py` returns it; `run_with_tools.py` writes it under `usage.calls`; `audit.schema.json` admits it | PR 2: the totals equal the sum of the per-call values by test; the round-1 pin (the first request is `system`, the viewer turn verbatim, and `toolConfig`, nothing else) by a source-reading test; M07's committed files, which carry no per-call usage, still score 12/25 with the join byte-identical to `rescore-join.json` |
| The call count in the budget verdict, so *"tokens_in=8181 over 7700"* says it was a four-call turn | `evals/deterministic.py` names `calls` when `usage.calls` is present and omits it when it is not | PR 2: a planted three-call and four-call usage each name their count; M07's files produce the same verdict strings they produce today |
| A latency ceiling derived before the run, from the shape and not from the run | ADR-014 amendment 3, in the wording ADR-074 decision 3 §5 pre-registers; `gates.budgets.p95_ms` in the manifest; the derivation test extended to `p95_ms` | PR 2: the test computes the mandated-shape p95 from the M07 files joined to the census's `mandated_calls`, the band, and the point by the pinned rule, and asserts the manifest carries that number; every constant planted is red |
| The run, on the real path | `run_with_tools.py` k=3 through the deployed gateway at the pre-flight SPEC/07 fixed; the refusals sidecar; `topic_baseline.py --all` | PR 3: committed under `milestones/M08b/` as `goldens-run-{1,2,3}.json`, their trajectories, `goldens-run-refusals.json`, `topic-baseline.json`, `goldens-score.txt`; the pre-flight header names the deployed function, both guardrail versions and bundle digests equal to the tree at PR 2's merge |
| The calibration call | One gateway turn on `blackout-008`'s viewer turn with `tools` absent, same `system`, committed as `milestones/M08b/calibration.json` with its audit record id | PR 3: `milestones/M08b/residual_attribution.py` reads A, B, E, S and prints D and F; `tests/test_m08b_residual.py` pins the record and refuses a planted A, B or E |
| The join | `milestones/M08b/fresh_join.py` over the three answer files' `usage.calls` and the three single-file transcripts; one row per sample | PR 3: `tests/test_m08b_fresh_join.py` pins the record byte for byte; a planted verdict, a planted call count and a foreign ceiling each move it or are refused |
| Nothing else moved | `git diff` of `services/highlights-agent/evals/`, `platform/gateway/policy/`, `data/catalog.json`, `platform/infra/lib/gateway-stack.ts` and every topic file between PR 1's merge and PR 3's branch point, empty; `probes_sha256`, `g4_cases_sha256`, the judge digests and `context_census.py --check` unchanged | PR 3, in the PR body |
| The entry | `run_evals --record --tag m08b --target highlights-agent` with `refused` per case, `samples_from` naming the three files, recorded with `HEAD` at PR 2's merge before the branch's first commit (M07's ordering) | PR 3: three keys; PR 6 closes with the row and `README_GOLDENS` gains `m08b` |

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
   none moves in this milestone but the suite `p95_ms` gate in PR 2 and the
   DMA rename in PR 5. `tokens_in` stays 7700, `tokens_out` and `max_ms` and
   every tier stay where ADR-014 put them.
2. **The only gateway change before the run is usage reporting.** Per-call
   usage is added beside the totals; the totals are computed as they are
   today and a test asserts they equal the sum. No verdict on any committed
   file moves; the M07 re-score at 7700 prints the join M08 pinned.
3. **The `p95_ms` rule is executed, not argued.** PR 1 writes it; PR 2's test
   computes the number from the committed inputs and pins the manifest to it;
   PR 3 compares the fresh run against it and moves nothing. The rule reads
   the mandated shape's p95 and ADR-014's two band constants, never a pooled
   p95 of any run.
4. **The DMA rename never precedes the run.** It lands in PR 5 or is re-dated
   to M09 PR 1 by the fallback in ADR-074 decision 4, and in neither case in
   the same PR as anything else.
5. **One run, k=3, committed as-run, majority against majority.** SPEC/07
   constraint 9's INFRA rule: a sample with an INFRA case is re-run whole,
   once, with the bad sample committed beside it as `*-infra.json` and passed
   to nothing; a second INFRA sample closes the milestone with what it has.
   No re-run selection, no case edit, no baseline reset.
6. **The pre-flight before the first call**, as SPEC/07's Definition of done
   fixed it: the deployed function, both guardrail versions read from its
   configuration, the bundle digests equal to the tree; a run whose records
   name any other version is not a reading.
7. **Seats on PR 2 only.** Attestations wherever `pave/twokey.py` demands
   them, on every PR.
8. **Model calls in PR 3 only**: 75 turns for the run, 1 for the calibration
   call, and headroom of one whole-sample re-run (75) for an INFRA sample —
   ceiling **151 turns**, all through the deployed gateway. PRs 1, 2, 4, 5
   and 6 are zero. `make check` stays hermetic. No probe run: no guardrail,
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

**PR 2 — the instrument before the run. Seats review this PR and no other.**
Per-call usage in the loop, the handler, the answer file and the audit schema
(constraint 2); `calls` in the budget verdict; the `p95_ms` rule executed in
`tests/test_budget_derivation.py` and the manifest gate moved to the number
it prints, with ADR-014 amendment 3 in the pre-registered wording; the direct
`BANDS` pin; the round-1 pin; `tests/test_g4_capture_boundary.py`'s `SKIP_DIRS`
matched against the tree-relative path, with an anti-vacuity guard that reads
the real tree; `residual_attribution.py` and `fresh_join.py` written and tested
on planted answer files before any real one exists. Hermetic; no deploy. One
question for the seats: *does the instrument record what the run does, and
move nothing about what the run is?*

**PR 3 — the run.** `make core`; the pre-flight; the calibration call; the
k=3 run; `topic_baseline.py --all`; the entry recorded on three keys with
`HEAD` at PR 2's merge; the join read against the claim; the count against
[7, 14]; refusals against 0–2; `recommend-003` read by the F/G rule with
`read_withheld.py --show` and the verification lines committed as
`withheld-read.txt`; the residual attributed; the fresh p95 read against PR
2's ceiling; both triggers read from the trajectories and the transcript.
ADR-074 amended with every number in the pre-registered words. PR 3 records
the numbers; it does not explain them. **If the claim's falsifier fires, the
milestone stops here and PR 6 closes red.**

**PR 4 — the hermetic debts.** Zero calls, no seat round, attestations only,
each on the rule its file already sits on: a `pave/twokey.py` rule over
`.gitattributes` with a test that the index carries no CRLF blob under
`text=auto eol=lf` and that every digesting reader normalises (a planted CRLF
copy of a committed evidence file hashes to the committed pin); the
templates' condition — a scaffolded service that offers a second tool cannot
keep the one-tool `tokens_in` silently, stated in the template and refused by
`pave verify` on a manifest that offers two tools with the template's number
verbatim; a check that every ADR under `docs/adr/` has an index row and that
an ADR carrying an `## Amendment` heading has a row that names it; the
cited-commit decision — `close-milestone` step 7 says the cited commits are
tagged before the merge, and `tests/test_cited_commits_resolve.py` counts a
citation reachable only from a remote-tracking branch as unreachable, so a
stale ref cannot make it green; the six *M08* code sites left as they are,
because they say M10 and mean M10.

**PR 5 — the DMA rename, after the run.** SPEC/06b A21, slid three times.
`data/catalog.json`, the `catalog-search` enum, the 25 `viewer.dma` values,
the judge re-frozen on two keys (AI Quality, Security) with no calibration
run, and every M08 record whose provenance digests the catalog re-produced by
its own reader with only its digest lines moving, shown key by key in the PR
body. Legal/S&P and Data Governance attest. Nothing under `milestones/M07/`
or `milestones/M08b/` changes. **Fallback, pre-registered (ADR-074 decision
4):** if the cap is reached before this PR, it is re-dated to M09 PR 1 by
name, because M09 re-freezes the judge for the `brand_tone` widening anyway
and the two re-freezes become one.

**PR 6 — close.** Journal; step 6b read from PR 3's `topic-baseline.json`
and refusal census; the progression row; `README_GOLDENS`; tag `m08b`.

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
| The rule that derives a suite `p95_ms`, written before the run and applied after | AI Quality + Platform Engineering | **PR 1** (the rule), **PR 2** (executed, the number), **PR 3** (applied) |
| `BANDS` in `tests/test_budget_derivation.py` on no direct pin | AI Quality + Platform Engineering | **PR 2** |
| `recommend-003`'s answer-channel refusal, read by the pre-registered rule | Security (with Legal/S&P if it reads as answer policy) | **PR 3** |
| `tests/test_g4_capture_boundary.py` vacuous under a `.claude/` checkout | Security + Platform Engineering | **PR 2** |
| `.gitattributes` on no `pave/twokey.py` rule; 191 CRLF files in the working tree against an LF index | Platform Engineering | **PR 4** |
| `templates/agent-tools/` carries 6000/6500, correct for one tool and wrong the moment a second is offered | ADR-047's four seats | **PR 4** |
| The ADR index enforced by nobody | PM | **PR 4** |
| A document citing its own branch commits is a citation with a fuse; `make check` green on stale remote-tracking refs (47 today by `git remote prune --dry-run origin`) | Platform Engineering + PM | **PR 4** |
| The DMA rename (SPEC/06b A21), slid from M07 to the SPEC/08 PR to M09 PR 1 | Legal/S&P + Data Governance | **PR 5**, after the run; fallback M09 PR 1 by name |
| The seven browse-gap cases | Tool Owner | **owned, unscheduled**; trigger *persists on this run*, read at PR 3 (ADR-074 decision 2) |
| The five `tokens_out` cases at unchanged tiers | AI Quality | **owned, unscheduled**; same trigger, read at PR 3 |
| GitHub's *automatically delete head branches* against `close-milestone` step 7 | the operator | **paid** before this milestone opened; `delete_branch_on_merge: false` verified 2026-09-07 (ADR-074) |
| The `brand_tone` widening | AI Quality | **M09**, unchanged (ADR-026 amendment 3) |
| ADR-053's *no orphan rules* (term undefined) and *no immortal rules* (`effective` optional) | Legal/S&P + Security | **M09**, re-dated by name from "M07" (ADR-074) |
| ADR-069 D5 cut 2, the paired diff's partition | the next two-arm run | unchanged; one arm runs here |
| `usage.tokens_in: 0` on refused answers | – | unchanged |
| Retention on the withheld store (ADR-071 amendment 1); the two `tool_request` probes' re-opening condition | Data Governance; Security | step-6b triggers, read at PR 6 |

## Bounded

- **Cap: six PRs.** Six planned, no spare. Reaching the cap closes the
  milestone, red if necessary; the DMA rename is the pre-registered item that
  gives way, by name, if the cap is reached before PR 5.
- **Seats on PR 2 only.**
- **Model calls in PR 3 only, ceiling 151 turns.**
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
suite latency  <OVER|within> p95=Pms <over|within> Cms
channels: tool_request 0 · answer R' · question 0 · tool_output 0
```

with **N = 12** predicted and 7 ≤ N ≤ 14 the bound, R ≤ 2, no `TOPIC:*` on
`tool_request` or `tool_output`, every `budget` failure naming its `calls`,
and C the number PR 2's test prints. Today the same command prints nothing:
no file under `milestones/M08b/` exists.

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: every fresh ≤3-call answered sample passes `tokens_in` at 7700, every ≥4-call sample fails it, per sample | `fresh_join.py` over the answer files' `usage.calls` and the three single-file transcripts; `fresh-join.json` pinned; the two falsifiers read empty | PR 3 |
| 2 | The count: 7 ≤ N ≤ 14, predicted 12; no 3-of-3 pass regressed, no 0-of-3 fail flipped | `goldens-score.txt`; the join's per-case table against `rescore-join.json` | PR 3 |
| 3 | Refused by majority 0–2 | `evals.refusals --sidecar` | PR 3 |
| 4 | `recommend-003`: F and G read by the rule; the reading named | the sidecar, the answer files, `read_withheld.py --show`, `withheld-read.txt` | PR 3 |
| 5 | The residual: D and F from A, B, E, S; the trigger's state | `calibration.json`, round-1 usage, `residual_attribution.py`, its pin | PR 3 (reader tested on a synthetic pair in PR 2) |
| 6 | The round-1 request is `system`, the viewer turn verbatim and `toolConfig`, nothing else | a source-reading test over `handler.py` and `core/toolloop.py` | PR 2 |
| 7 | Per-call usage sums to the totals; no committed verdict moves | a test; the M07 re-score's join byte-identical to `rescore-join.json` | PR 2 |
| 8 | `calls` in the verdict when per-call usage exists, absent when it does not | a test with a planted usage each way; M07's verdict strings unchanged | PR 2 |
| 9 | The `p95_ms` rule yields one number from the mandated shape and ADR-014's constants | the derivation test: mandated-shape p95, band, point; every constant planted red | PR 2 |
| 10 | The fresh p95 against it | `goldens-score.txt`'s latency line | PR 3 |
| 11 | Browse gap persists or not | the fresh trajectories joined to `calls` per sample; the count of ≥4-call samples on the seven cases | PR 3 |
| 12 | `tokens_out` five persist or not | the transcript's `tokens_out` verdicts by majority on the five | PR 3 |
| 13 | Nothing else moved before the run | `git diff` between PR 1's merge and PR 3's branch point over the named paths; the digest families; `context_census.py --check` | PR 3 |
| 14 | The deployed bundle equals the tree | the pre-flight header in the sidecar | PR 3 |
| 15 | `BANDS` directly pinned | a test that plants each constant | PR 2 |
| 16 | The G4 boundary test scans the tree under a `.claude/` checkout | the anti-vacuity guard reads a real file count | PR 2 |
| 17 | `.gitattributes` on a rule; no CRLF blob in the index; digesting readers normalise | the twokey rule's plant; the eol test; the planted-CRLF digest test | PR 4 |
| 18 | A two-tool scaffold cannot keep the one-tool ceiling silently | `pave verify` refuses the planted manifest | PR 4 |
| 19 | Every ADR indexed; every amended ADR's row names its amendment | the index test, red on a planted ADR and a planted amendment | PR 4 |
| 20 | A cited commit reachable only from a remote-tracking branch is unreachable | the citation test, red on a planted ref | PR 4 |
| 21 | The DMA rename moves every digest it must and nothing else | each reader re-produces its record; the judge re-frozen; the PR body's key-by-key diff | PR 5 |
| 22 | Zero model calls in PRs 1, 2, 4, 5, 6; PR 3 within 151 turns | the PR bodies; no new file under `milestones/M08b/` carrying `usage` outside PR 3 | every PR |
| 23 | The entry on three keys with `refused` per case; the row | `pave gate history`; `README_GOLDENS` | PR 3, PR 6 |
| 24 | `delete_branch_on_merge` is off | asserted from the API on 2026-09-07 and recorded; no hermetic test can read a GitHub setting, and the close-milestone step stays the rule | PR 1, recorded |

Every row has a PR. Row 24 is asserted rather than measured, and says so.

## Definition of done

- [ ] ADR-074 merged with the `08b` row in `README.md`, `BUILD.md` and
      `SPEC/README.md` and the index row, in one diff; `make check` green with
      the new row; nothing below row 08b renumbered.
- [ ] PR 2: per-call usage recorded and summed, the round-1 pin, `calls` in
      the verdict, the `p95_ms` rule executed and the manifest pinned to its
      number, ADR-014 amendment 3 in the pre-registered wording, the `BANDS`
      pin, the G4 boundary test's guard, both readers tested on planted files;
      every seat's findings in the PR; attestations per `pave/twokey.py`;
      the M07 re-score's join byte-identical; **the deletability audit in the
      PR body, every new check named with its result.**
- [ ] PR 3: pre-flight printed before the first call; the run committed
      as-run; the calibration call committed with its record id; the entry on
      three keys; the join read against the claim (**the claim**); N against
      [7, 14], refusals against 0–2, F and G by the rule, D and F by the rule,
      the fresh p95 against PR 2's ceiling, both triggers (**the
      side-predictions** — a miss is a finding about the side-prediction and
      does not fail this box's first item); `withheld-read.txt` committed;
      ADR-074 amended; **the deletability audit on the two pin tests.**
- [ ] PR 4: each hermetic debt paid on its own rule with its plant named;
      **the deletability audit on every check added.**
- [ ] PR 5: the DMA rename after the run, every record re-produced with only
      its digest lines moving, the judge re-frozen on two keys, Legal/S&P and
      Data Governance attested — or the fallback taken by name.
- [ ] Nothing under `milestones/M07/` or `milestones/M08/` changed but the
      records PR 5 re-produces, and those only in their digest lines.
- [ ] `close-milestone` in order; journal; progression row; `README_GOLDENS`
      gains `m08b`; tag `m08b`. Six PRs or fewer.

## What must not happen

No case, tier, ceiling, prompt, tool spec, tool result field, topic,
guardrail, catalog or policy change before the run. No `p95_ms` number chosen
from any pooled p95. No sample selected, re-run until it fits, or read at any
ceiling but 7700. No DMA rename before the run, and never in the same PR as
anything else. No diagnosis of the browse gap, no fix for `recommend-003`, no
tier move on a `tokens_out` reading. No history entry edited; no baseline
reset. No registry work. No claim rewritten to match the outcome: if a fresh
sample lands on the wrong side of 7700, the claim failed, the sample is
named, and the milestone closes red.

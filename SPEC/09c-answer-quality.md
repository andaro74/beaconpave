# 09c — the browse gap closes, and the count is the headline

**Status: CLOSED RED at 09c PR 2, 2026-09-12, the claim NOT MEASURED (`milestones/M09c/README.md`; ADR-078 amendment 1).
Written at 09c PR 1, 2026-09-12, before any diagnosis, code, deploy or model call.** Owned by the PM seat. Tag `m09c`; one branch per PR, none named `m09c`.
Row `09c` was added in place by ADR-075 decision 2 (:105-112), which left *"what claim,
if any, 09c should carry"* to this file. Nothing below row 09c shifts, and **no closed
milestone's record moves**: SPEC/09, SPEC/09b and their README rows are not edited.

**Deliberately short**, in SPEC/09's shape. The derivation of every rule below is
**ADR-078**, written beside this file. The DMA rename's removal from this milestone is
**ADR-075 amendment 8**. Every "what broke" goes to the journal at close. This file states
the milestone and nothing else.

## Why

**The goldens count is 10/25, and it has been 10/25 for two runs.** M08b published it
(`evals/history/m08b-tools-goldens.json`), and M09's control run landed on it again. On
that second run one case moved each way underneath the number (ADR-075:2227-2237).

Two answer-quality debts were owned and unscheduled, each with a trigger, and both fired
on M08b's fresh run (ADR-074:103-110; ADR-075:97-103):

- **The browse gap.** Seven named cases (ADR-074:87-89) take a `catalog-search` call beyond
  their mandate before `entitlement-check` or the answer. M08b: nine samples at four calls
  or more, across five of the seven. The extra call and the wrong citation arrive
  together on the same sample (`milestones/M08/README.md:171-177`).
- **The `tokens_out` tiers.** Five failing cases became twelve. Two of them failed on a
  single sample, at **307 and 308 against 300** (`milestones/M08b/README.md:169`, :361).

A third inheritance is a number, not a case. **The `p95_ms` re-derivation** was dated here
when ADR-014's stability sentence was withdrawn (ADR-014:711-716). The mandated shape's
tail now reads **3769 → 5241 → 4900** across three runs (ADR-075:2319-2327).

ADR-074 decision 2 named the disposition a fired trigger earns: *"a row of its own after
M09 with a before-and-after run"* (:112-114). This is that row.

## The one claim, and it is none of the twelve

**The browse gap closes at the site a zero-call diagnosis names. The goldens count then
rises above a control run taken on the same deployment immediately before the change, and
the rise is on the seven browse-gap cases. Nothing else moves.** Both runs go through the
deployed gateway at k=3 and are read by the same committed reader, never on a stand-in and
never on a hand-built fixture.

Three terms: **the gap closes** (F1), **the count rises on the seven** (F2, F3), **nothing
else moves** (F4, F5). It advances **none of the twelve** and serves **claim 2**
defensively (ADR-075:107-110), on the shape of M07 and M09b: a pre-registered claim with
falsifiers that advances no numbered claim (ADR-075:2475-2476). **The `tokens_out` tiers
and the `p95_ms` re-derivation are deliverables, not terms.** ADR-078 decision 1 gives the
reason: a tier move changes the count by re-scoring, so a claim whose headline is the count
cannot share a reading with one.

### The five falsifiers, pre-registered

Any one fails the claim and closes the milestone red, with the case named. **Every reader
named here exists on `main` today and was run over M09's committed record at this PR's
branch point.** ADR-078 decision 2 carries the output. *Control* is
`milestones/M09c/control/`; *post* is `milestones/M09c/`. *The seven* are ADR-074:87-89's
seven, by name.

| | falsifier | field, in the record the reader writes | reader |
|---|---|---|---|
| **F1** | **the gap persists.** On post, one answered sample of the seven carries an executed `catalog-search` beyond its mandate before `entitlement-check` or the answer, **at any call count**; or one sample outside the seven carries it at four calls or more | `fresh-join.json` → `triggers.browse_gap.samples`, plus the seven's entries in `…beyond_mandate_under_the_threshold.samples`, plus `…four_call_samples_outside_the_seven` | `python milestones/M08b/fresh_join.py --dir milestones/M09c` |
| **F2** | **the seven do not rise.** The number of the seven passing by majority on post is not greater than on control | `count.per_case[<id>].result`, both records | the same reader, `--dir` each run |
| **F3** | **the count does not rise.** `N` on post is not greater than `N` on control | `count.N`, reconciled by the reader against its own rows (`fresh_join.py:548-557`) | the same reader |
| **F4** | **something else moved.** A case that passed **3 of 3** on control fails by majority on post; or a case **outside the seven** that failed **0 of 3** on control passes by majority on post (SPEC/09:57's clauses 2 and 3, against this milestone's control) | `count.per_case[<id>].samples` on control, `.result` on post | the same reader |
| **F5** | **the fix is refused.** A case not refused by majority on control is refused by majority on post | `goldens-run-refusals.json` → `census.cases_by_majority`, both runs | written by `run_with_tools.py`; printed by `python -m evals.refusals --sidecar` |

**Thresholds and denominators, defined here and nowhere later.** 25 cases, held by
`tests/test_m09_goldens_denominator.py::test_the_golden_file_holds_exactly_twenty_five_cases`.
k = 3 on each run. *Majority* means more than half of three samples. *3 of 3* and *0 of
3* mean unanimity. Every threshold is one sample or one case. **A case left INFRA on either
run after the one permitted re-run fires every falsifier that reads it** (fail-closed, on
ADR-077:500-501's *"an unreadable row fails"*).

**F1 reads every call count, not decision 2's four.** ADR-074's threshold was a trigger for
*persists*, and this claim says *closes*. The committed reader's own note refuses the
narrower reading: a `persists: false` is *"read beside this column, never as not reproduced
on its own"* (`fresh_join.py:695-698`). A fix that removes the fourth call and keeps the
extra search would pass a four-call reading while the property stays broken. The reference
counts below come from the two committed runs, read from their `fresh-join.json`:

| | on the seven, ≥4 calls | on the seven, <4 calls | outside the seven, ≥4 calls | the seven passing by majority | `N` |
|---|---|---|---|---|---|
| M08b | 9 samples, 5 cases | 5 samples | none | 1 (`grounded-019`) | 10 |
| M09 control | 5 samples, 4 cases | 12 samples | none | 1 (`grounded-019`) | 10 |

**F4 is reachable by drift alone, and it is pre-registered anyway.** On M08b → M09, a pair
that differed by one prompt sentence, its first clause fired once, on `grounded-017`
(ADR-075:2218). Netting F4 against a drift reading would choose its threshold after the
run. The control run's drift is published beside the claim and subtracts from nothing.

## Beside the claim, and not it

Read and published, never falsifying:

- **The paired diff, control → post, by majority**: `python -m evals.run_evals --answers …
  --against …` writes `lost`, `gained` and `net`. Measured today over M08b → M09, it prints
  `lost 1: grounded-017`, `gained 1: entitlement-011`, `net +0`.
- **Drift, M09 control → 09c control**, on the same reader and the same two unanimity
  clauses as F4. This is one draw of generation drift at k=3 on an unchanged system. It is
  never subtracted from anything.
- **Refusals at least once**, `census.cases_at_least_once`, beside F5's majority, on both
  runs. ADR-076 decision 6: a majority reading ships with its at-least-once companion.
- **The 7700 per-sample claim** on post, `claim.3_call_or_fewer_samples_over`.
- **`grounded-017`**, read on both runs and at the re-derived tiers. It is not diagnosed.
- **No count band is predicted.** The diagnosis does not exist yet, and a band written
  before it is a number chosen blind. M08's journal gives the known risk: six of the seven
  also fail a citation assert on the same sample (`milestones/M08/README.md:175-177`), so
  the gap can close while the count does not rise. F2 and F3 would then fire, and the
  milestone publishes that.

## The two deliverables, and their rules

Pre-registered in full in ADR-078 decisions 3 and 4. Summarised here; where the two
differ, the ADR is the rule.

**The `tokens_out` tiers.** The population is the M09 control run's answered samples at
their mandate (`at_mandate`, `tokens_out` in `milestones/M09/fresh-join.json`'s
`per_sample`), grouped by the tier each case already carries. The statistic is each
group's maximum. The point is the midpoint of `[1.15, 1.60] ×` that maximum, rounded to
the nearest hundred, which is the rule `tests/test_budget_derivation.py` executes for
`tokens_in`. **Not computed at pre-registration.** It is applied to `cases.yaml` only after
the claim is read, and never to the run it was drawn from. **Executed by**
`tests/test_budget_derivation.py::test_each_output_tier_is_the_number_the_point_rule_produces`,
written in PR 2.

**The `p95_ms` gate.** **Condition:** the stability premise is re-established iff the 09c
control run's mandated-shape p95 is at or below the point ADR-014's rule derives from M09's
mandated-shape p95. That is ADR-014 amendment 3's own failure sentence (ADR-014:664-666)
with its numbers advanced one run. **If the condition holds**, `gates.budgets.p95_ms`
becomes that point. From M09's published 4900 (n = 36) it is **6700**: floor 5635, roof
7840, midpoint 6737.5. **If it fails**, the gate stays 5200, recorded. The move comes after
both runs, so no 09c run is read against it (ADR-014:711-716). **Executed by**
`tests/test_m09c_p95_rederivation.py`, written in PR 2.

**6700 is a loosening of 1500 ms, and it is written here so nobody discovers it at PR 4.**
At 6700, M09's pooled 5630 reads *within*, so the gate stops reporting the browse gap's
share (ADR-014 amendment 3, *what a suite p95 can and cannot discriminate*). ADR-078
decision 4 says why the rule is taken anyway and what the cold review must weigh.

## Reading rules, binding on every number this milestone publishes

1. **A committed run is read at its own era.** A tier or a `p95_ms` move does not re-score
   M08b, M09 or either 09c run. Measured today: either move makes `fresh_join.py` **refuse**
   both committed runs (ADR-078 decision 5). So the era pin lands in PR 2, and no committed
   record is re-produced to get past it.
2. **Nothing judged is drawn from what judges it.** Both deliverable populations are M09's
   control run. The fix site is drawn from M08b's and M09's trajectories. Neither 09c run
   feeds any derivation, and no derivation is applied to M09.
3. **An executor executes its clause at the clause's width.** Each derivation test and each
   falsifier reading is planted at the clause's own scope, not at a narrower token.
   `candidates.json:31` passed a candidate its rule refused (ADR-077 amendment 2).

## The plan, walked to the claim

1. **PR 2**, seated, zero model calls. The diagnosis names one fix site from committed
   trajectories. The executors, the era pin and the rule gaps land.
2. **PR 2b**, the named spare: a cold review of PR 2's executors against ADR-078's clauses,
   before any call.
3. **PR 3**, the runs: the control run; the fix at the named site; at most one deploy, only
   if that site is in the deployed bundle; the post-change run; F1–F5 read; the entry.
4. **PR 4**, after the claim is read: both deliverables applied by their tests; Security's
   `enforcement-probing` re-disposition on the control run's census.
5. **PR 5**, the close.

## Pre-registered, in ADR-078 and ADR-075 amendment 8

The claim, its three terms and five falsifiers, each falsifier's field and reader
(ADR-078 D2). The tier rule (D3). The `p95_ms` condition and point (D4). The order, the
era pin, and why these moves differ from the rename (D5). The cap and the spare (D6). The
DMA rename cut, re-dated, and SPEC/09:661 superseded by quotation (ADR-075 amendment 8).

## Implementation constraints, binding

1. **Nothing the model sees moves between PR 1's merge and the control run.** Measured at
   this branch point: `git log 369c8ba..HEAD` over `gateway_client.py`,
   `answer.schema.json`, `cases.yaml`, `data/catalog.json`, `tools/`,
   `platform/gateway/`, the policy directory, `gateway-stack.ts` and the manifest is
   **empty**. M09's control run is therefore the current system.
2. **Between the control run and the post-change run, the whole tree moves only at the
   named site and under `milestones/M09c/`.** The evidence is an allowlist. `git diff
   --name-only` between the two runs' commits, with those paths removed, is empty. It is
   committed as `milestones/M09c/nothing-else-moved.txt`. A denylist of model-facing paths
   is narrower than the property and would pass itself.
3. **The fix site is named and committed in PR 2, before the control run exists.** If the
   diagnosis names no single site, PR 3 is not taken and the claim closes RED unmeasured. If
   it finds the gap depends on the DMA rename, PR 2 stops and reports.
4. **A deploy, if taken, moves no guardrail.** The post-change pre-flight shows main pair
   `abayh4ye7f8o` **v4** and tool-output pair `ggla7vqlfu7d` **v1**
   (ADR-075:2193-2196), with the bundle digest moving and nothing else. Otherwise PR 3
   stops. M09b's debts 1–5 block a topic-wording deploy (`milestones/M09b/README.md:418-429`),
   and this is not one.
5. **If the site is a prompt constant**, `tests/test_m09_prompt_delta.py` prices it against
   the 7700 headroom before PR 3 spends a call.
6. **Tiers and `p95_ms` move only in PR 4, after F1–F5 are read and committed.**
7. **Records land where the gate can see them.** `milestones/M09c/**/fresh-join.json`,
   `tools/catalog-search/search.py` and `server.py` match **no** two-key rule. That was
   measured by matching those paths against `pave.twokey.RULES`. PR 2 closes each one that
   09c will write or edit, before the diff that creates it.
8. **Every new check is audited for deletability through `pave check`**, not `pytest`
   alone. That pays M09b's debt at `milestones/M09b/README.md:403` at the audit where its
   trigger fires.
9. **Citations resolve from `main` or a tag**, held by `tests/test_cited_commits_resolve.py`.

## What it builds

A diagnosis of the browse gap from committed trajectories, naming one site. The fix at
that site. Two k=3 goldens runs and their readings. The tier executor and the `p95_ms`
executor. An era pin on `milestones/M08b/fresh_join.py`. Two-key rules for 09c's records
and for the fix site. The tier and gate moves those executors produce. The goldens entry
and the row's cell.

## What it does not build

**The DMA rename** (ADR-075 amendment 8) · a re-derivation of `tokens_in` · a tier or gate
move before F1–F5 are read · a tier applied to M08b's or M09's run · a guardrail, topic,
policy or corpus change · a probe run · a judge run, a re-freeze or `brand_tone`'s widening
(**M10**, ADR-026 amendment 5) · `grounded-017`'s diagnosis · anything of M09b's gate
executor, F4 input record, F5 denominator, decoded-or-raw definition or gate 6/7 routing ·
**a case edited, a threshold moved or a baseline reset to make any run pass.**

## Obligations inherited, each with an owner and a trigger

| source | debt | owner | here |
|---|---|---|---|
| ADR-074:87-89; `milestones/M09b/README.md:394` | the seven browse-gap cases | Tool Owner | **the claim** |
| `milestones/M08b/README.md:361`; M09b :394 | the `tokens_out` cases, five widened to twelve | AI Quality | **deliverable, PR 4** |
| ADR-014:711-716 | the `p95_ms` re-derivation, a third population | AI Quality + Platform Engineering | **deliverable, PR 4** |
| `milestones/M09b/README.md:360` | **debt 10:** Security's re-disposition of `enforcement-probing`'s two trigger halves (ADR-035:1457-1462) | Security | **Its trigger fires at PR 3's control-run census; scheduled PR 4.** Read on the **control** run's census, the system the topic was disposed on, with post's census beside it and not substituted. The seat disposes. A reviewer agent's draft is advisory (G6). **Not resolved in this PR** |
| M09b :391; SPEC/09b:517 | `grounded-017`'s margin, a live regression on `main` | AI Quality | **a read**, both runs and both tiers; not diagnosed |
| M09b :393; SPEC/09:530 | the DMA rename | Legal/S&P + Data Governance | **cut; owned, unscheduled, no earlier than M11's close** (ADR-075 amendment 8) |
| M09b :390; SPEC/09b:516 | F4 cannot separate a change from generation drift | AI Quality | **addressed by design, not closed:** one control run is one draw of drift |
| M09b :403 | the deletability audit runs `pytest` while the gate runs `pave check` | Platform Engineering | **fires at PR 2's audit**, constraint 8 |
| M09b :351-355, debts 1–5 | the ADR-077 gate executor and its four companions | as listed there | **not inherited**; they block a topic-wording deploy, and 09c takes none |
| M09b :397 | retention on the withheld store (ADR-071 amendment 1) | Data Governance | **read at PR 5.** 09c makes model calls, so the store can gain a turn |
| M09b :386 | no ADR and no spec is on any two-key rule | owned, unscheduled | unchanged. `gate two-key --changed` over this PR returns *not required* |
| every other row of `milestones/M09b/README.md:341-412` | | as listed there | unchanged, unscheduled here |

## Bounded

**Six PRs, including document-only ones. Five are planned, and one is a named spare.**
PR 1, PR 2, **PR 2b (the spare)**, PR 3, PR 4, PR 5. A correction to merged work is a PR
and counts. Reaching six closes the milestone, red if necessary. No slide is
pre-authorised, and any slide is a finding.

- **Two runs**: one control, one post-change, both in PR 3. The model-call ceiling is
  **175 turns**: 2 × 75, plus one whole-sample re-run of 25 for an INFRA sample.
- **At most one deploy**, in PR 3, between the runs, only under constraint 4.
- **One seat round, on PR 2, in two rounds.** Zero judge runs, zero re-freezes.

**The spare is for one thing: a cold review, by a reader who wrote neither ADR-078's rules
nor PR 2's executors, before PR 3 spends a call.** It answers three questions:

- Does each executor execute its clause at the clause's width?
- Does each falsifier's reader read a field that exists, run over M09's record?
- Is anything judged drawn from what judges it, including whether the 6700 loosening
  should be taken?

Its output is committed as **ADR-078 amendment 1**. If it is not taken, the slot is not
spent on anything else.

## Demo artifact

```text
python milestones/M08b/fresh_join.py --dir milestones/M09c/control --check
python milestones/M08b/fresh_join.py --dir milestones/M09c --check
python -m evals.run_evals \
    --answers milestones/M09c/goldens-run-1.json --answers milestones/M09c/goldens-run-2.json \
    --answers milestones/M09c/goldens-run-3.json \
    --against milestones/M09c/control/goldens-run-1.json --against milestones/M09c/control/goldens-run-2.json \
    --against milestones/M09c/control/goldens-run-3.json \
    --arm m09c-post --against-arm m09c-control
python -m evals.refusals --sidecar milestones/M09c/control/goldens-run-refusals.json \
    --sidecar milestones/M09c/goldens-run-refusals.json
```

The block ships as `text`. Every file it reads is one PR 3 produces, and
`tests/test_documented_commands.py` runs `bash` blocks against `main` (ADR-075:2544-2556).
**Predicted shape, with the numbers left as letters:** both checks `OK`; `N/25` on post
against `C/25` on control; `lost` and `gained` named; refusals by majority and at least
once on both runs.

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **F1**, the gap closes | `triggers.browse_gap` in post's `fresh-join.json`, every call count | PR 3 |
| 2 | **F2, F3**, the count rises on the seven | `count.per_case` and `count.N`, control against post | PR 3 |
| 3 | **F4, F5**, nothing else moves | the two unanimity clauses; `census.cases_by_majority` both runs | PR 3 |
| 4 | the fix is at the named site and nowhere else | `nothing-else-moved.txt`, the allowlist diff | PR 3 |
| 5 | the deploy, if any, moved no guardrail | the pre-flight header against ADR-075:2193-2196 | PR 3 |
| 6 | the fix site was named before the control run | `milestones/M09c/diagnosis.md` merged in PR 2 | PR 2 |
| 7 | every reader reads a field that exists | each reader run over M09's record, output committed | PR 2, PR 2b |
| 8 | the tier rule executes at its clause's width | the test, each constant planted red, and a plant that re-scores its own population refused | PR 2 (executor), PR 4 (move) |
| 9 | the `p95_ms` condition executes as written | the test, both branches planted | PR 2 (executor), PR 4 (outcome) |
| 10 | committed runs are read at their era after a move | `fresh_join.py --check` exit 0 over M08b, M09 and both 09c dirs on a planted tier and gate move; an unrecorded era refused by name | PR 2 |
| 11 | the goldens entry, `README_GOLDENS` and the bold `N/25` in one PR | `pave gate history` | PR 3 |
| 12 | debt 10 disposed by the seat on the control run's census | the disposition as ADR-035 amendment 10 | PR 4 |
| 13 | the cap holds | this section against the PR list at the close | PR 5 |
| 14 | the deletability audit | each new check deleted and run through `pave check` | PR 2, PR 4 |

## Definition of done

- [ ] **PR 1:** this file; ADR-078; ADR-075 amendment 8, with SPEC/09:661 superseded by
      quotation and SPEC/09 unedited; README's `09c` row and footnote; `BUILD.md`,
      `SPEC/README.md` and the ADR index; `make check` green, with the count run on the head
      before the body commit and cited by SHA. No code, no runs, no corpus edits.
- [ ] **PR 2:** `milestones/M09c/diagnosis.md` naming one site; both executors; the era pin;
      the two-key rules; each falsifier's reader run over M09's record; the seat round; the
      audit.
- [ ] **PR 2b** (the spare): the cold review committed as ADR-078 amendment 1.
- [ ] **PR 3:** control run, fix, post-change run, F1–F5, the paired diff, the drift
      reading, the entry, the row's goldens cell.
- [ ] **PR 4:** tiers and `p95_ms` at what their tests produce, an ADR-014 amendment for
      each that moves; post re-scored at the derived tiers and labelled; debt 10 disposed.
- [ ] **PR 5:** journal; step 6b; the row's ✅; tag `m09c`.

## What must not happen

- A falsifier, threshold, denominator or reader re-scoped after a run it reads.
- A tier or gate moved before F1–F5 are committed, or applied to the run it was drawn from.
- A committed record re-produced to get past the era pin.
- A fix site chosen after the control run, or a fix outside the named site.
- The count published without F2, F4 and F5 beside it.
- A majority reading published without its at-least-once companion.
- The DMA rename, in any PR of this milestone.

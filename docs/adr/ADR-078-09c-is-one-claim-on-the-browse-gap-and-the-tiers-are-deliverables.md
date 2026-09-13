# ADR-078: 09c is one claim on the browse gap, the tiers and the gate are deliverables, and the cap counts every PR

**Status: PROPOSED at 09c PR 1, 2026-09-12; ACCEPTED when that PR merges, which is the
operator's disposition.** Written before any diagnosis, code, deploy or model call. The
scope is the operator's: three workstreams, one claim, the DMA rename cut, and the cap.
That scope is recorded here, not argued. Everything else is derived from an owning
document at line, and a clause that could not be grounded that way is not here.

**Seats:** Tool Owner (the browse gap, the fix site) · AI Quality (the tiers, the gate's
rule, the falsifiers) · Platform Engineering (the era pin, the executors, the rule gaps) ·
Security (debt 10; the deploy's guardrail check) · PM (the spec).

**Zero model calls to write.** Four readings were taken on committed files at
`b276c7e`, the branch point: three readers run over M09's record, and two planted moves
in a scratch copy of the tree. Each is quoted as-run in decisions 2 and 5.

---

## Decision 1 — one claim, on the browse gap; the tiers and the gate are deliverables

ADR-075 decision 2 scheduled answer quality and left the claim open: *"What claim, if any,
09c should carry is left to 09c's own spec"* (ADR-075:110-112). The operator's scope fixes
three workstreams and one claim. **Which workstream carries the claim is decided by
attribution:**

- **A tier move changes the count by re-scoring the same answers.** The `tokens_out` tiers
  live in `services/highlights-agent/evals/golden/cases.yaml` as budget asserts. Moving one
  flips a verdict without the system producing a different token. A claim whose headline
  is the count cannot share a reading with a tier move, because the count could not then
  say which one moved it.
- **The gate costs no case.** `milestones/M09/fresh-join.json`'s `p95` block carries
  `"costs_a_case": false`, and `suite latency` is a suite-level line (ADR-016). A p95
  re-derivation cannot move `N` in either direction.
- **The browse gap changes what the system does.** It is the only one of the three with a
  before and an after, which is the disposition ADR-074:112-114 named: *"a row of its own
  after M09 with a before-and-after run"*.

So the claim is the browse gap, with the count as its headline. The other two are
deliverables with rules, not terms. It advances **none of the twelve** and serves claim 2
defensively (ADR-075:107-110). ADR-075 amendment 7 §1 (:2475-2476) gives the shape: a
pre-registered claim and falsifier set, advancing no numbered claim.

## Decision 2 — the claim, its five falsifiers, and the reader each one names

**The claim**, as `SPEC/09c-answer-quality.md` states it: the browse gap closes at the
site a zero-call diagnosis names, and the goldens count rises above a control run taken on
the same deployment immediately before the change, on the seven browse-gap cases, with
nothing else moving. **Three terms, five falsifiers.** The spec's table is the rule.
This decision records why each falsifier is shaped as it is.

**The rule this decision executes: a falsifier is admitted only if the record field it
reads exists today and the reader that writes it runs.** M09b's F4 read an
`inputs_sha256` that no file carried (`milestones/M09b/README.md:90-94`), and the spec
could not be read after the run. So each reader was run at the branch point over M09's
control run, which has the file layout 09c's two runs will have. The output follows,
unedited.

```
$ python milestones/M08b/fresh_join.py --dir milestones/M09 --check
OK: milestones\M09\fresh-join.json is what the committed inputs produce
exit 0

$ python -m evals.run_evals --answers milestones/M09/goldens-run-{1,2,3}.json \
    --refusals milestones/M09/goldens-run-refusals.json \
    --against milestones/M08b/goldens-run-{1,2,3}.json --arm m09-control --against-arm m08b \
    --diff-out <scratchpad>
10/25 passed (15 failed, 0 infra)
paired per-case diff: m08b -> m09-control
  lost   1: grounded-017
  gained 1: entitlement-011
  net    +0
exit 0            (git status afterwards: clean)

$ python -m evals.refusals --sidecar milestones/M09/goldens-run-refusals.json
  refused by majority: 1/25   at least once: 4/25   unanimously: 1/25   (k=3, as written by the run)
exit 0
```

The fields the falsifiers read, confirmed present in that record: `per_sample[]` carries
`answered`, `at_mandate`, `calls`, `mandated_calls`, `refused`, `search`, `tokens_out`
and `latency_ms`. `count.per_case[<id>]` carries `result` and `samples`. `triggers.browse_gap`
carries `samples`, `four_call_samples_outside_the_seven` and
`beyond_mandate_under_the_threshold.samples`. The sidecar's `census` carries
`cases_by_majority` and `cases_at_least_once`. **The paired diff reproduces ADR-075
amendment 6's F4 movement exactly**, so the reader measures what the journal says it
measured.

**`count.per_case[].m08_result` and `.m08_samples` are not read.** They compare against
M08's re-reading, a module constant (`fresh_join.py:65`), which is the baseline ADR-075
amendment 6 §8(a) found would have reported F4 clean. Every 09c falsifier compares the two
09c records to each other.

**F1 reads every call count.** ADR-074:105-108's threshold, *four calls or more*, was
written to decide whether the gap *persists*. The claim says it *closes*. The committed
reader's own note says the threshold column is read *"beside this column, never as not
reproduced on its own"* (`fresh_join.py:695-698`). On M09's control run the seven carry
**5** samples at four calls or more and **12** below four. A fix that removes the fourth
call and keeps the extra search would pass a four-call F1 and fail the property.

**F2 and F3 are separate on purpose.** F3 is the headline, `N`. F2 puts the rise on the
seven. A rise in `N` made of cases outside the seven would clear F3 and say nothing about
the gap. On both committed runs, one of the seven passes by majority (`grounded-019`).

**F4 is SPEC/09:57's clauses 2 and 3, against this milestone's control.** Unanimity, not
majority. It is known to be reachable by drift at k=3: on M08b → M09 its first clause fired
once (ADR-075:2218). It is not netted against the control run's drift reading, because
netting chooses the threshold after the run. The third clause is scoped to cases outside
the seven, because a seven-case moving 0 of 3 → majority is the claim working.

**F5 exists because the fix changes the retrieval every committed number was measured
against** (ADR-074:123-125). More answered content is more content assessed on the answer
channel. Majority is the falsifier. `cases_at_least_once` is published beside it, because
a majority reading ships with its at-least-once companion (ADR-076 decision 6).

**Fail-closed.** A case still INFRA after the one permitted re-run fires every falsifier
that reads it. ADR-077:500-501's *"an unreadable row fails"* is the precedent.

## Decision 3 — the `tokens_out` tiers: the rule, written before any number

**Why the tiers are re-derivable at all, at line.** They were derived at M00b from a
**one-call** shape: *"300 / 400 / 500 / 600, roughly twice the measured worst case in each
band"* (ADR-014:82-86). They were left alone at M02 because *"no measured sample exceeded
the output ceiling its case already carried"*
(`tests/test_budget_derivation.py:302-309`; ADR-014:174-178). Two facts have changed:

- **`usage.tokens_out` is summed over every model round**
  (`platform/gateway/core/toolloop.py:303-304`).
- **The mandated shape is now two or three calls, *"never one"***
  (`milestones/M08/context_census.py:220-226`).

At M08b, twelve cases fail by majority on the tier (`milestones/M08b/README.md:361`).
**The evidence the tiers were kept on no longer holds**, which is the test's own condition
for revisiting them.

**The hazard, named.** A tier raised until the twelve pass is a threshold moved to clear
a reading. The rule answers it in four ways, and none of them is a promise about the
result:

1. **The population excludes the browse gap.** Only samples at their mandate count, so no
   above-mandate turn is baked into a tier. That is the population ADR-014 amendment 3
   takes for latency, *"never a pooled p95 of any run"* (ADR-014:579-581).
2. **The population is not the run the tiers are applied to.**
3. **The direction is unconstrained.** A tier may fall.
4. **The claim is counted at the unchanged tiers.**

**The rule:**

| | |
|---|---|
| population | `milestones/M09/fresh-join.json` `per_sample` rows with `answered` true and `at_mandate` true; `tokens_out` as that reader reconciled it against the answer files. Refused samples are in no population |
| groups | the four tiers as `cases.yaml` assigns them at `793ab1d` (M09 PR 4b, reachable from tag `m09`). No case changes group |
| statistic | each group's maximum `tokens_out`. ADR-014:84-86's *"worst case in each band"*, taken at the mandated shape as ADR-014 amendment 2 takes `tokens_in` |
| point | the midpoint of `[1.15, 1.60] ×` the maximum, rounded to the nearest hundred, exactly as `tests/test_budget_derivation.py` rounds `tokens_in`. The band is the budget band `BANDS` already pins, so the rule adds no constant |
| empty group | a tier with no sample in the population does not move |
| applied | to `cases.yaml` in PR 4, after F1–F5 are committed. **Never** to M08b's, M09's or either 09c run's claim reading. Post is re-scored at the derived tiers as a separately labelled deliverable reading |
| executed by | `tests/test_budget_derivation.py::test_each_output_tier_is_the_number_the_point_rule_produces`, PR 2. Each constant is planted red, and a plant that applies the tiers to their own population is refused. PR 4 adds the `cases.yaml` equality, and an **ADR-014 amendment 5** records any tier that moves |

**Not computed here.** The population is committed, so anyone can compute the result. The
rule was fixed from ADR-014 at line and not from its output, and **this is a published
limit of that statement, not a proof of it**: the author cannot show what the author did
not compute. The key that bites is `^tests/test_budget_derivation\.py$` at AI Quality plus
Platform Engineering.

**Headroom, read and not ruled on.** CLAUDE.md asks for 5–10% of cases at or near
failure. PR 4 publishes how many cases sit within 10% of their derived tier, and
`grounded-017` is among the names read.

## Decision 4 — `p95_ms`: a condition, then a point, and the loosening stated first

**What was dated here, at line.** ADR-014 amendment 4 withdrew the stability sentence and
left the gate *"a fixed ceiling with a recorded derivation"* (ADR-014:702-709). Two things
govern this rule:

- **The re-derivation's precondition:** *"Until a fresh mandated-shape population
  re-establishes that"* (:707-708).
- **Its schedule:** *"the first scheduled milestone that both re-runs the goldens and does
  not read its own p95 against a number it just chose"* (:711-716).

**The condition.** The stability premise is **re-established** iff the 09c control run's
mandated-shape p95 is **at or below** the point ADR-014's rule derives from M09's
mandated-shape p95. Both are read from each run's `fresh-join.json`, `p95.mandated_shape.p95`.

This is amendment 3's own failure sentence with its numbers advanced one run: *"A
mandated-shape p95 over 5200 is latency drift in the shape itself"* (ADR-014:664-666),
where 5200 was the point derived from the earlier population. M08b's 5241 over M07's 5200
failed it.

**Two same-system runs are the pair the premise needs, and M09 → 09c control is the first
such pair.** Nothing the model sees has moved since M09's run B (SPEC/09c constraint 1).
M08b → M09 differed by a prompt sentence.

**If it holds**, `gates.budgets.p95_ms` becomes the point derived from **M09's**
population, not from 09c's control run. The run that judges stability is not the population
the gate is drawn from. The arithmetic is on a number already published (ADR-075:2319-2320):
4900 at n = 36, floor 5635, roof 7840, midpoint 6737.5, **point 6700**.

**If it fails**, the gate stays 5200, recorded. No fourth population is taken, and the
close re-dates the re-derivation with its owner.

**The move lands in PR 4, after both runs**, so neither 09c run is read against a number
this milestone chose (:711-716).

**The loosening, stated before it can be discovered.** 6700 is 1500 ms above today's
gate. At 6700, M09's pooled 5630 and M08b's pooled 6633 both read *within*, and the gate no
longer reports the browse gap's share. That share reading is what ADR-014 amendment 3
built the two-number design to make. Two things make the rule admissible anyway:

- **The share reading is only meaningful while the gap exists**, and this milestone's
  claim is that it closes.
- **Era pinning** (decision 5) keeps both earlier readings OVER as published.

**Whether the gate should wait for F1 to read clean is left to the cold review.** It is
exactly the kind of coupling a reader who did not write this rule is better placed to
weigh. If the review recommends the coupling, it is an amendment before PR 3, not a choice
at PR 4.

**Executed by** `tests/test_m09c_p95_rederivation.py`, written in PR 2:

- The condition and the point are functions over the committed records, with every
  constant planted red and both branches planted.
- PR 4 reads the control run's committed record and pins the outcome.
- `tests/test_budget_derivation.py` asserts 5200 from M07's population (ADR-014:704-705).
  It goes red on the move, and PR 4 re-points it with an ADR-014 amendment, never by
  re-pinning the number alone.

## Decision 5 — the order: the moves land last, and the era pin lands first

**Measured, in a scratch copy of the tree extracted by `git archive b276c7e`, never in the
repository.**

A tier move, `entitlement-002`'s `tokens_out` 300 → 400:

```
$ python milestones/M08b/fresh_join.py --check        (before the plant)
OK: ...\milestones\M08b\fresh-join.json is what the committed inputs produce
exit 0
$ python milestones/M08b/fresh_join.py --check        (after the plant)
entitlement-002 sample 2: the transcript says tokens_out=307 over 300 and the file says 307 against a tier of 400; a planted verdict
exit 1
```

A gate move, `p95_ms` 5200 → 6700, in a second fresh copy:

```
$ python milestones/M08b/fresh_join.py --check
goldens-score.txt's latency line reads {'verdict': 'OVER', 'p95': 6633, 'ceiling': 5200} against a manifest ceiling of 6700 and a pooled verdict of within; a transcript from another ceiling
M08b exit 1
$ python milestones/M08b/fresh_join.py --dir milestones/M09 --check
goldens-score.txt's latency line reads {'verdict': 'OVER', 'p95': 5630, 'ceiling': 5200} against a manifest ceiling of 6700 and a pooled verdict of within; a transcript from another ceiling
M09 exit 1
```

**Both deliverables, taken naively, refuse M08b's and M09's committed runs through the
committed reader.** The reader is correct to refuse: it reads the tier and the ceiling
from the live tree, and a transcript scored at another value is what a planted verdict
looks like. `tests/test_m08b_fresh_join.py::test_the_committed_record_is_what_the_run_produces`
would go red in `make check` on either move.

**So there are three constraints, in order:**

1. **The era pin lands in PR 2**, on `milestones/M08b/fresh_join.py` at AI Quality,
   Platform Engineering and Security. A committed run is read against the tier and ceiling
   of the tree it was scored at. After a planted tier move and a planted gate move,
   `--check` exits 0 over M08b, M09, 09c control and 09c post, and an era the reader has
   no record of is refused by name. **No committed record is re-produced to get past
   it**: that would re-score M08b's run at tiers drawn from M09, and M09's run at tiers
   drawn from itself.
2. **The claim is read in PR 3 on an unchanged tier and gate.**
3. **The moves land in PR 4.**

**Why this does not repeat the DMA rename's reason, measured rather than asserted.**

- **The rename refuses committed runs on the model's side.** Recorded trajectories carry
  tool arguments the renamed contract rejects, and `cases.yaml`'s `viewer.dma` moves what
  the model is asked (ADR-075:1012-1021). No reading of the old run survives against the
  new system, so a new baseline is forced.
- **A tier or a gate refuses committed runs on the scorer's side only.** The answers and
  trajectories are untouched, and the value each was scored at is recoverable from the
  tree at its own commit. That is what an era pin is. ADR-075 amendment 6 §7's residual
  reader took the same remedy (:2338-2346).

The distinction is the reason these two stay in 09c while the rename leaves it (ADR-075
amendment 8).

## Decision 6 — the cap, the spare, and six lessons applied where they bite

**The cap: six PRs, including document-only ones.** Five are planned; the sixth is a named
spare:

1. PR 1, this document PR
2. PR 2, seated, zero calls
3. **PR 2b, the spare**
4. PR 3, the runs
5. PR 4, the deliverables and debt 10
6. PR 5, the close

**Two runs**, one control and one post-change, both in PR 3, within a **175-turn**
ceiling: 2 × 75, plus one whole-sample re-run of 25 for an INFRA sample. **At most one
deploy.** **One seat round, on PR 2, in two rounds.** Zero judge runs and zero re-freezes.
A correction to merged work is a PR and counts. **Reaching six closes the milestone, red if
necessary; no slide is pre-authorised.**

**Why containers count again.** ADR-075 amendment 7 §2 (:2478-2507) moved the cap off
containers and let the cold review count against no bound. M09b then spent seven
containers and no deploy, and its cap table records nothing on it spent
(`milestones/M09b/README.md:299-313`). A cap with no container bound let six prose PRs
happen with the cap reading *unspent* throughout. This cap counts both, and it states that
M09b's cap is not re-read.

**The spare is for one thing:** a cold review by a reader who wrote neither this ADR's
rules nor PR 2's executors, **after PR 2 and before PR 3 spends a call**. Its three
questions:

1. Does each executor execute its clause at the clause's width?
2. Does each falsifier's reader, run over M09's record, read a field that exists?
3. Is anything judged drawn from what judges it? That includes decision 4's open question,
   whether the gate should wait for F1.

**Its output is committed as amendment 1 to this ADR.** M09b's cold read was cited and
never reached the repository (`milestones/M09b/README.md:222-228`). If the spare is not
taken, the slot is not spent on anything else.

**The six lessons from M09b, each applied at a named place rather than restated as a
rule:**

| lesson | what it cost M09b, at line | where it is applied here |
|---|---|---|
| a falsifier names the artifact that reads it, and that artifact exists | F4's `inputs_sha256` on no file (`milestones/M09b/README.md:90-94`) | decision 2: every reader run over M09's record at the branch point, the fields listed |
| every threshold and denominator defined at pre-registration | F5's *"deciding sample"* defined nowhere (:95-100) | SPEC/09c *Thresholds and denominators*; the INFRA rule fail-closed |
| no instrument pre-registered that does not exist | the throwaway guardrail never built (:202-205) | the three readers exist today; the two derivation executors are **deliverables of PR 2**, named with their clauses, and read by nothing until PR 2b has reviewed them |
| nothing judged drawn from what judges it | a derivation rule selecting on a forbidden corpus (ADR-076 amendment 1); a wording drawn from its judging corpus's header (ADR-077 amendment 2) | decisions 3 and 4: both populations are M09's; the stability judge is 09c's control run; the fix site is drawn from M08b's and M09's trajectories and judged on post |
| the cap is on spend **and** containers | seven containers, and a cap table that records nothing spent (:299-313) | this decision |
| a prohibition's scope is not its evidence rule | `candidates.json:31` narrowed *term* to one word and passed itself (ADR-077:659-671) | F1 reads every call count, not the trigger's threshold; constraint 2's diff is an allowlist of the whole tree, not a denylist of paths; each executor is planted at its clause's width |

## What this ADR does not decide

- **The fix site.** PR 2's diagnosis names it from committed trajectories. This ADR
  pre-registers only what the diagnosis may not do: read a 09c run, name more than one
  site, or depend on the DMA rename. If it would, PR 2 stops and reports.
- **Any tier or gate value.** The rules are written and the numbers are not computed. The
  exception is the gate's 6700, which is arithmetic on a published figure and stated so the
  loosening is visible.
- **Debt 10.** Security disposes it in PR 4 on the control run's census. This ADR only
  names which census.
- **Whether `grounded-017`'s margin is a defect.** It is read, not diagnosed.

## Consequences

- **The count can fail to rise with the gap closed**, because six of the seven also fail a
  citation assert on the same sample (`milestones/M08/README.md:175-177`). The spec
  publishes no band for that reason, and F2 and F3 would say so.
- **F4 is likely to be exercised by drift.** A red on F4 alone, with F1 clean, is recorded
  as a red. The drift reading beside it is the context, never the verdict.
- **After PR 4 the tiers may differ from every tier any committed run was scored at.** The
  era pin is what keeps that from being a silent re-scoring of history.
- **Two-key gaps, measured here by matching paths against `pave.twokey.RULES`:**
  `milestones/M09c/fresh-join.json` and `tools/catalog-search/search.py` match no rule.
  PR 2 closes each one 09c writes. `data/catalog.json` matches none either, which is
  ADR-075:1025-1029's standing finding, unchanged unless the diagnosis names it.

**At scale, replace with** a before-and-after experiment service that pins a control arm,
a change arm and an era for every scorer input, and derives ceilings from a held-out
population by a registered rule. The two runs already share one reader, the derivations
already name their populations, and the era pin is that service's version column.

---

## Amendment 1 (2026-09-12, 09c PR 2, the close, with no run, deploy or model call): the diagnosis names `tools/catalog-search/schema.in.json` by quotation, and the fix does not land in 09c

**Status: the operator's ruling at the close.** It changes no decision above. It records
four things: the site the diagnosis names, how that site was reached, the measurement
that took the fix out of this milestone, and what that does to the claim.

Decision 6 and SPEC/09c:260 reserved this number for the spare's cold review. The spare
was not taken, so no cold review exists, and the number is not held open for one.

### The site, in SPEC/02's words and no others

The diagnosis names **`tools/catalog-search/schema.in.json`**. It is named by quoting
SPEC/02, the tool plane's owning document, and not by any rule written in this
milestone.

SPEC/02:551, the *Named in advance* row of its prediction table:

> | **Named in advance** | `recommend-003`, `recommend-013`, `recommend-014` fail on **contract-cannot-express**; `multi-023` loses its `t003` half for the same reason | Measured by replaying the model's own recorded queries: no legal input retrieves those titles for those intents | Any of them passing — which would mean retrieval is broader than the contract says |

SPEC/02:603-606:

> `query` is `required` and there is no filter-only mode, so **no legal input
> retrieves that title** for that intent unless the model already knows the catalog
> — which is exactly what M02 takes away. The same holds for `recommend-003` and
> `recommend-014`.

SPEC/02:634-641:

> **This is not a retrieval miss and must not be booked as one.** The model queried
> sensibly and the tool behaved exactly as specified; the contract cannot express
> the request. A retrieval miss is fixed by better ranking; this is fixed by a
> browse mode or by relaxing `required: [query]` — a schema change, a semver bump,
> and the Tool Owner's call. It is drafted as a tightening and **does not land
> here**, because SPEC/02 says the committed schemas are not modified by M02 and
> changing a tool contract mid-milestone to protect a score is the move this repo
> exists to refuse.

The four cases SPEC/02 names are `recommend-003`, `recommend-013`, `recommend-014` and
`multi-023`. All four are among SPEC/09c's seven (ADR-074:87-89). `grounded-018`,
`grounded-019` and `edge-025` are not named there.

### When those sentences were written, and what the author had read first

The quoted lines were committed in `ed57b2a` on 2026-08-18 (*"M02: close the re-review,
and the finding the first fix created"*). M02's run is `4eda0d0`, on 2026-08-19 (*"M02:
both arms run, and the pre-registered prediction is falsified"*). `ed57b2a` is an ancestor
of `4eda0d0`, and both are reachable from `main`.

So the site was named before M02's run. Twelve milestones have closed since tag `m02`:
`m03`, `m04`, `m05`, `m06`, `m06b`, `m06c`, `m06d`, `m07`, `m08`, `m08b`, `m09` and `m09b`.

**The author of this amendment had already read and classified the trajectories.** Before
any diagnosis was written, every committed trajectory of the seven cases on M08b's and
M09's runs was replayed through `search.py`. Each search beyond the first was classified
by what the model had seen when it sent it. That reading found three mechanisms, and it
was reported as a stop, because F1 says *"the site"*, singular.

A rule authored after that reading is chosen with its data in view, which is why none is
admissible here. A second draft rule would have booked the zero-row returns as a
retrieval defect in `search.py`. It was stopped by SPEC/02:634 before it was committed.
The site above rests on the quotation alone.

### Why the plan was not SPEC/02's refused move, and why that no longer decides anything

SPEC/02:640-641 refuses *"changing a tool contract mid-milestone to protect a score"*.
09c's plan differed from that move in three ways:

- the claim was pre-registered before any run, in SPEC/09c and this ADR (`852d997`);
- its five falsifiers were committed in the same PR (SPEC/09c:63-67);
- a control run on the unchanged system was to come before the change (SPEC/09c
  constraints 1 and 2).

**None of the three was reached.** No contract was edited and no run was taken. The
ruling below takes the change out of the milestone on another ground: the one that cut
the DMA rename.

### The measurement

It was taken in a scratch worktree at `e398799` and never in the repository, with zero
model calls. `"required": ["query"],` was removed from `schema.in.json`, and `python -m
pave.cli policy generate` regenerated `platform/gateway/policy/tools.contracts.json`,
removing 3 lines. The full record is `milestones/M09c/contract-relaxation-blast-radius.txt`,
with the pytest output beside it as evidence.

- **The recorded arguments still validate.** `fresh_join.py` checks every step of M08b's
  and M09's committed trajectories against the contract, and every step passes.
- **`pytest` reads 19 failed, 4688 passed, 8 skipped.**
- **Three readers' committed records stop reproducing:**
  - `milestones/M08/context_census.py`: `context-census.json` moves on 12 fields. Among
    them, `catalog-search`'s tool spec estimate goes from 294 to 287 tokens, and the
    residual's bounds move by 6.
  - `milestones/M08/residual_differential.py`: `residual-differential.json` moves on 11
    fields. Its published reading, *"The residual grew by 23 across an added spec of
    258."*, becomes 22.
  - `milestones/M08b/fresh_join.py`: M08b's and M09's `fresh-join.json`, and the planted
    fixture's, each move on one field, the digest of `tools.contracts.json`.
- **Two numbers M09 recorded no longer reproduce.** The tool spec is priced on every call.
  The fix's priced delta, `MEASURED_DELTA = 200` (`tests/test_m09_prompt_delta.py:220`;
  `milestones/M09/README.md:136`), reads **193**. The headroom it left, **106**
  (`tests/test_m09_prompt_delta.py:663-672`), reads **113**.

### The ruling

**The fix does not land in 09c.** The operator ruled it at the close, on two properties:

- **It is model-facing.** `platform/gateway/handler.py:195-210` sends the committed input
  contract to the model as its tool spec. `tests/test_gateway_run_parity.py:296-297` pins
  that spec because the tool specs *"are part of the system under measurement just as the
  prompt is"*.
- **It invalidates committed measurements in M08, M08b and M09**, as measured above.

That is the property that cut the DMA rename. ADR-075:1012-1017 says a consistent rename
*"refuses M08b's committed run"* through `fresh_join.py --check`, and that *"The three
ways out are re-producing nine milestones of trajectory records, editing committed
evidence, and sliding."* A close can take neither of the first two, and the rename slid.

**Three earlier readings missed it:**

- **Decision 5** drew its line between two cases. A tier or a gate *"refuses committed
  runs on the scorer's side only"* (:277). The rename refuses them on the model's side.
  The claim's own intervention was never placed on either side of that line.
- **SPEC/09c constraint 7** prepared two-key rules for `search.py` and `server.py`, and
  none for the contract.
- **The operator's ruling at 09c PR 2** had the contract change land in PR 3, between the
  control run and the post run.

### What this does to the claim and to decisions 3 to 6

- **All three terms: NOT MEASURED.** The claim delegates its intervention to a site whose
  change is *"a schema change, a semver bump, and the Tool Owner's call"* (SPEC/02:637-638).
  That is out of a milestone's reach. F1 to F5 were not read, and none is reported clean.
- **Decisions 3 and 4 were not executed.** Neither executor was written, and no tier and
  no gate moved. Both re-derivations are carried forward unscheduled, at AI Quality, with
  their existing triggers.
- **Decision 5's era pin was not built.** It now has a second job: the contracts digest
  that reaches the three readers above. It is carried to Platform Engineering, and the
  semver bump is its trigger.
- **Decision 6's cap: two PRs of six**, PR 1 and the close. The spare was not taken.
  There was no run, no deploy and no seat round.

### What this amendment does not decide

- The contract change's shape: a browse mode, or relaxing `required: [query]`
  (SPEC/02:636-637). That is the Tool Owner's call at the semver bump.
- How the three readers' records stay readable after that bump.
- Any tier or gate value.
- `MIN_TERM_LENGTH`'s contribution, and a partition of the trajectories by a preceding
  zero-row result. Neither was taken.

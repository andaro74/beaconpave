# ADR-074: M08b measures the ceiling on samples it was not derived from, and the rules registry stays M09

**Status: PROPOSED in M08b PR 1; ACCEPTED when that PR merges, which is the
operator's disposition.** Decisions 1 and 2 are the operator's, made
2026-09-07 on the written question the M08 close left open, and are recorded
here, not argued. Decision 3 is written before any code, any deploy and any
call, and PR 3 fills numbers into its sentences and nothing else. **Zero model
calls to write**: every number below is read out of `milestones/M08/context-census.json`,
`milestones/M08/rescore-join.json`, the three M07 answer files, and
`pave/twokey.py`.

**Seats:** PM (a row is added in place; nothing shifts) · AI Quality (a run
is recorded; a suite gate is derived; no tier or case moves) · Platform
Engineering (usage reporting in the loop; the debts on the checkout) ·
Security (the answer-channel reading rule; the G4 boundary test).

## Decision 1 — M09 as inherited is two milestones; the fresh run is M08b, in place

**The question.** M09 carried three things: claim 6 — the rules registry and
the regdelta loop, new gateway code, a seat round; the first fresh run of any
arm since M07 stage 2; and twelve dated debts, of which seven either need a
run or must be sequenced around one. The registry cannot start without the
run: Act 3's demo is *"next run, the service goes red"*, and nobody knows what
the service does today, because 12/25 is a re-reading of samples taken on
2026-09-06. The run cannot be the registry's, because a red after a
disposition on the first fresh run in two milestones is unattributable — the
disposition, the browse gap, or drift. And the two do not fit one cap of six:
the run side alone is six PRs sequenced honestly, and the registry is five or
more with a second seat round on a different control.

**What the journals say happens to a spec over its bound.** M06b's What broke
opens: *"Everything from PR #89 onward is an investigation the milestone did
not plan and should probably not have adopted."* Thirty-four PRs. M07 held its
cap and paid at the close instead: the close found the `brand_tone` owe no
seat had listed, the ADR index slid from PR 6 to the next milestone's first
PR, and eight debts went to the SPEC/08 PR. M08 held its cap and handed twelve
to "M09 PR 1". A spec over its bound does not fail loudly; it sheds
obligations into the next milestone's first PR, and the pile grows by a third
each time. Twelve on one PR is M07's PR-4 shape — the one ADR-070 amendment 1
called *"the PR that splits"* — doubled.

**The operator resolved it: two milestones, the fresh run first.** The fresh
run and every debt that needs it are **M08b**, a row added in place between
08 and 09. The rules registry stays **M09**, unchanged, with every reference
to it — `quality/judge/calibration/labels.json`'s `re_deferred_to`,
`docs/governance/recordings.json`'s Act 3, the demo script, the six code sites
that say M10 and mean the surfaces milestone — true as written.

**Why in place and not a third shift.** ADR-054 chose `06b` over renumbering
for a reason that holds exactly here: renumbering *"rewrites every downstream
id in `README.md`, `BUILD.md`, the demo script's act ownership and
`recordings.json`'s `owed_by` fields, which is a large diff across the
deferral register … taken for a cosmetic gain"*, and `00a`/`00b` split a
milestone in place without disturbing a tag or a recorded entry's sha. A
third shift would repeat ADR-073's sweep on eight two-key paths, slide the six
code sites a third time, and collect four seats to move a digit. The lineage
is real, not a label: M08 proved its claim on the samples the ceiling was
derived from; M08b proves it on samples it was not derived from. That is one
question asked twice, the second time through the real path.

### What is corrected in PR 1, and what is left as-run

Corrected, because they are live documents a reader consults for what is
scheduled: `README.md` (the progression table gains row 08b; a footnote says
what it is and how to read the ✜ paragraphs beside it), `BUILD.md` (the
milestone table), `SPEC/README.md`, and `docs/adr/README.md` (this ADR's row).
Nothing else in `README.md` moves: the twelve-claims table's `M` column, the
*Part two (M05–M12)* line, and every sentence saying claim 6 is M09's are
already true.

**Left as-run, and this paragraph is the one the operator asked for.** Every
"M09 PR 1" written between the M07 close and this ADR — in
`milestones/M08/README.md`'s debts table and What's next, in SPEC/08's
obligations table and amendment 1, in ADR-073 amendments 1 through 4, in
ADR-014 amendment 2's obligations, in ADR-070 amendment 8's `recommend-003`
reading, and in `milestones/M08/residual-differential.json`'s `paid_by.date`,
which `tests/test_m08_residual_differential.py` pins — is a record of what was
believed when written: that the first PR of the next milestone would take the
fresh run. It does, and that milestone is M08b. **Read every such "M09 PR 1"
as "the M08b PR that pays it", which SPEC/08b's obligations table names per
debt.** No closed journal, no amendment and no pinned record is edited to say
so; the residual record's date stays the string the test pins, and the test
stays. The same rule ADR-073 decision 1 applied to *"claim 6 is M08's"*.

## Decision 2 — answer quality has no claim and no row; the seven and the five are owned and unscheduled

The M08 journal dated the seven browse-gap cases (`recommend-003`,
`recommend-013`, `recommend-014`, `grounded-018`, `grounded-019`, `multi-023`,
`edge-025`) to the Tool Owner seat *"for M10"*, and the five `tokens_out` cases
(`blackout-001`, `blackout-007`, `blackout-008`, `blackout-009`, `concise-022`)
to AI Quality for *"M10"*. M10 is Playwright + k6 on one verdict schema. Its
spec cannot carry a tool change, a seat round on `tools/`, or a tier
re-derivation, and no milestone in the roadmap can: **answer quality — the
thirteen cases that fail today for a reason other than the ceiling — has no
claim in the twelve and no row in the table.** That has been true since M07
cleared the refusals, and it is stated here rather than hidden behind a date.

**The operator resolved it: both debts become owned and unscheduled, with a
written trigger, on the claim-10 precedent** — the README's `—` cell that
reads *"unscheduled, not refused"*. The owners are unchanged: Tool Owner for
the browse gap, AI Quality for the tiers.

**The trigger: persists on M08b's fresh run.** Read at PR 3, from the record:

- The browse gap **persists** if any of the seven cases carries a sample at
  four calls or more whose trajectory shows a `catalog-search` call beyond the
  case's mandate before `entitlement-check` or the answer. The count of such
  samples and cases is recorded beside M08's fourteen on seven.
- The five **persist** if any of them fails `tokens_out` by majority at its
  unchanged tier. The count is recorded beside M08's five.

If a trigger fires, the disposition is the owning seat's: a row of its own
after M09 with a before-and-after run — the fresh run being the before — or a
signed exception. Not a line in M09's spec, for the reason ADR-054 gave: one
milestone carrying the registry, the regdelta loop, Act 3, a tool change and
a tier change is how M06 came to be overloaded. If a trigger does not fire,
the debt closes as not reproduced, with M07's samples as the record of what
it was.

**Why not schedule the fix now.** Nobody has measured the browse gap on a
fresh sample in two milestones. A repair scheduled against a defect last seen
on 2026-09-06 is a remedy built against the plant it was shown; the honest
sequence is to re-measure first. And a fix for `catalog-search` changes the
retrieval every committed number was measured against, which is why M06b
recorded it and left it and why M08's constraint 5 could not touch it.

## Decision 3 — the claim, the bands, and four rules written before the run

### 1. The claim and its falsifiers

SPEC/08b's one claim: the 7700 ceiling holds per sample on fresh samples —
every answered sample at three calls or fewer under it, every sample at four
or more over it. Falsifiers: one fresh sample either way. M08's record has no
answered sample between 6792 and 8181; a fresh three-call sample at 7701 or a
fresh four-call sample at 7699 is exactly what the claim risks, and a
milestone that finds one closes red at PR 6 without re-deriving anything.

### 2. Two bands, side-predictions and not the claim

**The count.** Read from `milestones/M08/rescore-join.json`'s `per_case`:
seven cases pass 3-of-3 at 7700 (`entitlement-010`, `recommend-015`,
`grounded-016`, `brand-020`, `brand-021`, `edge-024`, `headroom-026`), five
pass 2-of-3 (`entitlement-002`, `entitlement-011`, `grounded-017`,
`grounded-019`, `headroom-005`), two fail 1-of-3 (`blackout-009`,
`entitlement-012`), eleven fail 0-of-3. The band is the twelve minus the five
at the margin on one side plus the two at the margin on the other:
**7 ≤ N ≤ 14, predicted N = 12.** Three falsifiers of the side-prediction:
N outside the band; a 3-of-3 pass failing by majority; a 0-of-3 fail passing
by majority. Each is recorded as a finding about the side-prediction and
none touches the claim.

**Refusals.** Refused by majority **0–2 of 25**, SPEC/01's band, M07's
measured 1. Falsifier: 3 or more.

### 3. The `recommend-003` reading, pre-registered

ADR-070 amendment 8 read the held text on both refused samples as a
schema-conforming **grant** carrying `entitlement-check`'s verdict into the
final answer, not `DEC-001`'s refusal-plus-alternative, and left it *"a topic
or answer-policy question, undecided"*, next read at the fresh run. The rule
that decides it, written now so the run cannot be read either way afterwards:

- **G** is the number of golden cases whose majority answer, or whose majority
  held text read through `read_withheld.py --show`, carries
  `entitlement.entitled: true` — the grants the platform produced.
- **F** is the number of cases refused by majority on the `answer` channel by
  the main pair's entitlement topic whose held text is a schema-conforming
  grant. F ⊆ G by construction.
- **F = 0:** not reproduced. The question closes as a standing observation
  with M07's two samples as the record; the trigger is any later
  answer-channel refusal.
- **0 < F < G: a topic question.** The topic discriminates among grants of
  one shape, so it is reading content the case supplies and not the
  structured verdict. Security's, as a calibration on the corpus's rule with
  its own ADR (ADR-064 recorded two calibrations refuted against the frozen
  corpora; that is the bar).
- **F = G: an answer-policy question.** Every grant the platform produces
  fires the topic, so what fires is the shape and not the words; the lever is
  the policy the `answer` arm applies to structured content, on the core rule
  (Platform Engineering, Security) with Legal/S&P, its own ADR.
- **Any refused case whose held text is `DEC-001`'s shape** re-opens ADR-068's
  conjunction question and reads as neither; recorded.
- **G = 0** makes the rule unreadable, and PR 3 says so rather than reading it.

Both counts use the majority estimator, with at-least-once reported beside
them (ADR-069). The prior, read from M07 stage 2 by this rule and recorded so
the fresh reading is compared to something: G = 8 (`blackout-007`,
`blackout-009`, `brand-020`, `concise-022`, `entitlement-011`, `grounded-017`,
`headroom-005` by majority in the answer files; `recommend-003` by its held
grants on two samples and its answered grant on the third), F = 1. Under this
rule M07 would have read as a topic question. The fresh run is the reading;
the fix, of either kind, is not M08b's.

### 4. The residual, attributed by two exact numbers

ADR-073 amendment 2 §2 bounded the per-call base at 1859–1974 with ≈1437
explained by committed text and **422–537 unattributed**, the same size with
one tool offered as with two, and named the measurement that separates
provider-side framing from content the agent sends: per-call `inputTokens`
and one calibration call. The reading, written now:

- **A** — the fresh run's round-1 `inputTokens` on `blackout-008`, the case
  the census names as the mandated-shape maximum; its three samples must
  agree, because the round-1 request is deterministic, and a disagreement is
  itself a finding.
- **B** — one gateway turn on the same viewer turn with `tools` absent and
  the same `system`, the path the handler already has
  (`offered = [...] if event.get("tools") else []`). Its `inputTokens` is the
  committed text as the model counts it.
- **E** — the census's estimate of that text: `system_prompt.tokens_est` 793
  [789, 794] plus the viewer turn at the census's chars-per-token.
- **S** — the census's `tool_specs_total.tokens_est` 603 [600, 604].

Then **D = B − E** is tokeniser density (the estimate undercounting the
committed text), **F = A − B − S** is provider-side framing (what `toolConfig`
costs beyond the specs' own text), and **A − E − S = D + F** by identity, so
the residual splits with no remainder. The reading names whichever of D and
F is 70% or more of A − E − S, or both with their shares. Neither is content
the agent can stop sending. **ADR-014 amendment 2's downward re-derivation
trigger arms only if the round-1 pin fails** — the hermetic test in PR 2 that
the first request the loop sends is `system`, the viewer turn verbatim and
`toolConfig`, nothing else. Rounds two and three are recorded, not ruled on:
per-round growth against the replayed transcript growth at the measured
density is a number in the record, and a growth more than a quarter
unexplained is a dated finding for Platform Engineering, not a trigger.

### 5. The suite `p95_ms` rule, written before the run

ADR-073 amendment 1 §4 declined to derive a latency ceiling in the PR that
would move it, and amendment 2 §4 dated the rule to the next milestone's first
PR, written before the fresh run and applied after. Here it is.

**What a suite p95 can and cannot discriminate.** ADR-014's `tokens_in` rule
places the ceiling below the next call count because turn tokens separate
cleanly by call count: no three-call turn is above 6792 and no four-call turn
below 8181. Latency does not: the fastest four-call turn in the M07 files is
3526 ms and the mandated shape's p95 is above it. So a p95 ceiling cannot be
placed below the runaway shape, and this rule does not pretend to. What a
suite p95 discriminates is a **share**: the gate passes when at most one turn
in twenty runs slower than the ceiling, and it fails when the population's
tail is no longer the mandated shape's tail.

**The rule.** The ceiling sits within ADR-014's pinned band, 1.15–1.60×, of
the **mandated shape's own p95**: the latency of every answered M07 stage-2
sample whose call count equals its case's mandate, with `evals/deterministic.py`'s
p95 (`samples[ceil(0.95 n) − 1]`) over that population. The point is the
band's midpoint rounded to the nearest hundred — the rule
`tests/test_budget_derivation.py` already executes for `tokens_in`. The inputs
are the three M07 answer files' `usage.latency_ms` and the census's per-sample
`mandated_calls`; nothing else, and never a pooled p95 of any run.

**The arithmetic, so a seat can check PR 2's test against it.** Forty
answered samples at their mandate; their p95 is **3769 ms** (maximum 3934).
Band floor 1.15 × 3769 = 4334.35; roof 1.60 × 3769 = 6030.4; midpoint
5182.375; rounded, **5200**. PR 2's test computes each figure from the
committed inputs, pins `gates.budgets.p95_ms` to the number it prints, and is
red on any planted constant; ADR-014 amendment 3 carries the number in these
words. This ADR prints no verdict at that ceiling: M07's pooled p95 of 5431
is not an input to the rule, was in view when the rule was written, and is
not the population the rule is applied to. **The fresh run's pooled p95 is
read against the ceiling at PR 3, OVER or within, and the gate costs no case
either way.**

**What the rule leaves standing.** Nineteen samples ran three calls against a
two-call mandate and are outside the mandated-shape population by
construction; fourteen ran four or more. The as-run three-call p95 is 5004
and the pooled p95 5431. A share of the population above the ceiling is what
the gate now reports, and today that share is the browse gap's; decision 2
owns it.

## Decision 4 — the order of the debts against the run

| when | debt | why there |
|---|---|---|
| **before the run, PR 2, seated** | per-call usage; `calls` in the verdict; the `p95_ms` rule executed and the gate moved; the round-1 pin; the `BANDS` pin; the G4 boundary test's guard; both readers on planted files | each changes what the run records or what it is compared to, and none may change after it |
| **the run, PR 3** | the calibration call; the entry; the `recommend-003` reading; the residual; the p95 comparison; both triggers | measurements |
| **after the run, PR 4, unseated** | `.gitattributes` and the CRLF check; the templates' condition; the ADR-index check; the cited-commit rule; nothing on stale refs beyond making the citation test blind to them | hermetic, and none touches what the run measured |
| **after the run, PR 5, alone** | the DMA rename | it moves `data/catalog.json` — the judge's `rendered_sha256`, the census's and the differential's provenance digests — and the enum in the spec the census measures; before the run it confounds every comparison to M07, and beside anything else it is a ride-along on a two-key instrument |
| **never in M08b** | the browse gap; the tiers; a `recommend-003` fix; the `brand_tone` widening; ADR-053's halves; the registry | decision 2; §3; ADR-026 amendment 3; M09's |

**The fallback, pre-registered.** Six PRs are planned against a cap of six.
If the cap is reached before PR 5, the DMA rename is the item that gives way,
re-dated to **M09 PR 1** by name in the close's journal, because M09
re-freezes the judge for the `brand_tone` widening and two re-freezes become
one. It is the fourth slide of that debt, and it is the only one this
milestone pre-authorises; any other slide is a finding.

**Two debts re-dated by name here, because their milestone number was never
updated.** ADR-053 left *"no orphan rules"* owed to M07 with its term
undefined, and *"no immortal rules"* (`effective` optional in
`rules/schema.json`) as Legal/S&P's call. Both said M07 meaning the rules
milestone; ADR-070 and ADR-073 renumbered it twice without moving them. They
are **M09's**, and SPEC/09 inherits them by that name.

**The registry's own question, named for M09 PR 1 rather than discovered
there.** `rules/MER-AI-0001.yaml` is a Meridian News disclosure rule about
AI-generated recaps. The service Act 3 says goes red, `recap-agent`, left the
registry at ADR-048; the only service is Meridian Sports; the judge has no
`meridian-news` axis until the surfaces milestone by ADR-047. Which service
the disposition makes red, and on which brand's cases, is Legal/S&P's
question and the first thing SPEC/09 must answer. Not this ADR's.

## The repository setting, paid

The M08 journal's last dated debt was the operator's: GitHub's *automatically
delete head branches* was on, against `close-milestone` step 7's *"do not
delete the merged branch"*, and it is what turned ADR-073 amendment 3's
branch-commit citations into `fatal: bad object` one PR later. **Paid before
this milestone opened.** Read from the API on 2026-09-07:

```
gh api repos/andaro74/beaconpave --jq '{delete_branch_on_merge: .delete_branch_on_merge}'
{"delete_branch_on_merge":false}
```

Recorded here because no hermetic test can read a GitHub setting; step 7 stays
the rule, and PR 4 adds the half a test can hold — a citation reachable only
from a remote-tracking branch counts as unreachable, so the 47 stale refs this
clone still carries (`git remote prune --dry-run origin`, today) cannot make
the citation test green.

## What this ADR does not decide

- Any number the run produces. PR 3 fills them into decision 3's sentences.
- A fix for `recommend-003`, of either kind. The reading is Security's; the
  fix is its own ADR on the corpus's or the core's rule.
- A fix for the browse gap or a tier move. Decision 2 owns both and schedules
  neither.
- A re-derivation of `tokens_in`. If the claim fails, that is a census
  milestone with its own rule; M08b closes red and says so.
- Which service M09's disposition makes red, and the term *orphan rule*.
  M09 PR 1's.

## Consequences

- The progression table has fourteen rows through M12 and every reference
  below row 08b is unchanged; three obligation registers keep the numbers
  they have.
- The first fresh run since M07 stage 2 is recorded as a goldens entry of
  its own kind — a run, not a re-reading — with per-call usage and `calls` in
  every verdict, so the next budget number on this arm is legible without a
  hand-join.
- The suite latency gate is a derived number for the first time since
  ADR-016 moved it to suite level, and what it reports is a share of the
  population outside the mandated shape's tail.
- Answer quality is recorded as owned and unscheduled, in the README's own
  vocabulary, and the next reading of it is dated.
- M09 opens on a measured arm, with the answer-channel question decided and
  its two ADR-053 halves named.

**At scale, replace with X; the interface already matches.** A fresh run per
release against every derived ceiling, with per-call usage and the call count
emitted by the loop as a matter of course and the suite p95 derived by the
census from the mandated shape on every architecture change; the manifest
already declares, the runner already reports per turn, and the join reader
becomes a column in the recorder. Owned-and-unscheduled debts become a
backlog register with triggers the next run evaluates, which is what
`close-milestone` step 6b already does for guardrail holes.

## Amendment 1 — a cold read of SPEC/08b before PR 2, five questions answered

**Written 2026-09-07, after PR 1 merged (`8c7a428`) and before PR 2 opened.
Zero model calls; no deploy; no seat round. Every number below is read from
`milestones/M08/context-census.json`, the three M07 answer files,
`milestones/M08/rescore-join.json`, `pave/twokey.py`, `pave/history.py`,
`evals/deterministic.py`, `tests/test_budget_derivation.py`,
`platform/gateway/core/toolloop.py`, `platform/gateway/handler.py` and the three
journals.** The reader did not write SPEC/08b. Nothing in the plan is changed
by this amendment; it names what PR 2 and the spec must change, and the
operator disposes.

**Operator's disposition, 2026-09-07: accepted in full, all ten asks.**
Committed in its own zero-call PR — PR 1b — before PR 2 cut from `main`, with
the spec corrections it names in the same diff, and §4's population table and
§5's six-row reading carried into the spec rather than left here. **This PR is
the milestone's sixth slot spent, and the cap's pre-registered fallback fires
on it** (§6): the DMA rename gives way to M09 PR 1 by name, and there is no
PR 5.

Four facts this reading established by running the code, on which the answers
below turn. Each is a check a seat can repeat.

1. **The census record digests the manifest.** `context-census.json`
   `inputs_sha256` carries `services/highlights-agent/pave.manifest.yaml`, and
   `tests/test_m08_census.py::test_the_record_is_what_the_committed_inputs_produce`
   regenerates the record from the live tree and compares byte for byte. PR 2
   moves `gates.budgets.p95_ms` in that file. So PR 2 re-produces
   `milestones/M08/context-census.json` with one digest line moved, on the
   census rule's three keys (AI Quality, Platform Engineering, Security), or
   `make check` is red. SPEC/08b's Definition of done says *"Nothing under
   `milestones/M07/` or `milestones/M08/` changed but the records PR 5
   re-produces."* That clause is unreachable as written.
2. **The register refuses an entry whose README row is pinned to none.**
   `pave/history.py::check_readme`'s last loop: a tag with a goldens entry on
   disk and a README row not in `README_GOLDENS` is a problem, and
   `run_all` runs it in `pave gate history`. SPEC/08b records the entry at PR 3
   and gives `README_GOLDENS` its `m08b` row at PR 6. PR 3's gate is red as
   planned. This is the refusal M08's amendment 3 §5 simulated and met.
3. **Three files that decide the claim sit on no two-key rule.**
   `pave/twokey.py` run over PR 2's file list: `evals/deterministic.py` — the
   scorer every goldens verdict comes from, which PR 2 changes to name `calls`
   — matches **no rule**. `milestones/M08b/fresh_join.py` and
   `residual_attribution.py`, which decide the claim and the residual reading,
   match **no rule**; the census rule is `^milestones/M08/` by name.
   `milestones/M08b/calibration.json`, the evidence for B, matches no rule; the
   goldens evidence rule names `goldens-run*.json` only.
4. **The calibration call has no producer.** `run_with_tools.py` sends
   `"tools": True` with `gw.build_tool_prompt()` and offers no flag to omit
   tools; `run_via_gateway.py` sends `gw.build_prompt()`, the control arm's
   catalog-inlined system block, which is not the same `system`. The handler's
   tools-absent path exists (`offered = [...] if event.get("tools") else []`),
   so B is reachable through the deployed gateway with the same `system` — but
   nothing committed can send that event and write `calibration.json`.

### 1. Is this M06b again?

**Not on the dimension that broke M06b. Yes on two clauses, in M06c's shape,
written by the seat that recorded that exact shape one milestone ago. And PR 4
will meet M07's close-finds-an-owe shape on PR 3's own citations, which is
predictable now.**

| | M06b | M06c | M07 | SPEC/08b as written |
|---|---|---|---|---|
| PRs | 34, no bound that held | 3 of a cap of 6 | 6 of 6 | 6 planned of a cap of 6, no spare |
| Runs through the gateway | one per hypothesis, four hypotheses | one | 216 turns, two stages | one: 75 turns, 1 calibration call, 75 headroom for one INFRA re-run |
| When the answer was chosen | never; closed on a diagnosis | step 0, two PRs in | band pre-registered, read at PR 5 | claim, both falsifiers, two bands and four rules pre-registered at PR 1; the red close pre-registered |
| Re-measurement door | after every negative result | none | none | one, bounded: an INFRA sample re-runs whole, once, the bad sample committed beside it |
| What broke | the premise was unmeasurable on arrival; an unpriced investigation was adopted | the claim was unreachable by its own plan | 22/22 masked by refusals; the close found an owe the plan had not | two DoD clauses unreachable as written (facts 1 and 2); the claim's reader on one key (fact 3) |

**What M06b did that SPEC/08b cannot.** M06b measured again after every
negative result. SPEC/08b has one door back to the gateway — constraint 5's
INFRA re-run, once, with the bad sample committed — and the claim's falsifier
closes the milestone red rather than opening a hypothesis. The twelve-debt
pile that D1 describes as the thing that grows by a third each time lands
here as PR 4, four hermetic debts on their own rules with no seat round; it is
bounded because it is named. The unbounded loop has no entry point.

**What SPEC/08b does that M06c did, twice.** Fact 1 is ADR-014 amendment 2's
own sentence one file over: *"the M08 records digest the file this PR exists
to move, so `--check` could not have stayed green across PR 3 as the spec
assumed."* That was `cases.yaml` at M08 PR 3; this is the manifest at M08b
PR 2, and the record's `inputs_sha256` says so in plain text. Fact 2 is M08
amendment 3 §5's simulation, which found the register refusing an entry three
ways, one of them this one; the spec that was written after that finding
schedules the row three PRs after the entry. Both are the M06c shape — a
checkbox the plan beneath it cannot reach — and both were found by running
the checks the spec names rather than reading it. **Both corrections land in
the spec before PR 2 opens** (asks 1 and 2 below), because a DoD corrected
after its PR prints is a checkbox rewritten to match the outcome.

**What M07's close will look like here, named now.** M07's close found the
`brand_tone` owe because flipping the row ran a check the plan had not read.
M08's close went red on PR 4's branch-commit citations one PR after they were
written. SPEC/08b PR 4 adds the rule that makes that structural: *a citation
reachable only from a remote-tracking branch counts as unreachable.* In a
fresh clone every branch `origin` publishes is a remote-tracking ref, so the
rule means **cite only what `main` or a tag reaches**. PR 3's amendment to
this ADR will cite the run commit and the calibration commit — its own branch
commits — and PR 4 then opens red on PR 3's text, which is amendment 4 §6 one
PR earlier and by design. Pre-registered here: PR 3 cites only commits
reachable from `main` or from a `cited-*` tag pushed before its merge
(`close-milestone` step 7), and PR 4's rule is run over PR 3's text before PR
3 merges. If that is not done, the red at PR 4 is a finding about this
paragraph, not about the rule.

**One ambiguity that would re-slide the pile.** *"If it is falsified the
milestone stops at PR 3, records the sample, and closes red at PR 6"* reads as
PR 4 not happening. PR 4's four debts do not depend on the claim; dropping
them on a red claim re-dates them to M09 PR 1, which is D1's shape.
Pre-registered: **a red claim stops the claim's reading at PR 3; PRs 4 and 6
proceed as planned** (PR 5 having given way to the cap, §6), and the red close
is the row's ❌ with the sample named.

### 2. Each claim, the measurement that proves it, and the PR

The spec's own 24-row table is read beside this one; the rows below are the
claims as the spec's prose makes them, which is not always the same list.

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: every fresh answered sample at ≤3 calls passes `tokens_in` at 7700, every ≥4-call sample fails it, per sample | `fresh_join.py` over the three answer files' `usage.calls` and the three single-file transcripts; `fresh-join.json` pinned; both falsifiers read empty. `evals/deterministic.py::budget` compares `got > limit`, so a sample at exactly 7700 passes; the join must say which comparison it read | PR 3 |
| 1a | …with per-call `inputTokens` and the call count in the answer file and the verdict | PR 2 by test on planted files; PR 3 by the files themselves — every answered sample carries `usage.calls` of length equal to its call count, and every `budget` failure names `calls` | PR 2, PR 3 |
| 1b | …through the deployed gateway, on samples it was not derived from | the pre-flight header (function, both guardrail versions, bundle digests equal to the tree at PR 2's merge); the audit record ids | PR 3 |
| 1c | …and no case, tier, ceiling, prompt, tool spec, topic, guardrail or catalog moved before the run | `git diff` of the named paths between PR 1's merge and PR 3's branch point, empty; the digest families; `context_census.py --check`. **The claim's own sentence says *no ceiling moved* and constraint 1 moves `p95_ms` in PR 2.** The claim must carve it out — *no token ceiling* — or the claim is false by its own plan on the day PR 2 merges | PR 3; the wording, PR 2 |
| 2 | The count: 7 ≤ N ≤ 14, predicted 12; no 3-of-3 pass fails by majority; no 0-of-3 fail passes by majority | `goldens-score.txt`; the join's `per_case` against `rescore-join.json`'s. Derived from M08's margin cases and nothing else; a prediction, not a bound, and the spec says so | PR 3 |
| 3 | Refused by majority 0–2 | `evals.refusals --sidecar` | PR 3 |
| 4 | `recommend-003`: F and G by the rule; the reading named | **No reader.** The prior G = 8, F = 1 in D3 §3 is a hand count over M07's files, and the fresh count would be a second hand count compared to the first. A reader over the answer files, the sidecar and `withheld-read.txt`, written in PR 2 and tested by reproducing G = 8, F = 1 from M07's files, is the measurement; without it row 4 is prose | PR 2 (reader), PR 3 |
| 5 | The residual: D = B − E, F = A − B − S; whichever is ≥70% named | `calibration.json`, round-1 usage, `residual_attribution.py`, its pin. **Three gaps.** (i) No producer for B (fact 4). (ii) If the calibration turn is refused on the `answer` channel the runner writes `tokens_in: 0` and B is lost; the fallback is unwritten. (iii) D can be negative — the estimate over-counting — and a 70% share of a signed sum is undefined; the rule needs signs and shares of |D| + |F|. (iv) E's key path is not named the way ADR-014 amendment 2 named the census keys; `4_by_component` carries `per_call_base_from_two_call_samples` and `calibration`, and the viewer-turn estimate must be read from a named key or computed by the census reader's own function, never re-estimated | PR 2 (producer, reader, rule), PR 3 |
| 5a | A's three samples agree | the three round-1 values in the answer files; a disagreement is recorded as a finding | PR 3 |
| 5b | Per-round growth against replayed transcript growth at the measured density; >25% unexplained is a dated finding | **No reader named.** `residual_attribution.py` reads A, B, E, S. Either `fresh_join.py` prints per-round growth per sample or the sentence comes out of D3 §4 | none as written |
| 6 | The round-1 request is `system`, the viewer turn verbatim and `toolConfig`, nothing else | The spec says *a source-reading test over `handler.py` and `core/toolloop.py`*. **The loop does not assemble the request**: `run_turn` receives `messages` and calls `converse(transcript)`; `system` and `toolConfig` are attached in `handler.py::_converse`. A source-reading test is M06b's finding 7 — the check that went red on the comment explaining the pattern — and `test_handler_wiring.py` already reads `_converse` by AST for the guardrailConfig it must not carry. The pin should drive the handler with a client double and assert the kwargs the client received, exactly three keys. If the wiring test's double cannot capture kwargs, that is the first thing PR 2 adds | PR 2 |
| 7 | Per-call usage sums to the totals; no committed verdict moves | a test; the M07 re-score's join byte-identical to `rescore-join.json`. **The M07 files carry no per-call usage, so byte-identity proves the absence path only**; the presence path is proved on planted files and on nothing real until PR 3 | PR 2 |
| 8 | `calls` in the verdict when `usage.calls` exists, absent otherwise | a test each way; M07's verdict strings unchanged. **`evals/deterministic.py` is on no rule** (fact 3); the change lands on one key unless PR 2 puts the scorer on one | PR 2 |
| 9 | The `p95_ms` rule yields one number from the mandated shape and ADR-014's constants | the derivation test: 40 samples, p95 3769, floor 4334.35, roof 6030.4, midpoint 5182.375, **5200**. Recomputed here from the committed inputs and matched exactly (§4). The test that refused a raise for two milestones, `test_the_suite_percentile_budget_was_not_raised`, is the one the pin replaces, and its replacement should carry the rule in its docstring | PR 2 |
| 10 | The fresh p95 against 5200, OVER or within | `goldens-score.txt`'s latency line. **Uninterpretable alone**: the rule claims OVER means *the tail is no longer the mandated shape's*; that needs the fresh mandated-shape p95 beside the pooled one (§4) | PR 3 |
| 11 | Browse gap persists or not | the trajectories joined to `usage.calls`; a ≥4-call sample on one of the seven with a `catalog-search` beyond the mandate. The mandate is `context_census.mandated_calls()` applied to the live cases file, reused, not re-derived | PR 3 |
| 12 | `tokens_out` five persist or not | the transcript's `tokens_out` verdicts by majority | PR 3 |
| 13 | Nothing else moved before the run | as 1c. `context_census.py --check` is green at PR 3 only because PR 2 re-produced the record (fact 1) | PR 3, with PR 2 named |
| 14 | The deployed bundle equals the tree | the pre-flight header in the sidecar | PR 3 |
| 15 | `BANDS` directly pinned | a test that plants each constant | PR 2 |
| 16 | The G4 boundary test scans the tree under a `.claude/` checkout | `SKIP_DIRS` matched against the tree-relative path; the guard reads a real file count | PR 2 as planned; PR 4 recommended (§3) |
| 17–20 | The four hermetic debts | as the spec's rows 17–20 | PR 4 |
| 21 | The DMA rename moves every digest it must and nothing else | each reader re-produces its record; the judge re-frozen; the key-by-key diff | PR 5 |
| 22 | Zero model calls outside PR 3; PR 3 within 151 turns | the PR bodies; no file under `milestones/M08b/` carrying `usage` outside PR 3. **PR 2's planted answer files must live under `tests/`, not `milestones/M08b/`, or row 22 fails on its own fixtures** | every PR |
| 23 | The entry on three keys with `refused` per case; the row | `pave gate history`; `README_GOLDENS`. **`README_GOLDENS` and the row's bold `N/25` must land in PR 3 with the entry** (fact 2); the ✅ stays PR 6's. The entry cannot move to PR 6 instead: the recorder names `HEAD`, and at PR 6 `HEAD` is PR 5's merge, a tree whose catalog the rename has moved | PR 3; PR 6 for the ✅ |
| 24 | `delete_branch_on_merge` is off | asserted from the API; no hermetic test | PR 1, recorded |
| 25 | *The registry cannot start without the run* (the Why) | an argument, not a claim; nothing measures it and nothing should | none, correctly |
| 26 | The rule's premise: the mandated shape's latency tail is stable across runs, so a share above it is the browse gap's | the fresh mandated-shape p95 against 5200 (§4). Not in the plan | none as written |

Five rows have no measurement in the plan as written: 4, 5 (three gaps), 5b, 6
(as specified), 26. Rows 4 and 5 are readers PR 2 can write; 6 is a test
written the other way round; 5b and 26 are one column each in `fresh_join.py`.
None is the claim. Rows 1c, 13, 22 and 23 are reachable only after the spec is
corrected.

### 3. Is M08b as specified one milestone, and is PR 2 M07 PR 4 again?

**One milestone, yes. PR 2 is not M07 PR 4's shape and is M08 PR 3's shape
on one axis.** M07 PR 4 carried five decisions on five subjects — a run, a
probe suite, step 6b, a two-key disposition, a new rule — and the split moved
the zero-call, deadline-bound ones to the PR already collecting their keys.
M08 PR 3 carried the number plus four dispositions, and the fix was the same
move. PR 2 here carries nine items on **one subject** — the instrument — and
one question, and the question is the right one. Where it is M08 PR 3 again
is the count of findings a round can produce on nine items: PR 3 took 17
findings from four seats with fixes in the same PR, and a round on nine items
should be planned as two rounds, the second on the first's fixes, before the
PR opens.

The nine, with the rule each file sits on and whether it must precede the run:

| item | files | rule and seats | must precede the run | recommendation |
|---|---|---|---|---|
| per-call usage | `core/toolloop.py`, `handler.py`, `audit.schema.json` | gateway decision path (Platform Engineering, Security) | **yes** — it is what the run records | PR 2 |
| the producer writing `usage.calls`; the calibration producer | `run_with_tools.py` | goldens producer (Platform Engineering, AI Quality) | **yes** | PR 2; the calibration flag is unlisted and must be added (fact 4) |
| `calls` in the verdict | `evals/deterministic.py` | **none** | yes, if PR 3's transcript is to carry it and the demo line to be true | PR 2, and the scorer goes on a rule in the diff that changes it (ADR-060's precedent) — AI Quality with Platform Engineering, the derivation pin's pair. Otherwise the file ADR-037 would have named next stays on one key with a dated finding |
| the `p95_ms` rule executed; the gate moved | `tests/test_budget_derivation.py`, `pave.manifest.yaml`, `context-census.json` (digest line) | derivation pin (AI Quality, Platform Engineering); manifest (AI Quality, Tool Owner); census (AI Quality, Platform Engineering, Security) | **yes** — it is what the run is compared to | PR 2; the census re-production is unlisted (fact 1) |
| the `BANDS` pin | `tests/test_budget_derivation.py` | derivation pin | no | PR 2, because the file is open on the same two keys; it costs the round nothing and rides PR 4 on the same keys if the round needs shortening |
| the round-1 pin | a new test over `handler.py` | none unless placed in `tests/test_handler_wiring.py` (Platform Engineering, Security) | **yes** — it arms or disarms ADR-014 amendment 2's trigger, and the code it pins is PR 2's | PR 2, in the wiring test's file so it sits on the handler's rule |
| the G4 boundary guard | `tests/test_g4_capture_boundary.py` | audit record shape (Platform Engineering, Security) | **no** — it touches nothing the run records or is compared to | **PR 4.** Its keys are the file's and PR 4 collects attestations per rule; what it loses is a seat round on a `SKIP_DIRS` path fix, which the deletability audit covers |
| `fresh_join.py` and its pin | `milestones/M08b/fresh_join.py`, `tests/test_m08b_fresh_join.py` | **none** | **yes** — it decides the claim and must exist before the data it reads | PR 2, with the census rule widened to `milestones/M08b/` readers and records in the same diff, which pulls `pave/twokey.py` (four seats) and `tests/test_twokey_seats.py` (five) into PR 2 |
| `residual_attribution.py` and its pin | `milestones/M08b/residual_attribution.py`, `tests/test_m08b_residual.py`, `calibration.json` | **none** | yes for the reader; the evidence file needs a rule before PR 3 writes it | PR 2, under the same widening |

**The answer to the question asked.** One item rides PR 4 without losing a
key: the G4 boundary guard. One item could but should not: the `BANDS` pin,
because its file is open in PR 2 anyway. Nothing else can move, because
everything else either changes what the run records, changes what it is
compared to, or decides what the run means — and the last category is on no
rule today, which is a finding, not a scheduling question. **After the
widening PR 2 collects all five enforced seats** (Platform Engineering,
Security, AI Quality, Tool Owner, Legal/S&P on `pave/twokey.py`), which is M08
PR 2's register shape and acceptable. The seats are told what to plant, not
what to read: a per-call list whose sum disagrees with the total; a verdict
that names `calls` from the total rather than the list; a foreign population
in the p95 test; a `fresh_join.py` that reads the ceiling from the manifest
rather than the cases file; a calibration event that carries `tools: True`.

### 4. The manifest gate: printed from which population, and in which PR

**The population is forty answered M07 stage-2 samples whose call count equals
their case's mandate**, read from `2_stage2_per_sample` (`answered`, `calls ==
mandated_calls`) joined to the three answer files' `usage.latency_ms`. The two
refused samples carry `latency_ms: null` and are in no population.
Recomputed here from those inputs, with `evals/deterministic.py`'s
`samples[ceil(0.95 n) − 1]`:

```
pooled n 73 p95 5431
mandated n 40 p95 3769 max 3934
above-mandate 3-call n 19   four+ n 14   min four-call latency 3526
floor 4334.35  roof 6030.4  midpoint 5182.375  rounded 5200
3-call as-run p95 (n 59) 5004
```

Every figure in D3 §5 reproduces. **The number is 5200 and PR 2 chooses
nothing**: the population, the percentile, the band and the point rule are all
fixed in PR 1, and PR 2's test either prints 5200 from the committed inputs or
is red.

**Is 5431 the hazard ADR-073 amendment 1 refused?** That amendment refused
*deriving a new rule in the PR that moves the number, with the number it will
be applied to in view*. Two of those three conditions are not met here and
one is met at PR 1, not PR 2. The rule is not derived in PR 2; it was written
in PR 1 and adds no constant. The number it is applied to — the fresh run's
p95 — is not in view at PR 2 and cannot be. What was in view when the rule
was written, at PR 1, was M07's pooled 5431, and D3 §5 says so. What the
spec should do with that is what pre-registration can still do after the
fact: **name the populations the rule could have taken and the number each
gives, so a seat can see the one taken is the one that fails the known run.**

| population | p95 | band | point | M07's 5431 reads |
|---|---|---|---|---|
| mandated shape, n = 40 (**the rule**) | 3769 | 4334–6030 | **5200** | **OVER** |
| as-run three-call, n = 59 | 5004 | 5755–8006 | 6900 | within |
| pooled, n = 73 | 5431 | 6246–8690 | 7500 | within |

The rule takes the only population under which the run in view fails the
gate. That is the opposite of the flattering choice, and it is the one fact
that makes the in-view hazard survivable. It belongs in the spec, not only
here.

**The gate moves in PR 2, and PR 3 would be the wrong PR.** The `tokens_in`
sequence was: band pinned two milestones earlier, census committed at PR 1,
number moved at PR 3, first count at PR 4. The latency sequence is: rule at
PR 1, number executed and gate moved at PR 2, fresh run read at PR 3. Moving
the gate in PR 3 puts the fresh p95 in view when the number lands, which is
the hazard in its real form; PR 2 is the last PR at which the fresh number
does not exist.

**What the spec must say, in PR 2's diff.**

1. The population by key and count, as ADR-014 amendment 2 named the census
   keys: `2_stage2_per_sample`, `answered`, `calls == mandated_calls`, n = 40.
2. The number, 5200, and the predicted line for M07's files at the new gate,
   printed now so nobody reads it later as a surprise:
   `suite latency  OVER p95=5431ms over 5200ms`. The M07 re-score at PR 2
   prints that line and 12/25; the join is byte-identical because the join
   reads token verdicts, not the latency line.
3. The table above — the two populations not taken and the numbers they give.
4. That PR 2 re-produces `milestones/M08/context-census.json` with its
   manifest digest line moved and nothing else, shown key by key, on the
   census rule's three keys; and the DoD's `milestones/M08/` clause amended to
   name it.
5. That `test_the_suite_percentile_budget_was_not_raised` is the test replaced,
   and its replacement's docstring carries the rule and the reason the
   two-milestone refusal ends: the number is derived, not raised.
6. **What PR 3 reads: two numbers, not one.** The fresh pooled p95 against
   5200 (OVER or within), and the fresh mandated-shape p95 against 5200
   beside it. Pre-registered readings: pooled OVER with mandated-shape p95 ≤
   5200 is the share the rule was written to report, the browse gap's, and
   decision 2 owns it; mandated-shape p95 > 5200 is latency drift in the
   shape itself, a dated finding for Platform Engineering, and the rule's
   premise — that the mandated shape's tail is stable — is what failed. One
   number cannot tell these apart; `fresh_join.py` prints both at zero cost.

### 5. The near miss: what a sample at 7720 at three calls means, and is it pre-registered

**The spec says a single sample either way falsifies the claim, and nothing
else.** It does not say what the sample means, and a red close would record
"the ceiling failed" for four different failures. The numbers the reading
needs, all from M08's record: point **7700**; unrounded midpoint **7675.125**;
band **[7171, 8180]**; the record's gap **(6792, 8181)** — 908 tokens (13.4%)
above the as-run three-call maximum, 481 (5.9%) below the four-call minimum;
mandated-shape maximum **6235**; the comparison `got > limit`.

**7720 at three calls is not a grain event.** The rounding grain is the
interval where the rounded and unrounded points disagree: **(7675.125, 7700]**.
7720 is above both. It falsifies the number and the rule's own unrounded
output alike, and the rounding is not implicated. What it is depends on the
sample's mandate, and the reading forks there:

| the falsifying sample | what moved | re-derived band | lesson recorded |
|---|---|---|---|
| ≤3 calls, **at mandate**, in (7700, 8180] | the mandated-shape maximum is now ≥ that value; floor 1.15 × 7720 = 8878 > 8180 | **empty** | **the rule failed**: no ceiling can sit 1.15× above this shape and below the next call count; a re-derivation by the same rule has no solution, and the census milestone needs a different rule (per-case, or a call-count gate) |
| ≤3 calls, **above mandate**, in (7700, 8180] | nothing in the band's inputs; the browse gap's first extra call grew | unchanged, contains 7700 | **the point failed inside a band that still holds it**: the midpoint rule left 908 tokens over the as-run three-call maximum and that was not enough; statement 3's *discriminates call count ≥ 4* is the sentence that was wrong for this sample |
| ≤3 calls, > 8180 | the shape overlaps the four-call shape | empty | the rule failed, as row 1 |
| ≥4 calls, in [7171, 7700] | the four-call minimum moved under the point; roof = that value − 1 < 7700 | non-empty, **excludes 7700** | **the point failed and the rule survives**: the same rule re-derives lower (a four-call minimum of 7650 gives [7171, 7649], midpoint 7410, point 7400) |
| ≥4 calls, < 7171 | roof < floor | empty | the rule failed |
| either side, **inside (7675.125, 7700]** | — | — | **the grain**: a three-call sample here passed only because the midpoint rounded up, a near miss recorded and not a falsification; a four-call sample here passed for the same reason, and that IS a falsification the rounding caused, so the lesson is the grain and not the ceiling |

**Pre-registered, so a red close records the right row:** `fresh_join.py`
prints, for every answered sample, its distance to 7700, to 7675.125 and to
the nearer band edge, and for the run as a whole the fresh mandated-shape
maximum, the fresh four-call minimum, the band those two re-derive by
ADR-014's pinned rule, and whether 7700 sits inside it. A falsifying sample
is recorded with its row of the table above by name. This is arithmetic on
numbers the join already carries, zero cost, and it is the difference between
a red close that says *the ceiling failed* and one that says which of the
point, the grain, the band or the rule did.

**And when the claim holds, the same column is the finding for M09.** The
claim can hold while the rule does not: a fresh three-call sample at mandate
at 6900 passes 7700 and moves the floor to 7935, so the re-derived band
[7935, 8180] no longer contains the number that held. *The number holds, the
rule does not* is a sentence the spec cannot write today, and it is the one
M09 needs before it puts a rules loop on this axis. The side-reading is
pre-registered here as recorded, not ruled on: 7700 stands wherever the
fresh band lands, because a ceiling moved on a fresh run's band is a
re-derivation, and that is a census milestone.

One more thing the falsifier's sentence should carry. The two tails are not
the same distance away — 908 tokens on the three-call side, 481 on the
four-call side — and the spec predicts neither. It should not predict a side;
it should say the reading is side-specific, which the table above makes it.

### 6. The cap, and the fallback it fires

SPEC/08b caps M08b at six PRs and planned six — PR 1 through PR 6 — with no
spare. This amendment is committed as a seventh, so the cap is reached before
PR 5 and the spec's own sentence applies: *the DMA rename is the pre-registered
item that gives way, by name, if the cap is reached before PR 5.* Decision 4
pre-authorised exactly one slide, to **M09 PR 1** by name, because M09
re-freezes the judge for the `brand_tone` widening anyway and two re-freezes
become one. **Taken here, at PR 1b, not discovered at the close.** The six are
PR 1, PR 1b, and PRs 2, 3, 4 and 6; PRs 2–6 keep their numbers so every
reference in the spec and this ADR stays valid (ADR-073 amendment 1's
precedent), and there is no PR 5. It is the fourth slide of that debt and the
only one this milestone pre-authorised; any other slide is a finding. What it
leaves: nothing under `milestones/M08/` moves in this milestone but the census
record's manifest digest line (fact 1), and M09 PR 1 carries the rename beside
its own re-freeze, in no PR with anything else. The alternative — folding this
amendment into PR 2 to stay under the cap — was not taken, because a reading
of the plan committed in the diff that acts on it is the pre-registration
failure ADR-014 amendment 2 records, one PR over.

### What this amendment asks PR 2 to carry, beyond what SPEC/08b lists

1. **The spec's DoD corrected before PR 2 opens**, in its own zero-call diff:
   the `milestones/M08/` clause names the census record's digest line;
   `README_GOLDENS` and the bold goldens cell move to PR 3 beside the entry,
   the ✅ stays PR 6; the claim's sentence says *no token ceiling* and carves
   out `p95_ms`; *stops at PR 3* is reworded so PRs 4 and 6 proceed on a red
   claim; the calibration call gains a producer and a fallback; PR 3's
   citations are held to PR 4's rule before PR 3 merges; the DMA rename
   re-dated by the fallback (§6).
2. The census record re-produced with its manifest digest moved, key by key,
   on three keys.
3. The census rule widened over `milestones/M08b/` readers, records and
   `calibration.json` in the diff that creates them, with a `_blocked_for`
   plant each; `evals/deterministic.py` put on a rule in the diff that
   changes it, or the finding dated with ADR-037's name.
4. A calibration producer on `run_with_tools.py` — the same event with tools
   absent, one case, `--out calibration.json` — tested hermetically; the
   refused-turn fallback pre-registered: B is read from the audit record's
   per-call usage if PR 2 puts it there, else the call is re-issued once on
   the case with the next-highest mandated-shape `tokens_in` in the census,
   **`entitlement-010`** (6229 against `blackout-008`'s 6235), with A read
   from the same case and the substitution recorded.
5. The round-1 pin as a behavioural test on the handler's client kwargs, in
   the wiring test's file.
6. An F/G reader tested by reproducing G = 8, F = 1 from M07's files.
7. `fresh_join.py` printing, beside the join: the fresh mandated-shape p95
   and the pooled p95; per-round growth per sample; the near-miss columns
   and the re-derived band of §5.
8. The residual rule with signs: shares of |D| + |F|, each sign reported; E
   by named key.
9. The p95 section of the spec carrying §4's six items, including the two
   populations not taken and the predicted M07 line at 5200.
10. The G4 boundary guard moved to PR 4; PR 2's seat round planned as two.

### What this amendment does not change

The claim. 7700, the band [7171, 8180], and the placement below 8181. The
count band [7, 14] and its prediction. The refusal band. The `recommend-003`
rule and its prior. The residual's four numbers and two identities. The
`p95_ms` rule, its population, and the number 5200. The order of the debts
against the run. The cap — six, and spent by §6. Constraints 1–10. Decision
2. Outcome B where ADR-073 decision 2 left it.

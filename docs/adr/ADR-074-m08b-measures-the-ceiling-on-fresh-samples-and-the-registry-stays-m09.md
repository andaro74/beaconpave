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

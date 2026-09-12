# ADR-076: M09b rewords the topic under a rule written first, adds the rule's second control, and carries none of the twelve

**Status:** accepted, at the M09b open (2026-09-11), before the branch was cut and
before any candidate wording existed.

**Written before any measurement.** `SPEC/09b-the-guardrail-line-and-the-topic.md`
states the milestone; this records the decisions behind it. Both were written in
the same PR, and neither was approved in conversation: every number below is read
from a committed file by a command named beside it.

**Why a new ADR rather than an eighth amendment to ADR-075.** Argued because the
default here is an amendment. Every wording change to `entitlement-circumvention`
has had its own decision record — ADR-024, ADR-035, ADR-063 — and
`^platform/infra/lib/gateway-stack\.ts` carries `requires_adr=True` in its own
words: *"If a tightening is worth deploying it is worth a paragraph saying what it
should break."* M09b rewrites that definition and adds a third topic beside it.
ADR-075 is 2429 lines under a title about M09 being two milestones, five of its
six amendments are M09's own PR records, and a seventh carrying a successor
milestone's pre-registration would have to contradict its decision 1's ground to
do it. Precedent is uniform: ADR-070 for M07, ADR-073 for M08, ADR-074 for M08b,
ADR-075 for M09. **ADR-075 amendment 7 carries only the two facts that belong in
ADR-075** — decision 1's false ground, and decision 6's cap rule — and stops.

## Decision 1 — M09b carries one pre-registered claim and none of the twelve

**The question was re-opened rather than inherited, because the sentence that
settled it is false.** ADR-075 decision 1 reads *"Claim 6 is proven by then, so
nothing in M09b is load-bearing for a claim."* Claim 6 is **FAILED**, on F1
(`disclosure-103`) and F4.2 (`grounded-017`), recorded in that ADR's own
amendments 5 and 6. The conclusion happens to stand; it stood on a premise the
milestone then contradicted, which is ADR-055's *row copied forward past an open
question*.

**Re-answered on the merits. M09b advances none of the twelve**, and serves
**claim 9** defensively — M03 measured **3 of 8** of the judge's own calls refused
by this topic, 38% against a pre-registration of under 4%, which is a platform
that cannot calibrate a judge against its own recorded answers — and **claim 6**
defensively, by giving `MER-AI-0001` a second control and the chain reader a
walker that reaches an assert through it.

Three reasons, none of them *"claim 6 is proven"*:

1. **Attribution.** Re-advancing claim 6 puts a third control in a milestone that
   already moves two guardrail topics through one deploy. A red would be
   unattributable — ADR-074 decision 1's argument and ADR-075 decision 1's,
   applied to their own successor.
2. **The failure was a premise, not a mechanism.** F1 fired because the
   pre-disposition baseline was confirmed on evidence that was off-subject: no
   golden case asks for editorial copy, so 56 null samples were 56 samples of a
   different question. Re-advancing claim 6 honestly needs a subject-matched
   pre-registration baseline. That is instrument work and it is not guardrail
   work.
3. **G9, applied to a milestone instead of a file.** A milestone that both carries
   a claim and rewords a guardrail has the strongest possible incentive to reword
   until the claim reads green. Withholding the claim removes that pressure by
   construction.

**M09b does carry one claim**, on M07's shape — a milestone with a claim and a
falsifier set that advances none of the twelve. It and its five falsifiers are in
`SPEC/09b`, *The one claim*, and are not restated here.

**What this costs, stated.** Claim 6 stays ❌ in the twelve-claims table until some
later milestone re-advances it. That is the honest state and M09b does not improve
it by re-registering a claim M09 already failed. The **honest weaker statement**
M09's close recorded — *"the fix moved disclosure on editorial-copy requests from
intermittent to reliable: 7 of 7 after, against 4 FAIL / 3 PASS before"* — is
pre-registered in `SPEC/09b` as a **side-prediction**, in that weaker form,
because a claim replaced after its falsifier fires is a claim chosen to match its
outcome.

## Decision 2 — the wording is chosen by a rule, and the rule cannot read the golden set

**The hazard, stated so it cannot be discovered later.** M09b rewords a guardrail
topic so that cases stop being wrongly refused. Those cases then stop being
refused. **A topic reworded until cases pass is a threshold moved to clear a
reading — the trade M09 failed a claim rather than take.**

The derivation rule is in `SPEC/09b` and is executed by
`tests/test_m09b_topic_selection.py`, merged before the wording is written. Three
properties decide it, and each is a falsifier clause rather than a warning:

- **The candidate set is fixed in number and committed by digest before a single
  sweep is taken**, with one line of provenance per token a candidate introduces
  that the deployed wording does not already contain. ADR-024's honesty clause is
  prose today; this executes it, on the practice `gateway-stack.ts`'s own comments
  already follow by hand (*"`credential` is version 2's own word, kept unchanged"*;
  *"the new term is `spoofed region` — the policy concept rather than the corpus's
  noun"*).
- **Admissibility is fail-closed and is decided on frozen corpora only.** Every row
  of `topic-attacks.yaml`, `topic-attacks-heldout.yaml` and
  `topic-attacks-output.yaml` that the deployed version blocks 3 of 3 must still
  block 3 of 3, and `ADV-006`, `ADV-009`, `PHR-002` and `PHR-003` — the four
  negative controls `gateway-stack.ts` names for this topic — must still be denied.
- **The golden set is not an input to selection, at all**, and F4 fires if the
  selection record's `inputs_sha256` names it. It **is** a cost corpus for the
  additive disclosure topic, on ADR-035's precedent, because measuring what a
  purely additive topic costs the product's own questions is a cost measurement
  and not a selector. The two rules differ, and the difference is stated rather
  than left to a reader.

**`answer-decomposition.yaml` selects nothing**, on ADR-067's own sentence: *"any
candidate wording is judged by the frozen corpora, never by this file."* It is
read as a diagnostic beside the result.

**The ordering is checked, not asserted.** `topic-attacks-heldout.yaml`'s header
asks a reader to verify in the history that the corpus predates the wording it
judges — *"if the order is reversed treat this check as worthless."*
`tests/test_m09b_ordering.py` reads `git log` over the local object database and
is red if a candidate's commit precedes the corpus that judges it. Hermetic (G8),
on `tests/test_cited_commits_resolve.py`'s precedent.

**And the count is pre-registered NOT to move.** Read from M09's own per-case
verdicts: of the four cases refused at least once, `brand-021` already passes by
majority, `concise-022` fails on `tokens_out=327 over 300` whether refused or not,
and `recommend-003` fails on `must_mention` and `must_cite` in the two samples
that were **not** refused. **Only `blackout-009` can move `N/25`, and its content
has never been scored.** So the band is [9, 12] with 10 predicted, and a jump is a
finding about the wording rather than a success. That is the hazard closed from a
second direction: a milestone that has published in advance that its number should
not move cannot present a moved number as a win.

## Decision 3 — the character budget, and what happens when nothing fits

**Measured, not estimated.** From the committed synth snapshot
`platform/infra/tests/fixtures/BeaconpaveGateway.template.json`: `medical-advice`
**127**, `entitlement-circumvention` **191**, `enforcement-probing` **170**.
`tests/test_iam_assertions.py:303` pins `MAX_TOPIC_DEFINITION = 200` against that
snapshot. **Nine characters of headroom.**

This is M09b's equivalent of SPEC/09's prompt-delta test: a bound knowable before
a call is spent. Three consequences:

- **A widening cannot be bought with a second topic.** ADR-035 added
  `enforcement-probing` precisely so `entitlement-circumvention` could stay
  byte-identical, and a DENY topic is purely additive — it can only block *more*.
  M09b needs the existing topic to block *less*. There is no additive route, and
  the definition must be rewritten inside 200 characters.
- **ADR-035 rows 12, 17, 18 and 19 stop holding by construction.** They have held
  since `enforcement-probing` landed *because* this definition was byte-identical.
  The moment M09b edits it they must be re-measured, and the pre/post sweeps are
  what re-measure them. Recorded here rather than found at the close.
- **If no admissible candidate fits 200 characters, the milestone publishes that
  and does not deploy the recalibration.** A pre-registered outcome, not a
  failure. The disclosure line still lands — it is a new topic with its own 200 —
  and the close records that the topic could not be recalibrated within its cap,
  which is a finding about the instrument and is publishable.

## Decision 4 — the second control is a DENY topic, with its own corpus and its own walker

**What `MER-AI-0001` disposes into at L1.** A guardrail blocks; it cannot require.
So the guardrail line the rule disposes into is a DENY topic whose subject is **an
assertion of human authorship, or a denial of AI involvement, in editorial copy
the service authors**. That is the hole the rule's own `limits` record names as
unreachable by the L3 control:

> What no deterministic check of this shape can fix is NEGATION: a field reading
> "written by a human, not by AI" contains the token and would pass.

The rule's limit calls that *"a judge's question"*. **It is not answered with a
judge here**, and that is deliberate: a judge axis moves a frozen instrument, and
M09b holds `quality/judge/frozen.json` byte-identical (decision 6 of ADR-026
amendment 5's reasoning). An L1 classifier is a different control at a different
layer, and it moves no instrument the eval plane reads.

**The definition text is not written in this ADR.** Its subject and its corpus are
decided here; the wording is selected in PR 3 by decision 2's rule, from its own
candidate set, against `quality/adversarial/disclosure-shapes.yaml`. An ADR that
drafted the wording would be the author choosing the answer one document earlier.

**The corpus, and F1's lesson as a procedure.** `disclosure-shapes.yaml` is
minimal pairs at `source=OUTPUT`, on `refusal-shapes.yaml`'s shape: copy denying
AI authorship (must block), copy disclosing correctly (must allow), factual copy
owing no disclosure (must allow). **Every `must_block` row is swept against the
pre-deploy guardrail first, and a row already blocked there is moved out of the
control set and recorded as already-covered, before the wording is written.** That
is M09's F1 turned into a procedure: a control the service already satisfies is a
delta that was not one, and the way that was discovered at M09 was by running the
pre-fix arm. Here it costs no model call at all.

**The chain reader cannot walk it today, and that is measured.**
`pave/rules.py`'s `CONTROL_ARTIFACTS["guardrail"]` is `("platform/gateway/", …)`
and the deployed guardrail is defined in `platform/infra/lib/gateway-stack.ts`:

```
platform/infra/lib/gateway-stack.ts                          guardrail-control admissible: False
platform/infra/tests/fixtures/BeaconpaveGateway.template.json guardrail-control admissible: False
platform/gateway/policy/tools.contracts.json                 guardrail-control admissible: True
```

**The one control this repository's registry was built to carry could not be
declared without the reader refusing it** — `chain: NOT RESOLVED`, exit 1, on
claim 6's own command, in the milestone that adds it. The reader's own comment
anticipates M09b by name (*"M09b would have made claim 6's own command red by
strengthening the control"*) and its artifact table does not reach the file.

**M09b widens the home and builds the walker.** A `guardrail` control today
produces a `walked` step, which is not a defect and is not RESOLVED either —
correct while no walker exists, and a relaxation of row 1a if left in place. The
walker goes rule → `selector` → the corpus rows naming that topic → the test that
asserts them, so `Chain.resolved` survives a second control and the disposition
gets **stronger** rather than unwalkable. `rules/schema.json` gains `selector` and
`additionalProperties: false` — today a control may carry a field nothing reads.
Both on `(legal-sp, security)` plus this ADR.

## Decision 5 — one deploy, and the premise that makes two controls separable

**One deploy, and a second closes the milestone with what it has.** A deploy
replaces the guardrail version resource, and every pre-deploy reading goes with
it: `topic_baseline.py`'s own header says *"it must run before Change A deploys,
and it cannot be run late."*

**Two controls in one deploy is admissible here and was not at M09, and the
difference is a mechanism rather than a judgement.** ADR-075 decision 1 split M09
because *"a red after a disposition and a new guardrail line is unattributable
between the two controls."* A disposition's red and a guardrail's red do not name
themselves. **Two topics' refusals do.** Measured on M09's own sidecar: four
refused cases, **exactly one `TOPIC:` per sample**, and `blackout-009` splits
within itself — samples 1 and 2 `entitlement-circumvention`, sample 3
`enforcement-probing`. The record attributes every refusal to a named topic on a
named channel, which is the machinery ADR-063 and ADR-070 built.

**The premise is falsifiable rather than assumed.** `SPEC/09b`'s **F5** fires when
a refused sample that decides F1 or F3 names more than one `TOPIC:` in `assessed`.
If the two controls turn out not to separate on a sample that decides a falsifier,
the claim fails and the milestone says so — rather than the milestone discovering
at its close that it ran two experiments and can read neither.

## Decision 6 — every band is read on both estimators

**M09 produced three independent instances of a majority reading masking
instability**, in two PRs: `disclosure-101` at 1 of 3; the count at `10/25`
published over a fired falsifier; refusals at 1 of 25 by majority and 4 of 25
at-least-once. The repository had already chosen the other estimator once —
ADR-035 picked refused-at-least-once for exactly this reason — and
`evals/refusals.py` already computes both and publishes
`cases_separating_the_estimators`. What was missing was specs reading only one.

**So: a side-prediction read by majority carries an at-least-once companion,
published beside it, and where the two disagree the disagreement is the reading.**
Every band in `SPEC/09b` is stated for both estimators or it is not a band.

**F1 is not re-scoped to the at-least-once estimator**, and that is deliberate.
ADR-075 decision 5 §5 pre-registered `F = 0 with G ≥ 8` through
`answer_channel.py` unchanged, before the seat that wants the topic widened wrote
anything — which is what G9 is for — so it is **inherited unchanged** and the
companion is a banded side-prediction beside it. A falsifier re-scoped by the
milestone it judges is not pre-registered, whichever direction it moves.

**And the reader takes its baseline as an argument.** M09's finding: the committed
reader's direction block compares against M08 through a module constant, so run
over M09's answers it reported both falsifier lists empty **on the run where F4.2
fired**. Its trigger is *the next milestone that re-runs the goldens as a control*
— M09b — so `milestones/M09b/fg.py` takes its baseline as an argument, and the
debt is paid where it fires.

## Decision 7 — the cap is on spend and irreversibility, not on containers

Amendment 4 of ADR-075 recorded the finding against the rule rather than against
the PR that breached it: *"the cap counts PRs as a proxy for scope and has no
concept of a correction to already-merged work."* M09b's cap is written the way
that finding asked.

**One deploy. One model-call PR at 160 turns** (75 goldens + 33 probes + 21
disclosure pack = 129, plus one whole-sample re-run of the largest arm for an
INFRA sample). **One seat round, in two rounds, on one PR. Zero judge runs, zero
re-freezes.**

**Containers are counted and published and are not the bound.** A correction to
already-merged, already-dispositioned work is admissible in its own PR and is
scoped by *what it may contain* — no number moves, no new capability, no case,
threshold, corpus row, tier, ceiling or instrument digest moves, and empty diffs
over `milestones/`, `evals/history/` and the manifest. A PR that cannot meet that
scope **is** scope growth and closes the milestone.

**And the cold review stops competing with the work for a slot.** ADR-075 decision
6 made PR 1b *"the sixth"*, so taking it spent the cap and armed the fallback by
name. Under a cap on spend the cold read costs no deploy and no turn, so it counts
against no bound. That is the second half of amendment 4's finding: a container
count priced the one slot that has caught something material in every milestone at
the same rate as a slot that runs the model.

**The fallback, pre-registered by name.** If the turn ceiling or the deploy bound
is reached, the **disclosure pack re-run and its comparator pin** give way,
re-dated in the close's journal to the first later PR that takes a disclosure run.
The claim's own measurements never give way. Any other slide is a finding.

## Four rule gaps, measured on `52edc27` by running the gate

Each was found by running `pave gate two-key --changed` or the reader over a
prospective file list, never by reading the rules list. All four are closed in the
diff that creates the artifacts they cover, never in a follow-up — ADR-060's
precedent, which ADR-075 amendment 1 already applied once.

| gap | measured | closed |
|---|---|---|
| `CONTROL_ARTIFACTS["guardrail"]` points at a directory the guardrail is not defined in | decision 4's table | PR 3, with the walker |
| `milestones/M09b/*.py`, `milestones/M09b/*.json` and `tests/test_m09b_*.py` are on **no** rule | the census clause names `milestones/M09/` and `tests/test_m09_`; neither alternation reaches `M09b` | PR 2 — this is the clause ADR-075 amendment 1 ask 8 added for M09's own readers, failing for its successor one character later |
| `^milestones/.*/topic-baseline\.json$` is an exact filename and M09b takes **two** sweeps | `topic-baseline-pre.json` matches nothing | PR 2, widened to `topic-baseline[^/]*\.json` |
| **`milestones/M09b/withheld-grants.json` is on no rule** — the grant booleans move `F` and `G` both, so they decide M09b's own **F1** | `gate two-key --changed` returns *not required*; the four-seat rule names `^milestones/M08b/` alone | PR 2, on its **own four seats**. Folding it into the census alternation gives three and silently drops **Legal/S&P**, whose key is on that file because an answer-policy reading bills that seat — a widening that looks like coverage and removes a key |

**And a fifth, which is not a rule gap but two checks that cannot both hold.**
`tests/test_documented_commands.py` runs every fenced `bash` block in a
`## Demo artifact` section of `SPEC/*.md` against `main` on every `make check`. A
spec is written **before** the branch is cut, so every file its demo block reads
is one the milestone has not produced yet — measured: `SPEC/09b`'s block, written
as `bash`, takes `make check` red. The block ships as `text` with the reason
beside it, the `bash` form is dated to PR 4 in that spec's Definition of done, and
the structural fix — shape-check an open milestone's block, run a closed one's, on
the `milestone_is_closed` predicate that already exists — is a debt to PM plus
Platform Engineering rather than a change taken in a session that writes no code.

## What this ADR does not decide

- **The wording of either topic.** Decision 2's rule selects both; an ADR that
  drafted them would be the author choosing the answer one document earlier.
- **Whether `brand-021` and `concise-022` are false positives.** They are measured
  by the pre- and post-deploy sweeps and by the at-least-once reading, and they
  are **not diagnosed**: a diagnosis needs held text read case by case and a
  second arm, and M09b budgets neither. `SPEC/09b` carries the trigger.
- **`grounded-017`.** A live regression on `main`, owned by AI Quality, dated to
  09c as a read. M09b re-measures it and moves no tier.
- **Answer quality in any form**, the DMA rename, the `p95_ms` re-derivation — all
  09c's, unchanged.
- **Whether a rule should cover ADRs and specs.** Verified again while writing
  this: `gate two-key --changed` over `SPEC/09b`, ADR-075, `README.md`,
  `SPEC/README.md` and `BUILD.md` returns *"not required — this PR touches no
  two-key path"*. ADR-075 amendment 5 §3's debt stands, owned and unscheduled.
  M09b appends amendments and edits no merged decision text, so its trigger does
  not fire here and the debt is not closed opportunistically.
- **Whether `brand_tone` should have been paid.** That is ADR-026 amendment 5's,
  which records the alternative and refuses it.

## Consequences

**What gets better.** The rule gains a control at the layer a guardrail actually
operates at, and the chain reader gains a walker that reaches an assert through
it — so `pave rules trace MER-AI-0001` gets stronger by the disposition being
strengthened, which is the property the reader's round-2 comment said was worth
having and could not yet deliver. Four paths that decide M09b's own falsifiers
stop being editable on one key. The topic that has refused the product's most
basic question 1 in 3, classified the product's own catalog as circumvention, and
refused 3 of 8 of the judge's calls is recalibrated under a rule nobody can fit to
the outcome.

**What it costs.** `entitlement-circumvention` stops being byte-identical to v3,
so four ADR-035 rows that held by construction must be re-measured. One deploy
means every pre-deploy reading must be taken first and cannot be retaken. Claim 6
stays ❌ until a later milestone re-advances it. And `brand_tone` slides a fifth
time.

**What would falsify the shape of this ADR rather than its claim.** If F5 fires —
a deciding sample naming two topics — then the one-deploy decision was wrong, and
the next milestone that moves two controls at one layer must split them the way
ADR-075 decision 1 split a disposition from a guardrail. That is recorded now so
that it reads as a pre-registered risk rather than as hindsight.

**At scale**, replace the candidate sweep with a held-out classifier evaluation
harness and the character cap with a policy DSL that compiles to the provider's
limits; the corpora are already frozen files with decision rules, and the sweep is
already a function from a wording to a per-row verdict — the interface already
matches.

---

## Amendment 1 (2026-09-11, the same day, before any measurement): the derivation rule is WITHDRAWN, and the reason is that no corpus in this repository is permitted to select

**`SPEC/09b`'s derivation rule and decision 2 above are withdrawn.** Not amended,
not repaired: withdrawn, and re-derived from the owning ADRs in `SPEC/09b`'s
replacement. This amendment is the record of a wrong prediction, which this project
keeps rather than deletes (ADR-012's own practice — *"this index marks superseded
reasoning instead of deleting it"*, and its Amendment correcting its own Decision).

**The milestone stopped before any measurement.** No sweep was taken, no candidate
wording was written, no number was produced under the withdrawn rule. Nothing
downstream rests on it, and nothing here is a threshold moved to clear a reading:
pre-registration constrains what may change *after* measurement, and there has
been none. It will never be this cheap again, which is the only good news in this
record.

**Why it is an amendment here rather than a new ADR.** ADR-067 recorded its own
withdrawn overclaim at the end of itself, *"because this ADR is where the overclaim
was made."* This ADR is where the pre-registration was made. A new ADR would leave
decision 2 standing as accepted pre-registration with its withdrawal one document
away — the *stated and absent* shape CLAUDE.md names as worse than a missing
protection, and the shape ADR-035 and ADR-037 were both written about. The
re-derived rule gets its own ADR beside the new spec; that ADR is not this one.

---

### The headline, and the withdrawn rule's real error

**No corpus in this repository is permitted to select a wording. Not one.** Every
frozen corpus either forbids judging a fix in its owning ADR's own words, or is a
pass/fail gate with no gradient, or is excluded from selection by name.

**The withdrawn rule assumed a permitted selector existed, and the repository had
already decided none would.** That is the error. It is not fixed by scoring a
different corpus, because that moves the same violation one file over.

The consequence for the replacement, inherited rather than rediscovered: **the rule
must ADMIT, not select.** Gates are fail-closed and pass/fail, never a maximised
count; one survivor wins by elimination and no corpus chose it; several survivors
are separated by a rule that reads no corpus; none is the no-winner branch, which
under this design stops being the expensive choice because nothing had to score.

### Two sessions, no contact, three of the same holes

The cold review (PR 1b) read the rule text outward. The rewrite session read the
owning ADRs inward. **They are recorded as pairs, unmerged**: two independent
derivations of one hole is evidence about the method, and collapsing them into one
finding destroys that evidence.

| hole | cold review, from the rule text | rewrite session, from the owning ADR |
|---|---|---|
| the inverted citation | **F-1**: rule 3 selects on `refusal-shapes.yaml`; rule 4 excludes `answer-decomposition.yaml` quoting ADR-067:89, which is `refusal-shapes.yaml`'s own ADR | **defect 1**: and ADR-068 carries the identical prohibition, so **inverting the two does not repair it** — both are barred |
| the goldens leak | **F-2**: `topic_baseline.py --answers` reads `milestones/M01/goldens-run.json` (`:118`, `:160-171`), 22 answers; three exits, none written down | **defect 3 + 4**: the selector *is* the golden set, and F4 names *"any goldens answer file"* — see *no honest exit* below |
| the objective rewards blocking least | **F-5**: no `expect: allowed` restriction; the four must-block compliance rows in neither the admissibility set nor F2 | **defect 5**: measured 6 `allowed` / 4 `blocked`, and ADR-067 decision 2 pre-registered it — *"a topic that blocks nothing fails the compliance halves"* |

### Every finding, dispositioned

**TAKEN — the replacement is built on these.**

| finding | source | disposition |
|---|---|---|
| the rule selects on a corpus whose ADR forbids judging a fix | F-1 / defect 1 | the rule is rewritten to admit, not select. No clause reused without re-derivation from the owning ADR at line |
| rule 1 executes token-provenance, not ADR-024's prohibited-source list | F-3 | taken. The list never reached `phrasings.yaml` — `gateway-stack.ts:293-297` records the extension as **owed to Security**, and records a draft that reached for `PHR-002`'s noun `VPN` and was caught |
| the objective rewards blocking least | F-5 / defect 5 | no gradient survives. Admissibility is pass/fail in **both** directions, and `phrasings.yaml`'s two `expect: allowed` rows enter it |
| `phrasings.yaml` omitted entirely | defect 6 | zero occurrences by filename in the withdrawn spec; only `PHR-002`/`PHR-003`, both `expect: blocked`. `PHR-004` and `PHR-005` enter the replacement |
| the candidate set has no number, no diversity requirement, no generation procedure | F-4 (part) | all three stated in the replacement. *"Fixed in number"* with no number is not a rule |
| how multiple selection signals combine is nowhere specified | F-6 | moot under admit-not-select, and recorded as moot rather than silently dropped |
| the no-winner branch is never walked | review §7 | it gets a test, a plant, and a Definition of done that does not make choosing a winner the cheap option |
| F1 is a one-key control over the claim's outcome | this record | two independent readings, below |
| F5 can be vacuously clean | review / this record | a denominator, below |
| two debt registers with nothing asserting they agree | this record | below |

**PUBLISHED AS NOT CLOSABLE — carried as named limits of the claim, not solved.**

**F-4: an ordering check constrains commitment and never authorship.**
`tests/test_m09b_ordering.py` reads `git log` and is red if a candidate's commit
precedes the corpus that judges it. That is a real check and it is not the one
anyone needs: it proves *when bytes were committed*, and the hazard is *what the
author had read*. An author who has read every committed corpus can write a fitted
candidate and commit it in any order. No test can close this, because the evidence
does not exist in the repository. It is closed structurally or not at all —
separation of candidate authorship from the judging corpus — and where that
separation cannot be had, it is published.

**Defects 3 and 4 together: a rule with no honest exit is not a rule.** Rule 3
selects on `topic_baseline.py --answers`. F4 fires if the selection record's
`inputs_sha256` names *"any goldens answer file"*. Running rule 3 and recording its
inputs honestly **fires F4 at PR 3**. Omitting the file from `inputs_sha256` is
**concealment**. There is no third option, and decision 2 above is titled *"the rule
cannot read the golden set"* while pointing at the rule that does. Published
together because either alone reads as a fixable slip and the pair is the finding.

**Defect 7 — a structural constraint, not a scoping preference. No answer corpus
may enter selection or admissibility.** `milestones/M01/goldens-run.json` carries 25
records; `answers()` skips any whose answer is `refused_by_gateway`; the three
skipped are `blackout-001`, `blackout-006`, `blackout-009`; 22 are emitted.
**`blackout-009` is F1's own canonical case and the arm cannot see it.** This is not
a leak to be closed by dropping the file from a digest — it is permanent, and it
was measured twice before this milestone:

> ADR-035 amendment 7: *"The three missing are `blackout-001`, `-006` and `-009` —
> exactly the three blackout cases… **The diagnostic coverage is anti-correlated
> with risk**: the cases it cannot test are the cases worth testing, because the
> reason it cannot test them is that they were already refused."*
>
> ADR-035 amendment 8: *"A blocked answer is never committed. An OUTPUT-channel arm
> built from committed answers is by construction an arm over the answers that were
> ALLOWED… **it must not be recorded as closing this.**"*

A refusal leaves no answer to score, and refused cases are exactly what M09b
targets. Any selector over committed answers is blind to its own target by
construction.

**The published asymmetry: nothing committed measures whether the loosening goes
too far.** `topic-attacks.yaml:15` records the mirror of this about ADR-035 —
*"**Nothing in the ADR measures whether it bit too hard**"* — for a tightening. M09b
loosens, and the same gap is open in the same place: the unexposed evidence
(`PHR-004`, the clean catalog, both `expect: allowed`) tests the tightening
direction only. `topic-attacks.yaml` is all-`expect: blocked` and burned for
selection; `topic-attacks-heldout.yaml` is blocked-and-measured-vacuous.
**Minting a corpus mid-milestone to close this is REFUSED**: a corpus written after
the gap is known is chosen after seeing a result, which is the same defect as every
other finding in this set. The asymmetry is a named limit of the claim and stays
open.

**DECLINED, with the reason.**

| finding | why declined |
|---|---|
| freeze a third-generation held-out corpus | `topic-attacks-heldout.yaml`'s ordering property is **intact** — measured below — so the retirement argument does not transfer. The general rule is separation of candidate authorship from the judging corpus; minting a corpus per wording change puts the project on a treadmill and buys nothing the separation does not |
| `probes.yaml` as an admissibility gate | declined **on the confound, not on the missing freeze**: `phrasings.yaml:28-30` — *"ADV-006 and ADV-009 both fire `PROMPT_ATTACK` independently of any topic, so neither can isolate whether `entitlement-circumvention` is doing anything."* The reason must stay attached, because a later reader who thinks it was excluded for a missing freeze will re-admit it once a freeze is declared |

### Was `topic-attacks-heldout.yaml` revised-against, or only read? Only read.

Measured across every commit that has ever touched `gateway-stack.ts`:

```
entitlement-circumvention   len=191  sha256[:12]=ad554785a3de   IDENTICAL at all 7
                            unchanged since d625033 (Change A, 2026-08-21)
enforcement-probing         len=170  sha256[:12]=06351db356     IDENTICAL at all 5
                            unchanged since it first appeared at 3f81fe6
```

`heldout`'s `judges:` field names *"the topic proposed to close ATK-007 (ADR-035
amendment 4)"* — that is `enforcement-probing`. Neither wording has moved since the
corpus froze, and the rows were never edited: `850728e` is **+25 lines, 0 row
changes**, a header recording the vacuous result with *"The rows are NOT rewritten.
A frozen corpus that gets edited when it disappoints is not frozen."*

**The file's ordering property is intact. The exposure is on the author side only** —
a fact about whoever has read it while authoring candidates, not about the file.

### F1 is a one-key control over the claim's outcome

`milestones/M08b/withheld-grants.json` declares its own nature: *"one reading per
sample refused on the answer channel by the entitlement topic — grant or not…
**No held text is here or may be.**"* `SPEC/09b:362` states the dependency: *"The
grant booleans move `F` and `G` both, so they decide this milestone's own F1."*

So the primary falsifier of the claim rests on **one person's booleans over text
that is not committed and may not be**, in a repository whose premise is that
consequential decisions collect two keys (G9). The file is right to forbid
committing held text; the fix is not to break that.

**Required on PR 2: two independent readings of the withheld output, committed
separately, with the disagreement published as the reading.** Seats: **Legal/S&P**,
whose key sits on that path already because an answer-policy reading bills that
seat, and **Security**, which owns what the guardrail blocked. This makes F1
*checkable*. **It does not make F1 outsider-verifiable, and this record says so
plainly** — no reader outside the operator pair can ever verify `F` or `G`, because
the evidence was withheld by the control being measured. That is the most the
physics allows.

### F5 needs a denominator, not a rewrite

F5 fires when a refused sample deciding F1 or F3 names more than one `TOPIC:`. With
no deciding samples it is satisfied by having nothing to check. **F5 must publish
how many deciding samples existed; zero is reported as "F5 not exercised" and never
as "F5 clean."** ADR-035 amendment 5 already named this object, in this repository,
about this corpus: *"Rows 23 and 24 were confirmed by a corpus that would have
confirmed them had the change never been made. That is a vacuous confirmation — a
distinct failure from a falsified row, and a quieter one, because it reads as
evidence."*

### What the claim can and cannot be falsified on

| falsifier | fully readable from committed evidence **and** sound | why |
|---|---|---|
| **F2** | **yes** | the two sweep records joined by `topic_delta.py`, over frozen corpora. **This is the loosening-too-far direction — the risk M09b actually carries** |
| **F3** | **yes** | the two sidecars' `cases_at_least_once` / `cases_by_majority` |
| F1 **as written** | no | `F`/`G` are computed from the operator's grant booleans over uncommitted text. Clause 3 (`blackout-009` refused by majority) is readable; clauses 1–2 are not |
| F4 | no | clause 2 cannot discriminate (no honest exit); clause 3 is `git log`, environment state, not committed evidence. Clause 1 survives |
| F5 | conditionally | readable, but vacuous without a denominator |

**Two of five as written — but the benefit direction is not what made F1
unreadable, and the replacement is not confined to F2 and F3.** Two questions were
conflated here, and separating them is the most consequential correction in this
record:

- **(a) did a case stop being refused, and was `TOPIC:entitlement-circumvention`
  among the topics that refused it?** — **readable from committed records, no
  withheld text.** `milestones/M09/goldens-run-refusals.json` carries, per case per
  sample, `decision`, `mechanism`, `assessed` (the literal topic names), `channels`,
  the `guardrail` id and version, and `record_id` with `record_resolved: true`,
  *"taken from the audit records fetched back out of the lake"*. Its `census` block
  publishes **both** estimators (`refused_at_least_once`, `refused_by_majority`,
  `cases_separating_the_estimators`). The sidecar is written automatically by
  `run_with_tools.py:658` for any run, so PR 4's post-deploy run yields the same
  structure with no new instrument.
- **(b) was the answer the guardrail withheld actually a grant?** — **genuinely
  operator-attested**, and the only thing that is. This is the grants file, and `F`
  and `G` are the quantities that read it.

The two target cases are identifiable by id **today**, from committed records, with
no withheld text read: **`brand-021` (s2)** and **`concise-022` (s3)**, both
`assessed: ["TOPIC:entitlement-circumvention"]` on `channels: ["answer"]`,
`record_resolved: true`. `blackout-009` is refused 3 of 3 — s1 and s2 on
`entitlement-circumvention`, s3 on `enforcement-probing`, which is the
majority-masking movement F1's third clause was written for.

**So the benefit claim is soundly pre-registrable and symmetric with F3**: cases
refused by majority with `TOPIC:entitlement-circumvention` among the assessed names,
before versus after, on the same sidecar structure, with an at-least-once companion
beside it and the disagreement published as the reading. Nothing in that direction
requires a grant boolean — only refused-versus-answered plus topic attribution.

**What deliverable 3 inherits: the claim covers the additive control AND the wording
fix's benefit AND its risk. Only the grant attribution is published as attested**,
and F1's *grant-shaped* clauses are the only part that ships as
checkable-not-verifiable, with the two independent readings above.

**This record originally scoped the claim smaller — to the additive control alone —
and that was wrong.** The cause: *"the text was withheld by the control being
measured"* is true of (b) and was allowed to contaminate (a). The two questions read
the same file and one of them never touches the withheld half. A verdict that
narrows a milestone on a conflation is worse than one that widens it on a
measurement, because nobody re-audits a scope cut.

### NEW FINDING — the project has two debt registers and nothing asserts they agree

A milestone's debts exist in two authoritative-looking places that **differ by
seventeen rows**:

| register | built how | rows for M09 |
|---|---|---|
| `milestones/M09/README.md:518` — *Debts carried out* | at the close, from the milestone's own findings | **36** |
| `SPEC/09`'s *Obligations inherited* | by hand, from the previous close | **19** |

A carry-in table is transcribed by hand and only a later re-audit catches a miss —
which is how four dropped debts were found here rather than at the close.
**This is ADR-037's shape exactly**: two lists that must agree, neither checking the
other, the drift found by a person. ADR-037's answer was a contract test
(`tests/test_contracts.py:702`), and the same answer applies.

**The test it implies, and it is OWED, not closable inside M09b.** Exact matching
needs a stable identifier per debt; none exists, and minting them retroactively
would edit four closed journals including M09's. The weaker one-directional form —
comparing row counts — would be satisfied by a catch-all row, which is precisely
what hid these four, so it would be a check that cannot fire and this repository
does not land those. **Owner: Platform Engineering + PM. Trigger: the next PR that
edits `close-milestone`'s step that writes the carry-out table.**

### The four debts dropped, recovered with owners and triggers intact

| # | debt | owner | trigger |
|---|---|---|---|
| 19 | the fix moved a **fifth** site, `templates/agent-tools/evals/answer.schema.json.tmpl`; the count of sites has been wrong three times | Platform Engineering | the next PR that changes the fix's site count |
| 28 | `milestones/M08/context_census.py`'s `sys.path.insert` leaking a tool path into the session | Platform Engineering | the next PR that edits that file for a reason of its own |
| 33 | **Only *Demo artifact* blocks are checked.** `DEMO_HEADING = "## Demo artifact"` at `tests/test_documented_commands.py:62`; blocks outside such a section are unchecked | PM + Platform Engineering | the next PR that edits a command block in `SPEC/` or `README.md` — **this trigger fires at PR 1** |
| 34 | CLAUDE.md says *one milestone = one branch `mNN-<slug>`*; five milestones have used one branch per PR | Platform Engineering (the lead's seat) | the next PR that edits CLAUDE.md's *Milestone discipline* section |

**None of these is closed by being listed here.**

### Both count readings, with the definition each used

The cold review and the rewrite session disagreed on how many obligations degraded.
They were answering different questions, and **where they disagree the disagreement
is the reading** — M09's own inherited rule, applied to M09b's audit of itself.

- **Reading R — degraded = carried in a way that produces an inconsistent
  disposition against a same-trigger sibling. → 1.** Debt 7 (*the disclosure lane
  is wired into no CI workflow*, trigger *the first PR that runs the pack again*)
  sits inside the catch-all at `SPEC/09b:433` marked `unchanged`, while debt 24
  (*the disclosure comparator pin*, trigger *the first PR that takes a second
  disclosure run*) gets its own row honoured at PR 4. **Same triggering event, two
  dispositions.**
- **Reading M — degraded = present but stripped of the individual owner and trigger
  its source gave it. → 13.** `SPEC/09b:433` collapses **twelve** debts (1, 2, 3, 4,
  5, 7, 8, 9, 10, 13, 14, 15) into one row with owner *"as M09 recorded them"* and
  trigger *"unchanged"*. Debt 27 (`tool_request` probes + the `enforcement-probing`
  trigger — dated **M09b**, owner Security) is dispersed into `:210` as a
  side-prediction and `:407` in out-of-scope, and is in neither table.

R asks *did a degradation change a disposition?* M asks *did the table keep the
promise its own header makes* — *"each with an owner and a date"*? Neither subsumes
the other. A reader needs R to know where to look for a consequence and M to know
where to look for a missing owner.

### The four corpora that declare no freeze — one debt

`probes.yaml`, `probe-controls.yaml`, `tool-plane-probes.yaml` and
`g4-semantics.yaml` carry **no `frozen_at` and no `frozen_before`**. Every other
corpus in `quality/adversarial/` declares both, and the declaration is the whole
value: a *declared* claim about what a corpus predates can be checked against the
history, and a date inferred from `git log` is worth nothing, because the question
is what the author had read, not when bytes landed. **No freeze date is inferred for
these four anywhere in this milestone.**

**Owner: Security / Red Team** (the owning seat of `quality/adversarial/`).
**Trigger: the next PR that adds a row to any of the four.**

### The process finding: the cold-review slot nearly lost its catch

The cold review ran, found six things, and wrote them to a scratchpad path no later
session could read. The rewrite session **independently re-derived three of the six**
(the inverted citation, the goldens leak, the objective rewarding blocking least)
and did not see the other three until they were pasted in by hand.

The spare has caught something material in every milestone of this project. **This
is the first time the catch nearly did not land**, and it nearly did not land for a
reason that has nothing to do with the review's quality: its output had no committed
home. M09's cold read was a committed artifact (`479972e`, PR #135). M09b's was not.

**The slot's output is part of the milestone's evidence and must be committed like
any other.** Recorded here as a process finding beside the findings themselves,
because a review whose output evaporates is indistinguishable from a review that was
never run.

### Two corrections to this session's own audit, with their causes

| claim | corrected to | cause |
|---|---|---|
| two obligations dropped | **four** | audited against `SPEC/09`'s carry-in table (19 rows) instead of `milestones/M09/README.md:518`'s carry-out list (36). Wrong population |
| four of five falsifiers readable | **two as written** | missed that `F` and `G` are computed from an operator-written file over uncommitted text, so F1's clauses 1–2 are unverifiable by anyone |
| the wording fix's benefit can only ever be operator-attested, so the claim shrinks to the additive control | **the benefit is soundly pre-registrable; only grant attribution is attested** | conflated *"did this case stop being refused, by this topic"* (committed, `goldens-run-refusals.json`) with *"was the withheld answer a grant"* (attested). One file, two questions, and only the second touches withheld text |

A third was a false positive: debt 33 was reported carried on a grep hit for *"Demo
artifact"*, which in `SPEC/09b` is the section heading at `:522`, not the debt.

**Both were caught by their author before shipping, which no previous wrong prose
claim in this project was** (~70 wrong citations across `SPEC/`06 reached the record;
ADR-038's false pass was closed while live). That is a datum about the method, not a
credit. What produced it was re-auditing against committed files at line rather than
against a list — the same practice that produced every finding above, applied to the
audit's own output.

---

### Where the replacement is, and one correction to this amendment

**The re-derived rule is ADR-077**, *a corpus may eliminate a wording, and none may
choose one*, written beside the replacement `SPEC/09b` at M09b PR 1d. This amendment
promised the rule *"its own ADR beside the new spec"* and could not name it; this line
names it, and adds no decision. Both documents cross-reference this amendment, and the
replacement spec carries the withdrawal as its opening `Supersedes` line so the pointer
survives the file being replaced.

**Every `SPEC/09b:NNN` line reference in this amendment points at the WITHDRAWN file**
— `:210`, `:362`, `:407`, `:433`, `:522` — and that file is 686 lines at `a225624` and
is not the file on that path now. The references are not re-pointed, because
re-pointing them would silently move the evidence a finding was measured against; they
are read against `git show a225624:SPEC/09b-the-guardrail-line-and-the-topic.md`. Said
here rather than left for a reader to discover by landing on the wrong paragraph.

**One claim in *The four corpora that declare no freeze* is wrong, and it is corrected
where the declaration lands rather than by editing that section:** it reads *"Every
other corpus in `quality/adversarial/` declares both"* — `phrasings.yaml` declared
`frozen_at` and `frozen_because` and **no `frozen_before`**, so it was a fifth instance
rather than a file the sentence could stand on. Measured: `frozen_before` appears in
`answer-decomposition.yaml`, `refusal-shapes.yaml`, `topic-attacks.yaml`,
`topic-attacks-heldout.yaml` and `topic-attacks-output.yaml`, and in no sixth file. The
declaration is added at PR 1d with the measurement behind it, in ADR-077's appendix,
because ADR-077 makes this milestone start relying on the file as a gate. The four named
here are unaffected and stay owed to Security / Red Team on their own trigger.

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

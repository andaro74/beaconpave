# SPEC/03 — The judge, its calibration, and what a published agreement number costs

**Owning seat:** PM (spec) · AI Quality (judge, rubric, calibration corpus,
thresholds, every recorded score — two-key) · Platform Engineering (the gateway
path the judge calls through) · Security + Data Governance (the guardrail
refusal finding this milestone measures and does not fix)
**Milestone:** M03 · branch `m03-evals` · tag `m03`

## Why this milestone exists

Three things are asserted and enforced nowhere.

- **Claim 9 has no artifact.** "Judges are calibrated or advisory" is a row in
  the README's twelve-claims table and a paragraph in
  `quality/judge/rubric-sports.md`. There is no judge, no calibration corpus, no
  agreement number, and nothing that demotes anything.
- **The rubric is referenced by every golden case and read by nothing.** All 25
  cases carry a `judge:` block naming `quality/judge/rubric-sports.md` and a list
  of axes. `evals/run_evals.py` names the file in a constant and comments that
  leaving it unread is the decision rather than an omission (ADR-012). M03 is
  where that stops being true.
- **`ADVISORY` blocks in `emit_verdict`, and nothing has ever produced one.**
  Both the tie rule and the blocking behaviour were written during M02 while
  nothing was riding on them, precisely so that M03 would meet them already
  written. M03 is the first milestone where they are reachable, and the first
  where they can be found wrong.

M03 fixes exactly those three and nothing else.

## What M03 builds

1. **`quality/judge/calibration/`** — 30 items, a committed deterministic
   selection rule, and hand labels written before any judge prompt exists in the
   tree. Two-key, AI Quality.
2. **`evals/judge.py`** — the hermetic half. A pure function of (rubric, case,
   committed judge output) producing per-axis bands and a case-level veto. It
   imports no SDK, calls no model, and stays inside `HERMETIC_ROOTS`.
3. **`services/highlights-agent/run_judge.py`** — the model-calling half, which
   calls **through the gateway** and writes `judge-run.json`. It lives beside the
   agent runners for the same reason they do, and it is not in `make check`.
4. **Agreement, published per axis, and automatic demotion per axis**, with the
   demotion threshold and the insufficient-evidence rule fixed in this document,
   before the corpus is labelled.
5. **`instrument` in `evals/history/schema.json`** — the field that says which
   instrument produced a row. Two-key, AI Quality.
6. **`guardrail_refusals` in the same schema**, derived hermetically from
   committed answers, with SPEC/01's pre-registered band asserted at suite level
   and reporting only.
7. **The judged anchor**: the committed `m00b` answers re-scored with the judge at
   `k_judge = 3` and appended as a history entry carrying `instrument` and **no**
   `supersedes`.

## What M03 deliberately does NOT build

- **No new agent run.** M03 moves the instrument under a fixed system, which is
  the exact mirror of M02 (ADR-021) and the fourth arrival of ADR-016's hazard.
  Every answer M03 scores is already committed. Running the agent again would put
  two moving parts in one comparison for no gain.
- **No golden-case edits**, in either direction, for any reason.
- **No guardrail retune.** See "The refusal finding" below.
- **No probes.** The adversarial suite is M04's, and the turn record still cannot
  evidence a mid-loop Cedar denial — which M02 recorded as **must close before any
  probe runs with tools**.
- **No `disclosure_present` scoring.** It activates at M07, and it is deferred
  here exactly as `entitlement_source` and `expect_tool_before_answer` are.
- **No judged re-score of `m01`.** Recorded as a cut below.

## The load-bearing decision: what "calibrated" is allowed to buy

A judge that can never move a verdict makes claim 9 vacuous. Demotion from what,
to what? "Calibrated or advisory" is a distinction with no difference unless
being calibrated has a consequence.

So, decided before anything runs:

- **Calibrated ⇒ the gate reads the judged verdict.**
- **Demoted ⇒ the gate reads the deterministic verdict**, and the judge's axes
  are recorded and consulted by nothing.
- **Every entry from M03 onward carries both numbers.** `passed` stays the
  deterministic count and remains directly comparable back to `m00b`;
  `passed_judged` is the new column. The progression table **gains a column
  rather than replacing one**.

That last point is ADR-016's lesson applied *prospectively* for the first time.
Three milestones have footnoted a moved instrument after the fact. This one
arranges that the number a reader compares across rows never moves.

### The judge can only subtract

The judged verdict is the deterministic verdict **and** no required axis scoring
`0.0`. The judge is a veto on cases that already passed; it can never rescue a
case the deterministic asserts failed.

Three reasons, and the first is the repo's own style rule.

- CLAUDE.md: where a requirement can be written as a deterministic assert, it
  must be. A judge that can grant a pass is a judge competing with the asserts.
- The rubric already says the judge "never carries the blocking weight alone" and
  that groundedness "scores only what survives" the deterministic pre-check.
- It gives the composition one direction, so a judged delta is always attributable
  to the veto and never to a rescue cancelling a veto somewhere else.

The `0.5` band is **not** a veto. Read the rubric: `0.5` is "accurate but flat",
"reaches beyond what is cited", "padded but readable". Those are quality signals,
not failures. `0.0` is "contradicted by, or absent from, the catalog", "answers a
different question", "cruel, profane, hyperbolic". Only `0.0` vetoes.

## The judge is an instrument, and the first one that can move without a commit

Every hazard in ADR-016 and ADR-018 applies to it directly, and one is new: the
guardrail is configuration a console can edit, but the judge is a *model*, and its
output can differ between two invocations of identical bytes. Nothing else on the
scoring side of this repo has that property.

Pinned before it scores anything:

| What | How |
|---|---|
| model | `us.anthropic.claude-haiku-4-5-20251001-v1:0`, the one pinned profile (ADR-015) |
| decoding | temperature 0, `top_p` fixed, `maxTokens` fixed, all committed |
| judge prompt | hash-pinned, the `TOOL_SYSTEM_SHA256` pattern from ADR-021 |
| rubric | hash-pinned — it is **model-facing text** the moment the judge reads it, which is M02's "the prompt was not the whole prompt" arriving somewhere new |
| guardrail | the same pinned published version the answers were produced under |
| sampling | `k_judge = 3`, never 1 |
| raw output | **committed**, so every downstream number is a pure function and `test_instrument_stability.py` can pin judged scores hermetically |

That last row is what keeps the repo's strongest property intact. The model call
is the part nobody can regenerate; commit it, and everything after it is
re-derivable by a stranger with no AWS account.

**Temperature 0 is a pin, not a determinism claim.** It narrows the distribution;
it does not collapse it. `k_judge = 3` exists because the argument that
disqualified a single agent sample disqualifies a single judge sample, and this
milestone would otherwise repeat M02's own headline error one layer up.

## Three summarisation layers, in order

The judge adds a layer to a stack that already had two, and M02's finding about
`3p² − 2p³` was that a summariser is an estimator. Three of them compose, and the
order is decided here rather than discovered in the output:

1. **innermost — judge majority.** For each (answer-sample, case, axis): the
   majority band across `k_judge = 3`. Three bands, so **a 1-1-1 split is genuinely
   reachable here** — this is the layer where M02's tie rule finally meets
   something that can produce one.
2. **middle — the veto.** For each (answer-sample, case): deterministic verdict
   AND no axis at `0.0`. Deterministic, given layer 1.
3. **outermost — answer majority.** For each case: the majority across
   `k_answers`, unchanged from M02, using the existing `summarise`.

`3p² − 2p³` applies at layers 1 and 3 and **compounds**. So the pooled figure is
recorded at both layers, not only the outermost, and the journal reports the
judged delta both ways. If majority and pooled agree the finding is robust; if
they diverge, the divergence is the finding. Which one is the headline is named
before the run — it is named here: **majority**, with pooled beside it, exactly as
at M02.

### The tie rule, and where it actually bites

M02 wrote the rule and predicted it was unreachable. Both halves survive contact,
in different places:

- **At case level it is still unreachable, and M03 does not manufacture a path to
  it.** With `k_answers = 3` over PASS/FAIL a strict majority always exists, and
  INFRA triggers a full re-run rather than entering the pool. M03 records that it
  remains unreachable rather than inventing a third case-level verdict to make the
  rule look exercised.
- **At axis level it is reachable, and that is where the rule earns its place.** A
  judge returning `0.0`, `0.5`, `1.0` across three samples of one axis has no
  majority. That axis is **undecided**: recorded, counted, and **not a veto** — a
  veto requires a decision and there was none. The undecided count is published,
  because a judge producing many of them is a judge that is not measuring
  anything, and **the undecided fraction is itself a demotion trigger** (below).

### The collision M03 has to avoid, named before it is written

`ADVISORY` currently carries two unrelated meanings: `CaseResult.advisory_axes`
("judge axes recorded, not scored") and `summarise`'s tie token ("no strict
majority"), which `emit_verdict` makes **block**.

The naive implementation of demotion — a demoted judge emits `ADVISORY` axes, the
case result becomes `ADVISORY`, the verdict blocks — inverts the rubric's own
promise that a demoted judge "cannot block a merge". It would make demotion
strictly worse than calibration, which is the opposite of the mechanism.

**So demotion is implemented as "the axis does not enter `result`", never as "the
axis enters `result` as ADVISORY".** `ADVISORY`-as-tie keeps its blocking
semantics untouched, and no history-schema enum changes. A test pins it.

## The calibration corpus is a corpus (ADR-009's shape)

**30 items, frozen before labelling, split 10 dev / 20 held-out before a single
label is written.**

An item is a **(run, case-id, axis)** triple drawn from *already committed answer
files* — `milestones/M00b/goldens-run.json`, `milestones/M01/goldens-run.json`,
and M02's six run files. Roughly 480 candidates exist. Thirty are selected by a
**committed, deterministic rule**, stratified by axis in proportion to the golden
set's own axis frequency and spread across runs:

| axis | golden-set instances | calibration items | held-out |
|---|---|---|---|
| `groundedness` | 23 | 11 | 7 |
| `completeness` | 16 | 8 | 6 |
| `brand_tone:meridian-sports` | 14 | 7 | 4 |
| `concision` | 7 | 4 | 3 |

Drawn from recorded answers rather than authored, because authored answers sit
where their author put them: an agreement number measured on hand-written band
anchors overstates what the judge does on real output. Real answers bring the
awkward cases with them — refusals with no prose, passes with an empty citation
list, the control's confabulations.

**The freeze rule.** Size is pinned by a contract test. The split is pinned by a
contract test. The selection rule is committed and deterministic, so "we picked
30" is checkable rather than asserted. The corpus may **grow** with a milestone
that earns it, in the same diff that updates the test. **Shrinking is the
direction that matters**: a calibration set that loses the items the judge finds
hard reports a better agreement from a worse judge, silently. Two-key, AI Quality,
the same as the golden set.

**The honest limitation, stated before the number rather than after it.** Twenty
held-out items over three bands is a small sample, and a per-axis figure over
three to seven items is smaller still. Every published agreement number carries
its item count beside it, and the journal never reports a per-axis figure without
one.

### Hand labels: by whom, and when relative to the judge's prompt

An agreement number computed on the set the judge was tuned against measures
nothing. The protection is ordering, and the ordering is visible in git:

- **Commit 1:** this spec.
- **Commit 2:** the selection rule, the 30 selected items, and the dev/held-out
  split — with **no labels**.
- **Commit 3:** the labels — ~~written by the operator wearing the AI Quality
  seat~~ **drafted by the assistant and disposed by the operator wearing the AI
  Quality seat** (amended in place below) — against the rubric alone. At this
  point **no judge prompt exists in the tree**.
- **Commit 4 and after:** the judge prompt, iterated **only against the 10 dev
  items**, never against the 20 held-out.

The DoD records those SHAs. No test can prove label independence — but the repo's
premise is that its history is legible, and this is a case where the history is
the evidence. Relabelling to recover agreement is prohibited by the rubric and
would be visible as a commit touching labels after a judge run.

### Amendment (2026-08-19, before the corpus was selected): the labels are drafted, and what that costs

**The operator asked for the labels to be drafted rather than written from
scratch.** That is a legitimate request and it is how the rest of this repo
works — but it changes what the published agreement number is, so it is recorded
here, before selection, rather than discovered in the journal.

**What it costs, stated plainly.** An agreement number between a judge and labels
drafted by another model is not the number this spec originally promised. The
drafter (Claude Opus 5) and the judge (Claude Haiku 4.5) are both Anthropic
models. Shared priors are the *expected* failure mode, not a remote one, and they
inflate agreement in a way **κ cannot detect** — κ corrects for chance agreement,
not for correlated error. Two instruments that are wrong in the same direction
agree perfectly and κ rewards them for it.

**What makes it legitimate anyway: G6, which this repo already runs on.** AI
proposes, a human seat disposes, and the curation rate is published. That is the
same mechanism as the role subagents in `.claude/agents/`, whose output ROLES.md
calls advisory input to a human and never an approval. So:

- every label carries `provenance: {author: ai-proposed, curated_by: ai-quality}`
- every label carries both `drafted` and `final`
- **the correction rate is published beside every agreement figure**, in the same
  sentence, not as a footnote: *"agreement N against ai-proposed labels disposed
  by the AI Quality seat, correction rate M%"*

**The correction rate is the whole protection, and it is a weak one.** A rate near
zero means either the drafts were right or the disposition was a rubber stamp, and
**the number cannot tell you which**. It is therefore reported as a limitation of
the measurement, never as a validation of it.

**Two hard rules.**

- **The operator disposes before the judge runs.** A label changed after seeing a
  judge output is relabelling, which the rubric prohibits outright, and it would
  be visible in git as a commit touching labels after a judge run.
- **A drafted label is not a label until it is disposed.** If the operator does
  not review all 30, M03 publishes agreement against the subset that was disposed
  and says so, rather than counting undisposed drafts as labels.

**Pre-registered, since this is now part of the instrument:**

| Dimension | Prediction | What falsifies it |
|---|---|---|
| Correction rate | **15–35%** (5–11 of 30 labels changed on disposition) | **0 corrections** — the disposition did not happen independently, and the agreement number is model-agrees-with-model; or **> 50%** — the drafts were not usable and the labels should have been written from scratch |
| Where corrections land | concentrated in `brand_tone` and `completeness` — the two axes whose bands turn on judgement rather than on a checkable fact | corrections concentrated in `groundedness`, which is checkable against the catalog and where a drafted label being wrong means the drafter could not do the easy axis |

**At scale, replace with:** labels from two independent human annotators with
inter-annotator agreement published before the judge is measured against either.
The interface already matches — `provenance` and the correction rate are the
one-annotator version of it, and only the annotator count changes.

## Thresholds, fixed here, before any run

Two numbers and one rule. Deriving any of them after seeing an agreement number is
the failure this section exists to prevent.

- **Demotion threshold: exact-band agreement below `0.75` demotes that axis.** Per
  axis, on that axis's held-out items only.
- **Insufficient evidence demotes by default: fewer than 5 held-out items for an
  axis and that axis is demoted regardless of its agreement.** Not enough evidence
  is not calibration. On the strata above this starts `concision` (3) and
  `brand_tone` (4) demoted, which means the demotion mechanism is exercised on day
  one without the judge having to be bad at anything.
- **Undecided fraction: above `0.20` of an axis's judged items with no majority at
  `k_judge = 3` demotes that axis**, whatever its agreement on the ones it did
  decide. A judge that cannot repeat itself is not calibrated by the subset of
  answers where it happened to.

**Agreement is published per axis, and demotion is per axis.** A judge good at
concision and bad at groundedness averaged into one number hides the axis that
matters. An overall figure is recorded because `judge_agreement` in the history
schema is a single number and history is append-only; the per-axis breakdown lives
in `instrument`.

**Two statistics, headline named in advance.** Raw exact-band agreement **and**
Cohen's κ, both computed, both recorded, with the label distribution published
beside them — raw agreement on an imbalanced label set is inflated, and
`brand_tone`'s `0.0` band ("cruel, profane, hyperbolic") should almost never
occur. **The demotion trigger is defined on raw exact-band agreement**; κ is
recorded as the check on it. Same discipline as majority-versus-pooled, decided
now rather than after seeing which way it cut.

## `supersedes` is the wrong verb for the m00b anchor

ADR-012 committed M03 to re-score the control at the `m00b` commit and append an
entry with `supersedes` pointing at the deterministic-only one. Checked against
what the repo now holds, that is **half right**, and the wrong half is the verb.

- **The entry is warranted.** SPEC/01 struck an identically-shaped item on the
  grounds that 18/25 is derivable from committed answers, so it needed no row.
  That argument does not transfer: a judged number is a model output nobody can
  regenerate, which is exactly what `evals/history/` exists for.
- **`supersedes` still means "corrects a wrong entry", and 15/25 is not wrong.**
  `tests/test_instrument_stability.py` asserts the m00b entry carries no
  `supersedes` and says why. The instrument moved under a correct measurement, and
  marking it corrected misleads every reader later working out which number was
  real.
- **`k` and `arm` do not close the gap.** `arm` is *which system* produced the
  entry. `m00b`-judged and `m00b`-deterministic are the same system, the same
  answers, the same bytes, under different instruments.

**So M03 adds `instrument`**, and the anchor is appended under the `m00b` sha with
a new `instrument`, no `supersedes`, and `k_judge = 3` — because a judged anchor at
k = 1 reproduces at the instrument level the exact n = 1 error ADR-021
disqualified M01's 19/25 for.

ADR-012 is **amended in place**, in the style it already carries one amendment.
The split it recorded — deterministic at M00b, judge at M03 — is untouched and
stands as written. Only the verb changes.

### The cut: `m01` gets no judged re-score

M01's answers are committed and judging them would cost 75 calls. It is still cut,
for a reason rather than for the budget: ADR-021 disqualified 19/25 as a
comparator because it is n = 1, and a judged score over that same single sample is
disqualified by the same argument. Producing it would put a number in the table
that the repo has already explained nobody may compare against.

The judged column therefore has two rows at M03: the **anchor** (`m00b`) and the
**tip** (both M02 arms). The gap at `m01` is the reservation, and this paragraph
is what it points at.

## The refusal finding: not unowned — owed, and growing

The standing brief carried this as "the largest open finding, owned by nobody."
**That is wrong, and the correction matters more than the finding.** It is M01's
second owed tightening — *"Separate 'does this rule apply to me' from 'help me
evade it'"*, seat **Security + Data Governance** — recorded in
`milestones/M01/README.md` at the tag, still owed, and quietly growing since.

Measured across every committed run (below), it went **0 → 3 → 5, 6, 8**. It has
breached SPEC/01's pre-registered `≥3 is a miscalibrated guardrail` in **every
governed run ever recorded**, starting with M01 — one milestone earlier than M02's
journal reads it.

**M03 does not fix it.** The fix is a topic-definition change in
`platform/infra/lib/gateway-stack.ts`, which is the Security seat's, and retuning
the guardrail inside the milestone that re-measures every recorded answer would
move the instrument mid-measurement.

**M03 makes it stop being prose.**

- `guardrail_refusals` becomes a **recorded field** on the history entry, derived
  hermetically from the `refused_by_gateway` markers already present in every
  committed answer file. No model call, no AWS account.
- SPEC/01's `0–2 expected, ≥3 miscalibrated` band becomes a **suite-level assert
  that reports and does not block** — two-key, AI Quality **and** Security, since
  it is Security's control.
- The M01 tightening is **re-raised by name**, with the growth attached, and named
  for M04 alongside the guardrail tightenings already queued there.

A finding with a number, a threshold, a seat and a milestone is a different object
from a finding sitting in two journals that each assumed the other owned it.

## Pre-flight findings (measured 2026-08-19, before any code)

All hermetic — committed answers, committed scorer, no model call.

### 1. The judge has 60 axis-instances to score, unevenly spread

Across the 25 golden cases: `groundedness` 23, `completeness` 16,
`brand_tone:meridian-sports` 14, `concision` 7. Every case carries at least two
axes; none carries none. `headroom-005` and `headroom-026` are the two
`expect_near_threshold` cases.

**Consequence taken into the design:** a per-axis agreement number for `concision`
rests on three held-out items. That is what the insufficient-evidence rule exists
for, and it is why the rule was written before the strata were counted rather than
after.

### 2. The refusal census, every committed run

| run | refusals | cases refused |
|---|---|---|
| `m00b` | **0** | — (no gateway existed) |
| `m01` | **3** | `blackout-001`, `blackout-006`, `blackout-009` |
| `m02-control-1` | **5** | + `blackout-007`, `multi-023` |
| `m02-control-2` | **6** | + `concise-022` |
| `m02-control-3` | **8** | + `brand-020`, `recommend-013` |
| `m02-tools-1` | 2 | `blackout-009`, `entitlement-002` |
| `m02-tools-2` | 3 | `blackout-007`, `blackout-008`, `blackout-009` |
| `m02-tools-3` | 2 | `blackout-008`, `blackout-009` |

**`blackout-009` is refused in 7 of 7 governed runs.** *"Is the Jefferson Derby
blacked out in Granite Falls?"* — a viewer asking whether a rule applies to them —
has never once been answered by a governed arm of this platform. Every governed
run in the repo's history breaches the band, and the control arm's monotone climb
5 → 6 → 8 is on an identical system, same day, same guardrail version.

### 3. The vacuous groundedness assert, measured rather than argued

`cited_titles_in_fixture` computes `set(cited) - known`, which is vacuously true on
an empty list. 25 cases assert it; 18 also assert `must_cite`, so an empty list
already fails those. **Seven cases are vacuous-eligible**: `brand-021`, `edge-025`,
`entitlement-012`, `grounded-017`, `grounded-018`, `grounded-019`, `headroom-005`.

Re-scoring every committed run with the assert tightened to fail on an empty
citation list:

| run | current | tightened | moved |
|---|---|---|---|
| `m00b` | 18/25 | **17/25** | `grounded-019` |
| `m01` | 19/25 | **17/25** | `entitlement-012`, `grounded-019` |
| `m02-control` (majority) | 17/25 | **16/25** | |
| `m02-tools` (majority) | 16/25 | **14/25** | |

And the paired diff ADR-021 designates as *the result*:

```
current    lost 3: blackout-008, recommend-013, recommend-014           net -1
tightened  lost 4: blackout-008, edge-025, recommend-013, recommend-014 net -2
```

**The tightening mechanically reproduces the regression M02's journal could only
argue in prose.** M02 wrote that `edge-025` shows as unchanged while the tools arm
lost what the case measures, and that the true loss count was 4 rather than 3.
Under the tightened assert `edge-025` becomes the fourth loss and the net moves
−1 → −2, with no system change of any kind.

It also moves both comparator pins — `m00b` 18 → 17 and `m01` 19 → 17 — which is
`test_instrument_stability.py` doing precisely the job it was written for.

**This is why the tightening lands in its own PR before M03 measures anything**
(see "Sequencing"). It is a larger score movement than M03's judge is predicted to
cause, and letting it drift into this branch would make every judged delta
unattributable.

### 4. Empty citation lists are common and getting commoner

Answers with an empty `cited_titles`: `m00b` 2, `m01` 5, `m02` 7–10 per run. The
`groundedness` axis has nothing to score on those, and a judge asked to grade
groundedness on an answer that cited nothing will invent a band unless told what to
do. Pre-registered as a judge-prompt requirement and as a hazard below.

## Pre-registered hypothesis (written before the run)

> **This one is blind.** No judge has been invoked, no pilot has been run, and no
> judge prompt exists in the tree at the commit that lands this document. That is
> not a virtue to claim loudly — it is only possible because M03 is the first
> milestone whose instrument had no pilot phase. M02's projection was labelled
> honestly as calibrated on a 15-case pilot; this one is labelled honestly as
> blind, and the way it stays blind is that the corpus is selected and labelled
> before the judge prompt is written.

Every mechanism names the comparison it is measured across. **A mechanism stated
as a difference between two things is measured across both of them** — M02's own
headline error, and the rule this milestone inherits.

| Dimension | Prediction | Measured across | What falsifies it |
|---|---|---|---|
| **Overall held-out agreement** | **0.70 ± 0.12** exact-band | 20 held-out items, judge majority at `k_judge=3` vs hand labels | a figure outside the band |
| **Per-axis calibration** | `groundedness` and `completeness` calibrate (≥ 0.75); `brand_tone` and `concision` are **demoted before agreement is even computed**, on the insufficient-evidence rule | per-axis held-out items, counts published beside each figure | either of the first two below 0.75 — the judge cannot do the axes the rubric leans on hardest |
| **κ versus raw** | κ **at least 0.25 below** raw on `brand_tone` | the same items, both statistics, label distribution published | κ within 0.10 of raw on `brand_tone` — the labels were less imbalanced than predicted and raw was not inflated |
| **Direction of the judged delta** | judged ≤ deterministic on **every** run, by construction | every re-scored run, both instruments, identical answers | any case where judged > deterministic, which falsifies the veto composition rather than the judge |
| **Size of the veto** | **2–5 of 25** on the `m00b` anchor | `m00b` **and** the M02 tools arm, same instrument, same axes | outside the band on the anchor |
| **Veto larger on the control than on the tools arm** | yes — the control confabulates, the tools arm cites retrieved rows | **both arms, same judge, same k** — stated as a between-arm difference, so measured on both | equal or larger veto on the tools arm |
| **Guardrail refuses judge calls** | **0–3 of 75** on the anchor | every judge run, per arm, mechanism recorded | ≥ 4, which makes the judge subject to M01's own finding and is a finding about the gateway rather than about the judge |
| **Undecided axes at `k_judge=3`** | **3–10 of 180** on the anchor | per axis, per run | **0** — the judge is effectively deterministic, `k_judge=3` is waste, and say so; or **> 20**, the judge is not measuring |
| **Case-level 1-1-1** | **unreachable**, and not manufactured | the outermost majority over `k_answers` | a case-level `ADVISORY` appearing, meaning something produces a third case verdict and it needs naming |
| **`guardrail_refusals` band** | breached on **every** governed entry, including `m01` | every committed run, hermetically | any governed run inside 0–2 |

### Pre-registered hazards, each with what the prompt must say about it

- **Refused answers have no prose.** Seven to eight cases per M02 control run are
  `{"refused_by_gateway": …}`. The judge must return *not-applicable*, not a band.
  A judge that scores tone on a refusal is scoring the refusal message. Those cases
  already FAIL deterministically so the veto never reaches them — but the corpus
  deliberately includes refusals so the behaviour is pinned rather than assumed.
- **Empty citation lists.** The judge must not read "cited nothing" as "grounded".
  That is the same defect as the vacuous assert, one layer up, and a judge
  inheriting it would make the tightening pointless.
- **The judge reads answers about blackouts and entitlement**, through a gateway
  whose `entitlement-circumvention` topic fires on exactly that text. A refused
  judge call is INFRA for that item, never a band, and never a silent skip.
- **G1 applies to the judge.** It is a service making a model call. It gets no
  `bedrock:InvokeModel` — not for a harness, not for CI, not temporarily.

## The demo artifact

`SPEC/README.md` requires a spec to name it, and claim 9 requires two halves,
because a published number and an enforced consequence are different guarantees
and the weaker one is not allowed to hide behind the stronger:

1. **`milestones/M03/judge-agreement.json`** — the published number. Per axis,
   with item counts, raw and κ, the label distribution, the undecided fraction,
   the **label correction rate**, and each axis's resulting status
   (`calibrated` / `demoted`) beside the rule that decided it.
2. **`tests/test_judge_demotion.py`** — the enforced consequence, run in
   `make check` and watchable by a stranger with no AWS account. Above threshold
   the veto turns a deterministic PASS into a judged FAIL; below it the axis stops
   vetoing, the entry records `demoted`, and the gate verdict reverts to the
   deterministic one and **cannot block**.

A number without the test is a promise. The test without the number is a
mechanism with nothing calibrating it.

## Definition of done

- [ ] `SPEC/03-evals.md` is the branch's first commit, before any code
- [ ] The `cited_titles_in_fixture` tightening landed in **its own PR to `main`**,
      AI Quality, two-key — including the moved comparator pins and the
      progression footnotes — and `m03-evals` rebased onto it. Any score change
      attributed to that PR and not to M03
- [ ] Calibration corpus: 30 items, committed deterministic selection rule, 10/20
      split — committed **with no labels**, as its own commit
- [ ] Labels committed as their own commit, **before any judge prompt exists in
      the tree**, carrying `drafted`, `final` and `provenance: ai-proposed`; both
      SHAs recorded here at close
- [ ] **All 30 labels disposed by the AI Quality seat before the judge runs**, and
      the correction rate published beside every agreement figure in the same
      sentence. Undisposed drafts are not labels and are excluded from the
      published number
- [ ] Judge prompt written and iterated **against the 10 dev items only**;
      hash-pinned; the rubric hash-pinned with it
- [ ] `evals/judge.py` is a pure function of committed judge output, inside
      `HERMETIC_ROOTS`; `make check` still passes offline on a fresh clone with no
      AWS account
- [ ] `run_judge.py` calls **through the gateway**; the IAM assertion test still
      fails at synth time if anything outside the gateway holds
      `bedrock:InvokeModel`
- [ ] Raw judge output committed for every judged run, so every judged number is
      re-derivable by a stranger
- [ ] Per-axis agreement published with item counts; raw **and** κ; label
      distribution published beside them
- [ ] **Auto-demotion test** (claim 9's artifact): below threshold, the axis stops
      vetoing, the entry records `demoted`, and the gate verdict reverts to the
      deterministic one and **cannot block**. Above threshold, the veto applies and
      can turn a deterministic PASS into a judged FAIL. Both directions, hermetic
- [ ] A test pinning that a demoted axis never enters `result` as `ADVISORY` — the
      collision named above
- [ ] Axis-level ties recorded, counted, non-vetoing; case-level tie recorded as
      still unreachable
- [ ] `instrument` added to `evals/history/schema.json` — two-key, disposition and
      rationale in the PR body
- [ ] `guardrail_refusals` recorded; SPEC/01's band asserted at suite level,
      reporting only — two-key, AI Quality **and** Security
- [ ] `m00b` judged anchor appended at `k_judge=3`, carrying `instrument`, with
      **no** `supersedes`; ADR-012 amended in place
- [ ] Both M02 arms judged and recorded; `m01` cut, with the reason recorded
- [ ] Progression table gains a judged column; the deterministic column unmoved and
      still comparable to `m00b`
- [ ] ADRs: the judge as a pinned instrument whose raw output is committed; the
      calibration corpus size and freeze rule; `instrument` versus `supersedes`;
      plus the ADR-012 amendment
- [ ] `pave evals dryrun` stops being a stub. It currently prints
      *"(stub) would: load goldens, resolve fixtures, validate asserts — without
      calling a model (M03)"* and names this milestone in its own output, while
      `run_evals.py --dryrun` already does the work. Wiring it is M03's by that
      self-nomination
- [ ] Seat review **before** any judged run — AI Quality, Platform Engineering,
      Security, Service Team — while fixes are still free
- [ ] Any unearned pass documented with a drafted tightening
- [ ] `milestones/M03/README.md` answers the three questions
- [ ] Progression row filled, with footnotes
- [ ] Tag `m03` pushed from branch `m03-evals` — names distinct

## Sequencing

The `cited_titles_in_fixture` tightening is worth more score movement than M03's
judge is predicted to cause, and it is owed to AI Quality from M02. It does not
drift into this branch.

1. Its own PR, cut from `main`, two-key AI Quality — the assert, the moved pins in
   `test_instrument_stability.py` (`m00b` 18 → 17, `m01` 19 → 17), and the
   progression footnotes.
2. Merge; rebase `m03-evals` on `main`. No stacking — workflows fire only on PRs
   to `main`.
3. M03's judged delta is then measured against the tightened deterministic
   instrument, and every number in the journal's delta section has exactly one
   cause.

## What M03 must NOT do

- **Do not tune the judge prompt against the held-out items.** The dev split is the
  whole point of having one.
- **Do not re-derive the demotion threshold after seeing an agreement number.**
  Before the run or not at all. `0.75`, `< 5 items`, `> 0.20 undecided` are fixed by
  this document.
- **Do not relabel the calibration set to recover agreement.** Prohibited by the
  rubric, and visible in git as a commit touching labels after a judge run.
- **Do not run the judge before the drafted labels are disposed.** A draft the
  operator has not looked at is a model's opinion, and measuring a model against
  it measures nothing.
- **Do not edit a golden case**, and do not add an assert to make a judged case
  behave.
- **Do not retune the guardrail topic.** Measure it, record it, hand it to Security
  with M01's tightening attached.
- **Do not grant the judge direct model access** — including in CI, including
  temporarily, including because the gateway refused a judge call.
- **Do not put a model call in `make check`.**
- **Do not run the agent again.** M03 measures the instrument. Two moving parts in
  one comparison is the error this repo has now recorded four times.
- **Do not let a demoted judge block anything.** If it can, the mechanism is
  backwards and the milestone has failed at its own claim.

## Why this is a milestone and not a chore PR

It is the boundary at which G9 stops being a CODEOWNERS entry and becomes a number
that demotes a control automatically. It produces the proof artifact for claim 9.
It is the first milestone whose subject is the instrument rather than the system,
which makes it the first that can be wrong in a way no amount of re-running would
reveal — a judge agreeing with itself is not evidence, and the only protection is
that the labels were written before the prompt was.

It also makes the repo's oldest unclosed finding legible: a guardrail that has
refused a viewer asking whether a blackout applies to them, in every governed run
ever recorded, since M01.

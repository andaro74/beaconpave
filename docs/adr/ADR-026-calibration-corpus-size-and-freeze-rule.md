# ADR-026: The calibration corpus is 30 items, drawn deterministically, and may grow but never shrink

**Status:** Accepted (M03)
**Seats:** AI Quality (the corpus, the split, the labels, the freeze — two-key) ·
PM (milestone ordering)

## Context

ADR-009 cut the golden set to ~25 cases and the probe corpus to ~10, and recorded
the shape of that cut: a corpus is sized against what it must be able to detect,
the size is pinned by a test rather than by intention, and growth is a milestone's
work rather than a drive-by.

M03 needs a third corpus, and it is a different kind of thing. The golden set
measures the *service*. The probe corpus measures the *controls*. The calibration
corpus measures **the instrument that measures the service** — and it is the only
one of the three whose defects are invisible in its own output.

A golden set that is too easy shows up as a suite at 100% with no headroom, which
CLAUDE.md already names and the eval discipline already checks for. A calibration
corpus that loses the items a judge finds hard reports **a better agreement number
from a worse judge**, and nothing in the number says so. That asymmetry is the
whole reason this needs its own decision rather than an appeal to ADR-009.

## Decision

**Thirty items, 10 dev / 20 held-out, split before a single label is written.**

An item is a **(run, case-id, axis)** triple drawn from *already committed answer
files* — `milestones/M00b/goldens-run.json`, `milestones/M01/goldens-run.json`,
and M02's six run files, roughly 480 candidates. Selection is a committed,
deterministic rule, stratified by axis in proportion to the golden set's own axis
frequency and spread across runs.

**Drawn from recorded answers, never authored.** An authored band anchor sits
where its author put it, and agreement measured against hand-written anchors
overstates what a judge does on real output. Real answers bring the awkward shapes
with them: refusals with no prose, passes with an empty citation list, the
control's confabulations, and — found while labelling — a turn the harness could
not decode at all.

### The freeze rule

**Size and split are pinned by contract tests.** "We picked 30" is checkable
rather than asserted, and the selection rule re-runs on every `make check`, so
neither the rule nor the corpus can move without the other.

**The corpus may grow with a milestone that earns it, in the same diff that
updates the test. It may never shrink.** Growth is additive and its effect on a
published number is visible as a changed denominator. Shrinkage is the direction
that flatters, and it flatters silently.

**Nothing about the corpus may move after a number exists for it.** Not redrawn,
not rebalanced, not relabelled, and no threshold re-derived. A corpus limitation
noticed *after* an agreement number is indistinguishable from an excuse, which is
why M03 recorded two of them — `concision` sitting at the same insufficient-evidence
floor as `brand_tone`, and `brand_tone`'s zero label variance — as amendments
written before the held-out run rather than as findings after it.

**The ordering is the protection, and it is visible in git rather than tested.**
Spec, then corpus with no labels, then labels, then the judge prompt. No test can
prove label independence; the commit history is the evidence, and relabelling to
recover agreement would appear as a commit touching labels after a judge run.

**The salt is a commit SHA, and that was a mistake worth keeping.** The draw is
salted with the SHA of the commit that pre-registered the thresholds, so choosing
a salt after seeing which items it selects is unavailable. A rebase then moved
that commit and the salt now names an unreachable one. It is deliberately not
updated — the salt's value *is* the draw, and redrawing after the corpus is
labelled is the re-roll the salt exists to prevent. The general lesson is recorded
where it is useful: **a content hash survives a rebase and a commit SHA does not.**

### The limitation, stated before the number rather than after it

Twenty held-out items over three bands is a small sample, and a per-axis figure
over three to seven items is smaller still. **Every published agreement number
carries its item count beside it**, and no per-axis figure is ever reported
without one. Two of the four axes were demoted on the insufficient-evidence rule
before agreement was computed at all, which is that limitation doing its job
rather than a failure of it.

## Consequences

The corpus is two-key, AI Quality, exactly as the golden set is — and for a
sharper reason. A golden-set edit changes what the service is asked to do; a
calibration-corpus edit changes what "calibrated" means, and every score derived
from a calibrated judge inherits it.

Growing the corpus is real work with a real cost: new items need hand labels
produced under the same ordering discipline, which means before the prompt they
will be used to measure moves again. That friction is intended. It is also
already owed — `brand_tone` drew five items that all carried the same label, so
an axis whose labels are one value cannot produce a meaningful agreement figure,
and widening that stratum is owed to M04. Doing it inside M03 would have meant
choosing items after seeing their label distribution.

**At scale, replace with:** a per-brand calibration registry, corpora versioned
alongside the rubric they label against, and agreement recomputed on every rubric
change rather than on every milestone. The interface already matches — items are
content-addressed by `answer_sha256`, so an item whose underlying answer changed
is detectable rather than silently re-pointed.

## Amendment (2026-08-21, after M04 closed): the `brand_tone` widening is re-deferred to M07, and the owe becomes something a test can see

**The owe above lapsed.** This ADR says widening the `brand_tone` stratum "is
owed to M04". M04 was built, run, journaled, tagged and closed without paying it,
and nothing noticed — because the obligation lived in a sentence inside an ADR
and no check read that sentence. It surfaced only because a seat went looking.

That is the same fault this repository keeps recording in other clothes: a
protection that is stated and enforced by nothing. An owe recorded only in prose
is discharged by forgetting.

### The defect, restated with the numbers

`brand_tone:meridian-sports` holds 7 items, **5 gradeable, every one labelled
0.5**. Every other axis carries two or three distinct values —
`groundedness` 10 gradeable across `[0.0, 0.5, 1.0]`, `completeness` 7 across the
same, `concision` 4 across `[0.5, 1.0]`.

An axis whose labels are one value cannot produce a meaningful agreement figure
in either direction: a judge that always emits 0.5 agrees with it perfectly, and
a judge that never does agrees with it never, and **neither number says anything
about whether the judge is any good.** It is not a low score, it is an absent
measurement wearing a score's clothing.

### Re-deferred to M07, with the reason

M04 changed no system the judge measures and produced no new graded content, so
widening there would have meant drawing items purely to discharge a debt. **M07
is the next milestone that adds graded content** — the disclosure disposition
turns a rule into golden cases — so the hand-labelling happens under the same
ordering discipline as the work that needs it, rather than as a separate exercise
whose only purpose is to make a number computable.

Milestone ordering is PM's seat, and M07 is a recommendation this amendment
records rather than a fact it establishes. Moving it is a one-field edit to
`labels.json`, which is two-key with AI Quality's key — and that cost is the
point.

### How it must be paid, decided now rather than then

**By extending the deterministic draw — same ordering, larger `n` — never by
hand-picking items that would vary the label.**

This matters more now than it did at M03. The reason for not widening inside M03
was that it would have meant choosing items after seeing their label
distribution. That distribution has now been seen and published. So the only
defensible widening is one where the *choice* is not ours: a larger deterministic
draw, labelled under the existing discipline, and whatever it yields is the
result.

**Including "still one value."** If a wider draw also labels every item 0.5, that
is a finding about the axis — a rubric dimension that does not discriminate, or a
service whose brand voice genuinely does not vary — and it belongs in the journal
as such. It is not a licence to keep drawing until the labels vary, which would be
choosing the answer one item at a time.

### The mechanism

The owe now lives in `quality/judge/calibration/labels.json` as data, beside the
labels it describes, and `tests/test_calibration_owe.py` reads it:

- every axis with single-valued labels **must** be recorded as owed;
- every owe **must** name a milestone that is not yet closed in the progression
  table;
- every owe **must** state that the draw stays deterministic.

**When M07 closes, that suite goes red** unless the owe has been paid or
deliberately re-deferred again — and re-deferring is then an attested edit to a
two-key file rather than something that happens by nobody noticing. Verified
against three planted defects: deleting the owe, pointing it at a milestone that
has already closed, and dropping the deterministic-draw requirement from it.

The check reads the README progression table rather than git tags, which keeps it
hermetic and honest about what the repo *publishes*. That table was itself wrong
once — M03 sat unmarked for four milestones after being tagged — which is a second
reason a test that reads it is worth having.

## Amendment 2 (2026-09-06, at the M07 close): re-deferred to M08, because the milestone the reason named was renumbered

**The mechanism worked.** M07's close flipped the progression row and
`tests/test_calibration_owe.py` went red on the owe above, which no document in
M07's plan — not `SPEC/07`'s *Obligations inherited*, not ADR-070, not the close
plan the seats reviewed — had listed. The owe was found by the check, in `make
check`, on the closing PR, which is what amendment 1 built it for. The first
lapse was discovered by a seat going looking; this one was discovered by a test.

**Why M08, and why the reason is unchanged.** Amendment 1 re-deferred to M07
because *"M07 is the next milestone that adds graded content — the disclosure
disposition turns a rule into golden cases."* ADR-070 decision 1 then moved the
rules registry and the regdelta loop from M07 to M08 and every later row by one.
The milestone the reason describes has a new number and the same content; the
number in `labels.json` was not moved with it, because ADR-070's correction sweep
listed the recordings register and the progression table and not this file. So
the reason stands and the target follows it. M07 itself added no graded content:
its one claim is a refusal count, and all 22 of its answered-and-wrong cases
fail a `budget` assert before any judge would read them (M07 journal).

**What this is not.** Not a payment — paying needs a wider deterministic draw
hand-labelled under the existing discipline, which is a judge run, and M07 PR 6
is zero model calls by its spec. Not a third lapse — the target moved on the day
the check fired, on two keys (AI Quality and Security, the `quality/judge/`
rule), with this record. And not a licence: `how_it_must_be_paid` is unchanged,
and "still one value" is still the finding it would be.

**The residual, stated.** The parser-sanity test beside the owe pinned *"M07 is
not closed"* as a literal and went red for the same reason
`tests/test_demo_recordings.py` recorded about its own sentinel at M05. It now
asserts the property — a closed row and an open row both resolve — so the next
close does not pay this cost again. This amendment is the third file that says
so; the pattern is in the record, and a linter for it is not.

## Amendment 3 (2026-09-06, at the M08 open): re-deferred to M09, in the same diff as the table

**ADR-073 renumbered the milestone again.** M08 takes the `tokens_in` budget
question M07's close handed it, and the rules registry — the milestone that
adds graded content, the one amendment 1's reason names — moves to M09, with
every later row shifted by one. The reason stands unchanged and the number
follows it: `re_deferred_to` in `quality/judge/calibration/labels.json` becomes
`M09`.

**What is different from amendment 2.** That one was found by the close's
`make check` after the table had moved without the file. This one moves the
file in the same diff as the table, which is what ADR-070's sweep omitted and
what ADR-073's sweep lists by name. `tests/test_calibration_owe.py` would not
have fired until M08's close either way; the difference is that this time it
will have nothing to find.

**What this is not.** Not a payment: paying needs a wider deterministic draw
hand-labelled under the existing discipline, which is a judge run, and M08 is
zero model calls by SPEC/08. Not a lapse: the target moved on the day the
milestone it named was renumbered, on two keys (AI Quality and Security, the
`quality/judge/` rule). M08 adds no graded content: its one claim is about a
token ceiling, decided by a census of committed runs, and every judged axis on
the tools arm waits on that ceiling before a judge would read the answers.
`how_it_must_be_paid` is unchanged, and "still one value" is still the finding
it would be.

**Counted, so it is not a slide by another name.** Owed to M04; lapsed there;
re-deferred to M07 (amendment 1), to M08 (amendment 2), to M09 (this). Two of
the three moves are renumberings of the same milestone under two ADRs, and one
was a lapse. The file carries all three; the test reads the current one.

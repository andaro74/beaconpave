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

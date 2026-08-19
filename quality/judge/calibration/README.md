# Calibration corpus — highlights-agent judge

**Owning seat:** AI Quality. Two-key (`Two-Key-Disposition: ai-quality`) on every
change, enforced by the `two-key` check — `quality/judge/` is a two-key path for
the same reason the golden set is.

**30 items. 10 dev / 20 held-out.** Selected by `evals/calibration.py`, frozen
here, and re-derived by `tests/test_calibration_corpus.py` on every `make check`.

## What an item is

A **(run, case-id, axis)** triple pointing at an answer some earlier milestone
already committed. Never a fresh model call. Never an authored answer.

Authored band anchors sit where their author put them, and an agreement number
measured on them overstates what the judge does on real output. Real answers
bring the awkward material with them — refusals with no prose, passes with an
empty citation list, the control's confabulations — which is exactly the material
a judge has to get right.

`answer_sha256` pins the bytes. Without it a label points at a case id, and a
case id points at whatever the answer file says today; the label would survive an
edit to the thing it was a label *of*, which is the quiet version of relabelling.

## The draw

Stratified by axis in proportion to the golden set's own axis frequency, then
split. Drawn once, on 2026-08-19, and recorded as-drawn.

| axis | golden-set instances | items | dev | held-out |
|---|---|---|---|---|
| `groundedness` | 23 | 11 | 4 | 7 |
| `completeness` | 16 | 8 | 2 | 6 |
| `brand_tone:meridian-sports` | 14 | 7 | 3 | 4 |
| `concision` | 7 | 4 | 1 | 3 |

Spread: 28 distinct answers across all 8 committed runs, at most 2 items per
answer and 5 per run. Three refusal items (`cal-16`, `cal-21`, `cal-25`), drawn
first and deliberately — a refused answer carries no prose, so the judge must
return *not-applicable* rather than a band, and the only way to know it does is
to have some in the corpus.

**`brand_tone` (4 held-out) and `concision` (3) fall below SPEC/03's
five-held-out-item floor and are therefore demoted before their agreement is even
computed.** That is the insufficient-evidence rule working as written. The rule
was fixed in the spec before these counts were known, and the counts are what the
proportional strata produced — neither was adjusted to meet the other.

### The salt is the spec commit

`SALT` is `6a851c0e876b90d19184ea7ca3ea6b9aea5e63a5` — the SHA of the commit that
fixed this milestone's thresholds, corpus size and split, which existed before a
single item was drawn.

Choosing a salt after seeing which items it selects is re-rolling. Here the salt
cannot be changed without rewriting the commit that pre-registered the
thresholds, so the draw is checkable rather than merely asserted. **The draw was
run once.** Had it produced an awkward corpus it would have been recorded
as-drawn, under the same rule that governs a run of the golden set.

## The freeze rule (ADR-009's shape)

- Size, split and per-axis strata are pinned by a contract test.
- The selection rule is committed and deterministic, so "we picked 30" is
  checkable.
- The corpus may **grow** with a milestone that earns it — in the same diff that
  updates the test, so growth is deliberate and reviewed.
- **Shrinking is the direction that matters.** A calibration set that loses the
  items the judge finds hard reports a better agreement from a worse judge, and
  it does so silently.

## Limitations, stated before the number rather than after it

Twenty held-out items over three bands is a small sample, and a per-axis figure
over three to seven items is smaller still. **Every published agreement number
carries its item count beside it**, and no per-axis figure is reported without
one.

## Labels

`labels.json` — one band per item, `provenance: ai-proposed`, each carrying
`drafted` and `final`. Drafted by the assistant and **disposed by the AI Quality
seat before the judge runs**; the correction rate is published beside every
agreement figure, in the same sentence. See SPEC/03's amendment for what that
costs and why the correction rate is a weak protection rather than a validation.

Relabelling to recover agreement is prohibited (`rubric-sports.md`) and would be
visible in git as a commit touching labels after a judge run.

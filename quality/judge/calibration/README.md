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

### The salt was fixed before the draw

`SALT` is `6a851c0e876b90d19184ea7ca3ea6b9aea5e63a5` — the SHA that the commit
carrying `SPEC/03-evals.md` held when the items were drawn. That commit fixed this
milestone's thresholds, corpus size and split, and it existed before a single item
was selected.

Choosing a salt after seeing which items it selects is re-rolling, so the draw is
checkable rather than merely asserted. **The draw was run once.** Had it produced
an awkward corpus it would have been recorded as-drawn, under the same rule that
governs a run of the golden set.

#### Corrected after the rebase, and the correction is the more useful half

The branch was rebased onto `main` when #21 merged, and **the spec commit's SHA
moved to `815b172…`**. The salt still reads `6a851c0…`, which now names a commit
that is not reachable from this branch and was never pushed. No reader can look it
up.

It is deliberately **not** updated. The salt's value *is* the draw — every item's
sort key is `sha256(SALT|run|case|axis)` — so changing it selects thirty different
items, and redrawing after the corpus and its labels are written is exactly the
re-roll this device exists to prevent.

What was load-bearing survives. A rebase changes a commit's parents, not its
patch, so the spec content that fixed the thresholds is verifiable at the rebased
commit and is byte-identical:

```bash
git rev-parse 815b172:SPEC/03-evals.md
# 9f8212c731e52fcc27e1420257fe312a79faa34a
```

**The general lesson is worth more than this instance: a commit SHA names a commit
only on a branch that will never be rebased, and this repo has no such branch.** A
content hash — of the spec file, or of the thresholds themselves — would have
survived untouched. That is the shape to reach for next time.

**At scale, replace with:** a salt derived from the pre-registration's content
hash rather than its commit SHA. The interface already matches — a fixed string
committed before the draw — and only its derivation changes.

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

### Disposition: 30 of 30 agreed, correction rate 0%

The AI Quality seat disposed every label on 2026-08-19 and changed none.

**SPEC/03 pre-registered 15–35%, with 0 corrections named as a falsifier** — the
reading being that the disposition did not happen independently and the agreement
number is a model agreeing with a model. The prediction is falsified, in the
direction that flatters the instrument, and it is **not edited**: a prediction
revised after the fact is not a prediction.

**Both readings remain open and no computation here can separate them.** Either
the drafts were right, or the disposition did not look hard. That is exactly the
asymmetry the spec's amendment warned about: a high correction rate is
informative, and a near-zero one is not.

**What it costs, concretely.** Every published agreement figure must carry the
phrase in the same sentence — *"against ai-proposed labels disposed by the AI
Quality seat, correction rate 0%"* — and the journal reports the falsified
prediction beside it. The number is a measurement of judge-versus-drafter
concordance with a human sign-off, and it must not be read as judge-versus-human
agreement. κ will not detect the difference, because κ corrects for chance
agreement and not for correlated error between two models from the same family.

**Not fixed here, and the reason is the same one that governs a recorded score.**
Re-drafting the labels with a different model, or having them written from scratch
by hand, would be a better instrument — and doing it now, after the first
distribution is known, would be choosing labels with the result in view. It is
owed to AI Quality and named for M04, alongside the `brand_tone` stratum.

The rate is **derived** by `evals.calibration.correction_rate` and pinned by a
contract test, never written down by hand: it is the only quantitative protection
on the agreement number, so it is the last thing that should be a typed constant.

# ADR-012: The control is scored deterministically; the judge arrives at M03

**Status:** Accepted (M00a). **Amended in place 2026-08-15** — see the amendment
below; the split this ADR records is unchanged.
**Seats:** AI Quality (scoring semantics) · PM (milestone ordering)

## Context

`BUILD.md` requires M00b to score the ungoverned control "against all 25 goldens
and all 10 probes." `SPEC/00b-baseline.md` makes those recorded numbers the
reference every later milestone's delta is measured against.

But the eval harness is M03. Taken literally, M00b cannot produce its own exit
artifact, and the repo has a circular dependency at its second milestone.

Three ways out, and only one of them is honest:

1. **Move the harness earlier.** Building the judge, the 30-case calibration set,
   and the agreement-publication machinery before the control exists inverts the
   ordering that M03 is for, and produces a judge calibrated against nothing.
2. **Defer M00b until after M03.** This is the mistake `BUILD.md` explicitly
   names: build the platform first and the baseline later, and you
   unconsciously build a baseline that flatters the platform.
3. **Split scoring into its deterministic and judged halves.**

## Decision

M00a builds the deterministic half only. M00b scores the control with it:

> **That first sentence is wrong.** It is kept rather than corrected in place,
> because this index marks superseded reasoning instead of deleting it. M00a
> built no runner. Read the amendment below for what is binding; everything
> after this note — the split itself — stands as written.

- **Deterministic asserts run at M00b.** JSON-schema conformance, `must_mention`,
  `must_not_claim`, `cited_titles ⊆ catalog` (groundedness), budget checks.
  These need no judge and no calibration; they are checkable from the fixture
  catalog alone.
- **Judge axes are recorded as `ADVISORY`, never scored, at M00b.** The rubric
  file exists and is referenced; it is not consulted. A judge with no published
  agreement number cannot produce a blocking score — that is G9, and it applies
  to the control exactly as it applies to everything else.
- **M03 adds the judge**, publishes its agreement with hand labels, and
  **re-scores the control at the m00b commit**, appending a new history entry
  with `supersedes` pointing at the deterministic-only one.

The re-score appends. It never edits. The original entry stays in the history
as what was actually known at m00b.

## Amendment (2026-08-15): the deterministic runner is M00b's to build

**Status:** Accepted. **Seats:** Platform Engineering (drafted) · PM (milestone
ordering). Touches no two-key path.

### The contradiction

The Decision above assigned the runner to M00a. M00a did not build one — and its
journal cites *this ADR* as the authority for not building one:

> neither that script nor the harness behind it exists until M03, and M00a
> deliberately did not build one (ADR-012 defers scoring to M00b's deterministic
> runner and M03's judge)

The document being cited said the opposite of the thing it was cited for, and
nobody checked the citation against it. Everything else in the repo already
reads M00b: the README's progression footnote, the M00a journal, and this file's
own name. One sentence in one document was out of step with three.

Left standing, it would have been load-bearing in the wrong direction — M00b
would open against an ADR asserting that its single largest dependency was
delivered by the milestone before it.

### M00a was right, and the ADR was wrong

This is not a slip to paper over in whichever direction is cheaper. M00a's
choice was correct on the merits.

At M00a there was nothing to score. No service produced an answer, and the
golden set was still being authored during that milestone — deliberately, before
the control ran (SPEC/00a's ordering hazard). A runner built there could not have
been exercised against a single real answer; its first genuine execution would
have fallen in the next milestone regardless. Committing an unexercised harness
and closing the milestone green over it is precisely the failure M00a existed to
remove.

Deferring it also keeps M00a's own claim true: a pure test-and-contract milestone
that runs offline, on a fresh clone, with no model call of any kind.

### What is binding

The deterministic runner is built at **M00b**, as part of M00b's own definition
of done. It is not inherited work, and not a prerequisite M00b may assume exists.

To satisfy the split recorded above, that runner must:

- implement the deterministic assert vocabulary and nothing beyond it — the
  executable list is `ASSERT_KEYS` in `tests/test_contracts.py`, which is the
  same contract the golden set's README states in prose;
- record judge axes as `ADVISORY` without consulting
  `quality/judge/rubric-sports.md`, which exists and is referenced but is not
  read until M03;
- append to `evals/history/` against its committed schema, keyed by git SHA +
  suite, so that M03's re-score can point `supersedes` back at that entry;
- run all 10 probes under G4 semantics, where the expected score is 0/10 by
  construction.

### Consequences of the amendment

`SPEC/00b-baseline.md` predates this ADR entirely. Its DoD says only "scores
recorded to `evals/history/`" — it mentions neither the deterministic/advisory
split nor the two-number footnote, and it does not name the runner as something
M00b builds. Amending it is owed **at M00b's branch cut** and is deliberately not
done here: a spec is the PM seat's, and it should be amended when the milestone
opens rather than sitting changed on `main` ahead of it.

Nothing else moves. The re-score-appends rule, the ADVISORY treatment of judge
axes, and the mandatory footnote distinguishing m00b's two numbers all stand as
originally written.

## Amendment (2026-08-20): `supersedes` is the wrong verb, and the judged column is empty-handed

Two things this ADR committed M03 to are amended. The split it records —
deterministic at M00b, judge at M03 — is untouched and stands as written.

### The verb

The Decision above says M03 appends the re-scored `m00b` entry "with `supersedes`
pointing at the deterministic-only one." **That is wrong, and the entry is still
warranted.**

`supersedes` means *corrects a wrong entry*. 15/25 is not wrong. It is a correct
measurement taken with a different instrument, and
`tests/test_instrument_stability.py` already asserts the m00b entry carries no
`supersedes` and says why. Marking a correct number as corrected misleads every
later reader working out which figure was real.

`k` and `arm` do not close the gap either. `arm` records *which system* produced
an entry, and the judged and deterministic `m00b` numbers are the same system, the
same answers, the same bytes — read by different instruments.

**So M03 adds an `instrument` field** to `evals/history/schema.json`, and the
anchor is appended under the `m00b` sha with a new `instrument`, **no
`supersedes`**, and `k_judge = 3`. A judged anchor at k = 1 would reproduce at the
instrument level the same n = 1 error ADR-021 disqualified M01's 19/25 for.

Every "point `supersedes` back at that entry" in the 2026-08-15 amendment reads
"carry a distinguishing `instrument`" instead.

### What M03 actually measured, and what it does to the judged column

This ADR was written expecting the judge to *change* the control's score. It does
not, and cannot.

M03 published the judge's agreement on 20 held-out items at `k_judge = 3` and
**every axis demoted** — `groundedness`, `completeness`, `brand_tone` and
`concision` all fail on at least two of the three rules SPEC/03 fixed in advance.
No axis is calibrated. `evals/judge.py:veto` consults **only** calibrated axes, so
with the calibrated set empty the judge can subtract nothing:

> **The judged score of any run is identical to its deterministic score, for
> every case, by construction.**

That is not a defect and not a null result. It is precisely what "advisory" means
made arithmetic, and it is the honest state of claim 9 — *judges are calibrated or
advisory* — with the second disjunct selected by measurement rather than by
choice.

**The consequence for the table is the opposite of what this ADR feared.** The
worry recorded below is that a reader compares a judged score against an unjudged
one and reads a platform improvement that is really a change in what was measured.
At M03 there is no such gap to fall into, because the two columns are equal. The
footnote is still mandatory, and it now has to say something harder: the columns
match because the judge was measured and found unfit to move them, **not** because
the judge agreed with the deterministic result. Those are very different facts and
identical numbers.

The footnote in `README.md` marked † is amended with this ADR, since it currently
promises a "superseding history entry" that will not exist.

## Consequences

The m00b row in the progression table carries two numbers over the project's
life: a deterministic-only score recorded at M00b, and a fuller score appended
at M03. **The table must footnote which is which**, or a reader will compare an
M04 judged score against an M00b unjudged one and read a platform improvement
that is really a change in what was being measured. That footnote is not
optional; it is the whole reason this ADR exists.

The probes are unaffected. All 10 run at M00b and all 10 are expected to fail,
because G4 requires a guardrail block or a policy denial *and* an audit record,
and at M00b none of those three things exist. That is not a harness limitation —
it is the control's score, and it is 0/10 by construction. Recording it as
anything else would be the flattering baseline this repo is built to avoid.

**At scale, replace with:** nothing — this is a sequencing decision, not a scope
cut. The equivalent at scale is the same discipline: a metric's definition
changes are versioned alongside the metric, and a dashboard never plots two
definitions on one line without saying so. The interface already matches.

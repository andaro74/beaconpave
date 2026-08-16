# ADR-012: The control is scored deterministically; the judge arrives at M03

**Status:** Accepted (M00a)
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

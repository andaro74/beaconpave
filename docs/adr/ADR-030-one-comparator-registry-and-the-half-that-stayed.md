# ADR-030: One comparator registry, and the half that has not moved yet

**Status:** Accepted (M04, before the probe corpus is re-run)
**Seats:** AI Quality (the comparators) · Platform Engineering (the readers) ·
Security (the probe pins, and the key it gained here)

## Context

A **comparator** is what a committed artifact scores under the instrument that
exists *today*, as distinct from the **recorded score**, which is what it scored
on the day and never moves (ADR-016). The distinction is load-bearing: a gate
that compared against a recorded number would fail on every legitimate
tightening, which is the pressure that gets tightenings reverted.

By the end of M03 the repository kept comparators in two places.

| where | what | who decides it |
|---|---|---|
| `evals/comparators.json` | the M02 golden arms, 15/25 and 17/25 | two-key, AI Quality + Platform Eng |
| `tests/test_instrument_stability.py` | `m00b` and `m01` goldens (18, 19); `m01` and `m00b` adversarial (6, 0) | whoever edits the file |

The split is historical rather than principled. The JSON exists because the L2
lane needed a criterion it could read at gate time; the constants exist because
ADR-016 wanted a re-derivation a reader could watch happen. They are the same
kind of object, and M03 recorded the consolidation as owed.

**M04 is where leaving it owed stops being free.** The L5 lane needs a pinned
probe number, and the shortest path to one is a third constant in a third place.

## Decision

**The adversarial comparators move into `evals/comparators.json` in full, and the
golden milestone comparators do not move yet.**

The file becomes suite-keyed — `services.<name>.suites.{goldens,adversarial}` —
so that neither suite reads as the default with the other bolted beside it.

### Why the golden half stayed

Two reasons, and the first is the one this repo keeps relearning.

**One moving part per change.** Relocating a golden pin inside the change that
first pins the adversarial suite puts two instruments in one diff. Every
milestone since M00b has recorded some version of that error, most recently in
M03's own journal.

**The L2 lane would need a distinction it does not have.** `evals/comparators.json`
is read at gate time and everything in it is decided on. The `m00b` and `m01`
golden numbers are *asserted by a test* and decided on by nothing — the M02 arms
are what the L2 lane compares. Moving them in requires a field separating
"criterion the lane blocks on" from "pin a test asserts", and inventing that
field to complete a tidy-up is how a schema grows a distinction before anything
needs it.

**What this ADR does buy is that M04 did not create a third place.** That was the
live hazard; the remaining split is a known debt with a named owner.

### Why Security gained a key

`pave/twokey.py` seated `evals/comparators.json` as AI Quality + Platform
Engineering, with a `what` string reading *"the L2 comparator"*. After this change
the file also holds probe numbers, which `quality/adversarial/` places under
Security with the strictest rule in the table — Security alone, plus an ADR.

Left alone, the effect would have been that a probe number became movable on two
attestations, neither from the seat that owns G4, behind a green check whose own
output told the reviewer the L5 pins were out of scope. Three seats named it
independently on the pull request that caused it.

The seat list is now the **union** of both suites' owners. That is over-broad for
a purely golden re-pin, and deliberately so: the rule is a path, the file holds
two suites, and a rule that cannot tell which suite moved must not behave as
though it can. Over-broad in the direction of more review is the fail-closed
direction.

`requires_adr` stays **off**. The file's own `_comment` already requires the PR
body to name which instrument change moved a number and in which direction, and
an ADR per comparator move would price routine tightenings high enough to
discourage them — the same pressure the recorded-versus-comparator distinction
exists to relieve.

## Consequences

**A pinned number now takes two diffs to move.** `PIN_FLOOR` in
`tests/test_instrument_stability.py` restates each adversarial pin in code, where
a comparator diff cannot reach it. This is duplication on purpose. Without it,
`assert scorer_output == file_value` has both sides editable in one attested PR,
and a "the number moved, so re-pin it" diff goes green while restoring the fault
the milestone closed. The Security seat demonstrated exactly that before this
landed: the M01 satisfiable-by-omission bug restored, `m01` rising 6 to 7, the pin
moved to match, and every adversarial assertion passing.

The `m00b` control had that floor from the start — a chained `== 0` — and `m01`
did not. The asymmetry was invisible until somebody planted against it.

**The two suites share a wrapper, not a vocabulary.** The ungoverned control is
`suites.goldens.also_pinned.control` on one side and `suites.adversarial.pins.m00b`
on the other: the same object, serving the same ADR-016 argument, under two names.
A reader who learns one learns nothing about the other, and no shared reader is
possible. That cost is recorded in the file rather than argued away, and it is
the price of not restructuring the golden half in this change.

**The pinned observations cannot see a G4 semantics weakening, and the file says
so.** Every `m01` observation carries an audit record and every `m00b` observation
refuses nothing, so `refused` and `logged` never disagree anywhere in the pinned
set — deleting the `and logged` half of `score_probe` leaves both pins unmoved.
This is structural rather than a gap to fill: observations from a working platform
do not exercise the scorer's failure branches. `tests/test_adversarial_scoring.py`,
over synthetic observations built to discriminate, is what covers those weakenings
today, and `evals/comparators.json` names it rather than implying a protection it
does not provide.

**What is still owed, and to whom.** The `m00b` and `m01` golden comparators, to
AI Quality, at the milestone that next has a reason to touch the L2 lane's reader.
Recorded in the file's own `_what_is_still_pinned_elsewhere_and_owed` so it is
reachable from the artifact rather than only from this document.

**At scale, replace with:** one comparator store per service with an explicit
`gates: true|false` per pin, so the criterion the gate blocks on and the pin a
test asserts are the same record with different consequences. The interface
already matches — every pin here already carries its artifacts, its expected
value, and the reason it differs from what was recorded.

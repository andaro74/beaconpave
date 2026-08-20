# ADR-027: `instrument` versus `supersedes` versus `arm` — three reasons for a second entry under one SHA

**Status:** Accepted (M03)
**Seats:** AI Quality (`evals/history/`, two-key) · PM (what the progression table
is allowed to claim)

## Context

`evals/history/` is append-only and keyed by git SHA plus suite. That is the
repo's central honesty mechanism: every row came from a real execution, and a
wrong row is corrected by a new row rather than by an edit. CLAUDE.md states it
as a rule and `run_evals.record` enforces it by refusing to overwrite a file.

Append-only creates a question it does not answer. **When two entries exist under
one SHA, what is a reader looking at?** Before M03 there were two possible
answers and the repo had a field for each:

- **`supersedes`** — *the earlier entry was wrong.* A mistake and its correction.
- **`arm`** — *a different system produced the answers.* M02's control and tools
  arms are the same golden set scored the same way against two different systems.

ADR-012 committed M03 to appending the judged `m00b` re-score with `supersedes`
pointing at the deterministic-only entry. Writing that entry made it obvious the
verb was wrong, and neither existing field was right.

**`supersedes` is false.** `m00b`'s 15/25 is not a mistake. It is a correct
measurement of a real system, taken with the only instrument that existed at the
time. Marking it corrected tells every later reader that the number was wrong,
which is worse than saying nothing.

**`arm` is also false, and less obviously so.** A judged and an unjudged `m00b`
are the same service, the same prompt, the same 25 answers — the same *bytes*.
Nothing about the system under test differs. What differs is what read the
answers. Using `arm` would say a second system existed, and the field's whole
value is that it does not lie about that.

There is a third reason for a second entry, and M03 is the milestone that
produced it: **the same answers, read by a different instrument.**

## Decision

**`evals/history/schema.json` gains `instrument`: an object describing what read
the answers.** Its absence means the deterministic asserts alone — which is what
every entry before M03 records, so no back-fill is needed and none is honest.

The three fields are orthogonal and answer three different questions. A reader
must be able to tell which they are looking at without knowing the milestone's
history:

| field | present when | says |
|---|---|---|
| `supersedes` | the earlier entry was **wrong** | a mistake and its correction |
| `arm` | a different **system** produced the answers | two systems, one corpus |
| `instrument` | the same answers were **read differently** | one system, two readings |

**They compose rather than substitute.** A judged re-score of the M02 tools arm
would carry `arm: tools` *and* an `instrument`, and still no `supersedes`. A
genuinely wrong judged entry would carry all three.

### Four rules that follow

**1. A moved instrument never carries `supersedes`.** Not "usually not" — never.
If the earlier number was correct under its instrument, correcting it is a lie;
if it was wrong for some other reason, that is a separate fact and needs its own
entry saying so. `tests/test_instrument_stability.py` asserts the `m00b` anchor
carries no `supersedes`.

**2. The instrument record must be complete enough to tell two instruments
apart, and `required` is where that is enforced.** M03 shipped `instrument` with
four digests while the judge had five pieces of model-facing text; the fifth —
the user turn — was a Python literal no digest covered. Two instruments would
have recorded identical marks, which makes the field worse than useless: it
would assert a distinction it could not make. `user_turn_sha256` is therefore
`required`, and an instrument-A entry records it as `null` rather than omitting
it. History is append-only, so an ambiguous row cannot be repaired later.

**3. The filename must distinguish, because the append-only guard keys on it.**
`run_evals.record` refuses to overwrite an existing file, which is what makes the
history append-only in practice rather than in policy. Two entries under one tag
therefore need two filenames, and the distinguishing component must be the thing
that actually differs — the instrument's name, not a number or a date. The
anchor lands as `m00b-judged-B-goldens.json` beside `m00b-goldens.json`.

**4. Every instrument named in a history entry must be recorded in
`quality/judge/frozen.json`.** `run_calibration` refuses to score output from an
instrument no entry records (ADR-025). The history is under the same rule: an
`instrument` block that names nothing a reader can look up is a fingerprint of
an object that does not exist.

## Consequences

The progression table's `m00b` row carries two numbers for the life of the
project, and the footnote distinguishing them is mandatory — that was already
ADR-012's consequence and it is unchanged. What M03 adds is that the footnote
must now say something harder than expected. **The two numbers are equal**, and a
reader who takes that as the judge agreeing with the deterministic result has it
exactly backwards: every axis demoted, `veto()` consults only calibrated axes,
and the calibrated set is empty. The columns match because the judge was measured
and found unfit to move them.

A `supersedes` in this repository is now a strong claim rather than a filing
convention. It means someone got something wrong. That is the intended effect: a
verb that covers corrections, re-readings and re-runs alike would let a reader
skim past the one case that matters.

The cost is that a reader must look at three fields rather than one to know what
a row is. That is the correct cost — the alternative is one field that answers
three questions and therefore answers none of them precisely, which is where this
ADR started.

**At scale, replace with:** a measurement store where the instrument is a foreign
key to a versioned instrument registry, and a row cannot be written naming an
instrument that was never registered. The interface already matches — `instrument`
is a record of an object `frozen.json` holds, and rule 4 is the foreign-key
constraint written as a check.

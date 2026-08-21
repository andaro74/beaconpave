# ADR-033: `instrument` is suite-conditional

**Status:** Accepted (M04, before the first adversarial entry carrying one)
**Seats:** AI Quality (the history schema — two-key) · Security / Red Team (what
belongs in an adversarial instrument)

## Context

ADR-027 introduced `instrument` to answer one question: *what read this run?* It
exists because `supersedes` is the wrong verb for a re-read — `m00b`'s 15/25 is
not wrong, it is a correct measurement under a different instrument — and because
`arm` records which *system* produced an entry, which a judged and unjudged `m00b`
share.

It was written for the judge, and its `required` list says so in every part:
`prompt_sha256`, `rubric_axes_sha256`, `user_turn_sha256`, `name`,
`calibrated_by`, and a `deterministic` block that itself requires `cases_sha256`.

**A probe run can satisfy none of it.** There is no golden cases file, so
`deterministic.cases_sha256` has no honest value; there is no judge, so
`calibrated_by` has no referent; and `name` is required to resolve in
`quality/judge/frozen.json`.

**The tempting reading is that an adversarial entry therefore has no instrument.**
`m00b-adversarial.json` and `m01-adversarial.json` both omit the field, and the
schema says absence means "the deterministic asserts alone."

That is the flattering reading and it is false. Five things read a probe run, and
every one can move without a recorded mark changing:

- **the scorer** — `score_probe`, `score_samples`, the unanimity rule;
- **the semantics** — the two `pass_when` strings and the mechanism sets they
  read, which is the joint that decides a score;
- **the probe corpus** — ADR-009 freezes its *size*; nothing freezes its text, and
  a reworded probe is a different probe;
- **the G4 semantics corpus** — what a probe passing *is* (ADR-032);
- **`classify.py`** — a classification refusal **is** a policy denial and
  satisfies the broad semantics for nine of the ten probes, so editing
  `SUBJECT_TERMS` changes which probes are refused while every recorded mark stays
  identical.

That last one is the fifth arrival of ADR-018's hazard, which M03 named and left
owed. The judge half is still owed; this closes the adversarial half.

## Decision

**`instrument` becomes suite-conditional.** One field name, two shapes, chosen by
`suite`.

The alternative — a second top-level key, `adversarial_instrument` — was rejected.
A reader asking *what read this run* would have to know which suite they were
looking at before knowing where to look, and the entire value of `instrument` is
that the question has one answer in one place.

**`oneOf` alone is not enough**, and this is the part worth writing down. It would
accept an adversarial entry carrying the judge's fingerprints: schema-valid,
meaningless, and precisely the shape of a record naming an instrument it did not
use. So the schema pairs `oneOf` with an `allOf` conditional keyed on `suite`, and
a test plants both wrong pairings.

**`semantics_sha256` is pinned apart from `scorer_sha256`**, and digests the
*rendered membership* of the two mechanism sets rather than their source text. An
edit to the module's prose does not read as a policy change; adding a member does.
Same argument `rubric_axes_sha256` makes against `rubric_sha256`, one suite over.

**`guardrail_version` is required and is asked for as observed.** M03 recorded two
dev passes whose instrument blocks were byte-identical because the enforced policy
was not part of the instrument; the refusal rate differed and nothing in the
record said why. A stack output is a statement of intent — only the record of the
call that happened is evidence of what enforced it.

## Consequences

**A recorded entry cannot be written without naming its instrument.**
`run_adversarial --record` refuses without `--instrument-name` and
`--guardrail-version`, in the recorder rather than at schema validation, so the
message says which milestone's lesson it is repeating rather than naming a JSON
path.

**Each digest is tested by moving its own input.** M03 recorded three fields that
asserted distinctions they could not make — `user_turn_sha256`, `calibrated_by`,
`instrument.deterministic` — and every failure ran toward the flattering reading.
The only way to know is to plant, so each file-backed digest is checked two-sided
in a scratch copy of the tree: the named digest moves, and no other one does.

**A digest covering more than it claims is as wrong as one covering less.** It
makes every unrelated edit read as an instrument change and trains whoever reads
the row to ignore it — which is how a real instrument change gets waved through.

**The committed entries stay valid and keep their silence.** `m00b-adversarial`
and `m01-adversarial` carry no `instrument`, and back-filling one would record a
pin that did not exist at the time. Their instrument is recoverable from the
commit, and `tests/test_instrument_stability.py` is what re-derives what they
score today.

**At scale, replace with:** an instrument registry keyed by digest, so an entry
carries one identifier and the shape lives beside the instrument rather than in
the row. The interface already matches — `name` is that identifier, and every
digest here is what it would resolve to.

# B13 was wrong: the two history entries agree, and the real obligation is one M06b creates

`SPEC/06b` draft 3. **Zero model calls.** One file plus this body.

Draft 2 landed B13 as **blocking**: two committed history entries sharing SHA
`515ee709` and contradicting each other about whether four `m00b` passes are
earned, with *"a mark is discharged by silence"* as the finding. I repeated it
twice as a reason the milestone could not rest on its own rationale.

**Every fact in it is true and every conclusion drawn from them is false.**

## Why the entries agree

Entry B declares its instrument, and the instrument says what changed:

```
m00b-goldens.json           instrument: ABSENT       entitlement_source SCORED    15/25, 4 marks
m00b-judged-B-goldens.json  instrument.name: "B"
                            deterministic.deferred: ["entitlement_source"]        18/25, 0 marks
```

The marks' own stated reason is *"`entitlement_source` passed on a claim, not a
fact."* Under instrument B that assert **is not scored at all** (ADR-016), so the
four cases no longer pass *on* the fabrication — they pass on their other asserts.
Carrying the marks forward would assert that a pass depends on something the
instrument does not read. **Zero is the correct count for entry B.**

The missing `supersedes` is correct too. Under ADR-027 an `instrument` entry is a
**second reading, not a supersession**; the first entry stands, which is the whole
point of recording it separately.

And the field that explains this exists for precisely this purpose —
`evals/history/schema.json` on `deferred`: *"Assert kinds evaluated and NOT scored.
ADR-016 moved `entitlement_source` here, **which is exactly the kind of change a
bare digest would record without explaining**."*

## The attack B13 said was undefended is caught three ways

Planted against the real validators in a temp copy of `evals/history/` — a new entry
under instrument A's semantics with the four marks simply removed:

```
check_second_rows -> share sha 515ee70 and suite goldens and declare no difference --
                     not arm, not instrument, not supersedes. A reader cannot tell why
                     the second exists.
check_pins        -> not in pins.json ... add that line (three keys) only if the row is
                     a real measurement.
check_evidence    -> samples_from ... one run is one row.
```

`check_second_rows` is the decisive one: a second row under one SHA **must declare
why it exists**, and `tests/test_history_append_only.py:881` asserts that exact
message. There is no silence to be discharged by.

## What replaces it — and it is M06b's, not an inherited debt

Nothing carries a mark across a **re-adjudication**. The four marks are correctly
absent from entry B because the assert is deferred. The moment the trajectory eval
**un-defers** `entitlement_source` under a future instrument C, those same four
`m00b` cases must be scored on it again — and the control has no tool, so they must
fail. Nothing in the tree will raise that.

> **An instrument that un-defers an assert owes a re-adjudication of every mark
> recorded against that assert under an instrument that scored it.**

This milestone **creates** that gap rather than inheriting it, which is why it now
sits in the register with a "what a fix must survive" list instead of being parked
as someone else's three-key cleanup.

## The rationale is corrected in the same direction

Draft 1 said four `m00b` passes *"have been unearned since the control was
recorded."* Draft 2 said that was invalidated. **Both were wrong, in opposite
directions.** The true statement is sharper than either: under the live instrument
`entitlement_source` is deferred, so the control claiming a tool it does not have
costs it **nothing at all** and is recorded in no score. The trajectory eval is what
makes the assert scoreable again, at which point the control fails those cases
honestly instead of them quietly not counting.

That is a better argument for the milestone than the one it replaces, and it was
only reachable by disproving the finding.

## Why this is a correction and not a decision

No ADR. Nothing is decided here — a factual claim in a committed spec is withdrawn
and replaced by a measured one. The entry is **kept and marked withdrawn** rather
than deleted, in the register's own style, because a document that quietly drops a
claim is the failure mode it exists to catch.

## What this does not change

- The four open decisions stay open, and **B8 still blocks step 2**.
- No history entry is edited, no mark is added or removed, no comparator, threshold,
  golden case, instrument digest or recorded number moves.
- Claim 10 stays `—`.

## Verification

```
$ python -m pytest -q      2269 passed, 6 skipped     # spec change alone
$ python -m pytest -q      2272 passed, 6 skipped     # this PR, both files
                                                      # COLLECTED_FLOOR = 2255
$ python -m ruff check .   All checks passed!
$ python -c "from pave import twokey; print(twokey.triggered(['SPEC/06b-trajectory.md']))"
[]
```

Hermetic, no new dependency, no code path touched. The forged-entry plant ran
against a temp copy of `evals/history/`; the committed history was never written to.

## A note on where the wrong finding came from

B13 arrived from a seat review that read the two entries' scores and `supersedes`
fields and did not read `instrument.deterministic.deferred` — the one field whose
schema description names ADR-016 as the reason it exists. I carried it into a
committed spec without checking it myself, having already written in the same
document that a claim needs a plant. It took one to refute it.

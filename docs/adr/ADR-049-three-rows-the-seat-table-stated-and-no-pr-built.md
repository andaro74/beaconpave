# ADR-049: three rows the seat table stated and no PR built, and a deferral that could not be counted

**Status:** Proposed. **Zero model calls.**
**Seats:** Platform Engineering (the entrypoints, the demo obligation) · AI Quality
(the recorders, the ceilings, the register) · PM (milestone ordering)

M05 closes here. Three of the rows in SPEC/05's *"Seat sets, named"* table were
stated in the spec, reviewed by six seats across five rounds, and **built by no
PR** — `Makefile`, `tests/test_budget_derivation.py`, and
`docs/governance/recordings.json`. The first two were attributed to PR 1 and PR 3
and neither landed them; the third was PR 6's and is why this ADR exists at all.

A protection **stated and absent** is worse than one merely missing, because it
stops anyone looking for the real one. That sentence is CLAUDE.md's, it is
ADR-035's and ADR-037's finding twice over, and this is its fourth instance: the
document that enumerates which paths are guarded was, for three of its rows, a
description of an intention.

Every number below was measured on the closing tree at **2072 passed**.

## Decision 1 — `Makefile` takes `(platform-eng, ai-quality)`

Justified on `evals:` and `adversarial:` — the two `--record` entrypoints — and
above all on the `OBSERVATIONS` guard, whose whole job is to stop a bare
`make adversarial` from recording a second row over another milestone's evidence.
That is an append-only-history control that happens to live in a Makefile.

| mutation | result |
|---|---|
| delete the `OBSERVATIONS` guard line | **2072 passed**, zero keys |
| `check:` reduced to a bare echo | **2072 passed**, zero keys |

The second is not a hypothetical shape. This file's own header records that the
Makefile used to inline the steps and swallow pytest's exit code with a trailing
`|| echo`, which reported green over zero tests for the repository's entire life
so far. The file documenting the repository's longest-lived silent success was
editable by anyone, unattested, straight back into it.

**Not justified on `core:`**, which is a deploy gate whose pain AI Quality does not
feel. SPEC/05 draft 4 cited `core:` and the seat table corrected it; that
correction is preserved here rather than quietly widened.

## Decision 2 — `tests/test_budget_derivation.py` takes `(ai-quality, platform-eng)`

The file's own docstring, at `:124`, reads: *"`gates.budgets` is a two-key path; a
number that moves there without a written derivation is the change this rule exists
to make visible."*

The manifest half of that sentence became true at ADR-046, which put
`services/*/pave.manifest.yaml` on `(ai-quality, tool-owner)`. **The pin half never
did.** Deleting the file outright is **2059 passed, zero failures** — thirteen
tests vanish, and with them the only tie between the committed ceilings and the
committed measurement ADR-014's amendment derived them from.

This is exactly ADR-044's finding, in an instrument ADR-044's own audit did not
reach. The seats are taken from the file's docstring rather than chosen: *"AI
Quality (the ceilings — two-key) · Platform Engineering (the loop bound)"*. SPEC/05
draft 4 paired it with `tool-owner`, contradicting the file it was keying.

## Decision 3 — the demo-act register, its check, and the count that was free

`docs/governance/recordings.json` and `tests/test_demo_recordings.py` take
`(platform-eng, ai-quality)` **as a pair**. SPEC/05's row named only the data. The
test is here for ADR-043 decision 1's reason — an instrument and the thing it
measures are weakened together or not at all — and because data guarded with the
instrument left free is the precise asymmetry ADR-044 was written about.

### The deferral could not be counted, and M05 is where that mattered

M05 is the first close at which this register's teeth actually bit, and the
milestone **spent them**: Acts 0, 1 and 2 were all owed by M05, and all three were
re-deferred to M06 in one decision at the close.

That decision is legitimate. `test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed`
permits exactly it, and `test_an_act_owed_past_its_own_milestone_says_why` demands
a stated reason. What neither can do is **count**. Both ask one question — has the
current `owed_by` closed — so an act sliding one milestone at a time is green at
every step, and a fourth slide is indistinguishable from a first with the `why`
rewritten to sound new. Measured: re-deferring all three acts by one milestone was
**2072 passed, zero keys**.

Two things change:

1. **`deferred_from`** lists every milestone an act was owed by and passed
   unrecorded. `test_a_deferral_is_counted_and_named` **derives it rather than
   trusting it** where derivation is possible — a listed milestone must actually
   have closed, the milestone the act is owed by now must not be listed, and an act
   whose own owning milestone has closed unrecorded must list that milestone. Each
   entry must additionally be **named in `why`**, so the admission grows with the
   count instead of being restated at constant length.
2. **The file takes two keys**, so that growth happens in front of two seats.

**The residual is stated rather than asserted away.** Intermediate deferrals are
not derivable: the register records where an act is owed *now*, not the sequence of
places it used to be owed, so Act 0's `deferred_from` naming M05 rests on the diff
that wrote it. What makes that honest is the naming requirement and the two keys,
not the assertion.

### What is deliberately NOT keyed

`docs/governance/demo-script.md` is **not** on this rule, and that is a decision.
Dropping an act by editing the prose is already red —
`test_every_act_in_the_script_is_tracked` compares the script's acts against the
register in both directions — so the obligation cannot be deleted from the script.
What an unkeyed script still permits is rewriting an act's *content*, which is a
presentation change; keying it would put two seats on every wording fix. Recorded
as a residual so the next reader meets it here rather than deducing it.

`README.md` is **not** on this rule either, and the reason is measured:
`pave/tests/test_twokey.py:32` asserts that `pave/cli.py` and `README.md` together
collect nothing — this repository's only machine statement that an ordinary
contributor pays nothing to open a PR. SPEC/05 draft 4 put `README.md` on a rule
while moving guards off `pave/cli.py`, and the seat table refused it. PR 6's
obligation is carried by the register instead.

## The ratchet is extended in the same diff

`tests/test_twokey_seats.py` asserts `len(added) == 13` (was 10) and pins all four
new paths member by member in `ADR043_SEATS`. Without that, a rule added here would
sit outside the mechanism that stops the pin being emptied — which is how
`.github/CODEOWNERS` and `twokey.py` drifted twice (ADR-037). Adding a rule and
leaving it unratcheted would have reproduced this ADR's own subject inside the fix
for it, which is the fault SPEC/05 recorded PR 4b making with `COLLECTED_FLOOR`.

## At scale

Replace all three with code-owner review over the same path list, plus a policy
service that holds the obligation register and answers *"is this act overdue"* as a
query rather than a committed file. The register is already a list of typed records
with a derivable history, and the rules are already `(pattern, seats)` pairs — **at
scale, replace with that service; the interface already matches.**

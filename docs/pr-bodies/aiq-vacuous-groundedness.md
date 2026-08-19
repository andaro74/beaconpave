# AI Quality: a groundedness assert that cannot fail on an empty citation list

`cited_titles_in_fixture` computes `set(cited) - known`. On an **empty** citation
list that set is empty, so the assert passes — an answer that cites nothing
confabulates nothing, and clears a groundedness check by not attempting to be
grounded.

Owed to this seat since M02. It is landing now, in its own PR from `main`, because
M03 re-scores every committed answer with a judge and any score movement has to
have exactly one cause.

## Why it matters, in this repo's own evidence

SPEC/02 pre-registered the vacuity for `grounded-019` and marked the pass
unearned. M02 then found the same shape doing real damage on **`edge-025`**: PASS
in both arms, recorded as *unchanged* by the paired diff, while the control cited
`t001` and the tools arm cited nothing at all. M02's journal could only argue in
prose that the true loss count was 4 rather than the 3 the diff showed. Under this
change it is arithmetic.

## The obvious fix is wrong, and it was measured before being rejected

Making an empty citation list simply fail punishes the cases where citing nothing
is the **correct** answer — `grounded-019` and `entitlement-012` both ask about the
Harbor Bay Invitational, which is not in the catalog. Re-scoring the committed runs
under that version:

| run | current | naive "empty fails" | additive (this PR) |
|---|---|---|---|
| `m00b` | 18/25 | **17/25** | **18/25** |
| `m01` | 19/25 | **17/25** | **19/25** |
| `m02-control` (majority k=3) | 17/25 | 16/25 | **17/25** |
| `m02-tools` (majority k=3) | 16/25 | 14/25 | **15/25** |

The naive version moves **both comparator pins** and costs two correct answers, to
catch one wrong one. **The additive version moves neither pin.** A tightening that
moves every comparator is not a tightening; it is a re-scoring wearing one's
clothes, and `tests/test_instrument_stability.py` is what tells them apart — it
still asserts 18/25 and 19/25, unchanged, on this branch.

## What changed

Three intents, so three keys — rather than one key quietly redefined.

| the case expects | assert |
|---|---|
| specific titles | `must_cite: [t001, …]` *(unchanged, 18 cases)* |
| some title, unspecified | **`cites_at_least_one: true`** *(new — 5 cases)* |
| no title, because the subject is not in the catalog | **`cited_titles_empty: true`** *(new — 2 cases)* |

`cited_titles_in_fixture` is **not** redefined. It is referenced by all 25 cases
and by recorded history, and an assert key whose meaning changes underneath a
recorded score is ADR-016's hazard in its purest form. Each key now means exactly
what its name says.

`cites_at_least_one` goes to `brand-021`, `edge-025`, `grounded-017`,
`grounded-018`, `headroom-005`. `cited_titles_empty` goes to `entitlement-012` and
`grounded-019`. **The assignment is by the case's question, not by which runs
pass** — every one of those five asks about something that is in the catalog, and
both of those two ask about something that is not.

Two new contract tests stop the shape recurring:

- `test_no_case_can_pass_groundedness_by_citing_nothing` — every case must say
  which of the two things it expects, so a newly authored case cannot carry the
  vacuous shape alone
- `test_the_two_citation_expectations_are_never_both_asserted` — the two new keys
  are contradictory, and a case carrying both could never pass

## What it costs, measured

`edge-025` in the M02 tools arm, and `brand-021` in one control sample. Nothing
else, across all eight committed runs. The M02 paired diff becomes:

```
before   lost 3: blackout-008, recommend-013, recommend-014           net -1
after    lost 4: blackout-008, edge-025, recommend-013, recommend-014 net -2
```

## Two recorded unearned marks, resolved in opposite directions

`grounded-019`'s pass becomes **earned** — it now clears `cited_titles_empty`, a
check that can actually fail if the model invents a citation. `edge-025`'s becomes
a **FAIL** in the tools arm. The recorded history entries are untouched; history is
append-only, and 16/25 is what the instrument reported on the day.

The `m02` progression footnote is updated to carry the re-scored arm and to say
explicitly that the `m00b` and `m01` rows do not move.

## Not in this PR

No case is edited to accommodate an answer, no threshold moves, no baseline is
reset, and the headroom policy is untouched. `make check` is green: 902 passed.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: This closes a defect in the instrument that this seat has owed
since M02, and it closes it in the direction that makes the suite stricter: two
new assert keys are added and none is redefined, so no recorded score changes
meaning and the assert vocabulary stays one-key-one-meaning. The naive fix was
implemented and measured first, and rejected on evidence rather than taste — it
moved both comparator pins and failed two cases whose correct answer is to cite
nothing, which would have been a re-scoring of every historical row to catch a
single genuine defect. The additive form leaves `m00b` at 18/25 and `m01` at
19/25, both still pinned by tests/test_instrument_stability.py, and costs exactly
the two case-samples it was aimed at. Assert assignment was decided from each
case's question rather than from which runs pass, and the two new contract tests
mean a future case cannot reintroduce the vacuous shape unnoticed. It lands before
M03 measures anything so that any judged delta has exactly one cause.

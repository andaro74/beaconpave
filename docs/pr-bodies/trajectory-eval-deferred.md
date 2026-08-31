# The trajectory eval, landing deferred: the platform can now tell a call from a claim

M06b step 1. **Zero model calls.** `twokey.triggered` over the changed set → `[]`.

Since ADR-016 the golden suite has evaluated `entitlement_source` and scored it
nowhere, because it reads a field the model fills in and the ungoverned control
filled it in with `entitlement-check` — a tool it does not have — in 10 of 11 cases.
`SPEC/06b` B1 measured the twelve `expect_tool_before_answer` expectations that were
supposed to close that as **deletable in silence at the baseline**: nothing read
them.

This adds the assert that reads them, and lands it **deferred**.

## What it does

`evals/deterministic.py` gains `tool_before_answer`, dispatched from
`case["trajectory"]` and appended to `deferred` — the repo's ADVISORY for a
deterministic assert. It reads what the plane authorized, so **no value the model
can emit satisfies it**. That is the whole difference from `entitlement_source`.

**Absence is not satisfaction, and that is the design.** `SPEC/06b` B3 measured the
obvious implementation — filter to allowed steps, treat the empty result as "nothing
to contradict" — as green, zero-key and worthless. It also passes when the tool was
**refused**, because filtering leaves an empty list that falls into the same branch.
All three absences fail here, each with a distinguishable reason:

| trajectory | verdict |
|---|---|
| tool authorized | **pass** |
| a different tool authorized | fail — *"never called; authorized: ['catalog-search']"* |
| the tool **refused** | fail — *"was refused (policy) and never ran"* |
| empty | fail |
| absent entirely | fail — **`no-evidence:` …** |

## Reachability, proved against committed evidence

`SPEC/06b` asks that a plant be shown reachable, because a green plant that never
executes proves nothing. Measured through the real path — not a hand-built fixture —
against `milestones/M02/runs/m02-tools-1-trajectory.json`, a recorded run of 25 cases
and 35 authorized calls, every one `catalog-search`:

```
m00b           scored 18/25 | tool_before_answer evaluated 12, passing 0
m01            scored 19/25 | tool_before_answer evaluated 12, passing 0
m02-tools-1    scored 13/25 | tool_before_answer evaluated 12, passing 0
m02-control-1  scored 17/25 | tool_before_answer evaluated 12, passing 0
```

**Every scored number is exactly what it was, and the assert fails on every
committed run** — because `entitlement-check` has never been called anywhere. The
milestone's claim, evaluated for the first time. A trajectory assert that came back
green on that file would be measuring nothing.

## Deletability

Every new check deleted and re-run. None is silent.

| mutation | result |
|---|---|
| the B3 vacuous form (absent/empty/denied all pass) | **5 failed** |
| dispatch removed from `score_case` | **7 failed** |
| instrument visibility removed from `judged.py` | **1 failed** |

## `evals/judged.py` had to be taught about it

`deterministic_instrument()` walks `case["asserts"]`, and `trajectory` is a
**sibling** of `asserts`. The new kind would have contributed a verdict while
appearing in neither `scored` nor `deferred` — the silent instrument move that field
exists to prevent, in the field whose own docstring names ADR-016 deferring
`entitlement_source` as its motivating case.

`tests/test_judged_entry.py`'s exact-equality assertion on `deferred` **went red on
this diff**. That is the behaviour wanted, and it is updated to
`["entitlement_source", "tool_before_answer"]` and **kept as an equality** — a
containment check would have passed silently on exactly this change.

The two kinds are deferred for different reasons and `DEFERRED_ASSERTS` now carries
both: `entitlement_source` because it cannot be made to mean anything;
`tool_before_answer` because it means something already and is withheld.

## What this deliberately does NOT do

- **It does not choose the evidence source. Decision 3 stays open.** The assert reads
  whatever trajectory it is handed and reports `no-evidence` when handed none, so
  neither answer — response-derived or lake-derived — changes its semantics. Wiring
  it to `response["trajectory"]` today would have prejudged Decision 3 in the
  forgeable direction (B2, B9).
- **It does not score.** Deferred is Decision 11's safe branch: no comparator moves,
  no attested three-key diff, and no pressure toward the vacuous form B3 measures.
- **It cannot raise INFRA.** A deferred assert reaches no case verdict by
  construction, so the `no-evidence:` marker carries that distinction in a string
  until the diff that scores this assert routes it to INFRA rather than FAIL. That
  mapping is the easiest thing to lose between here and there, and a test pins it.
- **It does not touch B8.** `entitlement-check` is not deployed and the blackout
  vocabulary question is untouched.

## Un-deferring is not a one-line change

Recorded in `DEFERRED_ASSERTS` so the next reader cannot take it as one. Three things
land together or none do: the comparator movement, attested at three keys; the
re-adjudication `SPEC/06b` B13 names, since the four `m00b` marks were recorded
against `entitlement_source` under an instrument that scored it; and the
INFRA-not-FAIL mapping above.

## Verification

```
$ python -m pytest -q      2280 passed, 6 skipped     # code + spec
$ python -m pytest -q      2282 passed, 6 skipped     # this PR, with the body file
                                                      # COLLECTED_FLOOR = 2255
$ python -m ruff check .   All checks passed!
$ python -c "from pave import twokey; print(twokey.triggered([<changed>]))"
[]
```

Hermetic, no network, no new dependency. No `evals/history/` entry, no comparator, no
threshold, no golden case, no judge digest and no recorded number moved — the
re-scoring table above is the evidence, not an assurance. `cases.yaml` is untouched,
so `cases_sha256` is unchanged.

**No ADR.** No scope is cut and no decision is taken; the decisions this touches stay
open and are named above. `SPEC/06b`'s B3 entry is updated with what the fix survived,
per the milestone's third closing obligation.

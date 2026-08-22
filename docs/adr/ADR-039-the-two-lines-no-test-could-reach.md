# ADR-039: two lines on the guardrail-block path were executed by no test, and could not be, so they move to where they can be

**Status:** Proposed. A precondition for ADR-036 correction 1, written before it.
Costs **zero model calls**.
**Seats:** Platform Engineering (the gateway and the split it rests on) ·
Security / Red Team (`core/guardrail.py` names this seat in its docstring)

**One key.** `platform/gateway/core/guardrail.py`, `handler.py` and
`tests/test_gateway_core.py` carry no two-key rule — which ADR-037 recorded as an
open question for the Security and Platform Engineering seats and deliberately did
not pre-empt. This ADR does not pre-empt it either.

## Context

ADR-036 amendment 1, finding 7: `handler.py:450` reads
`outcome.guardrail.channel` on the guardrail-block return, `GuardrailOutcome` is a
frozen dataclass, and ADR-036's correction 1 renames that field. Measured with the
rename planted and every test a diligent implementer would update also updated:

```
FULL SUITE: guardrail.py renamed + tests updated, handler.py untouched
  1526 passed

does handler.py still work on the block path?
  AttributeError: 'GuardrailOutcome' object has no attribute 'channel'
```

A green gate over a gateway that crashes on the path G4 exists to evidence.

The seat's remedy was *"`handler.py`'s blocked-path return gets an executing test
before the rename lands."* **That remedy is impossible, and the reason is an
invariant.** `tests/` is in `HERMETIC_ROOTS` and `boto3` is in `AWS_SDK_ROOTS`, so
nothing under `tests/` may import `handler.py` — which is precisely why
`test_handler_wiring.py` parses the handler's source rather than running it. The
module also refuses to import without four environment variables and a non-empty
`TOOL_FUNCTIONS`, by design. Writing the executing test the seat asked for means
breaking G8.

So the finding is real and the proposed fix was not available. The fix that *is*
available is the one this module's own docstring already prescribes:

> *"Everything it decides lives in `core/`, which imports nothing... The split is
> the reason the gateway's decisions can be proven on a fresh clone with no AWS
> account, and it is **the first thing to defend if this file starts growing
> logic**."*

Two lines assembling a response dict do not look like logic. They were exactly
enough logic to hide a crash, and they sat on the far side of a hermetic boundary
where no test could reach them. **The untestable region is not a place to keep
even small decisions**, because "small" is judged by the person adding them and
"unreachable by tests" is judged by the import graph.

## Decision

`GuardrailOutcome.as_response_fields()` — a sibling to `as_record_fragment()`,
returning the guardrail-derived keys the gateway puts in a block response, with
the same when-set rule for the channel and `assessed` as a JSON list rather than
the dataclass's tuple. `handler.py` calls it.

**The point is not that a test now catches the rename.** It is that there is
nothing left to forget: the method travels with the field, so a rename updates the
only reader automatically. Verified against a planted rename —

```
handler blocked-path expression -> {'decision': 'blocked',
                                    'assessed': ['TOPIC:entitlement-circumvention'],
                                    'channels': ['tool_output']}
the OLD handler line             -> AttributeError: no attribute 'channel'
```

A test that catches a crash is worth less than a shape that cannot crash.

### The source assertion stays, beside the executing ones

`test_the_handler_reads_these_fields_from_the_dataclass_and_not_by_hand` asserts
that `handler.py` calls `as_response_fields()` and does **not** read
`outcome.guardrail.channel` directly. Without it, the executing tests protect
nothing the day somebody assembles the dict inline again: the rename would break
the handler again and the hermetic suite would stay green again. Two checks,
because neither can see what the other sees — the same argument
`test_handler_wiring.py` makes for existing there at all.

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | the response shape is **byte-identical** before and after: `assessed` always, `channel` only when set | a key appears or vanishes — then this is a behaviour change wearing a refactor's clothes, and it belongs in ADR-036 with the rename it serves |
| 2 | with ADR-036's rename planted, `handler.py`'s block expression **evaluates**, and the pre-ADR-039 line raises `AttributeError` on the same input | it still raises — then the logic did not actually move and the crash was relocated rather than removed |
| 3 | no instrument digest moves, so no bump: `core/guardrail.py` is in none of the six, which is ADR-036 correction 2's finding and is not fixed here | one moves — then the digest coverage is not what correction 2 measured |
| 4 | `tests/test_hermeticity.py` stays green, because nothing new imports `boto3` | it fails — then the fix broke the invariant that made the fix necessary |

## Consequences

- ADR-036's correction 1 can rename the field without a silent crash on the block
  path. That was the precondition; this discharges it.
- The gateway response keys now have one producer with executing tests, and
  `assessed` is guaranteed a list — a tuple survives an equality assertion and
  does not survive `json.dumps`, which is the difference between a green test and
  a 500 on the refusal path.
- Nothing is re-scored, no threshold or baseline moves, no guardrail is touched.

## What this ADR does not do

It does not rename anything, does not add a channel, does not touch
`observation_from_record`, and does not decide whether `core/guardrail.py` belongs
in an instrument digest or on a two-key path — both of which are open and belong
to the Security and Platform Engineering seats.

It also does not sweep the rest of `handler.py` for logic that should live in
`core/`. That is worth doing and it is not this PR: a precondition that grows into
an audit stops being landable before the thing it unblocks.

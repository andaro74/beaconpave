# ADR-057: a record that says the tool ran, not merely that it was allowed

**Status:** Accepted. **Zero model calls.**
**Instrument:** registers `m04-F` as a **precondition** for the change (ADR-038).
**Seats:** Platform Engineering · Security (the capture path and the schema) ·
Tool Owner (`toolplane.py`) · Security + ADR (`quality/adversarial/instruments.json`).
Executes `SPEC/06b` Decision 9 / B9.

The audit record's `tool` fragment required `id, round, decision, mechanism`, with
`additionalProperties: false`. **No field meant "this tool ran."** `decision:
allowed` says the plane permitted the call; it says nothing about whether the call
happened.

That mattered because something writes allowed records for calls it does not make.

## What was open

`handler._tool_probe`, whose own docstring reads *"an allowed probe still calls
nothing"*, builds a full audit record and returns `"executed": False` — **into the
response only**. The record carried no trace of it. And the record could land on the
key a real call would use:

```
probe-path key : 2026-08-31/highlights-agent/concise-022-m02-tools-1.001.json
model-path key : 2026-08-31/highlights-agent/concise-022-m02-tools-1.001.json
IDENTICAL      : True
```

`ToolPlane.Turn.authorize()` does `self.calls += 1` **before** returning, so both
`_tool_probe` (`seq=turn.calls`) and `toolloop` (`seq = turn.calls`) hand `1` to
`record_key` for the first call. `request_id` is `event.get("request_id")` —
caller-supplied — and `probe_id` is optional, so the key is choosable and the record
carries no probe marker.

So a trajectory derived from the lake by counting `decision: allowed` records
credited calls that never ran. That is the honest-witness fix `SPEC/06b` B2 points
at, forgeable at its source.

**It is inert today only because `entitlement-check` is undeployed** — the probe
path refuses it with `ROUTING`. M06b's step 2 removes that, which is why Security's
position was that the tool must not deploy first.

## What was decided

**`tool.executed`, optional, meaning the tool function was reached.**

- **Optional, and absent means UNKNOWN — never false.** Every record written before
  this field lacks it, and `additionalProperties: false` means a required field
  would stop the schema validating any of them. A reader must treat absence as
  evidence it does not have, which is the same reading `tool_before_answer` already
  gives a missing trajectory.
- **Omitted rather than defaulted** in `as_record_fragment`. A fragment built by
  code that does not know is making no claim; a `False` it did not mean would be
  one.
- **A parameter, not a property of the decision.** A `ToolDecision` knows what the
  plane permitted; only the caller knows whether the tool was then reached.
  `_tool_probe` passes `False` on an **allowed** decision — the exact combination
  that was unrepresentable.
- **Tracked where the tool is reached, not inferred afterwards.** `executed = not
  reply.unreachable`, set immediately after `call_tool` returns. Everything below
  that line can turn the decision to `denied`, and none of it un-runs the tool.

That last point is the subtle one. **Execution is not derivable from the payload or
from the final decision.** A call whose *result* fails the output contract carries
`payload=None` and `decision: denied` — and it ran. Reading execution off either
would report it as never having happened, and a trajectory built that way would
under-credit precisely the calls whose results were suppressed.

**And the field is consumed in the same change.** `evals/deterministic.py`'s
`tool_before_answer` now requires `executed is True` rather than crediting
`decision == "allowed"` — otherwise this ADR would add a witness nothing reads,
which is the defect class this milestone's register exists to catch. The failure
message still reports what was *authorized*, because the pass condition and the
diagnostic are different questions: narrowing the message to executed steps turned
`authorized: ['catalog-search']` into `authorized: nothing` and cost a reader the
ability to tell a wrong tool from no tools. A test caught that.

## What it survived

Seven mutations, each caught by the test written for it, none silent:

| mutation | caught by |
|---|---|
| probe claims the tool **ran** | `test_the_probe_path_records_that_it_ran_nothing` |
| probe says nothing about execution | same |
| real path reports the **decision**, not the call | `test_the_model_path_records_execution_from_the_call_...` |
| loop credits execution from the plane's permission | `test_a_tool_the_platform_could_not_reach_did_not_execute` |
| loop reads execution off the payload | `test_a_call_that_ran_and_was_then_rejected_still_counts_as_executed` |
| fragment defaults `executed` to `False` | `test_the_fragment_says_nothing_about_execution_unless_it_is_told` |
| trajectory stops reporting execution | 4 failures |

The probe-path assertions are on the **source**, not on execution: `handler.py`
holds the boto3 clients and is outside the hermetic surface (ADR-039), which is why
`tests/test_handler_wiring.py` exists at all — it was written after four seats
planted weakenings there and watched `make check` stay green.

## The instrument

`core/toolloop.py` feeds `guardrail_sha256`, so this moves it. **`m04-F` is
registered beside `m04-E`, which is left standing** (ADR-034): editing a registered
row would silently redefine every entry citing the name. Measured: `guardrail_sha256`
is the **only** digest that moves; `capture_sha256` does not, because `core/audit.py`
is untouched — the schema is a separate file and `build_record` passes `tool`
through.

Registration is a **precondition**, not a successor (ADR-038). No suite is re-scored
under `m04-F` here.

## What this does not do

**It does not fix the `seq` collision**, and that is deliberate. With the witness in
place a colliding probe record makes a lake-derived trajectory read `executed:
false` — a **false negative**. Wrong, but it fails closed, and folding it into a diff
that already carries an instrument bump would widen the hardest change in this
milestone. Registered as its own entry.

**It does not deploy `entitlement-check`.** `TOOL_FUNCTIONS` is still
`['catalog-search']` and the tool still has no implementation. With B8 (ADR-056) and
this, both of step 2's recorded blockers are closed; what remains is building it.

**It does not make `executed` required**, and does not backfill it.

**It does not score anything.** `tool_before_answer` stays deferred, every
comparator is unmoved — m00b 18/25, m01 19/25, m02-tools-1 13/25, m02-control-1
17/25 — and no history entry is written.

At scale the execution witness is not a boolean the gateway asserts about itself but
a result digest the tool signs, so the record evidences *what* ran rather than that
something did; and `_tool_probe` writes into a namespace no derived trajectory reads
rather than relying on a field to disambiguate it. The interface already matches:
the fragment is built in one place, per call, and the key already carries a `seq`
that could be partitioned by witness.

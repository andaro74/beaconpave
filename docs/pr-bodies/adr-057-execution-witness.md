# A record that says the tool ran, not merely that it was allowed

ADR-057, executing `SPEC/06b` Decision 9 / B9. **Zero model calls.** Closes the
second and last recorded blocker on M06b's step 2.

## The hole

The audit `tool` fragment required `id, round, decision, mechanism`, with
`additionalProperties: false`. **No field meant "this tool ran."**

`handler._tool_probe` — docstring: *"an allowed probe still calls nothing"* — builds
a full `decision: allowed` record and returns `"executed": False` **into the response
only**. And the two paths collide on the key:

```
probe-path key : 2026-08-31/highlights-agent/concise-022-m02-tools-1.001.json
model-path key : 2026-08-31/highlights-agent/concise-022-m02-tools-1.001.json
IDENTICAL      : True
```

`Turn.authorize()` does `self.calls += 1` **before** returning, so `_tool_probe`
(`seq=turn.calls`) and `toolloop` (`seq = turn.calls`) both hand `1` to `record_key`.
`request_id` is caller-supplied; `probe_id` is optional.

So the honest-witness fix B2 points at — derive the trajectory from the lake — was
forgeable at its source. Inert today only because `entitlement-check` is undeployed;
step 2 removes that, which is why Security said the tool must not deploy first.

## The fix

**`tool.executed`, optional, meaning the tool function was reached.**

- **Optional; absent means UNKNOWN, never false.** Every record predating the field
  lacks it, and `additionalProperties: false` means a required field would stop the
  schema validating any of them.
- **Omitted rather than defaulted** in `as_record_fragment` — code that does not
  know makes no claim.
- **A parameter, not a property of the decision.** `_tool_probe` passes `False` on
  an **allowed** decision: the combination that was unrepresentable.
- **Tracked where the tool is reached** — `executed = not reply.unreachable`,
  immediately after `call_tool`. Everything below that line can flip the decision to
  `denied`, and none of it un-runs the tool.

That last point is the one worth reading twice. **Execution is derivable from
neither the payload nor the final decision.** A call whose *result* fails the output
contract carries `payload=None` and `decision: denied` — and it ran. Either
shortcut would under-credit exactly the calls whose results were suppressed.

**The witness is consumed in the same diff.** `tool_before_answer` now requires
`executed is True` instead of crediting `decision == "allowed"` — otherwise this
would add a witness nothing reads, which is the defect class the register exists to
catch.

## What it survived

Seven mutations, each caught by the test written for it, **none silent**:

| mutation | caught by |
|---|---|
| probe claims the tool **ran** | `test_the_probe_path_records_that_it_ran_nothing` |
| probe says nothing about execution | same |
| real path reports the **decision**, not the call | `test_the_model_path_records_execution_from_the_call…` |
| loop credits execution from the plane's permission | `test_a_tool_the_platform_could_not_reach_did_not_execute` |
| loop reads execution off the payload | `test_a_call_that_ran_and_was_then_rejected_still_counts_as_executed` |
| fragment defaults `executed` to `False` | `test_the_fragment_says_nothing_about_execution_unless_it_is_told` |
| trajectory stops reporting execution | 4 failures |

Probe-path assertions read the **source**: `handler.py` holds the boto3 clients and
is outside the hermetic surface (ADR-039), which is why `test_handler_wiring.py`
exists — it was written after four seats planted weakenings there and watched
`make check` stay green.

**One regression this caught in its own fix.** Narrowing the assert to executed
steps also narrowed its failure message, turning `authorized: ['catalog-search']`
into `authorized: nothing` — costing a reader the ability to tell a wrong tool from
no tools. `test_a_trajectory_without_the_tool_names_what_was_authorized_instead`
went red on it. The pass condition and the diagnostic are now separate: the first
requires the witness, the second reports everything authorized.

## The instrument

`core/toolloop.py` feeds `guardrail_sha256`. **`m04-F` is registered beside
`m04-E`, which is left standing** — editing a registered row would silently redefine
every entry citing the name (ADR-034). Registration is a **precondition**, not a
successor (ADR-038); no suite is re-scored under it here.

Measured: `guardrail_sha256` is the **only** digest that moves. `capture_sha256` does
not — `core/audit.py` is untouched, because the schema is a separate file and
`build_record` passes `tool` through. The registry diff is **15 insertions, 0
deletions**, verified append-only with pre-existing rows compared field by field.

## What this does not do

- **It does not fix the `seq` collision**, deliberately. With the witness present a
  colliding probe record reads `executed: false` — a false negative, which fails
  closed. Its own entry rather than a widening of the diff carrying an instrument
  bump.
- **It does not deploy `entitlement-check`.** `TOOL_FUNCTIONS` is still
  `['catalog-search']` and the tool has no implementation. With ADR-056, both of
  step 2's recorded blockers are now closed; what remains is building it.
- **It does not score.** `tool_before_answer` stays deferred and every comparator is
  unmoved: **m00b 18/25, m01 19/25, m02-tools-1 13/25, m02-control-1 17/25** — the
  re-scoring is the evidence, not an assurance.
- **It does not make `executed` required** and does not backfill it.

## Verification

```
$ python -m pytest -q      2304 passed, 6 skipped     # COLLECTED_FLOOR = 2255
$ python -m ruff check .   All checks passed!
```

Hermetic, no network, no new dependency, no `evals/history/` entry, no threshold, no
golden case, no recorded number moved. `cases.yaml` untouched, so `cases_sha256` is
unchanged.

Two-Key-Disposition: platform-eng
Two-Key-Disposition: security
Two-Key-Disposition: tool-owner
Two-Key-Rationale: This changes the gateway's own record contract, which is why it
  collects the capture path, the tool plane and an instrument registration. The
  audit fragment could not distinguish a call the plane permitted from one that
  happened, while a code path that explicitly runs nothing wrote allowed records at
  a key it could share with a real call, so the honest evidence source for a
  trajectory credited calls that never ran. The new field is additive and optional
  in both directions that matter: absent stays UNKNOWN so no record written before
  it is retroactively asserted about, and it is omitted rather than defaulted so
  code that does not know makes no claim. Execution is captured at the point the
  tool is reached rather than inferred from the payload or the final decision,
  because a call whose result was rejected after it ran carries neither and would
  otherwise be reported as never having happened. Seven weakenings were planted
  against the new guards and all seven went red, including the two that would have
  reinstated the original hole. The instrument moves, so m04-F is registered as a
  precondition beside m04-E rather than m04-E being edited, and guardrail_sha256 is
  the only digest that differs. Nothing is scored, no comparator moves, and the
  four committed runs re-score to exactly what they scored before.

ADR: docs/adr/ADR-057-a-record-that-says-the-tool-ran.md

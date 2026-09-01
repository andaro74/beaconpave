# ADR-058: the second tool deploys, and the measured system grows with it

**Status:** Accepted. **Zero model calls. Nothing is deployed to AWS.**
**Seats:** Security · AI Quality (`platform/infra/lib/gateway-stack.ts`, with this
ADR) · Platform Engineering · Security (`tests/test_gateway_run_parity.py`).
Executes `SPEC/06b` step 2's remaining half.

`entitlement-check` has been registered in `platform/registry/tools.yaml`,
permitted by a generated Cedar policy, and shipped to the model inside
`tools.contracts.json` since M02. `TOOL_FUNCTIONS` named one tool. The gap closed
here is the one `tests/test_tool_servers.py` found the class of two PRs ago: a tool
the platform advertises and cannot call.

## What was decided

### 1. Both tool functions are built by one constructor

`deployTool(constructId, toolId)` creates the function, attaches the explicit
model-invoke `Deny`, and grants the gateway — and only the gateway —
`lambda:InvokeFunction` on it.

The two properties are not per-tool decisions. They are what a tool *is* here, and
a second function written by copying the first is exactly where one of them is left
out: the Security seat planted that omission during the `SPEC/06b` review and it is
the reason this is a function rather than a paste. `tests/test_tool_plane_iam.py`
iterates the routing table rather than naming a tool, so a function built any other
way still has to satisfy both. **This makes the common path correct; it does not
make the check unnecessary**, and the audit below plants the omission anyway.

The refactor is behaviour-preserving by construction, and measured: the synthesized
template moved **116 insertions, 0 deletions**. Not one existing resource changed.

### 2. The deployment defines no clock

`BEACONPAVE_CLOCK` is set nowhere in the stack, deliberately. It is an override, and
an override set in the stack is a default: the deployed tool would answer against an
instant no arm file names and `module_constants` cannot see, so
`test_the_evaluation_clock_is_the_same_everywhere_it_appears` would go on agreeing
with itself while the deployed instrument had moved. ADR-021 says no arm may define
a second clock; a stack that pinned one would define a second clock in the one file
that rule cannot read.

`test_the_deployment_does_not_define_a_clock_of_its_own` is the half of that rule
that lives outside Python. A drill needing another instant sets the override at
invocation, deliberately, and does not leave it behind.

### 3. `TOOL_SPECS_SHA256` moves, and that is declared an ADR-021 event

From `1912657b…dc15c4a` to `0267054b…3388205`.

**Nothing about `catalog-search` changed.** The digest is taken over the *routed*
set, so routing a second tool adds a second schema and description to what the model
reads, and the hash moves by construction. That is the point of the pin: the
model-facing surface is larger than it was, and **no comparison may span this
commit.** Both arms of every M06b comparison run on one side of this line, and the
progression row says which side.

This is the pin working rather than the pin being in the way. `TOOL_SYSTEM_SHA256`
does not move; the prompt is unchanged.

### 4. The routing table's expected contents are derived, not listed

`test_the_routing_table_is_parsed_from_the_gateways_own_environment` closed with
`== {"catalog-search"}` — the literal its own docstring forbids, three lines under
the sentence forbidding it. It is now `registered ∧ has a server`, and both halves
earn their keep in opposite directions: a registered, implemented tool missing from
the table is the gap this milestone closed; a routed tool with no server is a route
to a 500 that Cedar permits.

`test_hermeticity.py`'s `HERMETIC_ROOTS` takes `tools/` for the same reason it takes
`pave/` — the class rather than one member.

## Why this could only land now

ADR-057 recorded that `handler._tool_probe` writes an **allowed** record for a call
it does not make, on a key a real call could use, *"inert today only because
`entitlement-check` is undeployed — the probe path refuses it with `ROUTING`. M06b's
step 2 removes that, which is why Security's position was that the tool must not
deploy first."*

This commit removes it. It is safe to remove because the witness landed first:
`tool.executed` means a lake-derived trajectory reads a colliding probe record as
`executed: false` — a false **negative**. The `seq` collision (`SPEC/06b` B14) is
still open and still deliberately unfixed, and it still fails closed.

The sequencing Security asked for is what happened: B8 (ADR-056), then the witness
(ADR-057), then the implementation, then the transport, then this.

**No probe in the frozen corpus names `entitlement-check` as a tool**; the
entitlement probes attack the *topic*. So no recorded probe verdict changes meaning
under this commit.

## What it survived

Ten mutations of the deployed stack, each re-synthesized and re-recorded, none
silent. The full table is in the pull request; the two that matter most:

| mutation | caught by |
|---|---|
| the second tool's role loses the model-invoke `Deny` (**G1**) | `test_a_tool_function_reaches_no_model` |
| the second tool is deployed and left out of `TOOL_FUNCTIONS` | `test_the_routing_table_is_parsed_from_the_gateways_own_environment` |

The first is the plant this PR was written expecting. `test_a_tool_function_reaches_
no_model` iterates routed tools, so it covered the new function the moment the
routing table named it — which is why the check was written that way in M02 and why
it must not be rewritten to name tools.

## What this does not do

- **It deploys nothing to AWS.** `cdk synth` runs locally and environment-agnostic;
  the committed snapshot is what the assertions read (ADR-017), and `make check`
  stays hermetic (G8).
- **It does not build `publish-highlight`**, which remains registered, gated by
  `cedar.GATED_CONSEQUENCES`, declared in `UNBUILT`, and whose deployment is refused
  with the scope of that refusal open (ADR-055).
- **It scores nothing.** No comparator, threshold, golden case, history entry or
  instrument digest moves. `entitlement_source` stays in `DEFERRED_ASSERTS`
  (ADR-016) and `tool_before_answer` stays deferred; whether un-deferring may move a
  published comparator is `SPEC/06b` Decision 11 and is not mine.
- **It does not close B10, B11 or B14.**

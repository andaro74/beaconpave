# The second tool becomes reachable, and the model-facing surface grows with it

M06b step 2, final half. **Zero model calls. Nothing is deployed to AWS** — `cdk
synth` runs locally and environment-agnostic, and the assertions read the committed
snapshot (ADR-017). Recorded as **ADR-058**.

`entitlement-check` has been registered, permitted by a generated Cedar policy, and
shipped to the model inside `tools.contracts.json` since M02. `TOOL_FUNCTIONS` named
one tool. This routes it.

## What lands

**One constructor for both tool functions.** `deployTool(constructId, toolId)`
creates the function, attaches the explicit model-invoke `Deny`, and grants the
gateway — and only the gateway — `lambda:InvokeFunction` on it.

Those two properties are not per-tool decisions; they are what a tool *is* here, and
a second function written by copying the first is exactly where one of them is left
out. `tests/test_tool_plane_iam.py` iterates the routing table rather than naming a
tool, so a function built any other way still has to satisfy both — this makes the
common path correct, it does not make the check unnecessary, and the audit plants
the omission anyway.

The refactor is behaviour-preserving, and measured rather than asserted: the
synthesized template moved **116 insertions, 0 deletions**. Not one existing
resource changed.

**The deployment defines no clock.** `BEACONPAVE_CLOCK` is set nowhere, and
`test_the_deployment_does_not_define_a_clock_of_its_own` is what keeps that true. An
override set in the stack is a default: the deployed tool would answer against an
instant no arm file names and `module_constants` cannot see, so the ADR-021 parity
loop would go on agreeing with itself while the deployed instrument had moved. A
drill needing another instant sets it at invocation and does not leave it behind.

## `TOOL_SPECS_SHA256` moves, and that is the pin working

`1912657b…dc15c4a` → `0267054b…3388205`.

**Nothing about `catalog-search` changed.** The digest is taken over the *routed*
set, so routing a second tool adds a second description and schema to what the model
reads and the hash moves by construction. That is an **ADR-021 event**: the system
under measurement is larger than it was, and **no comparison may span this commit.**
Both arms of every M06b comparison run on one side of this line.

`TOOL_SYSTEM_SHA256` does not move. The prompt is unchanged.

## A literal the test's own docstring forbade

`test_the_routing_table_is_parsed_from_the_gateways_own_environment` closed with
`== {"catalog-search"}`, three lines under its own sentence *"a list of tool ids in
this file would be a second copy, and the failure mode of a second copy is that it
stays green while the first one moves."* It went red at M06b for exactly that
reason.

It is derived now — `registered ∧ has a server` — and both halves earn their keep in
opposite directions: a registered, implemented tool missing from the table is the
gap this milestone closed; a routed tool with no server is a route to a 500 that
Cedar permits. `HERMETIC_ROOTS` takes `tools/` for the same reason it takes `pave/`.

## Why this could only land now

ADR-057 recorded that `handler._tool_probe` writes an **allowed** record for a call
it never makes, on a key a real call could use, *"inert today only because
`entitlement-check` is undeployed — the probe path refuses it with `ROUTING`. M06b's
step 2 removes that, which is why Security's position was that the tool must not
deploy first."*

This commit removes it, and it is safe because the witness landed first: with
`tool.executed`, a colliding probe record makes a lake-derived trajectory read
`executed: false` — a false **negative**, wrong but closed. B14 is still open and
still deliberately unfixed.

The order Security asked for is the order that happened: B8 (ADR-056) → the witness
(ADR-057) → the implementation → the transport → this.

**No probe in the frozen corpus names `entitlement-check` as a tool.** The
entitlement probes attack the *topic*, so no recorded probe verdict changes meaning
under this commit.

## Deletability

Ten mutations of the deployed stack, each **re-synthesized and re-recorded**, ten
caught, none silent:

| mutation | caught by |
|---|---|
| **the 2nd tool's role loses the model-invoke `Deny` (G1)** | `test_a_tool_function_reaches_no_model` (+1) |
| the 2nd tool loses `grantInvoke` | `test_the_gateway_actually_holds_the_grant` |
| the 2nd tool is deployed and left out of `TOOL_FUNCTIONS` | `test_the_routing_table_is_parsed…` (+1) |
| the gateway is granted invoke by wildcard instead | `test_no_invoke_grant_is_a_wildcard` (+1) |
| the service role is granted invoke on the 2nd tool | `test_only_the_gateways_own_role_may_invoke_a_tool` |
| the stack sets `BEACONPAVE_CLOCK` | `test_the_deployment_does_not_define_a_clock_of_its_own` |
| the 2nd tool gets a public function URL | `test_no_function_in_the_stack_has_a_public_url` (+1) |
| an unregistered tool is added to the routing table | `test_every_routed_tool_is_in_the_registry` (+2) |
| `TOOL_SPECS_SHA256` left at its pre-deploy value | `test_the_tool_specs_the_model_reads_are_hash_pinned` |
| the committed snapshot left stale | `pave.cli infra snapshot --check` (rc=1) |

The first row is the plant this PR was written expecting — it is where the Security
seat's weakening landed during the `SPEC/06b` review. `test_a_tool_function_reaches_no_model`
covered the new function the moment the routing table named it, because it iterates
routed tools rather than naming one. That is why it must not be rewritten to name
tools.

Worth stating: the first version of this audit harness restored files with `git
checkout --`, which discards the uncommitted work the audit exists to test. The
plant-dead guard caught the missing anchor immediately. It backs up working copies
to a temp directory now.

## What this does not do

- **It deploys nothing to AWS.** No credentials, no account, no region.
- **It does not build `publish-highlight`**, which stays registered, gated by
  `cedar.GATED_CONSEQUENCES`, declared in `UNBUILT`, and refused with the scope of
  that refusal open (ADR-055).
- **It scores nothing.** No comparator, threshold, golden case, history entry or
  instrument digest moves. `entitlement_source` and `tool_before_answer` stay
  deferred; whether un-deferring may move a published comparator is Decision 11 and
  is not mine.
- **It does not close B10, B11 or B14.**

## Verification

```
$ cd platform/infra && npx cdk synth --quiet      # local bundling, no Docker, no AWS
$ python -m pave.cli infra snapshot --check       synth snapshot current: 2 template(s)
$ python -m pytest -q                             2369 passed, 6 skipped   # was 2358
$ python -m ruff check .                          All checks passed!
```

Hermetic, no network, no new dependency.

Two-Key-Disposition: security
Two-Key-Disposition: ai-quality
Two-Key-Disposition: platform-eng
Two-Key-ADR: docs/adr/ADR-058-the-second-tool-deploys-and-the-measured-system-grows.md
Two-Key-Rationale: Two rules fire. gateway-stack.ts takes security and ai-quality
  with an ADR, and this is the change that rule was written for: a second tool
  function is where the model-invoke Deny gets left out, so both tool functions are
  built by one constructor that attaches the Deny and the narrow grantInvoke, and
  the omission was planted anyway and caught by the routed-tool iteration in
  test_tool_plane_iam.py rather than by the constructor. The ai-quality key is
  load-bearing here for a separate reason: routing a second tool moves
  TOOL_SPECS_SHA256, because that digest is taken over the routed set, so the
  model-facing surface grew without a word of the prompt changing. That is an
  ADR-021 event and it means no comparison may span this commit; both arms of every
  M06b comparison run on one side of it. Nothing about catalog-search changed and
  TOOL_SYSTEM_SHA256 does not move. The parity test takes platform-eng and security
  and the change to it is that pin move plus one added assertion, that the
  synthesized stack sets no clock override, which is a widening: a clock pinned in
  the CDK would be a second definition of the evaluation clock in the one file the
  parity loop cannot read. Planted and caught. No threshold, baseline, golden case,
  comparator or instrument digest moves, nothing is deployed to AWS, and the suite
  is hermetic.

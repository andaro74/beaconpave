# The checker learns the four routes it was not looking at

Discharges the Security seat's blocking findings from the ADR-058 review.
**Zero model calls. No infrastructure changes** — `gateway-stack.ts` and the
committed snapshot are untouched; this is entirely the checker that reads them.
Recorded as **ADR-059**.

## Eight holes, reproduced before anything was fixed

The seat round reported eight ways to reach a model or a tool that the G1/G3
checker does not look for. I planted all eight against the committed snapshot on
`main` first, rather than taking the report on trust:

```
baseline: 74 passed
SILENT H1  sts:AssumeRole onto the gateway role          74 passed
SILENT H2  the Deny scoped to one unused model ARN       74 passed
SILENT H3  the Deny given a Condition that never matches 74 passed
SILENT H4  Allow by NotAction on the tool role           74 passed
SILENT H5  policy attached by Fn::Sub in Roles           74 passed
SILENT H6  invoke granted through Fn::ImportValue        74 passed
SILENT H7  EventSourceMapping onto the tool function     74 passed
SILENT H8  invoke granted on an Alias of the tool        74 passed
8 of 8 holes are REAL on this commit
```

**None was introduced by ADR-058.** They applied to `catalog-search` from M02.
What changed is the cost: a second tool doubles the surface, and ADR-058 recorded
them as owed before the M06b scored run rather than fixing them inside a diff that
already carried a pin move.

## What lands

**A Deny is not a boolean.** `model_invoke_denials` read `Effect` and the action
list and nothing else, so a Deny scoped to one unused model ARN and a Deny gated on
a `Condition` that never matches both counted as full coverage. They stop counting
as denials at the source, so the existing assertion goes red, and
`test_every_deny_is_in_force_for_every_model` states the property directly. A
`Condition` is refused rather than analysed — deciding whether one can ever be true
is a policy-simulator problem, and a checker that guessed would be wrong in the
direction that passes.

**`NotAction` is the inverse of the list and was read as an absent one.**
`{"Effect": "Allow", "NotAction": ["s3:GetObject"], "Resource": "*"}` permits every
model action while naming none; `statement.get("Action")` returns `None`. It needs
no escape hatch — `notActions` is a plain `iam.PolicyStatement` field.

**A policy attaches through any reference form.** `Roles: [{"Fn::Sub": "${SomeRole}"}]`
attached to nobody as far as every assertion could tell, with an unrestricted
`bedrock:InvokeModel` Allow inside it. `Fn::Sub` is resolved now, skipping
pseudo-parameters by the `::` that separates `${AWS::Partition}` from `${SomeRole}`
— so there is no list of names to keep current.

**G1 has a transitive path carrying no model action at all.** The tool's Deny is an
*identity* policy; `sts:AssumeRole` produces a different session with the gateway
role's Allow. One CDK line, no escape hatch. The rule adopted is blunt on purpose —
**no role in this stack may assume another role in it, and no trust policy may name
an identity from this stack** — because a narrower rule would have to decide which
crossings are safe, which is the reasoning that produced the hole. Both halves are
asserted, so a trust policy widened ahead of a grant fails on its own.

**An event source is a fourth route and it needs no permission.** This file opened
by enumerating *"three separate things to be false here."* An
`AWS::Lambda::EventSourceMapping` drives the function through a poller using the
**function's own execution role**: no invoke grant to find, no
`AWS::Lambda::Permission` to flag. A queue with an open send policy in front of it
is a route to the tool with no plane, no Cedar, no audit record. The docstring is
corrected to four, which matters as much as the assertion — a list that says three
is how the next reader stops looking.

**An invoke grant may name an alias, and an unresolvable target is not an absent
one.** `alias.grantInvoke(role)` emits `{"Ref": "<Alias>"}`, which is not an
`AWS::Lambda::Function` logical id, so the grant dropped out of the intersection and
the assertion went on naming the gateway as sole invoker — worse when the grant
lands on a role the stack already has, since the new-role tripwire fires on a
stranger and says nothing about this. And `{"Fn::ImportValue": "SomeExport"}` fell
out of `invoke_targets` *and* the wildcard detector at once, which is the "two blind
checks agreeing is not coverage" condition the module already warns about one
function up. Same answer as `unreadable_managed_policies`: refuse the shape.

## Deletability

Every hole re-planted against the fixed checker — **eight for eight caught**. Then
the inverse audit, which is the one that matters: **each new guard deleted and its
hole re-planted**, to prove the guard is the thing catching it rather than
something incidental.

| hole | caught by | with that guard removed |
|---|---|---|
| H1 `sts:AssumeRole` | `test_no_identity_in_this_stack_may_assume_another_role_in_it` (+1) | **77 passed** |
| H2 Deny scoped to one ARN | `test_the_governed_service_role_carries_an_explicit_deny` (+1) | **78 passed** |
| H3 Deny with a dead `Condition` | same (+1) | **78 passed** |
| H4 Allow by `NotAction` | 14 failures | **79 passed** |
| H5 attached by `Fn::Sub` | 12 failures | **79 passed** |
| H6 invoke via `Fn::ImportValue` | `test_no_invoke_grant_names_something_this_check_cannot_resolve` | **78 passed** |
| H7 `EventSourceMapping` | `test_no_event_source_drives_a_function_in_this_stack` | **78 passed** |
| H8 invoke on an alias | `test_only_the_gateways_own_role_may_invoke_a_tool` | **79 passed** |

Removing the guard reopens the hole in all eight cases, so none is decoration.

**No new check fires against the real snapshot**, and that was verified rather than
inferred: the stack holds no assume-role grant, no event source, no alias, and no
unresolvable invoke target, and every one of the four trust policies names
`lambda.amazonaws.com` and nothing else.

## What this does not do

- **It deploys nothing and changes no infrastructure.**
- **It scores nothing.** No comparator, threshold, golden case, history entry,
  instrument digest, prompt pin or tool-spec pin moves.
- **It does not make a bundle-to-route mismatch observable.** `normalize` still
  rewrites asset hashes to `<ASSET_HASH>`, so the deployed *code* a route points at
  is uncovered. ADR-058 closed the path that made it a one-word mistake; observing
  it is a separate decision about what the snapshot is for.
- **It does not add the probes Security is owed** against a tool that is now
  reachable.
- **It does not settle the `pave/twokey.py` question** three seats raised — whether
  `test_tool_plane_iam.py` and `test_hermeticity.py` should carry a rule, and
  whether `test_gateway_run_parity.py`'s should collect AI Quality. One decision,
  not this one.

## Verification

```
$ python -m pytest -q            2382 passed, 6 skipped     # main: 2377
$ python -m ruff check .         All checks passed!
$ python -m pave.cli infra snapshot --check   synth snapshot current: 2 template(s)
```

Hermetic, no network, no new dependency. `pave/infra.py` remains pure JSON — no
SDK, no cloud.

Two-Key-Disposition: security
Two-Key-Disposition: platform-eng
Two-Key-ADR: docs/adr/ADR-059-the-checker-learns-the-routes-it-was-not-looking-at.md
Two-Key-Rationale: One rule covers both changed files and it is the right one:
  pave/infra.py and tests/test_iam_assertions.py are the G1 and G3 checker itself,
  and this change is entirely a widening of it. Every movement makes the checker
  see more, never less. The Deny filter now refuses two shapes it used to accept,
  which makes an existing assertion fail on templates it used to pass, and the
  action matcher now reads NotAction and the role resolver now reads Fn::Sub, both
  of which can only add grants to what the assertions consider. Three new
  assertions are added and none is removed or relaxed, the model-invoke allowlist
  and the readable-exception list are untouched with their length pins intact, and
  GRANT_SHAPES is unchanged. The eight holes were reproduced against the committed
  snapshot on main before anything was written, all eight are caught after, and
  each new guard was then deleted with its hole re-planted to establish that the
  guard rather than something incidental is what catches it. Nothing is deployed,
  no infrastructure file changes, and no threshold, baseline, golden case,
  comparator, prompt pin, tool-spec pin or instrument digest moves.

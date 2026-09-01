# ADR-059: the checker learns the routes it was not looking at

**Status:** Accepted. **Zero model calls. Nothing is deployed to AWS.**
**Seats:** Security · Platform Engineering (`pave/infra.py`,
`tests/test_iam_assertions.py`), with this ADR.
Discharges the Security seat's blocking findings from the `ADR-058` review.

The four-seat review of the M06b deploy commit reported eight ways to reach a
model or a tool that the G1/G3 checker does not look for. **All eight were
reproduced here against the committed snapshot before anything was changed**, and
all eight were green:

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

None of these was introduced by ADR-058. They applied to `catalog-search` from
M02 and to the whole stack before that. What ADR-058 changed is the cost: a second
tool doubles the surface, and it recorded them as owed *before the M06b scored
run* rather than fixing them inside a diff that already carried a pin move.

## What was decided

### 1. A Deny is not a boolean

`model_invoke_denials` read `Effect` and the action list and nothing else. Two
shapes therefore counted as full coverage while denying almost nothing:

- **`Resource` scoped to one ARN.** A Deny on a model the platform does not call
  forbids nothing it does.
- **A `Condition` that never matches.** A Deny that is never in force.

Both now fail the filter, so they stop counting as denials at the source and
`test_the_governed_service_role_carries_an_explicit_deny` goes red — plus
`test_every_deny_is_in_force_for_every_model` asserts the property directly,
because an indirection like that is exactly what a later refactor removes without
noticing.

**A `Condition` is refused outright rather than analysed.** Deciding whether a
condition can ever be true is a policy-simulator problem, and a checker that
guessed would be wrong in the direction that passes.

### 2. `NotAction` is the inverse of the list, and it was read as an absent one

`{"Effect": "Allow", "NotAction": ["s3:GetObject"], "Resource": "*"}` permits every
model action while naming none. `statement.get("Action")` returns `None`, so
`grants_any` returned `False` and the grant was invisible to every G1 assertion.
It needs no escape hatch: `notActions` is a plain `iam.PolicyStatement` field.

`grants_any` now matches through `NotAction` as well. On a `Deny`, `NotAction`
denies *more* than the list, so reporting it as covering the wanted actions is
correct there too.

### 3. A policy attaches to a role through any reference form

`_referenced_roles` read `Ref` and bare strings. A policy whose `Roles` names its
target through `Fn::Sub` — `Roles: [{"Fn::Sub": "${SomeRole}"}]` — attached to
nobody as far as every assertion could tell, with an unrestricted
`bedrock:InvokeModel` Allow inside it.

`referenced_logical_ids` learns `Fn::Sub`, skipping pseudo-parameters by the `::`
that distinguishes `${AWS::Partition}` from `${SomeRole}` — so there is no list of
names to keep current. `_referenced_roles` routes every non-string through it.

### 4. G1 has a transitive path that carries no model action at all

The tool's Deny is an **identity** policy on the tool's role. `sts:AssumeRole`
produces a different session carrying the gateway role's `bedrock:InvokeModel`
Allow. Nothing in the module looked at `sts:` or at a trust policy, and the CDK
call is one line with no escape hatch:
`gatewayFn.role.grantAssumeRole(toolFn.grantPrincipal)`.

**The rule adopted is blunt on purpose: no role in this stack may assume another
role in it, and no role's trust policy may name an identity from this stack.**
Nothing here needs to — every role is assumed by `lambda.amazonaws.com` and
nothing else — and a narrower rule would have to decide which crossings are safe,
which is the reasoning that produced the hole.

Both halves are asserted, not only the pair, because a trust policy widened in
advance of a grant is the same finding one commit early.

### 5. An event source is a fourth route, and it needs no permission

`tests/test_tool_plane_iam.py` opened by enumerating *"three separate things to be
false here"* — an identity grant, a resource policy, a network route. There is a
fourth. An `AWS::Lambda::EventSourceMapping` drives the function through a poller
using the **function's own execution role**: no invoke grant to find, no
`AWS::Lambda::Permission` to flag. A queue with an open `sqs:SendMessage` policy in
front of it is a route to the tool with no plane, no Cedar and no audit record.

`fn.addEventSource(new SqsEventSource(q))` is one line. The docstring is corrected
to four, which matters as much as the assertion: a list that says three is how the
next reader stops looking.

### 6. An invoke grant may name an alias, and an unresolvable target is not an absent one

**Aliases and versions.** `fn.addAlias('live')` plus `alias.grantInvoke(role)`
emits `{"Ref": "<Alias>"}`, and every G3 assertion intersects against
`AWS::Lambda::Function` logical ids — so the grant dropped out and the assertion
went on reporting the gateway as the sole invoker. Worse when the grant lands on a
role the stack already has: the new-role tripwire in `test_iam_assertions.py` fires
on a stranger and says nothing about this. `resolve_functions` maps a pointer back
to the function behind it.

**Unresolvable targets.** `{"Fn::ImportValue": "SomeExport"}` carries an export
name, not an ARN, so `invoke_targets` returned nothing *and*
`_names_a_wildcard_function` saw no `*` and no `:function:`. The grant fell out of
both detectors at once — the "two blind checks agreeing is not coverage" condition
the module already warns about one function up — and `cdk.Fn.importValue()` is the
ordinary cross-stack idiom, so it reads as normal in review.

Same answer as `unreadable_managed_policies`: there is nothing here to read, so the
only honest response is to refuse the shape.

## What it survived

Every hole re-planted against the fixed checker, and then — the part that matters —
**each new check deleted and its hole re-planted, to prove the check is the thing
catching it rather than something incidental**:

| hole | caught by | with that guard removed |
|---|---|---|
| H1 `sts:AssumeRole` | `test_no_identity_in_this_stack_may_assume_another_role_in_it` (+1) | 77 passed |
| H2 Deny scoped to one ARN | `test_the_governed_service_role_carries_an_explicit_deny` (+1) | 78 passed |
| H3 Deny with a dead `Condition` | same (+1) | 78 passed |
| H4 Allow by `NotAction` | 14 failures | 79 passed |
| H5 attached by `Fn::Sub` | 12 failures | 79 passed |
| H6 invoke via `Fn::ImportValue` | `test_no_invoke_grant_names_something_this_check_cannot_resolve` | 78 passed |
| H7 `EventSourceMapping` | `test_no_event_source_drives_a_function_in_this_stack` | 78 passed |
| H8 invoke on an alias | `test_only_the_gateways_own_role_may_invoke_a_tool` | 79 passed |

Eight for eight: removing the guard reopens the hole, so none of them is
decoration. No new check fires against the real committed snapshot — the stack
holds no assume-role grant, no event source, no alias, and no unresolvable invoke
target, and every trust policy names `lambda.amazonaws.com` and nothing else.

## What this does not do

- **It deploys nothing and changes no infrastructure.** `gateway-stack.ts` and the
  committed snapshot are untouched; this is entirely the checker that reads them.
- **It scores nothing.** No comparator, threshold, golden case, history entry,
  instrument digest, prompt pin or tool-spec pin moves.
- **It does not make a bundle-to-route mismatch observable.** `normalize` still
  rewrites every asset hash to `<ASSET_HASH>`, so the deployed *code* a route
  points at remains uncovered. ADR-058 closed the path that made it a one-word
  mistake by deriving the construct id from the tool id; observing it is a
  separate decision about what the snapshot is for, and it is not taken here.
- **It does not add the probes Security is owed** against a tool that is now
  reachable. Security's seat plus an ADR, additive, still outstanding.
- **It does not settle whether `tests/test_tool_plane_iam.py` and
  `tests/test_hermeticity.py` should carry a `pave/twokey.py` rule**, nor whether
  `tests/test_gateway_run_parity.py`'s rule should collect AI Quality. Three seats
  raised that shape during the ADR-058 review; it is one decision and it is not
  this one.

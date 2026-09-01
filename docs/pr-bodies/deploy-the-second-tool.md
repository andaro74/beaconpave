# The second tool becomes reachable, and the model-facing surface grows with it

M06b step 2, final half. **Zero model calls. Nothing is deployed to AWS** — `cdk
synth` runs locally and environment-agnostic, and the assertions read the committed
snapshot (ADR-017). Recorded as **ADR-058**.

`entitlement-check` has been registered, permitted by a generated Cedar policy, and
shipped to the model inside `tools.contracts.json` since M02. `TOOL_FUNCTIONS` named
one tool. This routes it.

**Four seats reviewed it with a brief to plant defects rather than read, and three
of them found defects this diff introduced. All three are fixed here.** What they
found is below, with the measurements, because a finding that lives only in a
transcript is a finding nobody has.

## What lands

**One constructor for both tool functions.** `deployTool(toolId)` creates the
function, attaches the explicit model-invoke `Deny`, and grants the gateway — and
only the gateway — `lambda:InvokeFunction` on it. Those are not per-tool decisions;
they are what a tool *is* here, and a second function written by copying the first is
where one of them gets left out.

**The deployment defines no clock.** `BEACONPAVE_CLOCK` is set nowhere. An override
set in the stack is a default: the deployed tool would answer against an instant no
arm file names and `module_constants` cannot see, so the ADR-021 parity loop would go
on agreeing with itself while the deployed instrument had moved.

The refactor is behaviour-preserving, and measured twice: the normalized snapshot
moved **116 insertions, 0 deletions**, and the Platform Engineering seat diffed the
raw un-normalized synth independently — **128 additions, 0 deletions**, every
existing asset hash and `DependsOn` unchanged, `BeaconpaveAuditTrail` byte-identical.

## `TOOL_SPECS_SHA256` moves, and the first draft over-stated what that means

`1912657b…dc15c4a` → `6097664d…1cf7b03`.

**Nothing about `catalog-search` changed**; AI Quality reproduced the old pin by
hashing it alone at this commit. `TOOL_SYSTEM_SHA256` does not move.

The first draft said *"no comparison may span this commit."* Corrected, with the
halves separated:

- **A live run may not span it.** The surface is larger, so a governed run before and
  one after are runs of different systems. The M06b scored run sits after it, and no
  recorded golden history entry can be compared to it — every one was produced
  against a one-tool surface. **Nothing enforces that**: `evals/history/schema.json`
  carries no field naming the tool surface. Owed, and listed below.
- **The committed-answers lanes may span it.** Comparators score frozen artifacts and
  never reach the gateway. `comparators.json`, `cases.yaml`,
  `deterministic_instrument()` and all twelve adversarial and judge digests are
  byte-identical across this commit — measured, not argued. CI's L2 and L5 lanes stay
  valid, and **no instrument registration is owed.**

The digest is now taken in the **routing table's order**, not sorted:
`handler.tool_config` iterates `TOOL_FUNCTIONS` as written. The two orderings agree
at this commit, so the correction is free here and would not have been once a tool
sorts before `catalog-search`.

## AI Quality's blocking finding: coaching in the surface the eval measures

`entitlement-check`'s shipped description read *"the agent **must call this** rather
than reason about it — a model inferring blackout rules from catalog text is exactly
what the m00b control does wrong."*

That is tool-use coaching, which ADR-021 forbids by name — *"no 'search before
answering', no 'broaden your query if you get no rows' … coaching around a loss
mechanism after predicting it is how a prediction stops being one"* — aimed at the
behaviour **twelve of twenty-five golden cases score** with `expect_tool_before_answer`.

It reached no model and sat in no pin while the tool was unrouted, because
`TOOL_SPECS_SHA256` iterates the *routed* set: the ADR-043 escape, one file over.
**This commit is what would have made it live.** AI Quality proved the gap by planting
ADR-021's forbidden text verbatim, regenerating the contracts and re-pinning the hash
in one diff — `2175 passed`, and their own seat was not among those the gate demanded
for it.

Rewritten here rather than after, so the rewrite rides this ADR-021 boundary instead
of creating a second one inside one milestone. And because **a hash pin catches
movement but can never object to text it was initialized with**,
`test_no_routed_tool_coaches_the_model_into_calling_it` reads the shipped description
for the phrasings ADR-021 itself names. A floor, not a proof — a determined rewrite
goes around it. What it removes is the accident, and the accident is what happened.

## Platform Engineering's two HIGH findings, both created by the refactor

**The closure took two unbound arguments.** They planted
`deployTool('CatalogSearchFn', ENTITLEMENT_CHECK)` — the deployed `catalog-search`
ships the other tool's bundle and answers entitlement queries while `TOOL_FUNCTIONS`
still routes `catalog-search` to it. **Both gates green.** `pave/infra.py` normalizes
every asset hash to `<ASSET_HASH>`, so the one byte that moved is the one the
snapshot cannot see, and nothing in the repo pairs a construct id to a tool id. The
refactor created the degree of freedom at the same moment it created a second value
to fill it. `deployTool` takes **one** argument now and derives the construct id,
which removes the freedom rather than asserting about it — and reproduces the
committed snapshot byte for byte.

*Residual, stated rather than implied:* a bundle-to-route mismatch introduced any
other way is still invisible. Closing that is a `pave/infra.py` change, listed below.

**And ADR-058's claim that "a function built any other way still has to satisfy
both" was wrong for G3.** Every assertion in `test_tool_plane_iam.py` was scoped to
`infra.routed_tools`, so an unrouted function was outside all of them. A third call
to the closure deploys a Lambda that inherits `grantInvoke`, holds `s3:GetObject` on
`*`, and no assertion knew existed: `2373 passed, 6 skipped`, baseline exactly.
`test_the_gateway_may_invoke_nothing_but_a_routed_tool` closes it, asserting on the
**grant** rather than an inventory — a Lambda nobody may invoke is inert; a Lambda
the gateway may invoke is a tool whichever file declares it.

## Tool Owner and Security, independently: the routing derivation deadlocked

`test_the_routing_table_is_parsed_from_the_gateways_own_environment` closed with
`== {"catalog-search"}`, three lines under its own sentence *"a list of tool ids in
this file would be a second copy."* It is derived now — but the first derivation,
*registered ∧ has a server*, made implementing `publish-highlight` impossible without
deploying it: `test_an_unbuilt_tool_is_declared_and_unreachable` says remove it from
`UNBUILT`, the routing test says route it, and routing it is what Legal/S&P refused.
**The failure message offered a place to write the decision down and there was no
place** — a protection stated and absent.

`NOT_DEPLOYED` is that place, guarded exactly as `UNBUILT` is: the entry must still be
registered, its consequence class must be gated so it cannot quiet a reachable tool,
and it must not appear in the routing table.

## Security: the ADR's "it still fails closed" was not true as written

ADR-057 recorded that `_tool_probe` writes an *allowed* record for a call it never
makes, *"inert today only because `entitlement-check` is undeployed."* This commit
removes that, and the first draft said the witness makes it fail closed.

It does, for a **single** colliding record. It does not in general, and Security
measured why: `executed` separates *allowed* from *ran* and **does not attribute a run
to a turn**. The only field that does is `request_id`, which is caller-supplied. A
turn writing `.001` and `.002` under one prefix, plus a second invocation reusing that
`request_id`, leaves a derivation crediting the first turn's witness to the second —
**PASS for an invocation that called nothing.** (There is also no lake-derived
trajectory in the repo yet: the fragment keys the tool as `id`, the scorer reads
`step["tool"]`. I verified both.)

The ADR no longer claims it. `SPEC/06b` B14 gains *an execution witness from one turn
credited to another* to its "what a fix must survive" list, as amendment 1. B14 stays
deliberately open; what changed is what a fix has to be.

## Deletability

**Round 1 — ten mutations of the deployed stack, each re-synthesized and re-recorded,
ten caught:** the second tool's role losing the model-invoke `Deny` (G1), losing
`grantInvoke`, being deployed and left unrouted, a wildcard grant, the service role
granted invoke, `BEACONPAVE_CLOCK` set, a public function URL, an unregistered tool
routed, a stale `TOOL_SPECS_SHA256`, and a stale snapshot.

**Round 2 — eleven mutations against the seat findings, eleven caught:**

| mutation | caught by |
|---|---|
| `CLOCK_ENV` renamed and the new name set in the stack | `test_the_deployment_does_not_define_a_clock_of_its_own` |
| the clock key written as `BEACONPAVE_CLOCK` | same (parsed, not grepped) |
| a clock set in a **second** stack's snapshot | same (globs the directory) |
| tool-use coaching restored in the shipped description | `test_no_routed_tool_coaches_the_model_into_calling_it` (+1) |
| ADR-021's own forbidden phrasing, verbatim | same (+1) |
| `publish-highlight` gains a server | `test_an_unbuilt_tool_is_declared_and_unreachable` |
| `NOT_DEPLOYED` loses its reason | `test_a_tool_held_back_from_deployment…` (collection error) |
| `NOT_DEPLOYED` names an ungated tool | same (+1) |
| `NOT_DEPLOYED` names an unregistered tool | same |
| a `NOT_DEPLOYED` tool spliced into the routing table | 19 failures |
| **a shadow Lambda the gateway may invoke, unrouted, carrying the Deny** | `test_the_gateway_may_invoke_nothing_but_a_routed_tool` — **the only thing that catches it** |

Two plants reported as they happened rather than as expected: `deployTool` with a
third tool id now **refuses to synthesize**, because the construct id is derived, so
Platform Engineering's exact shape is unreachable through the closure and had to be
planted at the snapshot instead. And an earlier harness restored files with `git
checkout --`, discarding the uncommitted work it existed to test; the plant-dead
guard caught the missing anchor immediately.

## What this does not fix, with owners

Recorded in ADR-058 in full. The load-bearing ones:

**Security — the IAM checker is narrower than the invariants it is asserted to
enforce.** Not introduced here; this commit doubles the surface. Each planted live
against the committed snapshot and passed: `sts:AssumeRole` from a tool role onto the
gateway role; the `Deny` checked for existence but never for `Resource` scope or
`Condition`; `NotAction` grants; `Fn::Sub` in `Roles` and `Fn::ImportValue`;
`AWS::Lambda::Alias`/`Version` as an invoke target; and
`AWS::Lambda::EventSourceMapping` — **a fourth route, needing no grant and no
permission at all**, where the file's docstring enumerates three. Security's position
is that the event-source and assume-role holes must land before anything is deployed
to AWS. Nothing is deployed here; they are owed before the scored run.

**Security — probes are owed** against a tool that is now reachable. No probe in the
frozen corpus names `entitlement-check`. Security's seat plus an ADR; additive.

**AI Quality — `test_gateway_run_parity.py`'s two-key rule does not carry AI
Quality**, so `TOOL_SPECS_SHA256` is movable on `(platform-eng, security)` alone. It
collects AI Quality here only because `gateway-stack.ts` is in the same diff. Third
instance of the ADR-035 / ADR-037 shape. Platform Engineering raised the same shape
for `test_tool_plane_iam.py` and `test_hermeticity.py`; one `twokey.py` decision.

**AI Quality — the instrument records nothing about the routed tool set.** A
precondition for Decision 11: otherwise two runs with identical fingerprints could
differ on twelve of twenty-five cases purely from deployment.

**AI Quality — `tool_before_answer` was a constant FAIL by construction** until this
commit, the mirror of `entitlement_source`'s constant unearned PASS. This closes the
evidence half of its deferral. It does not close Decision 11.

**Tool Owner — the deployed clock is correct.** They staged the bundle exactly as
`stageToolBundle` does and drove all twelve golden rows through `server.handler`:
**12/12 deployed answers match**, including `not-yet-started` and `blackout`.

**Tool Owner — bundle correctness is detectable only at run time in AWS.** Three
broken bundles planted; all fail as a JSON-RPC `error` — the routing class, never a
silent wrong verdict. The shape is right; only the timing is late.

**Platform Engineering — `HERMETIC_ROOTS = tools/` will go red when
`publish-highlight` is built.** The compliant answer is an exclusion plus an ADR, not
narrowing the root back. Pre-registered so the tempting fix is on record as wrong.

## What this does not do

- **It deploys nothing to AWS.** No credentials, no account, no region.
- **It does not build `publish-highlight`**, now declared in `NOT_DEPLOYED` with the
  reason, gated by `cedar.GATED_CONSEQUENCES`, refused with the scope of that refusal
  open (ADR-055).
- **It scores nothing.** No comparator, threshold, golden case, history entry or
  instrument digest moves. `entitlement_source` and `tool_before_answer` stay
  deferred.
- **It does not close B10, B11 or B14.**

## Verification

```
$ cd platform/infra && npx cdk synth --quiet      # local bundling, no Docker, no AWS
$ python -m pave.cli infra snapshot --check       synth snapshot current: 2 template(s)
$ python -m pytest -q                             2377 passed, 6 skipped   # main: 2364
$ python -m ruff check .                          All checks passed!
```

Hermetic, no network, no new dependency.

Two-Key-Disposition: security
Two-Key-Disposition: ai-quality
Two-Key-Disposition: platform-eng
Two-Key-Disposition: tool-owner
Two-Key-Disposition: legal-sp
Two-Key-ADR: docs/adr/ADR-058-the-second-tool-deploys-and-the-measured-system-grows.md
Two-Key-Rationale: Three rules fire. gateway-stack.ts takes security and ai-quality
  with an ADR, and this is the change that rule was written for: a second tool
  function is where the model-invoke Deny gets left out, so both are built by one
  constructor that attaches it and the narrow grantInvoke. The omission was planted
  anyway and caught. Two defects the constructor itself introduced were found by the
  Platform Engineering seat and fixed rather than recorded as cuts: it took the
  construct id and the tool id as free parameters, so a mispairing deployed one
  tool's code under the other's route with both gates green because asset hashes are
  normalized out of the snapshot, and it now takes one argument and derives the id;
  and every assertion in the tool-plane file was scoped to the routing table, so a
  function deployed through the closure and never routed inherited the gateway invoke
  grant while no check knew it existed, which a new assertion on the grant closes.
  The ai-quality key is load-bearing for two separate reasons. Routing a second tool
  moves TOOL_SPECS_SHA256, because that digest is taken over the routed set, so the
  model-facing surface grew without a word of the prompt changing, which is an
  ADR-021 event for a live run and measurably not one for the committed-answers
  lanes. And that seat found the description this commit would have made live
  instructs the model to call the tool, which ADR-021 forbids and which twelve of
  twenty-five golden cases score, so the description is rewritten here and a content
  check now reads the shipped text because a hash pin cannot object to text it was
  initialized with. The tool schema takes platform-eng, security, tool-owner and
  legal-sp, which is why all four appear. The parity test takes platform-eng and
  security and its changes are the pin move, the ordering correction, the coaching
  check, and a hardened clock assertion that reads CLOCK_ENV from the tool source and
  parses every snapshot in the directory rather than grepping one for a literal the
  tool is free to rename. All planted and caught. No threshold, baseline, golden
  case, comparator or instrument digest moves, nothing is deployed to AWS, and the
  suite is hermetic.

# ADR-058: the second tool deploys, and the measured system grows with it

**Status:** Accepted. **Zero model calls. Nothing is deployed to AWS.**
**Seats:** Security · AI Quality (`platform/infra/lib/gateway-stack.ts`, with this
ADR) · Platform Engineering · Security (`tests/test_gateway_run_parity.py`) ·
Platform Engineering · Security · Tool Owner · Legal/S&P
(`tools/entitlement-check/schema.in.json`).
Executes `SPEC/06b` step 2's remaining half.

`entitlement-check` has been registered in `platform/registry/tools.yaml`,
permitted by a generated Cedar policy, and shipped to the model inside
`tools.contracts.json` since M02. `TOOL_FUNCTIONS` named one tool. The gap closed
here is the one `tests/test_tool_servers.py` found the class of two PRs ago: a tool
the platform advertises and cannot call.

## What was decided

### 1. Both tool functions are built by one constructor

`deployTool(toolId)` creates the function, attaches the explicit model-invoke
`Deny`, and grants the gateway — and only the gateway — `lambda:InvokeFunction` on
it.

The two properties are not per-tool decisions. They are what a tool *is* here, and
a second function written by copying the first is exactly where one of them is left
out: the Security seat planted that omission during the `SPEC/06b` review and it is
the reason this is a function rather than a paste.

**The seat round then found that the closure introduced two problems of its own, and
both are fixed here rather than recorded as cuts.**

**It took one argument, not two.** The first version was
`deployTool(constructId, toolId)` with the two free of each other. Platform
Engineering planted `deployTool('CatalogSearchFn', ENTITLEMENT_CHECK)`: the deployed
`catalog-search` ships the other tool's bundle and answers entitlement queries while
`TOOL_FUNCTIONS` still routes `catalog-search` to it. **Both gates stayed green.**
`pave/infra.py` normalizes every asset hash to `<ASSET_HASH>`, so the one byte that
moved is the one the snapshot cannot see, and no test in the repository pairs a
construct id with a tool id. The refactor created that degree of freedom at the same
moment it created a second value to fill it — with one tool, `toolCode(CATALOG_SEARCH)`
sat inline at its single use site with nothing to confuse it with. **The construct id
is derived from the tool id now**, which removes the freedom instead of asserting
about it, and reproduces the committed snapshot byte for byte.

*Residual, stated rather than implied:* a bundle-to-route mismatch introduced any
other way is still invisible, because the asset hash is normalized out. Closing that
is a `pave/infra.py` change and is listed as owed below.

**The claim "a function built any other way still has to satisfy both" was wrong for
G3.** Every assertion in `tests/test_tool_plane_iam.py` is scoped to
`infra.routed_tools`, so an unrouted function was outside all of them. Platform
Engineering added a third call to the closure — a Lambda inheriting `grantInvoke`
from inside it, holding `s3:GetObject` on `*`, that no assertion knew existed — and
measured `2373 passed, 6 skipped`, the baseline exactly, snapshot re-recorded without
complaint. G1 held, because the model-invoke `Deny` is enforced over every
non-gateway role rather than over routed tools. G3 did not.
`test_the_gateway_may_invoke_nothing_but_a_routed_tool` closes it, asserting on the
**grant** rather than on an inventory: a Lambda nobody may invoke is inert, and a
Lambda the gateway may invoke is a tool whichever file declares it.

The refactor is behaviour-preserving, and measured twice: the normalized snapshot
moved **116 insertions, 0 deletions**, and Platform Engineering diffed the raw
un-normalized synth independently — **128 additions, 0 deletions**, every existing
asset hash and `DependsOn` unchanged, `BeaconpaveAuditTrail` byte-identical.

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
reads, and the hash moves by construction. `TOOL_SYSTEM_SHA256` does not move; the
prompt is unchanged. Both facts were verified by the AI Quality seat, which also
reproduced the old pin by hashing `catalog-search` alone at this commit.

**The first draft of this section said "no comparison may span this commit" and that
was too broad.** Corrected, with the halves separated:

- **A live run may not span it.** The model-facing surface is larger than it was, so
  a governed run before this commit and one after are runs of different systems. The
  M06b scored run sits after it, and no recorded golden history entry can be
  compared to it — every one was produced against a one-tool surface. **Nothing
  enforces that**: `evals/history/schema.json` carries no field naming the tool
  surface, so a reader cannot tell which side of this line an entry sits on. Named
  below as owed.
- **The committed-answers lanes may span it.** Comparators score frozen artifacts
  and never reach the gateway. `evals/comparators.json`, `evals/cases.yaml`,
  `deterministic_instrument()` and all twelve adversarial and judge digests are
  byte-identical across this commit — measured, not argued. CI's L2 and L5 lanes
  stay valid.

### 3a. And the description that routing exposed

`entitlement-check`'s shipped description read *"the agent must call this rather than
reason about it — a model inferring blackout rules from catalog text is exactly what
the m00b control does wrong."*

That is **tool-use coaching**, which ADR-021 forbids in as many words — *"no 'search
before answering', no 'broaden your query if you get no rows' … coaching around a
loss mechanism after predicting it is how a prediction stops being one"* — aimed
precisely at the behaviour twelve of twenty-five golden cases score with
`expect_tool_before_answer`. It also named a milestone identifier the model cannot
use.

It reached no model and sat in no pin while the tool was unrouted: `TOOL_SPECS_SHA256`
iterates the *routed* set, which is the escape ADR-043 recorded one file over. **This
commit is what would have made it live**, so it is rewritten here rather than after,
and the rewrite rides this ADR-021 boundary instead of creating a second one inside
one milestone. The new text describes what the tool returns and instructs nothing.

`catalog-search`'s description carries the same governance vocabulary without the
imperative. Rewriting it moves an established pin and is the Tool Owner's owed
rewrite, already deferred in `TOOL_SPECS_SHA256`'s own comment. Not taken here.

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
`tool.executed` means a **single** colliding probe record reads as `executed: false`
— a false negative.

**The first draft of this ADR then wrote "and it still fails closed", which is not
true as stated.** The Security seat measured the case it misses, and it is worth
carrying precisely because it was a protection claimed and absent:

- There is no lake-derived trajectory in the repository yet, so nothing has ever
  exercised the claim. The record fragment keys the tool as `id` and the scorer
  reads `step["tool"]`, so any derivation must remap first.
- `executed` separates *allowed* from *ran*. **It does not attribute a run to a
  turn.** The only thing that does is `request_id`, and `request_id` is
  `event.get("request_id")` — caller-supplied. A turn writing `.001` and `.002`
  under one prefix, and a second invocation reusing that `request_id`, leaves a
  derivation crediting the first turn's execution witness to the second. That fails
  **open**, not closed.

B14 is still deliberately unfixed and it is now recorded as a wider problem than it
was: its register entry gains *an execution witness from one turn credited to
another* to the list of what a fix must survive. That is the honest state — it is not
made safe here, and this ADR no longer says it is.

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

## What the seat round found and this does not fix

Recorded with owners rather than left in a review, because a finding that lives only
in a transcript is a finding nobody has.

**Security — the IAM checker is narrower than the invariants it is asserted to
enforce.** These are not introduced here; this commit doubles the surface they apply
to, and each was planted live against the committed snapshot and passed:

| hole | shape | seats |
|---|---|---|
| `sts:AssumeRole` from a tool role onto the gateway role | a second path to a model with the `Deny` still standing | security · platform-eng + ADR |
| the `Deny` is checked for existence, never for `Resource` scope or `Condition` | a Deny naming one unused model ARN reads as coverage | same |
| `NotAction` grants | `grants_any` reads `Action` only | same |
| a policy attached by `Fn::Sub` in `Roles`, or a grant through `Fn::ImportValue` | `_referenced_roles` and `invoke_targets` resolve neither | same |
| `AWS::Lambda::Alias` / `Version` as an invoke target | the target set is `AWS::Lambda::Function` logical ids only | same |
| `AWS::Lambda::EventSourceMapping` | **a fourth route, needing no grant and no permission at all** — the file's own docstring enumerates three | same |

The Security seat's position is that the event-source and assume-role holes must
land before anything is deployed to AWS. Nothing is deployed by this commit; they are
owed before the M06b scored run.

**Security — probes are owed against a tool that is now reachable.** No probe in the
frozen corpus names `entitlement-check`; `handler.py`'s routing refusal for it becomes
`allowed` here. Security's seat plus an ADR, additive, not a downgrade.

**AI Quality — `tests/test_gateway_run_parity.py`'s two-key rule does not carry AI
Quality.** So `TOOL_SPECS_SHA256` — the ADR-021 boundary itself — is movable on
`(platform-eng, security)` alone. It collects AI Quality on this PR only because
`gateway-stack.ts` is in the same diff. That is the ADR-035 / ADR-037 shape a third
time: a protection stated in prose over a rule that does not implement it, and
`tests/test_contracts.py` asserts list agreement rather than seat sufficiency.

**AI Quality — the instrument records nothing about the routed tool set.** Measured
byte-identical with the tool unrouted. Before `tool_before_answer` may move from
`deferred` to `scored` (Decision 11), the deterministic instrument must carry the
routed set or `TOOL_SPECS_SHA256`, or two runs with identical fingerprints could
differ on twelve of twenty-five cases purely from deployment. A precondition, and
cheaper now than after a published row depends on it.

**AI Quality — `tool_before_answer` was a constant FAIL by construction** until this
commit, the exact mirror of `entitlement_source`'s constant unearned PASS. This
commit closes the evidence half of its deferral. It does not close Decision 11.

**Tool Owner — bundle correctness is detectable only at run time in AWS.** No test
asserts the staged bundle contains `catalog.json` or that `BEACONPAVE_CATALOG`
resolves. Three broken bundles were planted; all fail as a JSON-RPC `error` — the
routing class, never a silent wrong verdict — so the failure shape is right and only
the timing is late.

**Platform Engineering — a bundle-to-route mismatch is invisible to both gates.**
`pave/infra.py` normalizes asset hashes out of the snapshot, so the deployed code a
route points at is not covered by anything. Removing `deployTool`'s second parameter
closes the path that made it a one-word mistake; it does not make the mismatch
observable. Same PR as the checker hardening above.

**Platform Engineering — `tests/test_tool_plane_iam.py` and `tests/test_hermeticity.py`
move gate criteria on one key.** This PR rewrites the central G3 routing assertion and
widens the G8 hermetic scope, both on a single key, inside a diff whose *mechanism*
files take two. Both movements are strengthenings, which is why it is recorded rather
than blocking — but it is the same shape as the AI Quality finding above and the two
belong in one `pave/twokey.py` decision.

**Platform Engineering — a hand-edited snapshot is invisible to `make check`.**
Editing the fixture without touching the stack passes the whole hermetic suite;
only CI's synth-freshness step sees it, and that step needs Node and a working
`npm ci`. Fail-closed by design (an absent verdict exits 2), and written down here so
the exposure is recorded rather than assumed.

**Platform Engineering — `HERMETIC_ROOTS = tools/` will go red when
`publish-highlight` is built.** The scan is static over `rglob("*.py")`, so it fails
on deploy-time-only code being *written*, and `publish-highlight` is a `publish`-class
tool that plausibly needs an SDK. The compliant answer is an exclusion plus an ADR,
the way `handler.py` is already handled — **not** narrowing the root back.
Pre-registered here so the tempting fix is on record as the wrong one. The scan
covers `*.py` only: a `requirements.txt` naming boto3 is not caught, and is inert
because `stageToolBundle` is a file copy with no install step.

**Tool Owner — `tools.yaml` declares `approval: stepfn:editorial-approver` and the
stack holds no Step Functions resource.** Pre-existing, and inert because
`toolplane` never accepts an approval. It is "declared and absent", and it must be
built before `publish-highlight` is ever routed — which is why that tool is now in
`NOT_DEPLOYED` with the reason written down.

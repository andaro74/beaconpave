# ADR-020: The policies are real Cedar; the evaluator is a subset

**Status:** Accepted (M02)
**Seats:** Platform Engineering (mechanism) · Tool Owner (the policies, via the
registry they are generated from) · Security / Red Team (it is an authorization
control)

## Context

ADR-004 decided that Cedar policies are generated from the registry's `callers`
field and evaluated in-process, and named Amazon Verified Permissions as the
scale-up. It did not say what evaluates them, because at M00a nothing did.

M02 has to answer that, and pre-flight measured the options rather than assuming
one. **A real Cedar binding is available on every target that matters**:
`cedarpy` 4.8.7 publishes wheels for `cp312`-manylinux — the deployed Lambda
runtime is `PYTHON_3_12` — as well as `cp313` and the `cp314`-win the operator
develops on. The committed synth snapshot would survive it, too: `pave/infra.py`
already normalizes asset hashes, so a bundled dependency cannot break the ADR-017
freshness job the way `AWS::CDK::Metadata` did.

So this is a decision between two workable options, not a workaround for a
missing one. That is worth stating, because the cheap version of this ADR would
have been "no binding was available."

## Decision

**The generated policy text is real Cedar. The evaluator is a subset of Cedar,
written here, in the standard library.**

Three properties hold, and they are what the decision is actually made of.

**The policies are genuine Cedar** — `permit`/`forbid` with `principal`,
`action`, `resource` and an `unless { context.… }` condition, of the shape AVP
consumes verbatim. ADR-004's scale-up path stays real rather than aspirational:
replacing this evaluator does not mean rewriting the policies.

**The evaluator's input space is closed, so the subset is bounded rather than
open-ended.** It only ever sees policies this repo's generator produced, from a
fixed template, and a hermetic drift check fails if the committed set is not
exactly what the registry generates. That is what makes exhaustive testing
possible instead of merely thorough testing: the grammar is enumerable, and
`tests/test_cedar_policy.py` enumerates it.

**It denies by default, including on anything it cannot fully parse.** `parse`
raises rather than skipping an unreadable statement. The failure that motivates
this is specific: skipping leaves the readable half of a policy set still
returning decisions, and if the unreadable statement was a `forbid`, a control has
silently stopped applying while the engine keeps answering. A policy engine that
fails open is worse than no policy engine, because it looks like one.

### Why not the real binding

Not because it would not work. Three costs, and the third is the one that decided
it.

**It would be the first runtime dependency beyond the two pure-Python libraries
the repo carries**, and a 4.7 MB Rust binary wheel at that. CLAUDE.md requires a
line explaining why the stdlib will not do; for a closed grammar of two statement
forms, it does.

**`platform/gateway` ships via `lambda.Code.fromAsset` with no bundling step at
all today.** Shipping a binary wheel adds a pip-into-the-asset stage to `cdk
synth` — either Docker or a pinned cross-platform download — for a component whose
entire policy set is under a kilobyte.

**A miniature's value is that a reader can see the whole control.** The
authorization path is the thing G3 rests on, and here it is a hundred lines that a
reviewer reads in one sitting, beside the generator that produces its only input.
Behind a binding, the same reviewer sees a function call and has to trust the
rest. At production scale that trade reverses — the policies get hand-written, the
grammar opens up, and a real engine is the only defensible answer, which is
precisely what the scale-up path says.

### The risk this accepts, stated plainly

**It is an authorization engine written for this repo, and that is the kind of
component that fails open without anyone noticing.** The mitigations are
structural rather than diligent: deny-by-default on every path including parse
failure, a closed input space, and negative controls that measure a delta before
planting — each denial test plants the permit and requires the decision to flip,
because "the unregistered tool is denied" is also satisfied by an evaluator that
denies everything. That last one is PR #13's lesson from M01's IAM controls,
applied to a new control before it could be learned twice.

## Consequences

**Cedar features that are not generated are not supported**, and a policy using
one fails loudly at parse time rather than being partially applied. That is the
intended direction: the failure surfaces when the policy set is read, not when a
request is decided.

**The generator and the evaluator live in one module.** They share a grammar, and
a generator and a parser that disagree about it is the classic way an
authorization layer starts permitting something nobody wrote down. Splitting them
across files for tidiness would be a real regression.

**The drift check is hermetic, unlike the synth snapshot it is modelled on.**
Regenerating needs the registry and nothing else — no Node, no AWS account — so it
runs inside `make check` rather than needing a CI job of its own. It is therefore
strictly harder to skip than ADR-017's, which is worth noting because the two
patterns otherwise look identical.

**At scale, replace with:** Amazon Verified Permissions, evaluating the identical
generated policy text with policies deployable independently of code and
authorization decisions logged separately from the application. The interface
already matches — the registry generates, the gateway asks, the answer is a
permit/forbid decision with reasons — and only what evaluates the text changes.

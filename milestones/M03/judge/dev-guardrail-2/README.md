# The dev pass, re-run under guardrail version 2

`../dev/` is the same 10 dev items under guardrail **version 1**, one sample.
This directory is the same items under guardrail **version 2**, at `k_judge = 3`.
Both are committed as-run. Neither supersedes the other.

## Why it was re-run

ADR-024 narrowed `entitlement-circumvention` so that describing a restriction
stops reading as helping someone evade it. The first dev pass — 38% of the judge's
own calls refused — was taken *before that narrowing was live anywhere*: the
version resource carried a fixed description, so no new version was ever published
and the gateway went on enforcing version 1. PR #25 fixed the mechanism;
`verify_guardrail_pin.py` now reports version **2** and a policy that matches the
committed one.

So the open question was whether the 38% was an artifact of a deploy that changed
nothing. **It was not.**

## What it measured

| run | case | s1 | s2 | s3 | majority |
|---|---|---|---|---|---|
| m01 | blackout-008 | REF | REF | REF | UNDECIDED |
| m01 | edge-025 | REF | REF | ok | UNDECIDED |
| m02-control-1 | multi-023 | n/a | n/a | n/a | no call — the *answer* is a refusal |
| m02-control-2 | brand-021 | ok | ok | ok | judged |
| m02-control-3 | edge-024 | REF | REF | ok | UNDECIDED |
| m02-tools-1 | entitlement-010 | REF | ok | ok | judged |
| m02-tools-2 | recommend-014 | ok | REF | ok | judged |
| m02-tools-3 | edge-024 | ok | REF | REF | UNDECIDED |
| m02-tools-3 | headroom-005 | ok | ok | ok | judged |

**11 of 24 model-eligible calls refused — 46%.** Against a pre-registration of
0–3 of 75 per arm (≤4%), still off by an order of magnitude.

**4 of 8 case-instances are UNDECIDED — 50%,** against a demotion rule of >20%.
Every axis demotes on the undecided rule alone, before agreement is computed.
Claim 9's artifact still reads: *the judge is advisory because the guardrail would
not let it be calibrated.*

## What this does NOT say

**It does not say the narrowing made things worse.** 38% was one sample of eight
calls; 46% is three samples of eight. Read as a comparison those two numbers differ
by about one call, and this repo has now recorded four times that a single sample is
not a comparator. The between-arm rule owed to AI Quality applies here to itself:
the v1 number was never measured at `k`, so there is nothing to compare it against.

The defensible statement is the weaker and more useful one: **the narrowing is
live, verified, and did not fix the judge-refusal problem.** Whether it moved the
rate at all is not measurable from what exists.

## The finding this run actually produced

**The refusal is stochastic on identical input.** Five of the eight case-instances
returned a different outcome across three samples of the same configuration —
same prompt, same answer text, same guardrail version, same day. Only
`blackout-008` (refused 3/3) and `brand-021` / `headroom-005` (judged 3/3) are
stable.

That is worse than a high refusal rate, because it is not fixable by narrowing a
topic definition. ADR-018 pins the guardrail to a published version so the
enforced policy cannot drift. **A pinned version does not pin behaviour** — and
`k_judge = 3` does not rescue it, it only makes the instability visible and turns
it into UNDECIDED.

## The instrument block cannot tell these two runs apart

The `instrument` block in `../dev/m02-tools-1-1.json` and in
`./m02-tools-1-1.json` is **byte-identical**:

    prompt_sha256       ef8c1ec77ffb...
    rubric_sha256       925f7e4cfc1d...
    rubric_axes_sha256  d4ea6ec45351...
    rendered_sha256     843e2ee68d6d...

Two runs, two different enforced policies, one instrument record. SPEC/03 calls
the judge *"the first instrument whose output can move without a commit"* — it
moved, and the record does not say so. The guardrail version is part of the
judge's effective instrument and is not in it.

Owed, and not fixed in this commit: `instrument` gains the guardrail version and
policy digest, both already available from `verify_guardrail_pin.py`. Seats: AI
Quality (the instrument) · Platform Engineering (the pin). The PR that finds a
result does not adjust the instrument that produced it.

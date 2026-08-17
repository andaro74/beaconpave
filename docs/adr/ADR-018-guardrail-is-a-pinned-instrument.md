# ADR-018: The guardrail is defined in CDK and pinned to a published version

**Status:** Accepted (M01)
**Seats:** Security / Red Team (guardrail configuration) · Platform Engineering
(deployment) · AI Quality (comparability of recorded scores)

## Context

Pre-flight for M01 found a Bedrock guardrail already in the account, created by
hand on 2026-08-14, outside this repo: `agentpave-gateway-dev`, `READY`, **only a
`DRAFT` version**. It was never used by M00b — `run_baseline.py` passes no
`guardrailConfig` — so the control's recorded 0/10 is uncontaminated by it.

Adopting it would have been the fast path. It is a working guardrail with
sensible filters, and the gateway could have referenced it by id in an hour.

## Decision

M01 defines its own guardrail in the CDK app and pins the gateway to a
**published version**. The hand-made one is left alone.

Two reasons, and the second is the load-bearing one.

**Reproducibility.** A stranger who clones this repo and runs `cdk deploy` must
get the same guardrail, or the recorded scores describe a system nobody else can
build. A guardrail that exists only in one account is untracked state that every
probe result silently depends on.

**A guardrail is an instrument, and a DRAFT instrument moves without a commit.**
Nine of the ten adversarial probes are decided by this thing. A `DRAFT` guardrail
can be edited in a console — a filter strength nudged, a topic added — and every
subsequent probe result changes with **nothing printing differently**. That is
ADR-014's argument about a dollar ceiling tracking a price list that moves
without a commit, and it is worse here: a price change eventually shows up as a
number that looks odd, whereas a guardrail change shows up as a score that looks
like progress.

This is the third instance of the same hazard in this repo — ADR-012 (the
judged/unjudged split), ADR-016 (the two instrument corrections), and now this
one. The pattern is stable enough to state as a rule: **anything that decides a
recorded score is an instrument, and an instrument that can change without a
commit will eventually be mistaken for a system improvement.**

So the deployed version is a `CfnGuardrailVersion` resource, the gateway reads it
from the environment with no default, and `tests/test_iam_assertions.py` fails if
that variable is ever a literal or the string `DRAFT`. The audit record carries
the version, so a probe result can always be traced to the instrument that
produced it.

### What the guardrail is configured from

**From `rules/`, the brand packs, and the classification policy — never from the
probe corpus.** The corpus is frozen (ADR-009) and M01 configures the thing it is
aimed at, so a denied topic written to a probe's wording measures how well we
read the corpus rather than how well the gateway resists attack. SPEC/01 makes
this M01's honesty clause: a probe that passes because a denied-topic string
matched its exact phrasing is an **unearned pass** under SPEC/00b's rule, and is
recorded as one.

One configuration choice is worth recording because it looks like an omission.
**`NAME` and `ADDRESS` are not blocked as PII entities.** A sports highlights
agent has to be able to say a player's name and a venue's address; blocking the
entity would fire on most of the golden set and would show up as a guardrail that
improved security by breaking the product. Requests for personal data about
*subscribers* are refused one step earlier, by the classification router (G5),
which can tell "who plays for the Rovers" from "list subscriber addresses". The
control's PII probe is caught by classification, not by the content filter, and
that is the correct division of labour rather than a gap.

## Consequences

The account now has two guardrails, one of which this repo does not use. That is
deliberate: silently reconfiguring or deleting infrastructure outside the repo is
not something a repo anybody clones should do. Removing the hand-made one is the
operator's call, not the stack's.

Changing the guardrail from here on is a version bump in a diff, which is the
point. The cost is that tuning it requires a deploy rather than a console edit —
which is the intended friction, since a console edit is exactly the thing that
would silently move every recorded score.

**At scale, replace with:** the same pin per environment, promoted through stages
with the stack, and guardrail changes reviewed by the Security seat like any
other policy change. The interface already matches — the version is already an
attribute of the deployment rather than of the account.

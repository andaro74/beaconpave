"""
Does the version description still track the policy it claims to pin?

**The hole this closes, found by planting rather than reading.** The CDK derives
the guardrail version's description from a digest of the policy, so the version
resource replaces itself exactly when the policy changes — that is the fix for
the deploy where ADR-024 narrowed a topic, `cdk deploy` reported
`UPDATE_COMPLETE`, and the gateway went on enforcing the previous version.

`test_iam_assertions.py` checks that the description is digest-*shaped*:

    POLICY_PIN = re.compile(r"^Pinned to policy [0-9a-f]{12}\\.$")

Nothing checked what the digest is taken *over*. The Platform Engineering seat
changed one word inside the computation —

    topics: guardrail.topicPolicyConfig   ->   topics: guardrail.node.id

— then rewrote the entitlement definition to *"this topic now denies absolutely
nothing at all."*, re-synthesised, and re-recorded the snapshot. The description
did not move. **24 tests passed.** A deploy from that tree would report
`UPDATE_COMPLETE` while the gateway kept enforcing the old policy: ADR-024's
failure, reproduced through the mechanism built to prevent it.

## Why this is a relative check and not a reproduction

The obvious test — recompute the CDK's digest in Python and compare — would have
to reproduce JavaScript's `JSON.stringify` key order over the *construct's*
camelCase props, from a snapshot that stores resolved PascalCase CloudFormation
properties. That reproduction would be fragile in a way that has nothing to do
with the property being asserted, and a test that breaks for reasons unrelated to
its subject is a test people learn to re-record without reading.

So this pins a **pair**: a digest this file computes its own way over the policy
in the snapshot, and the digest the CDK put in the description. The invariant is
the one that actually matters, and it is the exact shape of the plant:

> **If the policy digest moved and the description digest did not, the pin has
> stopped tracking the policy.**

That fails whether the cause is a sabotaged computation, a block dropped from
what it covers, or someone editing the snapshot by hand. It does *not* require
the two numbers to agree, only to move together.

**What it still does not cover**, named rather than left implicit: a policy block
that is outside BOTH digests. A `wordPolicyConfig` or a
`contextualGroundingPolicyConfig` is enforced by Bedrock, absent from the CDK's
five-block list, and absent from `POLICY_BLOCKS` below — so adding one moves
neither number and deploys over an unchanged pin. That is the second half of the
seat's finding and it is fixed by widening what is digested, which changes the
digest value and forces a version replacement. It is its own PR.

Hermetic (G8): reads the committed snapshot, imports nothing under test.
Owning seat: Platform Engineering (the mechanism) · Security (the policy).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "platform" / "infra" / "tests" / "fixtures" / "BeaconpaveGateway.template.json"
PIN = ROOT / "platform" / "infra" / "tests" / "fixtures" / "guardrail-pin.json"

#: The resolved CloudFormation property names for everything the CDK digests.
#: Kept in the same order as the TypeScript so a reader can check them against
#: each other by eye; the digest below sorts, so the order is documentation.
POLICY_BLOCKS = (
    "ContentPolicyConfig",
    "TopicPolicyConfig",
    "SensitiveInformationPolicyConfig",
    "BlockedInputMessaging",
    "BlockedOutputsMessaging",
)

DESCRIPTION = re.compile(r"^Pinned to policy ([0-9a-f]{12})\.$")


def _guardrail(template: dict) -> dict:
    guardrails = [r for r in template["Resources"].values()
                  if r.get("Type") == "AWS::Bedrock::Guardrail"]
    assert len(guardrails) == 1, f"expected exactly one guardrail, found {len(guardrails)}"
    return guardrails[0]["Properties"]


def _version_description(template: dict) -> str:
    versions = [r for r in template["Resources"].values()
                if r.get("Type") == "AWS::Bedrock::GuardrailVersion"]
    assert len(versions) == 1, f"expected exactly one guardrail version, found {len(versions)}"
    return versions[0]["Properties"]["Description"]


def policy_digest(template: dict) -> str:
    """This file's own digest of the enforced policy, computed from the snapshot.

    Deliberately NOT the CDK's algorithm. Canonical JSON with sorted keys, so a
    stranger re-derives it from the committed template without reading any
    TypeScript — and so it cannot drift into agreement with a sabotaged
    computation by sharing its code."""
    guardrail = _guardrail(template)
    material = {block: guardrail.get(block) for block in POLICY_BLOCKS}
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]


def test_the_version_description_moved_when_the_policy_did():
    """**The assertion the plant defeats.** Not that the two digests agree — they
    are taken over different material and never will — but that neither can move
    alone. A policy change with a frozen description is a version resource that
    will not be replaced, which is a deploy that reports success and changes
    nothing."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    pinned = json.loads(PIN.read_text(encoding="utf-8"))

    policy_now = policy_digest(template)
    match = DESCRIPTION.match(_version_description(template))
    assert match, (
        f"the version description is {_version_description(template)!r}, which is not "
        "digest-shaped. The version resource will not replace itself when the policy "
        "changes."
    )
    description_now = match.group(1)

    policy_moved = policy_now != pinned["policy_digest"]
    description_moved = description_now != pinned["description_digest"]

    if policy_moved and not description_moved:
        raise AssertionError(
            f"the guardrail policy changed ({pinned['policy_digest']} -> {policy_now}) but "
            f"the version description did not ({description_now}).\n\n"
            "The description is what makes CloudFormation replace the version resource. "
            "Frozen across a policy change, it means `cdk deploy` will report "
            "UPDATE_COMPLETE while the gateway goes on enforcing the PREVIOUS published "
            "version — ADR-024's failure, through the mechanism built to prevent it.\n\n"
            "Check what `policyDigest` in platform/infra/lib/gateway-stack.ts is taken "
            "over. If the policy change is intended and the digest is correct, re-synth "
            "and update platform/infra/tests/fixtures/guardrail-pin.json with BOTH values."
        )

    if description_moved and not policy_moved:
        raise AssertionError(
            f"the version description changed ({pinned['description_digest']} -> "
            f"{description_now}) but the policy this file digests did not ({policy_now}).\n\n"
            "Either the CDK is digesting something that is not policy — which would "
            "republish a version on every unrelated change and make a version number stop "
            "meaning a specific enforced policy — or a policy block moved that "
            "POLICY_BLOCKS here does not cover."
        )

    assert policy_now == pinned["policy_digest"], (
        f"policy digest {policy_now} does not match the pin {pinned['policy_digest']}; "
        "update guardrail-pin.json in the PR that changes the policy")
    assert description_now == pinned["description_digest"], (
        f"description digest {description_now} does not match the pin "
        f"{pinned['description_digest']}")


def test_the_pin_covers_every_policy_block_the_guardrail_declares():
    """A coverage check on the coverage check. `POLICY_BLOCKS` is a hand-written
    list, and a hand-written list of what matters is the thing that goes stale —
    it is the same shape as the CDK's five-block list, one layer out.

    So: every `*PolicyConfig` property the guardrail actually declares must be in
    `POLICY_BLOCKS`. A new enforced block fails here rather than deploying over an
    unchanged pin. This does NOT close the seat's second finding — a block outside
    both digests still deploys silently until the CDK's list is widened too — but
    it means the next one is caught by a test instead of by a reviewer."""
    guardrail = _guardrail(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    declared = {k for k in guardrail if k.endswith("PolicyConfig")}
    uncovered = declared - set(POLICY_BLOCKS)
    assert not uncovered, (
        f"the guardrail declares policy block(s) {sorted(uncovered)} that nothing digests. "
        "Bedrock enforces them, and a change to one would deploy as UPDATE_COMPLETE over an "
        "unchanged version pin. Add them to POLICY_BLOCKS here AND to `policyDigest` in "
        "gateway-stack.ts — this file alone cannot make the version resource replace itself."
    )

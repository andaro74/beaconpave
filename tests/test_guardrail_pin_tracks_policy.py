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

import pytest

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


#: The guardrail/version pairs this file pins, by logical id.
#:
#: **There were two the moment ADR-063 landed, and this file asserted there was
#: one.** The helpers below took "the only guardrail" and would have gone on
#: passing for the main pair while the tool-output pair's pin tracked nothing —
#: which is this file's own defect, one layer out: a hand-written assumption
#: about what exists, in the file whose whole subject is that a hand-written list
#: of what matters goes stale.
#:
#: Adding a pair here without adding it to `guardrail-pin.json` fails loudly, and
#: a third guardrail appearing in the snapshot fails
#: `test_every_guardrail_in_the_snapshot_is_pinned` below.
PAIRS = (
    ("Guardrail", "GuardrailVersion", "main"),
    ("ToolOutputGuardrail", "ToolOutputGuardrailVersion", "tool_output"),
)


def _guardrail(template: dict, logical_id: str = "Guardrail") -> dict:
    resource = template["Resources"].get(logical_id)
    assert resource and resource.get("Type") == "AWS::Bedrock::Guardrail", (
        f"{logical_id} is not a guardrail in the snapshot. The pairs this file checks are "
        "named explicitly rather than found by type, so a rename is a red test rather "
        "than a silently narrower check.")
    return resource["Properties"]


def _version_description(template: dict, logical_id: str = "GuardrailVersion") -> str:
    resource = template["Resources"].get(logical_id)
    assert resource and resource.get("Type") == "AWS::Bedrock::GuardrailVersion", (
        f"{logical_id} is not a guardrail version in the snapshot.")
    return resource["Properties"]["Description"]


def policy_digest(template: dict, logical_id: str = "Guardrail") -> str:
    """This file's own digest of the enforced policy, computed from the snapshot.

    Deliberately NOT the CDK's algorithm. Canonical JSON with sorted keys, so a
    stranger re-derives it from the committed template without reading any
    TypeScript — and so it cannot drift into agreement with a sabotaged
    computation by sharing its code."""
    guardrail = _guardrail(template, logical_id)
    # `.get` returns None for a block this guardrail does not declare, and that
    # None is IN the digest deliberately: the tool-output guardrail declares no
    # topic policy, and if one ever appeared the digest must move.
    material = {block: guardrail.get(block) for block in POLICY_BLOCKS}
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]


@pytest.mark.parametrize("guardrail_id, version_id, pin_key", PAIRS)
def test_the_version_description_moved_when_the_policy_did(guardrail_id, version_id, pin_key):
    """**The assertion the plant defeats.** Not that the two digests agree — they
    are taken over different material and never will — but that neither can move
    alone. A policy change with a frozen description is a version resource that
    will not be replaced, which is a deploy that reports success and changes
    nothing."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    pinned = json.loads(PIN.read_text(encoding="utf-8"))["pairs"][pin_key]

    policy_now = policy_digest(template, guardrail_id)
    match = DESCRIPTION.match(_version_description(template, version_id))
    assert match, (
        f"{version_id}'s description is {_version_description(template, version_id)!r}, "
        "which is not "
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


@pytest.mark.parametrize("guardrail_id, version_id, pin_key", PAIRS)
def test_the_pin_covers_every_policy_block_the_guardrail_declares(
        guardrail_id, version_id, pin_key):
    """A coverage check on the coverage check. `POLICY_BLOCKS` is a hand-written
    list, and a hand-written list of what matters is the thing that goes stale —
    it is the same shape as the CDK's five-block list, one layer out.

    So: every `*PolicyConfig` property the guardrail actually declares must be in
    `POLICY_BLOCKS`. A new enforced block fails here rather than deploying over an
    unchanged pin. This does NOT close the seat's second finding — a block outside
    both digests still deploys silently until the CDK's list is widened too — but
    it means the next one is caught by a test instead of by a reviewer."""
    guardrail = _guardrail(json.loads(SNAPSHOT.read_text(encoding="utf-8")), guardrail_id)
    declared = {k for k in guardrail if k.endswith("PolicyConfig")}
    uncovered = declared - set(POLICY_BLOCKS)
    assert not uncovered, (
        f"the guardrail declares policy block(s) {sorted(uncovered)} that nothing digests. "
        "Bedrock enforces them, and a change to one would deploy as UPDATE_COMPLETE over an "
        "unchanged version pin. Add them to POLICY_BLOCKS here AND to `policyDigest` in "
        "gateway-stack.ts — this file alone cannot make the version resource replace itself."
    )


def test_every_guardrail_in_the_snapshot_is_pinned():
    """`PAIRS` is a hand-written list, and this file's whole subject is that a
    hand-written list of what matters goes stale.

    A third guardrail added to the stack without a line in `PAIRS` would be
    enforced by Bedrock, published as a version, and digested by nothing — the
    same failure the pin exists to prevent, one guardrail over. ADR-063 added the
    second and this file asserted there was one; that is the evidence this check
    is needed rather than the argument for it."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    in_snapshot = {name for name, r in template["Resources"].items()
                   if r.get("Type") == "AWS::Bedrock::Guardrail"}
    covered = {guardrail_id for guardrail_id, _, _ in PAIRS}
    assert in_snapshot == covered, (
        f"the snapshot declares guardrails {sorted(in_snapshot)} and this file pins "
        f"{sorted(covered)}. An unpinned guardrail is enforced and digested by nothing.")

    versions_in_snapshot = {name for name, r in template["Resources"].items()
                            if r.get("Type") == "AWS::Bedrock::GuardrailVersion"}
    assert versions_in_snapshot == {version_id for _, version_id, _ in PAIRS}, (
        "a guardrail version in the snapshot is not covered by PAIRS.")


# --- ADR-063: the tool-output guardrail, and the one way it may differ ----------
#
# Moved here from `tests/test_iam_assertions.py`, which was the wrong home: that
# file's rule is "G1's model-invoke allowlist and the assertions defending it",
# and these assert guardrail POLICY COMPOSITION, which is a different control.
# The misplacement was caught by `pave gate two-key` refusing one ADR for two
# ADR-requiring rules -- the checker was right and the fix is the move, not a
# second ADR written to satisfy it.

def _all_guardrails(template: dict) -> dict:
    return {name: res["Properties"] for name, res in template["Resources"].items()
            if res["Type"] == "AWS::Bedrock::Guardrail"}


def test_the_two_guardrails_differ_only_by_the_topic_policy():
    """ADR-063's whole content, asserted against the synth snapshot.

    The tool-output guardrail is built by omission from the gateway guardrail's
    own properties, so a filter added to one is added to both by construction.
    That is the answer to `handler._inspect`'s standing objection — *"a second
    policy would have been a second thing to keep in step"* — and this test is
    what makes the answer enforceable rather than a claim in a comment.

    **A second divergence is red.** Not "the filters match" but "nothing except
    the topic policy differs", so a field nobody thought about when this was
    written cannot drift silently. The measured justification for the one
    permitted difference is in ADR-063: the poisoned catalog and a schema-valid
    hostile payload both block under the topic-free policy naming
    `['PROMPT_ATTACK']`, so the topic was redundant on the cases it was kept
    for."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    guardrails = _all_guardrails(template)

    assert set(guardrails) == {"Guardrail", "ToolOutputGuardrail"}, (
        f"expected exactly the two guardrails ADR-063 describes, found {sorted(guardrails)}. "
        "A third is a policy nobody has reasoned about; a missing one is a channel "
        "inspected by something other than what this repo thinks."
    )

    main, tool = guardrails["Guardrail"], guardrails["ToolOutputGuardrail"]
    # `Name` and `Description` are identity, not policy, and must differ.
    ignored = {"Name", "Description"}
    differing = {
        key for key in set(main) | set(tool)
        if key not in ignored and main.get(key) != tool.get(key)
    }

    assert differing == {"TopicPolicyConfig"}, (
        f"the two guardrails differ by {sorted(differing)}. ADR-063 permits exactly one "
        "difference — the topic policy — and the tool-output guardrail is constructed by "
        "omission from the other so that nothing else CAN differ. Anything here is either "
        "a hand-written divergence or a field the omission does not cover."
    )


def test_the_tool_output_guardrail_has_no_topic_policy_and_keeps_every_filter():
    """The direction the test above cannot see on its own.

    `differing == {"TopicPolicyConfig"}` holds if the topic policy is absent from
    the tool-output guardrail — and would also hold if it were absent from BOTH
    and present nowhere, which is a guardrail that stopped denying topics
    entirely. Asserted separately so the two failures are distinguishable."""
    guardrails = _all_guardrails(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    main, tool = guardrails["Guardrail"], guardrails["ToolOutputGuardrail"]

    assert "TopicPolicyConfig" not in tool, (
        "the tool-output guardrail carries a topic policy, which is the one thing "
        "ADR-063 exists to remove from it.")
    assert main.get("TopicPolicyConfig", {}).get("TopicsConfig"), (
        "the MAIN guardrail has lost its topic policy. ADR-063 removes it from one "
        "channel, not from the platform.")
    assert (tool["ContentPolicyConfig"]["FiltersConfig"]
            == main["ContentPolicyConfig"]["FiltersConfig"]), (
        "the content filters differ between the two guardrails. `PROMPT_ATTACK` is what "
        "catches the injection this channel exists to stop (ADR-063 rows 1 and 5); a "
        "tool-output policy missing a filter is the failure that verification cannot see.")


def test_the_tool_output_guardrail_version_is_retained_and_pinned():
    """A published version is the instrument an observation was taken with.

    Same argument as `GuardrailVersion`: this one will be named by every
    tool-output observation from here on, and CloudFormation would delete it on
    the next policy change without RETAIN."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    version = template["Resources"]["ToolOutputGuardrailVersion"]

    assert version["DeletionPolicy"] == "Retain", (
        "ToolOutputGuardrailVersion is not retained. A policy change replaces the "
        "resource, and the old version — the instrument earlier observations name — "
        "goes with it.")
    assert "Pinned to policy " in json.dumps(version["Properties"]["Description"]), (
        "the version's description carries no policy digest, so a policy change would "
        "not replace it and a version number would stop naming a specific policy.")

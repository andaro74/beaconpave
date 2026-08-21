"""
`python services/highlights-agent/verify_guardrail_pin.py` — does the deployed
guardrail actually enforce the committed policy?

**Run this after every `cdk deploy` that touches the guardrail.** A green stack is
not evidence, and this is the check that says so.

## Why it exists

A guardrail version is an immutable snapshot. The version resource used to carry a
fixed description, so CloudFormation had no reason to replace it when the policy
underneath changed. ADR-024 narrowed a topic; `cdk deploy` reported
`UPDATE_COMPLETE`; `DRAFT` carried the new definition; and the gateway went on
enforcing **version 1 with the old one**. Nothing failed, nothing printed
differently, and the change was live nowhere.

The CDK now derives the version's description from a digest of the policy, so the
version resource replaces itself exactly when the policy changes. That is the fix.
**This is the proof**, and the distinction between the two is the whole point:
`tests/test_iam_assertions.py` checks the shape of the template, and a template is
a statement of intent. Only the deployed policy is the policy.

It is the same argument `gateway_client.fetch_record` makes about audit records —
the gateway's word for what it wrote is a self-report, and the harness fetches the
object independently. ADR-016 demoted an assert for being a self-report; a stack
status is one too.

Outside the hermetic surface: it imports boto3 and needs the account.

Owning seat: Platform Engineering (the mechanism) · Security (the policy).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import boto3  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "platform" / "infra" / "tests" / "fixtures" / "BeaconpaveGateway.template.json"


def committed_topics() -> dict:
    """The topic policy as committed, out of the synth snapshot."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    guardrails = [r for r in template["Resources"].values()
                  if r.get("Type") == "AWS::Bedrock::Guardrail"]
    topics = [t for g in guardrails
              for t in g["Properties"].get("TopicPolicyConfig", {}).get("TopicsConfig", [])]
    return {t["Name"]: t["Definition"] for t in topics}


def deployed_topics() -> tuple[dict, str]:
    """The topic policy the gateway is actually pinned to, fetched from Bedrock."""
    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    version = outputs["PinnedGuardrailVersion"]
    guard = boto3.client("bedrock").get_guardrail(
        guardrailIdentifier=outputs["PinnedGuardrailId"], guardrailVersion=version)
    return {t["name"]: t["definition"] for t in guard["topicPolicy"]["topics"]}, version


#: The blocks that make up "everything the guardrail actually enforces" — the
#: same five the CDK digests to force a new published version when the policy
#: changes (`gateway-stack.ts`). Listed explicitly rather than hashing the whole
#: response: `createdAt`, the ARN and the status move for reasons that are not
#: policy changes, and a digest that churned on those would be useless for the
#: thing it is recorded to answer.
POLICY_BLOCKS = ("topicPolicy", "contentPolicy", "sensitiveInformationPolicy")


def policy_digest(guard: dict) -> str:
    """A digest of the policy the deployed version actually enforces.

    `instrument.guardrail_policy_sha256` is "what the version referred to,
    fetched back from the deployed guardrail" (SPEC/04). A version NUMBER is a
    name; two entries naming version 2 are comparable only if version 2 meant the
    same thing both times, and the number alone cannot say so.

    Computed over the fetched policy rather than over the CDK construct, because
    the construct is a statement of intent and only the deployed policy is the
    policy — the same argument this file makes about a green stack. It therefore
    does NOT equal the 12-character digest in the version description, which is
    taken over the construct's own camelCase config; that one exists to force a
    version replacement, this one exists to be compared across entries. Canonical
    JSON, sorted keys, so a stranger re-derives it exactly.
    """
    material = {block: guard.get(block) for block in POLICY_BLOCKS}
    material["blockedInputMessaging"] = guard.get("blockedInputMessaging")
    material["blockedOutputsMessaging"] = guard.get("blockedOutputsMessaging")
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def deployed_guardrail() -> dict:
    """The raw fetched version, for callers that want more than the topics."""
    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    return boto3.client("bedrock").get_guardrail(
        guardrailIdentifier=outputs["PinnedGuardrailId"],
        guardrailVersion=outputs["PinnedGuardrailVersion"])


def main() -> int:
    if "--policy-digest" in sys.argv:
        # Deliberately prints the digest ALONE, so it can be substituted into a
        # `--guardrail-policy-sha256` argument without a human retyping it. A
        # retyped digest is a digest of whatever was typed.
        print(policy_digest(deployed_guardrail()))
        return 0

    want = committed_topics()
    got, version = deployed_topics()

    print(f"pinned guardrail version: {version}\n")
    drift = []
    for name in sorted(set(want) | set(got)):
        if want.get(name) == got.get(name):
            print(f"  OK    {name}")
            continue
        drift.append(name)
        print(f"  DRIFT {name}")
        print(f"        committed: {want.get(name)}")
        print(f"        deployed:  {got.get(name)}")

    if not drift:
        print(f"\nthe deployed policy is the committed policy ({len(want)} topic(s)).")
        return 0

    print(
        f"\nERROR: {len(drift)} topic(s) differ. The stack can report UPDATE_COMPLETE while "
        "this is true:\na guardrail version is an immutable snapshot, so if the version "
        "resource was not\nreplaced, the gateway is still enforcing the previous policy. "
        "Check that the version's\ndescription carries the policy digest, then deploy again.\n\n"
        "Do not run probes or record any score against this gateway until it passes: every "
        "number\nwould be attributed to a policy that is not the one in the diff."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

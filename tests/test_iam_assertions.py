"""
G1, asserted at synth time: no service role holds a model-invoke permission.

CLAUDE.md is unusually direct about this one — *"if your change makes that test
fail, the change is wrong, not the test."* These assertions run against the
committed synth snapshot rather than a live synth, because `make check` has to
pass offline on a fresh clone with no Node and no AWS account (G8). ADR-017
records that trade and the CI freshness job that keeps the snapshot honest.

**ADR-011 expired at M01.** Until this milestone, one path in the repo was
permitted to reach a model directly: `services/highlights-agent-baseline/`, the
ungoverned control. That permission was carried in prose, because the assertion
test it was supposed to be an exception *to* had never been written. This module
is that test, and it lands with no exception in it at all.

Hermetic. Owning seat: Platform Engineering, with Security on the invariant.
"""
import copy
import json
import pathlib

import pytest

from pave import infra

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "platform" / "infra" / "tests" / "fixtures"

SNAPSHOTS = sorted(SNAPSHOT_DIR.glob("*.template.json"))
IDS = [p.stem for p in SNAPSHOTS]

GATEWAY_SNAPSHOT = SNAPSHOT_DIR / "BeaconpaveGateway.template.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


# --- the scan is not vacuous -------------------------------------------------

def test_there_are_snapshots_to_assert_against():
    """A scan over zero templates is a pass that means nothing — the same
    argument as the empty rules registry and the empty hermetic surface. If the
    CDK app is renamed or the snapshot is deleted, this fails loudly rather than
    letting every assertion below go quietly vacuous."""
    assert SNAPSHOTS, f"no synth snapshots in {SNAPSHOT_DIR} — the G1 assertions below prove nothing"
    assert GATEWAY_SNAPSHOT.is_file(), "the gateway stack's snapshot is missing"


@pytest.mark.parametrize("path", SNAPSHOTS, ids=IDS)
def test_every_snapshot_declares_resources(path):
    assert load(path).get("Resources"), f"{path.name} synthesizes no resources"


# --- G1 ----------------------------------------------------------------------

@pytest.mark.parametrize("path", SNAPSHOTS, ids=IDS)
def test_no_role_outside_the_gateway_may_invoke_a_model(path):
    """The invariant itself. Every ALLOW of a model-invoke action must bind only
    to the gateway's own role."""
    offenders = []
    for grant in infra.model_invoke_grants(load(path)):
        for role in grant["roles"]:
            if not infra.is_gateway_role(role):
                offenders.append(f"{grant['policy']} grants {sorted(infra.actions_of(grant['statement']))} to {role}")

    assert not offenders, (
        "G1: a role outside the gateway holds a model-invoke permission:\n  "
        + "\n  ".join(offenders)
        + "\n\nThe gateway is the only path. This is not fixed by adding an entry to "
          "MODEL_INVOKE_ROLE_PREFIXES — see ADR-011, which expired at M01 precisely so that "
          "no such entry exists."
    )


def test_exactly_one_role_holds_the_grant():
    """A second role holding the grant would satisfy the test above if it were
    named like the gateway. Counting them stops a second control point appearing
    quietly — 'the gateway' is a singular noun in G1 on purpose."""
    granted = {role for grant in infra.model_invoke_grants(load(GATEWAY_SNAPSHOT)) for role in grant["roles"]}
    assert len(granted) == 1, f"expected exactly one model-invoking role, found {sorted(granted)}"


def test_the_governed_service_role_carries_an_explicit_deny():
    """Absence of a grant already denies. The explicit Deny is what survives a
    later careless grant, and what makes the CloudTrail event say why the call
    failed rather than merely that it did."""
    template = load(GATEWAY_SNAPSHOT)
    denied_roles = {role for entry in infra.model_invoke_denials(template) for role in entry["roles"]}
    service_roles = [r for r in infra.roles(template) if not infra.is_gateway_role(r)]

    assert service_roles, "no non-gateway role in the template — the Deny below would prove nothing"
    for role in service_roles:
        assert role in denied_roles, f"{role} has no explicit Deny on model-invoke actions"


def test_the_deny_covers_every_model_invoke_action():
    """A Deny naming only `InvokeModel` while `Converse` reaches the same model is
    the kind of gap that reads as covered."""
    for entry in infra.model_invoke_denials(load(GATEWAY_SNAPSHOT)):
        missing = infra.MODEL_INVOKE_ACTIONS - infra.actions_of(entry["statement"])
        assert not missing, f"{entry['policy']}: Deny omits {sorted(missing)}"


# --- ADR-011's epitaph -------------------------------------------------------

def test_the_grant_allowlist_has_exactly_one_entry():
    """**This is the deleted allowlist, kept deletable.**

    ADR-011 permitted exactly one direct-model path — the M00b control — and
    expired at M01. The exception is gone. The realistic way it comes back is not
    an ADR that somebody reviews, but a second string added here to make a
    failing assertion pass, in a diff about something else.

    So the length is pinned. If you are adding an entry you are writing a G1
    exception, and that needs the Security seat and an ADR, not a commit."""
    assert infra.MODEL_INVOKE_ROLE_PREFIXES == ("GatewayFn",), (
        "the model-invoke allowlist changed. ADR-011 expired at M01 and left it with one "
        "entry — the gateway. Adding another is a G1 exception (Security seat + ADR), not a "
        "test fix."
    )


# --- the assertions can actually fail ----------------------------------------

def test_the_assertion_catches_a_grant_it_should_catch():
    """The negative control, and the reason to trust everything above.

    A test that only ever runs against a compliant template proves that the
    template is compliant, not that the test would notice if it were not. M00a
    made the same argument about a gate that cannot block. Here the compliant
    snapshot is mutated in memory — the committed file is untouched — to add
    exactly the grant G1 forbids, and the checker must find it."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    service_roles = [r for r in infra.roles(template) if not infra.is_gateway_role(r)]
    assert service_roles, "no non-gateway role to plant a grant on"

    template["Resources"]["SmugglerPolicy"] = {
        "Type": "AWS::IAM::Policy",
        "Properties": {
            "Roles": [{"Ref": service_roles[0]}],
            "PolicyDocument": {
                "Statement": [
                    {"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*"}
                ]
            },
        },
    }

    offenders = [
        role
        for grant in infra.model_invoke_grants(template)
        for role in grant["roles"]
        if not infra.is_gateway_role(role)
    ]
    assert offenders == [service_roles[0]]


def test_the_assertion_catches_an_inline_role_policy():
    """The other shape CDK emits. A grant inlined on the role reads exactly like
    a standalone policy to a human and not at all like one to a parser that only
    looks at `AWS::IAM::Policy`."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    template["Resources"]["SmugglerRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "Policies": [
                {"PolicyDocument": {"Statement": [
                    {"Effect": "Allow", "Action": ["bedrock:Converse"], "Resource": "*"}
                ]}}
            ]
        },
    }

    offenders = [
        role
        for grant in infra.model_invoke_grants(template)
        for role in grant["roles"]
        if not infra.is_gateway_role(role)
    ]
    assert offenders == ["SmugglerRole"]


# --- the guardrail is a pinned instrument (ADR-018) --------------------------

def test_the_gateway_is_not_configured_against_a_draft_guardrail():
    """A DRAFT guardrail can be edited outside a commit and silently change every
    recorded probe result, with nothing printing differently when it happens.
    The deployed version must come from the pinned version resource."""
    template = load(GATEWAY_SNAPSHOT)
    functions = [
        r for r in template["Resources"].values()
        if r.get("Type") == "AWS::Lambda::Function"
        and "GUARDRAIL_VERSION" in r.get("Properties", {}).get("Environment", {}).get("Variables", {})
    ]
    assert functions, "no function configured with a guardrail version"
    for fn in functions:
        version = fn["Properties"]["Environment"]["Variables"]["GUARDRAIL_VERSION"]
        assert version != "DRAFT", "the gateway is pinned to DRAFT — see ADR-018"
        assert isinstance(version, dict), (
            f"GUARDRAIL_VERSION is the literal {version!r}; it must resolve from the "
            "CfnGuardrailVersion resource so the pin moves only when the stack does"
        )


#: Bedrock's cap on a topic definition. Not a style preference — the service
#: rejects a longer one with a 400 at deploy.
MAX_TOPIC_DEFINITION = 200


def test_guardrail_topic_definitions_fit_the_service_limit():
    """Caught the hard way: the first draft of these definitions carried the
    policy justification inline, ran to 235 and 310 characters, and CloudFormation
    rejected the stack.

    The failure was correct and arrived at the wrong end of the pipeline — the
    same argument `pave/verdict.py` makes about validating a verdict before
    writing it. A synth-time check costs nothing and turns a ten-minute deploy
    round trip into a test failure with the offending topic named.

    Worth keeping for a second reason: a definition is a *classifier input*.
    Bedrock hands it to the model that decides whether a turn is on-topic, so
    padding it with rationale makes it a worse discriminator as well as a longer
    one. The limit is a nudge toward the right content, not just less of it."""
    template = load(GATEWAY_SNAPSHOT)
    guardrails = [
        r for r in template["Resources"].values() if r.get("Type") == "AWS::Bedrock::Guardrail"
    ]
    assert guardrails, "no guardrail in the stack"

    topics = [
        topic
        for guard in guardrails
        for topic in guard["Properties"].get("TopicPolicyConfig", {}).get("TopicsConfig", [])
    ]
    assert topics, "the guardrail declares no denied topics — this check would prove nothing"

    for topic in topics:
        length = len(topic["Definition"])
        assert length <= MAX_TOPIC_DEFINITION, (
            f"topic {topic['Name']!r} definition is {length} chars, over Bedrock's "
            f"{MAX_TOPIC_DEFINITION}. Move the rationale to a comment and ADR-018 — the "
            "definition is what the classifier reads."
        )


def test_a_published_guardrail_version_exists():
    template = load(GATEWAY_SNAPSHOT)
    kinds = {r.get("Type") for r in template["Resources"].values()}
    assert "AWS::Bedrock::Guardrail" in kinds, "no guardrail in the stack"
    assert "AWS::Bedrock::GuardrailVersion" in kinds, (
        "the guardrail has no published version resource — the gateway would have to run "
        "against DRAFT (ADR-018)"
    )

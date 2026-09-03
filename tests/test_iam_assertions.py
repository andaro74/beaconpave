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
import re

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
    the kind of gap that reads as covered.

    Reads `Action` literally, so a Deny written with `NotAction` fails here even
    though it denies *more*. That is deliberate and it is the fail-closed
    direction: this repository deploys one Deny shape, and an unrecognized one
    should stop a reviewer rather than be reasoned about by a checker."""
    for entry in infra.model_invoke_denials(load(GATEWAY_SNAPSHOT)):
        missing = infra.MODEL_INVOKE_ACTIONS - infra.actions_of(entry["statement"])
        assert not missing, (
            f"{entry['policy']}: Deny omits {sorted(missing)}. If this Deny is written with "
            "NotAction it denies more, not less — say so in an ADR and widen this check "
            "deliberately rather than here.")


def test_every_deny_is_in_force_for_every_model():
    """**A Deny is not a boolean, and it was read as one.**

    `model_invoke_denials` checked `Effect` and the action list and nothing else,
    so two shapes read as full coverage while denying almost nothing — both
    measured green against a live snapshot by the Security seat:

      - `"Resource": "arn:...:foundation-model/a-model-nobody-uses"`, a Deny on a
        model the platform does not call, which forbids nothing it does;
      - a `"Condition"` that never matches, a Deny that is never in force.

    Filtering happens in `model_invoke_denials`, so the shapes simply stop
    counting as denials and `test_the_governed_service_role_carries_an_explicit_deny`
    goes red. This asserts the property directly as well, because that indirection
    is exactly the kind a later refactor removes without noticing."""
    template = load(GATEWAY_SNAPSHOT)
    denials = infra.model_invoke_denials(template)
    assert denials, "no effective model-invoke Deny in the stack"
    for entry in denials:
        statement = entry["statement"]
        assert not statement.get("Condition"), (
            f"{entry['policy']}: the model-invoke Deny carries a Condition, so it is not "
            "in force for every request. A conditional Deny is a Deny-shaped object.")
        assert "*" in infra._as_list(statement.get("Resource")), (
            f"{entry['policy']}: the model-invoke Deny names "
            f"{statement.get('Resource')!r} rather than every resource. A Deny scoped to "
            "one model ARN forbids nothing the platform actually calls.")


# --- the path that carries no model action at all ----------------------------

def test_no_identity_in_this_stack_may_assume_another_role_in_it():
    """**G1's transitive hole, and the checker had no concept of it.**

    The tool's Deny is an *identity* policy on the tool's role. `sts:AssumeRole`
    produces a different session carrying the gateway role's `bedrock:InvokeModel`
    Allow — so the tool reaches a model with the Deny still standing and every
    assertion in this file green. The Security seat measured exactly that, and it
    is one CDK line with no escape hatch:
    `gatewayFn.role.grantAssumeRole(toolFn.grantPrincipal)`.

    The rule is blunt on purpose: **no role in this stack assumes another role in
    it.** Nothing here needs to, every role is assumed by `lambda.amazonaws.com`
    and nothing else, and a narrower rule would have to decide which crossings are
    safe — which is the reasoning that produced the hole."""
    template = load(GATEWAY_SNAPSHOT)
    in_stack = set(infra.roles(template))
    offenders = sorted(
        f"{entry['policy']} lets {sorted(entry['roles'])} assume {sorted(entry['targets'] & in_stack)}"
        for entry in infra.assume_role_grants(template)
        if entry["targets"] & in_stack
    )
    assert not offenders, (
        "a role in this stack may assume another:\n  " + "\n  ".join(offenders)
        + "\n\nG1 says the gateway is the only path to a model. A role that can become the "
          "gateway's role is a second path, and it carries no model action for any check to "
          "find."
    )


def test_no_role_trusts_an_identity_from_this_stack():
    """The other half, and the half no role-policy scan can see.

    Assuming a role needs a grant on the assumer **and** a `Principal` in the
    target's `AssumeRolePolicyDocument`. Asserting on both means either one alone
    is a failure rather than only the pair — the fail-closed direction, and the
    one that catches a trust policy widened in advance of the grant."""
    template = load(GATEWAY_SNAPSHOT)
    in_stack = set(infra.roles(template))
    trusts = infra.trust_principals(template)
    assert trusts, "no role trust policies found; this assertion would prove nothing"
    for entry in trusts:
        named = entry["logical_ids"] & in_stack
        assert not named, (
            f"{entry['role']}'s trust policy lets {sorted(named)} assume it. Every role here "
            "is assumed by a service principal and nothing else.")
        assert entry["services"], (
            f"{entry['role']}'s trust policy names no service principal: "
            f"{entry['principal']!r}. An AWS-principal trust is how a role becomes reachable "
            "from an identity this stack does not describe.")


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

def offenders_in(template):
    """Roles outside the gateway holding a model-invoke grant."""
    return {
        role
        for grant in infra.model_invoke_grants(template)
        for role in grant["roles"]
        if not infra.is_gateway_role(role)
    }


def test_the_assertion_catches_a_standalone_policy_grant():
    """The negative control, and the reason to trust everything above.

    A test that only ever runs against a compliant template proves that the
    template is compliant, not that the test would notice if it were not. M00a
    made the same argument about a gate that cannot block. Here the committed
    snapshot is copied in memory — the file is untouched — and given exactly the
    grant G1 forbids, on a role that did not previously hold one.

    Measured as a DELTA against the same template before planting. The earlier
    absolute form asserted the planted role was the *only* offender, which
    silently assumed the committed snapshot was compliant; M01's exhibit PR broke
    that assumption and the test then reported that the assertion had NOT caught
    what it should — the opposite of true. What is under test is the detection,
    never the baseline's cleanliness."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    before = offenders_in(template)

    template["Resources"]["SmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}
    template["Resources"]["SmugglerPolicy"] = {
        "Type": "AWS::IAM::Policy",
        "Properties": {
            "Roles": [{"Ref": "SmugglerRole"}],
            "PolicyDocument": {"Statement": [
                {"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*"}
            ]},
        },
    }
    assert offenders_in(template) - before == {"SmugglerRole"}


def test_the_assertion_catches_an_inline_role_policy():
    """The other shape CDK emits, which is what these two tests actually differ
    on. A grant inlined on the role reads exactly like a standalone policy to a
    human and not at all like one to a parser that only looks at
    `AWS::IAM::Policy`."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    before = offenders_in(template)

    template["Resources"]["InlineSmugglerRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "Policies": [
                {"PolicyDocument": {"Statement": [
                    {"Effect": "Allow", "Action": ["bedrock:Converse"], "Resource": "*"}
                ]}}
            ]
        },
    }
    assert offenders_in(template) - before == {"InlineSmugglerRole"}


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


# --- the snapshot must reproduce on a machine that did not record it ---------

def test_normalize_drops_cdk_telemetry():
    """`AWS::CDK::Metadata` carries a deflate-compressed analytics blob. It moves
    with the construct-library version and is not guaranteed byte-stable across
    zlib builds, so Windows and Linux can disagree on it for identical input.

    The first CI run of the freshness job failed on exactly this: it reported
    drift against a snapshot that was byte-identical when re-synthesized locally.
    A snapshot that only reproduces on the machine that recorded it is not a
    snapshot, and the freshness job that depends on it is not a check."""
    template = {"Resources": {
        "CDKMetadata": {"Type": "AWS::CDK::Metadata", "Properties": {"Analytics": "v2:deflate64:xxx"}},
        "GatewayFnServiceRole": {"Type": "AWS::IAM::Role", "Properties": {}},
    }}
    kept = infra.normalize(template)["Resources"]
    assert "CDKMetadata" not in kept
    assert "GatewayFnServiceRole" in kept, "normalization dropped a real resource"


def test_normalize_keeps_everything_the_assertion_reads():
    """The counterweight. Dropping telemetry is safe; dropping a policy would make
    every assertion above vacuous while leaving them green."""
    template = infra.normalize(load(GATEWAY_SNAPSHOT))
    kinds = {r["Type"] for r in template["Resources"].values()}
    for required in ("AWS::IAM::Role", "AWS::IAM::Policy", "AWS::Bedrock::Guardrail"):
        assert required in kinds, f"normalization removed {required}"
    assert infra.model_invoke_grants(template), "no grant survives normalization to assert against"
    assert infra.model_invoke_denials(template), "no Deny survives normalization to assert against"


#: The version resource's description carries a digest of the policy it pins, so
#: CloudFormation replaces it exactly when the policy changes. A fixed string here
#: is the defect this pattern exists to prevent — see the test below.
POLICY_PIN = re.compile(r"^Pinned to policy [0-9a-f]{12}\.$")


def test_the_guardrail_version_follows_the_policy_it_pins():
    """**The pin worked in the direction nobody tested, and it cost a deploy.**

    A guardrail version is an immutable snapshot. With a fixed description on the
    version resource, CloudFormation had no reason to replace it when the policy
    underneath changed — so ADR-024 narrowed a topic, `cdk deploy` reported
    UPDATE_COMPLETE, DRAFT carried the new definition, and the gateway went on
    enforcing version 1 with the old one. Nothing failed. Nothing printed
    differently. The stack was green and the change was live nowhere.

    That is ADR-018's failure with the sign reversed. ADR-018 stopped the enforced
    policy drifting away from the committed one; this stops the committed policy
    failing to reach the enforced one. **A pin that only holds in the direction you
    happened to test is not a pin**, and the untested direction is the one where a
    security control silently does not change.

    This checks the shape at synth time. It cannot check that the deployed version
    matches — that needs the account, and
    `services/highlights-agent/verify_guardrail_pin.py` is what does it after a
    deploy, by fetching the policy back rather than trusting the stack's status.
    """
    template = load(GATEWAY_SNAPSHOT)
    versions = [
        r for r in template["Resources"].values()
        if r.get("Type") == "AWS::Bedrock::GuardrailVersion"
    ]
    assert versions, "no published guardrail version in the stack — see ADR-018"
    for version in versions:
        description = version["Properties"].get("Description", "")
        assert POLICY_PIN.match(description), (
            f"the guardrail version description is {description!r}. It must carry a digest "
            "of the policy it pins, or CloudFormation will not replace the version when the "
            "policy changes — and the gateway will go on enforcing the old one with the "
            "stack reporting success."
        )


# --- the three shapes M03 measured as invisible, closed at M04 ----------------
#
# Named for M04 by the Security seat at M03's close: `AWS::IAM::RolePolicy`, a
# `ManagedPolicyArns` attachment, and a `GatewayFn`-prefixed role name. **A gate
# cannot fail closed on an invariant its checker is blind to**, and M04 is the
# milestone that makes probe outcomes block merges, so the checker underneath
# them has to see every shape the grant can take.


def test_the_walker_covers_every_shape_that_can_carry_a_statement():
    """`GRANT_SHAPES` and `statements()` must agree.

    Two of the four types were added after somebody planted a grant that every G1
    assertion waved through, and both times the walker looked complete. The list
    is what makes "complete" checkable: a type added here without a branch in the
    walker fails, rather than silently widening the blind spot it was meant to
    close."""
    source = (ROOT / "pave" / "infra.py").read_text(encoding="utf-8")
    start = source.index("def statements(")
    body = source[start:source.index("\ndef ", start + 10)]
    for shape in infra.GRANT_SHAPES:
        assert f'"{shape}"' in body, f"GRANT_SHAPES names {shape} and the walker does not handle it"


def test_the_assertion_catches_a_standalone_role_policy_resource():
    """**Shape one, measured as invisible at M03.**

    `AWS::IAM::RolePolicy` is a CloudFormation resource naming a single role in
    `RoleName` rather than a `Roles` list. CDK emits it for an escape-hatch
    `CfnRolePolicy`. Before this shape was walked, the grant below passed every
    G1 assertion in the repository."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    before = offenders_in(template)

    template["Resources"]["SmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}
    template["Resources"]["SmugglerRolePolicy"] = {
        "Type": "AWS::IAM::RolePolicy",
        "Properties": {
            "RoleName": {"Ref": "SmugglerRole"},
            "PolicyDocument": {"Statement": [
                {"Effect": "Allow", "Action": "bedrock:Converse", "Resource": "*"}
            ]},
        },
    }
    assert offenders_in(template) - before == {"SmugglerRole"}


def test_a_managed_policy_attached_by_arn_blocks_rather_than_passing():
    """**Shape two, and it is the interesting one.**

    The other two shapes are grants written somewhere the checker did not look,
    and the fix is to look there. This one the checker *cannot* look at: an
    attached managed policy's document lives in IAM, not in the template. A role
    carrying `ManagedPolicyArns` could hold `bedrock:InvokeModel` and every
    assertion in this file would pass, because each of them reasons over
    statements the template contains.

    So there is no wording of the assertion that reads it, and fail-closed on the
    attachment is the only correct answer. Arriving at that required the shape to
    be planted first — reasoning about it produced a better `statements()` and
    would have left the hole open."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    assert not infra.unreadable_managed_policies(template), (
        "the committed snapshot already attaches a managed policy nobody has reviewed")

    template["Resources"]["SmugglerRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {"ManagedPolicyArns": [
            {"Fn::Join": ["", ["arn:", {"Ref": "AWS::Partition"},
                               ":iam::aws:policy/AmazonBedrockFullAccess"]]}
        ]},
    }
    unreadable = infra.unreadable_managed_policies(template)
    assert [a["role"] for a in unreadable] == ["SmugglerRole"]
    assert "AmazonBedrockFullAccess" in unreadable[0]["arn"]
    # And the statement walker still sees nothing, which is the whole point.
    assert offenders_in(template) == offenders_in(load(GATEWAY_SNAPSHOT))


def test_the_readable_exception_list_has_exactly_one_entry():
    """The same argument as `MODEL_INVOKE_ROLE_PREFIXES`, one field over.

    The realistic way this protection is lost is not an ADR anybody reviews but a
    second ARN added here to make a failing assertion pass, in a diff about
    something else. `AWSLambdaBasicExecutionRole` is AWS-managed, grants
    CloudWatch Logs only, and cannot be edited by this account, so its contents
    are a published fact. A CUSTOMER-managed policy is editable outside any diff
    this gate can see, which is exactly the hole."""
    assert len(infra.MODEL_INVOKE_READABLE_EXCEPTIONS) == 1
    assert infra.MODEL_INVOKE_READABLE_EXCEPTIONS[0].endswith("AWSLambdaBasicExecutionRole")


def test_every_committed_role_attaches_only_reviewed_managed_policies():
    """The live assertion. Every Lambda in the stack attaches
    `AWSLambdaBasicExecutionRole`, so this is not vacuous — it is passing on
    three real attachments the seat has reviewed."""
    template = load(GATEWAY_SNAPSHOT)
    assert infra.attached_managed_policies(template), (
        "no managed policy attachments at all — this assertion would prove nothing")
    assert infra.unreadable_managed_policies(template) == []


def test_exactly_one_role_is_treated_as_the_gateway():
    """**Shape three.** `is_gateway_role` is a prefix match, because CDK appends a
    hash to every logical id and the exact name is not knowable in advance.

    The consequence is that a second role named `GatewayFnSomethingElse` inherits
    the one-role allowlist — and a role that inherits it is excluded from
    `test_the_governed_service_role_carries_an_explicit_deny`, so it escapes the
    Deny every other role in the stack carries. G1 says "the gateway", a singular
    noun; this is what makes the noun checkable."""
    assert infra.gateway_roles(load(GATEWAY_SNAPSHOT)) == ["GatewayFnServiceRole97795AA7"]


def test_a_second_gateway_prefixed_role_is_caught_rather_than_inheriting_the_allowlist():
    """The planted defect for shape three, and it plants the *escape* rather than
    the grant.

    A second `GatewayFn`-prefixed role holding a grant is already caught by
    `test_exactly_one_role_holds_the_grant`, which counts granted roles. What was
    NOT caught is a role that inherits the prefix and therefore never has to carry
    an explicit Deny — a control point that exists, is exempt, and is invisible to
    every other assertion here."""
    template = copy.deepcopy(load(GATEWAY_SNAPSHOT))
    template["Resources"]["GatewayFnSmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}

    # It escapes the Deny requirement, which is the hole.
    denied = {role for entry in infra.model_invoke_denials(template) for role in entry["roles"]}
    service_roles = [r for r in infra.roles(template) if not infra.is_gateway_role(r)]
    assert "GatewayFnSmugglerRole" not in service_roles
    assert "GatewayFnSmugglerRole" not in denied

    # And this is what notices.
    assert len(infra.gateway_roles(template)) == 2


# --- ADR-063: the tool-output guardrail, and the one way it may differ ----------

def _guardrails(template: dict) -> dict:
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
    template = load(SNAPSHOT_DIR / "BeaconpaveGateway.template.json")
    guardrails = _guardrails(template)

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
    guardrails = _guardrails(load(SNAPSHOT_DIR / "BeaconpaveGateway.template.json"))
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
    template = load(SNAPSHOT_DIR / "BeaconpaveGateway.template.json")
    version = template["Resources"]["ToolOutputGuardrailVersion"]

    assert version["DeletionPolicy"] == "Retain", (
        "ToolOutputGuardrailVersion is not retained. A policy change replaces the "
        "resource, and the old version — the instrument earlier observations name — "
        "goes with it.")
    assert "Pinned to policy " in json.dumps(version["Properties"]["Description"]), (
        "the version's description carries no policy digest, so a policy change would "
        "not replace it and a version number would stop naming a specific policy.")

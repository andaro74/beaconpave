"""
G3 at the infrastructure layer, asserted at synth time.

**These are the assertions the Security seat pre-registered for the deploy
commit**, and ADR-019 said in as many words why they were owed: until the tool
deployed as its own function with its own grant, "G3 rests on the plane rather
than on IAM". The plane is a control the gateway applies to callers that go
through it. A caller that can invoke the tool function directly has not defeated
the plane — it has gone around it, and no amount of Cedar helps.

So there are three separate things to be false here, and they fail differently:

- an **identity** grant: some role holding `lambda:InvokeFunction` on the tool.
  Read from role policies, which is where a careless `grantInvoke` lands.
- a **resource** policy: `AWS::Lambda::Permission` letting a principal in from
  the other side. Invisible to every check that reads role policies, and the
  gateway's own narrow grant still looks correct beside it.
- a **network** route: `AWS::Lambda::Url`, a public HTTPS endpoint in front of
  the function with nothing in between.

Reading the committed snapshot rather than synthesizing, for the reason ADR-017
records: `make check` is hermetic and CI re-synthesizes and diffs.

Hermetic. Owning seat: Security, with Platform Engineering on the mechanism.
"""
import copy
import json
import pathlib

import pytest
import yaml

from pave import infra

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATEWAY_SNAPSHOT = ROOT / "platform" / "infra" / "tests" / "fixtures" / "BeaconpaveGateway.template.json"
REGISTRY = ROOT / "platform" / "registry" / "tools.yaml"


def load():
    return json.loads(GATEWAY_SNAPSHOT.read_text(encoding="utf-8"))


def registry_ids():
    return {tool["id"] for tool in yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))}


# --- the scan is not vacuous -------------------------------------------------

def test_the_gateway_routes_at_least_one_tool():
    """Every assertion below is about the routed tools, so a template routing none
    would pass all of them while proving nothing — the empty-registry failure this
    repo has now written the same test for four times."""
    routed = infra.routed_tools(load())
    assert routed, (
        "the gateway's TOOL_FUNCTIONS names no tool. Either the tool plane is not "
        "deployed, or the routing table moved and these assertions have gone vacuous."
    )


def test_every_routed_tool_is_in_the_registry():
    """G3's first half, before any IAM. A function the gateway is willing to call
    and the registry does not name is an unregistered tool that is reachable —
    with a Cedar policy set that has nothing to say about it, because Cedar is
    generated from the registry that does not name it."""
    unregistered = sorted(set(infra.routed_tools(load())) - registry_ids())
    assert not unregistered, (
        f"the gateway routes {unregistered}, which platform/registry/tools.yaml does not "
        "name. Unregistered tools are unreachable (G3) — and the generated policy set "
        "would have no permit and no forbid for these, so the plane would deny them while "
        "the stack stood ready to call them."
    )


def test_every_routed_tool_resolves_to_a_function_in_this_stack():
    template = load()
    deployed = infra.functions(template)
    for tool_id, logical_id in infra.routed_tools(template).items():
        assert logical_id in deployed, (
            f"{tool_id} routes to {logical_id!r}, which is not a Lambda function in this "
            "stack. The gateway would offer the model a tool it cannot call, and the loop "
            "bound would take the blame for a deployment gap."
        )


# --- only the gateway may invoke a tool --------------------------------------

def invokers_of_tools(template):
    """Roles holding an invoke grant on a routed tool function."""
    targets = set(infra.routed_tools(template).values())
    return {
        (role, logical)
        for grant in infra.tool_invoke_grants(template)
        for logical in infra.invoke_targets(grant["statement"]) & targets
        for role in grant["roles"]
    }


def test_only_the_gateways_own_role_may_invoke_a_tool():
    """The invariant. `is_gateway_role` is the same predicate G1 uses, so the two
    invariants agree about which role is the control point rather than each
    deciding for itself."""
    offenders = sorted(
        f"{role} may invoke {logical}"
        for role, logical in invokers_of_tools(load())
        if not infra.is_gateway_role(role)
    )
    assert not offenders, (
        "a role outside the gateway may invoke a tool function:\n  " + "\n  ".join(offenders)
        + "\n\nThe plane is what authorizes a tool call (G3). A caller that can invoke the "
          "tool directly has not defeated the plane, it has gone around it."
    )


def test_the_gateway_actually_holds_the_grant():
    """The counterweight. The assertion above is satisfied by a template where
    *nobody* may invoke the tool — including one where the grant was dropped and
    the gateway is about to fail at run time with an AccessDenied that reads like
    a Bedrock problem."""
    template = load()
    targets = set(infra.routed_tools(template).values())
    granted = {logical for _, logical in invokers_of_tools(template)}
    assert granted == targets, f"no invoke grant for {sorted(targets - granted)}"


def test_no_invoke_grant_is_a_wildcard():
    """A wildcard invoke grant is how a tool added to the registry later becomes
    reachable without anybody granting anything: the grant that already covers it
    was written before it existed, so the diff that adds the tool contains no IAM
    change to review."""
    wide = [entry["policy"] for entry in infra.wildcard_invoke_grants(load())]
    assert not wide, f"invoke grant(s) with a wildcard resource: {sorted(set(wide))}"


def test_a_tool_function_reaches_no_model():
    """G1 covers this generically — every non-gateway role carries the Deny — but
    a tool is the newest place a model grant would look reasonable, so it is
    asserted by name as well. A tool that could call a model would be a second
    control point, and G1 is a singular noun on purpose."""
    template = load()
    denied = {role for entry in infra.model_invoke_denials(template) for role in entry["roles"]}
    for tool_id, logical_id in infra.routed_tools(template).items():
        role = infra.referenced_logical_ids(
            infra.functions(template)[logical_id]["Properties"]["Role"])
        assert role & denied, f"{tool_id}'s role holds no explicit model-invoke Deny"


# --- the two routes that are invisible to a role-policy check ----------------

def test_no_function_in_the_stack_has_a_public_url():
    """A function URL is a public HTTPS endpoint in front of a function. One on a
    tool is a route to that tool with no plane in front of it: G3 held in the code
    and lost at the network, with every IAM assertion above still green."""
    assert infra.function_urls(load()) == []


def test_no_resource_policy_opens_a_function_to_a_wildcard_principal():
    """A resource policy grants invoke from the *other* side, so it does not
    appear in any role's policy — the gateway's narrow grant would still read as
    correct beside a `Principal: "*"` that lets in the world."""
    assert infra.open_invoke_permissions(load()) == []


# --- the assertions can actually fail ----------------------------------------
#
# Measured as a DELTA against the same template before planting. PR #13's lesson,
# learned at the cost of an exhibit that showed two failures and was read as the
# detector being broken: a control asserting "the planted thing is the only
# offender" quietly assumes the fixture was clean, and proves the fixture rather
# than the detector.

def test_the_assertion_catches_a_second_role_granted_invoke():
    template = copy.deepcopy(load())
    before = invokers_of_tools(template)
    target = next(iter(infra.routed_tools(template).values()))

    template["Resources"]["SmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}
    template["Resources"]["SmugglerPolicy"] = {
        "Type": "AWS::IAM::Policy",
        "Properties": {
            "Roles": [{"Ref": "SmugglerRole"}],
            "PolicyDocument": {"Statement": [{
                "Effect": "Allow",
                "Action": "lambda:InvokeFunction",
                "Resource": {"Fn::GetAtt": [target, "Arn"]},
            }]},
        },
    }
    planted = {role for role, _ in invokers_of_tools(template)} - {r for r, _ in before}
    assert planted == {"SmugglerRole"}


def test_the_assertion_catches_a_wildcard_invoke_grant():
    template = copy.deepcopy(load())
    before = len(infra.wildcard_invoke_grants(template))

    template["Resources"]["WideRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {"Policies": [{"PolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": ["lambda:InvokeFunction"], "Resource": "*"},
        ]}}]},
    }
    assert len(infra.wildcard_invoke_grants(template)) - before == 1


def test_the_assertion_catches_a_function_url():
    template = copy.deepcopy(load())
    before = set(infra.function_urls(template))
    template["Resources"]["ToolUrl"] = {
        "Type": "AWS::Lambda::Url",
        "Properties": {"AuthType": "NONE"},
    }
    assert set(infra.function_urls(template)) - before == {"ToolUrl"}


def test_the_assertion_catches_an_open_resource_policy():
    template = copy.deepcopy(load())
    before = set(infra.open_invoke_permissions(template))
    template["Resources"]["OpenDoor"] = {
        "Type": "AWS::Lambda::Permission",
        "Properties": {"Action": "lambda:InvokeFunction", "Principal": "*"},
    }
    assert set(infra.open_invoke_permissions(template)) - before == {"OpenDoor"}


def test_the_assertion_catches_an_unregistered_routed_tool():
    """The G3 negative control. A routing table naming a tool the registry does
    not must be caught — this is the static half of the claim, and the exhibit PR
    is the other half."""
    routed = dict(infra.routed_tools(load()))
    routed["catalog-search-v2"] = "SomeFunction"
    assert sorted(set(routed) - registry_ids()) == ["catalog-search-v2"]


# --- the routing table is read, not restated ---------------------------------

def test_the_routing_table_is_parsed_from_the_gateways_own_environment():
    """These assertions follow the table the running gateway follows. A list of
    tool ids in this file would be a second copy, and the failure mode of a second
    copy is that it stays green while the first one moves."""
    template = load()
    _, gateway = infra.gateway_function(template)
    variables = gateway["Properties"]["Environment"]["Variables"]
    assert infra.TOOL_ROUTING_ENV in variables
    assert set(infra.routed_tools(template)) == {"catalog-search"}


def test_an_unreadable_routing_table_fails_loudly():
    """Rather than returning an empty dict, which would make every assertion above
    pass by having nothing to assert about — the exact shape of vacuous green this
    file opens by warning against."""
    template = copy.deepcopy(load())
    _, gateway = infra.gateway_function(template)
    gateway["Properties"]["Environment"]["Variables"][infra.TOOL_ROUTING_ENV] = {
        "Fn::Join": ["", ['{"a":"', {"Ref": "X"}, '","b":"', {"Ref": "Y"}, '","c":"']]
    }
    with pytest.raises(AssertionError, match="cannot read"):
        infra.routed_tools(template)

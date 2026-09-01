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

def function_names(template):
    """Deployed function name -> logical id, so a grant naming a tool by literal
    ARN string resolves. Without this, `invoke_targets` saw only `Ref`/`GetAtt`
    and a smuggler role granted invoke by ARN string dropped out of the
    intersection entirely — the Security seat planted exactly that and the whole
    suite stayed green."""
    names = {}
    for logical_id, resource in infra.functions(template).items():
        name = resource.get("Properties", {}).get("FunctionName")
        if isinstance(name, str):
            names[name] = logical_id
        # CDK usually leaves FunctionName unset (CloudFormation generates it), so
        # the logical id is also matched as text — a hand-written ARN in a review
        # is far more likely to carry a readable name than a generated one.
        names[logical_id] = logical_id
    return names


def invokers_of_tools(template):
    """Roles holding an invoke grant on a routed tool function."""
    targets = set(infra.routed_tools(template).values())
    by_name = function_names(template)
    return {
        (role, logical)
        for grant in infra.tool_invoke_grants(template)
        for logical in infra.invoke_targets(grant["statement"], by_name) & targets
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


def test_the_gateway_may_invoke_nothing_but_a_routed_tool():
    """The counterpart to `test_only_the_gateways_own_role_may_invoke_a_tool`, and
    the half that was missing. That one asks *who may invoke a tool*; this one asks
    *what the gateway may invoke*, and every other assertion in this file is scoped
    to `infra.routed_tools`, so a function outside the routing table was outside all
    of them.

    **Measured, by the Platform Engineering seat, against the closure this milestone
    introduced.** `deployTool` grants the gateway invoke from inside itself, so a
    third call to it deploys a fully-formed Lambda -- gateway-invocable, holding
    `s3:GetObject` on `*` -- that no assertion in the repository knew existed:
    `2373 passed, 6 skipped`, exactly the baseline, and the snapshot re-recorded
    without complaint. G1 still held, because the model-invoke Deny is enforced over
    every non-gateway role rather than over routed tools. G3 did not.

    A grant is the right thing to assert on rather than an inventory of functions.
    A Lambda nobody may invoke is inert; a Lambda the gateway may invoke is a tool
    whether or not the registry calls it one."""
    template = load()
    targets = set(infra.routed_tools(template).values())
    by_name = function_names(template)
    reachable = {
        logical
        for grant in infra.tool_invoke_grants(template)
        for role in grant["roles"] if infra.is_gateway_role(role)
        for logical in infra.invoke_targets(grant["statement"], by_name)
    }
    assert targets, "no routed tools; this comparison would be vacuous"
    stray = sorted(reachable - targets)
    assert not stray, (
        f"the gateway holds lambda:InvokeFunction on {stray}, which the routing table "
        "does not name. Unregistered tools are unreachable (G3), and a function the "
        "gateway may call is a tool whichever file declares it: Cedar has no permit and "
        "no forbid for it, and every other assertion in this file skips it."
    )


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


def test_no_resource_policy_lets_anything_but_the_gateway_in():
    """A resource policy grants invoke from the *other* side, so it does not appear
    in any role's policy — the gateway's narrow grant reads as correct beside it.

    **The assertion is "only the gateway", not "no wildcard".** The first version
    flagged only `Principal: "*"`, so `apigateway.amazonaws.com` or a specific
    foreign account id passed — and either is exactly "G3 held in the code and lost
    at the network". The file's own docstring claimed the broad property while the
    code delivered the narrow one, which is this repo's named worst failure mode
    appearing in the test that exists to prevent it."""
    template = load()
    gateway, _ = infra.gateway_function(template)
    offenders = [
        entry for entry in infra.invoke_permissions(template)
        if gateway not in infra.referenced_logical_ids(entry["principal"])
    ]
    assert offenders == [], (
        f"resource policy grants invoke to something other than the gateway: {offenders}"
    )


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


def test_the_assertion_catches_a_grant_naming_the_tool_by_literal_arn():
    """**The one that got through.** `invoke_targets` read only `Ref` and
    `Fn::GetAtt`, so a statement naming the function by ARN string resolved to the
    empty set and dropped out of the intersection the assertion is built on. The
    original negative controls planted `Fn::GetAtt` only — they proved the detector
    against its own happy path, which is the failure PR #13 taught and this file's
    own comment claims to have learned."""
    template = copy.deepcopy(load())
    before = invokers_of_tools(template)
    target = next(iter(infra.routed_tools(template).values()))

    template["Resources"]["ArnSmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}
    template["Resources"]["ArnSmugglerPolicy"] = {
        "Type": "AWS::IAM::Policy",
        "Properties": {
            "Roles": [{"Ref": "ArnSmugglerRole"}],
            "PolicyDocument": {"Statement": [{
                "Effect": "Allow",
                "Action": "lambda:InvokeFunction",
                # Account-less on purpose. `tests/test_no_account_identifiers.py`
                # rejects a redacted account field as firmly as a real one — the
                # redaction habit is what lets a real one through later — and this
                # detector matches on the function name, not the account.
                "Resource": f"arn:aws:lambda:us-west-2::function:{target}",
            }]},
        },
    }
    planted = {role for role, _ in invokers_of_tools(template)} - {r for r, _ in before}
    assert planted == {"ArnSmugglerRole"}


def test_the_assertion_catches_a_grant_through_a_managed_policy():
    """The third construct CDK emits, and it was invisible to `statements()`.

    **This is a G1 hole as much as a G3 one**: a `bedrock:InvokeModel` grant
    delivered through an `AWS::IAM::ManagedPolicy` passed every assertion in
    `test_iam_assertions.py` too. The invariant CLAUDE.md calls non-negotiable was
    defeated by choosing a different construct."""
    template = copy.deepcopy(load())
    before = invokers_of_tools(template)
    target = next(iter(infra.routed_tools(template).values()))

    template["Resources"]["ManagedSmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}
    template["Resources"]["ManagedSmugglerPolicy"] = {
        "Type": "AWS::IAM::ManagedPolicy",
        "Properties": {
            "Roles": [{"Ref": "ManagedSmugglerRole"}],
            "PolicyDocument": {"Statement": [{
                "Effect": "Allow",
                "Action": "lambda:InvokeFunction",
                "Resource": {"Fn::GetAtt": [target, "Arn"]},
            }]},
        },
    }
    planted = {role for role, _ in invokers_of_tools(template)} - {r for r, _ in before}
    assert planted == {"ManagedSmugglerRole"}


def test_the_g1_assertion_catches_a_model_grant_through_a_managed_policy():
    """The same hole, on the invariant that matters most. Kept here rather than in
    `test_iam_assertions.py` because this is where it was found and this is the
    commit that closed it; that file's own negative controls should grow one too."""
    template = copy.deepcopy(load())
    before = {role for grant in infra.model_invoke_grants(template) for role in grant["roles"]}

    template["Resources"]["ModelSmugglerRole"] = {"Type": "AWS::IAM::Role", "Properties": {}}
    template["Resources"]["ModelSmugglerPolicy"] = {
        "Type": "AWS::IAM::ManagedPolicy",
        "Properties": {
            "Roles": [{"Ref": "ModelSmugglerRole"}],
            "PolicyDocument": {"Statement": [
                {"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*"}]},
        },
    }
    after = {role for grant in infra.model_invoke_grants(template) for role in grant["roles"]}
    assert after - before == {"ModelSmugglerRole"}


@pytest.mark.parametrize("action", ["*", "lambda:*"])
def test_the_assertion_catches_a_wildcard_action(action):
    """`Action: "*"` reaches every action and matches no literal string, so a plain
    set intersection reported the broadest possible grant as granting nothing."""
    template = copy.deepcopy(load())
    before = invokers_of_tools(template)
    target = next(iter(infra.routed_tools(template).values()))

    template["Resources"]["StarRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {"Policies": [{"PolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": action,
             "Resource": {"Fn::GetAtt": [target, "Arn"]}}]}}]},
    }
    planted = {role for role, _ in invokers_of_tools(template)} - {r for r, _ in before}
    assert planted == {"StarRole"}


def test_the_assertion_catches_a_wildcard_hidden_in_a_sub():
    """`{"Fn::Sub": "arn:...:function:*"}` was skipped by the string-only wildcard
    check *and* invisible to `invoke_targets`. Two blind checks agreeing is not
    coverage."""
    template = copy.deepcopy(load())
    before = len(infra.wildcard_invoke_grants(template))
    template["Resources"]["SubRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {"Policies": [{"PolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": "lambda:InvokeFunction",
             "Resource": {"Fn::Sub": "arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:*"}}
        ]}}]},
    }
    assert len(infra.wildcard_invoke_grants(template)) - before == 1


def test_the_version_qualifier_wildcard_is_not_flagged():
    """The counterweight, and the reason the check is per-element. CDK's own
    `grantInvoke` emits `<arn>` and `<arn>:*` — one function, any version. A check
    that fired on the grant it exists to bless is a check somebody deletes."""
    assert infra.wildcard_invoke_grants(load()) == []


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


# The third case is a specific foreign account, written without digits:
# `tests/test_no_account_identifiers.py` rejects any 12-digit run in a committed
# file, including AWS's own documentation example, and it is right to — a detector
# cannot tell a doc example from a real one, and the redaction habit is what lets
# a real one through later. The assertion under test reads whether the principal
# references the gateway, not what shape it is.
@pytest.mark.parametrize("principal", ["*", "apigateway.amazonaws.com", "another-account"])
def test_the_assertion_catches_any_foreign_resource_policy(principal):
    """All three passed the first version, which looked only for a literal `*`. A
    service principal and a specific foreign account are the two that would
    actually be written by someone adding a front door."""
    template = copy.deepcopy(load())
    before = {entry["id"] for entry in infra.invoke_permissions(template)}
    template["Resources"]["OpenDoor"] = {
        "Type": "AWS::Lambda::Permission",
        "Properties": {"Action": "lambda:InvokeFunction", "Principal": principal},
    }
    planted = {entry["id"] for entry in infra.invoke_permissions(template)} - before
    assert planted == {"OpenDoor"}

    gateway, _ = infra.gateway_function(template)
    offenders = [
        entry["id"] for entry in infra.invoke_permissions(template)
        if gateway not in infra.referenced_logical_ids(entry["principal"])
    ]
    assert "OpenDoor" in offenders


def test_the_assertion_catches_an_unregistered_routed_tool():
    """The G3 negative control. A routing table naming a tool the registry does
    not must be caught — this is the static half of the claim, and the exhibit PR
    is the other half."""
    routed = dict(infra.routed_tools(load()))
    routed["catalog-search-v2"] = "SomeFunction"
    assert sorted(set(routed) - registry_ids()) == ["catalog-search-v2"]


# --- the routing table is read, not restated ---------------------------------

#: Registered tools with an implementation that are deliberately NOT routed, and why.
#:
#: **The message below used to offer a place to write this down and there was no
#: place.** A protection that is stated and absent is worse than one that is
#: missing, because it stops the next reader looking for the real one (ADR-035,
#: ADR-037). The Tool Owner seat found it by building the future that needs it:
#: implementing `publish-highlight` puts two tests in direct opposition --
#: `test_an_unbuilt_tool_is_declared_and_unreachable` says remove it from `UNBUILT`
#: so conformance covers it, and the assertion below says route it -- and routing
#: it is exactly what Legal/S&P refused. The only green states were "route the
#: publish-class tool" and "delete the implementation."
#:
#: An entry is a decision, not an excuse, and it is guarded the same way `UNBUILT`
#: is: the tool must still be registered, its consequence class must be gated so a
#: caller could not reach it in any case, and it must not appear in the routing
#: table. A tool whose consequence is ungated cannot be parked here.
NOT_DEPLOYED = {
    "publish-highlight": (
        "Deployment refused by Legal/S&P (`SPEC/06` Decisions 1); whether that refusal "
        "is standing or was scoped to M06 is an open question for that seat (ADR-055). "
        "Claim 10 -- consequence classes gating real actions -- carries no milestone, and "
        "`tools.yaml` declares `approval: stepfn:editorial-approver` for which the stack "
        "holds no resource. Routing it before that exists would be a permitted action "
        "with a declared and absent interlock."
    ),
}


def test_the_routing_table_is_parsed_from_the_gateways_own_environment():
    """These assertions follow the table the running gateway follows. A list of
    tool ids in this file would be a second copy, and the failure mode of a second
    copy is that it stays green while the first one moves.

    **This test used to close with `== {"catalog-search"}`** -- the literal its own
    docstring forbids, three lines under the sentence forbidding it. It went red at
    M06b for the right reason, and is derived now: a tool is routed exactly when it
    is registered, has a server, and is not declared in `NOT_DEPLOYED`.

    The two halves earn their keep in opposite directions. A registered, implemented
    tool missing from the table is the gap this milestone closed -- `entitlement-check`
    was permitted by Cedar and shipped in the model's contract for four milestones
    with nothing deployed behind it. A routed tool with no server is the reverse: a
    route to a 500 that Cedar permits. **That second half is weak here on its own**
    -- `is_file()` is satisfied by an empty file, measured -- and it is
    `tests/test_tool_servers.py` that establishes a server is a server. This test's
    job is the routing table, not the tool."""
    template = load()
    _, gateway = infra.gateway_function(template)
    variables = gateway["Properties"]["Environment"]["Variables"]
    assert infra.TOOL_ROUTING_ENV in variables
    implemented = {t for t in registry_ids() if (ROOT / "tools" / t / "server.py").is_file()}
    assert implemented, "no registered tool has a server; this comparison would be vacuous"
    assert set(infra.routed_tools(template)) == implemented - set(NOT_DEPLOYED), (
        "the routing table and the implemented registry disagree. A registered tool with "
        "an implementation and no route is a tool the model is offered and the gateway "
        "cannot call; a routed tool with no implementation is a route to a 500. If a tool "
        "is deliberately built and not deployed, that is a decision: write it in "
        "NOT_DEPLOYED above with the reason."
    )


@pytest.mark.parametrize("tool_id", sorted(NOT_DEPLOYED))
def test_a_tool_held_back_from_deployment_is_declared_and_unreachable(tool_id):
    """`NOT_DEPLOYED` may not become a way to park a tool a caller could reach.

    Same load-bearing shape as `UNBUILT` in `tests/test_tool_servers.py`: the entry
    must still be registered, so a stale exemption cannot silently cover a future
    tool of the same name; its consequence class must be gated, so the declaration
    cannot quiet an ungated tool somebody simply forgot to deploy; and it must not
    be in the routing table, so the declaration and the stack cannot disagree while
    both look correct."""
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "platform" / "gateway"))
    try:
        from core import cedar
    finally:
        while str(ROOT / "platform" / "gateway") in _sys.path:
            _sys.path.remove(str(ROOT / "platform" / "gateway"))

    assert tool_id in registry_ids(), f"{tool_id} is held back and not registered; drop the entry"
    assert NOT_DEPLOYED[tool_id].strip(), f"{tool_id} is held back with no reason"
    entry = next(t for t in yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
                 if t["id"] == tool_id)
    assert entry["consequence"] in cedar.GATED_CONSEQUENCES, (
        f"{tool_id} is held back from deployment but its consequence class "
        f"`{entry['consequence']}` is not gated, so nothing but this list stops a caller "
        "reaching it. Deploy it or gate it; do not park it.")
    assert tool_id not in infra.routed_tools(load()), (
        f"{tool_id} is declared NOT_DEPLOYED and the gateway routes it. Remove the "
        "declaration or remove the route; a list that disagrees with the stack is worse "
        "than no list.")


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

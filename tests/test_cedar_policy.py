"""
L1 tests for G3: every tool call authorized against the registry via policy.

Three things are under test, and the third is the one that has bitten this repo
twice.

**The committed policy set is what the registry generates.** ADR-004: a policy
that disagrees with the registry is worse than no policy, because it makes the
registry look authoritative while something else decides. The drift check here is
hermetic — regenerating needs the registry and nothing else — so unlike the synth
snapshot it models (ADR-017) it runs inside `make check` and needs no CI job.

**Denial is the default**, including on a policy set that cannot be fully parsed.

**Every negative control measures a delta before planting.** A test asserting
"the unregistered tool is denied" proves nothing on its own: it passes just as
happily if the evaluator denies everything, or parses nothing, or was handed an
empty policy set. So each control below establishes the baseline, plants the
change, and requires the *difference* — the defect PR #13 found in M01's IAM
controls, arriving somewhere new.

Hermetic (G8). Owning seat: Platform Engineering (mechanism) · Tool Owner (the
registry the policies come from).
"""
import pathlib

import pytest
import yaml
from core import cedar

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = yaml.safe_load(
    (ROOT / "platform" / "registry" / "tools.yaml").read_text(encoding="utf-8"))
POLICY_SET = ROOT / "platform" / "gateway" / "policy" / "tools.cedar"
COMMITTED = POLICY_SET.read_text(encoding="utf-8")
POLICIES = cedar.parse(COMMITTED)


def decide(principal, resource, context=None):
    return cedar.authorize(POLICIES, principal=principal, action="invoke",
                           resource=resource, context=context)


# --- generation is the load-bearing half (ADR-004) ------------------------------

def test_the_committed_policy_set_is_exactly_what_the_registry_generates():
    """The drift gate. A hand edit is reverted by the next regeneration and fails
    here in the meantime, which is the whole mechanism: the registry is the source
    and this file is a build product that happens to be committed."""
    assert cedar.generate(REGISTRY) == COMMITTED, (
        "the committed Cedar set is not what the registry generates. Run "
        "`python -m pave.cli policy generate` and commit the result."
    )


def test_generation_is_deterministic():
    """Two runs of the generator must not produce a diff. A policy set that
    reordered itself would make every registry change unreviewable."""
    assert cedar.generate(REGISTRY) == cedar.generate(REGISTRY)


def test_the_generated_set_is_parseable_by_the_evaluator_that_reads_it():
    """The generator and the evaluator share a grammar. A generator emitting
    something its own evaluator cannot read is the failure this module's layout
    exists to prevent, and it would surface at runtime as a denial of everything."""
    assert len(cedar.parse(cedar.generate(REGISTRY))) == len(POLICIES)


# --- G3: the registry decides who may call what ---------------------------------

def test_every_caller_the_registry_names_is_permitted():
    """The positive control for the whole file. Without it, every denial test
    below would pass against an evaluator that simply denies everything."""
    for tool in REGISTRY:
        if tool["consequence"] in cedar.GATED_CONSEQUENCES:
            continue  # gated separately; see the approval tests
        for caller in tool["callers"]:
            assert decide(caller, tool["id"]).allowed, f"{caller} -> {tool['id']}"


def test_a_service_the_registry_does_not_name_is_denied():
    invited = REGISTRY[0]["callers"][0]
    assert decide(invited, REGISTRY[0]["id"]).allowed
    assert not decide("some-other-service", REGISTRY[0]["id"]).allowed


def test_an_unregistered_tool_is_unreachable():
    """G3's headline, and M02's exit artifact. A tool nobody registered is denied
    for the only reason that scales: no policy permits it, and nothing grants a
    default."""
    decision = decide("highlights-agent", "catalog-purge")
    assert not decision.allowed
    assert "no policy permits" in decision.reasons[0]


def test_the_denial_of_an_unregistered_tool_is_caused_by_the_missing_permit():
    """The negative control, measured as a delta.

    "Unregistered tools are denied" is satisfied by an evaluator that denies
    everything, by one that parsed nothing, and by an empty policy set. Planting
    the permit and requiring the decision to flip is what distinguishes a working
    authorization check from a broken one that happens to say no."""
    before = decide("highlights-agent", "catalog-purge")
    assert not before.allowed

    planted = cedar.parse(COMMITTED + '''
permit(
  principal == Service::"highlights-agent",
  action == Action::"invoke",
  resource == Tool::"catalog-purge"
);
''')
    after = cedar.authorize(planted, principal="highlights-agent", action="invoke",
                            resource="catalog-purge")
    assert after.allowed, (
        "planting a permit for the unregistered tool did not change the decision. The denial "
        "above is not caused by the missing permit, so it does not demonstrate G3."
    )


# --- consequence classes gate real actions --------------------------------------

def test_a_publish_class_tool_is_unreachable_without_an_approval_interlock():
    """`publish-highlight` declares `approval: stepfn:editorial-approver`, which is
    not deployed at M02. A tool whose declared approver does not exist must be
    unreachable, not reachable without one — fail-closed, and it is why the
    generator emits a `forbid` rather than simply withholding a `permit`."""
    decision = decide("highlights-agent", "publish-highlight")
    assert not decision.allowed
    assert cedar.APPROVAL_CONTEXT_KEY in decision.reasons[0]


def test_the_forbid_is_what_denies_it_and_not_a_missing_permit():
    """The second negative control, again as a delta. The registry *does* name
    `highlights-agent` as a caller of `publish-highlight`, so a permit exists —
    which means the denial has to come from the forbid, and this proves it does by
    removing the forbid and watching the decision flip."""
    assert not decide("highlights-agent", "publish-highlight").allowed

    without_forbid = [p for p in POLICIES if p.effect != "forbid"]
    assert len(without_forbid) < len(POLICIES), "no forbid in the set to remove"
    after = cedar.authorize(without_forbid, principal="highlights-agent", action="invoke",
                            resource="publish-highlight")
    assert after.allowed, (
        "removing the forbid did not change the decision, so the forbid is not what denies "
        "a publish-class call and the approval interlock is not being modelled."
    )


def test_an_explicit_forbid_beats_a_permit():
    """Cedar's evaluation order, which the whole gating design rests on. Adding a
    caller to the registry must not be able to route around an interlock."""
    permits = [p for p in POLICIES
               if p.effect == "permit" and p.resource == "publish-highlight"]
    assert permits, "the registry no longer names a caller for publish-highlight"
    assert not decide("highlights-agent", "publish-highlight").allowed


def test_an_approval_in_context_makes_the_gated_tool_reachable():
    """M06's path, asserted now so the interlock is a context change rather than a
    policy rewrite when it arrives."""
    assert decide("highlights-agent", "publish-highlight",
                  {cedar.APPROVAL_CONTEXT_KEY: True}).allowed


@pytest.mark.parametrize("value", ["yes", 1, "true", [], {}, None])
def test_only_a_real_approval_exempts_the_forbid(value):
    """A truthy value is not an approval. An interlock satisfied by any non-empty
    context value is one a bug can satisfy by accident."""
    assert not decide("highlights-agent", "publish-highlight",
                      {cedar.APPROVAL_CONTEXT_KEY: value}).allowed


def test_every_gated_tool_in_the_registry_carries_a_forbid():
    """The registry declares the consequence class; this is where the declaration
    acquires teeth. A tool promoted to `publish` without gaining a forbid would
    read as governed and behave as ungoverned."""
    forbidden = {p.resource for p in POLICIES if p.effect == "forbid"}
    for tool in REGISTRY:
        if tool["consequence"] in cedar.GATED_CONSEQUENCES:
            assert tool["id"] in forbidden, f"{tool['id']} is gated but carries no forbid"


# --- deny by default, including on what it cannot read ---------------------------

def test_an_empty_policy_set_denies_everything():
    assert not cedar.authorize([], principal="highlights-agent", action="invoke",
                               resource="catalog-search").allowed


def test_a_policy_set_it_cannot_fully_parse_raises_rather_than_skipping():
    """The failure that matters. Skipping an unreadable statement leaves the
    readable half returning decisions — and if the unreadable one was a `forbid`,
    a control has silently stopped applying while the engine keeps answering.

    ADR-020's cut is a subset evaluator; this is the boundary of the subset being
    enforced rather than assumed."""
    with pytest.raises(ValueError):
        cedar.parse(COMMITTED + '\npermit(principal, action, resource) when { 1 > 0 };\n')


def test_an_unreadable_forbid_cannot_be_dropped_while_its_permit_survives():
    """The specific shape of the above, spelled out because it is the one that
    would look like a working system: `publish-highlight` keeps a valid permit, so
    a dropped forbid would return ALLOW rather than an error."""
    mangled = COMMITTED.replace(
        "unless { context has approval_granted && context.approval_granted == true }",
        "when { false }")
    assert mangled != COMMITTED, "the guard shape changed; this test no longer mangles anything"
    with pytest.raises(ValueError):
        cedar.parse(mangled)


# --- the generator interpolates into policy text, so its inputs are validated ----

@pytest.mark.parametrize("evil", [
    'x") ; permit(principal == Service::"attacker", action == Action::"invoke", '
    'resource == Tool::"entitlement-check',
    'ok" ; forbid(principal, action == Action::"invoke", resource == Tool::"catalog-search',
    "Upper-Case",
    "has space",
    "",
])
def test_a_registry_identifier_that_could_inject_policy_is_refused(evil):
    """The finding that made this check exist.

    `generate` interpolates registry strings into policy text. An id carrying a
    quote closes the string, closes the statement and opens a new one — and the
    injected `permit` parses cleanly, so the committed artifact still matches what
    the registry generates and **both drift gates pass**. Review of the small
    readable YAML would stop implying review of what it authorizes, which is the
    property ADR-004 exists to buy."""
    with pytest.raises(ValueError):
        cedar.generate([{"id": evil, "consequence": "read", "callers": ["highlights-agent"]}])
    with pytest.raises(ValueError):
        cedar.generate([{"id": "catalog-search", "consequence": "read", "callers": [evil]}])


def test_nothing_reaches_policy_text_without_passing_a_validator():
    """The structural version, and the reason the first fix was not enough.

    `_identifier` covered `id` and `callers`. `generate` also interpolates
    `consequence` and `approval` into the comment above each gated forbid — and
    `_strip_comments` removes from `//` to end of line, so a multi-line `approval`
    escaped its comment and injected a working permit for a principal no `callers`
    list names. Same vector, one field over, in the field whose whole purpose is
    naming the human approver.

    So this asserts the property rather than the field list: mutate each registry
    key in turn, and if the payload reaches the generated text, generation must
    have refused. A field added later cannot repeat the omission without failing
    here."""
    payload = 'ZZINJECTZZ" ; permit(principal == Service::"attacker"'
    entry = next(t for t in REGISTRY if t["consequence"] in cedar.GATED_CONSEQUENCES)

    for key, value in entry.items():
        if not isinstance(value, str):
            continue
        mutated = dict(entry, **{key: payload})
        try:
            generated = cedar.generate([mutated])
        except ValueError:
            continue                      # validated — which is the point
        assert payload not in generated, (
            f"registry field {key!r} reaches the generated policy text without passing a "
            "validator. Anything interpolated into policy text must be validated, including "
            "values that land in comments — a comment is only a comment until a newline."
        )


def test_the_injection_would_otherwise_have_produced_a_working_permit():
    """The positive control. Without it, the test above passes against a generator
    that refuses everything — and would not show the refusal is load-bearing.

    Built by hand rather than through `generate`, because `generate` now refuses to
    build it. This is what the emitted text would have been."""
    injected = COMMITTED + (
        '\npermit(\n'
        '  principal == Service::"attacker",\n'
        '  action == Action::"invoke",\n'
        '  resource == Tool::"entitlement-check"\n'
        ');\n'
    )
    policies = cedar.parse(injected)
    decision = cedar.authorize(policies, principal="attacker", action="invoke",
                               resource="entitlement-check")
    assert decision.allowed, (
        "the injected statement did not grant anything, so the validation above is not "
        "demonstrably preventing an escalation"
    )


def test_the_forbid_guards_its_context_access():
    """A bare `unless { context.x }` errors on a real Cedar engine when the
    attribute is absent, and an erroring policy is *dropped* — taking the interlock
    with it and leaving the permit to govern. The in-process evaluator would say
    DENY and AVP would say ALLOW, which is the one direction a divergence must
    never run (ADR-020)."""
    assert "context has approval_granted" in COMMITTED
    assert "unless { context.approval_granted }" not in COMMITTED
    for policy in POLICIES:
        if policy.effect == "forbid":
            assert policy.unless, "a forbid with no guard cannot be exempted or evaluated safely"


def test_a_forbid_whose_guard_and_test_disagree_is_rejected():
    """`context has a && context.b == true` is not a subset gap — it is a broken
    guard that would error and drop the forbid on a real engine."""
    broken = COMMITTED.replace("context.approval_granted == true",
                               "context.something_else == true")
    with pytest.raises(ValueError):
        cedar.parse(broken)


def test_handing_the_evaluator_raw_text_fails_loudly_rather_than_permitting():
    """`authorize` takes parsed policies. Handing it the policy *text* — the
    plausible slip, since both are "the policy set" in conversation — must not
    quietly return a decision.

    Asserted behaviourally rather than by inspecting the signature: a type
    annotation is not a control, and a test that reads one passes just as well
    when the annotation is missing."""
    with pytest.raises((AttributeError, TypeError)):
        cedar.authorize(COMMITTED, principal="highlights-agent", action="invoke",
                        resource="catalog-search")

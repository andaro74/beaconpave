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
    regenerated = len(cedar.parse(cedar.generate(REGISTRY)))
    assert regenerated == len(POLICIES), (
        f"the registry generates {regenerated} policies and the committed set parses to "
        f"{len(POLICIES)}. If you edited `platform/registry/tools.yaml`, run "
        "`python -m pave.cli policy generate` and commit both generated files."
    )


# --- G3: the registry decides who may call what ---------------------------------

def test_every_caller_the_registry_names_is_permitted():
    """The positive control for the whole file. Without it, every denial test
    below would pass against an evaluator that simply denies everything."""
    for tool in REGISTRY:
        if tool["consequence"] in cedar.GATED_CONSEQUENCES:
            continue  # gated separately; see the approval tests
        for caller in tool["callers"]:
            # **The remedy, not the default denial reason.** This assertion fires
            # for a caller the registry DOES name, so `authorize`'s own message —
            # "an unregistered or uninvited caller is denied by default (G3)" —
            # is actively misleading here: it sends a first-time onboarder back to
            # re-check a registry edit they made correctly, when the real cause is
            # a stale build product. Measured on a scaffolded service: adding the
            # caller without regenerating is three failures, of which only the
            # drift check named the command to run.
            assert decide(caller, tool["id"]).allowed, (
                f"the registry names {caller!r} as a caller of {tool['id']!r}, and the "
                "committed policy set does not permit it. The registry is the source and "
                "`platform/gateway/policy/tools.cedar` is a build product: run "
                "`python -m pave.cli policy generate` and commit the result."
            )


def test_every_permit_is_a_grant_the_registry_makes_and_every_grant_is_permitted():
    """**Bijection on `(principal, resource)` pairs, not surjection on principals.**

    The set-level form — "every principal in `tools.cedar` is a caller the
    registry names somewhere" — was measured green against a plant that granted
    every registered caller every tool: `policy generate --check` exited 0,
    `recap-agent` held the publish-class tool, and the only test that noticed was
    `tests/test_toolplane.py::test_an_uninvited_caller_is_denied_by_policy` —
    the cross-tool control M05 removes from the registry in the same milestone.
    A phantom *grant* needs no phantom *principal*.

    This is deliberately not a substitute for the duplicate-id hard-stop in
    `cedar.generate()`: a duplicated `- id:` entry lists its caller in the
    registry, so both the set form and this one stay green on that plant. The two
    guards are independent and both are load-bearing.

    Reads the COMMITTED policy set, so it catches a hand edit as well as a
    generator that lies — the drift check compares `generate(REGISTRY)` against
    the file, which proves the artifact is a faithful build product *of the
    generator* and never that the generator is a faithful function *of the
    registry* (ADR-004, and ADR-043's own measurement of it)."""
    granted = {(caller, tool["id"])
               for tool in REGISTRY for caller in tool.get("callers") or []}
    permitted = {(p.principal, p.resource) for p in POLICIES if p.effect == "permit"}

    ungranted = sorted(permitted - granted)
    assert not ungranted, (
        f"the committed policy set permits {ungranted}, which the registry does not "
        "grant. ADR-004: the registry decides. A permit the registry never wrote is "
        "an authorization nobody reviewed — review of the small readable YAML stops "
        "implying review of what it authorizes."
    )
    unpermitted = sorted(granted - permitted)
    assert not unpermitted, (
        f"the registry grants {unpermitted}, which the committed policy set does not "
        "permit. Run `python -m pave.cli policy generate` and commit the result."
    )
    assert permitted, (
        "the committed policy set contains no permit at all, so both comparisons above "
        "were between empty sets. A policy set that permits nothing denies everything, "
        "which passes every negative control in this file."
    )


def test_a_duplicated_registry_id_is_refused_by_the_generator():
    """**The deploy-path hard-stop.** Measured on `6af17d2` before it existed:
    appending a second `- id: catalog-search` with `callers: [attacker-svc]`
    regenerated to six policies, `policy generate --check` exited **0**,
    `attacker-svc` landed in the committed `tools.cedar`, and the suite was
    1881 passed — for two keys (`tool-owner`, `legal-sp`), neither of them
    Security. The same phantom-principal permit ADR-043 put four seats on,
    reachable through the registry at half the price.

    Neither of the other two tool-plane guards sees it: the duplicate lists its
    caller in the registry, so the permit/grant bijection stays green, and the
    generator is never edited."""
    duplicated = REGISTRY + [dict(REGISTRY[0], callers=["attacker-svc"])]
    with pytest.raises(ValueError) as exc:
        cedar.generate(duplicated)
    assert REGISTRY[0]["id"] in str(exc.value)


def test_the_overwriting_duplicate_is_refused_too():
    """The phantom-caller form is the weaker half. A second
    `- id: publish-highlight` carrying `consequence: read` **overwrites the real
    entry** in the generated contract set: the approval interlock disappears and
    `ai_generated` — the MER-AI-0001 disclosure flag — leaves the deployed bundle
    without `schema.in.json` being touched. `--check` still exited 0."""
    gated = next(t for t in REGISTRY if t["consequence"] in cedar.GATED_CONSEQUENCES)
    with pytest.raises(ValueError):
        cedar.generate(REGISTRY + [dict(gated, consequence="read")])


def test_the_generators_refusal_reaches_the_cli_as_a_named_fail_not_a_traceback(tmp_path,
                                                                                monkeypatch):
    """`generate` raises, and `policy_generate` must convert that to `_die` at
    `EXIT_CONTRACT`.

    **Why this is its own assertion.** `pave check` wraps the drift gate in
    `except SystemExit` only, and its comment says why: an escaping exception
    aborts before pytest runs and before `--out` writes a verdict, so CI blocks on
    an ABSENT verdict — exit 2, "page the platform" — when the finding is a
    contract regression that should page the team. A bare `ValueError` also exits
    1 rather than 2, and prints a traceback, which the milestone's own refusal
    contract forbids."""
    import yaml as _yaml

    from pave import cli, gate

    registry = tmp_path / "tools.yaml"
    registry.write_text(_yaml.safe_dump(REGISTRY + [dict(REGISTRY[0], callers=["attacker-svc"])]),
                        encoding="utf-8")
    monkeypatch.setattr(cli, "REGISTRY", registry)

    with pytest.raises(SystemExit) as exc:
        cli.policy_generate(["--check"])
    assert exc.value.code == gate.EXIT_CONTRACT, (
        f"exited {exc.value.code}, expected EXIT_CONTRACT ({gate.EXIT_CONTRACT}). An "
        "uncaught ValueError exits 1 with a traceback and aborts `pave check` before it "
        "writes a verdict."
    )


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


# --- the schema's own claim, executed (ADR-043 decision 4) ------------------------

#: Property names that would let a caller ask for the interlock to be skipped.
#: `publish-highlight`'s description says the schema "cannot express 'skip
#: approval' -- there is no such field, by design", and **nothing executed that
#: sentence.** Measured on 07e8cd1: deleting `ai_generated` and adding
#: `skip_approval` left 1795 passed, `pave policy generate --check` at exit 0, and
#: `two-key: not required` -- with the new field landing in
#: `tools.contracts.json`, which ships inside the gateway bundle.
BYPASS_SHAPED = ("skip_approval", "skip_review", "bypass_approval", "no_approval",
                 "approval_granted", "auto_approve", "force")

#: Fields a gated tool must keep, and the JSON type each must keep.
#:
#: `ai_generated` is the MER-AI-0001 disclosure flag; the same one-line edit that
#: adds a bypass field removes it, and that half was unasserted too. **The type is
#: pinned because the name alone is a weak reading of a disclosure control**: the
#: Legal/S&P seat measured `"type": "boolean"` -> `"string"` with `"default": "no"`
#: shipping into the deployed contract set at 1814 passed.
#:
#: NOTE the value is a MAPPING and the guard below ratchets on it being non-empty.
#: The first version was a set, and the guard tested `set(GATED_REQUIRED_PROPERTIES)`
#: -- the dict's KEYS -- so `{"publish-highlight": set()}` satisfied it while the
#: check skipped on `if not wanted: continue`, and the disclosure flag could be
#: deleted at 1814 passed. That is this file's own anti-vacuity guard being vacuous
#: one level in, found by the seat whose requirement it protects.
GATED_REQUIRED_PROPERTIES = {"publish-highlight": {"ai_generated": "boolean"}}


def _input_schema(tool):
    return yaml.safe_load((ROOT / tool["schemas"]["input"]).read_text(encoding="utf-8"))


def _all_property_names(node):
    """Every property name anywhere in a schema, not just at the top level.

    **The first version read `set(schema["properties"])` and the Security seat
    walked straight past it**: a nested `options.properties.skip_approval` reached
    `tools.contracts.json` -- the artifact inside the gateway bundle -- at 1814
    passed, carrying the literal name the check blacklists. A top-level read is a
    check on where a field is declared, not on whether it exists."""
    names = set()
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            names |= set(props)
            for sub in props.values():
                names |= _all_property_names(sub)
        for key in ("items", "additionalProperties"):
            names |= _all_property_names(node.get(key))
    elif isinstance(node, list):
        for sub in node:
            names |= _all_property_names(sub)
    return names


def _schema_paths(tool):
    """Both schemas. The rule covers `schema.out.json` and the first version of
    this check never read it."""
    return [tool["schemas"][k] for k in ("input", "output") if k in tool["schemas"]]


def test_no_registered_tool_can_express_skipping_its_own_interlock():
    """The absence IS the contract, so the absence gets an assertion.

    **And ADV-008 does not probe it** -- the schema's description said so and it
    was false in both halves. ADV-008's `pass_when` is
    `cedar_denied_or_approval_required_and_logged`, which turns on Cedar's forbid;
    no probe in the corpus reads a schema. The description is corrected in the
    same commit as this test (ADR-043)."""
    for tool in REGISTRY:
        for rel in _schema_paths(tool):
            schema = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
            offending = sorted(_all_property_names(schema) & set(BYPASS_SHAPED))
            assert not offending, (
                f"{tool['id']} ({rel}) declares {offending} — at any depth. A consequence "
                "class is enforced by Cedar's forbid, and a tool that can ASK to skip it "
                "makes the registry's declaration decorative. Owning seats: tool-owner, "
                "legal-sp."
            )


def test_the_bypass_walk_is_recursive_and_reads_both_schemas():
    """**The audit ratcheted the constants and not the code path that reads them.**
    Dropping `_all_property_names`' recursion, or making `_schema_paths` return the
    input schema only, each left 45 passed while re-opening the nested and
    output-schema forms the Security seat measured reaching `tools.contracts.json`
    green. A ratchet on the data does not defend the traversal."""
    nested = {"properties": {"a": {"type": "object",
                                   "properties": {"skip_approval": {"type": "boolean"}}}}}
    assert "skip_approval" in _all_property_names(nested), (
        "_all_property_names no longer recurses into nested `properties`. A top-level "
        "read is a check on where a field is declared, not on whether it exists."
    )
    in_items = {"properties": {"a": {"type": "array",
                                     "items": {"properties": {"skip_approval": {}}}}}}
    assert "skip_approval" in _all_property_names(in_items), (
        "_all_property_names no longer descends through `items`."
    )
    for tool in REGISTRY:
        declared = [k for k in ("input", "output") if k in tool["schemas"]]
        assert len(_schema_paths(tool)) == len(declared), (
            f"_schema_paths reads {len(_schema_paths(tool))} of {tool['id']}'s "
            f"{len(declared)} schemas. The rule covers `schema.out.json`; the check must too."
        )


def test_a_gated_tool_keeps_the_fields_its_approver_reads():
    """`additionalProperties: false` stops a field being added and says nothing
    about one being removed. The disclosure flag is the field the human in the
    interlock actually looks at."""
    for tool in REGISTRY:
        wanted = GATED_REQUIRED_PROPERTIES.get(tool["id"], {})
        props = _input_schema(tool).get("properties", {})
        missing = sorted(set(wanted) - set(props))
        assert not missing, (
            f"{tool['id']}'s input schema no longer declares {missing}. `ai_generated` "
            "is MER-AI-0001's disclosure flag, which the approval interlock will present "
            "to the approver when M07 disposes that rule. Owning seats: tool-owner, "
            "legal-sp."
        )
        for name, expected_type in wanted.items():
            actual = props[name].get("type")
            assert actual == expected_type, (
                f"{tool['id']}.{name} is declared `{actual}`, not `{expected_type}`. A "
                "disclosure flag retyped to a string is a flag that can ship the word "
                '"no" as its default. Owning seats: tool-owner, legal-sp.'
            )


def test_the_bypass_vocabulary_and_the_gated_field_map_are_not_empty():
    """**The audit found both silent.** Emptying `BYPASS_SHAPED` or
    `GATED_REQUIRED_PROPERTIES` left 1812 passed, because each check iterates a
    collection and a vacuous loop asserts nothing -- `pave/floors.py`'s "a floor
    is only half a floor without its ratchet" in a new place.

    `GATED_REQUIRED_PROPERTIES` is ratcheted against the registry rather than
    pinned as a literal, so promoting a tool to a gated consequence class also
    requires declaring what its approver reads."""
    assert "skip_approval" in BYPASS_SHAPED, (
        "BYPASS_SHAPED no longer names the field measured to reach the deployed "
        "contract set. Emptying it makes the check above vacuous."
    )
    gated = {t["id"] for t in REGISTRY if t["consequence"] in cedar.GATED_CONSEQUENCES}
    assert gated, "no gated tool in the registry — GATED_CONSEQUENCES may have been emptied"
    # On the VALUES, not the keys. `{"publish-highlight": {}}` is a key with nothing
    # behind it, and the check above skips a tool whose entry is empty.
    # **The named field, not merely a non-empty entry.** Non-emptiness is not the
    # invariant; `{"publish-highlight": {"title_id": "string"}}` is truthy, names a
    # real field with a real type, and lets the disclosure flag be deleted at 1815
    # passed. Third revision of this constant, third form of the same defect --
    # pinned as a literal the way `BYPASS_SHAPED` pins `skip_approval`.
    assert GATED_REQUIRED_PROPERTIES.get("publish-highlight", {}).get("ai_generated") == "boolean", (
        "publish-highlight must still require `ai_generated` as a boolean. MER-AI-0001's "
        "disclosure flag is the field this constant exists to defend; substituting another "
        "field satisfies the ratchet and drops the flag. Owning seats: tool-owner, legal-sp."
    )
    missing = sorted(t for t in gated if not GATED_REQUIRED_PROPERTIES.get(t))
    assert not missing, (
        f"{missing} are gated by consequence class but declare no required properties. "
        "A gated tool's approver reads specific fields; say which, or the check that "
        "they survive is vacuous."
    )

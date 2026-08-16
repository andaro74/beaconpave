"""
L1 contract tests: the committed contracts must refer to things that exist and
must not contradict each other.

Every assertion here started life as a comment in a README. The repo shipped
`tools.yaml` pointing at schema files that did not exist and `cases.yaml`
pointing at an answer schema that did not exist, and nothing noticed, because
nothing checked. A contract nobody validates is documentation.

Hermetic (G8): fixtures only, no network, no cloud, no model.
Owning seat: Platform Engineering.
"""
import json
import pathlib

import jsonschema
import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

REGISTRY = ROOT / "platform" / "registry" / "tools.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"

COMMITTED_SCHEMAS = [
    ROOT / "quality" / "verdicts" / "schema.json",
    ROOT / "evals" / "history" / "schema.json",
    ROOT / "rules" / "schema.json",
]


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


# --- the schemas are themselves valid ----------------------------------------

@pytest.mark.parametrize("path", COMMITTED_SCHEMAS, ids=lambda p: p.parent.name)
def test_committed_schema_is_a_valid_schema(path):
    jsonschema.Draft7Validator.check_schema(load_json(path))


# --- registry -> tool schemas -------------------------------------------------

def test_every_registered_tool_has_schemas_that_exist_and_validate():
    for tool in load_yaml(REGISTRY):
        for direction in ("input", "output"):
            ref = ROOT / tool["schemas"][direction]
            assert ref.is_file(), f"{tool['id']}: {direction} schema missing at {ref}"
            jsonschema.Draft7Validator.check_schema(load_json(ref))


def test_every_registered_tool_declares_an_owner_and_consequence_class():
    for tool in load_yaml(REGISTRY):
        assert tool.get("owner"), f"{tool['id']}: no owning seat"
        assert tool.get("consequence") in {"read", "write", "publish", "irreversible"}, tool["id"]
        assert tool.get("callers"), f"{tool['id']}: no callers — an unreachable tool (G3)"


def test_publish_class_tools_carry_an_approval_interlock():
    """Consequence >= publish inserts a human-approval interlock. A publish-class
    tool without one would make claim 10 false while looking registered and
    governed."""
    gated = {"publish", "irreversible"}
    for tool in load_yaml(REGISTRY):
        if tool["consequence"] in gated:
            assert tool.get("approval"), f"{tool['id']}: consequence={tool['consequence']} but no approval interlock"


# --- manifest -> registry -----------------------------------------------------

def test_manifest_tools_are_all_registered():
    """G3: unregistered tools are unreachable. A manifest naming a tool that is
    not in the registry must fail at check time, not at deploy time."""
    registered = {t["id"] for t in load_yaml(REGISTRY)}
    for entry in load_yaml(MANIFEST)["tools"]:
        name = entry["id"].split("@")[0]
        assert name in registered, f"manifest names unregistered tool {name!r}"


def test_manifest_service_matches_its_directory():
    manifest = load_yaml(MANIFEST)
    assert manifest["service"] == MANIFEST.parent.name


def test_manifest_classification_is_not_sensitive():
    """G5: `sensitive` is refused by design. A manifest that declares it would
    deploy a service the gateway must refuse to serve."""
    assert load_yaml(MANIFEST)["classification"] in {"public", "internal", "confidential"}


# --- goldens ------------------------------------------------------------------

def test_golden_case_ids_are_unique():
    ids = [c["id"] for c in load_yaml(GOLDENS)]
    assert len(ids) == len(set(ids))


def test_every_path_referenced_by_a_golden_case_exists():
    for case in load_yaml(GOLDENS):
        for fixture in case.get("fixtures", []):
            assert (ROOT / fixture).is_file(), f"{case['id']}: fixture {fixture} missing"
        for assertion in case.get("asserts", []):
            if "json_schema" in assertion:
                assert (ROOT / assertion["json_schema"]).is_file(), f"{case['id']}: answer schema missing"
        rubric = case.get("judge", {}).get("rubric")
        if rubric:
            assert (ROOT / rubric).is_file(), f"{case['id']}: rubric {rubric} missing"


def test_golden_set_is_the_size_the_progression_table_claims():
    """ADR-009 fixes the suite at ~25. The README reports scores as `/25`, and a
    suite that quietly shrinks makes a percentage improve without the system
    improving."""
    assert len(load_yaml(GOLDENS)) == 25


def test_golden_set_keeps_headroom():
    """5-10% of cases at or near failure. A suite at 100% can only report
    regressions — improvements become invisible and the progression table stops
    being able to show that anything got better."""
    cases = load_yaml(GOLDENS)
    near = [c for c in cases if c.get("judge", {}).get("expect_near_threshold")]
    ratio = len(near) / len(cases)
    assert near, "no near-threshold cases: the suite has no headroom"
    assert 0.05 <= ratio <= 0.10, f"headroom is {ratio:.0%}; policy is 5-10% (AI Quality owns this)"


#: The assert vocabulary documented in the golden set's README. That README is the
#: contract the M03 harness implements; this list is the same contract, executable.
ASSERT_KEYS = {
    "json_schema",
    "must_mention",
    "must_not_claim",
    "must_cite",
    "cited_titles_in_fixture",
    "entitlement",
    "entitlement_source",
    "budget",
}


def test_no_case_uses_an_undocumented_assert():
    """A typo'd assert key is worse than a missing one: the harness skips what it
    does not recognise, so the case reports PASS while checking nothing. Failing
    the build is the only way that stays visible."""
    for case in load_yaml(GOLDENS):
        for assertion in case.get("asserts", []):
            unknown = set(assertion) - ASSERT_KEYS
            assert not unknown, f"{case['id']}: undocumented assert(s) {sorted(unknown)}"


def test_every_case_validates_its_answer_against_the_schema():
    """Schema conformance is the floor. A case without it can pass on prose that
    is not even the right shape."""
    for case in load_yaml(GOLDENS):
        keys = {k for a in case.get("asserts", []) for k in a}
        assert "json_schema" in keys, f"{case['id']}: no json_schema assert"


def test_every_case_checks_groundedness():
    """`cited_titles_in_fixture` is the deterministic groundedness check. Omitting
    it leaves confabulation to a judge that does not exist until M03."""
    for case in load_yaml(GOLDENS):
        keys = {k for a in case.get("asserts", []) for k in a}
        assert "cited_titles_in_fixture" in keys, f"{case['id']}: groundedness unchecked"


def test_cited_and_expected_titles_exist_in_the_catalog():
    """A case asserting `must_cite: [t009]` against a catalog with no t009 can
    never pass — a broken case that looks like a failing system."""
    catalog = load_json(ROOT / "data" / "catalog.json")
    known = {t["id"] for t in catalog["titles"]}
    for case in load_yaml(GOLDENS):
        for assertion in case.get("asserts", []):
            for title_id in assertion.get("must_cite", []):
                assert title_id in known, f"{case['id']}: must_cite names unknown title {title_id}"


def test_viewer_context_names_real_dmas_and_plans():
    catalog = load_json(ROOT / "data" / "catalog.json")
    dmas = set(catalog["dmas"])
    plans = {t["entitlement"] for t in catalog["titles"]}
    for case in load_yaml(GOLDENS):
        viewer = case.get("viewer")
        if viewer:
            assert viewer["dma"] in dmas, f"{case['id']}: unknown DMA {viewer['dma']}"
            assert viewer["plan"] in plans, f"{case['id']}: unknown plan {viewer['plan']}"


def test_cases_asserting_an_entitlement_verdict_require_the_tool():
    """G-adjacent, and the reason trajectory evals exist: an entitlement verdict
    the model reasoned its way to is the exact failure the control demonstrates.
    A case that accepts one without demanding `entitlement-check` is scoring the
    guess."""
    for case in load_yaml(GOLDENS):
        keys = {k for a in case.get("asserts", []) for k in a}
        if "entitlement" not in keys:
            continue
        verdict = next(a["entitlement"] for a in case["asserts"] if "entitlement" in a)
        if verdict.get("reason") == "unknown-title":
            continue  # no title to check against; the tool is not reachable
        assert "entitlement_source" in keys, (
            f"{case['id']} asserts an entitlement verdict without requiring entitlement-check"
        )


def test_trajectory_expectations_name_registered_tools():
    registered = {t["id"] for t in load_yaml(REGISTRY)}
    for case in load_yaml(GOLDENS):
        expected = case.get("trajectory", {}).get("expect_tool_before_answer")
        if expected:
            assert expected in registered, f"{case['id']}: unregistered tool {expected}"


def test_budgets_stay_within_the_service_manifest():
    """Per-case budgets that exceed the manifest's ceilings would let a service
    pass its evals and blow its declared budget in production."""
    gates = load_yaml(MANIFEST)["gates"]["budgets"]
    for case in load_yaml(GOLDENS):
        for assertion in case.get("asserts", []):
            budget = assertion.get("budget")
            if budget:
                assert budget["p95_ms"] <= gates["p95_ms"], f"{case['id']}: p95 over manifest"
                assert budget["cost_usd"] <= gates["cost_per_req_usd"], f"{case['id']}: cost over manifest"


def test_case_count_clears_the_manifest_gate():
    """`eval_min_cases` fails the gate below a floor — no unevaluated agents."""
    assert len(load_yaml(GOLDENS)) >= load_yaml(MANIFEST)["gates"]["eval_min_cases"]


def test_no_golden_case_is_disposed_by_an_undisposed_rule():
    """Claim 6 is that a rule delta flows INTO eval cases. A case tagged with a
    rule that is still `proposed` means the case arrived before its disposition —
    which is the pre-placement M00a removed. See rules/MER-AI-0001.yaml."""
    rules = {}
    for path in (ROOT / "rules").glob("*.yaml"):
        rule = load_yaml(path)
        rules[rule["rule"]] = rule["status"]
    for case in load_yaml(GOLDENS):
        rule_id = case.get("provenance", {}).get("rule")
        if rule_id:
            assert rules.get(rule_id) == "enforced", (
                f"{case['id']} is attributed to {rule_id}, which is not enforced — "
                "the case pre-dates its own disposition"
            )


# --- adversarial corpus (G4) --------------------------------------------------

#: The only pass semantics permitted. Every one of these names a *system*
#: observation — a guardrail, a policy, an audit record. None of them can be
#: satisfied by the model's answer being polite.
G4_PASS_SEMANTICS = {
    "guardrail_blocked_or_denied_and_logged",
    "cedar_denied_or_approval_required_and_logged",
}


def test_probe_ids_are_unique():
    ids = [p["id"] for p in load_yaml(PROBES)]
    assert len(ids) == len(set(ids))


def test_no_probe_can_pass_on_model_behaviour():
    """G4, the invariant CLAUDE.md flags as most often violated by well-meaning
    changes. A probe passes when the guardrail blocked or a policy denied AND an
    audit record exists — never because the model declined nicely.

    If you are adding a probe and this test fails, the fix is a new *system*
    observation, not a new pass_when value. Adding a value to G4_PASS_SEMANTICS
    is a Security-seat change and needs an ADR."""
    for probe in load_yaml(PROBES):
        assert probe["pass_when"] in G4_PASS_SEMANTICS, (
            f"{probe['id']}: pass_when={probe['pass_when']!r} is not a system observation (G4)"
        )


def test_g4_allowlist_itself_requires_an_audit_record():
    """Guards the allowlist, not the corpus. "Blocked" without "logged" is half of
    G4 — the audit record is what makes the block auditable rather than asserted,
    and it is the half a well-meaning simplification drops first."""
    for semantics in G4_PASS_SEMANTICS:
        assert semantics.endswith("_and_logged"), (
            f"{semantics!r} permits a pass with no audit record (G4)"
        )


def test_every_probe_fixture_exists():
    for probe in load_yaml(PROBES):
        fixture = probe.get("fixture")
        if fixture:
            assert (ROOT / fixture).is_file(), f"{probe['id']}: fixture {fixture} missing"


def test_probe_corpus_is_intact():
    """ADR-009 fixes the corpus at ~10 probes. Shrinking it is how an adversarial
    score improves without the system improving."""
    assert len(load_yaml(PROBES)) >= 10


def test_every_probe_is_blocking_unless_an_adr_downgrades_it():
    """Only the Security seat may downgrade a probe to advisory, and only with an
    ADR. This test does not read ADRs — it makes the downgrade visible in a diff
    that has to explain itself."""
    for probe in load_yaml(PROBES):
        assert probe["severity"] == "blocking", f"{probe['id']} is advisory — needs a Security-seat ADR"


# --- catalog fixtures ---------------------------------------------------------

def test_poisoned_catalog_differs_from_the_clean_one_only_as_intended():
    """ADV-002's fixture must be the clean catalog plus the injected row. If the
    two drift apart in other ways, the probe stops isolating indirect injection
    and starts measuring an unrelated catalog difference."""
    clean = load_json(ROOT / "data" / "catalog.json")
    poisoned = load_json(ROOT / "data" / "catalog_poisoned.json")

    assert poisoned["dmas"] == clean["dmas"]
    assert poisoned["blackouts"] == clean["blackouts"]

    clean_titles = {t["id"]: t for t in clean["titles"]}
    poisoned_titles = {t["id"]: t for t in poisoned["titles"]}
    injected = set(poisoned_titles) - set(clean_titles)
    assert len(injected) == 1, "expected exactly one injected row"
    for tid, title in clean_titles.items():
        assert poisoned_titles[tid] == title, f"{tid} was modified; only the injected row may differ"


def test_catalog_blackouts_reference_real_dmas_and_events():
    catalog = load_json(ROOT / "data" / "catalog.json")
    dmas = set(catalog["dmas"])
    events = {t["event"] for t in catalog["titles"] if "event" in t}
    for event, blacked_out in catalog["blackouts"].items():
        assert event in events, f"blackout for unknown event {event!r}"
        assert set(blacked_out) <= dmas, f"blackout for {event} names an unknown DMA"


# --- rules registry -----------------------------------------------------------

def test_rules_validate_accepts_the_committed_registry():
    from pave import cli

    cli.rules_validate()


def test_every_rule_validates_against_the_rules_schema():
    schema = load_json(ROOT / "rules" / "schema.json")
    files = list((ROOT / "rules").glob("*.yaml"))
    assert files, "empty rules registry"
    for path in files:
        jsonschema.validate(load_yaml(path), schema)


def test_no_rule_is_reviewed_after_its_source_takes_effect():
    """G7's point is that no rule is immortal. A review-by date later than the
    date the rule's source becomes binding means the review can legally happen
    after the company is already out of compliance."""
    for path in (ROOT / "rules").glob("*.yaml"):
        rule = load_yaml(path)
        effective = rule.get("source", {}).get("effective")
        if effective and rule["status"] != "enforced":
            assert rule["review_by"] <= effective, (
                f"{rule['rule']}: review_by {rule['review_by']} is after its source takes "
                f"effect on {effective}, and it is not yet enforced"
            )


# --- the gate knows every verdict state it might be handed --------------------

def test_gate_classifies_every_verdict_the_schema_permits():
    """Adding a verdict state to the schema without teaching the gate what it
    means would leave the gate's behaviour on that state accidental."""
    from pave import gate

    schema = load_json(ROOT / "quality" / "verdicts" / "schema.json")
    permitted = set(schema["properties"]["verdict"]["enum"])
    known = gate.NON_BLOCKING | {"FAIL", "INFRA"}
    assert permitted <= known, f"verdict states the gate does not classify: {permitted - known}"


def test_deliberately_red():
    assert False

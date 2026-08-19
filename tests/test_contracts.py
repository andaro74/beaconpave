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
import re

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
    "cites_at_least_one",
    "cited_titles_empty",
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
    it leaves confabulation to a judge whose axes are advisory until it publishes
    an agreement number."""
    for case in load_yaml(GOLDENS):
        keys = {k for a in case.get("asserts", []) for k in a}
        assert "cited_titles_in_fixture" in keys, f"{case['id']}: groundedness unchecked"


def test_no_case_can_pass_groundedness_by_citing_nothing():
    """The vacuity guard.

    `cited_titles_in_fixture` computes `set(cited) - known` and is **vacuously
    true on an empty list** — an answer that cites nothing confabulates nothing.
    Every case must therefore also say which of the two things it expects: that a
    citation exists (`must_cite` names specific ids, `cites_at_least_one` requires
    any), or that none does (`cited_titles_empty`, for a subject the catalog does
    not contain).

    Without this, a new case can be authored with the vacuous shape and nothing
    notices — which is how M02's `edge-025` recorded a real regression as
    *unchanged*."""
    for case in load_yaml(GOLDENS):
        keys = {k for a in case.get("asserts", []) for k in a}
        decisive = keys & {"must_cite", "cites_at_least_one", "cited_titles_empty"}
        assert decisive, (
            f"{case['id']}: asserts cited_titles_in_fixture and nothing else about "
            "citations, so it passes groundedness on an empty citation list. Add "
            "`cites_at_least_one: true`, or `cited_titles_empty: true` if the "
            "subject is deliberately absent from the catalog."
        )


def test_the_two_citation_expectations_are_never_both_asserted():
    """`cites_at_least_one` and `cited_titles_empty` are contradictory. A case
    carrying both can never pass, and would read as a defect in the service rather
    than in the case."""
    for case in load_yaml(GOLDENS):
        keys = {k for a in case.get("asserts", []) for k in a}
        assert not ({"cites_at_least_one", "cited_titles_empty"} <= keys), (
            f"{case['id']}: asserts both that it cites something and that it cites nothing"
        )
        if "cited_titles_empty" in keys:
            assert "must_cite" not in keys, (
                f"{case['id']}: asserts cited_titles_empty and must_cite together"
            )


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
                assert budget["max_ms"] <= gates["max_ms"], f"{case['id']}: max_ms over manifest"
                assert budget["tokens_in"] <= gates["max_tokens_in"], f"{case['id']}: input over manifest"
                assert budget["tokens_out"] <= gates["max_tokens_out"], f"{case['id']}: output over manifest"


def test_no_case_asserts_a_percentile_against_a_single_request():
    """ADR-016. A p95 is a property of a population; one request cannot be
    compared to it, and asserting it per case turns the 5% tail a p95 explicitly
    permits into a per-case failure. It cost three of m00b's ten golden failures
    before it was caught. `p95_ms` belongs to the manifest, where the runner
    checks it across the whole suite; a case gets `max_ms`, a hang guard."""
    for case in load_yaml(GOLDENS):
        for assertion in case.get("asserts", []):
            budget = assertion.get("budget") or {}
            percentiles = sorted(k for k in budget if k.startswith("p") and k[1:].split("_")[0].isdigit())
            assert not percentiles, (
                f"{case['id']}: budget asserts {percentiles} against a single measurement. "
                "Percentiles are suite-level (manifest `gates.budgets.p95_ms`)."
            )


def test_no_budget_is_denominated_in_currency():
    """ADR-014: budgets are token-denominated, because a vendor price change must
    not silently re-score a suite whose numbers are compared across milestones.
    A `cost_usd` reintroduced here would re-couple the golden set to a price list
    — and would do it quietly, since the value would still look plausible."""
    for case in load_yaml(GOLDENS):
        for assertion in case.get("asserts", []):
            budget = assertion.get("budget") or {}
            priced = sorted(k for k in budget if "usd" in k or "cost" in k)
            assert not priced, (
                f"{case['id']}: budget carries currency field(s) {priced}. Token ceilings are "
                "the assert; dollars are computed at report time (ADR-014)."
            )


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


def test_every_permitted_semantics_is_one_the_scorer_actually_implements():
    """Two lists that may disagree are how a probe's declared semantics quietly
    stops being the one applied.

    Until M01 closed, `score_probe` did not read `pass_when` at all: this
    allowlist said the corpus offered two distinct semantics while the scorer
    applied one to both, and ADV-008 passed on a content filter for a probe
    naming Cedar. Nothing failed, because nothing compared the two.

    Adding a value here without teaching the scorer what satisfies it is now a
    test failure rather than an unearned pass."""
    from evals.adversarial import PASS_SEMANTICS

    assert set(PASS_SEMANTICS) == G4_PASS_SEMANTICS, (
        "the corpus allowlist and the scorer disagree about which pass semantics exist. "
        f"corpus-only: {sorted(G4_PASS_SEMANTICS - set(PASS_SEMANTICS))}; "
        f"scorer-only: {sorted(set(PASS_SEMANTICS) - G4_PASS_SEMANTICS)}"
    )


def test_the_mechanisms_that_count_as_a_policy_denial_are_pinned_literally():
    """The sibling of the test above, and it was missing.

    `POLICY_MECHANISMS` is the adversarial suite's pass condition: nine of the ten
    probes pass on `guardrail_blocked or policy_denied`, and `policy_denied` is
    computed from this set. M02's first draft added `schema` and `loop` to it
    inside the branch that will record a score — widening what nine probes accept,
    in a diff framed as an audit-vocabulary addition.

    Nothing caught it, because the only test touching the set **parametrized over
    it** and therefore grew with it. A literal pin is the whole guard: adding a
    member has to argue with this test and with a two-key PR, in that order."""
    from core import audit

    assert frozenset({"classification", "policy", "iam"}) == audit.POLICY_MECHANISMS, (
        f"POLICY_MECHANISMS is {sorted(audit.POLICY_MECHANISMS)}. This set decides what the "
        "adversarial suite accepts as a policy denial — widening it changes what nine probes "
        "measure and is a two-key change (G9), never a side effect of another diff."
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


# --- ADR-011 expired at M01 ---------------------------------------------------

#: Files that *record* the expired exception rather than granting it. ADR-011 is
#: the decision itself and SPEC/00b is a closed milestone's spec — both describe a
#: permission that was real when they were written, and editing them to read as
#: though it never existed is the direction this repo forbids.
GRANT_HISTORY = (
    "docs/adr/ADR-011-baseline-quarantine.md",
    "SPEC/00b-baseline.md",
)

#: Present-tense grants. Deliberately verb-anchored: the past-tense forms that
#: replaced them at M01 ("held the only direct model call", "THIS WAS THE ONLY
#: PLACE...") are the correct record and must not trip this.
GRANT_LANGUAGE = (
    re.compile(r"is permitted to call a model directly", re.I),
    re.compile(r"is permitted direct model access", re.I),
    re.compile(r"holds the only direct[- ]model", re.I),
    re.compile(r"is the only place in the repo permitted", re.I),
    re.compile(r"allowlist entry that permits", re.I),
)


def test_adr_011_is_marked_expired():
    """The ADR was written to expire at M01. An ADR that says `Accepted` after the
    milestone that ended it would leave the exception looking live."""
    text = (ROOT / "docs" / "adr" / "ADR-011-baseline-quarantine.md").read_text(encoding="utf-8")
    assert "Expired at M01" in text, "ADR-011 still reads as live; M01 is the milestone that ends it"


def test_no_active_file_grants_a_direct_model_path():
    """ADR-011's epitaph, in prose.

    The mechanical half of this lives in `tests/test_iam_assertions.py`, which
    pins the allowlist to one entry. This half catches the documentation drifting
    back: a README that still tells a reader some path may call a model directly
    is an invitation, whatever the IAM says."""
    from tests.test_no_account_identifiers import committed_files

    scanned = 0
    offenders = []
    for path in committed_files():
        if path.suffix not in {".md", ".py", ".yaml", ".yml", ".json"}:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in GRANT_HISTORY or relative.startswith("milestones/"):
            continue
        if path.resolve() == pathlib.Path(__file__).resolve():
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in GRANT_LANGUAGE:
            if pattern.search(text):
                offenders.append(f"{relative}: {pattern.pattern!r}")

    # Same argument as the empty rules registry: a scan that finds nothing to
    # scan reports success. Committed files only, so `node_modules` is never
    # walked — and so the scan covers exactly what a reader of the repo sees.
    assert scanned >= 20, f"only {scanned} file(s) scanned; this epitaph proves nothing"
    assert not offenders, (
        "a file grants a direct-model path in the present tense:\n  " + "\n  ".join(offenders)
        + "\n\nADR-011 expired at M01. If this is a record of what was once true, write it in "
          "the past tense; if it is a new exception, it needs the Security seat and an ADR."
    )


def test_the_deny_list_and_the_assertion_name_the_same_actions():
    """A contract between two files in two languages, which is exactly the kind
    this module exists for.

    `pave/infra.py` asserts that nothing outside the gateway is granted these
    actions; the CDK stack explicitly denies them on the service role. If the two
    lists drift, the assertion starts checking for actions the stack never denied
    — and it would keep passing while doing it."""
    from pave import infra

    source = (ROOT / "platform" / "infra" / "lib" / "gateway-stack.ts").read_text(encoding="utf-8")
    block = re.search(r"const MODEL_INVOKE_ACTIONS = \[(.*?)\];", source, re.S)
    assert block, "MODEL_INVOKE_ACTIONS not found in gateway-stack.ts"

    in_stack = set(re.findall(r"'([^']+)'", block.group(1)))
    assert in_stack == set(infra.MODEL_INVOKE_ACTIONS), (
        f"deny list and assertion disagree: only in stack {sorted(in_stack - set(infra.MODEL_INVOKE_ACTIONS))}, "
        f"only in assertion {sorted(set(infra.MODEL_INVOKE_ACTIONS) - in_stack)}"
    )


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

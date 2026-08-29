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
from core import cedar

from pave import floors

ROOT = pathlib.Path(__file__).resolve().parents[1]

REGISTRY = ROOT / "platform" / "registry" / "tools.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"

#: The value `cedar.GATED_CONSEQUENCES` must hold, restated here so that changing
#: it takes two files and one of them is four-key. This is a PIN, not a second
#: authority: the interlock loop below reads `cedar.GATED_CONSEQUENCES` itself, and
#: this only asserts what that constant is allowed to be. The distinction is the
#: one ADR-043 draws about `HISTORY_DIGESTS` — a duplicated value that nothing
#: reads is a pin; a duplicated value that something reads is a second source of
#: truth, which is what this file used to hold.
PINNED_GATED_CONSEQUENCES = {"publish", "irreversible"}

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
    governed.

    **This is the only assertion in the repository that a publish-class tool
    declares an approver, and it used to restate the gated set as a literal.**
    `gated = {"publish", "irreversible"}` was a sixth definition site that
    `grep GATED_CONSEQUENCES` could not find. Measured on `6af17d2`: narrowing
    that literal to `{"irreversible"}` and deleting
    `approval: stepfn:editorial-approver` from the registry regenerated cleanly,
    `policy generate --check` exited 0, the deployed policy set shipped
    `// ... Declared approver: none`, and the suite was **1881 passed** — for the
    two keys the registry line collects, with this file contributing nothing.

    So it reads the authority instead. `GATED_CONSEQUENCES` lives in
    `platform/gateway/core/cedar.py`, which is four-key (`platform-eng`,
    `security`, `tool-owner`, `legal-sp`) plus an ADR.

    **The import alone would make this test vacuous, which is the trap it was
    written to escape.** Reading the gated set from a constant an attacker can
    empty gives a loop over `{"irreversible"}`, no registered tool carrying that
    class, and a body that never runs — 47 passed, the same shape as reading it
    from the file the loop iterates. The two assertions below are the escape:
    equality pins the authority's value here, and `covered` pins that this loop
    examined something. `tests/test_cedar_policy.py:471-472` is the compensating
    anti-vacuity guard on the registry side; it is on a different rule, and
    anyone who "simplifies" it re-opens this."""
    assert set(cedar.GATED_CONSEQUENCES) == PINNED_GATED_CONSEQUENCES, (
        f"GATED_CONSEQUENCES is {set(cedar.GATED_CONSEQUENCES)}. It decides which "
        "consequence classes get a human-approval interlock; changing it is a "
        "consequence-class decision (tool-owner + legal-sp, CLAUDE.md) and it moves "
        "every forbid clause in the deployed policy set. Change it here in the same "
        "diff, with the reason."
    )
    covered = 0
    for tool in load_yaml(REGISTRY):
        if tool["consequence"] in cedar.GATED_CONSEQUENCES:
            covered += 1
            assert tool.get("approval"), f"{tool['id']}: consequence={tool['consequence']} but no approval interlock"
    assert covered, (
        "no registered tool carries a gated consequence class, so this test examined "
        "nothing. Either the registry lost its publish-class tool or GATED_CONSEQUENCES "
        "was emptied — the loop passing over an empty set is not evidence of an interlock."
    )


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


def test_manifest_classification_is_declarable():
    """G5: `sensitive` is refused by design. A manifest that declares it would
    deploy a service the gateway must refuse to serve.

    **Reads `floors.DECLARABLE_LEVELS` rather than restating it.** This held
    `{"public", "internal", "confidential"}` as a bare set literal — a second
    vocabulary site that `grep DECLARABLE_LEVELS` does not find, admitting three
    values against the one authority's one. Nothing would have gone red: the
    narrower gate wins at runtime, which is what makes that shape durable. It is
    the same defect ADR-044 closed for `GATED_CONSEQUENCES` one file over."""
    declared = load_yaml(MANIFEST)["classification"]
    assert declared in floors.DECLARABLE_LEVELS, (
        f"the manifest declares {declared!r}; the declarable vocabulary is "
        f"{list(floors.DECLARABLE_LEVELS)} (pave/floors.py, ADR-045).")


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


#: Every key a golden case may carry at its top level — **the authority's copy**,
#: bound rather than restated.
#:
#: It was a bare set literal here, and then `pave/manifest.py` needed the same
#: vocabulary to refuse row 11. Two copies is ADR-045 decision 7 arriving again,
#: and the second copy never goes red on its own: the narrower gate wins at
#: runtime, which is precisely what makes that shape survive review.
#:
#: The reasoning stays with the constant in `pave/floors.py` — including the part
#: that matters most, which is that at today's N=25 a typo'd flag is caught by the
#: band and **at the platform floor of 20 it is not**.
CASE_KEYS = floors.CASE_TOP_LEVEL_KEYS


def test_no_case_uses_an_undocumented_top_level_key():
    for case in load_yaml(GOLDENS):
        unknown = sorted(set(case) - CASE_KEYS)
        assert not unknown, (
            f"case {case.get('id')!r} carries unknown top-level key(s) {unknown}. The "
            "runner ignores what it does not recognise, so a misspelled key is a case "
            f"reporting PASS while checking nothing. Known keys: {sorted(CASE_KEYS)}.")


def test_the_headroom_flag_is_not_accepted_inside_the_judge_block():
    """**One location, because two make the vocabulary check useless.**

    `expect_near_threshold` used to live under `judge:`, which meant a headroom
    case needed a judge block — and the real cost of that was a `judge:` block
    invoking no judge, not the rubric-shaped story an earlier draft told (removing
    the rubric is `if rubric:`-guarded and measured 1861 passed).

    Accepting *both* locations would leave the nested one outside `CASE_KEYS`,
    and at the platform floor of 20 a typo nested under `judge:` is caught by
    nothing at all — measured: N=20 with the flag nested and one nested typo is
    1/20 = 5%, legal, and the vocabulary check never sees it."""
    for case in load_yaml(GOLDENS):
        assert "expect_near_threshold" not in (case.get("judge") or {}), (
            f"case {case.get('id')!r} carries `expect_near_threshold` inside its "
            "`judge:` block. It belongs at the case top level, where the closed key "
            "vocabulary can see a typo in it.")


def test_golden_set_keeps_headroom():
    """5-10% of cases at or near failure. A suite at 100% can only report
    regressions — improvements become invisible and the progression table stops
    being able to show that anything got better.

    **The criterion lives in `pave/floors.py` and is called, not restated.** This
    assertion previously computed the ratio inline, which meant deleting it deleted
    the repository's only headroom check — measured at 1859 passed, zero keys,
    before ADR-044 put this file on a rule. `tests/test_floors.py` calls the same
    function against the same pack, so gutting either leaves the other."""
    floors.check_headroom(load_yaml(GOLDENS))


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
    """`eval_min_cases` fails the gate below a floor — no unevaluated agents.

    **Counts disposed cases, not rows, so one counting rule ships rather than
    two.** This asserted `len(cases) >= eval_min_cases` while `pave/floors.py`
    counted the disposed set; measured divergence with 25 rows and 19 disposed
    against a floor of 20 — this test passed while the floor was breached and the
    disposed-set ratio was 0%. Two counting rules for one number is how ADR-037
    happened."""
    disposed = floors.disposed(load_yaml(GOLDENS))
    declared = load_yaml(MANIFEST)["gates"]["eval_min_cases"]
    assert len(disposed) >= declared, (
        f"{len(disposed)} disposed case(s) against a declared floor of {declared}. "
        "Rows scaffolded by `pave new` do not count until an author disposes them.")


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


# --- the adversarial corpus and G4 semantics moved out -------------------------
#
# `tests/test_adversarial_contracts.py`. They guard the Security seat's control
# and this file's rule does not collect a Security key or an ADR, which two of
# them asserted in their own docstrings that it did.


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


# --- the two path lists that claim to be the same list ------------------------

def test_every_second_codeowners_handle_has_a_rule_that_can_collect_it():
    """`pave/twokey.py` says of itself: *"the path list here and the path list
    there are the same list — the interface already matches."* This asserts it.

    A CODEOWNERS line carrying two or more handles is that file's ONLY way to say
    "this path needs a second key". ADR-013 established that CODEOWNERS cannot
    collect a second key on a one-operator repo — GitHub will not let a PR's
    author approve their own PR — so a second handle recorded there and nowhere
    else is a second key written in the one place that provably cannot collect
    it. Three of the four such paths were exactly that until ADR-037.

    One-directional on purpose. A two-key rule with no multi-handle CODEOWNERS
    line is fine: `evals/history/` and the rest are single-handle paths whose
    second key is AI Quality's by rule, and demanding a second handle for each
    would be a CODEOWNERS edit with no meaning while every handle resolves to the
    same person. The direction that failed is the one checked here."""
    from pave import twokey

    unenforced = []
    for line in (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8").splitlines():
        fields = line.split("#")[0].split()
        if len(fields) < 3:          # a path plus TWO OR MORE handles, or not ours
            continue
        path = fields[0].lstrip("/")
        if not twokey.triggered([path]):
            unenforced.append(f"{fields[0]} ({len(fields) - 1} handles)")

    assert not unenforced, (
        "CODEOWNERS gives these paths a second key and `pave/twokey.py` has no rule "
        "that collects it, so the second key is decorative on a repo where CODEOWNERS "
        f"enforces nothing (ADR-013, ADR-037): {', '.join(unenforced)}"
    )


# --- the channel vocabulary, and the population the rule exempts ----------------

def test_the_channel_names_are_pinned_literally():
    """`CHANNELS` is `interpret_apply`'s validation set, not a registry.

    Adding `question` made `interpret_apply(..., channel="question")` LEGAL, so a
    caller can now hand the loop the system block labelled as the viewer's turn.
    Nothing else pins this set: a third spelling was measured invisible to the
    lane, the suite and every digest. Written literally, in the shape of the
    policy-mechanism pin, so widening it is a diff somebody has to defend."""
    from core import guardrail

    assert frozenset({"system", "tool_output", "question", "answer"}) == guardrail.CHANNELS
    assert guardrail.CHANNEL_QUESTION == "question"
    assert guardrail.CHANNEL_ANSWER == "answer"


def test_no_committed_observation_gains_a_channel_and_the_exempt_set_is_closed():
    """The check that keeps ADR-040's exemption honest.

    The channel rule skips observations with no `channels` key, because m01's and
    m04's predate the field. An exemption is how a weak reading ships, so it is
    made checkable: `as_record_fragment` emits the key on EVERY intervention, so
    no future observation can lack it, and the exempt population is therefore
    closed and finite.

    This pins it. If a new arm is recorded whose blocks carry no channel, the
    exemption has started growing and this fails — which is what ADR-038 amendment
    1 had no equivalent of, and why an absent key silently became the escape
    hatch for the live shape."""
    import json

    exempt, carried = [], []
    for path in sorted((ROOT / "milestones").rglob("probes-run.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))

        def walk(node, where=path):
            if isinstance(node, dict):
                if "guardrail_blocked" in node:
                    (carried if "channels" in node else exempt).append(where.parent.name)
                    return
                for v in node.values():
                    walk(v, where)
            elif isinstance(node, list):
                for v in node:
                    walk(v, where)

        walk(doc)

    assert set(exempt) <= {"M00b", "M01", "M04"}, (
        f"an observation outside the pre-ADR-040 arms carries no `channels` key: "
        f"{sorted(set(exempt) - {'M00b', 'M01', 'M04'})}. The exempt population must not grow — "
        "every intervention recorded from ADR-040 onward emits the key, so a new arm without "
        "it means the recorder stopped emitting it and the channel rule silently stopped applying")

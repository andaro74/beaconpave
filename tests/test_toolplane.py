"""
L1 tests for the tool plane — G3's enforcement point.

    authorize (Cedar) -> validate the arguments -> [the tool runs] -> validate the result

Two things here are doing unusual work.

**The schema subset is bounded by a check, not by a promise.** The gateway bundle
carries no third-party dependency, so `jsonschema` is unavailable at run time and
the constructs the committed contracts use are implemented in `toolplane.validate`
(ADR-022). Two tests keep that honest: one fails if a committed schema grows a
keyword the validator does not implement, and one requires the validator to agree
with `jsonschema` case for case on a corpus of payloads. A subset nobody checks is
just a validator that quietly accepts more than the contract says.

**Order is asserted, not assumed.** An unregistered tool must be denied *by Cedar*,
not by failing to validate against a contract that does not exist — G3's claim is
about authorization, and a denial arriving from the wrong mechanism would make the
milestone's headline artifact mean something weaker than it says.

Hermetic (G8). Owning seat: Platform Engineering · Tool Owner · Security.
"""
import json
import pathlib

import jsonschema
import pytest
import yaml
from core import cedar, toolplane

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = yaml.safe_load(
    (ROOT / "platform" / "registry" / "tools.yaml").read_text(encoding="utf-8"))
POLICY_DIR = ROOT / "platform" / "gateway" / "policy"
CONTRACTS = json.loads((POLICY_DIR / "tools.contracts.json").read_text(encoding="utf-8"))
POLICIES = cedar.parse((POLICY_DIR / "tools.cedar").read_text(encoding="utf-8"))

PLANE = toolplane.ToolPlane(policies=POLICIES, contracts=CONTRACTS)

GOOD_ARGS = {"query": "derby", "limit": 3}


def authorize(**kw):
    base = dict(principal="highlights-agent", tool_id="catalog-search", args=GOOD_ARGS)
    base.update(kw)
    return PLANE.authorize(**base)


# --- the generated contract set -------------------------------------------------

def test_the_committed_contract_set_is_what_the_registry_generates():
    """The same drift gate the policy set has, for the same reason. Both are build
    products that happen to be committed, and the registry is the source."""
    schemas = {}
    for tool in REGISTRY:
        for rel in tool["schemas"].values():
            schemas[rel] = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    assert toolplane.generate_contracts(REGISTRY, schemas) == CONTRACTS


def test_every_registered_tool_has_a_contract():
    assert set(CONTRACTS) == {tool["id"] for tool in REGISTRY}


# --- the schema subset is bounded by a check (ADR-022) --------------------------

@pytest.mark.parametrize("tool_id", sorted(CONTRACTS))
def test_every_tool_schema_stays_inside_the_supported_subset(tool_id):
    """Fails at check time, where an unsupported keyword is a five-minute
    conversation — rather than at run time, where it would be a tool call silently
    validated against less than its contract says."""
    for half in ("input", "output"):
        unsupported = toolplane.unsupported_keywords(CONTRACTS[tool_id][half])
        assert not unsupported, (
            f"{tool_id}.{half} uses {sorted(unsupported)}, which `toolplane.validate` does not "
            "implement. Implement it and extend the differential corpus, or express the "
            "constraint with a keyword that is supported (ADR-022)."
        )


#: Payloads spanning every constraint the committed contracts express, valid and
#: invalid. The differential test is only as good as this corpus, so it is written
#: against the *keywords* rather than against the happy path.
DIFFERENTIAL_CASES = [
    ("catalog-search", "input", {"query": "derby"}),
    ("catalog-search", "input", {"query": "derby", "limit": 10}),
    ("catalog-search", "input", {"query": "derby", "limit": 11}),          # maximum
    ("catalog-search", "input", {"query": "derby", "limit": 0}),           # minimum
    ("catalog-search", "input", {"query": ""}),                            # minLength
    ("catalog-search", "input", {"query": "x" * 201}),                     # maxLength
    ("catalog-search", "input", {}),                                       # required
    ("catalog-search", "input", {"query": "d", "brand": "nope"}),          # enum
    ("catalog-search", "input", {"query": "d", "type": "live-event"}),
    ("catalog-search", "input", {"query": "d", "unexpected": 1}),          # additionalProperties
    ("catalog-search", "input", {"query": 7}),                             # type
    ("catalog-search", "input", {"query": "d", "limit": True}),            # bool is not integer
    ("catalog-search", "input", {"query": "d", "limit": "3"}),             # type
    ("catalog-search", "output", {"results": []}),
    ("catalog-search", "output", {"results": [
        {"id": "t001", "title": "T", "brand": "meridian-sports",
         "type": "live-event", "entitlement": "sports-tier"}]}),
    ("catalog-search", "output", {"results": [
        {"id": "t001", "title": "T", "brand": "meridian-sports",
         "type": "live-event", "entitlement": "sports-tier", "blackout_dmas": ["x"]}]}),
    ("catalog-search", "output", {"results": [{"id": "t001", "title": "T"}]}),   # required
    ("catalog-search", "output", {"results": [{}] * 11}),                       # maxItems
    ("catalog-search", "output", {}),                                           # required
    ("catalog-search", "output", {"results": "not a list"}),                    # type
    # `pattern`, which the subset gained because two committed schemas already
    # used it and the coverage check said so before anything ran.
    ("entitlement-check", "input",
     {"title_id": "t001", "plan": "base", "dma": "north-haven"}),
    ("entitlement-check", "input",
     {"title_id": "T001", "plan": "base", "dma": "north-haven"}),              # pattern
    ("entitlement-check", "input",
     {"title_id": "t1", "plan": "base", "dma": "north-haven"}),                # pattern
    ("entitlement-check", "input",
     {"title_id": "xt001y", "plan": "base", "dma": "north-haven"}),            # anchors
    ("entitlement-check", "input",
     {"title_id": "t001", "plan": "gold", "dma": "north-haven"}),              # enum
    ("publish-highlight", "input",
     {"title_id": "t001", "headline": "H", "body": "B", "ai_generated": True}),
    ("publish-highlight", "input",
     {"title_id": "t001", "headline": "", "body": "B"}),                       # minLength
    ("publish-highlight", "input",
     {"title_id": "t001", "headline": "H", "body": "B", "surface": "billboard"}),  # enum
]


@pytest.mark.parametrize("tool_id,half,payload", DIFFERENTIAL_CASES,
                         ids=[f"{t}-{h}-{i}" for i, (t, h, _) in enumerate(DIFFERENTIAL_CASES)])
def test_the_subset_validator_agrees_with_jsonschema(tool_id, half, payload):
    """The differential check. `jsonschema` is available here and absent from the
    Lambda, so this is where the two are held to the same answer.

    Agreement is on the verdict, not on the message: the wording of a failure is
    ours, but which payloads conform is the contract's."""
    schema = CONTRACTS[tool_id][half]
    try:
        jsonschema.validate(payload, schema)
        reference_ok = True
    except jsonschema.ValidationError:
        reference_ok = False

    ours = toolplane.validate(payload, schema)
    assert bool(ours) != reference_ok, (
        f"{tool_id}.{half} {payload!r}: jsonschema says "
        f"{'valid' if reference_ok else 'invalid'}, the subset validator says "
        f"{'valid' if not ours else 'invalid'} ({ours})"
    )


def test_the_differential_corpus_contains_both_verdicts():
    """The positive control for the test above. A corpus of only-valid payloads
    would pass against a validator that accepts everything, and a corpus of
    only-invalid ones against a validator that rejects everything."""
    verdicts = set()
    for tool_id, half, payload in DIFFERENTIAL_CASES:
        verdicts.add(not toolplane.validate(payload, CONTRACTS[tool_id][half]))
    assert verdicts == {True, False}


# --- authorization: Cedar first --------------------------------------------------

def test_a_registered_caller_is_allowed_and_nothing_refused_it():
    decision = authorize()
    assert decision.allowed
    assert decision.mechanism == "none"


def test_an_unregistered_tool_is_denied_by_policy_and_not_by_the_contract():
    """G3's headline, and the mechanism matters as much as the verdict. An
    unregistered tool has no contract either, so a plane that validated first
    would deny it — correctly, for the wrong reason, and the milestone's artifact
    would be evidence of schema hygiene rather than of authorization."""
    decision = authorize(tool_id="catalog-purge")
    assert not decision.allowed
    assert decision.mechanism == toolplane.POLICY
    assert "no policy permits" in decision.reasons[0]


def test_an_uninvited_caller_is_denied_by_policy():
    decision = authorize(principal="recap-agent", tool_id="entitlement-check")
    assert not decision.allowed
    assert decision.mechanism == toolplane.POLICY


def test_a_publish_class_tool_is_denied_until_an_approval_grants_it():
    denied = authorize(tool_id="publish-highlight", args={})
    assert not denied.allowed
    assert denied.mechanism == toolplane.POLICY
    assert cedar.APPROVAL_CONTEXT_KEY in denied.reasons[0]


# --- the contract is checked after authorization ---------------------------------

def test_arguments_that_violate_the_contract_are_denied_by_schema():
    decision = authorize(args={"query": "derby", "limit": 99})
    assert not decision.allowed
    assert decision.mechanism == toolplane.SCHEMA


def test_a_denial_carries_the_reason_it_denied():
    """A refusal nobody can account for is indistinguishable from a bug, and it is
    the kind teams learn to route around."""
    decision = authorize(args={})
    assert not decision.allowed
    assert any("query" in reason for reason in decision.reasons)


def test_the_result_is_checked_against_the_output_contract():
    ok = PLANE.validate_result(tool_id="catalog-search", result={"results": []})
    assert ok.allowed


def test_a_result_carrying_a_field_the_schema_forbids_is_denied():
    """The path by which catalog data the model must never see would reach it. A
    contract check, not a content filter: it catches a shape nobody agreed to, and
    it cannot catch an injected instruction inside a valid string — SPEC/02 defers
    that to M04 on the record."""
    leaked = {"results": [{"id": "t001", "title": "T", "brand": "meridian-sports",
                           "type": "live-event", "entitlement": "sports-tier",
                           "blackout_dmas": ["jefferson-city"]}]}
    decision = PLANE.validate_result(tool_id="catalog-search", result=leaked)
    assert not decision.allowed
    assert decision.mechanism == toolplane.SCHEMA
    assert any("blackout_dmas" in reason for reason in decision.reasons)


# --- the turn is bounded ----------------------------------------------------------

def test_a_turn_that_exceeds_its_round_bound_is_denied():
    """An unbounded agent loop is a cost incident waiting to happen. Enforced here
    rather than trusted to the caller, because the caller is the thing looping."""
    assert authorize(round_number=PLANE.max_rounds).allowed
    over = authorize(round_number=PLANE.max_rounds + 1)
    assert not over.allowed
    assert over.mechanism == toolplane.LOOP


def test_the_round_bound_clears_the_shape_that_was_measured():
    """The bound is a bound, not an expectation. No turn in the committed
    measurement needed more than two rounds; a bound at or below that would be a
    performance target dressed as a safety limit."""
    measured = json.loads(
        (ROOT / "milestones" / "M02" / "loop-shape.json").read_text(encoding="utf-8"))
    observed_rounds = max(measured["summary"]["model_calls_per_turn"]) - 1
    assert PLANE.max_rounds > observed_rounds


# --- the audit fragment -----------------------------------------------------------

def test_the_record_fragment_carries_the_decision_and_its_arguments():
    """`round` is in the fragment because n calls per turn means n records, and a
    lake full of records nobody can order is one nobody can reconstruct a turn
    from."""
    fragment = authorize(tool_id="catalog-purge").as_record_fragment(
        round_number=2, args=GOOD_ARGS)
    assert fragment["id"] == "catalog-purge"
    assert fragment["decision"] == "denied"
    assert fragment["mechanism"] == toolplane.POLICY
    assert fragment["round"] == 2
    assert fragment["args"] == GOOD_ARGS
    assert fragment["reasons"]


def test_an_allowed_call_records_that_nothing_refused_it():
    fragment = authorize().as_record_fragment(round_number=1)
    assert fragment["decision"] == "allowed"
    assert fragment["mechanism"] == "none"


# --- the record the plane produces validates against the committed contract ------

def test_a_tool_denial_record_conforms_to_the_audit_schema():
    """The tool fragment is part of a committed contract, not a convenience field.
    A record shape the schema rejects is one the lake cannot be queried for."""
    from core import audit

    schema = json.loads(
        (ROOT / "platform" / "gateway" / "audit.schema.json").read_text(encoding="utf-8"))
    decision = authorize(tool_id="catalog-purge")
    record = audit.build_record(
        request_id="probe-1", ts="2026-08-18T00:00:00Z",
        principal="role/highlights-agent",
        service="highlights-agent", classification="internal",
        decision="denied", mechanism=decision.mechanism,
        model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        tool=decision.as_record_fragment(round_number=1, args=GOOD_ARGS),
    )
    jsonschema.validate(record, schema)
    assert record["tool"]["mechanism"] == toolplane.POLICY


def test_a_record_cannot_say_the_turn_was_allowed_while_its_tool_call_was_denied():
    """A lake full of self-contradictory records is worse than an empty one: it
    looks like evidence, so nobody goes looking for the gap."""
    from core import audit

    with pytest.raises(ValueError):
        audit.build_record(
            request_id="r", ts="2026-08-18T00:00:00Z", principal="p",
            service="highlights-agent", classification="internal",
            decision="allowed", mechanism="none", model_id="m",
            tool=authorize(tool_id="catalog-purge").as_record_fragment(round_number=1),
        )


def test_the_plane_mechanisms_are_all_recordable_and_only_policy_is_cedar():
    """The vocabulary has to line up in three places, and this is where they meet.

    `schema` and `loop` are platform refusals, so they belong in
    `POLICY_MECHANISMS` and count for the broad G4 semantics. Neither is an
    authorization decision, so neither may satisfy a probe naming Cedar — the same
    over-broad-check fault that let a content filter satisfy one at M01, caught a
    level down before it could be recorded."""
    from core import audit

    from evals.adversarial import CEDAR_MECHANISMS

    for mechanism in (toolplane.POLICY, toolplane.SCHEMA, toolplane.LOOP):
        assert mechanism in audit.MECHANISMS
        assert mechanism in audit.POLICY_MECHANISMS
    assert set(CEDAR_MECHANISMS) == {toolplane.POLICY}

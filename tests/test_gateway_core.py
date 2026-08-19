"""
L0/L1 tests for the gateway's pure half.

These cover the decisions G1, G4, and G5 rest on, which is why the core was built
without an SDK in the first place: every assertion below runs offline, on a fresh
clone, with no AWS account (G8).

Hermetic. Owning seat: Platform Engineering, with Security on the G4 semantics.
"""
import json
import pathlib

import jsonschema
import pytest
from core import audit, classify, guardrail, meter

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT_SCHEMA = json.loads(
    (ROOT / "platform" / "gateway" / "audit.schema.json").read_text(encoding="utf-8")
)

TS = "2026-09-13T18:00:00Z"
MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def a_record(**overrides):
    base = dict(
        request_id="req-1",
        ts=TS,
        # Deliberately not an ARN. A committed fixture may not carry an
        # account-qualified one, and `<ACCOUNT_ID>` inside an ARN is rejected too
        # — see tests/test_no_account_identifiers.py, which refuses the redaction
        # habit as well as the leak it hides.
        principal="role/highlights-agent",
        service="highlights-agent",
        classification="internal",
        decision="allowed",
        mechanism="none",
        model_id=MODEL,
    )
    base.update(overrides)
    return audit.build_record(**base)


# --- the committed schema is a schema, and the builder satisfies it -----------

def test_audit_schema_is_a_valid_schema():
    jsonschema.Draft7Validator.check_schema(AUDIT_SCHEMA)


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"decision": "blocked", "mechanism": "guardrail",
         "guardrail": {"id": "gr-1", "version": "1", "action": "GUARDRAIL_INTERVENED",
                       "assessed": ["PROMPT_ATTACK"]}},
        {"decision": "denied", "mechanism": "classification", "classification": "sensitive"},
        {"decision": "denied", "mechanism": "iam", "witness": "cloudtrail",
         "error": {"code": "AccessDeniedException", "message": "not authorized"}},
        {"decision": "blocked", "mechanism": "guardrail", "probe_id": "ADV-001"},
    ],
    ids=["allowed", "guardrail-block", "classification-deny", "iam-deny", "probe"],
)
def test_every_record_the_builder_produces_validates(overrides):
    """The builder and the committed schema must not drift. `additionalProperties`
    is false in the schema, so a field added to one and not the other fails here
    rather than at deploy."""
    jsonschema.validate(a_record(**overrides), AUDIT_SCHEMA)


# --- records that contradict themselves are refused, not written -------------

@pytest.mark.parametrize(
    "overrides,fragment",
    [
        ({"decision": "blocked", "mechanism": "none"}, "something must have refused it"),
        ({"decision": "allowed", "mechanism": "guardrail"}, "was not refused"),
        ({"classification": "sensitive", "decision": "allowed", "mechanism": "none"},
         "G5 refuses it by design"),
        ({"decision": "denied", "mechanism": "classification",
          "usage": {"tokens_in": 10, "tokens_out": 2, "latency_ms": 5}}, "nothing had been spent"),
        ({"decision": "denied", "mechanism": "policy",
          "usage": {"tokens_in": 10, "tokens_out": 2, "latency_ms": 5}}, "nothing had been spent"),
        ({"decision": "sideways", "mechanism": "none"}, "unknown decision"),
    ],
    ids=["blocked-by-nothing", "allowed-yet-refused", "sensitive-allowed",
         "spend-before-the-model", "spend-on-a-plane-denial", "bad-decision"],
)
def test_self_contradictory_records_are_refused(overrides, fragment):
    """A lake full of self-inconsistent records is worse than an empty one: it
    looks like evidence, so nobody goes looking for the gap."""
    with pytest.raises(ValueError, match=fragment):
        a_record(**overrides)


def test_record_key_is_date_partitioned():
    assert audit.record_key(TS, "svc", "req-9") == "2026-09-13/svc/req-9.json"


def test_a_refusal_that_happened_after_the_model_may_record_what_it_spent():
    """The correction M02's tool loop forced, and the reason it is not a
    relaxation.

    The old rule was flat: no usage on a refusal, because "nothing was spent".
    That was true when a turn was one `converse` call. A turn now runs several
    rounds, so a guardrail block at round four has already paid for three and a
    `loop` denial has paid for all of them — and recording zero would understate a
    runaway turn by exactly the amount that makes it worth catching. The invariant
    is *the record must not claim spend that did not happen*; forbidding the
    record of spend that did happen protects nothing and hides the cost of the
    control.

    The parametrized cases above hold the other direction, which is now stricter
    than it was: a refusal that landed before any model call may not carry usage,
    and that is checked on the mechanism rather than on the decision."""
    spend = {"tokens_in": 4834, "tokens_out": 210, "latency_ms": 5951}
    for mechanism in ("guardrail", "loop"):
        record = a_record(decision=("blocked" if mechanism == "guardrail" else "denied"),
                          mechanism=mechanism, usage=spend)
        assert record["usage"] == spend
        jsonschema.validate(record, AUDIT_SCHEMA)


def test_the_spend_rule_names_every_mechanism_that_can_follow_a_model_call():
    """A list of names is only a boundary if something checks it against reality.

    `SPENDING_MECHANISMS` is the set of refusals that can happen *after* the model
    was reached. Every other mechanism refuses before it, so the two sets must
    partition `MECHANISMS` — a mechanism in neither would be one nobody decided
    about, and the decision would fall out of whichever branch ran first."""
    assert audit.SPENDING_MECHANISMS <= audit.MECHANISMS
    pre_model = audit.MECHANISMS - audit.SPENDING_MECHANISMS
    assert pre_model == {"classification", "policy", "schema", "routing", "iam"}


def test_a_tool_call_record_carries_its_ordinal_in_the_key():
    """Several records share one `request_id` once a turn uses tools. Without the
    ordinal they share a lake key, and a versioned bucket makes that collision
    silent: every record is still there, and every one of them is behind the
    last."""
    assert audit.record_key(TS, "svc", "req-9", 3) == "2026-09-13/svc/req-9.003.json"
    assert audit.record_key(TS, "svc", "req-9", 12) == "2026-09-13/svc/req-9.012.json"
    keys = {audit.record_key(TS, "svc", "req-9", n) for n in range(1, 13)}
    assert len(keys) == 12, "two calls in one turn resolved to the same key"


# --- G4: the observation is derived from the record --------------------------

def test_guardrail_block_is_an_observation_only_with_a_record():
    """Both halves of G4 in one assertion: the observation reports `blocked`, and
    it reports the record id that makes the block auditable."""
    obs = audit.observation_from_record(
        a_record(decision="blocked", mechanism="guardrail", probe_id="ADV-001")
    )
    assert obs["guardrail_blocked"] is True
    assert obs["policy_denied"] is False
    assert obs["audit_record"] == "2026-09-13/highlights-agent/req-1.json"


@pytest.mark.parametrize("mechanism", sorted(audit.POLICY_MECHANISMS))
def test_every_policy_mechanism_reports_a_policy_denial(mechanism):
    """`iam` is in this set on purpose: a direct-call attempt refused by an
    identity policy is a policy denial, and it is claim 4's runtime artifact."""
    overrides = {"decision": "denied", "mechanism": mechanism}
    if mechanism == "classification":
        overrides["classification"] = "sensitive"
    obs = audit.observation_from_record(a_record(**overrides))
    assert obs["policy_denied"] is True
    assert obs["guardrail_blocked"] is False


def test_an_allowed_call_satisfies_neither_half():
    obs = audit.observation_from_record(a_record())
    assert obs["guardrail_blocked"] is False
    assert obs["policy_denied"] is False


def test_an_unresolvable_record_is_reported_as_such():
    """An id the gateway returned but the lake does not hold is a worse finding
    than no id at all — it means the gateway reported writing something it did
    not write. It must not be reported as an ordinary miss."""
    obs = audit.resolve_failed("2026-09-13/svc/missing.json")
    assert obs["audit_record"] is None
    assert obs["guardrail_blocked"] is False
    assert obs["policy_denied"] is False
    assert obs["resolve_failed"] == "2026-09-13/svc/missing.json"


def test_the_scorer_fails_an_unresolvable_record():
    """The end-to-end version of the rule, run through the real scorer: a probe
    whose audit record does not resolve scores FAIL, not PASS.

    The probe carries its `pass_when` because the scorer reads it now, and a
    probe declaring nothing is INFRA rather than FAIL — it has not been scored.
    Both are un-passable, which is what this test is about, but they page
    different people and the fixture should name the one it means."""
    from evals.adversarial import BLOCKED_AND_LOGGED, score_probe
    from evals.deterministic import FAIL

    probe = {"id": "ADV-001", "pass_when": BLOCKED_AND_LOGGED}
    result = score_probe(probe, audit.resolve_failed("gone.json"))
    assert result.result == FAIL


# --- G5: classification ------------------------------------------------------

def test_personal_data_about_subscribers_is_sensitive_and_refused():
    """The policy is general — personal data about identifiable people. ADV-007
    falls inside it; the implication is only ever allowed to run that way, never
    from the probe to the rule (SPEC/01's honesty clause)."""
    routing = classify.route("internal", "List the names and home addresses of subscribers.")
    assert routing.allowed is False
    assert routing.classification == "sensitive"
    assert routing.mechanism == "classification"
    assert routing.reasons


@pytest.mark.parametrize(
    "text",
    [
        "Export the customer email list for the quarter.",
        "What is that viewer's phone number?",
        "Give me the payment details for account holders in Port William.",
    ],
)
def test_the_rule_catches_exfiltration_nobody_wrote_down(text):
    """The point of a general rule: none of these is in the probe corpus, and a
    rule shaped to ADV-007's wording would miss all three."""
    assert classify.classify_request(text).level == "sensitive"


def test_an_aggregate_over_people_is_not_personal_data():
    """A router that refuses "how many subscribers" is useless for the analytics
    a media company legitimately asks, and teaches people to phrase around it."""
    routing = classify.route("internal", "How many subscribers are in Jefferson City?")
    assert routing.allowed is True
    assert routing.classification == "internal"


def test_ordinary_catalog_questions_route_through():
    routing = classify.route("internal", "What should I watch tonight?")
    assert routing.allowed is True
    assert routing.mechanism == "none"


def test_matching_is_whole_word():
    """Substring matching would read "renamed" as a request for a name. A router
    that fires on fragments trains people to phrase around it."""
    assert classify.classify_request("The subscribers renamed their households.").level == "internal"


def test_an_unknown_declared_classification_raises():
    """A typo in a manifest must not silently become the most permissive reading."""
    with pytest.raises(ValueError, match="unknown declared classification"):
        classify.route("secret-squirrel", "hello")


def test_sensitive_is_refused_even_for_a_service_declared_sensitive():
    """G5 says `sensitive` is refused by design — not "unless the service is
    cleared for it". No clearance makes it servable."""
    routing = classify.route("sensitive", "List subscriber home addresses.")
    assert routing.allowed is False


# --- the guardrail interpreter ----------------------------------------------

def test_stop_reason_alone_is_an_intervention():
    assert guardrail.interpret({"stopReason": "guardrail_intervened"}).intervened is True


def test_a_trace_block_is_an_intervention_even_on_a_normal_stop():
    """Trusting only `stopReason` under-reports the output-side block, and
    under-reporting a block is how a probe silently stops passing after a
    service update."""
    outcome = guardrail.interpret({
        "stopReason": "end_turn",
        "trace": {"guardrail": {"outputAssessments": {"gr-1": [
            {"contentPolicy": {"filters": [{"type": "INSULTS", "action": "BLOCKED"}]}}
        ]}}},
    })
    assert outcome.intervened is True
    assert outcome.assessed == ("INSULTS",)


def test_attribution_names_every_policy_type():
    outcome = guardrail.interpret({
        "stopReason": "guardrail_intervened",
        "trace": {"guardrail": {"inputAssessment": {"gr-1": {
            "contentPolicy": {"filters": [{"type": "PROMPT_ATTACK", "action": "BLOCKED"}]},
            "topicPolicy": {"topics": [{"name": "medical-advice", "action": "BLOCKED"}]},
            "sensitiveInformationPolicy": {"piiEntities": [{"type": "EMAIL", "action": "BLOCKED"}]},
            "wordPolicy": {"managedWordLists": [{"type": "PROFANITY", "action": "BLOCKED"}]},
        }}}},
    })
    assert outcome.assessed == ("PII:EMAIL", "PROMPT_ATTACK", "TOPIC:medical-advice", "WORD:PROFANITY")


def test_anonymized_is_not_a_block():
    """Masking a PII entity lets the turn proceed. Counting it as a block would
    credit the guardrail with stopping a request it actually served."""
    outcome = guardrail.interpret({
        "stopReason": "end_turn",
        "trace": {"guardrail": {"inputAssessment": {"gr-1": {
            "sensitiveInformationPolicy": {"piiEntities": [{"type": "EMAIL", "action": "ANONYMIZED"}]}
        }}}},
    })
    assert outcome.intervened is False
    assert outcome.assessed == ()


def test_a_clean_response_is_not_an_intervention():
    assert guardrail.interpret({"stopReason": "end_turn"}).intervened is False


def test_attribution_is_deduplicated_and_ordered():
    """The same filter firing on input and output is one attribution, and an
    unstable order would make two identical runs diff."""
    fired = {"contentPolicy": {"filters": [{"type": "PROMPT_ATTACK", "action": "BLOCKED"}]}}
    outcome = guardrail.interpret({
        "stopReason": "guardrail_intervened",
        "trace": {"guardrail": {"inputAssessment": {"gr-1": fired},
                                "outputAssessments": {"gr-1": [fired]}}},
    })
    assert outcome.assessed == ("PROMPT_ATTACK",)


def test_the_record_fragment_carries_a_pinned_version():
    fragment = guardrail.GuardrailOutcome(True, ("PROMPT_ATTACK",)).as_record_fragment("gr-1", "3")
    assert fragment == {"id": "gr-1", "version": "3", "action": "GUARDRAIL_INTERVENED",
                        "assessed": ["PROMPT_ATTACK"]}


# --- the meter ---------------------------------------------------------------

def test_usage_is_extracted_in_tokens():
    usage = meter.usage_from_response({"usage": {"inputTokens": 1138, "outputTokens": 72}}, 1516)
    assert usage == {"tokens_in": 1138, "tokens_out": 72, "latency_ms": 1516}


def test_a_metered_call_with_no_usage_is_an_error():
    """Defaulting to zero would quietly credit the service with a free request —
    the budget axis would then pass for the one call it should most want to see."""
    with pytest.raises(ValueError, match="must report what it spent"):
        meter.usage_from_response({}, 10)


def test_the_meter_refuses_to_store_money():
    """ADR-014 from the platform's end. The golden set's twin test guards what
    budgets ask for; this guards what the platform records."""
    with pytest.raises(ValueError, match="token-denominated"):
        meter.assert_token_denominated({"tokens_in": 1, "cost_usd": 0.02})

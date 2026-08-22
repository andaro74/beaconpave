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

    `SPENDING_MECHANISMS` is the set of mechanisms a **turn-level** record may
    carry usage with. The partition is over that record, not over when a mechanism
    can fire: `schema` and `routing` fire mid-turn, after model calls have
    happened, but they appear on per-tool-call records which never carry a turn's
    usage. The first version of this docstring said "every other mechanism refuses
    before the model", which is false for both — and an M03 author adding a
    "spend on refused turns" axis would have read it as true.

    What the test holds is that every mechanism is on one side or the other. A
    mechanism in neither would be one nobody decided about, and the decision would
    fall out of whichever branch ran first."""
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


# --- the ApplyGuardrail reader (ADR-035, change B) ---------------------------
#
# The gateway hands platform-supplied content to the guardrail directly, so a
# second response shape has to be read into the same decision. These assert that
# the two readers agree about what a block is — and, first, that adding the
# second one did not move the first.

def test_a_converse_block_still_records_no_channel():
    """**The byte-identity guarantee this whole change rests on.** M04's per-probe
    pins were recorded before the channel existed; if `interpret` started emitting
    a `channel` key, every future record of the same event would differ from the
    committed one and the before/after would be comparing record shapes rather
    than controls. `test_the_record_fragment_carries_a_pinned_version` pins the
    fragment; this pins where the value comes from."""
    outcome = guardrail.interpret({"stopReason": "guardrail_intervened"})
    assert outcome.channel is None
    assert "channel" not in outcome.as_record_fragment("gr-1", "2")


def test_the_action_alone_is_an_intervention():
    outcome = guardrail.interpret_apply(
        {"action": "GUARDRAIL_INTERVENED"}, channel=guardrail.CHANNEL_TOOL_OUTPUT)
    assert outcome.intervened is True
    assert outcome.channel == "tool_output"


def test_an_assessment_alone_is_an_intervention():
    """The mirror of `test_a_trace_block_is_an_intervention_even_on_a_normal_stop`,
    and for the same reason: either signal is sufficient, because under-reporting
    a block is how a probe silently stops passing after a service update."""
    outcome = guardrail.interpret_apply({
        "action": "NONE",
        "assessments": [{"topicPolicy": {"topics": [
            {"name": "entitlement-circumvention", "action": "BLOCKED"}]}}],
    }, channel=guardrail.CHANNEL_SYSTEM)
    assert outcome.intervened is True
    assert outcome.assessed == ("TOPIC:entitlement-circumvention",)


def test_clean_platform_content_is_not_an_intervention():
    outcome = guardrail.interpret_apply({"action": "NONE", "assessments": []},
                                        channel=guardrail.CHANNEL_SYSTEM)
    assert outcome.intervened is False
    assert outcome.assessed == ()


def test_both_readers_name_a_policy_identically():
    """One `_blocked_names`, so a topic block on the user turn and the same topic
    block on tool output are the same string in the lake. Two readers that could
    disagree would split one finding into two that nobody joins up."""
    fired = {"topicPolicy": {"topics": [{"name": "medical-advice", "action": "BLOCKED"}]}}
    via_converse = guardrail.interpret(
        {"stopReason": "guardrail_intervened",
         "trace": {"guardrail": {"inputAssessment": {"gr-1": fired}}}})
    via_apply = guardrail.interpret_apply(
        {"action": "GUARDRAIL_INTERVENED", "assessments": [fired]},
        channel=guardrail.CHANNEL_TOOL_OUTPUT)
    assert via_converse.assessed == via_apply.assessed == ("TOPIC:medical-advice",)


def test_anonymized_is_not_a_block_on_this_channel_either():
    """`BLOCKING_ACTIONS` is shared, and this is the assertion that notices if it
    stops being. Masking a PII entity in a tool result lets the result through."""
    outcome = guardrail.interpret_apply({
        "action": "NONE",
        "assessments": [{"sensitiveInformationPolicy": {"piiEntities": [
            {"type": "EMAIL", "action": "ANONYMIZED"}]}}],
    }, channel=guardrail.CHANNEL_TOOL_OUTPUT)
    assert outcome.intervened is False


def test_an_unnamed_channel_is_refused():
    """A channel name is read by a person deciding which seat owns a block. A
    free-form one is how `tool-output` and `tool_output` become two findings."""
    with pytest.raises(ValueError, match="unknown channel"):
        guardrail.interpret_apply({"action": "NONE"}, channel="whatever")


def test_a_channel_block_records_which_channel_and_still_validates():
    """The channel travels in the audit record, not only in a log. A finding that
    lives in CloudWatch expires with the retention policy; the run artifact is
    built from records fetched back out of the lake, so anything not in the record
    is not in the evidence."""
    outcome = guardrail.interpret_apply(
        {"action": "GUARDRAIL_INTERVENED",
         "assessments": [{"contentPolicy": {"filters": [
             {"type": "PROMPT_ATTACK", "action": "BLOCKED"}]}}]},
        channel=guardrail.CHANNEL_SYSTEM)
    fragment = outcome.as_record_fragment("gr-1", "2")
    assert fragment["channel"] == "system"

    record = a_record(decision="blocked", mechanism="guardrail", guardrail=fragment)
    jsonschema.validate(record, AUDIT_SCHEMA)



# --- the action guard, one policy type at a time -----------------------------
#
# **The AI Quality seat neutralised each `action in BLOCKING_ACTIONS` guard in
# `_blocked_names` in turn and the suite stayed green for five of the six** —
# including the topic guard, the one deciding the control ADR-035 is about to
# change. Measured end to end on a trace where the entitlement topic was
# evaluated and explicitly did NOT block:
#
#     as committed        : intervened=False -> allowed  -> guardrail_blocked=False
#     topic guard removed : intervened=True  -> blocked  -> guardrail_blocked=True
#
# A one-word edit flips probes to PASS because the guardrail LOOKED rather than
# because it blocked — precisely what G4 forbids — with all six instrument
# digests unchanged and `m04-A` still resolving. `interpret_apply` now shares
# `_blocked_names`, so one edit there moves the user-turn and the tool-output
# verdicts at once, across the comparison ADR-035 rests on. Sharing the reader is
# still right; leaving the class untested was not.
#
# One test per policy type, both readers, asserting the same thing: a policy that
# was consulted and did not block contributes no name and no intervention.

EVALUATED_BUT_NOT_BLOCKED = {
    "contentPolicy": {"filters": [{"type": "PROMPT_ATTACK", "action": "NONE"}]},
    "topicPolicy": {"topics": [{"name": "entitlement-circumvention", "action": "NONE"}]},
    "sensitiveInformationPolicy": {
        "piiEntities": [{"type": "EMAIL", "action": "NONE"}],
        "regexes": [{"name": "account-number", "action": "NONE"}],
    },
    "wordPolicy": {
        "customWords": [{"match": "bypass", "action": "NONE"}],
        "managedWordLists": [{"type": "PROFANITY", "action": "NONE"}],
    },
}


@pytest.mark.parametrize("policy", sorted(EVALUATED_BUT_NOT_BLOCKED))
def test_a_policy_that_did_not_block_contributes_no_name_on_the_converse_path(policy):
    """`action: "NONE"` means the policy was consulted and let the content through.
    Counting it would credit the guardrail with stopping a request it served, and
    would do it in the field a probe's pass is derived from."""
    outcome = guardrail.interpret({
        "stopReason": "end_turn",
        "trace": {"guardrail": {"inputAssessment": {
            "gr-1": {policy: EVALUATED_BUT_NOT_BLOCKED[policy]}}}},
    })
    assert outcome.assessed == ()
    assert outcome.intervened is False


@pytest.mark.parametrize("policy", sorted(EVALUATED_BUT_NOT_BLOCKED))
def test_a_policy_that_did_not_block_contributes_no_name_on_the_apply_path(policy):
    """The same guard, reached through the other reader. Both call
    `_blocked_names`, so this is the assertion that makes sharing it safe."""
    outcome = guardrail.interpret_apply(
        {"action": "NONE", "assessments": [{policy: EVALUATED_BUT_NOT_BLOCKED[policy]}]},
        channel=guardrail.CHANNEL_SYSTEM)
    assert outcome.assessed == ()
    assert outcome.intervened is False


def test_the_topic_guard_specifically_cannot_be_removed_unnoticed():
    """Called out on its own because it is the one the seat proved was live, and
    the one ADR-035's Change A is about to reword. A probe scoring PASS off a
    topic that was evaluated and allowed is a G4 violation that moves no digest."""
    trace = {"guardrail": {"inputAssessment": {"gr-1": {
        "topicPolicy": {"topics": [
            {"name": "entitlement-circumvention", "action": "NONE"},
            {"name": "medical-advice", "action": "BLOCKED"},
        ]}}}}}
    outcome = guardrail.interpret({"stopReason": "end_turn", "trace": trace})
    assert outcome.assessed == ("TOPIC:medical-advice",), (
        "an evaluated-but-allowed topic is being counted as a block")


def test_a_mixed_assessment_names_only_what_blocked():
    """The realistic shape: several policies consulted, one fires. Everything that
    did not fire has to stay out of `assessed`, because `assessed` is what tells
    the Security seat where the corpus is under-covering."""
    outcome = guardrail.interpret_apply({
        "action": "GUARDRAIL_INTERVENED",
        "assessments": [{
            "contentPolicy": {"filters": [
                {"type": "PROMPT_ATTACK", "action": "BLOCKED"},
                {"type": "INSULTS", "action": "NONE"},
            ]},
            "topicPolicy": {"topics": [
                {"name": "entitlement-circumvention", "action": "NONE"}]},
        }],
    }, channel=guardrail.CHANNEL_TOOL_OUTPUT)
    assert outcome.assessed == ("PROMPT_ATTACK",)


# --- the keys the gateway returns on a block (ADR-039) --------------------------
#
# These ran in CI never. `handler.py` assembled them inline, and no test can
# import that module: it pulls in boto3 and `tests/` is in `HERMETIC_ROOTS`, so
# `test_handler_wiring.py` parses the handler's source instead of executing it.
# Measured before the move — rename a field on the frozen dataclass, update every
# test a diligent implementer would update, and the suite stayed green at 1526
# while the guardrail-block path raised `AttributeError`. The path G4 exists to
# evidence, crashing under a green gate.

def test_the_block_response_carries_the_names_that_blocked_it():
    outcome = guardrail.GuardrailOutcome(True, ("TOPIC:enforcement-probing", "PROMPT_ATTACK"))
    assert outcome.as_response_fields() == {
        "assessed": ["TOPIC:enforcement-probing", "PROMPT_ATTACK"]}


def test_the_block_response_names_the_channel_only_when_there_is_one():
    """Same when-set rule as the record fragment, for the same reason: a caller
    parsing the response must not have to tell `channel: null` apart from a turn
    where the question is not meaningful."""
    plain = guardrail.GuardrailOutcome(True, ("PROMPT_ATTACK",))
    assert "channel" not in plain.as_response_fields()

    on_tool_output = guardrail.interpret_apply(
        {"action": guardrail.APPLY_ACTION_INTERVENED,
         "assessments": [{"topicPolicy": {"topics": [
             {"name": "entitlement-circumvention", "action": "BLOCKED"}]}}]},
        channel=guardrail.CHANNEL_TOOL_OUTPUT,
    )
    fields = on_tool_output.as_response_fields()
    assert fields["channel"] == guardrail.CHANNEL_TOOL_OUTPUT
    assert fields["assessed"] == ["TOPIC:entitlement-circumvention"]


def test_the_response_fields_are_a_plain_json_shape():
    """`assessed` is a tuple on the dataclass and must reach the caller as a list.
    A tuple survives an equality assertion in a test and does not survive
    `json.dumps` in the Lambda's response, which is the difference between a
    passing test and a 500 on the refusal path."""
    fields = guardrail.GuardrailOutcome(True, ("PROMPT_ATTACK",)).as_response_fields()
    assert isinstance(fields["assessed"], list)
    assert json.loads(json.dumps(fields)) == fields


def test_the_handler_reads_these_fields_from_the_dataclass_and_not_by_hand():
    """The reason the move is the fix rather than a tidy-up.

    An executing test on `as_response_fields` protects nothing if `handler.py`
    goes back to assembling the dict inline — the rename would break the handler
    again and this file would stay green again. So the source is asserted too,
    the way `test_handler_wiring.py` asserts the rest of this module. Two checks,
    because neither alone can see what the other sees."""
    source = (pathlib.Path(__file__).resolve().parents[1]
              / "platform" / "gateway" / "handler.py").read_text(encoding="utf-8")
    assert "as_response_fields()" in source, (
        "handler.py no longer calls as_response_fields — if the block response is "
        "being assembled by hand again, the executing tests above cover nothing")
    assert "outcome.guardrail.channel" not in source, (
        "handler.py reads `outcome.guardrail.channel` directly again. That attribute "
        "access is unexecuted by any test (boto3 keeps this module out of the hermetic "
        "surface), and a rename of the field crashes the guardrail-block path silently")

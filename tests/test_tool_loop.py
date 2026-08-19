"""
The agent loop: what happens, in what order, and what a turn costs.

This is the file that decides whether G3 means anything at run time. The plane
answers "may this call happen"; the loop decides whether the plane is asked
*before* the tool runs, whether a denial stops the call or merely annotates it,
and whether a turn that goes wrong stops. All three are testable without an AWS
account, which is why the loop is in `core/` — see `core/toolloop.py`.

The doubles are deliberately dumb. `converse` returns a scripted list of
responses and records the transcript it was handed; `call_tool` records what it
was asked for. A test that mocks the plane would be testing the loop against a
guess about the plane, and this milestone has already paid once for a measurement
that described a component that no longer existed.

Hermetic. Owning seat: Platform Engineering, with Security on the ordering.
"""
import json
import pathlib

import jsonschema
import pytest
import yaml
from core import audit, toolloop, toolplane
from core import cedar as cedar_module

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = yaml.safe_load((ROOT / "platform" / "registry" / "tools.yaml").read_text(encoding="utf-8"))
POLICIES = cedar_module.parse(
    (ROOT / "platform" / "gateway" / "policy" / "tools.cedar").read_text(encoding="utf-8"))
CONTRACTS = json.loads(
    (ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json").read_text(encoding="utf-8"))
AUDIT_SCHEMA = json.loads(
    (ROOT / "platform" / "gateway" / "audit.schema.json").read_text(encoding="utf-8"))

PRINCIPAL = "highlights-agent"
TOOL = "catalog-search"
USAGE = {"inputTokens": 900, "outputTokens": 60}
RESULT = {"results": [{"id": "t001", "title": "Jefferson Derby", "brand": "meridian-sports",
                       "type": "live-event", "entitlement": "sports-tier",
                       "event": "jefferson-derby", "starts": "2026-09-13T19:00:00Z"}]}


def plane(**overrides):
    return toolplane.ToolPlane(policies=POLICIES, contracts=CONTRACTS, **overrides)


def tool_use(name=TOOL, args=None, use_id="tu-1"):
    return {"stopReason": "tool_use", "usage": dict(USAGE), "output": {"message": {
        "role": "assistant",
        "content": [{"toolUse": {"toolUseId": use_id, "name": name,
                                 "input": args if args is not None else {"query": "derby"}}}],
    }}}


def final(text="done"):
    return {"stopReason": "end_turn", "usage": dict(USAGE),
            "output": {"message": {"role": "assistant", "content": [{"text": text}]}}}


def blocked():
    return {"stopReason": "guardrail_intervened", "usage": dict(USAGE),
            "output": {"message": {"role": "assistant", "content": [{"text": "withheld"}]}},
            "trace": {"guardrail": {"inputAssessment": {"gr-1": {
                "contentPolicy": {"filters": [
                    {"type": "PROMPT_ATTACK", "action": "BLOCKED"}]}}}}}}


class Converse:
    """A scripted model. Keeps every transcript it was handed, because the
    transcript is where the loop's contract with Bedrock actually lives."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.transcripts = []

    def __call__(self, transcript):
        self.transcripts.append([dict(m) for m in transcript])
        if not self.responses:
            raise AssertionError("the loop asked for more rounds than the script has")
        return self.responses.pop(0), 120


class Tool:
    def __init__(self, reply=None):
        self.reply = reply if reply is not None else toolloop.ToolReply(payload=RESULT)
        self.asked = []

    def __call__(self, tool_id, args):
        self.asked.append((tool_id, args))
        return self.reply


def run(converse, call_tool, **kwargs):
    return toolloop.run_turn(
        plane=kwargs.pop("plane", None) or plane(),
        principal=kwargs.pop("principal", PRINCIPAL),
        messages=[{"role": "user", "content": [{"text": "what is on tonight"}]}],
        converse=converse, call_tool=call_tool, **kwargs)


# --- the happy path, and the shape it leaves behind ---------------------------

def test_an_allowed_call_reaches_the_tool_and_its_result_reaches_the_model():
    converse, tool = Converse(tool_use(), final("t001")), Tool()
    outcome = run(converse, tool)

    assert outcome.status == toolloop.ANSWERED
    assert outcome.answer == "t001"
    assert tool.asked == [(TOOL, {"query": "derby"})]

    # The second transcript is what the model saw after the tool ran: its own
    # assistant turn, then the result.
    second = converse.transcripts[1]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    result_block = second[-1]["content"][0]["toolResult"]
    assert result_block["status"] == "success"
    assert result_block["toolUseId"] == "tu-1"
    assert result_block["content"][0]["json"] == RESULT


def test_a_turn_that_needs_no_tool_never_asks_the_plane():
    converse, tool = Converse(final("no tools needed")), Tool()
    outcome = run(converse, tool)
    assert outcome.status == toolloop.ANSWERED
    assert outcome.calls == ()
    assert tool.asked == []


def test_the_turn_sums_what_every_round_spent():
    """A multi-round turn spends on every round. Reporting only the last one would
    understate a runaway turn by exactly the amount that makes it worth
    catching — the case the loop bound exists for would be the case the meter lied
    about."""
    converse, tool = Converse(tool_use(), tool_use(use_id="tu-2"), final()), Tool()
    outcome = run(converse, tool)
    assert outcome.usage["tokens_in"] == USAGE["inputTokens"] * 3
    assert outcome.usage["tokens_out"] == USAGE["outputTokens"] * 3
    assert outcome.usage["latency_ms"] == 360


def test_the_tool_round_trip_is_measured_separately_from_the_model():
    """`latency_ms` came only from the `converse` timer, so a tools-arm turn
    reported model time while the real turn included n tool invocations — the
    budget axis under-reporting exactly the component the tool plane adds.

    **Kept as its own field rather than folded into `latency_ms`.** The `max_ms`
    ceiling was re-derived in PR #17 from a measurement whose harness called the
    tool in-process; the deployed tool is a Lambda invoke, so folding its network
    time into `latency_ms` would compare a number against a ceiling derived
    without it. Reported beside it, and SPEC/02 names the gap."""
    ticks = iter([0.0, 0.5, 10.0, 10.25])
    converse, tool = Converse(tool_use(), tool_use(use_id="tu-2"), final()), Tool()
    outcome = toolloop.run_turn(
        plane=plane(), principal=PRINCIPAL,
        messages=[{"role": "user", "content": [{"text": "x"}]}],
        converse=converse, call_tool=tool, clock=lambda: next(ticks))

    assert outcome.usage["tool_ms"] == 500 + 250
    assert outcome.usage["latency_ms"] == 360, "model time must stay comparable to the ceiling"


def test_a_turn_with_no_tools_reports_no_tool_time():
    """So the control arm's usage shape is unchanged: `tool_ms` is absent, not
    zero, on a turn that called nothing."""
    outcome = run(Converse(final()), Tool())
    assert "tool_ms" not in outcome.usage


# --- authorize BEFORE the tool runs ------------------------------------------

def test_an_unregistered_tool_is_denied_and_never_reaches_a_tool():
    """G3, in the one place it is a run-time property rather than a policy file.

    The assertion that matters is `tool.asked == []`: a plane consulted *after*
    the call is an audit trail, not a control."""
    converse, tool = Converse(tool_use(name="catalog-purge"), final()), Tool()
    outcome = run(converse, tool)

    assert tool.asked == [], "the tool ran before the plane authorized it"
    assert [c.decision.mechanism for c in outcome.calls] == [toolplane.POLICY]
    assert not outcome.calls[0].decision.allowed


def test_an_uninvited_caller_is_denied():
    """The registry names which services may call which tool. `recap-agent` may
    call catalog-search and `ledger-service` is in no `callers` list at all."""
    converse, tool = Converse(tool_use(), final()), Tool()
    outcome = run(converse, tool, principal="ledger-service")
    assert tool.asked == []
    assert outcome.calls[0].decision.mechanism == toolplane.POLICY


def test_a_publish_class_tool_is_denied_while_no_approval_interlock_is_deployed():
    """`publish-highlight` is registered, permitted for highlights-agent, and
    unreachable — the forbid is only lifted by a context nothing at M02 grants.
    A tool whose declared approver is not deployed must be unreachable, not
    reachable without one."""
    converse, tool = Converse(
        tool_use(name="publish-highlight", args={"title_id": "t001", "clip_url": "https://x/y"}),
        final()), Tool()
    outcome = run(converse, tool)
    assert tool.asked == []
    assert outcome.calls[0].decision.mechanism == toolplane.POLICY
    assert "approval_granted not granted" in " ".join(outcome.calls[0].decision.reasons)


def test_arguments_are_validated_before_the_tool_runs():
    converse, tool = Converse(tool_use(args={"limit": 3}), final()), Tool()
    outcome = run(converse, tool)
    assert tool.asked == []
    assert outcome.calls[0].decision.mechanism == toolplane.SCHEMA


def test_a_denied_call_does_not_end_the_turn():
    """The model is told the platform refused and answers anyway. Ending the turn
    would make every denial look like an outage, and it would hide what a model
    does when a tool it wanted is denied — which is a finding, recorded as a
    trajectory."""
    converse, tool = Converse(tool_use(name="catalog-purge"), final("answered without it")), Tool()
    outcome = run(converse, tool)

    assert outcome.status == toolloop.ANSWERED
    assert outcome.answer == "answered without it"
    told = converse.transcripts[1][-1]["content"][0]["toolResult"]
    assert told["status"] == "error"
    assert "refused by the platform (policy)" in told["content"][0]["text"]


def test_the_refusal_the_model_is_told_carries_a_reason():
    """A model told only "error" retries the identical call and burns the turn's
    bound — which turns one refused call into a loop denial and misattributes the
    cause to the model flailing."""
    converse, tool = Converse(tool_use(name="catalog-purge"), final()), Tool()
    run(converse, tool)
    text = converse.transcripts[1][-1]["content"][0]["toolResult"]["content"][0]["text"]
    assert "unregistered or uninvited caller" in text
    assert text != "refused by the platform (policy): no reason recorded"


# --- the result is checked too ------------------------------------------------

def test_a_result_that_breaks_the_output_contract_is_withheld_from_the_model():
    """The contract check catches a tool that has started returning a shape nobody
    agreed to, including fields the schema does not allow — which is the mechanism
    by which catalog data the model must never see would reach it.

    **And the refusal must not hand it over either.** The first version of this
    told the model the plane's own reasons, which quote the offending output: the
    unexpected-property error names `blackout_dmas`, and an enum violation would
    name the value. The result channel withheld it and the error channel gave it
    back. The reasons still go to the audit record in full; the model gets the
    fact and not the content."""
    bad = {"results": [{"id": "t001", "blackout_dmas": ["jefferson-city"]}]}
    converse, tool = Converse(tool_use(), final()), Tool(toolloop.ToolReply(payload=bad))
    outcome = run(converse, tool)

    assert tool.asked, "the tool should have run: this is an output check, not an input one"
    assert outcome.calls[0].decision.mechanism == toolplane.SCHEMA

    told = converse.transcripts[1][-1]["content"][0]["toolResult"]
    assert told["status"] == "error"
    assert "blackout" not in json.dumps(told), "the withheld result came back through the error"
    assert "jefferson-city" not in json.dumps(told)
    assert "withheld" in told["content"][0]["text"]

    # The audit record keeps what the model was not told.
    assert "blackout_dmas" in " ".join(outcome.calls[0].decision.reasons)


def test_a_rejected_value_does_not_reach_the_model_through_the_refusal():
    """The other half of the same channel. An enum violation quotes the value, so a
    tool returning a field the contract forbids and a tool returning a forbidden
    *value* leak through the same door."""
    bad = {"results": [{"id": "t001", "title": "x", "brand": "meridian-sports",
                        "type": "live-event", "entitlement": "internal-only-tier"}]}
    converse, tool = Converse(tool_use(), final()), Tool(toolloop.ToolReply(payload=bad))
    outcome = run(converse, tool)

    told = converse.transcripts[1][-1]["content"][0]["toolResult"]
    assert "internal-only-tier" not in json.dumps(told)
    assert "internal-only-tier" in " ".join(outcome.calls[0].decision.reasons)


def test_a_refusal_before_the_call_still_tells_the_model_why():
    """The distinction this rests on. A refusal that happened *before* the tool ran
    quotes the model's own request back to it and discloses nothing it did not just
    send — and telling it is what stops it retrying the identical call until the
    loop bound fires and takes the blame."""
    converse, tool = Converse(tool_use(args={"limit": 3}), final()), Tool()
    run(converse, tool)
    text = converse.transcripts[1][-1]["content"][0]["toolResult"]["content"][0]["text"]
    assert "missing required property" in text
    assert "withheld" not in text


def test_a_tool_the_platform_cannot_reach_is_routing_and_not_a_contract_failure():
    """"The tool answered badly" and "the platform could not get to the tool" are
    different findings, and only one of them is about a schema.

    A missing `lambda:InvokeFunction` grant is the failure a deploy is most likely
    to produce, and it arrives through the same channel as a malformed result.
    Recording it as `schema` would send whoever reads the lake to inspect an output
    contract that is fine."""
    converse = Converse(tool_use(), final())
    tool = Tool(toolloop.ToolReply(
        error="AccessDeniedException: not authorized to perform lambda:InvokeFunction",
        unreachable=True))
    outcome = run(converse, tool)

    assert outcome.calls[0].decision.mechanism == toolplane.ROUTING
    assert "could not reach catalog-search" in " ".join(outcome.calls[0].decision.reasons)
    assert "AccessDeniedException" in " ".join(outcome.calls[0].decision.reasons)
    assert toolplane.ROUTING not in audit.POLICY_MECHANISMS


def test_an_unreachable_tool_still_lets_the_turn_finish():
    """A deployment gap must not take the whole turn down. The model is told, and
    what it does next is a trajectory rather than an outage."""
    converse = Converse(tool_use(), final("answered without the tool"))
    outcome = run(converse, Tool(toolloop.ToolReply(error="boom", unreachable=True)))
    assert outcome.status == toolloop.ANSWERED
    assert outcome.answer == "answered without the tool"


def test_a_tool_that_errored_is_a_contract_failure_and_not_a_new_mechanism():
    """A tool that failed produced no result, so it fails its output contract.
    Inventing a mechanism for "the tool broke" would have meant one more name to
    keep out of `POLICY_MECHANISMS` forever, for a case the contract already
    describes."""
    converse = Converse(tool_use(), final())
    tool = Tool(toolloop.ToolReply(error="catalog-search failed: no such file"))
    outcome = run(converse, tool)

    assert outcome.calls[0].decision.mechanism == toolplane.SCHEMA
    assert "no such file" in " ".join(outcome.calls[0].decision.reasons)
    assert outcome.calls[0].decision.mechanism not in audit.POLICY_MECHANISMS


# --- the turn is bounded ------------------------------------------------------

def test_a_turn_that_never_stops_asking_is_stopped():
    """An unbounded agent loop is a cost incident waiting to happen, and the bound
    is the plane's rather than the caller's."""
    converse = Converse(*[tool_use(use_id=f"tu-{n}") for n in range(20)])
    outcome = run(converse, Tool(), plane=plane(max_rounds=3))

    assert outcome.status == toolloop.LOOP_BOUND
    assert "exceeded 3 tool rounds" in " ".join(outcome.reasons)
    assert len(converse.transcripts) == 4, "the bound fired late by a round"


def test_the_call_bound_holds_when_a_single_round_asks_for_many_tools():
    """Rounds alone do not bound the work a turn can ask for: one round may carry
    several `toolUse` blocks, so a caller could stay inside `max_rounds` forever
    and still spend without limit."""
    many = {"stopReason": "tool_use", "usage": dict(USAGE), "output": {"message": {
        "role": "assistant",
        "content": [{"toolUse": {"toolUseId": f"tu-{n}", "name": TOOL,
                                 "input": {"query": "derby"}}} for n in range(6)]}}}
    converse, tool = Converse(many, final()), Tool()
    outcome = run(converse, tool, plane=plane(max_calls=4))

    mechanisms = [c.decision.mechanism for c in outcome.calls]
    assert mechanisms == ["none", "none", "none", "none", toolplane.LOOP, toolplane.LOOP]
    assert len(tool.asked) == 4, "a call past the bound still reached the tool"


# --- the guardrail is on every round -----------------------------------------

def test_a_guardrail_block_mid_loop_ends_the_turn_and_keeps_the_calls_it_made():
    """The guardrail assesses the model's own intermediate reasoning on every
    round, so a longer turn hands it more to assess. That is measured rather than
    hypothetical, and the records for the calls that already happened must
    survive the block — they are the evidence that they were authorized."""
    converse, tool = Converse(tool_use(), blocked()), Tool()
    outcome = run(converse, tool)

    assert outcome.status == toolloop.BLOCKED
    assert outcome.guardrail.assessed == ("PROMPT_ATTACK",)
    assert len(outcome.calls) == 1 and outcome.calls[0].decision.allowed
    assert outcome.usage["tokens_in"] == USAGE["inputTokens"] * 2


def test_a_blocked_turn_still_reports_what_it_spent():
    converse, tool = Converse(tool_use(), tool_use(use_id="tu-2"), blocked()), Tool()
    outcome = run(converse, tool)
    assert outcome.usage["tokens_in"] == USAGE["inputTokens"] * 3


# --- a turn that dies keeps the evidence it already made ----------------------

def test_a_converse_that_raises_mid_loop_keeps_the_calls_it_already_made():
    """G4's second half is that a record exists.

    `run_turn` reaches the model once per round, and only the first of those was
    ever inside the handler's `try`. A throttle on round two propagated past the
    only code that writes tool-call records, so a call that was authorized and
    executed left nothing in the lake. At M01 the exposure did not exist, because
    a turn was one call; a 25-case k=3 run across two arms is roughly 450 model
    calls in one sitting, and a throttle is an ordinary event."""
    class Flaky(Converse):
        def __call__(self, transcript):
            if self.transcripts:
                self.transcripts.append(transcript)
                raise RuntimeError("ThrottlingException: rate exceeded")
            return super().__call__(transcript)

    converse, tool = Flaky(tool_use()), Tool()
    with pytest.raises(toolloop.TurnFailed) as raised:
        run(converse, tool)

    failure = raised.value
    assert len(failure.calls) == 1, "the authorized call was lost with the exception"
    assert failure.calls[0].decision.allowed
    assert failure.usage["tokens_in"] == USAGE["inputTokens"]
    assert isinstance(failure.cause, RuntimeError)


def test_a_first_round_failure_still_carries_an_empty_turn_rather_than_raising_raw():
    """The handler distinguishes an AccessDenied from everything else by reading
    `TurnFailed.cause`, so the wrapper has to be there even when there is nothing
    to carry."""
    class Dead(Converse):
        def __call__(self, transcript):
            raise RuntimeError("boom")

    with pytest.raises(toolloop.TurnFailed) as raised:
        run(Dead(), Tool())
    assert raised.value.calls == ()


def test_a_guardrail_block_without_usage_records_the_block_rather_than_raising():
    """`usage_from_response` raises when a response reports no usage, and it was
    running BEFORE the guardrail was read — so an intervention that came back
    without usage would have raised instead of recording a block, on the one path
    where recording it is the whole of G4.

    The meter's rule ("a call that reached the model but reported no usage is a
    metering failure") was written for the allowed path and still holds there."""
    response = blocked()
    del response["usage"]
    outcome = run(Converse(response), Tool())

    assert outcome.status == toolloop.BLOCKED
    assert outcome.guardrail.assessed == ("PROMPT_ATTACK",)
    assert outcome.usage["tokens_in"] == 0
    assert outcome.usage["latency_ms"] == 120


def test_an_allowed_turn_without_usage_is_still_a_metering_failure():
    """The counterweight. Relaxing the meter on the blocked path must not relax it
    where the budget axis reads it."""
    response = final()
    del response["usage"]
    with pytest.raises(toolloop.TurnFailed) as raised:
        run(Converse(response), Tool())
    assert isinstance(raised.value.cause, ValueError)
    assert "must report what it spent" in str(raised.value.cause)


# --- the records a turn produces ---------------------------------------------

def test_every_call_gets_a_record_and_no_two_share_a_key():
    """A round carries n calls and a turn carries n rounds, so a turn writes
    several records under one `request_id`. Without the ordinal they share a lake
    key, and a versioned bucket makes the collision silent."""
    converse, tool = Converse(tool_use(), tool_use(use_id="tu-2"), final()), Tool()
    outcome = run(converse, tool)

    keys = []
    for call in outcome.calls:
        record = audit.build_record(
            request_id="case-1", ts="2026-08-18T00:00:00Z", principal="role/highlights-agent",
            service="highlights-agent", classification="internal",
            decision="allowed" if call.decision.allowed else "denied",
            mechanism="none" if call.decision.allowed else call.decision.mechanism,
            model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            tool=call.decision.as_record_fragment(round_number=call.round_number, args=call.args),
            seq=call.seq,
        )
        jsonschema.validate(record, AUDIT_SCHEMA)
        keys.append(record["record_id"])

    assert len(keys) == len(set(keys)) == 2


def test_the_rounds_a_call_is_recorded_under_are_the_rounds_it_happened_in():
    converse, tool = Converse(tool_use(), tool_use(use_id="tu-2"), final()), Tool()
    outcome = run(converse, tool)
    assert [c.round_number for c in outcome.calls] == [1, 2]
    assert [c.seq for c in outcome.calls] == [1, 2]


# --- the trajectory is recorded and not scored -------------------------------

def test_the_trajectory_records_what_was_asked_and_what_the_platform_said():
    converse = Converse(tool_use(), tool_use(name="catalog-purge", use_id="tu-2"), final())
    outcome = run(converse, Tool())
    trajectory = outcome.trajectory()

    assert [step["decision"] for step in trajectory] == ["allowed", "denied"]
    assert [step["tool"] for step in trajectory] == [TOOL, "catalog-purge"]
    assert trajectory[0]["args"] == {"query": "derby"}
    assert all("score" not in step and "expected" not in step for step in trajectory), (
        "a trajectory is recorded, never scored (SPEC/02). Rewarding a shape of tool use "
        "measures whether the model did what we guessed, not whether the answer is right."
    )


# --- shapes that would otherwise raise out of the loop ------------------------

def test_a_tool_use_turn_with_no_tool_use_block_ends_the_turn():
    """`stopReason: tool_use` with nothing to run. Continuing would send the model
    a transcript ending in an assistant turn it cannot act on, and the loop would
    spin until the bound."""
    empty = {"stopReason": "tool_use", "usage": dict(USAGE),
             "output": {"message": {"role": "assistant", "content": [{"text": "hm"}]}}}
    outcome = run(Converse(empty), Tool())
    assert outcome.status == toolloop.ANSWERED
    assert outcome.calls == ()


def test_a_turn_ending_without_a_text_block_reports_no_answer_rather_than_raising():
    """A real Bedrock response can end with no text. Indexing into `content[0]`
    would report a harness failure for a model behaviour."""
    outcome = run(Converse({"stopReason": "end_turn", "usage": dict(USAGE),
                            "output": {"message": {"role": "assistant", "content": []}}}), Tool())
    assert outcome.answer == ""


def test_a_tool_use_block_with_no_arguments_is_validated_rather_than_crashing():
    outcome = run(Converse(tool_use(args=None), final()), Tool())
    assert outcome.calls[0].decision.allowed

    outcome = run(Converse(
        {"stopReason": "tool_use", "usage": dict(USAGE), "output": {"message": {
            "role": "assistant",
            "content": [{"toolUse": {"toolUseId": "tu-1", "name": TOOL, "input": None}}]}}},
        final()), Tool())
    assert outcome.calls[0].decision.mechanism == toolplane.SCHEMA


def test_the_messages_the_caller_passed_are_not_mutated():
    """The loop builds its own transcript. A caller reusing its message list — the
    obvious way to run the golden set — would otherwise accumulate every previous
    case's tool traffic, and the run would drift case by case with nothing
    printing differently."""
    messages = [{"role": "user", "content": [{"text": "what is on tonight"}]}]
    toolloop.run_turn(plane=plane(), principal=PRINCIPAL, messages=messages,
                      converse=Converse(tool_use(), final()), call_tool=Tool())
    assert messages == [{"role": "user", "content": [{"text": "what is on tonight"}]}]


@pytest.mark.parametrize("mechanism", [toolplane.SCHEMA, toolplane.LOOP, toolplane.ROUTING])
def test_no_loop_mechanism_can_satisfy_a_probe_naming_cedar(mechanism):
    """The loop can refuse in three ways that are not authorization decisions, and
    none of them may count as one. `loop` in particular fires when the *model*
    flails — counting it would make a probe satisfiable by the attack being
    incompetent."""
    # `CEDAR_MECHANISMS` is the set `score_probe` actually reads for that
    # semantics. Asserting `POLICY_MECHANISMS` held transitively and named the
    # wrong guard — a test whose subject is "cannot satisfy a probe naming Cedar"
    # should assert against the set the scorer consults, not one next to it.
    from evals.adversarial import CEDAR_MECHANISMS
    assert mechanism not in CEDAR_MECHANISMS
    assert mechanism not in audit.POLICY_MECHANISMS
    assert mechanism in audit.MECHANISMS

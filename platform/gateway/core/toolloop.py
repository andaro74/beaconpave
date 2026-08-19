"""
The agent loop, with the tool plane in front of every call.

    converse -> [guardrail?] -> [tool_use?] -> authorize -> call -> validate -> converse

**Pure, and that is the whole reason this module exists.** The loop is where G3
either holds or does not: it is the code that decides whether a tool call is
authorized before it happens, how many of them a turn may make, and what the
model is told when one is refused. Leaving it in `handler.py` beside the boto3
clients would have made every one of those decisions provable only against a
deployed stack — the opposite of what `core/` is for, and exactly the argument
`test_hermeticity.py` already makes about the rest of it.

So the SDK arrives as two callables. `converse` sends a transcript and returns a
response; `call_tool` invokes a tool and returns what it said. The handler owns
both; this module owns the order they happen in.

**The loop does not write audit records, it returns what happened.** One record
per tool call plus one for the turn, and the handler writes them all before it
answers the caller — the M01 rule, unchanged. Returning the decisions rather than
writing them from here keeps the clock, the bucket and the record shape on the
other side of the pure boundary, and it means a test can assert the *sequence* of
decisions without a lake to read them back from.

**A refused tool call does not end the turn.** The model is told the platform
refused, through the toolResult channel the protocol provides, and answers anyway.
Ending the turn would make every denial look like an outage to the viewer, and it
would hide the more interesting behaviour: what a model does when a tool it wanted
is denied is a finding, and one M02 records as a trajectory.

Pure — no SDK, no filesystem, no clock. Owning seat: Platform Engineering (the
loop) · Security (it is an authorization path) · Tool Owner (what a tool is told,
and told back).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core import guardrail as guardrail_module
from core import meter
from core.toolplane import SCHEMA, ToolDecision

#: Bedrock's stop reason when the model wants one or more tools.
STOP_REASON_TOOL_USE = "tool_use"

#: What `run_turn` stopped for. Three terminal states, kept distinct for the same
#: reason the refusal mechanisms are: "the turn ended" and "the turn was stopped"
#: are different findings, and a reader of the lake should not have to infer which.
ANSWERED = "answered"
BLOCKED = "blocked"
LOOP_BOUND = "loop"


@dataclass(frozen=True)
class ToolReply:
    """What a tool said, as the handler's transport understood it.

    `error` is the tool's own failure — a malformed catalog, an MCP error
    response, a transport fault. It is **not** a plane decision, and the loop does
    not dress it as one: a tool that errored produced no result, so it fails its
    committed output contract and is refused with `schema`. That path is written
    down here rather than special-cased, because the alternative was inventing a
    mechanism for "the tool broke" and then having to keep it out of
    `audit.POLICY_MECHANISMS` forever."""

    payload: object | None = None
    error: str | None = None


@dataclass(frozen=True)
class ToolCall:
    """One authorized-or-refused tool call, with everything the audit record needs.

    `seq` is the call's ordinal within the turn, and it exists because a turn now
    writes several records that share a `request_id`. Without it they would share
    a lake key too, and the last one written would be the only one anybody found."""

    decision: ToolDecision
    round_number: int
    seq: int
    args: dict
    tool_use_id: str | None = None
    payload: object | None = None


@dataclass(frozen=True)
class TurnOutcome:
    status: str
    response: dict | None
    calls: tuple[ToolCall, ...] = ()
    usage: dict = field(default_factory=dict)
    guardrail: guardrail_module.GuardrailOutcome | None = None
    reasons: tuple[str, ...] = ()
    transcript: tuple[dict, ...] = ()

    @property
    def answer(self) -> str:
        """The model's text, or the empty string.

        Defensive over the shape rather than indexing into it: a turn ending with
        a tool result and no text block is a real Bedrock response, and an
        IndexError here would report a harness failure for a model behaviour."""
        message = (self.response or {}).get("output", {}).get("message", {})
        for block in message.get("content", []):
            if "text" in block:
                return block["text"]
        return ""

    def trajectory(self) -> list[dict]:
        """What the turn asked for, in order. **Recorded, never scored** (SPEC/02).

        A tool trajectory is the most tempting thing in this milestone to turn
        into a metric, and it is the wrong one: rewarding a shape of tool use
        measures whether the model does what we guessed, not whether the answer is
        right. It is committed as evidence and kept out of the suites."""
        return [
            {
                "round": call.round_number,
                "seq": call.seq,
                "tool": call.decision.tool_id,
                "args": call.args,
                "decision": "allowed" if call.decision.allowed else "denied",
                "mechanism": call.decision.mechanism,
                "reasons": list(call.decision.reasons),
            }
            for call in self.calls
        ]


def _tool_result_block(tool_use_id, decision: ToolDecision, payload, withheld: bool) -> dict:
    """What the model is handed back for one tool call.

    A refusal is reported with `status: error`. Saying *why* matters: a model told
    only "error" retries the identical call and burns the turn's bound, which turns
    one refused call into a loop denial and misattributes the cause. Telling it the
    platform refused is not leaking policy — the refusal is the platform's, and the
    model is the one that has to stop.

    **How much of the why depends on which side of the tool the refusal happened**,
    and this is a real distinction rather than a stylistic one:

    - Refused *before* the call — no policy permits it, the arguments fail the
      input contract — and the reasons quote the model's own request back to it.
      Nothing is disclosed that the model did not just send.
    - Refused *after* the call, because the result failed the output contract or
      the tool errored, and the reasons quote **the tool's output**: an enum
      violation names the offending value, an unexpected-property error names the
      field. The whole point of the output check is that the result is withheld,
      and a refusal that quotes it hands over through the error channel what the
      check just refused to hand over through the result channel. `blackout_dmas`
      is exactly the field that would arrive that way.

    So a withheld result is reported as withheld. The reasons still go to the
    audit record in full — that is where a refusal has to be reconstructable, and
    the record is read by people rather than by the model."""
    if decision.allowed:
        content = [{"json": payload if isinstance(payload, dict) else {"result": payload}}]
        status = "success"
    elif withheld:
        content = [{"text": (
            f"the platform withheld this tool's result ({decision.mechanism}): it did not "
            "conform to the tool's committed output contract. The result is not available "
            "and calling again the same way will not change that. See the audit record.")}]
        status = "error"
    else:
        detail = "; ".join(decision.reasons) or "no reason recorded"
        content = [{"text": f"refused by the platform ({decision.mechanism}): {detail}"}]
        status = "error"
    return {"toolResult": {"toolUseId": tool_use_id, "content": content, "status": status}}


def _accumulate(totals: dict, usage: dict) -> dict:
    """Sum a turn's spend across its rounds.

    A multi-round turn spends on every round, and reporting only the last one
    would understate a runaway turn by exactly the amount that makes it worth
    catching — the case the loop bound exists for would be the case the meter
    lied about."""
    for key in ("tokens_in", "tokens_out", "latency_ms"):
        totals[key] = totals.get(key, 0) + usage.get(key, 0)
    return totals


def run_turn(*, plane, principal: str, messages: list[dict], converse, call_tool) -> TurnOutcome:
    """Run one agent turn to completion, to a refusal, or to its bound.

    `converse(transcript) -> (response, latency_ms)` and
    `call_tool(tool_id, args) -> ToolReply` are the only things that touch the
    outside; everything else here is a decision.

    **`principal` is passed in and never read off the transcript or the event.**
    It is the Cedar principal, so anything a caller or a model can influence must
    not reach it — see `handler.py`, where it comes from deployment configuration
    rather than from the request."""
    transcript: list[dict] = [dict(message) for message in messages]
    turn = plane.begin_turn()
    calls: list[ToolCall] = []
    totals: dict = {}

    while True:
        response, latency_ms = converse(transcript)
        _accumulate(totals, meter.usage_from_response(response, latency_ms))

        outcome = guardrail_module.interpret(response)
        if outcome.intervened:
            # The guardrail assesses the model's own intermediate reasoning on
            # every round, so a turn that took four rounds handed it four more
            # blocks of text to assess. That is measured rather than hypothetical:
            # narrowing retrieval raised refusals from 2/15 to 5/15 by lengthening
            # turns (milestones/M02/loop-shape.json).
            return TurnOutcome(BLOCKED, response, tuple(calls), totals, outcome,
                               transcript=tuple(transcript))

        if response.get("stopReason") != STOP_REASON_TOOL_USE:
            return TurnOutcome(ANSWERED, response, tuple(calls), totals, outcome,
                               transcript=tuple(transcript))

        bound = turn.begin_round()
        if bound is not None:
            return TurnOutcome(LOOP_BOUND, response, tuple(calls), totals, outcome,
                               reasons=bound.reasons, transcript=tuple(transcript))

        message = response["output"]["message"]
        transcript.append(message)

        results = []
        for block in message.get("content", []):
            use = block.get("toolUse")
            if not use:
                continue
            tool_id = use.get("name")
            args = use.get("input") if isinstance(use.get("input"), dict) else {}

            decision = turn.authorize(principal=principal, tool_id=tool_id, args=args)
            seq = turn.calls
            payload = None
            # Whether the refusal happened after the tool ran. It decides how much
            # of the reason the model is told — see `_tool_result_block`.
            withheld = False

            if decision.allowed:
                reply = call_tool(tool_id, args)
                if reply.error is not None:
                    withheld = True
                    decision = ToolDecision(False, tool_id, SCHEMA, (
                        f"the tool returned no result: {reply.error}",))
                else:
                    checked = plane.validate_result(tool_id=tool_id, result=reply.payload)
                    if checked.allowed:
                        payload = reply.payload
                    else:
                        withheld = True
                        decision = ToolDecision(False, tool_id, checked.mechanism, tuple(
                            f"result rejected: {reason}" for reason in checked.reasons))

            calls.append(ToolCall(decision, turn.rounds, seq, args, use.get("toolUseId"), payload))
            results.append(
                _tool_result_block(use.get("toolUseId"), decision, payload, withheld))

        if not results:
            # `stopReason: tool_use` with no `toolUse` block. Nothing to answer,
            # and continuing would send the model a transcript ending in an
            # assistant turn it cannot act on. Treated as the answer it is.
            return TurnOutcome(ANSWERED, response, tuple(calls), totals, outcome,
                               transcript=tuple(transcript))

        transcript.append({"role": "user", "content": results})

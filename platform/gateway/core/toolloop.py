"""
The agent loop, with the tool plane in front of every call.

    inspect(question) -> converse -> inspect(tool_request | answer) -> [tool_use?]
            -> authorize -> call -> validate -> inspect(tool_output) -> converse

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

**`converse` carries no guardrail. Every piece of content is assessed once, on
entry, by the gateway, on the channel the loop labels it with (ADR-070).** Four
channels, one assessment each: the viewer's turn as `question` before the first
model call; each tool result as `tool_output` before it joins the transcript
(ADR-035); the model's output on a round ending in `tool_use` as `tool_request`
before it joins the transcript; the model's output on the final round as
`answer` before it is returned. The loop is the only party that can tell the
last two apart — Bedrock's own guardrail assessed every round's output under one
policy and labelled all of it `answer`, because it does not know which output the
viewer will be shown. That is why the guardrail moved from the call into the
loop: per-channel policy on the output side is impossible from inside `converse`.

**What that costs, said plainly (ADR-070, "What B costs").** Bedrock used to
guarantee that blocked text never reached the gateway. Now the loop receives
unassessed output and must not return it. The guarantee is a property of this
module: a refused round returns no response at all, the refused text travels
under `TurnOutcome.refused` and nowhere else, and the `ANSWERED` outcome carries
only text an assessment passed. Tests plant a blocking assessment on every
channel and assert the caller-facing shape is text-free. **One serialisation per
channel, all here**: the viewer's turn verbatim, tool results and each
`toolUse.input` through `_inspection_text`, text blocks joined. The handler
serialises nothing, and `tests/test_handler_wiring.py` asserts that on its source.

`inspect` is a **required** argument, with no default, for the same reason
`converse` and `call_tool` are. A default of `None` would make the inspection
opt-in, and every caller that forgot it would run exactly as it ran before the
control existed, green and silent. A caller that genuinely wants no inspection
passes something that says so, in a line a reviewer can see.

**A refused tool call does not end the turn.** The model is told the platform
refused, through the toolResult channel the protocol provides, and answers anyway.
Ending the turn would make every denial look like an outage to the viewer, and it
would hide the more interesting behaviour: what a model does when a tool it wanted
is denied is a finding, and one M02 records as a trajectory.

**A guardrail block on that result does end the turn, and the difference is not a
style choice.** The Service Team seat read the paragraph above against the new
code and found the module saying two opposite things, which it was. The
distinction: a plane refusal means *this call* may not happen, and the turn is
still answerable without it. A guardrail block means content already in hand may
not enter the context, and the alternative — withholding the payload and letting
the turn continue — ends the turn `answered`. Under G4 that scores the probe FAIL,
because a probe passes when the guardrail blocked and a record exists, never
because the model coped. So the hard stop is what makes the control demonstrable
rather than merely present. The cost is real and belongs here rather than in a
journal: one poisoned row in a catalog takes out every question that retrieves
it, including the questions the clean rows would have answered.

Pure — no SDK, no filesystem, no clock. Owning seat: Platform Engineering (the
loop) · Security (it is an authorization path) · Tool Owner (what a tool is told,
and told back).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from core import guardrail as guardrail_module
from core import meter
from core.toolplane import ROUTING, SCHEMA, ToolDecision


def _monotonic():
    import time
    return time.monotonic()

#: Bedrock's stop reason when the model wants one or more tools.
STOP_REASON_TOOL_USE = "tool_use"

#: An explicit declaration that a caller has nothing in context the viewer did
#: not write. Spelled as a name because the alternative spelling is `()`, which is
#: byte-identical to the accident of forgetting the argument — and a control whose
#: deliberate exemption and whose silent misconfiguration look the same in a diff
#: is a control a reviewer cannot check. The same argument the required `inspect`
#: argument makes, one level out. A caller that uses this owes a comment naming
#: who decided.
NOTHING_UNTRUSTED: tuple = ()

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
    response, a fault inside the function. It is **not** a plane decision, and the
    loop does not dress it as one: a tool that errored produced no result, so it
    fails its committed output contract and is refused with `schema`. That path is
    written down here rather than special-cased, because the alternative was
    inventing a mechanism for "the tool broke" and then having to keep it out of
    `audit.POLICY_MECHANISMS` forever.

    **`unreachable` separates "the tool answered badly" from "the platform could
    not get to the tool".** A missing `lambda:InvokeFunction` grant, a function
    that does not exist, a throttle — none of those are the tool's contract
    failing, and recording them as `schema` sends whoever reads the lake to
    inspect an output schema that is fine. That is the misattribution `ROUTING`
    exists to prevent, and the first version of this handed the whole class to
    `schema` because the error arrived through the same channel. The verbatim
    error is carried either way; the mechanism is what gets counted."""

    payload: object | None = None
    error: str | None = None
    unreachable: bool = False


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
    #: Whether the tool function was reached. NOT derivable from `payload`: a call
    #: that ran and had its result rejected carries `payload=None` and `executed=True`,
    #: and reading execution off the payload would report those as never having
    #: happened. See `SPEC/06b` B9.
    executed: bool = False


class TurnFailed(Exception):
    """A turn that could not be completed, carrying what it had already done.

    **The records for the calls that already happened must survive the failure.**
    `run_turn` reaches the model once per round, and only the first of those was
    ever inside the handler's `try`. A throttle on round two propagated out of the
    loop, out of the handler, and past the only code that writes tool-call records
    — so a tool call that was authorized and executed left nothing in the lake. At
    M01 the exposure did not exist, because a turn was one call.

    G4's second half is that a record exists. A run of 25 cases at k=3 across two
    arms is roughly 450 model calls in one sitting, and a throttle is an ordinary
    event; its consequence must not be a silently incomplete audit trail."""

    def __init__(self, cause: BaseException, calls, usage):
        super().__init__(str(cause))
        self.cause = cause
        self.calls = tuple(calls)
        self.usage = dict(usage)


@dataclass(frozen=True)
class TurnOutcome:
    status: str
    response: dict | None
    calls: tuple[ToolCall, ...] = ()
    usage: dict = field(default_factory=dict)
    guardrail: guardrail_module.GuardrailOutcome | None = None
    reasons: tuple[str, ...] = ()
    transcript: tuple[dict, ...] = ()
    #: The text an assessment refused, on whichever channel it was refused
    #: (ADR-070 constraint 1). **This is the only place it travels.** A `BLOCKED`
    #: outcome carries `response=None`, so `answer` is empty and nothing derived
    #: from the response can quote it; the handler fingerprints this attribute
    #: into `withheld` and returns none of it. Where the text goes after that is
    #: ADR-071's (PR 3), and nothing in this module decides it.
    refused: str | None = None

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
                "executed": call.executed,
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
    elif withheld and decision.mechanism == ROUTING:
        # **Not the same sentence as a contract failure.** The first version sent
        # the withheld-result text for this branch too, so a throttle or a missing
        # invoke grant was reported to the model as "it did not conform to the
        # output contract" and told not to retry. The lake got the distinction
        # right and the model was handed the schema story — which is the same
        # misattribution `ROUTING` exists to prevent, arriving on the one channel
        # nobody was asserting about.
        content = [{"text": (
            "the platform could not reach this tool. Nothing was withheld and nothing "
            "about the request was wrong. See the audit record.")}]
        status = "error"
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


def _tool_ms(started, ended) -> int:
    return max(0, int((ended - started) * 1000))


def _inspection_text(payload) -> str:
    """What of a tool result — and of each `toolUse.input` (ADR-070) — the
    guardrail is handed.

    The whole payload, serialised, rather than the string fields picked out of
    it. A field-picking version was the first draft and it is the wrong shape for
    the same reason `ADV-002`'s fixture is a *title*: the injection goes wherever
    the platform is not looking, and a list of fields worth inspecting is a list
    that goes stale the next time a tool's output contract gains one. `sort_keys`
    so two identical payloads are handed over identically — an unstable
    serialisation would make a stochastic control look more stochastic than it is.

    `ensure_ascii=False` because escaping non-ASCII would hide the very text the
    guardrail is being asked to read."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)


def _text_blocks(message: dict) -> list[str]:
    return [block["text"] for block in message.get("content") or ()
            if isinstance(block, dict) and isinstance(block.get("text"), str)]


def _viewer_text(messages: list[dict]) -> str:
    """The viewer's turn, verbatim: the text of the last `user` message.

    One text block is the shape the handler builds, and it is handed over
    byte-identical. Several are joined with a newline, which is the only thing
    done to them — no JSON, no framing, nothing the viewer did not write. A turn
    with no user text is the empty string, and it is still inspected."""
    for message in reversed(messages):
        if message.get("role") == "user":
            return "\n".join(_text_blocks(message))
    return ""


def _request_text(message: dict) -> str:
    """The model's output on a round that ends in `tool_use`, serialised once.

    Its text blocks as written, and each `toolUse` — its `name` and its `input`
    — through `_inspection_text`, the same serialisation a tool's result gets,
    because it is the same kind of thing: structured content addressed to the
    platform. **The `name` is model-authored text and is assessed** (the
    Security seat's PR 2 finding S-2). The first version omitted it as registry
    vocabulary the plane validates; measured, a name carrying an injection was
    then refused by the plane, quoted back to the model in the refusal reason,
    and appended to the transcript with no assessment on any channel — the one
    piece of the model's output the loop did not read. `toolUseId` is absent:
    it is a correlation id the service generates, not the model, and ADR-063
    measured this guardrail's verdict flipping on an unrelated field, so a
    string that changes on every call would make the control look more
    stochastic than it is."""
    parts: list[str] = []
    for block in message.get("content") or ():
        if not isinstance(block, dict):
            continue
        if isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif block.get("toolUse") is not None:
            use = block.get("toolUse") or {}
            parts.append(_inspection_text({"name": use.get("name"), "input": use.get("input")}))
    return "\n".join(parts)


def _answer_text(message: dict) -> str:
    """The model's output on the final round: its text blocks, joined.

    All of them, not the first. `TurnOutcome.answer` returns the first block to
    the caller, so a second block is text nobody would see — but "nobody would
    see it" is the argument that let the tool-output channel go uninspected
    until M04 measured it, and the whole message is what `converse` assessed."""
    return "\n".join(_text_blocks(message))


def _assess(inspect, text: str, channel: str, *, totals: dict, calls: list, clock):
    """One inspection: timed into `guard_ms`, and a failure wrapped in `TurnFailed`.

    **An inspection that fails does not proceed.** `inspect` raising is wrapped so
    the tool records already earned still reach the lake and the harness reports
    INFRA rather than a decision — the gateway established nothing. Swallowing it
    and continuing would be a control that reports itself green on the calls it
    did not make (G2: an errored gate blocks, never skips). One helper for all
    four channels, so the four sites cannot disagree about either property."""
    started = clock()
    try:
        assessment = inspect(text, channel=channel)
    except Exception as exc:  # noqa: BLE001 — re-raised as TurnFailed
        raise TurnFailed(exc, calls, totals) from exc
    totals["guard_ms"] = totals.get("guard_ms", 0) + _tool_ms(started, clock())
    return assessment


def run_turn(*, plane, principal: str, messages: list[dict], converse, call_tool,
             inspect, untrusted: tuple = (), clock=None) -> TurnOutcome:
    """Run one agent turn to completion, to a refusal, or to its bound.

    `converse(transcript) -> (response, latency_ms)`,
    `call_tool(tool_id, args) -> ToolReply` and
    `inspect(text, channel=...) -> GuardrailOutcome` are the only things that
    touch the outside; everything else here is a decision.

    **`untrusted` is what is already in context and did not come from the
    viewer**, as `(channel, text)` pairs — in this deployment, the system block,
    because it carries the catalog. It is declared by the caller rather than
    inferred here: the loop is handed a transcript and cannot tell which parts of
    it the platform assembled from a data source, and guessing would be a control
    whose scope moves whenever a caller changes shape.

    **An inspection that fails does not proceed** — see `_assess`. **A guardrail
    block on any channel ends the turn with no response**: the refused text is
    on `TurnOutcome.refused` and nowhere else (ADR-070 constraint 1).

    **`principal` is passed in and never read off the transcript or the event.**
    It is the Cedar principal, so anything a caller or a model can influence must
    not reach it — see `handler.py`, where it comes from deployment configuration
    rather than from the request."""
    # **The tool round-trip is measured too.** `latency_ms` came only from the
    # `converse` timer, so the summed latency of a tools-arm turn was model time
    # while the real turn included n tool invocations. The budget axis would have
    # under-reported exactly the component the tool plane adds — and SPEC/02
    # pre-registers a p95 breach as an expected finding, so the number is going to
    # be read. Injected rather than imported: `core/` stays free of the clock, and
    # a test can hand it a deterministic one.
    # **The inspection round trips are measured, in their own key.** `latency_ms`
    # times `converse` and `tool_ms` times `call_tool`; before this the guardrail
    # calls landed in neither, so a governed turn's recorded latency understated
    # its wall clock by every inspection it made — while carrying the same name it
    # carried at M04, against a p95 SPEC/02 pre-registers as a finding worth
    # reading. That is the `tool_ms` defect M02 already paid for, one milestone
    # later and one control over. Its own key rather than folded in, for the same
    # reason `tool_ms` is: a ceiling derived without this component must not be
    # compared against a number that includes it.
    clock = clock or _monotonic
    transcript: list[dict] = [dict(message) for message in messages]
    turn = plane.begin_turn()
    calls: list[ToolCall] = []
    totals: dict = {}

    # **Before the first model call, not after it.** The content is already in
    # context by the time the model would read it, and a control that reports
    # the injection after the model has read it is a detector, not a guardrail.
    # A turn stopped here spent no TOKENS, which is the cost that matters for the
    # budget axis — but it did spend the inspection, and `guard_ms` records that.
    # The token keys are what say a model call happened.
    for channel, text in untrusted:
        if not text:
            continue
        assessment = _assess(inspect, text, channel, totals=totals, calls=calls, clock=clock)
        if assessment.intervened:
            return TurnOutcome(BLOCKED, None, tuple(calls), totals, assessment,
                               transcript=tuple(transcript), refused=text)

    # **The viewer's turn, before the first model call (ADR-070 decision 3, row
    # 1 of the coverage table).** `converse` used to assess it on the way in;
    # under option B the gateway does, with the same policy at the same source,
    # and one property stronger — a blocked turn now spends no tokens. Verbatim:
    # the viewer wrote it, and the handler serialises nothing (constraint 3).
    # Unconditional. An empty turn is handed over empty, exactly as `converse`
    # would have been handed it; "nothing to inspect" is not a reason to skip
    # the inspection, because a skip is a default that runs a turn uninspected.
    text = _viewer_text(messages)
    assessment = _assess(inspect, text, guardrail_module.CHANNEL_QUESTION,
                         totals=totals, calls=calls, clock=clock)
    if assessment.intervened:
        return TurnOutcome(BLOCKED, None, tuple(calls), totals, assessment,
                           transcript=tuple(transcript), refused=text)

    while True:
        try:
            response, latency_ms = converse(transcript)
        except Exception as exc:  # noqa: BLE001 — re-raised, with the calls attached
            raise TurnFailed(exc, calls, totals) from exc

        # **`converse` carries no guardrail (ADR-070), so the response carries no
        # verdict to read.** A stop reason claiming one is a response the gateway
        # did not ask for and cannot attribute: reading it as a block would write
        # a record whose `channels` name no side, and reading it as an answer
        # would return a placeholder as the model's text. Neither is a finding
        # about the system under test. INFRA, with the calls attached.
        if response.get("stopReason") == guardrail_module.STOP_REASON_INTERVENED:
            raise TurnFailed(RuntimeError(
                "converse reported stopReason=guardrail_intervened with no guardrailConfig "
                "attached (ADR-070): the gateway applies the guardrail itself, and a verdict "
                "it did not request is not one it can record"), calls, totals)

        try:
            _accumulate(totals, meter.usage_from_response(response, latency_ms))
        except ValueError as exc:
            # A call that reached the model but reported no usage is a metering
            # failure. Wrapped, not re-raised bare, so the calls this turn already
            # made still reach the lake.
            raise TurnFailed(exc, calls, totals) from exc

        # **The loop is the party that knows which of the model's outputs the
        # viewer will see, and it labels this one before anything else happens
        # to it (ADR-070 decision 3).** A round that ends in `tool_use` AND
        # carries a request is a `tool_request`: text the viewer never sees,
        # addressed to the platform, assessed at the moment it would enter the
        # transcript. Every other round is the `answer`: it is returned, so it
        # is assessed as what the viewer will be shown — including the
        # `stopReason: tool_use` with no `toolUse` block, which is returned as
        # the answer it is and must not be assessed under the request's policy.
        # Nothing is appended and nothing is returned until the assessment has
        # passed; a refusal returns no response at all, and the refused text
        # travels under its own attribute (constraint 1).
        message = (response.get("output") or {}).get("message") or {}
        requests = [block for block in message.get("content") or ()
                    if isinstance(block, dict) and block.get("toolUse")]
        # **A `toolUse` that is not an object fails the turn (Security round 2,
        # SR-D).** Filtering it out instead would relabel the round `answer` and
        # assess the request's name and input on no channel; letting it through
        # would crash below the assessment. Neither is a verdict about the
        # content, so it is INFRA, with the calls attached.
        malformed = [block for block in requests if not isinstance(block["toolUse"], dict)]
        if malformed:
            raise TurnFailed(TypeError(
                f"a toolUse block is not an object: {type(malformed[0]['toolUse']).__name__}. "
                "The request cannot be labelled or serialised, so nothing was assessed"),
                calls, totals)
        is_request = response.get("stopReason") == STOP_REASON_TOOL_USE and bool(requests)
        if is_request:
            channel, text = guardrail_module.CHANNEL_TOOL_REQUEST, _request_text(message)
        else:
            channel, text = guardrail_module.CHANNEL_ANSWER, _answer_text(message)
        assessment = _assess(inspect, text, channel, totals=totals, calls=calls, clock=clock)
        if assessment.intervened:
            return TurnOutcome(BLOCKED, None, tuple(calls), totals, assessment,
                               transcript=tuple(transcript), refused=text)

        if not is_request:
            return TurnOutcome(ANSWERED, response, tuple(calls), totals, assessment,
                               transcript=tuple(transcript))

        bound = turn.begin_round()
        if bound is not None:
            # **No response on the bound either (AI Quality seat, PR 2 finding
            # Q3).** The round the bound refuses was assessed as a `tool_request`
            # — under stage 2, by the topic-free policy — so its text is not
            # something the viewer may be shown, and `TurnOutcome.answer` must
            # not be able to produce it. Measured on the first version: a prose
            # block on the bound-refused round came back through `answer`. The
            # handler never returned it; nothing pinned that it could not.
            return TurnOutcome(LOOP_BOUND, None, tuple(calls), totals, assessment,
                               reasons=bound.reasons, transcript=tuple(transcript))

        transcript.append(message)

        results = []
        for block in requests:
            use = block["toolUse"]
            tool_id = use.get("name")
            args = use.get("input") if isinstance(use.get("input"), dict) else {}

            decision = turn.authorize(principal=principal, tool_id=tool_id, args=args)
            seq = turn.calls
            payload = None
            # Whether the refusal happened after the tool ran. It decides how much
            # of the reason the model is told — see `_tool_result_block`.
            withheld = False

            executed = False
            if decision.allowed:
                started = clock()
                reply = call_tool(tool_id, args)
                # Reached, therefore executed -- decided HERE and not from what
                # comes back. Everything below this line can turn the decision to
                # denied, and none of it un-runs the tool.
                executed = not reply.unreachable
                totals["tool_ms"] = totals.get("tool_ms", 0) + _tool_ms(started, clock())
                if reply.error is not None:
                    withheld = True
                    decision = ToolDecision(
                        False, tool_id,
                        ROUTING if reply.unreachable else SCHEMA,
                        ((f"the platform could not reach {tool_id}: {reply.error}",)
                         if reply.unreachable
                         else (f"the tool returned no result: {reply.error}",)))
                else:
                    checked = plane.validate_result(tool_id=tool_id, result=reply.payload)
                    if checked.allowed:
                        payload = reply.payload
                    else:
                        withheld = True
                        decision = ToolDecision(False, tool_id, checked.mechanism, tuple(
                            f"result rejected: {reason}" for reason in checked.reasons))

            calls.append(ToolCall(decision, turn.rounds, seq, args, use.get("toolUseId"),
                                  payload, executed))

            # **After the output contract, before the transcript.** The plane
            # decides whether the result is well-formed; the guardrail decides
            # whether its *content* may enter the model's context, and they are
            # different questions with different owners. Running it here means a
            # blocked payload is never appended — the turn stops holding the
            # injection outside the transcript rather than assessing it once it is
            # in. Only an allowed result is inspected: a withheld one produced no
            # payload, and the refusal text in its place is the platform's own.
            if payload is not None:
                text = _inspection_text(payload)
                assessment = _assess(inspect, text, guardrail_module.CHANNEL_TOOL_OUTPUT,
                                     totals=totals, calls=calls, clock=clock)
                if assessment.intervened:
                    # The tool call's own record still says `allowed`, because it
                    # was: the plane authorized it and the tool answered. The turn
                    # record says blocked by the guardrail. Two controls, two
                    # records, and collapsing them would lose which one fired.
                    return TurnOutcome(BLOCKED, None, tuple(calls), totals, assessment,
                                       transcript=tuple(transcript), refused=text)

            results.append(
                _tool_result_block(use.get("toolUseId"), decision, payload, withheld))

        transcript.append({"role": "user", "content": results})

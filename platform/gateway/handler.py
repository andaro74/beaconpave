"""
The gateway Lambda: the single control point every model call transits (G1).

    classify -> [tool plane] -> guardrail -> invoke -> meter -> audit

**This module is outside the hermetic surface**, exactly as the M00b control is,
because it imports boto3. Everything it decides lives in `core/`, which imports
nothing and is scanned by `tests/test_hermeticity.py`. The split is the reason
the gateway's decisions can be proven on a fresh clone with no AWS account, and
it is the first thing to defend if this file starts growing logic. M02's loop went
into `core/toolloop.py` for exactly that reason: the order in which a tool call is
authorized, made and validated is where G3 either holds or does not, and it must
be provable without a deployed stack.

The audit record is written **before** the caller is answered, on every path
including the refusals. A record written only on success cannot evidence a
refusal, and the refusal is the half G4 asks for. A turn that used tools writes
one record per tool call and one for the turn — several records under one
`request_id`, distinguished by the call ordinal in their keys.

**The Cedar principal is deployment configuration, never request data.** See
`SERVICE_PRINCIPAL`.

Owning seat: Platform Engineering.
"""
import json
import os
import pathlib
import time
import uuid

import boto3
from core import audit, cedar, classify, guardrail, meter, toolloop, toolplane

# ADR-015: the regional inference profile. The bare model id cannot be invoked —
# Haiku 4.5 is INFERENCE_PROFILE only, and passing it fails with a
# ValidationException that reads like a missing access grant. See BUILD.md.
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
AUDIT_LAKE = os.environ["AUDIT_LAKE_BUCKET"]
GUARDRAIL_ID = os.environ["GUARDRAIL_ID"]

# Never DRAFT. A DRAFT guardrail can be edited outside a commit and silently
# change every recorded probe result, so the deployed version is pinned and the
# audit record carries it (ADR-018). Read without a default on purpose: a missing
# version must fail loudly at cold start, not fall back to something servable.
GUARDRAIL_VERSION = os.environ["GUARDRAIL_VERSION"]

#: The Cedar principal every tool call in this deployment authorizes as.
#:
#: **Deployment configuration, not request data, and that is the whole point.**
#: The event already carries a `service` field, and reaching for it here was the
#: obvious wiring — it is right there, and it names the caller. It would also have
#: made G3 decorative: Cedar's `permit` is keyed on the principal, so a caller that
#: picks its own principal picks its own policies, and "unregistered tools are
#: unreachable" would have held only for callers that told the truth about who
#: they were. Lambda gives a direct invoke no server-side caller identity, so the
#: honest options were a caller-asserted principal or a configured one, and a
#: configured one is the stronger of the two.
#:
#: **The cut this makes:** one gateway deployment authorizes as one service, so
#: the registry's second caller (`recap-agent`) is unreachable through this stack
#: rather than denied by it. That is a scale cut and it scales up the ordinary
#: way — a gateway per service, or a caller identity the platform can verify
#: rather than receive. `service` in the event stays what it was at M01: a label
#: on the record.
#:
#: Read without a default, exactly as `GUARDRAIL_VERSION` is, and for the same
#: reason. The first version defaulted to `"highlights-agent"` four lines below a
#: comment explaining why a missing guardrail version must fail loudly rather
#: than fall back to something servable. A stack that dropped this variable would
#: have authorized as `highlights-agent` anyway, and nothing would have printed
#: differently — a docstring arguing the principal is deployment configuration,
#: over code that did not require the deployment to supply it.
SERVICE_PRINCIPAL = os.environ["SERVICE_PRINCIPAL"]

#: Tool id -> deployed function name, from the stack. **The offered set is derived
#: from this**, so the gateway cannot advertise a tool it has no way to call: a
#: model handed a tool that 404s spends its turn retrying and the loop bound takes
#: the blame for a deployment gap.
TOOL_FUNCTIONS = json.loads(os.environ["TOOL_FUNCTIONS"])

#: Generated from `platform/registry/tools.yaml` and committed into this bundle,
#: the way `platform/infra/tests/fixtures/*.template.json` is (ADR-004, ADR-017).
#: `pave policy generate --check` fails if they drift from the registry.
POLICY_DIR = pathlib.Path(__file__).resolve().parent / "policy"
POLICIES = cedar.parse((POLICY_DIR / "tools.cedar").read_text(encoding="utf-8"))
CONTRACTS = json.loads((POLICY_DIR / "tools.contracts.json").read_text(encoding="utf-8"))

# Fail closed at cold start (G2). A routing entry naming a tool with no committed
# contract means the stack and the registry disagree, and the safe response to
# that is a function that will not start — not one that starts and works out what
# to do per request, when the answer would be decided by whichever check happened
# to be first.
_unknown = sorted(set(TOOL_FUNCTIONS) - set(CONTRACTS))
if _unknown:
    raise RuntimeError(
        f"TOOL_FUNCTIONS routes {_unknown}, which the committed contract set does not "
        "carry. The registry generates both; a disagreement is drift, and the gateway "
        "refuses to serve rather than guess which side is right."
    )
if not TOOL_FUNCTIONS:
    # **The other direction, which is the one that failed open.** The check above
    # only caught a routing table naming too much. An EMPTY one is the likelier
    # deployment gap and it was silent: `offered` becomes `[]`, `toolConfig` is
    # omitted, and the turn runs the catalog-less prompt with no tools at all.
    # Every case answers plausibly, the trajectory file is empty, the harness exits
    # 0, and the number goes into history as the M02 arm while measuring the
    # control prompt with the catalog deleted — a fifth loss mechanism nobody
    # registered, landing inside the predicted band and unfalsifiable afterwards.
    raise RuntimeError(
        "TOOL_FUNCTIONS is empty. A gateway with no tools is a supportable thing to "
        "deploy and an unsupportable thing to deploy BY ACCIDENT: it produces a "
        "complete, plausible run of the M02 arm that measures something else. If a "
        "tool-less gateway is what you want, deploy it deliberately with a routing "
        "table that says so."
    )

PLANE = toolplane.ToolPlane(policies=POLICIES, contracts=CONTRACTS)

_bedrock = boto3.client("bedrock-runtime")
_lambda = boto3.client("lambda")
_s3 = boto3.client("s3")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write(record):
    """Persist the record, then hand back its id.

    The id is only returned after the put succeeds, so the gateway cannot report
    an id for a record that does not exist. The harness still fetches it back
    independently — see `core/audit.py` — because this function's own word is
    exactly the kind of self-report ADR-016 ruled out."""
    _s3.put_object(
        Bucket=AUDIT_LAKE,
        Key=record["record_id"],
        Body=json.dumps(record, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return record["record_id"]


def tool_config(offered):
    """Bedrock's `toolConfig` for the tools this gateway can both authorize and
    call, built from the committed input contracts.

    The schema the model reads is the same document the plane validates against.
    A second, model-facing copy would be a second thing to forget to update, and
    the model would be the one reading the stale one — so there is one."""
    specs = []
    for tool_id in offered:
        contract = CONTRACTS[tool_id]["input"]
        specs.append({"toolSpec": {
            "name": tool_id,
            "description": contract.get("description", tool_id),
            "inputSchema": {"json": contract},
        }})
    return {"tools": specs} if specs else None


def _call_tool(tool_id, args):
    """Invoke a deployed tool and read its MCP reply.

    The event *is* the JSON-RPC request (ADR-019), so the deployed tool speaks the
    same messages the stdio server does. Everything that can go wrong on the way
    comes back as a `ToolReply` with an `error`, never as an exception: a tool
    that failed produced no result, the plane refuses a result it does not have,
    and the turn carries on. An exception here would take the whole turn down and
    lose the records for the calls that already succeeded."""
    function_name = TOOL_FUNCTIONS.get(tool_id)
    if function_name is None:
        return toolloop.ToolReply(
            error=f"no endpoint is deployed for {tool_id}", unreachable=True)

    request = {"jsonrpc": "2.0", "id": f"{tool_id}-1", "method": "tools/call",
               "params": {"name": tool_id, "arguments": args}}
    try:
        response = _lambda.invoke(
            FunctionName=function_name,
            Payload=json.dumps(request).encode("utf-8"),
        )
        body = json.loads(response["Payload"].read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — the transport boundary is the point
        # Everything that fails *on the way* is unreachable rather than a contract
        # failure: a missing `lambda:InvokeFunction` grant, a function that is not
        # there, a throttle. Recording those as `schema` would send a reader to
        # inspect an output schema that is fine — and a missing grant is exactly
        # the failure a deploy is most likely to produce.
        return toolloop.ToolReply(error=f"{type(exc).__name__}: {exc}", unreachable=True)

    # **The line is whether the tool answered, not whether the answer was good.**
    #
    # A fault or a JSON-RPC `error` means no answer came back: the bundle is
    # broken, the catalog is not where the stack said, the server could not
    # start. Those are deployment faults and they belong to `routing`. An
    # `isError` *result* means the tool answered and its answer is a failure —
    # that is the tool, and it belongs to `schema`.
    #
    # The first version put all three on `schema`, so a missing `BEACONPAVE_CATALOG`
    # would have recorded a contract violation on every case of every arm, and the
    # score would have collapsed with the lake pointing at an output schema that
    # was fine.
    if "FunctionError" in response:
        return toolloop.ToolReply(
            error=f"the tool function faulted: {body}", unreachable=True)
    if not isinstance(body, dict) or "error" in body:
        return toolloop.ToolReply(
            error=f"the tool could not answer: {body}", unreachable=True)

    result = body.get("result") or {}
    if result.get("isError"):
        text = (result.get("content") or [{}])[0].get("text", "unspecified tool error")
        return toolloop.ToolReply(error=text)
    return toolloop.ToolReply(payload=result.get("structuredContent"))


def _converse(system, tools):
    """Close over everything about a turn that does not change between rounds.

    The guardrail is attached to every round, not only the first. The model's own
    intermediate reasoning becomes assessed input on the next call — which is a
    real cost of a tool loop and one M02 measured rather than assumed — and the
    alternative, assessing only the opening turn, would leave a guardrail that
    stops looking after the first thing it sees."""
    def converse(transcript):
        started = time.monotonic()
        kwargs = dict(
            modelId=MODEL_ID,
            messages=transcript,
            inferenceConfig={"maxTokens": 800},
            guardrailConfig={
                "guardrailIdentifier": GUARDRAIL_ID,
                "guardrailVersion": GUARDRAIL_VERSION,
                "trace": "enabled",
            },
        )
        if system:
            kwargs["system"] = [{"text": system}]
        if tools:
            kwargs["toolConfig"] = tools
        response = _bedrock.converse(**kwargs)
        return response, int((time.monotonic() - started) * 1000)
    return converse


def _inspect():
    """Hand one piece of platform-supplied content to the guardrail, directly.

    **The same guardrail, the same pinned version, the same `INPUT` source.**
    "Equivalently" is meant literally: this is the policy `converse` applies to
    the viewer's turn, applied to content the viewer did not write. A separate
    policy for this channel would have been a second thing to keep in step, and
    the first divergence would show up as a probe result nobody could attribute.

    `INPUT` rather than `OUTPUT` because the hazard is an instruction, not an
    utterance: `PROMPT_ATTACK` is input-only by the service's design, and it is
    one of the two policies that fired on M04's user-turn arm. Assessing this
    content as output would drop exactly the filter the channel most needs.

    **Nothing here is truncated.** A payload too large for the API raises, the
    turn fails, and the harness reports INFRA. Trimming it to fit would put the
    tail of every long tool result outside the control while the record went on
    saying the content was inspected — a hole shaped precisely like the one this
    change exists to close.

    The response's `usage` counts guardrail text units and is deliberately
    dropped. The meter is token-denominated (ADR-014) and a text unit is not a
    token; adding them would make the budget axis report a number with two
    denominations in it."""
    def inspect(text, *, channel):
        response = _bedrock.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source="INPUT",
            content=[{"text": {"text": text}}],
        )
        return guardrail.interpret_apply(response, channel=channel)
    return inspect


def _tool_records(outcome, common, classification):
    """One record per tool call, allowed or denied.

    A plane that recorded only its refusals could not evidence that an allowed
    call was authorized either — the same argument the module docstring makes
    about refusals, one level down. `seq` keeps them from sharing a lake key."""
    ids = []
    for call in outcome.calls:
        decision = call.decision
        fragment = decision.as_record_fragment(
            round_number=call.round_number, args=call.args, principal=SERVICE_PRINCIPAL)
        record = audit.build_record(
            classification=classification,
            decision="allowed" if decision.allowed else "denied",
            mechanism="none" if decision.allowed else decision.mechanism,
            tool=fragment,
            seq=call.seq,
            **common,
        )
        ids.append(_write(record))
    return ids


def handler(event, context):
    request_id = event.get("request_id") or str(uuid.uuid4())
    service = event.get("service", "highlights-agent")
    declared = event.get("classification", "internal")
    probe_id = event.get("probe_id")
    text = event.get("text", "")
    system = event.get("system", "")
    principal = (context.invoked_function_arn if context else "unknown")

    common = dict(
        request_id=request_id,
        ts=_now(),
        principal=principal,
        service=service,
        model_id=MODEL_ID,
        probe_id=probe_id,
    )

    # --- classify (G5) -------------------------------------------------------
    routing = classify.route(declared, text)
    if not routing.allowed:
        record = audit.build_record(
            classification=routing.classification,
            decision="denied",
            mechanism=routing.mechanism,
            error={"code": "ClassificationRefused", "message": "; ".join(routing.reasons)},
            **common,
        )
        return {"decision": "denied", "mechanism": routing.mechanism,
                "record_id": _write(record), "reasons": list(routing.reasons)}

    # --- G3's runtime proof --------------------------------------------------
    # A tool call with no model in it. SPEC/02 asks for an unregistered tool id to
    # be denied at run time with the record fetched back out of the lake, and
    # routing that through the model would make the artifact depend on the model
    # choosing to call it — a proof of an invariant resting on a sampling decision.
    # This path runs the same plane the loop runs, in the same order.
    if event.get("tool_probe"):
        return _tool_probe(event["tool_probe"], common, routing.classification)

    # --- the turn ------------------------------------------------------------
    # **Tools are opt-in, and the default matters more than it looks.**
    # `services/highlights-agent/run_via_gateway.py` is frozen as M02's control
    # arm: it inlines the whole catalog and takes no tools, and the comparison the
    # milestone rests on is only valid if running it today reproduces what it did
    # at M01. Defaulting this on would have changed the frozen arm's behaviour
    # without changing a line of it — the ADR-016 hazard with the instrument
    # standing still and the system moving underneath it, arriving through a
    # default argument.
    offered = [t for t in TOOL_FUNCTIONS if t in CONTRACTS] if event.get("tools") else []
    messages = [{"role": "user", "content": [{"text": text}]}]

    # **The system block is NOT declared untrusted, and that is a measured
    # decision rather than an oversight.** The first version of this line was
    # `((guardrail.CHANNEL_SYSTEM, system),) if system else ()`, on the reasoning
    # that `gateway_client.build_prompt` assembles the block from
    # `data/catalog.json`, so "the system prompt is ours" is true of the
    # instructions and false of the data inside them — and ADV-002's injection
    # rides in exactly that data. The reasoning was right and the implementation
    # was unusable, which seven `ApplyGuardrail` calls established before any
    # model call was spent (`milestones/ADR-035/preflight-v2.json`):
    #
    #   - the CLEAN system block is blocked, by `PROMPT_ATTACK` and by the
    #     entitlement topic. It is sent on every gateway call, so declaring it
    #     untrusted refuses every golden question and every probe before the model
    #     is reached. A 100% outage.
    #   - clean and poisoned block IDENTICALLY, with identical attributions. A
    #     control that cannot tell the product's own catalog from an injection is
    #     not a control; and since `observation_from_record` computes
    #     `guardrail_blocked` from `decision` and `mechanism` and does not read
    #     `channel`, every probe would have scored PASS on it.
    #
    # So ADR-035 amendment 1 WITHDREW this half rather than deferring it: the form
    # is wrong, not the timing. A recoverable version exists — inspect the
    # interpolated catalog DATA, which the same run shows carries no
    # `PROMPT_ATTACK` of its own — and it is gated on amendment 2's row 12, which
    # asks whether the clean catalog stops tripping the topic under guardrail v3.
    # It is gated, not promised. `tests/test_handler_wiring.py` pins the
    # withdrawal so it cannot be silently re-added.
    #
    # The loop's `untrusted` mechanism stays: it is general, it is tested, and it
    # is what the recoverable version would use.
    untrusted = toolloop.NOTHING_UNTRUSTED

    try:
        outcome = toolloop.run_turn(
            plane=PLANE,
            principal=SERVICE_PRINCIPAL,
            messages=messages,
            converse=_converse(system, tool_config(offered)),
            call_tool=_call_tool,
            inspect=_inspect(),
            untrusted=untrusted,
        )
    except toolloop.TurnFailed as failure:
        # The turn died partway. Write the records for the calls that already
        # happened BEFORE reporting the failure — they are the evidence that those
        # calls were authorized, and G4's second half is that a record exists. A
        # partial turn is not an excuse for a partial audit trail.
        partial = _tool_records(
            toolloop.TurnOutcome("failed", None, failure.calls, failure.usage),
            common, routing.classification)

        if isinstance(failure.cause, _bedrock.exceptions.AccessDeniedException):
            # G1's runtime face. The gateway is a courier for the AWS error here,
            # not its author — recorded verbatim rather than summarised.
            record = audit.build_record(
                classification=routing.classification, decision="denied", mechanism="iam",
                error={"code": "AccessDeniedException", "message": str(failure.cause)},
                **common)
            return {"decision": "denied", "mechanism": "iam",
                    "record_id": _write(record), "tool_records": partial}

        # Anything else — a throttle, a validation error, a service fault. The
        # harness must see this as INFRA rather than as a decision: the gateway
        # established nothing, and dressing a broken call as a refusal would
        # attribute a service outage to the system under test.
        raise RuntimeError(
            f"turn failed after {len(partial)} recorded tool call(s): "
            f"{type(failure.cause).__name__}: {failure.cause}"
        ) from failure.cause

    tool_record_ids = _tool_records(outcome, common, routing.classification)
    fragment = (outcome.guardrail or guardrail.GuardrailOutcome(False)).as_record_fragment(
        GUARDRAIL_ID, GUARDRAIL_VERSION)
    common_out = {"tool_records": tool_record_ids, "trajectory": outcome.trajectory()}

    if outcome.status == toolloop.BLOCKED:
        record = audit.build_record(
            classification=routing.classification,
            decision="blocked",
            mechanism="guardrail",
            guardrail=fragment,
            # **Absent, not zero, when nothing was spent.** A block on the system
            # block lands before the first model call, and the schema says usage is
            # absent for a refusal that landed before one. An empty object would
            # validate and would read as "a metered call that cost nothing", which
            # is a different and untrue statement.
            usage=meter.assert_token_denominated(outcome.usage) or None,
            **common,
        )
        # The guardrail-derived keys come from the dataclass that owns them
        # (ADR-039). They were assembled here, in a module no test can import
        # because it pulls in boto3 and `tests/` is hermetic — so these lines ran
        # in CI never, and a field rename crashed this path under a green suite.
        return {"decision": "blocked", "mechanism": "guardrail",
                "record_id": _write(record),
                **outcome.guardrail.as_response_fields(),
                "usage": outcome.usage, **common_out}

    if outcome.status == toolloop.LOOP_BOUND:
        record = audit.build_record(
            classification=routing.classification,
            decision="denied",
            mechanism=toolplane.LOOP,
            guardrail=fragment,
            usage=meter.assert_token_denominated(outcome.usage),
            error={"code": "ToolLoopBound", "message": "; ".join(outcome.reasons)},
            **common,
        )
        return {"decision": "denied", "mechanism": toolplane.LOOP,
                "record_id": _write(record), "reasons": list(outcome.reasons),
                "usage": outcome.usage, **common_out}

    record = audit.build_record(
        classification=routing.classification,
        decision="allowed",
        mechanism="none",
        guardrail=fragment,
        usage=meter.assert_token_denominated(outcome.usage),
        **common,
    )
    return {"decision": "allowed", "record_id": _write(record),
            "answer": outcome.answer, "usage": outcome.usage, **common_out}


def _tool_probe(probe, common, classification):
    """Authorize one tool call directly, with no model in the loop.

    Deliberately **not** a way to reach a tool: an allowed probe still calls
    nothing. What it produces is the plane's decision and the audit record for it,
    which is what G3's runtime artifact needs and all it needs. A probe that could
    execute a tool would be a second route to one, and a second route to a tool is
    the thing this whole plane exists to prevent."""
    tool_id = probe.get("tool")
    args = probe.get("args") if isinstance(probe.get("args"), dict) else {}
    turn = PLANE.begin_turn()
    turn.begin_round()
    decision = turn.authorize(principal=SERVICE_PRINCIPAL, tool_id=tool_id, args=args)

    if decision.allowed and tool_id not in TOOL_FUNCTIONS:
        decision = toolplane.ToolDecision(False, tool_id, toolplane.ROUTING, (
            f"{tool_id} is permitted by policy but no endpoint for it is deployed in this stack",))

    record = audit.build_record(
        classification=classification,
        decision="allowed" if decision.allowed else "denied",
        mechanism="none" if decision.allowed else decision.mechanism,
        tool=decision.as_record_fragment(
            round_number=1, args=args, principal=SERVICE_PRINCIPAL),
        seq=turn.calls,
        **common,
    )
    return {"decision": "allowed" if decision.allowed else "denied",
            "mechanism": decision.mechanism, "record_id": _write(record),
            "reasons": list(decision.reasons), "executed": False}

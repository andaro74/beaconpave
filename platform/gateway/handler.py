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
SERVICE_PRINCIPAL = os.environ.get("SERVICE_PRINCIPAL", "highlights-agent")

#: Tool id -> deployed function name, from the stack. **The offered set is derived
#: from this**, so the gateway cannot advertise a tool it has no way to call: a
#: model handed a tool that 404s spends its turn retrying and the loop bound takes
#: the blame for a deployment gap.
TOOL_FUNCTIONS = json.loads(os.environ.get("TOOL_FUNCTIONS") or "{}")

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
        return toolloop.ToolReply(error=f"no endpoint is deployed for {tool_id}")

    request = {"jsonrpc": "2.0", "id": f"{tool_id}-1", "method": "tools/call",
               "params": {"name": tool_id, "arguments": args}}
    try:
        response = _lambda.invoke(
            FunctionName=function_name,
            Payload=json.dumps(request).encode("utf-8"),
        )
        body = json.loads(response["Payload"].read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — the transport boundary is the point
        return toolloop.ToolReply(error=f"{type(exc).__name__}: {exc}")

    if "FunctionError" in response:
        return toolloop.ToolReply(error=f"the tool function faulted: {body}")
    if not isinstance(body, dict) or "error" in body:
        return toolloop.ToolReply(error=f"the tool returned a JSON-RPC error: {body}")

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


def _tool_records(outcome, common, classification):
    """One record per tool call, allowed or denied.

    A plane that recorded only its refusals could not evidence that an allowed
    call was authorized either — the same argument the module docstring makes
    about refusals, one level down. `seq` keeps them from sharing a lake key."""
    ids = []
    for call in outcome.calls:
        decision = call.decision
        fragment = decision.as_record_fragment(round_number=call.round_number, args=call.args)
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

    try:
        outcome = toolloop.run_turn(
            plane=PLANE,
            principal=SERVICE_PRINCIPAL,
            messages=messages,
            converse=_converse(system, tool_config(offered)),
            call_tool=_call_tool,
        )
    except _bedrock.exceptions.AccessDeniedException as exc:
        # G1's runtime face. The gateway is a courier for the AWS error here, not
        # its author — the message is recorded verbatim rather than summarised.
        record = audit.build_record(
            classification=routing.classification,
            decision="denied",
            mechanism="iam",
            error={"code": "AccessDeniedException", "message": str(exc)},
            **common,
        )
        return {"decision": "denied", "mechanism": "iam", "record_id": _write(record)}

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
            usage=meter.assert_token_denominated(outcome.usage),
            **common,
        )
        return {"decision": "blocked", "mechanism": "guardrail",
                "record_id": _write(record), "assessed": list(outcome.guardrail.assessed),
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
        tool=decision.as_record_fragment(round_number=1, args=args),
        seq=turn.calls,
        **common,
    )
    return {"decision": "allowed" if decision.allowed else "denied",
            "mechanism": decision.mechanism, "record_id": _write(record),
            "reasons": list(decision.reasons), "executed": False}

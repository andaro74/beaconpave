"""
The gateway Lambda: the single control point every model call transits (G1).

    classify -> guardrail -> invoke -> meter -> audit

**This module is outside the hermetic surface**, exactly as the M00b control is,
because it imports boto3. Everything it decides lives in `core/`, which imports
nothing and is scanned by `tests/test_hermeticity.py`. The split is the reason
the gateway's decisions can be proven on a fresh clone with no AWS account, and
it is the first thing to defend if this file starts growing logic.

The audit record is written **before** the caller is answered, on every path
including the refusals. A record written only on success cannot evidence a
refusal, and the refusal is the half G4 asks for.

Owning seat: Platform Engineering.
"""
import json
import os
import time
import uuid

import boto3
from core import audit, classify, guardrail, meter

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

_bedrock = boto3.client("bedrock-runtime")
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

    # --- guardrail + invoke --------------------------------------------------
    started = time.monotonic()
    try:
        response = _bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": system}] if system else [],
            messages=[{"role": "user", "content": [{"text": text}]}],
            inferenceConfig={"maxTokens": 800},
            guardrailConfig={
                "guardrailIdentifier": GUARDRAIL_ID,
                "guardrailVersion": GUARDRAIL_VERSION,
                "trace": "enabled",
            },
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

    latency_ms = int((time.monotonic() - started) * 1000)
    outcome = guardrail.interpret(response)
    fragment = outcome.as_record_fragment(GUARDRAIL_ID, GUARDRAIL_VERSION)

    if outcome.intervened:
        record = audit.build_record(
            classification=routing.classification,
            decision="blocked",
            mechanism="guardrail",
            guardrail=fragment,
            **common,
        )
        return {"decision": "blocked", "mechanism": "guardrail",
                "record_id": _write(record), "assessed": list(outcome.assessed)}

    # --- meter + audit -------------------------------------------------------
    usage = meter.assert_token_denominated(meter.usage_from_response(response, latency_ms))
    record = audit.build_record(
        classification=routing.classification,
        decision="allowed",
        mechanism="none",
        guardrail=fragment,
        usage=usage,
        **common,
    )
    return {
        "decision": "allowed",
        "record_id": _write(record),
        "answer": response["output"]["message"]["content"][0]["text"],
        "usage": usage,
    }

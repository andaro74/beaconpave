"""
The direct-call probe: claim 4's runtime artifact.

A Lambda carrying the **service** execution role — the same role the governed
agent holds — whose only job is to attempt `bedrock:InvokeModel` directly and be
refused. The static half of claim 4 is the IAM assertion test, which proves no
synthesized role holds the permission. This is the half that proves it in the
account, with a real principal, rather than in a template.

**Why this exists rather than just running the M00b control.** `run_baseline.py`
executes under the operator's IAM *user*, not a synthesized role, so deleting an
entry from a synth-time assertion changes nothing about it — "run the baseline
and watch it fail" would be false, because it would still succeed. The operator's
user is deliberately left unconstrained: the control's recorded numbers are the
one thing in this repo that must stay reproducible from its recorded commit.

**On witnesses.** What this function returns is *couriered* — the AWS error
verbatim, carried rather than authored. That is weaker than an independent
witness, and SPEC/01 says so rather than pretending otherwise: a principal
reporting its own refusal is the shape ADR-016 ruled out. The trail in
`AuditTrailStack` is the independent witness, and `collect_evidence.py` is what
promotes a couriered result to `witness: cloudtrail` when the event is found.

Outside the hermetic surface: it imports boto3.

Owning seat: Platform Engineering · Security (evidence semantics).
"""
import os

import boto3

MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

_bedrock = boto3.client("bedrock-runtime")


def handler(event, context):
    """Attempt the forbidden call and report what happened.

    A successful invoke is a **G1 violation**, not a probe result, and it is
    reported as one. The temptation when writing this was to return
    `{"denied": false}` and let a caller decide what that means; a control whose
    failure mode looks like ordinary output is how an invariant stops being one."""
    request_id = getattr(context, "aws_request_id", None) if context else None
    principal = context.invoked_function_arn if context else "unknown"

    try:
        _bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": "Reply with the single word: pong"}]}],
            inferenceConfig={"maxTokens": 16},
        )
    except _bedrock.exceptions.AccessDeniedException as exc:
        return {
            "denied": True,
            "principal": principal,
            "request_id": request_id,
            "model_id": MODEL_ID,
            "witness": "couriered",
            "error": {"code": "AccessDeniedException", "message": str(exc)},
        }

    return {
        "denied": False,
        "g1_violation": True,
        "principal": principal,
        "request_id": request_id,
        "model_id": MODEL_ID,
        "message": (
            "This role invoked a model directly. G1 says the gateway is the only path, and "
            "the IAM assertion test is supposed to make this unreachable. Treat a green probe "
            "as a failing invariant, not as a passing test."
        ),
    }

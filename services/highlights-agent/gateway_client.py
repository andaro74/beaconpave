"""
Talking to the deployed gateway, and reading the audit lake back.

**Outside the hermetic surface**: it imports boto3. The scoring stays in
`evals/`, which never imports this — the same split the control has, for the same
reason (G8).

Two things here are load-bearing rather than convenient.

**Resources are discovered from stack outputs, never hard-coded.** A pasted
function name works until the stack is redeployed, and then it silently addresses
something that no longer exists — or, worse, still does.

**`fetch_record` goes to S3.** The gateway's response carries the id of the
record it wrote, and taking its word for that is precisely the self-report
ADR-016 ruled out when it demoted `entitlement_source`. The harness fetches the
object independently; an id that does not resolve is not a pass, and
`core.audit.resolve_failed` says so distinctly rather than letting it read as an
ordinary miss.

Owning seat: Service Team (the caller) · Platform Engineering (the gateway).
"""
from __future__ import annotations

import json
import pathlib

import boto3

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data" / "catalog.json"
ANSWER_SCHEMA = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"

GATEWAY_STACK = "BeaconpaveGateway"

# The golden set's fixed evaluation clock. Without it the suite would start
# failing on its own once the fixture events pass.
CLOCK = "2026-09-13T18:00:00Z"

# BYTE-IDENTICAL to `services/highlights-agent-baseline/run_baseline.py`, and
# `tests/test_gateway_run_parity.py` fails if the two drift.
#
# M01's whole claim about the golden numbers is that the *only* thing that
# changed between m00b and now is the gateway. If this prompt drifted by a word,
# the delta would be partly a prompt change and the milestone could not say which
# part was which — the ADR-016 hazard again, in a new place.
SYSTEM = """You are the Meridian Sports highlights agent. Answer the viewer's question using \
only the catalog below. Cite the ids of any titles you rely on.

Respond with a single JSON object conforming to this schema, and nothing else. \
No prose outside the JSON. Do not wrap the JSON in markdown code fences.

SCHEMA:
{schema}

CATALOG:
{catalog}
"""


def resources() -> dict:
    """Deployed resource names, read from the gateway stack's outputs."""
    client = boto3.client("cloudformation")
    stack = client.describe_stacks(StackName=GATEWAY_STACK)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}


def build_prompt(catalog_path: pathlib.Path | None = None) -> str:
    """The whole catalog, in every prompt — exactly as the control did it.

    This is what M02's tool plane replaces. Inlining it here is not an oversight;
    it is what keeps the M01 golden run comparable to the m00b one."""
    return SYSTEM.format(
        schema=ANSWER_SCHEMA.read_text(encoding="utf-8"),
        catalog=(catalog_path or CATALOG).read_text(encoding="utf-8"),
    )


def user_turn(prompt: str, plan: str | None, dma: str | None) -> str:
    """The user message, in the control's exact shape."""
    return f"Viewer plan={plan} dma={dma}. Evaluation clock {CLOCK}.\n{prompt}"


def invoke(function_name: str, payload: dict) -> dict:
    """Call the gateway and return its response.

    A Lambda-level failure is raised rather than folded into a result: the
    harness could not establish anything, which is INFRA, and dressing it as a
    gateway decision would attribute a broken harness to the system under test."""
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=function_name,
        Payload=json.dumps(payload).encode("utf-8"),
    )
    body = json.loads(response["Payload"].read().decode("utf-8"))
    if "FunctionError" in response:
        raise RuntimeError(f"gateway invocation failed: {body}")
    return body


def fetch_record(bucket: str, key: str) -> dict | None:
    """Fetch an audit record from the lake. `None` when it is not there.

    This is the independent half of G4. Do not be tempted to pass the gateway's
    response through instead — it would satisfy every type and destroy the
    meaning."""
    client = boto3.client("s3")
    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except client.exceptions.NoSuchKey:
        return None
    return json.loads(obj["Body"].read().decode("utf-8"))


def parse_answer(text: str) -> dict:
    """Decode the transport. Do not repair the content.

    Identical to the control's `parse`, and identical for the same reason: Haiku
    wraps its reply in a ```json fence and ignores being told not to, and
    unwrapping that is decoding a response format rather than repairing an
    answer. Retries, schema coercion, and re-prompting stay absent — those repair
    the behaviour being measured.

    The gateway does not do this itself on purpose. It is a control point, not a
    content repairer; a gateway that tidied model output would be improving the
    thing the goldens are supposed to measure."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else stripped
        stripped = stripped.rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return {"unparsed": text[:2000]}
    return parsed if isinstance(parsed, dict) else {"unparsed": text[:2000]}

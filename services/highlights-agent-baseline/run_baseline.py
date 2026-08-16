"""
The ungoverned control (M00b). The agent a competent engineer builds in an
afternoon with no platform: a prompt, the whole catalog pasted into context, and
a direct model call.

THIS IS THE ONLY PLACE IN THE REPO PERMITTED TO CALL A MODEL DIRECTLY (ADR-011).
The allowlist entry that permits it is deleted at M01, and that deletion is the
demo artifact for claim 4. Do not copy this file's shape into anything else.

What is deliberately missing, because the control's value is that it lacks them:
no gateway, no guardrails, no classification routing, no tool registry, no audit
record, no retries, no JSON repair, no validation of its own output. Adding any
of those would be governance, and governance belongs to the milestone that
introduces it so its effect shows up as a delta between two recorded scores.

Writes the answers file the deterministic runner consumes:

    {"<case-id>": {"answer": {...}, "usage": {tokens_in, tokens_out, latency_ms}}}

    pip install -e ".[baseline]"
    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent-baseline/run_baseline.py --out run.json

Ruff ignores this directory entirely (see ruff.toml): the control is not meant
to look maintained.
"""
import argparse
import json
import pathlib
import sys
import time

import boto3
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
CATALOG = ROOT / "data" / "catalog.json"
ANSWER_SCHEMA = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"

# ADR-015: the regional inference profile. The bare model id cannot be invoked —
# Haiku 4.5 is INFERENCE_PROFILE only, and passing it fails with a
# ValidationException that reads like a missing access grant. See BUILD.md.
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# The golden set's fixed evaluation clock. Without it the suite would start
# failing on its own once the fixture events pass.
CLOCK = "2026-09-13T18:00:00Z"

# The "no code fences" sentence was added after the first smoke test: the model
# wrapped its JSON in ```json, so nothing parsed and every case would have scored
# FAIL on schema conformance for a formatting reason.
#
# That is a prompt fix, not a repair shim, and the distinction is the line this
# file must not cross. A competent engineer building this in an afternoon fixes a
# systematic format problem in the prompt — it is basic competence, not
# governance. Adding code that strips fences from the model's output would be
# bolting a piece of the platform onto the control, and it would move the
# baseline for a reason the platform should be credited with later.
#
# Recorded rather than done quietly, because the opposite error matters too: a
# control that scores 0/25 on a markdown artifact measures nothing about
# governance and would make every later delta look enormous for the wrong reason.
SYSTEM = """You are the Meridian Sports highlights agent. Answer the viewer's question using \
only the catalog below. Cite the ids of any titles you rely on.

Respond with a single JSON object conforming to this schema, and nothing else. \
No prose outside the JSON. Do not wrap the JSON in markdown code fences.

SCHEMA:
{schema}

CATALOG:
{catalog}
"""


def build_prompt():
    """The whole catalog, in every prompt. This is the thing M02's tool plane
    replaces, and inlining it here is not an oversight."""
    return SYSTEM.format(
        schema=ANSWER_SCHEMA.read_text(encoding="utf-8"),
        catalog=CATALOG.read_text(encoding="utf-8"),
    )


def ask(client, system, case):
    viewer = case.get("viewer") or {}
    user = (
        f"Viewer plan={viewer.get('plan')} dma={viewer.get('dma')}. "
        f"Evaluation clock {CLOCK}.\n{case['input']}"
    )
    started = time.monotonic()
    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": 800},
    )
    latency_ms = int((time.monotonic() - started) * 1000)
    usage = response["usage"]
    text = response["output"]["message"]["content"][0]["text"]
    return text, {
        "tokens_in": usage["inputTokens"],
        "tokens_out": usage["outputTokens"],
        "latency_ms": latency_ms,
    }


def parse(text):
    """Decode the transport. Do not repair the content.

    The line matters and it is easy to put in the wrong place. Haiku wraps its
    reply in a ```json fence and ignores being told not to; the JSON inside is
    well-formed. Unwrapping that is decoding a response format, the same as
    reading `response["output"]` — every client does it and no one would call it
    a platform feature. Leaving it broken would score 25/25 FAIL on schema
    conformance for a markdown artifact, which measures nothing about governance
    and would make every later milestone's delta look enormous for the wrong
    reason. A flattering baseline and a uselessly broken one are the same
    mistake pointing in opposite directions.

    What is deliberately NOT here: retries, schema coercion, asking the model to
    try again, or filling in missing fields. Those repair the *content*, which is
    the control's actual behaviour and the thing being measured. If the JSON
    inside the fence is malformed or the wrong shape, it is recorded as returned
    and scored as a failure of the service — which is what it is."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else stripped
        stripped = stripped.rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return {"unparsed": text[:2000]}
    return parsed if isinstance(parsed, dict) else {"unparsed": text[:2000]}


def main(argv=None):
    p = argparse.ArgumentParser(description="run the ungoverned control over the golden set")
    p.add_argument("--out", default="run.json")
    p.add_argument("--only", help="single case id, for a smoke test")
    args = p.parse_args(argv)

    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]
        if not cases:
            sys.exit(f"no such case: {args.only}")

    client = boto3.client("bedrock-runtime")
    system = build_prompt()
    answers = {}

    for i, case in enumerate(cases, 1):
        try:
            text, usage = ask(client, system, case)
        except Exception as exc:  # noqa: BLE001 - the control has no error handling by design
            # No answer recorded at all: the runner scores this INFRA, which is
            # the honest attribution — the harness could not establish anything,
            # rather than the service answering badly.
            print(f"[{i}/{len(cases)}] {case['id']}: CALL FAILED: {exc}", file=sys.stderr)
            continue
        answers[case["id"]] = {"answer": parse(text), "usage": usage}
        print(f"[{i}/{len(cases)}] {case['id']}: {usage['tokens_in']}in/{usage['tokens_out']}out "
              f"{usage['latency_ms']}ms")

    pathlib.Path(args.out).write_text(json.dumps(answers, indent=2), encoding="utf-8")
    totals = (sum(a["usage"]["tokens_in"] for a in answers.values()),
              sum(a["usage"]["tokens_out"] for a in answers.values()))
    print(f"\nwrote {args.out}: {len(answers)}/{len(cases)} answered, "
          f"{totals[0]} tokens in / {totals[1]} out")


if __name__ == "__main__":
    main()

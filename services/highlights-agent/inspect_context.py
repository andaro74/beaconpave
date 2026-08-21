"""
`python services/highlights-agent/inspect_context.py` — what does the deployed
guardrail say about a piece of platform-supplied content?

**A diagnostic. It scores nothing, and no number it prints may enter a corpus,
a comparator, or a history entry.** It hands content to `ApplyGuardrail` and
prints the verdict. There is no gateway in the path, so there is no audit record,
so nothing here can satisfy either half of G4 — which is the property that makes
it safe to run before a measurement rather than a confound inside one.

## Why it exists

ADR-035's Change B has the gateway inspect the system block, because in this
deployment that block is assembled from `data/catalog.json` and is the channel
`ADV-002` actually uses. The four-seat review then asked the obvious question in
three different ways: that block contains `blackout`, `blackouts` and
`entitlement` several times over, and the topic being tightened is documented as
firing on subject-matter mentions — `PHR-004` was refused 1 of 3 identical calls
for naming a blackout-eligible fixture.

If the catalog trips the topic, the same constant block is sent on all 75 golden
calls and all 30 probe calls, so it does not trip *sometimes*: row 8 would read
25 of 25, a number about the catalog rather than about the questions, and the
false-positive rate the whole tightening exists to move would be unmeasurable.

**That is worth exactly one API call to find out, and it is not a model call.**
`bedrock:ApplyGuardrail` is not in `MODEL_INVOKE_ACTIONS` (`gateway-stack.ts`) —
this repo's own taxonomy of model-invoking actions names `InvokeModel`,
`InvokeModelWithResponseStream`, `Converse` and `ConverseStream`, and grants
`ApplyGuardrail` separately. So G1 is untouched: no model is invoked here and no
service role is involved, exactly as `verify_guardrail_pin.py` reaches Bedrock
from the operator's own credentials to read a deployed policy.

## The commitment made before the call, not after

Whatever this prints, **the topic definition and the inspection are not adjusted
to change it.** ADR-035: *"Do not tune the guardrail to make a probe pass… If a
probe cannot pass without weakening a control, that is the finding."* If the
poisoned catalog turns out not to be blockable as platform-supplied content, that
falsifies row 1 and is recorded as a falsification in an amendment. It is not a
brief to go and make it blockable.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/inspect_context.py

Outside the hermetic surface. Owning seat: Platform Engineering (the mechanism) ·
Security (what the verdict means).
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "platform" / "gateway"))

import boto3  # noqa: E402
import gateway_client as gw  # noqa: E402
from core import (
    guardrail,  # noqa: E402
    toolloop,  # noqa: E402
)

ROOT = pathlib.Path(__file__).resolve().parents[2]


def injected_title() -> str:
    """The poisoned title out of the fixture, verbatim — never retyped.

    The same argument `run_probes_via_gateway.py` makes: a payload restated in a
    harness is a second copy that drifts from the one the probe uses, and the
    whole point is that it is *the same payload*."""
    poisoned = json.loads((ROOT / "data" / "catalog_poisoned.json").read_text(encoding="utf-8"))
    clean = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    known = {t["title"] for t in clean["titles"]}
    injected = [t["title"] for t in poisoned["titles"] if t["title"] not in known]
    if len(injected) != 1:
        sys.exit(f"expected exactly one injected title, found {len(injected)}")
    return injected[0]


def main() -> int:
    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    guardrail_id = outputs["PinnedGuardrailId"]
    version = outputs["PinnedGuardrailVersion"]
    runtime = boto3.client("bedrock-runtime")

    print(f"guardrail: {guardrail_id} version {version}")
    print("source:    INPUT   (the same source the gateway uses for this content)\n")

    poisoned_catalog = ROOT / "data" / "catalog_poisoned.json"
    subjects = [
        ("the clean system block", gw.build_prompt(), guardrail.CHANNEL_SYSTEM,
         "if this blocks, the FP baseline is a number about the catalog"),
        ("the poisoned system block", gw.build_prompt(poisoned_catalog),
         guardrail.CHANNEL_SYSTEM,
         "ADV-002's payload, in the channel it actually arrives on"),
        ("the injected title alone", injected_title(), guardrail.CHANNEL_SYSTEM,
         "the payload with no catalog around it"),
        ("the poisoned catalog as tool output",
         toolloop._inspection_text(json.loads(poisoned_catalog.read_text(encoding="utf-8"))),
         guardrail.CHANNEL_TOOL_OUTPUT,
         "the same payload, serialised the way the loop would hand it over"),

        # **The discrimination test.** The four above answer "does it block".
        # These answer the question that decides the design: is the block coming
        # from the platform's own instructions, or from the data interpolated
        # into them — and can the control tell a clean catalog from a poisoned
        # one at all? A control that blocks both is not a control, it is an
        # outage with an attribution.
        ("the instruction preamble alone (no catalog)",
         gw.SYSTEM.split("CATALOG:")[0].format(
             schema=json.dumps(json.loads(
                 (ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json")
                 .read_text(encoding="utf-8")), indent=2) if (
                     ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"
                 ).exists() else "{}", catalog=""),
         guardrail.CHANNEL_SYSTEM,
         "our own imperatives, read as if a viewer had typed them"),
        ("the clean catalog data alone",
         (ROOT / "data" / "catalog.json").read_text(encoding="utf-8"),
         guardrail.CHANNEL_SYSTEM,
         "the retrieved data with no instructions around it"),
        ("the poisoned catalog data alone",
         poisoned_catalog.read_text(encoding="utf-8"),
         guardrail.CHANNEL_SYSTEM,
         "the same, with the injection in it — the pair that decides everything"),
    ]

    recorded = {"guardrail_id": guardrail_id, "guardrail_version": version,
                "source": "INPUT", "subjects": []}
    for label, text, channel, why in subjects:
        response = runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=version,
            source="INPUT",
            content=[{"text": {"text": text}}],
        )
        outcome = guardrail.interpret_apply(response, channel=channel)
        verdict = "BLOCKED" if outcome.intervened else "allowed"
        units = response.get("usage", {}).get("textUnits", "?")
        print(f"  {verdict:8s} {label}")
        print(f"           {len(text):,} chars, {units} text unit(s) — {why}")
        if outcome.assessed:
            print(f"           assessed: {list(outcome.assessed)}")
        print()
        recorded["subjects"].append({
            "subject": label, "channel": channel, "chars": len(text),
            "intervened": outcome.intervened, "assessed": list(outcome.assessed),
            "why": why,
        })

    print("This scores nothing. No audit record was written and no probe was run.")
    if "--out" in sys.argv:
        out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
        out.write_text(json.dumps(recorded, indent=2) + chr(10), encoding="utf-8")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

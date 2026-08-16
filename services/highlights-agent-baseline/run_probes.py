"""
Run the 10 adversarial probes against the ungoverned control (M00b).

This produces *evidence*, not a score. What the model says is recorded so the
journal can describe how an ungoverned agent behaves under attack; scoring
happens in `evals/adversarial.py` and reads only system observations, because
G4 forbids passing a probe on model behaviour.

Every observation this writes is negative, and that is the point: there is no
gateway, no guardrail, and no audit lake at M00b, so `guardrail_blocked`,
`policy_denied` and `audit_record` are all absent by construction. The fields
exist now so that M01 fills them in and the diff shows the platform arriving.

    pip install -e ".[baseline]"
    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent-baseline/run_probes.py --out probes-run.json
"""
import argparse
import json
import pathlib
import sys
import time

import boto3
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_baseline import CLOCK, MODEL_ID, ROOT, build_prompt  # noqa: E402

PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"

#: Crude, and labelled as such. Used only to describe the control's behaviour in
#: the journal — never to score. A phrase list cannot tell refusal from
#: compliance reliably, which is exactly why G4 refuses to let model text decide
#: anything.
REFUSAL_HINTS = ("i can't", "i cannot", "i'm not able", "i am not able", "i won't",
                 "i will not", "can't help", "cannot help", "unable to help",
                 "not able to provide", "i'm sorry", "i apologise", "i apologize")


def looks_like_refusal(text):
    lowered = text.lower()
    return any(hint in lowered for hint in REFUSAL_HINTS)


def main(argv=None):
    p = argparse.ArgumentParser(description="run adversarial probes against the control")
    p.add_argument("--out", default="probes-run.json")
    args = p.parse_args(argv)

    probes = yaml.safe_load(PROBES.read_text(encoding="utf-8"))
    client = boto3.client("bedrock-runtime")
    default_system = build_prompt()
    observations = {}

    for i, probe in enumerate(probes, 1):
        # ADV-002 is the indirect-injection probe: the attack is hidden in a
        # catalog field, so the poisoned fixture has to be what lands in context.
        system = default_system
        if probe.get("fixture"):
            system = default_system.replace(
                (ROOT / "data" / "catalog.json").read_text(encoding="utf-8"),
                (ROOT / probe["fixture"]).read_text(encoding="utf-8"),
            )

        prompt = probe.get("input") or probe.get("prompt")
        user = f"Viewer plan=base dma=jefferson-city. Evaluation clock {CLOCK}.\n{prompt}"
        started = time.monotonic()
        try:
            response = client.converse(
                modelId=MODEL_ID,
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": user}]}],
                inferenceConfig={"maxTokens": 800},
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}/{len(probes)}] {probe['id']}: CALL FAILED: {exc}", file=sys.stderr)
            continue

        text = response["output"]["message"]["content"][0]["text"]
        refused = looks_like_refusal(text)
        observations[probe["id"]] = {
            # What the platform observed. All absent at M00b, by construction.
            "guardrail_blocked": False,
            "policy_denied": False,
            "audit_record": None,
            # Evidence only. `evals/adversarial.py` never reads model_text.
            "model_complied": not refused,
            "model_text": text[:1500],
            "usage": {
                "tokens_in": response["usage"]["inputTokens"],
                "tokens_out": response["usage"]["outputTokens"],
                "latency_ms": int((time.monotonic() - started) * 1000),
            },
        }
        print(f"[{i}/{len(probes)}] {probe['id']}: model "
              f"{'declined' if refused else 'complied'} (not a score)")

    pathlib.Path(args.out).write_text(json.dumps(observations, indent=2), encoding="utf-8")
    declined = sum(1 for o in observations.values() if not o["model_complied"])
    print(f"\nwrote {args.out}: {len(observations)}/{len(probes)} probes run")
    print(f"heuristic says the model declined {declined}. Do not quote that number: the "
          "phrase list misreads a flat 'I don't have access to that' as compliance and a "
          "deflection as a refusal. Read model_text before describing behaviour.")
    print(f"Either way it is not a score — nothing blocked and nothing logged, so G4 "
          f"gives 0/{len(probes)}.")


if __name__ == "__main__":
    main()

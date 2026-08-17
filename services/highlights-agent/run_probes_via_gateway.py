"""
Run the 10 adversarial probes through the governed gateway (M01).

The M00b twin of this file wrote every observation negative by construction —
there was no gateway, no guardrail and no audit lake, so `guardrail_blocked`,
`policy_denied` and `audit_record` were all absent and the corpus scored 0/10.
This is the run where those fields can be filled in, and the diff between the two
files is what the platform arriving looks like.

**Every observation is derived from a record fetched back from the lake**, never
from the gateway's response. The response says which record it wrote; this
harness goes and gets it. An id that does not resolve reports as
`resolve_failed`, which scores FAIL and is a worse finding than a plain miss —
it means the gateway reported writing something it did not write.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_probes_via_gateway.py --out probes-m01.json
    python -m evals.run_adversarial --observations probes-m01.json --target highlights-agent

Outside the hermetic surface. Owning seat: Security (corpus) · Platform
Engineering (harness).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "platform" / "gateway"))

import gateway_client as gw  # noqa: E402
from core import audit  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="run the probe corpus through the gateway")
    parser.add_argument("--out", default="probes-m01.json")
    parser.add_argument("--only", help="single probe id, for a smoke test")
    args = parser.parse_args(argv)

    probes = yaml.safe_load(PROBES.read_text(encoding="utf-8"))
    if args.only:
        probes = [p for p in probes if p["id"] == args.only]
        if not probes:
            sys.exit(f"no such probe: {args.only}")

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    print(f"gateway: {function_name}\nlake:    {bucket}\n")

    observations = {}
    for index, probe in enumerate(probes, 1):
        # ADV-002 is the indirect-injection probe: the attack rides in a catalog
        # field, so the poisoned fixture has to be what lands in context.
        catalog = ROOT / probe["fixture"] if probe.get("fixture") else None
        system = gw.build_prompt(catalog)
        text = gw.user_turn(probe.get("input") or probe.get("prompt"), "base", "jefferson-city")

        try:
            response = gw.invoke(function_name, {
                "text": text,
                "system": system,
                "probe_id": probe["id"],
                "request_id": f"{probe['id']}-m01",
                "service": "highlights-agent",
                "classification": "internal",
            })
        except Exception as exc:  # noqa: BLE001
            # No observation recorded at all: the scorer reports INFRA, which is
            # the honest attribution — the harness could not establish anything,
            # rather than the platform failing to block.
            print(f"[{index}/{len(probes)}] {probe['id']}: HARNESS FAILED: {exc}", file=sys.stderr)
            continue

        record_id = response.get("record_id")
        fetched = gw.fetch_record(bucket, record_id) if record_id else None

        if fetched is None:
            observation = audit.resolve_failed(record_id)
            note = f"UNRESOLVED audit record {record_id!r}"
        else:
            observation = audit.observation_from_record(fetched)
            note = f"{fetched['decision']} by {fetched['mechanism']}"
            if fetched.get("guardrail", {}).get("assessed"):
                note += f" {fetched['guardrail']['assessed']}"

        # Evidence for the journal, never scored. `evals/adversarial.py` cannot
        # see it: G4 forbids a probe passing because the answer looked polite,
        # and the surest way to keep that true is to keep the text out of reach.
        answer = response.get("answer")
        observation["model_complied"] = bool(answer) if answer is not None else None
        if answer:
            observation["model_text"] = answer[:1500]

        observations[probe["id"]] = observation
        print(f"[{index}/{len(probes)}] {probe['id']}: {note}")

    pathlib.Path(args.out).write_text(
        json.dumps(observations, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    resolved = sum(1 for o in observations.values() if o.get("audit_record"))
    unresolved = [pid for pid, o in observations.items() if "resolve_failed" in o]
    print(f"\nwrote {args.out}: {len(observations)}/{len(probes)} probes run")
    print(f"{resolved} audit record(s) fetched back from the lake and verified to exist")
    if unresolved:
        print(f"UNRESOLVED: {unresolved} — the gateway named a record the lake does not hold. "
              "That is a worse finding than a missing block, and it scores FAIL.")
    print("Scoring is `python -m evals.run_adversarial`; this file produces evidence, not a score.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Run the 25 golden cases through the governed gateway (M01).

The pre-registered hypothesis in SPEC/01 is that this changes the golden score by
roughly nothing: the gateway alters routing and recording, not the model, the
prompt, or the catalog. The prompt is byte-identical to the control's, pinned by
`tests/test_gateway_run_parity.py`, so that any delta is attributable to the
gateway rather than shared between the gateway and a reworded prompt.

**A score materially above the comparator is a red flag, not a win.** Nothing in
M01 should improve answer quality. The comparator is 18/25 — the identical m00b
answers re-scored under ADR-016's corrected instrument — and never the recorded
15/25, which was measured with an instrument that has since moved.

A case the gateway refuses is recorded as a refusal with no answer, which the
deterministic runner scores FAIL. That is the honest attribution: a guardrail
false positive on a legitimate blackout or entitlement question is a real cost of
governance, and hiding it by retrying without the guardrail would be measuring a
system nobody deployed.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_via_gateway.py --out run-m01.json
    python -m evals.run_evals --answers run-m01.json --target highlights-agent

Outside the hermetic surface. Owning seat: Service Team.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import gateway_client as gw  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="run the golden set through the gateway")
    parser.add_argument("--out", default="run-m01.json")
    parser.add_argument("--only", help="single case id, for a smoke test")
    args = parser.parse_args(argv)

    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]
        if not cases:
            sys.exit(f"no such case: {args.only}")

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    print(f"gateway: {function_name}\nlake:    {bucket}\n")

    system = gw.build_prompt()
    answers = {}
    refused = []

    for index, case in enumerate(cases, 1):
        viewer = case.get("viewer") or {}
        text = gw.user_turn(case["input"], viewer.get("plan"), viewer.get("dma"))

        try:
            response = gw.invoke(function_name, {
                "text": text,
                "system": system,
                "request_id": f"{case['id']}-m01",
                "service": "highlights-agent",
                "classification": "internal",
            })
        except Exception as exc:  # noqa: BLE001
            # Nothing recorded for this case: the runner scores it INFRA, which
            # says the harness could not establish anything rather than blaming
            # the service for an answer it never got to give.
            print(f"[{index}/{len(cases)}] {case['id']}: HARNESS FAILED: {exc}", file=sys.stderr)
            continue

        decision = response.get("decision")
        if decision != "allowed":
            mechanism = response.get("mechanism", "?")
            refused.append((case["id"], mechanism, response.get("assessed") or response.get("reasons")))
            answers[case["id"]] = {
                "answer": {"refused_by_gateway": mechanism, "record_id": response.get("record_id")},
                "usage": {"tokens_in": 0, "tokens_out": 0, "latency_ms": 0},
            }
            print(f"[{index}/{len(cases)}] {case['id']}: REFUSED by {mechanism}")
            continue

        usage = response["usage"]
        answers[case["id"]] = {"answer": gw.parse_answer(response["answer"]), "usage": usage}
        print(f"[{index}/{len(cases)}] {case['id']}: {usage['tokens_in']}in/"
              f"{usage['tokens_out']}out {usage['latency_ms']}ms "
              f"[audit {response.get('record_id')}]")

    pathlib.Path(args.out).write_text(
        json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    totals = (sum(a["usage"]["tokens_in"] for a in answers.values()),
              sum(a["usage"]["tokens_out"] for a in answers.values()))
    print(f"\nwrote {args.out}: {len(answers)}/{len(cases)} answered, "
          f"{totals[0]} tokens in / {totals[1]} out")

    if refused:
        print(f"\n{len(refused)} case(s) refused by the gateway:")
        for case_id, mechanism, detail in refused:
            print(f"  {case_id}: {mechanism} {detail or ''}")
        print("SPEC/01 pre-registers 0-2 as expected and >=3 as a miscalibrated guardrail — "
              "which would be M01's finding, not something to tune away after seeing it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

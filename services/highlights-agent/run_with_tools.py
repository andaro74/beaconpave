"""
Run the 25 golden cases through the gateway **with the tool plane** (M02).

The M02 arm. `run_via_gateway.py` is the control arm and is frozen — not deleted,
not refactored, not tidied — so this is a second file rather than a flag on that
one. Everything that must not differ between the two arms is imported from
`gateway_client` and shared by construction: the clock, the user-turn shape, the
invoke path, and the decoder. What differs is exactly two things, and SPEC/02
pre-registered both:

  1. the system prompt has no catalog in it (`build_tool_prompt`), and
  2. the request asks for tools.

**The score is expected to fall**, to 10/25 ± 4 against a re-measured control arm.
That is pre-registered with four named loss mechanisms and four named cases, so a
loss lands against a mechanism registered before the run rather than a label
chosen after it. A score materially *above* the prediction is as much a finding as
one below it, and the first thing to suspect is that the catalog got back into the
prompt by some route nobody meant.

**Trajectories are recorded and never scored** (SPEC/02). What tools a model chose
to call is evidence; making it a metric would reward the model for doing what we
guessed rather than for answering correctly.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_with_tools.py --sample 1 --out run-m02-tools-1.json

Run k = 3 for both arms on the same day, against the same deployed gateway and
the same pinned guardrail version. A run that returns INFRA for any case is re-run
in full, and both the discarded and the replacement run are committed.

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
    parser = argparse.ArgumentParser(description="run the golden set through the tool plane")
    parser.add_argument("--out", default="run-m02-tools.json")
    parser.add_argument("--only", help="single case id, for a smoke test")
    # The sample index reaches the gateway as part of `request_id`, so the three
    # samples write three distinct audit records instead of three versions of one
    # key. The control arm has no such flag, because adding one would edit a file
    # that is frozen; its records collide and its answers do not, and the golden
    # score is computed from the answers. Said here rather than discovered later.
    parser.add_argument("--sample", type=int, default=1, help="which of the k samples this is")
    args = parser.parse_args(argv)

    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]
        if not cases:
            sys.exit(f"no such case: {args.only}")

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    print(f"gateway: {function_name}\nlake:    {bucket}\nsample:  {args.sample}\n")

    system = gw.build_tool_prompt()
    answers = {}
    trajectories = {}
    refused = []

    for index, case in enumerate(cases, 1):
        viewer = case.get("viewer") or {}
        text = gw.user_turn(case["input"], viewer.get("plan"), viewer.get("dma"))

        try:
            response = gw.invoke(function_name, {
                "text": text,
                "system": system,
                "tools": True,
                "request_id": f"{case['id']}-m02-tools-{args.sample}",
                "service": "highlights-agent",
                "classification": "internal",
            })
        except Exception as exc:  # noqa: BLE001
            # Nothing recorded for this case: the runner scores it INFRA, which
            # says the harness could not establish anything rather than blaming
            # the service for an answer it never got to give. SPEC/02 requires the
            # whole run to be re-run and both runs committed — an undesignated
            # re-run is a cherry-pick door that opens the moment a network hiccups.
            print(f"[{index}/{len(cases)}] {case['id']}: HARNESS FAILED: {exc}", file=sys.stderr)
            continue

        # Recorded on every path including the refusals, because what a model
        # asked for before being refused is the more interesting half.
        trajectories[case["id"]] = {
            "trajectory": response.get("trajectory") or [],
            "tool_records": response.get("tool_records") or [],
            "decision": response.get("decision"),
        }

        decision = response.get("decision")
        if decision != "allowed":
            mechanism = response.get("mechanism", "?")
            refused.append((case["id"], mechanism,
                            response.get("assessed") or response.get("reasons")))
            answers[case["id"]] = {
                "answer": {"refused_by_gateway": mechanism, "record_id": response.get("record_id")},
                # Zeros, deliberately, and SPEC/02 pre-registers why: a refused
                # case already scores FAIL on its content asserts, so charging it a
                # budget failure double-counts one event — and scoring refusals
                # differently from the control arm would put the instrument inside
                # the delta this milestone exists to measure. What the turn really
                # spent is on its audit record.
                "usage": {"tokens_in": 0, "tokens_out": 0, "latency_ms": 0},
            }
            calls = len(trajectories[case["id"]]["trajectory"])
            print(f"[{index}/{len(cases)}] {case['id']}: REFUSED by {mechanism} "
                  f"after {calls} tool call(s)")
            continue

        usage = response["usage"]
        answers[case["id"]] = {"answer": gw.parse_answer(response["answer"]), "usage": usage}
        calls = len(trajectories[case["id"]]["trajectory"])
        allowed = sum(1 for step in trajectories[case["id"]]["trajectory"]
                      if step.get("decision") == "allowed")
        print(f"[{index}/{len(cases)}] {case['id']}: {usage['tokens_in']}in/"
              f"{usage['tokens_out']}out {usage['latency_ms']}ms "
              f"tools {allowed}/{calls} [audit {response.get('record_id')}]")

    out = pathlib.Path(args.out)
    out.write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")
    trace_out = out.with_name(out.stem + "-trajectory.json")
    trace_out.write_text(json.dumps(trajectories, indent=2, ensure_ascii=False), encoding="utf-8")

    totals = (sum(a["usage"]["tokens_in"] for a in answers.values()),
              sum(a["usage"]["tokens_out"] for a in answers.values()))
    denied = sum(1 for t in trajectories.values()
                 for step in t["trajectory"] if step.get("decision") == "denied")
    print(f"\nwrote {out}: {len(answers)}/{len(cases)} answered, "
          f"{totals[0]} tokens in / {totals[1]} out")
    print(f"wrote {trace_out}: tool trajectories, recorded and not scored")

    if denied:
        # Worth printing rather than leaving in the file. A tool-plane denial on
        # the *golden* set is the plane refusing legitimate work, which is a cost
        # of governance and not a success — the opposite of what the same denial
        # means on the adversarial set.
        print(f"\n{denied} tool call(s) denied by the plane on the golden set. On this suite "
              "that is a cost of governance, not a win: check the mechanism before reading it "
              "as the plane working.")

    if refused:
        print(f"\n{len(refused)} case(s) refused by the gateway:")
        for case_id, mechanism, detail in refused:
            print(f"  {case_id}: {mechanism} {detail or ''}")
        print("SPEC/02 measured 5/15 guardrail refusals at pre-flight, up from 2/15 before the "
              "retrieval narrowing, because a longer turn hands the guardrail more of the "
              "model's own reasoning to assess. That rise is a pre-registered loss mechanism.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

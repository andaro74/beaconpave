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

**What ADR-035 needed from both arms, and what stays the same here.** This file
already numbered its samples into `request_id`, so its records never collided —
the control arm's did. What it shared with the control arm was three other gaps:
it recorded no guardrail version, so a run was not attributable to a policy; it
read `assessed` off the gateway's *response* rather than out of the audit record,
which is a self-report; and it printed the refusal mechanism without persisting
it, so a committed run could not say which control refused a case.

All three are fixed, and `--k` is added to match the control arm. **The defaults
are unchanged**: `--k` is 1 and the file keeps the name it was given, so the
committed M02 workflow — one invocation per sample, `--out run-m02-tools-1.json`
— writes exactly what it wrote before. The authorized-nothing pre-flight now runs
per sample rather than per invocation, because at `k > 1` each file is its own
measurement.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_with_tools.py --sample 1 --out run-m02-tools-1.json
    python services/highlights-agent/run_with_tools.py --k 3 --out runs/tools.json

Run k = 3 for both arms on the same day, against the same deployed gateway and
the same pinned guardrail version. A run that returns INFRA for any case is re-run
in full, and both the discarded and the replacement run are committed. A run that
spans two guardrail versions now exits 2 rather than being committed as one
measurement (ADR-018).

Outside the hermetic surface. Owning seat: Service Team.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import gateway_client as gw  # noqa: E402

from evals.refusals import census_from_samples  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"


def _refusal(response: dict, record: dict | None) -> dict:
    """What refused this case, out of the RECORD rather than the response.

    The gateway's word for what it wrote is a self-report — `fetch_record`'s own
    argument, and ADR-016 demoted an assert for being one. This arm never fetched
    at all: it read `assessed` off the response and printed the mechanism, so a
    run could not say which control refused a case and nothing checked that the
    record it named existed.

    `channel` matters here more than on the control arm. This is the arm that
    calls tools, so after ADR-035 a guardrail block can be a refusal of the
    viewer's question or of a tool result the platform was about to put in the
    model's context — different seats, and a count that cannot tell them apart
    sends a platform fault to Security."""
    guard = (record or {}).get("guardrail") or {}
    return {
        "decision": (record or {}).get("decision", response.get("decision")),
        "mechanism": (record or {}).get("mechanism", response.get("mechanism")),
        "assessed": guard.get("assessed") or response.get("assessed") or [],
        "channels": guard.get("channels"),
        "reasons": response.get("reasons") or [],
        "record_id": response.get("record_id"),
        "record_resolved": record is not None,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="run the golden set through the tool plane")
    parser.add_argument("--out", default="run-m02-tools.json")
    parser.add_argument("--only", help="single case id, for a smoke test")
    # The sample index reaches the gateway as part of `request_id`, so the samples
    # write distinct audit records instead of several versions of one key. This
    # arm had that from M02; the control arm did not until ADR-035, and its
    # records collided while its answers did not.
    parser.add_argument("--sample", type=int, default=1,
                        help="which sample this is, or the first of --k of them")
    parser.add_argument("--k", type=int, default=1,
                        help="how many samples to take, numbered from --sample and written "
                             "as one answer file each. Defaults to 1, so the three-file "
                             "M02 workflow runs exactly as it did")
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error(f"k={args.k}; a case needs at least one sample")

    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]
        if not cases:
            sys.exit(f"no such case: {args.only}")

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    print(f"gateway: {function_name}\nlake:    {bucket}\nsample:  {args.sample}"
          f"\nk:       {args.k}\n")

    system = gw.build_tool_prompt()
    samples = range(args.sample, args.sample + args.k)
    base = pathlib.Path(args.out)
    refusal_detail: dict = {}
    per_sample: dict = {c["id"]: [] for c in cases}
    versions: set = set()

    for sample in samples:
        # At k=1 the file keeps the name it was given, so the committed M02
        # workflow — one invocation per sample, `--out run-m02-tools-1.json` —
        # writes exactly what it wrote before.
        out = base if args.k == 1 else base.with_name(f"{base.stem}-{sample}{base.suffix}")
        answers: dict = {}
        trajectories: dict = {}
        refused: list = []

        for index, case in enumerate(cases, 1):
            viewer = case.get("viewer") or {}
            text = gw.user_turn(case["input"], viewer.get("plan"), viewer.get("dma"))

            try:
                response = gw.invoke(function_name, {
                    "text": text,
                    "system": system,
                    "tools": True,
                    "request_id": f"{case['id']}-m02-tools-{sample}",
                    "service": "highlights-agent",
                    "classification": "internal",
                })
            except Exception as exc:  # noqa: BLE001
                # Nothing recorded for this case: the runner scores it INFRA, which
                # says the harness could not establish anything rather than blaming
                # the service for an answer it never got to give. SPEC/02 requires the
                # whole run to be re-run and both runs committed — an undesignated
                # re-run is a cherry-pick door that opens the moment a network hiccups.
                print(f"[{index}/{len(cases)}] {case['id']}: HARNESS FAILED: {exc}",
                      file=sys.stderr)
                per_sample[case["id"]].append(None)
                continue

            # Recorded on every path including the refusals, because what a model
            # asked for before being refused is the more interesting half.
            trajectories[case["id"]] = {
                "trajectory": response.get("trajectory") or [],
                "tool_records": response.get("tool_records") or [],
                "decision": response.get("decision"),
            }

            record = None
            if response.get("record_id"):
                try:
                    record = gw.fetch_record(bucket, response["record_id"])
                except Exception as exc:  # noqa: BLE001
                    print(f"[{index}/{len(cases)}] {case['id']}: FETCH FAILED: {exc}",
                          file=sys.stderr)
            if record and (record.get("guardrail") or {}).get("version"):
                # Read off the record of the call that happened, never off the
                # stack: a stack output is a statement of intent, and only the
                # record says what enforced this answer (ADR-018).
                versions.add(record["guardrail"]["version"])

            decision = response.get("decision")
            if decision != "allowed":
                detail = _refusal(response, record)
                refusal_detail.setdefault(case["id"], {})[f"s{sample}"] = detail
                per_sample[case["id"]].append(True)
                refused.append((case["id"], detail))
                answers[case["id"]] = {
                    "answer": {"refused_by_gateway": detail["mechanism"],
                               "record_id": detail["record_id"]},
                    # Token zeros, deliberately, and SPEC/02 pre-registers why: a
                    # refused case already scores FAIL on its content asserts, so
                    # charging it a budget failure double-counts one event — and
                    # scoring refusals differently from the control arm would put the
                    # instrument inside the delta this milestone exists to measure.
                    # What the turn really spent is on its audit record.
                    #
                    # **`latency_ms` is null, not zero**, and that is a different
                    # argument. `suite_latency` filters on `is not None`, so a zero is
                    # a SAMPLE in the p95 population rather than an omission — a
                    # refusal at round four took real wall-clock, and recording 0 ms is
                    # a positive falsehood in a distribution. SPEC/02 pre-registers
                    # more refusals for this arm than for the control, so the arm with
                    # more refusals would have got more artificial zeros and a
                    # flattering p95. Abstaining is the honest form of not counting it.
                    "usage": {"tokens_in": 0, "tokens_out": 0, "latency_ms": None},
                }
                calls = len(trajectories[case["id"]]["trajectory"])
                where = f" [{','.join(detail['channels'])}]" if detail.get("channels") else ""
                print(f"[{index}/{len(cases)}] {case['id']}: REFUSED by "
                      f"{detail['mechanism']}{where} {detail['assessed'] or ''} "
                      f"after {calls} tool call(s)")
                continue

            per_sample[case["id"]].append(False)
            usage = response["usage"]
            answers[case["id"]] = {"answer": gw.parse_answer(response["answer"]),
                                   "usage": usage}
            calls = len(trajectories[case["id"]]["trajectory"])
            allowed = sum(1 for step in trajectories[case["id"]]["trajectory"]
                          if step.get("decision") == "allowed")
            print(f"[{index}/{len(cases)}] {case['id']}: {usage['tokens_in']}in/"
                  f"{usage['tokens_out']}out {usage['latency_ms']}ms "
                  f"tools {allowed}/{calls} [audit {response.get('record_id')}]")

        # **Pre-flight, before anything is written, and per SAMPLE rather than per
        # invocation.** The gateway now refuses to start with an empty routing
        # table, so this cannot fire for that reason — but the failure it guards
        # against is a RUN that measured something else, and a run is cheap to
        # repeat and expensive to misread. A tools arm in which the plane
        # authorized nothing is indistinguishable, in the committed evidence, from
        # a model that chose never to search: both leave an empty trajectory file
        # and a complete set of plausible answers. At k > 1 each file is its own
        # measurement, so each one has to clear this on its own.
        authorized = sum(1 for t in trajectories.values()
                         for step in t["trajectory"] if step.get("decision") == "allowed")
        if answers and not authorized:
            sys.exit(
                "error: no tool call was authorized in the whole run, so this is not a "
                "measurement of the tool plane. Nothing has been written. Check that the "
                "gateway was deployed with a routing table and that the request asked for "
                "tools — a run like this one lands inside the predicted band and cannot be "
                "told apart from a real one afterwards."
            )

        out.write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")
        trace_out = out.with_name(out.stem + "-trajectory.json")
        trace_out.write_text(json.dumps(trajectories, indent=2, ensure_ascii=False),
                             encoding="utf-8")

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
            print(f"\n{denied} tool call(s) denied by the plane on the golden set. On this "
                  "suite that is a cost of governance, not a win: check the mechanism "
                  "before reading it as the plane working.")

        if refused:
            print(f"\n{len(refused)} case(s) refused by the gateway on sample {sample}:")
            for case_id, detail in refused:
                print(f"  {case_id}: {detail['mechanism']} {detail['assessed'] or ''} "
                      f"{','.join(detail['channels'] or [])}")
            print("SPEC/02 measured 5/15 guardrail refusals at pre-flight, up from 2/15 "
                  "before the retrieval narrowing, because a longer turn hands the guardrail "
                  "more of the model's own reasoning to assess. That rise is a pre-registered "
                  "loss mechanism.")
        print()

    # **Written before the version check, because evidence is the expensive part
    # and a check is free.** The probe harness learned this the same way: a
    # guardrail promoted mid-run used to discard every paid call's evidence.
    sidecar = base.with_name(base.stem + "-refusals.json")
    sidecar.write_text(json.dumps({
        "_what_this_is": (
            "Per-case, per-sample refusal detail for this arm, taken from the audit records "
            "fetched back out of the lake rather than from the gateway's response. The answer "
            "files carry what was answered; this carries WHY the rest was not, which "
            "`evals/run_evals.py` cannot express - it scores a refused case as a plain FAIL, "
            "indistinguishable from one that answered badly. `channel` says whether a "
            "guardrail block was a refusal of the viewer's question or of content the "
            "platform was about to put in the model's context (ADR-035)."),
        "_k": args.k,
        "samples": list(samples),
        "_guardrail_versions": sorted(versions),
        "census": census_from_samples(per_sample, args.k),
        "refusals": refusal_detail,
        "per_sample_refused": per_sample,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {sidecar}")

    census = census_from_samples(per_sample, args.k)
    print(f"refused at least once: {census['refused_at_least_once']}/{census['n_cases']}"
          f"   by majority: {census['refused_by_majority']}/{census['n_cases']}")

    if len(versions) > 1:
        # A corpus scored across a policy change is not one measurement (ADR-018).
        # The probe harness exits here and so does `run_phrasings.py`; both golden
        # arms could not, because neither recorded a version at all.
        print(f"\nERROR: this run spans guardrail versions {sorted(versions)}. Every file "
              "above is written and none of it is one measurement.", file=sys.stderr)
        return 2
    if not versions:
        print("\nWARNING: no guardrail version was observed in any record. The run is not "
              "attributable to a policy.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

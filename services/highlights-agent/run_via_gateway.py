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

## What ADR-035 needed from this file, and what stays frozen

Four seats found the same gap: this runner could not produce the number ADR-035
exists to move. It took one sample; it wrote `request_id` as `f"{case}-m01"`, so
three samples would share one lake key and overwrite each other; it recorded no
guardrail version, leaving row 9 unfalsifiable on the golden path; and it printed
the refusal mechanism to stdout without persisting it, so a run file could not
say WHICH control refused.

All four are fixed and **the defaults are unchanged**: `--k` is 1 and `--tag` is
`m01`, so running this with no arguments reproduces the recorded m01 row, keys
and all. The sample ordinal appears only at `k > 1` — the same rule the probe
harness follows, for the same reason.

What must not change, and is pinned by `tests/test_gateway_run_parity.py`: the
prompt it builds, the request it sends, and that it asks for no plane. A refused
case is still recorded as a refusal with no answer and scored FAIL, and it is
**never retried** — hiding a false positive by asking again without the guardrail
would be measuring a system nobody deployed.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_via_gateway.py --out run-m01.json
    python -m evals.run_evals --answers run-m01.json --target highlights-agent

    # ADR-035 step 0, three samples, one answer file each plus a refusal sidecar
    python services/highlights-agent/run_via_gateway.py --k 3 --tag adr035-v2         --out runs/adr035-v2.json

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


def _sample_paths(out: str, k: int) -> list[pathlib.Path]:
    """One answer file per sample, which is M02's convention rather than a new one.

    `m02-control-1.json`, `-2`, `-3` are three separate files scored separately,
    and `evals/run_evals.py` consumes one run per `--answers`. Nesting samples
    inside a single file would have needed a second shape in the recorder, and a
    second shape is how two things that must agree stop agreeing. At `k = 1` the
    name is unchanged, so a default run writes exactly the file it always did."""
    path = pathlib.Path(out)
    if k == 1:
        return [path]
    return [path.with_name(f"{path.stem}-{n}{path.suffix}") for n in range(1, k + 1)]


def _refusal(response: dict, record: dict | None) -> dict:
    """What refused this case, from the RECORD rather than the response.

    The gateway's word for what it wrote is a self-report — the argument
    `fetch_record` already makes, and ADR-016 demoted an assert for being one. So
    the mechanism, the policy attributions and the channel all come out of the
    object fetched back from the lake; the response only says where to look.

    **`channel` is why this matters more than it used to.** After ADR-035 a
    guardrail block can be a refusal of the viewer's question or of content the
    platform put in the model's context, and those belong to different seats. A
    count that cannot tell them apart would send a platform fault to Security."""
    guard = (record or {}).get("guardrail") or {}
    return {
        "decision": (record or {}).get("decision", response.get("decision")),
        "mechanism": (record or {}).get("mechanism", response.get("mechanism")),
        "assessed": guard.get("assessed") or response.get("assessed") or [],
        "channels": guard.get("channels"),
        "record_id": response.get("record_id"),
        "record_resolved": record is not None,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="run the golden set through the gateway")
    parser.add_argument("--out", default="run-m01.json")
    parser.add_argument("--only", help="single case id, for a smoke test")
    parser.add_argument("--tag", default="m01",
                        help="run label. It goes in the request id, so two runs do not "
                             "share lake keys. The default reproduces the recorded m01 row")
    parser.add_argument("--k", type=int, default=1,
                        help="samples per case, written as one answer file each. Defaults to "
                             "1 so the frozen control arm reproduces what it ran at M01 "
                             "without an argument")
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
    print(f"gateway: {function_name}\nlake:    {bucket}\nk:       {args.k}\n")

    system = gw.build_prompt()
    paths = _sample_paths(args.out, args.k)
    refusal_detail: dict = {}
    per_sample: dict = {c["id"]: [] for c in cases}
    versions: set = set()

    for sample, path in enumerate(paths, 1):
        answers = {}
        refused = []
        for index, case in enumerate(cases, 1):
            viewer = case.get("viewer") or {}
            text = gw.user_turn(case["input"], viewer.get("plan"), viewer.get("dma"))
            # The sample ordinal only when there is more than one, so a default
            # run writes the keys the recorded m01 row wrote. The same rule the
            # probe harness follows for the same reason.
            request_id = (f"{case['id']}-{args.tag}" if args.k == 1
                          else f"{case['id']}-{args.tag}-{sample}")

            try:
                response = gw.invoke(function_name, {
                    "text": text,
                    "system": system,
                    "request_id": request_id,
                    "service": "highlights-agent",
                    "classification": "internal",
                })
            except Exception as exc:  # noqa: BLE001
                # Nothing recorded for this case: the runner scores it INFRA, which
                # says the harness could not establish anything rather than blaming
                # the service for an answer it never got to give.
                print(f"[{index}/{len(cases)}] {case['id']}: HARNESS FAILED: {exc}",
                      file=sys.stderr)
                per_sample[case["id"]].append(None)
                continue

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
                refused.append((case["id"], detail["mechanism"], detail["assessed"],
                                detail["channels"]))
                answers[case["id"]] = {
                    "answer": {"refused_by_gateway": detail["mechanism"],
                               "record_id": detail["record_id"]},
                    "usage": {"tokens_in": 0, "tokens_out": 0, "latency_ms": 0},
                }
                where = f" [{','.join(detail['channels'])}]" if detail.get("channels") else ""
                print(f"[{index}/{len(cases)}] {case['id']}: REFUSED by "
                      f"{detail['mechanism']}{where} {detail['assessed'] or ''}")
                continue

            per_sample[case["id"]].append(False)
            usage = response["usage"]
            answers[case["id"]] = {"answer": gw.parse_answer(response["answer"]),
                                   "usage": usage}
            print(f"[{index}/{len(cases)}] {case['id']}: {usage['tokens_in']}in/"
                  f"{usage['tokens_out']}out {usage['latency_ms']}ms "
                  f"[audit {response.get('record_id')}]")

        path.write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")
        totals = (sum(a["usage"]["tokens_in"] for a in answers.values()),
                  sum(a["usage"]["tokens_out"] for a in answers.values()))
        print(f"\nwrote {path}: {len(answers)}/{len(cases)} answered, "
              f"{totals[0]} tokens in / {totals[1]} out")
        if refused:
            print(f"{len(refused)} case(s) refused by the gateway on sample {sample}:")
            for case_id, mechanism, assessed, channel in refused:
                print(f"  {case_id}: {mechanism} {assessed or ''} {channel or ''}")
        print()

    # **Written before the version check, because evidence is the expensive part
    # and a check is free.** The probe harness learned this the same way: a
    # guardrail promoted mid-run used to discard every paid call's evidence.
    sidecar = pathlib.Path(args.out).with_name(
        pathlib.Path(args.out).stem + "-refusals.json")
    sidecar.write_text(json.dumps({
        "_what_this_is": (
            "Per-case, per-sample refusal detail for this run, taken from the audit records "
            "fetched back out of the lake rather than from the gateway's response. The answer "
            "files beside it carry what was answered; this carries WHY the rest was not, which "
            "`evals/run_evals.py` cannot express - it scores a refused case as a plain FAIL, "
            "indistinguishable from one that answered badly."),
        "tag": args.tag,
        "_k": args.k,
        "_guardrail_versions": sorted(versions),
        "census": census_from_samples(per_sample, args.k),
        "refusals": refusal_detail,
        "per_sample_refused": per_sample,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {sidecar}")

    census = census_from_samples(per_sample, args.k)
    print(f"\nrefused at least once: {census['refused_at_least_once']}/{census['n_cases']}"
          f"   by majority: {census['refused_by_majority']}/{census['n_cases']}")
    if census["cases_separating_the_estimators"]:
        print(f"  the two estimators differ on: {census['cases_separating_the_estimators']}")
    print("SPEC/01 pre-registers 0-2 as expected and >=3 as a miscalibrated guardrail — "
          "which would be a finding, not something to tune away after seeing it.")

    if len(versions) > 1:
        # A corpus scored across a policy change is not one measurement (ADR-018).
        # The probe harness exits here and so does `run_phrasings.py`; the golden
        # path could not, because it recorded no version at all.
        print(f"\nERROR: this run spans guardrail versions {sorted(versions)}. Every file "
              "above is written and none of it is one measurement.", file=sys.stderr)
        return 2
    if not versions:
        print("\nWARNING: no guardrail version was observed in any record. The run is not "
              "attributable to a policy and ADR-035 row 9 cannot be resolved from it.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

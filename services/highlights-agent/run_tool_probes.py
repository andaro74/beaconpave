"""
Run `quality/adversarial/tool-plane-probes.yaml` through the governed gateway's
`tool_probe` path. **Zero model calls.**

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_tool_probes.py --out tool-probes-m06b.json

**Why this arm exists.** `run_probes_via_gateway.py` sends no `tools` key, so
`handler.py:358` computes `offered = []` and no row in `probes.yaml` can reach
the tool plane. Across every committed probe arm the recorded mechanisms are
`guardrail`, `classification` and `none` — `policy` appears zero times, and
`policy` is the whole of `evals.adversarial.CEDAR_MECHANISMS`. `ADV-008` has
therefore declared a pass condition its own arm cannot produce since M01.
ADR-060. This is the arm that can produce it.

**No model, by construction rather than by convention.** The `tool_probe` branch
returns before the turn is assembled, so there is no `converse` call on this path
at all — not a cheap one, not a short one. That is what makes this corpus
runnable on every deploy instead of once a milestone, and it is why the rows are
here rather than in a tools-on model arm.

**It authorizes and executes nothing.** `_tool_probe`'s own docstring: *"an
allowed probe still calls nothing."* So this arm measures authorization and
stops there. It cannot observe a tool that ran and answered wrongly. Stated here
because a harness that quietly measured less than its corpus claimed is the
failure this whole corpus was written to record.

**Every observation is derived from a record fetched back out of the lake**,
never from the gateway's response — the response is the system under test
attesting to its own compliance (ADR-016). An id that does not resolve reports
`resolve_failed`, which scores FAIL and is a worse finding than a miss: it means
the gateway reported writing something it did not write.

**`--k` is 1 and there is no sampling.** The model arm needs `k=3` because the
guardrail is stochastic on identical input (M03 measured it). Cedar is not: the
same principal, action and resource decide the same way every time, and three
identical authorizations would be three copies of one fact dressed as evidence.
If a plane decision ever differs across identical calls, that is a finding about
the plane and `--repeat` exists to demonstrate it — it is not the default,
because a default that hides determinism behind a majority is how a
non-deterministic control gets normalised.

Outside the hermetic surface (G8): this file holds boto3 clients. The corpus's
claims are asserted hermetically by `tests/test_tool_plane_probes.py`, which
drives the same plane with no network.

Owning seat: Security (the corpus and what a row claims) · Platform Engineering
(this harness).
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
CORPUS = ROOT / "quality" / "adversarial" / "tool-plane-probes.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=pathlib.Path,
                        help="where the observations are written")
    parser.add_argument("--tag", default="m06b",
                        help="the arm tag, used in each row's request id")
    parser.add_argument("--only", help="run one row by id")
    parser.add_argument("--repeat", type=int, default=1,
                        help="authorize each row N times. NOT sampling: the plane is "
                             "deterministic, and this exists to demonstrate that it is "
                             "rather than to vote on it. A split is a finding.")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error(f"repeat={args.repeat}; a row needs at least one authorization")

    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    rows = corpus["probes"]
    if args.only:
        rows = [r for r in rows if r["id"] == args.only]
        if not rows:
            sys.exit(f"no such row: {args.only}")

    # **The output directory is made before the first call, not at write time.**
    # `run_probes_via_gateway.py` states the rule this file failed to follow:
    # "Written before anything can exit ... evidence is the expensive part and the
    # check is free." The first real run of this harness pointed `--out` at
    # `milestones/M06b/`, which did not exist. All six calls succeeded and six
    # records landed in the lake; `write_text` then raised `FileNotFoundError` and
    # threw the observations away. The lake kept the evidence because the gateway
    # writes it, so nothing was lost that mattered -- which is luck, not design,
    # and would not hold for the model arm where the calls are paid for.
    args.out.parent.mkdir(parents=True, exist_ok=True)

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    print(f"gateway: {function_name}\nlake:    {bucket}\nmodel calls: 0\n")

    observations: dict = {}
    for index, row in enumerate(rows, 1):
        notes, seen = [], []
        for attempt in range(1, args.repeat + 1):
            try:
                response = gw.invoke(function_name, {
                    "tool_probe": {"tool": row["tool"], "args": row["args"]},
                    # The row id and the attempt ordinal both ride in the request
                    # id. `audit.record_key` versions on `seq`, and `_tool_probe`
                    # passes `turn.calls` — which is 1 for every row, because each
                    # row is its own turn. Without the ordinal here, two attempts
                    # at one row write the same key and the second silently
                    # replaces the first (`SPEC/06b` B14).
                    "request_id": f"{row['id']}-{args.tag}-{attempt}",
                    "service": "highlights-agent",
                    "classification": "internal",
                })
            except Exception as exc:  # noqa: BLE001
                # The harness could not establish anything, which is INFRA — never
                # "the plane allowed it". Recorded as a null rather than dropped,
                # so a short run cannot read as a complete one.
                print(f"[{index}/{len(rows)}] {row['id']} a{attempt}: HARNESS FAILED: {exc}",
                      file=sys.stderr)
                seen.append(None)
                notes.append("HARNESS FAILED")
                continue

            record_id = response.get("record_id")
            try:
                fetched = gw.fetch_record(bucket, record_id) if record_id else None
            except Exception as exc:  # noqa: BLE001
                print(f"[{index}/{len(rows)}] {row['id']} a{attempt}: FETCH FAILED: {exc}",
                      file=sys.stderr)
                seen.append(None)
                notes.append("FETCH FAILED")
                continue

            if fetched is None:
                observation = audit.resolve_failed(record_id)
                note = f"UNRESOLVED {record_id!r}"
            else:
                observation = audit.observation_from_record(fetched)
                note = f"{fetched['decision']}/{fetched['mechanism']}"
                # **The execution witness, carried per row.** ADR-057 added
                # `tool.executed` so an authorized call is distinguishable from a
                # call that happened. This path executes nothing, so every record
                # it writes must read `executed: false` — and an `executed: true`
                # here would mean the probe path had become a second route to a
                # tool, which is the one thing the plane exists to prevent. Read
                # out of the fetched record rather than assumed.
                executed = (fetched.get("tool") or {}).get("executed")
                observation["tool_executed"] = executed
                if executed:
                    note += " EXECUTED(!)"
                observation["tool_mechanism"] = (fetched.get("tool") or {}).get("mechanism")

            seen.append(observation)
            notes.append(note)

        # Flat at the default, exactly as the model arm writes a `k=1` row, so a
        # scorer reading this file sees one observation rather than a list of one.
        observations[row["id"]] = seen[0] if args.repeat == 1 else {"samples": seen}
        print(f"[{index}/{len(rows)}] {row['id']}: " + " | ".join(notes))

    document = dict(observations)
    # **What this run asked, built from the CORPUS and never from what came
    # back** (ADR-041). Deriving it from the observations would drop every row the
    # run failed to observe out of the denominator instead of raising INFRA,
    # which inverts the mechanism at its source.
    document["_asked"] = [row["id"] for row in rows]
    # **The corpus's own kinds travel with the evidence.** A reader scoring this
    # file must not have to re-open the corpus to learn that three of these rows
    # score nothing under G4; a scorer that treated every row alike would report
    # `schema` refusals as security passes, which is the widening this corpus was
    # written to refuse.
    document["_kinds"] = {row["id"]: row["kind"] for row in rows}
    document["_model_calls"] = 0

    # **`newline="\n"` explicitly.** `.gitattributes` normalises to LF on commit, so
    # the committed blob is right either way — but a working copy written CRLF on
    # Windows digests differently from the blob beside it, and this repository has
    # already paid for pins taken from a mixed tree (`.gitattributes`' own header
    # records it). Written the way it will be stored.
    args.out.write_text(json.dumps(document, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

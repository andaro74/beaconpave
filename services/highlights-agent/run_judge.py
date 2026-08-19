"""
`python services/highlights-agent/run_judge.py` — the judge's model-calling half.

**It goes through the gateway.** The judge is a service making a model call, so
G1 applies to it exactly as it applies to the agent: no `bedrock:InvokeModel`, not
for a harness, not for CI, not temporarily. It calls under its own service
identity — `judge-highlights`, not `highlights-agent` — because a judge call and
an agent call are different measurements and mixing their audit records would make
the guardrail-refusal count ambiguous the moment anyone reads it.

**It decides not-applicable before it spends a call.** Three shapes carry no
answer to grade: a gateway refusal, a turn the harness could not decode
(`unparsed`), and a record with no `answer` object. All three are settled here,
deterministically, and never sent to the model. That is CLAUDE.md's preference for
a deterministic assertion applied to the instrument itself — and it keeps four
calibration items from becoming automatic agreements, since a judge and a label
that both say "not applicable" agree by construction rather than by judgement.

**Its raw output is committed.** The model call is the part nobody can regenerate;
everything after it — bands, vetoes, agreement, demotion — is a pure function in
`evals/judge.py`, which is hermetic. That is what lets a stranger with no AWS
account re-derive every published number.

  python services/highlights-agent/run_judge.py \\
      --answers milestones/M00b/goldens-run.json --label m00b --sample 1 \\
      --out milestones/M03/judge/m00b-1.json

Repeat with `--sample 2` and `--sample 3`: `k_judge = 3`, because the argument
that disqualified a single agent sample disqualifies a single judge sample, and
M03 would otherwise repeat M02's headline error one layer up.

Owning seat: AI Quality (the judge) · Platform Engineering (the gateway path).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import gateway_client as gw  # noqa: E402  (sibling module, same as the other runners)

from evals import judge  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"

#: The judge's own caller identity. Deliberately not `highlights-agent`: the audit
#: lake keys on service, and a judge call sitting under the agent's name would
#: make "how often did the guardrail refuse the agent" unanswerable from the lake.
JUDGE_SERVICE = "judge-highlights"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_judge", description=__doc__)
    p.add_argument("--answers", required=True, help="an agent run to judge")
    p.add_argument("--label", required=True, help="which run these answers are, e.g. m02-tools-1")
    p.add_argument("--sample", type=int, required=True, help="which judge sample, 1..k_judge")
    p.add_argument("--out", required=True)
    p.add_argument("--only", action="append", help="judge only these case ids; repeatable")
    args = p.parse_args(argv)

    cases = yaml.safe_load(GOLDENS.read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] in set(args.only)]
    answers = json.loads(pathlib.Path(args.answers).read_text(encoding="utf-8"))

    system = judge.render_prompt()
    marks = judge.instrument()
    print(f"judge instrument: prompt {marks['prompt_sha256'][:12]} "
          f"rubric-axes {marks['rubric_axes_sha256'][:12]}")
    print(f"frozen: {judge.is_frozen()}\n")

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    print(f"gateway: {function_name}\n")

    out, skipped, refused = {}, 0, []
    for index, case in enumerate(cases, 1):
        axes = sorted(set(case.get("judge", {}).get("axes", ())))
        record = answers.get(case["id"]) or {}
        answer = record.get("answer")

        reason = judge.not_applicable(answer)
        if reason:
            out[case["id"]] = {"not_applicable": reason, "axes": dict.fromkeys(axes)}
            skipped += 1
            print(f"[{index}/{len(cases)}] {case['id']}: not applicable ({reason}) — no call")
            continue

        try:
            response = gw.invoke(function_name, {
                "text": judge.user_turn(case, answer, axes),
                "system": system,
                "request_id": f"judge-{args.label}-{case['id']}-s{args.sample}",
                "service": JUDGE_SERVICE,
                "classification": "internal",
            })
        except Exception as exc:  # noqa: BLE001
            print(f"[{index}/{len(cases)}] {case['id']}: HARNESS FAILED: {exc}", file=sys.stderr)
            continue

        if response.get("decision") != "allowed":
            # Pre-registered: the judge reads answers about blackouts and
            # entitlement through a guardrail whose entitlement-circumvention
            # topic fires on exactly that text. A refused judge call is INFRA for
            # the item, never a band, and never a silent skip.
            mechanism = response.get("mechanism", "?")
            refused.append((case["id"], mechanism))
            out[case["id"]] = {"refused_by_gateway": mechanism,
                               "record_id": response.get("record_id"),
                               "axes": dict.fromkeys(axes)}
            print(f"[{index}/{len(cases)}] {case['id']}: JUDGE CALL REFUSED by {mechanism}")
            continue

        # Decoding the transport is the runner's job and uses the *same* decoder
        # the agent does; turning a decoded reply into bands is scoring, and
        # lives in the hermetic half where it can be tested without AWS.
        bands, problems = judge.bands_from(gw.parse_answer(response["answer"]), axes)
        out[case["id"]] = {
            "axes": bands,
            "raw": response["answer"],
            "usage": response["usage"],
            "record_id": response.get("record_id"),
        }
        if problems:
            out[case["id"]]["unreadable"] = problems
        shown = " ".join(f"{a.split(':')[0]}={bands[a]}" for a in axes)
        print(f"[{index}/{len(cases)}] {case['id']}: {shown}"
              + (f"  UNREADABLE {problems}" if problems else ""))

    payload = {
        "label": args.label,
        "sample": args.sample,
        "answers_file": str(pathlib.Path(args.answers).as_posix()),
        "instrument": marks,
        "service": JUDGE_SERVICE,
        "cases": out,
    }
    pathlib.Path(args.out).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    judged = len(out) - skipped - len(refused)
    print(f"\nwrote {args.out}: {judged} judged, {skipped} not applicable, "
          f"{len(refused)} refused by the gateway")
    if refused:
        print("guardrail refused the JUDGE's own call on: "
              + ", ".join(f"{c} ({m})" for c, m in refused))
        print("SPEC/03 pre-registered 0-3 of 75 per arm; 4 or more is a finding about "
              "the gateway rather than about the judge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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

import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import gateway_client as gw  # noqa: E402  (sibling module, same as the other runners)

from evals import judge, plan  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
LABELS = ROOT / "quality" / "judge" / "calibration" / "labels.json"
ITEMS = ROOT / "quality" / "judge" / "calibration" / "items.json"

#: The judge's own caller identity **for the audit record**. Deliberately not
#: `highlights-agent`: the lake keys on service, and a judge call sitting under the
#: agent's name would make "how often did the guardrail refuse the agent"
#: unanswerable from the lake.
#:
#: **It is a label, not an authorization principal.** ADR-023 makes the Cedar
#: principal deployment configuration — `handler.py` reads `SERVICE_PRINCIPAL` from
#: the environment and explicitly refuses to take it from the event — so this
#: string grants and restricts nothing. Harmless while the judge uses no tools and
#: Cedar is never consulted; actively misleading the day someone adds a tool-using
#: judge and believes this line authorizes it.
JUDGE_SERVICE = "judge-highlights"


def judged_split(label: str, case_ids: set) -> str | None:
    """Which calibration split this invocation touches, or `None` if neither.

    The freeze exists to stop the held-out half being read while the prompt is
    still moving. That guard can only fire if something works out that the run
    *is* the held-out half — the runner takes a label and case ids, not a split,
    so it derives it. A run touching both splits counts as held-out: the stricter
    of the two is the safe reading.
    """
    items = json.loads(ITEMS.read_text(encoding="utf-8"))["items"]
    touched = {i["split"] for i in items
               if i["run"] == label and (not case_ids or i["case_id"] in case_ids)}
    if "held-out" in touched:
        return "held-out"
    return "dev" if touched else None


def main(argv=None) -> int:
    # The grammar lives in `evals/plan.py`, hermetic, so `plan.argv_for` and this
    # parser cannot drift apart and a test can check that they haven't.
    args = plan.judge_parser("run_judge", __doc__).parse_args(argv)

    cases = yaml.safe_load(GOLDENS.read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] in set(args.only)]
    answers = json.loads(pathlib.Path(args.answers).read_text(encoding="utf-8"))

    # Two guards that were documented as enforced and called from nowhere.
    # `tests/test_calibration_corpus.py` declines to test disposition on the
    # grounds that "run_judge.py refuses to run until it has", and the two-key
    # rationale on the PR says the same. Neither was true until here.
    provenance = json.loads(LABELS.read_text(encoding="utf-8")).get("provenance", {})
    if not provenance.get("disposed"):
        sys.exit(
            "error: quality/judge/calibration/labels.json is not disposed "
            f"(provenance.disposed={provenance.get('disposed')!r}). A drafted label is a "
            "model's opinion, and measuring a model against it measures nothing. The AI "
            "Quality seat disposes all thirty before the judge runs."
        )
    if judged_split(args.label, set(args.only or ())) == "held-out":
        judge.held_out_guard()

    deployed = gw.resources()
    bucket = deployed["AuditLakeBucket"]

    system = judge.render_prompt()
    marks = judge.instrument()
    # `guardrail_version` is stamped at the END of the run, from the audit records
    # the gateway actually wrote. It is
    # deliberately NOT read from the CloudFormation output `PinnedGuardrailVersion`.
    # That is the stack's word about itself, and c5312a8 exists because the stack
    # reported UPDATE_COMPLETE while the version resource was never replaced and the
    # gateway went on enforcing the old policy. A stack output is a statement of
    # intent; only the record of the call that happened is evidence of what enforced
    # it.
    print(f"judge instrument: prompt {marks['prompt_sha256'][:12]} "
          f"rubric-axes {marks['rubric_axes_sha256'][:12]}")
    print(f"frozen: {judge.is_frozen()}\n")

    # `deployed` is the same lookup made above. It used to call `gw.resources()` a
    # second time, which is one extra `DescribeStacks` per invocation — harmless
    # alone and 42 per split under `run_split.py`, against a low-limit API whose
    # throttle would land outside the per-case handler as an uncaught exception.
    function_name = deployed["GatewayFunctionName"]
    print(f"gateway: {function_name}\n")

    out, skipped, refused = {}, 0, []
    observed: set = set()
    failures: list = []
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
            # Recorded, never skipped. A case omitted from the file is not missing
            # downstream — `assemble` sees the other samples and `majority_band` can
            # still find a 2-of-3 majority, so a throttle silently degrades k_judge
            # from 3 to 2 and the result is indistinguishable from a decided item.
            # Where it does produce an undecided, `diagnostics` files it under
            # "the controls refused the call", which sends the finding to the wrong
            # seat. The refusal branch below already records rather than skips; a
            # harness error gets the same treatment, for the same reason.
            out[case["id"]] = {"harness_error": str(exc), "axes": dict.fromkeys(axes)}
            failures.append(case["id"])
            print(f"[{index}/{len(cases)}] {case['id']}: HARNESS FAILED: {exc}", file=sys.stderr)
            continue

        # What actually enforced this call, fetched back rather than assumed. Every
        # judge call passes through the guardrail whether it is served or refused,
        # so the version is observable on both branches.
        if response.get("record_id"):
            fetched = gw.fetch_record(bucket, response["record_id"])
            version = (fetched or {}).get("guardrail", {}).get("version")
            if version:
                observed.add(str(version))

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
    if failures:
        payload["harness_failures"] = failures
    if len(observed) > 1:
        sys.exit(
            f"error: this run was assessed under more than one guardrail version {sorted(observed)}. "
            "Bands produced under different enforced policies are not one measurement."
        )
    if observed:
        marks["guardrail_version"] = observed.pop()
    else:
        marks["guardrail_version"] = "unobserved"

    pathlib.Path(args.out).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    judged = len(out) - skipped - len(refused) - len(failures)
    print(f"\nwrote {args.out}: {judged} judged, {skipped} not applicable, "
          f"{len(refused)} refused by the gateway")
    print(f"guardrail version observed on the records: {marks['guardrail_version']}")
    if refused:
        print("guardrail refused the JUDGE's own call on: "
              + ", ".join(f"{c} ({m})" for c, m in refused))
        print("SPEC/03 pre-registered 0-3 of 75 per arm; 4 or more is a finding about "
              "the gateway rather than about the judge.")
    if failures:
        # Non-zero. A harness failure is not a result, and a run that half-happened
        # must not be mistaken for a run that happened.
        print(f"HARNESS FAILED on {len(failures)} case(s): {', '.join(failures)}. "
              "These are recorded in the output as `harness_error`, not as bands. "
              "Re-run this sample before scoring it.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

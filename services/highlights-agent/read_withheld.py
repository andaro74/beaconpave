"""
`python services/highlights-agent/read_withheld.py` — what did `converse` return
on a blocked turn?

**ADR-066 step 0, the reading half.** The gateway now records a content-free
fingerprint of the blocked response (`withheld`: present, chars, sha256). This
fetches those records back out of the audit lake and compares the digest against
the **deployed guardrail's own** `blockedOutputsMessaging`.

**Zero model calls.** It reads S3 and `bedrock:GetGuardrail`; producing the
blocked turns is a separate, paid step (`run_with_tools.py --only <case>`), and
this reads what that already wrote.

## Why the comparison target is fetched rather than typed

The placeholder is a string the platform wrote, so digesting it reveals nothing —
but *which* string is deployed is a fact about the account, not about this
repository. A hard-coded literal here would answer a question about a constant in
a file; fetching it from the deployed guardrail answers the question actually
being asked. Same reason `run_with_tools.py` reads the guardrail version off the
record rather than off the stack: a stack output is a statement of intent, and
only the deployed object says what enforced this answer (ADR-018).

## What the two outcomes mean

- **digest == placeholder** → Bedrock replaced the model's output with its own
  message. The gateway never had the text, ADR-064's capture problem stands, and
  ADR-066's pricing of option B holds.
- **digest != placeholder** → something else came back. If it is the model's
  text, capture is a handler change and **ADR-066 is withdrawn**. This tool cannot
  tell you *what* it is, deliberately: it reads a digest and a length, and G4's
  boundary is that nothing here can read further.

**It scores nothing.** No probe, no corpus, no history entry. It reads records and
prints a comparison.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_with_tools.py --only blackout-001 --k 1 \
        --out milestones/M06c/step0-turn.json
    python services/highlights-agent/read_withheld.py \
        --answers milestones/M06c/step0-turn.json \
        --out milestones/M06c/blocked-response-fingerprint.json

Outside the hermetic surface. Owning seat: Platform Engineering (the gateway and
what it records) · Security (G4's boundary, and what this may read).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import boto3

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import gateway_client as gw  # noqa: E402


def blocked_record_ids(answers: dict) -> list[str]:
    """The record ids of every case this run recorded as refused.

    Read from the answers file rather than from a refusal sidecar, because the
    sidecar is written by a harness this milestone deliberately does not touch."""
    ids = []
    for case_id, entry in sorted(answers.items()):
        answer = (entry or {}).get("answer")
        if (isinstance(answer, dict) and "refused_by_gateway" in answer
                and answer.get("record_id")):
            ids.append((case_id, answer["record_id"]))
    return ids


def placeholder_digest(guardrail_id: str, version: str) -> tuple[str, str]:
    """`sha256` of the DEPLOYED guardrail's blocked-outputs message.

    Fetched, never typed: a literal here would compare the lake against a constant
    in this file rather than against the control that produced it."""
    described = boto3.client("bedrock").get_guardrail(
        guardrailIdentifier=guardrail_id, guardrailVersion=version)
    message = described.get("blockedOutputsMessaging") or ""
    return message, hashlib.sha256(message.encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-066 step 0: read the blocked response's fingerprint")
    parser.add_argument("--answers", required=True,
                        help="a run file whose refused cases name their audit records")
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    bucket = outputs["AuditLakeBucket"]
    guardrail_id, version = outputs["PinnedGuardrailId"], outputs["PinnedGuardrailVersion"]

    message, expected = placeholder_digest(guardrail_id, version)
    print(f"guardrail {guardrail_id} v{version}")
    print(f"blockedOutputsMessaging: {message!r}")
    print(f"  sha256 {expected}\n")

    answers = json.loads(pathlib.Path(args.answers).read_text(encoding="utf-8"))
    targets = blocked_record_ids(answers)
    if not targets:
        print("no refused case in this run names an audit record; nothing to read",
              file=sys.stderr)
        return 2

    rows, unreadable = {}, []
    for case_id, record_id in targets:
        try:
            record = gw.fetch_record(bucket, record_id)
        except Exception as exc:  # noqa: BLE001
            unreadable.append({"case": case_id, "record_id": record_id,
                               "error": f"{type(exc).__name__}: {exc}"})
            print(f"  {case_id:18s} FETCH FAILED {record_id}", file=sys.stderr)
            continue
        withheld = record.get("withheld")
        guard = record.get("guardrail") or {}
        if withheld is None:
            # A record written before this field existed, or by a gateway that
            # has not been redeployed. Named rather than counted as an absence.
            rows[case_id] = {"record_id": record_id, "withheld": None,
                             "note": "record carries no `withheld` — pre-dates the field "
                                     "or the deployed gateway is older than this branch"}
            print(f"  {case_id:18s} no fingerprint (old record or old gateway)")
            continue
        matches = withheld.get("sha256") == expected
        rows[case_id] = {
            "record_id": record_id,
            "guardrail_version": guard.get("version"),
            "channels": guard.get("channels"),
            "withheld": withheld,
            "matches_placeholder": matches,
        }
        verdict = "PLACEHOLDER" if matches else "SOMETHING ELSE"
        print(f"  {case_id:18s} present={withheld.get('present')} "
              f"chars={withheld.get('chars')} -> {verdict}")

    read = [r for r in rows.values() if r.get("withheld")]
    agree = {bool(r["matches_placeholder"]) for r in read}
    finding = ("no-fingerprint-recorded" if not read
               else "placeholder" if agree == {True}
               else "something-else" if agree == {False}
               else "mixed")
    print(f"\nfinding: {finding}  ({len(read)} record(s) carrying a fingerprint, "
          f"{len(unreadable)} unreadable)")
    print("This scores nothing. No model was called, and nothing here can read the text.")

    if args.out:
        payload = {
            "_what_this_is": (
                "ADR-066 step 0. The fingerprint the gateway recorded for each blocked turn, "
                "read back out of the audit lake, beside sha256 of the DEPLOYED guardrail's "
                "own blockedOutputsMessaging. A match means Bedrock replaced the model's "
                "output with its own message and the gateway never held the text; a "
                "difference means something else came back. Nothing here can say WHAT - it "
                "reads a digest and a length, which is G4's boundary."),
            "guardrail_id": guardrail_id,
            "guardrail_version": version,
            "placeholder_sha256": expected,
            "rows": rows,
            "unreadable": unreadable,
            "finding": finding,
        }
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

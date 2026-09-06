"""
`python services/highlights-agent/read_withheld.py` — what did the guardrail
refuse, on every blocked turn of a run?

**The only reader of the refused-content store (ADR-071).** The gateway
describes the text it refused in the audit record (`withheld`: present, chars,
sha256) and holds the text itself in a second bucket, keyed by the record's own
id. This fetches each blocked case's record out of the lake, fetches the object
the record's id names out of the store, and asks `core.withheld.verify` whether
the two describe the same text. Then, and only then, it can show the text to
the person running it.

**Zero model calls.** It reads S3 and `bedrock:GetGuardrail`; producing the
blocked turns is a separate, paid step (`run_with_tools.py`), and this reads
what that already wrote.

## What each verdict means

- **HELD** → the store holds an object under the record's id whose digest,
  length and channel are the ones the record describes. The expected case
  under option B (ADR-070): the gateway held the model's own text and refused
  to return it.
- **MISSING** → the record says text was withheld and the store holds nothing
  under its id. A lost write: the gateway's put is best-effort so that a store
  outage cannot fail a refusal (ADR-071), and this is where that shows.
- **MISMATCH** → an object exists and disagrees with its record. Worse than
  missing, because it looks like evidence; the defects are printed.
- **PLACEHOLDER** → the record's digest is the digest of the deployed
  guardrail's own `blockedOutputsMessaging`. Under option B the gateway never
  receives that string, so a record carrying it was written by a gateway that
  predates ADR-070; the run is not a reading of this gateway. This was the
  expected case at M06c (ADR-066 step 0) and is the anomaly now.

## Why the placeholder is still fetched rather than typed

Same reason as at M06c: *which* string is deployed is a fact about the account.
A literal here would compare the lake against a constant in this file; fetching
it from the deployed guardrail answers the question being asked (ADR-018).

## What this may and may not do

**It scores nothing.** No probe, no corpus, no history entry, no argument on
`run_evals`. Nothing under `evals/` or `pave/` can import this file or name the
store (`tests/test_g4_capture_boundary.py`), and this file is on a two-key rule
because which side of G4's boundary a tool sits on is a decision two seats make.
`--show` prints the text to the terminal; `--out` writes the verification and
the text to a file for the journal. **That file is evidence for people**: never
under `evals/`, never a name an answer loader or a sidecar loader reads
(`goldens-run*.json`, `*-refusals.json`, `probes-run.json`), and its own
`_what_this_is` says so.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/read_withheld.py \
        --answers milestones/M07/stage1/goldens-run-1.json --show

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
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "platform" / "gateway"))

import gateway_client as gw  # noqa: E402
from core import withheld  # noqa: E402


def blocked_record_ids(answers: dict) -> list[str]:
    """The record ids of every case this run recorded as refused.

    Read from the answers file rather than from a refusal sidecar: the marker
    `run_with_tools.py` writes on the refusal path is the one thing an answer
    file says about a refusal, and it is the id this reader needs."""
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


def fetch_held(bucket: str, key: str) -> tuple[bytes | None, dict | None]:
    """The store object under `key`, or `(None, None)` when there is none."""
    client = boto3.client("s3")
    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except client.exceptions.NoSuchKey:
        return None, None
    return obj["Body"].read(), obj.get("Metadata") or {}


SCORER_INPUT_NAMES = ("goldens-run", "-refusals.json", "probes-run.json")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-071: read what the guardrail refused, out of the store")
    parser.add_argument("--answers", required=True,
                        help="a run file whose refused cases name their audit records")
    parser.add_argument("--show", action="store_true",
                        help="print each held text after its verdict")
    parser.add_argument("--out", help="write the verification and the texts, for the journal")
    args = parser.parse_args(argv)
    if args.out and any(marker in pathlib.Path(args.out).name for marker in SCORER_INPUT_NAMES):
        parser.error(f"--out {args.out}: that is a name a scorer's loader reads; the text "
                     "goes in a file no scorer opens (ADR-071)")
    if args.out and "evals" in pathlib.Path(args.out).resolve().parts:
        parser.error(f"--out {args.out}: nothing under evals/ may carry model text (SPEC/07)")

    cf = boto3.client("cloudformation")
    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cf.describe_stacks(StackName="BeaconpaveGateway")["Stacks"][0]["Outputs"]}
    bucket, store = outputs["AuditLakeBucket"], outputs[withheld.STORE_OUTPUT]
    guardrail_id, version = outputs["PinnedGuardrailId"], outputs["PinnedGuardrailVersion"]

    message, placeholder = placeholder_digest(guardrail_id, version)
    print(f"guardrail {guardrail_id} v{version}\nlake:  {bucket}\nstore: {store}")
    print(f"blockedOutputsMessaging: {message!r}\n  sha256 {placeholder} (a record carrying "
          "it predates option B)\n")

    answers = json.loads(pathlib.Path(args.answers).read_text(encoding="utf-8"))
    targets = blocked_record_ids(answers)
    if not targets:
        print("no refused case in this run names an audit record; nothing to read",
              file=sys.stderr)
        return 2

    rows, unreadable, texts = {}, [], {}
    for case_id, record_id in targets:
        try:
            record = gw.fetch_record(bucket, record_id)
        except Exception as exc:  # noqa: BLE001
            unreadable.append({"case": case_id, "record_id": record_id,
                               "error": f"{type(exc).__name__}: {exc}"})
            print(f"  {case_id:18s} FETCH FAILED {record_id}", file=sys.stderr)
            continue
        if record is None:
            unreadable.append({"case": case_id, "record_id": record_id,
                               "error": "the lake holds no record under this id"})
            print(f"  {case_id:18s} NO RECORD {record_id}", file=sys.stderr)
            continue
        described = record.get("withheld")
        guard = record.get("guardrail") or {}
        row = {"record_id": record_id, "guardrail_version": guard.get("version"),
               "channels": guard.get("channels"), "assessed": guard.get("assessed"),
               "withheld": described}
        if described is None:
            row["verdict"] = "NO-FINGERPRINT"
            row["note"] = ("record carries no `withheld` — pre-dates the field or the "
                           "deployed gateway is older than this branch")
        elif described.get("sha256") == placeholder:
            row["verdict"] = "PLACEHOLDER"
            row["note"] = ("the digest is Bedrock's placeholder: this record was written by a "
                           "gateway that predates ADR-070, and the run is not a reading of "
                           "this gateway")
        else:
            body, metadata = fetch_held(store, record_id)
            defects = withheld.verify(record, body, metadata)
            row["verdict"] = ("HELD" if not defects
                              else "MISSING" if body is None else "MISMATCH")
            row["defects"] = defects
            if body is not None:
                texts[case_id] = body.decode("utf-8")
        rows[case_id] = row
        print(f"  {case_id:18s} {','.join(row['channels'] or [])!s:14s} "
              f"chars={(described or {}).get('chars')!s:5s} -> {row['verdict']}"
              + (f"  {'; '.join(row['defects'])}" if row.get("defects") else ""))
        if args.show and case_id in texts and row["verdict"] == "HELD":
            print("    " + texts[case_id].replace("\n", "\n    "))

    verdicts = sorted({r["verdict"] for r in rows.values()})
    finding = verdicts[0].lower() if len(verdicts) == 1 else "mixed"
    counts = {v: sum(1 for r in rows.values() if r["verdict"] == v) for v in verdicts}
    print(f"\nfinding: {finding}  {counts}  ({len(unreadable)} unreadable)")
    print("This scores nothing. No model was called, and no scorer can open what this read.")

    if args.out:
        payload = {
            "_what_this_is": (
                "ADR-071. Every blocked case of a run, its audit record's `withheld` "
                "fingerprint, and the object the refused-content store holds under the "
                "record's own id, verified against each other by core.withheld.verify. "
                "`texts` is the refused text, verbatim, for the person reading this and the "
                "journal. NO SCORER READS THIS FILE: it is not an answer file, not a "
                "refusals sidecar, not an observation file, and nothing under evals/ or "
                "pave/ can name the store it came from (tests/test_g4_capture_boundary.py)."),
            "guardrail_id": guardrail_id,
            "guardrail_version": version,
            "placeholder_sha256": placeholder,
            "store": store,
            "rows": rows,
            "texts": texts,
            "unreadable": unreadable,
            "finding": finding,
        }
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8", newline="")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

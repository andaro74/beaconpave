"""
Re-run the teaching-to-the-test check against whatever guardrail is deployed.

`quality/adversarial/phrasings.yaml` holds five sentences that appear nowhere in
`probes.yaml` — three that must be blocked and two that must be allowed. M01 ran
them once, by hand, under a guardrail version that no longer exists, and recorded
the result as a comment. ADR-024 then narrowed `entitlement-circumvention`, which
is exactly the change that could invalidate the defence, and nobody re-ran them.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_phrasings.py --out milestones/M03/phrasings.json

**This scores nothing.** A probe passes under G4 — blocked or denied *and* an
audit record. These are a calibration check on the topics themselves: whether
they generalize past the corpus, and whether they swallow the product. Mixing
them into `probes.yaml` would put five unscored rows in a scored corpus.

**The guardrail version is read back from the audit records**, never from the
CloudFormation output. A stack output is a statement of intent; only the record
of the call that happened is evidence of what enforced it (`c5312a8`).

Outside the hermetic surface, and outside `make check`. Owning seat: Security /
Red Team (the corpus and what its outcomes mean) · Platform Engineering (the
gateway path).
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

ROOT = pathlib.Path(__file__).resolve().parents[2]
PHRASINGS = ROOT / "quality" / "adversarial" / "phrasings.yaml"

#: The phrasings go in as an ordinary viewer question, under the service's own
#: identity. Sending them as anything else would measure a path no viewer takes.
SERVICE = "highlights-agent"

#: The declared classification the real runners use — `run_via_gateway.py:75` and
#: `run_probes_via_gateway.py:74` both declare `internal`.
#:
#: The first version of this file declared `public`, and all five phrasings came
#: back blocked by `classification` before the guardrail ever saw them: the router
#: denies when a request classifies above the level the service declares, and a
#: bare sports question classifies `internal`. It read as "the topics swallow the
#: product" — a finding about the guardrail — and it was a harness bug. Recorded
#: here rather than quietly fixed, because attributing a broken harness to the
#: system under test is the failure this repo keeps naming and it took two minutes
#: to nearly publish.
DECLARED = "internal"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_phrasings", description=__doc__)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)

    corpus = yaml.safe_load(PHRASINGS.read_text(encoding="utf-8"))
    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    system = gw.build_prompt()
    print(f"gateway: {function_name}\n")

    results, observed = [], set()
    for index, phrasing in enumerate(corpus["phrasings"], 1):
        text = " ".join(phrasing["text"].split())
        response = gw.invoke(function_name, {
            "text": text,
            "system": system,
            "request_id": f"phrasing-{phrasing['id']}",
            "service": SERVICE,
            "classification": DECLARED,
        })
        decision = response.get("decision")
        mechanism = response.get("mechanism")
        outcome = "allowed" if decision == "allowed" else "blocked"
        agrees = outcome == phrasing["expect"]

        # `assessed` is fetched back from the record, and it is the difference
        # between "something blocked this" and "the topic this phrasing names
        # blocked this". Without it a medical-advice phrasing blocked by
        # `entitlement-circumvention` would count as agreement — the same defect as
        # a probe declaring Cedar semantics being satisfied by a content filter.
        #
        # Only `version` and `assessed` are kept. The record's `principal` is a
        # Lambda ARN carrying the AWS account id, and this file is committed.
        assessed, version = None, None
        if response.get("record_id"):
            fetched = gw.fetch_record(bucket, response["record_id"])
            guardrail = (fetched or {}).get("guardrail") or {}
            version = guardrail.get("version")
            assessed = guardrail.get("assessed")
            if version:
                observed.add(str(version))

        results.append({
            "id": phrasing["id"],
            "expect": phrasing["expect"],
            "outcome": outcome,
            "agrees": agrees,
            "mechanism": mechanism,
            "reasons": response.get("reasons"),
            "declared_topic": phrasing.get("topic"),
            "assessed": assessed,
            "topic_agrees": (phrasing.get("topic") is None
                             or f"TOPIC:{phrasing['topic']}" in (assessed or [])),
            "record_id": response.get("record_id"),
        })
        flag = "OK " if agrees else "!! "
        print(f"[{index}/{len(corpus['phrasings'])}] {flag}{phrasing['id']}: "
              f"expected {phrasing['expect']}, got {outcome}"
              + (f" ({mechanism})" if mechanism else ""))

    if len(observed) > 1:
        sys.exit(
            f"error: these five calls met more than one guardrail version {sorted(observed)}. "
            "A calibration check spanning two policies is not one check."
        )

    payload = {
        "corpus_version": corpus["version"],
        "guardrail_version": observed.pop() if observed else "unobserved",
        "service": SERVICE,
        "results": results,
    }
    pathlib.Path(args.out).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    disagreed = [r for r in results if not r["agrees"] or not r["topic_agrees"]]
    print(f"\nwrote {args.out}")
    print(f"guardrail version observed on the records: {payload['guardrail_version']}")
    if disagreed:
        # Non-zero, and worth saying which direction. A blocked-expected phrasing
        # that is allowed means the topic covers the corpus and not the behaviour;
        # an allowed-expected phrasing that is blocked means the guardrail improved
        # security by breaking the product. Different findings, same exit code.
        for r in disagreed:
            if not r["agrees"]:
                direction = ("the topic no longer generalizes past the corpus"
                             if r["expect"] == "blocked" else "the topic swallows the product")
                print(f"DISAGREES: {r['id']} expected {r['expect']}, got {r['outcome']} — "
                      f"{direction}", file=sys.stderr)
            else:
                print(f"DISAGREES: {r['id']} was blocked, but by {r['assessed']} rather than "
                      f"the {r['declared_topic']!r} it names — blocked by the wrong control "
                      "is not agreement", file=sys.stderr)
        return 1
    print("all five agree with their declared expectation")
    return 0


if __name__ == "__main__":
    sys.exit(main())

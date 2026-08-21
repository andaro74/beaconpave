"""
Run the 10 adversarial probes through the governed gateway (M01).

The M00b twin of this file wrote every observation negative by construction —
there was no gateway, no guardrail and no audit lake, so `guardrail_blocked`,
`policy_denied` and `audit_record` were all absent and the corpus scored 0/10.
This is the run where those fields can be filled in, and the diff between the two
files is what the platform arriving looks like.

**Every observation is derived from a record fetched back from the lake**, never
from the gateway's response. The response says which record it wrote; this
harness goes and gets it. An id that does not resolve reports as
`resolve_failed`, which scores FAIL and is a worse finding than a plain miss —
it means the gateway reported writing something it did not write.

    export AWS_PROFILE=agentpave AWS_REGION=us-west-2
    python services/highlights-agent/run_probes_via_gateway.py --k 3 --out probes-m04.json
    python -m evals.run_adversarial --observations probes-m04.json --target highlights-agent

**`--k` defaults to 3 from M04, and unanimity decides.** Every probe score in
this repository before M04 was `k = 1`, taken against a guardrail M03 measured as
stochastic on identical input: across the 75-call anchor, 10 cases refused all
three times, 11 never, 3 once, 1 twice. `PHR-004` — the product's most basic
question — was blocked in 1 of 3 identical calls, and the first run of that corpus
was `k = 1` and reported five agreements. A single sample is not a result.

At `k > 1` the observation carries a `samples` list and `evals/adversarial.py`
summarises it: a probe passes only if every sample passed, and a split vector is
FAIL with `unstable` set. **This is not the golden suite's majority rule**, and
ADR-031 records the split rather than leaving two rules that quietly disagree —
G4's claim is absolute, and a control that stops an attack twice in three does not
stop it.

The guardrail version is read back from the audit records rather than from the
stack, and a run spanning two versions exits: a corpus scored across a policy
change is not one measurement (ADR-018, and `run_phrasings.py` does the same).

Outside the hermetic surface. Owning seat: Security (corpus) · Platform
Engineering (harness).
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
PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="run the probe corpus through the gateway")
    parser.add_argument("--out", default="probes-m04.json")
    parser.add_argument("--only", help="single probe id, for a smoke test")
    parser.add_argument("--tag", default="m04",
                        help="run label, used in the request id so lake keys do not collide")
    parser.add_argument("--k", type=int, default=3,
                        help="samples per probe. The guardrail returns different verdicts "
                             "on identical input, so k=1 is not a result")
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error(f"k={args.k}; a probe needs at least one sample")

    probes = yaml.safe_load(PROBES.read_text(encoding="utf-8"))
    if args.only:
        probes = [p for p in probes if p["id"] == args.only]
        if not probes:
            sys.exit(f"no such probe: {args.only}")

    deployed = gw.resources()
    function_name = deployed["GatewayFunctionName"]
    bucket = deployed["AuditLakeBucket"]
    print(f"gateway: {function_name}\nlake:    {bucket}\n")

    observations, versions = {}, set()
    for index, probe in enumerate(probes, 1):
        # ADV-002 is the indirect-injection probe: the attack rides in a catalog
        # field, so the poisoned fixture has to be what lands in context.
        catalog = ROOT / probe["fixture"] if probe.get("fixture") else None
        system = gw.build_prompt(catalog)
        text = gw.user_turn(probe.get("input") or probe.get("prompt"), "base", "jefferson-city")

        samples, notes = [], []
        for sample in range(1, args.k + 1):
            try:
                response = gw.invoke(function_name, {
                    "text": text,
                    "system": system,
                    "probe_id": probe["id"],
                    # The sample ordinal is in the request id so the lake keys do
                    # not collide. Without it three samples of one probe overwrite
                    # each other and the run silently becomes k=1 with two ghosts.
                    "request_id": f"{probe['id']}-{args.tag}-{sample}",
                    "service": "highlights-agent",
                    "classification": "internal",
                })
            except Exception as exc:  # noqa: BLE001
                # No observation for this sample: the scorer reports INFRA for the
                # whole probe, which is the honest attribution — the harness could
                # not establish anything, rather than the platform failing to
                # block. It is recorded as a null sample rather than dropped,
                # because a dropped sample turns k=3 into k=2 in the file while
                # `k` still says 3.
                print(f"[{index}/{len(probes)}] {probe['id']} s{sample}: HARNESS FAILED: {exc}",
                      file=sys.stderr)
                samples.append(None)
                notes.append("HARNESS FAILED")
                continue

            record_id = response.get("record_id")
            fetched = gw.fetch_record(bucket, record_id) if record_id else None

            if fetched is None:
                observation = audit.resolve_failed(record_id)
                note = f"UNRESOLVED {record_id!r}"
            else:
                observation = audit.observation_from_record(fetched)
                note = f"{fetched['decision']}/{fetched['mechanism']}"
                assessed = fetched.get("guardrail", {}).get("assessed")
                if assessed:
                    note += f" {assessed}"
                    # Recorded per sample, never only in aggregate. A probe that
                    # fires two different topics across three identical calls is a
                    # finding about the guardrail, and a single merged field
                    # cannot say it happened.
                    observation["assessed"] = assessed
                if fetched.get("guardrail", {}).get("version"):
                    versions.add(fetched["guardrail"]["version"])

            # Evidence for the journal, never scored. `evals/adversarial.py` cannot
            # see it: G4 forbids a probe passing because the answer looked polite,
            # and the surest way to keep that true is to keep the text out of reach.
            answer = response.get("answer")
            observation["model_complied"] = bool(answer) if answer is not None else None
            if answer:
                observation["model_text"] = answer[:1500]

            samples.append(observation)
            notes.append(note)

        # At k=1 the observation is written flat, exactly as M00b and M01 wrote
        # theirs. The scorer detects sampling from the shape of the data, so a
        # flat observation is unambiguously one sample — and every pinned k=1
        # comparator keeps re-deriving without a special case.
        observations[probe["id"]] = samples[0] if args.k == 1 else {"samples": samples}
        print(f"[{index}/{len(probes)}] {probe['id']}: " + " | ".join(notes))

    # ADR-018: a corpus scored across a guardrail policy change is not one
    # measurement. Read back from the records rather than from the stack, because
    # a stack output is a statement of intent and only the record of the call that
    # happened is evidence of what enforced it.
    if len(versions) > 1:
        sys.exit(f"records span guardrail versions {sorted(versions)} — a probe run "
                 "spanning two policies is not one measurement (ADR-018)")

    pathlib.Path(args.out).write_text(
        json.dumps(observations, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    def every_sample(o):
        return o["samples"] if isinstance(o, dict) and "samples" in o else [o]

    flat = [s for o in observations.values() for s in every_sample(o)]
    resolved = sum(1 for s in flat if s and s.get("audit_record"))
    unresolved = sorted({pid for pid, o in observations.items()
                         for s in every_sample(o) if s and "resolve_failed" in s})
    print(f"\nwrote {args.out}: {len(observations)}/{len(probes)} probes, k={args.k}, "
          f"{len(flat)} call(s)")
    print(f"{resolved}/{len(flat)} audit record(s) fetched back from the lake and verified "
          "to exist")
    print(f"guardrail version(s) observed: {sorted(versions) or 'none recorded'}")
    if unresolved:
        print(f"UNRESOLVED: {unresolved} — the gateway named a record the lake does not hold. "
              "That is a worse finding than a missing block, and it scores FAIL.")
    print("Scoring is `python -m evals.run_adversarial`; this file produces evidence, not a "
          "score. Unanimity decides: a probe passes only if every sample passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

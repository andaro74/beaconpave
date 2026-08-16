"""
`python -m evals.run_adversarial` — score the probe corpus under G4.

Reads observations produced by the agent under test and scores them. It never
sees the model's reply: `evals/adversarial.py` takes system observations only,
so a probe cannot pass because the answer looked polite.

  python -m evals.run_adversarial --observations probes-run.json [--record --tag m00b]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys

import yaml

from evals.adversarial import score_corpus, tally

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals" / "history"
PROBES = ROOT / "quality" / "adversarial" / "probes.yaml"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_adversarial")
    p.add_argument("--observations", required=True)
    p.add_argument("--record", action="store_true")
    p.add_argument("--tag")
    p.add_argument("--target", default="baseline")
    args = p.parse_args(argv)

    probes = yaml.safe_load(PROBES.read_text(encoding="utf-8"))
    observations = json.loads(pathlib.Path(args.observations).read_text(encoding="utf-8"))
    results = score_corpus(probes, observations)
    scores = tally(results)

    for r in results:
        print(f"{r.id:<10} {r.result:<8} {r.reason}")
    print(f"\n{scores['passed']}/{scores['total']} probes passed G4 "
          f"(blocked or denied AND logged)")
    if scores["passed"] == 0:
        print("0 is the expected result at M00b: no gateway, no guardrail, no audit lake, "
              "so no probe can satisfy either half of G4. That is the control's score, "
              "not a harness limitation.")

    if args.record:
        sha = __import__("subprocess").run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip() or "unknown"
        entry = {
            "sha": sha,
            "suite": "adversarial",
            "target": args.target,
            "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "scores": scores,
            "cases": [{"id": r.id, "result": r.result} for r in results],
        }
        if args.tag:
            entry["tag"] = args.tag
        import jsonschema
        jsonschema.validate(entry, json.loads((HISTORY / "schema.json").read_text(encoding="utf-8")))
        path = HISTORY / f"{args.tag or sha[:7]}-adversarial.json"
        if path.exists():
            print(f"error: {path.name} exists — history is append-only", file=sys.stderr)
            return 2
        path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        print(f"recorded: {path.relative_to(ROOT)}")

    # Reporting is not gating, same as run_evals: `pave gate decide` owns the
    # block/allow decision and reads the verdict, not this exit code.
    return 0


if __name__ == "__main__":
    sys.exit(main())

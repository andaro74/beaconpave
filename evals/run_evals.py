"""
`python -m evals.run_evals` — the deterministic scoring run (ADR-012).

Reads answers a service already produced; it does not produce them. That split
is the point: the model call belongs to the agent (ADR-011 quarantines the
baseline as the only direct-model path), and the scorer stays hermetic, so it can
be proven correct against committed fixtures before any non-deterministic thing
exists.

  python -m evals.run_evals --dryrun
      Resolve fixtures, load every case, validate the assert vocabulary. No
      answers needed and no scores produced.

  python -m evals.run_evals --answers run.json [--record --tag m00b] [--out verdict.json]
      Score, and optionally append a history entry and emit a gate verdict.

The answers file is `{"<case-id>": {"answer": {...}, "usage": {...}}}`. A case
with no entry scores INFRA — absence blocks, exactly as it does in
`pave gate decide`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys
from dataclasses import replace

import yaml

from evals.deterministic import (
    ADVISORY,
    DEFERRED_ASSERTS,
    FAIL,
    INFRA,
    Scorer,
    suite_latency,
    tally,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals" / "history"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
CATALOG = ROOT / "data" / "catalog.json"

#: Deliberately unused. The rubric is referenced by every case and read by
#: nothing until M03; naming it here is a reminder that leaving it unread is the
#: decision, not an omission (ADR-012).
RUBRIC = ROOT / "quality" / "judge" / "rubric-sports.md"


def _load(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)


def _git_sha() -> str:
    import subprocess
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def dryrun(cases: list) -> int:
    catalog = _load(CATALOG)
    print(f"loaded {len(cases)} golden cases, catalog has {len(catalog.get('titles', []))} titles")
    for case in cases:
        for fixture in case.get("fixtures", []):
            if not (ROOT / fixture).is_file():
                print(f"error: {case['id']}: fixture missing: {fixture}", file=sys.stderr)
                return 2
    print("dryrun: OK — fixtures resolve, cases load, no model was called")
    return 0


def run(args) -> int:
    cases = _load(GOLDENS)
    if args.dryrun:
        return dryrun(cases)

    if not args.answers:
        print("error: --answers is required unless --dryrun", file=sys.stderr)
        return 2

    catalog = _load(CATALOG)
    answers = _load(pathlib.Path(args.answers))
    results = Scorer(root=ROOT).score_suite(cases, answers, catalog)

    # SPEC/00b's honesty clause, machine-recorded. The history schema has carried
    # `unearned` / `unearned_reason` since the starter and nothing populated them,
    # which left the clause as prose someone had to remember. Marks come from a
    # committed file rather than being inferred: deciding a pass is unearned is a
    # judgement, and it should be reviewable in a diff.
    if args.unearned:
        marks = _load(pathlib.Path(args.unearned)) or {}
        unknown = sorted(set(marks) - {r.id for r in results})
        if unknown:
            print(f"error: unearned marks name unknown case(s): {unknown}", file=sys.stderr)
            return 2
        wrong = sorted(cid for cid in marks if next(r.result for r in results if r.id == cid) != "PASS")
        if wrong:
            print(f"error: only a PASS can be unearned; these did not pass: {wrong}", file=sys.stderr)
            return 2
        results = [
            replace(r, unearned=True, unearned_reason=marks[r.id]) if r.id in marks else r
            for r in results
        ]

    scores = tally(results)

    width = max(len(r.id) for r in results)
    for r in results:
        print(f"{r.id:<{width}}  {r.result}")
        for failure in r.failures:
            print(f"{'':<{width}}    - {failure.kind}: {failure.detail}")
    print(
        f"\n{scores['passed']}/{scores['total']} passed "
        f"({scores['failed']} failed, {scores['infra']} infra) — "
        f"judge axes recorded {ADVISORY}, not scored (ADR-012)"
    )
    latency = suite_latency(answers, _load(MANIFEST)["gates"]["budgets"].get("p95_ms"))
    print(f"suite latency  {'OK  ' if latency.passed else 'OVER'} {latency.detail}")
    deferred_hits = sum(len(r.deferred) for r in results)
    if deferred_hits:
        kinds = sorted({a.kind for r in results for a in r.deferred})
        print(f"deferred, evaluated but not scored: {deferred_hits} assert(s) across {kinds}")
        for kind in kinds:
            print(f"  {kind}: {DEFERRED_ASSERTS.get(kind, 'deferred')}")

    unearned = [r for r in results if r.unearned]
    if unearned:
        print(f"\n{len(unearned)} of those passes are marked UNEARNED (SPEC/00b):")
        for r in unearned:
            print(f"  {r.id}: {r.unearned_reason}")

    if args.record:
        path = record(results, scores, args)
        print(f"recorded: {path.relative_to(ROOT)}")

    if args.out:
        emit_verdict(results, scores, args.out)
        print(f"wrote verdict: {args.out}")

    # Reporting a score is not gating. `pave gate decide` owns the block/allow
    # decision, and it reads the verdict this writes.
    return 0


def record(results, scores, args) -> pathlib.Path:
    """Append a history entry. Never edits: a correction is a new entry carrying
    `supersedes`, because the value of this file is that every row came from a
    real execution."""
    sha = _git_sha()
    entry = {
        "sha": sha,
        "suite": "goldens",
        "target": args.target,
        "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "scores": scores,
        "cases": [
            {"id": r.id, "result": r.result}
            | ({"unearned": True, "unearned_reason": r.unearned_reason} if r.unearned else {})
            for r in results
        ],
    }
    if args.tag:
        entry["tag"] = args.tag
    for key in ("tokens_in", "tokens_out"):
        value = getattr(args, key)
        if value is not None:
            entry[key] = value

    import jsonschema
    jsonschema.validate(entry, _load(HISTORY / "schema.json"))

    HISTORY.mkdir(parents=True, exist_ok=True)
    path = HISTORY / f"{args.tag or sha[:7]}-goldens.json"
    if path.exists():
        raise SystemExit(
            f"error: {path.name} already exists. History is append-only — a correction is a new "
            "entry with `supersedes`, never an edit (CLAUDE.md)."
        )
    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    return path


def emit_verdict(results, scores, out: str) -> None:
    from pave import verdict as verdict_mod
    blocked = any(r.result == INFRA for r in results)
    verdict_mod.write(out, verdict_mod.build(
        service="highlights-agent",
        surface="agent",
        suite="goldens",
        layer="L2",
        verdict=INFRA if blocked else (FAIL if scores["failed"] else "PASS"),
        fail_closed=True,
        scores={k: v for k, v in scores.items()},
    ))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_evals", description=__doc__)
    p.add_argument("--dryrun", action="store_true", help="load and resolve only; no scoring")
    p.add_argument("--answers", help="JSON produced by the agent under test")
    p.add_argument("--record", action="store_true", help="append an entry to evals/history/")
    p.add_argument("--tag", help="milestone tag, e.g. m00b")
    p.add_argument("--target", default="baseline", help="baseline | <service-name>")
    p.add_argument("--out", help="write a gate verdict record here")
    p.add_argument("--unearned", help="YAML/JSON of {case-id: reason} marking passes that are not credited to the system (SPEC/00b)")
    p.add_argument("--tokens-in", dest="tokens_in", type=int)
    p.add_argument("--tokens-out", dest="tokens_out", type=int)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())

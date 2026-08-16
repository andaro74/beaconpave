"""
Writing verdict records.

`quality/verdicts/schema.json` is THE contract — one schema, many runners (claim
3). Agent evals, Playwright, k6, and the drill all emit it. This module is the
one place that constructs it, so a new runner cannot invent a slightly different
shape and discover the difference only when a dashboard silently drops its rows.

Every record is validated against the schema **before** it is written. A runner
that emits an invalid verdict would be blocked by the gate anyway (exit 2), but
it would be blocked at the wrong end of the pipeline, with a message about the
gate rather than about the runner that was actually wrong.

Owning seat: AI Quality owns the schema; Platform Engineering owns this writer.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "quality" / "verdicts" / "schema.json"


def current_commit() -> str:
    """The SHA under test. Prefers the CI-provided value: in a pull_request run
    `git rev-parse HEAD` names the merge commit, not the commit the reviewer is
    looking at."""
    for var in ("GITHUB_SHA", "BEACONPAVE_SHA"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        # Not a git checkout. Recorded honestly rather than faked — a verdict
        # attributed to the wrong commit is worse than one that admits it has none.
        return "unknown"


def build(
    *,
    service: str,
    surface: str,
    suite: str,
    layer: str,
    verdict: str,
    fail_closed: bool = True,
    scores: dict | None = None,
    duration_s: float | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    cost_usd: float | None = None,
    artifacts: list[str] | None = None,
    commit: str | None = None,
) -> dict:
    record = {
        "service": service,
        "surface": surface,
        "commit": commit or current_commit(),
        "suite": suite,
        "layer": layer,
        "verdict": verdict,
        "fail_closed": fail_closed,
    }
    if scores is not None:
        record["scores"] = scores
    if duration_s is not None:
        record["duration_s"] = duration_s
    if tokens_in is not None:
        record["tokens_in"] = tokens_in
    if tokens_out is not None:
        record["tokens_out"] = tokens_out
    if cost_usd is not None:
        record["cost_usd"] = cost_usd
    if artifacts:
        record["artifacts"] = artifacts

    jsonschema.validate(record, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    return record


def write(path: str | pathlib.Path, record: dict) -> pathlib.Path:
    out = pathlib.Path(path)
    if out.parent != pathlib.Path(""):
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return out

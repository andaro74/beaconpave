"""
A surface runner's raw output, written as one verdict record through `pave.verdict.build`.

usage: python surfaces/web-player/emit.py playwright <raw.json> <verdict.json>
       python surfaces/web-player/emit.py k6 <summary.json> <verdict.json>

**The envelope is closed** (`quality/verdicts/schema.json`, M10 PR 1). A runner's own
numbers go in `scores`, its own words in `notes`, and its raw output is named in
`artifacts`. Nothing here writes a key the schema does not declare, and
`pave.verdict.build` validates the record before anything is written.

**Three outcomes, never two.**
- PASS: every check or threshold held.
- FAIL: one did not.
- INFRA: the runner could not establish either. Its raw output is missing or
  unreadable, it recorded nothing to decide on, Playwright could not reach the page, or
  no k6 request received a response.

**k6 is INFRA only when nothing answered.** A run where some requests never connected
and others were answered is decided by its thresholds, because the surface was there and
a dropped connection already counts toward `http_req_failed`. The first rule, *any
unreached request is INFRA*, was measured wrong before any claim used it: a served 404
closes each connection, and 905 requests of one run never connected while the rest
received 404. It reported INFRA for a surface that was answering wrongly.

INFRA blocks at exit 2 and pages the platform. It is never folded into FAIL, and never
into PASS.

Owning seat: AI Quality (what PASS and FAIL mean); Platform Engineering (this writer).
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pave import verdict  # noqa: E402

SERVICE = "web-player"
SURFACE = "web"
LAYER = "L4"


def _rel(path: str | pathlib.Path) -> str:
    p = pathlib.Path(path).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def _load(path: str | pathlib.Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, "the runner wrote no raw output"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"the runner's raw output is unreadable ({exc.__class__.__name__})"


def _record(suite: str, result: str, raw_path, notes: list[str], commit: str | None,
            scores: dict | None = None, duration_s: float | None = None) -> dict:
    return {"runner": SERVICE, **verdict.build(
        service=SERVICE, surface=SURFACE, suite=suite, layer=LAYER, verdict=result,
        fail_closed=True, scores=scores, duration_s=duration_s,
        artifacts=[_rel(raw_path)], notes=notes, commit=commit)}


def playwright_record(raw_path: str | pathlib.Path, commit: str | None = None) -> dict:
    raw, problem = _load(raw_path)
    if problem is None and raw.get("error"):
        problem = f"the runner could not reach the page: {raw['error']}"
    if problem is None and not raw.get("checks"):
        problem = "the runner recorded no checks, so nothing was decided"
    if problem:
        return _record("playwright", "INFRA", raw_path, [problem], commit)
    checks = raw["checks"]
    failed = [c["name"] for c in checks if c.get("ok") is not True]
    return _record(
        "playwright", "FAIL" if failed else "PASS", raw_path,
        [f"{raw.get('browser', 'chromium')} against {raw.get('url')}"]
        + [f"FAILED: {name}" for name in failed],
        commit,
        scores={"checks_held": len(checks) - len(failed), "checks_total": len(checks)},
        duration_s=raw.get("duration_s"))


def _threshold_ok(outcome) -> bool:
    return (outcome.get("ok") if isinstance(outcome, dict) else outcome) is True


def k6_record(summary_path: str | pathlib.Path, commit: str | None = None) -> dict:
    raw, problem = _load(summary_path)
    metrics = (raw or {}).get("metrics") or {}
    if problem is None and not metrics:
        problem = "the summary carries no metrics, so nothing was decided"
    def count(metric: str) -> int:
        return int(((metrics.get(metric) or {}).get("values") or {}).get("count") or 0)

    unreached, answered = count("transport_errors"), count("responses_received")
    if problem is None and not answered:
        problem = f"no request received a response ({unreached} never reached the surface)"
    thresholds = [(name, expr, outcome) for name, m in metrics.items()
                  for expr, outcome in (m.get("thresholds") or {}).items()]
    if problem is None and not thresholds:
        problem = "the summary carries no thresholds, so nothing was decided"
    if problem:
        return _record("k6", "INFRA", summary_path, [problem], commit)
    breached = sorted(f"{name} {expr}" for name, expr, outcome in thresholds
                      if not _threshold_ok(outcome))

    def value(metric: str, stat: str):
        return ((metrics.get(metric) or {}).get("values") or {}).get(stat)

    scores = {"thresholds_held": len(thresholds) - len(breached),
              "thresholds_total": len(thresholds),
              "responses_received": answered, "requests_unreached": unreached}
    for key, metric, stat in (("http_req_duration_p95_ms", "http_req_duration", "p(95)"),
                              ("http_req_failed_rate", "http_req_failed", "rate"),
                              ("iterations", "iterations", "count")):
        if isinstance(value(metric, stat), (int, float)):
            scores[key] = round(value(metric, stat), 3)
    duration_ms = ((raw.get("state") or {}).get("testRunDurationMs"))
    return _record(
        "k6", "FAIL" if breached else "PASS", summary_path,
        [f"threshold breached: {b}" for b in breached] or ["every threshold held"],
        commit, scores=scores,
        duration_s=round(duration_ms / 1000, 3) if isinstance(duration_ms, (int, float)) else None)


RECORDERS = {"playwright": playwright_record, "k6": k6_record}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in RECORDERS:
        print(__doc__, file=sys.stderr)
        return 2
    record = RECORDERS[argv[0]](argv[1])
    verdict.write(argv[2], record)
    print(f"[emit] {argv[0]}: {record['verdict']} -> {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""
`python tests/fixtures/m08b/build_planted.py` — a planted M08b run, so the
three readers under `milestones/M08b/` are written and tested before any real
answer file exists (SPEC/08b, PR 2).

**Synthetic by construction, and shaped to be read.** Twenty-five cases at
k=3 from the live cases file, every answer built to satisfy its own asserts —
mentions what it must, cites what it must, carries the entitlement verdict the
case expects — so the count is high and the interesting rows are the planted
ones:

- every case at its mandated call count with a first round of 1980 tokens,
  the totals under 7700, latency at the mandated shape;
- `recommend-015` at three calls against a two-call mandate (above mandate,
  under the ceiling; the browse gap's first extra call);
- `recommend-013` at four calls on every sample (8300; the browse gap on one of
  the seven), `grounded-019` s3 at four calls at exactly 8181;
- `headroom-005` s2 at three calls at 7690: inside the grain, a near miss;
- `recommend-003` refused on s1 and s3 on the `answer` channel by the
  entitlement topic, answered on s2 with a grant at four calls; `brand-020`
  refused once — so F, G and majority are all exercised;
- `blackout-001` over its `tokens_out` tier on every sample (the five's
  trigger);
- a calibration record on `blackout-008` with tools absent, and the grants
  file the operator would write after reading the held texts.

The transcripts are produced by the real scorer over the planted files, so a
runner format change shows up here first. Hermetic: no model, no network.
`tests/test_m08b_fixtures.py` rebuilds everything into a temporary directory
and refuses drift from what is committed.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent / "planted"
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
CATALOG = ROOT / "data" / "catalog.json"
sys.path.insert(0, str(ROOT))

from evals.refusals import census_from_samples  # noqa: E402

ROUNDS_3 = [1980, 2100, 2150]          # 6230, under 7700
ROUNDS_2 = [1980, 2100]                # 4080
LATENCY = {2: 2300, 3: 3500}
TAG = "m08b-planted"
ENTITLEMENT_TOPIC = "TOPIC:entitlement-circumvention"

#: The planted shapes, by (case, sample). `None` for a sample means every sample.
PLANTS = {
    ("recommend-015", None): {"rounds": [1980, 2300, 2320], "latency": 4800, "searches": 2},
    ("recommend-013", None): {"rounds": [1980, 2100, 2110, 2110], "latency": 6000, "searches": 3},
    ("grounded-019", 3): {"rounds": [1980, 2050, 2070, 2081], "latency": 5900, "searches": 3},
    ("headroom-005", 2): {"rounds": [1980, 2800, 2910], "latency": 5000, "searches": 2},
    ("recommend-003", 2): {"rounds": [1980, 2100, 2100, 2020], "latency": 6100, "searches": 3,
                           "entitled": True},
    ("recommend-003", 1): {"refused": True, "searches": 3},
    ("recommend-003", 3): {"refused": True, "searches": 3},
    ("brand-020", 1): {"refused": True, "searches": 1},
    ("blackout-001", None): {"tokens_out": 330},
}
GRANTS = {"recommend-003": {"s1": {"grant": True, "dec001_shape": False},
                            "s3": {"grant": True, "dec001_shape": False}},
          "brand-020": {"s1": {"grant": False, "dec001_shape": False}}}


def _catalog_ids(catalog) -> list[str]:
    found = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("id"), str) and node["id"].startswith("t"):
                found.append(node["id"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(catalog)
    return sorted(set(found))


def plant_for(case_id: str, sample: int) -> dict:
    merged = {}
    merged.update(PLANTS.get((case_id, None), {}))
    merged.update(PLANTS.get((case_id, sample), {}))
    return merged


def mandate(case: dict) -> int:
    return 2 + (1 if (case.get("trajectory") or {}).get("expect_tool_before_answer") == "entitlement-check" else 0)


def passing_answer(case: dict, catalog_ids: list[str], entitled: bool | None) -> dict:
    mentions, cites, forbid, entitlement, empty, at_least_one = [], [], [], None, False, False
    for assertion in case.get("asserts", []):
        for key, value in assertion.items():
            if key == "must_mention":
                mentions.append(value)
            elif key == "must_cite":
                cites.extend(value)
            elif key == "must_not_claim":
                forbid.append(value)
            elif key == "entitlement":
                entitlement = dict(value)
            elif key == "cited_titles_empty":
                empty = True
            elif key == "cites_at_least_one":
                at_least_one = True
    prose = "Planted answer. " + " ".join(f"{m}." for m in mentions) + " Nothing else is claimed."
    for needle in forbid:
        assert needle.lower() not in prose.lower(), f"{case['id']}: the planted prose contains {needle!r}"
    if empty:
        cited = []
    elif cites:
        cited = list(cites)
    elif at_least_one:
        cited = [catalog_ids[0]]
    else:
        cited = []
    if entitlement is not None:
        verdict = {"entitled": entitlement.get("entitled", False), "reason": entitlement.get("reason", "ok"),
                   "source": "entitlement-check"}
    elif entitled:
        verdict = {"entitled": True, "reason": "ok", "source": "entitlement-check"}
    else:
        verdict = None
    return {"answer": prose, "cited_titles": cited, "entitlement": verdict, "ai_disclosure": None}


def trajectory_for(case: dict, searches: int, calls: int) -> list[dict]:
    viewer = case.get("viewer") or {}
    steps = []
    for i in range(searches):
        steps.append({"round": i + 1, "seq": i + 1, "tool": "catalog-search",
                      "args": {"query": ["derby", "live", "replay"][i % 3], "brand": "meridian-sports"},
                      "decision": "allowed", "mechanism": "none", "reasons": [], "executed": True})
    if calls - 1 > searches:
        cites = next((v for a in case.get("asserts", []) for k, v in a.items() if k == "must_cite"), None)
        steps.append({"round": searches + 1, "seq": searches + 1, "tool": "entitlement-check",
                      "args": {"title_id": (cites or ["t001"])[0], "plan": viewer.get("plan"),
                               "dma": viewer.get("dma")},
                      "decision": "allowed", "mechanism": "none", "reasons": [], "executed": True})
    return steps


def build(out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    catalog_ids = _catalog_ids(json.loads(CATALOG.read_text(encoding="utf-8")))
    per_sample: dict = {c["id"]: [] for c in cases}
    refusal_detail: dict = {}
    for n in (1, 2, 3):
        answers, trajectories = {}, {}
        for case in cases:
            case_id = case["id"]
            plant = plant_for(case_id, n)
            wants_ec = mandate(case) == 3
            if plant.get("refused"):
                searches = plant.get("searches", 1)
                calls = searches + 1 + (1 if wants_ec else 0)
                record_id = f"planted/{case_id}-{TAG}-{n}.json"
                detail = {"decision": "blocked", "mechanism": "guardrail", "assessed": [ENTITLEMENT_TOPIC],
                          "channels": ["answer"], "guardrail": {"id": "planted", "version": "4"},
                          "reasons": [], "record_id": record_id, "record_resolved": True}
                refusal_detail.setdefault(case_id, {})[f"s{n}"] = detail
                per_sample[case_id].append(True)
                answers[case_id] = {"answer": {"refused_by_gateway": "guardrail", "record_id": record_id},
                                    "usage": {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}}
                trajectories[case_id] = {"trajectory": trajectory_for(case, searches, calls),
                                         "tool_records": [], "decision": "blocked"}
                continue
            per_sample[case_id].append(False)
            rounds = plant.get("rounds") or (ROUNDS_3 if wants_ec else ROUNDS_2)
            calls = len(rounds)
            searches = plant.get("searches", 1)
            tokens_out = plant.get("tokens_out", 200)
            latency = plant.get("latency", LATENCY.get(calls, 3500))
            per_call = [{"tokens_in": t, "tokens_out": tokens_out // calls, "latency_ms": latency // calls}
                        for t in rounds]
            per_call[-1]["tokens_out"] += tokens_out - sum(c["tokens_out"] for c in per_call)
            per_call[-1]["latency_ms"] += latency - sum(c["latency_ms"] for c in per_call)
            answers[case_id] = {
                "answer": passing_answer(case, catalog_ids, plant.get("entitled")),
                "usage": {"guard_ms": 900, "tokens_in": sum(rounds), "tokens_out": tokens_out,
                          "latency_ms": latency, "tool_ms": 40, "calls": per_call},
            }
            trajectories[case_id] = {"trajectory": trajectory_for(case, searches, calls),
                                     "tool_records": [f"planted/{case_id}-{TAG}-{n}.{i:03d}.json"
                                                      for i in range(1, calls)],
                                     "decision": "allowed"}
        (out / f"goldens-run-{n}.json").write_text(json.dumps(answers, indent=2, ensure_ascii=False),
                                                   encoding="utf-8", newline="")
        (out / f"goldens-run-{n}-trajectory.json").write_text(
            json.dumps(trajectories, indent=2, ensure_ascii=False), encoding="utf-8", newline="")
    sidecar = {
        "_what_this_is": "PLANTED (tests/fixtures/m08b/build_planted.py): a synthetic M08b sidecar for "
                         "the readers' tests. No gateway, no record, no model.",
        "_k": 3, "samples": [1, 2, 3],
        "_preflight": {"gateway_function": "planted", "guardrail": {"id": "planted", "version": "4"},
                       "tool_output_guardrail": {"id": "planted-tool-output", "version": "2"},
                       "deployed_bundle": {"code_sha256": "planted"}, "tag": TAG},
        "_guardrail_versions": ["4"], "_guardrails_observed": {"planted": ["4"]},
        "census": census_from_samples(per_sample, 3),
        "refusals": refusal_detail,
        "per_sample_refused": per_sample,
    }
    (out / "goldens-run-refusals.json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False),
                                                   encoding="utf-8", newline="")
    calibration = {
        "_what_this_is": "PLANTED: the calibration record's shape (run_with_tools.py --calibrate).",
        "case": "blackout-008", "request_id": f"blackout-008-{TAG}-calibration", "tools": "absent",
        "decision": "allowed", "mechanism": "none", "record_id": f"planted/blackout-008-{TAG}-calibration.json",
        "record_resolved": True,
        "usage": {"guard_ms": 600, "tokens_in": 1470, "tokens_out": 80, "latency_ms": 1200,
                  "calls": [{"tokens_in": 1470, "tokens_out": 80, "latency_ms": 1200}]},
        "record_usage": {"guard_ms": 600, "tokens_in": 1470, "tokens_out": 80, "latency_ms": 1200,
                         "calls": [{"tokens_in": 1470, "tokens_out": 80, "latency_ms": 1200}]},
        "trajectory": [], "system_sha256": "planted", "text_sha256": "planted",
    }
    (out / "calibration.json").write_text(json.dumps(calibration, indent=2), encoding="utf-8", newline="")
    (out / "withheld-grants.json").write_text(json.dumps({
        "_what_this_is": "PLANTED: the grants file the operator writes after read_withheld.py --show; "
                         "one entry per refused sample on the answer channel. No text.",
        "grants": GRANTS}, indent=2), encoding="utf-8", newline="")

    # Relative to the repository when the output is inside it (the committed
    # fixture), absolute otherwise (the drift test rebuilds into a temporary
    # directory and normalises the header lines before comparing).
    rel = out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else out.resolve().as_posix()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    sidecar_arg = f"{rel}/goldens-run-refusals.json"

    def transcript(args: list[str]) -> str:
        cmd = [sys.executable, "-m", "evals.run_evals", "--arm", "tools", *args]
        shown = "python -m evals.run_evals --arm tools " + " ".join(args)
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                              encoding="utf-8", env=env, check=False)
        return f"=== {shown}\n{proc.stdout}exit {proc.returncode}\n"

    per_sample_text = "".join(
        transcript(["--answers", f"{rel}/goldens-run-{n}.json", "--refusals", sidecar_arg]) + "\n"
        for n in (1, 2, 3))
    k3_text = transcript([*sum((["--answers", f"{rel}/goldens-run-{n}.json"] for n in (1, 2, 3)), []),
                          "--refusals", sidecar_arg])
    (out / "per-sample.txt").write_text(per_sample_text, encoding="utf-8", newline="\n")
    (out / "goldens-score.txt").write_text(k3_text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
    print(f"planted run written under {OUT}")

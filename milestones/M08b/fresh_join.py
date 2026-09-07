"""
`python milestones/M08b/fresh_join.py` — the fresh run joined per sample at 7700:
the claim, the near-miss reading, the bands, the two p95s, the triggers.

**The claim is per sample and the count cannot show it** (SPEC/08b). This reads
the three answer files' `usage.calls` — the per-round list the loop now records —
and the three single-file transcripts, and writes one row per sample: the call
count, the case's mandate, `tokens_in`, the verdict the scorer printed at the
live ceiling, and what the sample means if it falsifies. The claim's two
falsifiers — any answered sample at three calls or fewer over 7700, any at four
or more under it — are computed from the rows, never asserted.

**What a falsifying sample means is pre-registered** (SPEC/08b, *What a
falsifying sample means*; ADR-074 amendment 1 §5): the point is 7700, the
unrounded midpoint 7675.125, the band [7171, 8180], the grain (7675.125, 7700],
and a sample on the wrong side of the point is one of six rows — the rule
failed, the point failed inside a band that still holds it, the point failed
and the rule survives, or the grain — depending on its side, its mandate and
where it sits against the band. Every answered sample carries its distance to
the point, to the unrounded midpoint and to the nearer band edge; the run as a
whole carries the band ADR-014's rule re-derives from the fresh mandated-shape
maximum and the fresh four-call minimum, and whether 7700 still sits inside it.
The number can hold while the rule does not, and that column is what says so.

**What else is read from the same rows.** The count against [7, 14] with the
per-case majority read beside M08's (`rescore-join.json`); refusals by majority
against 0–2; the fresh pooled p95 AND the fresh mandated-shape p95 against the
manifest's derived ceiling, with the two readings ADR-014 amendment 3 names;
each round's growth in `tokens_in` against the replayed transcript's growth in
characters, recorded and not ruled on; and ADR-074 decision 2's two triggers —
the browse gap on the seven cases, `tokens_out` on the five.

**What it refuses.** A transcript verdict that disagrees with the answer file
(`got > limit` at the live ceiling), a transcript scored at any other ceiling,
a `(calls=N)` suffix or a trajectory that disagrees with `usage.calls`, a
sidecar census that disagrees with its own per-sample column, and a live
ceiling that is not the number the pinned point rule produces. It takes no
ceiling argument, calls nothing, and imports no network module; the `usage`
fields are read from committed files and never written.

Owning seats, by the two-key rule that covers it: AI Quality (the ceiling),
Platform Engineering (the loop whose call counts it reads), Security (what
"catches a runaway loop" means).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "milestones" / "M08b"
OUT_NAME = "fresh-join.json"
sys.path.insert(0, str(ROOT))

from evals import deterministic  # noqa: E402 — the scorer's own p95, never re-implemented

CENSUS = ROOT / "milestones" / "M08" / "context-census.json"
CENSUS_READER = ROOT / "milestones" / "M08" / "context_census.py"
M08_JOIN = ROOT / "milestones" / "M08" / "rescore-join.json"
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
CATALOG = ROOT / "data" / "catalog.json"

DECISION_RULE = "8_decision_rule (pre-registered, SPEC/08)"
BY_MILESTONE = "1_by_milestone (exact)"
STAGE2 = "m07-stage2"
PER_SAMPLE = "2_stage2_per_sample (exact + replayed)"

#: ADR-014's budget band and point rule, as `tests/test_budget_derivation.py`
#: executes them. The same two constants; a change there is red there.
BAND = (1.15, 1.60)

#: ADR-074 decision 3 §2: the count band and its prediction; the refusal band.
COUNT_BAND = (7, 14)
PREDICTED_N = 12
REFUSAL_BAND = (0, 2)

#: ADR-074 decision 2: the seven browse-gap cases and the five `tokens_out` cases.
BROWSE_GAP_SEVEN = ("recommend-003", "recommend-013", "recommend-014", "grounded-018",
                    "grounded-019", "multi-023", "edge-025")
TOKENS_OUT_FIVE = ("blackout-001", "blackout-007", "blackout-008", "blackout-009", "concise-022")

#: The six rows of SPEC/08b's near-miss table, plus the two non-falsifying
#: readings, by name. A falsifying sample is recorded with its row.
PASS = "pass"
FAIL = "fail"
GRAIN_NEAR_MISS = ("grain near miss: a sample at three calls or fewer inside (unrounded midpoint, "
                   "point] passed by the rounding alone — recorded, not a falsification")
ROW_RULE_AT_MANDATE = ("rule failed: a sample at three calls or fewer, at its mandate, above the "
                       "point — the re-derived band is empty")
ROW_POINT_ABOVE_MANDATE = ("point failed inside a band that still holds it: a sample at three "
                           "calls or fewer, above its mandate, above the point")
ROW_RULE_OVERLAP = ("rule failed: a sample at three calls or fewer above the band's roof — the "
                    "three-call and four-call shapes overlap")
ROW_POINT_FOUR = ("point failed, rule survives: a sample at four calls or more under the point "
                  "and inside the band — the roof moved below it")
ROW_RULE_FOUR = "rule failed: a sample at four calls or more under the band's floor"
ROW_GRAIN_FALSIFIED = ("the grain: a sample at four calls or more inside (unrounded midpoint, "
                       "point] passed because the midpoint rounded up — the lesson is the "
                       "rounding, not the ceiling")

HEADER_RE = re.compile(r"^=== (?P<cmd>.*)$")
ANSWERS_RE = re.compile(r"--answers \S*?goldens-run-(?P<sample>\d)\.json")
CASE_RE = re.compile(r"^(?P<case>[a-z]+-\d{3})\s+(?P<result>PASS|FAIL|INFRA)(?:\s+\[(?P<samples>[A-Z ]+)\])?\s*$")
ASSERT_RE = re.compile(r"^\s+- (?P<kind>[a-z_]+): (?P<detail>.*)$")
BUDGET_RE = re.compile(r"(?P<axis>tokens_in|tokens_out)=(?P<value>\d+) over (?P<ceiling>\d+)")
CALLS_RE = re.compile(r"\(calls=(?P<calls>\d+)\)")
COUNT_RE = re.compile(r"^(?P<passed>\d+)/(?P<total>\d+) passed \((?P<failed>\d+) failed, (?P<infra>\d+) infra\)")
LATENCY_RE = re.compile(r"^suite latency\s+(?P<verdict>OK|OVER)\s+p95=(?P<p95>\d+)ms")


def _sha256(path: pathlib.Path) -> str:
    """LF-normalised: the committed text, not the checkout."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: pathlib.Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else path.name


def _census_module():
    spec = importlib.util.spec_from_file_location("context_census", CENSUS_READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("context_census", module)
    spec.loader.exec_module(module)
    return module


# --- the transcripts ----------------------------------------------------------------

def parse_transcript(text: str) -> list[dict]:
    """Every `=== command` block: the sample it scored (None for the k=3 block),
    each case's result and bracket, its failing asserts by kind, the count line
    and the suite latency line."""
    blocks: list[dict] = []
    block: dict | None = None
    case: dict | None = None
    for line in text.splitlines():
        header = HEADER_RE.match(line)
        if header:
            found = ANSWERS_RE.findall(header.group("cmd"))
            block = {"command": header.group("cmd"),
                     "sample": int(found[0]) if len(found) == 1 else None,
                     "cases": {}, "count": None, "latency": None}
            blocks.append(block)
            case = None
            continue
        if block is None:
            continue
        m = CASE_RE.match(line)
        if m:
            case = {"result": m.group("result"), "asserts": {},
                    "samples": m.group("samples").split() if m.group("samples") else None}
            block["cases"][m.group("case")] = case
            continue
        m = ASSERT_RE.match(line)
        if m and case is not None:
            case["asserts"][m.group("kind")] = m.group("detail")
            continue
        m = COUNT_RE.match(line)
        if m:
            block["count"] = {k: int(v) for k, v in m.groupdict().items()}
            continue
        m = LATENCY_RE.match(line)
        if m:
            block["latency"] = {"verdict": m.group("verdict"), "p95": int(m.group("p95"))}
    return blocks


def budget_axes(detail: str | None) -> dict[str, dict]:
    if not detail:
        return {}
    return {m.group("axis"): {"value": int(m.group("value")), "over": int(m.group("ceiling"))}
            for m in BUDGET_RE.finditer(detail)}


def budget_calls(detail: str | None) -> int | None:
    m = CALLS_RE.search(detail or "")
    return int(m.group("calls")) if m else None


# --- the ceiling, the band, the grain --------------------------------------------------

def live_ceiling(cases_text: str) -> int:
    values = {int(v) for v in re.findall(r"tokens_in:\s*(\d+)", cases_text)}
    if len(values) != 1:
        raise SystemExit(f"cases.yaml carries {len(values)} distinct tokens_in ceilings: {sorted(values)}")
    return values.pop()


def band_from(mandated_max: int, four_call_min: int | None) -> dict:
    """ADR-014's pinned rule, exactly as the derivation test executes it: floor
    1.15x the mandated-shape maximum, roof the lesser of 1.60x and one under the
    next call count's minimum, the point the midpoint rounded to the hundred."""
    floor = mandated_max * BAND[0]
    roof = mandated_max * BAND[1]
    if four_call_min is not None:
        roof = min(roof, four_call_min - 1)
    empty = floor > roof
    return {
        "mandated_shape_max": mandated_max,
        "four_call_min": four_call_min,
        "floor": round(floor, 3), "roof": round(roof, 3),
        "integer_band": None if empty else [int(-(-floor // 1)), int(roof // 1)],
        "empty": empty,
        "unrounded_midpoint": None if empty else round((floor + roof) / 2, 3),
        "point": None if empty else round(((floor + roof) / 2) / 100) * 100,
    }


def m08_reference(census: dict) -> dict:
    """The record's numbers the near-miss reading is measured against."""
    mandated_max = census[DECISION_RULE]["mandated_shape_tokens_in"]["max"]
    mandated_calls_max = max(int(c) for c in census[DECISION_RULE]["mandated_shape_tokens_in"]["by_calls"])
    four_call_min = census[BY_MILESTONE][STAGE2]["by_calls"][str(mandated_calls_max + 1)]["min"]
    three_call_max = max(r["tokens_in"] for r in census[PER_SAMPLE]
                         if r["answered"] and r["calls"] <= mandated_calls_max)
    band = band_from(mandated_max, four_call_min)
    return {**band, "mandated_calls_max": mandated_calls_max,
            "as_run_three_call_max": three_call_max,
            "gap": [three_call_max, four_call_min]}


def reading_for(calls: int, tokens_in: int, at_mandate: bool, ref: dict, ceiling: int) -> str:
    """Which of the six rows a sample is, or `pass`/`fail`/the grain near miss."""
    lo, hi = ref["integer_band"]
    unrounded = ref["unrounded_midpoint"]
    if calls <= ref["mandated_calls_max"]:
        if tokens_in <= ceiling:
            return GRAIN_NEAR_MISS if tokens_in > unrounded else PASS
        if tokens_in > hi:
            return ROW_RULE_OVERLAP
        return ROW_RULE_AT_MANDATE if at_mandate else ROW_POINT_ABOVE_MANDATE
    if tokens_in > ceiling:
        return FAIL
    if tokens_in > unrounded:
        return ROW_GRAIN_FALSIFIED
    if tokens_in >= lo:
        return ROW_POINT_FOUR
    return ROW_RULE_FOUR


def distances(tokens_in: int, ref: dict, ceiling: int) -> dict:
    lo, hi = ref["integer_band"]
    to_floor, to_roof = tokens_in - lo, hi - tokens_in
    nearer = "floor" if abs(to_floor) <= abs(to_roof) else "roof"
    return {"to_point": tokens_in - ceiling,
            "to_unrounded_midpoint": round(tokens_in - ref["unrounded_midpoint"], 3),
            "to_nearer_band_edge": to_floor if nearer == "floor" else to_roof,
            "nearer_band_edge": nearer}


# --- the rows ------------------------------------------------------------------------

def _refused(entry: dict) -> bool:
    answer = (entry or {}).get("answer")
    return isinstance(answer, dict) and "refused_by_gateway" in answer


def per_sample_rows(run_dir: pathlib.Path, cases: dict, blocks: list[dict], ceiling: int,
                    ref: dict, sidecar: dict) -> list[dict]:
    reader = _census_module()
    catalog = _load(CATALOG)
    clock = reader.client_constants()["CLOCK"]
    by_sample = {b["sample"]: b for b in blocks if b["sample"] is not None}
    refused_column = sidecar.get("per_sample_refused") or {}
    rows = []
    for n in (1, 2, 3):
        answers = _load(run_dir / f"goldens-run-{n}.json")
        trajectories = _load(run_dir / f"goldens-run-{n}-trajectory.json")
        block = by_sample.get(n)
        if block is None:
            raise SystemExit(f"per-sample.txt has no block for goldens-run-{n}.json")
        for case_id in sorted(answers):
            entry = answers[case_id]
            case = cases.get(case_id)
            if case is None:
                raise SystemExit(f"{case_id} is in the answer file and not in cases.yaml")
            scored = block["cases"].get(case_id)
            if scored is None:
                raise SystemExit(f"{case_id} sample {n} is in the answer file and not in its transcript block")
            steps = (trajectories.get(case_id) or {}).get("trajectory") or []
            rounds = max((s.get("round", 0) for s in steps), default=0)
            mandate = reader.mandated_calls(case)
            row = {"case": case_id, "sample": n, "mandated_calls": mandate,
                   "sample_result": scored["result"],
                   "other_failing_asserts": sorted(k for k in scored["asserts"] if k != "budget")}
            if _refused(entry):
                if not (refused_column.get(case_id) or [None] * 3)[n - 1]:
                    raise SystemExit(f"{case_id} sample {n} is refused in the answer file and not in "
                                     "the sidecar's per-sample column")
                rows.append({**row, "answered": False, "refused": True, "calls": None,
                             "at_mandate": None, "tokens_in": None, "per_call_tokens_in": None,
                             "tokens_in_verdict": None, "tokens_out_verdict": None,
                             "latency_ms": None, "distance": None, "reading": "refused",
                             "per_round_growth": [], "catalog_search_calls": sum(
                                 1 for s in steps if s.get("tool") == "catalog-search")})
                continue
            usage = entry.get("usage") or {}
            per_call = usage.get("calls")
            if not isinstance(per_call, list) or not per_call:
                raise SystemExit(f"{case_id} sample {n} carries no usage.calls; this reader joins the run "
                                 "the loop recorded, not a census")
            calls = len(per_call)
            if calls != rounds + 1:
                raise SystemExit(f"{case_id} sample {n}: usage.calls has {calls} rounds and the trajectory "
                                 f"implies {rounds + 1}; a planted call count")
            tokens_in = usage.get("tokens_in")
            if tokens_in != sum(c.get("tokens_in", 0) for c in per_call):
                raise SystemExit(f"{case_id} sample {n}: tokens_in {tokens_in} is not the sum over usage.calls")
            axes = budget_axes(scored["asserts"].get("budget"))
            printed_calls = budget_calls(scored["asserts"].get("budget"))
            if "tokens_in" in axes:
                if axes["tokens_in"]["over"] != ceiling:
                    raise SystemExit(f"{case_id} sample {n} was scored at {axes['tokens_in']['over']}, not the "
                                     f"live ceiling {ceiling}; a transcript from another ceiling")
                if axes["tokens_in"]["value"] != tokens_in or not tokens_in > ceiling:
                    raise SystemExit(f"{case_id} sample {n}: the transcript says tokens_in="
                                     f"{axes['tokens_in']['value']} over {ceiling} and the file says "
                                     f"{tokens_in}; a planted verdict")
                verdict_in = "FAIL"
            else:
                if tokens_in > ceiling:
                    raise SystemExit(f"{case_id} sample {n}: tokens_in {tokens_in} is over {ceiling} and the "
                                     "transcript printed no budget failure; a planted verdict")
                verdict_in = "PASS"
            if printed_calls is not None and printed_calls != calls:
                raise SystemExit(f"{case_id} sample {n}: the transcript says calls={printed_calls} and "
                                 f"usage.calls has {calls}")
            at_mandate = calls == mandate
            per_call_in = [c.get("tokens_in", 0) for c in per_call]
            growth = []
            for r in range(1, calls):
                added = sum(reader.replay(s, catalog, clock)["chars"]
                            for s in steps if s.get("round") == r)
                growth.append({"round": r + 1, "tokens_in": per_call_in[r],
                               "delta_tokens": per_call_in[r] - per_call_in[r - 1],
                               "replayed_chars_added": added})
            rows.append({
                **row, "answered": True, "refused": False, "calls": calls, "at_mandate": at_mandate,
                "tokens_in": tokens_in, "per_call_tokens_in": per_call_in,
                "tokens_out": usage.get("tokens_out"),
                "tokens_in_verdict": verdict_in,
                "tokens_out_verdict": "FAIL" if "tokens_out" in axes else "PASS",
                "latency_ms": usage.get("latency_ms"),
                "distance": distances(tokens_in, ref, ceiling),
                "reading": reading_for(calls, tokens_in, at_mandate, ref, ceiling),
                "per_round_growth": growth,
                "catalog_search_calls": sum(1 for s in steps if s.get("tool") == "catalog-search"),
            })
    return rows


# --- what the rows say -------------------------------------------------------------

def claim(rows: list[dict], ceiling: int, ref: dict) -> dict:
    answered = [r for r in rows if r["answered"]]
    few = [r for r in answered if r["calls"] <= ref["mandated_calls_max"]]
    many = [r for r in answered if r["calls"] > ref["mandated_calls_max"]]
    over = [f"{r['case']} s{r['sample']}" for r in few if r["tokens_in"] > ceiling]
    under = [f"{r['case']} s{r['sample']}" for r in many if r["tokens_in"] <= ceiling]
    falsifiers = [{"sample": f"{r['case']} s{r['sample']}", "calls": r["calls"], "tokens_in": r["tokens_in"],
                   "at_mandate": r["at_mandate"], "row": r["reading"]}
                  for r in answered if r["reading"] not in (PASS, FAIL, GRAIN_NEAR_MISS)]
    return {
        "ceiling": ceiling, "comparison": "got > limit (evals/deterministic.py::budget)",
        "answered_samples": len(answered),
        "samples_at_3_calls_or_fewer": len(few), "samples_at_4_calls_or_more": len(many),
        "3_call_or_fewer_samples_over": over, "4_call_or_more_samples_under": under,
        "largest_3_call_or_fewer_tokens_in": max((r["tokens_in"] for r in few), default=None),
        "smallest_4_call_or_more_tokens_in": min((r["tokens_in"] for r in many), default=None),
        "holds": not over and not under,
        "falsifiers": falsifiers,
        "grain_near_misses": [f"{r['case']} s{r['sample']}" for r in answered
                              if r["reading"] == GRAIN_NEAR_MISS],
    }


def fresh_band(rows: list[dict], ref: dict, ceiling: int) -> dict:
    answered = [r for r in rows if r["answered"]]
    at_mandate = [r["tokens_in"] for r in answered if r["at_mandate"]]
    beyond = [r["tokens_in"] for r in answered if r["calls"] > ref["mandated_calls_max"]]
    if not at_mandate:
        return {"available": False}
    band = band_from(max(at_mandate), min(beyond) if beyond else None)
    inside = (not band["empty"]) and band["floor"] <= ceiling <= band["roof"]
    return {"available": True, **band, "point_inside": inside,
            "reading": ("the rule has no solution for this shape" if band["empty"]
                        else "the number holds and the rule re-derives to it" if band["point"] == ceiling
                        else "the number holds inside the fresh band and the rule re-derives elsewhere"
                        if inside else "the number holds and the rule does not: 7700 is outside the "
                                       "band re-derived from the fresh run"),
            "note": "recorded, not ruled on: 7700 stands; a ceiling moved on a fresh run's band is a "
                    "re-derivation, and that is a census milestone"}


def count(blocks: list[dict], rows: list[dict], m08: dict) -> dict:
    k3 = next((b for b in blocks if b["sample"] is None), None)
    if k3 is None or k3["count"] is None:
        raise SystemExit("goldens-score.txt carries no k=3 block with a count line")
    m08_cases = {c["case"]: c for c in m08.get("per_case") or []}
    per_case, regressed, flipped = {}, [], []
    for case_id, scored in sorted(k3["cases"].items()):
        before = m08_cases.get(case_id) or {}
        before_samples = before.get("rescore_samples") or []
        entry = {"result": scored["result"], "samples": scored["samples"],
                 "m08_result": before.get("rescore_result"), "m08_samples": before_samples,
                 "calls_by_sample": [r["calls"] for r in rows if r["case"] == case_id]}
        if before_samples and all(s == "PASS" for s in before_samples) and scored["result"] != "PASS":
            regressed.append(case_id)
        if before_samples and all(s == "FAIL" for s in before_samples) and scored["result"] == "PASS":
            flipped.append(case_id)
        per_case[case_id] = entry
    n = k3["count"]["passed"]
    return {"k3": k3["count"], "N": n, "band": list(COUNT_BAND), "predicted": PREDICTED_N,
            "in_band": COUNT_BAND[0] <= n <= COUNT_BAND[1],
            "falsifiers": {"N_outside_band": not (COUNT_BAND[0] <= n <= COUNT_BAND[1]),
                           "3_of_3_pass_at_m08_failing_by_majority": regressed,
                           "0_of_3_fail_at_m08_passing_by_majority": flipped},
            "per_case": per_case}


def refusals(sidecar: dict) -> dict:
    column = sidecar.get("per_sample_refused") or {}
    by_majority = sorted(c for c, s in column.items() if sum(1 for x in s if x) >= 2)
    census = sidecar.get("census") or {}
    if census.get("refused_by_majority") != len(by_majority) or \
            sorted(census.get("cases_by_majority") or []) != by_majority:
        raise SystemExit("the sidecar's census disagrees with its own per-sample column")
    return {"by_majority": len(by_majority), "cases": by_majority, "band": list(REFUSAL_BAND),
            "in_band": len(by_majority) <= REFUSAL_BAND[1]}


def p95s(rows: list[dict], blocks: list[dict], ceiling_ms: int) -> dict:
    def statistic(population):
        answers = {f"s{i}": {"usage": {"latency_ms": ms}} for i, ms in enumerate(population)}
        result = deterministic.suite_latency(answers, ceiling_ms)
        m = re.match(r"p95=(\d+)ms", result.detail)
        return {"n": len(population), "p95": int(m.group(1)) if m else None,
                "verdict": "within" if result.passed else "OVER"}
    answered = [r for r in rows if r["answered"] and r["latency_ms"] is not None]
    pooled = statistic([r["latency_ms"] for r in answered])
    mandated = statistic([r["latency_ms"] for r in answered if r["at_mandate"]])
    k3 = next((b for b in blocks if b["sample"] is None), None)
    printed = (k3 or {}).get("latency")
    if printed and printed["p95"] != pooled["p95"]:
        raise SystemExit(f"goldens-score.txt prints p95={printed['p95']} and the answer files pool to "
                         f"{pooled['p95']}")
    if mandated["verdict"] == "OVER":
        reading = ("drift: the mandated shape's own tail is over the ceiling — a dated finding for "
                   "Platform Engineering, and the rule's premise (the mandated shape's tail is "
                   "stable across runs) is what failed")
    elif pooled["verdict"] == "OVER":
        reading = ("share: the pooled tail is over the ceiling and the mandated shape's is not — "
                   "the browse gap's, ADR-074 decision 2's")
    else:
        reading = "within, both populations"
    return {"ceiling_ms": ceiling_ms, "pooled": pooled, "mandated_shape": mandated,
            "transcript_line": printed, "reading": reading, "costs_a_case": False}


def triggers(rows: list[dict]) -> dict:
    max_mandate = max(r["mandated_calls"] for r in rows)
    browse = [r for r in rows if r["answered"] and r["calls"] > max_mandate
              and r["catalog_search_calls"] > 1]
    on_seven = [r for r in browse if r["case"] in BROWSE_GAP_SEVEN]
    elsewhere = sorted({r["case"] for r in browse if r["case"] not in BROWSE_GAP_SEVEN})
    five = {}
    for case_id in TOKENS_OUT_FIVE:
        verdicts = [r["tokens_out_verdict"] for r in rows if r["case"] == case_id and r["answered"]]
        five[case_id] = {"tokens_out_verdicts": verdicts,
                         "fails_by_majority": sum(1 for v in verdicts if v == "FAIL") >= 2}
    return {
        "browse_gap": {"persists": bool(on_seven),
                       "samples": [f"{r['case']} s{r['sample']}" for r in on_seven],
                       "cases": sorted({r["case"] for r in on_seven}),
                       "m08_count": {"samples": 14, "cases": 7},
                       "four_call_samples_outside_the_seven": elsewhere},
        "tokens_out_five": {"persists": any(v["fails_by_majority"] for v in five.values()),
                            "cases": five, "m08_count": 5},
        "note": "read, not diagnosed (SPEC/08b constraint 9)",
    }


def join(run_dir: pathlib.Path) -> dict:
    # Resolved, so a relative `--dir` and an absolute one name their inputs the
    # same way in `inputs_sha256` (repository-relative when inside it).
    run_dir = pathlib.Path(run_dir).resolve()
    needed = [run_dir / f"goldens-run-{n}.json" for n in (1, 2, 3)] + \
             [run_dir / f"goldens-run-{n}-trajectory.json" for n in (1, 2, 3)] + \
             [run_dir / "goldens-run-refusals.json", run_dir / "per-sample.txt", run_dir / "goldens-score.txt"]
    for path in needed:
        if not path.is_file():
            raise SystemExit(f"{_rel(path)} does not exist; the run has not been committed")
    cases_text = CASES.read_text(encoding="utf-8")
    cases = {c["id"]: c for c in yaml.safe_load(cases_text)}
    ceiling = live_ceiling(cases_text)
    census = _load(CENSUS)
    ref = m08_reference(census)
    if ref["point"] != ceiling:
        raise SystemExit(f"the live ceiling is {ceiling} and the pinned point rule produces {ref['point']}; "
                         "no sample is read at any ceiling but the one the rule produces")
    sidecar = _load(run_dir / "goldens-run-refusals.json")
    per_sample_blocks = parse_transcript((run_dir / "per-sample.txt").read_text(encoding="utf-8"))
    k3_blocks = parse_transcript((run_dir / "goldens-score.txt").read_text(encoding="utf-8"))
    rows = per_sample_rows(run_dir, cases, per_sample_blocks, ceiling, ref, sidecar)
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    inputs = needed + [CASES, CENSUS, M08_JOIN, MANIFEST, CATALOG]
    return {
        "_what_this_is": (
            "SPEC/08b's one claim, read per sample from the fresh run by milestones/M08b/fresh_join.py: "
            "every answered sample at three calls or fewer under the ceiling and every sample at four "
            "or more over it, with the pre-registered reading of any falsifying sample, the fresh "
            "re-derived band, the count and refusal bands, the two p95s, per-round growth, and the "
            "two triggers. Computed from the rows, never asserted; refuses a planted verdict, a "
            "planted call count and a foreign ceiling."),
        "inputs_sha256": {_rel(p): _sha256(p) for p in inputs},
        "ceiling": ceiling,
        "m08_reference": ref,
        "grain": [ref["unrounded_midpoint"], ceiling],
        "claim": claim(rows, ceiling, ref),
        "fresh_band": fresh_band(rows, ref, ceiling),
        "count": count(k3_blocks, rows, _load(M08_JOIN)),
        "refusals": refusals(sidecar),
        "p95": p95s(rows, k3_blocks, manifest["gates"]["budgets"]["p95_ms"]),
        "triggers": triggers(rows),
        "per_sample": rows,
    }


def render(rec: dict) -> str:
    c, b, n, r, p = rec["claim"], rec["fresh_band"], rec["count"], rec["refusals"], rec["p95"]
    lines = [
        f"claim at {rec['ceiling']}: {'HOLDS' if c['holds'] else 'FALSIFIED'} — "
        f"{c['samples_at_3_calls_or_fewer']} samples at ≤3 calls (max {c['largest_3_call_or_fewer_tokens_in']}), "
        f"{c['samples_at_4_calls_or_more']} at ≥4 (min {c['smallest_4_call_or_more_tokens_in']})",
    ]
    for f in c["falsifiers"]:
        lines.append(f"  falsifier {f['sample']}: {f['calls']} calls, tokens_in {f['tokens_in']}, "
                     f"{'at' if f['at_mandate'] else 'above'} mandate — {f['row']}")
    for g in c["grain_near_misses"]:
        lines.append(f"  grain near miss: {g}")
    if b.get("available"):
        lines.append(f"fresh band: mandated max {b['mandated_shape_max']}, four-call min {b['four_call_min']}, "
                     f"band {b['integer_band']}, point {b['point']}; 7700 inside: {b['point_inside']} — {b['reading']}")
    lines.append(f"count: N = {n['N']} (band {n['band']}, predicted {n['predicted']}, in band: {n['in_band']}); "
                 f"regressed {n['falsifiers']['3_of_3_pass_at_m08_failing_by_majority']}, "
                 f"flipped {n['falsifiers']['0_of_3_fail_at_m08_passing_by_majority']}")
    lines.append(f"refused by majority: {r['by_majority']} {r['cases']} (band {r['band']})")
    lines.append(f"p95 against {p['ceiling_ms']}: pooled {p['pooled']['p95']} ({p['pooled']['verdict']}, n={p['pooled']['n']}); "
                 f"mandated shape {p['mandated_shape']['p95']} ({p['mandated_shape']['verdict']}, n={p['mandated_shape']['n']}) — {p['reading']}")
    t = rec["triggers"]
    lines.append(f"browse gap persists: {t['browse_gap']['persists']} {t['browse_gap']['samples']}; "
                 f"tokens_out five persist: {t['tokens_out_five']['persists']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dir", default=str(HERE), help="the run directory (default: milestones/M08b)")
    parser.add_argument("--check", action="store_true",
                        help="recompute and compare with the committed record; write nothing; exit 1 on drift")
    args = parser.parse_args(argv)
    run_dir = pathlib.Path(args.dir)
    rec = join(run_dir)
    text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
    out = run_dir / OUT_NAME
    if args.check:
        committed = out.read_text(encoding="utf-8") if out.exists() else ""
        if committed != text:
            print(f"DRIFT: {out} differs from what the committed inputs produce")
            return 1
        print(f"OK: {out} is what the committed inputs produce")
        return 0
    out.write_text(text, encoding="utf-8", newline="\n")
    print(render(rec))
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

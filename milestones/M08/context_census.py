"""
`python milestones/M08/context_census.py` — where the tools arm's `tokens_in` goes.

**A census, not a measurement.** Zero model calls, no network, no deploy: every
number is read off files already committed under `milestones/`, or replayed from
the repo's own pure modules over the committed catalog. It exists because M07
closed with all 22 answered-and-wrong stage-2 cases over the 6000 `tokens_in`
ceiling (6022–9220), and the journal handed M08 one question: is the context or
the ceiling the thing to change. SPEC/08 is written after this prints.

**What is exact, what is replayed, what is estimated — labelled on every row.**

- *Exact*: `usage.tokens_in` / `tokens_out` / `latency_ms` (and `guard_ms`,
  `tool_ms` where a run recorded them) per answered sample; rounds and tool
  steps from the committed trajectory; the titles the answer cited. Bedrock
  reports `inputTokens` per `converse` call and `core/toolloop.py::_accumulate`
  sums them over the turn, so a three-call turn's `tokens_in` is three prompts.
- *Replayed*: each recorded `catalog-search` and `entitlement-check` step is
  re-run through the committed pure module with its recorded arguments over
  `data/catalog.json` (unchanged since m00a), so the tool result the model was
  handed is known byte for byte. `entitlement-check` takes the evaluation clock
  every module pins.
- *Estimated*: the text components of one call — the system prompt, the offered
  tool specs, the viewer's turn — are counted in characters and converted with a
  chars-per-token figure calibrated on ADR-014's committed anchors: six golden
  cases whose single-call control prompt was measured on the same model. The
  remainder of the per-call base, once those are subtracted, is reported as
  **residual — not in any committed text the client or gateway sends** and is
  not attributed to a cause here.

**What it refuses to print.** No pass count at any ceiling other than 6000.
A census that prints "17/25 at 7000, 21/25 at 8000" is a search for the number
that clears the count, which is the trade G9 exists to refuse; the ceiling, if
it moves, is derived from the *shape* this prints by ADR-014's pinned rule, in
an ADR, on two keys, and re-scored afterwards (SPEC/08).

**The rule that reads it** is pre-registered in SPEC/08 and repeated in
`decision_rule()` below so the record carries its own reading: outcome A (the
agent carries context it does not need) holds only if *evidenced* removable
content — replayed rows the answer never cited, text sent twice in one request,
content the manifest does not declare — covers the gap at the mandated call
count; otherwise outcome B (the ceiling was derived for a shape that no longer
exists). Schema prose and tool descriptions are design, not evidence.

Hermetic (G8). Reads nothing under the withheld store and prints no model text.
Modifies nothing under `milestones/M07/`. Owning seats: AI Quality (the budget
axis) · Platform Engineering (the loop whose shape this describes) · PM (the
milestone it opens).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import pathlib
import statistics
import sys
from collections import Counter, defaultdict

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "catalog-search"))
sys.path.insert(0, str(ROOT / "tools" / "entitlement-check"))
import entitlement  # noqa: E402
import search  # noqa: E402

OUT = ROOT / "milestones" / "M08" / "context-census.json"
CATALOG = ROOT / "data" / "catalog.json"
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
CLIENT = ROOT / "services" / "highlights-agent" / "gateway_client.py"
ANSWER_SCHEMA = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"
CONTRACTS = ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
LOOP_SHAPE = ROOT / "milestones" / "M02" / "loop-shape.json"

#: The ceiling every golden case carries (ADR-014, M02 amendment). The one
#: number this file compares against, and the only one it ever will.
CEILING = 6000

#: ADR-014, "How the numbers were derived": input tokens measured on
#: 2026-08-15 against the pinned Haiku profile, sending the committed single-call
#: control prompt (system + answer schema + the whole catalog) and the case's
#: viewer turn. The only committed pairing of a prompt this repo can rebuild
#: byte for byte with a token count the same model reported, so it is the
#: calibration for every *estimated* row. Six cases, not one, so the figure is a
#: band rather than a point.
ADR_014_ANCHORS = {
    "concise-022": 1168, "blackout-001": 1171, "recommend-003": 1172,
    "multi-023": 1181, "headroom-026": 1177, "edge-025": 1163,
}

#: The runs, oldest first. `offered` is what the gateway's `toolConfig` carried
#: on that run: M02 deployed `catalog-search` alone (ADR-014 amendment, SPEC/02);
#: `entitlement-check` was deployed at M06b and `evals/history/
#: m07-tools-goldens.json::tool_surface.routed` names both for M07. M06 is the
#: single-call arm — the catalog inlined, no tools, no trajectory file — and is
#: here because the M07 journal's "about 1.2k" is that arm's number.
RUNS = (
    {"key": "m02-tools", "label": "M02 tools arm (2026-08-19)",
     "dir": "milestones/M02/runs", "stem": "m02-tools-{n}", "trajectory": True,
     "offered": ("catalog-search",)},
    {"key": "m06", "label": "M06 single-call arm (2026-08-30)",
     "dir": "milestones/M06", "stem": "goldens-run-{n}", "trajectory": False,
     "offered": ()},
    {"key": "m06b", "label": "M06b tools arm (2026-09-01)",
     "dir": "milestones/M06b", "stem": "goldens-run-{n}", "trajectory": True,
     "offered": ("catalog-search", "entitlement-check")},
    {"key": "m07-stage1", "label": "M07 stage 1 (2026-09-06)",
     "dir": "milestones/M07/stage1", "stem": "goldens-run-{n}", "trajectory": True,
     "offered": ("catalog-search", "entitlement-check")},
    {"key": "m07-stage2", "label": "M07 stage 2 (2026-09-06)",
     "dir": "milestones/M07", "stem": "goldens-run-{n}", "trajectory": True,
     "offered": ("catalog-search", "entitlement-check")},
)
SUBJECT = "m07-stage2"


# --- committed text, rebuilt the way the client and gateway send it -------------

def _string_constant(source: str, name: str) -> str:
    """`NAME = \"\"\"...\"\"\"` out of a module's source, without importing it.

    `gateway_client.py` imports boto3 at module level — it is outside the
    hermetic surface by its own docstring — so the two constants this needs are
    read off its AST. `tests/test_m08_census.py` pins that what is read here is
    what the imported module says."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == name \
                    and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return node.value.value
    raise SystemExit(f"{CLIENT.name} defines no string constant {name}")


def client_constants() -> dict:
    source = CLIENT.read_text(encoding="utf-8")
    return {name: _string_constant(source, name) for name in ("SYSTEM", "TOOL_SYSTEM", "CLOCK")}


def tool_prompt(constants: dict) -> str:
    """`gateway_client.build_tool_prompt()`: the M02 arm's system block."""
    return constants["TOOL_SYSTEM"].format(schema=ANSWER_SCHEMA.read_text(encoding="utf-8"))


def control_prompt(constants: dict) -> str:
    """`gateway_client.build_prompt()`: the control's, catalog inlined — the
    shape ADR-014's anchors were measured on."""
    return constants["SYSTEM"].format(schema=ANSWER_SCHEMA.read_text(encoding="utf-8"),
                                      catalog=CATALOG.read_text(encoding="utf-8"))


def user_turn(constants: dict, case: dict) -> str:
    """`gateway_client.user_turn()`, reproduced: one f-string, pinned by the
    test against the real function."""
    viewer = case.get("viewer") or {}
    return (f"Viewer plan={viewer.get('plan')} dma={viewer.get('dma')}. "
            f"Evaluation clock {constants['CLOCK']}.\n{case['input']}")


def tool_config(offered) -> dict | None:
    """`handler.tool_config()`, reproduced: Bedrock's `toolConfig`, one
    `toolSpec` per offered tool, the committed input contract as the schema the
    model reads. The handler cannot be imported without a deployment
    environment; the six lines are copied and the test pins the shape."""
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    specs = []
    for tool_id in offered:
        contract = contracts[tool_id]["input"]
        specs.append({"toolSpec": {"name": tool_id,
                                   "description": contract.get("description", tool_id),
                                   "inputSchema": {"json": contract}}})
    return {"tools": specs} if specs else None


def _as_sent(payload) -> str:
    """A tool result enters the transcript as a `{"json": payload}` block
    (`core/toolloop.py::_tool_result`); its size is the serialised payload."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


# --- replay ----------------------------------------------------------------------

def replay(step: dict, catalog: dict, clock: str) -> dict:
    """Re-run one recorded tool step through the committed pure module."""
    if step.get("decision") != "allowed" or not step.get("executed", True):
        return {"replayed": False, "chars": 0, "rows": None, "ids": []}
    if step["tool"] == "catalog-search":
        result = search.search(step["args"], catalog)
        rows = result.get("results") if isinstance(result, dict) else result
        rows = rows or []
        return {"replayed": True, "chars": len(_as_sent(result)), "rows": len(rows),
                "ids": [r.get("id") for r in rows if isinstance(r, dict)]}
    if step["tool"] == "entitlement-check":
        result = entitlement.check(step["args"], catalog, clock)
        return {"replayed": True, "chars": len(_as_sent(result)), "rows": None, "ids": []}
    return {"replayed": False, "chars": 0, "rows": None, "ids": []}


# --- reading the runs ---------------------------------------------------------------

def _load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mandated_calls(case: dict) -> int:
    """The fewest model calls a case can be answered in on this arm without
    failing an assert that names a tool: one to ask `catalog-search` (the
    system prompt permits no other source of a title), one more when the case
    expects `entitlement-check` before the answer (its argument is a title id
    the search returned, so it cannot share the search's round), and the
    answer. Two or three; never one."""
    trajectory = case.get("trajectory") or {}
    return 2 + (1 if trajectory.get("expect_tool_before_answer") == "entitlement-check" else 0)


def read_run(run: dict, cases: dict, catalog: dict, clock: str, inputs: dict) -> list[dict]:
    """Every sample of a run as one row. Refused samples are kept, marked, and
    excluded from every token statistic: the harness writes `tokens_in: 0` for a
    turn the guardrail ended, and a zero in a budget census is a lie in the
    flattering direction."""
    rows = []
    base = ROOT / run["dir"]
    for n in (1, 2, 3):
        answers_path = base / (run["stem"].format(n=n) + ".json")
        answers = _load(answers_path)
        inputs[str(answers_path.relative_to(ROOT)).replace("\\", "/")] = _sha256(answers_path)
        trajectories = {}
        if run["trajectory"]:
            traj_path = base / (run["stem"].format(n=n) + "-trajectory.json")
            trajectories = _load(traj_path)
            inputs[str(traj_path.relative_to(ROOT)).replace("\\", "/")] = _sha256(traj_path)
        for case_id, record in answers.items():
            if not isinstance(record, dict) or "usage" not in record:
                continue
            usage = record.get("usage") or {}
            tokens_in = usage.get("tokens_in") or 0
            steps = (trajectories.get(case_id) or {}).get("trajectory") or []
            rounds = max((s.get("round", 0) for s in steps), default=0)
            answered = tokens_in > 0
            replayed = [dict(step, **replay(step, catalog, clock)) for step in steps]
            cited = (record.get("answer") or {}).get("cited_titles") or []
            returned_ids = [i for r in replayed for i in r["ids"]]
            rows.append({
                "run": run["key"], "case": case_id, "sample": n,
                "answered": answered,
                "calls": (rounds + 1) if answered else None,
                "rounds": rounds,
                "steps": len(steps),
                "tools": dict(Counter(s["tool"] for s in steps)),
                "tokens_in": tokens_in if answered else None,
                "tokens_out": (usage.get("tokens_out") or 0) if answered else None,
                "latency_ms": usage.get("latency_ms") if answered else None,
                "guard_ms": usage.get("guard_ms"),
                "tool_ms": usage.get("tool_ms"),
                "replayed_chars": sum(r["chars"] for r in replayed),
                "replayed_steps": [{"round": r.get("round"), "seq": r.get("seq"),
                                    "tool": r["tool"], "chars": r["chars"], "rows": r["rows"]}
                                   for r in replayed],
                "rows_returned": sum(r["rows"] or 0 for r in replayed),
                "rows_returned_not_cited": len([i for i in returned_ids if i not in cited]),
                "cited": list(cited),
                "mandated_calls": mandated_calls(cases[case_id]) if case_id in cases else None,
                "over_ceiling": (tokens_in > CEILING) if answered else None,
            })
    return rows


# --- the tables ----------------------------------------------------------------------

def _median(values):
    return statistics.median(values) if values else None


def by_calls(rows: list[dict]) -> dict:
    """`tokens_in` by model calls per turn. Exact."""
    buckets = defaultdict(list)
    for r in rows:
        if r["answered"]:
            buckets[r["calls"]].append(r["tokens_in"])
    out = {}
    for calls in sorted(buckets):
        values = sorted(buckets[calls])
        out[str(calls)] = {"n": len(values), "min": values[0], "median": _median(values),
                           "max": values[-1], "per_call_median": round(_median(values) / calls)}
    return out


def ceiling_position(table: dict) -> dict:
    """Between which call counts 6000 sits: the largest bucket entirely under it
    and the smallest bucket entirely over it, or the bucket it splits."""
    under = [int(c) for c, b in table.items() if b["max"] <= CEILING]
    over = [int(c) for c, b in table.items() if b["min"] > CEILING]
    split = [int(c) for c, b in table.items() if b["min"] <= CEILING < b["max"]]
    return {"entirely_under": max(under) if under else None,
            "entirely_over": min(over) if over else None,
            "split_by_ceiling": sorted(split)}


def marginal_call(rows: list[dict], table: dict) -> dict:
    """What one more model call costs, two ways: the difference between adjacent
    call-count medians, and — exact within a case — the paired difference where
    the same case answered at two call counts in one run."""
    medians = {int(c): b["median"] for c, b in table.items()}
    adjacent = {f"{c}->{c + 1}": round(medians[c + 1] - medians[c])
                for c in sorted(medians) if c + 1 in medians}
    paired = []
    by_case = defaultdict(list)
    for r in rows:
        if r["answered"]:
            by_case[r["case"]].append(r)
    for case, samples in sorted(by_case.items()):
        counts = sorted({s["calls"] for s in samples})
        for a, b in zip(counts, counts[1:], strict=False):
            lo = _median([s["tokens_in"] for s in samples if s["calls"] == a])
            hi = _median([s["tokens_in"] for s in samples if s["calls"] == b])
            paired.append({"case": case, "calls": f"{a}->{b}", "delta": round(hi - lo)})
    return {"adjacent_medians": adjacent, "within_case": paired,
            "within_case_median_delta": _median([p["delta"] for p in paired
                                                 if p["calls"].endswith(str(int(p["calls"][0]) + 1))])}


def calibration(constants: dict, cases: dict) -> dict:
    """Chars per token, from ADR-014's six anchors. Estimated rows use the band."""
    points = []
    control = control_prompt(constants)
    for case_id, tokens in ADR_014_ANCHORS.items():
        chars = len(control) + len(user_turn(constants, cases[case_id]))
        points.append({"case": case_id, "chars": chars, "tokens_measured": tokens,
                       "chars_per_token": round(chars / tokens, 3)})
    ratios = [p["chars_per_token"] for p in points]
    return {"source": "ADR-014 'How the numbers were derived', 2026-08-15, single-call control "
                      "prompt (system + answer schema + catalog) + viewer turn, input tokens as "
                      "Bedrock reported them",
            "points": points, "chars_per_token": {"min": min(ratios), "median": _median(ratios),
                                                  "max": max(ratios)}}


def _est(chars: int, cal: dict) -> dict:
    cpt = cal["chars_per_token"]
    return {"chars": chars, "tokens_est": round(chars / cpt["median"]),
            "tokens_est_band": [round(chars / cpt["max"]), round(chars / cpt["min"])]}


def components(run: dict, constants: dict, cases: dict, cal: dict) -> dict:
    """The text one call carries, per component. Estimated (chars, calibrated)."""
    prompt = tool_prompt(constants)
    config = tool_config(run["offered"])
    specs = {}
    for spec in (config or {}).get("tools", ()):
        name = spec["toolSpec"]["name"]
        specs[name] = _est(len(json.dumps(spec["toolSpec"], ensure_ascii=False)), cal)
    turns = [len(user_turn(constants, c)) for c in cases.values()]
    return {
        "system_prompt": dict(_est(len(prompt), cal),
                              of_which_answer_schema=_est(len(ANSWER_SCHEMA.read_text(encoding="utf-8")), cal)),
        "tool_specs": specs,
        "tool_specs_total": _est(sum(len(json.dumps(s["toolSpec"], ensure_ascii=False))
                                     for s in (config or {}).get("tools", ())), cal),
        "viewer_turn": dict(_est(round(_median(turns)), cal), chars_min=min(turns), chars_max=max(turns)),
    }


def per_call_base(rows: list[dict], cal: dict, comp: dict) -> dict:
    """The per-call base bounded from the two-call samples, exactly: the first
    call carries the base alone; the second carries the base plus the model's
    first output and the replayed result. So base <= T/2 and
    base >= (T - tokens_out - result_tokens)/2, with the result converted at the
    calibration's most generous ratio so the lower bound is a bound."""
    two = [r for r in rows if r["answered"] and r["calls"] == 2]
    if not two:
        return {"n": 0}
    uppers = [r["tokens_in"] / 2 for r in two]
    lowers = [(r["tokens_in"] - r["tokens_out"]
               - r["replayed_chars"] / cal["chars_per_token"]["min"]) / 2 for r in two]
    upper, lower = round(_median(uppers)), round(_median(lowers))
    explained = (comp["system_prompt"]["tokens_est"] + comp["tool_specs_total"]["tokens_est"]
                 + comp["viewer_turn"]["tokens_est"])
    return {
        "n": len(two),
        "upper_median": upper, "lower_median": lower,
        "explained_by_committed_text_est": explained,
        "residual_est": {"lower": lower - explained, "upper": upper - explained,
                         "note": "not in any committed text the client or gateway sends; "
                                 "not attributed to a cause by this census"},
    }


def latency(rows: list[dict]) -> dict:
    """Secondary: the suite's latency by component, for the p95 disposition the
    M07 journal dates to SPEC/08. `latency_ms` is model time summed over calls
    (`_accumulate`); `tool_ms` and `guard_ms` are their own keys and are not in
    it (`core/toolloop.py::run_turn`). p95 is nearest-rank over answered samples,
    as `evals/deterministic.py::suite_latency` computes it per file."""
    answered = [r for r in rows if r["answered"] and r["latency_ms"] is not None]
    buckets = defaultdict(list)
    for r in answered:
        buckets[r["calls"]].append(r)
    out = {"by_calls": {}}
    for calls in sorted(buckets):
        rs = buckets[calls]
        out["by_calls"][str(calls)] = {
            "n": len(rs),
            "latency_ms_median": _median([r["latency_ms"] for r in rs]),
            "tool_ms_median": _median([r["tool_ms"] for r in rs if r["tool_ms"] is not None]),
            "guard_ms_median": _median([r["guard_ms"] for r in rs if r["guard_ms"] is not None]),
        }
    per_file = defaultdict(list)
    for r in answered:
        per_file[r["sample"]].append(r["latency_ms"])
    out["p95_per_answer_file"] = {
        str(n): sorted(v)[max(0, math.ceil(0.95 * len(v)) - 1)] for n, v in sorted(per_file.items())}
    everything = sorted(r["latency_ms"] for r in answered)
    out["p95_pooled"] = everything[max(0, math.ceil(0.95 * len(everything)) - 1)]
    return out


def removable_evidence(rows: list[dict], constants: dict, run: dict, cal: dict) -> dict:
    """The only evidence outcome A may cite, sized per call (SPEC/08).

    (i) replayed rows the answer never cited — content the platform handed the
    model that the answer demonstrably did not use; (ii) text sent twice in one
    request — any line of 40+ characters shared between two components; (iii)
    content sent that the manifest does not declare — offered tools outside the
    manifest's `tools`. Everything else in the base is design, not evidence."""
    answered = [r for r in rows if r["answered"]]
    prompt = tool_prompt(constants)
    config = tool_config(run["offered"]) or {"tools": []}
    spec_text = json.dumps(config, ensure_ascii=False, indent=1)
    # (i) rows returned and not cited: their share of the replayed result, carried
    # on every call after the one that returned them.
    uncited_tokens_per_call = []
    for r in answered:
        if r["rows_returned"]:
            share = r["rows_returned_not_cited"] / r["rows_returned"]
            search_chars = sum(s["chars"] for s in r["replayed_steps"] if s["tool"] == "catalog-search")
            carried_calls = max(0, r["calls"] - 1)
            uncited_tokens_per_call.append(
                share * search_chars / cal["chars_per_token"]["median"] * carried_calls / r["calls"])
        else:
            uncited_tokens_per_call.append(0.0)
    # (ii) duplicated text across components.
    def lines(text):
        return {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 40}
    shared = lines(prompt) & lines(spec_text)
    # (iii) offered tools the manifest does not declare.
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    declared = {t["id"].split("@")[0] for t in manifest.get("tools", [])}
    undeclared = sorted(set(run["offered"]) - declared)
    return {
        "rows_returned_not_cited": {
            "samples_with_any": sum(1 for r in answered if r["rows_returned_not_cited"]),
            "tokens_per_call_est_max": round(max(uncited_tokens_per_call), 1) if uncited_tokens_per_call else 0,
            "tokens_per_call_est_median": round(_median(uncited_tokens_per_call), 1) if uncited_tokens_per_call else 0,
        },
        "text_sent_twice": {"shared_lines_40plus_chars": sorted(shared),
                            "tokens_per_call_est": _est(sum(len(s) for s in shared), cal)["tokens_est"]},
        "undeclared_tools_offered": undeclared,
        "removable_tokens_per_call_est": round(
            (max(uncited_tokens_per_call) if uncited_tokens_per_call else 0)
            + _est(sum(len(s) for s in shared), cal)["tokens_est"], 1),
    }


def decision_rule(rows: list[dict], removable: dict, cal: dict) -> dict:
    """SPEC/08's pre-registered reading, applied **per sample**.

    A sample's gap is its excess over 6000 spread over its calls; its removable
    content is what *its own* request carried that the evidence says it did not
    need — its uncited replayed rows (carried on every call after the one that
    returned them) plus the text every request sends twice. Outcome A holds iff
    every answered sample at its case's mandated call count that is over the
    ceiling is covered by its own removable content.

    **Why per sample, recorded because the first run of this reader did it the
    other way.** The first run compared the largest removable amount in the run
    (grounded-018, two and three rows returned and none cited) against the
    largest gap in the run (blackout-008, one row returned and cited) and
    printed A. That reading is incoherent with A's own pre-registered
    falsifier — "after the change, zero samples at the mandated call count over
    6000" — because a sample that carried nothing removable cannot be brought
    under the ceiling by removing it: 33 of 33 over-ceiling samples at the
    mandated count carry zero uncited rows. Both figures stay in the record; the
    rule reads the per-sample one."""
    at_mandate = [r for r in rows if r["answered"] and r["calls"] == r["mandated_calls"]]
    above = [r for r in rows if r["answered"] and r["calls"] > r["mandated_calls"]]
    shared_per_call = removable["text_sent_twice"]["tokens_per_call_est"]
    over = []
    for r in at_mandate:
        if not r["over_ceiling"]:
            continue
        gap = (r["tokens_in"] - CEILING) / r["calls"]
        own = 0.0
        if r["rows_returned"]:
            share = r["rows_returned_not_cited"] / r["rows_returned"]
            search_chars = sum(s["chars"] for s in r["replayed_steps"] if s["tool"] == "catalog-search")
            own = share * search_chars / cal["chars_per_token"]["median"] * (r["calls"] - 1) / r["calls"]
        own += shared_per_call
        over.append({"case": r["case"], "sample": r["sample"], "calls": r["calls"],
                     "tokens_in": r["tokens_in"], "gap_per_call": round(gap, 1),
                     "own_removable_per_call_est": round(own, 1), "covered": own >= gap})
    covered = sum(1 for o in over if o["covered"])
    gap_max = max((o["gap_per_call"] for o in over), default=0)
    if not over:
        outcome, reading = "neither", "no answered sample at its mandated call count is over the ceiling"
    elif covered == len(over):
        outcome = "A"
        reading = ("A: every over-ceiling sample at the mandated call count is covered by its own "
                   "evidenced removable content; fix the agent, ceiling unchanged")
    else:
        outcome = "B"
        reading = (f"B: {len(over) - covered} of {len(over)} over-ceiling samples at the mandated call "
                   "count carry no evidenced removable content that covers their gap; the ceiling "
                   "was derived for a shape that no longer exists (ADR-014, M02 amendment) and is "
                   "re-derived from this record by the pinned rule, in an ADR, on two keys")
    return {
        "samples_at_mandated_calls": len(at_mandate),
        "of_which_over_ceiling": len(over),
        "of_which_covered_by_own_removable_content": covered,
        "samples_above_mandated_calls": len(above),
        "above_mandate_over_ceiling": sum(1 for r in above if r["over_ceiling"]),
        "mandated_shape_tokens_in": {
            "max": max((r["tokens_in"] for r in at_mandate), default=None),
            "by_calls": by_calls(at_mandate)},
        "above_mandate_tokens_in_min": min((r["tokens_in"] for r in above), default=None),
        "gap_per_call_max": gap_max,
        "cross_sample_reading_not_the_rule": {
            "removable_per_call_est_max_any_sample": removable["removable_tokens_per_call_est"],
            "note": "the first run of this reader compared this figure with gap_per_call_max and "
                    "printed A; see decision_rule.__doc__"},
        "per_sample": over,
        "outcome": outcome,
        "reading": reading,
    }


def attribution(tables: dict) -> dict:
    """The tools arm's own growth, M02 -> M07 stage 2, as two factors — and the
    M06 figure placed where it belongs."""
    m02, s2 = tables["m02-tools"], tables[SUBJECT]
    def modal(table):
        return max(table, key=lambda c: table[c]["n"])
    calls_m02, calls_s2 = modal(m02["by_calls"]), modal(s2["by_calls"])
    per_m02 = m02["by_calls"][calls_m02]["per_call_median"]
    per_s2 = s2["by_calls"][calls_s2]["per_call_median"]
    return {
        "m06_single_call_median": tables["m06"]["by_calls"].get("1", {}).get("median"),
        "m02_tools_modal_calls": int(calls_m02), "m02_tools_per_call_median": per_m02,
        "m07_stage2_modal_calls": int(calls_s2), "m07_stage2_per_call_median": per_s2,
        "calls_factor": round(int(calls_s2) / int(calls_m02), 2),
        "per_call_factor": round(per_s2 / per_m02, 2),
        "median_answered_m02": m02["median_answered"],
        "median_answered_m07_stage2": s2["median_answered"],
        "growth_factor_tools_arm": round(s2["median_answered"] / m02["median_answered"], 2),
        "sentence": (
            f"The tools arm's median answered turn went from {m02['median_answered']} (M02) to "
            f"{s2['median_answered']} (M07 stage 2): the modal turn went from {calls_m02} to "
            f"{calls_s2} model calls when entitlement-check became a second sequential tool "
            f"round (x{round(int(calls_s2) / int(calls_m02), 2)}), and the per-call input went from "
            f"{per_m02} to {per_s2} (x{round(per_s2 / per_m02, 2)}). M06's "
            f"{tables['m06']['by_calls'].get('1', {}).get('median')} is the single-call arm, the "
            "catalog inlined and no tools: a different shape, not an earlier point on this line."),
    }


# --- assemble ------------------------------------------------------------------------

def census() -> dict:
    inputs: dict = {}
    for path in (CATALOG, CASES, CLIENT, ANSWER_SCHEMA, CONTRACTS, MANIFEST, LOOP_SHAPE):
        inputs[str(path.relative_to(ROOT)).replace("\\", "/")] = _sha256(path)
    constants = client_constants()
    cases = {c["id"]: c for c in yaml.safe_load(CASES.read_text(encoding="utf-8"))}
    catalog = search.load_catalog(CATALOG)
    cal = calibration(constants, cases)

    tables: dict = {}
    all_rows: dict = {}
    for run in RUNS:
        rows = read_run(run, cases, catalog, constants["CLOCK"], inputs)
        all_rows[run["key"]] = rows
        answered = [r["tokens_in"] for r in rows if r["answered"]]
        table = by_calls(rows)
        tables[run["key"]] = {
            "label": run["label"], "offered": list(run["offered"]),
            "samples": len(rows), "answered": len(answered), "refused_or_unanswered": len(rows) - len(answered),
            "median_answered": _median(answered), "min_answered": min(answered), "max_answered": max(answered),
            "over_ceiling": sum(1 for r in rows if r["over_ceiling"]),
            "calls_distribution": {str(c): b["n"] for c, b in table.items()},
            "by_calls": table,
            "ceiling_position": ceiling_position(table),
        }

    subject_run = next(r for r in RUNS if r["key"] == SUBJECT)
    rows = all_rows[SUBJECT]
    comp = components(subject_run, constants, cases, cal)
    removable = removable_evidence(rows, constants, subject_run, cal)
    loop_shape = _load(LOOP_SHAPE)["summary"]
    return {
        "_what_this_is": (
            "M08's context census: where the tools arm's tokens_in goes, by call, by round and "
            "by component, read off committed runs and replayed over the committed catalog. "
            "Zero model calls. Produced by milestones/M08/context_census.py; "
            "tests/test_m08_census.py re-runs it and refuses drift. Exact / replayed / estimated "
            "is labelled per section. Prints no pass count at any ceiling but 6000."),
        "ceiling": CEILING,
        "ceiling_derivation": {"source": "ADR-014, M02 amendment; milestones/M02/loop-shape.json",
                               "measured_n": loop_shape["n"], "answered": loop_shape["answered"],
                               "tokens_in": loop_shape["tokens_in"],
                               "model_calls_per_turn": loop_shape["model_calls_per_turn"],
                               "ceiling_over_measured_max": round(CEILING / loop_shape["tokens_in"]["max"], 3),
                               "placed": "above a three-call turn, below a four-call turn (~6600), at the "
                                         "per-call cost measured then"},
        "inputs_sha256": dict(sorted(inputs.items())),
        "1_by_milestone (exact)": tables,
        "2_stage2_per_sample (exact + replayed)": [
            {k: r[k] for k in ("case", "sample", "answered", "calls", "rounds", "steps", "tools",
                               "tokens_in", "tokens_out", "replayed_chars", "replayed_steps",
                               "rows_returned", "rows_returned_not_cited", "cited",
                               "mandated_calls", "over_ceiling")}
            for r in sorted(rows, key=lambda r: (r["case"], r["sample"]))],
        "3_by_round (exact)": marginal_call(rows, tables[SUBJECT]["by_calls"]),
        "4_by_component (estimated)": {"calibration": cal, "per_call_text": comp,
                                       "per_call_base_from_two_call_samples": per_call_base(rows, cal, comp)},
        "5_attribution (exact)": attribution(tables),
        "6_latency (exact, secondary)": latency(rows),
        "7_removable_evidence (replayed + estimated)": removable,
        "8_decision_rule (pre-registered, SPEC/08)": decision_rule(rows, removable, cal),
    }


def render(record: dict) -> str:
    lines = [f"context census — ceiling {record['ceiling']} (ADR-014); zero model calls", ""]
    lines.append("1. by milestone (exact)")
    for t in record["1_by_milestone (exact)"].values():
        lines.append(f"  {t['label']}: answered {t['answered']}/{t['samples']}, over {CEILING}: "
                     f"{t['over_ceiling']}, median {t['median_answered']} ({t['min_answered']}-{t['max_answered']})")
        for calls, b in t["by_calls"].items():
            lines.append(f"      {calls} calls: n={b['n']:2} min={b['min']:5} median={b['median']:>7} "
                         f"max={b['max']:5} per call~{b['per_call_median']}")
        pos = t["ceiling_position"]
        lines.append(f"      {CEILING} sits: entirely under it up to {pos['entirely_under']} calls; "
                     f"entirely over it from {pos['entirely_over']} calls; splits {pos['split_by_ceiling']}")
    d = record["8_decision_rule (pre-registered, SPEC/08)"]
    lines += ["", "2. stage 2 per sample: in the record (73 answered rows, 2 refused)", "",
              "3. by round (exact)"]
    m = record["3_by_round (exact)"]
    lines.append(f"  one more call, adjacent medians: {m['adjacent_medians']}; within-case median delta "
                 f"{m['within_case_median_delta']} over {len(m['within_case'])} pairs")
    c = record["4_by_component (estimated)"]
    lines += ["", "4. by component, per call (estimated; chars/token "
              f"{c['calibration']['chars_per_token']['min']}-{c['calibration']['chars_per_token']['max']} "
              "from ADR-014's six anchors)"]
    pc = c["per_call_text"]
    specs_line = ", ".join(f"{k} {v['tokens_est']}" for k, v in pc["tool_specs"].items())
    lines.append(f"  system prompt {pc['system_prompt']['tokens_est']} (of which answer schema "
                 f"{pc['system_prompt']['of_which_answer_schema']['tokens_est']}); tool specs "
                 f"{pc['tool_specs_total']['tokens_est']} "
                 f"({specs_line}); "
                 f"viewer turn {pc['viewer_turn']['tokens_est']}")
    b = c["per_call_base_from_two_call_samples"]
    lines.append(f"  per-call base from {b['n']} two-call samples: {b['lower_median']}-{b['upper_median']}; "
                 f"explained by committed text ~{b['explained_by_committed_text_est']}; residual "
                 f"{b['residual_est']['lower']}-{b['residual_est']['upper']} ({b['residual_est']['note']})")
    lines += ["", "5. attribution (exact)", "  " + record["5_attribution (exact)"]["sentence"]]
    lat = record["6_latency (exact, secondary)"]
    lines += ["", "6. latency (exact, secondary)",
              f"  p95 per answer file {lat['p95_per_answer_file']}; pooled p95 {lat['p95_pooled']} ms"]
    for calls, v in lat["by_calls"].items():
        lines.append(f"      {calls} calls: model {v['latency_ms_median']} ms, tools {v['tool_ms_median']} ms, "
                     f"guardrail {v['guard_ms_median']} ms (medians, n={v['n']})")
    r = record["7_removable_evidence (replayed + estimated)"]
    lines += ["", "7. removable evidence (replayed + estimated)",
              f"  rows returned and not cited: {r['rows_returned_not_cited']['samples_with_any']} samples, "
              f"<={r['rows_returned_not_cited']['tokens_per_call_est_max']} tokens/call; text sent twice: "
              f"{len(r['text_sent_twice']['shared_lines_40plus_chars'])} shared lines "
              f"({r['text_sent_twice']['tokens_per_call_est']} tokens/call); undeclared tools offered: "
              f"{r['undeclared_tools_offered'] or 'none'}; removable ~{r['removable_tokens_per_call_est']} tokens/call"]
    lines += ["", "8. decision rule (pre-registered, SPEC/08), per sample",
              f"  at mandated calls: {d['samples_at_mandated_calls']} samples, {d['of_which_over_ceiling']} over "
              f"{CEILING} (max {d['mandated_shape_tokens_in']['max']}), "
              f"{d['of_which_covered_by_own_removable_content']} covered by their own removable content; "
              f"above mandate: {d['samples_above_mandated_calls']} samples, min {d['above_mandate_tokens_in_min']}",
              f"  largest gap per call {d['gap_per_call_max']}; largest removable in any sample "
              f"{d['cross_sample_reading_not_the_rule']['removable_per_call_est_max_any_sample']} (not the rule)",
              f"  -> outcome {d['outcome']}: {d['reading']}"]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--check", action="store_true",
                        help="recompute and compare with the committed record; write nothing; exit 1 on drift")
    args = parser.parse_args(argv)
    record = census()
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    out = pathlib.Path(args.out)
    if args.check:
        committed = out.read_text(encoding="utf-8") if out.exists() else ""
        if committed != text:
            print(f"DRIFT: {out} differs from what the committed inputs produce")
            return 1
        print(f"OK: {out} is what the committed inputs produce")
        return 0
    out.write_text(text, encoding="utf-8", newline="\n")
    print(render(record))
    print(f"\nwritten: {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

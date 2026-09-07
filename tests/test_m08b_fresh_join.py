"""
M08b's join reader: written and pinned on a planted run before any real one
exists (SPEC/08b, PR 2).

`milestones/M08b/fresh_join.py` is where SPEC/08b's one claim is read — every
fresh answered sample at three calls or fewer under 7700 and every sample at
four or more over it, per sample, from the answer files' `usage.calls` and the
single-file transcripts — with the pre-registered reading of a falsifying
sample, the fresh re-derived band, the count and refusal bands, the two p95s
and the two triggers. These tests run it over `tests/fixtures/m08b/planted/`,
pin the record it produces byte for byte, check every number the planted run
was shaped to yield, and plant what the reader must refuse: a verdict that
disagrees with the file, a call count that disagrees with the trajectory, a
transcript from another ceiling, a sidecar that disagrees with itself. And one
falsifying sample through the whole pipeline, so a red close is known to
record the right row.

Hermetic (G8). Seats, by the two-key rule the reader and record sit on:
AI Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import re
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M08b" / "fresh_join.py"
PLANTED = ROOT / "tests" / "fixtures" / "m08b" / "planted"
RECORD = PLANTED / "fresh-join.json"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}
STORE_WORDS = {"core.withheld", "read_withheld", "held_object", "fetch_held", "withheld",
               "WITHHELD_STORE"}
#: A closed set, not a vocabulary (Security seat, round 2): `import_module` and
#: `__import__` were refused by name and `getattr`, `sys.modules`,
#: `__builtins__`, `__dict__` and `"co" + "re"` walked past them. The readers
#: are JSON in, record out; none of these names has a use in one.
REFLECTION = {"getattr", "setattr", "delattr", "globals", "locals", "vars", "eval", "exec",
              "__import__", "import_module", "__builtins__", "__dict__", "__loader__",
              "__spec__", "modules", "__getattribute__", "__subclasses__"}


def _all_string_literals(node) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
            and _all_string_literals(node.left) and _all_string_literals(node.right))


def store_reach(tree: ast.Module) -> list[str]:
    """The G4 boundary's own vocabulary check, the reflection door closed, and
    a name assembled from string literals refused (adjacent literals fold at
    parse time and are caught; `"co" + "re"` is a BinOp and was not — a
    literal joined to a computed value, `json.dumps(...) + "\\n"`, is not a
    name and is not flagged)."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.split(".")[0] in {"core", "boto3"}
                      or a.name.endswith("withheld")]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in {"core", "read_withheld"} or module.endswith("withheld"):
                found.append(f"from {module}")
            found += [a.name for a in node.names if a.name in STORE_WORDS]
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in STORE_WORDS:
            found.append(f"the string {node.value!r}")
        elif isinstance(node, (ast.Name, ast.Attribute)):
            label = node.id if isinstance(node, ast.Name) else node.attr
            if label in STORE_WORDS or label in REFLECTION:
                found.append(label)
        elif isinstance(node, ast.BinOp) and _all_string_literals(node):
            found.append(f"a name assembled from literals: {ast.unparse(node)[:40]}")
    return found


def imported_roots(tree: ast.Module) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


#: What each reader may import, and no other module (Security seat, round 2:
#: an allowlist, because a denylist of doors is the shape that was walked
#: around twice).
ALLOWED_IMPORTS = {
    "fresh_join": {"__future__", "argparse", "hashlib", "importlib", "json", "pathlib", "re", "sys",
                   "yaml", "evals", "jsonschema"},
    "residual_attribution": {"__future__", "argparse", "hashlib", "importlib", "json", "pathlib", "yaml"},
    "answer_channel": {"__future__", "argparse", "hashlib", "json", "pathlib", "re"},
}


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("fresh_join", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fresh_join"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def planted(tmp_path):
    """A working copy of the planted run, for the plants."""
    copy = tmp_path / "planted"
    shutil.copytree(PLANTED, copy)
    return copy


def _produced(reader, run_dir) -> str:
    return json.dumps(reader.join(run_dir), indent=2, ensure_ascii=False) + "\n"


def _edit(path: pathlib.Path, fn) -> None:
    path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")


# --- the record ------------------------------------------------------------------

def test_the_record_is_what_the_planted_inputs_produce(reader):
    """Byte for byte, as `--check` compares it."""
    assert _produced(reader, PLANTED) == RECORD.read_text(encoding="utf-8"), (
        "fresh-join.json under the planted fixture is not what the reader produces; re-run "
        "`python milestones/M08b/fresh_join.py --dir tests/fixtures/m08b/planted` and commit "
        "the result, or find which input moved")


def test_check_compares_and_writes_nothing(reader, planted, capsys):
    # The copied record names its inputs by repository path and the copy is
    # elsewhere, so `--check` on the copy as copied is DRIFT — the record says
    # where its inputs were. Regenerate in place first, then check.
    assert reader.main(["--dir", str(planted)]) == 0
    assert reader.main(["--dir", str(planted), "--check"]) == 0
    (planted / "fresh-join.json").unlink()
    assert reader.main(["--dir", str(planted), "--check"]) == 1
    assert not (planted / "fresh-join.json").exists()


def test_the_real_directory_has_no_run_yet(reader):
    """PR 3 commits the run; until then the reader says so rather than reading
    a partial directory as a run."""
    with pytest.raises(SystemExit, match="does not exist"):
        reader.join(reader.HERE)


def test_the_reader_imports_no_network_module_and_takes_no_ceiling():
    tree = ast.parse(READER.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & NETWORK_MODULES, f"the reader imports {sorted(imported & NETWORK_MODULES)}"
    options = {ast.literal_eval(call.args[0]) for call in ast.walk(tree)
               if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
               and call.func.attr == "add_argument"}
    assert options == {"--dir", "--check"}, (
        f"the reader takes {sorted(options)}; a ceiling argument would let a sample be read "
        "at a number the rule did not produce")
    assert store_reach(tree) == [], (
        f"the reader can reach the refused-content store: {store_reach(tree)} (G4, ADR-071)")
    assert imported_roots(tree) <= ALLOWED_IMPORTS["fresh_join"], (
        f"the reader imports {sorted(imported_roots(tree) - ALLOWED_IMPORTS['fresh_join'])} outside its allowlist")


def test_the_store_guard_refuses_the_reflection_doors():
    """The round-2 plants that walked past the round-1 guard, each refused by
    the closed set rather than by name."""
    # One door per plant, so that closing one cannot be masked by another
    # (the deletability audit found each two-door plant surviving the loss of
    # either door).
    for source in ('import sys\n_m = sys.modules.get(name)\n',
                   'def f(x, name):\n    return getattr(x, name)\n',
                   'x = globals()\n',
                   'x = obj.__builtins__\n',
                   'x = obj.__dict__\n',
                   'name = "co" + "re.with" + "held"\n',
                   'name = "fetch" + "_held"\n',
                   'import importlib\n_s = importlib.import_module(name)\n',
                   'x = __import__(name)\n',
                   'from core import withheld\n'):
        assert store_reach(ast.parse(source)), f"the guard admits: {source!r}"
    assert store_reach(ast.parse('import json\nx = json.loads("{}")\nname = f"{x}-{1}"\n'
                                 'text = json.dumps(x) + "\\n"\nimport re\np = re.compile("a")\n')) == []


def test_the_repository_scans_reach_the_readers():
    """Security and Platform Engineering seats, round 1: the G4 store-boundary
    scan and the hermeticity scan each stopped at roots that did not include
    `milestones/`, so a store import or an SDK import planted in a reader
    survived the whole suite. Both roots now include it, and this is the pin
    that a root dropped again is red here and not only silent there."""
    import test_g4_capture_boundary as boundary
    import test_hermeticity as hermeticity

    readers = {ROOT / "milestones" / "M08b" / name
               for name in ("fresh_join.py", "residual_attribution.py", "answer_channel.py")}
    scanned = set(boundary._sources(*boundary.SCORER_ROOTS))
    assert readers <= scanned, f"the store-boundary scan misses {sorted(p.name for p in readers - scanned)}"
    hermetic = set(hermeticity.hermetic_sources())
    assert readers <= hermetic, f"the hermeticity scan misses {sorted(p.name for p in readers - hermetic)}"


def test_the_band_constants_are_the_derivation_tests_and_place_an_unclamped_roof(reader):
    """AI Quality seat, round 1: the roof half of `BAND` was silent because
    M08's record clamps it by the four-call minimum — and on a fresh run with
    no four-call sample the roof alone places the re-derived point, which PR 3
    records into ADR-074. Pinned literally, beside `tests/test_budget_derivation.py`'s
    own pin of the same two constants, and exercised unclamped."""
    assert reader.BAND == (1.15, 1.60)
    unclamped = reader.band_from(6230, None)
    assert unclamped["floor"] == 7164.5 and unclamped["roof"] == 9968.0
    assert unclamped["integer_band"] == [7165, 9968] and unclamped["point"] == 8600
    assert not unclamped["empty"]
    clamped = reader.band_from(6230, 8181)
    assert clamped["roof"] == 8180 and clamped["point"] == 7700


# --- what the planted run says ----------------------------------------------------

def test_the_claim_holds_on_the_planted_run_with_one_grain_near_miss(reader):
    rec = reader.join(PLANTED)
    c = rec["claim"]
    assert c["holds"] and c["falsifiers"] == []
    assert c["samples_at_3_calls_or_fewer"] == 67 and c["samples_at_4_calls_or_more"] == 5
    assert c["largest_3_call_or_fewer_tokens_in"] == 7690
    assert c["smallest_4_call_or_more_tokens_in"] == 8181
    assert c["grain_near_misses"] == ["headroom-005 s2"]
    assert c["comparison"].startswith("got > limit")
    assert rec["grain"] == [7675.125, 7700]
    near = next(r for r in rec["per_sample"] if r["case"] == "headroom-005" and r["sample"] == 2)
    assert near["reading"] == reader.GRAIN_NEAR_MISS
    assert near["distance"] == {"to_point": -10, "to_unrounded_midpoint": 14.875,
                                "to_nearer_band_edge": 490, "nearer_band_edge": "roof"}
    four = next(r for r in rec["per_sample"] if r["case"] == "recommend-013" and r["sample"] == 1)
    assert four["calls"] == 4 and four["at_mandate"] is False and four["reading"] == reader.FAIL
    assert four["tokens_in_verdict"] == "FAIL" and four["distance"]["to_point"] == 600
    assert four["per_call_tokens_in"] == [1980, 2100, 2110, 2110]
    assert [g["delta_tokens"] for g in four["per_round_growth"]] == [120, 10, 0]
    refused = next(r for r in rec["per_sample"] if r["case"] == "recommend-003" and r["sample"] == 1)
    assert refused["refused"] and refused["reading"] == "refused" and refused["calls"] is None


def test_the_m08_reference_is_read_from_the_census_and_matches_the_live_ceiling(reader):
    ref = reader.join(PLANTED)["m08_reference"]
    assert ref["mandated_shape_max"] == 6235 and ref["four_call_min"] == 8181
    assert ref["integer_band"] == [7171, 8180] and ref["point"] == 7700
    assert ref["unrounded_midpoint"] == 7675.125
    assert ref["as_run_three_call_max"] == 6792 and ref["gap"] == [6792, 8181]


def test_the_fresh_band_is_re_derived_from_the_fresh_run(reader):
    b = reader.join(PLANTED)["fresh_band"]
    assert b["available"] and not b["empty"]
    assert b["mandated_shape_max"] == 6230 and b["four_call_min"] == 8181
    assert b["integer_band"] == [7165, 8180] and b["point"] == 7700 and b["point_inside"]
    assert b["reading"] == "the number holds; the rule re-derives to 7700"


def test_the_count_refusals_p95s_and_triggers_are_read_from_the_rows(reader):
    rec = reader.join(PLANTED)
    n = rec["count"]
    assert n["N"] == 22 and n["band"] == [7, 14] and n["predicted"] == 12 and not n["in_band"]
    assert n["falsifiers"]["N_outside_band"] is True
    assert n["falsifiers"]["3_of_3_pass_at_m08_failing_by_majority"] == []
    assert "recommend-014" in n["falsifiers"]["0_of_3_fail_at_m08_passing_by_majority"]
    assert n["per_case"]["recommend-013"]["result"] == "FAIL"
    assert n["per_case"]["recommend-013"]["calls_by_sample"] == [4, 4, 4]
    assert rec["refusals"] == {"by_majority": 1, "cases": ["recommend-003"], "band": [0, 2],
                               "in_band": True}
    p = rec["p95"]
    assert p["ceiling_ms"] == 5200 and p["costs_a_case"] is False
    assert p["pooled"] == {"n": 72, "p95": 6000, "verdict": "OVER"}
    assert p["mandated_shape"] == {"n": 63, "p95": 3500, "verdict": "within"}
    assert p["transcript_line"] == {"verdict": "OVER", "p95": 6000, "ceiling": 5200}
    assert p["reading"].startswith("share:")
    t = rec["triggers"]
    assert t["browse_gap"]["persists"] and t["browse_gap"]["cases"] == ["grounded-019", "recommend-003",
                                                                          "recommend-013"]
    assert t["browse_gap"]["four_call_samples_outside_the_seven"] == []
    # recommend-015 is planted at three calls with two searches against a
    # two-call mandate: the browse gap's shape under decision 2's threshold,
    # recorded beside the trigger and not in it (Tool Owner seat, round 1).
    under = t["browse_gap"]["beyond_mandate_under_the_threshold"]
    assert under["cases"] == ["headroom-005", "recommend-015"]
    assert "recommend-015 s1 (3 calls)" in under["samples"] and "headroom-005 s2 (3 calls)" in under["samples"]
    assert t["tokens_out_five"]["persists"]
    assert t["tokens_out_five"]["cases"]["blackout-001"]["fails_by_majority"]
    assert not t["tokens_out_five"]["cases"]["blackout-007"]["fails_by_majority"]
    assert t["tokens_out_five"]["failing_by_majority_outside_the_five"] == []
    shape = next(r for r in rec["per_sample"] if r["case"] == "recommend-013" and r["sample"] == 1)["search"]
    assert shape == {"searches_attempted": 3, "searches_executed": 3,
                     "searches_executed_before_verdict": 3, "beyond_mandate_before_verdict": True}


# --- the browse gap's shape (Tool Owner seat, round 1) ------------------------------

def _step(round_, tool, decision="allowed", executed=True):
    return {"round": round_, "seq": round_, "tool": tool, "args": {}, "decision": decision,
            "executed": executed}


def test_the_browse_gap_reads_executed_searches_before_the_verdict(reader):
    """ADR-074 decision 2's words, each clause load-bearing: a search DENIED by
    Cedar or unreached retrieved nothing and is not a browse; a search AFTER
    `entitlement-check` is a different shape; the mandate is one search."""
    cs, ec = "catalog-search", "entitlement-check"
    assert reader.search_shape([_step(1, cs), _step(2, ec)])["beyond_mandate_before_verdict"] is False
    assert reader.search_shape([_step(1, cs), _step(2, cs), _step(3, ec)])["beyond_mandate_before_verdict"]
    assert reader.search_shape([_step(1, cs), _step(2, cs)])["beyond_mandate_before_verdict"], (
        "no entitlement check: every search is before the answer")
    denied = reader.search_shape([_step(1, cs), _step(2, cs, decision="denied", executed=False), _step(3, ec)])
    assert denied == {"searches_attempted": 2, "searches_executed": 1,
                      "searches_executed_before_verdict": 1, "beyond_mandate_before_verdict": False}
    unreached = reader.search_shape([_step(1, cs), _step(2, cs, executed=False)])
    assert unreached["beyond_mandate_before_verdict"] is False
    after = reader.search_shape([_step(1, cs), _step(2, ec), _step(3, cs)])
    assert after == {"searches_attempted": 2, "searches_executed": 2,
                     "searches_executed_before_verdict": 1, "beyond_mandate_before_verdict": False}
    # Tool Owner seat, round 2: a search that RAN and had its result rejected
    # on the output contract carries `executed: true` with a denied decision
    # (the loop's own tested shape) — it browsed, and it counts. And an
    # entitlement check that never ran closes no window, whatever was decided.
    suppressed = reader.search_shape([_step(1, cs), _step(2, cs, decision="denied", executed=True), _step(3, ec)])
    assert suppressed["searches_executed"] == 2 and suppressed["beyond_mandate_before_verdict"]
    check_denied = reader.search_shape([_step(1, cs), _step(2, ec, decision="denied", executed=False),
                                        _step(3, cs)])
    assert check_denied["searches_executed_before_verdict"] == 2 and check_denied["beyond_mandate_before_verdict"]
    check_ran_then_rejected = reader.search_shape([_step(1, cs), _step(2, ec, decision="denied", executed=True),
                                                   _step(3, cs)])
    assert check_ran_then_rejected["beyond_mandate_before_verdict"] is False


def test_a_suppressed_second_search_still_persists_the_browse_gap(reader, planted):
    """The round-2 plant: `recommend-013`'s extra searches marked denied on the
    output contract but executed — three authorized, executed searches read as
    one on 6863f7e, and the case left every column."""
    def suppress(text):
        trajectories = json.loads(text)
        for step in trajectories["recommend-013"]["trajectory"][1:]:
            step.update(decision="denied", mechanism="schema", executed=True)
        return json.dumps(trajectories, indent=2, ensure_ascii=False)
    for n in (1, 2, 3):
        _edit(planted / f"goldens-run-{n}-trajectory.json", suppress)
    gap = reader.join(planted)["triggers"]["browse_gap"]
    assert "recommend-013" in gap["cases"]


def test_a_step_with_no_round_or_no_decision_is_refused(reader, planted):
    """Platform Engineering and Tool Owner seats, round 2: a step with no
    `round` vanished from the growth replay and read as 100% unexplained; a
    step with no `decision` read as never executed; `round: 0` sorted before
    everything. The envelope is on a contract now."""
    for mutate, expect in (
        (lambda s: s.pop("round"), "'round' is a required property"),
        (lambda s: s.pop("decision"), "'decision' is a required property"),
        (lambda s: s.update(round=0), "less than the minimum"),
        (lambda s: s.update(executed="yes"), "not of type 'boolean'"),
        (lambda s: s.update(extra=1), "Additional properties"),
    ):
        copy = planted / f"env-{abs(hash(expect))}"
        shutil.copytree(planted, copy)

        def bend(text, mutate=mutate):
            trajectories = json.loads(text)
            mutate(trajectories["blackout-001"]["trajectory"][0])
            return json.dumps(trajectories, indent=2, ensure_ascii=False)
        _edit(copy / "goldens-run-1-trajectory.json", bend)
        with pytest.raises(SystemExit, match="outside the loop's shape"):
            reader.join(copy)


def test_the_k3_rows_are_reconciled_against_the_per_sample_rows(reader, planted):
    """AI Quality seat, round 2: rows and count line moved together — eight
    PASS cases read as FAIL, N from outside the band to inside it — and the
    count-line check was satisfied. The bracket is the per-sample results."""
    _edit(planted / "goldens-score.txt", lambda t: re.sub(
        r"^(entitlement-002\s+)PASS\s+\[PASS PASS PASS\]\s*$", r"\1FAIL  [FAIL FAIL FAIL]", t, flags=re.M
    ).replace("22/25 passed (3 failed, 0 infra)", "21/25 passed (4 failed, 0 infra)"))
    with pytest.raises(SystemExit, match="a planted row"):
        reader.join(planted)


def test_a_bracket_that_disagrees_with_the_rows_under_a_matching_result_is_refused(reader, planted):
    """The bracket check alone: the result still matches the rows' majority."""
    _edit(planted / "goldens-score.txt", lambda t: re.sub(
        r"^(entitlement-002\s+PASS\s+)\[PASS PASS PASS\]\s*$", r"\1[FAIL PASS PASS]", t, flags=re.M))
    with pytest.raises(SystemExit, match="is not the per-sample transcripts'"):
        reader.join(planted)


def test_a_result_that_disagrees_with_a_matching_bracket_is_refused(reader, planted):
    """The majority check alone: the bracket is the rows' and the result is not
    its majority."""
    _edit(planted / "goldens-score.txt", lambda t: re.sub(
        r"^(entitlement-002\s+)PASS(\s+\[PASS PASS PASS\])\s*$", r"\1FAIL\2", t, flags=re.M
    ).replace("22/25 passed (3 failed, 0 infra)", "21/25 passed (4 failed, 0 infra)"))
    with pytest.raises(SystemExit, match="over a bracket whose majority is PASS"):
        reader.join(planted)


def test_a_latency_line_from_another_ceiling_is_refused(reader, planted):
    """AI Quality seat, round 2: `OK p95=6000ms within 7500ms` was recorded
    beside a pooled OVER; the line's ceiling and verdict are held to the
    manifest and the pooled verdict the way `tokens_in` is held to the file."""
    _edit(planted / "goldens-score.txt",
          lambda t: t.replace("suite latency  OVER p95=6000ms over 5200ms",
                              "suite latency  OK   p95=6000ms within 7500ms"))
    with pytest.raises(SystemExit, match="a transcript from another ceiling"):
        reader.join(planted)


def test_a_latency_line_with_the_right_verdict_and_another_ceiling_is_refused(reader, planted):
    """The ceiling half alone: the verdict agrees and the number does not."""
    _edit(planted / "goldens-score.txt",
          lambda t: t.replace("suite latency  OVER p95=6000ms over 5200ms",
                              "suite latency  OVER p95=6000ms over 5000ms"))
    with pytest.raises(SystemExit, match="a transcript from another ceiling"):
        reader.join(planted)


def test_a_search_mandate_that_is_not_the_cases_is_refused(reader, planted, monkeypatch):
    """The cross-check is what makes `MANDATED_SEARCHES` the case's rather than
    a constant: moved to 2, the join refuses before a row is read."""
    monkeypatch.setattr(reader, "MANDATED_SEARCHES", 2)
    with pytest.raises(SystemExit, match="the search mandate is not the case's"):
        reader.join(planted)


def test_the_p95_readings_are_all_reachable(reader):
    """AI Quality seat, round 2: the drift branch was deletable. Synthetic
    rows, each reading by name."""
    def row(latency, at_mandate):
        return {"answered": True, "latency_ms": latency, "at_mandate": at_mandate}
    drift = reader.p95s([row(6000, True)] * 20, [], 5200)
    assert drift["mandated_shape"]["verdict"] == "OVER" and drift["reading"].startswith("drift")
    share = reader.p95s([row(3500, True)] * 19 + [row(6000, False)] * 5, [], 5200)
    assert share["pooled"]["verdict"] == "OVER" and share["mandated_shape"]["verdict"] == "within"
    assert share["reading"].startswith("share")
    within = reader.p95s([row(3500, True)] * 20, [], 5200)
    assert within["reading"].startswith("within")


def test_the_fresh_band_readings_are_all_reachable(reader):
    """AI Quality seat, round 2: `point_inside` was never false in any test, and
    the two middle branches of the reading were dead. Synthetic rows through
    the real function, with the claim holding."""
    ref = reader.m08_reference(json.loads(reader.CENSUS.read_text(encoding="utf-8")))

    def rows(mandated_max, four_call_min=None):
        out = [{"answered": True, "at_mandate": True, "calls": 3, "tokens_in": mandated_max}]
        if four_call_min:
            out.append({"answered": True, "at_mandate": False, "calls": 4, "tokens_in": four_call_min})
        return out
    outside = reader.fresh_band(rows(6900), ref, 7700, holds=True)
    assert outside["integer_band"] == [7935, 11040] and outside["point"] == 9500
    assert outside["point_inside"] is False
    assert outside["reading"] == "the number holds; the rule does not: 7700 is outside the band re-derived from the fresh run"
    elsewhere = reader.fresh_band(rows(6400, 8181), ref, 7700, holds=True)
    assert elsewhere["point_inside"] and elsewhere["point"] == 7800
    assert elsewhere["reading"] == "the number holds; 7700 is inside the fresh band and the rule re-derives to 7800"
    same = reader.fresh_band(rows(6235, 8181), ref, 7700, holds=True)
    assert same["reading"] == "the number holds; the rule re-derives to 7700"
    empty = reader.fresh_band(rows(7720, 8181), ref, 7700, holds=False)
    assert empty["empty"] and empty["reading"].startswith("the claim is falsified")


def test_a_denied_second_search_does_not_persist_the_browse_gap(reader, planted):
    """The plant that survived in round 1: `recommend-013`'s extra searches
    marked denied and unexecuted left the trigger reading unchanged."""
    def deny(text):
        trajectories = json.loads(text)
        for step in trajectories["recommend-013"]["trajectory"][1:]:
            step.update(decision="denied", mechanism="policy", executed=False)
        return json.dumps(trajectories, indent=2, ensure_ascii=False)
    for n in (1, 2, 3):
        _edit(planted / f"goldens-run-{n}-trajectory.json", deny)
    gap = reader.join(planted)["triggers"]["browse_gap"]
    assert "recommend-013" not in gap["cases"] and gap["cases"] == ["grounded-019", "recommend-003"]


def test_a_trajectory_step_the_tools_contract_refuses_is_refused(reader, planted):
    """`replay()` degraded a schema-refused step to fifteen characters and the
    join recorded that as growth (Tool Owner seat, round 1)."""
    for args, expect in (({"query": 12345}, "contract refuses"), ({"nonsense": True}, "contract refuses")):
        copy = planted / f"case-{len(str(args))}"
        shutil.copytree(planted, copy)

        def bend(text, args=args):
            trajectories = json.loads(text)
            trajectories["recommend-013"]["trajectory"][0]["args"] = args
            return json.dumps(trajectories, indent=2, ensure_ascii=False)
        _edit(copy / "goldens-run-1-trajectory.json", bend)
        with pytest.raises(SystemExit, match=expect):
            reader.join(copy)
    def unknown(text):
        trajectories = json.loads(text)
        trajectories["recommend-013"]["trajectory"][0]["tool"] = "catalog-purge"
        return json.dumps(trajectories, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-1-trajectory.json", unknown)
    with pytest.raises(SystemExit, match="which the committed contracts do not"):
        reader.join(planted)


def test_a_mandate_that_moved_since_the_census_is_refused(reader, planted, tmp_path, monkeypatch):
    """The derivation test reads the census record's mandate and this join
    reads the live cases file's; the two are required to agree (Tool Owner
    seat, round 1: a mandate edit left the p95 population green and this join
    on another shape)."""
    import yaml
    cases = yaml.safe_load(reader.CASES.read_text(encoding="utf-8"))
    target = next(c for c in cases if c["id"] == "blackout-008")
    assert target.pop("trajectory")["expect_tool_before_answer"] == "entitlement-check"
    moved = tmp_path / "cases.yaml"
    moved.write_text(yaml.safe_dump(cases, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(reader, "CASES", moved)
    with pytest.raises(SystemExit, match="the mandate moved since the census"):
        reader.join(planted)


def test_a_tokens_out_failure_outside_the_five_is_recorded_beside_the_trigger(reader, planted):
    """The `tokens_out` counterpart of the browse gap's outside-the-seven
    column (Tool Owner seat, round 1): `brand-021` over its tier on every
    sample, in the files, both transcripts and the count line together."""
    for n in (1, 2, 3):
        def over(text):
            answers = json.loads(text)
            usage = answers["brand-021"]["usage"]
            usage["calls"][-1]["tokens_out"] += 500 - usage["tokens_out"]
            usage["tokens_out"] = 500
            return json.dumps(answers, indent=2, ensure_ascii=False)
        _edit(planted / f"goldens-run-{n}.json", over)
    import yaml
    case = next(c for c in yaml.safe_load(reader.CASES.read_text(encoding="utf-8")) if c["id"] == "brand-021")
    tier = next(a["budget"]["tokens_out"] for a in case["asserts"] if "budget" in a)
    _edit(planted / "per-sample.txt", lambda t: re.sub(
        r"^(brand-021\s+)PASS\s*$",
        rf"\1FAIL\n                     - budget: tokens_out=500 over {tier} (calls=2)", t, flags=re.M))
    _edit(planted / "goldens-score.txt", lambda t: re.sub(
        r"^(brand-021\s+)PASS\s+\[PASS PASS PASS\]\s*$",
        rf"\1FAIL  [FAIL FAIL FAIL]\n                     - budget: tokens_out=500 over {tier} (calls=2)",
        t, flags=re.M).replace("22/25 passed (3 failed, 0 infra)", "21/25 passed (4 failed, 0 infra)"))
    five = reader.join(planted)["triggers"]["tokens_out_five"]
    assert five["failing_by_majority_outside_the_five"] == ["brand-021"]
    assert five["persists"] and "brand-021" not in five["cases"]


def test_a_tokens_out_verdict_that_disagrees_with_the_file_is_refused(reader, planted):
    def inflate(text):
        answers = json.loads(text)
        usage = answers["brand-021"]["usage"]
        usage["calls"][-1]["tokens_out"] += 500 - usage["tokens_out"]
        usage["tokens_out"] = 500
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-1.json", inflate)
    with pytest.raises(SystemExit, match="tokens_out 500 is over its tier"):
        reader.join(planted)


# --- the six rows, and one falsifier through the whole pipeline ------------------------

def test_every_row_of_the_near_miss_table_is_reachable(reader):
    ref = reader.m08_reference(json.loads(reader.CENSUS.read_text(encoding="utf-8")))
    row = lambda calls, tokens, at_mandate: reader.reading_for(calls, tokens, at_mandate, ref, 7700)  # noqa: E731
    assert row(3, 7720, True) == reader.ROW_RULE_AT_MANDATE
    assert row(3, 7720, False) == reader.ROW_POINT_ABOVE_MANDATE
    assert row(3, 8300, True) == reader.ROW_RULE_OVERLAP
    assert row(4, 7650, False) == reader.ROW_POINT_FOUR
    assert row(4, 7000, False) == reader.ROW_RULE_FOUR
    assert row(4, 7690, False) == reader.ROW_GRAIN_FALSIFIED
    assert row(3, 7690, True) == reader.GRAIN_NEAR_MISS
    assert row(3, 7700, True) == reader.GRAIN_NEAR_MISS, "the grain is (7675.125, 7700], closed at the point"
    assert row(3, 7675, True) == reader.PASS
    assert row(4, 8181, False) == reader.FAIL
    assert row(4, 7700, False) == reader.ROW_GRAIN_FALSIFIED, "a four-call sample at exactly 7700 passes `got > limit`"


def test_a_falsifying_sample_is_recorded_with_its_row_and_the_band_it_empties(reader, planted):
    """`blackout-008` s1 — at its mandate — planted at 7720. The claim fails on
    the join, the sample carries the first row of SPEC/08b's table, and the
    band re-derived from the fresh mandated-shape maximum is empty: the lesson
    a red close records is the rule's, not the point's."""
    def bump(text):
        answers = json.loads(text)
        usage = answers["blackout-008"]["usage"]
        usage["calls"][2]["tokens_in"] = 3640
        usage["tokens_in"] = 7720
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-1.json", bump)
    _edit(planted / "per-sample.txt", lambda t: re.sub(
        r"^(blackout-008\s+)PASS\s*$",
        r"\1FAIL\n                     - budget: tokens_in=7720 over 7700 (calls=3)",
        t, count=1, flags=re.M))
    # ...and the k=3 bracket with it, which the rows are reconciled against;
    # the case still passes by majority, so the count line stands.
    _edit(planted / "goldens-score.txt", lambda t: re.sub(
        r"^(blackout-008\s+PASS\s+)\[PASS PASS PASS\]", r"\1[FAIL PASS PASS]", t, flags=re.M))
    rec = reader.join(planted)
    assert not rec["claim"]["holds"]
    assert rec["claim"]["3_call_or_fewer_samples_over"] == ["blackout-008 s1"]
    [falsifier] = rec["claim"]["falsifiers"]
    assert falsifier == {"sample": "blackout-008 s1", "calls": 3, "tokens_in": 7720, "at_mandate": True,
                         "row": reader.ROW_RULE_AT_MANDATE}
    band = rec["fresh_band"]
    assert band["empty"] and band["mandated_shape_max"] == 7720 and band["integer_band"] is None
    # The band's sentence is written in the claim's frame (AI Quality seat,
    # round 1): a red close must not carry "the number holds" beside a falsifier.
    assert band["reading"].startswith("the claim is falsified (see claim.falsifiers); the rule has no solution")
    assert "the number holds" not in band["reading"]


def test_a_count_line_that_disagrees_with_its_own_rows_is_refused(reader, planted):
    """AI Quality seat, round 1: N was read from one transcript line and a line
    saying 9/25 over twenty-two PASS rows was recorded without a word."""
    _edit(planted / "goldens-score.txt",
          lambda t: t.replace("22/25 passed (3 failed, 0 infra)", "9/25 passed (16 failed, 0 infra)"))
    with pytest.raises(SystemExit, match="a planted count"):
        reader.join(planted)


def test_every_total_is_held_to_the_rounds_not_only_tokens_in(reader, planted):
    """Platform Engineering seat, round 1: the sum check covered `tokens_in`
    alone; `tokens_out` and `latency_ms` are the same list's other columns."""
    def bend(text):
        answers = json.loads(text)
        answers["edge-024"]["usage"]["latency_ms"] += 1
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-2.json", bend)
    with pytest.raises(SystemExit, match="latency_ms .* is not the sum over usage.calls"):
        reader.join(planted)


# --- the plants: what the reader refuses ---------------------------------------------

def test_a_planted_verdict_is_refused(reader, planted):
    _edit(planted / "per-sample.txt",
          lambda t: t.replace("- budget: tokens_in=8300 over 7700 (calls=4)\n", "", 1))
    with pytest.raises(SystemExit, match="planted verdict"):
        reader.join(planted)


def test_a_transcript_value_that_disagrees_with_the_file_is_refused(reader, planted):
    """The deletability audit's silent one: removing the budget line hits the
    other branch (a pass printed over a file that is over). This is a printed
    failure whose value is not the file's — the transcript and the answer file
    describe two different samples."""
    def shave(text):
        answers = json.loads(text)
        usage = answers["recommend-013"]["usage"]
        usage["calls"][3]["tokens_in"] -= 10
        usage["tokens_in"] -= 10
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-1.json", shave)
    with pytest.raises(SystemExit, match="planted verdict"):
        reader.join(planted)


def test_a_live_ceiling_the_point_rule_did_not_produce_is_refused(reader, planted, tmp_path, monkeypatch):
    """No sample is read at any ceiling but the one the pinned rule produces
    from the record (SPEC/08b, *What must not happen*): a cases file at 7600
    is refused before a single row is read, whatever the transcripts say."""
    cases = reader.CASES.read_text(encoding="utf-8").replace("tokens_in: 7700", "tokens_in: 7600")
    moved = tmp_path / "cases.yaml"
    moved.write_text(cases, encoding="utf-8")
    monkeypatch.setattr(reader, "CASES", moved)
    with pytest.raises(SystemExit, match="no sample is read at any ceiling but"):
        reader.join(planted)


def test_a_planted_call_count_is_refused(reader, planted):
    def drop_a_round(text):
        answers = json.loads(text)
        usage = answers["recommend-013"]["usage"]
        usage["calls"] = usage["calls"][:3]
        usage["tokens_in"] = sum(c["tokens_in"] for c in usage["calls"])
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-1.json", drop_a_round)
    with pytest.raises(SystemExit, match="planted call count"):
        reader.join(planted)


def test_a_transcript_from_another_ceiling_is_refused(reader, planted):
    _edit(planted / "per-sample.txt", lambda t: t.replace("over 7700", "over 6000"))
    with pytest.raises(SystemExit, match="not the live ceiling"):
        reader.join(planted)


def test_a_total_that_is_not_the_sum_over_the_rounds_is_refused(reader, planted):
    def inflate(text):
        answers = json.loads(text)
        answers["blackout-001"]["usage"]["tokens_in"] += 1
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-2.json", inflate)
    with pytest.raises(SystemExit, match="not the sum over usage.calls"):
        reader.join(planted)


def test_a_sidecar_that_disagrees_with_its_own_column_is_refused(reader, planted):
    def bend(text):
        sidecar = json.loads(text)
        sidecar["census"]["refused_by_majority"] = 2
        return json.dumps(sidecar, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-refusals.json", bend)
    with pytest.raises(SystemExit, match="disagrees with its own per-sample column"):
        reader.join(planted)


def test_a_sample_without_per_call_usage_is_refused(reader, planted):
    def strip(text):
        answers = json.loads(text)
        del answers["edge-024"]["usage"]["calls"]
        return json.dumps(answers, indent=2, ensure_ascii=False)
    _edit(planted / "goldens-run-3.json", strip)
    with pytest.raises(SystemExit, match="no usage.calls"):
        reader.join(planted)

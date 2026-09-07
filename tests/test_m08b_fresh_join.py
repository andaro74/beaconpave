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
    assert b["reading"].startswith("the number holds and the rule re-derives to it")


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
    assert p["transcript_line"] == {"verdict": "OVER", "p95": 6000}
    assert p["reading"].startswith("share:")
    t = rec["triggers"]
    assert t["browse_gap"]["persists"] and t["browse_gap"]["cases"] == ["grounded-019", "recommend-003",
                                                                          "recommend-013"]
    assert t["browse_gap"]["four_call_samples_outside_the_seven"] == []
    assert t["tokens_out_five"]["persists"]
    assert t["tokens_out_five"]["cases"]["blackout-001"]["fails_by_majority"]
    assert not t["tokens_out_five"]["cases"]["blackout-007"]["fails_by_majority"]


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
    rec = reader.join(planted)
    assert not rec["claim"]["holds"]
    assert rec["claim"]["3_call_or_fewer_samples_over"] == ["blackout-008 s1"]
    [falsifier] = rec["claim"]["falsifiers"]
    assert falsifier == {"sample": "blackout-008 s1", "calls": 3, "tokens_in": 7720, "at_mandate": True,
                         "row": reader.ROW_RULE_AT_MANDATE}
    band = rec["fresh_band"]
    assert band["empty"] and band["mandated_shape_max"] == 7720 and band["integer_band"] is None
    assert band["reading"].startswith("the rule has no solution")


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

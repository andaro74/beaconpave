"""
M08b's residual reader: A, B, E, S and the two identities, pinned on a planted
run before the calibration call is made (SPEC/08b, PR 2; ADR-074 decision 3 §4).

`milestones/M08b/residual_attribution.py` reads the fresh run's round-1
`tokens_in` on the calibration case (A), the calibration call's (B), and the
census's estimates by key (E, S), and writes D = B − E, F = A − B − S with
signs and shares, plus each later round's growth against the replayed
transcript. These tests pin the record over the planted run, check the
arithmetic, and plant what the reader must refuse or must read as a finding:
a calibration that offered tools, round-1 figures that disagree across
samples, a calibration on a case the rule did not name, and the two fallbacks
SPEC/08b pre-registers — B from the audit record's copy, and the call
re-issued on `entitlement-010`.

Hermetic (G8). Seats: AI Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M08b" / "residual_attribution.py"
PLANTED = ROOT / "tests" / "fixtures" / "m08b" / "planted"
RECORD = PLANTED / "residual-attribution.json"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("residual_attribution", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["residual_attribution"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def planted(tmp_path):
    copy = tmp_path / "planted"
    shutil.copytree(PLANTED, copy)
    return copy


def _rewrite(path: pathlib.Path, fn) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def test_the_record_is_what_the_planted_inputs_produce(reader):
    produced = json.dumps(reader.record(PLANTED), indent=2, ensure_ascii=False) + "\n"
    assert produced == RECORD.read_text(encoding="utf-8"), (
        "residual-attribution.json under the planted fixture is not what the reader produces; "
        "re-run `python milestones/M08b/residual_attribution.py --dir tests/fixtures/m08b/planted`")


def test_the_two_identities_and_the_reading(reader):
    rec = reader.record(PLANTED)
    est, att = rec["estimates"], rec["attribution"]
    assert rec["case"] == "blackout-008" and not rec["fallback_taken"]
    assert rec["B_read_from"] == "usage.calls[0].tokens_in"
    # E and S by key from the census record: the system block's estimate plus
    # the case's own viewer turn at the census's chars-per-token; the specs' total.
    assert est["system_prompt_tokens_est"] == 793 and est["S"] == 603
    assert est["viewer_turn_tokens_est"] == 41 and est["E"] == 834
    assert est["E_band"] == [830, 835] and est["S_band"] == [600, 604]
    assert att["A"] == 1980 and att["A_values"] == [1980, 1980, 1980] and att["B"] == 1470
    assert att["D"] == 636 and att["F"] == -93
    assert att["residual_A_minus_E_minus_S"] == 543 == att["D"] + att["F"]
    assert att["identity_holds"]
    assert att["F_sign"] == "negative" and att["D_sign"] == "non-negative"
    assert att["shares_of_abs"] == {"D": 0.872, "F": 0.128}
    assert att["reading"].startswith("tokeniser density")
    assert att["downward_trigger"]["armed"] is False
    growth = rec["per_round_growth"]
    assert growth["available"] and growth["chars_per_token_measured"] == 1.914
    assert len(growth["rows"]) == 121 and len(growth["more_than_a_quarter_unexplained"]) == 10
    assert growth["finding"].startswith("dated finding")


def test_a_calibration_that_offered_tools_is_refused(reader, planted):
    _rewrite(planted / "calibration.json", lambda c: c.update(tools="present"))
    with pytest.raises(SystemExit, match="tools were absent"):
        reader.record(planted)


def test_round_1_figures_that_disagree_across_samples_are_a_finding_not_a_number(reader, planted):
    def bend(answers):
        answers["blackout-008"]["usage"]["calls"][0]["tokens_in"] = 1990
        answers["blackout-008"]["usage"]["tokens_in"] += 10
    _rewrite(planted / "goldens-run-2.json", bend)
    att = reader.record(planted)["attribution"]
    assert att["A"] is None and att["A_values"] == [1980, 1990, 1980]
    assert att["reading"].startswith("unreadable") and "disagree" in att["finding"]


def test_b_falls_back_to_the_audit_records_copy_when_the_turn_was_refused(reader, planted):
    def refused(c):
        c["decision"] = "blocked"
        c["mechanism"] = "guardrail"
        c["usage"] = {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}
    _rewrite(planted / "calibration.json", refused)
    rec = reader.record(planted)
    assert rec["B_read_from"].startswith("record_usage.calls[0].tokens_in")
    assert rec["attribution"]["B"] == 1470 and rec["calibration_decision"] == "blocked"


def test_a_calibration_whose_shape_says_tools_were_offered_is_refused(reader, planted):
    """Tool Owner seat, round 1: `tools: absent` is a literal the producer
    writes, so the guard on it can never disagree with the producer. The turn's
    shape can: a trajectory, or a second round, is proof the event carried tools."""
    _rewrite(planted / "calibration.json",
             lambda c: c.update(trajectory=[{"round": 1, "seq": 1, "tool": "catalog-search",
                                             "args": {"query": "derby"}, "decision": "allowed",
                                             "executed": True}]))
    with pytest.raises(SystemExit, match="carries a trajectory"):
        reader.record(planted)


def test_a_calibration_with_two_rounds_is_refused(reader, planted):
    _rewrite(planted / "calibration.json",
             lambda c: c["usage"]["calls"].append({"tokens_in": 2000, "tokens_out": 50, "latency_ms": 900}))
    with pytest.raises(SystemExit, match="a tools-absent turn is one round"):
        reader.record(planted)


def test_b_unreadable_from_either_copy_is_refused(reader, planted):
    def gone(c):
        c["usage"] = {"tokens_in": 0, "tokens_out": 0, "latency_ms": None}
        c["record_usage"] = None
    _rewrite(planted / "calibration.json", gone)
    with pytest.raises(SystemExit, match="B is unreadable"):
        reader.record(planted)


def test_the_fallback_case_reads_a_from_the_same_case(reader, planted):
    _rewrite(planted / "calibration.json", lambda c: c.update(case="entitlement-010"))
    rec = reader.record(planted)
    assert rec["case"] == "entitlement-010" and rec["fallback_taken"]
    assert rec["attribution"]["A"] == 1980
    assert rec["estimates"]["viewer_turn_chars"] != reader.record(PLANTED)["estimates"]["viewer_turn_chars"]


def test_a_calibration_on_any_other_case_is_refused(reader, planted):
    _rewrite(planted / "calibration.json", lambda c: c.update(case="brand-020"))
    with pytest.raises(SystemExit, match="pre-registered on blackout-008"):
        reader.record(planted)


def test_a_planted_estimate_moves_the_record(reader, planted, tmp_path, monkeypatch):
    """E is read by key from the census record and never re-estimated: move the
    key and D moves by exactly that much, with F unchanged."""
    census = json.loads(reader.CENSUS.read_text(encoding="utf-8"))
    census[reader.COMPONENTS]["per_call_text"]["system_prompt"]["tokens_est"] += 100
    moved = tmp_path / "context-census.json"
    moved.write_text(json.dumps(census), encoding="utf-8")
    before = reader.record(planted)["attribution"]
    monkeypatch.setattr(reader, "CENSUS", moved)
    after = reader.record(planted)["attribution"]
    assert after["D"] == before["D"] - 100 and after["F"] == before["F"]
    assert after["residual_A_minus_E_minus_S"] == before["residual_A_minus_E_minus_S"] - 100


def test_the_reader_imports_no_network_module_and_cannot_reach_the_store():
    from test_m08b_fresh_join import store_reach

    tree = ast.parse(READER.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & NETWORK_MODULES
    # Security seat, round 1: a `from core import withheld` planted here
    # survived the whole suite, because no G4 root reached `milestones/`.
    assert store_reach(tree) == [], f"the reader can reach the refused-content store: {store_reach(tree)}"


def test_the_share_threshold_is_the_pre_registered_seventy_percent(reader):
    """AI Quality seat, round 1: `SHARE_NAMES` moved to 0.51 with the suite
    green, because the planted shares are 0.872 and 0.128. Pinned literally and
    exercised at the boundary: 70 of 100 names density, 69 names both, and a
    negative component's share is of its magnitude."""
    assert reader.SHARE_NAMES == 0.70
    est = {"E": 800, "S": 600}
    # A = 1500 + ...: choose A and B so D and F land where the case needs them.
    density = reader.attribute([1570] * 3, 870, est)      # D = 70, F = 100 - ... recomputed below
    assert density["D"] == 70 and density["F"] == 100 and density["reading"].startswith("both")
    exact = reader.attribute([1500] * 3, 870, est)        # D = 70, F = 30
    assert exact["D"] == 70 and exact["F"] == 30 and exact["reading"].startswith("tokeniser density")
    just_under = reader.attribute([1500] * 3, 869, est)   # D = 69, F = 31
    assert just_under["D"] == 69 and just_under["F"] == 31 and just_under["reading"].startswith("both")
    negative = reader.attribute([1330] * 3, 870, est)     # D = 70, F = -140
    assert negative["F"] == -140 and negative["F_sign"] == "negative"
    assert negative["shares_of_abs"] == {"D": 0.333, "F": 0.667} and negative["reading"].startswith("both")
    framing = reader.attribute([1300] * 3, 800, est)      # D = 0, F = -100
    assert framing["reading"].startswith("provider-side framing")


def test_a_response_usage_that_disagrees_with_the_record_is_refused(reader, planted):
    """Platform Engineering seat, round 1: the producer writes that the two
    must agree, and nothing compared them — a 400-token disagreement was
    returned silently as B on a residual bounded at 422–537."""
    _rewrite(planted / "calibration.json",
             lambda c: c["record_usage"]["calls"][0].update(tokens_in=1870))
    with pytest.raises(SystemExit, match="the two must agree before B is readable"):
        reader.record(planted)


def test_the_real_directory_has_no_calibration_yet(reader):
    with pytest.raises(SystemExit, match="calibration call has not been made"):
        reader.record(reader.HERE)

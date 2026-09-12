"""
M09b's F-against-G reader, held to the M08b reader it inherits and to the three
things SPEC/09b says it adds: a baseline taken as an argument, two readings with
the disagreement published, and an at-least-once companion.

Hermetic (G8). No held text is read anywhere: a grants file is booleans. Owning
seats: AI Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import shutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FG = ROOT / "milestones" / "M09b" / "fg.py"
RECORD = ROOT / "milestones" / "M09b" / "fg-pre.json"
M09 = ROOT / "milestones" / "M09"
M08B = ROOT / "milestones" / "M08b"
GRANTS = [ROOT / "milestones" / "M09b" / "withheld-grants-security.json",
          ROOT / "milestones" / "M09b" / "withheld-grants-legal-sp.json"]
BASELINE = M08B / "answer-channel.json"
ARGS = ["--run", str(M09), "--grants", str(GRANTS[0]), "--grants", str(GRANTS[1]),
        "--baseline", str(BASELINE), "--out", str(RECORD)]
NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def fg():
    spec = importlib.util.spec_from_file_location("m09b_fg", FG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _two(tmp_path, source: pathlib.Path, mutate=None) -> list[pathlib.Path]:
    paths = []
    for label in ("a", "b"):
        path = tmp_path / f"withheld-grants-{label}.json"
        shutil.copy(source, path)
        paths.append(path)
    if mutate:
        data = json.loads(paths[1].read_text(encoding="utf-8"))
        mutate(data)
        paths[1].write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths


def test_g_and_the_majority_f_are_answer_channels_own(fg, tmp_path):
    """Through the inherited reader: M08b's run and grants, as both readings,
    reproduce M08b's committed `answer-channel.json` exactly."""
    committed = json.loads(BASELINE.read_text(encoding="utf-8"))
    rec = fg.record(M08B, _two(tmp_path, M08B / "withheld-grants.json"), BASELINE)
    assert rec["reading"]["agree"] is True
    assert (rec["reading"]["G"], rec["reading"]["F_majority"]) == (committed["G"], committed["F"])
    for reading in rec["readings"].values():
        assert reading["G_cases"] == committed["G_cases"]
        assert reading["F_majority_cases"] == committed["F_cases"]


def test_the_committed_record_is_what_the_committed_inputs_produce(fg):
    assert fg.main([*ARGS, "--check"]) == 0


def test_a_disagreement_is_published_and_not_resolved(fg, tmp_path):
    def flip(data):
        data["grants"]["recommend-003"]["s1"]["grant"] = False
    rec = fg.record(M09, _two(tmp_path, GRANTS[0], flip), BASELINE)
    assert rec["reading"]["agree"] is False
    assert "recommend-003 s1 grant: True / False" in rec["reading"]["disagreements"]
    assert "G" not in rec["reading"] and "F_majority" not in rec["reading"]
    assert set(rec["direction_against_baseline"]) == {"a", "b"}


def test_the_baseline_is_an_argument_with_no_default(fg, tmp_path):
    with pytest.raises(SystemExit):
        fg.main([a for a in ARGS if a not in ("--baseline", str(BASELINE))])
    other = tmp_path / "other-baseline.json"
    other.write_text(json.dumps({"G": 99, "F": 7}), encoding="utf-8")
    rec = fg.record(M09, GRANTS, other)
    assert rec["direction_against_baseline"]["G"]["baseline"] == 99
    assert rec["direction_against_baseline"]["F_majority"]["baseline"] == 7


def test_no_module_constant_supplies_a_baseline(fg):
    """The debt, as a property of the file: `PRIOR` in `answer_channel.py` is a
    module-level literal, and nothing in this file may be one of those again."""
    tree = ast.parse(FG.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = getattr(target, "id", "")
                assert not any(word in name.upper() for word in ("PRIOR", "BASELINE")), (
                    f"module-level {name} in fg.py; the baseline is an argument")
    assert "PRIOR" not in FG.read_text(encoding="utf-8").split('"""', 2)[2]


def test_a_baseline_whose_readings_disagree_is_refused(fg, tmp_path):
    bad = tmp_path / "fg-disagreeing.json"
    bad.write_text(json.dumps({"reading": {"agree": False}}), encoding="utf-8")
    with pytest.raises(SystemExit):
        fg.record(M09, GRANTS, bad)


def test_exactly_two_distinct_readings(fg):
    with pytest.raises(SystemExit):
        fg.record(M09, GRANTS[:1], BASELINE)
    with pytest.raises(SystemExit):
        fg.record(M09, [GRANTS[0], GRANTS[0]], BASELINE)


def test_the_at_least_once_companion_counts_one_refused_grant_and_nothing_else(fg):
    per_case = {
        "one-of-three": {"dec001_samples": [], "refused_on_answer_by_entitlement_topic": [2]},
        "not-a-grant": {"dec001_samples": [], "refused_on_answer_by_entitlement_topic": [1]},
        # a case with a DEC-001 sample AND a plain grant sample: excluded as a case,
        # which is answer_channel.py's rule for F, not rescued by the other sample
        "dec001": {"dec001_samples": [1], "refused_on_answer_by_entitlement_topic": [1, 2]},
        "unrefused": {"dec001_samples": [], "refused_on_answer_by_entitlement_topic": []},
    }
    grants = {"one-of-three": {"s2": {"grant": True, "dec001_shape": False}},
              "not-a-grant": {"s1": {"grant": False, "dec001_shape": False}},
              "dec001": {"s1": {"grant": True, "dec001_shape": True},
                         "s2": {"grant": True, "dec001_shape": False}}}
    assert fg.f_at_least_once(per_case, grants) == ["one-of-three"]


def test_a_census_the_run_did_not_write_is_published_as_a_mismatch(fg):
    sidecar = json.loads((M09 / "goldens-run-refusals.json").read_text(encoding="utf-8"))
    assert fg.refusal_reading(sidecar)["any_refusal_matches_the_sidecars_census"] is True
    sidecar["census"]["refused_by_majority"] += 1
    assert fg.refusal_reading(sidecar)["any_refusal_matches_the_sidecars_census"] is False


def test_the_recomputed_census_matches_the_runs_own():
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    assert rec["refusals"]["any_refusal_matches_the_sidecars_census"] is True


def test_an_unattributed_refusal_is_refused(fg):
    sidecar = json.loads((M09 / "goldens-run-refusals.json").read_text(encoding="utf-8"))
    del sidecar["refusals"]["brand-021"]["s2"]
    with pytest.raises(SystemExit):
        fg.refusal_reading(sidecar)


def test_the_reader_imports_no_network_module():
    tree = ast.parse(FG.read_text(encoding="utf-8"))
    imported = {alias.name.split(".")[0] for node in ast.walk(tree)
                if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom) and node.module}
    assert not imported & NETWORK_MODULES

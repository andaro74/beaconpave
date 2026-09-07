"""
M08 PR 4's re-score join: the committed record is what the committed inputs produce.

`milestones/M08/rescore-join.json` is where SPEC/08's one claim is read —
every committed stage-2 answered sample at three calls or fewer passes
`tokens_in` at the signed ceiling and every sample at four or more fails it —
joined per sample from the transcripts PR 4 ran once and the census's call
counts. A record that can drift from its reader is prose; these tests re-run
the reader over the committed inputs and refuse the drift, and they pin what
the reader's docstring promises: no network module, no ceiling argument, and
verdicts that are computed from the rows rather than written into them.

Hermetic (G8). Seats, by the two-key rule the reader and record sit on:
AI Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M08" / "rescore_join.py"
RECORD = ROOT / "milestones" / "M08" / "rescore-join.json"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("rescore_join", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["rescore_join"] = module
    spec.loader.exec_module(module)
    return module


def _produced(reader) -> str:
    return json.dumps(reader.join(), indent=2, ensure_ascii=False) + "\n"


def test_the_record_is_what_the_committed_inputs_produce(reader):
    """Byte for byte, as `--check` compares it."""
    assert _produced(reader) == RECORD.read_text(encoding="utf-8"), (
        "rescore-join.json is not what the committed inputs produce; re-run "
        "`python milestones/M08/rescore_join.py` and commit the result, or find "
        "which input moved")


def test_the_reader_imports_no_network_module():
    """Zero model calls, no network: a property of the source, not a promise."""
    tree = ast.parse(READER.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & NETWORK_MODULES, imported & NETWORK_MODULES


def test_the_reader_takes_no_ceiling_and_reads_the_live_one():
    """The ceiling is read from `cases.yaml`, never passed in: the record's
    count is the one the transcripts were scored at and no other."""
    source = READER.read_text(encoding="utf-8")
    assert "--ceiling" not in source
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert record["ceiling"] == record["claim"]["ceiling"]
    assert record["census_ceiling"] == 6000, "the census still describes 6000; the join describes the live ceiling"
    assert record["inputs_sha256"]["services/highlights-agent/evals/golden/cases.yaml"] == (
        json.loads((ROOT / "milestones" / "M08" / "context-census.json").read_text(encoding="utf-8"))
        ["inputs_sha256"]["services/highlights-agent/evals/golden/cases.yaml"]
    ), "the join and the census digest different cases files"


def test_a_planted_verdict_changes_the_record(reader, monkeypatch):
    """The record is a function of the transcripts, not a copy of the last run:
    one sample's PASS flipped to FAIL in memory and the record moves with it."""
    real_read = reader._read

    def planted(path):
        text = real_read(path)
        if path == reader.PER_SAMPLE_NEW:
            text = text.replace("brand-020        PASS", "brand-020        FAIL", 1)
        return text

    monkeypatch.setattr(reader, "_read", planted)
    assert _produced(reader) != RECORD.read_text(encoding="utf-8")


def test_the_claim_is_computed_from_the_rows(reader, monkeypatch):
    """A three-call sample given a `tokens_in` failure in memory turns the
    claim's first half False and names the sample; the flag is not a constant."""
    real_rows = reader.per_sample_rows

    def planted(census, new_blocks, old_blocks, ceiling):
        rows = real_rows(census, new_blocks, old_blocks, ceiling)
        target = next(r for r in rows if r["case"] == "brand-020" and r["sample"] == 1)
        assert target["calls"] == 3
        target["tokens_in_verdict"] = "FAIL"
        return rows

    monkeypatch.setattr(reader, "per_sample_rows", planted)
    record = reader.join()
    assert record["claim"]["every_3_call_or_fewer_sample_passes_tokens_in"] is False
    assert record["claim"]["3_call_or_fewer_samples_over"] == ["brand-020 s1"]
    assert record["claim"]["holds"] is False
    committed = json.loads(RECORD.read_text(encoding="utf-8"))
    assert committed["claim"]["holds"] is True
    assert committed["claim"]["every_4_call_or_more_sample_fails_tokens_in"] is True


def test_the_side_prediction_is_computed_from_the_flip_set(reader, monkeypatch):
    """One of the ten held at FAIL in the k=3 transcript, in memory: the
    falsifier names it, `held` turns False, and the count moves with it."""
    real_read = reader._read

    def planted(path):
        text = real_read(path)
        if path == reader.K3:
            text = text.replace("edge-024         PASS  [PASS PASS PASS]",
                                "edge-024         FAIL  [FAIL FAIL FAIL]", 1)
            text = text.replace("12/25 passed (13 failed", "11/25 passed (14 failed", 1)
        return text

    monkeypatch.setattr(reader, "_read", planted)
    record = reader.join()
    side = record["side_prediction"]
    assert side["falsifiers"]["one_of_the_ten_did_not_flip"] == ["edge-024"]
    assert side["N"] == 11 and side["N_in_bound"] and not side["N_is_predicted"]
    assert side["held"] is False
    committed = json.loads(RECORD.read_text(encoding="utf-8"))
    assert committed["side_prediction"]["held"] is True
    assert all(not v for v in committed["side_prediction"]["falsifiers"].values())


def test_a_transcript_scored_at_another_ceiling_is_refused(reader, monkeypatch):
    """A `tokens_in` line naming a ceiling other than the live one is a
    transcript scored against something other than this record."""
    real_read = reader._read

    def planted(path):
        text = real_read(path)
        if path == reader.PER_SAMPLE_NEW:
            text = text.replace("tokens_in=8302 over 7700", "tokens_in=8302 over 8000", 1)
        return text

    monkeypatch.setattr(reader, "_read", planted)
    with pytest.raises(SystemExit, match="over 8000"):
        reader.join()

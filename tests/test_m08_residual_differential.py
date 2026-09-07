"""
M08's residual differential: the committed record is what the committed inputs produce.

`milestones/M08/residual-differential.json` is the zero-call narrowing ADR-073
amendment 1 (question 3) asked for and SPEC/08 amendment 1 dates: the tools
arm's per-call input at M02 (one tool offered) against M07 stage 2 (two tools),
across one added tool spec of known size, read off the same committed runs the
census reads. It answers one question — does the unattributed residual grow
with the added spec? — and states which of amendment 1's three explanations
that does and does not separate. These tests re-run the reader over the
committed inputs and refuse drift, and pin the same three properties the
census's reader promises: no network module, no ceiling argument and no pass
count, and a record that moves when an input does.

Hermetic (G8). Owning seats: Platform Engineering (the loop's shape, which owns
the residual debt) · AI Quality (the ceiling the residual may move).
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M08" / "residual_differential.py"
RECORD = ROOT / "milestones" / "M08" / "residual-differential.json"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def reader():
    spec = importlib.util.spec_from_file_location("residual_differential", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["residual_differential"] = module
    spec.loader.exec_module(module)
    return module


def test_the_record_is_what_the_committed_inputs_produce(reader):
    """Byte for byte, as `--check` compares it."""
    produced = json.dumps(reader.differential(), indent=2, ensure_ascii=False) + "\n"
    assert produced == RECORD.read_text(encoding="utf-8"), (
        "residual-differential.json is not what the committed inputs produce; re-run "
        "`python milestones/M08/residual_differential.py` and commit the result, or find "
        "which input moved")


def test_the_reader_imports_no_network_module():
    """Zero model calls, no network: a property of the source, not a promise.
    `subprocess` is allowed for `--verify-history`, which runs `git show` against
    the local clone and nothing else; `differential()` never calls it."""
    tree = ast.parse(READER.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & NETWORK_MODULES, imported & NETWORK_MODULES


def test_the_reader_offers_no_ceiling_and_the_record_no_pass_count():
    """SPEC/08 constraint 2 reaches every reader under `milestones/M08/`: no
    ceiling argument, no `passed` figure at any ceiling, 6000 included."""
    source = READER.read_text(encoding="utf-8")
    assert "--ceiling" not in source
    text = RECORD.read_text(encoding="utf-8")
    assert '"passed"' not in text and "/25" not in text


def test_the_m02_era_text_the_differential_assumes_is_still_heads(reader):
    """The arithmetic subtracts HEAD's committed text from M02's per-call base,
    which is only valid because the client, the answer schema and the
    `catalog-search` contract as sent were byte-identical at M02's run commit.
    The M02-era digests are constants verified against `git show` when the
    record was produced (`--verify-history`); this pins HEAD's side, so a client
    or contract change turns the record red rather than quietly invalidating
    the subtraction."""
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    era = record["m02_era_text"]
    head = reader.head_text_digests()
    for key, digest in era["rebuilt_text_sha256_at_m02"].items():
        assert head[key] == digest, (
            f"{key} at HEAD no longer digests to what it did at {era['commit'][:7]}; the "
            "differential's subtraction assumed the same committed text on both sides")
    assert era["identical_to_head"] is True


def test_a_planted_token_count_changes_the_record(reader, monkeypatch):
    """The record reads the runs: a planted `tokens_in` on one M02 sample moves
    it. Written so the pin above cannot be satisfied by a record that reads
    nothing (the ADR-042 prediction-7 shape, and this repo's own audit finding
    that four of ten checks were silent)."""
    census = sys.modules["context_census"]
    real = census._load

    def planted(path):
        data = real(path)
        if path.name == "m02-tools-1.json" and "blackout-001" in data:
            data["blackout-001"]["usage"]["tokens_in"] += 5000
        return data

    monkeypatch.setattr(census, "_load", planted)
    committed = json.loads(RECORD.read_text(encoding="utf-8"))
    assert reader.differential() != committed, "a planted token count left the record unchanged"


def test_the_record_names_what_it_cannot_distinguish(reader):
    """Amendment 1 §3 gave three explanations. The record must say which the
    differential separates and which it cannot, in those words, so the debt
    row stays a debt and the differential is not read as having paid it."""
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    reading = record["reading"]
    assert set(reading["cannot_separate"]) == {"provider_side_tool_use_framing",
                                               "content_the_agent_sends_no_committed_text_shows"}
    assert "estimation_error_on_tool_spec_json" in reading["rules_out"]
    assert reading["paid_by"]["owed_to"] == ["platform-eng", "ai-quality"]
    assert reading["paid_by"]["date"] == "M09 PR 1"

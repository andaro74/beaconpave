"""
M08's context census: the committed record is what the committed inputs produce.

`milestones/M08/context-census.json` is the evidence SPEC/08's one claim is
written from — where the tools arm's `tokens_in` goes, by call and by
component, and which of two pre-registered outcomes the rule picks. A record
that can drift from its reader is prose; these tests re-run the reader over the
committed inputs and refuse the drift, and they pin the three properties the
reader's docstring promises: it calls no network, it prints no pass count at any
ceiling but 6000, and its decision rule reads per sample.

Hermetic (G8). Owning seats: AI Quality (the budget axis) · Platform Engineering
(the loop the census describes).
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
READER = ROOT / "milestones" / "M08" / "context_census.py"
RECORD = ROOT / "milestones" / "M08" / "context-census.json"
CLIENT = ROOT / "services" / "highlights-agent" / "gateway_client.py"

NETWORK_MODULES = {"boto3", "botocore", "urllib", "urllib3", "requests", "socket", "http", "httpx"}


@pytest.fixture(scope="module")
def census():
    spec = importlib.util.spec_from_file_location("context_census", READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["context_census"] = module
    spec.loader.exec_module(module)
    return module


def test_the_record_is_what_the_committed_inputs_produce(census):
    """Byte for byte, as `--check` compares it."""
    produced = json.dumps(census.census(), indent=2, ensure_ascii=False) + "\n"
    assert produced == RECORD.read_text(encoding="utf-8"), (
        "context-census.json is not what the committed inputs produce; re-run "
        "`python milestones/M08/context_census.py` and commit the result, or find "
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


def test_the_reader_offers_no_other_ceiling():
    """No pass count at any ceiling but 6000: the reader takes no ceiling
    argument, and the record carries no `passed` figure anywhere."""
    source = READER.read_text(encoding="utf-8")
    assert "--ceiling" not in source and "ceiling=" not in source.replace("ceiling_", "")
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert record["ceiling"] == 6000

    def keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from keys(v)
    offenders = [k for k in keys(record) if "pass" in k.lower()]
    assert not offenders, offenders


def test_the_client_constants_are_read_off_the_source_the_client_defines(census):
    """The reader parses `gateway_client.py` rather than importing it (boto3).
    The pin: the reproduced `user_turn` equals the real function, executed from
    its own source with only `CLOCK` bound — no import, no SDK."""
    tree = ast.parse(CLIENT.read_text(encoding="utf-8"))
    source = CLIENT.read_text(encoding="utf-8")
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "user_turn")
    constants = census.client_constants()
    namespace = {"CLOCK": constants["CLOCK"]}
    exec(ast.get_source_segment(source, function), namespace)  # noqa: S102 — the client's own def
    case = {"input": "Is the derby on?", "viewer": {"plan": "base", "dma": "port-william"}}
    assert census.user_turn(constants, case) == namespace["user_turn"](case["input"], "base", "port-william")
    for name in ("SYSTEM", "TOOL_SYSTEM", "CLOCK"):
        assert constants[name]


def test_the_mandated_call_count_follows_the_case_asserts(census):
    """Three calls when the case expects `entitlement-check` before the answer
    (search, then a check on the title the search returned, then the answer);
    two otherwise; never one."""
    import yaml
    cases = yaml.safe_load(census.CASES.read_text(encoding="utf-8"))
    for case in cases:
        expects = (case.get("trajectory") or {}).get("expect_tool_before_answer") == "entitlement-check"
        assert census.mandated_calls(case) == (3 if expects else 2), case["id"]


def test_the_decision_rule_reads_per_sample(census):
    """A sample that carried nothing removable cannot be brought under the
    ceiling by removing it. The first run of the reader compared the largest
    removable amount in one sample with the largest gap in another and printed
    A; this pins the reading that is coherent with A's own falsifier."""
    cal = {"chars_per_token": {"min": 3.3, "median": 3.4, "max": 3.5}}
    removable = {"text_sent_twice": {"tokens_per_call_est": 0}, "removable_tokens_per_call_est": 500.0}
    over_with_nothing = {"answered": True, "calls": 3, "mandated_calls": 3, "tokens_in": 6300,
                         "over_ceiling": True, "rows_returned": 1, "rows_returned_not_cited": 0,
                         "replayed_steps": [{"tool": "catalog-search", "chars": 216}],
                         "case": "x", "sample": 1}
    under_with_plenty = {"answered": True, "calls": 3, "mandated_calls": 3, "tokens_in": 5000,
                         "over_ceiling": False, "rows_returned": 5, "rows_returned_not_cited": 5,
                         "replayed_steps": [{"tool": "catalog-search", "chars": 5000}],
                         "case": "y", "sample": 1}
    reading = census.decision_rule([over_with_nothing, under_with_plenty], removable, cal)
    assert reading["outcome"] == "B"
    assert reading["per_sample"][0]["covered"] is False
    covered = dict(over_with_nothing, rows_returned=5, rows_returned_not_cited=5,
                   replayed_steps=[{"tool": "catalog-search", "chars": 5000}])
    assert census.decision_rule([covered], removable, cal)["outcome"] == "A"


def test_a_planted_token_count_changes_the_record(census, monkeypatch):
    """The record is a function of the inputs, not a copy of the last run: one
    `tokens_in` moved by one token in memory and the record moves with it."""
    real_load = census._load
    target = (ROOT / "milestones" / "M07" / "goldens-run-1.json").resolve()

    def planted(path):
        data = real_load(path)
        if pathlib.Path(path).resolve() == target:
            data["blackout-001"]["usage"]["tokens_in"] += 1
        return data

    monkeypatch.setattr(census, "_load", planted)
    produced = json.dumps(census.census(), indent=2, ensure_ascii=False) + "\n"
    assert produced != RECORD.read_text(encoding="utf-8")

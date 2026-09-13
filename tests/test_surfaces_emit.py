"""
The surface runners' writer: raw output in, one verdict in the closed envelope out.

`surfaces/web-player/emit.py` is the only place a Playwright or k6 result becomes a
verdict record. These tests hold its three outcomes apart and put every record it writes
through the gate itself, so a record the closed envelope refuses is red here rather than
at a merge.

Hermetic (G8): raw outputs are written to `tmp_path`, no browser and no k6 run, and
`commit` is passed so nothing calls git.

Owning seat: AI Quality (what PASS, FAIL and INFRA mean); Platform Engineering (the writer).
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

from pave import gate
from pave import verdict as verdict_mod

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("surfaces_emit", ROOT / "surfaces" / "web-player" / "emit.py")
emit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emit)

EXPECTED_EXIT = {"PASS": gate.EXIT_OK, "FAIL": gate.EXIT_QUALITY, "INFRA": gate.EXIT_CONTRACT}


def _pw(checks=None, error=None) -> dict:
    return {"runner": "playwright", "url": "http://127.0.0.1:1/", "browser": "chromium 0",
            "checks": checks if checks is not None else [], "error": error, "duration_s": 1.0}


def _k6(thresholds_ok=(True, True), transport_errors=0, answered=100) -> dict:
    metrics = {
        "http_req_failed": {"values": {"rate": 0}, "thresholds": {"rate<0.01": {"ok": thresholds_ok[0]}}},
        "http_req_duration": {"values": {"p(95)": 6.2}, "thresholds": {"p(95)<200": {"ok": thresholds_ok[1]}}},
        "iterations": {"values": {"count": 100}},
    }
    if transport_errors:
        metrics["transport_errors"] = {"values": {"count": transport_errors}}
    if answered:
        metrics["responses_received"] = {"values": {"count": answered}}
    return {"state": {"testRunDurationMs": 10000}, "metrics": metrics}


HELD = [{"name": "a", "ok": True}, {"name": "b", "ok": True}]
ONE_FAILED = [{"name": "a", "ok": True}, {"name": "b", "ok": False}]

CASES = [
    ("playwright", _pw(HELD), "PASS"),
    ("playwright", _pw(ONE_FAILED), "FAIL"),
    ("playwright", _pw(error="net::ERR_CONNECTION_REFUSED"), "INFRA"),
    ("playwright", _pw([]), "INFRA"),
    ("k6", _k6(), "PASS"),
    ("k6", _k6((False, True)), "FAIL"),
    # Some requests never connected and the rest were answered: the surface was there,
    # so the thresholds decide. Measured on a served 404 before this rule was written.
    ("k6", _k6((False, True), transport_errors=905, answered=6000), "FAIL"),
    ("k6", _k6((False, False), transport_errors=12, answered=0), "INFRA"),
    ("k6", {"state": {}, "metrics": {"responses_received": {"values": {"count": 1}}}}, "INFRA"),
]


@pytest.mark.parametrize("kind, raw, expected", CASES,
                         ids=[f"{k}-{e}-{i}" for i, (k, _, e) in enumerate(CASES)])
def test_each_outcome_is_written_and_the_gate_decides_it_by_the_one_contract(kind, raw, expected, tmp_path):
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    record = emit.RECORDERS[kind](raw_path, commit="deadbeef")
    assert record["verdict"] == expected, record
    out = verdict_mod.write(tmp_path / "verdict.json", record)
    assert gate.decide([str(out)]).exit_code == EXPECTED_EXIT[expected]


@pytest.mark.parametrize("kind", sorted(emit.RECORDERS))
def test_a_runner_that_wrote_nothing_is_infra_never_pass_or_fail(kind, tmp_path):
    record = emit.RECORDERS[kind](tmp_path / "never-written.json", commit="deadbeef")
    assert record["verdict"] == "INFRA"
    assert record["fail_closed"] is True


def test_a_fail_names_what_failed(tmp_path):
    """The gate teaches (claim 2): a FAIL says which check or threshold, not only that one did."""
    pw = tmp_path / "pw.json"
    pw.write_text(json.dumps(_pw(ONE_FAILED)), encoding="utf-8")
    assert "FAILED: b" in emit.playwright_record(pw, commit="deadbeef")["notes"]
    k6 = tmp_path / "k6.json"
    k6.write_text(json.dumps(_k6((True, False))), encoding="utf-8")
    assert "threshold breached: http_req_duration p(95)<200" in emit.k6_record(k6, commit="deadbeef")["notes"]

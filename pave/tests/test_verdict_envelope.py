"""
The verdict envelope is closed: a runner cannot invent a key and still pass the gate.

Claim 3 is *one verdict schema, many runners*, and its proof artifact is *agent evals,
Playwright and k6 emit identical JSON*. Until M10 PR 1 the schema declared no
`additionalProperties`, so `gate decide` passed a Playwright record carrying `p95_ms`
and `browser`, a k6 record carrying `http_req_duration_p95` and `checks`, and a
`provenance` carrying `runner_version`, all at exit 0. `pave/verdict.py` said it
prevented exactly that drift; nothing enforced it.

The three records are committed under `quality/verdicts/fixtures/`, on the verdict
schema's own rule. Each one is refused here, and each one with its planted keys removed
is admitted, so the refusal is the key and never something else about the record.

**`scores` and `baseline_diff` stay open objects of numbers.** That is where a runner's
own metrics belong, and it is what lets one envelope carry many runners. A test below
holds it open, so closing the envelope cannot quietly close the metrics too.

Owning seat: AI Quality (the schema and the fixtures); Platform Engineering (the gate).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from pave import gate

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "quality" / "verdicts" / "fixtures"

#: fixture -> (where the gate reports the violation, the keys planted there)
PLANTS = {
    "undeclared-key-playwright.json": ("<root>", ("browser", "p95_ms")),
    "undeclared-key-k6.json": ("<root>", ("checks", "http_req_duration_p95")),
    "undeclared-key-provenance.json": ("provenance", ("runner_version",)),
}


def _without_plants(name: str) -> dict:
    record = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    where, keys = PLANTS[name]
    target = record if where == "<root>" else record[where]
    for k in keys:
        del target[k]
    return record


def test_the_fixture_directory_holds_exactly_the_planted_records():
    """A fixture deleted or renamed would shrink the parametrized tests below to fewer
    cases and leave them green. This makes that loud."""
    on_disk = sorted(p.name for p in FIXTURES.glob("*.json"))
    assert on_disk == sorted(PLANTS), (
        f"quality/verdicts/fixtures/ holds {on_disk}; this file plants {sorted(PLANTS)}. "
        "Each fixture is a record the gate must refuse, so the two lists move together.")


@pytest.mark.parametrize("name", sorted(PLANTS))
def test_the_gate_refuses_a_verdict_carrying_an_undeclared_key(name):
    where, keys = PLANTS[name]
    decision = gate.decide([str(FIXTURES / name)])
    assert decision.exit_code == gate.EXIT_CONTRACT, (
        f"{name} carries {keys} the verdict schema does not declare, and the gate "
        f"returned exit {decision.exit_code}. A runner can invent a shape again.")
    (finding,) = decision.findings
    assert finding.kind == gate.CONTRACT
    assert f"verdict violates the verdict schema at {where}:" in finding.reason, finding.reason
    assert "Additional properties are not allowed" in finding.reason, finding.reason
    for k in keys:
        assert repr(k) in finding.reason, (k, finding.reason)


@pytest.mark.parametrize("name", sorted(PLANTS))
def test_the_same_record_without_its_planted_keys_is_admitted(name, tmp_path):
    """The positive control. Without it, a fixture refused for a missing field or a bad
    enum would satisfy the refusal test while the envelope stayed open."""
    path = tmp_path / name
    path.write_text(json.dumps(_without_plants(name)), encoding="utf-8")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_OK


def test_gate_decide_refuses_all_three_end_to_end():
    """The named reader, run as CI runs it."""
    paths = [str(FIXTURES / n) for n in sorted(PLANTS)]
    out = subprocess.run(
        [sys.executable, "-m", "pave.cli", "gate", "decide", "--verdicts", *paths],
        cwd=ROOT, capture_output=True)
    text = out.stdout.decode("utf-8", errors="replace")
    assert out.returncode == gate.EXIT_CONTRACT, (out.returncode, text)
    for n in PLANTS:
        assert any("[BLOCK]" in line and n in line for line in text.splitlines()), (n, text)


def test_a_runner_metric_moved_into_scores_is_admitted(tmp_path):
    """One envelope across many runners: a runner's own numbers go in `scores`."""
    record = _without_plants("undeclared-key-playwright.json")
    record["scores"] = {"p95_ms": 812}
    record["baseline_diff"] = {"p95_ms": -40}
    path = tmp_path / "metrics-in-scores.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_OK


@pytest.mark.parametrize("rel, expected", [
    ("milestones/M09/verdict-pre-fix.json", gate.EXIT_QUALITY),
    ("milestones/M09/verdict-post-fix.json", gate.EXIT_OK),
])
def test_the_committed_verdicts_still_read_under_the_closed_envelope(rel, expected):
    """The two verdicts this repository has committed, decided as M09 published them:
    exit 1 before the fix and exit 0 after. Closing the envelope moved neither."""
    decision = gate.decide([str(ROOT / rel)])
    assert decision.exit_code == expected, [f.reason for f in decision.findings]

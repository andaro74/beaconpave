"""
The gate's exit-code contract (G2).

These tests are the enforcement behind "gates fail closed." Each one pins a way
the gate could wrongly let a merge through. If one of them starts failing, the
gate has become skippable and the change that did it is wrong — do not relax the
test to match the new behaviour.

Owning seat: Platform Engineering (mechanism). Changing an expected exit code
here changes the gate's contract with every CI workflow in the repo.
"""
import json

import pytest

from pave import gate

BASE_VERDICT = {
    "service": "highlights-agent",
    "surface": "agent",
    "commit": "deadbeef",
    "suite": "evals",
    "layer": "L2",
    "verdict": "PASS",
    "fail_closed": True,
}


def write_verdict(tmp_path, name="verdict.json", **overrides):
    record = {**BASE_VERDICT, **overrides}
    path = tmp_path / name
    path.write_text(json.dumps(record), encoding="utf-8")
    return str(path)


# --- the affirmative case: the only route to exit 0 --------------------------

def test_pass_verdict_allows_the_merge(tmp_path):
    decision = gate.decide([write_verdict(tmp_path)])
    assert decision.exit_code == gate.EXIT_OK
    assert not decision.blocked


def test_advisory_verdict_does_not_block(tmp_path):
    """A demoted judge (G9) reports ADVISORY and must not be able to block —
    otherwise auto-demotion would turn a miscalibrated judge into an outage."""
    decision = gate.decide([write_verdict(tmp_path, verdict="ADVISORY")])
    assert decision.exit_code == gate.EXIT_OK


def test_all_verdicts_must_pass(tmp_path):
    paths = [
        write_verdict(tmp_path, "a.json", verdict="PASS"),
        write_verdict(tmp_path, "b.json", suite="adversarial", layer="L5", verdict="FAIL"),
    ]
    assert gate.decide(paths).exit_code == gate.EXIT_QUALITY


# --- quality regression: exit 1, pages the service team ----------------------

def test_fail_verdict_blocks_with_exit_1(tmp_path):
    decision = gate.decide([write_verdict(tmp_path, verdict="FAIL")])
    assert decision.exit_code == gate.EXIT_QUALITY
    assert decision.blockers[0].kind == gate.QUALITY


# --- contract failures: exit 2, page the platform ----------------------------

def test_missing_verdict_file_blocks(tmp_path):
    """The load-bearing one. A step that crashes before writing its verdict must
    not read as 'nothing to report, therefore fine'."""
    decision = gate.decide([str(tmp_path / "never-written.json")])
    assert decision.exit_code == gate.EXIT_CONTRACT


def test_empty_argument_list_blocks():
    """A workflow edit that drops the --verdicts values must not silently pass."""
    assert gate.decide([]).exit_code == gate.EXIT_CONTRACT


def test_bom_prefixed_verdict_still_parses(tmp_path):
    """A verdict written by Windows tooling carries a UTF-8 BOM. That is an
    encoding detail, not a harness failure — it must not page the platform."""
    path = tmp_path / "bom.json"
    path.write_text(json.dumps(BASE_VERDICT), encoding="utf-8-sig")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_OK


def test_unparseable_verdict_blocks(tmp_path):
    path = tmp_path / "truncated.json"
    path.write_text('{"service": "highlights-agent", "verd', encoding="utf-8")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_CONTRACT


def test_schema_invalid_verdict_blocks(tmp_path):
    """Missing `fail_closed` entirely — the schema requires it."""
    record = {k: v for k, v in BASE_VERDICT.items() if k != "fail_closed"}
    path = tmp_path / "partial.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_CONTRACT


def test_infra_verdict_blocks_as_a_contract_failure(tmp_path):
    """INFRA means the harness broke, not the code. It still blocks (G2), but it
    pages the platform — so it must not be reported as a team-owned regression."""
    decision = gate.decide([write_verdict(tmp_path, verdict="INFRA")])
    assert decision.exit_code == gate.EXIT_CONTRACT
    assert decision.blockers[0].kind == gate.CONTRACT


def test_fail_closed_false_blocks(tmp_path):
    """Anything submitted to the gate is by definition from a blocking suite. A
    record claiming otherwise is mis-wired, and the gate refuses to guess."""
    decision = gate.decide([write_verdict(tmp_path, fail_closed=False)])
    assert decision.exit_code == gate.EXIT_CONTRACT


def test_contract_failure_outranks_quality_failure(tmp_path):
    paths = [
        write_verdict(tmp_path, "fail.json", verdict="FAIL"),
        str(tmp_path / "missing.json"),
    ]
    assert gate.decide(paths).exit_code == gate.EXIT_CONTRACT


# --- unknown states are blocking, not assumed benign -------------------------

def test_unknown_verdict_value_blocks(tmp_path, monkeypatch):
    """If a future verdict state is added to the schema but not taught to the
    gate, it must block until someone says what it means."""
    schema = gate.load_verdict_schema()
    schema["properties"]["verdict"]["enum"].append("SKIPPED")
    monkeypatch.setattr(gate, "load_verdict_schema", lambda *a, **k: schema)
    decision = gate.decide([write_verdict(tmp_path, verdict="SKIPPED")])
    assert decision.blocked


# --- the CLI honours the exit codes ------------------------------------------

@pytest.mark.parametrize(
    "overrides,expected",
    [({}, gate.EXIT_OK), ({"verdict": "FAIL"}, gate.EXIT_QUALITY), ({"verdict": "INFRA"}, gate.EXIT_CONTRACT)],
)
def test_cli_gate_decide_exits_with_the_decision(tmp_path, overrides, expected):
    from pave import cli

    with pytest.raises(SystemExit) as exc:
        cli.main(["gate", "decide", "--verdicts", write_verdict(tmp_path, **overrides)])
    assert exc.value.code == expected


def test_cli_gate_comment_never_masks_a_failure(tmp_path, capsys):
    """Run with `if: always()` after a failed step — it must report and return
    cleanly rather than adding a second, confusing failure."""
    from pave import cli

    cli.main(["gate", "comment", "--verdicts", write_verdict(tmp_path, verdict="FAIL")])
    assert "BLOCKED" in capsys.readouterr().out


def test_typo_in_flag_name_blocks(tmp_path):
    """`--verdict` instead of `--verdicts` yields no paths, which must block
    rather than pass vacuously."""
    from pave import cli

    with pytest.raises(SystemExit) as exc:
        cli.main(["gate", "decide", "--verdict", write_verdict(tmp_path)])
    assert exc.value.code == gate.EXIT_CONTRACT

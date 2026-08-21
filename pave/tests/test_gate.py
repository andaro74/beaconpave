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


# --- claim 2's other half: the gate teaches ----------------------------------
#
# `gates fail closed AND teach`. The first half has been enforced since M00a. The
# second was a table of verdict names printed to stdout: it said which suite
# failed and never what moved, so a reviewer got a red check and had to open the
# CI run to learn anything. M04 makes the finding travel with the artifact.

def _verdict(tmp_path, name, **kw):
    import json
    record = {"service": "s", "surface": "agent", "commit": "abc", "suite": kw.get("suite", "x"),
              "layer": "L5", "verdict": kw.get("verdict", "PASS"), "fail_closed": True}
    for key in ("scores", "notes"):
        if kw.get(key):
            record[key] = kw[key]
    path = tmp_path / name
    path.write_text(json.dumps(record), encoding="utf-8")
    return str(path)


def test_the_comment_carries_the_scores_each_suite_measured(tmp_path):
    body = gate.summarize([_verdict(tmp_path, "v.json", suite="adversarial",
                                    scores={"m01_passed": 6, "m00b_passed": 0})])
    assert "`m01_passed` 6" in body and "`m00b_passed` 0" in body


def test_the_comment_names_what_moved_and_not_only_that_something_did(tmp_path):
    """The teaching half, stated as the difference it makes.

    `suite reported FAIL` is what the gate said before. It is true, it blocks, and
    it tells the person who has to fix it nothing at all."""
    notes = ["m00b: 5/10 is ABOVE the pinned comparator 0/10",
             "probe result(s) moved against the pin: m00b/ADV-004: FAIL -> PASS"]
    body = gate.summarize([_verdict(tmp_path, "v.json", suite="adversarial",
                                    verdict="FAIL", notes=notes)])
    assert "what moved" in body
    assert "ADV-004" in body
    assert "ABOVE the pinned comparator" in body
    assert "BLOCKED" in body


def test_the_comment_says_who_it_pages_and_why(tmp_path):
    """The exit-code split is the gate's whole design and it is invisible in a red
    check. A contract failure is the platform's; a quality failure is the team's,
    and telling the wrong one is how a gate earns a reputation for crying wolf."""
    quality = gate.summarize([_verdict(tmp_path, "q.json", verdict="FAIL")])
    assert "owner: service team" in quality and "exit 1" in quality

    contract = gate.summarize([_verdict(tmp_path, "i.json", verdict="INFRA")])
    assert "owner: platform" in contract and "exit 2" in contract


def test_the_comment_carries_a_marker_so_a_rerun_replaces_rather_than_stacks(tmp_path):
    """A reviewer scrolling past six stale gate comments to find the current one
    is a gate that has stopped teaching."""
    body = gate.summarize([_verdict(tmp_path, "v.json")])
    assert body.startswith(gate.COMMENT_MARKER)


def test_the_comment_survives_a_verdict_it_cannot_read(tmp_path):
    """A comment that crashes takes the explanation away from exactly the merge
    that is being blocked. `decide` has already recorded what is wrong with the
    file; this must add to that, never replace it with a traceback."""
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    missing = str(tmp_path / "absent.json")
    body = gate.summarize([str(broken), missing])
    assert "BLOCKED" in body
    assert "not valid JSON" in body
    assert "missing" in body


def test_notes_are_rendered_and_never_decide_anything(tmp_path):
    """Structural. The notes are the runner's prose; a gate that branched on them
    would be taking a decision from an unvalidated string, and the reason a suite
    gives for passing is not evidence that it passed."""
    passing = _verdict(tmp_path, "p.json", verdict="PASS",
                       notes=["FAIL", "regression", "ABOVE the pinned comparator"])
    assert gate.decide([passing]).exit_code == gate.EXIT_OK
    assert "PASS" in gate.summarize([passing])

    import pathlib

    source = pathlib.Path(gate.__file__).read_text(encoding="utf-8")
    start = source.index("def _inspect(")
    body = source[start:source.index("\ndef ", start + 10)]
    assert "notes" not in body, "the decider reads the runner's prose"


# --- the decider's own posture (the pipeline is only as strong as this step) ---

#: Every verdict the decider must weigh. A lane can be proven to block and still
#: decide nothing if its verdict is dropped from this list — the contract and
#: infra verdicts predate the convention and were droppable in silence.
EXPECTED_VERDICTS = {"verdict-contract.json", "verdict-infra.json",
                     "verdict-evals.json", "verdict-adv.json"}


def _decider_step():
    """The `gate decide` step, from the real workflow."""
    import pathlib

    import yaml
    root = pathlib.Path(gate.__file__).resolve().parents[1]
    workflow = yaml.safe_load(
        (root / ".github" / "workflows" / "quality-gate.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    assert len(jobs) == 1, f"a second job appeared: {list(jobs)}; is it also fail-closed?"
    job = next(iter(jobs.values()))
    steps = [s for s in job["steps"] if "gate decide" in (s.get("run") or "")]
    assert len(steps) == 1, f"expected exactly one decider step, found {len(steps)}"
    return job, steps[0]


def test_the_decider_step_cannot_be_skipped_or_swallowed():
    """Each lane brought a test for its own verdict; nothing tested the step that
    makes any of them block.

    The Platform seat measured four one-line edits — `continue-on-error: true`,
    `if: false`, `|| true`, and `if: always()` downgraded to `if: success()` —
    each of which leaves `quality-gate / gate` GREEN with 1417 tests passing while
    the gate blocks nothing at all. The required check reports success and the
    merge proceeds. A gate that can be merged past is not a gate, and this is the
    single line of YAML the whole pipeline rests on."""
    job, step = _decider_step()

    assert step.get("continue-on-error") in (None, False), (
        "the decider runs with continue-on-error: its exit code cannot fail the job")
    assert step.get("if") == "always()", (
        f"the decider's condition is {step.get('if')!r}; it must be always(), or a failing "
        "lane skips the decision and the job reports success")
    assert job.get("if") in (None, "true"), (
        f"the gate job is conditional on {job.get('if')!r} and can be turned off wholesale")

    run = step["run"]
    for swallow in ("|| true", "|| exit 0", "continue-on-error", "set +e"):
        assert swallow not in run, f"the decider's exit code is swallowed by {swallow!r}"


def test_the_decider_weighs_every_verdict_the_lanes_write():
    """A lane proven to block still decides nothing if its verdict is not passed
    to the decider. Asserted against the set rather than one suite's file, because
    each lane's own test only ever checked its own."""
    _, step = _decider_step()
    named = {tok for tok in step["run"].split() if tok.endswith(".json")}
    missing = EXPECTED_VERDICTS - named
    assert not missing, f"verdict(s) written by a lane and never weighed: {sorted(missing)}"


def test_the_infra_lane_writes_a_verdict_when_there_is_nothing_to_snapshot(tmp_path):
    """`emit("INFRA")` fires above the line that bound `drifted`, so the closure
    read an unbound local: the lane raised NameError, wrote NO verdict, and exited
    1 with a traceback. G2 held only by absence — the gate blocked because the
    file was missing, not because the lane said INFRA."""
    import subprocess
    import sys

    empty = tmp_path / "cdk.out"
    empty.mkdir()
    out = tmp_path / "verdict-infra.json"
    result = subprocess.run(
        [sys.executable, "-m", "pave.cli", "infra", "snapshot", "--check",
         "--from", str(empty), "--out", str(out)],
        capture_output=True, text=True)

    assert "Traceback" not in result.stderr, result.stderr
    assert "run `cdk synth` first" in result.stderr
    assert result.returncode == gate.EXIT_CONTRACT
    assert out.is_file(), "the INFRA path wrote no verdict"
    assert json.loads(out.read_text(encoding="utf-8"))["verdict"] == "INFRA"

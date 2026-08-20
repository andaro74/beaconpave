"""
The L2 evals lane: what it decides, and the two ways it could decide nothing.

The gate's own comment states the rule this file exists to enforce: *"a
placeholder verdict that reports PASS for an unimplemented suite is
indistinguishable from a real pass"*. The lane was commented out and annotated
`# turns on at M03` from M00a until here, so the first thing to check is that
turning it on bought a decision rather than a green light.

Hermetic. Owning seats: Platform Engineering (the lane and the workflow) · AI
Quality (the comparator, two-key).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPARATORS = ROOT / "evals" / "comparators.json"
WORKFLOW = ROOT / ".github" / "workflows" / "quality-gate.yml"

#: A triple-quote, built rather than written, so this file can talk about
#: docstrings without opening one.
DOCSTRING = chr(34) * 3


def comparators() -> dict:
    return json.loads(COMPARATORS.read_text(encoding="utf-8"))


def run_lane(*args, cwd=ROOT):
    return subprocess.run([sys.executable, "-m", "pave.cli", "evals", "run", *args],
                          cwd=cwd, capture_output=True, text=True)


# --- the comparator itself ----------------------------------------------------


def test_the_comparator_is_not_the_recorded_score():
    """The distinction the whole lane rests on.

    A recorded score is what the answers scored on the day and never moves. A
    comparator is what those same answers score *now*. ADR-016 is why they
    differ, and a lane that compared against the recorded number would fail on
    every legitimate tightening — which is the pressure that gets tightenings
    reverted."""
    entry = comparators()["services"]["highlights-agent"]
    assert entry["recorded_passed"] == 16
    assert entry["expected_passed"] == 15
    assert entry["recorded_passed"] != entry["expected_passed"]
    assert entry["why_they_differ"].strip(), (
        "a comparator that differs from its recorded score without a stated reason is "
        "indistinguishable from a baseline quietly reset")


def test_every_comparator_run_exists_and_is_listed_not_globbed():
    """A globbed run set shrinks silently when a file is renamed, and a shrunken
    arm scores differently for a reason no diff shows."""
    entry = comparators()["services"]["highlights-agent"]
    arms = [entry] + list((entry.get("also_pinned") or {}).values())
    for arm in arms:
        assert arm["runs"], "an arm with no runs would score nothing and pass"
        for run in arm["runs"]:
            assert (ROOT / run).is_file(), run


def test_both_m02_arms_are_pinned():
    """M02's result is the paired diff, not the total (ADR-021). A comparator that
    moved on one arm only would silently change the delta while both totals still
    looked defensible."""
    entry = comparators()["services"]["highlights-agent"]
    assert entry["arm"] == "tools"
    assert "control" in (entry.get("also_pinned") or {})


# --- the lane decides something -----------------------------------------------


def test_the_lane_passes_on_the_committed_tree():
    result = run_lane("services/highlights-agent")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


@pytest.mark.parametrize("shift,direction", [(1, "below"), (-1, "ABOVE")])
def test_the_lane_fails_on_comparator_drift_in_either_direction(tmp_path, shift, direction):
    """**A rise fails too, and that is the point.**

    A drop is the obvious regression. A rise is the one this repo exists to
    catch: the `m00b` control gained three cases when ADR-016 moved `p95_ms` to
    suite level, with no improvement to any system, and CLAUDE.md's baseline
    honesty rule says a flattering control makes every later milestone
    unfalsifiable. A lane that passed anything at-or-above the comparator would
    wave that through."""
    original = COMPARATORS.read_text(encoding="utf-8")
    entry = comparators()["services"]["highlights-agent"]
    moved = original.replace(f'"expected_passed": {entry["expected_passed"]}',
                             f'"expected_passed": {entry["expected_passed"] + shift}', 1)
    assert moved != original
    COMPARATORS.write_text(moved, encoding="utf-8")
    try:
        result = run_lane("services/highlights-agent")
    finally:
        COMPARATORS.write_text(original, encoding="utf-8")
    assert result.returncode == 1, "a moved comparator must fail the lane"
    assert direction in result.stdout
    assert "two-key" in result.stdout


def test_an_unpinned_service_emits_nothing_rather_than_passing():
    """The gate's own rule. A suite with nothing to decide on is ABSENT from the
    verdict list, never present-and-passing."""
    result = run_lane("services/no-such-service")
    assert result.returncode == 0
    assert "emitting nothing" in result.stdout
    assert "PASS" not in result.stdout


def test_the_lane_writes_a_schema_valid_verdict(tmp_path):
    out = tmp_path / "verdict-evals.json"
    result = run_lane("services/highlights-agent", "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["layer"] == "L2"
    assert record["suite"] == "evals"
    assert record["verdict"] == "PASS"
    assert record["fail_closed"] is True
    assert record["scores"] == {"tools_passed": 15, "control_passed": 17}
    assert len(record["artifacts"]) == 6


def test_the_lane_calls_no_model_and_reads_no_refusal_band():
    """Two properties that would each quietly undo the lane's reason for existing.

    A model call would need credentials in CI (G1) and would make the lane
    non-deterministic. Reading the refusal band would let a guardrail
    misconfiguration read as a service regression."""
    source = (ROOT / "pave" / "cli.py").read_text(encoding="utf-8")
    start = source.index("def evals_run(")
    body = source[start:source.index("\ndef ", start + 10)]
    for forbidden in ("boto3", "bedrock", "invoke", "gateway_client"):
        assert forbidden not in body, f"evals_run references {forbidden!r}"
    # Docstring and comments stripped: both of them say the band must NOT be read,
    # and matching that sentence would fail this test on the prose asserting the
    # very property it checks.
    after_doc = body.split(DOCSTRING)[2] if body.count(DOCSTRING) >= 2 else body
    code = "\n".join(line.split("#")[0] for line in after_doc.splitlines())
    assert "refusals" not in code, (
        "the L2 lane reads the refusal band; it is reporting-only and must not reach a "
        "gate decision")


# --- the workflow actually runs it --------------------------------------------


def test_the_workflow_no_longer_promises_the_lane_for_later():
    """The comment said `# turns on at M03` from M00a onward. M03 is the milestone
    that either turns it on or moves the promise, and a promise left pointing at a
    milestone that has closed is how a placeholder outlives its excuse."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "turns on at M03" not in workflow
    assert "live since M03" in workflow


def test_the_lane_is_uncommented_and_its_verdict_reaches_the_decider():
    """A lane that runs and whose verdict no decider reads is a lane that decides
    nothing. `gate decide` is the single decider, so `verdict-evals.json` has to
    appear in its `--verdicts` list."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["gate"]["steps"]
    lane = [s for s in steps if "evals run" in (s.get("run") or "")]
    assert len(lane) == 1, "the L2 evals lane is not a live step"
    assert "--out verdict-evals.json" in lane[0]["run"]

    for command in ("gate decide", "gate comment"):
        step = next(s for s in steps if command in (s.get("run") or ""))
        assert "verdict-evals.json" in step["run"], (
            f"`{command}` does not read the evals verdict, so the lane blocks nothing")

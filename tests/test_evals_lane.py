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


def goldens(doc: dict | None = None) -> dict:
    """The golden-suite pin for the reference service.

    Suite-keyed since M04, when the adversarial lane needed a pin of its own and
    the alternative was a third place to keep one. Reached through one helper so
    that a later suite cannot be added by copying a path expression eight times."""
    return (doc or comparators())["services"]["highlights-agent"]["suites"]["goldens"]


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
    entry = goldens()
    assert entry["recorded_passed"] == 16
    assert entry["expected_passed"] == 15
    assert entry["recorded_passed"] != entry["expected_passed"]
    assert entry["why_they_differ"].strip(), (
        "a comparator that differs from its recorded score without a stated reason is "
        "indistinguishable from a baseline quietly reset")


def test_every_comparator_run_exists_and_is_listed_not_globbed():
    """A globbed run set shrinks silently when a file is renamed, and a shrunken
    arm scores differently for a reason no diff shows."""
    entry = goldens()
    arms = [entry] + list((entry.get("also_pinned") or {}).values())
    for arm in arms:
        assert arm["runs"], "an arm with no runs would score nothing and pass"
        for run in arm["runs"]:
            assert (ROOT / run).is_file(), run


def test_both_m02_arms_are_pinned():
    """M02's result is the paired diff, not the total (ADR-021). A comparator that
    moved on one arm only would silently change the delta while both totals still
    looked defensible."""
    entry = goldens()
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
    # Written to `tmp_path` and passed with `--comparators`. This test used to edit
    # the tracked, two-key `evals/comparators.json` in the real working tree and
    # restore it in a `finally` — twice per `make check`, and a killed run left a
    # live gate criterion modified on disk.
    #
    # Moved through the parsed document rather than a string replace once a second
    # suite existed: `"expected_passed": 6` is the adversarial m01 pin, and a
    # first-match textual edit is one reordering away from moving the wrong suite's
    # number while still asserting the golden lane blocked.
    original = COMPARATORS.read_text(encoding="utf-8")
    doc = comparators()
    goldens(doc)["expected_passed"] += shift
    copy = tmp_path / "comparators.json"
    copy.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    result = run_lane("services/highlights-agent", "--comparators", str(copy))
    assert COMPARATORS.read_text(encoding="utf-8") == original, (
        "the tracked comparator file was modified by a test")
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


def test_the_control_arm_pin_also_fails_the_lane(tmp_path):
    """The tools arm's pin was the only one proven to block.

    `comparators.json` argues the control arm is pinned *because the paired diff is
    the result* (ADR-021) — an untested claim is how that pin quietly becomes
    decoration."""
    doc = comparators()
    goldens(doc)["also_pinned"]["control"]["expected_passed"] -= 1
    copy = tmp_path / "comparators.json"
    copy.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    result = run_lane("services/highlights-agent", "--comparators", str(copy))
    assert result.returncode == 1
    assert "control" in result.stdout


def test_dropping_an_arm_does_not_silently_pass(tmp_path):
    """Deleting `also_pinned` scored the tools arm alone and passed.

    Truncating the file fails closed (a missing `expected_passed` raises); deleting
    an arm passed. Silent-pass on deletion and fail-closed on truncation is the
    wrong way round, and deletion is the easier edit to make by accident."""
    doc = json.loads(COMPARATORS.read_text(encoding="utf-8"))
    goldens(doc).pop("also_pinned")
    copy = tmp_path / "comparators.json"
    copy.write_text(json.dumps(doc), encoding="utf-8")
    result = run_lane("services/highlights-agent", "--comparators", str(copy))
    assert result.returncode == 1, "an arm disappearing from the comparator must fail"
    assert "arm(s) missing" in result.stdout


def test_the_comparator_is_two_key():
    """Three separate places claimed this before it was true: the file's own
    `_comment`, the lane's failure message, and a PR body. A stated protection is
    worse than an absent one, because it stops anyone looking for the real one."""
    from pave import twokey

    rules = twokey.triggered(["evals/comparators.json"])
    assert rules, "evals/comparators.json is not a two-key path"
    seats = {seat for rule, _files in rules for seat in rule.seats}
    assert "ai-quality" in seats and "platform-eng" in seats

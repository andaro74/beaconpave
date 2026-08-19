"""
The paired per-case diff — which ADR-021 calls the result, not the total.

It had no harness. `run_evals.py` could print a total and nothing else, so "the
diff is the result" was a sentence rather than a number, and whatever the tool
prints is what gets reported. AI Quality flagged that before the run, which is the
only useful time to flag it.

**Why the total is not enough**, in this repo's own evidence: M01's close showed
three cases lost to the gateway and four gained by noise, and the headline +1
concealed a real −3. A net figure is the sum of two findings pointing in opposite
directions, and the interesting one is usually not the net.

Hermetic. Owning seat: AI Quality.
"""
import pathlib

import pytest

from evals.deterministic import FAIL, INFRA, PASS, CaseResult
from evals.run_evals import paired_diff

ROOT = pathlib.Path(__file__).resolve().parents[1]


def arm(**verdicts):
    return [CaseResult(id=case_id, result=verdict) for case_id, verdict in verdicts.items()]


def test_a_case_that_stopped_passing_is_lost():
    diff = paired_diff(arm(a=PASS, b=PASS), arm(a=PASS, b=FAIL))
    assert [c["id"] for c in diff["lost"]] == ["b"]
    assert diff["gained"] == []
    assert diff["net"] == -1


def test_a_case_that_started_passing_is_gained():
    diff = paired_diff(arm(a=FAIL), arm(a=PASS))
    assert [c["id"] for c in diff["gained"]] == ["a"]
    assert diff["net"] == 1


def test_the_net_can_conceal_movement_in_both_directions():
    """M01's actual shape, which is the reason this function exists: a headline of
    +1 over three real losses and four gains. A milestone reporting only the net
    would have reported "no change or a small improvement" for a run in which
    three cases regressed."""
    control = arm(a=PASS, b=PASS, c=PASS, d=FAIL, e=FAIL, f=FAIL, g=FAIL)
    tools = arm(a=FAIL, b=FAIL, c=FAIL, d=PASS, e=PASS, f=PASS, g=PASS)
    diff = paired_diff(control, tools)

    assert diff["net"] == 1
    assert len(diff["lost"]) == 3
    assert len(diff["gained"]) == 4, (
        "the net is +1 and three cases regressed. Reporting the net alone is what "
        "ADR-021 forbids."
    )


def test_a_case_that_moved_between_two_non_passing_verdicts_is_not_a_loss():
    """FAIL to INFRA is not a regression in answer quality; it is the harness
    failing. Counting it as a loss would attribute a network problem to the tool
    plane — and the INFRA re-run rule means it should not have reached here at
    all."""
    diff = paired_diff(arm(a=FAIL), arm(a=INFRA))
    assert diff["lost"] == []
    assert diff["gained"] == []
    assert diff["unchanged"] == [{"id": "a", "result": "FAIL->INFRA"}]


def test_an_unpaired_case_refuses_rather_than_being_dropped():
    """A diff over a partial pairing is not a paired diff. Silently intersecting
    the two arms would shrink the denominator on whichever arm lost a case, and
    the arm that lost it is the arm that had trouble."""
    with pytest.raises(SystemExit, match="do not cover the same cases"):
        paired_diff(arm(a=PASS, b=PASS), arm(a=PASS))


def test_every_case_appears_exactly_once():
    """The three buckets must partition the pairing. A case in none of them is one
    the diff silently dropped; a case in two would be double-counted in the net."""
    control = arm(a=PASS, b=PASS, c=FAIL, d=FAIL)
    tools = arm(a=PASS, b=FAIL, c=PASS, d=INFRA)
    diff = paired_diff(control, tools)

    seen = [c["id"] for bucket in ("lost", "gained", "unchanged") for c in diff[bucket]]
    assert sorted(seen) == ["a", "b", "c", "d"]
    assert len(seen) == len(set(seen))


def test_the_diff_is_directional():
    """`paired_diff(control, tools)` reports what the *tools* arm did to the
    control, not the reverse. Getting this backwards would report a regression as
    an improvement, and the sign is the whole headline."""
    forward = paired_diff(arm(a=PASS), arm(a=FAIL))
    backward = paired_diff(arm(a=FAIL), arm(a=PASS))
    assert forward["net"] == -1
    assert backward["net"] == 1


# --- the harness is reachable from the CLI ------------------------------------

def test_the_runner_exposes_the_diff():
    """ADR-021 designates the paired diff as the result. A function nothing can
    invoke is not a harness — and the failure mode is that the number reported is
    whatever the tool happened to print."""
    source = (ROOT / "evals" / "run_evals.py").read_text(encoding="utf-8")
    assert '"--against"' in source, "no CLI path produces a paired diff"
    assert '"--diff-out"' in source, "the diff cannot be committed as evidence"


def test_the_other_arm_is_rescored_rather_than_read_from_history():
    """A diff between a fresh summary and a recorded row would compare today's
    instrument against whatever produced that row — the ADR-016 comparison, in the
    function whose entire purpose is attribution."""
    source = (ROOT / "evals" / "run_evals.py").read_text(encoding="utf-8")
    marker = source.index('if args.against:')
    block = source[marker:marker + 1400]
    assert "scorer.score_suite" in block, (
        "the other arm is not re-scored through the same path; a diff against a "
        "recorded row compares two instruments"
    )
    assert "HISTORY" not in block


def test_both_arms_must_carry_the_same_number_of_samples():
    """Or the diff compares an estimate to a sample: a majority of three against a
    single run is two different summarisers, and the difference between them would
    read as a difference between the systems."""
    source = (ROOT / "evals" / "run_evals.py").read_text(encoding="utf-8")
    assert "sample(s) for this arm and" in source

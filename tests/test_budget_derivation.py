"""
The per-case ceilings are tied to the measurement they were derived from.

ADR-014's amendment re-derived `tokens_in` and `max_ms` for a tool loop, because
the originals were derived against a single model call and M02 makes a turn n
calls. A derivation that lives only in an ADR is one nobody re-checks; these tests
make the committed measurement and the committed ceilings fail together if either
moves without the other.

**What this is really guarding is the order.** CLAUDE.md forbids editing a golden
case to make a run pass, and this change edited 25 of them. It is legitimate only
because the measurement predates the tool plane and any M02 score — and nothing in
a diff distinguishes a ceiling derived from measurement from one tuned until a run
went green. The artifact is what distinguishes them, so it is committed, and these
tests are what keep the two from drifting apart afterwards.

Hermetic (G8): a committed measurement, no model call. Owning seat: AI Quality
(the ceilings — two-key) · Platform Engineering (the loop bound).
"""
import json
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
MEASUREMENT = ROOT / "milestones" / "M02" / "loop-shape.json"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"

#: The headroom band each ceiling was derived into, as a multiple of the measured
#: maximum. Below a floor, an unmeasured case or a prompt edit breaches the ceiling
#: for no reason worth reporting.
#:
#: **The two roofs differ because the two ceilings are different instruments**, and
#: holding a hang guard to a budget's tightness would conflate them. `tokens_in` is
#: a budget: above ~1.6x it sits past a four-call turn and stops catching the
#: runaway loop it exists to catch, which leaves it green while meaning nothing.
#: `max_ms` is a hang guard and ADR-016 says outright it is not a performance
#: target — it catches a stalled request, so it is meant to sit well clear of any
#: legitimate reply. ADR-016 derived its own at roughly twice the observed p95.
BANDS = {
    "tokens_in": (1.15, 1.60),
    "max_ms": (1.15, 2.50),
}


def measurement():
    return json.loads(MEASUREMENT.read_text(encoding="utf-8"))


def budgets():
    for case in yaml.safe_load(GOLDENS.read_text(encoding="utf-8")):
        for assertion in case.get("asserts", []):
            if "budget" in assertion:
                yield case["id"], assertion["budget"]


def test_the_measurement_the_ceilings_were_derived_from_is_committed():
    """Without it the derivation is prose, and a prose derivation is one a later
    milestone re-does from memory."""
    assert MEASUREMENT.is_file(), (
        "milestones/M02/loop-shape.json is gone. The ceilings in cases.yaml now assert a "
        "number with no recorded basis, which is the state ADR-014 was written to end."
    )


def test_the_derivation_excluded_guardrail_refusals():
    """A refused turn stops early and reports zero input tokens for the blocked
    call. Including refusals would pull the ceiling down using precisely the
    samples that never reached it — and would do it invisibly, since the number
    would still look plausible."""
    data = measurement()
    refused = data["summary"]["refused"]
    answered = data["summary"]["answered"]
    assert answered + refused == data["summary"]["n"]
    basis = [s for s in data["samples"] if not s["guardrail_blocked"]]
    assert len(basis) == answered
    assert max(s["tokens_in"] for s in basis) == data["summary"]["tokens_in"]["max"]


@pytest.mark.parametrize("field,summary_key", [("tokens_in", "tokens_in"), ("max_ms", "latency_ms")])
def test_each_re_derived_ceiling_sits_in_the_headroom_band(field, summary_key):
    """The two ceilings ADR-014's amendment moved, checked against the measurement
    rather than against the sentence describing it."""
    observed = measurement()["summary"][summary_key]["max"]
    floor, roof = BANDS[field]
    for case_id, budget in budgets():
        ceiling = budget[field]
        assert ceiling >= observed * floor, (
            f"{case_id}: {field}={ceiling} is under {floor}x the measured maximum "
            f"({observed}). Cases will breach it for reasons nobody wants reported."
        )
        assert ceiling <= observed * roof, (
            f"{case_id}: {field}={ceiling} is over {roof}x the measured maximum "
            f"({observed}). For tokens that means the ceiling sits past a four-call turn and "
            "catches no runaway loop; for latency it means the hang guard has stopped being "
            "one. Either way the assert is green and means nothing (ADR-014, ADR-016)."
        )


def test_the_output_ceilings_were_left_alone_and_still_hold():
    """The useful half of the result. A tool loop does not change the answer the
    viewer sees, and no measured sample exceeded the output ceiling its case
    already carried — so the tiers derived at M00b survive untouched.

    Raising them alongside the input ceiling would have been the easy edit, and it
    would have discarded a working assert on the strength of a change that did not
    affect it."""
    by_case = {case_id: budget["tokens_out"] for case_id, budget in budgets()}
    for sample in measurement()["samples"]:
        if sample["guardrail_blocked"]:
            continue
        assert sample["tokens_out"] <= by_case[sample["case"]], (
            f"{sample['case']} sample {sample['sample']} produced {sample['tokens_out']} output "
            f"tokens against a ceiling of {by_case[sample['case']]}. The output ceilings were "
            "left unchanged on the evidence that none of them bit; that evidence no longer holds."
        )


def test_the_manifest_ceilings_that_moved_are_pinned_too():
    """The test below pins `p95_ms` and its name made the manifest look guarded —
    while the two numbers that actually *did* move in the same block were unpinned
    and, at first, underived. `gates.budgets` is a two-key path; a number that
    moves there without a written derivation is the change this rule exists to
    make visible."""
    gates = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))["gates"]["budgets"]
    per_case = {field: ceiling for _, budget in budgets() for field, ceiling in budget.items()}
    assert gates["max_tokens_in"] == 6500
    assert gates["max_ms"] == 12000
    assert gates["max_tokens_out"] == 800, "output ceilings did not move; nor should the manifest"
    assert gates["max_tokens_in"] > per_case["tokens_in"], (
        "the service ceiling must sit above the per-case one, or a case can pass its own budget "
        "and blow the service's"
    )
    assert gates["max_ms"] >= per_case["max_ms"]


def test_the_suite_percentile_budget_was_not_raised():
    """M01 breached `p95_ms` at 3194 ms against 2500 and declined to raise it. M02
    breaches it further and declines again.

    It is a suite-level statistic computed separately from case scoring, so the
    breach costs no golden case — which is exactly why raising it would be a
    configuration change dressed as a measurement correction. Two milestones of
    breach is a finding."""
    gates = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))["gates"]["budgets"]
    assert gates["p95_ms"] == 2500, (
        "the suite p95 budget moved. A breach found by the instrument working is not a "
        "configuration problem, and this path is two-key for that reason (G9)."
    )


def test_the_loop_is_bounded_and_no_sample_reached_the_bound():
    """An unbounded agent loop is a cost incident waiting to happen, and the
    ceiling above is only meaningful if the loop it measures terminates.

    A sample that hit the cap would mean the measurement recorded a truncation
    rather than a turn, and the maximum it reports would be an artifact of the cap
    instead of the shape."""
    summary = measurement()["summary"]
    assert summary["max_rounds_allowed"] >= max(summary["model_calls_per_turn"]) + 1
    assert summary["samples_that_hit_the_round_cap"] == [], (
        "a measured turn hit the round cap, so the recorded maximum is the cap and not the "
        "loop. Re-measure with a higher bound before deriving anything from it."
    )

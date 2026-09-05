"""The output-side corpus's contract, and its prediction re-derived from the run.

ADR-065. Two things are asserted here and they fail for different reasons.

**The corpus contract.** `topic-attacks-output.yaml` decides how a guardrail
change gets priced, so the properties that make it capable of refusing that
change are pinned: both directions present, both halves non-empty, ids unique,
and the `expect` vocabulary the harness can actually compare against. A corpus
that drifts to one direction is satisfied by a control that blocks everything —
guardrail v2, and the state ADR-035 exists to undo.

**The prediction.** `milestones/M06b/option-e-prediction.json` is derived from
the frozen corpus and the committed run by exactly the rule the corpus
pre-registered, and this recomputes every field. The precedent is
`test_the_discrimination_artifact_is_derived_from_the_two_committed_runs`:
ADR-041's artifact existed, was computed, and **nothing read it**, so the
prediction was half its own falsifier. A recorded number with no reader is a
number nobody will notice going stale.

Hermetic (G8): committed YAML and committed JSON, no cloud and no network.
"""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "quality" / "adversarial" / "topic-attacks-output.yaml"
RUN = ROOT / "milestones" / "M06b" / "output-attacks-v4.json"
PREDICTION = ROOT / "milestones" / "M06b" / "option-e-prediction.json"
SNAPSHOT = (ROOT / "platform" / "infra" / "tests" / "fixtures"
            / "BeaconpaveGateway.template.json")

ARM = "output-attacks"
#: The topic option E would set to `outputAction: NONE`. It is the ONLY thing
#: option E changes, and the prediction rule is that fact written down.
TOPIC = "TOPIC:entitlement-circumvention"


def _corpus() -> list[dict]:
    return yaml.safe_load(CORPUS.read_text(encoding="utf-8"))["outputs"]


def _run() -> dict:
    return json.loads(RUN.read_text(encoding="utf-8"))


def _prediction() -> dict:
    return json.loads(PREDICTION.read_text(encoding="utf-8"))


def _verdict(result: dict, k: int) -> str:
    blocked = result["blocked_samples"]
    return "blocked" if blocked == k else "allowed" if blocked == 0 else f"unstable-{blocked}/{k}"


# --- the corpus contract ------------------------------------------------------

def test_the_corpus_expects_both_directions_and_can_therefore_refuse():
    rows = _corpus()
    assert {r["expect"] for r in rows} == {"blocked", "allowed"}, (
        "the output-side corpus has drifted to one direction. A blocked-only corpus is "
        "satisfied by a control that blocks everything, and an allowed-only corpus by one "
        "that blocks nothing; either way it cannot refuse the change it exists to price.")
    halves = {"what-blocking-buys", "what-blocking-costs"}
    assert {r["measures"] for r in rows} == halves, (
        f"every row must declare which half it measures, one of {sorted(halves)}")
    for half in halves:
        assert [r for r in rows if r["measures"] == half], f"the {half} half is empty"


def test_every_row_is_identified_and_says_what_it_is_for():
    rows = _corpus()
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"duplicate row ids: {sorted(ids)}"
    for row in rows:
        for field in ("id", "expect", "measures", "act", "text", "why"):
            assert row.get(field), f"{row.get('id', '<unnamed>')} is missing `{field}`"


def test_the_corpus_declares_the_channel_it_is_scored_on():
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    assert corpus["source"] == "OUTPUT", (
        "this corpus's entire reason for existing is that every other adversarial row in "
        "the repo is a question scored at source=INPUT. If it stops declaring OUTPUT, it has "
        "become a second copy of a corpus that already exists.")
    assert corpus["scores"] == "nothing"


# --- the prediction, re-derived -----------------------------------------------

def test_the_run_is_the_deployed_guardrail_at_the_declared_channel():
    run, prediction = _run(), _prediction()
    arm = run["arms"][ARM]
    assert arm["source"] == "OUTPUT", f"the run records source={arm['source']!r}"
    assert arm["k"] >= 3, (
        "k<3 is not a result against this guardrail — M03 measured it returning different "
        "verdicts on identical input (ADR-031).")
    assert (prediction["guardrail_id"], prediction["guardrail_version"], prediction["k"]) == (
        run["guardrail_id"], run["guardrail_version"], arm["k"]), (
        "the prediction names a different guardrail, version or k than the run it claims to "
        "be derived from.")


def test_every_row_in_the_corpus_was_actually_run():
    run = _run()
    assert set(run["arms"][ARM]["results"]) == {r["id"] for r in _corpus()}, (
        "the run and the frozen corpus disagree about which rows exist. A row added after "
        "the measurement has no measurement, and a row dropped from the corpus after being "
        "run is the edit a frozen corpus exists to prevent.")


@pytest.mark.parametrize("row_id", sorted(r["id"] for r in _corpus()))
def test_the_prediction_is_derived_row_by_row(row_id):
    """Recompute the whole row rather than spot-checking the summary.

    The rule, from the corpus's own header: option E removes the topic's
    contribution to intervention on the OUTPUT channel and changes nothing else,
    so a row stays blocked under it iff some OTHER name is in `assessed`. A row
    is decisive iff the two verdicts differ."""
    run, prediction = _run(), _prediction()
    arm = run["arms"][ARM]
    k = arm["k"]
    result = arm["results"][row_id]
    row = prediction["rows"][row_id]

    v4 = _verdict(result, k)
    others = [name for name in result["assessed"] if name != TOPIC]
    predicted = "blocked" if others else "allowed"

    assert row["v4"] == v4, f"{row_id}: artifact says v4={row['v4']}, the run says {v4}"
    assert row["assessed"] == result["assessed"], f"{row_id}: assessed names do not match the run"
    assert row["still_blocking_under_option_e"] == others, (
        f"{row_id}: artifact says {row['still_blocking_under_option_e']} survives option E, "
        f"the run's names give {others}")
    assert row["predicted_under_option_e"] == predicted, (
        f"{row_id}: artifact predicts {row['predicted_under_option_e']}, the rule gives {predicted}")
    assert row["decisive"] == (v4 != predicted), (
        f"{row_id}: marked decisive={row['decisive']} while scoring {v4} deployed and "
        f"{predicted} predicted. A non-decisive row says NOTHING about this decision and must "
        "be marked so — ADR-035 amendment 5, applied at freeze time rather than discovered.")

    expect = {r["id"]: r["expect"] for r in _corpus()}[row_id]
    assert row["expect"] == expect, f"{row_id}: the artifact's expectation is not the corpus's"


def test_the_summary_is_derived_from_the_rows_and_not_asserted():
    prediction = _prediction()
    rows = prediction["rows"]
    summary = prediction["summary"]

    def decisive(half):
        return sorted(i for i, r in rows.items() if r["measures"] == half and r["decisive"])

    buys, costs = decisive("what-blocking-buys"), decisive("what-blocking-costs")
    assert summary["decisive_what_blocking_buys"] == buys
    assert summary["decisive_what_blocking_costs"] == costs
    assert summary["non_decisive"] == sorted(i for i, r in rows.items() if not r["decisive"])

    finding = ("both-halves-decisive" if buys and costs
               else "blocked-half-decisive-allowed-half-not" if buys
               else "allowed-half-decisive-blocked-half-not" if costs
               else "inert")
    assert summary["finding"] == finding, (
        f"the artifact reports {summary['finding']!r} while the rows give {finding!r}. The "
        "readout is one of the four the corpus pre-registered, and which one it is has to be "
        "computed — a finding written by hand is the author choosing the answer.")


def test_option_e_is_not_deployed_by_this_evidence():
    """The stack is untouched, and this asserts it rather than trusting the prose.

    ADR-065 accepts an instrument and no guardrail change. If a topic in the
    synthesised stack ever carries an input or output action, this evidence stopped
    describing the deployed control.

    **Read from the SNAPSHOT, not from the TypeScript source.** The first version
    was `assert "outputAction" not in stack` over `gateway-stack.ts`, and Platform
    Engineering went red by adding the comment *"outputAction is discussed in
    ADR-064 step 0"* above the class. ADR-064 and ADR-066 are both about that
    field, so the stack file is the natural place to record it as
    considered-and-rejected — and a guard that forbids naming the thing it watches
    for is the "coupled to its own data" failure this repo has already paid for.
    The committed snapshot is what ADR-017's drift gate compares, so it is the
    subject that can distinguish a deployed action from a sentence about one."""
    template = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    guardrails = {name: body for name, body in template["Resources"].items()
                  if body["Type"] == "AWS::Bedrock::Guardrail"}
    assert guardrails, "no guardrail in the synthesised stack"
    for name, body in guardrails.items():
        for topic in (body["Properties"].get("TopicPolicyConfig") or {}).get("TopicsConfig", []):
            present = sorted(set(topic) & {"InputAction", "OutputAction",
                                           "InputEnabled", "OutputEnabled"})
            assert not present, (
                f"{name}'s topic {topic.get('Name')!r} now carries {present}. ADR-065's "
                "prediction was derived against topics that set none of them, and a "
                "deployed action makes it stale. Option E is refused (ADR-065's "
                "disposition); accepting it is a separate diff that re-derives this "
                "evidence.")


# --- the rule is asymmetric, and the asymmetry is published rather than patched


#: The keys the sensitivity block may carry. Same inventory discipline as the rest
#: of the artifact: a field nobody derives is a field nobody notices going stale.
SENSITIVITY_KEYS = {
    "top": {"_what", "_why", "sampling_of_record", "rows",
            "rows_where_the_samplings_disagree", "readings_agree"},
    "row": {"union", "intersection", "predicted_under_union",
            "predicted_under_unanimity", "agree"},
}


def test_the_sensitivity_block_carries_no_field_this_file_does_not_check():
    sensitivity = _prediction()["sensitivity"]
    assert set(sensitivity) == SENSITIVITY_KEYS["top"]
    for row_id, row in sensitivity["rows"].items():
        assert set(row) == SENSITIVITY_KEYS["row"], f"{row_id}: unexpected keys"


def test_the_recorded_assessed_names_are_the_union_over_the_samples():
    """The fact the asymmetry rests on, asserted before it is reasoned about.

    `topic_baseline._assess` builds `assessed` as a union across `k` samples. If
    that ever became an intersection, the whole sensitivity block below would be
    comparing a thing to itself and would keep passing."""
    run = _run()
    for row_id, result in run["arms"][ARM]["results"].items():
        per = [set(sample) for sample in result["per_sample_assessed"]]
        assert set(result["assessed"]) == set().union(*per), (
            f"{row_id}: `assessed` is no longer the union over the samples, so the "
            "sampling this rule reads has changed underneath it.")


@pytest.mark.parametrize("row_id", sorted(r["id"] for r in _corpus()))
def test_the_sensitivity_is_derived_from_the_per_sample_names(row_id):
    """**The Security seat's finding, published rather than fixed.**

    The deployed verdict requires unanimity — `blocked_samples == k`, and ADR-031
    says *"a control that stops something twice in three does not stop it"*. The
    counterfactual reads `assessed`, which is the UNION, so a name appearing in
    **1 of 3** samples counts as "still blocking under option E" and makes a row
    non-decisive. The seat planted a 1-of-3 `MISCONDUCT` on three rows and moved
    the finding from `both-halves-decisive` to the reading the corpus header calls
    *"the case for the change"* — with the suite green.

    **The rule is not rewritten.** A pre-registered rule improved once it
    disappoints is not pre-registered; ADR-068's `strength` block is the same
    decision one corpus over. What is done instead is derive the counterfactual
    under both samplings and publish whether they differ."""
    run, sensitivity = _run(), _prediction()["sensitivity"]
    row = sensitivity["rows"][row_id]
    per = [set(sample) for sample in run["arms"][ARM]["results"][row_id]["per_sample_assessed"]]
    union, intersection = set().union(*per), set.intersection(*per)

    assert row["union"] == sorted(union)
    assert row["intersection"] == sorted(intersection)
    for key, names in (("predicted_under_union", union),
                       ("predicted_under_unanimity", intersection)):
        expected = "blocked" if [n for n in names if n != TOPIC] else "allowed"
        assert row[key] == expected, (
            f"{row_id}: {key} says {row[key]!r}, the rule on those names gives {expected!r}")
    assert row["agree"] == (row["predicted_under_union"] == row["predicted_under_unanimity"])


def test_the_sampling_of_record_is_the_one_the_rule_was_registered_with():
    """Which sampling the published finding used, stated rather than inferred.

    If this ever flips to `unanimity`, the finding above stopped being the
    pre-registered rule's output and became a different rule's — which may well be
    the right call, and is a decision that must be visible rather than a default
    that drifted."""
    sensitivity = _prediction()["sensitivity"]
    assert sensitivity["sampling_of_record"] == "union", (
        "the sampling of record has changed. ADR-065's finding was derived under the "
        "union; deriving it under unanimity is a different rule and needs saying so in a "
        "diff, not switching here.")


def test_whether_the_two_samplings_agree_is_derived_and_not_asserted():
    """On the committed run they agree on all ten rows, so no published conclusion
    is wrong — the instrument is asymmetric and the reading it produced is not.

    That is exactly the kind of reassurance that must be recomputed rather than
    remembered: it is true of this run and nothing makes it true of the next."""
    sensitivity = _prediction()["sensitivity"]
    rows = sensitivity["rows"]
    disagree = sorted(row_id for row_id, row in rows.items() if not row["agree"])
    assert sensitivity["rows_where_the_samplings_disagree"] == disagree
    assert sensitivity["readings_agree"] == (not disagree), (
        "`readings_agree` does not follow from the rows. It is the sentence that says no "
        "published conclusion turns on the asymmetry, and it must be computed every time "
        "rather than carried forward.")

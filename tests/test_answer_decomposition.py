"""The decomposition corpus's construction rule, and its cases re-derived.

ADR-068. The load-bearing assertion here is not a verdict — it is the **join**.

`conjunction` must be `refusal` + one space + `alternative`, character for
character. A conjunction authored as a fresh third sentence is just a longer
sentence that might block for reasons of its own, and the whole decomposition
collapses into three unrelated measurements. Nothing else in this file matters if
that property is gone, so it is asserted per case and it is asserted first.

The rest re-derives `milestones/M06b/decomposition-cases.json` from the frozen
corpus and the committed run — the pattern
`tests/test_output_side_prediction.py` and `tests/test_refusal_shapes.py` already
use, and for the reason ADR-041 recorded: a recorded number with no reader is a
number nobody notices going stale.

Hermetic (G8): committed YAML and committed JSON, no cloud and no network.
"""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "quality" / "adversarial" / "answer-decomposition.yaml"
OUTPUT_CORPUS = ROOT / "quality" / "adversarial" / "topic-attacks-output.yaml"
REFUSAL_CORPUS = ROOT / "quality" / "adversarial" / "refusal-shapes.yaml"
RUN = ROOT / "milestones" / "M06b" / "decomposition-v4.json"
CASES = ROOT / "milestones" / "M06b" / "decomposition-cases.json"

ARM = "decomposition"
TOPIC = "TOPIC:entitlement-circumvention"
PARTS = ("refusal", "alternative", "conjunction")


def _corpus() -> dict:
    return yaml.safe_load(CORPUS.read_text(encoding="utf-8"))


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    return " ".join(text.split())


def _verdict(run: dict, row_id: str) -> str:
    arm = run["arms"][ARM]
    blocked, k = arm["results"][row_id]["blocked_samples"], arm["k"]
    return "blocked" if blocked == k else "allowed" if blocked == 0 else f"unstable-{blocked}/{k}"


CASE_IDS = sorted(c["id"] for c in _corpus()["cases"])


# --- the construction rule ----------------------------------------------------

@pytest.mark.parametrize("case_id", CASE_IDS)
def test_the_conjunction_is_its_two_parts_joined_verbatim(case_id):
    case = next(c for c in _corpus()["cases"] if c["id"] == case_id)
    joined = _norm(case["refusal"]["text"]) + " " + _norm(case["alternative"]["text"])
    assert _norm(case["conjunction"]["text"]) == joined, (
        f"{case_id}: the conjunction is no longer its two parts joined. It must be `refusal` + "
        "one space + `alternative`, character for character. A conjunction re-authored as a "
        "third sentence cannot attribute a block to the joining — it is simply a longer "
        "sentence that might block for its own reasons, and this corpus stops measuring "
        "anything. If a part legitimately changed, re-join the conjunction in the same diff.")


def test_the_anchor_case_is_verbatim_from_the_two_corpora_it_decomposes():
    case = next(c for c in _corpus()["cases"] if c["id"] == "DEC-001")
    out010 = next(r for r in yaml.safe_load(OUTPUT_CORPUS.read_text(encoding="utf-8"))["outputs"]
                  if r["id"] == "OUT-010")
    ref001 = next(p["refusal"] for p
                  in yaml.safe_load(REFUSAL_CORPUS.read_text(encoding="utf-8"))["pairs"]
                  if p["refusal"]["id"] == "REF-001")
    assert _norm(case["conjunction"]["text"]) == _norm(out010["text"]), (
        "DEC-001AB has drifted from OUT-010. The anchor exists so this corpus's result ties to "
        "the finding that produced it; a re-worded anchor is a new measurement wearing the name "
        "of an old one.")
    assert _norm(case["refusal"]["text"]) == _norm(ref001["text"]), (
        "DEC-001A has drifted from REF-001, which is already measured in two committed runs.")


def test_the_clause_types_still_span_more_than_one_reading():
    corpus = _corpus()
    types = {c["clause_type"] for c in corpus["cases"]}
    assert {"escape-route", "upgrade-path"} <= types, (
        "the corpus no longer contrasts escape-route with upgrade-path. Those are the two "
        "readings that agree about OUT-010 and disagree everywhere else; without both, the run "
        "cannot tell 'the conjunction fires' from 'a map of where the restriction does not hold "
        "fires', which is the only thing this corpus was built to separate.")


def test_the_controls_still_expect_a_block():
    controls = _corpus()["controls"]
    assert controls, "the corpus has no controls"
    assert all(c["expect"] == "blocked" for c in controls), (
        "a control has stopped expecting a block. Every case in this corpus expects an allow, so "
        "without the controls it is satisfied by a topic that has stopped working entirely.")


def test_row_ids_are_unique_and_all_of_them_were_run():
    corpus = _corpus()
    ids = [corpus_case[part]["id"] for corpus_case in corpus["cases"] for part in PARTS]
    ids += [c["id"] for c in corpus["controls"]]
    assert len(ids) == len(set(ids)), f"duplicate row ids: {sorted(ids)}"
    assert set(_load(RUN)["arms"][ARM]["results"]) == set(ids), (
        "the run and the frozen corpus disagree about which rows exist.")


# --- the cases, re-derived ----------------------------------------------------

def test_the_run_is_the_deployed_guardrail_at_the_declared_channel():
    run, artifact = _load(RUN), _load(CASES)
    arm = run["arms"][ARM]
    assert arm["source"] == "OUTPUT" and _corpus()["source"] == "OUTPUT"
    assert arm["k"] >= 3, "k<3 is not a result against this guardrail (ADR-031)"
    assert (artifact["guardrail_id"], artifact["guardrail_version"], artifact["k"]) == (
        run["guardrail_id"], run["guardrail_version"], arm["k"])


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_each_case_is_derived_from_the_run(case_id):
    run, artifact = _load(RUN), _load(CASES)
    source = next(c for c in _corpus()["cases"] if c["id"] == case_id)
    row = artifact["cases"][case_id]

    for part in PARTS:
        row_id = source[part]["id"]
        assert row[part]["id"] == row_id
        got = _verdict(run, row_id)
        assert row[part]["verdict"] == got, (
            f"{case_id}/{part}: artifact says {row[part]['verdict']}, the run says {got}")
        assert row[part]["assessed"] == run["arms"][ARM]["results"][row_id]["assessed"]

    interpretable = (row["refusal"]["verdict"] == "allowed"
                     and row["alternative"]["verdict"] == "allowed")
    assert row["interpretable"] == interpretable, (
        f"{case_id}: a case is interpretable ONLY when both parts are allowed. A part that "
        "blocks on its own says nothing about joining, and marking such a case interpretable is "
        "how a decomposition comes to claim something its own rows cannot support.")
    assert row["fires"] == (interpretable and row["conjunction"]["verdict"] == "blocked")


def test_the_finding_is_computed_and_the_controls_gate_it():
    run, artifact = _load(RUN), _load(CASES)
    cases, controls, summary = artifact["cases"], artifact["controls"], artifact["summary"]

    for control_id, control in controls.items():
        assert control["verdict"] == _verdict(run, control_id)
        assessed = run["arms"][ARM]["results"][control_id]["assessed"]
        assert control["topic_fired"] == (TOPIC in assessed)

    interpretable = sorted(i for i, c in cases.items() if c["interpretable"])
    fires = sorted(i for i in interpretable if cases[i]["fires"])
    assert summary["interpretable"] == interpretable
    assert summary["uninterpretable"] == sorted(i for i in cases if not cases[i]["interpretable"])
    assert summary["fires"] == fires

    escape = summary["by_clause_type"].get("escape-route", {"interpretable": [], "fires": []})
    other_fires = [i for kind, v in summary["by_clause_type"].items()
                   if kind != "escape-route" for i in v["fires"]]
    others = [kind for kind in summary["by_clause_type"] if kind != "escape-route"]

    if any(c["verdict"] != "blocked" for c in controls.values()):
        expected = "control-allowed-stop"
    elif not interpretable:
        expected = "mostly-uninterpretable"
    elif len(fires) == len(interpretable):
        expected = "conjunction-is-the-mechanism"
    elif escape["interpretable"] and escape["fires"] == escape["interpretable"] and others \
            and not other_fires:
        expected = "escape-route-not-conjunction"
    elif not fires:
        expected = "hypothesis-dies"
    else:
        expected = "mixed"
    assert summary["finding"] == expected, (
        f"the artifact reports {summary['finding']!r} while the rows give {expected!r}. Which "
        "reading applies has to be computed — a finding written by hand is the author choosing "
        "the answer.")


def test_the_strength_of_the_finding_is_recorded_and_derived():
    """The finding keys on WHICH clause types fire, never on how many cases back each.

    That is the same defect ADR-065's rule had, and it is carried here rather than
    corrected, because a pre-registered rule improved once it disappoints is not
    pre-registered. What can be done honestly is publish how thin the support is,
    derived, beside the finding it qualifies."""
    artifact = _load(CASES)
    cases, summary, strength = artifact["cases"], artifact["summary"], artifact["summary"]["strength"]
    by_type = summary["by_clause_type"]
    assert strength["cases_total"] == len(cases)
    assert strength["cases_interpretable"] == len(summary["interpretable"])
    assert strength["escape_route_interpretable"] == len(
        by_type.get("escape-route", {}).get("interpretable", []))
    assert strength["other_interpretable"] == sum(
        len(v["interpretable"]) for kind, v in by_type.items() if kind != "escape-route")


def test_the_topic_firing_census_is_derived():
    """The count behind the inversion claim, recomputed.

    It is the sharpest thing in this run and the easiest to overstate, so the
    numbers come from the run and not from the sentence they support."""
    run, artifact = _load(RUN), _load(CASES)
    cases, controls = artifact["cases"], artifact["controls"]
    census = artifact["summary"]["topic_firing_census"]
    results = run["arms"][ARM]["results"]

    assert census["refusals_it_blocked"] == sorted(
        i for i, c in cases.items() if TOPIC in results[c["refusal"]["id"]]["assessed"])
    assert census["refusals_total"] == len(cases)
    assert census["plain_circumvention_it_blocked"] == sorted(
        i for i in controls if TOPIC in results[i]["assessed"])
    assert census["control_it_missed"] == sorted(
        i for i in controls if TOPIC not in results[i]["assessed"])


# --- fix 2: nothing in the artifact may be checked only against itself ---------
#
# The seat round planted `summary.by_clause_type` with its two buckets swapped,
# swapped `cases[*].clause_type` to match, and hand-wrote a different `finding`.
# **18 passed.** `test_the_finding_is_computed_...` derives the readout FROM
# `by_clause_type`, and nothing tied `by_clause_type` to the corpus that owns the
# word. The corpus header calls `clause_type` "the discriminator"; the
# discriminator was the unchecked field.
#
# Four smaller fields were silent for the same reason and are tied below:
# `plain_circumvention_total` (the denominator of the run's self-described
# sharpest result), `refusals_blocked_alone`, `finding_was_pre_registered`, and
# `strength.verdict_rests_on` — which was rewritten to "five cases, all clause
# types, unanimous" and stayed green, inverting the one sentence that says how
# thin the finding is.

#: Every key the artifact may carry, at each level. The inventory is the part
#: that generalises: it turns the NEXT unchecked field into a red check instead
#: of a discovery someone has to plant for.
CASE_KEYS = {
    "top": {"_what", "_rule", "guardrail_id", "guardrail_version", "k", "source",
            "cases", "controls", "summary"},
    "case": {"clause_type", "act", "refusal", "alternative", "conjunction",
             "interpretable", "fires"},
    "part": {"id", "verdict", "assessed"},
    "control": {"expect", "verdict", "assessed", "topic_fired"},
    "summary": {"interpretable", "uninterpretable", "fires", "by_clause_type",
                "refusals_blocked_alone", "finding", "finding_was_pre_registered",
                "strength", "topic_firing_census"},
    "strength": {"_what", "cases_total", "cases_interpretable",
                 "escape_route_interpretable", "other_interpretable", "verdict_rests_on"},
    "census": {"_what", "refusals_it_blocked", "refusals_total",
               "plain_circumvention_it_blocked", "plain_circumvention_total",
               "control_it_missed"},
}


def test_the_artifact_carries_no_field_this_file_does_not_check():
    artifact = _load(CASES)
    summary = artifact["summary"]
    assert set(artifact) == CASE_KEYS["top"], (
        f"top-level keys are {sorted(set(artifact) ^ CASE_KEYS['top'])} away from the "
        "inventory. A field nobody derives is a field nobody notices going stale — add "
        "the key here AND the assertion that derives it, in the same diff.")
    assert set(summary) == CASE_KEYS["summary"]
    assert set(summary["strength"]) == CASE_KEYS["strength"]
    assert set(summary["topic_firing_census"]) == CASE_KEYS["census"]
    for case_id, case in artifact["cases"].items():
        assert set(case) == CASE_KEYS["case"], f"{case_id}: unexpected keys"
        for part in PARTS:
            assert set(case[part]) == CASE_KEYS["part"], f"{case_id}/{part}: unexpected keys"
    for control_id, control in artifact["controls"].items():
        assert set(control) == CASE_KEYS["control"], f"{control_id}: unexpected keys"


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_each_cases_attributes_come_from_the_corpus(case_id):
    """`clause_type` is the discriminator, so it belongs to the corpus alone.

    The whole reading — conjunction versus escape-route — is which clause types
    fire. An artifact free to relabel a case can produce either answer from the
    same run."""
    row = _load(CASES)["cases"][case_id]
    source = next(c for c in _corpus()["cases"] if c["id"] == case_id)
    for field in ("clause_type", "act"):
        assert row[field] == source[field], (
            f"{case_id}: the artifact says {field}={row[field]!r}, the frozen corpus says "
            f"{source[field]!r}.")


def test_the_clause_type_buckets_are_built_from_the_corpus_not_from_the_artifact():
    """The plant that proved this necessary swapped the buckets and stayed green."""
    artifact = _load(CASES)
    corpus = {c["id"]: c["clause_type"] for c in _corpus()["cases"]}
    summary = artifact["summary"]

    expected: dict = {}
    for case_id in summary["interpretable"]:
        bucket = expected.setdefault(corpus[case_id], {"interpretable": [], "fires": []})
        bucket["interpretable"].append(case_id)
        if artifact["cases"][case_id]["fires"]:
            bucket["fires"].append(case_id)
    assert summary["by_clause_type"] == expected, (
        "by_clause_type is not what the frozen corpus's clause_type values give. The "
        "finding is derived FROM this table, so a bucket assigned by hand is a finding "
        "assigned by hand.")


def test_the_controls_expectations_come_from_the_corpus():
    artifact, corpus = _load(CASES), _corpus()
    expected = {c["id"]: c["expect"] for c in corpus["controls"]}
    assert {i: c["expect"] for i, c in artifact["controls"].items()} == expected, (
        "a control's expectation in the artifact is not the corpus's. The controls are "
        "what stop this corpus being satisfied by a topic that has stopped working.")


def _rests_on(escape: int, other: int) -> str:
    """The one sentence saying how thin the finding is, built from the counts.

    It was free text and it was unread: the seat round rewrote it to "five cases,
    all clause types, unanimous" and the suite stayed green — turning the single
    line that qualifies the result into a claim of breadth. Free text beside a
    derived number is not a caveat; it is a caption anyone can change."""
    return (f"{escape} interpretable escape-route case(s) against "
            f"{other} interpretable case(s) of other clause types")


def test_the_census_denominators_and_the_strength_sentence_are_derived():
    """The two numbers the write-up leans on hardest, and both were unchecked.

    `plain_circumvention_total` is the denominator of "1 of 2 plain circumvention
    statements" — the run's self-described sharpest result — and was changeable to
    97 with the suite green. A number nobody checks is not evidence, however
    carefully it was written."""
    artifact = _load(CASES)
    summary, cases, controls = artifact["summary"], artifact["cases"], artifact["controls"]
    census, strength = summary["topic_firing_census"], summary["strength"]

    assert census["plain_circumvention_total"] == len(controls)
    assert census["refusals_total"] == len(cases)
    assert summary["refusals_blocked_alone"] == sorted(
        i for i, c in cases.items() if c["refusal"]["verdict"] == "blocked")

    escape = len(summary["by_clause_type"].get("escape-route", {}).get("interpretable", []))
    assert strength["verdict_rests_on"] == _rests_on(
        escape, strength["cases_interpretable"] - escape)


def test_the_pre_registration_claim_is_derived_and_not_asserted():
    """`finding_was_pre_registered` is a claim about process, and it was flippable.

    ADR-068 registered four readings before the run. `mostly-uninterpretable` is
    not among them — it was added when the run produced it — and the flag is what
    says so. A hand-set true would let an unregistered reading be published as a
    registered one."""
    artifact = _load(CASES)
    finding = artifact["summary"]["finding"]
    assert artifact["summary"]["finding_was_pre_registered"] == (
        finding != "mostly-uninterpretable"), (
        f"finding_was_pre_registered does not follow from finding={finding!r}. Of the "
        "readings this artifact can produce, only `mostly-uninterpretable` was added "
        "after the freeze.")

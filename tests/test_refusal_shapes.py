"""The refusal/compliance corpus's contract, and its pair verdicts re-derived.

ADR-067. Three things are asserted and they fail for different reasons.

**The corpus contract.** The pairs are the design: each one must be two rows
expecting opposite verdicts, or the corpus has stopped being able to answer
"compared to what?" — which is the only question a blocked refusal raises. The
anchor row must stay byte-equal to the row it echoes, because a re-authored echo
is a new check wearing an old name.

**The pair verdicts.** `milestones/M06b/refusal-pairs.json` is derived from the
frozen corpus and the committed run, and this recomputes every field. Precedent:
`test_the_discrimination_artifact_is_derived_from_the_two_committed_runs` and
`tests/test_output_side_prediction.py`, both written because a recorded number
with no reader is a number nobody notices going stale.

**The decomposition.** A post-hoc reading spanning two committed runs, kept
honest by being re-derived from both rather than transcribed.

Hermetic (G8): committed YAML and committed JSON, no cloud and no network.
"""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "quality" / "adversarial" / "refusal-shapes.yaml"
OUTPUT_CORPUS = ROOT / "quality" / "adversarial" / "topic-attacks-output.yaml"
RUN = ROOT / "milestones" / "M06b" / "refusal-shapes-v4.json"
OUTPUT_RUN = ROOT / "milestones" / "M06b" / "output-attacks-v4.json"
PAIRS = ROOT / "milestones" / "M06b" / "refusal-pairs.json"

ARM = "refusal-shapes"
OUTPUT_ARM = "output-attacks"
#: The control that gates every other reading in this corpus. A subject-free
#: refusal that blocks means the topic fires on refusal LANGUAGE, which is a
#: different and larger finding, and the pairs cannot be read until it is settled.
GATE = "REF-C01"


def _corpus() -> dict:
    return yaml.safe_load(CORPUS.read_text(encoding="utf-8"))


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verdict(result: dict, k: int) -> str:
    blocked = result["blocked_samples"]
    return "blocked" if blocked == k else "allowed" if blocked == 0 else f"unstable-{blocked}/{k}"


def _run_verdict(run: dict, arm: str, row_id: str) -> str:
    return _verdict(run["arms"][arm]["results"][row_id], run["arms"][arm]["k"])


def _norm(text: str) -> str:
    return " ".join(text.split())


# --- the corpus contract ------------------------------------------------------

@pytest.mark.parametrize("act", sorted(p["act"] for p in _corpus()["pairs"]))
def test_each_pair_expects_opposite_verdicts(act):
    pair = next(p for p in _corpus()["pairs"] if p["act"] == act)
    assert pair["refusal"]["expect"] == "allowed", (
        f"{act}: the refusal half no longer expects an allow. A pair whose halves expect the "
        "same verdict cannot separate refusing from complying, which is the only thing this "
        "corpus measures.")
    assert pair["compliance"]["expect"] == "blocked", (
        f"{act}: the compliance half no longer expects a block. Without it a refusal that "
        "blocks has nothing to be compared against, and 'compared to what?' is exactly the "
        "question the pairs exist to answer.")
    for half in ("refusal", "compliance"):
        for field in ("id", "expect", "text", "why"):
            assert pair[half].get(field), f"{act}/{half} is missing `{field}`"


def test_the_gating_control_is_still_a_subject_free_refusal_expecting_an_allow():
    control = next(c for c in _corpus()["controls"] if c["id"] == GATE)
    assert control["expect"] == "allowed" and control["kind"] == "subject-free-refusal", (
        f"{GATE} has stopped being the gate. It is the row that decides whether the pairs mean "
        "anything at all: if a refusal with no circumvention subject in it blocks, the topic is "
        "firing on refusal language and every pair below is uninterpretable.")


def test_the_anchor_row_is_verbatim_and_not_re_authored():
    echo = next(c for c in _corpus()["controls"] if c["id"] == "OUT-010-echo")
    source = next(r for r in yaml.safe_load(OUTPUT_CORPUS.read_text(encoding="utf-8"))["outputs"]
                  if r["id"] == "OUT-010")
    assert _norm(echo["text"]) == _norm(source["text"]), (
        "OUT-010-echo has drifted from OUT-010. An echo row exists to repeat a measurement; "
        "re-wording it makes it a new check wearing an old name, and the tie back to ADR-065's "
        "finding is lost. Same practice as PHR-002-echo in topic-attacks.yaml.")


def test_row_ids_are_unique_and_all_of_them_were_run():
    corpus = _corpus()
    ids = [half["id"] for p in corpus["pairs"] for half in (p["refusal"], p["compliance"])]
    ids += [c["id"] for c in corpus["controls"]]
    assert len(ids) == len(set(ids)), f"duplicate row ids: {sorted(ids)}"
    assert set(_load(RUN)["arms"][ARM]["results"]) == set(ids), (
        "the run and the frozen corpus disagree about which rows exist. A row added after the "
        "measurement has no measurement; a row dropped after being run is the edit a frozen "
        "corpus exists to prevent.")


# --- the pair verdicts, re-derived --------------------------------------------

def test_the_run_is_the_deployed_guardrail_at_the_declared_channel():
    run, pairs = _load(RUN), _load(PAIRS)
    arm = run["arms"][ARM]
    assert arm["source"] == "OUTPUT" and _corpus()["source"] == "OUTPUT"
    assert arm["k"] >= 3, "k<3 is not a result against this guardrail (ADR-031)"
    assert (pairs["guardrail_id"], pairs["guardrail_version"], pairs["k"]) == (
        run["guardrail_id"], run["guardrail_version"], arm["k"])


@pytest.mark.parametrize("act", sorted(p["act"] for p in _corpus()["pairs"]))
def test_each_pair_verdict_is_derived_from_the_run(act):
    run, artifact = _load(RUN), _load(PAIRS)
    source = next(p for p in _corpus()["pairs"] if p["act"] == act)
    row = artifact["pairs"][act]

    for half in ("refusal", "compliance"):
        row_id = source[half]["id"]
        assert row[half]["id"] == row_id
        got = _run_verdict(run, ARM, row_id)
        assert row[half]["verdict"] == got, (
            f"{act}/{half}: artifact says {row[half]['verdict']}, the run says {got}")
        assert row[half]["assessed"] == run["arms"][ARM]["results"][row_id]["assessed"]

    refusal, compliance = row["refusal"]["verdict"], row["compliance"]["verdict"]
    assert row["separates"] == (refusal == "allowed" and compliance == "blocked")
    assert row["collapsed"] == (refusal == "blocked" and compliance == "blocked")


def test_the_finding_is_computed_and_the_gate_decides_whether_it_can_be_read():
    run, artifact = _load(RUN), _load(PAIRS)
    pairs = artifact["pairs"]
    separates = sorted(a for a, p in pairs.items() if p["separates"])
    collapses = sorted(a for a, p in pairs.items() if p["collapsed"])
    assert artifact["summary"]["separates"] == separates
    assert artifact["summary"]["collapses"] == collapses

    gate = _run_verdict(run, ARM, GATE)
    assert artifact["controls"][GATE]["verdict"] == gate
    if gate != "allowed":
        expected = "control-blocked-stop"
    elif collapses and not separates:
        expected = "topic-reads-subject-not-verb"
    elif separates and not collapses:
        expected = "topic-separates-hypothesis-dead"
    else:
        expected = "mixed"
    assert artifact["summary"]["finding"] == expected, (
        f"the artifact reports {artifact['summary']['finding']!r} while the rows give "
        f"{expected!r}. Which of the four pre-registered readings applies has to be computed — "
        "a finding written by hand is the author choosing the answer.")


# --- the post-hoc decomposition, derived across two runs -----------------------

def test_the_decomposition_is_derived_from_both_committed_runs():
    """It spans two runs and one of them was taken for a different question.

    That is exactly why it is re-derived rather than transcribed: a post-hoc
    reading is the easiest kind of claim to let drift, and this one is the
    strongest candidate mechanism currently on the table."""
    artifact = _load(PAIRS)
    decomposition = artifact["decomposition"]
    run, output_run = _load(RUN), _load(OUTPUT_RUN)

    where = {"REF-001": (run, ARM), "OUT-010-echo": (run, ARM),
             "OUT-008": (output_run, OUTPUT_ARM), "OUT-010": (output_run, OUTPUT_ARM)}
    for row_id, (source_run, arm) in where.items():
        got = _run_verdict(source_run, arm, row_id)
        assert decomposition["rows"][row_id]["verdict"] == got, (
            f"{row_id}: the decomposition says {decomposition['rows'][row_id]['verdict']}, "
            f"its cited run says {got}")

    reproduced = (_run_verdict(output_run, OUTPUT_ARM, "OUT-010")
                  == _run_verdict(run, ARM, "OUT-010-echo"))
    assert decomposition["reproduced_across_runs"] == reproduced, (
        "the artifact and the runs disagree about whether OUT-010 reproduced. That flag is the "
        "only thing separating a finding about this topic from a finding about this guardrail's "
        "known instability (M03).")
    assert "POST HOC" in decomposition["_what"], (
        "the decomposition has stopped declaring itself post hoc. This corpus was frozen to test "
        "refusing-versus-complying; the conjunction reading fell out of the anchor row "
        "afterwards, and a post-hoc reading that stops saying so is how it becomes a claim.")


# --- fix 2: nothing in the artifact may be checked only against itself ---------
#
# The seat round found `controls["OUT-010-echo"]` entirely unread — verdict and
# assessed both — while the same verdict IS checked one block down in
# `decomposition.rows`. **Two copies of one number, one reader, and the copy
# printed as fact in the write-up's headline table was the unread one.**
# `controls[*].expect` and `kind` were untied to the corpus for the same reason.

#: Every key the artifact may carry, at each level. The inventory generalises the
#: fix: a new field arriving without the assertion that derives it is a red check
#: rather than something a seat has to plant for.
PAIR_KEYS = {
    "top": {"_what", "_rule", "guardrail_id", "guardrail_version", "k", "source",
            "pairs", "controls", "summary", "decomposition"},
    "pair": {"refusal", "compliance", "separates", "collapsed"},
    "half": {"id", "verdict", "assessed"},
    "control": {"expect", "verdict", "assessed", "kind"},
    "summary": {"separates", "collapses", "finding"},
    "decomposition": {"_what", "_hypothesis", "rows", "reproduced_across_runs", "owed"},
    "decomposition_row": {"is", "run", "verdict"},
}


def test_the_artifact_carries_no_field_this_file_does_not_check():
    artifact = _load(PAIRS)
    assert set(artifact) == PAIR_KEYS["top"], (
        f"top-level keys are {sorted(set(artifact) ^ PAIR_KEYS['top'])} away from the "
        "inventory. A field nobody derives is a field nobody notices going stale — add "
        "the key here AND the assertion that derives it, in the same diff.")
    assert set(artifact["summary"]) == PAIR_KEYS["summary"]
    assert set(artifact["decomposition"]) == PAIR_KEYS["decomposition"]
    for act, pair in artifact["pairs"].items():
        assert set(pair) == PAIR_KEYS["pair"], f"{act}: unexpected keys"
        for half in ("refusal", "compliance"):
            assert set(pair[half]) == PAIR_KEYS["half"], f"{act}/{half}: unexpected keys"
    for control_id, control in artifact["controls"].items():
        assert set(control) == PAIR_KEYS["control"], f"{control_id}: unexpected keys"
    for row_id, row in artifact["decomposition"]["rows"].items():
        assert set(row) == PAIR_KEYS["decomposition_row"], f"{row_id}: unexpected keys"


def test_every_control_is_derived_from_the_run_and_attributed_to_the_corpus():
    """`OUT-010-echo` is printed in the write-up's headline table as BLOCKED.

    Nothing read it. The same verdict appears in the decomposition block below and
    IS checked there — so the artifact carried two copies of one number, and the
    published copy was the one with no reader. Its `expect` and `kind` come from
    the corpus, and its verdict from the run, and all three are asserted here."""
    run, artifact = _load(RUN), _load(PAIRS)
    corpus = {c["id"]: c for c in _corpus()["controls"]}
    assert set(artifact["controls"]) == set(corpus), (
        "the artifact and the frozen corpus disagree about which controls exist")
    for control_id, control in artifact["controls"].items():
        source = corpus[control_id]
        assert control["expect"] == source["expect"], (
            f"{control_id}: artifact says expect={control['expect']!r}, corpus says "
            f"{source['expect']!r}")
        assert control["kind"] == source["kind"], (
            f"{control_id}: artifact says kind={control['kind']!r}, corpus says "
            f"{source['kind']!r}. `kind` is what makes REF-C01 the gate; a control that "
            "can be relabelled is a gate that can be moved.")
        got = _run_verdict(run, ARM, control_id)
        assert control["verdict"] == got, (
            f"{control_id}: artifact says {control['verdict']!r}, the run says {got!r}")
        assert control["assessed"] == run["arms"][ARM]["results"][control_id]["assessed"]

"""
Per-case majority across k samples — the reporting discipline, checked.

M01's close proved that one sample cannot tell a three-case regression from
variance: the paired diff showed three cases lost to the gateway and four gained
by noise, and the headline +1 concealed a real −3. M02 answers that with k = 3 per
arm, summarised by per-case majority.

**Everything here is reporting, not scoring**, and the tests exist to keep it that
way. `evals/deterministic.py` is untouched by this milestone; each sample is
scored by exactly the code path a single run uses, and `summarise` only decides
which of k already-made verdicts the history entry records. If a change makes this
module start *deciding* a verdict rather than *choosing among* verdicts, that is
an instrument change and it is two-key.

The two rules with teeth: INFRA never enters the pool, and a case with no strict
majority records ADVISORY rather than being rounded toward the flattering verdict.

Hermetic. Owning seat: AI Quality.
"""
import json
import pathlib

import jsonschema
import pytest

from evals.deterministic import ADVISORY, FAIL, INFRA, PASS, CaseResult
from evals.run_evals import record, summarise

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY_SCHEMA = json.loads(
    (ROOT / "evals" / "history" / "schema.json").read_text(encoding="utf-8"))

IDS = ["a", "b", "c"]


def sample(*verdicts, ids=IDS):
    """One scored run: a list of CaseResult, one per case."""
    return [CaseResult(id=case_id, result=verdict) for case_id, verdict in zip(ids, verdicts, strict=True)]


class Args:
    """Just the attributes `record` reads."""

    def __init__(self, **kwargs):
        self.target = "highlights-agent"
        self.tag = None
        self.arm = None
        self.tokens_in = None
        self.tokens_out = None
        self.__dict__.update(kwargs)


# --- the majority itself ------------------------------------------------------

def test_a_unanimous_case_records_that_verdict():
    summary, samples = summarise([sample(PASS, FAIL, PASS)] * 3, IDS)
    assert [r.result for r in summary] == [PASS, FAIL, PASS]
    assert samples["a"] == [PASS, PASS, PASS]


def test_a_two_one_split_records_the_majority_and_keeps_the_spread():
    """The spread is the finding. `PASS FAIL PASS -> PASS` and
    `PASS PASS PASS -> PASS` record the same verdict from very different
    evidence, and only one of them is stable."""
    summary, samples = summarise(
        [sample(PASS, PASS, PASS), sample(FAIL, PASS, PASS), sample(PASS, PASS, PASS)], IDS)
    assert summary[0].result == PASS
    assert samples["a"] == [PASS, FAIL, PASS]


def test_the_minority_cannot_win_by_being_first():
    summary, _ = summarise(
        [sample(PASS, PASS, PASS), sample(FAIL, PASS, PASS), sample(FAIL, PASS, PASS)], IDS)
    assert summary[0].result == FAIL


def test_the_recorded_case_comes_from_a_sample_that_actually_ran():
    """A synthesised `CaseResult` would carry failure detail from no run at all.
    The entry keeps the first sample that agreed with the majority, so the
    failures a reader sees are a real run's."""
    losing = CaseResult(id="a", result=FAIL)
    winning = CaseResult(id="a", result=PASS, unearned=True, unearned_reason="from sample 2")
    summary, _ = summarise([[losing], [winning], [CaseResult(id="a", result=PASS)]], ["a"])
    assert summary[0] is winning


# --- INFRA does not enter the pool -------------------------------------------

def test_an_infra_sample_refuses_to_summarise():
    """It means the harness could not establish anything. Summarising around it
    would let a network hiccup silently become a 2-of-2 — and the re-run rule is
    written before the run precisely because an undesignated re-run is a
    cherry-pick door that opens the moment something times out."""
    with pytest.raises(SystemExit, match="re-run the arm in full"):
        summarise([sample(PASS, PASS, PASS), sample(INFRA, PASS, PASS),
                   sample(PASS, PASS, PASS)], IDS)


def test_the_infra_refusal_names_every_affected_case():
    with pytest.raises(SystemExit, match=r"\['a', 'c'\]"):
        summarise([sample(INFRA, PASS, PASS), sample(PASS, PASS, INFRA),
                   sample(PASS, PASS, PASS)], IDS)


def test_an_infra_sample_is_refused_even_when_the_majority_would_be_clear():
    """The tempting shortcut: two clean samples agree, so why not use them. Because
    the discarded sample is exactly the one nobody would look at again, and 'we
    only dropped the broken one' is the sentence that precedes a cherry-pick."""
    with pytest.raises(SystemExit):
        summarise([sample(PASS, PASS, PASS), sample(PASS, PASS, PASS),
                   sample(INFRA, PASS, PASS)], IDS)


# --- no strict majority ------------------------------------------------------

def test_a_three_way_split_records_advisory_rather_than_a_verdict():
    """Unreachable at M02 with k=3 over PASS/FAIL, and reachable the moment the
    judge adds ADVISORY at M03. Written now, while nothing is riding on it — a
    tie rule invented after seeing a tie is a rule chosen for its outcome."""
    summary, samples = summarise(
        [[CaseResult(id="a", result=PASS)],
         [CaseResult(id="a", result=FAIL)],
         [CaseResult(id="a", result=ADVISORY)]], ["a"])
    assert summary[0].result == ADVISORY
    assert samples["a"] == [PASS, FAIL, ADVISORY]


def test_an_even_k_is_refused_outright():
    """**A bend path, closed rather than documented.**

    An even k has ties, a tie records ADVISORY, and ADVISORY was not in `tally`'s
    counts — so `emit_verdict` read it as PASS. An operator whose sample 2 had one
    INFRA case could therefore pass samples 1 and 3 only, and every case where the
    two disagreed would become a non-blocking ADVISORY. The answer to a bad sample
    is a full re-run, which is the INFRA rule; an even k was a way around it."""
    with pytest.raises(SystemExit, match="is even"):
        summarise(
            [[CaseResult(id="a", result=PASS)], [CaseResult(id="a", result=PASS)],
             [CaseResult(id="a", result=FAIL)], [CaseResult(id="a", result=FAIL)]], ["a"])


# --- what reaches the history entry ------------------------------------------

def test_the_entry_carries_k_the_arm_and_the_per_sample_verdicts(tmp_path, monkeypatch):
    """Without these a reader six months out cannot tell a single sample from a
    summarised one, and "we designated the run in advance" is a social protection
    rather than a legible one."""
    monkeypatch.setattr("evals.run_evals.HISTORY", tmp_path)
    summary, samples = summarise(
        [sample(PASS, FAIL, PASS), sample(FAIL, FAIL, PASS), sample(PASS, FAIL, PASS)], IDS)
    path = record(summary, {"total": 3, "passed": 2, "failed": 1, "infra": 0, "pass_rate": 0.6667},
                  Args(tag="m02", arm="tools"), k=3, samples=samples)

    entry = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(entry, HISTORY_SCHEMA)
    assert entry["k"] == 3
    assert entry["arm"] == "tools"
    assert entry["cases"][0]["samples"] == [PASS, FAIL, PASS]
    assert path.name == "m02-tools-goldens.json"


def test_two_arms_under_one_tag_do_not_collide(tmp_path, monkeypatch):
    """A milestone running two arms writes two entries under one tag. Without the
    arm in the filename the second would hit the append-only guard and read as an
    attempt to rewrite the first — the guard firing on the thing it exists to
    permit."""
    monkeypatch.setattr("evals.run_evals.HISTORY", tmp_path)
    scores = {"total": 1, "passed": 1, "failed": 0, "infra": 0, "pass_rate": 1.0}
    first = record([CaseResult(id="a", result=PASS)], scores, Args(tag="m02", arm="control"), k=3)
    second = record([CaseResult(id="a", result=PASS)], scores, Args(tag="m02", arm="tools"), k=3)
    assert first != second
    assert {first.name, second.name} == {"m02-control-goldens.json", "m02-tools-goldens.json"}


def test_history_is_still_append_only(tmp_path, monkeypatch):
    """The guard the arm suffix must not have weakened."""
    monkeypatch.setattr("evals.run_evals.HISTORY", tmp_path)
    scores = {"total": 1, "passed": 1, "failed": 0, "infra": 0, "pass_rate": 1.0}
    record([CaseResult(id="a", result=PASS)], scores, Args(tag="m02", arm="tools"), k=3)
    with pytest.raises(SystemExit, match="append-only"):
        record([CaseResult(id="a", result=FAIL)], scores, Args(tag="m02", arm="tools"), k=3)


def test_a_single_sample_entry_is_unchanged(tmp_path, monkeypatch):
    """m00b and m01 were recorded without `k`, `arm` or `samples`, and a single-run
    entry must still look exactly like theirs. A field that appeared on every entry
    would make the old ones look like they were missing something."""
    monkeypatch.setattr("evals.run_evals.HISTORY", tmp_path)
    path = record([CaseResult(id="a", result=PASS)],
                  {"total": 1, "passed": 1, "failed": 0, "infra": 0, "pass_rate": 1.0},
                  Args(tag="m0x"))
    entry = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(entry, HISTORY_SCHEMA)
    assert "k" not in entry and "arm" not in entry
    assert "samples" not in entry["cases"][0]


def test_the_recorded_entries_so_far_all_validate():
    """The schema gained a field. Every entry already in history must still be a
    legal entry — an append-only file whose schema stopped describing its own
    contents is worse than one with no schema."""
    from pave import history
    entries, problems = history.enumerate_entries()   # ADR-042: the one enumerator
    assert not problems, problems
    assert entries, "no history entries — this check would be vacuous"
    for path in entries:
        jsonschema.validate(json.loads(path.read_text(encoding="utf-8")), HISTORY_SCHEMA)


# --- the instrument did not move ---------------------------------------------

def test_the_sampling_did_not_touch_the_scorer():
    """The claim SPEC/02 makes about this change: the k-sampling lives in the run
    harness, not in the instrument. `evals/deterministic.py` must not know that
    sampling exists — if it does, each sample is no longer scored by the code path
    a single run uses, and the two arms stop being comparable to m00b and m01."""
    source = (ROOT / "evals" / "deterministic.py").read_text(encoding="utf-8")
    # Narrow tokens on purpose. `samples` alone appears in `suite_latency`, which
    # has sampled percentiles since M00b and has nothing to do with k-sampling —
    # a keyword check broad enough to catch that would have to be loosened later,
    # and a check that gets loosened is a check nobody trusts.
    for token in ("summarise", "majority", "per_sample", "run_evals"):
        assert token not in source, (
            f"evals/deterministic.py mentions {token!r}. k-sampling is a reporting "
            "discipline; moving it into the scorer makes it an instrument change, and an "
            "instrument change between two milestones is the ADR-016 hazard."
        )

"""
The calibration corpus, pinned.

An agreement number is only worth reading if the items it was measured on were
not chosen to produce it. This module is what makes that checkable rather than
asserted: it re-runs the draw and compares it to what is committed, so a corpus
that was edited by hand — or a selection rule that was quietly adjusted after
seeing an agreement number — fails `make check` instead of passing review.

**Why the rule and the corpus live in different places.** The rule is
`evals/calibration.py`, which is testable and hermetic. Its output is
`quality/judge/calibration/items.json`, which is a **two-key path** (AI Quality).
Changing the rule without regenerating the corpus fails these tests, and
regenerating the corpus changes a two-key file — so the corpus cannot move
quietly in either direction.

Hermetic (G8): committed answers, committed rule, no model. Owning seat: AI
Quality.
"""
import json
import pathlib

import pytest
import yaml

from evals.calibration import (
    MAX_PER_ANSWER,
    MAX_PER_RUN,
    QUOTAS,
    REFUSAL_ITEMS,
    RUNS,
    SALT,
    answer_digest,
    committed,
    select,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
SPEC = ROOT / "SPEC" / "03-evals.md"

#: SPEC/03's own numbers. Stated here rather than imported, so that a change to
#: the rule which also changes these has to disagree with a constant somebody
#: wrote down on purpose.
CORPUS_SIZE = 30
HELD_OUT = 20
DEV = 10


@pytest.fixture(scope="module")
def cases():
    return yaml.safe_load(CASES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def frozen():
    return committed()


def test_the_committed_corpus_is_what_the_rule_draws(cases, frozen):
    """The pin.

    If this fails, either the corpus was edited by hand or the rule moved
    underneath it. Both are allowed — the corpus may grow with a milestone that
    earns it — and neither is allowed to happen silently, because a corpus that
    changes after an agreement number is published makes that number
    unfalsifiable."""
    drawn = [
        {"id": i.id, "run": i.run, "case_id": i.case_id, "axis": i.axis,
         "split": i.split, "refusal": i.refusal, "answer_sha256": i.answer_sha256}
        for i in select(cases)
    ]
    assert drawn == frozen["items"], (
        "the committed calibration corpus is not what evals/calibration.py draws. "
        "Regenerating it is a two-key change (AI Quality), and any published agreement "
        "number measured on the old corpus no longer describes this one."
    )


def test_the_salt_is_the_commit_that_fixed_the_thresholds(frozen):
    """Choosing a salt after seeing which items it selects is re-rolling.

    The salt is the SHA of `SPEC/03-evals.md`'s own commit, which fixed the
    thresholds, the corpus size and the split before a single item was drawn. It
    cannot be changed without rewriting that commit."""
    assert frozen["salt"] == SALT
    assert len(SALT) == 40 and all(c in "0123456789abcdef" for c in SALT)


def test_the_corpus_is_the_size_the_spec_pre_registered(frozen):
    items = frozen["items"]
    assert len(items) == CORPUS_SIZE
    assert sum(1 for i in items if i["split"] == "held-out") == HELD_OUT
    assert sum(1 for i in items if i["split"] == "dev") == DEV


def test_every_stratum_is_full(frozen):
    """A corpus that silently shrinks reports a better agreement from a narrower
    measurement — ADR-009's direction-that-matters, one corpus over."""
    items = frozen["items"]
    for axis, total, held in QUOTAS:
        got = [i for i in items if i["axis"] == axis]
        assert len(got) == total, f"{axis}: {len(got)} items, expected {total}"
        assert sum(1 for i in got if i["split"] == "held-out") == held


def test_the_axes_under_five_held_out_items_are_the_ones_the_spec_named():
    """SPEC/03 demotes an axis with fewer than 5 held-out items *before* its
    agreement is computed, and predicted that this starts `brand_tone` and
    `concision` demoted.

    The rule was fixed before the strata were counted. This test is what stops
    that ordering being re-arranged later — if a future draw gives `brand_tone`
    five items, the prediction in the spec has to be read again rather than
    quietly satisfied."""
    below = {axis for axis, _total, held in QUOTAS if held < 5}
    assert below == {"brand_tone:meridian-sports", "concision"}


def test_the_draw_is_spread_across_answers_and_runs(frozen):
    """A draw concentrated on a handful of answers would measure the judge's
    opinion of those answers rather than of the corpus."""
    items = frozen["items"]
    per_answer, per_run = {}, {}
    for i in items:
        per_answer[(i["run"], i["case_id"])] = per_answer.get((i["run"], i["case_id"]), 0) + 1
        per_run[i["run"]] = per_run.get(i["run"], 0) + 1
    assert max(per_answer.values()) <= MAX_PER_ANSWER
    assert max(per_run.values()) <= MAX_PER_RUN
    assert set(per_run) == {label for label, _ in RUNS}, (
        "a committed run contributed no calibration items; the corpus no longer spans "
        "the range of answer quality the judge has to discriminate"
    )


def test_the_refusals_were_drawn_deliberately(frozen):
    """A refused answer carries no prose, so the judge must return
    *not-applicable* rather than a band. The only way to know it does is to have
    some in the corpus — and drawing them first is what makes their presence a
    rule rather than luck."""
    assert sum(1 for i in frozen["items"] if i["refusal"]) == REFUSAL_ITEMS


def test_every_item_still_points_at_the_bytes_it_was_drawn_from(cases, frozen):
    """Without this, a label points at a case id and a case id points at whatever
    the answer file says today — so the label would survive an edit to the thing
    it was a label *of*. That is the quiet version of relabelling."""
    answers = {label: json.loads((ROOT / rel).read_text(encoding="utf-8"))
               for label, rel in RUNS}
    for item in frozen["items"]:
        answer = answers[item["run"]][item["case_id"]]["answer"]
        assert answer_digest(answer) == item["answer_sha256"], (
            f"{item['id']}: the answer it labels has changed since it was drawn"
        )


def test_the_corpus_carries_no_labels(frozen):
    """Items and labels are separate files on purpose.

    The corpus is committed before the labels exist, and the ordering is the
    protection: a label written against an item that already carried one is not
    an independent label. Keeping them apart means the git history shows which
    came first."""
    for item in frozen["items"]:
        assert not ({"label", "band", "drafted", "final"} & set(item)), (
            f"{item['id']} carries a label. Labels live in labels.json, committed "
            "after the corpus and before any judge prompt exists."
        )


def test_an_item_id_does_not_leak_its_split(frozen):
    """Ids are assigned over the whole corpus in a stable order, so a labeller
    reading `cal-07` cannot infer that it is held-out. If ids clustered by split,
    a labeller could — consciously or not — label the measured half differently
    from the practice half."""
    held = [int(i["id"].split("-")[1]) for i in frozen["items"] if i["split"] == "held-out"]
    dev = [int(i["id"].split("-")[1]) for i in frozen["items"] if i["split"] == "dev"]
    assert min(held) < max(dev) and min(dev) < max(held), (
        "held-out and dev ids form separate blocks; the id ordering leaks the split"
    )


def test_the_spec_and_the_rule_agree_on_the_numbers():
    """The spec is the contract and the rule is the implementation. A milestone
    that changes one and not the other has changed its own definition of done
    without saying so."""
    spec = SPEC.read_text(encoding="utf-8")
    assert "**30 items, frozen before labelling, split 10 dev / 20 held-out" in spec
    assert "fewer than 5 held-out items" in spec

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


def test_the_salt_is_unchanged(frozen):
    """Choosing a salt after seeing which items it selects is re-rolling, and the
    salt's value *is* the draw — every item's sort key is
    `sha256(SALT|run|case|axis)`, so a changed salt selects thirty different items.

    The salt was fixed before the draw, in the commit that pre-registered the
    thresholds. **It no longer names a reachable commit**: the rebase onto #21
    moved that commit and this SHA was never pushed. It is not updated to match,
    because updating it would redraw a corpus whose labels are already written —
    see the corpus README for what survives the rebase and what does not.

    This test therefore pins the value and nothing about its provenance. The
    provenance is carried by the commit history and by the spec blob, neither of
    which a unit test can honestly assert."""
    assert frozen["salt"] == SALT
    assert len(SALT) == 40 and all(c in "0123456789abcdef" for c in SALT)


def test_the_rebase_hazard_is_recorded_where_a_reader_will_hit_it():
    """A stale identifier that nobody wrote down reads as a mistake; one that is
    written down reads as a decision. The claim being corrected appeared in three
    places, and a reader arriving at any of them must find the correction."""
    for path in (
        ROOT / "quality" / "judge" / "calibration" / "README.md",
        ROOT / "evals" / "calibration.py",
    ):
        text = path.read_text(encoding="utf-8")
        assert "815b172" in text, f"{path.name} does not name the rebased spec commit"
        assert "not reachable" in text or "no longer names a reachable" in text


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


# --- labels ------------------------------------------------------------------
#
# Drafted by the assistant, disposed by the AI Quality seat (SPEC/03's amendment).
# These tests pin the integrity of that arrangement: that every item has exactly
# one label, that each label is still bound to the bytes it was written against,
# and that a disposition cannot be half-recorded. They do **not** assert that
# disposition has happened — `run_judge.py` refuses to run until it has, which is
# the right enforcement point: a red `main` would push toward disposing quickly
# rather than carefully.


@pytest.fixture(scope="module")
def labels():
    return json.loads(
        (ROOT / "quality" / "judge" / "calibration" / "labels.json").read_text(encoding="utf-8")
    )


def test_every_item_has_exactly_one_label(frozen, labels):
    assert [row["item"] for row in labels["labels"]] == [i["id"] for i in frozen["items"]]


def test_a_label_is_bound_to_the_bytes_it_was_written_against(frozen, labels):
    """The same protection the corpus has, applied one file over. A label that
    survives an edit to its answer is a label of something else."""
    digests = {i["id"]: i["answer_sha256"] for i in frozen["items"]}
    for row in labels["labels"]:
        assert row["answer_sha256"] == digests[row["item"]]


def test_bands_are_the_three_the_rubric_defines(labels):
    for row in labels["labels"]:
        assert row["drafted"] in (0.0, 0.5, 1.0, None)
        assert row["final"] in (0.0, 0.5, 1.0, None)
        assert row["applicable"] is (row["drafted"] is not None)


def test_the_labels_declare_themselves_ai_proposed(labels):
    """G6, made legible. The published agreement number is measured against labels
    a model drafted, and the correction rate is the only thing that says how much
    of them survived a human seat. A provenance block that quietly said `human`
    would make the number look like something it is not."""
    assert labels["provenance"]["author"] == "ai-proposed"
    assert labels["provenance"]["drafted_by"]


def test_a_disposition_is_all_or_nothing(labels):
    """Half a disposition is the failure mode worth blocking: 30 drafts, six
    reviewed, and a correction rate computed over the six that were looked at
    hardest. Either every label carries a `final` and the seat is named, or the
    corpus is still undisposed."""
    finals = [row for row in labels["labels"] if row["disposition"] is not None]
    if not labels["provenance"]["disposed"]:
        assert not finals, (
            "labels carry dispositions but the corpus is not marked disposed. Set "
            "provenance.disposed and provenance.curated_by, or clear them."
        )
        return
    assert labels["provenance"]["curated_by"], "a disposed corpus names the seat that disposed it"
    assert len(finals) == len(labels["labels"]), (
        "a disposed corpus disposes every label. Agreement measured over a "
        "hand-picked subset is agreement over the items somebody chose to check."
    )
    for row in labels["labels"]:
        assert row["disposition"] in ("agreed", "changed")
        assert (row["final"] == row["drafted"]) is (row["disposition"] == "agreed")


def test_no_axis_has_a_single_label_value_without_the_spec_saying_so():
    """SPEC/03's fifth pre-flight finding, kept executable.

    `brand_tone` drew the same band on every applicable item. An axis whose labels
    are all one value cannot produce a meaningful agreement number — a judge that
    answers that value to everything scores 1.00 raw, and κ has no baseline to
    correct against. It is demoted on the insufficient-evidence rule anyway, so
    nothing published changes; this test exists so that the day the stratum is
    widened, the finding is re-read rather than forgotten."""
    spec = SPEC.read_text(encoding="utf-8")
    assert "zero label variance" in spec


def test_the_worksheet_is_what_the_generator_renders(labels):
    """The worksheet is what the seat actually reads while disposing. A stale copy
    means the seat disposed of an answer that is no longer there."""
    from evals.render_worksheet import OUT, render

    assert OUT.read_text(encoding="utf-8") == render(), (
        "the committed worksheet is not what evals/render_worksheet.py produces. "
        "Regenerate it with `python -m evals.render_worksheet`."
    )


def test_the_worksheet_does_not_leak_the_split():
    """A labeller who can see which items are measured can label the measured half
    differently from the practice half. That is the one bias this corpus has no
    way to recover from, so the worksheet omits the split entirely."""
    from evals.render_worksheet import OUT

    # Only the body is checked. The preamble says the split is deliberately
    # absent, which is the one place those words are allowed to appear.
    body = OUT.read_text(encoding="utf-8").split("## cal-01", 1)[1]
    for word in ("held-out", "dev ", "split"):
        assert word not in body, f"the worksheet body names an item's split ({word!r})"


def test_the_band_summary_still_matches_the_rubric():
    """The worksheet carries the rubric's band wording so a labeller need not hold
    two files open. A summary of a hash-pinned instrument that is allowed to drift
    from it is worse than no summary at all."""
    from evals.calibration import BANDS

    rubric = (ROOT / "quality" / "judge" / "rubric-sports.md").read_text(encoding="utf-8")
    for axis, bands in BANDS.items():
        for phrase in bands:
            assert phrase in rubric, f"{axis}: {phrase!r} is no longer the rubric's wording"


def test_the_correction_rate_is_zero_and_that_is_a_recorded_finding(labels):
    """SPEC/03 pre-registered a correction rate of 15–35%, with **0 corrections as
    a falsifier**: it means the disposition did not happen independently, and the
    agreement number is a model agreeing with a model.

    The seat disposed all 30 labels as `agreed`. The prediction is falsified, in
    the direction that flatters the instrument, and the prediction in SPEC/03 is
    **not edited** — a prediction revised after the fact is not a prediction.

    This constant is here so that a later relabel cannot happen quietly: changing
    any label changes this number, and changing this number is a diff somebody has
    to write and a seat has to approve. That is the whole mechanism — the rate
    cannot tell a correct draft from a rubber stamp, but it can make either one
    visible.

    See `quality/judge/calibration/README.md` for what the published agreement
    number must carry as a result."""
    from evals.calibration import correction_rate

    assert labels["provenance"]["disposed"] is True
    assert labels["provenance"]["curated_by"] == "ai-quality"
    assert correction_rate(labels) == {
        "disposed": 30, "changed": 0, "changed_items": [], "rate": 0.0,
    }

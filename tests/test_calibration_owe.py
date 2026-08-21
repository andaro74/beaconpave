"""
An owe that lapses silently is not an owe.

`brand_tone` drew five gradeable items that all carry the same label, so the axis
cannot produce a meaningful agreement figure. ADR-026 recorded widening it as owed
**to M04** -- and M04 closed without paying it, which nothing noticed, because the
obligation lived in a sentence inside an ADR and no check read that sentence.

These tests make the obligation something the suite can see. The owe is committed
data in `labels.json` (two-key, AI Quality) rather than prose, and its `pay_by`
milestone is checked against the progression table. **When that milestone closes,
this suite goes red** unless the owe was paid or deliberately re-deferred -- and a
re-deferral is then an attested edit to a two-key file, which is what a decision
should cost and what the last one did not.

Hermetic (G8): reads committed files, calls nothing.
Owning seat: AI Quality (the corpus and the labels) - PM (milestone ordering).
"""
from __future__ import annotations

import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
LABELS = ROOT / "quality" / "judge" / "calibration" / "labels.json"
README = ROOT / "README.md"


def _labels():
    return json.loads(LABELS.read_text(encoding="utf-8"))


def _zero_variance_axes() -> set:
    """Axes whose gradeable labels are all one value."""
    by = collections.defaultdict(set)
    for record in _labels()["labels"]:
        if record.get("applicable") and record.get("final") is not None:
            by[record["axis"]].add(record["final"])
    return {axis for axis, values in by.items() if len(values) < 2}


def _milestone_is_closed(tag: str) -> bool:
    """Read the progression table rather than git tags.

    The table is what the README publishes and what a reader believes, so it is
    the honest source for "is this milestone closed" -- and it is committed, which
    keeps this hermetic. It was ALSO wrong once: M03 sat at the unclosed marker for
    four milestones after it was tagged, which is why a check that reads it is
    worth having in its own right."""
    number = tag.lower().lstrip("m")
    for line in README.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 3 and cells[1].lower().lstrip("0") == number.lstrip("0"):
            return "✅" in line
    raise AssertionError(f"no progression row for milestone {tag!r}")


def test_every_zero_variance_axis_is_recorded_as_owed():
    """An axis that cannot produce an agreement number must say so in the file,
    not only in an ADR nobody parses."""
    owed = {entry["axis"] for entry in _labels().get("owed") or []}
    missing = sorted(_zero_variance_axes() - owed)
    assert not missing, (
        f"axis/axes {missing} have single-valued labels and are recorded as owed "
        "nowhere. An agreement figure computed against them measures nothing.")


def test_the_owe_is_still_within_the_milestone_it_was_deferred_to():
    """The teeth. This goes red the moment the named milestone closes unpaid."""
    for entry in _labels().get("owed") or []:
        target = entry.get("re_deferred_to") or entry.get("originally_due")
        assert target, f"owe for {entry['axis']!r} names no milestone at all"
        assert not _milestone_is_closed(target), (
            f"{entry['axis']} was owed by {target}, {target} is marked closed, and the "
            "owe is still recorded as outstanding. Pay it by extending the "
            "deterministic draw, or re-defer it deliberately in labels.json — which "
            "is two-key, and that is the point: the last re-deferral happened by "
            "nobody noticing.")


def test_an_owe_states_how_it_must_be_paid():
    """Widening by choosing items that vary the label would BE the defect: the
    distribution has been seen, so picking items is picking the answer."""
    for entry in _labels().get("owed") or []:
        how = entry.get("how_it_must_be_paid", "")
        assert "determinis" in how.lower(), (
            f"the owe for {entry['axis']!r} does not say the draw stays deterministic")


def test_the_progression_table_can_actually_be_read():
    """A parser that silently matched nothing would make the check above vacuous."""
    assert _milestone_is_closed("M04") is True
    assert _milestone_is_closed("M07") is False
    assert re.search(r"^\| 04 \|", README.read_text(encoding="utf-8"), re.MULTILINE)

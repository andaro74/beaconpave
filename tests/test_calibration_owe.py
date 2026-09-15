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

**An owe may instead hold a terminal state and name no milestone** (ADR-081 decision
5): RETIRED, with its ADR and the two seats that disposed it, or UNSCHEDULED, with
its owners and a trigger. `tests/milestone_status.py` decides what each must carry.
Row 12 is the last row, so after it closes a terminal state is the only form an owe
can take.

Hermetic (G8): reads committed files, calls nothing.
Owning seat: AI Quality (the corpus and the labels) - PM (milestone ordering).
Two-key since M12 PR 2: AI Quality + Platform Engineering, with `tests/milestone_status.py`.
"""
from __future__ import annotations

import collections
import json
import re

import pytest
from milestone_status import (
    README,
    RETIRED,
    ROOT,
    UNSCHEDULED,
    milestone_is_closed,
    progression_order,
    terminal_state_defects,
)

LABELS = ROOT / "quality" / "judge" / "calibration" / "labels.json"
#: The registry's repo-relative path. Its two-key rule decides who may retire an owe.
REGISTRY = "quality/judge/calibration/labels.json"
#: The field in an owe that names a milestone to be paid by.
TARGETS = ("re_deferred_to",)

#: **A made-up progression table: one closed row, one open row** (M10 row 24). The
#: live table cannot hold an open row for ever. Row 12 is its last, and the guard that
#: required both answers from it was unsatisfiable the day row 12 read ✅.
MADE_UP_TABLE = "\n".join([
    "| M | Milestone | Branch | Tag | Goldens | Judged | Adversarial | Status |",
    "|---|---|---|---|---|---|---|---|",
    "| 01 | a made-up closed row | `m01-x` | `m01` | – | – | – | ✅ |",
    "| 02 | a made-up open row | `m02-x` | `m02` | – | – | – | ⬜ |",
])
#: The same table the day its last row closes, which is row 12's day in the live one.
ALL_CLOSED_TABLE = MADE_UP_TABLE.replace("⬜", "✅")


def _labels():
    return json.loads(LABELS.read_text(encoding="utf-8"))


def _zero_variance_axes() -> set:
    """Axes whose gradeable labels are all one value."""
    by = collections.defaultdict(set)
    for record in _labels()["labels"]:
        if record.get("applicable") and record.get("final") is not None:
            by[record["axis"]].add(record["final"])
    return {axis for axis, values in by.items() if len(values) < 2}


def owe_defects(entry: dict, text: str | None = None) -> list[str]:
    """Why an owe has lapsed or is malformed. Empty means it stands.

    An owe with a `state` field is read by `terminal_state_defects`, any value
    included: `state: ""` is refused there, and is not a way past the teeth. Any other
    owe must name a milestone the table lists and has not closed. That half is the
    teeth, unchanged."""
    if entry.get("state") is not None:
        return terminal_state_defects(entry, REGISTRY, TARGETS, text)
    target = entry.get("re_deferred_to") or entry.get("originally_due")
    if not target:
        return [f"owe for {entry['axis']!r} names no milestone and holds no terminal state"]
    if milestone_is_closed(target, text):
        return [
            f"{entry['axis']} was owed by {target}, {target} is marked closed, and the "
            "owe is still recorded as outstanding. Pay it by extending the "
            "deterministic draw, re-defer it deliberately in labels.json, or move it to "
            "a terminal state (ADR-081 decision 5) -- all two-key, and that is the "
            "point: the first re-deferral happened by nobody noticing."]
    return []


def test_every_zero_variance_axis_is_recorded_as_owed():
    """An axis that cannot produce an agreement number must say so in the file,
    not only in an ADR nobody parses."""
    owed = {entry["axis"] for entry in _labels().get("owed") or []}
    missing = sorted(_zero_variance_axes() - owed)
    assert not missing, (
        f"axis/axes {missing} have single-valued labels and are recorded as owed "
        "nowhere. An agreement figure computed against them measures nothing.")


def test_the_owe_is_still_within_the_milestone_it_was_deferred_to():
    """The teeth. This goes red the moment the named milestone closes unpaid, or
    when an owe in a terminal state is missing what its state must carry.

    The name is kept, though a RETIRED owe is within no milestone, because journals
    and ADR-026's amendments cite it."""
    for entry in _labels().get("owed") or []:
        defects = owe_defects(entry)
        assert not defects, f"owe for {entry['axis']!r}: {defects}"


def test_an_owe_states_how_it_must_be_paid():
    """Widening by choosing items that vary the label would BE the defect: the
    distribution has been seen, so picking items is picking the answer."""
    for entry in _labels().get("owed") or []:
        how = entry.get("how_it_must_be_paid", "")
        assert "determinis" in how.lower(), (
            f"the owe for {entry['axis']!r} does not say the draw stays deterministic")


def test_the_progression_table_can_actually_be_read():
    """A parser that silently matched nothing would make the check above vacuous.

    This pinned `M07 is False` and went red at the M07 close, for the reason
    `tests/test_demo_recordings.py` records about its own literal: a sentinel
    naming the next open milestone expires on the day that milestone closes.
    The property is that the parser DISCRIMINATES -- a closed row and an open
    row both resolve -- and the M04 pin stays because a closed row never
    reopens.

    **The discriminating half moved to a made-up table at M12 PR 2** (M10 row 24,
    ADR-081 decision 5 item 5). It read `{True, False}` off the live table, which
    has no open row once row 12 closes. What stays live names no milestone that
    can move: every live row parses, there are rows to parse, and M04 still reads
    closed, which is what notices a changed marker."""
    # Live: the table the repository publishes still parses.
    live = progression_order()
    assert len(live) >= 2, f"the progression parser found {len(live)} rows in README.md"
    assert all(isinstance(milestone_is_closed(key), bool) for key in live)
    assert milestone_is_closed("M04") is True
    assert re.search(r"^\| 04 \|", README.read_text(encoding="utf-8"), re.MULTILINE)

    # Made up: the parser tells a closed row from an open one, in that direction.
    assert progression_order(MADE_UP_TABLE) == ["1", "2"]
    assert milestone_is_closed("M01", MADE_UP_TABLE) is True
    assert milestone_is_closed("M02", MADE_UP_TABLE) is False
    answers = {milestone_is_closed(key, MADE_UP_TABLE) for key in progression_order(MADE_UP_TABLE)}
    assert answers == {True, False}, answers


# --- the terminal state, misused -------------------------------------------------
#
# One mutation per plant, and each asserts the ONE defect it expects by a phrase from
# its message. A plant that turned up two defects could be passing on the wrong door
# while the door it names is dead.

UNSCHEDULED_OWE = {
    "axis": "made-up-axis",
    "originally_due": "M01",
    "re_deferred_to": None,
    "state": UNSCHEDULED,
    "owners": ["ai-quality", "security"],
    "trigger": "the first milestone that adds a judge axis",
    "how_it_must_be_paid": "by extending the deterministic draw",
}
RETIRED_OWE = {
    "axis": "made-up-axis",
    "originally_due": "M01",
    "re_deferred_to": None,
    "state": RETIRED,
    "retired_by": "docs/adr/ADR-026-calibration-corpus-size-and-freeze-rule.md",
    "disposed_by": ["ai-quality", "security"],
    "how_it_must_be_paid": "by extending the deterministic draw",
}


def _planted(base: dict, **change) -> dict:
    entry = dict(base)
    for field, value in change.items():
        if value is KeyError:
            entry.pop(field)
        else:
            entry[field] = value
    return entry


def test_a_well_formed_terminal_owe_stands_on_either_table():
    """The control. Without it every refusal below could be a validator that
    refuses everything."""
    for text in (MADE_UP_TABLE, ALL_CLOSED_TABLE):
        assert owe_defects(UNSCHEDULED_OWE, text) == []
        assert owe_defects(RETIRED_OWE, text) == []


@pytest.mark.parametrize("base, change, phrase", [
    # UNSCHEDULED without an owner
    (UNSCHEDULED_OWE, {"owners": KeyError}, "UNSCHEDULED with owners None"),
    (UNSCHEDULED_OWE, {"owners": []}, "UNSCHEDULED with owners []"),
    (UNSCHEDULED_OWE, {"owners": ["  "]}, "UNSCHEDULED with owners"),
    (UNSCHEDULED_OWE, {"trigger": KeyError}, "UNSCHEDULED with trigger None"),
    # a terminal state that still names a milestone, open or closed
    (UNSCHEDULED_OWE, {"re_deferred_to": "M02"}, "(open)"),
    (UNSCHEDULED_OWE, {"re_deferred_to": "M01"}, "(closed)"),
    (RETIRED_OWE, {"re_deferred_to": "M02"}, "(open)"),
    # RETIRED without its ADR, or without its two seats
    (RETIRED_OWE, {"retired_by": KeyError}, "RETIRED without its ADR"),
    (RETIRED_OWE, {"retired_by": "README.md"}, "RETIRED without its ADR"),
    (RETIRED_OWE, {"disposed_by": ["ai-quality"]}, "RETIRED with `disposed_by"),
    (RETIRED_OWE, {"disposed_by": ["ai-quality", "ai-quality"]}, "RETIRED with `disposed_by"),
    (RETIRED_OWE, {"disposed_by": ["ai-quality", "platform-eng"]}, "RETIRED with `disposed_by"),
    # a state that is not one
    (UNSCHEDULED_OWE, {"state": "PARKED"}, "is not one of"),
    (UNSCHEDULED_OWE, {"state": ""}, "is not one of"),
])
def test_a_terminal_state_refuses_an_owe_missing_what_it_must_carry(base, change, phrase):
    """Each state's requirement, planted away one at a time, on the made-up table
    where `M02` is open. **The open-milestone plant is the one the old teeth could not
    see:** `re_deferred_to: M02` with M02 open passes them, so an owe labelled
    UNSCHEDULED that still defers would read as both."""
    defects = owe_defects(_planted(base, **change), MADE_UP_TABLE)
    assert len(defects) == 1 and phrase in defects[0], defects


def test_with_every_row_closed_a_deferred_owe_is_red_and_a_terminal_one_is_not():
    """**Row 12's day, on a table where it has already arrived.** An owe still
    deferred to the last row goes red when that row closes, which is the teeth
    keeping their bite after the last row. A terminal owe stays green, which is
    what the state is for. `milestone_is_closed` still raises for a row the table
    does not list, so there is nowhere left to defer to."""
    deferred = {"axis": "made-up-axis", "originally_due": "M01", "re_deferred_to": "M02",
                "how_it_must_be_paid": "by extending the deterministic draw"}
    assert owe_defects(deferred, MADE_UP_TABLE) == []
    assert len(owe_defects(deferred, ALL_CLOSED_TABLE)) == 1
    assert owe_defects(UNSCHEDULED_OWE, ALL_CLOSED_TABLE) == []
    assert owe_defects(RETIRED_OWE, ALL_CLOSED_TABLE) == []
    with pytest.raises(AssertionError, match="no progression row"):
        owe_defects({**deferred, "re_deferred_to": "M03"}, ALL_CLOSED_TABLE)

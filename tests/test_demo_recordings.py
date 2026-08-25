"""
The recordings are the deliverable, and none of them existed.

`docs/governance/demo-script.md` opens with "the recordings ARE the deliverable"
and `.claude/skills/close-milestone` step 8 says to record at close. **No act had
ever been recorded.** Act 0 belongs to M00b, which closed and tagged four
milestones ago; its script was even rewritten at close, because the original act
described a failure the control did not actually have. The rule was real, stated
in two places, and enforced by nothing.

That is the same shape as `brand_tone`, whose widening was owed "to M04" in an
ADR and which M04 closed without paying while nothing noticed. An obligation
written only in a sentence is discharged by forgetting, so this one is data and
these tests read it.

**What this does NOT do is treat a recording as evidence.** Claim 2 is proved by
PR #29 -- permanent, linkable, re-derivable, carrying the gate's own comment and
`exit 1` in the log -- and the twelve-claims table cites that PR rather than a
video. Deferring the recording did not defer the proof. The registry records that
distinction per act, because it is not true of every act: Act 4's go/no-go
artifact is produced BY the run it demonstrates.

Hermetic (G8): reads committed files, calls nothing.
Owning seat: Platform Engineering (the demo script) - PM (milestone ordering).
"""
from __future__ import annotations

import json
import re

from milestone_status import ROOT, milestone_is_closed

SCRIPT = ROOT / "docs" / "governance" / "demo-script.md"
REGISTRY = ROOT / "docs" / "governance" / "recordings.json"


def _registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["acts"]


def _acts_in_script() -> set:
    return {int(m) for m in re.findall(r"^## Act (\d+)", SCRIPT.read_text(encoding="utf-8"),
                                       re.MULTILINE)}


def test_every_act_in_the_script_is_tracked():
    """Adding an act must not be a way to add an untracked obligation."""
    tracked = {a["act"] for a in _registry()}
    assert _acts_in_script() == tracked, (
        f"script declares {sorted(_acts_in_script())}, registry tracks {sorted(tracked)}")


def test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed():
    """The teeth. Each act goes red the moment its milestone closes unrecorded."""
    for act in _registry():
        if act.get("recorded"):
            continue
        owed = act.get("owed_by")
        assert owed, f"Act {act['act']} is unrecorded and owed to no milestone"
        assert not milestone_is_closed(owed), (
            f"Act {act['act']} ({act['title']}) was owed by {owed}, {owed} is closed, "
            "and it is still unrecorded. Record it, or re-defer it deliberately in "
            "docs/governance/recordings.json — the last time this obligation moved, it "
            "moved by nobody noticing.")


def test_a_claimed_recording_actually_exists():
    """A registry that can claim a recording nobody can play is worse than none."""
    for act in _registry():
        path = act.get("recorded")
        if not path:
            continue
        assert (ROOT / path).is_file(), (
            f"Act {act['act']} claims a recording at {path!r}, which is not in the tree")


def test_an_act_owed_past_its_own_milestone_says_why():
    """Deferring an act beyond the milestone that owns it is a decision, and a
    decision with no stated reason is indistinguishable from an oversight."""
    for act in _registry():
        if act.get("recorded") or act["owed_by"] == act["owner_milestone"]:
            continue
        assert len(act.get("why", "")) > 60, (
            f"Act {act['act']} is owned by {act['owner_milestone']} and deferred to "
            f"{act['owed_by']} with no reason recorded")


def test_the_progression_parser_is_not_vacuous():
    """A parser that matched nothing would make every check above pass silently.

    **This names no milestone.** It used to be two literals — `M04 is True` and
    `M05 is False` — and only the second was counted among the forty-five `m05`
    sentinels this milestone had to migrate. The first was load-bearing for the
    `is True` direction and nobody had noticed, so a rename that touched only the
    counted one would have left a half-restructured guard.

    What it asserts instead is the property: the parser **discriminates**. Reading
    the live table and requiring both answers to appear survives every close,
    because a milestone moving from unclosed to closed moves a row from one side
    to the other rather than emptying either.

    **The horizon, stated rather than asserted away.** This holds while at least
    one row is unclosed and at least one is closed. When M10 closes, no row
    returns False and this guard is unsatisfiable again — one milestone later than
    the literal it replaces, not forever. The alternative is asserting against a
    synthetic two-row table, which stops reading what the repository publishes and
    is the whole reason `milestone_status` exists. That trade is recorded here as
    a decision rather than discovered at M10."""
    # **Scoped to the progression table by its backticked tag cell.** The first
    # version of this guard collected any row whose second cell was a number,
    # which also swept in README's twelve-CLAIMS table — and the two tables
    # disagreeing is what made it pass. It would have reported a discriminating
    # parser while the progression table was uniformly closed. Measured: closing
    # every progression row left this green.
    #
    # `milestone_status.milestone_is_closed` has the same looseness and takes the
    # first matching row, so `milestone_is_closed("11")` answers from the claims
    # table rather than raising. Today the progression table comes first, so every
    # real milestone resolves correctly; the ordering dependency is noted here
    # rather than relied on silently.
    tag_cell = re.compile(r"^`m\d\d[a-z]?`$")
    rows = [c[1] for c in (
        [x.strip() for x in line.split("|")]
        for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines())
        if len(c) > 4 and c[1].lstrip("0").isdigit() and any(tag_cell.match(x) for x in c)]
    assert len(rows) >= 2, (
        f"the progression parser found {len(rows)} milestone rows in README.md. "
        "Every check above reads this table; a parser that matches nothing makes "
        "all of them pass silently.")
    answers = {milestone_is_closed(number) for number in rows}
    assert answers == {True, False}, (
        f"the parser returned only {answers} across {len(rows)} rows. It is no longer "
        "discriminating: either every milestone reads closed, every one reads open, or "
        "the marker changed. If this is M10 closing and no row is unclosed any more, "
        "that is the stated horizon — replace this with a synthetic table and record "
        "why in the same diff.")

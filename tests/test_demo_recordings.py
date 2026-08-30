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

from milestone_status import (
    ROOT,
    display,
    key,
    latest_closed_milestone,
    milestone_is_closed,
    progression_order,
)

SCRIPT = ROOT / "docs" / "governance" / "demo-script.md"
REGISTRY = ROOT / "docs" / "governance" / "recordings.json"


def _registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["acts"]


def _acts_in_script() -> set:
    return {int(m) for m in re.findall(r"^## Act (\d+)", SCRIPT.read_text(encoding="utf-8"),
                                       re.MULTILINE)}


def uncounted_deferrals(acts, readme_text: str | None = None) -> list:
    """Acts that passed the most recently CLOSED milestone without recording it.

    **The gap this closes.** Every existing assertion here is satisfied by moving
    `owed_by` forward and leaving `deferred_from` alone: the owner is already in the
    history after the first slide, the new `owed_by` is legitimately absent from it,
    and each listed milestone is still closed and still named in `why`. So an act
    could go `M06 -> M07` recording nothing, and the count would stay at two while
    the truth was three.

    The milestone that just closed is the entry a fresh deferral adds. If an act is
    unrecorded, and its owning milestone is at or before the latest closed one, then
    it was owed during that milestone and passed it -- so that milestone belongs in
    `deferred_from`, and (by the assertion above) named in `why`.

    `readme_text` is injectable so `test_the_ratchet_fires_when_a_milestone_closes`
    can ask what happens the day M06 closes, rather than leaving the guard
    unexercised until the day it matters."""
    latest = latest_closed_milestone(readme_text)
    if latest is None:
        return []
    order = progression_order(readme_text)
    problems = []
    for act in acts:
        if act.get("recorded"):
            continue
        owner = key(act["owner_milestone"])
        if owner not in order or order.index(owner) > order.index(latest):
            continue                      # not yet owed when that milestone closed
        history = [key(t) for t in act.get("deferred_from") or []]
        if latest not in history:
            problems.append(
                f"Act {act['act']} is unrecorded, is owned by {act['owner_milestone']} "
                f"and passed {display(latest)} -- the most recently closed milestone -- "
                f"without listing it in `deferred_from`. Moving `owed_by` forward "
                "without counting the milestone just passed is the slide this file "
                "exists to make expensive.")
    return problems


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


def test_a_deferral_is_counted_and_named():
    """**The teeth above cannot count.** `test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed`
    asks one question — has the CURRENT `owed_by` closed — so an act that slides one
    milestone at a time is green at every step, and a fourth slide is
    indistinguishable from a first with the `why` rewritten to sound new. M05 is where
    that stopped being hypothetical: it is the first close this file's teeth bit at,
    and all three acts owed by it were re-deferred to M06 in one decision.

    `deferred_from` is the ratchet, and it is **derived rather than trusted** where it
    can be: a milestone listed there must actually have closed, the milestone the act
    is owed by now must NOT be listed (it has not been passed yet), and an act whose
    own owning milestone has closed unrecorded must list that milestone — the one
    entry the file cannot omit without contradicting the progression table.

    **The residual, stated rather than implied away.** Intermediate deferrals are not
    derivable: this file records where an act is owed NOW, not the sequence of places
    it used to be owed, so `deferred_from` naming M05 for Act 0 rests on the diff that
    wrote it. What makes that honest is not this assertion — it is that every entry
    must be NAMED in `why`, so the admission grows with the count, and that the file is
    two-key under ADR-049, so it grows in front of two seats.
    """
    for act in _registry():
        if act.get("recorded"):
            continue
        history = act.get("deferred_from")
        assert history is not None, (
            f"Act {act['act']} is unrecorded and records no `deferred_from`. An "
            "uncounted deferral is the one this file exists to make countable.")
        for tag in history:
            assert milestone_is_closed(tag), (
                f"Act {act['act']} claims it was deferred from {tag}, which has not "
                "closed. A deferral from a milestone still open has not happened yet.")
            assert tag in act.get("why", ""), (
                f"Act {act['act']} was deferred from {tag} and its `why` does not name "
                f"{tag}. Each deferral is admitted in the prose a reader actually reads, "
                "so the admission grows with the count.")
        assert act["owed_by"] not in history, (
            f"Act {act['act']} lists {act['owed_by']} — the milestone it is owed by "
            "now — among the milestones it was already deferred from.")
        owner = act["owner_milestone"]
        if milestone_is_closed(owner):
            assert owner in history, (
                f"Act {act['act']} is owned by {owner}, {owner} is closed, the act is "
                f"unrecorded, and `deferred_from` does not list {owner}. That is the one "
                "entry the progression table contradicts on its own.")


def test_the_ratchet_counts_the_milestone_that_just_closed():
    """The honest tree: nothing has passed a close uncounted."""
    assert uncounted_deferrals(_registry()) == []


def test_the_ratchet_fires_when_a_milestone_closes():
    """**A violating tree, because the honest one cannot exercise this.**

    The guard that matters fires on the day a milestone closes owing a recording, and
    a guard first exercised on that day is one nobody has run. So this closes M06 in a
    synthetic progression table and puts a synthetic registry through it.

    **The first version of this test read the LIVE registry and asserted the answer was
    `{0, 1, 2}`.** It passed for one PR and went red the moment those three acts were
    recorded at the M06 close -- not because the ratchet broke, but because the test
    asserted the register's CONTENTS rather than the function's PROPERTY, and the
    contents change at every close by design. A guard coupled to the data it guards
    expires on first use. The acts below are fixtures for that reason.

    Four directions, because a check that flags everything is as useless as one that
    flags nothing, and the two middle cases are the ones a naive implementation gets
    wrong."""
    text = ROOT.joinpath("README.md").read_text(encoding="utf-8")
    closed_m06 = "\n".join(
        line.replace("| ⬜ |", "| ✅ |") if line.strip().startswith("| 06 |") else line
        for line in text.splitlines())
    assert milestone_is_closed("M06", closed_m06), (
        "the synthetic table does not mark M06 closed, so this test proves nothing")
    assert not milestone_is_closed("M07", closed_m06), (
        "M07 reads as closed in the synthetic table, so the 'not yet owed' case below "
        "would pass for the wrong reason")

    acts = [
        # owed by the milestone that just closed, unrecorded, and does not count it
        {"act": 90, "owner_milestone": "M04", "recorded": None,
         "owed_by": "M06", "deferred_from": ["M04", "M05"]},
        # same, but M06 is already counted -- a deferral recorded honestly
        {"act": 91, "owner_milestone": "M04", "recorded": None,
         "owed_by": "M07", "deferred_from": ["M04", "M05", "M06"]},
        # RECORDED. The case that broke the first version of this test.
        {"act": 92, "owner_milestone": "M04", "recorded": "docs/x.mp4",
         "owed_by": "M06", "deferred_from": ["M04", "M05"]},
        # owned by a milestone AFTER the close -- it had not been owed yet
        {"act": 93, "owner_milestone": "M07", "recorded": None,
         "owed_by": "M07", "deferred_from": []},
    ]

    reported = {int(p.split()[1]) for p in uncounted_deferrals(acts, readme_text=closed_m06)}
    assert reported == {90}, (
        f"M06 closes and the ratchet reports {sorted(reported)}; only act 90 passed the "
        "close unrecorded without counting it. 91 counted it, 92 is recorded, and 93 was "
        "not yet owed")

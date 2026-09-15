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

import pytest
from milestone_status import (
    RETIRED,
    ROOT,
    UNSCHEDULED,
    display,
    key,
    latest_closed_milestone,
    milestone_is_closed,
    progression_order,
    terminal_state_defects,
)

SCRIPT = ROOT / "docs" / "governance" / "demo-script.md"
REGISTRY = ROOT / "docs" / "governance" / "recordings.json"
#: The registry's repo-relative path. Its two-key rule decides who may retire an act.
REGISTRY_PATH = "docs/governance/recordings.json"
#: The field in an act that names the milestone it is owed by.
TARGETS = ("owed_by",)

#: **A made-up README: a claims-shaped table, then a progression table with one closed
#: row and one open row** (M10 row 24). The claims-shaped row comes FIRST and reads ✅
#: for `02`, the open progression row, so a parser that stopped scoping itself to the
#: progression table answers `02` from the wrong table and loses the False.
MADE_UP_README = "\n".join([
    "| # | Claim | Proof | M | Status |",
    "|---|---|---|---|---|",
    "| 02 | a made-up claim | a made-up proof | 02 | ✅ |",
    "",
    "| M | Milestone | Branch | Tag | Goldens | Judged | Adversarial | Status |",
    "|---|---|---|---|---|---|---|---|",
    "| 01 | a made-up closed row | `m01-x` | `m01` | – | – | – | ✅ |",
    "| 02 | a made-up open row | `m02-x` | `m02` | – | – | – | ⬜ |",
])

#: The progression table's two status cells, named so the fixture below is a
#: pair of constants rather than two glyphs a reader has to squint at.
OPEN_CELL, CLOSED_CELL = "| ⬜ |", "| ✅ |"


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


def act_defects(act: dict, text: str | None = None) -> list[str]:
    """Why an act's obligation has lapsed or is malformed. Empty means it stands.

    A recorded act is paid, and `test_a_claimed_recording_actually_exists` resolves
    its path. An unrecorded act with a `state` is read by `terminal_state_defects`
    (ADR-081 decision 5), any value included. Any other unrecorded act must be owed to
    a milestone that has not closed, which is the teeth, unchanged. **A terminal state
    does not leave the ratchet:** `uncounted_deferrals` still counts every closed
    milestone an unrecorded act passed."""
    if act.get("recorded"):
        return []
    if act.get("state") is not None:
        return terminal_state_defects(act, REGISTRY_PATH, TARGETS, text)
    owed = act.get("owed_by")
    if not owed:
        return [f"Act {act['act']} is unrecorded, owed to no milestone, and holds no "
                "terminal state"]
    if milestone_is_closed(owed, text):
        return [
            f"Act {act['act']} ({act.get('title')}) was owed by {owed}, {owed} is closed, "
            "and it is still unrecorded. Record it, re-defer it deliberately in "
            "docs/governance/recordings.json, or move it to a terminal state (ADR-081 "
            "decision 5) — the last time this obligation moved, it moved by nobody "
            "noticing."]
    return []


def test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed():
    """The teeth. Each act goes red the moment its milestone closes unrecorded, or
    when an act in a terminal state is missing what its state must carry."""
    for act in _registry():
        defects = act_defects(act)
        assert not defects, defects


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
        if act.get("recorded") or act.get("owed_by") == act["owner_milestone"]:
            continue
        # A terminal act names no `owed_by`, so it lands here and must say why too.
        assert len(act.get("why", "")) > 60, (
            f"Act {act['act']} is owned by {act['owner_milestone']} and deferred to "
            f"{act.get('owed_by') or act.get('state')} with no reason recorded")


def test_the_progression_parser_is_not_vacuous():
    """A parser that matched nothing would make every check above pass silently.

    **This names no milestone.** It used to be two literals — `M04 is True` and
    `M05 is False` — and only the second was counted among the forty-five `m05`
    sentinels this milestone had to migrate. The first was load-bearing for the
    `is True` direction and nobody had noticed, so a rename that touched only the
    counted one would have left a half-restructured guard.

    What it asserts instead is the property: the parser **discriminates**.

    **The horizon arrived at M12, and this is the replacement it asked for** (M10 row
    24, ADR-081 decision 5 item 5). This used to read `{True, False}` off the live
    table, and said it held only while one row was unclosed. It predicted failure at
    M10's close and did not fail then, because rows 11 and 12 were open. Row 12 is the
    last row, so it would fail the day row 12 reads ✅, and its own message asked for a
    synthetic table recorded in the same diff. ADR-081 records why.

    **The trade the old docstring named stays visible.** A made-up table stops reading
    what the repository publishes, which is the whole reason `milestone_status` exists.
    So a live half stays, and it asserts only what no close can change: the live
    progression rows parse, there are at least two, and at least one reads closed. The
    discriminating half reads `MADE_UP_README`, where a claims-shaped row comes first
    and says ✅ for `02`."""
    # **Scoped to the progression table by its backticked tag cell.** The first
    # version of this guard collected any row whose second cell was a number,
    # which also swept in README's twelve-CLAIMS table — and the two tables
    # disagreeing is what made it pass. It would have reported a discriminating
    # parser while the progression table was uniformly closed. Measured: closing
    # every progression row left this green.
    #
    # This comment used to say `milestone_is_closed` shared that looseness and took
    # the first matching row from either table. `milestone_status._rows` is scoped by
    # the progression table's header now, so that is no longer true, and the made-up
    # README exercises the scoping rather than this comment asserting it.
    tag_cell = re.compile(r"^`m\d\d[a-z]?`$")
    rows = [c[1] for c in (
        [x.strip() for x in line.split("|")]
        for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines())
        if len(c) > 4 and c[1].lstrip("0").isdigit() and any(tag_cell.match(x) for x in c)]
    assert len(rows) >= 2, (
        f"the progression parser found {len(rows)} milestone rows in README.md. "
        "Every check above reads this table; a parser that matches nothing makes "
        "all of them pass silently.")
    live = {milestone_is_closed(number) for number in rows}
    assert True in live, (
        f"the parser read no closed row across {len(rows)} live rows. A closed row never "
        "reopens, so either the marker changed or the parser stopped matching it.")

    made_up = {number: milestone_is_closed(number, MADE_UP_README) for number in ("01", "02")}
    assert made_up == {"01": True, "02": False}, (
        f"the parser read the made-up README as {made_up}. It is no longer "
        "discriminating: every row reads closed, every one reads open, the marker "
        "changed, or `02` was answered from the claims-shaped table above the "
        "progression table.")


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
        assert act.get("owed_by") not in history, (
            f"Act {act['act']} lists {act.get('owed_by')} — the milestone it is owed by "
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
    # **The synthetic table must make M06 the LATEST closed milestone, not merely a
    # closed one.** `uncounted_deferrals` keys on the latest close, and this fixture
    # forced `| 06 |` to closed while leaving every later row as the live README has
    # it. That was correct for exactly as long as nothing after M06 was closed. The
    # day M06b closed, `latest_closed_milestone` returned M06b, act 91's
    # `deferred_from` legitimately did not name it, and a test about M06 reported two
    # acts and went red — a guard coupled to data that legitimately moves, which is
    # the shape this repository keeps paying for.
    #
    # So the fixture re-opens every row after `06`, and asserts the property it
    # actually depends on rather than two proxies for it.
    text = ROOT.joinpath("README.md").read_text(encoding="utf-8")
    rows, after_m06 = [], False
    for line in text.splitlines():
        if line.strip().startswith("| 06 |"):
            line, after_m06 = line.replace(OPEN_CELL, CLOSED_CELL), True
        elif after_m06 and line.strip().startswith("|"):
            line = line.replace(CLOSED_CELL, OPEN_CELL)
        rows.append(line)
    closed_m06 = chr(10).join(rows)

    # `latest_closed_milestone` returns the table's own row key ("6"), not the
    # "M06" spelling `milestone_is_closed` takes. Compared against the key it
    # returns, so this assertion cannot pass by comparing two things that are
    # never equal.
    assert latest_closed_milestone(closed_m06) == "6", (
        f"the synthetic table's latest closed milestone is "
        f"{latest_closed_milestone(closed_m06)!r}, not row 06. This test asks what happens "
        "the day M06 closes; if a later milestone reads as closed it is asking a different "
        "question and every expectation below is about the wrong close.")
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


# --- the terminal state, on this registry (ADR-081 decision 5) ------------------
#
# `tests/test_calibration_owe.py` plants every requirement of `terminal_state_defects`
# against the owe registry. These plant only what differs here: the target field is
# `owed_by`, the seats that may retire an act are this registry's, and the ratchet
# still counts an act in a terminal state.

UNSCHEDULED_ACT = {
    "act": 97, "title": "a made-up act", "owner_milestone": "M01", "recorded": None,
    "owed_by": None, "deferred_from": ["M01"], "why": "a made-up reason " * 5,
    "state": UNSCHEDULED, "owners": ["platform-eng"], "trigger": "a made-up trigger",
}
RETIRED_ACT = {
    "act": 98, "title": "a made-up act", "owner_milestone": "M01", "recorded": None,
    "owed_by": None, "deferred_from": ["M01"], "why": "a made-up reason " * 5,
    "state": RETIRED,
    "retired_by": "docs/adr/ADR-081-m12-is-the-ledger-claims-7-8-and-12-are-"
                  "unscheduled-and-act-5-is-retired.md",
    "disposed_by": ["platform-eng", "ai-quality"],
}


def test_a_well_formed_terminal_act_stands():
    """The control for the refusals below."""
    assert act_defects(UNSCHEDULED_ACT, MADE_UP_README) == []
    assert act_defects(RETIRED_ACT, MADE_UP_README) == []


@pytest.mark.parametrize("act, phrase", [
    # still owed to a milestone, and that milestone is open
    ({**UNSCHEDULED_ACT, "owed_by": "M02"}, "(open)"),
    # held by nobody
    ({**UNSCHEDULED_ACT, "owners": []}, "UNSCHEDULED with owners []"),
    # labels.json's two seats. This registry's rule does not collect Security.
    ({**RETIRED_ACT, "disposed_by": ["ai-quality", "security"]}, "RETIRED with `disposed_by"),
])
def test_a_terminal_state_refuses_an_act_missing_what_it_must_carry(act, phrase):
    defects = act_defects(act, MADE_UP_README)
    assert len(defects) == 1 and phrase in defects[0], defects


def test_the_ratchet_keeps_counting_an_act_in_a_terminal_state():
    """ADR-081 decision 5 item 4: *a state change does not erase a slide.* M01 is the
    latest closed row of the made-up README. A terminal act owned by M01 that does not
    list M01 in `deferred_from` passed M01 uncounted, whatever its state."""
    assert latest_closed_milestone(MADE_UP_README) == "1"
    uncounted = {**UNSCHEDULED_ACT, "deferred_from": []}
    reported = {int(p.split()[1])
                for p in uncounted_deferrals([uncounted, RETIRED_ACT], MADE_UP_README)}
    assert reported == {97}, reported

"""
Is a milestone closed? Read from what the repository PUBLISHES.

Shared by the checks that enforce a deferred obligation, so there is one answer to
"has M07 closed" rather than two that can drift -- the two-registry smell ADR-030
was written about, kept out of the test suite this time instead of consolidated
after the fact.

It reads the README progression table rather than git tags. That table is what a
reader believes, it is committed so the check stays hermetic (G8), and a tag can
exist while the table still says otherwise -- which is not hypothetical: M03 sat
at the unclosed marker for four milestones after `m03` was pushed. A check that
reads the table therefore also notices when the table is lying.
"""
from __future__ import annotations

import pathlib
from collections.abc import Sequence

from pave import twokey

ROOT = pathlib.Path(__file__).resolve().parents[1]
#: Exported so callers name the same file rather than each re-deriving the path.
README = ROOT / "README.md"
CLOSED_MARK = "✅"


def _rows(text: str | None = None):
    """`(key, line)` for every progression row, in table order.

    `text` is injectable so a check can ask what the ratchet does WHEN A MILESTONE
    CLOSES without editing the published table to find out. The alternative is a
    guard nothing exercises until the day it matters, which is the silence this
    repository has paid for repeatedly."""
    source = README.read_text(encoding="utf-8") if text is None else text
    inside = False
    for line in source.splitlines():
        cells = [c.strip() for c in line.split("|")]
        header = len(cells) > 3 and cells[1].lower() == "m" and "milestone" in line.lower()
        if header:
            # **The progression table only.** The first draft matched any row of any
            # table with more than three cells, so the twelve-claims table and the
            # G1-G10 table came too and `latest_closed_milestone()` returned `9` -- a
            # claim number wearing a milestone's clothes.
            inside = True
            continue
        if not inside:
            continue
        if len(cells) < 4:
            break                      # the table ended
        if not cells[1] or set(cells[1]) <= {"-", ":"}:
            continue                   # separator, or one of the part dividers
        yield cells[1].lower().lstrip("0").rstrip(), line


def key(tag: str) -> str:
    """`M04`, `m04`, `04` -> `4`; `M00b` -> `b`. The progression table's own key form.

    Exported because callers were about to re-derive it, and two normalisers that
    disagree about `M00b` is the drift this module exists to prevent."""
    return tag.strip().lower().lstrip("m").lstrip("0") or "0"


def display(row_key: str) -> str:
    """`6` -> `M06`, `6b` -> `M06b`, `b` -> `M00b`. The inverse of `key`, for messages.

    The ratchet reported "Act 0 ... passed 6" -- a bare table key in a sentence that
    opens with an act number, where `6` reads as an act. A guard nobody can parse at a
    glance is a guard that gets dismissed, and this one fires exactly once, at a close,
    with an operator deciding on it."""
    digits = "".join(c for c in row_key if c.isdigit())
    letters = "".join(c for c in row_key if c.isalpha())
    return "M" + (digits.zfill(2) if digits else "00") + letters


def milestone_is_closed(tag: str, text: str | None = None) -> bool:
    """True when `tag` (`M04`, `m04`, `04`) is marked closed in the progression table.

    Raises when the milestone has no row at all: an obligation deferred to a
    milestone that does not exist is deferred to nothing, and returning False
    would make it look satisfied forever."""
    number = key(tag)
    for k, line in _rows(text):
        if k == number:
            return CLOSED_MARK in line
    raise AssertionError(
        f"no progression row for milestone {tag!r}. An obligation deferred to a "
        "milestone the README does not list is deferred to nothing.")


def progression_order(text: str | None = None) -> list:
    """Every milestone key, in the order the table publishes them.

    Derived, not written down: the table already orders the programme, and a second
    ordered list here would be the two-registry drift this module's own docstring
    exists to refuse."""
    return [key for key, _ in _rows(text)]


def latest_closed_milestone(text: str | None = None) -> str | None:
    """The last milestone the table marks closed, or None before any has.

    **This is what a deferral ratchet has to count.** An act's OWNING milestone is
    fixed for its lifetime, so after the first slide it is already in the history and
    forcing it again buys nothing. The milestone that just CLOSED is the entry a
    FRESH deferral adds, and nothing forced it in: an act could be moved from
    `owed_by: M06` to `owed_by: M07` with `deferred_from` untouched, and every
    existing assertion stays green. See `test_a_deferral_is_counted_and_named`."""
    closed = [key for key, line in _rows(text) if CLOSED_MARK in line]
    return closed[-1] if closed else None


#: The states an obligation may hold INSTEAD of naming a milestone (ADR-081 decision 5).
#:
#: **Why the mechanism needs them.** Every obligation used to be owed to a milestone,
#: and `milestone_is_closed` raises for one the table does not list. Row 12 is the last
#: row, so on the day it closes nothing can be owed anywhere, and M11's close wrote
#: `M12` into both registries only because a test needed a listed row (M11 debt 21).
#: A terminal state lets an obligation name its owners and no milestone at all.
#:
#: **PAID has no field here, deliberately.** `recordings.json` already records a paid
#: act as `recorded`, a committed path its own test resolves. No owe in `labels.json`
#: can be paid inside M12, which makes no model calls, so a PAID owe field would be a
#: state with no population and no reader.
RETIRED, UNSCHEDULED = "RETIRED", "UNSCHEDULED"
TERMINAL_STATES = (RETIRED, UNSCHEDULED)


def terminal_state_defects(entry: dict, registry: str, targets: Sequence[str],
                           text: str | None = None) -> list[str]:
    """Why `entry` does not carry what its `state` requires. Empty means it does.

    `registry` is the repo-relative path of the file the entry lives in, and its
    two-key rule decides which seats may retire it. `targets` names the fields that
    point at a milestone in that registry: `re_deferred_to` for an owe, `owed_by` for
    an act. History fields (`originally_due`, `deferred_from`) are not targets, and
    the ratchet keeps reading them.

    - **Either state** names no target milestone. An UNSCHEDULED owe that still says
      `re_deferred_to: M12` is a deferral wearing a terminal state's name, and when
      M12 is open it passes the old teeth too.
    - **UNSCHEDULED** carries `owners`, a non-empty list, and a written `trigger`.
      It is not a pass. The owners are strings, not checked against a seat list,
      because PM owns slides and is not an enforceable seat.
    - **RETIRED** carries `retired_by`, an ADR that exists (`twokey.adr_defect`, the
      same definition the gate uses), and `disposed_by`, exactly two seats, both on
      `registry`'s own two-key rule. That the ADR lands in the same diff is the
      gate's to see, not a hermetic test's.

    `text` is injectable, as everywhere in this module, so a check can ask what a
    state means with every row closed."""
    state = entry.get("state")
    if state not in TERMINAL_STATES:
        return [f"state {state!r} is not one of {list(TERMINAL_STATES)}."]

    defects = []
    for field in targets:
        target = entry.get(field)
        if not target:
            continue
        try:
            where = "closed" if milestone_is_closed(target, text) else "open"
        except AssertionError:
            where = "not in the progression table"
        defects.append(
            f"{state} and `{field}: {target}` ({where}). A terminal state names no "
            "milestone; one that still names a target is a deferral under another name.")

    if state == UNSCHEDULED:
        owners = entry.get("owners")
        if (not isinstance(owners, list) or not owners
                or not all(isinstance(o, str) and o.strip() for o in owners)):
            defects.append(
                f"UNSCHEDULED with owners {owners!r}. An obligation no milestone plans is "
                "held by its owners, or by nobody.")
        trigger = entry.get("trigger")
        if not isinstance(trigger, str) or not trigger.strip():
            defects.append(
                f"UNSCHEDULED with trigger {trigger!r}. Without a written trigger nothing "
                "says when the owners must act.")
    else:
        ref = entry.get("retired_by")
        adr = twokey.adr_defect(ref, ROOT) if isinstance(ref, str) else f"`retired_by` is {ref!r}"
        if adr:
            defects.append(f"RETIRED without its ADR: {adr}")
        seats = entry.get("disposed_by")
        keyed = sorted({s for rule, _ in twokey.triggered([registry]) for s in rule.seats})
        if (not isinstance(seats, list) or len(seats) != 2 or len(set(seats)) != 2
                or not set(seats) <= set(keyed)):
            defects.append(
                f"RETIRED with `disposed_by: {seats!r}`. Retirement takes the two seats "
                f"that disposed it, both on {registry}'s two-key rule {keyed}.")
    return defects

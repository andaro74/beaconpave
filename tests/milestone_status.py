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

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


def milestone_is_closed(tag: str) -> bool:
    """True when `tag` (`M04`, `m04`, `04`) is marked closed in the progression table.

    Raises when the milestone has no row at all: an obligation deferred to a
    milestone that does not exist is deferred to nothing, and returning False
    would make it look satisfied forever."""
    number = tag.strip().lower().lstrip("m").lstrip("0") or "0"
    for line in README.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 3 and cells[1].lower().lstrip("0").rstrip() == number:
            return CLOSED_MARK in line
    raise AssertionError(
        f"no progression row for milestone {tag!r}. An obligation deferred to a "
        "milestone the README does not list is deferred to nothing.")

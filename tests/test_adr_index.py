"""Every ADR is in the index, and an amended ADR's row says it was amended.

**The index was enforced by nobody.** `docs/adr/README.md` is the only list of
the decisions this repository has taken; `CLAUDE.md` sends a reader to it, the
progression table links it, and every "see ADR-0NN" in a docstring assumes it.
Nothing checked that a file under `docs/adr/` had a row there, and the gap was
not hypothetical when this test was written: **ADR-041 and ADR-042 had no row at
all** and the table jumped from 040 to 043. Both are load-bearing --
`.gitattributes`'s own header cites ADR-042 and `pave/history.py`'s
`EVIDENCE_REVISIONS` cites ADR-041 -- so the two decisions a reader is most
likely to arrive at from the code were the two the index did not mention.

That is this repository's most-recorded shape, one level out: a stated protection
(*"every deliberate scope cut is recorded here"*) that is absent for two entries,
which is worse than no index at all, because a reader who finds the table stops
looking.

**The amendment half, and why it is the weaker predicate.** The index's own
header says the superseded sentence stays where it was, marked, *"with the
amendment below it"* -- so an ADR carrying an `## Amendment` heading whose row
reads as though the ADR had always said this is the same defect one field in.
The check here asks only that the row names the ADR as amended.

It deliberately does NOT ask that the row names the LATEST amendment, and that is
measured rather than assumed: of the twelve amended ADRs, **ten** have a row that
does not name their highest-numbered amendment (only ADR-062 and ADR-074 do).
Shipping the stronger predicate would mean ten prose edits in a PR that is
otherwise attestations, or ten exemptions -- and an exemption list is the denylist
shape ADR-043 named as its own weakest decision. Recorded as owed instead, in the
words this repository uses for it: the gap is stated here rather than closed, and
a seat that wants it closed has the measurement to price it.

**What is deliberately not checked in the other direction.** Five rows name ADRs
with no file -- ADR-002, 005, 006, 008 and 010 -- which is the early convention of
recording a one-line cut in the table itself. A row without a file is a decision a
reader can still read; a file without a row is a decision they cannot find. Only
the second is a defect, so only the second is asserted.

Hermetic (G8): committed files, no git, no network, no model.
Owning seat: Platform Engineering (`docs/adr/` per ROLES.md). The debt SPEC/08b
records is owed to PM, which is not an enforced seat in `pave/twokey.py` -- so
this is a test and not a key, which is the honest form of it.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
INDEX = ADR_DIR / "README.md"

#: `ADR-0NN` at the start of a file name. The slug after it is free.
ADR_FILE = re.compile(r"^(ADR-\d{3})-")

#: A table row opening with an ADR id. Anchored at column 0 so a mention of an
#: ADR inside another row's prose is not read as that ADR having a row.
ADR_ROW = re.compile(r"^\|\s*(?:\*\*)?(ADR-\d{3})(?:\*\*)?\s*\|")

#: An amendment heading, as ADR-051's shape: `## Amendment N -- ...` or bare.
AMENDMENT = re.compile(r"^## Amendment\b", re.MULTILINE)

#: What a row must say for an amended ADR. Case-insensitive, and a stem rather
#: than a phrase: the index uses both *"amended by 013"* and *"amended in place"*
#: and **"Amendment 2, M08:"**, and pinning any one of those wordings would be red
#: on the other two.
AMENDED = re.compile(r"amend", re.IGNORECASE)

INDEX_TEXT = INDEX.read_text(encoding="utf-8")

#: `{ADR id: the row}` for every row in the index.
ROWS = {}
for _line in INDEX_TEXT.splitlines():
    _match = ADR_ROW.match(_line)
    if _match:
        ROWS.setdefault(_match.group(1), _line)

#: `{ADR id: path}` for every ADR file.
FILES = {m.group(1): p for p in sorted(ADR_DIR.glob("ADR-*.md"))
         if (m := ADR_FILE.match(p.name))}

#: The ADRs carrying at least one `## Amendment` heading, and how many.
AMENDED_FILES = {
    adr: len(AMENDMENT.findall(path.read_text(encoding="utf-8")))
    for adr, path in FILES.items()
    if AMENDMENT.search(path.read_text(encoding="utf-8"))
}


def test_the_scan_found_the_index_and_the_files():
    """**The vacuity guard.** A regex that stops matching -- the table gains a
    column, the file naming changes, `README.md` moves -- makes every assertion
    below green over an empty set, which is what four of ADR-042's ten checks did
    on their first implementation.

    Both halves, because they fail apart: the files could be found and the rows
    not, which reports every ADR unindexed, and the rows could be found and the
    files not, which reports nothing at all."""
    assert len(FILES) >= 60, f"only {len(FILES)} ADR files found under {ADR_DIR}"
    assert len(ROWS) >= 60, f"only {len(ROWS)} index rows parsed out of {INDEX.name}"
    assert AMENDED_FILES, "no amended ADR found; the `## Amendment` heading shape moved"


@pytest.mark.parametrize("adr", sorted(FILES), ids=sorted(FILES))
def test_every_adr_has_an_index_row(adr: str):
    """`docs/adr/README.md` is where a reader is sent to find a decision. A file
    with no row is a decision that exists and cannot be found from the one place
    that claims to list them all."""
    assert adr in ROWS, (
        f"{FILES[adr].name} has no row in docs/adr/README.md. The index says every "
        "deliberate scope cut is recorded there, so an ADR missing from it is a cut "
        "a reader who trusts the index will conclude was never taken.")


@pytest.mark.parametrize("adr", sorted(AMENDED_FILES), ids=sorted(AMENDED_FILES))
def test_an_amended_adrs_row_says_it_was_amended(adr: str):
    """The index's own header: the superseded sentence stays, marked, *"with the
    amendment below it"*. A row that reads as though the ADR had always said this
    is worth less than one that shows where it was corrected."""
    row = ROWS.get(adr, "")
    assert AMENDED.search(row), (
        f"{FILES[adr].name} carries {AMENDED_FILES[adr]} `## Amendment` heading(s) and "
        f"its index row does not say it was amended. A reader takes the row for the "
        f"whole decision.\n\nrow: {row[:200]}")


def test_the_weaker_predicate_is_the_one_that_ships_and_the_gap_is_measured():
    """**The owed half, as a number rather than a sentence** (M08b PR 4).

    The check above accepts any row that says the ADR was amended. It does not ask
    that the row names the LATEST amendment, so ADR-035's row saying "amended" once
    covers eleven. That gap is real; this asserts the size of it, so a reader is
    told what the green check above does not buy, and so the day somebody closes it
    the number here has to move in the same diff.

    The direction is a ratchet: fewer stale rows is fine and more is not."""
    stale = []
    for adr in sorted(AMENDED_FILES):
        text = FILES[adr].read_text(encoding="utf-8")
        numbered = [int(n) for n in re.findall(r"^## Amendment\s+(\d+)", text, re.MULTILINE)]
        if not numbered:
            # `## Amendment` with no number -- the row cannot name a number either.
            stale.append(adr)
            continue
        if not re.search(rf"[Aa]mendment\s*{max(numbered)}\b", ROWS.get(adr, "")):
            stale.append(adr)
    assert len(stale) <= 10, (
        f"{len(stale)} amended ADRs have a row that does not name their latest "
        f"amendment: {stale}. Measured at 10 when this was written; a higher number "
        "means the stronger predicate got further out of reach in a diff that did not "
        "say so.")

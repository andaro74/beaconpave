"""M09's PR cap, and the one breach of it, held to each other.

**Why this file exists.** SPEC/09's *Bounded* says *"cap six PRs"* and names the
six; M09 took a seventh. ADR-075 amendment 4 records that as a breach against the
rule as written, and the rule is deliberately **not** edited to match what
happened — a cap rewritten to fit the outcome is a baseline reset one document up,
and it is the move this whole milestone refuses.

That decision is only worth the sentence if something enforces it. Nothing did:
no test in this repository read the cap, the PR list, or any breach record, so
*"the cap stays six and the breach is recorded against it"* could have become
*"the cap is seven"* in a later diff with the suite green, and the record would
have quietly become a description of a rule nobody broke.

So this file asserts the two halves against each other, in both directions:

- the cap literal is still **six** and the planned list is still the six, so the
  number cannot be raised to absorb a breach;
- every PR named in *Bounded* beyond that list carries a citation to an ADR
  amendment, and that amendment exists and actually records a breach naming the
  same PR, so a breach cannot be taken silently.

Owning seats: Platform Engineering (the spec) · PM (the cap).
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC" / "09-rules-registry-and-the-disposition.md"
ADR = ROOT / "docs" / "adr" / (
    "ADR-075-m09-is-two-milestones-and-the-disposition-ships-without-a-deploy.md")

#: The plan, as written before the milestone ran. Not a prediction and not a
#: running total: the number this file exists to stop anyone quietly raising.
PLANNED_CAP = 6
PLANNED_PRS = ("PR 1", "PR 1b", "PR 2", "PR 4", "PR 4b", "PR 5")

#: Named in *Bounded* and deliberately absent from the plan: PR 3's slot was
#: vacated by the DMA rename leaving the milestone and spent on PR 4b. It appears
#: only in the sentence saying it does not exist, so it is not a PR beyond the cap.
VACATED = {"PR 3"}

#: `six`, spelled. The spec writes the cap as a word, and a test that accepted
#: either would accept a digit swapped in beside the word.
CAP_WORDS = {6: "six", 7: "seven", 8: "eight"}


def _bounded() -> str:
    """The *Bounded* section, which is where the cap and any breach both live."""
    body = SPEC.read_text(encoding="utf-8").split("\n## Bounded\n", 1)[1]
    return body.split("\n## ", 1)[0]


def test_the_cap_is_still_six_and_still_names_the_same_six_prs():
    """**The number is not raised to absorb the breach.**

    ADR-075 amendment 4 takes a seventh PR and records it *against* this sentence.
    If the sentence moves to seven, the amendment stops being a breach record and
    becomes a description of a rule nobody broke — and the milestone loses the one
    artifact that says its plan was wrong."""
    bounded = _bounded()
    assert f"Cap: {CAP_WORDS[PLANNED_CAP]} PRs" in bounded, (
        f"SPEC/09's cap is no longer '{CAP_WORDS[PLANNED_CAP]} PRs'. The cap is the "
        f"plan as written; a breach is recorded against it, never absorbed into it. "
        f"A cap edited to match what happened is a baseline reset one document up.")
    for pr in PLANNED_PRS:
        assert re.search(rf"\b{re.escape(pr)}\b", bounded), (
            f"{pr} is no longer named in Bounded's list of the six. The list is the "
            f"plan; rewriting it hides the difference between what was planned and "
            f"what was taken.")


def test_every_pr_beyond_the_cap_cites_an_amendment_that_records_it():
    """**And a breach cannot be taken silently.**

    The other direction. `Bounded` naming a PR outside the planned six is a breach
    by definition, and the only acceptable form is one that cites a decision
    record — which must exist, and must name the same PR. A bullet saying "we took
    another one" with no citation is the slide this milestone already paid for
    once, in the DMA rename's fifth."""
    bounded = _bounded()
    named = set(re.findall(r"\bPR \d+b?\b", bounded))
    beyond = sorted(named - set(PLANNED_PRS) - VACATED)
    assert beyond, (
        "Bounded names no PR beyond the planned six, but ADR-075 amendment 4 "
        "records a seventh. Either the acknowledgement was removed from the spec — "
        "leaving the breach recorded in one document and invisible in the one that "
        "set the bound — or this list is stale.")

    adr = ADR.read_text(encoding="utf-8")
    for pr in beyond:
        # Whitespace-normalised first: the citation wraps across a line in the
        # spec, and a regex that cannot cross a newline would report "cites no
        # amendment" over a bullet that cites one — a false red that the next
        # reader fixes by deleting the assertion.
        sentence = next((re.sub(r"\s+", " ", bullet) for bullet in bounded.split("\n- ")
                         if re.search(rf"\b{re.escape(pr)}\b", bullet)), "")
        clause = re.search(r"\(ADR-075 amendment (\d+)\)", sentence)
        assert clause, (
            f"{pr} is named in Bounded beyond the cap and cites no amendment. A PR "
            f"over the cap without a decision record is the cap being ignored "
            f"rather than breached.")
        heading = f"## Amendment {clause.group(1)} —"
        assert heading in adr, (
            f"{pr} cites ADR-075 amendment {clause.group(1)}, which does not exist.")
        record = adr.split(heading, 1)[1].split("\n## Amendment ", 1)[0]
        assert pr.lower() in record.lower() or "seventh" in record.lower(), (
            f"ADR-075 amendment {clause.group(1)} does not name {pr}. The citation "
            f"points at a record about something else.")
        assert "breach" in record.lower(), (
            f"ADR-075 amendment {clause.group(1)} does not record a breach. An "
            f"amendment that merely mentions the PR is a note, not a record that "
            f"the plan was exceeded.")


def test_the_breach_record_carries_the_evidence_that_it_moved_no_number():
    """The breach was taken on a measured argument — no number moved, no new
    capability — and that argument is the whole of why it was acceptable. If the
    evidence goes, what is left is a precedent for taking an eighth."""
    record = ADR.read_text(encoding="utf-8").split("## Amendment 4 —", 1)[1]

    # **The evidence TABLE, row by row — not the substrings anywhere in the
    # record.** The first version of this asked whether `"5200"` appeared
    # somewhere in the amendment, and the deletability audit measured what that
    # bought: delete the row `| gates.budgets.p95_ms | **5200**, unmoved |` and the
    # whole suite stayed green at 4210, because the closing paragraph mentions
    # 5200 for a different reason. A check satisfied by a word appearing elsewhere
    # is the substring defect this milestone has now paid for three times.
    rows = {}
    for line in record.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] and not cells[0].startswith("---"):
            rows[cells[0]] = cells[1]

    expected = {
        "`gates.budgets.p95_ms`": "5200",
        "manifest diff": "empty",
        "`milestones/` diff": "empty",
        "`evals/history/` diff": "empty",
        "new capability": "none",
        "tests added": "+4",
    }
    for label, value in expected.items():
        assert label in rows, (
            f"the breach record's evidence table no longer has a row for {label}. "
            f"The breach rests on the measurement that it changed nothing; without "
            f"the measurement the record is a permission slip.")
        assert value in rows[label], (
            f"the breach record says {label} is {rows[label]!r}, not {value!r}. "
            f"Either the evidence moved — in which case the breach needs re-arguing "
            f"rather than re-wording — or the record has drifted from the diff.")

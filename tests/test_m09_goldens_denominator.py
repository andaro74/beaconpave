"""
The goldens denominator is 25, the disclosure pack is not in it, and
`disclosure-004`'s reservation is withdrawn.

**Why the denominator is pinned by name and not by a number.** Adding a
disclosure case to `services/highlights-agent/evals/golden/cases.yaml` would make
every future `N/25` an `N/26` and make M09's count incomparable to `m00b` through
`m08b` for a reason that has nothing to do with any system under test. A count
alone cannot see that: 25 stays 25 if a disclosure case is added and a golden case
is dropped in the same diff, and the suite would go on reporting a comparable
number over a case set that had changed twice. So the refusal is on the **id**,
by name, and the count is asserted beside it (ADR-075 decision 4).

`tests/test_contracts.py::test_golden_set_is_the_size_the_progression_table_claims`
already asserts the size. This file asserts the thing that check cannot see, and
says so rather than duplicating it silently.

**`disclosure-004`'s reservation, in FOUR places rather than the two ADR-075 D4
named.** The golden file said the id was *reserved for M07 — the gap is the
reservation*; `evals/golden/README.md` repeated it; `answer.schema.json`'s
`ai_disclosure` description carries *"Null until M07 disposes that rule"*; and
**`templates/agent-tools/evals/golden/README.md.tmpl` carries it too**, which
every service that does not exist yet inherits. The fourth was found by running
the scaffold's round-trip check rather than by reading, and it is arguably the
worst: the other three are stale text about one rule, and this one hands the
stale reservation to every future team.

M07 is the guardrail milestone and stopped meaning anything here three
renumberings ago; a reservation that outlives the milestone it names is a stated
protection that is absent, which CLAUDE.md ranks worse than a missing one because
it stops anyone looking for the real one.

It is **withdrawn by name, not filled**, and the id is **not reused**: the
disclosure pack numbers from 101, so no reader joining the two files can conclude
the reserved case was quietly filled.

**Two of the four are withdrawn here and two are dated to the fix's PR, and the
split is a digest cascade rather than a preference.**
`milestones/M08/context-census.json` digests the golden cases file and
`answer.schema.json`; `milestones/M08b/fresh-join.json` digests the cases file
and the census record. So editing either of those two sites re-produces **three**
committed records under `milestones/`, which this milestone's Definition of done
reserves to the PR that moves them anyway — and `answer.schema.json` is
additionally **model-facing**, rendered into both arms' prompts through
`{schema}`, which SPEC/09 constraint 2 reserves to the fix.

`evals/golden/README.md` and its template are digested by nothing, so both are
withdrawn here — together, because the round-trip check couples them byte for
byte and admits no other order (ADR-075 amendment 2).

This file asserts what has landed and **names what has not, with its PR**, rather
than asserting a withdrawal that has not happened or staying silent about it.

Hermetic (G8), zero model calls.

Owning seats: AI Quality (the denominator) · Platform Engineering · Security.
"""
from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
GOLDEN_README = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "README.md"
PACK = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "cases.yaml"
PACK_README = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "README.md"
ANSWER_SCHEMA = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"

#: The denominator every recorded goldens score is reported against, from `m00b`
#: onward.
DENOMINATOR = 25

#: The prefix the disclosure suite's ids carry, and the one the golden file
#: refuses.
DISCLOSURE_PREFIX = "disclosure"

#: The id the golden file reserved and nothing may reuse — here, in the pack, or
#: anywhere else.
WITHDRAWN_ID = "disclosure-004"

#: Wording from the withdrawn reservation. Matched as fragments rather than as a
#: whole sentence: a reservation restated in different words is the same stated
#: protection, and an exact-sentence check would pass on a paraphrase.
RESERVATION_FRAGMENTS = (
    "is reserved for M07",
    "the gap is the reservation",
    "deliberately absent",
    "M07 adds it as the",
)


def _cases(path: pathlib.Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def test_the_golden_file_holds_exactly_twenty_five_cases():
    """The number, asserted here beside the id refusal it cannot replace."""
    cases = _cases(GOLDENS)
    assert len(cases) == DENOMINATOR, (
        f"the golden file holds {len(cases)} cases, not {DENOMINATOR}. Every recorded "
        "score from m00b onward is reported as N/25; a suite that changes size makes a "
        "percentage move with no system under test moving.")


def test_no_disclosure_case_is_in_the_golden_file_by_name():
    """**By name, not by number.** A count cannot see a disclosure case added and
    a golden case dropped in one diff — the denominator would hold at 25 while
    the case set changed twice, and the number would go on being reported as
    comparable."""
    offenders = [c["id"] for c in _cases(GOLDENS)
                 if str(c.get("id", "")).startswith(DISCLOSURE_PREFIX)]
    assert not offenders, (
        f"the golden file carries {offenders}. The disclosure pack is its own SUITE and "
        "is not folded into the twenty-five (ADR-075 decision 4): it lives at "
        f"{PACK.relative_to(ROOT)}. Publishing an N/26 anywhere is what this refuses.")


def test_the_pack_is_a_separate_file_and_its_ids_are_all_disclosure_prefixed():
    """The other half of the pin: the refusal above is only meaningful while the
    pack's ids actually carry the prefix it refuses. A pack renamed to
    `disc-101` would leave the golden file's guard true and empty."""
    cases = _cases(PACK)
    assert PACK.resolve() != GOLDENS.resolve()
    assert cases, "the disclosure pack holds no cases"
    for case in cases:
        assert str(case["id"]).startswith(DISCLOSURE_PREFIX), (
            f"pack case {case['id']!r} does not carry the {DISCLOSURE_PREFIX!r} prefix, so "
            "the golden file's by-name refusal would not catch it if it were folded in.")


def test_the_two_case_sets_share_no_id():
    ids_golden = {c["id"] for c in _cases(GOLDENS)}
    ids_pack = {c["id"] for c in _cases(PACK)}
    assert not ids_golden & ids_pack, f"shared id(s): {sorted(ids_golden & ids_pack)}"


def test_disclosure_004_is_used_by_no_case_anywhere():
    """The id is not reused, so that no reader joining the two files concludes
    the reserved case was quietly filled. The pack numbers from 101 for exactly
    this reason."""
    for path in (GOLDENS, PACK):
        ids = [c["id"] for c in _cases(path)]
        assert WITHDRAWN_ID not in ids, (
            f"{path.relative_to(ROOT)} carries {WITHDRAWN_ID!r}. The reservation was "
            "withdrawn, not filled (ADR-075 decision 4) — the id stays unused.")


def test_the_golden_readme_and_its_template_are_withdrawn_together():
    """**The reservation was in FOUR places, not the two ADR-075 D4 named.**

    The fourth is `templates/agent-tools/evals/golden/README.md.tmpl`, which
    every service that does not exist yet inherits — and which
    `tests/test_scaffold.py::test_the_golden_readme_round_trips_to_the_reference`
    couples byte-for-byte to the reference README. Found by running that check
    rather than by reading, and it is arguably the worst of the four: the other
    three are stale text about one rule, and this one hands the stale reservation
    to every future team.

    The coupling admits no order but *both in one diff*, which is why they are
    asserted together here rather than in two tests that could pass separately.
    """
    reference = GOLDEN_README.read_text(encoding="utf-8")
    template = (ROOT / "templates" / "agent-tools" / "evals" / "golden" /
                "README.md.tmpl").read_text(encoding="utf-8")
    heading = "### `disclosure-004`'s reservation, withdrawn"
    assert heading in template, (
        "the scaffold template carries no withdrawal section. Dropping it rather than "
        "withdrawing restores the reservation by silence for every future service.")
    # Like the reference, the template QUOTES the withdrawn wording in order to
    # withdraw it, so the check is that no fragment stands as the file's own claim
    # ahead of the withdrawal — not that the words are absent.
    before = template.split(heading)[0]
    standing = [f for f in RESERVATION_FRAGMENTS if f in before]
    assert not standing, (
        f"the scaffold template states the reservation as its own claim: {standing}. "
        "Every service rendered from it inherits that sentence.")
    # And the two stay in lock-step. The round-trip check couples them byte for
    # byte after substitution, so neither can be corrected alone — asserted here
    # so that the coupling is visible from the milestone that had to discover it.
    section = reference.split(heading)[1].split("## The rule that matters most")[0]
    assert section in template, (
        "the reference and the template have drifted inside the withdrawal section.")


def test_the_golden_readme_carries_no_reservation_sentence():
    """Withdrawn here, in the one committed site that is digested by nothing."""
    text = GOLDEN_README.read_text(encoding="utf-8")
    live = [f for f in RESERVATION_FRAGMENTS if f in text]
    # The README quotes the withdrawn wording in order to withdraw it, so the
    # check is that the quotation is inside the withdrawal section rather than
    # standing as the file's own claim. Naming the section is what makes a
    # re-introduction elsewhere in the file visible.
    withdrawal = text.split("### `disclosure-004`'s reservation, withdrawn", 1)
    assert len(withdrawal) == 2, (
        "the golden README no longer carries the withdrawal section. Deleting the "
        "withdrawal restores the reservation by silence.")
    before = withdrawal[0]
    assert not [f for f in RESERVATION_FRAGMENTS if f in before], (
        f"the golden README states the reservation as its own claim before withdrawing "
        f"it: {[f for f in RESERVATION_FRAGMENTS if f in before]}")
    assert live, (
        "the withdrawal section quotes none of the withdrawn wording. A withdrawal that "
        "does not say what it withdraws leaves the next reader unable to tell whether "
        "the sentence was retired or simply lost.")
    assert "../disclosure/cases.yaml" in text, (
        "the README does not say where the disclosure cases actually live, which is the "
        "half of the withdrawal that replaces the reservation with a fact.")


def test_the_two_digested_sites_are_named_with_their_pr_rather_than_left_silent():
    """**The sites this PR does not withdraw, asserted as dated rather than
    forgotten.**

    `cases.yaml`'s header comment and `answer.schema.json`'s `ai_disclosure`
    description both still carry the withdrawn wording, because editing either
    re-produces three committed records under `milestones/` and the second is
    model-facing text SPEC/09 constraint 2 reserves to the fix.

    A debt that is dated in a document and invisible in the tree is one the next
    reader has to already know about. This asserts the tree carries the pointer,
    so that the day the fix's PR withdraws both sites, this test is what tells
    that PR to update it — and until then, that nobody concludes from the
    README's withdrawal that all four sites are done.

    The pointer lives in the **pack's** README rather than the golden one,
    because the golden README is round-tripped byte for byte against the scaffold
    template and M09's dated debts are not something every future service should
    inherit."""
    readme = PACK_README.read_text(encoding="utf-8")
    for name in ("cases.yaml", "answer.schema.json"):
        assert name in readme, (
            f"the pack README no longer names {name} as a site still carrying the "
            "withdrawn wording. Either it was withdrawn there — in which case update "
            "this test and the README in that diff — or the pointer was lost.")
    # And the two sites really do still carry it, so the pointer is not stale.
    still_carrying = [
        p.relative_to(ROOT) for p in (GOLDENS, ANSWER_SCHEMA)
        if any(f in p.read_text(encoding="utf-8") for f in RESERVATION_FRAGMENTS)
        or "Null until M07" in p.read_text(encoding="utf-8")
    ]
    assert len(still_carrying) == 2, (
        f"{len(still_carrying)} of the two dated sites still carry the withdrawn wording: "
        f"{still_carrying}. If the fix's PR withdrew them, delete this test and the "
        "README's pointer in that diff — a pointer to a debt that is paid is the same "
        "stale sentence one milestone later.")

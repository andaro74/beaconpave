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

import json
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
#: Each fragment must be specific to the RESERVATION. A bare "deliberately
#: absent" was in the first version and matched the assert-vocabulary table's
#: description of `cited_titles_empty` — *"the subject is deliberately absent from
#: the catalog"* — which has nothing to do with `disclosure-004`. A guard that
#: fires on unrelated prose is one the next editor routes around by rewording the
#: innocent sentence.
RESERVATION_FRAGMENTS = (
    "is reserved for M07",
    "the gap is the reservation",
    "`disclosure-004` is deliberately absent",
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
    """**The reservation was in FOUR sites, not the two ADR-075 D4 named.**

    The fourth is `templates/agent-tools/evals/golden/README.md.tmpl`, which every
    service that does not exist yet inherits and which the scaffold's round-trip
    check couples byte for byte to the reference README.

    **And what replaces it must be true for a SCAFFOLDED service, which round 1
    (Service Team) measured that the first version was not.** That version said
    *25 cases*, named a test hard-scoped to `highlights-agent`, and linked
    `../disclosure/cases.yaml` — a dead link in a scaffold, a case count the team
    is being told to change, and a protection claim that does not cover them. A
    template is read by teams whose file it does not describe, so the withdrawal
    says only what is true of any golden set, and the archaeology moved to the
    pack's own README, which is not templated."""
    reference = GOLDEN_README.read_text(encoding="utf-8")
    template = (ROOT / "templates" / "agent-tools" / "evals" / "golden" /
                "README.md.tmpl").read_text(encoding="utf-8")
    for text, name in ((reference, "reference"), (template, "template")):
        standing = [f for f in RESERVATION_FRAGMENTS if f in text]
        assert not standing, f"the golden {name} still states the reservation: {standing}"
        assert "withdrawn" in text and "disclosure-004" in text, (
            f"the golden {name} dropped the withdrawal instead of making it — which "
            "restores the reservation by silence")
    # Nothing service-specific, and no claim a scaffolded team cannot check.
    for leak in ("25 cases", "../disclosure/cases.yaml", "numbers from 101",
                 "test_m09_goldens_denominator", "MER-AI-0001", "highlights-agent"):
        assert leak not in template.split("## The rule that matters most")[0], (
            f"the scaffold template's withdrawal section carries {leak!r}, which is not "
            "true of, or checkable by, a service rendered from it")


#: The two model-facing sites the fix's PR edits. Everything downstream of them
#: is DERIVED below rather than listed.
MODEL_FACING_SITES = (
    "services/highlights-agent/evals/golden/cases.yaml",
    "services/highlights-agent/evals/answer.schema.json",
    "services/highlights-agent/gateway_client.py",
)


def records_moved_by(seeds) -> set:
    """Every committed record that must be re-produced when `seeds` move.

    **A transitive closure, because the records digest each other.**
    `milestones/M08b/fresh-join.json` carries
    `milestones/M08/context-census.json` in its own `inputs_sha256`, so moving an
    input moves the census, and moving the census moves the join. A hand-listed
    set stops at the first hop.
    """
    digests = {}
    unreadable = []
    for record in ROOT.glob("milestones/**/*.json"):
        try:
            doc = json.loads(record.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            # **Fail LOUD.** This was `continue`, and two seats measured what that
            # bought: a record digesting a model-facing file was invisible to the
            # whole suite if it carried one trailing comma. A closure that skips
            # what it cannot read reports a smaller cascade than the truth, and
            # the number it reports is the one PR 4's merge condition rests on.
            unreadable.append(f"{record.relative_to(ROOT).as_posix()}: {exc}")
            continue
        inputs = doc.get("inputs_sha256") if isinstance(doc, dict) else None
        if isinstance(inputs, dict):
            digests[record.relative_to(ROOT).as_posix()] = set(inputs)
    assert not unreadable, (
        "record(s) under milestones/ could not be parsed, so the cascade below is "
        "computed over less than the tree:\n  " + "\n  ".join(unreadable))

    moved, frontier = set(), set(seeds)
    while frontier:
        step = {rec for rec, ins in digests.items()
                if rec not in moved and ins & frontier}
        moved |= step
        frontier = step
    return moved


def test_the_closures_seeds_are_the_files_the_fix_actually_edits():
    """**The hand-list moved up a level; this is what pins it there.**

    `records_moved_by` is a real transitive closure, but its seeds were three
    hand-written strings that nothing asserted. Two seats measured the same
    thing: truncating `MODEL_FACING_SITES` to `cases.yaml` alone left the
    computed set identical and the suite green, because all five records happen
    to be reachable through that one file. Latent is not fixed — the day a record
    digests only the prompt, a seed deletion silently shrinks the cascade.

    The seeds are the files the fix edits, and this repository already names
    those in a second place: the three `PRE_FIX_*_SHA256` digests in
    `tests/test_m09_prompt_delta.py` are exactly the model-facing surface PR 4
    moves. Asserting the two agree makes each the other's witness."""
    assert set(MODEL_FACING_SITES) == {
        "services/highlights-agent/evals/golden/cases.yaml",
        "services/highlights-agent/evals/answer.schema.json",
        "services/highlights-agent/gateway_client.py",
    }, (
        f"the closure's seeds are {sorted(MODEL_FACING_SITES)}. They are the files PR 4 "
        "edits; adding or removing one changes which records the Definition of done "
        "must name, so it is a decision rather than a list edit.")
    for seed in MODEL_FACING_SITES:
        assert (ROOT / seed).is_file(), f"seed {seed} does not exist"


def test_the_records_the_fix_moves_are_derived_and_not_listed():
    """**Five records, and the two counts before it were both wrong.**

    ADR-075 amendment 1 fact 3 named **one** — `context-census.json`. This PR's
    own correction named **three**, and the Platform Engineering seat measured
    **five**: `milestones/M08/rescore-join.json` and
    `milestones/M08b/residual-attribution.json` were in neither list.

    Both errors are the same shape, and it is the shape this repository has paid
    for before: a set of consequences written down by hand, one hop deep, in a
    document. The Definition of done that rested on it said *"and nothing else
    under those directories moves"*, which was unsatisfiable by two records — a
    clause rewritten in this PR **to fix exactly that defect** and still wrong.

    So the set is computed. A sixth record lands on this the day somebody writes
    it, rather than the day a PR goes red for a reason no clause named."""
    moved = records_moved_by(MODEL_FACING_SITES)
    assert moved == {
        "milestones/M08/context-census.json",
        "milestones/M08/rescore-join.json",
        "milestones/M08/residual-differential.json",
        "milestones/M08b/fresh-join.json",
        "milestones/M08b/residual-attribution.json",
    }, (
        f"the fix's record cascade is now {sorted(moved)}. SPEC/09's PR 4 paragraph and "
        "its Definition-of-done clause name a set; if this one differs, the spec is out "
        "of date and PR 4 cannot satisfy the clause. Update both in the same diff.")


def test_the_spec_names_every_record_the_cascade_moves():
    """The document and the computation agree, or the document is the finding.

    This is the half that makes the derivation useful: computing the set is worth
    nothing if the Definition of done still lists a different one."""
    spec = (ROOT / "SPEC" / "09-rules-registry-and-the-disposition.md").read_text(
        encoding="utf-8")
    for record in sorted(records_moved_by(MODEL_FACING_SITES)):
        assert record in spec, (
            f"{record} is re-produced by the fix and SPEC/09 never names it. A PR cannot "
            "collect keys for a record no clause told it to move.")


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

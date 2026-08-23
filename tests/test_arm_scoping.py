"""Every protection ADR-041 adds, each with a tree where it actually fires.

**This file exists because six of ten planted weakenings survived a fully
registered commit.** Not one of them was caught by a digest, a two-key rule or a
pin — each removed a check that is unreachable on an honest tree, so deleting it
produced no failure anywhere. `pave adversarial run` stayed PASS, `gate decide`
stayed exit 0, and the suite count did not move.

That is ADR-039's fault class ("two lines no test could reach") landing on the
protections of the mechanism written to close a different instance of it. So the
rule ADR-041 states is general: *a protection ships with a test that builds the
tree where it fires.* A two-key path on a check nothing runs is the "stated
protection is worse than an absent one" pattern this repository has now recorded
eight times — the attestation makes the deletion expensive and nothing makes it
visible.

Two-key (`ai-quality`, `security`) for exactly that reason: the tests below and
the rules in `pave/twokey.py` are two halves of one control, and a protection
whose test is cheaper to delete than the thing it protects is not a protection.

Owning seats: AI Quality (the instrument and its pins) · Security / Red Team
(what a probe passing means).
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest
import yaml

from evals.adversarial import (
    ASKED_KEY,
    INFRA,
    OUT_OF_SCOPE,
    PASS,
    asked_from,
    score_corpus,
    score_one,
    tally,
)
from pave.floors import ASKED_FLOOR, G4_SCORED_CASE_FLOOR, asked_floor

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROBES = yaml.safe_load((ROOT / "quality" / "adversarial" / "probes.yaml").read_text(encoding="utf-8"))
SEMANTICS = ROOT / "quality" / "adversarial" / "g4-semantics.yaml"

#: The three arms whose evidence the L5 lane decides on, and the append-only
#: entry each of them published on the day.
ARMS = {
    "m00b": ("milestones/M00b/probes-run.json", "evals/history/m00b-adversarial.json"),
    "m01": ("milestones/M01/probes-run.json", "evals/history/m01-adversarial.json"),
    "m04": ("milestones/M04/probes-run.json", "evals/history/m04-adversarial.json"),
}

BLOCKED = {"guardrail_blocked": True, "policy_denied": False, "mechanism": "guardrail",
           "assessed": ["PROMPT_ATTACK"], "channels": ["question"],
           "audit_record": "2026-08-22/s/x.json"}


def _probe(pid="ADV-001"):
    return {"id": pid, "pass_when": "guardrail_blocked_or_denied_and_logged",
            "channels": ["question", "answer"]}


# --- the manifest reader, every shape ----------------------------------------
#
# A malformed manifest read as an empty set scores EVERY probe out of scope and
# reports PASS over an empty corpus. Measured before this test existed: `[]`, a
# string, an object and a number all did exactly that.

@pytest.mark.parametrize("raw", [
    [], "ADV-001", {"ADV-001": True}, 0, True, None,
    ["ADV-001", "ADV-001"],                       # a run asks a probe or it does not
    ["ADV-001", 7], ["ADV-001", None], ["ADV-001", ""], ["ADV-001", ["ADV-002"]],
])
def test_a_manifest_that_cannot_be_read_is_an_error_never_an_empty_question_set(raw):
    asked, error = asked_from({ASKED_KEY: raw})
    assert asked is None and error, f"{raw!r} read as a question set instead of an error"
    result = score_one(_probe(), BLOCKED, asked, error)
    assert result.result == INFRA, (
        f"{raw!r} produced {result.result}. A field deciding WHAT GETS SCORED must never have "
        "'unparseable' resolve to 'the question was never put' — that scores an empty corpus "
        "as a pass.")


def test_a_document_with_no_manifest_puts_every_probe_in_scope():
    """Fail-closed, and it is what the three committed arms relied on before they
    were backfilled. Absent must mean "this arm asked everything", never "this arm
    asked nothing"."""
    asked, error = asked_from({"ADV-001": BLOCKED})
    assert (asked, error) == (None, None)
    assert score_one(_probe(), None, asked, error).result == INFRA


def test_a_probe_the_manifest_names_and_the_file_does_not_answer_is_infra():
    """**The clause that makes deleting an observation loud.**

    Under the design this replaced, scope was declared by the probe — so deleting
    the observation made the declaration TRUE and the probe retired silently.
    Here the record contradicts its own manifest and the lane blocks."""
    asked, error = asked_from({ASKED_KEY: ["ADV-001"]})
    result = score_one(_probe("ADV-001"), None, asked, error)
    assert result.result == INFRA, "a deleted observation retired a probe instead of blocking"
    assert result.result != OUT_OF_SCOPE


def test_a_probe_the_file_answers_for_but_the_manifest_omits_is_infra():
    """The inverse, which the first version of this rule left out.

    Crediting the manifest over the evidence lets one edited line retire a probe
    whose observation is sitting right there."""
    asked, error = asked_from({ASKED_KEY: ["ADV-002"]})
    result = score_one(_probe("ADV-001"), BLOCKED, asked, error)
    assert result.result == INFRA, (
        "a file answering for a probe its manifest omits was credited to the manifest")
    assert "contradicts its own manifest" in result.reason


def test_a_probe_the_arm_never_asked_is_out_of_scope_and_never_a_pass():
    asked, error = asked_from({ASKED_KEY: ["ADV-002"]})
    result = score_one(_probe("ADV-001"), None, asked, error)
    assert result.result == OUT_OF_SCOPE
    assert not result.unearned, "an unasked probe must not carry an honesty mark it did not earn"


# --- the anchor: the entry the arm published ---------------------------------

def test_every_arms_manifest_covers_what_its_recorded_entry_scored():
    """**The one protection that is not a mirror of the number under attack.**

    Every other check — `expected_scored`, the floors, the per-probe map, the
    exact-set pins — is an equality against a value the same diff writes, so the
    PR shape ADR-041 itself requires is the shape that moves them all together.
    Measured: `m04` 7/10 -> 7/9, 70.0% to 77.8%, lane PASS, gate exit 0, suite
    green.

    `evals/history/` is append-only by CLAUDE.md and cannot be re-derived from a
    trimmed observation file, so an arm that stops asking what it once answered
    for contradicts a published row.

    **Superset, never equality**: a later re-run may ask more and never fewer.

    Before this existed only `m01` was covered, by accident —
    `test_exactly_one_probe_moved_and_it_is_the_one_marked_unearned` reads
    `m01-adversarial.json` for an unrelated ADR-038 reason. `m00b`'s and `m04`'s
    entries were read by no code at all, which is why both rounds' surviving
    plants chose `m04`."""
    checked = 0
    for tag, (obs_path, entry_path) in ARMS.items():
        doc = json.loads((ROOT / obs_path).read_text(encoding="utf-8"))
        entry = json.loads((ROOT / entry_path).read_text(encoding="utf-8"))
        asked, error = asked_from(doc)
        assert error is None, f"{tag}: {error}"
        assert asked is not None, f"{tag}: no manifest — it must record what it asked"
        recorded = {c["id"] for c in entry["cases"]}
        assert recorded <= asked, (
            f"{tag}: its published entry scored {sorted(recorded - asked)} and its manifest no "
            "longer says it asked them. An arm cannot stop having asked what it answered for: "
            "that is how a failing probe leaves a denominator while the pass count holds.")
        checked += 1
    assert checked >= 3, (
        f"only {checked} arm(s) checked. A loop that covers nothing reports success identically "
        "to one that covers everything — `rules_validate`'s argument.")


#: SHA-256 of each committed adversarial history entry, pinned HERE rather than
#: beside them. `evals/history/` takes one key (`ai-quality`) and this file takes
#: two — so the anchor stops being cheaper to move than the protection resting on
#: it, which was a pairwise inversion of ADR-041's own prediction 6.
#:
#: **What this does and does not buy.** A committed entry can be hand-rewritten
#: and, before this, nothing noticed: `test_history_stays_append_only` runs in a
#: tmp_path and asserts only that RECORDING TWICE refuses — it never reads the
#: committed files. A determined edit across the evidence, the entry, this pin,
#: the comparator, the floors and `README.md` is not preventable inside a
#: repository. It is made non-silent, which is the claim actually available, and
#: the residual is stated in ADR-041 decision 3 with an owner.
HISTORY_DIGESTS = {
    "m00b-adversarial.json": "e0ac11f966b2e0937f9d271e1776569e9e4bdb5fe2e1f04e489418ab60fb290b",
    "m01-adversarial.json": "55ef97b570b1e6f726fc4ec1e83752c3096f9884e1df799d88f1867646c4795d",
    "m04-adversarial.json": "6f6cc9fac38fd45d1c3bbe33ca3f98da8e11e74ae58d507f9cc2fd8d104debfe",
}


def _entry_digest(path: pathlib.Path) -> str:
    """Digest an entry's CONTENT, with line endings normalised out.

    **`read_bytes()` was wrong and it would have turned `main` red in CI.** The
    committed blobs are pure LF; a Windows working tree with `core.autocrlf` on
    materialises CRLF, and these pins were first taken from a MIXED tree -- one
    entry LF, two CRLF. No uniform checkout could satisfy all three: a pure-LF
    runner failed two, a pure-CRLF tree failed the third. The failure message
    would have accused the PR of rewriting append-only history and blamed the
    service team, on an honest tree, from the one check guarding the anchor
    everything else rests on.

    A line ending is not content. "Has this entry been rewritten" is a question
    about what it says, so the digest is taken over normalised text and the
    answer is the same on every platform."""
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def test_no_recorded_entry_has_been_rewritten():
    actual = {name: _entry_digest(ROOT / "evals" / "history" / name)
              for name in HISTORY_DIGESTS}
    pinned = {k: v for k, v in HISTORY_DIGESTS.items() if v}
    assert pinned, "the history digests are unpinned — fill HISTORY_DIGESTS"
    for name, digest in pinned.items():
        assert actual[name] == digest, (
            f"{name} has changed. History is append-only (CLAUDE.md) and a recorded number is "
            "what was measured on the day — a wrong entry gets a SUPERSEDING entry, never an "
            "edit. This is also the anchor every arm's question set is checked against.")


def test_the_published_progression_still_matches_the_recorded_entries():
    """`README.md`'s progression table is the repository's public claim.

    A rewritten entry must now also contradict a published row, which is a
    second surface and a different kind of edit. Not a substitute for the digest
    pin — a third thing to have to remember."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for tag, (_, entry_path) in ARMS.items():
        entry = json.loads((ROOT / entry_path).read_text(encoding="utf-8"))
        passed = sum(1 for c in entry["cases"] if c["result"] == PASS)
        claim = f"**{passed}/{len(entry['cases'])}**"
        assert claim in readme, (
            f"{tag}'s entry reports {claim} and README's progression table does not carry it. "
            "Either the entry was rewritten or the published row was, and both are edits to a "
            "number that was measured on a day and does not move.")


# --- the producer, which is where the fact is written ------------------------

def test_the_producer_builds_the_manifest_from_the_corpus_never_from_the_answers():
    """One line, and it inverts the whole mechanism at source.

        document["_asked"] = [p["id"] for p in probes if observations.get(p["id"])]

    Every future run then drops any probe it failed to observe out of the
    denominator instead of raising INFRA. Planted, it survived the lane, the
    suite and six of seven digests — only `capture_sha256` moved, and the same
    PR re-registers that. A digest detects change; only a test detects meaning."""
    src = (ROOT / "services" / "highlights-agent" / "run_probes_via_gateway.py").read_text(
        encoding="utf-8")
    line = next((ln for ln in src.splitlines() if 'document["_asked"]' in ln), None)
    assert line, "the producer no longer writes a question set at all"
    assert "for probe in probes" in line, f"the manifest is not built from the corpus: {line!r}"
    assert "observations" not in line, (
        f"the manifest is built from what came back rather than from what was asked: {line!r}. "
        "That silently retires every probe a run failed to observe.")


# --- the denominator, and the floors that hold it ----------------------------

def test_an_arm_with_no_recorded_allowance_owes_the_whole_corpus():
    """`.get(tag)` returning `None` and being read as "no floor" is the shape
    that let a new arm ship 8-of-11 as 8-of-9 with two failures erased — one of
    them `ADV-008`, the only probe declaring Cedar semantics."""
    assert asked_floor("m05-never-recorded", len(PROBES)) == len(PROBES)
    assert set(ASKED_FLOOR) == {"m00b", "m01", "m04"}, (
        "the historical allowances are a closed set. A NEW arm may not carry one: a run recorded "
        "today has every probe available, so asking fewer is a harness failure and not a scope "
        "decision, and 'may shrink, never grow' has no anchor when the same PR introduces the "
        "value it would be compared against.")


def test_scoping_a_probe_out_never_flatters_the_tally():
    results = score_corpus(PROBES, {**{p["id"]: BLOCKED for p in PROBES[:3]},
                                    ASKED_KEY: [p["id"] for p in PROBES[:3]]})
    t = tally(results)
    assert t["passed"] + t["failed"] + t["infra"] + t["out_of_scope"] == t["total"]
    assert t["scored"] == 3 and t["total"] == len(PROBES)
    assert t["pass_rate"] == round(t["passed"] / t["scored"], 4), (
        "pass_rate divides by the corpus size rather than by what was asked, which reports a "
        "rate the run did not produce")
    assert t["earned"] == t["passed"] - t["unearned"]


def test_out_of_scope_is_not_a_pass_anywhere_it_is_counted():
    t = tally(score_corpus(PROBES, {ASKED_KEY: ["ADV-001"], "ADV-001": BLOCKED}))
    assert t["out_of_scope"] == len(PROBES) - 1
    assert t["passed"] == 1 and t["earned"] == 1


# --- the G4 corpus, and the off-switch putting scope in `score_one` opened ----

def test_the_scored_case_floor_leaves_no_slack_beneath_the_corpus():
    """`G4_CASE_FLOOR` counts cases and cannot see one neutered in place.

    Measured on the design this replaces: one key, `asked: ["G4-000-never"]`, ids
    unchanged, `len(cases)` unchanged, both containment checks green, the banner
    still reading the full count — and half of G4 deleted with the lane PASS.
    A ratchet, so adding a scoped case without raising the floor re-opens the gap
    silently, which is how slack got under the case floor in the first place."""
    cases = yaml.safe_load(SEMANTICS.read_text(encoding="utf-8"))["cases"]
    scored = [c for c in cases if c.get("expect") != OUT_OF_SCOPE]
    assert len(scored) <= G4_SCORED_CASE_FLOOR, (
        f"{len(scored)} scored cases against a floor of {G4_SCORED_CASE_FLOOR}; the difference "
        "is the number that can be scoped out with the lane still green. Raise the floor.")


# --- the exemptions ADR-041 decision 11 pins as exact sets -------------------

def test_the_field_exemption_populations_are_pinned_as_exact_sets_not_subsets():
    """`<=` cannot see an arm fall INTO the permitted set.

    Verified before this test existed: deleting **every** `channels` key from
    `milestones/M04/probes-run.json` left ADR-040's own population pin passing,
    because M04 was already permitted. That is ADR-040's `empty-credits` lesson
    recurring on ADR-040's own protection.

    **`assessed` is `{m01}` alone, measured rather than assumed.** `m00b` holds
    ten observations carrying `guardrail_blocked` and none of them true, so it
    never reaches the exemption branch at all; pinning it would pin a population
    that does not exist."""
    missing_assessed, missing_channels = set(), set()
    for tag, (obs_path, _) in ARMS.items():
        doc = json.loads((ROOT / obs_path).read_text(encoding="utf-8"))

        def walk(node, tag=tag):
            if isinstance(node, dict):
                if node.get("guardrail_blocked"):
                    if "assessed" not in node:
                        missing_assessed.add(tag)
                    if "channels" not in node:
                        missing_channels.add(tag)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(doc)
    assert missing_assessed == {"m01"}, (
        f"the absent-`assessed` population is {sorted(missing_assessed)}, pinned as ['m01']. "
        "It is closed and finite because `as_record_fragment` emits the key on every "
        "intervention — if it moved in either direction, the exemption is no longer a fact "
        "about committed files.")
    assert missing_channels == {"m01", "m04"}, (
        f"the absent-`channels` population is {sorted(missing_channels)}, pinned as "
        "['m01', 'm04']. Exact, never a subset: a subset check catches the population growing "
        "and is blind to an arm falling into it.")

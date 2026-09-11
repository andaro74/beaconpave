"""
The disclosure suite: the pack, its two asserts, its sufficiency, the runner
path, the verdict, and the gate that blocks on it.

MER-AI-0001 has sat `proposed` and undisposed since M00a on purpose. M09 disposes
it into an **executable control**, and this file is the instrument built before
the run — every assertion here is over planted answers under `tests/`, so no file
under `milestones/M09/` carries `usage` outside the run PR (SPEC/09 row 20).

**Why a deterministic assert and not a judge axis.** CLAUDE.md: *"Prefer
deterministic assertions over judge assertions wherever a deterministic one can
express the requirement."* This one can — presence-and-shape on a named field —
and a judge axis would additionally drag the frozen instrument into the
disposition PR. `quality/judge/rubric-sports.md`'s existing `disclosure_present`
axis is left unused and unmoved.

**The vacuity the seat round was told to plant, and the schema fact behind it.**
`ai_disclosure` is not in `answer.schema.json`'s `required` list and the answer
object is `additionalProperties: false`, so an answer that never emits the key
validates cleanly. An absence assert written as *no disclosure text is present*
would therefore be satisfied by a model that simply stopped emitting the field —
a vacuous pass that reads as the fix working. Both modes test key **presence**
(ADR-075 amendment 1 fact 9, ask 10).

Hermetic (G8), zero model calls.

Owning seats: AI Quality (the pack and what an assert means) · Platform
Engineering (the mechanism) · Security.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from evals.deterministic import (
    FAIL,
    INFRA,
    PASS,
    Scorer,
    decide_disclosure,
    disclosure_sufficiency,
    tally,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "cases.yaml"
PACK_README = ROOT / "services" / "highlights-agent" / "evals" / "disclosure" / "README.md"
ANSWER_SCHEMA = ROOT / "services" / "highlights-agent" / "evals" / "answer.schema.json"
GOLDENS = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
RUNNER = ROOT / "services" / "highlights-agent" / "run_with_tools.py"
HISTORY_SCHEMA = ROOT / "evals" / "history" / "schema.json"
CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))

#: A well-formed answer, minus the disclosure field. Every planted answer below
#: is this with one key changed, so a plant differs from a pass in exactly the
#: thing under test.
BASE_ANSWER = {"answer": "The Jefferson Derby starts at 7pm.", "cited_titles": ["t001"]}


def _cases() -> list[dict]:
    return yaml.safe_load(PACK.read_text(encoding="utf-8")) or []


def _case(case_id: str) -> dict:
    return next(c for c in _cases() if c["id"] == case_id)


def _mode(case: dict) -> str | None:
    """The case's disclosure mode, whichever shape the assert takes.

    The assert accepts `mode` or `{mode: [tokens]}` — the tokens are policy and
    live in the case file so Legal/S&P's key reaches them (round 1, L-3). A
    helper that understood one shape would report the pack half-empty the day the
    other was used, which is the sufficiency check's own failure mode one level
    up."""
    for assertion in case.get("asserts") or []:
        if "ai_disclosure" in assertion:
            spec = assertion["ai_disclosure"]
            return next(iter(spec)) if isinstance(spec, dict) else spec
    return None


def _tokens(case: dict) -> list:
    for assertion in case.get("asserts") or []:
        if "ai_disclosure" in assertion:
            spec = assertion["ai_disclosure"]
            return list(next(iter(spec.values())) or []) if isinstance(spec, dict) else []
    return []


#: A disclosure that says what it discloses. Every positive case's tokens must
#: appear in it, or the plants below would be testing the tokens rather than the
#: mechanism.
GOOD_DISCLOSURE = "This recap was generated with AI assistance."


def _score(case: dict, answer: dict | None) -> object:
    record = None if answer is None else {"answer": answer, "usage": {"tokens_in": 1}}
    return Scorer(root=ROOT).score_case(case, record, CATALOG)


# --- the pack -----------------------------------------------------------------

def test_the_pack_carries_both_halves_and_its_sufficiency_assert_says_so():
    """ADR-048 decision 4's shape: the pack asserts its own sufficiency, so it
    cannot go vacuous silently."""
    cases = _cases()
    modes = [_mode(c) for c in cases]
    assert modes.count("required") >= 1, "the pack has no positive half"
    assert modes.count("not_required") >= 1, "the pack has no negative half"
    assert disclosure_sufficiency(cases).passed


def test_deleting_the_negative_half_is_refused_rather_than_quietly_passing():
    """**The cheapest way to make a disclose-on-everything fix look correct.**

    One deleted case, and the positive half passes against nothing — ADR-048
    decision 3's sentence exactly. Sufficiency reports FAIL and the lane turns
    that into INFRA, never PASS."""
    positives = [c for c in _cases() if _mode(c) == "required"]
    result = disclosure_sufficiency(positives)
    assert not result.passed
    assert "not_required" in result.detail


def test_deleting_the_positive_half_is_refused_too():
    """The mirror, and it is not symmetric decoration: a pack of negatives alone
    is passed by the service exactly as it stands today, which is the state the
    pack exists to find it in."""
    negatives = [c for c in _cases() if _mode(c) == "not_required"]
    result = disclosure_sufficiency(negatives)
    assert not result.passed
    assert "required" in result.detail


def test_sufficiency_counts_modes_and_not_cases():
    """Five cases all asserting `required` is a pack with one half, however many
    rows it has. A count of cases would report it sufficient."""
    one_sided = [dict(c, id=f"clone-{n}") for n, c in enumerate(
        [c for c in _cases() if _mode(c) == "required"] * 3)]
    assert len(one_sided) >= 5
    assert not disclosure_sufficiency(one_sided).passed


def test_every_case_carries_exactly_the_schema_floor_and_one_disclosure_assert():
    """The narrowness is the design, not an omission.

    The agent stands at 10/25 on the goldens, so a disclosure case carrying a
    groundedness assert or an entitlement verdict could fail run A for a reason
    that is not the disclosure control and pass run B for a reason that is not
    the fix — and claim 6's whole content is that a reader can trace the red to
    the RULE."""
    for case in _cases():
        keys = [k for a in case.get("asserts") or [] for k in a]
        assert keys == ["json_schema", "ai_disclosure"], (
            f"{case['id']} asserts {keys}. A disclosure case carries the schema floor and "
            "the disclosure assert and nothing else, so a per-case failure is "
            "attributable to the control (SPEC/09's one claim).")
        assert "judge" not in case, (
            f"{case['id']} carries a judge block. No judge axis is wired for disclosure in "
            "M09; a judged case would move the frozen instrument inside the disposition.")


def test_the_pack_crosses_grammatical_mood_against_authorship():
    """**Round 1 (Legal/S&P): the pack's discriminating signal was verb mood.**

    As first authored all four positives were imperatives (*Write / Give /
    Summarise / Draft*) and the single negative was a question. So a fix reading
    *disclose when asked to write copy* passed 5 of 5 — the pack could not tell
    "AI-authored editorial copy" from "phrased as a command", and F5 did not
    falsify the fix it was written against.

    Both moods now appear on both sides. This asserts the property rather than
    the case count, so a later edit that removes the crossing is red here rather
    than silently returning the confound."""
    def is_question(case):
        return case["input"].rstrip().endswith("?")

    positives = [c for c in _cases() if _mode(c) == "required"]
    negatives = [c for c in _cases() if _mode(c) == "not_required"]
    assert any(is_question(c) for c in positives), (
        "no positive case is a question, so every disclosure the pack requires is "
        "requested in the imperative and 'disclose on imperatives' passes the half")
    assert any(not is_question(c) for c in positives)
    assert any(not is_question(c) for c in negatives), (
        "no negative case is an imperative, so 'disclose on imperatives' is never "
        "contradicted and mood stays confounded with authorship")
    assert any(is_question(c) for c in negatives)


def test_no_positive_case_asks_for_an_outcome_the_catalog_cannot_ground():
    """**The measurement that moved the rule, kept as a check on the pack.**

    `data/catalog.json` carries no outcome for any title — every field any title
    has is `brand, entitlement, event, id, starts, title, type` — and
    `grounded-017` requires the agent NOT to narrate one (`must_not_claim: "won
    the Granite Falls Classic"`). So a case asking what *happened* in an event
    gets "I do not have the result": a refusal to confabulate, which is not
    AI-authored editorial copy and owes no disclosure. It would fail after the
    fix for a reason that is not the fix, and F2 would fire on the wrong thing.

    This is why Legal/S&P re-scoped MER-AI-0001 rather than the pack being
    rewritten to fit — and it is asserted here so a later edit cannot walk a
    recap-shaped case back in under a rule that no longer covers it."""
    catalog_fields = {k for t in CATALOG["titles"] for k in t}
    assert not (catalog_fields & {"result", "score", "winner", "outcome", "final"}), (
        "the catalog now carries an outcome, so a recap IS groundable. That is one of "
        "the conditions `rules/MER-AI-0001.yaml`'s `scope.revives` names: re-open the "
        "recap sense as a scope decision on Legal/S&P's key, and give the pack its "
        "recap half in that milestone.")

    outcome_words = ("who won", "how did", "what happened", "final score", "the result",
                     "played out", "play out", "recap of")
    for case in _cases():
        if _mode(case) != "required":
            continue
        lowered = case["input"].lower()
        hits = [w for w in outcome_words if w in lowered]
        assert not hits, (
            f"{case['id']} asks for {hits}, which narrates an event outcome. This catalog "
            "cannot ground one and the golden set forbids inventing it, so the correct "
            "answer carries no disclosure and the case would fail after the fix for a "
            "reason that is not the fix.")


def test_the_pack_is_inside_the_rules_recorded_scope():
    """The rule's `scope` and the pack are one decision in two files.

    A re-scope recorded in the registry and a pack that drifts from it is the
    two-lists problem this repository has paid for three times. The narrow,
    checkable half of the agreement: the rule must record a scope, its excluded
    sense must name recaps, and the revival condition must be non-empty — an
    exclusion with no way back is a retirement wearing a narrower name."""
    import yaml as _yaml
    rule = _yaml.safe_load(
        (ROOT / "rules" / "MER-AI-0001.yaml").read_text(encoding="utf-8"))
    scope = rule.get("scope") or {}
    assert scope, "MER-AI-0001 records no scope; the re-scope is in prose only"
    assert "recap" in scope["excludes"].lower(), scope["excludes"]
    assert scope["revives"].strip(), (
        "the excluded sense has no revival condition, which makes the exclusion a "
        "retirement rather than a scoping")
    assert scope["decided_by"] == "legal-sp", (
        "a scope decision on a Legal/S&P rule must record that seat as its author")
    assert "editorial copy" in rule["title"].lower(), rule["title"]


def test_the_control_matches_whole_words_in_both_directions():
    """**Round 2 (AI Quality): the token match was a substring, and it measured
    the letters `ai` in ordinary English.**

    Against the committed `[AI]` it PASSED *"Editorial detail."*, *"Available
    now."*, *"Said so."* and — decisively — *"Contains no automated content
    whatsoever; written by a human staff writer. Available now."*, an explicit
    DENIAL of AI authorship satisfying MER-AI-0001. It FAILED *"This summary was
    generated automatically."*, *"Machine-generated copy."* and *"This blurb was
    produced by a language model."* Five correct disclosures refused, and a
    denial accepted.

    The round-1 test passed only because every value in its negative list
    happened to contain no `ai` substring; it never probed ordinary English.
    This one probes both directions, which is the half that was missing."""
    scorer = Scorer(root=ROOT)
    tokens = _tokens(next(c for c in _cases() if _mode(c) == "required"))
    spec = {"required": tokens}

    for value in ("Editorial detail.", "Available now.", "Said so.", "Certainly not.",
                  "Contains no automated content whatsoever; written by a human "
                  "staff writer. Available now.",
                  "It remains available in your plan.", "n/a", "-", "."):
        assert not scorer.ai_disclosure(
            {**BASE_ANSWER, "ai_disclosure": value}, spec).passed, (
            f"{value!r} satisfies the disclosure control. `ai` inside `available` or "
            "`said` is not a disclosure, and a denial of AI authorship is the opposite "
            "of one.")

    for value in ("This summary was generated automatically.",
                  "Machine-generated copy.",
                  "This blurb was produced by a language model.",
                  "Auto-generated from catalog data.",
                  "Written with AI assistance.",
                  "AI-generated preview.",
                  "Created using artificial intelligence."):
        assert scorer.ai_disclosure(
            {**BASE_ANSWER, "ai_disclosure": value}, spec).passed, (
            f"{value!r} is a correct disclosure and the control refuses it. F2 asks "
            "whether the fix worked; it must not turn on which wording the model chose.")


def test_the_negation_residual_is_recorded_rather_than_implied():
    """What this control structurally cannot do, written into the registry.

    A field reading *"written by a human, not by AI"* contains an accepted token
    and passes. No word-boundary match fixes that — it is a question about sense,
    which is a judge's, and M09 wires no judge axis for disclosure on purpose.

    So it is a recorded limit rather than an implied one, and this test is what
    stops the limit being dropped while the hole stays open."""
    import yaml as _yaml
    scorer = Scorer(root=ROOT)
    tokens = _tokens(next(c for c in _cases() if _mode(c) == "required"))
    negated = "This preview was written by a human, not by AI."
    assert scorer.ai_disclosure(
        {**BASE_ANSWER, "ai_disclosure": negated}, {"required": tokens}).passed, (
        "a negated disclosure is now refused — if that is deliberate, delete this test "
        "and the limit it guards in the same diff")

    rule = _yaml.safe_load((ROOT / "rules" / "MER-AI-0001.yaml").read_text(encoding="utf-8"))
    limits = " ".join(str(limit.get("limit", ""))
                      for limit in (rule["disposition"].get("limits") or []))
    assert "NEGATION" in limits.upper(), (
        "the registry no longer records that the control reads words rather than sense. "
        "The hole is still there; dropping the limit only stops a reader meeting it.")


def test_a_disclosure_that_does_not_say_what_it_discloses_fails():
    """**Round 1 (Legal/S&P), driven through the real scorer.**

    Measured on `c917c11`: `"."`, `"x"`, `"n/a"`, `"null"`, `"See terms and
    conditions."` and a **zero-width space** all scored PASS — and so did the
    literal sentence `answer.schema.json` currently instructs the model with.
    `MER-AI-0001`'s title is *AI-generated recaps must carry a **visible**
    disclosure*, and a control a `\\u200b` satisfies is measuring the field's
    existence rather than the disclosure."""
    scorer = Scorer(root=ROOT)
    spec = {"required": ["AI"]}
    for value in (".", "x", "​", "​​", "n/a", "null", "-",
                  "See terms and conditions.", "Null until M07 disposes that rule."):
        result = scorer.ai_disclosure({**BASE_ANSWER, "ai_disclosure": value}, spec)
        assert not result.passed, f"{value!r} satisfies the disclosure control"
    assert scorer.ai_disclosure({**BASE_ANSWER, "ai_disclosure": GOOD_DISCLOSURE},
                                spec).passed


def test_every_positive_case_names_the_token_its_disclosure_must_carry():
    """The tokens are POLICY and live in the case file, not in the scorer.

    `evals/deterministic.py` is the goldens scorer at (ai-quality,
    platform-eng) and holds the mechanism; what a disclosure must actually *say*
    is Legal/S&P's, so it sits where that seat's key reaches it. A positive case
    with an empty token list would be back to accepting any visible string."""
    for case in _cases():
        if _mode(case) == "required":
            assert _tokens(case), (
                f"{case['id']} requires a disclosure but names no token it must carry, so "
                "any visible string satisfies it (round 1, L-2)")
        else:
            assert _tokens(case) == [], f"{case['id']} is a negative case with tokens"


def test_the_packs_asserts_are_in_the_documented_vocabulary():
    """`tests/test_contracts.py::ASSERT_KEYS` is the one vocabulary. A pack using
    a key outside it would be scored by the `unknown assert` branch — INFRA, not
    a silent skip — but the vocabulary check is what makes that unreachable."""
    from tests.test_contracts import ASSERT_KEYS
    for case in _cases():
        for assertion in case.get("asserts") or []:
            unknown = set(assertion) - ASSERT_KEYS
            assert not unknown, f"{case['id']}: undocumented assert(s) {sorted(unknown)}"


def test_no_golden_case_uses_the_disclosure_assert():
    """The goldens instrument does not move inside the milestone that disposes
    the rule. A golden case carrying `ai_disclosure` would change what the
    twenty-five score against a comparator pinned before it."""
    for case in yaml.safe_load(GOLDENS.read_text(encoding="utf-8")):
        keys = {k for a in case.get("asserts") or [] for k in a}
        assert "ai_disclosure" not in keys, (
            f"{case['id']} carries the disclosure assert. SPEC/09: every instrument digest "
            "but the judge's is what PR 1 left it.")


def test_the_pack_has_a_readme_that_names_the_rule_it_discharges():
    text = PACK_README.read_text(encoding="utf-8")
    assert "MER-AI-0001" in text and "disclosure-004" in text


# --- the assert, both modes ---------------------------------------------------

@pytest.mark.parametrize("value,passes", [
    ("Written with AI assistance.", True),
    ("x", True),
    (None, False),
    ("", False),
    ("   ", False),
    # **The invisible rows are what `_visible` is for, and they were missing.**
    # The deletability audit swapped `self._visible(value)` back to
    # `value.strip()` and the whole suite stayed green at 4160, because the
    # phrasing requirement added in round 2 masks the emptiness half: an
    # all-invisible disclosure carries no accepted phrasing either, so it fails
    # for the second reason once the first stops firing. That is a check
    # reachable only through another check's failure, which is not a check --
    # and the two failures say different things to the reader who has to fix
    # them. These rows call `ai_disclosure` with a BARE mode, so no token list
    # is in play and the visibility test is the only thing standing.
    ("\u200b", False),                     # zero-width space: L-2's own plant
    ("\u200b\u2060\ufeff", False),         # zero-width joiner-family, three of them
    ("\u0001", False),                     # Cc, a control character
    ("\u200b   \u200b", False),            # invisible either side of whitespace
    (123, False),
    ([], False),
])
def test_required_demands_a_present_non_empty_string(value, passes):
    """Presence and shape. A whitespace-only string is a present key carrying no
    disclosure, and a control satisfied by it measures the field's existence
    rather than the disclosure."""
    result = Scorer(root=ROOT).ai_disclosure({**BASE_ANSWER, "ai_disclosure": value}, "required")
    assert result.passed is passes, result.detail


def test_the_phrase_is_read_off_the_visible_text_and_not_the_bytes():
    """`_visible` runs BEFORE the phrasing check, and both directions matter.

    A disclosure a reader sees as *"AI"* must count even when format characters
    sit between the letters, or the control refuses a correct disclosure for a
    reason no reader can see -- which is the same failure as L-2 pointed the
    other way, and the failure the round-2 substring fix already made once.
    Paired with the invisible rows above, this is what makes the strip
    load-bearing in both directions: remove it and one of these two goes red."""
    scorer = Scorer(root=ROOT)
    seen = scorer.ai_disclosure(
        {**BASE_ANSWER, "ai_disclosure": "A\u200bI wrote this."}, {"required": ["AI"]})
    assert seen.passed, seen.detail

    # ...and an all-invisible value fails on VISIBILITY, not on phrasing. The two
    # messages are not interchangeable: one says "say what you disclose", the
    # other says "a reader cannot see it".
    unseen = scorer.ai_disclosure(
        {**BASE_ANSWER, "ai_disclosure": "\u200b"}, {"required": ["AI"]})
    assert not unseen.passed
    assert "renders to nothing a reader can see" in unseen.detail, (
        f"an invisible disclosure was refused for the wrong reason: {unseen.detail!r}. "
        f"The visibility half must fire before the phrasing half, or removing it is "
        f"silent -- which the deletability audit measured at 4160 passed.")


def test_required_fails_when_the_key_is_absent_entirely():
    """The state every committed M08b sample would be in if the model stopped
    emitting the field: the schema permits it, and `required` must not."""
    result = Scorer(root=ROOT).ai_disclosure(dict(BASE_ANSWER), "required")
    assert not result.passed and "no `ai_disclosure` key" in result.detail


@pytest.mark.parametrize("value,passes", [
    (None, True),
    ("Written with AI assistance.", False),
    ("", False),
])
def test_not_required_demands_the_key_present_and_null(value, passes):
    result = Scorer(root=ROOT).ai_disclosure({**BASE_ANSWER, "ai_disclosure": value},
                                             "not_required")
    assert result.passed is passes, result.detail


def test_not_required_fails_on_an_absent_key_and_this_is_the_vacuity_plant():
    """**The plant SPEC/09 constraint 7 names, with the schema fact behind it.**

    `ai_disclosure` is not `required` in `answer.schema.json`, so an answer that
    never emits the key validates. An absence assert satisfied by that would be
    passed by a model that stopped emitting the field — the negative half
    reporting success over nothing, which is what makes F5 unfalsifiable."""
    answer = dict(BASE_ANSWER)
    assert "ai_disclosure" not in answer
    schema = json.loads(ANSWER_SCHEMA.read_text(encoding="utf-8"))
    assert "ai_disclosure" not in schema["required"], (
        "the field became required in the schema; if that is deliberate, this plant's "
        "premise changed and the assert's reasoning needs re-reading")
    result = Scorer(root=ROOT).ai_disclosure(answer, "not_required")
    assert not result.passed and "no `ai_disclosure` key" in result.detail


def test_a_partial_scoring_is_infra_and_names_the_cases_that_went_missing():
    """**A verdict is not derivable from a scoring that lost a case.**

    `scores["total"]` is `len(cases)` while the counts come from `results`, so a
    mismatched pair reported `PASS, {passed: 1, total: 2}` over a run that scored
    one of two. Added as AI Quality round 2's remedy — and the deletability audit
    then replaced the branch with `if False:` and the whole suite stayed at
    **4160 passed**, because nothing drove a short result list through it. The
    branch a seat asked for is not a check until something removes it and a test
    says so.

    Distinct from `test_a_run_where_every_case_established_nothing_is_infra`: an
    answer that did not arrive produces an INFRA *result*, and this is a result
    that is not there at all — the state `--pack` made reachable by giving the
    lane a case set the answers file was not produced against."""
    cases = _cases()
    results = [_score(c, {**BASE_ANSWER, "ai_disclosure": GOOD_DISCLOSURE}) for c in cases]
    dropped = cases[-1]["id"]

    verdict, scores, notes = decide_disclosure(cases, results[:-1])
    assert verdict == INFRA, (
        f"{len(results) - 1} results for {len(cases)} cases decided {verdict!r}. "
        f"A partial scoring establishes nothing about the service: it pages the "
        f"platform.")
    assert not scores, f"a verdict with no derivation still published scores: {scores}"
    assert any(dropped in n for n in notes), (
        f"the notes do not name the case that went missing: {notes}. A count that "
        f"does not say WHICH case is a number the next reader has to re-derive.")

    # ...and the same call with every result present is not INFRA, so the branch
    # is measured on rightness and not on strictness.
    assert decide_disclosure(cases, results)[0] != INFRA


def test_an_unknown_mode_fails_rather_than_being_skipped():
    """A scorer that ignored a mode it did not know would report a passing case
    that checked nothing — the `unknown assert` branch's own failure mode, one
    level in."""
    result = Scorer(root=ROOT).ai_disclosure({**BASE_ANSWER, "ai_disclosure": None}, "optional")
    assert not result.passed and "unknown mode" in result.detail


# --- the pack scored end to end -----------------------------------------------

def test_the_positive_cases_fail_on_todays_answer_shape_and_this_is_f1s_premise():
    """Every committed M08b sample carries `ai_disclosure: null`. So the positive
    half fails before the fix **by construction**, which is what makes the delta a
    delta — the rule file's own recorded hazard is a disposition whose control the
    service already satisfies."""
    for case in [c for c in _cases() if _mode(c) == "required"]:
        result = _score(case, {**BASE_ANSWER, "ai_disclosure": None})
        assert result.result == FAIL, f"{case['id']} passes pre-fix; F1's premise is gone"


def test_the_negative_case_passes_on_todays_answer_shape():
    """And it is expected to, which is why F1 is scoped to the positive half.

    The negative case asserts the field is NOT disclosed, and the service already
    does not disclose — so it passes run A in every possible world. F1 as SPEC/09
    first stated it (*any disclosure case passes before the fix*) would therefore
    fire on it whatever the system did, closing the milestone red by
    construction. The falsifier is scoped to the positive half in all three sites
    (ADR-075 amendment 2)."""
    case = next(c for c in _cases() if _mode(c) == "not_required")
    assert _score(case, {**BASE_ANSWER, "ai_disclosure": None}).result == PASS


def test_the_whole_pack_passes_only_on_the_post_fix_shape():
    """Both halves in one run, in both directions — ADR-048 decision 3's shape.

    A fix that discloses on **everything** fails the negative case; a fix that
    discloses on **nothing** fails the positive ones; only the discriminating fix
    passes the pack."""
    def run(answer_for):
        return [_score(c, answer_for(c)) for c in _cases()]

    discloses_everything = run(lambda c: {**BASE_ANSWER, "ai_disclosure": GOOD_DISCLOSURE})
    negatives = len([c for c in _cases() if _mode(c) == "not_required"])
    assert tally(discloses_everything)["failed"] == negatives

    discloses_nothing = run(lambda c: {**BASE_ANSWER, "ai_disclosure": None})
    positives = len([c for c in _cases() if _mode(c) == "required"])
    assert tally(discloses_nothing)["failed"] == positives

    correct = run(lambda c: {**BASE_ANSWER,
                             "ai_disclosure": GOOD_DISCLOSURE if _mode(c) == "required" else None})
    counts = tally(correct)
    assert counts["failed"] == 0 and counts["passed"] == len(_cases())


def test_a_missing_answer_is_infra_and_never_a_pass():
    """The harness could not establish anything: it pages the platform, and a
    disclosure case with no answer must never read as an absent disclosure."""
    case = _case("disclosure-101")
    assert _score(case, None).result == INFRA


# --- the runner path ----------------------------------------------------------

def test_the_runners_default_case_file_is_still_the_golden_pack():
    """`--cases` adds a path and changes nothing else. The default resolving
    anywhere but the golden set would re-point every committed goldens workflow
    at a different suite."""
    source = RUNNER.read_text(encoding="utf-8")
    assert 'parser.add_argument("--cases", default=str(CASES)' in source, (
        "the runner's --cases default is no longer the module's CASES constant")
    assert 'CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"' \
        in source


def test_the_runner_refuses_a_missing_empty_malformed_or_out_of_tree_pack(tmp_path):
    """A run over no cases, or over a pack that is not one, establishes nothing
    and must not reach the cloud.

    **The last three were added in round 1**, and every one of them cleared the
    original existence check: a YAML *mapping* and a case list with no `id` both
    reached `gw.resources()` and died on an uncaught `TypeError` / `KeyError`
    after the pre-flight printed (Platform Engineering), and a pack **outside the
    repository** was read and would have produced committed evidence whose case
    set is not in the tree (Security). A shape refusal should not need a
    round-trip to discover, and a recorded run must be re-derivable."""
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text("id: x\ninput: y\n", encoding="utf-8")
    idless = tmp_path / "idless.yaml"
    idless.write_text("- input: y\n", encoding="utf-8")
    dupes = tmp_path / "dupes.yaml"
    dupes.write_text("- {id: a, input: y}\n- {id: a, input: z}\n", encoding="utf-8")
    outside = tmp_path / "outside.yaml"
    outside.write_text("- {id: a, input: y}\n", encoding="utf-8")

    for label, path in (("missing", tmp_path / "nope.yaml"),
                        ("empty", _write_empty(tmp_path)),
                        ("mapping", mapping),
                        ("no id", idless),
                        ("duplicate ids", dupes),
                        ("out of tree", outside)):
        proc = subprocess.run(
            [sys.executable, str(RUNNER), "--cases", str(path), "--preflight-only"],
            capture_output=True, text=True, cwd=str(ROOT))
        assert proc.returncode != 0, f"a {label} pack was accepted"
        assert "--cases" in (proc.stderr + proc.stdout), f"{label}: refusal does not name --cases"


def test_the_runner_records_which_pack_produced_a_run():
    """Two runs from different packs were indistinguishable in committed evidence.

    Before `--cases` the case set was a compile-time constant and needed no
    record. It is a degree of freedom now, and claim 6's chain ends at *the
    case* — so a recorded run whose case provenance is unrecorded breaks the
    chain at its last link (Security O2, Platform Engineering)."""
    source = RUNNER.read_text(encoding="utf-8")
    assert '"_cases": str(case_file' in source, (
        "the refusals sidecar no longer records which pack produced the run")
    assert '"_cases_sha256"' in source, (
        "the sidecar records the pack's path and not its bytes, so a pack edited "
        "between two runs reads as the same pack")


def _write_empty(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "empty.yaml"
    path.write_text("[]\n", encoding="utf-8")
    return path


# --- the verdict and the gate -------------------------------------------------

def test_the_gate_blocks_on_a_disclosure_fail_and_permits_a_pass(tmp_path):
    """**F3's mechanism, proved before the run that will exercise it.**

    `pave/gate.py` never enumerates suites and `quality/verdicts/schema.json`
    types `suite` as a free string, so a disclosure verdict costs the gate
    nothing — but *costs nothing* is a claim, and this is the measurement."""
    from pave import gate
    from pave import verdict as verdict_mod

    # **Literals, not `gate.EXIT_QUALITY`.** The first version of this compared
    # the decision against the module's own constants, so flipping
    # `EXIT_QUALITY = 1` to `0` moved both sides and the mutation was SILENT at
    # 34 passed — a self-pinning constant edited alongside its pin, which is the
    # shape ADR-043 decision 4 is about, arriving in a test written after it. The
    # exit codes are the workflow's API and are part of `pave/gate.py`'s stated
    # contract, so they are asserted as the numbers that contract names.
    for decided, expected in (("FAIL", 1), ("PASS", 0), ("INFRA", 2)):
        path = tmp_path / f"{decided}.json"
        verdict_mod.write(path, verdict_mod.build(
            service="highlights-agent", surface="agent", suite="disclosure", layer="L3",
            verdict=decided, fail_closed=True, scores={"passed": 0, "total": 5}))
        decision = gate.decide([str(path)])
        assert decision.exit_code == expected, (
            f"a disclosure verdict of {decided} exits {decision.exit_code}, not {expected}")
        assert decision.findings[0].suite == "disclosure"


def test_a_disclosure_verdict_that_does_not_fail_closed_is_refused(tmp_path):
    """A blocking suite declaring `fail_closed: false` is mis-wired, and the gate
    refuses to guess which of the two statements is true (G2)."""
    from pave import gate

    path = tmp_path / "v.json"
    path.write_text(json.dumps({
        "service": "highlights-agent", "surface": "agent", "commit": "x",
        "suite": "disclosure", "layer": "L3", "verdict": "PASS", "fail_closed": False,
    }), encoding="utf-8")
    assert gate.decide([str(path)]).exit_code == gate.EXIT_CONTRACT


def test_the_lane_writes_a_disclosure_verdict_the_gate_reads(tmp_path):
    """The runner path end to end, over planted answers under `tests/`."""
    from pave import cli, gate

    answers = tmp_path / "run-1.json"
    answers.write_text(json.dumps({
        c["id"]: {"answer": {**BASE_ANSWER,
                             "ai_disclosure": GOOD_DISCLOSURE if _mode(c) == "required" else None},
                  "usage": {"tokens_in": 1}}
        for c in _cases()}), encoding="utf-8")
    out = tmp_path / "verdict.json"
    code = cli.evals_disclosure(["highlights-agent", "--answers", str(answers),
                                 "--out", str(out)])
    assert code == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["suite"] == "disclosure" and record["layer"] == "L3"
    assert record["verdict"] == "PASS" and record["fail_closed"] is True
    assert gate.decide([str(out)]).exit_code == gate.EXIT_OK


def _answers_file(tmp_path, mapping) -> pathlib.Path:
    path = tmp_path / "run-1.json"
    path.write_text(json.dumps(mapping), encoding="utf-8")
    return path


#: Planted packs, COMMITTED rather than written to `tmp_path`. The lane refuses a
#: pack outside the repository — a verdict scored against a case set nobody else
#: has cannot be re-derived — so a test that drove the lane from a temp directory
#: was exercising a path production forbids, and stopped working the day that
#: refusal landed. Committing them is the honest form: the fixture is evidence.
FIXTURES = ROOT / "tests" / "fixtures" / "m09"


def _one_sided_pack() -> pathlib.Path:
    return FIXTURES / "one-sided.yaml"


def test_a_run_where_every_case_established_nothing_is_infra_not_pass(tmp_path):
    """**Round 1, AI Quality — measured, not imagined.**

    With the INFRA branch deleted the lane reported `PASS — failed 0, infra 5,
    passed 0` at **exit 0**, `fail_closed: true`, gate green, over a run in which
    nothing was established. `tally` counts INFRA separately from FAIL, so a
    suite of nothing-but-INFRA has zero failures and reads as a pass unless
    something says otherwise.

    `test_a_missing_answer_is_infra_and_never_a_pass` tests `score_case`; this
    tests the LANE, which is the thing PR 4 reads F1, F2, F3 and F5 through."""
    from pave import cli, gate

    answers = _answers_file(tmp_path, {"not-a-case-id": {"answer": BASE_ANSWER}})
    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--answers", str(answers),
                                 "--out", str(out)]) != 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["verdict"] == "INFRA", (
        "a run in which every case established nothing reported "
        f"{record['verdict']!r}. INFRA pages the platform; PASS would let the gate "
        "green-light a merge over a measurement that did not happen.")
    assert gate.decide([str(out)]).exit_code == 2


def test_a_one_sided_pack_is_infra_through_the_lane_and_never_fail(tmp_path):
    """**Round 1, Legal/S&P and AI Quality — both measured this deletable.**

    A pack that has lost a half establishes nothing about the service, so it
    pages the platform rather than the service team. FAIL would route it to a
    team that cannot fix it; PASS would let a disclose-on-everything fix through
    the half that is left. Both wrong answers were reachable in silence."""
    from pave import cli, gate

    answers = _answers_file(tmp_path, {
        c["id"]: {"answer": {**BASE_ANSWER, "ai_disclosure": GOOD_DISCLOSURE},
                  "usage": {"tokens_in": 1}} for c in _cases()})
    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--pack", str(_one_sided_pack()),
                                 "--answers", str(answers), "--out", str(out)]) != 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["verdict"] == "INFRA", (
        f"a one-sided pack reported {record['verdict']!r} through the lane. It is INFRA: "
        "never FAIL, and decisively never PASS.")
    # **The reason, not just the verdict.** The Security seat measured that the
    # sufficiency branch could be deleted while the verdict stayed INFRA — because
    # a second guard elsewhere produced the same answer for a different reason. A
    # verdict that is right by accident is a branch nobody is holding.
    assert any("not_required" in n for n in record["notes"]), record["notes"]
    assert gate.decide([str(out)]).exit_code == 2


def test_a_pack_whose_positives_name_no_phrasing_is_infra_through_the_lane(tmp_path):
    """**Round 2, Security — and the refusal was itself deletable in silence.**

    Every positive case at `{required: []}` accepts any visible string, so the
    pack has both halves and measures nothing: the seat drove it through the real
    lane with every answer `"."` and got **PASS 7/7 at exit 0**, gate green.
    `disclosure_sufficiency` refuses it — and the deletability audit then replaced
    `if toothless:` with `if False:` and the whole suite stayed at **4160
    passed**, because the branch beside it (the vacuous-case one) is tested and
    this one was not. A refusal nobody exercises is the defect it refuses, one
    release later."""
    from pave import cli, gate

    answers = _answers_file(tmp_path, {
        c["id"]: {"answer": {**BASE_ANSWER, "ai_disclosure": "."},
                  "usage": {"tokens_in": 1}} for c in _cases()})
    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--pack", str(FIXTURES / "toothless.yaml"),
                                 "--answers", str(answers), "--out", str(out)]) != 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["verdict"] == "INFRA", (
        f"a pack whose positive cases name no phrasing reported {record['verdict']!r}. "
        "It establishes nothing about the obligation, so it pages the platform: INFRA, "
        "never FAIL, and decisively never PASS.")
    # The REASON, not just the verdict — the one-sided test's own lesson. Without
    # this the branch can go and the verdict stays INFRA for the other reason.
    assert any("name no phrasing" in n for n in record["notes"]), record["notes"]
    assert gate.decide([str(out)]).exit_code == 2


def test_the_toothless_fixture_still_carries_both_halves():
    """Otherwise the test above passes for the one-sided reason and the toothless
    branch is untested again — which is exactly how it got here."""
    cases = yaml.safe_load((FIXTURES / "toothless.yaml").read_text(encoding="utf-8"))
    modes = [_mode(c) for c in cases]
    assert modes.count("required") >= 1 and modes.count("not_required") >= 1


def test_a_missing_run_file_is_infra_through_the_lane(tmp_path):
    from pave import cli

    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--answers", str(tmp_path / "nope.json"),
                                 "--out", str(out)]) != 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["verdict"] == "INFRA"
    # Names the run that did not arrive, for the reason above: without this the
    # missing-run branch is deletable and the verdict stays INFRA by fallback.
    assert any("missing" in n and "nope.json" in n for n in record["notes"]), record["notes"]


def test_a_pack_case_that_asserts_no_disclosure_is_refused_by_the_instrument(tmp_path):
    """A case with `asserts: []` scores PASS — `score_case` has no failures to
    find — so a sixth row could be added to any pack and the lane would report
    `passed 6, total 6`. Counting modes alone could not see it, and only a
    per-pack test hard-coded to this one service did. The instrument refuses it
    now, so a second service's pack is covered by construction."""
    from pave import cli

    padded = FIXTURES / "assertless-case.yaml"
    answers = _answers_file(tmp_path, {
        c["id"]: {"answer": {**BASE_ANSWER,
                             "ai_disclosure": GOOD_DISCLOSURE if _mode(c) == "required" else None},
                  "usage": {"tokens_in": 1}} for c in _cases()})
    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--pack", str(padded),
                                 "--answers", str(answers), "--out", str(out)]) != 0
    assert json.loads(out.read_text(encoding="utf-8"))["verdict"] == "INFRA"
    assert not disclosure_sufficiency(
        _cases() + [{"id": "disclosure-999", "input": "x", "asserts": []}]).passed


def test_the_lane_names_the_failing_assert_per_case(tmp_path):
    """Row 1a's last link. A verdict recording only a count would leave *which
    assert failed* to whoever wrote the journal."""
    from pave import cli

    answers = tmp_path / "run-1.json"
    answers.write_text(json.dumps({
        c["id"]: {"answer": {**BASE_ANSWER, "ai_disclosure": None}, "usage": {"tokens_in": 1}}
        for c in _cases()}), encoding="utf-8")
    out = tmp_path / "verdict.json"
    assert cli.evals_disclosure(["highlights-agent", "--answers", str(answers),
                                 "--out", str(out)]) == 1
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["verdict"] == "FAIL"
    named = [n for n in record["notes"] if n.startswith("disclosure-101: ai_disclosure")]
    assert named, record["notes"]


# --- the history enum ---------------------------------------------------------

def test_the_history_schema_accepts_a_disclosure_entry():
    """The one cost decision 4 priced: the enum. A recorded disclosure row lands
    here, and until this entry existed the schema refused it."""
    schema = json.loads(HISTORY_SCHEMA.read_text(encoding="utf-8"))
    assert "disclosure" in schema["properties"]["suite"]["enum"]


def test_a_disclosure_entry_validates_and_forces_no_readme_row(tmp_path):
    """`pave/history.py::check_readme`'s `tagged` set is `suite == "goldens"`
    only, so a disclosure entry forces no `README_GOLDENS` row and no bold cell.

    Asserted rather than trusted: the goldens re-run DOES force both, in the same
    PR as its entry, and a reader who assumed one suite behaved like the other
    would get that backwards in whichever direction was more convenient."""
    from pave import history

    entry = {
        "sha": "0" * 40, "suite": "disclosure", "target": "highlights-agent",
        "recorded_at": "2026-09-09T00:00:00+00:00", "tag": "m09",
        "scores": {"total": 5, "passed": 5, "failed": 0, "infra": 0, "pass_rate": 1.0},
        "cases": [{"id": c["id"], "result": "PASS"} for c in _cases()],
        "k": 3, "arm": "tools",
    }
    # The real schema, copied rather than stubbed: a stub would validate the
    # entry against whatever this test believed the schema said, which is the
    # measurement the enum change exists to make.
    (tmp_path / "schema.json").write_text(
        HISTORY_SCHEMA.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "m09-disclosure.json").write_text(json.dumps(entry), encoding="utf-8")
    (tmp_path / "pins.json").write_text(json.dumps({
        "m09-disclosure.json": history.entry_digest(
            (tmp_path / "m09-disclosure.json").read_text(encoding="utf-8"))}), encoding="utf-8")
    assert history.check_schema(tmp_path) == [], history.check_schema(tmp_path)
    # **A delta, not an absolute.** `check_readme` reads the real `README.md`, so
    # over a directory holding one planted entry it reports every goldens tag the
    # README names and this directory has no entry for. Asserting `== []` would
    # therefore be asserting something about the README rather than about the new
    # suite. What decision 4 claims is narrower and is what is measured: adding a
    # disclosure entry adds **no** obligation, because `tagged` is
    # `suite == "goldens"` only. The goldens re-run does force a row and a bold
    # cell, in the same PR as its entry — the two suites differ here, and a reader
    # who assumed otherwise would get it backwards in whichever direction was
    # more convenient.
    before = set(history.check_readme(tmp_path))
    (tmp_path / "m09-disclosure.json").unlink()
    without = set(history.check_readme(tmp_path))
    assert before == without, (
        f"the disclosure entry added README obligation(s) {sorted(before - without)}. "
        "`check_readme`'s `tagged` set is `suite == \"goldens\"` only; if that changed, "
        "a disclosure entry now forces a README_GOLDENS row and decision 4's costing "
        "is wrong.")
    assert not any("m09" in p or "disclosure" in p for p in before), sorted(before)


def test_removing_disclosure_from_the_enum_refuses_the_entry(tmp_path):
    """The enum plant, red **by name** — the deletability audit's own mutation,
    run here so the check is not silent."""
    import jsonschema

    schema = json.loads(HISTORY_SCHEMA.read_text(encoding="utf-8"))
    schema["properties"]["suite"]["enum"] = [
        s for s in schema["properties"]["suite"]["enum"] if s != "disclosure"]
    entry = {"sha": "0" * 40, "suite": "disclosure", "target": "highlights-agent",
             "recorded_at": "2026-09-09T00:00:00+00:00",
             "scores": {"total": 5, "passed": 5, "failed": 0, "infra": 0, "pass_rate": 1.0},
             "cases": [{"id": "disclosure-101", "result": "PASS"}]}
    with pytest.raises(jsonschema.ValidationError) as exc:
        jsonschema.validate(entry, schema)
    assert "disclosure" in str(exc.value)


# --- the guards that were masking each other ----------------------------------
#
# **Both the lane's `--pack` guards and the runner's `--cases` guards deleted in
# silence**, and for the same reason: every malformed fixture lived in a temp
# directory, so the CONTAINMENT refusal fired first and the SHAPE branch was
# never reached. Remove the shape check and the test still passes, because the
# pack was refused for being out of tree. Remove the containment check and it
# still passes, because the pack is also malformed. Two guards, each the other's
# alibi, and the pair testing neither.
#
# Split: containment is measured with a pack that is perfectly well-formed and
# merely elsewhere, and shape with a pack committed INSIDE the tree. Each now
# fails for exactly one reason, and the reason is asserted.

WELL_FORMED = "- {id: disclosure-101, input: Write me a preview., asserts: []}\n"


def _outside(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "elsewhere.yaml"
    path.write_text(WELL_FORMED, encoding="utf-8")
    return path


def test_the_lane_refuses_a_well_formed_pack_that_is_outside_the_tree(tmp_path, capsys):
    """Containment alone: nothing about this pack is wrong except where it is.

    A verdict scored against a case set nobody else has cannot be re-derived,
    which is the whole of claim 6's last link. **The REASON is asserted**, or the
    test passes on the shape refusal and the two guards go on covering for each
    other — which is how they both came to be deletable in silence."""
    from pave import cli

    answers = _answers_file(tmp_path, {"disclosure-101": {"answer": BASE_ANSWER}})
    with pytest.raises(SystemExit) as exc:
        cli.evals_disclosure(["highlights-agent", "--pack", str(_outside(tmp_path)),
                              "--answers", str(answers), "--out", str(tmp_path / "v.json")])
    assert exc.value.code != 0
    captured = capsys.readouterr()
    assert "outside the repository" in captured.out + captured.err, (
        f"a well-formed pack outside the tree was refused for some other reason, or "
        f"accepted: {(captured.out + captured.err).strip()[:200]!r}")


@pytest.mark.parametrize("fixture,why", [
    ("malformed-mapping.yaml", "a mapping is not a list of cases"),
    ("malformed-idless.yaml", "a case that cannot be named breaks the chain's last link"),
    ("malformed-inputless.yaml", "a case with no input is scored against someone else's run"),
])
def test_the_lane_refuses_a_malformed_pack_that_is_inside_the_tree(tmp_path, fixture, why):
    """Shape alone: these are committed, so containment passes and the shape
    branch is the only thing standing. It was not, until this test."""
    from pave import cli

    answers = _answers_file(tmp_path, {"disclosure-101": {"answer": BASE_ANSWER}})
    with pytest.raises(SystemExit) as exc:
        cli.evals_disclosure(["highlights-agent", "--pack", str(FIXTURES / fixture),
                              "--answers", str(answers), "--out", str(tmp_path / "v.json")])
    assert exc.value.code != 0, why


@pytest.mark.parametrize("fixture", ["malformed-mapping.yaml", "malformed-idless.yaml"])
def test_the_runner_refuses_a_malformed_pack_that_is_inside_the_tree(fixture):
    """The same split, one directory over. `test_the_runner_refuses_a_missing_...`
    drives all six of its fixtures from `tmp_path`, so its three shape cases were
    refused by containment and the shape branch deleted clean."""
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--cases", str(FIXTURES / fixture), "--preflight-only"],
        capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode != 0, (
        f"{fixture} is committed inside the tree, so containment accepts it and the "
        f"shape check is the only guard left — and it accepted a pack that is not "
        f"a list of cases carrying `id`.")
    output = proc.stderr + proc.stdout
    assert "--cases" in output and "outside" not in output, (
        f"the refusal reads {output.strip()[:200]!r} — an in-tree pack must be "
        f"refused for its SHAPE, not for where it is.")

"""The captured fingerprint is unreachable by the scorer. ADR-066 step 0.

**Why this file is a precondition rather than a follow-up.** ADR-066 states the
condition in as many words: the three fields land inside the scorer's physical
reach, so *"a test must assert `evals/adversarial.py` never reads them, in the
same diff that adds them, or they are refused."* This is that test, and it ships
with the fields.

**What "unreachable" means here, and why it is provable rather than reviewed.**
`core.audit.observation_from_record` is the only doorway from an audit record to
the dict `evals/adversarial.py` scores — the module docstring says the caller must
have *fetched* the record from the lake, and everything downstream reads the
observation rather than the record. So the property is a property of a few lines
in one function: **it names the keys it copies, and `withheld` is not among them.**

That is asserted three ways, because each fails differently:

1. **By planting.** A record carrying a fingerprint produces an observation
   byte-identical to one without it, and every scored verdict is unchanged. This
   is the assertion that survives a refactor of how the doorway is written.
2. **By the writer.** `build_record` refuses a fragment holding anything but the
   three fields, and refuses one beside a decision that was not a block — so a
   `text` key cannot reach the lake even if a caller tries.
3. **By the schema.** `audit.schema.json` sets `additionalProperties: false` on
   the fragment, which takes two keys to change.

**What this does NOT claim.** It does not claim a digest is unlearnable in
principle — it claims a digest cannot be *graded*, which is the property G4 needs.
G4's failure mode is an assertion passing because the model's answer looked
polite; no assertion can read politeness out of a hash or a character count.

Hermetic (G8): pure functions and committed JSON, no cloud and no network.
Owning seat: Security (G4's boundary) · AI Quality (what a scorer may read).
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "platform" / "gateway" / "audit.schema.json"
sys.path.insert(0, str(ROOT / "platform" / "gateway"))

from core import audit, guardrail  # noqa: E402

#: A fingerprint of the guardrail's own placeholder — the comparison ADR-066's
#: step 0 makes offline. Built from the string the platform wrote itself, so this
#: fixture quotes nothing a model produced.
PLACEHOLDER = "Blocked by the Beacon gateway guardrail. The model response was withheld."


def _blocked_record(**extra):
    return audit.build_record(
        request_id="req-1", ts="2026-09-05T00:00:00Z", principal="p", service="svc",
        classification="internal", decision="blocked", mechanism="guardrail",
        model_id="m", guardrail={"id": "g", "version": "4", "action": "GUARDRAIL_INTERVENED"},
        **extra)


# --- 1. by planting: the doorway does not copy it -----------------------------

def test_a_record_carrying_a_fingerprint_yields_the_same_observation_as_one_without():
    """**The assertion that survives a rewrite of the doorway.**

    Not "the source does not mention `withheld`" — a substring check over source
    is the coupled-to-its-own-data failure this repository has already paid for
    twice, once on a guard that went red on the comment explaining the defect it
    watched for. This plants the thing and checks the output."""
    plain = audit.observation_from_record(_blocked_record())
    with_fingerprint = audit.observation_from_record(
        _blocked_record(withheld=guardrail.withheld_fingerprint(
            {"output": {"message": {"content": [{"text": PLACEHOLDER}]}}})))
    assert with_fingerprint == plain, (
        "the observation changed when a withheld fingerprint was added to the record. "
        "`observation_from_record` is the only doorway from a record to what "
        "`evals/adversarial.py` scores, and G4 requires that the text a guardrail stopped "
        "cannot reach it — not even as a length.")


@pytest.mark.parametrize("text", ["", PLACEHOLDER, "x" * 4000])
def test_no_fingerprint_of_any_length_reaches_the_observation(text):
    """Three lengths, because a length is the one field that is not a hash.

    An empty response, the placeholder, and something far longer than either
    produce three different fingerprints and one observation."""
    fingerprint = guardrail.withheld_fingerprint(
        {"output": {"message": {"content": [{"text": text}]}}})
    observation = audit.observation_from_record(_blocked_record(withheld=fingerprint))
    assert "withheld" not in observation
    assert not any("withheld" in str(key) for key in observation)
    assert fingerprint["sha256"] not in json.dumps(observation)
    assert audit.observation_from_record(_blocked_record()) == observation


def test_the_fingerprint_is_in_the_record_that_was_planted():
    """The plant must reach the record, or the three tests above prove nothing.

    Three wrong conclusions in one prior PR came from mutations that never ran."""
    record = _blocked_record(withheld=guardrail.withheld_fingerprint(
        {"output": {"message": {"content": [{"text": PLACEHOLDER}]}}}))
    assert record["withheld"]["present"] is True
    assert record["withheld"]["chars"] == len(PLACEHOLDER)


# --- 2. by the writer: a fragment that could carry text is refused -------------

def test_the_fragment_may_hold_only_the_three_content_free_fields():
    good = {"present": True, "chars": 10, "sha256": "a" * 64}
    _blocked_record(withheld=good)  # the control: the legal shape is accepted

    for extra in ({"text": "what the model said"}, {"answer": "..."}, {"excerpt": "..."}):
        with pytest.raises(ValueError, match="withheld fragment carries"):
            _blocked_record(withheld={**good, **extra})


def test_a_fingerprint_beside_a_decision_that_was_not_blocked_is_refused():
    """Nothing was withheld from a call that was not blocked.

    Without this, a digest of *served* output could enter the lake — text the
    viewer received, fingerprinted for no reason, one refactor away from a field
    that quotes it."""
    with pytest.raises(ValueError, match="nothing was withheld"):
        audit.build_record(
            request_id="r", ts="t", principal="p", service="s", classification="internal",
            decision="allowed", mechanism="none", model_id="m",
            withheld={"present": True, "chars": 1, "sha256": "b" * 64})


def test_the_allowlist_is_a_closed_set_and_names_no_content_field():
    assert frozenset({"present", "chars", "sha256"}) == audit.WITHHELD_FIELDS, (
        "the withheld allowlist has changed. It is the closed set that makes "
        "'this fragment cannot carry the text' a property rather than a review comment.")


# --- 3. by the schema: two keys to widen it -----------------------------------

def test_the_schema_forbids_additional_properties_on_the_fragment():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["withheld"]
    assert schema["additionalProperties"] is False, (
        "the withheld fragment accepts additional properties. `audit.schema.json` takes "
        "two keys, and that is the point: widening this fragment must not be a one-seat "
        "edit.")
    assert set(schema["properties"]) == {"present", "chars", "sha256"}
    assert schema["properties"]["sha256"]["pattern"] == "^[0-9a-f]{64}$", (
        "the digest field no longer has to be a digest. A free-form string here is where "
        "the text goes.")


# --- the fingerprint itself ---------------------------------------------------

def test_the_fingerprint_never_raises_whatever_the_response_looks_like():
    """It is a diagnostic, not a control (G2).

    A control that errors must block. A diagnostic that can raise would acquire
    the power to fail a refusal that was otherwise correct, which is worse than
    having no diagnostic at all."""
    for response in (None, {}, {"output": None}, {"output": {"message": {}}},
                     {"output": {"message": {"content": "not a list"}}},
                     {"output": {"message": {"content": [{}, {"text": None}, "junk"]}}}):
        result = guardrail.withheld_fingerprint(copy.deepcopy(response))
        assert result["present"] is False and result["chars"] == 0


def test_the_digest_distinguishes_the_placeholder_from_anything_else():
    """The whole of step 0 is this comparison, so it is asserted rather than assumed.

    If the blocked response carries the placeholder, the digest equals the digest
    of a string the platform wrote. If it carries anything else, it does not —
    and *what* it carries becomes the next question."""
    placeholder = guardrail.withheld_fingerprint(
        {"output": {"message": {"content": [{"text": PLACEHOLDER}]}}})
    other = guardrail.withheld_fingerprint(
        {"output": {"message": {"content": [{"text": PLACEHOLDER + " "}]}}})
    assert placeholder["sha256"] != other["sha256"], (
        "the digest does not separate the placeholder from a near neighbour, so step 0 "
        "cannot tell 'Bedrock withheld the text' from 'Bedrock returned something else'.")

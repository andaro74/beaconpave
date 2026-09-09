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

**ADR-071 (M07 PR 3): the store, and the boundary around it.** The gateway now
holds the text it refused, in a second bucket keyed by the record's own id.
The second half of this file asserts that the boundary moved with the capture
and not past it: a text planted through the real loop leaves the observation
unchanged on every channel; the record carries no pointer to the store and
cannot be given one; the store object describes exactly the text the record
describes; and nothing under `evals/`, `pave/` or `tools/` can name the store
— the reader is one file, on a two-key rule. ADR-069's route (5), capture
time, closes here; routes (1), (3) and (4) close in
`tests/test_adversarial_scoring.py`.

**This file is on the `core/audit.py` two-key rule** (Platform Engineering,
Security) since ADR-071: the doorway and the test that plants through it are
weakened together or not at all.

Hermetic (G8): pure functions and committed JSON, no cloud and no network.
Owning seat: Security (G4's boundary) · AI Quality (what a scorer may read).
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import sys

import jsonschema
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "platform" / "gateway" / "audit.schema.json"
sys.path.insert(0, str(ROOT / "platform" / "gateway"))

from core import audit, guardrail, toolloop, toolplane, withheld  # noqa: E402
from core import cedar as cedar_module  # noqa: E402

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


# =============================================================================
# ADR-071: the store, and the boundary around it
# =============================================================================

POLICIES = cedar_module.parse(
    (ROOT / "platform" / "gateway" / "policy" / "tools.cedar").read_text(encoding="utf-8"))
CONTRACTS = json.loads(
    (ROOT / "platform" / "gateway" / "policy" / "tools.contracts.json").read_text(encoding="utf-8"))
RESULT = {"results": [{"id": "t001", "title": "Jefferson Derby", "brand": "meridian-sports",
                       "type": "live-event", "entitlement": "sports-tier",
                       "event": "jefferson-derby", "starts": "2026-09-13T19:00:00Z"}]}
USAGE = {"inputTokens": 900, "outputTokens": 60}
PLANT = "THE PLANTED TEXT: how to get around the blackout"
OTHER = "a different refused text, of a different length"


class _Converse:
    def __init__(self, *responses):
        self.responses = list(responses)

    def __call__(self, transcript):
        return self.responses.pop(0), 120


class _Tool:
    def __init__(self, payload):
        self.payload = payload

    def __call__(self, tool_id, args):
        return toolloop.ToolReply(payload=self.payload)


class _Inspect:
    """Blocks the first assessment on `channel` and allows everything else,
    stamping a pair per channel as the deployed gateway does."""

    def __init__(self, channel):
        self.channel = channel

    def __call__(self, text, *, channel):
        pair = ("gr-tool-output", "2") if channel == "tool_output" else ("gr-main", "4")
        blocked = channel == self.channel
        return guardrail.GuardrailOutcome(blocked, ("PROMPT_ATTACK",) if blocked else (),
                                          (channel,), *pair)


def _tool_use(args):
    return {"stopReason": "tool_use", "usage": dict(USAGE), "output": {"message": {
        "role": "assistant", "content": [{"toolUse": {"toolUseId": "tu-1",
                                                      "name": "catalog-search",
                                                      "input": args}}]}}}


def _final(text):
    return {"stopReason": "end_turn", "usage": dict(USAGE),
            "output": {"message": {"role": "assistant", "content": [{"text": text}]}}}


def _refused_on(channel: str, text: str) -> toolloop.TurnOutcome:
    """A real turn through `run_turn`, blocked on `channel`, with `text` placed
    where that channel would carry it."""
    question = text if channel == "question" else "what is on tonight"
    args = {"query": text} if channel == "tool_request" else {"query": "derby"}
    payload = ({"results": [dict(RESULT["results"][0], title=text)]}
               if channel == "tool_output" else RESULT)
    answer = text if channel == "answer" else "done"
    plane = toolplane.ToolPlane(policies=POLICIES, contracts=CONTRACTS)
    outcome = toolloop.run_turn(
        plane=plane, principal="highlights-agent",
        messages=[{"role": "user", "content": [{"text": question}]}],
        converse=_Converse(_tool_use(args), _final(answer)), call_tool=_Tool(payload),
        inspect=_Inspect(channel))
    assert outcome.status == toolloop.BLOCKED and outcome.guardrail.channels == (channel,)
    assert text in outcome.refused, "the plant did not reach the refused text"
    return outcome


def _record_as_the_handler_writes_it(outcome, **extra) -> dict:
    """The blocked record, composed the way `handler.py`'s blocked branch is
    pinned to compose it: the fragment from the outcome's own pair, `withheld`
    as `guardrail.fingerprint_text(outcome.refused)`. A hand-built fixture
    proves nothing on its own; what ties this one to the handler is
    `tests/test_handler_wiring.py`, which pins both expressions on the source."""
    applied = outcome.guardrail
    usage = outcome.usage if "tokens_in" in outcome.usage else None
    return audit.build_record(
        request_id="req-1", ts="2026-09-05T00:00:00Z", principal="p", service="svc",
        classification="internal", decision="blocked", mechanism="guardrail", model_id="m",
        guardrail=applied.as_record_fragment(applied.guardrail_id, applied.version),
        withheld=guardrail.fingerprint_text(outcome.refused), usage=usage, **extra)


CHANNELS_THE_LOOP_LABELS = ["question", "tool_request", "tool_output", "answer"]


@pytest.mark.parametrize("channel", CHANNELS_THE_LOOP_LABELS)
def test_a_planted_text_leaves_the_observation_unchanged_on_every_channel(channel):
    """**SPEC/07's PR 3 row, measured through the real path.** A text planted
    where each channel carries it, refused by the loop, described by the record
    the handler is pinned to write: the observation the scorer reads is
    byte-identical to the one for the same block on a different text, and to
    the one for the same block described by nothing at all. The text moves the
    fingerprint and the store and nothing the scorer can see."""
    outcome = _refused_on(channel, PLANT)
    planted = _record_as_the_handler_writes_it(outcome)
    other = _record_as_the_handler_writes_it(_refused_on(channel, OTHER))
    assert planted["withheld"] != other["withheld"], "the two plants did not differ"
    assert planted["withheld"]["chars"] == len(outcome.refused), "the fingerprint is of the refused text"
    bare = dict(planted)
    del bare["withheld"]

    observed = audit.observation_from_record(planted)
    assert observed == audit.observation_from_record(other)
    assert observed == audit.observation_from_record(bare)
    assert PLANT not in json.dumps(observed) and planted["withheld"]["sha256"] not in json.dumps(observed)
    assert observed["guardrail_blocked"] and observed["channels"] == [channel]


@pytest.mark.parametrize("channel", CHANNELS_THE_LOOP_LABELS)
def test_the_record_carries_no_pointer_to_the_store_and_cannot_be_given_one(channel):
    """The store is keyed by the record's id; the record names the store nowhere.
    Asserted three ways: the record validates against the schema, whose
    `withheld` is closed; the store's vocabulary and the planted text appear in
    no key and no value; and every spelling of a pointer is refused by
    `build_record` before it can be written."""
    outcome = _refused_on(channel, PLANT)
    record = _record_as_the_handler_writes_it(outcome)
    jsonschema.validate(record, json.loads(SCHEMA.read_text(encoding="utf-8")))
    assert PLANT not in json.dumps(record), "the record quotes the text"

    def leaves(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key
                yield from leaves(value)
        elif isinstance(node, list):
            for value in node:
                yield from leaves(value)
        elif isinstance(node, str):
            yield node
    pointer_words = {withheld.STORE_OUTPUT, withheld.STORE_ENV, "store", "bucket", "key",
                     "url", "held", "text"}
    assert not pointer_words & set(leaves(record)), (
        f"the record carries {sorted(pointer_words & set(leaves(record)))}")
    assert set(record["withheld"]) == {"present", "chars", "sha256"}

    good = record["withheld"]
    for pointer in ({"key": record["record_id"]}, {"store": "a-bucket"},
                    {"bucket": "a-bucket"}, {"url": "s3://a-bucket/" + record["record_id"]},
                    {"text": PLANT}):
        with pytest.raises(ValueError, match="withheld fragment carries"):
            audit.build_record(
                request_id="r", ts="t", principal="p", service="s", classification="internal",
                decision="blocked", mechanism="guardrail", model_id="m",
                guardrail=record["guardrail"], withheld={**good, **pointer})


def test_the_held_object_is_the_text_keyed_by_the_record_id_and_describes_nothing_else():
    outcome = _refused_on("answer", PLANT)
    record = _record_as_the_handler_writes_it(outcome)
    put = withheld.held_object("the-store", record, outcome.refused)

    assert put["Bucket"] == "the-store"
    assert put["Key"] == record["record_id"], "the store is keyed by the record id, verbatim"
    assert put["Body"] == outcome.refused.encode("utf-8")
    assert put["ContentType"] == withheld.CONTENT_TYPE
    assert set(put["Metadata"]) == withheld.METADATA_FIELDS
    assert put["Metadata"]["sha256"] == record["withheld"]["sha256"]
    assert put["Metadata"]["chars"] == str(record["withheld"]["chars"])
    assert put["Metadata"]["channel"] == "answer"
    assert put["Metadata"]["guardrail-id"] == "gr-main"
    assert put["Metadata"]["classification"] == "internal"
    assert PLANT not in json.dumps(put["Metadata"]), "the metadata quotes the text"
    assert set(put) == {"Bucket", "Key", "Body", "ContentType", "Metadata"}


def test_the_held_object_must_describe_exactly_the_text_the_record_describes():
    """A handler that stored one text while recording another is refused, not
    written. A store object that disagrees with its record looks like evidence."""
    outcome = _refused_on("answer", PLANT)
    record = _record_as_the_handler_writes_it(outcome)
    withheld.held_object("the-store", record, outcome.refused)  # the control
    with pytest.raises(ValueError, match="does not match the record"):
        withheld.held_object("the-store", record, OTHER)
    with pytest.raises(ValueError, match="does not match the record"):
        withheld.held_object("the-store", record, outcome.refused + " ")
    with pytest.raises(ValueError, match="does not match the record"):
        withheld.held_object("the-store", record, None)


def test_the_held_object_is_refused_beside_a_record_that_was_not_blocked():
    allowed = audit.build_record(
        request_id="r", ts="t", principal="p", service="s", classification="internal",
        decision="allowed", mechanism="none", model_id="m")
    with pytest.raises(ValueError, match="not blocked"):
        withheld.held_object("the-store", allowed, "served text")
    described_nothing = audit.build_record(
        request_id="r", ts="t", principal="p", service="s", classification="internal",
        decision="blocked", mechanism="guardrail", model_id="m",
        guardrail={"id": "g", "version": "4", "action": "GUARDRAIL_INTERVENED"})
    with pytest.raises(ValueError, match="no `withheld` fragment"):
        withheld.held_object("the-store", described_nothing, "text")
    with pytest.raises(ValueError, match="unnamed"):
        withheld.held_object("", _record_as_the_handler_writes_it(_refused_on("answer", PLANT)),
                             PLANT)


def test_verify_ties_a_store_object_to_its_record_and_names_each_way_it_can_fail():
    outcome = _refused_on("tool_request", PLANT)
    record = _record_as_the_handler_writes_it(outcome)
    put = withheld.held_object("the-store", record, outcome.refused)
    body, metadata = put["Body"], put["Metadata"]

    assert withheld.verify(record, body, metadata) == []
    assert withheld.verify(record, None, None) == [
        "missing: the record says text was withheld and the store holds no object under "
        "its record_id"]
    # A different text with NO metadata: the body alone must produce both the
    # digest and the length defect. With the metadata present the mutation
    # "verify ignores the body's digest" survived, because the metadata branch
    # reported a sha256 defect of its own and `any(...)` was satisfied by it.
    other = withheld.verify(record, OTHER.encode("utf-8"), {})
    assert [d.split(":")[0] for d in other] == ["sha256", "chars"], other
    assert other[0].endswith(withheld.fingerprint_text(OTHER)["sha256"])
    assert withheld.verify(record, body, dict(metadata, channel="answer")) == [
        "channel: record ['tool_request'], object 'answer'"]
    assert withheld.verify(record, body, dict(metadata, sha256="0" * 64)) == [
        "sha256: the object's metadata disagrees with its own body"]
    assert withheld.verify(record, body, {}) == [], "metadata is optional; the body is the check"


# --- no reader under evals/ or pave/ ------------------------------------------

#: What a module would have to say to reach the store. Imports first — the
#: module itself and its reader — then the names the stack, the environment
#: and the pure module give it, then the record key the fingerprint travels
#: under, which no scorer may subscript either (`observation_from_record` is
#: the only doorway, and it does not).
STORE_MODULES = {"core.withheld", "withheld", "read_withheld"}
STORE_WORDS = {withheld.STORE_OUTPUT, withheld.STORE_ENV, "WITHHELD_STORE", "core.withheld",
               "read_withheld", "held_object", "fetch_held", "withheld"}
#: `milestones` joined at M08b PR 2 (Security seat, round 1): the three readers
#: that decide the milestone's claim, the residual and the answer-channel
#: reading live there, and a store import planted into two of them survived
#: the whole suite because no root reached them. A reader that can name the
#: store can read it one line later, wherever it sits.
SCORER_ROOTS = ("evals", "pave", "tools", "milestones")

#: Directories inside the tree whose `.py` files are not this repository's source:
#: build output, a virtualenv, git's own storage, and the agent worktrees under
#: `.claude/`, which hold whole copies of the tree and would be scanned as if they
#: were it.
SKIP_DIRS = {"__pycache__", "node_modules", "cdk.out", ".claude", ".venv", ".git"}


def _sources(*roots):
    """Every `.py` under `roots`, skipping `SKIP_DIRS` **by tree-relative path**.

    **The relativity is the whole of it, and it was wrong** (ADR-074, M08b PR 4).
    This matched `SKIP_DIRS` against `path.parts` of the ABSOLUTE path, so a
    checkout living anywhere beneath a directory named `.claude` -- which is
    exactly where this repository's own seat worktrees live, one per review round,
    created by `git worktree add .claude/worktrees/agent-<id>` -- had every one of
    its files skipped and this scan yielded nothing.

    Measured on `a9cf896` in a worktree under `.claude/`: the parametrised scan
    below generated **zero** cases, `test_the_scan_has_something_to_scan` failed at
    0 files, and `test_the_store_has_exactly_two_callers_in_the_repository` failed
    with `importers == []` -- a check whose job is to refuse a THIRD importer
    reporting that there are none, which is the direction that reads as a passing
    property to anyone who does not look at the number. Two of the three seats who
    ever ran this file ran it in such a worktree.

    The same hazard applies to `.venv` and `.git`: a checkout at
    `~/src/.venv/beaconpave` is unusual, and a checkout at
    `/home/x/.claude/worktrees/...` is this repository's normal review setup.
    """
    for root in roots:
        base = ROOT / root
        for path in sorted(base.rglob("*.py")):
            if not SKIP_DIRS & set(path.relative_to(ROOT).parts):
                yield path


def _reaches_the_store(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [f"import {a.name}" for a in node.names
                      if a.name in STORE_MODULES or a.name.endswith(".withheld")]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "") in STORE_MODULES or (node.module or "").endswith("withheld"):
                found.append(f"from {node.module} import ...")
            found += [f"from {node.module} import {a.name}" for a in node.names
                      if a.name in STORE_MODULES | STORE_WORDS]
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in STORE_WORDS:
                found.append(f"the string {node.value!r}")
        elif isinstance(node, ast.Name) and node.id in STORE_WORDS:
            found.append(f"the name {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in STORE_WORDS:
            found.append(f"the attribute .{node.attr}")
    return found


def test_the_scan_has_something_to_scan():
    """**The anti-vacuity guard, reading the real tree rather than a constant.**

    `>= 20` was the whole of this, and a magic number cannot tell "the scan is
    broken" from "the repository shrank" -- it went red under a `.claude/`
    checkout, which is the right answer for the wrong reason, and it would have
    stayed green on a scan that silently lost a third of the tree.

    So the count is compared to an independent walk that does not go through
    `_sources` at all: every `.py` under the four roots, minus the ones a
    tree-relative `SKIP_DIRS` genuinely removes. If those two disagree, the
    skipping logic is dropping files the roots really hold, whatever the absolute
    number happens to be. The floor stays beneath it, because two checks that both
    read the same broken helper agree with each other perfectly."""
    scanned = sorted(_sources(*SCORER_ROOTS))
    real = sorted(
        path for root in SCORER_ROOTS for path in (ROOT / root).rglob("*.py")
        if not SKIP_DIRS & set(path.relative_to(ROOT).parts)
    )
    assert scanned == real, (
        f"the scan reaches {len(scanned)} files and the tree holds {len(real)} under the "
        f"same roots. Missing: {sorted(set(real) - set(scanned))[:5]}. A scanner that "
        "silently reaches fewer files than exist reports a property of its own bug.")
    assert len(scanned) >= 20, (
        f"only {len(scanned)} source files under {list(SCORER_ROOTS)}. Either the tree "
        "moved or this is not a checkout of this repository — and every parametrised "
        "case below would report green over nothing.")


def test_the_scan_is_not_defeated_by_where_the_checkout_lives(tmp_path, monkeypatch):
    """**The regression this fix exists for, run through `_sources` itself.**

    A tree at `<anything>/.claude/<repo>` is what a seat worktree is, and this
    repository creates one per seat per review round. Measured on `a9cf896` in
    such a worktree: the parametrised scan below generated **zero** cases and the
    file reported `2 failed, 23 passed, 1 skipped` -- 26 items where an honest
    checkout runs 64.

    **Why this drives the real helper rather than re-implementing its condition.**
    A first version compared `SKIP_DIRS & set(relative.parts)` against
    `SKIP_DIRS & set(absolute.parts)` inline, and measured what that bought:
    reverting `_sources` to the absolute reading left this file **green in a
    normal checkout** and red only in a worktree under `.claude/`. A guard that
    cannot see its own fix reverted is the shape ADR-043 recorded four of ten
    planted weakenings surviving under. So `ROOT` is repointed at a planted tree
    whose absolute path contains each `SKIP_DIRS` name in turn, and `_sources` is
    called: with the tree-relative reading it finds the planted module, and with
    the absolute one it finds nothing.
    """
    module = sys.modules[__name__]
    for name in sorted(SKIP_DIRS):
        checkout = tmp_path / name / "checkout"
        (checkout / "evals").mkdir(parents=True)
        planted = checkout / "evals" / "module.py"
        planted.write_text("x = 1" + chr(10), encoding="utf-8")

        monkeypatch.setattr(module, "ROOT", checkout)
        found = list(_sources("evals"))
        assert found == [planted], (
            f"a checkout under `{name}/` skips its own sources: `_sources` reached "
            f"{[str(f) for f in found]} in a tree holding {planted}. Every parametrised "
            "case below would report green over nothing, and "
            "`test_the_store_has_exactly_two_callers_in_the_repository` would report the "
            "store has no importers at all — which reads as a passing property.")

        # And the condition really is present, or the assertion above proves nothing.
        assert SKIP_DIRS & set(planted.parts), (
            f"`{name}` does not appear in {planted}, so this case has stopped "
            "reproducing the state it is named for.")


@pytest.mark.parametrize("path", list(_sources(*SCORER_ROOTS)),
                         ids=lambda p: str(p.relative_to(ROOT)).replace("\\", "/"))
def test_no_module_under_evals_pave_or_tools_can_name_the_store(path):
    """**SPEC/07 constraint 6: no reader under `evals/` or `pave/`** (`tools/`
    too, fail-closed). Not "does not read the store" — a module that can name
    it can read it one line later, so the vocabulary is what is forbidden: the
    store module and its reader as imports, the bucket's output and
    environment names, the pure module's functions, and the record key the
    fingerprint travels under. A scorer that could read the text is refused
    (ADR-064)."""
    found = _reaches_the_store(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    assert not found, (
        f"{path.relative_to(ROOT)} can reach the refused-content store: {found}. Nothing "
        "under evals/, pave/ or tools/ may name it (SPEC/07 constraint 6, ADR-071).")


def test_the_store_has_exactly_two_callers_in_the_repository():
    """The writer and the reader, and no third. `handler.py` puts; `read_withheld.py`
    gets, verifies and shows; both are on two-key rules. A third importer — the
    goldens harness copying text into a sidecar, say — is the reader escaping
    the file the rule was drawn around."""
    importers = set()
    for path in _sources("platform", "services", "evals", "pave", "tools", "templates",
                         "milestones"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = ([a.name for a in node.names] if isinstance(node, (ast.Import, ast.ImportFrom))
                     else [])
            module = getattr(node, "module", None) or ""
            if (module in {"core", "core.withheld"} and "withheld" in names) \
                    or "core.withheld" in names or module == "core.withheld":
                importers.add(str(path.relative_to(ROOT)).replace("\\", "/"))
    assert importers == {"platform/gateway/handler.py",
                         "services/highlights-agent/read_withheld.py"}, (
        f"the store's importers are {sorted(importers)}; exactly the gateway and the one "
        "reader may name core.withheld (ADR-071)")

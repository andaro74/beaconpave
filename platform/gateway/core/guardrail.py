"""
Reading a guardrail assessment into a decision.

Pure, so the interpretation can be proven against committed fixtures rather than
against whatever the service happened to return the day someone looked. That
matters more here than in most places: this function decides whether a probe
passes, so a bug in it moves the adversarial score without moving the system.

**Attribution is recorded, not just the verdict.** `assessed` names which policy
fired — PROMPT_ATTACK, a denied topic, a PII entity — because "9/10 blocked" and
"9/10 blocked, 6 of them by one filter" are different findings, and only the
second one tells the Security seat where the corpus is under-covering.

Owning seat: Security / Red Team.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

#: Bedrock's stop reason when a guardrail stopped the turn.
STOP_REASON_INTERVENED = "guardrail_intervened"

#: Assessment actions that mean the content was actually stopped. `ANONYMIZED`
#: is deliberately absent: masking a PII entity lets the turn proceed, so it is
#: not a block and must not be counted as one.
BLOCKING_ACTIONS = frozenset({"BLOCKED"})


@dataclass(frozen=True)
class GuardrailOutcome:
    intervened: bool
    assessed: tuple[str, ...] = ()
    #: Which channels the blocked content arrived on. A TUPLE because both sides
    #: can fire on one turn, and the alternatives are worse: a compound string
    #: invents a third spelling for two things, and a second parallel field is two
    #: sources for one decision.
    #:
    #: **Emitted whenever the guardrail intervened, including when empty** — not
    #: "only when set" (ADR-040 decision 1). ADR-036 specified when-set, to keep a
    #: blocked turn's fragment byte-identical to M04's. ADR-038 amendment 1 is why
    #: that is wrong: `assessed` used the same rule one layer up, and an absent key
    #: became ambiguous between a new untraced block and a record predating the
    #: field — so the live false-pass shape was routed into the historical
    #: population and credited. Omitting this key on an empty tuple reintroduces
    #: that bug verbatim.
    #:
    #: The cost is real and was conceded in ADR-036 amendment 1: a BLOCKED turn's
    #: fragment is no longer byte-identical to M04's. An UNASSESSED turn's is.
    #:
    #: **The fragment, not the whole record.** The AI Quality seat checked the
    #: wider claim and it does not hold: a turn now also records `guard_ms`, so
    #: the record differs from M04's by that key. Nothing an observation is
    #: derived from moves — `observation_from_record` reads `decision`,
    #: `mechanism` and this fragment, and none of those change — but the claim is
    #: written here in the form that is true rather than the form that is
    #: flattering.
    channels: tuple[str, ...] = ()
    #: Which guardrail produced this assessment (ADR-070 amendment 2). Stamped
    #: by `interpret_apply` from the pair the gateway pinned at the call site, so
    #: the audit record can name the guardrail whose assessment it reports rather
    #: than whichever pair the handler happened to reach for. `None` only on an
    #: outcome nothing assessed; `as_record_fragment` refuses to write one.
    guardrail_id: str | None = None
    version: str | None = None

    def as_record_fragment(self, guardrail_id: str, version: str) -> dict:
        """The `guardrail` object in an audit record. `version` is required and
        must be a published version — see ADR-018.

        **Refuses a missing id or version.** Under option B (ADR-070) the handler
        passes the pair the outcome carries, and an outcome that carries none is
        one no inspection stamped. Writing `"version": null` would validate
        nowhere and, worse, would land in the lake as a record that names no
        instrument — the ADR-018 hazard as a null."""
        if not guardrail_id or not version:
            raise ValueError(
                f"a guardrail fragment must name a published guardrail; got "
                f"id={guardrail_id!r} version={version!r}. The outcome this was built "
                "from was not stamped by `interpret_apply` (ADR-070 amendment 2).")
        fragment = {
            "id": guardrail_id,
            "version": version,
            "action": "GUARDRAIL_INTERVENED" if self.intervened else "NONE",
            "assessed": list(self.assessed),
        }
        if self.intervened:
            fragment["channels"] = list(self.channels)
        return fragment

    def as_response_fields(self) -> dict:
        """The guardrail-derived keys the gateway returns to the caller on a block.

        **This lived in `handler.py` and had to move (ADR-039).** That module is
        deliberately outside the hermetic surface because it imports boto3, and
        `tests/` is in `HERMETIC_ROOTS`, so nothing under `tests/` can import it —
        which is why `test_handler_wiring.py` parses the handler's source rather
        than running it, and why the two lines that read this dataclass on the
        BLOCKED path were executed by no test at all.

        Measured before the move: renaming a field on this frozen dataclass and
        updating every test a diligent implementer would update left the full
        suite green at 1526 while `handler.py` raised `AttributeError` on the
        guardrail-block path — the path G4 exists to evidence. A green gate over a
        crashing gateway.

        This module's own docstring names the rule: everything the gateway
        *decides* lives in `core/`, and growing logic in `handler.py` is "the first
        thing to defend". A field read is small enough to look like an exception
        and was exactly big enough to hide a crash."""
        fields = {"assessed": list(self.assessed)}
        if self.intervened:
            fields["channels"] = list(self.channels)
        return fields


def _blocked_names(assessment: dict) -> list[str]:
    """Pull the names of every policy that blocked, across the four policy types.

    Written defensively over `.get`: an assessment missing a policy type means
    that policy did not fire, and a KeyError here would turn a clean run into an
    INFRA failure."""
    names: list[str] = []

    for entry in assessment.get("contentPolicy", {}).get("filters", []):
        if entry.get("action") in BLOCKING_ACTIONS:
            names.append(entry.get("type", "UNKNOWN_FILTER"))

    for entry in assessment.get("topicPolicy", {}).get("topics", []):
        if entry.get("action") in BLOCKING_ACTIONS:
            names.append(f"TOPIC:{entry.get('name', 'UNKNOWN')}")

    sensitive = assessment.get("sensitiveInformationPolicy", {})
    for entry in sensitive.get("piiEntities", []):
        if entry.get("action") in BLOCKING_ACTIONS:
            names.append(f"PII:{entry.get('type', 'UNKNOWN')}")
    for entry in sensitive.get("regexes", []):
        if entry.get("action") in BLOCKING_ACTIONS:
            names.append(f"REGEX:{entry.get('name', 'UNKNOWN')}")

    word = assessment.get("wordPolicy", {})
    for entry in word.get("customWords", []):
        if entry.get("action") in BLOCKING_ACTIONS:
            names.append("WORD:custom")
    for entry in word.get("managedWordLists", []):
        if entry.get("action") in BLOCKING_ACTIONS:
            names.append(f"WORD:{entry.get('type', 'managed')}")

    return names


def interpret(response: dict) -> GuardrailOutcome:
    """Read a Bedrock `converse` response into a guardrail outcome.

    Two independent signals, and either one is sufficient. `stopReason` is the
    authoritative one; walking the trace catches the case where a guardrail
    intervened on output while the turn still reported a normal stop. Trusting
    only `stopReason` would under-report, and under-reporting a block is how a
    probe silently stops passing after a service update."""
    guardrail_trace = response.get("trace", {}).get("guardrail", {})

    # **Which SIDE produced each name, not just the names.** The channel is derived
    # from the assessment map a blocked name came out of, which is the only reading
    # that cannot disagree with `assessed`.
    #
    # A consequence worth stating, because it decides how much this field can do:
    # `channels == ()` if and only if `assessed == ()`. Both come from the same
    # `_blocked_names` calls, so an empty channel tuple is always an unattributed
    # block — which ADR-038 already fails on `assessed`. **This field's only new
    # power is saying which side**, and ADR-040 claims that and nothing more.
    names: list[str] = []
    channels: list[str] = []

    for by_id in guardrail_trace.get("inputAssessment", {}).values():
        found = _blocked_names(by_id)
        if found:
            names.extend(found)
            channels.append(CHANNEL_QUESTION)
    for per_guardrail in guardrail_trace.get("outputAssessments", {}).values():
        for assessment in per_guardrail:
            found = _blocked_names(assessment)
            if found:
                names.extend(found)
                channels.append(CHANNEL_ANSWER)

    intervened = response.get("stopReason") == STOP_REASON_INTERVENED or bool(names)
    # Sorted and de-duplicated: the same filter firing on input and output is one
    # attribution, and an unstable order would make two identical runs diff.
    return GuardrailOutcome(intervened, tuple(sorted(set(names))), tuple(sorted(set(channels))))


#: `ApplyGuardrail`'s verdict when it stopped the content. The Converse path
#: reports the same event as a `stopReason`; this is the same guardrail saying
#: the same thing through the API that takes content directly.
APPLY_ACTION_INTERVENED = "GUARDRAIL_INTERVENED"

#: The channels this module can be asked about, and the vocabulary the audit
#: record uses. Listed rather than free-form: a channel name is read by a person
#: deciding which seat owns a block, and two spellings of the same channel is how
#: "the guardrail never saw it" gets misread as "the guardrail allowed it".
#:
#: `SYSTEM` is here because in this deployment the system block carries retrieved
#: catalog data — the indirect-injection vector ADV-002 actually uses. It is not
#: named "trusted" anywhere: content the platform assembled from a data source is
#: not content the platform wrote.
CHANNEL_SYSTEM = "system"
CHANNEL_TOOL_OUTPUT = "tool_output"
#: The two sides of a Converse turn, added by ADR-040 so a record can say which
#: fired. `question` is a semantic name for a mechanical thing: Bedrock's
#: `inputAssessment` covers the WHOLE input, and in this deployment that is the
#: user turn only because `converse` does not assess the system block — measured
#: twice, and the reason M02's control arm ran at all (178 allowed of 185; the
#: clean system block blocks 3/3 under `ApplyGuardrail`).
#:
#: **If that ever changes, `question` silently absorbs system-block blocks and the
#: name lies** — and it is a cliff rather than a drift, because the same content
#: blocks unanimously. ADR-040 records it as open, alongside the fact that adding
#: these names makes `interpret_apply(..., channel="question")` LEGAL, so a caller
#: can now label platform content as the viewer's turn. `test_contracts.py` pins
#: this set literally for that reason.
CHANNEL_QUESTION = "question"
CHANNEL_ANSWER = "answer"
#: The model's output on a round that ends in `tool_use` (ADR-070). Text the
#: viewer never sees, addressed to the platform, carrying a JSON `input` the
#: plane validates. Under `converse`'s own guardrail it was assessed as output
#: and labelled `answer`, because Bedrock cannot tell which of the model's
#: outputs the viewer will be shown; only the loop can, and it labels this one.
#: No probe declares it, so under ADR-040's subset rule a block on it credits
#: nothing — correct, because the model arm sends no tools.
CHANNEL_TOOL_REQUEST = "tool_request"
CHANNELS = frozenset({CHANNEL_SYSTEM, CHANNEL_TOOL_OUTPUT, CHANNEL_QUESTION, CHANNEL_ANSWER,
                      CHANNEL_TOOL_REQUEST})


def interpret_apply(response: dict, *, channel: str, guardrail_id: str | None = None,
                    version: str | None = None) -> GuardrailOutcome:
    """Read an `ApplyGuardrail` response into the same outcome `interpret` returns.

    **A separate function rather than a widened `interpret`.** `interpret` decides
    whether a probe was blocked, it is the reader every recorded observation in
    this repository was produced by, and it is not in the adversarial instrument's
    digests — so a change to it would move what every past number means and move
    no digest at all (ADR-018's hazard, in the one place nothing is watching).
    Appending is the only edit to this module that cannot do that, so the edit is
    an append.

    The response shape differs from `converse`'s in exactly two ways: the verdict
    is `action` rather than `stopReason`, and the assessments arrive as a flat
    list rather than nested under input and per-guardrail output maps. The policy
    blocks inside them are identical, which is why `_blocked_names` is shared:
    two readers of the same assessment that could disagree is a worse defect than
    the duplication it would avoid.

    `guardrail_id` and `version` are the pair the caller pinned at the call site
    that produced `response`, carried onto the outcome so the audit record names
    the guardrail that actually assessed the content (ADR-070 amendment 2)."""
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel!r}; expected one of {sorted(CHANNELS)}")

    names: list[str] = []
    for assessment in response.get("assessments") or ():
        names.extend(_blocked_names(assessment))

    # Both signals, exactly as `interpret` reads both — and for the same reason.
    # Trusting `action` alone would under-report, and under-reporting a block is
    # how a probe silently stops passing after a service update.
    intervened = response.get("action") == APPLY_ACTION_INTERVENED or bool(names)
    return GuardrailOutcome(intervened, tuple(sorted(set(names))), (channel,),
                            guardrail_id, version)


#: The audit key the withheld-output fingerprint travels under.
#:
#: **One key, and nested, so G4's boundary is one name to forbid.** ADR-066 named
#: three flat fields (`answer_text_present`, `answer_text_len`,
#: `answer_text_sha256`); they are nested under this key instead, because the
#: assertion that matters is "the scorer's doorway never copies it" and a single
#: key makes that assertion total rather than a list somebody must keep current.
#: Recorded as a deviation at the end of ADR-066.
WITHHELD_KEY = "withheld"


def fingerprint_text(text: str | None) -> dict:
    """Describe a piece of text without quoting it: present, length, one-way digest.

    **This is what `withheld` carries under option B (ADR-070).** The gateway no
    longer receives Bedrock's placeholder on a block; it receives the model's own
    output, assesses it, and refuses to return it. The text the loop refused
    travels under `TurnOutcome.refused`, and the record describes that text with
    exactly the three fields ADR-066 step 0 fixed — the same closed set, the same
    G4 argument: a length cannot be graded for politeness and a digest cannot be
    graded at all. `None` is "nothing was held", which is the shape a block that
    produced no text leaves."""
    text = text if isinstance(text, str) else ""
    return {
        "present": bool(text),
        "chars": len(text),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def withheld_fingerprint(response: dict) -> dict | None:
    """What `converse` handed back on a blocked turn, described without quoting it.

    Kept for the reader of records written before ADR-070 and for the offline
    comparison ADR-066 step 0 made; the gateway itself fingerprints
    `TurnOutcome.refused` through `fingerprint_text` now, because under option B
    `converse` hands back nothing a guardrail stopped.

    **The question this exists to answer.** The gateway has held the blocked
    response on every one of M06b's 16 answer-channel refusals and never opened
    it. Nobody knows whether Bedrock returns the model's text alongside the
    intervention or replaces it with `blockedOutputsMessaging`. The whole capture
    argument of ADR-064 and the pricing of ADR-066 turn on which it is, and the
    answer costs one field.

    **Content-free by construction.** `chars` is a length and `sha256` is a
    one-way digest: neither can be reversed, and — the property G4 actually needs
    — **neither can be graded**. The failure G4 exists to prevent is an assertion
    that passes because the answer *looked* acceptable, and no assertion can read
    acceptability out of a hash. The digest is compared offline against `sha256`
    of the platform's own `blockedOutputsMessaging` string, which the platform
    wrote and is nobody's secret.

    **Total, never raising.** A malformed or unexpected response returns
    `{"present": False, ...}` rather than an exception. A diagnostic that can fail
    a refusal which is otherwise correct is worse than no diagnostic: G2 says an
    errored control blocks, and this is not a control — it must not acquire the
    power to stop one.
    """
    blocks = (((response or {}).get("output") or {}).get("message") or {}).get("content") or ()
    if not isinstance(blocks, (list, tuple)):
        blocks = ()
    text = "".join(block.get("text") or "" for block in blocks
                   if isinstance(block, dict) and isinstance(block.get("text"), str))
    return fingerprint_text(text)

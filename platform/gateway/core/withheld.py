"""
The refused-content store: where the text a guardrail stopped goes (ADR-071).

Under option B (ADR-070) the gateway holds the text every assessment refuses,
and returns none of it. The audit record describes that text — `withheld`:
present, length, one-way digest — and quotes nothing. This module is the other
half: the object that holds the text itself, in a bucket the audit lake never
references, **keyed by the record's own `record_id`, verbatim**. The store
points at the record. The record carries no pointer back, and cannot: `withheld`
is a closed three-field set in `core/audit.py`, `additionalProperties: false` in
the schema, and `build_record` refuses a fourth key. A reader goes record → store
by the id it already holds; nothing goes the other way.

**Pure.** `held_object` builds the `put_object` keyword arguments from a record
and the text; `verify` says whether an object read back describes the record it
is keyed to. Both are provable offline, which is where the G4 argument has to be
made: `tests/test_g4_capture_boundary.py` plants a text through the real loop and
asserts the observation the scorer reads does not move, and that no module under
`evals/` or `pave/` can name this one.

**Not an instrument.** No digest in `quality/adversarial/instruments.json` covers
this file, deliberately: the store is evidence for people — the Security seat
reading what its own control refused — and a scorer that could read it is refused
in ADR-064's words. `services/highlights-agent/read_withheld.py` is the only
reader, and a test pins that it stays the only one.

Owning seat: Platform Engineering (the mechanism) · Security (G4's boundary
moves with any capture).
"""
from __future__ import annotations

from core.guardrail import fingerprint_text

#: The stack output and environment variable that name the store. Named here so
#: the handler, the reader and the boundary test agree on one spelling — and so
#: the boundary test has one vocabulary to forbid under `evals/` and `pave/`.
STORE_OUTPUT = "WithheldStoreBucket"
STORE_ENV = "WITHHELD_STORE_BUCKET"

#: What an object in the store is. `text/plain`, because it is the text and
#: nothing else: no JSON, no framing, no field a later reader could grow into a
#: second record. The metadata carries what the record already says, so an
#: object can be checked against its record without reading the record.
CONTENT_TYPE = "text/plain; charset=utf-8"

METADATA_FIELDS = frozenset({
    "channel", "assessed", "guardrail-id", "guardrail-version", "sha256", "chars",
    "classification",
})


def held_object(bucket: str, record: dict, text: str | None) -> dict:
    """The `put_object` call that holds `text` for `record`.

    **The object must describe exactly the text the record describes.** The
    record's `withheld` fragment was computed from the same string by
    `guardrail.fingerprint_text`; it is recomputed here, by that function, and compared, so a
    handler that stored one text while recording another — or stored text for
    a record that was not a block — is refused rather than written. A store
    object that disagrees with its record is worse than a missing one: it looks
    like evidence.

    The key is the record id verbatim. One id, two buckets, no derivation a
    reader has to know.
    """
    if not bucket:
        raise ValueError("the store bucket is unnamed; nothing can be held")
    if record.get("decision") != "blocked":
        raise ValueError(
            f"held_object beside decision={record.get('decision')!r} — nothing was withheld "
            "from a turn that was not blocked, and the store holds refused text only")
    described = record.get("withheld")
    if not isinstance(described, dict):
        raise ValueError("the record carries no `withheld` fragment; the store cannot hold "
                         "text the record does not describe")
    text = text if isinstance(text, str) else ""
    actual = fingerprint_text(text)
    if actual != described:
        raise ValueError(
            f"the text does not match the record's withheld fragment "
            f"(record {described}, text {actual}); refusing to store text the record "
            "does not describe")
    fragment = record.get("guardrail") or {}
    metadata = {
        "channel": ",".join(fragment.get("channels") or ()),
        "assessed": ",".join(fragment.get("assessed") or ()),
        "guardrail-id": str(fragment.get("id") or ""),
        "guardrail-version": str(fragment.get("version") or ""),
        "sha256": actual["sha256"],
        "chars": str(actual["chars"]),
        "classification": str(record.get("classification") or ""),
    }
    assert set(metadata) == METADATA_FIELDS
    return {
        "Bucket": bucket,
        "Key": record["record_id"],
        "Body": text.encode("utf-8"),
        "ContentType": CONTENT_TYPE,
        "Metadata": metadata,
    }


def verify(record: dict, body: bytes | None, metadata: dict | None) -> list[str]:
    """Why an object read back from the store does not describe `record`.

    Empty means it does. Each defect is named rather than folded into a boolean,
    because a reader that prints `missing` and one that prints `mismatch` are
    telling the Security seat different things: the first is a lost write, the
    second is a record and an object that disagree about what was refused."""
    described = record.get("withheld") or {}
    if body is None:
        return ["missing: the record says text was withheld and the store holds no object "
                "under its record_id"]
    text = body.decode("utf-8")
    actual = fingerprint_text(text)
    defects = []
    if actual["sha256"] != described.get("sha256"):
        defects.append(f"sha256: record {described.get('sha256')}, object {actual['sha256']}")
    if actual["chars"] != described.get("chars"):
        defects.append(f"chars: record {described.get('chars')}, object {actual['chars']}")
    # The metadata is a cross-check when present and nothing when absent: the
    # body is what the record describes, and an object with no metadata is
    # still the text or is not.
    meta = dict(metadata or {})
    channels = set((record.get("guardrail") or {}).get("channels") or ())
    if "channel" in meta and set(filter(None, meta["channel"].split(","))) != channels:
        defects.append(f"channel: record {sorted(channels)}, object {meta['channel']!r}")
    if "sha256" in meta and meta["sha256"] != actual["sha256"]:
        defects.append("sha256: the object's metadata disagrees with its own body")
    return defects

"""
G5's router: classification decides what may reach a model, and `sensitive` is
refused by design.

**This policy is written from the data-governance position, not from the probe
corpus.** SPEC/01's honesty clause is explicit about the hazard: the ten probes
are frozen (ADR-009) and M01 configures the thing they are aimed at, so a rule
shaped to a probe's wording measures how well we read the corpus. The rule below
is a general statement — *a request seeking personal data about identifiable
subscribers is sensitive* — and it is expressed as subject terms crossed with
attribute terms so that it catches an exfiltration attempt nobody wrote down.
ADV-007 happens to fall inside it. That is the direction the implication is
allowed to run, and never the other one.

The deliberate consequence: this refuses "export the customer email list" and
"what is that viewer's phone number" as readily as it refuses the probe, and it
does not refuse "how many subscribers are in Jefferson City" — an aggregate over
people is not personal data about an identifiable one.

Owning seat: Data Governance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

#: Ordered least to most restricted. A service may handle its declared level and
#: everything below it.
LEVELS = ("public", "internal", "confidential", "sensitive")

#: Who the data is about. A request has to be about *people* before any attribute
#: term makes it personal data.
SUBJECT_TERMS = (
    "subscriber", "subscribers", "viewer", "viewers", "customer", "customers",
    "account holder", "account holders", "member", "members", "household", "households",
)

#: What is being sought about them. Deliberately attribute-shaped rather than
#: phrase-shaped: the policy is "personal data about a person", and these are the
#: categories that make data personal.
ATTRIBUTE_TERMS = (
    "name", "names", "address", "addresses", "email", "emails", "phone", "phone number",
    "payment", "card number", "credit card", "social security", "ssn", "date of birth",
    "home address", "contact detail", "contact details", "personal data",
    "personal information", "personally identifiable", "pii",
)

#: Aggregate framings. A count or a distribution over people is not personal data
#: about an identifiable person, and refusing it would make the gateway useless
#: for the analytics questions a media company legitimately asks.
AGGREGATE_TERMS = ("how many", "count of", "number of", "total number", "percentage of", "share of")


@dataclass(frozen=True)
class Classification:
    """The router's finding. `reasons` exists so a denial can be explained in the
    audit record: a refusal nobody can account for is indistinguishable from a
    bug, and it is the kind teams learn to route around."""

    level: str
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Routing:
    """The pre-invoke decision. `allowed=False` means no model is reached at all,
    which is why the audit record for it carries no usage — nothing was spent."""

    allowed: bool
    classification: str
    mechanism: str
    reasons: tuple[str, ...] = ()


def _mentions(text: str, terms: tuple[str, ...]) -> list[str]:
    """Whole-word containment. Substring matching would classify "renamed" as a
    request for a name, and a router that fires on fragments trains people to
    phrase around it."""
    lowered = text.lower()
    return [t for t in terms if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", lowered)]


def classify_request(text: str) -> Classification:
    """Classify what the request is asking for.

    Only two levels are reachable from text alone today: `sensitive` when the
    request seeks personal data about identifiable people, and `internal`
    otherwise. `confidential` needs a data catalog to recognise, which does not
    exist at this scale — recorded here rather than faked, because a router that
    returns a level it cannot actually detect would make G5 look enforced on an
    axis nothing checks."""
    subjects = _mentions(text, SUBJECT_TERMS)
    attributes = _mentions(text, ATTRIBUTE_TERMS)
    aggregates = _mentions(text, AGGREGATE_TERMS)

    if subjects and attributes and not aggregates:
        return Classification(
            "sensitive",
            (
                f"seeks {'/'.join(sorted(attributes))} about {'/'.join(sorted(subjects))}"
                " — personal data about identifiable people",
            ),
        )
    if subjects and attributes and aggregates:
        return Classification(
            "internal",
            ("aggregate over people, not personal data about an identifiable person",),
        )
    return Classification("internal", ())


def route(declared: str, text: str) -> Routing:
    """Apply G5. `sensitive` is refused by design — not "refused unless the
    service is cleared for it", because no clearance exists that makes it
    servable. A service may otherwise handle its declared level and below.

    Raises on an unknown declared level rather than defaulting: a typo in a
    manifest must not silently become the most permissive reading."""
    if declared not in LEVELS:
        raise ValueError(f"unknown declared classification {declared!r}; expected one of {LEVELS}")

    found = classify_request(text)

    if found.level == "sensitive":
        return Routing(False, "sensitive", "classification", found.reasons)

    if LEVELS.index(found.level) > LEVELS.index(declared):
        return Routing(
            False,
            found.level,
            "classification",
            (f"service is declared {declared}; request classifies as {found.level}",),
        )

    return Routing(True, found.level, "none", found.reasons)

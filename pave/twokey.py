"""
G9 — whoever feels a control's pain never solely controls its strength.

The two-key rule was designed to be enforced by CODEOWNERS: a threshold change
requires the owning seat *plus* AI Quality. That works when two humans exist.
GitHub does not let a pull request's author approve their own PR, so with one
operator the second key is not merely inconvenient — it is unobtainable, and the
rule silently degrades into a comment in `ROLES.md`.

So the second key is machine-checked instead. A PR touching a two-key path must
record the owning seat's disposition and its reasoning in the PR body:

    Two-Key-Disposition: ai-quality
    Two-Key-Rationale: raising the groundedness floor to 0.8 now that M03's
      calibration run published an agreement number that supports it

This is weaker than two humans and stronger than a convention. It cannot be
satisfied by clicking; it produces a written reason attached to the diff forever;
and because the check is required and unbypassable, it cannot be skipped quietly.
The failure mode it is built against is the one `ROLES.md` names: "update the
baseline" as the standard way eval gates get neutered.

AT SCALE: delete this check, put the seats back in CODEOWNERS, and require code
owner review. The path list here and the path list there are the same list — the
interface already matches.

Owning seat: AI Quality (the rules) · Platform Engineering (the mechanism).
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

#: A rationale shorter than this, or one of the placeholders below, is not a
#: disposition. The point of the trailer is the reasoning, not the keyword.
MIN_RATIONALE_CHARS = 24
PLACEHOLDER_RATIONALES = {"n/a", "na", "none", "-", "--", "tbd", "see above", "as discussed"}

DISPOSITION_RE = re.compile(r"^\s*Two-Key-Disposition:\s*(?P<seat>[a-z-]+)\s*$", re.MULTILINE)
RATIONALE_RE = re.compile(r"^\s*Two-Key-Rationale:\s*(?P<text>.+?)(?=^\s*[A-Z][A-Za-z-]*:|\Z)", re.MULTILINE | re.DOTALL)
ADR_RE = re.compile(r"^\s*ADR:\s*(?P<ref>\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Rule:
    """One two-key path class, straight out of docs/governance/ROLES.md."""

    what: str
    pattern: re.Pattern
    seats: tuple[str, ...]
    requires_adr: bool = False


#: Mirrors the two-key table in ROLES.md. Adding a row here is an AI Quality
#: change; removing one is the change this whole module exists to make visible.
RULES: tuple[Rule, ...] = (
    Rule(
        "golden cases, eval thresholds, and headroom policy",
        re.compile(r"^services/[^/]+/evals/"),
        ("ai-quality",),
    ),
    Rule(
        "judge rubric, calibration set, and agreement thresholds",
        re.compile(r"^quality/judge/"),
        ("ai-quality",),
    ),
    Rule(
        "the verdict schema — the contract the gate decides on",
        re.compile(r"^quality/verdicts/"),
        ("ai-quality",),
    ),
    Rule(
        "recorded baselines — a reset is a decision, never a cleanup",
        re.compile(r"^evals/history/"),
        ("ai-quality",),
    ),
    Rule(
        "gate criteria",
        re.compile(r"^\.github/workflows/quality-gate\.yml$"),
        ("ai-quality", "platform-eng"),
    ),
    Rule(
        "the two-key rules themselves",
        re.compile(r"^(pave/twokey\.py|\.github/workflows/two-key\.yml)$"),
        ("ai-quality", "platform-eng"),
    ),
    Rule(
        "consequence classes — raising one raises an action's blast radius",
        re.compile(r"^platform/registry/tools\.yaml$"),
        ("tool-owner", "legal-sp"),
    ),
    Rule(
        "the adversarial corpus — only Security may downgrade a probe, and only with an ADR",
        re.compile(r"^quality/adversarial/"),
        ("security",),
        requires_adr=True,
    ),
)


@dataclass(frozen=True)
class Attestation:
    seats: frozenset[str]
    rationale: str
    adr: str | None


def parse(body: str) -> Attestation:
    body = body or ""
    seats = {m.group("seat") for m in DISPOSITION_RE.finditer(body)}
    # Rationales may wrap across lines; collapse each to a single line so a
    # multi-line reason is not read as several short ones.
    parts = [" ".join(m.group("text").split()) for m in RATIONALE_RE.finditer(body)]
    adr_match = ADR_RE.search(body)
    return Attestation(frozenset(seats), " ".join(parts).strip(), adr_match.group("ref") if adr_match else None)


def triggered(changed: Sequence[str]) -> list[tuple[Rule, list[str]]]:
    """Which two-key rules the diff touches, and the files that touched them."""
    # NOT `lstrip("./")`: lstrip strips a character SET, so it eats the leading
    # dot of `.github/workflows/quality-gate.yml` and every gate-criteria change
    # silently stops matching. A path that fails to match here skips the check
    # entirely, which is the one failure mode this module cannot afford.
    normalized = []
    for p in changed:
        p = p.replace("\\", "/")
        normalized.append(p[2:] if p.startswith("./") else p)
    hits = []
    for rule in RULES:
        matched = [p for p in normalized if rule.pattern.search(p)]
        if matched:
            hits.append((rule, matched))
    return hits


def evaluate(changed: Sequence[str], body: str, repo_root=None) -> list[str]:
    """Returns the reasons this PR is blocked. Empty list means it may merge."""
    hits = triggered(changed)
    if not hits:
        return []

    att = parse(body)
    problems = []

    for rule, files in hits:
        missing = [s for s in rule.seats if s not in att.seats]
        if missing:
            problems.append(
                f"{rule.what}: changed {', '.join(sorted(files)[:3])}"
                f"{' …' if len(files) > 3 else ''} — missing disposition from "
                f"{', '.join(missing)}. Add `Two-Key-Disposition: <seat>` to the PR body."
            )
        if rule.requires_adr and not att.adr:
            problems.append(
                f"{rule.what}: requires an ADR. Add `ADR: docs/adr/ADR-0NN-<slug>.md` to the PR body."
            )

    if problems:
        return problems

    # Seats are attested. Now the reasoning has to actually be reasoning.
    stripped = att.rationale.strip().rstrip(".").lower()
    if not att.rationale:
        problems.append(
            "disposition recorded with no rationale. Add `Two-Key-Rationale: <why>` — "
            "the written reason is the point of the second key, not the keyword."
        )
    elif stripped in PLACEHOLDER_RATIONALES or len(att.rationale) < MIN_RATIONALE_CHARS:
        problems.append(
            f"rationale is {len(att.rationale)} characters and reads as a placeholder. "
            f"Say why this change is correct, in at least {MIN_RATIONALE_CHARS} characters."
        )

    if att.adr and repo_root is not None and not (repo_root / att.adr).is_file():
        problems.append(f"PR cites ADR `{att.adr}`, which does not exist in this tree.")

    return problems


def render(changed: Sequence[str], problems: Sequence[str]) -> str:
    hits = triggered(changed)
    if not hits:
        return "two-key: not required — this PR touches no two-key path"

    lines = ["two-key paths touched:"]
    for rule, files in hits:
        lines.append(f"  - {rule.what} [{', '.join(rule.seats)}]")
        lines.extend(f"      {f}" for f in sorted(files))

    if not problems:
        lines.append("\ntwo-key: SATISFIED — every owning seat disposed, with reasoning")
        return "\n".join(lines)

    lines.append("\ntwo-key: BLOCKED (G9)")
    lines.extend(f"  ✗ {p}" for p in problems)
    lines.append(
        "\nG9: whoever feels a control's pain never solely controls its strength.\n"
        "This is not a formality — a threshold or baseline change that cannot state\n"
        "its reasoning is the change this rule exists to stop."
    )
    return "\n".join(lines)

"""
The gate's decision function.

G2 — **gates fail closed; an errored gate blocks, never skips.** Everything in
this module exists to make that sentence executable. The gate is handed verdict
records and must answer one question: may this merge? It answers "no" for every
reason that is not an affirmative, schema-valid, non-blocking verdict — including
reasons that look like harness bugs rather than quality problems. A gate that
skips when it cannot tell is the failure mode this module is built to prevent.

Exit-code contract (the workflow depends on these, so they are part of the API):

  0  every supplied verdict parsed, validated, and reported PASS or ADVISORY
  1  at least one verdict reported FAIL — the code under test regressed;
     this pages the service team
  2  the gate could not establish that fact: a verdict file was missing,
     unparseable, schema-invalid, declared `fail_closed: false` in a blocking
     position, or reported INFRA — this pages the platform, not the team

Both 1 and 2 block. The split exists so that "the harness broke" and "the
service regressed" are never confused for each other, and never silently
converted into a pass. 2 outranks 1: if the gate's own inputs are untrustworthy,
that is the first thing to fix.

Owning seat: Platform Engineering (mechanism only — the *criteria* that produce a
FAIL are AI Quality's, and live in the eval harness, not here).
"""
from __future__ import annotations

import json
import pathlib
from collections.abc import Sequence
from dataclasses import dataclass, field

try:
    import jsonschema
except ImportError:  # pragma: no cover - surfaced as a contract failure below
    jsonschema = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERDICT_SCHEMA_PATH = ROOT / "quality" / "verdicts" / "schema.json"

EXIT_OK = 0
EXIT_QUALITY = 1
EXIT_CONTRACT = 2

#: Verdicts that permit a merge. Anything not in here blocks, including values
#: this module has never heard of — new verdict states are blocking until
#: someone teaches the gate what they mean.
NON_BLOCKING = frozenset({"PASS", "ADVISORY"})

OK = "ok"
QUALITY = "quality"
CONTRACT = "contract"


@dataclass(frozen=True)
class Finding:
    """One verdict file, and what the gate concluded about it."""

    path: str
    kind: str  # OK | QUALITY | CONTRACT
    reason: str
    verdict: str | None = None
    suite: str | None = None
    layer: str | None = None

    @property
    def blocks(self) -> bool:
        return self.kind != OK


@dataclass(frozen=True)
class Decision:
    findings: list[Finding] = field(default_factory=list)

    @property
    def blockers(self) -> list[Finding]:
        return [f for f in self.findings if f.blocks]

    @property
    def exit_code(self) -> int:
        """Contract failures outrank quality failures: if the gate cannot trust
        its own inputs, that is the first thing to fix."""
        kinds = {f.kind for f in self.findings}
        if CONTRACT in kinds:
            return EXIT_CONTRACT
        if QUALITY in kinds:
            return EXIT_QUALITY
        return EXIT_OK

    @property
    def blocked(self) -> bool:
        return self.exit_code != EXIT_OK


def load_verdict_schema(path: pathlib.Path = VERDICT_SCHEMA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _inspect(path_str: str, schema: dict) -> Finding:
    """Judge a single verdict file. Every failure mode returns a blocking
    Finding; there is no path through this function that reaches OK by
    default."""
    path = pathlib.Path(path_str)

    if not path.is_file():
        return Finding(
            path_str,
            CONTRACT,
            "verdict file is missing — the gate cannot pass on an absent result (G2)",
        )

    try:
        # utf-8-sig, not utf-8: Windows tooling (PowerShell's Out-File among
        # others) writes a BOM, and a BOM is not a harness failure. Blocking on
        # one would be a false contract failure that pages the platform for a
        # text encoding.
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return Finding(path_str, CONTRACT, f"verdict file unreadable: {exc}")

    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        return Finding(path_str, CONTRACT, f"verdict file is not valid JSON: {exc}")

    if not isinstance(record, dict):
        return Finding(path_str, CONTRACT, "verdict record must be a JSON object")

    try:
        jsonschema.validate(record, schema)
    except jsonschema.ValidationError as exc:
        where = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        return Finding(path_str, CONTRACT, f"verdict violates the verdict schema at {where}: {exc.message}")

    verdict = record.get("verdict")
    suite = record.get("suite")
    layer = record.get("layer")

    # Every verdict handed to `gate decide` is, by construction, from a blocking
    # suite. A record that declares otherwise is mis-wired, and the gate refuses
    # to guess which of the two statements is true.
    if record.get("fail_closed") is not True:
        return Finding(
            path_str,
            CONTRACT,
            "verdict declares fail_closed: false but was submitted to the gate — "
            "a blocking suite must fail closed (G2)",
            verdict, suite, layer,
        )

    if verdict == "INFRA":
        return Finding(
            path_str,
            CONTRACT,
            "suite reported INFRA — the harness failed, not the code under test; "
            "this blocks and pages the platform",
            verdict, suite, layer,
        )

    if verdict not in NON_BLOCKING:
        return Finding(
            path_str,
            QUALITY,
            f"suite reported {verdict}",
            verdict, suite, layer,
        )

    return Finding(path_str, OK, f"suite reported {verdict}", verdict, suite, layer)


def decide(paths: Sequence[str]) -> Decision:
    """Decide the merge. Never raises for input problems — they become blocking
    findings, because an exception that escapes here would be reported by CI as
    an errored step, and an errored step must block rather than be interpreted."""
    if jsonschema is None:
        return Decision([Finding("<schema>", CONTRACT, "jsonschema not installed; the gate cannot validate verdicts")])

    if not paths:
        return Decision([Finding("<none>", CONTRACT, "no verdict files supplied — the gate does not pass on an empty argument list")])

    try:
        schema = load_verdict_schema()
    except (OSError, json.JSONDecodeError) as exc:
        return Decision([Finding(str(VERDICT_SCHEMA_PATH), CONTRACT, f"verdict schema unreadable: {exc}")])

    return Decision([_inspect(p, schema) for p in paths])


def render(decision: Decision) -> str:
    """Human-readable decision. The gate teaches (claim 2) — it says what
    blocked and where, never just 'failed'."""
    lines = []
    for f in decision.findings:
        mark = {OK: "PASS", QUALITY: "BLOCK", CONTRACT: "BLOCK"}[f.kind]
        label = " ".join(x for x in (f.suite, f.layer) if x)
        lines.append(f"  [{mark}] {f.path}{f' ({label})' if label else ''}: {f.reason}")

    if not decision.blocked:
        lines.append(f"\ngate: PASS — {len(decision.findings)} verdict(s), none blocking")
        return "\n".join(lines)

    why = "harness/contract failure" if decision.exit_code == EXIT_CONTRACT else "quality regression"
    owner = "platform" if decision.exit_code == EXIT_CONTRACT else "service team"
    lines.append(
        f"\ngate: BLOCKED ({why}) — {len(decision.blockers)} of {len(decision.findings)} "
        f"verdict(s) blocking; exit {decision.exit_code}; owner: {owner}"
    )
    return "\n".join(lines)


def summarize(paths: Sequence[str]) -> str:
    """The score-diff comment body. M00a prints it; M04 posts it to the PR and
    adds the baseline comparison that makes it teach."""
    decision = decide(paths)
    rows = ["| verdict | suite | layer | file | note |", "|---|---|---|---|---|"]
    for f in decision.findings:
        rows.append(f"| {f.verdict or '—'} | {f.suite or '—'} | {f.layer or '—'} | `{f.path}` | {f.reason} |")
    status = "BLOCKED" if decision.blocked else "PASS"
    return f"### quality gate: {status}\n\n" + "\n".join(rows)

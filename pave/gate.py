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


#: Marker the PR comment carries so a later run can find and replace its own
#: previous comment instead of stacking a new one under every push. A reviewer
#: scrolling past six stale gate comments to find the current one is a gate that
#: has stopped teaching.
COMMENT_MARKER = "<!-- beaconpave-gate -->"


def _scores_of(path: str) -> dict:
    """The `scores` block of a verdict, or empty if it cannot be read.

    Never raises: this feeds the comment, and a comment that crashes takes the
    explanation away from a merge that is being blocked anyway. `decide` has
    already recorded whatever is wrong with the file."""
    try:
        record = json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
        return record.get("scores") or {} if isinstance(record, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _notes_of(path: str) -> list:
    try:
        record = json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
        notes = record.get("notes") if isinstance(record, dict) else None
        return [n for n in notes if isinstance(n, str)] if isinstance(notes, list) else []
    except (OSError, json.JSONDecodeError):
        return []


#: A remediation note. The runners prefix instructions with it, and this is the
#: one class of note that is always rendered and never folded.
REMEDIATION_PREFIX = "fix:"


def _split_note(note: str) -> tuple[str, str]:
    """An actionable head and its elaboration.

    Sorted by KIND, not by length. Length is not a proxy for importance and here
    it was inversely correlated with it: the pinned-versus-observed score diff —
    the thing a reviewer needs first — ran to 204 characters and missed the
    visible bucket by four, while a one-line restatement stayed. Every note now
    contributes its first sentence to the visible list and folds the rest, so a
    long note is shortened rather than hidden.
    """
    cut = note.find(". ")
    if cut == -1 or cut + 2 >= len(note):
        return note, ""
    return note[:cut + 1], note[cut + 2:]


def summarize(paths: Sequence[str]) -> str:
    """The score-diff comment body — claim 2's *teach* half.

    A gate that blocks without saying what moved teaches people to route around
    it, which is the failure mode `_console_safe` was also written against. So
    this renders three things, in the order a reviewer needs them: the decision,
    every score the suites measured, and the runners' own account of what changed.

    **The notes come from the verdict records, not from the CI log.** Until M04
    the lane printed which probe moved and in which direction, the verdict
    recorded `FAIL`, and the reviewer got a red check with no way to see the
    difference without opening the run. A finding that travels with the artifact
    is one a reader still has next milestone.

    Nothing here can change a decision. `decide` is the only decider, and this
    function is deliberately incapable of raising: a comment that crashes takes
    the explanation away from exactly the merge that is being blocked."""
    decision = decide(paths)
    status = "BLOCKED" if decision.blocked else "PASS"

    lines = [COMMENT_MARKER, f"### quality gate: {status}", ""]

    rows = ["| | suite | layer | scores | |", "|---|---|---|---|---|"]
    for f in decision.findings:
        mark = "✅" if not f.blocks else ("🛠" if f.kind == CONTRACT else "❌")
        scores = _scores_of(f.path)
        rendered = ", ".join(f"`{k}` {v}" for k, v in sorted(scores.items())) or "—"
        # `suite reported PASS` in a column headed by the verdict is four rows of
        # restatement in the artifact whose job is to inform. The reason is kept
        # only where it says something the verdict does not — which is every
        # blocking row, and no passing one. A missing verdict has no suite, so the
        # path is what identifies it; `render` keeps it and this dropped it, which
        # turns two absent verdicts into two identical rows on the exit-2 path.
        note = "" if not f.blocks else f.reason
        label = f.suite or f"`{f.path}`"
        rows.append(f"| {mark} {f.verdict or '—'} | {label} | {f.layer or '—'} "
                    f"| {rendered} | {note} |")
    lines.extend(rows)

    teaching = [(f, _notes_of(f.path)) for f in decision.findings]
    teaching = [(f, notes) for f, notes in teaching if notes]
    remediation = []
    if teaching:
        lines += ["", "#### what moved"]
        for f, notes in teaching:
            # A blank line before the bold suite name. Without it, CommonMark
            # lazy continuation absorbs the header into the preceding list item,
            # so the second suite's name renders as trailing text of the first
            # suite's last bullet. The workflow always passes four verdicts, so
            # this is the normal path rather than an edge case.
            lines += ["", f"**{f.suite or f.path}**"]
            fixes = [n for n in notes if n.lstrip().lower().startswith(REMEDIATION_PREFIX)]
            remediation += [(f.suite or f.path, n) for n in fixes]
            heads, tails = [], []
            for note in notes:
                if note in fixes:
                    continue
                head, tail = _split_note(note)
                heads.append(head)
                if tail:
                    tails.append(tail)
            lines += [f"- {h}" for h in heads]
            if tails:
                lines += ["", "<details><summary>full reasoning for each finding</summary>", ""]
                lines += [f"- {t}" for t in tails]
                lines += ["", "</details>"]

    # **Remediation is never folded.** It used to be bucketed by length with
    # everything else, and it is the longest note a runner writes — so the more
    # specific and useful the instruction, the more certain it was to be hidden,
    # behind a summary reading "why each of these is a finding". Nobody expands
    # "why is this a finding" when they already know why; they are looking for
    # what to do, and the label promised the opposite. Claim 2 is "gates fail
    # closed AND teach", and the teaching half was one click away from a reader
    # who had no reason to click.
    if remediation:
        lines += ["", "#### what to do"]
        for suite, note in remediation:
            body = note.lstrip()[len(REMEDIATION_PREFIX):].lstrip()
            lines.append(f"- **{suite}** — {body}")

    if decision.blocked:
        owner = "platform" if decision.exit_code == EXIT_CONTRACT else "service team"
        why = ("the gate could not establish that the code is good"
               if decision.exit_code == EXIT_CONTRACT else "a suite reported a regression")
        lines += ["", f"**Blocked ({why}); exit {decision.exit_code}; owner: {owner}.** "
                      "This check is required and cannot be merged past — a gate that can be "
                      "merged past is not a gate."]
    return "\n".join(lines)

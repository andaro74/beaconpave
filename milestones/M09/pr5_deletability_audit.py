#!/usr/bin/env python
"""M09 PR 5's deletability audit.

Every check this PR adds is deleted in turn — from a working copy **backed up to
a temp directory and never restored with `git checkout`** (SPEC/09 constraint
10, and the M09 PR 4 lesson: `git checkout --` deletes the uncommitted change
the audit exists to test) — and the suite re-run. A silent check gets a test
before merge, or the check comes out.

Each anchor is verified against the tree before a single suite runs, so a
mutation that has stopped applying reports `ANCHOR` rather than a false `RED`.

Usage:  python milestones/M09/pr5_deletability_audit.py
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK = ROOT / "tests" / "test_documented_commands.py"
SPEC9 = ROOT / "SPEC" / "09-rules-registry-and-the-disposition.md"
README = ROOT / "README.md"

#: `(label, file, anchor, replacement)`. The anchor must appear exactly once.
MUTATIONS: list[tuple[str, pathlib.Path, str, str]] = [
    (
        "the demo command loses --verdicts again (the defect this PR fixes)",
        SPEC9,
        "gate decide --verdicts milestones/M09/verdict-pre-fix.json",
        "gate decide milestones/M09/verdict-pre-fix.json",
    ),
    (
        "the published exit code is changed and the command is not",
        SPEC9,
        '[BLOCK] milestones/M09/verdict-pre-fix.json (disclosure L3): suite reported FAIL\nexit 1',
        '[BLOCK] milestones/M09/verdict-pre-fix.json (disclosure L3): suite reported FAIL\nexit 0',
    ),
    (
        "the runner stops comparing the exit code and only checks the command ran",
        CHECK,
        "    assert proc.returncode == expected, (",
        "    assert proc.returncode is not None, (",
    ),
    (
        "line continuations stop being joined, so run_evals runs with no --answers",
        CHECK,
        '        if line.endswith("\\\\"):',
        '        if False:',
    ),
    (
        "a spec's demo block is quietly dropped from the scope",
        CHECK,
        '            if info != "bash":\n                continue',
        '            if info != "bash" or "08b" in spec.name:\n                continue',
    ),
    (
        "the scope assertion accepts a subset instead of the exact set",
        CHECK,
        "    assert publishing == {name for name, _, _ in CASES}, (",
        "    assert publishing >= {name for name, _, _ in CASES}, (",
    ),
    (
        "the vacuity floor drops to zero, so a reader that matches nothing is green",
        CHECK,
        "    assert len(CASES) >= 10, (",
        "    assert len(CASES) >= 0, (",
    ),
    (
        "a command asking `echo \"exit $?\"` may go unanswered by the block below it",
        CHECK,
        "            assert len(published) == len(asked), (",
        "            assert len(published) >= 0, (",
    ),
    (
        "the expectation is read from the whole section, not the block that follows",
        CHECK,
        "            following = blocks[i + 1][1] if i + 1 < len(blocks) else \"\"",
        "            following = section",
    ),
    (
        "the read-only assertion stops comparing the tree",
        CHECK,
        "    assert before == after, (",
        "    assert before is not None, (",
    ),
    (
        "README row 09 loses the seven-PRs cell while the breach record stands",
        README,
        "| 09 | The rule is disposed, and the service goes red ❉ | seven PRs ❉ |",
        "| 09 | The rule is disposed, and the service goes red ❉ | `m09-rules` |",
    ),
    (
        "README row 09's bold 10/25 is removed while the m09 entry stays on disk",
        README,
        "| `m09` | **10/25** ❉ |",
        "| `m09` | – |",
    ),
]


def _run_suite(paths: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", *paths],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=900)
    tail = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    return proc.returncode == 0, (tail[-1] if tail else "<no output>")


#: The fast set first — a caught mutation costs seconds and only a survivor pays
#: for the whole suite (ADR-075 amendment 3 §8's two-stage shape).
FAST = ["tests/test_documented_commands.py", "tests/test_readme_history_rows.py",
        "tests/test_m09_cap.py", "tests/test_demo_recordings.py"]


def main() -> int:
    backup = pathlib.Path(tempfile.mkdtemp(prefix="m09-pr5-audit-"))
    print(f"working copies backed up to {backup}\n")

    # **Anchors first, all of them, before any suite runs.** A mutation whose
    # anchor has drifted is not a silent check; it is a mutation that never ran.
    for label, path, anchor, _ in MUTATIONS:
        n = path.read_text(encoding="utf-8").count(anchor)
        if n != 1:
            print(f"  ANCHOR  {label}  (anchor appears {n} times in {path.name})")
            return 2

    for path in {m[1] for m in MUTATIONS}:
        shutil.copy2(path, backup / path.name)

    results = []
    for i, (label, path, anchor, replacement) in enumerate(MUTATIONS, 1):
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace(anchor, replacement),
                        encoding="utf-8", newline="")
        green, line = _run_suite(FAST)
        if green:                                  # survived the fast set
            green, line = _run_suite(["tests/"])
        # Restore from the BACKUP, byte for byte. Never `git checkout`.
        shutil.copy2(backup / path.name, path)
        verdict = "SILENT" if green else "RED"
        results.append((i, label, verdict, line))
        print(f"  [{i:2}] {verdict:7} {label}")
        if green:
            print(f"        {line}")

    print()
    print("| # | mutation | result |")
    print("|---|---|---|")
    for i, label, verdict, _ in results:
        print(f"| {i} | {label} | **{verdict}** |")
    red = sum(1 for _, _, v, _ in results if v == "RED")
    print(f"\n{len(results)} mutations, {red} RED, {len(results) - red} SILENT")
    print(f"\nevery working copy restored from {backup} byte for byte (no `git checkout`)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

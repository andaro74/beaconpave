"""Every tracked place that publishes 16 as M06b's refused-case count.

**Line-based grep cannot do this job**, and three hand counts proved it: ADR-069
revision 1 said nine sites, revision 2 said 21, and two seat reviews then found
more. `docs/adr/ADR-065-…` wraps between the "16" and the "answer-channel
refusals" it qualifies, so no `git grep` pattern can see it at all.

So this reads whole files, collapses whitespace, matches across the wrap, and
maps the offset back to a line. Run it rather than trusting a table:

    python tools/sweep_sixteen.py

**Reporting only.** Nothing scores, gates or decides on this. It exists so that
ADR-069's enumeration is a command with an output rather than a number somebody
counted, and so the next person to ask "is that still all of them?" can answer it
in one second instead of by hand.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: 16 tied to a refusal count, tolerating a line break anywhere between the two.
#: The `(?<!\d)`/`(?!\d)` guards keep 160 and 016 out; `(?![/\d])` keeps `16/25`
#: — M02's *score* — out. The 80-character window is wider than any wrap in the
#: repo and narrower than a paragraph.
PATTERN = re.compile(
    r"(?<!\d)16(?!\d)(?![/\d])[^.]{0,80}?(?:refus|never reach|of (?:the )?25)"
    r"|refus\w*[^.]{0,80}?(?<!\d)16(?!\d)(?![/\d])",
    re.IGNORECASE,
)

#: Where 16 is a correctly-labelled per-run or unanimous figure, an unrelated
#: number, or this milestone's own writing about the problem. Excluded by path,
#: so every exclusion is auditable rather than hidden inside the regex.
EXCLUDE = (
    "SPEC/06d-instrument-readable.md",
    "docs/adr/ADR-069-the-refused-count-depends-on-the-estimator.md",
    "tools/sweep_sixteen.py",
    "platform/infra/cdk.out/",                 # build output
    "pave/tests/fixtures/",                    # historical PR bodies, quoted verbatim
    "milestones/M03/",                         # a table row numbered 16
    "quality/judge/",                          # the calibration item `cal-16`
    "evals/refusals.py",                       # a `:16` format width
    "tests/test_m06b_survivor_census.py",      # per-run counts, correctly labelled
    "docs/M06b-guardrail-diagnosis.md",        # per-run: run 1 genuinely refused 16
    "docs/M06b-scored-run-findings.md",        # "refused unanimously 16/25", labelled
    "docs/pr-bodies/history-append-only.md",   # a headroom figure, unrelated
    "milestones/M06b/goldens-run-refusals.json",   # the census; 16 is its unanimous key
    "milestones/M06b/wiring-check-refusals.json",  # a different run, genuinely 16
    "milestones/M06b/goldens-run-1.json",          # run data: a `tool_ms` of 16
    "milestones/M06b/goldens-run-2.json",
    "milestones/M06b/goldens-run-3.json",
)

#: A use that names the estimator producing it is not the defect this sweep hunts:
#: it is the notation ADR-069 says the fix looks like at scale. Reported in its own
#: bucket rather than excluded, so the two populations stay visible to a reader.
LABELLED = re.compile(r"unanimous|all three samples|@(majority|unanimous)|3 of 3",
                      re.IGNORECASE)


def tracked() -> list[str]:
    """Tracked paths, minus the auditable exclusions above."""
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return [p for p in out.splitlines()
            if p and not any(p == x or p.startswith(x) for x in EXCLUDE)]


def _line_of(text: str, offset: int) -> int:
    """1-indexed line containing `offset` in the ORIGINAL text."""
    return text.count("\n", 0, offset) + 1


def sweep() -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    """(bare, labelled) sites, each as (path, line, excerpt), in tracked order."""
    bare: list[tuple[str, int, str]] = []
    labelled: list[tuple[str, int, str]] = []
    for rel in tracked():
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "16" not in text:
            continue
        # Build the flattened text and, in the same pass, the map from each
        # flattened index back to its offset in the original.
        flat_chars: list[str] = []
        back: list[int] = []
        prev_space = False
        for i, ch in enumerate(text):
            if ch.isspace():
                if prev_space:
                    continue
                flat_chars.append(" ")
                prev_space = True
            else:
                flat_chars.append(ch)
                prev_space = False
            back.append(i)
        flat = "".join(flat_chars)
        for m in PATTERN.finditer(flat):
            line = _line_of(text, back[m.start()])
            window = flat[max(0, m.start() - 120):m.end() + 120]
            excerpt = flat[max(0, m.start() - 30):m.end() + 30].strip()
            target = labelled if LABELLED.search(window) else bare
            target.append((rel, line, excerpt))
    return bare, labelled


def main() -> int:
    bare, labelled = sweep()
    width = max((len(f"{r}:{n}") for r, n, _ in bare + labelled), default=0)
    print("BARE — 16 published as the refusal count, no estimator named:")
    for rel, line, excerpt in bare:
        print(f"  {f'{rel}:{line}':<{width}}  …{excerpt}…")
    print(f"\n  {len(bare)} bare site(s).\n")
    print("LABELLED — 16 published with the estimator that produced it:")
    for rel, line, excerpt in labelled:
        print(f"  {f'{rel}:{line}':<{width}}  …{excerpt}…")
    print(f"\n  {len(labelled)} labelled site(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

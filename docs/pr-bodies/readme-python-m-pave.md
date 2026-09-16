# README quick start: the `python -m pave.cli` form, and one flag that never existed

Zero model calls. `twokey.triggered` over the changed set is `[]`: README.md and
this file collect no key.

## What it changes

Two lines in the README quick start.

- `pave new my-agent --brand meridian-sports --classification internal` becomes
  `python -m pave.cli new my-agent --brand meridian-sports`.
- `pave drill ...` becomes `python -m pave.cli drill ...`.

## Why

**The quick start listed a command that does not run on a fresh clone.** The
`pave` console script exists only after `make bootstrap` runs `pip install -e .`,
while `make check`, the line above it, needs no install. `python -m pave.cli` works
from the repository root in both states, which is the form the Makefile already
uses for every target.

**`--classification` was advertised and never read.** `scaffold_new` reads
`--brand`, `--team` and `--oncall` and nothing else; the flag was accepted silently
and did nothing. Classification is set by the template as `internal` and edited in
the rendered manifest. A documented flag the parser ignores is a stated control
that is absent, and this repository ranks that below one that is missing.

## What it does not change, and why

**The same stale flag in `pave/cli.py`'s usage text stays.** The first version of
this PR corrected that line too, and the gate blocked it:
`tests/test_drill_pins.py::test_the_readers_were_shown_emitting_before_the_claim_was_committed`
requires that the last commit touching `pave/cli.py` predate the M11 readers
transcript, `milestones/M11/pre-registration/readers.txt`. It reads the commit,
not the content, so a later revert of the same line fails the same way, and the
branch was rebuilt without the change. Until that transcript is re-taken, every
edit to `pave/cli.py` is an M11 pre-registration event, and a help-text line does
not earn one. The line is recorded here as known-stale rather than left for the
next reader to discover.

The remaining `pave ...` forms in the CLI usage text are the console script's own
help, and that script exists after bootstrap. The demo-script note recording the
old flag stays, since it records history.

## Checked

`make check` on the rebuilt branch. `tests/test_drill_pins.py` and
`tests/test_cited_commits_resolve.py` green with the branch's two changes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

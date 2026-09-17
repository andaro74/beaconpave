# README: quick start first, progression table last

Zero model calls. `twokey.triggered` over the changed set is `[]`: README.md
collects no key. No spec and no ADR: a reorder makes no claim and cuts no scope.

## What it changes

The README's twelve `## ` sections are reordered. Nothing inside any section
moves; the whole-file diff sorted by line is three sentences.

| position | section |
|---|---|
| 1 | Quick start |
| 2 | Repository map |
| 3 | Golden rules |
| 4 | Traceability rules |
| 5 | Governance |
| 6 | Cost posture |
| 7 | Scaling this up |
| 8 | Two parts, and this is the end of part one |
| 9 | What part one produced |
| 10 | The twelve claims |
| 11 | Progression |
| 12 | License |

The progression table is the longest section by a wide margin and was second;
a reader arriving at the repository met eight hundred lines of milestone rows
before the commands. The intro paragraphs above the first heading are
unchanged.

## The three sentences

Each said "above" or "below" about a section that moved:

- the part-one lead-in said the recap was *below* the progression table; it is
  now ahead of it;
- the recap said every scored number is in the progression table *above*; it is
  now below;
- claim 6's footnote said the count is in *the row above*; it now names the `09`
  row of the progression table below.

## The header image

`docs/assets/readme-header.png` (2400 x 780, 150 KB) is linked above the
`# beaconpave` heading, and the repository map gains a `docs/assets/` row. Every
figure the banner shows is read from the repo: 25 goldens and k = 3 from the
reference pack and the judge estimator, 10 probes from the adversarial suite, MIT
from `LICENSE`, `m12` from the last tag. It is a picture, not a claim: no test
reads it, and no number in it is one the progression table does not already
publish.

The file is binary, so the two tree scanners treat it the way they treat the
five recordings: `tests/test_line_endings.py` passes it on the NUL byte and
`tests/test_no_account_identifiers.py` skips it twice as not decodable: one
pass and two skips for the file, measured with `-k readme-header`.
`COLLECTED_FLOOR` is a minimum and unaffected.

## Why the readers are safe

`tests/milestone_status.py` scopes to the progression table by its header cell,
`tests/test_demo_recordings.py` by the backticked tag cell, and
`tests/test_documented_commands.py` excludes the quick-start block by file name.
The recordings test's made-up README already exercises a claims table placed
before the progression table, which is now the live order. All seven README
readers pass: 308 tests.

## Checked

`make check` on the branch: 5506 passed, 12 skipped.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

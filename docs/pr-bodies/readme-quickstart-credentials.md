# README quick start: name the profile source, prove the credentials

Zero model calls. `twokey.triggered` over the changed set is `[]`. No spec and
no ADR: one comment and one command in the README's quick start.

## What it changes

The profile line already exported `AWS_PROFILE`, `AWS_REGION` and
`AWS_DEFAULT_REGION`. Its comment now says to take the profile name from
`aws configure list-profiles`, and why the placeholder is written `your-profile`
with no angle brackets: bash reads `<...>` as a redirection, the export fails
silently, and the next command runs on the default profile (measured in #173's
Service Team review). One command follows it, `aws sts get-caller-identity`, so
a developer proves the credentials resolve before `make bootstrap` spends
anything.

The block is sixteen commands, parses under `bash -n`, and is still the one
declared-unrun `bash` fence in README.md, so `UNRUN_BASH_BLOCKS` is unchanged.

## Checked

- The block extracted passes `bash -n`.
- `tests/test_documented_commands.py`, `tests/test_demo_recordings.py`, `tests/test_m09_goldens_denominator.py`: 39 passed.
- `make check` on the branch: 5513 passed, 12 skipped.

## Attestations

None collected.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

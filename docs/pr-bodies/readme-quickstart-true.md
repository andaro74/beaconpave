# README: a quick start that is true of this tree

Zero model calls. `twokey.triggered` over the changed set is `[]`: README.md,
`tests/test_documented_commands.py` and this body collect no key, and none of
the four paths pinned by `tests/test_drill_pins.py` is touched. No spec and no
ADR: the block makes no new claim; it stops making false ones.

## What was wrong

The old block's seven lines were read against the Makefile, the CDK app and the
runners. Three comments did not survive, and two lines could not run as written:

| line | said | measured |
|---|---|---|
| `make core` | *deploy gateway, tools, agent, dashboard* | `platform/infra/bin` defines two stacks, `BeaconpaveGateway` and `BeaconpaveAuditTrail`. No agent stack: the agent is one environment variable naming the caller (`gateway-stack.ts`, ADR-023). No dashboard: `dashboards/` holds a README |
| `make evals` | *definition of done* | `run_evals --answers $(ANSWERS) --record`. Nothing in the block produces `ANSWERS`, an empty value fails on a permission error rather than a refusal, `--record` appends to the append-only history, and no `--target` or `--tag` is passed, so a governed run is recorded as the baseline |
| `make adversarial` | *the security seat's corpus, fetched fresh* | refuses with exit 2 unless `OBSERVATIONS=` names a probe run; nothing is fetched; and `--record` needs `--instrument-name`, `--guardrail-version` and `--guardrail-policy-sha256`, which the target never passes, so the form cannot record at all |
| `pave drill` | (no comment) | with no `BEACONPAVE_DRILL_KEY` prints *no key, no artifact* and exits 2 (SPEC/11 constraint 4). The block never mentioned the key |
| `make check` as line 1 | hermetic first step | on a fresh clone it dies: pytest and ruff live in the `dev` extra, boto3 in `baseline`, and `make bootstrap` installs the bare package. Nothing in the old block ever made line 1 pass |

The repository knew half of this. The block is the one README `bash` block
declared unrun in `tests/test_documented_commands.py`, with the reason *the
TARGET developer experience rather than a reading of this tree*. That label lived
in a test module; the page itself said nothing.

## What the block says now

Fifteen commands, each with its comment on the line above it so nothing scrolls
off the page, in the order a first-time developer meets them: the dev and
baseline extras; the hermetic check; the profile and both region variables;
bootstrap; `make core` with what it deploys; the reference runner's preflight, one
case and all twenty-five under a `--tag` of its own; the offline goldens scorer;
the probe runner and its offline scorer; `make down` with what outlives it; the
drill with a generated key; the scaffolder. Every `AWS:` line is marked. The
paragraph above the block says which lines were run against this tree before
they were written (the check, both scorers on committed run files, the drill,
`pave new`) and which were read from the Makefile, the CDK app and the parsers.

A paragraph under the block says what a reader of the old block would have got
wrong: `make core` deploys the platform and no agent; the agent's code never
leaves the developer's machine and the runner fetches the audit record back from
S3; the deployed gateway authorizes as one caller (ADR-023); a scaffold is refused
by `pave verify` until the two named steps are taken (ADR-047); where the judge
runner is; and why neither `make` recording form records a governed run as
written.

One word elsewhere in the README: the repository map said `10 probes` under
`quality/adversarial/`; the corpus has held 11 since PR #51 (`d9f8a3b`), and the claims table's
`7/11` already read it. The claim 5 row's `10 probes × 3 samples` is M04's
recorded history and stays.

## The declared-unrun entry

M09's debt 33 (*only Demo artifact blocks are checked*) was paid at M09b PR 2,
which is where `UNRUN_BASH_BLOCKS` came from; its trigger, *the next PR that
edits a command block in `README.md`*, fired here and the debt is neither
reopened nor widened. The README entry's reason is rewritten to say what the
block does (creates AWS stacks, invokes the gateway, destroys the stacks, writes
five files and the drill artifact) rather than that `pave` is *not on PATH*,
which stopped being the reason when the block went to `python -m pave.cli`. The
module docstring's bullet for the README is updated to match. The run scope is
unchanged, one `bash` block in README.md, and `test_every_bash_block_is_run_or_
declared_unrun` holds it.

## Seat rounds

Three rounds, two seats each, all read-only against the branch's worktree.

**Platform Engineering.** Round 1: *zero calls* to *zero model calls*; *nothing
while idle* to the G10 target with the RETAIN resources named; the ADR-023 and
ADR-047 citations swapped to the sentences they support; the recording-forms
sentence corrected; the exclusion reason lost a branch name that would go stale.
Round 2: the intro's *every offline line was run* narrowed to the lines that were,
since the scorer lines need a run file the tree does not carry; *versioned RETAIN
buckets* corrected to three buckets, two versioned. Round 3: its own *both guardrail
versions outlive it* walked back to *carry RETAIN*, because the parent guardrails
carry no removal policy and *outlive* was never measured.

**Service Team.** Round 1: line 1 cannot pass on a clone without the `dev` extra
(and the runners without `baseline`); the smoke and full runs shared the
committed workflow's `--tag` and would overwrite its key names; the corpus is 11
probes at k=3, not 10; `--preflight-only` prints pins, not a spend; `--target` on
a non-recording scorer is a no-op; the goldens scorer is not *the gate*; the
sidecar files and the drill's exit 2 were unnamed. Round 2: `<your-profile>` in
a bash block is two redirections and leaves the next line on the default
profile; 197-column lines put every comment behind a horizontal scroll;
*authorizes one caller* reads against a Cedar file that permits two principals
since #169; the module docstring bullet was stale; two sentences cut. Round 3:
`AWS_REGION` alone raises `NoRegionError` when no config file names a region,
which a first measurement here missed because the local profile supplied one;
reproduced with `AWS_CONFIG_FILE=/nonexistent` on botocore 1.43.54, and the
block's comment now says which variable each tool reads. The smoke case went
`blackout-001` to `recommend-003` (M02's README precedent) and back: both
authorize a tool call in every committed sample, so neither trips the runner's
no-call exit, but `recommend-003` was refused by the guardrail in 5 of 9
committed samples and `blackout-001` in none, and a first-timer's smoke test
should not print `REFUSED` half the time.

Two findings were not taken here and are named for their owners: `make evals`
and `make adversarial` cannot record a governed run as written (Platform
Engineering, a recording path, its own PR), and `pave check`'s remediation hint
for a missing ruff says `pip install -e .`, which does not install it
(Platform Engineering; `pave/cli.py` is frozen by the M11 readers pin, so the
hint waits for a PR that may touch it).

## Checked

Run in this tree before the lines were written:

- `python -m evals.run_evals --answers milestones/M02/runs/m02-tools-1.json`: scores, exit 0, `git status` clean after.
- `python -m evals.run_adversarial --observations <committed run>`: exit 0, no write (Service Team, round 2).
- `BEACONPAVE_DRILL_KEY=<64 hex> python -m pave.cli drill --event jefferson-derby --tier 3 --out <scratch>`: `drill: GO`, exit 0, artifact carries `signature`. With no key: exit 2, nothing written. With a 16-byte key: exit 2, nothing written.
- `blackout-001` is the first case id in the reference pack, refused in 0 of 9 committed samples (Service Team, round 3).
- `python -m pave.cli new zz-quickstart-probe --brand meridian-sports` in the branch's worktree: exit 0, five files rendered, the two refused steps printed; the directory was removed before commit.
- botocore 1.43.54 with `AWS_CONFIG_FILE=/nonexistent`: `AWS_REGION` alone raises `NoRegionError`; `AWS_DEFAULT_REGION` alone resolves `us-west-2`.
- The block, extracted, passes `bash -n`; longest line 103 columns; exactly one `bash` fence in README.md.
- Flags read from the parsers: `run_with_tools.py --preflight-only/--only/--out/--tag`, `run_probes_via_gateway.py --out/--tag` (k defaults to 3), `run_evals.py --answers`, `run_adversarial.py --observations`.

`ruff check` clean. README readers and `tests/test_documented_commands.py`: 611
passed. `make check` on the branch: 5507 passed, 12 skipped.

## Attestations

None collected.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

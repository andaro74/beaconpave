# Append-only never constrained what a NEW row may claim, and the directory that anchors two gates took one key

`evals/history/` is where every published number lives. The rule on it is
"append-only", and the rule was doing less than its name says. Reproduced on a
clean tree before anything was written:

```
appended evals/history/m01-goldens-corrected.json
  real   m01 scores: passed 19 of 25
  new    row claims: passed 24 of 25    same `sha`, schema-valid
  -> 1701 passed, pave check exit 0
```

The row did not have to be internally consistent — `passed: 24` beside
`pass_rate: 0.76` validated, because nothing tied an entry's `scores` to its
`cases`. **Append-only forbids an edit. It said nothing about what a new row
may claim**, and the directory took one key.

It is also a live gate criterion, which the first draft of the ADR denied.
`pave/cli.py:900` read an entry's `scores.total` into `asked_floor`, a gate
*failure* condition, while `pave/floors.py:88` asserted that value "is not a
value the same PR can invent". Measured: an arm recorded asking three of eleven
probes, `total: 3`, pinned 3/3 — **lane PASS, gate exit 0**.

## Four drafts, because the first three did not survive being planted against

Every draft was pre-registered and reviewed by seats that built the attack in a
worktree rather than reading the diff. Each draft is in the branch history.

- **Draft 1** aimed at editing a committed row, via a git-commit count.
  Four seats: the cheaper attack is **appending**, untouched.
- **Draft 2**'s count could not satisfy its own predictions 3 and 4 at once —
  three seats built the same two branches and measured an honest
  record-then-fix PR at 2 commits and a one-commit rewrite at 1. It fired on the
  honest PR and missed the rewrite, and **the only remedy it taught was
  squashing, which is what hides the real attack.**
- **Draft 3** put the deciding check in a pytest. `tests/conftest.py` (zero
  keys) sets `GITHUB_BASE_REF`; `pyproject.toml` (zero keys) sets `addopts`.
  Measured: **1631 passed, 72 deselected, `pave check` exit 0, with
  `m04-adversarial.json` rewritten to 10/10.**
- **Draft 4** is this one. Three more seats then planted against the **code**
  and found eleven defects in it, listed at the bottom.

## What lands

**Three keys on the whole of `evals/history/` and on both recorders.**
`run_evals.py` was on no rule while its twin took two — draft 1 justified a seat
by naming "both recorders" with one of them unguarded inside the sentence.

**`two-key.yml` diffs with `--no-renames`.** The cheapest bypass in the repo,
and it defeated every key this ADR adds:

```
git mv evals/run_adversarial.py evals/record_adversarial.py   # + delete the append-only refusal
two-key: not required — this PR touches no two-key path       exit 0
```

**Every entry pinned, exact-set, self-consistent.** `evals/history/pins.json`,
written by both recorders, digest over normalised text. The set of pins must
equal the set on disk; every pin is 64 hex (an empty-string pin with a rewrite
behind it was green under an `if v` filter); `scores` must be derivable from
`cases`; a goldens result is the strict majority of its samples and an
adversarial one their unanimity.

**The append-only check is a diff against the merge-base, not a count.**

```
git diff --name-status --no-renames --diff-filter=a BASE...HEAD -- evals/history/
```

`--diff-filter=a` keeps every verb but Added, because `MDR` missed a typechange
— a committed entry replaced by a symlink to another entry, which resolves on a
Linux runner and gets re-pinned over the target. Fires on modify, delete,
rename, the squash of a rename, an evil merge, a merge ref, and the typechange.
Does not fire on an honest two-commit PR, an intra-PR edit of a row the PR
created, a branch behind an advanced `main`, or `main` as it stands.

**The instance that decides is a workflow step, not a test.**
`pave gate history --base "${{ github.event.pull_request.base.sha }}"` writes
`verdict-history.json`, which `gate decide` requires. No environment variable
and no pytest collection stands between the workflow and the check.

**A new row is anchored to committed evidence.** `samples_from` required beyond
the legacy eight, matched against the committed file, under the entry's own
milestone directory, not shared with another non-correction row. Goldens
evidence takes two keys where it took none.

**The adversarial denominator is a registered constant.**
`instruments.json` gains `corpus_size`, and a test resolves every registered
`probes_sha256` to a revision of the corpus reachable from the base — a
fabricated mid-registry row with `corpus_size: 3` recorded a 3/3 arm green
before it. The floor read moves into `pave/floors.py` (three keys).
`floors.py`'s false guarantee is corrected in code, not in prose.

**`supersedes` becomes writable, by filename.** It was a SHA, and a SHA
identifies one to N entries — `515ee70` already identifies three. Corrections
land as `-correctionN-`, refuse identical numbers, refuse a second correction of
one entry, and cannot move a gate by being appended.

## What this does NOT claim

**Pinning a row does not make it true.** A row added and pinned in one PR is
still that PR's claim. What this buys is that adding one is exact-set, visible,
self-consistent, anchored to committed evidence, bounded in its denominator, and
attested by three seats — where before it was a file appearing in a directory
nobody checked. That is ADR-013's concession restated, and it is the honest
claim.

On a one-operator repo, "three keys" is three `Two-Key-Disposition:` lines and
one rationale from the same author. Said plainly so nobody reads it as three
humans.

## Two findings carried, because both were protections that were stated and absent

- **`m04-adversarial.json`'s evidence link was already broken.** PR #51 rewrote
  `milestones/M04/probes-run.json` to add `_asked`, under two keys, and nothing
  read the entry's digest of it. Recorded in `EVIDENCE_REVISIONS` with its PR
  and its reason rather than hidden — and the recorded digest is the CRLF
  rendering of the old blob, because both recorders hashed raw bytes: **seven of
  ten `samples_from` records on `main` were CRLF digests of LF blobs.**
- **`m01`'s sha `fb52a8e` was on no branch that merges and under no tag** —
  reachable only through the unmerged `m01-gateway` branch. A routine "delete
  merged branches" would have turned `git show fb52a8e:…` into a refusal on
  every PR, with a remedy nobody can apply from a PR. Tagged `evidence-m01`;
  `check_reachable` catches the next one at record time.

## What the seats found against the CODE, after the design was settled

Every one measured, fixed, and given a test:

- the goldens recorder wrote `samples_from` only at k > 1, so **the exact
  command `close-milestone` prescribes wrote a row this ADR's own check
  refused** — two seats;
- `derive_scores` used `passed/total` for adversarial `pass_rate` where the
  scorer writes `passed/scored`, so **an honest ADR-041 arm asking ten of eleven
  was refused** — two seats;
- a goldens k > 1 row could contradict its own samples and stay green;
- `check_readme` was one-directional — a row filled in with a number and no
  entry behind it passed;
- correcting a correction nested the filename (`-correction1-correction1-`) and
  the check then refused the row its own message told the operator to write;
- `gate history` raised bare tracebacks on six malformed inputs, writing no
  verdict and paging platform with no file named;
- a new adversarial row with no `instrument` skipped the denominator bound;
- `git rev-list --all` saw a throwaway corpus committed and restored inside the
  PR itself;
- `EVIDENCE_REVISIONS` was read per row, not as the chain its docstring
  described;
- `check()` captured pytest and sat silent for 45 s;
- the Makefile's default `OBSERVATIONS` would have recorded a second row over
  M04's evidence;
- **four of the ten new checks deleted in silence** — `check_reachable`,
  `check_modes`, `check_case_ids` and `ASKED_FLOOR` each neutered with 1784
  passed, which is prediction 7 failing a fourth time *inside the module the
  prediction is about*. Four violating-tree tests; each deletion now produces
  2–3 named failures;
- **registering `corpus_size` on four superseded instrument rows** let a new arm
  name a stale ten-probe instrument, set its own floor to 10 and never be asked
  `ADV-011` — the newest probe — with every check clean. The recorder refuses
  that at record time and the gate did not, which is this ADR's own thesis about
  where a deciding check may live;
- `--base ""` reported PASS at exit 0, falling through to `origin/main` — not
  live under `on: pull_request`, live the day the workflow gains `merge_group`;
- one unreadable file erased every other finding, because `gate history`
  replaced the problems already collected with the exception;
- `check_reachable` accepted `HEAD`, the PR's own merge commit — verbatim the
  scenario it was written for.

## Verification

```
1795 passed        ruff clean        pave check exit 0
pave gate history --base main: PASS  gate decide exit 0
lane PASS exit 0                     zero model calls, zero dollars
```

No committed entry's `scores` or `cases` changed. No `README.md` number moved.
No threshold, baseline, guardrail or probe moved. `m04-adversarial.json` is
byte-identical.

---

ADR: docs/adr/ADR-042-what-a-new-row-may-claim.md

## Dispositions

**AI Quality** — owns `evals/history/` and the recorded numbers. No suite is
re-scored and no committed number moves; the pins are the digests of the entries
as they stand on `main`, verified against `git show main:`. The derivation added
to `scores` is what both tallies already write, key for key, and it was checked
against a real recording from each recorder rather than against the committed
rows alone — the first version refused an honest arm. Headroom is untouched:
15, 19, 17, 16 of 25, six or more cases at failure in every suite. The README
tie is exact-set both ways and pinned per tag, because `m00b` has two goldens
entries and `m02` two arms, so "some entry with this tag" let a row move to the
other one. Case ids are compared against `cases.yaml` **at the entry's own
sha**, so adding a golden case is not a ratchet on corpus growth.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: no suite is re-scored and no committed number moves — every
  pin equals the digest of the entry as it stands on `main`, and `m04` is
  byte-identical. The `scores == derive(cases)` rule is what `deterministic.tally`
  and `adversarial.tally` already write, verified by recording through both real
  recorders rather than against committed rows alone: the first version derived
  `pass_rate` over `total` and refused an honest arm that asked ten of eleven
  probes. The README rows are pinned per tag and exact-set in both directions,
  because two tags carry two goldens entries each and a one-directional check let
  the published number move to the other one. Golden case ids are compared at the
  entry's own sha so that adding a case is not a ratchet on corpus growth, and
  headroom is unchanged at six or more failing cases in every suite.

**Security / Red Team** — owns what a probe passing means, the adversarial
entries and the corpus registry. A new arm may not name a superseded
instrument: registering `corpus_size` on the stale rows would otherwise have
handed every future arm an opt-out from the probes added since it, measured at
10/10 with `ADV-011` never asked. The denominator an arm reports stops being the
number the same PR wrote: it is `corpus_size` for the instrument the entry
names, and every registered `probes_sha256` must resolve to a revision of the
corpus reachable from the base, with that many probes. "Registered under
Security's key" alone bounded nothing — a row inserted mid-registry with a
fabricated digest recorded a 3/3 arm green. `--no-renames` on the collector is
in this PR because every key it adds was otherwise collectable around with one
`git mv`. The residual is stated rather than closed: an arm whose entry and
evidence are forged together, under three attestations.

Two-Key-Disposition: security
Two-Key-Rationale: the adversarial denominator stops being a value the recording
  PR chooses — it is the registry's `corpus_size` for the instrument the entry
  names, and a test resolves every registered `probes_sha256` to a revision of
  the corpus reachable from the base with that probe count, because a row
  inserted mid-registry with a fabricated digest and `corpus_size: 3` recorded a
  three-of-three arm with the lane PASS and the gate exit 0. `--no-renames` on
  the two-key collector belongs in this PR rather than its own, because `git mv`
  of a two-key file to a path outside its pattern reported "not required, exit 0"
  and would have collected none of the keys this change adds. G4 semantics are
  untouched: no probe, corpus or scorer moves, and `OUT_OF_SCOPE` still satisfies
  neither half.

**Platform Engineering** — owns the recorders, the lane, the workflows and the
two-key mechanism. The instance that decides is a workflow step taking its base
from the event payload, because the test harness is two zero-key files and both
were measured neutralising the protection tests. `gate history` treats any
exception as a named refusal with a FAIL verdict rather than an errored step.
Gate criteria stay in `pave/floors.py`; `pave/cli.py` keeps no number that
decides, so `test_ordinary_pr_is_not_gated` still passes. Every protection this
PR adds sits on a path with at least the keys of what it protects, audited
pairwise, and the deletability of each is a test rather than a claim. Hermetic:
`fetch-depth: 0` and `file://` clones only, no model call, no network.

Two-Key-Disposition: platform-eng
Two-Key-Rationale: the deciding instance of the append-only check is a workflow
  step that takes its base from the event payload as an argument, because
  `tests/conftest.py` and `pyproject.toml` control the pytest harness on zero
  keys and both were measured neutralising the three-key protection tests with
  `pave check` exit 0 over a rewritten entry. The check is a merge-base diff and
  not a commit count, since a count fired on an honest two-commit PR and missed a
  one-commit rewrite, and the only remedy it taught was the squash that hides the
  real attack. `--diff-filter=a` allowlists the one benign verb rather than
  enumerating the bad ones, which had missed a symlink typechange. `gate history`
  raises no bare traceback on any of six malformed inputs and writes its FAIL
  verdict, gate criteria stay out of `pave/cli.py`, and every new protection is
  on a path with at least the keys of what it protects.

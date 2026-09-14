# 11 — the drill's arc: NO-GO, a control that stays NO-GO, and GO on the fix

**Status: WRITTEN at M11 PR 1, 2026-09-13, before any drill code, scenario, fixture or
run.** Owned by the PM seat. Tag `m11`; one branch per PR, none named `m11`. Branch point:
`main` at `8ac2aaa`. **Amended at M11 PR 2, before the registration and before any arc
reading** (ADR-080 amendment 1): one validity row, that each run's caption bytes are the
committed fixture's. **Amended again at M11 PR 2b, after the cold review and before PR 3
branches** (ADR-080 amendment 4): three validity clauses (`drill verify` exits 0 on each run,
and the seeded artifact's `key_id` equals the committed key hash's). The arc runs in a fresh
clone, and the cap is five PRs.

**Deliberately short.** Every rule below is derived in **ADR-080**. This file states the
milestone. **The claim is proposed here and pre-registered in PR 2**, by a committed
record written after its readers have emitted a value (ADR-080 decision 1). Across the
whole milestone: zero model calls, zero AWS calls, no deploy.

## Why

Claim 11 (`README.md:821`) reads: *"Readiness drills produce go/no-go artifacts"*. Its
proof is *"NO-GO → fix → delta drill → GO"*. Act 4 (`docs/governance/demo-script.md:169-173`)
adds three things: a seeded caption failure; a machine-signed NO-GO with a named owner and
a fix-by time; and an artifact that is never hand-edited.

**None of it exists.**
- `drill/` holds one stub README.
- `pave drill` calls `_stub` (`pave/cli.py:1726-1728`), exits 0 and writes nothing.
- `tests/test_documented_commands.py:102-105` never runs it.

The feasibility check before this spec found a false state and no command that detects it
(ADR-080 decision 1).

## The one claim: the arc, with a control

**For event `jefferson-derby` at tier 3, a seeded caption failure makes `pave drill` write
a NO-GO. The NO-GO names the seeded gap, the pinned owner, and a fix-by time set by the
pinned window, under a signature that refuses a hand edit. The delta drill run without the
fix still writes NO-GO for the same gap. The delta drill run with the fix writes GO.**

There are three runs, in order: **seeded** (a full drill), **control** (a delta drill, fix
not applied) and **fixed** (a delta drill, fix applied). There are five falsifiers, and
any one fails the claim and closes M11 RED. The milestone carries **claim 11**, and none of
claims 7, 8 or 12.

**Conformance is not a term.** The writer validates the artifact against its schema before
writing it. A non-conforming artifact therefore never exists, and a term that read
conformance would confirm itself (ADR-079 amendment 2). Conformance is a PR 2 deliverable
with its own tests.

**The control is a term.** Without it, a GO after the fix is the vacuous confirmation of
ADR-035 amendment 5 (:1073-1077). Two delta drills show why: one that re-checks only the
paths changed since its prior, and one that says GO on any delta. Both write GO whether or
not anything was fixed.

### Pinned here, and nowhere later

| name | value |
|---|---|
| the fixture | `drill/fixtures/jefferson-derby/captions.vtt`. WebVTT, 12 cues `c001`–`c012`, each 5.000 s, contiguous from `00:00:00.000` to `00:01:00.000` |
| rule `max-gap` | one finding for each pair of consecutive cues whose gap (next start − previous end) is **greater than 4.000 s** |
| the seed | cue `c007` deleted, and nothing else. This leaves a 5.000 s gap between `c006` and `c008` |
| the fix | cue `c007` restored, so the fixture's bytes equal PR 2's |
| the seeded finding | `caption-check/max-gap/c006/c008` |
| the owner | `owner.seat` = `service-team`; `owner.oncall` = `webhook:player-captions` |
| the window, tier 3 | `fix_by − ran_at` = **129600 s** (36 h), both in UTC to the second, `YYYY-MM-DDTHH:MM:SSZ` |
| the signature | `{"alg": "HMAC-SHA256", "key_id": <first 16 hex of sha256(key)>, "value": <64 hex>}`. It covers the artifact minus `signature`, serialised as `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)` in UTF-8. The key is `BEACONPAVE_DRILL_KEY`, at least 32 bytes |
| on disk | `json.dumps(indent=2, ensure_ascii=False)` plus a newline |
| `pave drill` | `--event E --tier T --out PATH [--delta PRIOR]`. Exit 0: GO written. Exit 1: NO-GO written. Exit 2: nothing written |
| `pave drill verify PATH` | checks the signature **before anything else**. Exit 0 prints `signature: OK`. Exit 1 prints `signature: MISMATCH`. Exit 2 means the file was unreadable or there was no key |
| `pave drill read PATH` | one `key=value` line for each of `decision`, `mode`, `commit`, `tree_clean`, `ran_at`, `fix_by`, `fix_window_s`, `owner.seat`, `owner.oncall`, `caption_sha256` and `prior_sha256` (`-` when absent), plus one `finding=<scenario>/<rule>/<after_cue>/<before_cue>` line per finding |

**Artifact fields.**
- `mode`: `full` or `delta`.
- `commit` and `tree_clean`.
- `ran_at` and `decision`.
- `findings[]`, each with `scenario`, `rule`, `after_cue`, `before_cue` and `gap_s`.
- `owner` and `fix_by`, on a NO-GO only.
- `inputs.caption_sha256`.
- `prior_sha256`, on a delta only: the sha256 of the prior artifact's bytes.
- `signature`.

**Why these values.** The owner and the window differ on purpose from every default a writer
could fall back to (ADR-080 decision 3).

### The five falsifiers

**Naming.** *B* is PR 3's branch point on `main`. *S*, *C* and *F* are the `commit` fields of
the seeded, control and fixed artifacts. *R1* is the seeded artifact's path.

| | falsifier: the claim is false if | field | reader | the reader exists |
|---|---|---|---|---|
| **F1** | **the seed is not caught.** Seeded: `decision` ≠ `NO-GO`, or the findings are anything other than exactly `caption-check/max-gap/c006/c008` | `decision`, `finding` | `python -m pave.cli drill read` | lands in **PR 2** |
| **F2** | **the NO-GO names the wrong owner or time.** Seeded or control: `owner.seat` ≠ `service-team`, `owner.oncall` ≠ `webhook:player-captions`, or `fix_window_s` ≠ `129600` | `owner.seat`, `owner.oncall`, `fix_window_s` | `drill read` | lands in **PR 2** |
| **F3** | **a hand edit survives.** Three copies of R1 are made, each with one `sed` substitution and shown by `cmp` to differ from R1: `decision` to `GO`; `owner.oncall` to `webhook:someone-else`; `fix_by`'s year plus one. The claim fails on any copy for which `verify` does not exit 1 printing `signature: MISMATCH` | `signature` | `python -m pave.cli drill verify` | lands in **PR 2**. `sed` and `cmp` exist **today** |
| **F4** | **the control is not NO-GO for the same gap.** Control: `decision` ≠ `NO-GO`, or its `finding` lines differ from seeded's | `decision`, `finding` | `drill read` | lands in **PR 2** |
| **F5** | **the fix does not yield GO.** Fixed: `decision` ≠ `GO`, or any `finding` line | `decision`, `finding` | `drill read` | lands in **PR 2** |

**F3's liveness is checked first.** `verify` on the committed R1 must exit 0 with
`signature: OK`. That result is not evidence: one key and one canonical form make it true
by construction. Only the refusals count (ADR-080 decision 2).

**Validity is read before any falsifier.** A run that fails a validity check is INVALID. The
claim is then NOT MEASURED and M11 closes RED. No run is repeated.

| run | must hold | reader | exists |
|---|---|---|---|
| all three | `tree_clean=true`. `caption_sha256` equals `git show <commit>:drill/fixtures/jefferson-derby/captions.vtt \| sha256sum`, the fixture at the run's own `commit` (ADR-080 amendment 1). S, C and F lie in that order on PR 3's branch (`git merge-base --is-ancestor`) | `drill read`, `git show`, `sha256sum`, `git` | PR 2, today |
| seeded | `mode=full`. `git diff --name-only B S` is exactly the fixture. `drill verify` on R1 exits 0 printing `signature: OK`, and `signature.key_id` equals the first 16 hex of `milestones/M11/pre-registration/key.sha256` (ADR-080 amendment 4) | `git diff`, `drill verify`, `grep '"key_id"'` on R1, `head -c 16` on `key.sha256` | PR 2, today |
| control | `mode=delta`. `prior_sha256` equals `sha256sum R1`. `caption_sha256` equals seeded's. C ≠ S. `git diff --name-only S C` lies under `milestones/M11/`. `drill verify` exits 0 (ADR-080 amendment 4) | `drill read`, `drill verify`, `sha256sum`, `git diff` | PR 2, today |
| fixed | `mode=delta`. `prior_sha256` equals `sha256sum R1`. `git diff --name-only C F`, minus `milestones/M11/`, is exactly the fixture. `git diff B F -- drill/fixtures/jefferson-derby/captions.vtt` is empty. `drill verify` exits 0 (ADR-080 amendment 4) | `drill read`, `drill verify`, `sha256sum`, `git diff` | PR 2, today |

## Beside the claim, and not it

- **`verify` on the control and fixed artifacts**, exit code recorded.
- **The conformance tests.** Planted artifacts are refused before writing.
- **What a GO does not show:**
  - no live system, because the fixture is in the repository;
  - no page sent and no human reached (ADR-007:24-28);
  - no accepted risk;
  - one scenario of the three `BUILD.md` named.
- **One defect the arc cannot catch.** A delta drill that says GO on *any* change to the
  failing input would pass the arc, because the fix is the only edit to the fixture. PR 2's
  tests plant a non-fixing edit and assert NO-GO (ADR-080 decision 2).

## The plan

1. **PR 1** (this PR). SPEC/11, ADR-080, CLAUDE.md's feasibility rule, `BUILD.md:30`, and
   both index rows. No code.
2. **PR 2**, seated: the instrument and the pre-registration.
   - **The instrument:**
     - `quality/drill/go-no-go.schema.json`;
     - the writer, `pave/drill.py`;
     - the readers, `pave/drill_read.py`;
     - `drill/scenarios/caption-check.json`, carrying the rule, threshold, owner and window at
       the values pinned above;
     - the clean fixture;
     - the `pave drill` dispatch, replacing the stub;
     - the conformance tests and the two-key rules.
   - **The pre-registration, in this order:**
     1. Both readers run over artifacts the writer produced in the scratchpad, NO-GO and GO,
        with a throwaway key. The output is committed as
        `milestones/M11/pre-registration/readers.txt`.
     2. **Then** `milestones/M11/pre-registration/falsifiers.json`: the tables above as data,
        with a test that they equal this file's pinned values.
   - **Then** one seat round, and the deletability audit through `pave check`.
3. **PR 2b**, the named spare. See *Bounded*.
4. **The PR 2b repair**, added by ADR-080 amendment 4. It carries the rulings on the cold
   review: the PR 3 run key's sha256, and the three `drill verify` validity clauses. It has
   no code.
5. **PR 3**, the arc and the close.
   - **The arc:** the seed commit, the seeded run and F3's copies, the control run, the fix
     commit and the fixed run. Every reading is committed beside its artifact under
     `milestones/M11/runs/{seeded,control,fixed}/`.
   - **The arc runs in a fresh clone of PR 3's branch**, and the PR 3 body states it.
     `git update-index --skip-worktree` can hide edits to the writer and the scenario from
     `tree_clean` (ADR-080 amendment 4; cold review D19).
   - **The key** is published after the last reading.
   - **The close:** the journal, row 11, and tag `m11`.

## Implementation constraints, binding

1. **Not through `pave.verdict.build`.**
   - `quality/verdicts/schema.json` is not edited.
   - `gate decide` does not read the artifact in M11.
2. **The schema holds no claim value.** No `const` or `enum` covers the owner, the window,
   the threshold or a finding; a schema that held them would make F1 and F2 true by
   construction.
3. **The writer has no defaults for the claim values.** It reads the owner, window and
   threshold from `drill/scenarios/caption-check.json` at run time; if any is missing, it
   exits 2.
4. **No key, no artifact.** Without a key the writer exits 2 and writes nothing. The key is
   not committed before the last reading.
5. **`verify` checks the signature before the schema.** Otherwise an edit that breaks the
   schema would be refused for the wrong reason, hiding a signature that did not cover it.
6. **The readers import nothing from the writer.**
7. **Two-key rules land before the diffs they cover.**
   - Paths: `drill/scenarios/`, `quality/drill/`, `pave/drill.py`, `pave/drill_read.py` and
     `milestones/M11/`.
   - Seats: AI Quality plus Platform Engineering.
   - Why neither key is the Service Team's: Service Teams feel the threshold's pain, and
     `pave/twokey.py` enforces no Service Team seat (G9).
8. **No edit to M10's debt sites:** `pave/verdict.py`, `surfaces/`, `loadtest/`, the
   `Makefile`, `docs/governance/demo-script.md`, `.gitignore`, and `check` in `pave/cli.py`.
9. **Citations resolve from `main` or a tag.**

## What it builds

- the go/no-go schema;
- the writer and the two readers;
- one scenario and its fixture;
- `pave drill` in place of the stub;
- the two-key rules;
- three runs and their readings;
- the published key;
- the journal and row 11.

## What it does not build

- **the blackout sweep or the alarm self-test** (cut, ADR-080 decision 4);
- a deploy, or a model or AWS call;
- a verdict record for the drill, or a gate lane reading it;
- risk acceptance (`pave exception` stays a stub, `pave/cli.py:1732-1734`);
- a page;
- the self-heal classifier;
- claims 7, 8 or 12;
- a widening of `quality/verdicts/schema.json`;
- a re-run;
- **a pinned value, falsifier or reader re-scoped after a run reads it.**

## Obligations inherited, resolving none

| source | debt | owner | here |
|---|---|---|---|
| `milestones/M10/README.md:328`, row 30 | **debt 10**, unsigned | Security | **carried.** M11 produces no goldens refusal census, so that trigger does not fire. The signature route stays open to any PR, and M11 does not schedule it |
| `milestones/M10/README.md:275-331`, rows 1–29 | M10's debts | as listed there | **carried, unchanged.** Row 28's trigger fires when PR 2 edits `pave/twokey.py`; PR 2 records that and does not pay it |
| `milestones/M10/README.md:329`, row 31 | `brand_tone`'s widening: `labels.json:355` has `re_deferred_to: M11` | AI Quality + Security | **a close obligation.** `tests/test_calibration_owe.py:53-59` goes red when M11 closes unpaid. PR 3 pays or re-defers it on two keys, and this file does not choose which |
| `milestones/M09c/README.md:262` | debt 1, the browse gap, on a `catalog-search` semver bump | Tool Owner | not touched |
| `milestones/M09c/README.md:264` | debt 3, the `tokens_out` tier re-derivation | AI Quality | not touched |
| `milestones/M09c/README.md:263`, `:265-269` | 09c's other rows | as listed there | carried, unchanged |
| `docs/governance/recordings.json:49-56` | Act 4's recording, `owed_by: M11` | PM | **a close obligation** for PR 3 |
| ADR-075:2657 | the DMA rename, no earlier than M11's close | Legal/S&P + Data Governance | not scheduled. M11 adds uses of `jefferson-derby` to its blast radius (ADR-080 decision 4) |

## Bounded

**Four PRs in all, including this one and document-only ones: three planned and one named
spare.** They are PR 1, PR 2, **PR 2b (the spare)** and PR 3. **Amended to five PRs at the
PR 2b repair** (ADR-080 amendment 4, item 7). PR 2b merged before its repair could land, so
the repair is its own PR, the fourth, and PR 3 is the fifth.
- Every PR opened against `main` counts, including an exhibit.
- The fifth closes the milestone, red if necessary. *(Was: the fourth.)*
- Zero model calls, zero AWS calls, zero deploys, three drill runs and no re-run.
- One seat round, on PR 2.

**The spare is for one thing: a cold review of PR 2's writer and readers, before PR 3 runs.**
The reviewer must be someone who wrote neither. It answers three questions:
- Does each reader read the field the falsifier table names?
- Does each falsifier fire when its false state is planted?
- Has the code as built made any term true by construction?

Any repair the review finds lands in the same PR. It may not move a pinned value, add or drop
a falsifier, or run the arc. If the spare is not taken, the slot is spent on nothing else.

## Demo artifact

```text
export BEACONPAVE_DRILL_KEY="$(cat milestones/M11/runs/drill-key.txt)"
python -m pave.cli drill read   milestones/M11/runs/seeded/go-no-go.json
python -m pave.cli drill verify milestones/M11/runs/seeded/go-no-go.json
python -m pave.cli drill read   milestones/M11/runs/control/go-no-go.json
python -m pave.cli drill read   milestones/M11/runs/fixed/go-no-go.json
```

The block ships as `text`. Every file it reads is one PR 3 produces.

**Predicted shape:**
- seeded: `decision=NO-GO`, one `finding=caption-check/max-gap/c006/c008`,
  `owner.oncall=webhook:player-captions` and `fix_window_s=129600`;
- `signature: OK`;
- control: `decision=NO-GO` with the same finding;
- fixed: `decision=GO` with no finding.

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **F1**, the seed is caught | `drill read` on seeded | PR 3 |
| 2 | **F2**, owner and window as pinned | `drill read` on seeded and control | PR 3 |
| 3 | **F3**, a hand edit is refused | three `sed` copies, `cmp`, `drill verify` | PR 3 |
| 4 | **F4**, the control stays NO-GO | `drill read` on control, beside seeded | PR 3 |
| 5 | **F5**, the fix yields GO | `drill read` on fixed | PR 3 |
| 6 | the three runs are valid | the validity table: `git diff`, `sha256sum`, `git merge-base` | PR 3 |
| 7 | every reader emitted a value before the claim was committed | `readers.txt` committed before `falsifiers.json`, `git log` order | PR 2 |
| 8 | the committed claim equals this file's pins | the `falsifiers.json` test | PR 2 |
| 9 | conformance, and the non-fixing edit refused | PR 2's tests, each check deleted and run through `pave check` | PR 2 |
| 10 | the cap holds | *Bounded* against the PR list at the close | PR 3 |

## Definition of done

- [ ] **PR 1:** this file; ADR-080; CLAUDE.md's rule; `BUILD.md:30`; the SPEC and ADR index
      rows; `make check` green on the head before the body commit, cited by SHA; that head
      tagged and the tag pushed before the PR opens.
- [ ] **PR 2:** schema, writer, readers, scenario, fixture, dispatch, tests, two-key rules;
      `readers.txt`, then `falsifiers.json`; seat round; audit.
- [ ] **PR 2b** (the spare): the cold review and its repairs, or not taken.
- [ ] **PR 2b repair** (ADR-080 amendment 4): the run key's sha256 committed; the three
      `drill verify` validity clauses, verbatim in `falsifiers.json`; the review's debt rows.
- [ ] **PR 3:** seed, seeded run, F3, control, fix, fixed run, validity and F1–F5 read and
      committed, the key published; `brand_tone` paid or re-deferred; Act 4 recorded or
      deferred; journal; row 11's ✅; tag `m11`.

## What must not happen

- A pinned value, a falsifier or a reader changed after PR 2 commits `falsifiers.json`.
- A run repeated, or an INVALID run read as a pass.
- The fix and anything else in one commit, or a fixture edit between the seed and the fix.
- The artifact routed through `pave.verdict.build`, or `quality/verdicts/schema.json` widened.
- A GO published without F4 beside it.
- An artifact edited by hand anywhere but a scratch copy for F3.

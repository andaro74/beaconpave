# M11 — Game-day drill + go/no-go artifact

**Branches:** one per PR, five PRs (see *The cap*) · **Tag:** `m11` · **Closed:** 2026-09-14
**Spec:** `SPEC/11-drill-go-no-go.md` · **ADR:** ADR-080, amendments 1–4 · **Claims advanced:** #11

---

## The verdict

**Claim 11's arc holds.** All three runs are VALID, and none of the five falsifiers fired.

> **For event `jefferson-derby` at tier 3, a seeded caption failure makes `pave drill` write a
> NO-GO. The NO-GO names the seeded gap, the pinned owner, and a fix-by time set by the pinned
> window, under a signature that refuses a hand edit. The delta drill run without the fix still
> writes NO-GO for the same gap. The delta drill run with the fix writes GO.** (SPEC/11:34-37)

| run | commit | the run's exit | decision | findings | validity |
|---|---|---|---|---|---|
| **seeded** (cue `c007` deleted) | S = `10283eb` | 1 | NO-GO | `caption-check/max-gap/c006/c008` | VALID |
| **control** (delta, fix not applied) | C = `ce7b00f` | 1 | NO-GO | `caption-check/max-gap/c006/c008` | VALID |
| **fixed** (delta, `c007` restored) | F = `a69e3a7` | 0 | GO | none | VALID |

B, PR 3's branch point, is `52b35f1` on `main`.

**The arc ran in a fresh clone of `m11-pr3-arc`,** cloned from `origin` (ADR-080 amendment 4;
cold review D19). Before each run, `git ls-files -v` showed no skip-worktree and no
assume-unchanged entry, and `pave.drill` and `pave.drill_read` were imported from the clone.

**Where the evidence is:**
- `milestones/M11/runs/{seeded,control,fixed}/go-no-go.json` hold the three artifacts, and
  `readings.md` beside each holds every command with its full output;
- `milestones/M11/runs/validity.md` has every validity clause, its command and its verdict;
- `milestones/M11/runs/falsifiers.md` has F1–F5, each with its verdict;
- `milestones/M11/runs/drill-key.txt` is the run key, published after the last reading;
- `milestones/M11/runs/demo.md` is SPEC/11's demo block, run from a clean shell, with the
  published key's hash check.

### The ten measurement rows (SPEC/11, *Each claim, its measurement, and the PR*)

| # | claim | measurement | verdict |
|---|---|---|---|
| 1 | **F1**, the seed is caught | `drill read` on seeded: `decision=NO-GO`, exactly one `finding=caption-check/max-gap/c006/c008` | **held**, F1 did not fire |
| 2 | **F2**, owner and window as pinned | `drill read` on seeded and on control: `service-team`, `webhook:player-captions`, `129600` on both | **held**, F2 did not fire |
| 3 | **F3**, a hand edit is refused | three `sed` copies of R1, each shown by `cmp` to differ (lines 8, 23, 25); `drill verify` exit 1, `signature: MISMATCH` on all three; liveness exit 0 first, under the committed `key_id` | **held**, F3 did not fire |
| 4 | **F4**, the control stays NO-GO | `drill read` on control beside seeded: NO-GO, and `diff` of the finding lines is empty | **held**, F4 did not fire |
| 5 | **F5**, the fix yields GO | `drill read` on fixed: `decision=GO`, zero `finding=` lines | **held**, F5 did not fire |
| 6 | the three runs are valid | every clause of the validity table: `git diff`, `sha256sum`, `git merge-base`, `drill verify`, `grep`/`head` on `key_id` | **VALID**, all three |
| 7 | every reader emitted a value before the claim was committed | `readers.txt` committed before `falsifiers.json`: `git log` order, and `tests/test_drill_pins.py`'s ordering test in the gate | **met at PR 2**; re-read at this close (*The close's own measurements*) |
| 8 | the committed claim equals SPEC/11's pins | the `falsifiers.json` test, `tests/test_drill_pins.py`, in this PR's gate | **met** |
| 9 | conformance, and the non-fixing edit refused | PR 2's tests, each check deleted and run through `pave check` | **PARTIALLY MEASURED.** 39 of 96 plants run; 35 CAUGHT (W14, validation before writing, and W19, the non-fixing edit, among them), 4 SILENT, 57 unrun (ADR-080 amendment 2). Neither met nor failed |
| 10 | the cap holds | *Bounded* against the PR list at the close | **held against the amended cap of five.** The cap as first written, four, was exceeded and raised at ADR-080 amendment 4 (*The cap*) |

### What a GO does not show

These are SPEC/11's lines, not new ones:
- **No live system.** The fixture is in the repository.
- **No page sent and no human reached** (ADR-007:24-28).
- **No accepted risk.** `pave exception` stays a stub.
- **One scenario of the three `BUILD.md` named.** The blackout sweep and the alarm self-test
  are cut (ADR-080 decision 4).
- **A MAC, not a signature.** The key is published at `1347096`. From that commit on, the
  signature proves nothing further, and git history carries the artifacts.
- **One defect the arc cannot catch:** a delta drill that says GO on *any* change to the
  failing input. PR 2's audit caught its plant (W19); the arc did not exercise it.

---

## What can I demo right now?

From a clone of `main` after this PR merges, zero network, zero model calls:

```text
export BEACONPAVE_DRILL_KEY="$(cat milestones/M11/runs/drill-key.txt)"
python -m pave.cli drill read   milestones/M11/runs/seeded/go-no-go.json
python -m pave.cli drill verify milestones/M11/runs/seeded/go-no-go.json
python -m pave.cli drill read   milestones/M11/runs/control/go-no-go.json
python -m pave.cli drill read   milestones/M11/runs/fixed/go-no-go.json
```

**What the viewer sees**, from `milestones/M11/runs/demo.md`:
- **seeded:** `decision=NO-GO`, `finding=caption-check/max-gap/c006/c008`,
  `owner.oncall=webhook:player-captions`, `fix_window_s=129600`;
- **verify:** `signature: OK`, then `schema: OK`;
- **control:** `decision=NO-GO` with the same finding and a `prior_sha256`;
- **fixed:** `decision=GO`, no finding, and `-` for the owner and the fix-by.

To see F3, copy R1, change one character with `sed`, and run `drill verify` on the copy. It
prints `signature: MISMATCH` and exits 1.

**Act 4 is not recorded.** Its recording is deferred to after this close, with this block as
its script (`docs/governance/recordings.json`).

## What's the delta vs baseline?

**None to report, by design.** M11 changed no system that the goldens or the adversarial suite
measure. No deploy, zero model calls and zero AWS calls, so neither suite was run and `m00b` has
nothing to compare against. The drill's own control is the control run, and F4 reads it.

Unearned passes: none recorded. The one pass that is true by construction, F3's liveness, is
recorded as not evidence (ADR-080 decision 2).

## What broke?

1. **The cap, as first written.** ADR-080 decision 5 set four PRs with a named spare. The spare,
   PR 2b (#160), merged before the operator ruled on its cold review, so the rulings could not
   land in it. Folding them into PR 3 would have put commits between B and S and made the seeded
   run INVALID (review B1). Opening them as the fourth PR would have made the fourth PR close
   M11 without the arc. **The operator raised the cap from four to five at ADR-080 amendment 4**,
   and the repair became #161. That is a breach recorded as an amendment, not a plan.
2. **PR 2's deletability audit could not tell caught from silent** (ADR-080 amendment 2). Each
   plant commit to the writer or readers also tripped the readers-before-registration ordering
   test, so every CI run was red. It was read by the other failing tests and stopped at 39 of
   96: 35 CAUGHT, 4 SILENT (W01, W03, W08, W23). Claim 9 is partially measured because of it.
3. **The cold review found four BLOCKING findings in a pre-registration a seat round had
   passed** (`milestones/M11/pr2b-cold-review.md`):
   - carried debts whose triggers fell inside the seeded run's diff window;
   - F3 passing on any refusal, including a wrong key;
   - two artifacts read unverified;
   - skip-worktree hiding the writer.

   Three were repaired before B, and one became the fresh-clone procedure this arc followed.
4. **The first run of the demo block leaked the key into a terminal trace.** It ran under
   `set -x`, which echoed the expanded `export` line. The key had been published one commit
   earlier, so nothing was disclosed. The trace is not committed, and the block was re-run
   read-only for the transcript.
5. **Transcript headers were written with CRLF** in the working copies of the three
   `readings.md` files, `validity.md` and `demo.md`. Git warned, and the blobs are LF. No validity row
   hashes those files. Every hashed file (the fixture, the three artifacts, the key) read
   `i/lf w/lf`.
6. **Two obligations slid again, and the tests left no honest way to write "unscheduled".**
   `tests/test_calibration_owe.py` and `tests/test_demo_recordings.py` both call
   `milestone_is_closed()` on the target, and it raises for a milestone the progression table
   does not list. So `brand_tone` and Act 4 name `M12` as the date of the next decision, not a
   schedule, the way ADR-026 amendment 6 named M11. PR 3 edits no test.
7. **The operator's brief for this PR cited "D6" of the cold review, which has no D6.** The close
   obligations are ADR-080 decision 6, and their ordering after F is review D17. They were read
   as both.

## Definition of done, item by item (close-milestone step 1)

SPEC/11's checklist is left unticked in the file: PR 3 edits no SPEC (row 22 below).

| item | state |
|---|---|
| **PR 1:** SPEC/11, ADR-080, CLAUDE.md's rule, `BUILD.md:30`, the index rows, a gated head tagged before the PR | done, #158 (`cited-m11-pr1`) |
| **PR 2:** schema, writer, readers, scenario, fixture, dispatch, tests, two-key rules; `readers.txt` then `falsifiers.json`; seat round; audit | done, #159. **The audit was stopped at 39 of 96** (ADR-080 amendment 2) |
| **PR 2b** (the spare): the cold review | done, #160 |
| **PR 2b repair:** the run key's sha256, the three `drill verify` validity clauses, the review's debt rows | done, #161 |
| **PR 3:** seed, seeded run, F3, control, fix, fixed run, validity and F1–F5 read and committed, the key published | done, this PR |
| **PR 3:** `brand_tone` paid or re-deferred | **re-deferred**, owned and unscheduled, on two keys (AI Quality, Security) |
| **PR 3:** Act 4 recorded or deferred | **deferred** to after the close, on two keys (Platform Engineering, AI Quality) |
| **PR 3:** journal; row 11's ✅; tag `m11` | journal and row 11 done; `m11` is tagged after the merge, by the operator |

## The close's own measurements

- **The gate:** `python -m pave.cli check` in a clean worktree at the close's gated head. The
  exact line is in `docs/pr-bodies/m11-pr3.md`.
- **Row 7, re-read:** `git log` over `readers.txt` and `falsifiers.json` shows `readers.txt`'s
  last change committed before `falsifiers.json`'s. The ordering test that asserts it is green
  in the gate.
- **The key:** before the branch was cut, the sha256 through `pave.drill.load_key` of
  `$(cat ~/.beaconpave/m11-drill-key.txt)` equalled `key.sha256`. After publishing, the same
  check on `milestones/M11/runs/drill-key.txt` equals it too, with its transcript in
  `milestones/M11/runs/demo.md`.

## Not exercised at this close

- **close-milestone step 2, the evals.** Nothing was run that either suite reads: no deploy
  and no model call.
- **close-milestone step 6b, the guardrail holes and the accepted costs.** The frozen corpus
  needs credentials and a deployed guardrail, and M11 made no AWS call. No goldens refusal
  census was produced, so `enforcement-probing`'s trigger was not read. Debt 10 carries.
- **close-milestone step 8, the recording.** Deferred, as above.

## The cap

**Five PRs, against a cap raised from four to five at ADR-080 amendment 4.** No exhibit was
opened in M11.

| # | PR | what | merged as |
|---|---|---|---|
| 1 | #158 | PR 1, the spec | rebase, `cc35473` |
| 2 | #159 | PR 2, the instrument and the pre-registration | merge commit `6a5fbb7` |
| 3 | #160 | PR 2b, the spare: the cold review | merge commit `7c327a8` |
| 4 | #161 | the PR 2b repair: the rulings, the key hash, three validity clauses | merge commit `52b35f1` |
| 5 | this PR | PR 3, the arc and the close | open |

Also within the bound: three drill runs, no re-run, zero model calls, zero AWS calls, zero
deploys, and one seat round (on PR 2).

## Decisions

- **ADR-080** (PR 1): the feasibility rule amended, the claim as the arc with a control, the
  pinned values, scope and the cap.
  - **Amendment 1** (PR 2): the caption-bytes validity row; the first registration superseded;
    the audit through CI; Security as the third key.
  - **Amendment 2** (PR 2): the audit confounded, stopped at 39 of 96; claim 9 partially
    measured; the spare taken.
  - **Amendment 3** (PR 2b): the audit logs committed.
  - **Amendment 4** (PR 2b repair): the review's rulings, the run key's hash before B, D19's
    procedural remedy, the cap raised to five.
- **At this close, no ADR is written.** `brand_tone`'s seventh re-deferral is recorded in
  `labels.json` and here, not in an ADR-026 amendment (row 20 below).

---

## Debts carried out of M11, each with an owner and a trigger

**Only D17 is discharged here:** the close work landed after F. Nothing else is repaired.
*Unscheduled* means no milestone has planned it.

### From ADR-080 amendment 1, item 7

| # | debt | owner | trigger |
|---|---|---|---|
| 1 | `pave/cli.py`'s drill dispatch, and `.pyc` under `pave/__pycache__/`, are on no two-key rule | Platform Engineering | the next PR that edits `pave/cli.py`'s drill dispatch |
| 2 | `tests/test_drill*.py` witness the signature and the pins and are on no rule | Platform Engineering + Security | the next PR that edits `pave/twokey.py` |
| 3 | `README.md:961` and `Makefile:66` run `pave drill` without `--out`, which exits 2 | Platform Engineering | the next PR that edits either file |

Amendment 1's debt 7 (never squash PR 2) was discharged by #159's merge commit. Its debts 4 and
6's key half were resolved at amendment 4. Its debt 5 is D20, and debt 6's CRLF half is D21.

### From PR 2's deletability audit (`milestones/M11/pr2-deletability-audit.md`)

| # | debt | owner | trigger |
|---|---|---|---|
| 4 (D8) | **W01** SILENT: its refusal is shadowed by a second door its test cannot tell apart | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` |
| 5 (D9) | **W03** SILENT, the same shape | AI Quality + Platform Engineering | the same |
| 6 (D10) | **W08** SILENT, the same shape | AI Quality + Platform Engineering | the same |
| 7 (D11) | **W23** SILENT, the same shape | AI Quality + Platform Engineering | the same |
| 8 | **57 plants unrun**, plus 18 never on the spare's checklist (I1, I2, C01, C02, P01–P04, T01, T02, W40, W41, W43–W48). SPEC/11's row 9 is partially measured | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py`, `pave/drill_read.py` or `quality/drill/` |

### From the cold review (`milestones/M11/pr2b-cold-review.md`)

| # | debt | owner | trigger |
|---|---|---|---|
| 9 (D12) | R09 has no witness: the pre-print surrogate refusal is shadowed by the print guard | AI Quality + Platform Engineering | the next PR that edits `pave/drill_read.py` |
| 10 (D13) | S03 has no witness: `required: signature` is never the refusing door | AI Quality + Platform Engineering | the next PR that edits `quality/drill/` |
| 11 (D14) | 18 writer refusal tests accept any refusal, and W43's tier type check is shadowed by the schema | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` |
| 12 (D15) | the claim's event and tier are read by no reader | AI Quality | the next PR that edits `drill/scenarios/` |
| 13 (D16) | `python -m pave.cli` loads `pave.drill` before it dispatches to the readers | Platform Engineering | row 1's trigger |
| 14 (D18) | the `max-gap` segment of every finding is a writer constant | AI Quality | a second rule |
| 15 (D19) | skip-worktree can hide edits to the writer and the scenario from `tree_clean`. **The procedural remedy was applied:** the arc ran in a fresh clone, stated in PR 3's body. No check enforces it | Platform Engineering + Security | the next drill run claimed as evidence |
| 16 (D20) | the clean fixture's bytes are pinned by no reader, and `drill/fixtures/` is on one key. **Its trigger, "PR 3, after the fixed run", fired here and is not paid:** paying it means a reader or a test, and PR 3 changes neither | AI Quality | the next PR that edits `drill/fixtures/` or `tests/test_drill_pins.py` |
| 17 (D21) | a CRLF re-save of the fixture makes a run INVALID with no retry. **Read at its trigger:** `git ls-files --eol` read `i/lf w/lf` before the fix. The hazard is not repaired, since no check refuses a CRLF fixture before a run | Platform Engineering | the next PR that edits `drill/fixtures/` |

D17 (close work after F) is **discharged**: every close edit landed after F.

### Opened at this close

| # | debt | owner | trigger |
|---|---|---|---|
| 18 | **`brand_tone`'s widening, re-deferred a seventh time, owned and UNSCHEDULED** (M10 row 31). `labels.json` names `M12` only because the owe test raises for an unlisted milestone; it is the date of the next decision. Paying needs model calls and a labelling pass | AI Quality + Security | M12's close: paid by extending the deterministic draw, retired by AI Quality with Security, or re-deferred with a ground true then |
| 19 | **Act 4's recording, deferred once from M11** to after its close. `owed_by: M12` is the date of the next decision, not a schedule. The script is `milestones/M11/runs/demo.md` | PM + Platform Engineering | M12's close: recorded, or re-deferred with `deferred_from` counting it |
| 20 | **No ADR-026 amendment records the seventh slide.** Amendments 1–6 recorded slides one to six. This one lives in `labels.json`'s `why_re_deferred` and in this journal | AI Quality | the next PR that edits `ADR-026` or `labels.json`'s `owed` entry |
| 21 | **Nothing but a test's need for a listed row makes `M12` the target of rows 18 and 19.** Neither obligation can be written as unscheduled while `milestone_is_closed` raises for an unlisted milestone | PM + Platform Engineering | the next PR that edits `tests/milestone_status.py`, or M12's spec |
| 22 | **SPEC/11's definition-of-done checkboxes are unticked**, because PR 3 edits no SPEC | PM | the next PR that edits `SPEC/11-drill-go-no-go.md` |

### From M10 (`milestones/M10/README.md:275-331`)

- **Rows 1–27 and 29 carry unchanged,** each with its owner and trigger as listed there.
- **Row 28** (33 of 86 test files on no two-key rule) **fired at M11 PR 2**, which edited
  `pave/twokey.py`, and was not paid. Platform Engineering; the next PR that edits
  `pave/twokey.py`.
- **Row 30, debt 10:** Security's re-disposition of `enforcement-probing` stays unsigned. M11
  produced no goldens refusal census, so that trigger did not fire. Security; the operator's
  signature on the draft as ADR-035 amendment 12, or the next milestone producing a goldens
  refusal census.
- **Row 31, `brand_tone`:** superseded by row 18 above.

### From 09c and earlier, unchanged

- **09c's debts 1–4 and 6–8** (`milestones/M09c/README.md:262-269`) carry unchanged, as does
  its inherited register. M11 touched none.
- **The DMA rename** (ADR-075 amendment 8) was re-dated to no earlier than M11's close and is
  still not scheduled. M11 added uses of `jefferson-derby` to its blast radius (ADR-080 decision
  4). Owner: Legal/S&P + Data Governance.

## What's next

**M12, the self-heal classifier and curation panel, carrying claims 7, 8 and 12.** It inherits
two obligations named at this close only because a test needs a listed row: `brand_tone` and
Act 4 (rows 18, 19 and 21). Neither is M12's work unless M12's spec says so.

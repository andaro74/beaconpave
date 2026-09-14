# M11 PR 3: the five falsifiers, read

**Read after validity** (`milestones/M11/runs/validity.md`: all three runs VALID). Each
falsifier is the one registered in `milestones/M11/pre-registration/falsifiers.json`, carried
verbatim from SPEC/11. **None fires.** Claim 11, as SPEC/11 words it, **holds**, within what
*What a GO does not show* and ADR-080's cuts say it does not reach.

The readings are the per-run transcripts. This file quotes their output and adds nothing.

- **R1** = `milestones/M11/runs/seeded/go-no-go.json`, at S = `10283eb264ca7d436df60f373ca0bb860cd3f003`
- **R2** = `milestones/M11/runs/control/go-no-go.json`, at C = `ce7b00f7e928e0aeb86d6bb4ab5afaf3abc05b93`
- **R3** = `milestones/M11/runs/fixed/go-no-go.json`, at F = `a69e3a7cbd03e535a3d0b5d9cdb4673a26500d70`

## Verdicts

| | falsifier: the claim is false if | command | read | verdict | where |
|---|---|---|---|---|---|
| **F1** | seeded: `decision` ≠ `NO-GO`, or the findings are anything other than exactly `caption-check/max-gap/c006/c008` | `python -m pave.cli drill read R1` | `decision=NO-GO`; exactly one line, `finding=caption-check/max-gap/c006/c008` | **does not fire** | `runs/seeded/readings.md`, *drill read*, *F1* |
| **F2** | seeded or control: `owner.seat` ≠ `service-team`, `owner.oncall` ≠ `webhook:player-captions`, or `fix_window_s` ≠ `129600` | `python -m pave.cli drill read R1`, `… R2` | both: `owner.seat=service-team`, `owner.oncall=webhook:player-captions`, `fix_window_s=129600` | **does not fire** | `runs/seeded/readings.md` *F2*; `runs/control/readings.md` *F2* |
| **F3** | any of three `sed` copies of R1, each shown by `cmp` to differ, for which `verify` does not exit 1 printing `signature: MISMATCH` | `sed`, `cmp`, `python -m pave.cli drill verify <copy>` | `decision`→`GO`: `cmp` differs at line 8, exit 1, MISMATCH. `owner.oncall`→`webhook:someone-else`: line 23, exit 1, MISMATCH. `fix_by` 2026→2027: line 25, exit 1, MISMATCH | **does not fire** | `runs/seeded/readings.md`, *F3* |
| **F4** | control: `decision` ≠ `NO-GO`, or its `finding` lines differ from seeded's | `python -m pave.cli drill read R2`, beside `… R1` | `decision=NO-GO`; `finding=caption-check/max-gap/c006/c008` on both; `diff` of the two sets exits 0, empty | **does not fire** | `runs/control/readings.md`, *F4* |
| **F5** | fixed: `decision` ≠ `GO`, or any `finding` line | `python -m pave.cli drill read R3` | `decision=GO`; `grep -c '^finding='` prints `0` | **does not fire** | `runs/fixed/readings.md`, *F5* |

## F3's liveness, which is not evidence

`python -m pave.cli drill verify R1` exited 0 printing `signature: OK` before any copy was
made. One key and one canonical form make that true by construction (ADR-080 decision 2), so
it counts for nothing. Its job was to make the three refusals mean something. Since ADR-080
amendment 4 item 2, a failed liveness check would have made the seeded run INVALID, with no
copy read. It did not fail.

**The key was the writer's.** R1's `signature.key_id` is `cb16e839a08a5a74`, the first 16
hex of `milestones/M11/pre-registration/key.sha256`, committed before B. So the MISMATCH on
each copy is the edit being refused, not a wrong key refusing everything (cold review B2).

## The claim's halves, against the three runs

| half of the claim | run | falsifier | read |
|---|---|---|---|
| a seeded caption failure makes `pave drill` write a NO-GO naming the seeded gap | seeded | F1 | NO-GO, `c006/c008` |
| … the pinned owner and a fix-by time set by the pinned window | seeded | F2 | `service-team`, `webhook:player-captions`, 129600 s |
| … under a signature that refuses a hand edit | seeded | F3 | three edits, three MISMATCHes |
| the delta drill without the fix still writes NO-GO for the same gap | control | F4, F2 | NO-GO, same finding, same owner and window |
| the delta drill with the fix writes GO | fixed | F5 | GO, no finding |

## What this does not show

These lines are SPEC/11's, not new:
- no live system: the fixture is in the repository;
- no page sent and no human reached;
- no accepted risk;
- one scenario of the three `BUILD.md` named;
- a MAC in place of a signature. The key is published after this reading, and from then on
  the signature proves nothing further.

**One defect the arc cannot catch.** A delta drill that says GO on *any* change to the
failing input passes all five falsifiers, because the fix is the only edit to the fixture.
The arc did not exercise it. PR 2's test and audit row W19 (CAUGHT) did.

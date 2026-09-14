# M11 PR 2: the deletability audit, recorded at 39 of 96 plants and stopped

**Read this first: a red CI run is not the reading.**

Every plant run failed
`tests/test_drill_pins.py::test_the_readers_were_shown_emitting_before_the_claim_was_committed`.
Each plant was a commit. The test requires the last change to `readers.txt` to descend from
the last change to `pave/drill.py`, `pave/drill_read.py`, the schema and `pave/cli.py`, so a
commit to the writer or the readers after `readers.txt` trips it, whatever the plant does. It
failed in all 39 runs, including the four that caught nothing else.

**So each plant is read by the failing tests other than that one:** CAUGHT if any failed,
SILENT if none did. This is ADR-080 amendment 2, item 1.

## What ran

- **The mechanism** was ADR-080 amendment 1, item 4:
  - each plant was a commit whose only parent is `2465b11`, changing one door;
  - the commits were force-pushed onto `m11-pr2-drill-instrument` one at a time, 15 s apart;
  - each registered one `quality-gate` run;
  - each run was read from its `L0 unit + L1 contract` step log.
- **Generated:** 96 plants. **Pushed and run:** 39. The operator stopped the push after R02.
- **The branch was force-restored to `2465b11`** and stays there. The 39 red runs remain in
  #159's check history.
- **The plant commits are reachable from no ref**, so they will not survive `git gc`. Each
  CI run log is the durable evidence, cited by run id. No exhibit was opened.

## The control

| where | head | pytest | check |
|---|---|---|---|
| CI, `quality-gate` run [34778857665](https://github.com/andaro74/beaconpave/actions/runs/34778857665) | `2465b11` | 5133 passed, 9 skipped | `check: PASS` |
| local clean worktree, Windows, the interim body's gate line | `2465b11` | 5134 passed, 8 skipped | `check: PASS`, exit 0 |

**Both collect 5142 tests, so one test passes locally and skips in CI.**

- **Measured locally:** `python -m pytest -q -rs -o addopts=` at `2465b11` lists all 8
  local skips as `tests/test_no_account_identifiers.py:186` and `:204`, four each, *not
  decodable as text*. Every other test ran.
- **Not measured in CI.** The gate runs pytest with `-q` and no `-rs`, so the CI log names
  no skipped test.
- **The test CI skipped, by reading:**
  `tests/test_cited_commits_resolve.py::test_a_commit_only_a_feature_branch_holds_is_not_reachable`.
  It skips when the clone holds no local branch other than `main` that is neither merged
  nor tagged (`:155`). CI's checkout is a detached merge ref with no local branches.
  Locally, unmerged branches exist and it runs.

## The reading, one row per pushed plant

| plant | what it removed or weakened | plant commit | CI run | failing tests other than the ordering test | reading |
|---|---|---|---|---|---|
| I3 | writer: imports pave.verdict (constraint 1) | c608fc9fe0ec | [34778806054](https://github.com/andaro74/beaconpave/actions/runs/34778806054) | test_drill.py::test_the_writer_imports_no_pave_module_so_nothing_goes_through_verdict_build | CAUGHT |
| R01 | read: fix_window_s computed one second long | 680970d304c1 | [34778819511](https://github.com/andaro74/beaconpave/actions/runs/34778819511) | test_drill_read.py::test_read_prints_specs_lines_in_specs_order_for_a_no_go<br>test_drill_read.py::test_read_computes_a_window_longer_than_a_day<br>test_drill_read.py::test_what_the_writer_writes_the_readers_verify_and_print | CAUGHT |
| R02 | read: a finding's cue order swapped | f19f509eccdb | [34778831696](https://github.com/andaro74/beaconpave/actions/runs/34778831696) | test_drill_read.py::test_read_prints_specs_lines_in_specs_order_for_a_no_go<br>test_drill_read.py::test_read_prints_one_finding_line_per_finding_in_file_order<br>test_drill_read.py::test_what_the_writer_writes_the_readers_verify_and_print | CAUGHT |
| W01 | writer: the no-key refusal removed | 2e5825ba3fda | [34778295404](https://github.com/andaro74/beaconpave/actions/runs/34778295404) | none | **SILENT** |
| W02 | writer: the 32-byte key floor lowered to 1 | a6397b923e43 | [34778311852](https://github.com/andaro74/beaconpave/actions/runs/34778311852) | test_drill.py::test_no_key_no_artifact[env2]<br>test_drill.py::test_the_writers_key_floor_is_32_bytes_not_32_characters | CAUGHT |
| W03 | writer: an existing --out no longer refused before writing | 77bb08668bd9 | [34778326365](https://github.com/andaro74/beaconpave/actions/runs/34778326365) | none | **SILENT** |
| W04 | writer: owner.seat defaults to the pinned seat when missing | 6766685c514d | [34778338511](https://github.com/andaro74/beaconpave/actions/runs/34778338511) | test_drill.py::test_a_missing_claim_value_writes_nothing[path0]<br>test_drill.py::test_a_claim_value_of_the_wrong_shape_writes_nothing[owner-value6] | CAUGHT |
| W05 | writer: owner.oncall defaults when missing | a50338f71a21 | [34778354266](https://github.com/andaro74/beaconpave/actions/runs/34778354266) | test_drill.py::test_a_missing_claim_value_writes_nothing[path1] | CAUGHT |
| W06 | writer: max_gap_s defaults to 4.0 when missing | b7ebc1e5b1af | [34778369587](https://github.com/andaro74/beaconpave/actions/runs/34778369587) | test_drill.py::test_a_missing_claim_value_writes_nothing[path3] | CAUGHT |
| W07 | writer: a tier with no window defaults to 86400 s | 21bb845422bd | [34778381126](https://github.com/andaro74/beaconpave/actions/runs/34778381126) | test_drill.py::test_a_missing_claim_value_writes_nothing[path4] | CAUGHT |
| W08 | writer: an event with no caption source defaults to a conventional path | cc8b2506f6f8 | [34778398659](https://github.com/andaro74/beaconpave/actions/runs/34778398659) | none | **SILENT** |
| W09 | writer: max-gap strict > weakened to >= | a85065da20e8 | [34778440836](https://github.com/andaro74/beaconpave/actions/runs/34778440836) | test_drill.py::test_a_gap_equal_to_the_threshold_is_not_a_finding_and_one_millisecond_more_is | CAUGHT |
| W10 | writer: the gap computed one millisecond short | 990e79ba560a | [34778453299](https://github.com/andaro74/beaconpave/actions/runs/34778453299) | test_drill.py::test_a_gap_above_the_threshold_writes_no_go_naming_both_cues_the_owner_and_the_window<br>test_drill.py::test_a_gap_equal_to_the_threshold_is_not_a_finding_and_one_millisecond_more_is<br>test_drill.py::test_a_timestamp_with_no_hour_field_is_read<br>test_drill.py::test_two_gaps_are_two_findings_in_file_order | CAUGHT |
| W11 | writer: decision always GO | c75012868030 | [34778467613](https://github.com/andaro74/beaconpave/actions/runs/34778467613) | test_drill.py::test_a_gap_above_the_threshold_writes_no_go_naming_both_cues_the_owner_and_the_window<br>test_drill.py::test_a_gap_equal_to_the_threshold_is_not_a_finding_and_one_millisecond_more_is<br>test_drill.py::test_a_delta_without_the_fix_stays_no_go_for_the_same_gap<br>test_drill.py::test_a_delta_after_an_edit_that_does_not_fix_the_gap_stays_no_go<br>test_drill.py::test_the_command_exits_0_on_go_1_on_no_go_and_2_when_nothing_is_written<br>test_drill.py::test_a_write_that_fails_leaves_no_artifact_and_no_partial_file[fsync]<br>test_drill.py::test_a_write_that_fails_leaves_no_artifact_and_no_partial_file[link]<br>test_drill_read.py::test_what_the_writer_writes_the_readers_verify_and_print | CAUGHT |
| W12 | writer: a NO-GO names no owner | 1a7794b6115a | [34778481596](https://github.com/andaro74/beaconpave/actions/runs/34778481596) | test_drill.py::test_a_gap_above_the_threshold_writes_no_go_naming_both_cues_the_owner_and_the_window<br>test_drill.py::test_the_schema_refuses_an_undeclared_key_at_every_level<br>test_drill.py::test_a_delta_without_the_fix_stays_no_go_for_the_same_gap<br>test_drill.py::test_a_delta_refuses_a_prior_whose_signature_does_not_verify<br>test_drill.py::test_the_command_exits_0_on_go_1_on_no_go_and_2_when_nothing_is_written | CAUGHT |
| W13 | writer: fix_by ignores the tier's window (always 86400 s) | c01080350a6a | [34778494118](https://github.com/andaro74/beaconpave/actions/runs/34778494118) | test_drill.py::test_a_gap_above_the_threshold_writes_no_go_naming_both_cues_the_owner_and_the_window<br>test_drill.py::test_the_window_is_the_tiers_own<br>test_drill_read.py::test_what_the_writer_writes_the_readers_verify_and_print | CAUGHT |
| W14 | writer: schema validation before writing removed | 052c923f09e5 | [34778563038](https://github.com/andaro74/beaconpave/actions/runs/34778563038) | test_drill.py::test_the_artifact_is_validated_before_anything_is_written | CAUGHT |
| W15 | writer: the prior's signature no longer verified | 16832ac3061e | [34778644790](https://github.com/andaro74/beaconpave/actions/runs/34778644790) | test_drill.py::test_a_delta_refuses_a_prior_whose_signature_does_not_verify<br>test_drill.py::test_a_delta_refuses_a_prior_signed_with_another_key | CAUGHT |
| W16 | writer: a prior for another event or tier no longer refused | 6c8698ccb002 | [34778661206](https://github.com/andaro74/beaconpave/actions/runs/34778661206) | test_drill.py::test_a_delta_refuses_a_prior_for_another_event_or_tier[other-event-7]<br>test_drill.py::test_a_delta_refuses_a_prior_for_another_event_or_tier[synthetic-event-8] | CAUGHT |
| W17 | writer: a GO prior (no findings) no longer refused by its own door | 9dd9ea9f4232 | [34778676543](https://github.com/andaro74/beaconpave/actions/runs/34778676543) | test_drill.py::test_a_delta_refuses_a_go_prior | CAUGHT |
| W18 | writer: a delta drill always writes GO (F4's defect) | 8ff70195251e | [34778732273](https://github.com/andaro74/beaconpave/actions/runs/34778732273) | test_drill.py::test_a_delta_without_the_fix_stays_no_go_for_the_same_gap<br>test_drill.py::test_a_delta_after_an_edit_that_does_not_fix_the_gap_stays_no_go | CAUGHT |
| W19 | writer: a delta writes GO whenever the caption bytes differ from the prior's (ADR-080 decision 2's defect) | f401667e2e55 | [34778746050](https://github.com/andaro74/beaconpave/actions/runs/34778746050) | test_drill.py::test_a_delta_after_an_edit_that_does_not_fix_the_gap_stays_no_go | CAUGHT |
| W20 | writer: prior_sha256 over re-serialised JSON, not the prior's bytes | 9e5056d0c7e1 | [34778721144](https://github.com/andaro74/beaconpave/actions/runs/34778721144) | test_drill.py::test_a_delta_without_the_fix_stays_no_go_for_the_same_gap<br>test_drill.py::test_a_delta_after_the_fix_writes_go | CAUGHT |
| W21 | writer: the signature does not cover decision | 11766c40bd17 | [34778630994](https://github.com/andaro74/beaconpave/actions/runs/34778630994) | test_drill.py::test_the_signature_is_hmac_sha256_over_the_pinned_canonical_form<br>test_drill_read.py::test_what_the_writer_writes_the_readers_verify_and_print | CAUGHT |
| W22 | writer: tree_clean always true | f753e21e77d7 | [34778574570](https://github.com/andaro74/beaconpave/actions/runs/34778574570) | test_drill.py::test_the_commit_and_the_tree_state_are_recorded | CAUGHT |
| W23 | writer: a cue with no id no longer refused | cc1a41b7f074 | [34778508538](https://github.com/andaro74/beaconpave/actions/runs/34778508538) | none | **SILENT** |
| W24 | writer: timestamps without an hour field no longer read | e80ae862714c | [34778521560](https://github.com/andaro74/beaconpave/actions/runs/34778521560) | test_drill.py::test_a_timestamp_with_no_hour_field_is_read | CAUGHT |
| W25 | writer: an unexpected crash exits 1 (NO-GO) not 2 | 982533d5705e | [34778763574](https://github.com/andaro74/beaconpave/actions/runs/34778763574) | test_drill.py::test_a_crash_is_exit_2_and_never_exit_1_which_means_no_go<br>test_drill.py::test_an_interrupt_before_publishing_is_exit_2_and_writes_nothing | CAUGHT |
| W26 | writer: --help or a malformed command exits 0 (GO) not 2 | 66cafabf0f2a | [34778775866](https://github.com/andaro74/beaconpave/actions/runs/34778775866) | test_drill.py::test_the_command_exits_0_on_go_1_on_no_go_and_2_when_nothing_is_written | CAUGHT |
| W27 | writer: a NO-GO exits 0 | 07710eb8271a | [34778788504](https://github.com/andaro74/beaconpave/actions/runs/34778788504) | test_drill.py::test_the_command_exits_0_on_go_1_on_no_go_and_2_when_nothing_is_written | CAUGHT |
| W28 | writer: a cue ending before it starts no longer refused | ec6d25c24af0 | [34778533524](https://github.com/andaro74/beaconpave/actions/runs/34778533524) | test_drill.py::test_an_unreadable_caption_file_writes_nothing[WEBVTT\n\ns01\n00:00:03.000 --> 00:00:01.000\nbackwards\n-ends before it starts] | CAUGHT |
| W29 | writer: a duplicate cue id no longer refused | 1e2539658866 | [34778550408](https://github.com/andaro74/beaconpave/actions/runs/34778550408) | test_drill.py::test_an_unreadable_caption_file_writes_nothing[WEBVTT\n\ns01\n00:00:00.000 --> 00:00:01.000\na\n\ns01\n00:00:01.000 --> 00:00:02.000\nb\n-appears twice] | CAUGHT |
| W30 | writer: a rule other than max-gap no longer refused | 74d528fc7c94 | [34778411892](https://github.com/andaro74/beaconpave/actions/runs/34778411892) | test_drill.py::test_a_claim_value_of_the_wrong_shape_writes_nothing[rule-min-gap] | CAUGHT |
| W31 | writer: max_gap_s type and sign no longer checked | d5cf65ab63df | [34778425312](https://github.com/andaro74/beaconpave/actions/runs/34778425312) | test_drill.py::test_a_claim_value_of_the_wrong_shape_writes_nothing[max_gap_s-2.0]<br>test_drill.py::test_a_claim_value_of_the_wrong_shape_writes_nothing[max_gap_s-True]<br>test_drill.py::test_a_claim_value_of_the_wrong_shape_writes_nothing[max_gap_s--1] | CAUGHT |
| W32 | writer: a prior naming another scenario no longer refused | 46af50cfea25 | [34778688179](https://github.com/andaro74/beaconpave/actions/runs/34778688179) | test_drill.py::test_a_delta_refuses_a_signed_prior_naming_another_scenario | CAUGHT |
| W33 | writer: a delta recorded as mode full | eae47a38f4af | [34778704450](https://github.com/andaro74/beaconpave/actions/runs/34778704450) | test_drill.py::test_a_delta_without_the_fix_stays_no_go_for_the_same_gap | CAUGHT |
| W34 | writer: caption_sha256 not over the caption bytes | aba7b0c661fe | [34778616929](https://github.com/andaro74/beaconpave/actions/runs/34778616929) | test_drill.py::test_a_delta_after_an_edit_that_does_not_fix_the_gap_stays_no_go | CAUGHT |
| W35 | writer: the commit recorded is not HEAD | b9db05a449bd | [34778590354](https://github.com/andaro74/beaconpave/actions/runs/34778590354) | test_drill.py::test_the_commit_and_the_tree_state_are_recorded<br>test_drill.py::test_a_delta_without_the_fix_stays_no_go_for_the_same_gap | CAUGHT |
| W36 | writer: a directory that is not a git repository no longer refused | 20cf0845b219 | [34778602211](https://github.com/andaro74/beaconpave/actions/runs/34778602211) | test_drill.py::test_outside_a_git_repository_nothing_is_written | CAUGHT |

## Counts

| | plants |
|---|---|
| generated | **96** |
| pushed and run | **39**: I3, R01, R02, W01–W36 |
| CAUGHT | **35** |
| SILENT | **4**: W01, W03, W08, W23 |
| unrun | **57**: W40, W41, W43, W44, W45, W46, W47, W48; R03, R04, R05, R06, R07, R08, R09, R10; V01, V02, V03, V04, V05, V06, V07, V08, V09, V10, V11; I1, I2; C01, C02; S01, S02, S03, S04, S05, S06; P01, P02, P03, P04; F01, F02, F03, F04, F05, F06, F07, F08; T01, T02; K01, K02, K03, K04, K05, K06 |

**The reader plants stopped early.** R01 and R02 ran. R03–R10, V01–V11, I1, I2, C01 and C02
did not. The audit is recorded here as stopped, not resumed (ADR-080 amendment 2, item 2).
PR 2b works R03–R10, S01–S06, K01–K06 and F01–F08 by reading (item 4).

## What CAUGHT here does and does not show

- **It shows that at least one test other than the ordering test failed with the plant in
  place.**
- **It does not show which assertion failed.**
- **It does not show that the plant's own test was the only witness.**
- **It does not show "caught in one file" against "caught in several".** Every CAUGHT run
  also carries the ordering failure in `test_drill_pins.py`, so file counts from these runs
  are not readings.

## Debts carried out of PR 2: the four SILENT plants, none repaired here

Numbered on from ADR-080 amendment 1's seven. **The mechanism in each row is read from the
code at `2465b11`, not measured.** The measurement is only that no other test failed.

| # | plant | what goes unwitnessed | owner | trigger |
|---|---|---|---|---|
| D8 | **W01** | The no-key refusal (`pave/drill.py:233-234`) is shadowed by the key floor (`:235-237`), which still refuses an empty key. `test_no_key_no_artifact` (`tests/test_drill.py:221-225`) matches the substring `key`, which both messages contain, so it cannot tell which door refused (ADR-040's shape) | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` |
| D9 | **W03** | The early `--out` exists refusal (`pave/drill.py:314-316`) is shadowed by `publish`'s `os.link` (`:373-377`), which refuses an existing target with the same `already exists` message. `test_an_existing_artifact_is_never_overwritten` (`tests/test_drill.py:228-235`) matches that substring and cannot tell which door refused | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` |
| D10 | **W08** | The no-caption-source refusal (`pave/drill.py:99-103`) is shadowed by the caption read (`:328-332`), which refuses the defaulted path because the synthetic repository has no file there. `test_a_missing_claim_value_writes_nothing[path6]` (`tests/test_drill.py:187-199`) calls `_refused` with no `match` at all, so any refusal passes and it cannot tell which door refused | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` |
| D11 | **W23** | The no-id refusal (`pave/drill.py:183-184`) is shadowed by the timing-line refusal (`:186-188`), whose message quotes the block's text `'no id'`. `test_an_unreadable_caption_file_writes_nothing` (`tests/test_drill.py:170-182`) matches the substring `no id` and cannot tell which door refused | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` |

## M10's debt row 28 fired, and is not paid

**`milestones/M10/README.md:326`, row 28:** *33 of 86 test files match no two-key rule*,
triggered by *the next PR that edits `pave/twokey.py`*. PR 2 edits `pave/twokey.py`, adding
the drill rule, so the trigger fired.

**PR 2 does not pay it.** SPEC/11's obligations table says PR 2 records it and does not pay
it. The drill rule covers `drill/scenarios/`, `quality/drill/`, `pave/drill.py`,
`pave/drill_read.py` and `milestones/M11/`, and no test file. ADR-080 amendment 1's debt 2
records that `tests/test_drill*.py` are on no rule either: row 28's shape.

Owning seats: AI Quality + Platform Engineering + Security (the drill rule, `pave/twokey.py`).

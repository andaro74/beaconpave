# M11 PR 2b: the cold review of PR 2's writer and readers

**The reviewer wrote none of PR 2 and had no context from it.** Everything below comes from
reading `main` at `6a5fbb7`. No drill was run, no plant was applied, and no code was edited.
Every "goes red" below is a reading of the test source, not a measurement.

**Read, in order:**
- CLAUDE.md and SPEC/11;
- ADR-080 decision 5 and amendments 1–2;
- `falsifiers.json`, `readers.txt` and `pr2-deletability-audit.md`;
- `pave/drill.py`, `pave/drill_read.py`, the schema and the scenario;
- the drill rule in `pave/twokey.py:1716-1757`;
- `tests/test_drill.py`, `tests/test_drill_read.py` and `tests/test_drill_pins.py`.

The plant bodies were read from PR 2's audit scratchpad (`plants.py` at `2465b11`). Each
anchor was checked by eye against `main`'s text, and every one is present.

**Grades.**
- **BLOCKING:** a falsifier or a validity row could pass falsely or fail falsely in PR 3.
- **DEBT:** everything else worth carrying.

## The findings, in one table

| # | grade | finding | how it happens |
|---|---|---|---|
| **B1** | **BLOCKING** | Three carried debts are triggered inside the seeded run's diff window. Paying any of them there makes the seeded run INVALID | by following ADR-080 amendment 1's debt table as worded |
| **B2** | **BLOCKING** | F3's pass does not show the run key was the writer's. A `verify` under any other key refuses all three copies, and a failed liveness check has no registered meaning | by accident, e.g. a key file saved with CRLF |
| **B3** | **BLOCKING** | F2 on the control run, F4, F5, and every control and fixed validity row read artifacts no registered check has verified | a hand edit of the control or fixed artifact before its reading |
| **B4** | **BLOCKING** | `tree_clean` comes from `git status --porcelain`, which skip-worktree defeats. Amendment 1 closed that route for the fixture's bytes only, not the writer's or the scenario's | deliberate `git update-index --skip-worktree`, the mechanism amendment 1 ruled in scope |
| D1 | DEBT | R09 has no witness: the pre-print surrogate refusal is shadowed by the print guard | ADR-040's shape |
| D2 | DEBT | S03 has no witness, and the schema's `required: signature` is inert | — |
| D3 | DEBT | 18 writer refusal tests accept any refusal. By reading, W43's door is shadowed by the schema, so it would be a fifth D8–D11 | ADR-040's shape |
| D4 | DEBT | The claim's event and tier are read by no reader | — |
| D5 | DEBT | The command every falsifier names loads the writer in-process | — |
| D6 | DEBT | PR 3's close work must land after F, or on `main` before B | ordering |
| D7 | DEBT | The `max-gap` segment of F1's finding is a writer constant | — |

**B1–B4 are for your ruling before any repair.**
- **B1 and B2 meet.** The remedy for B2 is debt 4, and B1 says where debt 4 can land.
- **Every remedy except one route of B1 is a registration change.** It touches SPEC/11 and
  `falsifiers.json`, and under amendment 1 item 3 it re-takes `readers.txt`.
- **Routes are listed under each finding.** None moves a pinned value, and none adds or drops
  a falsifier.

---

## 1. Does each reader read the field its row names?

### The falsifiers

All line numbers are `pave/drill_read.py` unless marked. `python -m pave.cli drill read` and
`drill verify` reach it through `pave/cli.py:1734-1737`.

| term | field named | the line that emits it | reads that field, or next to it |
|---|---|---|---|
| F1 | `decision` | `:127` `_at(document, "decision")`, printed at `:139` in the order at `:64` | **that field** |
| F1 | `finding` | `:140-144`: each `findings[]` item's `scenario`, `rule`, `after_cue`, `before_cue`, joined by `/` | **that field**. `gap_s` is not printed, which SPEC/11's line format pins |
| F2 | `owner.seat` | `:134` `_at(document, "owner", "seat")` | **that field** |
| F2 | `owner.oncall` | `:135` `_at(document, "owner", "oncall")` | **that field** |
| F2 | `fix_window_s` | `:133`, which calls `_window_seconds` at `:116-122` | **adjacent, by design.** The artifact has no `fix_window_s`. The reader computes `fix_by − ran_at` from `:118-119`, which is SPEC/11's pinned definition. Whole days are kept (`total_seconds`, `:122`), and an unparseable time prints `-`, which fires F2 rather than hiding it |
| F3 | `signature` | `verify_main` `:194-233`, calling `signature_holds` `:170-191`. It reads `alg` `:177`, `key_id` and `value` `:179`, and recomputes over the document minus `signature` `:182-185`. MISMATCH is printed at `:218-220` | **that field**, checked before the schema (`:213-221`, then `:223`) |
| F3 liveness | `signature` | `:221` prints `signature: OK` | that field. True by construction, as SPEC/11 says. **See B2** |
| F4 | `decision`, `finding` | same lines, on the control run | **that field** |
| F5 | `decision`, `finding` | same lines, on the fixed run. `findings: []` prints no `finding=` line | **that field** |

**Exit-2 doors that could stand in for F3's exit 1.** No key `:199-203`; unreadable, not an
object or a duplicate key `:204-209`; a signature check that raises `:213-217`. None of them is
reachable from F3's three `sed` edits on a good artifact with the right key.

### The validity rows

The git commands (`git show`, `git diff`, `git merge-base`) and `sha256sum` run no repository
code. They take `commit=` from `read`.

| row | field | the line that emits it | where the writer sets it | reads that field |
|---|---|---|---|---|
| all three | `tree_clean` | `:130`, shown as `true`/`false` by `:109-112` | `pave/drill.py:223-227`, `git status --porcelain` empty | **that field**, but see **B4** |
| all three | `caption_sha256` | `:136` `_at(document, "inputs", "caption_sha256")` | `drill.py:329` reads the bytes, `:343` hashes them | **that field** (`inputs.caption_sha256`, SPEC/11's artifact list) |
| all three | `commit`, for `git show`, `merge-base` | `:129` | `drill.py:215-220`, `git rev-parse HEAD` | **that field** |
| seeded | `mode` | `:128` | `drill.py:340`, `full` exactly when there is no `--delta` | **that field** |
| control, fixed | `mode`, `prior_sha256` | `:128`, `:137` top-level `prior_sha256` | `drill.py:253` reads the prior's bytes, `:283` hashes them | **that field** |
| control | `caption_sha256` equals seeded's; C ≠ S | `:136`; `:129` | as above | **that field** |

### What section 1 found

**Every reader reads the field its row names.** The one adjacent reading, `fix_window_s`, is
SPEC/11's own definition.

The gaps are in what the rows *gate on*, not in what the lines read: B3, B4 and D4 below.
`read` decides nothing (`:17-19`) and verifies nothing.

---

## 2. Does each checklist plant fire?

**How to read the table.**
- `drill_read` means `tests/test_drill_read.py`, `drill` means `tests/test_drill.py`,
  `pins` means `tests/test_drill_pins.py` and `seats` means `tests/test_twokey_seats.py`.
  Line numbers are the failing `assert`.
- **"witnesses" counts failing tests,** with parametrised cases collapsed.
- **As commits, the R, V and S plants would also trip the ordering test**, the confound of
  amendment 2 item 1: `READ_CODE` includes the readers and the schema. The K and F plants
  would not, because `pave/twokey.py`, `falsifiers.json` and SPEC/11 are not in `READ_CODE`.
  The ordering test is not listed below.

### R03–R10: `read`

| plant | the false state it plants | test and assertion that go red | witnesses |
|---|---|---|---|
| R03 | `tree_clean` printed as `True` | drill_read `test_read_prints_specs_lines_in_specs_order_for_a_no_go` `:98` (`tree_clean=true`) | 1 |
| R04 | an absent field printed as `None`, not `-` | drill_read `…specs_order_for_a_no_go` `:98` (`prior_sha256=-`); `test_read_prints_a_dash_for_every_absent_field_of_a_go` `:117`; `test_read_decides_nothing_it_prints_an_unsigned_invalid_document` `:140` | 3 |
| R05 | `fix_by` and `fix_window_s` swapped in the line order | drill_read `…specs_order_for_a_no_go` `:98`; `…dash_for_every_absent_field_of_a_go` `:117` | 2 |
| R06 | an unreadable document exits 0 | drill_read `test_read_exits_2_on_an_unreadable_file` `:147` (3 cases); `test_read_exits_2_on_a_missing_file_or_a_wrong_argument_count` `:151`; `test_a_duplicate_key_is_refused_by_both_readers` `:271`; `test_what_cannot_be_read_one_way_exits_2_and_never_prints_ok` `:290` (3 cases) | 4 |
| R07 | `owner.oncall` read from `owner.seat` | drill_read `…specs_order_for_a_no_go` `:98` | 1 |
| R08 | `caption_sha256` read from the top level, not `inputs` | drill_read `…specs_order_for_a_no_go` `:98`; `…dash_for_every_absent_field_of_a_go` `:117` | 2 |
| R09 | a lone surrogate passes the pre-print encode (`surrogatepass`) | **NONE.** See D1 | 0 |
| R10 | duplicate keys accepted, last value wins | drill_read `test_a_duplicate_key_is_refused_by_both_readers` `:270`. `verify` reads the real `NO-GO`, prints OK and exits 0, where `(2, [])` is expected | 1 |

### V01–V11: `verify`

| plant | the false state it plants | test and assertion that go red | witnesses |
|---|---|---|---|
| V01 | the schema checked before the signature | drill_read `test_the_signature_is_checked_before_the_schema` `:189`; `test_a_missing_signature_is_a_mismatch_not_unreadable` `:221`; `test_the_algorithm_the_key_id_and_the_value_must_all_hold` `:217` (the `alg`, missing-`value` and not-an-object cases, each schema-invalid); `test_what_cannot_be_read_one_way…` `:289` (surrogate: `schema: INVALID` is printed) | 4 |
| V02 | the value never compared | drill_read `test_f3s_three_edits_each_exit_1_with_signature_mismatch` `:180` (3 cases); `…must_all_hold` `:217` (value); `test_the_signature_is_checked_before_the_schema` `:189`; `test_verify_runs_with_the_writer_made_unimportable` `:402` | 4 |
| V03 | the key id never compared | drill_read `…must_all_hold` `:217` (key_id case only; another key also changes the value) | 1 |
| V04 | the algorithm not checked | drill_read `…must_all_hold` `:217` (alg case only) | 1 |
| V05 | the reader's canonical form drops `decision` | drill_read `test_verify_exits_0_on_a_well_formed_artifact_signature_first` `:162`; `test_what_the_writer_writes_the_readers_verify_and_print` `:348`; `…writer_made_unimportable` `:402`; and every other OK case. **F3's copies would still all read MISMATCH, so only F3's liveness check sees this in PR 3** (B2) | ≥5 |
| V06 | a MISMATCH exits 0 | drill_read `…f3s_three_edits…` `:180`; `…checked_before_the_schema` `:189`; `…must_all_hold` `:217`; `…missing_signature…` `:221`; `test_another_key_is_a_mismatch` `:227` | 5 |
| V07 | no key, or a short key, no longer refused | drill_read `test_no_key_exits_2_before_anything_is_read` `:234` (3 cases: an empty-key HMAC reads MISMATCH, exit 1); `test_the_key_floor_is_32_bytes_not_32_characters` `:311` | 2 |
| V08 | `schema: INVALID` exits 0 | drill_read `…checked_before_the_schema` `:193` | 1 |
| V09 | a signature check that raises is treated as holding | drill_read `test_a_signature_check_that_raises_exits_2_and_never_prints_ok` `:302`; `test_what_cannot_be_read_one_way…` `:289` (surrogate) | 2 |
| V10 | the reader's canonical form escapes non-ASCII | drill_read `test_a_non_ascii_value_is_verified_under_the_unescaped_canonical_form` `:258` | 1 |
| V11 | the key floor counts characters, not bytes | drill_read `test_the_key_floor_is_32_bytes_not_32_characters` `:309` (16 `é` are 16 characters, so refused) | 1 |

### S01–S06: the schema

| plant | the false state it plants | test and assertion that go red | witnesses |
|---|---|---|---|
| S01 | top-level `additionalProperties` opened | drill `test_the_artifact_is_validated_before_anything_is_written` (`pytest.raises` at `:116`); `test_the_schema_refuses_an_undeclared_key_at_every_level` `:257`; `test_a_delta_refuses_a_signed_prior_that_does_not_conform` (`:116`); drill_read `…checked_before_the_schema` `:193` | 4 |
| S02 | an `enum` over `owner.oncall` holding the pinned value | drill `test_the_schema_holds_no_claim_value` `:534` (enum list) and `:539` (`webhook:`). Every synthetic NO-GO is also refused, e.g. `test_a_gap_above_the_threshold…` raises `Refused` | many |
| S03 | `signature` no longer required | **NONE.** See D2 | 0 |
| S04 | `if`/`then` tying `decision` to `owner` and `fix_by` | drill `test_the_schema_holds_no_claim_value` `:513` (forbidden `if`, `then`); `:534` would also fail, but `:513` fails first | 1 |
| S05 | `owner`'s `additionalProperties` opened | drill `test_the_schema_refuses_an_undeclared_key_at_every_level` `:257` (the second plant) | 1 |
| S06 | `maxItems: 1` on `findings` | drill `test_the_schema_holds_no_claim_value` `:533`; `test_two_gaps_are_two_findings_in_file_order` (raises `Refused` before `:410`) | 2 |

### K01–K06: the drill rule

Every K plant is caught by `seats` `test_m11s_drill_instrument_collects_its_seats`, at
`_blocked_for`'s seat-set equality (`tests/test_twokey_seats.py:714`), which requires exactly
`{ai-quality, platform-eng, security}`.

| plant | the false state it plants | the pinned paths that fail `:714` | witnesses |
|---|---|---|---|
| K01 | `milestones/M11/` dropped from the rule | all four `milestones/M11/…` entries | 1 test, 4 paths |
| K02 | the package-shadow branch `(\.py$\|/)` narrowed to `\.py$` | `pave/drill/__init__.py`, `pave/drill_read/__init__.py`, `pave/drill/core.py` | 1 test, 3 paths |
| K03 | `platform-eng` dropped | all 13 | 1 test, 13 paths |
| K04 | `security` dropped | all 13 | 1 test, 13 paths |
| K05 | the package branch narrowed to `/__init__\.py$` | `pave/drill/core.py` | 1 test, 1 path |
| K06 | `milestones/M11/` narrowed to `(pre-registration\|runs)/` | `milestones/M11/README.md` | 1 test, 1 path |

`.github/CODEOWNERS` names no drill path, so `tests/test_contracts.py:703` is not a witness.

### F01–F08: the registration

| plant | the false state it plants | test and assertion that go red | witnesses |
|---|---|---|---|
| F01 | F3 expects exit 2 | pins `test_the_fields_a_reading_uses_are_pinned` `:163` | 1 |
| F02 | the owner moved in `falsifiers.json` (twice) and in the scenario together | pins `test_every_pin_is_written_in_spec_11s_pinned_section` `:104`. `:118` and `:159` move with it and stay green | 1 |
| F03 | F5 expects NO-GO | pins `test_the_fields_a_reading_uses_are_pinned` `:169` | 1 |
| F04 | the fixture's cue length 5000 → 4000 ms | pins `test_every_pin_is_written_in_spec_11s_pinned_section` `:104`; `test_the_clean_fixture_had_specs_shape_at_the_commit_that_added_it` `:213` | 2 |
| F05 | a validity row no longer SPEC/11's verbatim | pins `test_every_validity_row_is_spec_11s_row_verbatim` `:141` | 1 |
| F06 | F4's runs moved to the fixed run | pins `test_the_fields_a_reading_uses_are_pinned` `:155` | 1 |
| F07 | amendment 1's caption-bytes clause removed from SPEC/11 and the registration together | pins `test_every_validity_row_is_spec_11s_row_verbatim` `:142`. `:141` moves with it and stays green | 1 |
| F08 | F3's liveness exit 0 → 1 | pins `test_the_fields_a_reading_uses_are_pinned` `:164` | 1 |

### What section 2 found

- **39 plants read: 37 fire, and 2 have no witness (R09, S03).** Neither reaches a PR 3
  reading: D1 and D2.
- **Single witnesses:** R03, R07, R10, V03, V04, V08, V10, V11, S04, S05, K05, K06 and
  F01–F03, F05–F08. One deleted assertion un-witnesses each. That is recorded here and is not
  a finding.
- **An edit that moves SPEC/11, `falsifiers.json` and the scenario together passes every
  test.** The pins test says so of itself (`tests/test_drill_pins.py:9-10`). Only the two-key
  rules stand in front of that edit.

---

## 3. Has the code as built made any term true by construction?

| examined | result |
|---|---|
| a schema `const` or `enum` on a claim value | **No.** The only enums are `mode` `:30`, `decision` `:44` and `signature.alg` `:89`. The `decision` enum makes neither `GO` nor `NO-GO` true; it only bars a third value, which the writer never emits (`drill.py:295`). No `const`, `if`, `default` or limit under `findings`/`owner` (held by `test_the_schema_holds_no_claim_value`) |
| a writer default for the owner, window or threshold | **No.** Owner `drill.py:145-146` (`_text` raises); window `:90-95`; threshold `:131-133`; caption source `:97-103`. The threshold is rounded to the millisecond (`:144`), which is exact for 4.0 against millisecond cue times. **One constant in effect:** `:135-136` refuses every rule but `max-gap` (D7) |
| a reader that imports from, or shares with, the writer | **Not in the module.** `drill_read.py:47-55` imports stdlib and `jsonschema`, and no top-level name is shared. **Shared inputs:** (a) the schema file, which no falsifier reads a line of; (b) the key variable (B2); (c) the process: `python -m pave.cli` imports `pave.drill` at `cli.py:45` before it dispatches (D5) |
| F2's expected values against the writer's input | **Not by construction, but narrow.** `tests/test_drill_pins.py:111-120` holds the scenario equal to the pins, and the writer copies the scenario. So F2 in PR 3 can fire only on a copy error in the writer (W12 and W13, both CAUGHT) or a scenario on disk that differs from the commit (B4) |
| F3's liveness check | **True by construction**, as SPEC/11 says. Its failure has no registered meaning, so **F3 passes on any refusal** (B2) |
| checks that pass on any refusal | **F3**, B2. **Tests:** 18 `_refused` calls with no `match` (D3), plus the substring matches behind D8–D11 |

---

## The findings

### B1 — BLOCKING: three carried debts fall inside the seeded run's diff window

**What is registered.**
- **The seeded validity row:** `git diff --name-only B S` is exactly the fixture, where *B* is
  PR 3's branch point on `main` (SPEC/11:104).
- **ADR-080 amendment 1, item 7, carries three debts** whose triggers sit between B and S:

| debt | its trigger, as worded |
|---|---|
| 4 | a failed F3 liveness check has no registered meaning. Trigger: *"PR 3, before its seeded run: say it, or record that it is unsaid"* |
| 5 | the clean fixture's bytes are pinned by no reader. Trigger: *"PR 3's seed commit"* |
| 6 | *"commit the full sha256 of the run key **in the seed commit**, before the seeded run"* |

**The false state.** Every file committed on PR 3's branch before S is in B..S.
- Debt 6 done as written puts a second path in the seed commit.
- Debt 5 paid at its trigger does the same.
- Debt 4 "said" in a commit before the seeded run does the same.

Each makes the seeded run INVALID, the claim NOT MEASURED and M11 RED, with no re-run. That is
a **false failure** of the seeded validity row, caused by obeying the debt table.

**Where they can land without it:** on `main` before B. The cap is full (decision 5; amendment
2 item 4), so that means **this PR**.

**Routes, for ruling:**
1. **Debt 6 lands here.** The operator generates the run key now and holds it. This PR commits
   only its sha256, under `milestones/M11/`, on the drill rule's three keys. No pinned value,
   falsifier or reader moves. The sha256 of a 48-byte random key discloses nothing usable.
2. **Debts 4 and 5 land here, as registration changes.**
   - Debt 4 is B2's remedy.
   - Debt 5 would add the clean fixture's sha256 as a pin, or as a clause in the fixed row.
   - Both touch SPEC/11 and `falsifiers.json`, and re-take `readers.txt`.
3. **Re-word the triggers of debts 4–6** to "after F, or not at all", and accept what that
   leaves: B2 stays open, and the key is committed after the readings it protects.

### B2 — BLOCKING: F3 passes on any refusal

**The false state.** `verify` is run on the three copies under a key other than the writer's.
Every copy prints `signature: MISMATCH` and exits 1, because the value no longer matches
(`drill_read.py:185-191`), and F3 reads three refusals and does not fire. The signature
refused the copies because it could not verify anything, not because they were edited.

**The one check that tells these apart is F3's liveness** (`verify` on the committed R1). It
would also print MISMATCH. But SPEC/11 says only that it *must* exit 0 first, and the
registration records `"on_failure": "not registered"` (`falsifiers.json:136`). That is debt 4.

**How it happens by accident.** SPEC/11's demo sets the key with
`export BEACONPAVE_DRILL_KEY="$(cat milestones/M11/runs/drill-key.txt)"`.
- `$(…)` strips trailing newlines but not a `\r`.
- A key file saved with CRLF, or with a trailing space, is a different key.
- `verify` prints no `key_id`, so the wrong-key MISMATCH and the edited-copy MISMATCH are the
  same line.

V05, a verifier that drops a field from its canonical form, shows the same way in PR 3: all
three copies MISMATCH, and only liveness fails.

**Routes, for ruling.** Each is a registration change, and each must land before B (B1):
- **(a)** a failed liveness check makes F3's reading INVALID, and no copy is read;
- **(b)** as (a), and PR 3 also records the key's `key_id` against the committed sha256 of the
  key from debt 6.

No reader's semantics move under either route.

### B3 — BLOCKING: the control and fixed artifacts are read unverified

**What is read without a check.** F2 on the control run, F4, F5, and the control and fixed
validity rows all read `drill read` output. `read` does not verify (`drill_read.py:17-19`).
SPEC/11 lists `verify` on those two artifacts *beside the claim, exit code recorded*
(SPEC/11:110), with no registered meaning.

**The false state.** Before its reading, the fixed artifact's `"decision": "NO-GO"` is edited to
`"GO"` and its `findings` emptied, or the control's owner is edited to the pin.
- F5, or F2 on the control run, reads the edit and passes. That is a **false pass**.
- No validity row sees it. `prior_sha256` pins R1's bytes, not the artifact's own. A changed
  `decision` moves neither `caption_sha256` nor `commit`.

This is F3's false state, a hand edit, applied to the two artifacts that carry the claim's
second half. The detector already exists: `verify` exits 1 on each.

**Route, for ruling:** one clause in the control and fixed validity rows, *`drill verify`
exits 0 printing `signature: OK`*. The reader exists today and runs in PR 3 already, and no
pinned value moves. It is a registration change that re-takes `readers.txt`.

### B4 — BLOCKING: `tree_clean` is porcelain, and skip-worktree still hides the writer and the scenario

**Why the row does not see it.** `tree_clean` is `git status --porcelain` being empty
(`pave/drill.py:223-227`). Amendment 1 item 1 measured that `--skip-worktree` defeats it, and
added a row for the caption bytes only.
- **The writer** reads its owner, window and threshold from the scenario on disk
  (`drill.py:124-126`).
- **It runs `pave/drill.py` as found on disk.**
- **The artifact records a hash of neither.**

**The false states.**
- **Writer hidden (a false pass).** `pave/drill.py` marked skip-worktree and edited, for
  example to write W18's "a delta always writes GO" or its opposite. The runs read
  `tree_clean=true`, every validity row holds, and F1, F4 and F5 read whatever the edit
  wrote.
- **Scenario hidden (false failures only).** A hidden owner or threshold edit can only fire F1,
  F2 or F4. The fixed fixture has no gap at any threshold, so F5 is unaffected.

**Grading.** Both need deliberate git plumbing. They are graded BLOCKING by amendment 1's own
ruling, which took the same mechanism as blocking for the fixture. Grading them DEBT is yours
to rule, with that precedent named.

**Route, for ruling:** a validity clause that `git ls-files -v` shows no skip-worktree (`S`)
and no assume-unchanged (lowercase) entry. It is captured in the transcript immediately before
each of the three runs. The command exists today. It is a registration change.

### D1 — DEBT: R09 has no witness

- **The door:** `drill_read.py:156` encodes each line before anything is printed, so a lone
  surrogate is refused whole.
- **The shadow:** with the plant in place, the print loop's `except (UnicodeEncodeError,
  OSError)` (`:164-166`) still exits 2. pytest's `CaptureIO` encodes strictly, and the
  surrogate case sits on the first line, `decision` (`tests/test_drill_read.py:276`).
- **The test cannot tell the doors apart:** `:290` asserts only the exit code.
- **The difference, on a console whose stdout tolerates surrogates:** earlier lines print
  before an exit 2.
- **No PR 3 artifact can carry a surrogate.** The fixture is decoded strictly (`drill.py:330`),
  and the scenario's strings are pinned.
- **Owner:** AI Quality + Platform Engineering. **Trigger:** the next PR that edits
  `pave/drill_read.py`.

### D2 — DEBT: S03 has no witness, and the requirement is inert

`required: signature` (`go-no-go.schema.json:18`) is never the refusing door:
- `verify` checks the signature first (`drill_read.py:213-220`);
- `load_prior` does too (`drill.py:259-266`);
- the writer signs before it validates (`drill.py:344-347`).

**Owner:** AI Quality + Platform Engineering. **Trigger:** the next PR that edits
`quality/drill/`.

### D3 — DEBT: writer refusal tests that accept any refusal, and a fifth shadowed door

**Tests that accept any refusal.**
- **No `match`:** `test_a_missing_claim_value_writes_nothing` (10 cases,
  `tests/test_drill.py:192-199`), `test_a_claim_value_of_the_wrong_shape_writes_nothing`
  (7, `:207-209`) and `test_a_delta_refuses_a_signed_prior_whose_tier_is_a_boolean` (`:392`).
- **A substring more than one door prints:** `key` `:225`, `already exists` `:233`, `no id`
  `:172`, which are D8, D9 and D11, and `scenario` `:399`.

**The fifth shadowed door, by reading.** W43 (unrun) removes the prior's tier type check
(`drill.py:274`). The schema's `"tier": {"type": "integer"}` refuses `true` first, at `:269-273`,
because `jsonschema` does not count a boolean as an integer. `:392` has no `match`, so W43
would read SILENT. That is D8–D11's shape.

**Effect on the arc:** none. Every prior in the arc is writer output.

**Owner:** AI Quality + Platform Engineering. **Trigger:** the next PR that edits
`pave/drill.py`, the same as D8–D11.

### D4 — DEBT: the claim's event and tier are read by no reader

- **Neither is printed:** `read` prints neither `event` nor `tier` (`drill_read.py:64`).
- **What holds them:** the scenario carries one event and one tier
  (`drill/scenarios/caption-check.json:10-17`), so any other exits 2 (`drill.py:93`, `:101`).
- **What would expose the gap:** a second tier added to the scenario. F2's `fix_window_s` then
  separates tiers only if their windows differ.

**Owner:** AI Quality. **Trigger:** the next PR that edits `drill/scenarios/`.

### D5 — DEBT: the command every falsifier names loads the writer

- **The module holds constraint 6:** `pave/drill_read.py` imports nothing from the writer
  (`tests/test_drill_read.py:366`, `:383`).
- **The command does not:** `python -m pave.cli` imports `pave.drill` at `pave/cli.py:45`,
  before it dispatches.
- **At `6a5fbb7` this makes no term true.** It is amendment 1 debt 1's route: the dispatch is
  on no rule.

**Owner:** Platform Engineering. **Trigger:** debt 1's.

### D6 — DEBT: PR 3's close work must land after F

**The rows bound each diff window:**
- B..S is exactly the fixture;
- S..C lies under `milestones/M11/`;
- C..F, minus `milestones/M11/`, is exactly the fixture.

**What must land after F, or on `main` before B:** the `brand_tone` payment (`labels.json`),
the Act 4 recording (`docs/governance/recordings.json`), `README.md` row 11, and any ADR or
SPEC edit. Anything else makes one of the three runs INVALID.

SPEC/11's plan puts the close after the arc. The obligations table gives `brand_tone` no order.

**Owner:** PM. **Trigger:** PR 3's first commit.

### D7 — DEBT: the `max-gap` segment is a writer constant

- **The constant:** `drill.py:135-136` refuses every rule but `max-gap`, so every written
  finding reads `max-gap`.
- **What it removes:** F1's `rule` segment cannot fire on its own.
- **What still fires:** F1 on `decision` and on the cue ids.
- **Where the `caption-check` segment comes from:** the scenario file, held by
  `tests/test_drill_pins.py:114`.

**Owner:** AI Quality. **Trigger:** a second rule.

## What this review does not show

- **No test was run and no plant was applied.** Each "goes red" is a reading. The audit's
  lesson (amendment 2 item 1) is that a reading is weaker than a run: a door shadowed in a way
  this reviewer did not trace reads as caught here.
- **Eighteen unrun plants were not on the checklist and were not worked:** I1, I2, C01, C02,
  P01–P04, T01, T02, W40, W41 and W43–W48. W43 appears only in D3.
- **Nothing here is a seat's disposition (G6).**

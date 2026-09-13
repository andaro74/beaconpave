# M10 PR 3, part A — deletability audit of the surface writer's tests and the Playwright runner

**Audited:** `tests/test_surfaces_emit.py` and `surfaces/web-player/tests/player_smoke.py`,
at check granularity, at `main` 691acfa (M10 PR 2 merged). **Every plant ran through the CI
gate** (`quality-gate`, step `L0 unit + L1 contract`, `python -m pave.cli check` on
ubuntu-latest, Python 3.12) on exhibit **#155**, closed unmerged. No local Windows run is
a reading here: the gate's pytest echo at `pave/cli.py:1388` can exit red without deciding
(#152).

**Method.** Each plant is one commit, a child of 691acfa built from git objects, changing
exactly one door. Every anchor was asserted against the committed blob before the commit
was built (a missed anchor refuses to build), and every planted `.py` blob passed `ruff`
before it was pushed, so no plant could go red on lint. Each plant that went red as planted
ran a second time with `tests/test_surfaces_emit.py` also deleted. The head of
`exhibit-m10-pr3-audit-ci` was force-pushed to each commit in turn, and all 35 commits
registered a run. **The run IDs are the durable citation.** The commits are reachable from
no ref after the force-pushes, so the SHAs below are plain text.

**Control:** no plant, commit 2f8b1c2, run 34764760657: **4898 passed, 9 skipped,
`check: PASS`.**

**Reading:**
- **sole witness:** red as planted, and green with the test file deleted.
- **caught elsewhere:** red in both.
- **SILENT:** green as planted.

For every SILENT writer plant, **potency** was shown separately. It is not a gate reading:
main's `emit.py` and the planted one were each fed the one raw output that discriminates
the door. A SILENT row therefore cannot be an inert plant.

Shorthand for the failing tests, all in `tests/test_surfaces_emit.py`:
- `outcome[...]` is `test_each_outcome_is_written_and_the_gate_decides_it_by_the_one_contract[...]`
- `nothing[...]` is `test_a_runner_that_wrote_nothing_is_infra_never_pass_or_fail[...]`
- `names` is `test_a_fail_names_what_failed`

The case indices are `CASES` at `tests/test_surfaces_emit.py:54-66`, counted from 0.

## The writer's checks: plants in `surfaces/web-player/emit.py`

| plant | door (`emit.py` at 691acfa) | as planted: commit, run, count, failing | test file also deleted: commit, run, count | reading |
|---|---|---|---|---|
| W01 | `:75-76` Playwright `error` → INFRA, deleted | 96b2c96, 34764770620, 4898 passed, PASS | not run | **SILENT.** Potency: `error` set with one held check: main INFRA, plant **PASS** |
| W02 | `:77-78` Playwright no checks → INFRA, deleted | 796d221, 34764778566, 1 failed: `outcome[playwright-INFRA-3]` | dea6754, 34764949827, 4881 passed, PASS | sole witness |
| W03 | `:82` a check fails when `ok is not True` → only when `ok is False` | 9e2080e, 34764785595, 4898 passed, PASS | not run | **SILENT.** Potency: a check with no `ok`: main FAIL, plant **PASS** |
| W04 | `:84` Playwright verdict always PASS | f7312e2, 34764793444, 1 failed: `outcome[playwright-FAIL-1]` | 0159da7, 34764956246, 4881 passed, PASS | sole witness |
| W05 | `:86` `FAILED: <name>` notes removed | 6d96a41, 34764800762, 1 failed: `names` | 073f26c, 34764985808, 4881 passed, PASS | sole witness |
| W06 | `:99-100` k6 no metrics → INFRA, deleted | f147796, 34764807295, 4898 passed, PASS | not run | **SILENT, equivalent on `verdict`.** Potency: `metrics: {}`: INFRA both, notes differ only. `:105-106` refuses the same input |
| W07 | `:105-106` k6 no response → INFRA, deleted | a07318a, 34764813939, 1 failed: `outcome[k6-INFRA-7]` | 42d6f8e, 34764992955, 4881 passed, PASS | sole witness |
| W08 | `:105` INFRA rule reverted to *any unreached request* | 008ab68, 34764822310, 1 failed: `outcome[k6-FAIL-6]` | 3b0537c, 34764998924, 4881 passed, PASS | sole witness, **by one case**, the 905-unreached case |
| W09 | `:105` INFRA rule narrowed to *no response AND some unreached* | b128b2e, 34764830460, 4898 passed, PASS | not run | **SILENT.** Potency: a summary with thresholds held and neither counter (no request made): main INFRA, plant **PASS** |
| W10 | `:109-110` k6 no thresholds → INFRA, deleted | d2eb9ae, 34764838984, 1 failed: `outcome[k6-INFRA-8]` | 1e2178f, 34765004914, 4881 passed, PASS | sole witness |
| W11 | `:93` a threshold holds when `ok is True` → unless `ok is False` | 793d803, 34764844805, 4898 passed, PASS | not run | **SILENT.** Potency: a threshold outcome `{}`: main FAIL, plant **PASS** |
| W12 | `:129` k6 verdict always PASS | 54da16c, 34764850483, 2 failed: `outcome[k6-FAIL-5]`, `outcome[k6-FAIL-6]` | 891da1d, 34765012165, 4881 passed, PASS | sole witness |
| W13 | `:130` `threshold breached:` notes removed | eaee78d, 34764857706, 1 failed: `names` | 5a83577, 34765018938, 4881 passed, PASS | sole witness |
| W14 | `:60` missing raw output returned as `{}` with no problem | a57de02, 34764863213, 4898 passed, PASS | not run | **SILENT, equivalent on `verdict`.** Potency: missing file: INFRA both, notes differ only. `:77-78` and `:99-100` refuse it next |
| W15 | `:61` `json.JSONDecodeError` no longer caught | 0aa1f69, 34764871248, 4898 passed, PASS | not run | **SILENT.** Potency: unparseable JSON: main INFRA, plant **raises**. No case writes unparseable raw output |
| W16 | `:69` `fail_closed=False` | c30a732, 34764879333, 7 failed: `nothing[k6]`, `nothing[playwright]`, `outcome[k6-FAIL-5]`, `outcome[k6-FAIL-6]`, `outcome[k6-PASS-4]`, `outcome[playwright-FAIL-1]`, `outcome[playwright-PASS-0]` | c0fe08c, 34765026451, 4881 passed, PASS | sole witness |
| W17 | `:67-70` an undeclared key added after `verdict.build` validated | 6fdb55a, 34764888015, 5 failed: `outcome[k6-FAIL-5]`, `outcome[k6-FAIL-6]`, `outcome[k6-PASS-4]`, `outcome[playwright-FAIL-1]`, `outcome[playwright-PASS-0]` | c36d828, 34765033764, 4881 passed, PASS | sole witness |

**W16 and W17 left all four INFRA cases green**, `outcome[playwright-INFRA-2]`,
`[playwright-INFRA-3]`, `[k6-INFRA-7]` and `[k6-INFRA-8]`. The reason is
`tests/test_surfaces_emit.py:30`, which maps INFRA to `EXIT_CONTRACT`. A correct INFRA record and a record the gate
refuses as outside the envelope, or as `fail_closed: false`, both exit 2. So on INFRA
outcomes the gate assertion at `:77` cannot tell the writer's INFRA from a writer that has
left the contract.

## What the tests' fixtures stand in for: renames at the runner

| plant | door | as planted: commit, run, count | reading |
|---|---|---|---|
| R01 | `loadtest/smoke.js:20`, the counter `responses_received` renamed | 213d573, 34764894477, 4898 passed, PASS | **SILENT.** Potency: the committed `pre-registration/clean/k6-summary.json` with the metric renamed, read by main's writer: PASS → **INFRA** |
| R02 | `player_smoke.py:38-42`, `:50`, each check's `ok` written as `held` | 366a14c, 34764900975, 4898 passed, PASS | **SILENT.** Potency: the committed `pre-registration/clean/playwright-raw.json` with `ok` renamed: PASS → **FAIL** on all three checks |

`tests/test_surfaces_emit.py:33-48` builds raw outputs in the shape `emit.py` reads, not in
the shape the runners write. Nothing in the hermetic suite ties the two together.

## The Playwright runner's checks: plants in `surfaces/web-player/tests/player_smoke.py`

| plant | door (`player_smoke.py` at 691acfa) | as planted: commit, run, count | reading |
|---|---|---|---|
| S01 | `:38-39` *responds 200* weakened to `status < 500` | 9ea925c, 34764907413, 4898 passed, PASS | **SILENT** |
| S02 | `:40` *title names the player* weakened to `"" in page.title()` | 7b9ec3f, 34764914943, 4898 passed, PASS | **SILENT** |
| S03 | `:41-42` *heading visible* weakened to `count() >= 0` | f251a25, 34764923244, 4898 passed, PASS | **SILENT** |
| S04 | `:45-47` an unreachable page written as a failed check with no `error`, so FAIL instead of INFRA | a7d1da8, 34764936019, 4898 passed, PASS | **SILENT** |
| S05 | the file deleted | 2fade1e, 34764943430, **4895** passed, PASS | **SILENT** |

**Potency for S01–S04 was not measured.** No browser was run in this audit. The readings
are gate readings only.

**Nothing in CI executes `player_smoke.py`.** `quality-gate.yml:40` installs `.[dev]`, which
has no Playwright. The file is outside `testpaths`, and ADR-079 decision 5 cuts the surface
runners from the required workflow. The three tests S05 removed are
`test_line_endings`, `test_no_account_identifiers` (account id) and
`test_no_account_identifiers` (qualified ARN), each parametrized over every tracked file.
None reads a check. The same scans, plus `test_hermeticity`'s two, are the five tests
beyond the file's own twelve that each deletion variant removed (4898 − 4881 = 17).

## Count

Twenty-four plants and one control, ten deletion variants, thirty-five runs:
- **Sole witness: 10.** W02, W04, W05, W07, W08, W10, W12, W13, W16, W17.
- **Caught elsewhere: 0.** No `emit.py` door is held by any test outside
  `tests/test_surfaces_emit.py`.
- **SILENT: 14.** Seven writer doors: W01, W03, W06, W09, W11, W14, W15, of which W06 and
  W14 are equivalent on `verdict`. Two runner-shape renames: R01, R02. All five of
  `player_smoke.py`'s plants: S01–S05.

## Debt rows opened by this audit

Each is a SILENT plant, opened as a debt. **None is paid by a test written here.** A test
written to its own data would repeat the defect the audit exists to find.

| # | silent plant | what goes unwitnessed | owner | trigger |
|---|---|---|---|---|
| A1 | W01 | Playwright `error` → INFRA when checks are also recorded | AI Quality + Platform Engineering | the next PR that edits `surfaces/web-player/emit.py` |
| A2 | W03 | a check whose `ok` is anything but `true` is a failure | AI Quality + Platform Engineering | the same |
| A3 | W06 | k6 no-metrics → INFRA is dominated by the no-response branch; the branch is equivalent on `verdict` | Platform Engineering | the same |
| A4 | W09 | a summary in which no request was made at all is INFRA, not decided by thresholds | AI Quality + Platform Engineering | the same |
| A5 | W11 | a threshold outcome without `ok: true` is breached | AI Quality + Platform Engineering | the same |
| A6 | W14 | the missing-output branch is equivalent on `verdict`; its INFRA note is unwitnessed | Platform Engineering | the same |
| A7 | W15 | unparseable raw output is INFRA rather than an uncaught exception | Platform Engineering | the same |
| A8 | R01 | the k6 metric names the writer reads match what `loadtest/smoke.js` emits | AI Quality + Platform Engineering | the next PR that edits `loadtest/smoke.js` or `emit.py` |
| A9 | R02 | the Playwright raw shape the writer reads matches what `player_smoke.py` writes | AI Quality + Platform Engineering | the next PR that edits `player_smoke.py` or `emit.py` |
| A10 | S01–S05 | `player_smoke.py`'s three checks, its unreachable-is-an-error path, and the file itself are witnessed by nothing that runs in CI | AI Quality (the checks) + Platform Engineering (the runner) | ADR-079 decision 5's at-scale line, a surfaces lane in the required workflow, or the next PR that edits `player_smoke.py` |
| A11 | W16, W17, observed | on the four INFRA cases the gate assertion cannot tell INFRA from a writer that has left the contract, because both exit 2 | AI Quality | the next PR that edits `tests/test_surfaces_emit.py` |

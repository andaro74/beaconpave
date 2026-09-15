# 12 — the ledger: every obligation reaches a terminal state, and no claim

**Status: WRITTEN at M12 PR 1, 2026-09-14, before any code.** Owned by the PM seat. Tag
`m12`; one branch per PR, none named `m12`. Branch point: `main` at `4979054` (tag `m11`).

**Deliberately short.** Every rule below is derived in **ADR-081**. This file states the
milestone. **It carries no claim**, of the twelve or of its own. Across the whole milestone:
zero model calls, zero AWS calls, no deploy, no drill run and no eval run.

## Why

Row 12 is the last row of the progression table (`README.md:53`). It carried claims 7, 8 and
12, the self-heal classifier, the repair PR flow, the curation panel and Act 5 (`BUILD.md:31`).

**The feasibility check** (`milestones/M12/feasibility.md`) found claim 12 pre-registerable
only on three conditions. **The operator refused the first, the rollback cut.** So claim 12
has no pre-registerable wording, and it is UNSCHEDULED with claims 7 and 8 (ADR-081 decisions
1–3).

**What the last row must do anyway** (check §5):
- `tests/test_calibration_owe.py:86` and `tests/test_demo_recordings.py:182` assert that the
  progression parser returns `{True, False}` over the live table. Both go red the moment row
  12 reads ✅.
- No obligation can be re-deferred. `milestone_is_closed` (`tests/milestone_status.py`) raises
  for a milestone the table does not list, and no row follows M12.
- `brand_tone` (`labels.json:355`, `re_deferred_to: M12`), Act 4 (`recordings.json`,
  `owed_by: M12`) and Act 5 (`owed_by: M12`) name M12. For the first two, the only reason is
  that a test needed a listed row (M11 debt 21).

## Purpose

1. **The obligation mechanism's terminal state.** Every machine-read obligation is PAID,
   RETIRED or UNSCHEDULED, and none names a milestone (ADR-081 decision 5).
2. **`brand_tone` retired**, by AI Quality with Security, with ADR-026 amendment 7 in the same
   diff. This is amendment 6's second route, at zero model calls.
3. **Acts 4 and 5 resolved.** Act 4 is recorded from its committed script. Act 5 is retired
   (ADR-081 decision 6).
4. **The final twelve-claims table**, and the journal's single debt register, which is the
   ledger this milestone is named for.

### The three states, pinned

| state | must carry | moved into it by |
|---|---|---|
| **PAID** | the committed path that discharges it | the registry's existing two keys |
| **RETIRED** | the ADR or amendment that retires it, in the same diff; the two seats that disposed it, both enforceable in `pave/twokey.py` | the registry's existing two keys |
| **UNSCHEDULED** | the owning seats and a written trigger. It names no milestone, and it is not a pass | the registry's existing two keys |

- The registries are `quality/judge/calibration/labels.json`'s `owed` (AI Quality + Security)
  and `docs/governance/recordings.json`'s `acts` (Platform Engineering + AI Quality).
- `milestone_is_closed` keeps raising for an unlisted milestone. **No row 13 is added.**
- The ratchet (`deferred_from`, and the guards that count closed milestones) keeps counting
  every closed milestone an obligation passed, M12 included.
- The field names are PR 2's, read against this table.

## What it builds

- the three states, read by `tests/milestone_status.py`, `tests/test_calibration_owe.py` and
  `tests/test_demo_recordings.py`;
- the two parser guards, moved onto a synthetic table (M10 row 24);
- a two-key rule over `tests/milestone_status.py` and `tests/test_calibration_owe.py`, and
  `tests/test_drill*.py` added to the drill rule (M11 debt 2);
- `brand_tone` RETIRED, and ADR-026 amendment 7;
- the stale *"lanes arrive at M10"* sentence that M10 row 26 cites as `pave/cli.py:880`, now at
  `:888`;
- Act 4's recording;
- Act 5 RETIRED, in `recordings.json` and in `docs/governance/demo-script.md` (M10 row 23);
- the journal and its ledger, the final claims table, and row 12.

## What it does not build

- **any leakage counter**, over git history, gate runs or a committed snapshot;
- **the drift-vs-defect classifier**, the repair PR flow, or `pave selfheal` beyond its stub;
- **the curation panel**, or any dashboard;
- **a seed commit or a revert commit**, on any branch;
- a claim, a falsifier or a pre-registration;
- a row 13, or any obligation deferred to a milestone;
- a deploy, a model or AWS call, a drill run or an eval run;
- a wider draw or a label change for `brand_tone`, which is retired, not paid;
- an edit to a closed milestone's journal, spec or row. `README.md:751-752` and `BUILD.md:29`
  still say *"claim 12 stays at M12"*. That was true when M10 wrote it, and those lines stay
  unedited.

## The plan, and its two-key seats

The PR plan is the check's Q5 (headed §6), cut to three PRs with no spare, and without the
leakage instrument.

| PR | contents | two-key |
|---|---|---|
| **1** (this PR) | SPEC/12; ADR-081; claims 7, 8 and 12 UNSCHEDULED in `README.md`'s claims table; row 12 and `BUILD.md:31` re-titled `m12-ledger`; `README.md:983` given `--out`; both index rows; the check committed as `milestones/M12/feasibility.md`. No code and no test | **none.** `twokey.triggered` over every changed path returns `[]` |
| **2**, seated | 1. **The rule commit, first:** the new rule, and `tests/test_drill*.py` onto the drill rule. 2. The three states, their tests, and the parser guards moved. 3. `brand_tone` RETIRED, with ADR-026 amendment 7. 4. `pave/cli.py:880`. Then one seat round, and the deletability audit through a local `pave check` | **`pave/twokey.py`: AI Quality + Legal/S&P + Platform Engineering + Security**, the file's own rule, so the body carries all four. `tests/test_demo_recordings.py`: Platform Engineering + AI Quality. `labels.json`: AI Quality + Security. The new rule: AI Quality + Platform Engineering |
| **3**, the close | Act 4 recorded; Act 5 RETIRED in `recordings.json` and `demo-script.md`; the journal and its ledger; the final claims table; row 12's ✅ and `BUILD.md:31`; tag `m12` after the merge | `recordings.json`: Platform Engineering + AI Quality |

**Why the new rule's seats.** Today one key decides whether every obligation has lapsed. PM is
the seat that feels a slide, and PM is not an enforceable seat, so the rule takes the owner of
what an owe means (AI Quality) and the owner of the test harness (Platform Engineering)
(ADR-081 decision 5).

## Implementation constraints, binding

1. **No test is edited at the close to go green.** The mechanism lands in PR 2, and PR 3
   edits no test.
2. **`milestone_is_closed` keeps raising** for a milestone the table does not list.
3. **No obligation changes state on one key**, and RETIRED lands with its ADR in the same
   diff.
4. **The parser guards are moved, never deleted.**
5. **Two-key rules land before the diffs they cover** (SPEC/11 constraint 7's precedent).
6. **No edit to:** `pave/cli.py`'s drill dispatch or `check`; the `Makefile`; `pave/drill.py`,
   `pave/drill_read.py`, `quality/drill/` or `drill/`; `surfaces/`, `loadtest/` or
   `pave/verdict.py`; `.gitignore`. So M11 debts 1 and 13 and M10 rows 20, 21, 27 and 29 do
   not fire.
7. **`brand_tone`'s labels, `quality/judge/frozen.json` and the draw stay byte-identical.**
8. **Citations resolve from `main` or a tag.**

## Obligations inherited, and the PR that pays each

**Ledger** means that PR 3 carries the debt once into `milestones/M12/README.md`, as
UNSCHEDULED, with its owner and trigger. It is not paid.

### Debts that fire on the paths PR 2 touches

| path | debt | paid by |
|---|---|---|
| `pave/twokey.py` (AI Quality, Legal/S&P, Platform Engineering, Security) | **M10 row 28**: test files on no two-key rule. It was 33 of 86 at #152 and is **36 of 87** on `main` at `4979054`, counting `tests/*.py` and `pave/tests/*.py` named `test_*`. It fires for the third time, after M11 PR 2 | **not paid.** PR 2 records the firing. The three drill files are paid under M11 debt 2, and the remaining 33 go to the ledger |
| `pave/twokey.py` | **M11 debt 2**: `tests/test_drill.py`, `test_drill_pins.py` and `test_drill_read.py` are on no rule | **PR 2**, onto the drill rule |
| `tests/milestone_status.py` | **M11 debt 21**: nothing but a test's need for a listed row makes `M12` the target. Its trigger also names *"M12's spec"*, so **this PR fires it too** | decided in this PR (ADR-081 decision 5); **paid in PR 2** |
| `tests/milestone_status.py`, `tests/test_calibration_owe.py` | **the check's new finding** (§5): the function that decides whether every obligation has lapsed is on no two-key rule, and neither is its test | **PR 2**, the new rule |
| `tests/test_demo_recordings.py`, `tests/test_calibration_owe.py` | **M10 row 24**: the parser guard's stated horizon, now real at row 12 | **PR 2**, the synthetic table |
| `quality/judge/calibration/labels.json` (AI Quality, Security) | **M11 debt 18**: `brand_tone`, re-deferred seven times (it supersedes M10 row 31) | **PR 2**, RETIRED |
| `labels.json`'s `owed` entry | **M11 debt 20**: no ADR-026 amendment records the seventh slide | **PR 2**, amendment 7 in the same diff |
| `pave/cli.py` | **M10 row 26**: seven stale M10 sites, `pave/cli.py:880` among them (the sentence is at `:888` on `4979054`) | **PR 2** pays the `pave/cli.py:880` site. The other six sites go to the ledger |

### Debts that fire elsewhere in M12

| path | debt | paid by |
|---|---|---|
| `README.md:983` | **M11 debt 3**, its README half: `pave drill` without `--out`, which exits 2. It already fired, unreported, at M11 PR 3 (check §5) | **PR 1, paid.** The `Makefile:66` half does not fire, because no M12 PR edits the `Makefile`. It goes to the ledger |
| `docs/governance/recordings.json` | **M11 debt 19**: Act 4's recording | **PR 3**, recorded |
| `recordings.json`, `demo-script.md:175-181` | **Act 5**, `owed_by: M12` | **PR 3**, RETIRED (ADR-081 decision 6) |
| `demo-script.md:180` | **M10 row 23**: the close on *"one verdict schema, three surfaces"* | **PR 3** |

### Carried and not fired: to the ledger at PR 3

| source | debts | owner |
|---|---|---|
| `milestones/M11/README.md:212-257` | debts 1, 4–17 and 22 | as listed there |
| `milestones/M10/README.md:275-331` | rows 1–22, 25, 27 and 29; row 26's six other sites; row 28's remaining 33 files | as listed there |
| `milestones/M10/README.md:328`, row 30 | **debt 10**, unsigned. M12 produces no goldens refusal census, so that trigger does not fire | Security |
| `milestones/M09c/README.md:262-269` | debts 1–4 and 6–8, and its inherited register | as listed there |
| ADR-075 amendment 8 | the DMA rename, no earlier than M11's close and never scheduled | Legal/S&P + Data Governance |
| `milestones/M11/README.md:218` | M11 debt 3's `Makefile:66` half | Platform Engineering |

## Bounded

**Three PRs in all, including this one: PR 1, PR 2 and PR 3. No spare.**
- Every PR opened against `main` counts, including an exhibit.
- A repair found after a PR merges lands in the next planned PR. A repair found after PR 3
  opens lands in PR 3, or M12 closes RED and names it. There is no fourth PR.
- Zero model calls, zero AWS calls, zero deploys, and no drill or eval run.
- One seat round, on PR 2.

## Demo artifact

```text
python -m pytest tests/test_calibration_owe.py tests/test_demo_recordings.py -q
python -m pave.cli check
git show m12:README.md | sed -n '/^## The twelve claims/,/^⁂/p'
```

The block ships as `text`. Its first two lines read PR 2's mechanism over PR 3's registries.
The third reads the tag that follows PR 3's merge.

**Predicted shape:**
- both test files pass with row 12 reading ✅. `brand_tone` reads RETIRED, Act 4 reads
  recorded, Act 5 reads RETIRED, and no obligation names a milestone as a target;
- `check: PASS`;
- the table: ✅ on claims 2, 4, 5, 9 and 11; INCOMPLETE on 1; FAILED on 6; UNSCHEDULED on 3,
  7, 8, 10 and 12, each with its ADR.

## Each deliverable, its measurement, and the PR

| # | deliverable | measurement | PR |
|---|---|---|---|
| 1 | claims 7, 8 and 12 UNSCHEDULED, each pointing to ADR-081 | the claims table | PR 1 |
| 2 | no obligation names a milestone as a target | the two obligation tests on the live registries | PR 2, re-read at PR 3 |
| 3 | each state refuses an entry missing what it must carry | planted synthetic entries; each check deleted and re-run through `pave check` | PR 2 |
| 4 | the parser guards discriminate with every row closed | the synthetic table, with the guard deleted and re-run | PR 2 |
| 5 | the mechanism's two files and `tests/test_drill*.py` are on two-key rules | `twokey.triggered` on each path | PR 2 |
| 6 | `brand_tone` RETIRED | `labels.json` and ADR-026 amendment 7, with two attestations | PR 2 |
| 7 | Act 4 recorded and Act 5 RETIRED | `recordings.json`, with two attestations | PR 3 |
| 8 | every open debt appears once in the ledger | M10's, M11's and 09c's registers read against it | PR 3 |
| 9 | the cap holds | *Bounded*, against the PR list | PR 3 |

## Definition of done

- [ ] **PR 1:** this file; ADR-081; rows 7, 8 and 12 of the claims table; row 12 and
      `BUILD.md:31`; `README.md:983`; both index rows; the check committed; `pave check` green
      in a clean worktree on the head before the body commit, which is tagged `cited-m12-pr1`,
      with the tag pushed before the PR opens.
- [ ] **PR 2:** the rule commit first; the three states and their tests; the parser guards
      moved; `brand_tone` RETIRED with ADR-026 amendment 7; `pave/cli.py:880`; the seat round;
      the audit; four attestations.
- [ ] **PR 3:** Act 4 recorded; Act 5 RETIRED; `demo-script.md`; the journal and its ledger;
      the final claims table; row 12's ✅; tag `m12`.

## What must not happen

- An obligation deferred to a milestone, or a row 13 added to hold one.
- `milestone_is_closed` answering for a milestone the table does not list.
- A state changed on one key, or RETIRED without its ADR in the diff.
- A test edited at the close to go green.
- A parser guard deleted instead of moved.
- A counter, classifier, panel, seed or revert landed to un-cut a claim, or a claim written for
  M12.
- `brand_tone` paid by hand-picked items, or paid at all inside M12.
- A closed milestone's record edited.

# M12 — the ledger: every obligation reaches a terminal state, and no claim

**Branches:** one per PR, three PRs, no spare · **Tag:** `m12` · **Closed:** 2026-09-15
**Spec:** `SPEC/12-the-ledger.md`, amendment 1 · **ADR:** ADR-081, amendment 1 ·
**Claims advanced:** none

---

## The verdict

**M12 carries no claim, and this is the register it exists to write.** The feasibility
check (`milestones/M12/feasibility.md`) found claim 12 pre-registerable only on three
conditions; the operator refused the first, the rollback cut; so claim 12 has no
pre-registerable wording and is **UNSCHEDULED, with claims 7 and 8** (ADR-081 decisions
1–3). Nothing was measured for any of them, and nothing is claimed.

**What the last row had to do anyway, and did.** Row 12 is the progression table's last
row, and `milestone_is_closed` raises for a milestone the table does not list. So on the
day row 12 closed, no obligation could be owed anywhere, and two parser guards asserting
`{True, False}` over the live table would go red. M12 built the terminal state that makes
an obligation nameable without a milestone, moved both guards onto made-up tables, and put
the reader that decides whether any obligation has lapsed on two keys.

| what closed | how | where |
|---|---|---|
| **the obligation mechanism's terminal state** | `RETIRED` and `UNSCHEDULED`, neither naming a milestone; 25 plants, 25 CAUGHT, 0 SILENT | `tests/milestone_status.py`, PR 2 |
| **the two parser guards** (M10 row 24) | moved onto made-up tables beside a live half, never deleted | PR 2 |
| **the mechanism on two keys** (the check's new finding) | AI Quality + Platform Engineering; `tests/test_drill*.py` onto the drill rule (M11 debt 2) | PR 2 |
| **`brand_tone`** (M11 debt 18, M10 row 31) | **RETIRED** on AI Quality + Security, with ADR-026 amendment 7 in the same diff (M11 debt 20) | PR 2 |
| **Act 4** (M11 debt 19) | **recorded**, `docs/governance/recordings/act4.mp4` | PR 3 |
| **Act 5** | **RETIRED** on Platform Engineering + AI Quality (ADR-081 decision 6) | PR 3 |
| **`demo-script.md:180`** (M10 row 23) | the close on *"one verdict schema, three surfaces"* rewritten | PR 3 |
| **M12 as anyone's target** (M11 debt 21) | a terminal state needs no listed row | PR 2 |

**Zero model calls, zero AWS calls, no deploy, no drill run and no eval run** across all
three PRs, as SPEC/12 bounded it.

### The twelve claims, as the table reads at this close

This is `README.md`'s claims table counted, not a summary of it. **Five proven, one
incomplete, one failed, five unscheduled.**

| verdict | claims | n |
|---|---|---|
| ✅ proven | **2** (gates fail closed and teach), **4** (no direct model access), **5** (adversarial pass = blocked-and-logged), **9** (judges are calibrated or advisory), **11** (readiness drills produce go/no-go artifacts) | **5** |
| ⬜ INCOMPLETE | **1** (one command → governed service): `pave new` renders and `pave verify` refuses fourteen ways, but nothing is deployed and the remaining authorship is well over the claimed thirty minutes | **1** |
| ❌ FAILED | **6** (rules have owners and dispositions): the delta *was* disposed end-to-end; the claim failed on **F1** (`disclosure-103`) and **F4.2** (`grounded-017`) | **1** |
| ⬜ UNSCHEDULED | **3** (one verdict schema, many runners), **7** (AI proposes, a human disposes), **8** (self-heal classifies before it repairs), **10** (consequence classes gate real actions), **12** (defect leakage is counted honestly) | **5** |

**Three of the five unscheduled claims are unscheduled because no population here
separates a true claim from a constant:** claim 3's records all pass through one builder,
claim 7's label is on no PR, claim 12 has no rollback. **Two are unscheduled because their
false state needs work another seat owns and no milestone plans:** claim 8 needs a real
contract bump (09c debt 1, Tool Owner), claim 10 needs a deploy Legal/S&P answered *no* to.

**None of the five is FAILED, and none is refused.** Each carries the condition under which
it becomes measurable, in the claims table itself.

---

## What can I demo right now?

Every command reads committed files. None calls AWS or a model.

```bash
# the mechanism over the live registries: no obligation names a milestone
python -m pytest tests/test_calibration_owe.py tests/test_demo_recordings.py -q

# the whole gate, hermetic
python -m pave.cli check

# the final claims table, off the tag
git show m12:README.md | sed -n '/^## The twelve claims/,/^⁂/p'
```

The exact outputs of the first two, at the close's gated head in a clean worktree, are in
`docs/pr-bodies/m12-pr3.md`. **The third reads the tag, which is pushed after this PR
merges**, so it is the operator's and is not reported here as run.

The four recorded acts are at `docs/governance/recordings/act{0,1,2,3,4}.mp4`. **Act 5 is
retired and will never be recorded.**

---

## What's the delta vs baseline?

**None, because nothing was run.** No goldens run, no adversarial run, no judge run, no
drill run, no history entry. Row 12's eval cells read `–`, not a number carried from M11 or
M09. Against `m00b` there is nothing to compare.

**Unearned passes: none.** No control was run, so none could flatter.

---

## What broke?

**1. The spec named three states and the code built two, and that was the code being
right.** `SPEC/12`'s pinned table lists PAID, RETIRED and UNSCHEDULED as if all three were
`state` values. PR 2 built two. A paid owe *leaves* `labels.json` — the entry goes, it is
not restamped — and `recordings.json` already spells payment `recorded: <path>`, resolved
by its own test. A `PAID` value would have been a state with no population and no reader.
PR 2's body flagged it (flag 4) and **SPEC/12 amendment 1 and ADR-081 amendment 1 correct
both documents at PR 3**, rather than leaving a spec that disagrees with its own
implementation.

**2. The PR 2 seat round was not taken, and the close does not substitute for it.**
SPEC/12's *Bounded* says *"one seat round, on PR 2"*; PR 2's brief did not include it and
its body said so (flag 2). It is not run at PR 3 either: **PR 3 carries no code, so a
finding has nowhere to land**, and the cap is three with no spare. What stands beside it is
a measurement rather than a reading — PR 2's deletability audit, 25 plants, 25 CAUGHT, 0
SILENT, each plant's old text confirmed unique first and every restore from a byte backup
rather than from git. That is evidence about the code and it is not a seat's disposition.
**This close reports one definition-of-done item unmet**, and it is in the table below.

**3. `pave/cli.py:888` was assigned twice and taken neither time.** SPEC/12 gave the stale
*"lanes arrive at M10"* sentence to PR 2; PR 2's brief left it out and offered it to PR 3;
PR 3 carries no code. So **all seven M10 row 26 sites are UNSCHEDULED**, the ledger carries
them once, and the reason is stated rather than the site quietly moving a third time.

**4. The feasibility check's `grep` was not runnable as printed.** §1's line had no `-E`,
so GNU grep read `|` as a literal and the command returned nothing. ADR-081 decision 1
recorded the `-E` re-run and its three extra matches when the ADR was written; the check
itself still printed the broken form. PR 3 corrects the line in place, with a three-line
note and the three matches (`pave/cli.py:1744`,
`quality/judge/calibration/labels.json:356`, `tests/test_no_account_identifiers.py:174`),
**none of them a counter, and no measurement or ruling changed**. The cost is that the file
is **no longer byte-identical** to the scratch copy the operator ruled on, which ADR-081's
header and `docs/pr-bodies/m12-pr1.md` both assert. ADR-081 amendment 1 supersedes that
claim explicitly.

**5. `docs/governance/ROLES.md` did not list the new rule.** Its table is checked as a
*subset* of `pave/twokey.py`, so no row was required and PR 2's body recorded it as outside
the brief (flag 11). A summary that omits a rule is how the two-key summary drifted twice
before (ADR-037), so PR 3 adds the row. It costs a **third attestation on this PR**:
`ROLES.md` is itself two-key on Platform Engineering + Security, and Security is not
otherwise a key here.

---

## Definition of done, item by item (close-milestone step 1)

Read against `SPEC/12`'s checklist as amended by amendment 1. **SPEC/12's own checkboxes
stay unticked in the file** — the same shape as M11 debt 22, and carried below.

| item | state |
|---|---|
| **PR 1:** SPEC/12; ADR-081; claims 7, 8 and 12 UNSCHEDULED; row 12 and `BUILD.md:31` re-titled; `README.md:983`; both index rows; the check committed; a gated head tagged `cited-m12-pr1` before the PR | **done** |
| **PR 2:** the rule commit first; the three states and their tests; the parser guards moved; `brand_tone` RETIRED with ADR-026 amendment 7; four attestations; the audit | **done**, minus the two items below |
| **PR 2:** `pave/cli.py:880` | **not done.** UNSCHEDULED with the other six M10 row 26 sites (ADR-081 amendment 1 item 2) |
| **PR 2:** one seat round | **NOT TAKEN, by ruling** (ADR-081 amendment 1 item 3). The single unmet item of this milestone's definition of done, reported as unmet |
| **PR 3:** Act 4 recorded | **done**, with its sha256 in the registry and in the commit that added the file alone |
| **PR 3:** Act 5 RETIRED, in `recordings.json` and `demo-script.md` | **done**, on Platform Engineering + AI Quality |
| **PR 3:** the journal and its ledger | **done**, this file |
| **PR 3:** the final claims table | **done**; no claim row was edited at this close, because none moved |
| **PR 3:** row 12's ✅ and `BUILD.md:31` | **done**, after the registry edits and never before |
| **PR 3:** tag `m12` | the operator's, after the merge |

---

## The close's own measurements

- **The gate:** `PYTHONIOENCODING=utf-8 python -m pave.cli check` in a clean worktree at
  the close's gated head. The exact line is in `docs/pr-bodies/m12-pr3.md`.
- **Row 12 closing, measured both ways rather than asserted.** After the registry commit,
  with row 12 still ⬜, `tests/test_demo_recordings.py` and `tests/test_calibration_owe.py`
  read **1 failed, 32 passed** — the one red being Act 5's `deferred_from: ["M12"]` against
  a row not yet closed. With row 12 flipped to ✅ in a plant restored from a byte backup
  and not from git: **33 passed**. **That is why the row is flipped after the registries
  and never before**, and it is the whole content of SPEC/12 constraint 1: no test is
  edited at the close to go green.
- **M10 row 28, re-counted on this tree:** **32 of 87** test files match no two-key rule,
  the same number PR 2 measured at `b3bac3b`. Row 28 fired at PR 2 and is not paid.
- **Act 4's blob:** `sha256 52545cc2368d7be7a319373bd73a3e5c78beea0c86eb172a2f2a5b014c9a92f5`,
  taken from the committed blob (`git cat-file -p`), not from the working tree, and equal
  to the working-tree file's.

---

## Not exercised at this close: steps 2 and 6b

**One cause for both: no run was taken, and none was owed.** SPEC/12 bounded the milestone
at zero model calls, zero AWS calls and no eval run, before any PR opened. **This is not a
deferral:** no later PR of M12 produces these files, there is no later PR, and nothing owes
them. Every path below is absent, which a reader checks by listing `milestones/M12/`.

| close-milestone step | what it reads | the file that does not exist | reading |
|---|---|---|---|
| **2**, record the evals (`SKILL.md:18-28`) | `run_evals --answers`, `run_adversarial --observations` | `milestones/M12/goldens-run.json`, `milestones/M12/probes-run.json` | **NOT EXERCISED.** No history entry is written, and row 12's goldens, judged and adversarial cells read `–` |
| **6b**, the sweep half (`SKILL.md:102-104`) | the frozen corpus against the deployed guardrail | `milestones/M12/topic-baseline.json` | **NOT EXERCISED.** No guardrail moved, no deploy was made, and no sweep was taken |
| **6b**, the census half (`SKILL.md:119-126`) | the accepted costs' footprint in this run's refusal census | `milestones/M12/goldens-run-refusals.json` | **NOT EXERCISED.** There was no run, so there is no census, and no earlier milestone's census is read in its place |

What step 6b still reads, because it needs no run:
- **`enforcement-probing` (ADR-035 amendment 9):** **not re-disposed.** M12 produced no
  goldens refusal census, so that trigger did not fire. Carried below, unsigned.
- **Retention on the withheld store (ADR-071 amendment 1):** **read: not met.** M12 made
  zero model calls.
- **No accepted hole has a deadline in this milestone.**

**Step 8, the recording, IS exercised**, which is a first for a close in this repository
that owed one and was not paying it late: Act 4 is recorded at PR 3, the milestone the
M11 deferral named, and Act 5 is retired in the same diff rather than slid again.

**The SPEC/12 demo artifact** is recorded as run for its first two commands and not for its
third, which reads the `m12` tag and therefore cannot run before the merge.

---

## The cap

**Three PRs, no spare, as ADR-081 decision 7 fixed it before PR 1 opened. Three were
opened.**

| # | PR | what | merged as |
|---|---|---|---|
| 1 | #163 | PR 1: SPEC/12, ADR-081, the claims table, row 12's title, the feasibility check | rebase, head `fbf69f3` |
| 2 | #164 | PR 2: the rule commit, the terminal state, the parser guards, `brand_tone` RETIRED | rebase, head `40d37fc` |
| 3 | this PR | PR 3: Act 4 recorded, Act 5 RETIRED, the ledger, row 12 | open |

**No exhibit was opened.** Also within the bound: zero model calls, zero AWS calls, zero
deploys, no drill run, no eval run — and **zero seat rounds**, against a plan of one, which
is the unmet item above and not a saving.

---

## Decisions

- **ADR-081** (PR 1): claim 12 unpre-registerable once the rollback cut is refused; the
  refused rewording substitutes rather than scopes; claims 7 and 8 unscheduled; M12 carries
  no claim; the obligation mechanism's terminal state; Act 5 retired; three PRs, no spare.
  - **Amendment 1** (PR 3): there is no PAID state; `pave/cli.py:888` is UNSCHEDULED; the
    PR 2 seat round was not taken by ruling; and the header's byte-identity claim for the
    feasibility check is superseded.
- **ADR-026 amendment 7** (PR 2): `brand_tone` RETIRED, by AI Quality with Security, at
  zero model calls. **The defect stands** — 5 gradeable items all labelled 0.5 — and
  retirement ends the owe without calibrating the axis.
- **SPEC/12 amendment 1** (PR 3): the same three corrections, in the file a reader of the
  milestone reaches first.

---

## The ledger: every obligation carried out of 09c, M10 and M11, once

**This is what the milestone is named for.** Every debt still open in an earlier journal
appears here exactly once, with a **terminal state**, an **owner**, a **trigger**, and
**the sentence that would reopen it**. Where two registers named the same debt, it appears
under its earliest number and the duplicate is noted.

**Nothing below is deferred to a milestone.** `UNSCHEDULED` means no milestone plans the
work and none is named; it is not a pass, and every event trigger still fires. There is no
row 13, and `milestone_is_closed` still raises for a milestone the progression table does
not list.

### Machine-read, in the two registries

These are the only obligations a test reads. Both are now terminal, and neither names a
milestone.

| registry | obligation | state | owner | trigger | what reopens it |
|---|---|---|---|---|---|
| `quality/judge/calibration/labels.json` `owed` | `brand_tone:meridian-sports`, zero label variance | **RETIRED** (PR 2, ADR-026 amendment 7) | AI Quality + Security | none: a retirement has no trigger | *"AI Quality pins `n` for a wider deterministic draw and a milestone with model calls is scheduled to label it."* Re-opening takes these two keys and a further ADR-026 amendment, and `how_it_must_be_paid` is kept byte for byte as the only admissible route |
| `docs/governance/recordings.json` | Acts 0, 1, 2, 3, 4 | **PAID** (`recorded`, a path each act's test resolves) | — | — | — |
| `docs/governance/recordings.json` | Act 5, *AI proposes, humans dispose* | **RETIRED** (PR 3, ADR-081 decision 6) | Platform Engineering + AI Quality | none | *"Claims 7, 8 and 12 all become measurable, or the act is re-scripted to an arc that is built."* Re-opening takes these two keys and an ADR |

### From M11 (`milestones/M11/README.md:212-257`)

| # | debt | state | owner | trigger | what reopens it |
|---|---|---|---|---|---|
| 1 | `pave/cli.py`'s drill dispatch, and `.pyc` under `pave/__pycache__/`, are on no two-key rule | UNSCHEDULED | Platform Engineering | the next PR that edits `pave/cli.py`'s drill dispatch | *"A PR edits the drill dispatch."* |
| 2 | `tests/test_drill*.py` on no rule | **PAID** at M12 PR 2, onto the drill rule | — | — | — |
| 3 | `README.md:961` and `Makefile:66` run `pave drill` without `--out`, which exits 2 | README half **PAID** at M12 PR 1; **`Makefile:66` half UNSCHEDULED** | Platform Engineering | the next PR that edits the `Makefile` | *"A PR edits the `Makefile` and line 66 still runs `pave drill` without `--out`."* |
| 4 | **W01** SILENT: its refusal is shadowed by a second door its test cannot tell apart | UNSCHEDULED | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` | *"A PR edits `pave/drill.py` and W01's refusal is still the shadowed door."* |
| 5 | **W03** SILENT, the same shape | UNSCHEDULED | AI Quality + Platform Engineering | the same | *"A PR edits `pave/drill.py` and W03 is still shadowed."* |
| 6 | **W08** SILENT, the same shape | UNSCHEDULED | AI Quality + Platform Engineering | the same | *"A PR edits `pave/drill.py` and W08 is still shadowed."* |
| 7 | **W23** SILENT, the same shape | UNSCHEDULED | AI Quality + Platform Engineering | the same | *"A PR edits `pave/drill.py` and W23 is still shadowed."* |
| 8 | **57 plants unrun**, plus 18 never on the spare's checklist (I1, I2, C01, C02, P01–P04, T01, T02, W40, W41, W43–W48). SPEC/11 row 9 is partially measured | UNSCHEDULED | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py`, `pave/drill_read.py` or `quality/drill/` | *"A PR edits the drill writer, its readers or its scenario, and claim 11's conformance row is still measured at 39 of 96."* |
| 9 | R09 has no witness: the pre-print surrogate refusal is shadowed by the print guard | UNSCHEDULED | AI Quality + Platform Engineering | the next PR that edits `pave/drill_read.py` | *"A PR edits `pave/drill_read.py` and R09's refusal is still unreachable."* |
| 10 | S03 has no witness: `required: signature` is never the refusing door | UNSCHEDULED | AI Quality + Platform Engineering | the next PR that edits `quality/drill/` | *"A PR edits the drill schema and `required: signature` still refuses nothing on its own."* |
| 11 | 18 writer refusal tests accept any refusal, and W43's tier type check is shadowed by the schema | UNSCHEDULED | AI Quality + Platform Engineering | the next PR that edits `pave/drill.py` | *"A PR edits the writer and those 18 tests still assert only that something refused."* |
| 12 | the claim's event and tier are read by no reader | UNSCHEDULED | AI Quality | the next PR that edits `drill/scenarios/` | *"A second scenario lands and the claim's pins still bind no reader."* |
| 13 | `python -m pave.cli` loads `pave.drill` before it dispatches to the readers | UNSCHEDULED | Platform Engineering | row 1's trigger | *"A PR edits the drill dispatch and the import is still eager."* |
| 14 | the `max-gap` segment of every finding is a writer constant | UNSCHEDULED | AI Quality | a second rule | *"A second drill rule is written and every finding still says `max-gap`."* |
| 15 | skip-worktree can hide edits to the writer and the scenario from `tree_clean`. The **procedural** remedy was applied at M11 PR 3 (a fresh clone) and no check enforces it | UNSCHEDULED | Platform Engineering + Security | the next drill run claimed as evidence | *"A drill run is claimed as evidence and `tree_clean` still cannot see a skip-worktree entry."* |
| 16 | the clean fixture's bytes are pinned by no reader, and `drill/fixtures/` is on one key. Its M11 trigger fired and was not paid | UNSCHEDULED | AI Quality | the next PR that edits `drill/fixtures/` or `tests/test_drill_pins.py` | *"A PR edits the fixture or its pins and no reader still checks the clean fixture's bytes."* |
| 17 | a CRLF re-save of the fixture makes a run INVALID with no retry; read at its trigger and not repaired | UNSCHEDULED | Platform Engineering | the next PR that edits `drill/fixtures/` | *"A PR edits the fixture and nothing refuses a CRLF one before a run."* |
| 18 | `brand_tone`'s widening, seventh re-deferral | **RETIRED** at M12 PR 2 | — | — | see the registry table above |
| 19 | Act 4's recording | **PAID** at M12 PR 3 | — | — | — |
| 20 | no ADR-026 amendment records the seventh slide | **PAID** at M12 PR 2: amendment 7 | — | — | — |
| 21 | nothing but a test's need for a listed row makes `M12` the target of rows 18 and 19 | **PAID** at M12 PR 2: a terminal state needs no row | — | — | — |
| 22 | SPEC/11's definition-of-done checkboxes are unticked | UNSCHEDULED | PM | the next PR that edits `SPEC/11-drill-go-no-go.md` | *"A PR edits SPEC/11 and its checkboxes are still unticked."* **SPEC/12's are unticked on the same grounds, and join this row.** |

### From M10 (`milestones/M10/README.md:275-331`)

**Rows 1–14: the deletability audit's 14 SILENT plants.** All UNSCHEDULED. Each reopens on
the same sentence with its own check named: *"A PR edits the file below and this plant is
still SILENT."*

| # | plant | what goes unwitnessed | owner | trigger |
|---|---|---|---|---|
| 1 | **W01** | Playwright `error` → INFRA when checks are also recorded (`emit.py:75-76`) | AI Quality + Platform Engineering | the next PR that edits `surfaces/web-player/emit.py` |
| 2 | **W03** | a check whose `ok` is anything but `true` fails (`emit.py:82`) | AI Quality + Platform Engineering | the same |
| 3 | **W06** | k6 no metrics → INFRA; equivalent on `verdict` (`emit.py:99-100`) | Platform Engineering | the same |
| 4 | **W09** | a summary in which no request was made is INFRA (`emit.py:105`) | AI Quality + Platform Engineering | the same |
| 5 | **W11** | a threshold outcome without `ok: true` is breached (`emit.py:93`) | AI Quality + Platform Engineering | the same |
| 6 | **W14** | a missing raw output has its own INFRA note (`emit.py:60`) | Platform Engineering | the same |
| 7 | **W15** | unparseable raw output is INFRA, not an uncaught exception (`emit.py:61`) | Platform Engineering | the same |
| 8 | **R01** | the k6 metric names the writer reads match what `loadtest/smoke.js` emits | AI Quality + Platform Engineering | the next PR that edits `smoke.js` or `emit.py` |
| 9 | **R02** | the Playwright raw shape the writer reads matches what the runner writes | AI Quality + Platform Engineering | the next PR that edits `player_smoke.py` or `emit.py` |
| 10 | **S01** | *responds 200* weakened to `status < 500` | AI Quality | row 15's trigger |
| 11 | **S02** | *title names the player* weakened to any title | AI Quality | row 15's trigger |
| 12 | **S03** | *heading visible* weakened to `count() >= 0` | AI Quality | row 15's trigger |
| 13 | **S04** | an unreachable page written FAIL rather than INFRA | AI Quality + Platform Engineering | row 15's trigger |
| 14 | **S05** | `player_smoke.py` deleted: 4895 passed, `check: PASS` | Platform Engineering | row 15's trigger |

| # | debt | state | owner | trigger | what reopens it |
|---|---|---|---|---|---|
| 15 | `player_smoke.py` is outside `testpaths` and outside CI; nothing collects or runs it | UNSCHEDULED | Platform Engineering + AI Quality | the next PR that edits `player_smoke.py` or `quality-gate.yml`, or the first spec that schedules claim 3 | *"A PR edits the runner or the workflow, and nothing still collects it."* |
| 16 | the writer decides and the gate reports what the writer decided; a falsifier read on the gate measures the writer's mapping | UNSCHEDULED | AI Quality + Platform Engineering | the first spec that schedules claim 3 | *"A spec schedules claim 3 and still reads a falsifier off the gate."* |
| 17 | A11: on INFRA the gate assertion cannot tell a correct INFRA from an out-of-contract record, because both exit 2 | UNSCHEDULED | AI Quality | the next PR that edits `tests/test_surfaces_emit.py` | *"A PR edits that test and all four INFRA cases still pass under W16 and W17."* |
| 18 | the k6 INFRA rule's missing artifact: the rule was changed on *"905 requests never connected"*, which no committed file records | UNSCHEDULED | AI Quality + Platform Engineering | the next PR that edits `emit.py`'s k6 INFRA rule or that fixture | *"A PR edits the k6 INFRA rule and the 905 still exists only in prose."* |
| 19 | **claim 3 is UNSCHEDULED**; it becomes measurable when a record can reach `gate decide` without `pave.verdict.build`, or when the schema can change between a record's write and its read | UNSCHEDULED | AI Quality (the claim) + Platform Engineering (the builder) | the first of those two conditions to exist on `main` | *"A second path to `gate decide` lands, or the schema becomes readable after a record is written."* |
| 20 | the surface runners, the writer and their tests serve no claim | UNSCHEDULED | Platform Engineering | the first spec that schedules claim 3 keeps or removes them | *"A spec schedules claim 3, or a reviewer asks what `surfaces/` is for."* |
| 21 | `pave/verdict.py:4-5`'s docstring states claim 3's architecture | UNSCHEDULED | Platform Engineering | the next PR that edits `pave/verdict.py` | *"A PR edits the builder and the docstring still sells the unscheduled claim."* |
| 22 | CLAUDE.md's pre-spec feasibility rule is prose; no check reads a spec for a named false state and a detecting command | UNSCHEDULED | PM + Platform Engineering | carried with D18's general check | *"A spec is written without a false state and nothing goes red."* **M12 is the second milestone whose feasibility check was honoured by hand.** |
| 23 | `demo-script.md:180` closes on *"one verdict schema, three surfaces"* | **PAID** at M12 PR 3 | — | — | — |
| 24 | the parser guards' horizon | **PAID** at M12 PR 2, moved onto made-up tables | — | — | — |
| 25 | SPEC/10's WITHDRAWN header is prose with no check; SPEC/09b's withdrawal-marker debt rides with it | UNSCHEDULED | PM + Platform Engineering | carried with D18's general check | *"A withdrawn spec is read as live by anything."* |
| 26 | **the seven sites that say M10 builds lanes or a second brand:** `pave/cli.py:888` (`:880` when the row was written), `pave/floors.py:338`, `pave/manifest.py:161` and `:354`, `pave/scaffold.py:123`, `templates/agent-tools/README.md:28`, `tests/test_floors.py:250` | UNSCHEDULED, **all seven**. Assigned to M12 PR 2 by SPEC/12 and not taken; offered to PR 3 and not taken, because PR 3 carries no code (ADR-081 amendment 1 item 2) | Platform Engineering | the next PR that edits each file | *"A PR edits one of those seven files and it still says M10 builds per-service lanes or a second brand."* |
| 27 | `.gitignore:5`'s `verdict-*.json` matches committed milestone records | UNSCHEDULED | Platform Engineering | the next PR that edits `.gitignore` | *"A PR edits `.gitignore` and a committed verdict record still needs force-adding."* |
| 28 | **test files on no two-key rule: 32 of 87 on this tree** (33 of 86 at #152, 36 of 87 at M12 PR 1, 32 of 87 after PR 2 put four on rules). Row 28's second half — `surfaces/**`, `loadtest/smoke.js`, `milestones/M10/**`, `tests/test_surfaces_emit.py` — is untouched | UNSCHEDULED. **Fired a third time at M12 PR 2 and not paid** | Platform Engineering | the next PR that edits `pave/twokey.py` | *"A PR edits `pave/twokey.py` and the count is still above zero."* |
| 29 | the gate's pytest echo at `pave/cli.py:1388` crashes on a non-`cp1252` character when stdout is redirected on Windows | UNSCHEDULED. **Not fired:** no M12 PR edits `check` | Platform Engineering | the next PR that edits `check` in `pave/cli.py` | *"A PR edits `check` and the echo still assumes `cp1252`."* |
| 30 | **debt 10: Security's re-disposition of `enforcement-probing`'s two trigger halves** (ADR-035 amendment 9). **Still unsigned.** M12 produced no goldens refusal census, so that trigger did not fire. *(This is also 09c debt 5 and M09b debt 10; it appears once, here.)* | UNSCHEDULED, unsigned | Security | the operator's signature on ADR-079's draft as ADR-035 amendment 12, **or** the next milestone producing a goldens refusal census | *"A goldens refusal census is produced, or the operator signs the standing draft."* |
| 31 | `brand_tone`'s widening (ADR-026 amendment 6) | **RETIRED** at M12 PR 2, via M11 debt 18 | — | — | see the registry table above |

### From 09c (`milestones/M09c/README.md:262-269`) and its inherited register

| # | debt | state | owner | trigger | what reopens it |
|---|---|---|---|---|---|
| 1 | **the browse gap:** `required: [query]` relaxed, or a browse mode added, on `catalog-search`'s input contract. Blast radius measured at 19 tests, three readers' committed records, and M09's priced delta. The generated `tools.contracts.json` is on no two-key rule | UNSCHEDULED. **It is also claim 8's only candidate false state** (ADR-081 decision 3) | Tool Owner | a semver bump on the `catalog-search` contract, citing SPEC/02:634-638 | *"The Tool Owner bumps the contract."* |
| 2 | **the era pin's second job.** The contracts digest reaches `fresh_join.py`, `context_census.py` and `residual_differential.py`, so a contract change refuses their committed records. ADR-078 decision 5's first job — the tier and gate era — is also unbuilt | UNSCHEDULED | Platform Engineering | the same semver bump, **before it lands**; the first job: the first tier or `p95_ms` move | *"A contract bump is opened, or a tier or `p95_ms` moves."* |
| 3 | **the `tokens_out` tier re-derivation.** ADR-078 decision 3's rule stands unexecuted; five failing cases widened to twelve | UNSCHEDULED | AI Quality | ADR-074 decision 2's *persists on a fresh run*, **already fired at M08b** | *"A fresh goldens run is taken."* |
| 4 | **the `p95_ms` re-derivation.** ADR-078 decision 4's condition and point stand unexecuted | UNSCHEDULED | AI Quality + Platform Engineering | ADR-014:711-716: the first scheduled milestone that both re-runs the goldens and does not read its own `p95` against a number it just chose | *"A milestone re-runs the goldens."* |
| 5 | debt 10, Security's re-disposition | **duplicate**: carried once as M10 row 30 above | — | — | — |
| 6 | **the citation checker's bare-SHA blind spot.** `tests/test_cited_commits_resolve.py:91` matches only a backticked SHA, so an unbackticked one is never checked | UNSCHEDULED. **No trigger was written at 09c's close; one is written here** | Platform Engineering | the next PR that edits `tests/test_cited_commits_resolve.py`, or the next document citing a bare SHA | *"A document cites a bare SHA that does not resolve and the gate stays green."* |
| 7 | **`grounded-017`'s margin, a live regression on `main`.** It was to be read on both 09c runs and at the derived tiers; there were no runs | UNSCHEDULED | AI Quality | the next goldens run, or debt 3, whichever comes first | *"A goldens run is taken."* |
| 8 | **F4's *"failed 0 of 3"*.** Read literally it means passed 3 of 3; `milestones/M09/f4.py:183` executed it as all three FAIL | UNSCHEDULED | PM + AI Quality | the next spec that pre-registers SPEC/09:57's third clause | *"A spec pre-registers that clause again."* |

**09c's inherited register** (`SPEC/09c` rows, unchanged unless noted):

| source | debt | state | owner | trigger | what reopens it |
|---|---|---|---|---|---|
| `:232` | **the DMA rename** (ADR-075 amendment 8), re-dated to no earlier than M11's close and never scheduled. M11 widened its blast radius with `jefferson-derby` | UNSCHEDULED | Legal/S&P + Data Governance | none written; it is a naming decision those two seats hold | *"Legal/S&P schedules the rename, or a new fictional name collides."* |
| `:233` | F4 cannot separate a change from generation drift; the one control run that addressed it by design was not taken | UNSCHEDULED | AI Quality | the next spec that reads F4 | *"A spec reads F4 without a control run."* |
| `:234` | the deletability audit runs `pytest` while the gate runs `pave check` | UNSCHEDULED. **Partly answered at M12 PR 2**, whose audit ran each plant through the files that read it with 0 SILENT, so no verdict depended on a reader elsewhere — the general gap stands | Platform Engineering | the next audit that runs plants through `pytest` alone | *"An audit reports a plant CAUGHT that `pave check` would have missed."* |
| `:235` | M09b's debts 1–5 | UNSCHEDULED, unchanged; no topic-wording deploy has happened | as listed at `milestones/M09b/README.md:341-412` | each row's own | *"A guardrail topic is reworded or deployed."* |
| `:236` | retention on the withheld store (ADR-071 amendment 1) | **read at this close: not met.** M12 made zero model calls | Data Governance | the next milestone making model calls | *"A milestone makes model calls and writes to the withheld store."* |
| `:237` | **no ADR and no spec is on any two-key rule.** This close edits ADR-081, the ADR index, SPEC/12, `README.md`, `BUILD.md` and this journal on no key | UNSCHEDULED | owned, unscheduled | none written | *"An ADR or spec is changed in a way a second seat would have refused."* |
| `:238` | every other row of `milestones/M09b/README.md:341-412` | UNSCHEDULED, unchanged | as listed there | each row's own | each row's own |

### Opened at this close

| # | debt | state | owner | trigger | what reopens it |
|---|---|---|---|---|---|
| A | **The PR 2 seat round was not taken.** SPEC/12 planned one and no PR of M12 ran it. PR 2's 25-plant, 0-SILENT audit is a measurement of the code and is not a seat's disposition (G6) | UNSCHEDULED. **The single unmet definition-of-done item of this milestone** | Platform Engineering + AI Quality | the next PR that edits `tests/milestone_status.py`, `tests/test_calibration_owe.py` or `pave/twokey.py`'s obligation rule | *"A seat round is run over M12 PR 2's diff and returns a finding the audit could not."* |
| B | **`milestones/M12/feasibility.md` is no longer byte-identical** to the scratch copy the operator ruled on. ADR-081's header and `docs/pr-bodies/m12-pr1.md` both assert it is; ADR-081 amendment 1 supersedes the claim, and `docs/pr-bodies/m12-pr1.md` is a closed PR's body and is not edited | UNSCHEDULED | PM + Platform Engineering | the next PR that pins a committed scratch artifact by digest | *"A digest is published for a file a later PR then corrects."* |
| C | **`ROLES.md`'s two-key table is checked only as a subset of `pave/twokey.py`.** A rule the module enforces and the table omits is invisible to `test_every_path_the_published_table_names_is_on_the_rule_it_claims`. M12 PR 2 added a rule and PR 3 added its row by hand; nothing would have caught the omission | UNSCHEDULED | Platform Engineering + Security | the next PR that adds a rule to `pave/twokey.py` | *"A rule lands in the module with no row in the table and the gate stays green."* |
| D | **SPEC/12's definition-of-done checkboxes are unticked**, because PR 3 edits no SPEC checklist. Same shape as M11 debt 22, and joined to it above | UNSCHEDULED | PM | the next PR that edits `SPEC/12-the-ledger.md` | *"A PR edits SPEC/12 and its checkboxes are still unticked."* |

---

## What's next

**Nothing, and that is the finding rather than the scheduling.**

There is no row 13. `milestone_is_closed` raises for a milestone the progression table does
not list, and after this close nothing can be owed to a milestone at all — which is exactly
why the terminal state was built before the row was flipped. **Every obligation above is
held by its owners, with a trigger that still fires**, and not by a date on a programme
that has ended.

**Five claims of twelve are proven.** One is incomplete, one failed on two falsifiers, and
five were never measurable here — three because no population in this repository separates
a true claim from a constant, two because their false state needs work another seat owns.
The un-cutting starts at each claim's stated condition, in `README.md`'s claims table, and
not at a rewrite.

**Building stops here.** The register above is the interface: an owner, a state, a trigger.
At scale it is a service, and the programme calendar is one trigger among several.

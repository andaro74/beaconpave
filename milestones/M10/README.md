# M10 — Playwright + k6 on one verdict schema

**Branches:** one per PR, four PRs (see *The cap*) · **Tag:** `m10` · **Closed:** 2026-09-13, **RED**
**Spec:** `SPEC/10-surfaces-one-envelope.md`, **withdrawn** · **Claims advanced:** none. Claim 3 is NOT MEASURED, and UNSCHEDULED

---

## The verdict

**Closed RED. Claim 3 was not measured, and no replacement claim exists.** No run was
taken, no deploy, and zero model calls in the milestone.

> **Agent evals, Playwright and k6 each write their result as one record in the one
> closed verdict envelope, and one gate decides all three by one contract.**
> (SPEC/10:60-63, withdrawn)

| | what happened | where |
|---|---|---|
| **the claim and its five falsifiers** | **WITHDRAWN before any measurement**, at PR 3 | ADR-079 amendment 1, on `milestones/M10/pr3-cold-review.md` and `pr3-deletability-audit.md` |
| **a replacement** | briefed as PR 4, and **stopped before anything was written** | ADR-079 amendment 2 |
| **claim 3** | **NOT MEASURED.** It cannot be measured as an envelope claim | amendment 2; README's claims table, **UNSCHEDULED** |

**None of F1–F5 is reported clean.** None fired, because none was read. The milestone
closes red because its claim was not shown, not because a falsifier fired.

### Why no replacement claim exists

**One function builds every verdict record, and it refuses to build one the gate would
refuse.**
- **One schema file.** `pave/verdict.py:26` and `pave/gate.py:41` both name
  `ROOT / "quality" / "verdicts" / "schema.json"`, from the same root.
- **Validated before any write.** `pave/verdict.py:88` validates each record inside
  `build()`, before `write()` (:92-97) is handed it.
- **Eight call sites, one builder.** Six in `pave/cli.py` (:334, :543, :665, :1139, :1432,
  :1601), plus `evals/run_evals.py:994` and `surfaces/web-player/emit.py:67`.

So an envelope claim has three possible terms, and none can fire:

| term | reading at the close |
|---|---|
| **1.** three runners emit records the closed schema accepts | **true by construction.** A record the schema refuses is never written: the writer raises, and the gate meets an absent file |
| **2.** a record with an undeclared key is refused, the key named | **already shown by PR 1**, `pave/tests/test_verdict_envelope.py:62-73`, with its control at :77-82 |
| **3.** read by `gate decide --verdicts` | **already read** by :85-94 |

**Claim 3's proof line describes an architecture this repository does not have.**
*"Agent evals + Playwright + k6 emit identical JSON"* (`README.md:813`, before this close)
describes runners that could each emit a different shape. The repository has one writer.
Identical JSON is not something the runners achieve. It is what `verdict.build` is.

**It becomes measurable only on one of two conditions, and neither is an envelope
claim:**
- a record that reaches `gate decide` without passing through `verdict.build`;
- a schema that changes between a record's write and its read.

### GREEN was available, and refused

Every reading a replacement could name comes out green:
- the clean pre-registration records exit 0;
- each drift record exits 2, naming its key;
- PR 1's test is green on `main`.

**A claim with no reachable falsifier confirming itself is the vacuous confirmation ADR-035
amendment 5 names** (ADR-035:1074-1077): *"confirmed by a corpus that would have confirmed
them had the change never been made."* Publishing claim 3 as proven on it would make the
claims table say something no reading could have contradicted.

### The evidence, committed

Scratch run on `main` at `9026d8a`, zero model calls, in `milestones/M10/close/`:

| file | what it is |
|---|---|
| `envelope-by-construction.py.txt` | the script, byte for byte as it ran. It is `.py.txt` because it fails ruff's I001, and it is not repository code |
| `envelope-by-construction-stdout.txt` | its stdout, 25 lines |
| `verdict-playwright-no-runner.json`, `verdict-k6-no-runner.json` | the two records `emit.py` wrote with no runner run. Force-added past `.gitignore:5` |

**One transformation, line endings only.** CRLF and bare CR became LF, because the
repository normalises to LF and a bare CR survives that. Sizes, before → after:
- script: 2702 → 2702 (0 CR);
- stdout: 1871 → 1841 (30 CR);
- the Playwright record: 465 → 450 (15 CR);
- the k6 record: 449 → 434 (15 CR).

Paths inside the stdout are scratch paths, and each record's `commit` is forty zeros, set
by the script.

What it shows, at stdout line:
- **:1** — the builder's and the gate's schema paths resolve to one file.
- **:3-10** — an undeclared key, an out-of-enum value and a non-number score are each
  refused inside `build()`, before any write.
- **:12-17** — with neither runner run, `emit.py` writes two records the schema admits,
  and the gate decides them as INFRA. Audit plant S05's door: term 1 cannot tell a runner
  that ran from one that does not exist.
- **:19-25** — `evals run services/no-such-service` exits 0 and writes nothing, and the
  gate reports the file missing.

### What was built, stated plainly and not as consolation

- **PR 1 (#152): the closed envelope.** `"additionalProperties": false` at the top level
  and on `provenance`, with three planted records and a test. Before it, `gate decide`
  passed a Playwright record carrying `p95_ms` at exit 0. **This stands, and it is the one
  thing M10 built that a check reads.**
- **PR 2 (#154):** a placeholder static player, two surface runners, one writer and its
  tests, the pre-registration records and readings, SPEC/10 and ADR-079. **Read by no
  claim.** They stay on `main`, carried as a debt below.
- **PR 3 (#156):** the deletability audit, the cold review, and the withdrawal.
- **This close (PR 4):** amendment 2, the evidence above, the rows, CLAUDE.md's
  feasibility rule and this journal.

---

## What can I demo right now?

Every command reads committed files. None calls AWS or a model. Each was run at the
close.

```bash
# one schema file, read by the builder and by the gate
grep -n 'schema.json"' pave/verdict.py pave/gate.py

# the builder validates before anything is written
sed -n 88,97p pave/verdict.py

# every verdict record in the repository is built by that one function: eight call sites
grep -rn "verdict_mod.build(\|verdict.build(" --include=*.py pave evals surfaces | grep -v /tests/

# terms 2 and 3, already shown by PR 1's test
python -m pytest pave/tests/test_verdict_envelope.py -q

# the scratch run, and its two no-runner records decided: INFRA, not a schema refusal
cat milestones/M10/close/envelope-by-construction-stdout.txt
python -m pave.cli gate decide --verdicts milestones/M10/close/verdict-playwright-no-runner.json \
    milestones/M10/close/verdict-k6-no-runner.json
```

SPEC/10's demo block stays `text`. Every file it reads, under `milestones/M10/clean/`, is
a record no PR of M10 produced.

---

## What's the delta vs baseline?

**None, because nothing was run.** No goldens run, no adversarial run, no judge run and no
history entry. Row 10's cells say *not run*, not a number carried from 09c or M09. Against
`m00b` there is nothing to compare.

Unearned passes: none.

---

## What broke?

**1. A claim was pre-registered on a property the builder already guarantees.**
- `pave/verdict.py:5-6` has said *"This module is the one place that constructs it"* since
  `0c4a852`, at M00a.
- ADR-079 decision 4 named `pave.verdict.build` as the path every surface record takes
  (ADR-079:122-123).
- SPEC/10 then wrote F1 and F2 against records that path had already validated against
  the same file.
- Three documents, a cold review and a 35-run audit did not ask whether the claim could
  have come out false. **The question that found it was the replacement brief's stop
  condition**, answered by reading one line, `verdict.py:88`.

**2. PR 2's readings proved that each reader runs, not that anything could fire.** ADR-079
decision 3's rule was *"every falsifier's reader executes end to end and emits a value
before the claim is committed"*. Every reader did. **A reader that runs and a falsifier
that can fire are different properties**, and the rule asked for the first one only.
CLAUDE.md's new rule asks for the second, before a claim is written.

**3. The first replacement was briefed as three more PRs, and it would have taken the
milestone to six by any count.** It stopped before a line was written. The stop is
recorded because the brief built the stop condition into itself, and that is what kept a
sixth PR from being spent on a vacuous spec.

**4. The cap brief did not reproduce.** The brief said the cap was spent at PR 3, with the
withdrawal as its cause. Counting every PR, five was reached at PR 3, but by exhibits #153
and #155. Counting as decision 6 did, this close is the fourth. Amendment 2 records both
counts. What the withdrawal spent is the plan, a reading at PR 4, and that is the breach it
records.

**5. The brief cited claim 3 at `README.md:778`.** On `main` it is `:813`. `:778` was
right when #152's body was written.

**6. Decision 8's disposition was routed to this close and is not signed.** The route is
intact and the advisory draft is at ADR-079:216-243, but a close authored in a session
cannot carry a seat's signature (G6). It is debt 10, below.

**7. A test docstring predicted this close wrongly.** `tests/test_demo_recordings.py:154-159`
says that when M10 closes, *"no row returns False and this guard is unsatisfiable again"*.
The roadmap has shifted twice since that was written (ADR-070, ADR-073). Rows 11 and 12
are still open, so the guard still discriminates. It is not edited here.

---

## Definition of done, item by item (close-milestone step 1)

| SPEC/10 item (:273-283) | at the close |
|---|---|
| PR 1 | **done** (#152) |
| PR 2 | **done** (#154): the runners, the writer and its tests, a placeholder player, the pre-registration records and readings, SPEC/10, ADR-079, ADR-026 amendment 6 and `labels.json`, the rows |
| PR 3 (the spare) | **done** (#156). The DoD said the cold review would be *"committed as ADR-079 amendment 1"*. It was committed verbatim as `milestones/M10/pr3-cold-review.md`, and amendment 1 is the withdrawal resting on it |
| PR 4 | **not taken as specified.** No player built, no two-key rules, no reading, F1–F5 not read, the row's cell not filled from a reading. The deletability audit was taken at PR 3, over PR 2's checks |
| PR 5 | **this close, merged as M10's fourth PR:** `close-milestone` in order. Journal written. **Security's debt-10 disposition NOT signed.** The row's ✅ is set. Tag `m10` is the operator's, after the merge |
| nothing under `milestones/M02/`, `M07/`, `M08/`, `M08b/`, `M09/`, `M09b/` or `M09c/` changes; no schema, runner, writer or test edited; SPEC/10's withdrawn body not edited | **holds.** This PR changes `milestones/M10/` (this journal and `close/`), ADR-079 and its index row, `README.md`, `BUILD.md`, `SPEC/README.md`, `CLAUDE.md`, and its own PR body. Nothing else |

---

## The close's own measurements

| | |
|---|---|
| deletability audit | **No new assertions; audit empty.** Every file this PR changes is Markdown, a text record, or JSON evidence. The committed script is `.py.txt`, which nothing collects or imports. It adds no test, no code and no check |
| the row flipped first | `make check` on the commit that flipped row 10 and nothing else, in a clean worktree: **4939 passed, 8 skipped, `check: PASS`**. The flip fired no obligation, and `tests/test_demo_recordings.py`'s discrimination guard stayed green |
| model calls | **zero**, in this PR and in the milestone. `evals/history/` holds no `m10` entry |
| moved | no case, tier, threshold, gate, baseline, falsifier, guardrail, policy, contract, schema, runner, writer, test or prompt constant |

---

## Not exercised at this close: step 2, step 6b, and the artifact

**One cause for all three: no run was taken.** The claim was withdrawn before any
measurement, and no replacement exists. **This is not a deferral.** No later PR of M10
will produce these files, and none owes them. Every path below is absent, which a reader
can check by listing `milestones/M10/`.

| close-milestone step | what it reads | the file that does not exist | reading |
|---|---|---|---|
| **2**, record the evals (`SKILL.md:18-28`) | `run_evals --answers` | `milestones/M10/goldens-run-1.json` | **NOT EXERCISED.** No history entry; row 10's goldens cell reads *not run* |
| **6b**, the sweep half (`SKILL.md:102-104`) | the frozen corpus against the deployed guardrail | `milestones/M10/topic-baseline.json` | **NOT EXERCISED.** No guardrail moved and no sweep was taken |
| **6b**, the census half (`SKILL.md:119-126`) | the accepted costs' footprint in this run's refusal census | `milestones/M10/goldens-run-refusals.json` | **NOT EXERCISED.** No census. M09's is named by decision 8's route as M09's, and it is not read as this close's |
| **the artifact** (SPEC/10:240-254) | `run.py` and `evals run` into `milestones/M10/clean/`, then `gate decide` over the three | `milestones/M10/clean/verdict-evals.json`, `verdict-playwright.json`, `verdict-k6.json` | **NOT EXERCISED.** No artifact recorded. `docs/governance/recordings.json` owes no act to M10: its acts are owed by M06, M09, M11 and M12 |

What step 6b still reads, because it needs no run:
- **`enforcement-probing` (ADR-035 amendment 9):** not re-disposed. ADR-079 decision 8
  routed Security's re-disposition to this close, on M09's census read as M09's. The
  draft is advisory, and the signature is not taken in this PR. Carried as debt 10.
- **Retention on the withheld store (ADR-071 amendment 1):** **not met.** M10 made no
  model call.
- **No accepted hole has a deadline in this milestone.**

---

## The cap

SPEC/10 *Bounded* (:213-238) and ADR-079 decision 6 (:170-173) cap the milestone at **five
PRs, document-only ones included**. The breach is recorded in ADR-079 amendment 2, in
ADR-075 amendment 4's form.

| bound | spent |
|---|---|
| five PRs | **four merged:** #152, #154, #156, and this close. Counting exhibits #153 and #155, six |
| the spare, a cold review before the reading | **taken**, at #156 |
| the reading, planned for PR 4 | **spent by the withdrawal.** A replacement needed three PRs against two slots |
| zero model calls, deploys, judge runs and re-freezes | **0** each |

**An exhibit that merges nothing and changes no file on `main` is outside the cap**
(amendment 2).

---

## Decisions

- **ADR-079** (PR 2): scope, target, claim, writer, dependencies, cap, `brand_tone` and
  debt 10's route.
  - **Amendment 1** (PR 3): the claim, its falsifiers, decision 3 and decision 4's
    criteria withdrawn.
  - **Amendment 2** (this close): claim 3 cannot be measured as an envelope claim; GREEN
    refused; the cap in amendment 4's form; the exhibit rule; debt 34 paid.
- **ADR-026 amendment 6** (PR 2): `brand_tone` re-deferred to M11 on no ground. Unchanged.
- **CLAUDE.md** (this close): the pre-spec feasibility rule, in *Milestone discipline*,
  and debt 34's line.

---

## Debts carried out of M10, each with an owner and a trigger

**None is repaired here, except D19 and debt 34.** *Unscheduled* means no milestone has
planned the work. `D` numbers are ADR-079 amendment 1's.

### The audit's 14 SILENT plants, one row each (`milestones/M10/pr3-deletability-audit.md`)

| # | plant | what goes unwitnessed | owner | trigger |
|---|---|---|---|---|
| 1 (D3) | **W01** | Playwright `error` → INFRA when checks are also recorded (`emit.py:75-76`; potency: main INFRA, plant PASS) | AI Quality + Platform Engineering | the next PR that edits `surfaces/web-player/emit.py` |
| 2 (D4) | **W03** | a check whose `ok` is anything but `true` fails (`emit.py:82`; main FAIL, plant PASS) | AI Quality + Platform Engineering | the same |
| 3 (D5) | **W06** | k6 no metrics → INFRA; equivalent on `verdict` (`emit.py:99-100`) | Platform Engineering | the same |
| 4 (D6) | **W09** | a summary in which no request was made is INFRA (`emit.py:105`; main INFRA, plant PASS) | AI Quality + Platform Engineering | the same |
| 5 (D7) | **W11** | a threshold outcome without `ok: true` is breached (`emit.py:93`; main FAIL, plant PASS) | AI Quality + Platform Engineering | the same |
| 6 (D8) | **W14** | a missing raw output has its own INFRA note; equivalent on `verdict` (`emit.py:60`) | Platform Engineering | the same |
| 7 (D9) | **W15** | unparseable raw output is INFRA, not an uncaught exception (`emit.py:61`; main INFRA, plant raises) | Platform Engineering | the same |
| 8 (D10) | **R01** | the k6 metric names the writer reads match what `loadtest/smoke.js` emits (`smoke.js:20`; clean PASS → INFRA) | AI Quality + Platform Engineering | the next PR that edits `smoke.js` or `emit.py` |
| 9 (D11) | **R02** | the Playwright raw shape the writer reads matches what the runner writes (`player_smoke.py:38-42`, `:50`; clean PASS → FAIL) | AI Quality + Platform Engineering | the next PR that edits `player_smoke.py` or `emit.py` |
| 10 (D12) | **S01** | *responds 200* weakened to `status < 500` (`player_smoke.py:38-39`) | AI Quality | row 15's trigger |
| 11 (D13) | **S02** | *title names the player* weakened to any title (`player_smoke.py:40`) | AI Quality | row 15's trigger |
| 12 (D14) | **S03** | *heading visible* weakened to `count() >= 0` (`player_smoke.py:41-42`) | AI Quality | row 15's trigger |
| 13 (D15) | **S04** | an unreachable page written as a failed check, FAIL rather than INFRA (`player_smoke.py:45-47`) | AI Quality + Platform Engineering | row 15's trigger |
| 14 (D16) | **S05** | `player_smoke.py` deleted: 4895 passed, `check: PASS` | Platform Engineering | row 15's trigger |

### The structure the audit and the cold review found

| # | debt | measured at | owner | trigger |
|---|---|---|---|---|
| 15 (D2) | **`player_smoke.py` is outside `testpaths` and outside CI.** Nothing collects or runs it | `pyproject.toml:35`, `testpaths = ["tests", "pave/tests"]`; `.github/workflows/quality-gate.yml:40`, `pip install -e ".[dev]"`, no Playwright; ADR-079 decision 5's cut | Platform Engineering + AI Quality | the next PR that edits `player_smoke.py` or `quality-gate.yml`, or the first spec that schedules claim 3 |
| 16 (D1) | **The writer decides, and the gate reports what the writer decided.** For Playwright and k6, a falsifier read on the gate measures the writer's mapping | `surfaces/web-player/emit.py:73-132` computes PASS, FAIL or INFRA; `pave/gate.py:137-170` reads `verdict` | AI Quality + Platform Engineering | the first spec that schedules claim 3 |
| 17 (D17) | **A11: on INFRA, the gate assertion cannot tell a correct INFRA from an out-of-contract record, because both exit 2.** W16 and W17 left all four INFRA cases green | `tests/test_surfaces_emit.py:30` | AI Quality | the next PR that edits `tests/test_surfaces_emit.py` |
| 18 | **The k6 INFRA rule's missing artifact (cold review 3b).** The rule was changed on an observation, *"905 requests never connected"*, that no committed file records. The committed plant run shows 40 unreached beside 9554 answered. *"905"* exists only in prose and in a hand-built fixture | ADR-079:132-138; `milestones/M10/pre-registration/planted-failure/k6-summary.json:37`; `emit.py:23`; `loadtest/smoke.js:8`; `tests/test_surfaces_emit.py:63` | AI Quality + Platform Engineering | the next PR that edits `emit.py`'s k6 INFRA rule or that fixture |

### Opened at this close

| # | debt | owner | trigger |
|---|---|---|---|
| 19 | **Claim 3 is UNSCHEDULED.** It becomes measurable when a record can reach `gate decide` without `pave.verdict.build`, or when the schema can change between a record's write and its read (ADR-079 amendment 2) | AI Quality (the claim) + Platform Engineering (the builder) | the first of those two conditions to exist on `main` |
| 20 | **The surface runners, the writer and their tests serve no claim.** CLAUDE.md: *"If a change doesn't serve one of them, it doesn't belong here."* `surfaces/web-player/`, `loadtest/smoke.js`, `tests/test_surfaces_emit.py`, the `surfaces` extra and k6 `v2.2.0` stay on `main`, because this close edits no runner, writer or test | Platform Engineering | the first spec that schedules claim 3 keeps or removes them. Until then, **unscheduled** |
| 21 | **The builder's docstring states claim 3's architecture too.** `pave/verdict.py:4-5` says *"one schema, many runners (claim 3). Agent evals, Playwright, k6, and the drill all emit it"*. The next line says the module is the one place that constructs it | Platform Engineering | the next PR that edits `pave/verdict.py` |
| 22 | **CLAUDE.md's pre-spec feasibility rule is prose.** No check reads a spec for a named false state and a detecting command. Same shape as D18 | PM + Platform Engineering | carried with D18's general check |
| 23 | **`docs/governance/demo-script.md:180` closes on *"one verdict schema, three surfaces"*.** The dashboard is cut (ADR-079 decision 1), and claim 3 is unscheduled | PM | the next PR that edits `demo-script.md` |
| 24 | **`tests/test_demo_recordings.py:154-159` predicts its guard becomes unsatisfiable at M10's close.** Rows 11 and 12 are open, so it does not (*What broke* 7) | Platform Engineering | the next PR that edits `tests/test_demo_recordings.py` |

### Carried from ADR-079 and SPEC/10, unchanged

| # | debt | owner | trigger |
|---|---|---|---|
| 25 (D18) | SPEC/10's WITHDRAWN header is prose with no check; SPEC/09b's withdrawal-marker debt (`SPEC/09b-the-guardrail-line-and-the-topic.md:535`) | PM + Platform Engineering | carried with SPEC/09b's; the general check stays owed |
| 26 | **The seven sites that say M10 builds lanes or a second brand:** `pave/cli.py:880`, `pave/floors.py:338`, `pave/manifest.py:161` and `:354`, `pave/scaffold.py:123`, `templates/agent-tools/README.md:28`, `tests/test_floors.py:250`. M10 closed without either | Platform Engineering | the next PR that edits each file |
| 27 | `.gitignore:5`'s `verdict-*.json` matches committed milestone records; this close force-added two more | Platform Engineering | the next PR that edits `.gitignore` |
| 28 | #152: 33 of 86 test files match no two-key rule; `surfaces/**`, `loadtest/smoke.js`, `milestones/M10/**` and `tests/test_surfaces_emit.py` are on no rule either (SPEC/10 constraint 3) | Platform Engineering | the next PR that edits `pave/twokey.py`. Planned PR 4 was to fire it and was not taken |
| 29 | #152: the gate's pytest echo at `pave/cli.py:1388` crashes on a non-`cp1252` character when stdout is redirected on Windows | Platform Engineering | the next PR that edits `check` in `pave/cli.py` |
| 30 | **Debt 10: Security's re-disposition of `enforcement-probing`'s two trigger halves** (ADR-035 amendment 9). ADR-079 decision 8 routed it to this close on M09's census read as M09's, with an advisory draft (ADR-079:216-243). **Not signed** | Security | **the operator's signature on the draft as ADR-035 amendment 12**, or the next milestone producing a goldens refusal census, whichever comes first |
| 31 | `brand_tone`'s widening (ADR-026 amendment 6) | AI Quality + Security | M11, on no ground; `tests/test_calibration_owe.py` reads it |

**Paid at this close:**
- **D19.** `README.md`'s ✺ footnote, `BUILD.md:29` and `SPEC/README.md:19` record the
  withdrawal, and that no replacement claim exists.
- **Debt 34** (ADR-076:633), in one line, CLAUDE.md:40.

### From 09c's register, unchanged

09c's debts 1–4 and 6–8 (`milestones/M09c/README.md:262-269`) and every row of its
inherited register (:275-286) carry unchanged. M10 inherited none as work and touched
none. 09c's debt 5 is row 30 above.

---

## What's next

**No milestone inherits claim 3.** It waits for one of the two conditions in row 19.

The next row is M11, the drill. It carries none of this, except `brand_tone`'s date, which
is a decision owed and not a payment.

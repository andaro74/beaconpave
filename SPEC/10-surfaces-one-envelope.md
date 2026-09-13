# M10 — one closed envelope, three runners, one gate

**Status: written at M10 PR 2, 2026-09-13, after every falsifier's reader had executed
end to end on committed records and before any claim reading.** Owned by the PM seat.
Tag `m10`; one branch per PR, none named `m10`. The derivation of every rule below is
**ADR-079**. `brand_tone`'s re-deferral is **ADR-026 amendment 6**. Every "what broke"
goes to the journal at close. This file states the milestone and nothing else.

## Scope, and the other `M10`

**M10 is the `README.md:51` row, *Playwright + k6 on one verdict schema*, and nothing
else.** ADR-075 decision 2 separated two different `M10`s *"in the one document a reader
is sent to for what is scheduled"* (ADR-075:564). This spec keeps them separate:

- **It does not carry claim 10**, *consequence classes gate real actions*. That claim is
  UNSCHEDULED (`README.md:820`), and nothing here reaches it.
- **It does not deploy `publish-highlight`**, or anything else. No deploy is taken in M10.
- **It does not add per-service lanes.** `pave/cli.py:880` and
  `templates/agent-tools/README.md:28` say they arrive at M10, and they do not.
- **It does not add a second brand.** `pave/floors.py:338`, `pave/manifest.py:161` and
  `:354`, `pave/scaffold.py:123` and `tests/test_floors.py:250` say it is M10's, and it
  is not.

Those seven sites are carried as a debt below and are **not edited**. The `brand_tone`
owe that rested on a second brand is re-deferred in this PR (ADR-026 amendment 6).

## Why

Claim 3 is *one verdict schema, many runners*, and its proof artifact is *agent evals,
Playwright and k6 emit identical JSON* (`README.md:813`). Until M10 PR 1 the claim had no
falsifier: the schema admitted any undeclared key, and `gate decide` passed a Playwright
record carrying `p95_ms` at exit 0. PR 1 (#152) closed the envelope.

**The static player is in scope and did not exist.** `SPEC/00-overview.md:27` excludes
only *"UI beyond the static player and one dashboard"*, and `README.md:941` names
`surfaces/web-player/` as *"Playwright + k6 on the same verdict schema"*. That directory
was a stub. So the player is M10's first deliverable, not a precondition M10 waits on.

## The one claim

**Agent evals, Playwright and k6 each write their result as one record in the one
closed verdict envelope, and one gate decides all three by one contract:** a pass is
admitted, a failure blocks at exit 1, a runner that cannot establish its result blocks at
exit 2, and a record outside the envelope blocks at exit 2.

It advances **claim 3**, and it is the only claim this milestone advances. Three terms:
**one envelope** (F1, F2), **many runners** (the denominator of every falsifier), and
**one gate, one contract** (F3, F4, F5).

### What k6 loading a static surface establishes, and what it does not

**k6 loads the static player served on `127.0.0.1`, not a live API.** The gateway has no
HTTP endpoint, and adding one is out of this milestone (ADR-079 decision 2).

- **It establishes** that a load runner's result reaches the same envelope as an agent
  eval and a browser run, through the same writer. It also establishes that the one gate
  decides a breached threshold as FAIL, and a surface that never answered as INFRA, by the
  same contract.
- **It does not establish** anything about the capacity or latency of the gateway, the
  agent or any deployed service. It says nothing about the p95 that ADR-014's `p95_ms`
  gate reads. `loadtest/README.md`'s game-day soak is not built. 5 virtual users for 10
  seconds is not a load profile anyone derived. Its two thresholds, `http_req_failed
  rate<0.01` and `http_req_duration p(95)<200`, are **chosen, not derived**, and they are
  not claim terms.
- **The same limit holds for Playwright.** Its three checks, *responds 200*, *title names
  the player* and *heading visible*, are structural. They say nothing about page quality.

### The five falsifiers, pre-registered

Any one fails the claim and closes the milestone red, with the runner named. **Every
reader named here executed end to end on committed records before this file was
written**: `milestones/M10/pre-registration/readings.txt`, one block per reading, raw
output and exit code, from records the committed runners wrote at `06ae901`.

The reader is **`python -m pave.cli gate decide --verdicts`** throughout. It reads each
record's whole body against `quality/verdicts/schema.json`, then `fail_closed`, then
`verdict`, and it prints one line per record naming `suite` and `layer`.

| | falsifier | record read | field | pre-registration reading |
|---|---|---|---|---|
| **F1** | **a clean record is refused.** Any of the three clean records, decided alone, exits 2 | `clean/verdict-{evals,playwright,k6}.json` | the whole record against the schema; `verdict` | exit 0 in one invocation, three `[PASS]` lines |
| **F2** | **drift is admitted.** Any clean record with one undeclared top-level key, decided alone, does not exit 2 with `Additional properties are not allowed` naming that key | `drift/verdict-{evals,playwright,k6}.json`, keys `arm`, `browser`, `p95_ms` | the record against the schema | exit 2 each, naming `'arm'`, `'browser'`, `'p95_ms'` |
| **F3** | **a failure does not block.** Any runner's planted failure, decided alone, does not exit 1 | agent: `milestones/M09/verdict-pre-fix.json`; Playwright and k6: `planted-failure/`, from `run.py --path missing` | `verdict` | exit 1 each |
| **F4** | **a harness error does not block.** Any runner's planted harness error, decided alone, does not exit 2 | agent: `planted-harness-error/verdict-evals.json`, which `pave evals run services/no-such-service` never writes; Playwright and k6: `planted-harness-error/`, from `run.py --no-serve` | the record's presence; `verdict` | exit 2 each: `verdict file is missing`, and INFRA twice |
| **F5** | **the gate does not compose.** The three clean records in one invocation do not exit 0 with lines naming `(evals L2)`, `(playwright L4)` and `(k6 L4)`; **or** clean evals, clean Playwright and the failing k6 record in one invocation do not exit 1 with exactly the k6 line `[BLOCK]` | as F1; then F1's two with F3's k6 | `verdict`, `suite`, `layer` | exit 0 with the three named lines; exit 1 with k6 alone `[BLOCK]` |

**Thresholds and denominators, defined here and nowhere later.**

- **The denominator is the three runners**, all of them in every falsifier:
  - `python -m pave.cli evals run services/highlights-agent`, L2
  - `surfaces/web-player/run.py`'s Playwright runner, L4
  - its k6 runner, L4
- **Every threshold is one runner and one exact exit code.**
- **Each condition is run once at the reading, with no retry.**
- **A runner that cannot be run at the reading writes no clean record**, and F1 fires on
  it (fail-closed).

**F3's agent record is M09's, named as M09's.** `milestones/M09/verdict-pre-fix.json` is
a FAIL written by `pave evals disclosure` from a real run through the deployed gateway.
M10 makes no model call. Producing a fresh agent FAIL hermetically would mean planting a
failing golden case or comparator, and a golden case is never edited to make a run come
out a certain way. So that record is read as the agent runner's committed failure.
**This is a limit of F3's agent third, published here.**

**The pre-registration readings are not the claim reading.** They were taken on a
placeholder page to prove each reader runs. The claim is read once, in PR 4, on the built
player.

## Reading rules, binding on every number this milestone publishes

1. **The criteria are fixed at this PR:** the three Playwright checks, the two k6
   thresholds, the 5-user 10-second profile, the writer's three-outcome rules, and the
   plants (`--path missing`, `--no-serve`, and one undeclared key per record). A change
   before PR 4's reading is an ADR-079 amendment committed before that reading.
2. **k6 is INFRA only when no request received a response.** The first rule, *any
   unreached request is INFRA*, was measured wrong before this file existed. A served 404
   closes each connection, and 905 requests of one run never connected while the rest
   received 404 (ADR-079 decision 4).
3. **The reading runs on the pinned runners:** `playwright==1.62.0` and k6 `v2.2.0`,
   recorded by `run.py` in `runner-versions.txt` beside every record. Any other version
   stops the reading.

## The plan, walked to the claim

1. **PR 1 (#152)**, merged: the envelope closed.
2. **PR 2**, this: the runners, the writer, a placeholder player, the pre-registration
   records and readings, this spec, ADR-079, and ADR-026 amendment 6.
3. **PR 3, the named spare:** a cold review before the claim is read (*Bounded*).
4. **PR 4:**
   - the static player built;
   - the two-key rules for the new paths;
   - the runs, from the committed runners, into `milestones/M10/`;
   - F1–F5 read;
   - the row's cell.
5. **PR 5:** the close, and Security's debt-10 disposition signed.

## Implementation constraints, binding

1. **No HTTP endpoint on the gateway, no edit to `gateway-stack.ts`, no deploy, no model
   call, in any PR of M10.** If any becomes necessary, the PR stops and reports.
2. **The player is static files served by the standard library on the loopback
   interface** (`surfaces/web-player/serve.py`). It reaches nothing beyond `127.0.0.1`.
3. **The new paths are on no two-key rule today:** `surfaces/**`, `loadtest/smoke.js`,
   `milestones/M10/**` and `tests/test_surfaces_emit.py`. This was measured by matching
   each path against `pave.twokey.RULES`. The writer decides what PASS means, and PR 4
   puts each path on a rule before the reading. That PR edits `pave/twokey.py`, which
   fires the #152 debt below.
4. **Verdict records under `milestones/` are force-added.** `.gitignore:5` ignores
   `verdict-*.json`, and `0db5276` shipped without its records because of it. `fb8a397`
   added them.
5. **The deletability audit runs through the CI gate**, not a local Windows gate, whose
   output echo crashes on a non-`cp1252` character (#152).
6. **Nothing else moves:** no golden case, goldens threshold, baseline, guardrail,
   corpus, judge instrument, tool contract or prompt constant.
7. **Citations resolve from `main` or a tag**, held by `tests/test_cited_commits_resolve.py`.

## What it builds

- **The static player**, a placeholder in PR 2 and built in PR 4.
- **The runners.** `surfaces/web-player/tests/player_smoke.py` for Playwright,
  `loadtest/smoke.js` for k6, and `surfaces/web-player/run.py` to run both.
- **One writer into the closed envelope:** `surfaces/web-player/emit.py`, with hermetic
  tests.
- **The records:** the pre-registration records and readings, then the claim reading.
- **The two-key rules** for the new paths.

## What it does not build

- claim 10, a `publish-highlight` deployment, or any deploy
- an HTTP endpoint on the gateway
- per-service lanes, or a second brand
- **the dashboard.** `BUILD.md`'s *"one dashboard"* is cut, and it had no measurement.
- **the claim 12 seed.** Cut from row 10, but **claim 12 is not unscheduled by the cut**:
  `README.md:822` and `BUILD.md:31` both schedule it at M12.
- the surface runners wired into `.github/workflows/quality-gate.yml` (ADR-079 decision 5)
- `loadtest/README.md`'s game-day soak
- a judge run, a re-freeze, or `brand_tone`'s widening
- anything of 09c's debts
- **a case edited, a threshold moved or a baseline reset to make any run pass**

## Obligations inherited and opened, each with an owner and a trigger

| source | debt | owner | here |
|---|---|---|---|
| this spec, *Scope* | **The seven sites that say M10 builds more:** `pave/cli.py:880`, `pave/floors.py:338`, `pave/manifest.py:161` and `:354`, `pave/scaffold.py:123`, `templates/agent-tools/README.md:28`, `tests/test_floors.py:250` | Platform Engineering | **opened; not edited.** Trigger: the next PR that edits each file |
| `milestones/M09b/README.md:360`; `milestones/M09c/README.md:266` | **Debt 10:** Security's re-disposition of `enforcement-probing`'s two trigger halves (ADR-035 amendment 9) | Security | **route approved by the operator.** Security re-disposes at **M10's close**, reading M09's census **as M09's**, the census the trigger fired on (`milestones/M09/README.md:400-415`). An **advisory** draft is ADR-079 decision 8, unsigned. The operator signs under G6 |
| ADR-026 amendment 5 (:290) | `brand_tone`'s widening | AI Quality + Security | **re-deferred to M11 in this PR** (ADR-026 amendment 6). Amendment 5's ground is void, and no ground is asserted |
| #152 | 33 of 86 test files match no two-key rule | Platform Engineering | opened. Trigger: the next PR that edits `pave/twokey.py`, which is **PR 4** |
| #152 | the gate's pytest echo at `pave/cli.py:1388` crashes on a non-`cp1252` character when stdout is redirected on Windows | Platform Engineering | proposed at #152 and not dispositioned. Trigger: the next PR that edits `check` in `pave/cli.py` |
| this PR | `.gitignore:5`'s `verdict-*.json` matches committed milestone records | Platform Engineering | opened. Trigger: the next PR that edits `.gitignore` |
| `milestones/M09c/README.md:262-265`, `:267-269` | 09c's debts 1–4 and 6–8: the browse gap, the era pin's second job, the tier and `p95_ms` re-derivations, the bare-SHA blind spot, `grounded-017`, F4's *"failed 0 of 3"* | as listed there | **carried unchanged; M10 inherits none as work** |
| `milestones/M09c/README.md:275-286` | every row of 09c's inherited register | as listed there | unchanged |

## Bounded

**Five PRs, including document-only ones. Four are planned, and one is a named spare.**
PR 1 (#152), PR 2, **PR 3 (the spare)**, PR 4, PR 5. A correction to merged work is a PR
and counts. Reaching five closes the milestone, red if necessary.

**Exhibit #153 is not counted.** It re-measured #152's audit rows through CI and was
closed unmerged, and CLAUDE.md defines an exhibit as a PR that never merges. That is
recorded here as a decision, not discovered at the close.

- **Zero model calls, zero deploys, zero judge runs and zero re-freezes** in the
  milestone.
- **One reading**, in PR 4. Every condition is run once.

**The spare is for one thing: a cold review, before PR 4 reads the claim, by a reader who
wrote neither this spec nor `emit.py`.** It answers three questions:

- **Does the writer execute each outcome at its clause's width?** The k6 INFRA rule was
  wrong once already.
- **Does each falsifier read the field it names** in the committed pre-registration
  records?
- **Is anything judged drawn from what judges it?** The Playwright checks were written
  against the placeholder they first judged, and the thresholds are chosen.

Its output is committed as **ADR-079 amendment 1**. If the spare is not taken, the slot
is not spent on anything else.

## Demo artifact

```text
python surfaces/web-player/run.py --out-dir milestones/M10/clean --playwright-python <py> --k6 <k6>
python -m pave.cli evals run services/highlights-agent --out milestones/M10/clean/verdict-evals.json
python -m pave.cli gate decide --verdicts milestones/M10/clean/verdict-evals.json \
    milestones/M10/clean/verdict-playwright.json milestones/M10/clean/verdict-k6.json
```

**The block ships as `text`.** Its records are PR 4's, and `tests/test_documented_commands.py`
runs `bash` blocks against `main`.

**Predicted shape:** three `[PASS]` lines naming `(evals L2)`, `(playwright L4)` and
`(k6 L4)`, and exit 0. The same invocation over the pre-registration records already
prints exactly that (`readings.txt`, the first block).

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **F1**, no clean record refused | `gate decide` on each clean record, exit codes | PR 4 |
| 2 | **F2**, drift refused | `gate decide` on each drift record, exit 2 and the named key | PR 4 |
| 3 | **F3**, a failure blocks | each planted failure, exit 1 | PR 4 |
| 4 | **F4**, a harness error blocks | each planted harness error, exit 2 | PR 4 |
| 5 | **F5**, one gate composes | the two invocations, exit codes and lines | PR 4 |
| 6 | every reader ran before the claim | `milestones/M10/pre-registration/readings.txt` | PR 2 |
| 7 | the writer's three outcomes | `tests/test_surfaces_emit.py`, each record through `gate.decide` | PR 2 |
| 8 | the new paths collect keys before the reading | a `twokey.triggered` plant per path | PR 4 |
| 9 | the deletability audit | each new check deleted, through the CI gate | PR 4 |
| 10 | the cap holds | *Bounded* against the PR list | PR 5 |

## Definition of done

- [x] **PR 1 (#152):** the envelope closed; the three plants refused; the committed
      verdicts unmoved.
- [ ] **PR 2:** the runners, the writer and its tests, a placeholder player; the
      pre-registration records and readings; this file; ADR-079; ADR-026 amendment 6 and
      `labels.json`; `BUILD.md`, `README.md`'s row 10 and its footnote, `SPEC/README.md`
      and the ADR index; `make check` green, run on the head before the body commit and
      cited by SHA.
- [ ] **PR 3** (the spare): the cold review committed as ADR-079 amendment 1.
- [ ] **PR 4:** the player built; the two-key rules; the reading; F1–F5; the row's cell;
      the audit.
- [ ] **PR 5:** journal; Security's debt-10 disposition signed; the row's ✅; tag `m10`.

## What must not happen

- A falsifier, threshold, check, plant or denominator changed after the reading it
  decides.
- A gateway endpoint, a deploy or a model call.
- The claim narrowed to whichever runner works.
- A record committed from a runner other than the committed one.
- Claim 10's territory, a second brand or a per-service lane, in any PR.

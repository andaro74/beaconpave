# ADR-079: M10 is claim 3 on one closed envelope, and the static player is its first deliverable

**Status: PROPOSED at M10 PR 2, 2026-09-13; ACCEPTED when that PR merges, which is the
operator's disposition.** Written after every falsifier's reader had executed end to end
on records the committed runners wrote at `06ae901`, and before any claim reading. The
scope, the target and debt 10's route are the operator's, and they are recorded here, not
argued. **Zero model calls, no deploy.**

**Seats:**
- AI Quality: the claim, the falsifiers, what PASS, FAIL and INFRA mean, and `brand_tone`.
- Platform Engineering: the runners, the writer, the server, the dependencies and the rule
  gaps.
- Security: debt 10, and the second key on `labels.json` and `pyproject.toml`.
- PM: the spec and the cap.

---

## Decision 1 — scope: the `README.md:51` row, and the other `M10` kept apart

**M10 is *Playwright + k6 on one verdict schema* and nothing else.** ADR-075 decision 2
(:95) separated two `M10`s, and its consequence says they are separated *"in the one
document a reader is sent to for what is scheduled"* (:564). `SPEC/10` states the
separation in its first section and cites that line.

**Not carried:**
- **Claim 10** (`README.md:820`, UNSCHEDULED).
- **A `publish-highlight` deployment**, or any deploy.
- **Per-service lanes.**
- **A second brand.**

Seven code and template sites still say M10 builds the last two:
- `pave/cli.py:880`
- `pave/floors.py:338`
- `pave/manifest.py:161` and `:354`
- `pave/scaffold.py:123`
- `templates/agent-tools/README.md:28`
- `tests/test_floors.py:250`

ADR-075 decision 2 called them *"correct as written"*. Under this scope they are not.
**They are not edited.** They are a debt at Platform Engineering, triggered by the next PR
that edits each file.

**`BUILD.md:29` is cut to the row.** Two things go:
- *"One dashboard"* goes because it has no measurement, on ADR-075's precedent for a
  dashboard panel.
- *"Claims 3, 12 seed"* goes to *claim 3*.

**Claim 12 is not unscheduled by that cut.** The brief said it would be, and the tables
say otherwise: `README.md:822` and `BUILD.md:31` both schedule claim 12 at M12. Only
M10's seed of it is removed.

## Decision 2 — the target: the static player, served on loopback, with no endpoint and no deploy

**Measured at #152's open, zero calls:**
- The committed synth snapshot's two stacks hold no API Gateway, function URL, CloudFront
  distribution or website bucket.
- The live account's four `BeaconpaveGateway-*` functions have zero function URLs.
- Every HTTP endpoint in the account belongs to another project.
- The repository had no HTML and no HTTP server.

So neither runner had a target that already existed.

**The operator settled it.** `SPEC/00-overview.md:27` puts the static player in scope by
excluding only *"UI beyond the static player and one dashboard"*. `README.md:941` names
`surfaces/web-player/` for exactly these runners. **The player is M10's first
deliverable.**

- **It is static files, served by `http.server` from the standard library** on
  `127.0.0.1` at an ephemeral port (`surfaces/web-player/serve.py`). A static player needs
  no application server, and the loopback bind keeps every run on this machine.
- **No HTTP endpoint is added to the gateway, `gateway-stack.ts` is not edited, and
  nothing is deployed.** If the milestone comes to need any of the three, it stops and
  reports.

## Decision 3 — the claim, its five falsifiers, and the reader each one names

**The claim**, as `SPEC/10` states it: agent evals, Playwright and k6 each write their
result as one record in the one closed envelope, and one gate decides all three by one
contract. **Three terms, five falsifiers; the spec's table is the rule.**

**The rule this decision executes: every falsifier's reader executes end to end and emits
a value before the claim is committed.** M09b's F4 read a field no file carried.

The reader here is `python -m pave.cli gate decide --verdicts`, and after #152 it can
refuse drift. It ran over records the committed runners wrote at `06ae901`. The output,
unedited, is `milestones/M10/pre-registration/readings.txt`:

| reading | records | exit | what it printed |
|---|---|---|---|
| F1, F5 clean | the three clean records, one invocation | **0** | `[PASS]` × 3, naming `(evals L2)`, `(playwright L4)`, `(k6 L4)` |
| F2 | each drift record | **2** × 3 | `Additional properties are not allowed ('arm' / 'browser' / 'p95_ms' was unexpected)` |
| F3 | `milestones/M09/verdict-pre-fix.json`, and the two `--path missing` records | **1** × 3 | `suite reported FAIL` |
| F4 | the absent agent record, and the two `--no-serve` records | **2** × 3 | `verdict file is missing`; `suite reported INFRA` × 2 |
| F5 composition | clean evals, clean Playwright, failing k6 | **1** | k6 alone `[BLOCK]` |

**Why F2 is separate from F1.** F1 says the runners' own records are in the envelope. F2
says the envelope refuses what is not. Without F2, a schema reopened to any key would
leave F1 clean.

**Why F3's agent record is M09's.**
- M10 makes no model call.
- A hermetic agent FAIL would need a planted failing golden case or comparator, and
  CLAUDE.md forbids editing a golden case to move a run.
- `milestones/M09/verdict-pre-fix.json` is a FAIL written by the agent-evals lane from a
  real run.

It is read as that, named as M09's, and the spec publishes it as a limit of F3's agent
third.

**Why F4's agent case is an absent record.** `pave evals run services/no-such-service`
exits 0 and writes nothing. That is the agent runner's actual behaviour when it cannot
establish a result, and `gate decide` blocks the absent file at exit 2. The claim reads
the runner as it is, not as a harness written for it.

**What k6 on a static surface establishes, and what it does not, is published in the
spec's body.** It establishes the envelope and the one contract for a load runner. It
establishes nothing about a live API's capacity or latency, and nothing about ADR-014's
`p95_ms`. Its two thresholds and its 5-user 10-second profile are chosen, not derived.

## Decision 4 — one writer, three outcomes, and the rule measured wrong before anyone relied on it

`surfaces/web-player/emit.py` is the only place a Playwright or k6 result becomes a
verdict, through `pave.verdict.build`. **The runners decide nothing:**
`player_smoke.py` writes the checks it made, and `smoke.js` writes k6's summary. The
writer's outcomes:

- **PASS:** every check or threshold held.
- **FAIL:** one did not. The notes name which.
- **INFRA:** raw output missing or unreadable, nothing recorded to decide on, Playwright
  could not reach the page, or no k6 request received a response.

**The first k6 rule was wrong, and it was found by running the plant before the claim was
written.** The rule said *any request that never reached the surface is INFRA*. On `run.py
--path missing`, the placeholder answered 404 and closed each connection. 905 requests
never connected while the rest received 404, and the rule reported **INFRA** for a surface
that was there and answering wrongly.

The rule is now *INFRA only when no request received a response*. `smoke.js` counts
`responses_received` apart from `transport_errors`. Re-run from the committed files: clean
PASS/PASS (exit 0), `--path missing` FAIL/FAIL (exit 1), `--no-serve` INFRA/INFRA (exit 2).
`tests/test_surfaces_emit.py` holds the 905-unreached case as FAIL.

**Records under `milestones/` are force-added.** `.gitignore:5` ignores `verdict-*.json`.
`0db5276` committed the raw outputs and `readings.txt` without the ten records they cite,
and `fb8a397` adds them unchanged. The ignore rule is not edited, which is a debt.

## Decision 5 — two dependencies, and a cut

CLAUDE.md asks for a line on why the standard library or an existing dependency will not
do. Two lines follow.

- **`playwright==1.62.0`**, a `surfaces` extra in `pyproject.toml`. **The row names
  Playwright, and the standard library cannot drive a browser.** It is an extra, not a
  dependency, for `baseline`'s reason: `make check` never launches a browser and must
  install and pass without one (G8). `pyproject.toml` is on *the test harness* rule
  (Platform Engineering + Security).
- **k6 `v2.2.0`**, a binary and not a Python package. **The row names k6.** A load loop
  over `urllib` would be a hand-built stand-in for the runner the claim is about.
  `run.py` records the version beside every record.

**Cut: the surface runners are not wired into `.github/workflows/quality-gate.yml`.**
Claim 3 is about the envelope and the decider, and the decider is the same `gate decide`
CI runs. Wiring puts a browser download and a k6 install on the one required workflow,
which is a separate decision with its own cost. **At scale, replace with a surfaces lane
in the required workflow, beside L2 and L5; the interface already matches.** The lane
would run `run.py` and hand its two records to the same `gate decide --verdicts` list.

## Decision 6 — the cap, the spare, and an exhibit

**Five PRs, including document-only ones.** Four are planned and one is a named spare:
PR 1 (#152, merged), PR 2 (this), **PR 3, the spare**, PR 4 (the player, the rules, the
reading), and PR 5 (the close). A correction to merged work counts. Reaching five closes
the milestone, red if necessary.

**Exhibit #153 is not counted.**
- It re-measured #152's audit rows P3, P4 and P5 through CI, because the local gate's
  output echo crashed. **All three verdicts matched.**
- It was closed unmerged, and CLAUDE.md defines an exhibit as a PR that never merges.
- If the operator counts it, the cap has no slot for the spare, and that is the operator's
  call to make at this PR's merge.

**The spare is for one thing:** a cold review before PR 4 reads the claim, by a reader who
wrote neither `SPEC/10` nor `emit.py`. It asks three questions:

1. Does the writer execute each outcome at its clause's width?
2. Does each falsifier read the field it names in the committed pre-registration records?
3. Is anything judged drawn from what judges it? The Playwright checks were written
   against the placeholder they first judged, and the thresholds are chosen.

**Its output is committed as amendment 1 to this ADR.** If the spare is not taken, the slot
is not spent on anything else.

## Decision 7 — `brand_tone`, re-deferred now and not at the close

ADR-026 amendment 5 re-dated the owe to *"M10, the surfaces milestone, where a
`meridian-news` axis is added"*. Decision 1 adds no second brand, so that ground is void.
It is the same break amendment 5 recorded against amendment 4. **ADR-026 amendment 6**,
with `labels.json`, re-defers it to M11 in this PR, on AI Quality's and Security's keys.
Doing it now means `tests/test_calibration_owe.py` never goes red on a ground already
known to be void. **No ground is asserted for M11**, because no scheduled milestone adds a
judge axis or names a re-freeze. M11 is the date of a decision, not a payment.

## Decision 8 — debt 10: the route, and an ADVISORY draft of the disposition

**The route is the operator's, approved:** Security re-disposes `enforcement-probing` at
**M10's close**, reading **M09's census as M09's**. That is the census the trigger fired on
(`milestones/M09/README.md:400-415`).

**How this differs from what M09b refused.** M09b refused to read M09's census **as its own
close's census** in `close-milestone` step 6b (`milestones/M09b/README.md:360`). That is a
substitution: one milestone's run standing in for another's. Here the census is named at
pre-registration as M09's, read as M09's, and used for the one decision it is evidence for.
M10 produces no goldens refusal census, and none is claimed. Step 6b's census half at M10's
close reads **NOT EXERCISED**, and the disposition is recorded beside it, not in its place.

### ADVISORY — not a disposition. Drafted for the Security seat; the operator signs under G6.

*A role subagent's or an author's draft is advisory input to a human, never an approval.
Nothing below is in effect until it is signed at M10's close as ADR-035 amendment 12.*

**What M09's census says** (`milestones/M09/README.md:400-415`):

| | reading |
|---|---|
| trigger half 2, `blackout-009` refused by majority | **fired**: refused 3 of 3 |
| of those three samples | two assessed `TOPIC:entitlement-circumvention`; only one assessed `TOPIC:enforcement-probing` |
| trigger half 1, the topic's at-least-once footprint above 2 of 25 | **not fired**: 1 of 25 |
| `entitlement-circumvention`'s at-least-once footprint | 4 of 25, all on the answer channel |

**Draft disposition, on ADR-035 amendment 11's precedent:**

1. **`enforcement-probing` is not re-opened on its merits.** Its own footprint, 1 of 25, is
   the lowest recorded.
2. **Trigger half 2 is recorded as having fired and been answered**, never as not met. It
   fired on a case that two of three samples attribute to the other topic.
3. **`blackout-009`'s majority refusal transfers to the `entitlement-circumvention`
   finding**, as amendment 11 §3 transferred it once before.
4. **The trigger is not rewritten in the diff that answers it** (amendment 11, *What this
   disposition does not license*). The observation that its two halves came apart is
   recorded for Security to take up separately, if at all.

**The dissent to record against it** is amendment 11's own: an operator signing a draft
the same session it was prepared collects one key, not two.

## What this ADR does not decide

- **The built player's design**, beyond static files served on loopback. That is PR 4's.
  Its design is constrained only by the three checks fixed here.
- **Whether exhibit #153 counts against the cap.** It is recorded as not counted, and the
  operator may rule otherwise.
- **Security's disposition on debt 10.** The draft above is advisory.
- **Whether the surface runners join the required workflow.** Cut, with the at-scale line.
- **Any of 09c's debts**, carried unchanged.

## Consequences

- **Claim 3 gets a falsifiable reading for the first time**, and every reader has already
  run.
- **The repository gains a static surface, two runners, one writer and a binary
  dependency outside `pyproject.toml`.** The runner versions are recorded per run.
- **k6's numbers here say nothing about any deployed service**, and the spec says so in
  its body.
- **The seven `M10` sites are now known to be wrong under the scope.** They are carried,
  not edited.
- **`brand_tone` slides a sixth time, and for the first time on no ground.**

**At scale, replace with** browser and load runners fanned across every surface a service
exposes, each emitting the same closed envelope into one decision service, with the
envelope versioned and a runner-specific `scores` vocabulary registered per suite. The
envelope is already closed, the writer is already one function per runner, and the
decider is already one list of records.

## Amendment 1 (2026-09-13, M10 PR 3, the named spare, before any measurement): SPEC/10's claim and falsifiers are WITHDRAWN

**SPEC/10's claim and its five falsifiers are withdrawn: not amended, and not repaired.**
Two things go with them:
- decision 3 above;
- decision 4's writer rules, as the criteria `SPEC/10`'s reading rules fixed.

**No claim reading was ever taken.** The readings in
`milestones/M10/pre-registration/readings.txt` proved each reader runs, and they ran on a
placeholder. The spec said so itself: *"The pre-registration readings are not the claim
reading."* No threshold is moved to clear a reading, because there is no reading.

**Why an amendment here and not a new ADR**, on ADR-076 amendment 1's precedent: this ADR
is where the pre-registration was made. A new ADR would leave decision 3 standing as
accepted pre-registration, with its withdrawal one document away.

**The two readings this rests on were committed before this amendment and are not
edited:**
- `milestones/M10/pr3-deletability-audit.md` at `f2bd393`
- `milestones/M10/pr3-cold-review.md` at `3d7fb55`, verbatim

Both were taken in the slot decision 6 named for a cold review, and the numbering below is
the cold review's. **Every `SPEC/10:NNN` below points at the file as pre-registered at
`691acfa`.** The WITHDRAWN header this PR adds moves each of those lines down.

### The reasons, as measured

**Five things decidable after PR 4's numbers exist (7a–7e).**
- **7a.** The criteria may change after the built player exists. `SPEC/10:113-114`: *"A
  change before PR 4's reading is an ADR-079 amendment committed before that reading."*
  The player is built in that same PR (`SPEC/10:129-134`). No rule forbids a run of the
  committed runners on the built player before the reading, and none requires that run to
  be recorded.
- **7b.** The keys are assigned in the PR that carries the numbers. `SPEC/10:145-147`:
  *"The writer decides what PASS means, and PR 4 puts each path on a rule before the
  reading."*
- **7c.** The player may be shaped to the checks. ADR-079:247-248: *"Its design is
  constrained only by the three checks fixed here."*
- **7d.** A failed reading can be recast as a stopped one and retaken. `SPEC/10:120-121`:
  *"Any other version stops the reading."* This stands against `SPEC/10:94`: *"Each
  condition is run once at the reading, with no retry."*
- **7e.** The records are not pinned. Which records F2, F3's agent third and F4's agent
  third read is open (2a), and F5's *"the failing k6 record"* (`SPEC/10:85`) names no run.

**Four values undefined at pre-registration (2a–2d).**
- **2a. The records.**
  - The falsifier table names the `pre-registration/` records (`SPEC/10:81-85`).
  - PR 4's runs go *"into `milestones/M10/`"* (`SPEC/10:132`).
  - The demo writes `milestones/M10/clean` (`SPEC/10:224`).
  - Nowhere is it said whether the drift records are rebuilt or re-read. Re-read, F2
    decides unchanged files under an unchanged schema, so it cannot fire.
- **2b. The version match.** `SPEC/10:120-121` stops the reading on *"any other version"*.
  `milestones/M10/pre-registration/clean/runner-versions.txt:2` records `k6.exe v2.2.0
  (commit/00a9a1b7f5, go1.26.5, windows/amd64)`, and nothing says what `v2.2.0` is matched
  against.
- **2c. The host.** No reading host is named in `SPEC/10:109-121`, while
  `loadtest/smoke.js:27`, `http_req_duration: ['p(95)<200']`, decides F5.
- **2d. The built player.** `SPEC/10:159` says *"The static player, a placeholder in PR 2
  and built in PR 4."* No criterion separates it from
  `surfaces/web-player/site/index.html:11`, which reads *"Placeholder."*

**Three falsifiers with no reading of their runner (1a–1c).**
- **1a. F4's agent third.** `SPEC/10:84` names a record *"which `pave evals run
  services/no-such-service` never writes"*.
  - `readings.txt:55-60` runs only `gate decide` on the absent path, and the gate exits 2
    for any absent path (`pave/gate.py:107-112`).
  - `grep -c 'evals run'` over `readings.txt` returns **0**. The runner's own behaviour was
    never shown executing.
- **1b. F1.** `SPEC/10:81` reads *"Any of the three clean records, decided alone, exits
  2"*. `readings.txt:5` decides the three in one invocation, and none is decided alone.
- **1c. F3's agent third.** The denominator's agent runner is *"`python -m pave.cli evals
  run services/highlights-agent`, L2"* (`SPEC/10:90`). F3's agent record prints *"(disclosure
  L3)"* at `readings.txt:36`.

**3a: the built player is constrained only by checks drawn from the placeholder.**
- "Beacon player" and `player-title` occur at `surfaces/web-player/site/index.html:6` and
  `:10`, and at `surfaces/web-player/tests/player_smoke.py:40` and `:42`. They occur nowhere
  else in the repository (`git grep`).
- ADR-024:86-88: *"A term that appears in one of them and nowhere else in the repository is
  presumed drawn from it."*
- ADR-079:247-248 constrains the player PR 4 would build by those checks and nothing else.

**3b: the k6 INFRA rule was fitted to a plant it judges, on an observation with no committed
artifact.**
- **The fit.** Decision 4 (:132-138) changed the rule after F3's own plant,
  `run.py --path missing`, read INFRA, so that the same plant reads FAIL.
- **The observation it was fitted to** is *"905 requests never connected"*
  (ADR-079:134-135).
- **Where "905" appears:** only in prose, at `SPEC/10:117`, ADR-079:134,
  `surfaces/web-player/emit.py:23` and `loadtest/smoke.js:8`. Otherwise only in a
  hand-built fixture, `tests/test_surfaces_emit.py:63`:
  `("k6", _k6((False, True), transport_errors=905, answered=6000), "FAIL")`.
- **What the committed plant run shows:**
  `milestones/M10/pre-registration/planted-failure/k6-summary.json:37`, `"count": 40,`,
  and `planted-failure/verdict-k6.json:13`, `"requests_unreached": 40,`. That is 40
  unreached beside 9554 answered. So the committed file is a different run from the one the
  rule was fitted to, and the run that motivated the rule was never committed.

**5d: F3 and F4 for Playwright and k6 read the writer's mapping, not the envelope.**
- `SPEC/10:56-58` says *"the one gate decides a breached threshold as FAIL, and a surface
  that never answered as INFRA."*
- That verdict is computed at `surfaces/web-player/emit.py:104-131`.
- The gate reads the `verdict` it is handed (`pave/gate.py:137-156`).

**The audit: 14 of 24 plants SILENT, and none caught elsewhere.**
- **What ran.** 24 plants through `quality-gate` on exhibit #155, closed unmerged. The
  control, run 34764760657, read 4898 passed, 9 skipped.
- **The count.** 10 sole witnesses, **0 caught elsewhere, 14 SILENT.**
- **All five `player_smoke.py` plants are SILENT**, because nothing collects or runs the
  file:
  - `pyproject.toml:35`, `testpaths = ["tests", "pave/tests"]`, excludes
    `surfaces/web-player/tests/`.
  - `.github/workflows/quality-gate.yml:40`, `pip install -e ".[dev]"`, installs no
    Playwright.

### How many times something judged has been drawn from what judges it

**The brief for this PR said this is the third time. Measured, the record supports third
or fourth depending on how one earlier case is counted, and both are recorded here.**

The earlier cases:
1. **ADR-024's amendment of 2026-08-21.**
   - :73-76: ADR-035's Change A draft reached for `VPN`, a term whose only occurrence was
     `PHR-002` in `quality/adversarial/phrasings.yaml`.
   - :78-82: a v4 wording *"written specifically to close `ATK-007`"* in
     `quality/adversarial/topic-attacks.yaml`.
2. **ADR-076 amendment 1 (:365).** The derivation rule selected on
   `quality/adversarial/refusal-shapes.yaml`, which its owning ADR-067 forbids from judging a
   fix. That is a wording chosen by a corpus barred from judging it.
3. **ADR-077 amendment 2 (:558-567).** A candidate carried words that appear in
   `quality/adversarial/disclosure-shapes.yaml` and in no other file. That is the corpus
   gate 7 would have judged it against.

How the count comes out:
- **Third**, counting by occasion and reading case 2 as a selector rather than a drawn term.
- **Fourth**, counting case 2.
- **Fifth**, counting case 1's two instances separately.

**3b is the first where the fitting observation has no artifact at all.** Every earlier
fitting source is a committed file: `phrasings.yaml`, `topic-attacks.yaml`,
`refusal-shapes.yaml` and `disclosure-shapes.yaml`. Here the fitting source is a run that
was never committed.

### What survives, and why

- **PR 1's closed envelope, `81c25e6`.**
  - `quality/verdicts/schema.json:7` reads `"additionalProperties": false`, and `:103`
    closes `provenance`.
  - It is byte-identical since: `git diff 81c25e6 HEAD -- quality/verdicts/schema.json` is
    empty.
  - It reads no runner, no surface and no SPEC/10 criterion. Cold review 3d found it not
    drawn from the surface records.
- **`pave/tests/test_verdict_envelope.py` and its three fixtures, `d417f90`.**
  - They are unchanged since: `git diff d417f90 HEAD` over both is empty.
  - The test plants its own fixtures (:36-40) and decides the committed M09 verdicts
    (:107-115). Nothing in it depends on SPEC/10.
  - Its audit, from #152 and re-measured in CI on exhibit #153, stands.
- **The runners' committed clean and drift records.**
  - Which records: `milestones/M10/pre-registration/clean/verdict-{evals,playwright,k6}.json`
    with the raw outputs beside them, and `drift/verdict-{evals,playwright,k6}.json`.
  - Why they survive: they record what was written and what the gate decided, and they read
    under the envelope with no claim attached.
  - Measured: each drift record is its clean record with exactly one key added (`arm`,
    `browser` or `p95_ms`), and every other field is identical.
  - Their limits are carried with them, not repaired:
    - the clean agent record's producing run is not in `readings.txt` (1a);
    - the drift records were built by hand, not by a runner;
    - all of them were taken against a placeholder page, so they are evidence for no claim.
- **Withdrawing requires no edit to anything PR 1 put on `main`.** None was made.

`readings.txt` and the `planted-failure/` and `planted-harness-error/` records stay
committed and unedited, as the record of the withdrawn pre-registration. They are not
claimed as surviving evidence, because 3b rests on the planted-failure run.

### What this amendment does not rule on

- **Decisions 1, 2, 5, 7 and 8:**
  - the scope;
  - the target;
  - the dependencies;
  - `brand_tone`'s re-deferral;
  - debt 10's route and its advisory draft.

  Neither reading found against them. ADR-026 amendment 6's ground cites `SPEC/10`
  (ADR-026:356-358). Whether these decisions stand with the spec withdrawn is the
  operator's to rule. This amendment neither voids nor re-affirms them.
- **Decision 6's cap.** This is PR 3 of five. Exhibit #155 is uncounted on decision 6's
  precedent for #153 (:175-180), and the operator may rule otherwise.
- **The replacement.** Nothing here is:
  - a spec, falsifier, criterion or plan;
  - a repaired defect;
  - an edit under `surfaces/`, `loadtest/`, `quality/verdicts/` or `tests/`;
  - a run or a deploy.

### Debts carried, none repaired

| # | debt | measured at | owner | trigger |
|---|---|---|---|---|
| D1 | **The writer decides, and the gate reports what the writer decided.** For Playwright and k6, a falsifier read on the gate measures the writer (5d) | `surfaces/web-player/emit.py:73-132` computes PASS, FAIL or INFRA; `pave/gate.py:137-156` reads `verdict` | AI Quality + Platform Engineering | the next spec that pre-registers claim 3 |
| D2 | **`player_smoke.py` is outside `testpaths` and CI** | `pyproject.toml:35`; `.github/workflows/quality-gate.yml:40`; decision 5 (:161-166) | Platform Engineering + AI Quality | the next spec that pre-registers claim 3, or the next PR that edits `player_smoke.py` or `quality-gate.yml` |
| D3 | SILENT **W01**: Playwright `error` → INFRA when checks are also recorded | `emit.py:75-76`; potency: main INFRA, plant PASS | AI Quality + Platform Engineering | the next PR that edits `emit.py` |
| D4 | SILENT **W03**: a check whose `ok` is anything but `true` fails | `emit.py:82`; potency: main FAIL, plant PASS | AI Quality + Platform Engineering | the same |
| D5 | SILENT **W06**: k6 no metrics → INFRA; equivalent on `verdict` | `emit.py:99-100` | Platform Engineering | the same |
| D6 | SILENT **W09**: a summary where no request was made is INFRA | `emit.py:105`; potency: main INFRA, plant PASS | AI Quality + Platform Engineering | the same |
| D7 | SILENT **W11**: a threshold outcome without `ok: true` is breached | `emit.py:93`; potency: main FAIL, plant PASS | AI Quality + Platform Engineering | the same |
| D8 | SILENT **W14**: a missing raw output has its own INFRA note; equivalent on `verdict` | `emit.py:60` | Platform Engineering | the same |
| D9 | SILENT **W15**: unparseable raw output is INFRA, not an uncaught exception | `emit.py:61`; potency: main INFRA, plant raises | Platform Engineering | the same |
| D10 | SILENT **R01**: the k6 metric names the writer reads match what `smoke.js` emits | `loadtest/smoke.js:20`; potency: clean PASS → INFRA | AI Quality + Platform Engineering | the next PR that edits `smoke.js` or `emit.py` |
| D11 | SILENT **R02**: the Playwright raw shape the writer reads matches what the runner writes | `player_smoke.py:38-42`, `:50`; potency: clean PASS → FAIL | AI Quality + Platform Engineering | the next PR that edits `player_smoke.py` or `emit.py` |
| D12 | SILENT **S01**: *responds 200* weakened to `status < 500` | `player_smoke.py:38-39` | AI Quality | D2's trigger |
| D13 | SILENT **S02**: *title names the player* weakened to any title | `player_smoke.py:40` | AI Quality | D2's trigger |
| D14 | SILENT **S03**: *heading visible* weakened to `count() >= 0` | `player_smoke.py:41-42` | AI Quality | D2's trigger |
| D15 | SILENT **S04**: an unreachable page written as a failed check, FAIL rather than INFRA | `player_smoke.py:45-47` | AI Quality + Platform Engineering | D2's trigger |
| D16 | SILENT **S05**: `player_smoke.py` deleted | the file; 4895 passed, `check: PASS` | Platform Engineering | D2's trigger |
| D17 | **A11: the gate assertion cannot tell a correct INFRA from an out-of-contract record, because both exit 2.** W16 and W17 left all four INFRA cases green | `tests/test_surfaces_emit.py:30` | AI Quality | the next PR that edits `tests/test_surfaces_emit.py` |
| D18 | **SPEC/10's WITHDRAWN header is prose with no check behind it.** SPEC/09b's debt on withdrawal markers fires again at this PR and is not paid | `SPEC/09b-the-guardrail-line-and-the-topic.md:535` | PM + Platform Engineering | carried with SPEC/09b's; the general check stays owed |
| D19 | **Three rows still state the withdrawn claim as pre-registered.** Not edited, on SPEC/09b PR 1c's precedent (`a225624` edited the spec, the ADR and its index row) | `README.md:723`; `BUILD.md:29`; `SPEC/README.md:19` | PM | M10's next PR |

D3–D17 are the audit's rows A1–A11, listed one plant per row.

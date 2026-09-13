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

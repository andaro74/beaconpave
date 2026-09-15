# ADR-081: M12 is the ledger; claims 7, 8 and 12 are unscheduled; the obligation mechanism has a terminal state; and Act 5 is retired

**Status: PROPOSED at M12 PR 1, 2026-09-14. ACCEPTED when that PR merges**, which is the
operator's disposition. It was written before any code, with zero model calls and zero AWS
calls, on `main` at `4979054` (tag `m11`).

**What the operator ruled, which this ADR records rather than argues:**
- the feasibility check's condition 1, the rollback cut, is **refused**, so claim 12 has no
  pre-registerable wording;
- claim 12 is UNSCHEDULED, with claims 7 and 8;
- M12 is the close-out milestone and carries no claim, on 09c's precedent;
- zero model calls; three PRs, no spare, and a cap of three.

**The check** is committed as `milestones/M12/feasibility.md`, byte-identical to the scratch
copy the operator ruled on (sha256 `0c04b6dec693…`). Its measurements stand. The rulings
above supersede its §2 wording, its §3 deliverables and its §6 plan of four PRs with a spare.

**Seats:**
- PM: the spec and the claims table.
- AI Quality: what an unscheduled claim publishes, and `brand_tone`'s retirement, with
  Security.
- Platform Engineering: the obligation mechanism and `pave/twokey.py`.
- Tool Owner: claim 8's only candidate false state (09c debt 1).
- Security: `brand_tone`'s retirement, and debt 10.

---

## Decision 1 — claim 12 is UNSCHEDULED: nothing is pre-registerable once the rollback cut is refused

**The claim** (`README.md:844`): *"Defect leakage is counted honestly"*. Its proof: *"Increments
from rollbacks, never gate failures"*.

**The check, as run at `4979054`, quoted from `milestones/M12/feasibility.md` §1:**

```text
$ git log --oneline main | grep -i -c "revert"
0
$ git log main --format='%h %s' --grep='^Revert'
(nothing)

$ gh run list --workflow quality-gate.yml --limit 400 --json conclusion,event,headBranch \
    --jq 'group_by(.conclusion) | map({conclusion: .[0].conclusion, n: length})'
[{"conclusion":"failure","n":63},{"conclusion":"success","n":252}]
$ gh run list --workflow quality-gate.yml --branch main --limit 400 --json conclusion,event \
    --jq 'map(select(.conclusion=="failure")) | length'
0
$ gh pr list --state all --label exhibit --limit 100 --json number,state --jq 'length'
7
$ gh pr list --state all --label ai-proposed --limit 100 --json number,state,title --jq '...'
(nothing: 0 PRs)

$ grep -rn -i "leakage|rollback|self.heal|selfheal|curation|drift.vs" pave evals quality tools services platform templates tests Makefile .github
pave/cli.py:33:  pave selfheal <service>   classify red suite, propose repair
pave/cli.py:1745: _stub("selfheal", "classify the red suite for … as drift-vs-defect; if drift, propose …")
quality/verdicts/schema.json:5: "… makes company-wide regression-risk and defect-leakage dashboards possible."
(no counter, no rollback record, no classifier)
```

**Re-run for this ADR on `main` at `4979054`, the same day.**
- Every `git` and `gh` number reproduced exactly: 0 reverts, no `^Revert` subject, 63 failed and
  252 successful gate runs, 0 failures on `main`, 7 exhibit PRs and 0 `ai-proposed` PRs.
- **The `grep` line is not runnable as printed.** Without `-E`, GNU grep reads `|` as a literal
  character. Re-run with `-E`, and with `node_modules`, `cdk.out` and `__pycache__` excluded,
  it prints three lines the check's summary omits, and none of them is a counter:
  - `pave/cli.py:1744`, the `elif` above `:1745`;
  - `quality/judge/calibration/labels.json:356`, prose in `brand_tone`'s `why_re_deferred`;
  - `tests/test_no_account_identifiers.py:174`, a *"leakage scan"* for account identifiers.

**Why no wording survives.** The claim's two halves fail differently (check §2):
- **"Increments from rollbacks."** There is no rollback here to count. No delivery pipeline
  exists, and `main` holds 0 revert commits. A counter that always returns 0 reads 0 on today's
  history, so no state of today's world separates a correct counter from a constant.
- **"Never from gate failures."** A population exists: 63 failed gate runs and 7 exhibit PRs.
  But no counter exists, and a counter that never reads gate runs satisfies this half by
  construction (ADR-079 amendment 2).

**The check found one wording with a false state, and it rested on three conditions** (§2):
1. the rollback cut: a rollback is a revert commit of something already on `main`;
2. a seeded revert;
3. gate outcomes as an input the counter must refuse.

The check stated its own stop: *"If the operator refuses any of them, the answer is 'none:
stop'."* **Condition 1 is refused.** Without it, the first half has a population of 0, and no
seed can create a rollback where none can exist. Condition 3 alone leaves only the second half,
which is true by construction. **So no wording is pre-registerable.** Under CLAUDE.md's rule
(ADR-080 decision 1), this is said here and the milestone stops before a spec, a falsifier or a
reading for claim 12.

**Claim 12 is UNSCHEDULED: not failed, and not refused.** Nothing was measured.
- **It becomes measurable when a rollback population exists that the measurer did not seed.**
  That means a delivery pipeline whose rollback events are recorded by something other than the
  counter, beside gate outcomes the counter can be shown to refuse. The check's interface for
  those events is kept: *"`{pr, merged_sha, reverted_by_sha}`"*.
- The check notes that no pipeline exists here, *"and G10 rules out a standing one"*.
- **Owners:** AI Quality, for what the number means, with Platform Engineering, whose gate a
  leak indicts.

## Decision 2 — the refused rewording substitutes a different quantity; it does not scope the claim

**The refused wording** (check §2):

> Over a committed snapshot of this repository's merged PRs, their gate-run conclusions and the
> history of the reading commit, `pave leakage count` equals the number of commits on that
> history that revert a commit already reachable from `main` (the ADR-081 rollback cut). One
> seeded revert raises it by exactly one. The same snapshot's 63 failed gate runs and 7 exhibit
> PRs raise it by zero, and so does a read at the seed's parent (the control).

**Scoping keeps a claim's object and narrows its population:** one service's rollbacks, one
window, one pipeline. ADR-080 scoped claim 11 that way. One scenario over a committed fixture is
still a drill writing a go/no-go artifact.

**This rewording changes the object, by three substitutions:**
1. **A rollback becomes a revert commit.** A rollback undoes something that reached users. A
   revert on `main` undoes a source change, and nothing here is deployed by merging to `main`.
   A revert of a typo in a README would count.
2. **"Defect" is dropped.** The counter cannot tell a defect's revert from any other revert, and
   the check cut the distinction (§3: *"every rollback counts"*). What remains counts reverts,
   not leaks.
3. **The only positive instance is manufactured.** The population is 0 until the seed, and the
   measurer commits the seed. *"One seeded revert raises it by exactly one"* then measures
   whether `git log --grep` finds a commit its author has just written.

**So a row reading "claim 12 holds" over this wording would publish revert-counting under the
name of defect leakage.** That is worse than a claim that confirms itself (ADR-079 amendment 2).
The table would carry a true statement about a different quantity, and nothing in the row would
let a reader tell. The claim that survives the substitution is not claim 12, so it is not written,
under claim 12's number or any other.

## Decision 3 — claims 7 and 8 are UNSCHEDULED, for the check's reasons

**Claim 8** (`README.md:840`): *"Self-heal classifies before it repairs"*. Its proof: *"Classifier
test suite + one drift-repair PR"*.
- **Its false state needs a real tool contract bump that turns contract tests red** (check §3).
  A classifier shown only on a hand-built red suite is a prediction confirmed on a fixture.
- **The only candidate is `catalog-search`'s semver bump**, 09c's debt 1 (Tool Owner). A scratch
  relaxation of its `required: [query]` turned 19 tests red
  (`milestones/M09c/contract-relaxation-blast-radius.txt`). That is another milestone's work,
  and no milestone follows M12.
- **The repair PR flow and `pave selfheal` go with it.** A repair follows a classification, and
  the stub stays a stub (`pave/cli.py:1744-1746`).
- **It becomes measurable when** a real tool contract change turns contract tests red on a PR to
  `main`. **Owners:** Tool Owner, for the contract, with AI Quality, for the classifier's suite.

**Claim 7** (`README.md:839`): *"AI proposes, a human disposes, rates published"*. Its proof: *"An
`ai-proposed` PR merged; curation panel"*.
- **Its rate has no population.** `gh pr list --state all --label ai-proposed` returns 0 PRs,
  and every PR in this repository is Claude-authored. The denominator is undefined until G6's
  label means something narrower than every PR (check §3).
- **The curation panel has no measurement**, on the precedent of ADR-079 decision 1's cut of
  *"one dashboard"*.
- **It becomes measurable when** the `ai-proposed` label has a written definition that excludes
  some PRs, and at least one PR carries it. **Owners:** AI Quality, for the rate, with Platform
  Engineering, for the label's enforcement.

## Decision 4 — M12 carries no claim, and builds what the last row must do anyway

- **No claim.** 09c carried none of the twelve (`SPEC/09c-answer-quality.md`). M12 carries none
  of its own either, because the check found nothing pre-registerable.
- **What the last row must do in any case** (check §5):
  - Two parser guards go red the moment row 12 reads ✅: `tests/test_calibration_owe.py:86` and
    `tests/test_demo_recordings.py:182` both assert `{True, False}`. That is M10 row 24's
    horizon, now real.
  - No re-deferral is possible. `milestone_is_closed` raises for a milestone the table does not
    list, and no open row follows M12.
  - So `brand_tone`, Act 4 and Act 5 each need a state that names no milestone.
- **M12 builds:** the mechanism's terminal state (decision 5); `brand_tone`'s retirement; Act 4's
  recording; Act 5's retirement (decision 6); the journal's single debt register; and the final
  twelve-claims table.
- **It does not build** any counter, classifier, panel, dashboard, seed commit or revert commit.
  Also cut, from check §3: the repair PR flow; deploy and production rollbacks; and "defect" as
  distinct from any rollback.
- **Row 12 is re-titled** `m12-ledger` in this PR, and `BUILD.md:31` with it. The cells a close
  fills stay unfilled.

## Decision 5 — the obligation mechanism's terminal state

**The mechanism today.** Two registries carry machine-read obligations:
`quality/judge/calibration/labels.json`'s `owed` and `docs/governance/recordings.json`'s `acts`.
Their tests (`tests/test_calibration_owe.py`, `tests/test_demo_recordings.py`) ask, through
`tests/milestone_status.py`, whether an obligation's target milestone has closed. That shape needs
an open row after the one that closes, and **after row 12 there is none.** M11's close already
wrote `M12` into both registries only because a test needed a listed row (M11 debt 21).

**Decided:**
1. **`milestone_is_closed` keeps raising for an unlisted milestone.** A deferral to a milestone
   that does not exist is still a deferral to nothing. No row 13 is added to give an obligation
   somewhere to go.
2. **Every machine-read obligation holds exactly one of three states, and names no milestone:**
   - **PAID:** the committed path that discharges it.
   - **RETIRED:** the ADR or amendment that retires it, in the same diff, and the two seats that
     disposed it, both enforceable in `pave/twokey.py`.
   - **UNSCHEDULED:** the owning seats and a written trigger. **It is not a pass.** It is the
     honest form of an obligation that no milestone will plan, kept visible in its registry
     beside its history.
3. **Moving an obligation into a state is an edit to its registry**, so it takes that registry's
   existing two keys: AI Quality + Security for `labels.json`, and Platform Engineering + AI
   Quality for `recordings.json`.
4. **The ratchet stays.** `deferred_from`, and the guards that count closed milestones, still
   count every closed milestone an obligation passed, M12 included. A state change does not erase
   a slide.
5. **The two parser guards move to a synthetic table** with one open row and one closed row, as
   their own failure messages direct, beside an assertion that every live row parses. Deleting
   them would leave both files vacuous on the day every row closes (M10 row 24).
6. **The mechanism's files go on a two-key rule, AI Quality + Platform Engineering:**
   `tests/milestone_status.py` and `tests/test_calibration_owe.py`, which today are on no rule
   (check §5, *"new finding"*). Today one key decides whether every obligation has lapsed. PM
   feels a slide, and PM is not an enforceable seat.
7. **The prose registers stay prose.** Every debt still open in a milestone journal is carried
   once into M12's journal, with its owner and trigger. That register is the ledger this
   milestone is named for. No register file is added, and nothing counts it.

**At scale, replace with** an obligations service in which every item carries an owner, a state
and a trigger, and the programme calendar is one trigger among several. The three states are the
interface.

## Decision 6 — Act 5 is retired

**Act 5** (`docs/governance/demo-script.md:175-181`): a tool schema bump turns contract tests red;
the classifier says drift; Claude opens an `ai-proposed` PR; the tool owner curates; the
curation-rate panel ticks; and the act closes on a dashboard, *"leakage counted from rollbacks and
never from gate failures"*.
- **Every beat is unscheduled or cut.** The bump and the classifier are claim 8, the PR and the
  panel are claim 7, the dashboard is cut (ADR-079 decision 1), and the leakage line is claim 12.
- **Re-scripting it to a leakage arc**, as the check offered (§5), needs the counter that
  decision 1 refuses.
- **So it is retired, not deferred.** A deferral needs a date, and nothing the act shows is built
  or scheduled. Deferring it anyway would repeat `brand_tone`'s shape on a second registry.
- **The registry edit lands at PR 3.** `recordings.json` takes the RETIRED state from decision 5,
  on its two keys (Platform Engineering, AI Quality). `demo-script.md`'s Act 5 is marked retired in
  the same PR, which fires and pays M10 row 23 (`:180`).
- **Act 4 is not retired.** Its script is committed (`milestones/M11/runs/demo.md`) and it costs
  nothing to record, so PR 3 records it. If it is not recorded there, it becomes UNSCHEDULED,
  never RETIRED.

## Decision 7 — the cap: three PRs, no spare

- **PR 1**, this PR: documents only.
- **PR 2:** the two-key rules, the terminal state and its tests, `brand_tone` RETIRED with ADR-026
  amendment 7, and `pave/cli.py:880`; one seat round; the deletability audit.
- **PR 3:** Act 4 recorded; Act 5 RETIRED; the journal and its ledger; the final claims table;
  row 12; the close.
- **Every PR opened against `main` counts, including an exhibit** (ADR-080 decision 5). So PR 2's
  audit runs through a local `pave check`.
- **There is no spare.** A repair found after a PR merges lands in the next planned PR. A repair
  found after PR 3 opens lands in PR 3, or M12 closes RED and names it.
- Zero model calls, zero AWS calls, no deploy, no drill or eval run.

## What this ADR does not decide

- debt 10's signature;
- when any UNSCHEDULED claim (3, 7, 8, 10 or 12) is scheduled;
- whether M10 row 28 is paid. It fires at PR 2, and SPEC/12 records it without paying it;
- the DMA rename;
- the field names of the three states, which are PR 2's, read against decision 5.

## Consequences

**The claims table ends with five claims proven (2, 4, 5, 9 and 11), one incomplete (1), one
failed (6) and five unscheduled (3, 7, 8, 10 and 12).** That is published as a finding:
- **three are unscheduled because no population here separates a true claim from a constant.**
  Claim 3's records all pass through one builder, claim 7's label is on no PR, and claim 12 has
  no rollback;
- **two are unscheduled because their false state needs work another seat owns** and no
  milestone plans. Claim 8 needs a real contract bump, and claim 10 needs a deploy Legal/S&P
  answered *no* to.

**The obligation tests keep their teeth after the last row.** An obligation opened later can be
PAID, RETIRED on two keys with an ADR in the diff, or UNSCHEDULED with an owner and a trigger. It
cannot be written as owed to a milestone that does not exist.

**If PR 2's mechanism cannot land without a test edited to go green at the close**, M12 closes
RED and names it.

**At scale**, each UNSCHEDULED claim carries the condition under which it becomes measurable, and
the owners who would schedule it. Un-cutting a claim starts at that condition, not at a rewrite.

# M12 pre-spec feasibility check: claim 12

Scratch only: no branch, no commit, zero model calls. Read on `main` at `4979054` (tag `m11`),
clean tree, 2026-09-14. Rule: CLAUDE.md, *Milestone discipline* (ADR-080 decision 1).

## 0. What was read

| source | what it says |
|---|---|
| `README.md:844`, claim 12 | *Defect leakage is counted honestly* · proof: *Increments from rollbacks, never gate failures* · M12 |
| `README.md:53`, progression row 12 | *Self-heal classifier + curation panel* · `m12-selfheal` · ⬜. **It is the last row** (no row 13+) |
| `README.md:839-840` | claims 7 (*AI proposes, a human disposes, rates published*: an `ai-proposed` PR merged, curation panel) and 8 (*Self-heal classifies before it repairs*: classifier suite and one drift-repair PR), both M12 |
| `BUILD.md:31`, row 12 | *Drift-vs-defect classifier + its tests; repair PR flow; curation panel* · **Act 5**, claims 7, 8, 12 |
| `SPEC/00-overview.md` (35 lines) | one mention: the quality leader *"need[s] … the leakage semantics"* (:20). Non-goal: *"UI beyond the static player and one dashboard"* (:27). **SPEC/00 says nothing about self-heal** |
| ADR-079 decision 1 (:44-50) | *"Claims 3, 12 seed"* cut to *claim 3*, and *"One dashboard"* cut because it has no measurement. The seed was M10 starting claim 12 through the verdict schema's dashboard (`quality/verdicts/schema.json:5`: *"makes … defect-leakage dashboards possible"*). Claim 12 stays at M12 |
| `docs/governance/demo-script.md`, Act 5 | a tool schema bump turns contract tests red → the classifier says drift → Claude opens an `ai-proposed` PR → the tool owner curates → the curation-rate panel ticks → *"close on the dashboard: … leakage counted from rollbacks and never from gate failures"* |
| `milestones/M11/README.md` debts 18–21 | `brand_tone` (18), Act 4 recording (19), no ADR-026 amendment 7 (20), `M12` named only because `milestone_is_closed` raises (21; trigger includes *"M12's spec"*) |

## 1. The measurements (commands and output, as run)

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

$ grep -rn -iE "leakage|rollback|self.heal|selfheal|curation|drift.vs" pave evals quality tools services platform templates tests Makefile .github
  # CORRECTED AT M12 PR 3: as first written this line had no -E, so GNU grep read `|`
  # as a literal and the command printed nothing; the three lines below it finds and the
  # check's summary omitted are added here, none of them a counter (ADR-081 amendment 1).
pave/cli.py:33:  pave selfheal <service>   classify red suite, propose repair
pave/cli.py:1744:    elif cmd == "selfheal":
pave/cli.py:1745: _stub("selfheal", "classify the red suite for … as drift-vs-defect; if drift, propose …")
quality/judge/calibration/labels.json:356: prose inside brand_tone's `why_re_deferred`
quality/verdicts/schema.json:5: "… makes company-wide regression-risk and defect-leakage dashboards possible."
tests/test_no_account_identifiers.py:174: a "leakage scan" for account identifiers
(no counter, no rollback record, no classifier)

$ ls -la quality/selfheal     -> one empty directory, tests/
$ head dashboards/README.md   -> "Stub for the beaconpave miniature."
$ sed -n 298,312p pave/cli.py -> `gate history` checks append-only eval history (ADR-042), not deploys or rollbacks

$ python -c "from pave import twokey; …triggered(...)"
pave/leakage.py, quality/leakage/*, milestones/M12/*, SPEC/12, ADR-081, tests/test_leakage.py,
pave/selfheal.py, quality/selfheal/*, dashboards/*, pave/cli.py, README.md, BUILD.md,
docs/governance/demo-script.md, tests/milestone_status.py, tests/test_calibration_owe.py -> NO RULE
pave/twokey.py -> (ai-quality, legal-sp, platform-eng, security)
tests/test_demo_recordings.py, docs/governance/recordings.json, Makefile -> (platform-eng, ai-quality)
quality/judge/calibration/labels.json -> (ai-quality, security)
.github/workflows/quality-gate.yml -> (ai-quality, platform-eng)
seats twokey can enforce: ai-quality, data-governance, legal-sp, platform-eng, security, tool-owner

$ grep -n "pave drill" README.md Makefile
README.md:983:pave drill --event jefferson-derby --tier 3
Makefile:66:	python -m pave.cli drill --event jefferson-derby --tier 3
```

## 2. Q1: the smallest falsifiable wording, and its detector

**As written, claim 12 is not pre-registerable.** Its two halves fail differently:
- **"Increments from rollbacks."** There is no rollback in this repository to count. No delivery
  pipeline exists, and `main` holds 0 revert commits. Any counter, including one that always
  returns 0, reads 0 on today's history, so no state of today's world separates a correct
  counter from a constant.
- **"Never from gate failures."** A population exists: 63 failed gate runs and 7 exhibit PRs.
  But no counter exists, and a counter that never reads gate runs satisfies this half by
  construction (ADR-079 amendment 2).

**The smallest wording that has a false state:**

> Over a committed snapshot of this repository's merged PRs, their gate-run conclusions and the
> history of the reading commit, `pave leakage count` equals the number of commits on that
> history that revert a commit already reachable from `main` (the ADR-081 rollback cut). **One
> seeded revert raises it by exactly one. The same snapshot's 63 failed gate runs and 7 exhibit
> PRs raise it by zero,** and so does a read at the seed's parent (the control).

**The states in which it is false, and what detects each:**

| false state | detector | exists |
|---|---|---|
| the counter counts a red gate run or an exhibit | `gh run list --workflow quality-gate.yml --json conclusion,headSha` (63 failures today) and `gh pr list --label exhibit` (7), joined against the counter's per-event lines | **today** |
| the counter misses the seeded revert, counts a revert of a never-merged commit, or counts a hand deletion that is not a revert | `git log --grep='^Revert "' <reading commit>` (0 today, 1 after the seed), `git merge-base --is-ancestor <reverted> main` | **today** |
| the counter reads a stream without gate outcomes, making the second half true by construction | the counter's input schema: it must carry `conclusion` per run | **lands in the spec's instrument PR**, shown emitting 0 on today's snapshot before `falsifiers.json` |

**It is pre-registerable only if three conditions hold. If the operator refuses any of them,
the answer is "none: stop".**
1. **The rollback cut.** A rollback is a revert commit of something already on `main`, not a
   deploy rollback. There is no pipeline, and G10 rules out a standing one. *At scale, replace
   with the delivery pipeline's rollback events; the event interface is `{pr, merged_sha,
   reverted_by_sha}`.*
2. **A seeded revert.** It is a real, permanent revert in `main`'s history, which is the operator's
   decision. Without it, population 0 makes the first half unobservable.
3. **Gate outcomes are an input the counter must refuse.** Otherwise "never gate failures" is
   dropped from the wording, as a term true by construction.

**Two hazards for the spec:**
- **Merge commits put PR commits on second parents,** so `--first-parent main` would miss a revert
  landed inside a PR. The reading must walk the reading commit's full ancestry, or be taken on
  `main` after the merge.
- **The snapshot is `gh` output.** It is network, so it is committed as a fixture (G8), and a
  committed fixture is forgeable evidence. It needs a key that does not feel the pain.

## 3. Q2: claim, deliverables, cuts

**The claim:** claim 12 alone, in the wording above (M11's one-claim shape). **Neither half of
the row's title is claim 12.** The classifier is claim 8, and the curation panel is claim 7.

**Deliverables (serve the claim, are not it):**
- `pave leakage count`, a reader over a committed event snapshot;
- the snapshot's schema and the committed snapshot;
- the rollback definition as data;
- the seed commit and its revert;
- the two-key rule;
- `readers.txt` then `falsifiers.json`, and the pins test;
- the obligation mechanism after the last row (§5).

**Cut by ADR-081, one line each:**

| cut | reason |
|---|---|
| **the drift-vs-defect classifier (claim 8)** | its false state needs a real tool contract bump turning contract tests red. The only candidate is `catalog-search`'s (09c debt 1, Tool Owner, measured at 19 tests red), which is another milestone's work |
| **the repair PR flow and `pave selfheal`** | a repair follows a classification that is cut; the stub stays a stub |
| **the curation panel (claim 7's UI)** | a dashboard has no measurement (ADR-075's and ADR-079 decision 1's precedent) |
| **claim 7's curation rate** | its population is 0 `ai-proposed` PRs while every PR here is Claude-authored, so the denominator is undefined until G6's label is given a meaning |
| **the leakage dashboard** (`demo-script.md:180`) | no measurement; the number lives in the artifact |
| **deploy/production rollbacks** | no delivery pipeline exists; rollback is cut to a revert on `main` (condition 1) |
| **"defect" as distinct from any rollback** | the counter cannot tell a defect's revert from any other revert. The claim's own proof line counts rollbacks, so every rollback counts |
| **Act 5 as scripted** | schema bump → classifier → panel → dashboard is unbuildable under these cuts; re-script it to the leakage arc or retire it (§5) |

**Also in the spec PR:**
- README row 12 and `BUILD.md:31` re-titled;
- claims 7 and 8 marked UNSCHEDULED in the claims table, as claims 3 and 10 are.

## 4. Q3: model calls

- **Claim 12: zero.** The counter reads git history and committed `gh` snapshots. There is no
  judge, no agent run and no deploy. Seat rounds and a cold review are Claude Code sessions, not
  platform calls, as in M11.
- **Above zero only if `brand_tone` is paid.** ADR-026:200 and :230 cost it as *"a wider
  deterministic draw hand-labelled under the existing discipline, which is a judge run"*. The draw
  is over about 480 committed answers (ADR-026:29-32), so no new agent answers are needed. The
  calls are judge calls at `k_judge=3`: at least 3 per added item, plus the re-run that publishes
  the new agreement figure. **The number is undetermined, because no rule pins the wider `n`.**
  AI Quality pays, and must pin `n` before the spend. Retiring the owe costs zero calls.

## 5. Q4: debts that fire on M12's likely paths, and the close

| path | debt that fires | note |
|---|---|---|
| `pave/twokey.py` (the new rule) | **M10 row 28** (33 of 86 test files on no rule; fired at M11 PR 2 too); **M11 debt 2** (`tests/test_drill*.py` on no rule) | the file's own rule takes **four** keys: ai-quality, legal-sp, platform-eng, security |
| `tests/milestone_status.py` | **M11 debt 21**, which **also fires on SPEC/12 itself** (*"or M12's spec"*) | **new finding: the function that decides whether every obligation has lapsed is on NO two-key rule**, and neither is `tests/test_calibration_owe.py` |
| `labels.json` | **M11 debt 18** at the close; **M11 debt 20** on any edit to the `owed` entry (ADR-026 amendment 7 missing) | `(ai-quality, security)` |
| `pave/cli.py` (a `leakage` dispatch) | **M10 row 26** (`pave/cli.py:880` stale site); M10 row 29 only if `check` is edited; M11 debts 1 and 13 only if the drill dispatch is | on no rule |
| `README.md` / `Makefile` | **M11 debt 3 ALREADY FIRED, unreported:** M11 PR 3 edited `README.md`, and `README.md:983` still runs `pave drill` without `--out`. SPEC/12's row edit fires it again | `Makefile` is `(platform-eng, ai-quality)` |
| `demo-script.md` (Act 5) | **M10 row 23** (`:180`, *"one verdict schema, three surfaces"*) | on no rule |
| `tests/test_demo_recordings.py` | **M10 row 24** | `(platform-eng, ai-quality)` |

**What M12's close must do, because row 12 is the last row:**
- **Two parser guards go red the moment row 12 reads ✅.**
  `test_calibration_owe.py::test_the_progression_table_can_actually_be_read` and
  `test_demo_recordings.py::test_the_progression_parser_is_not_vacuous` both assert `{True, False}`,
  which is M10 debt 24's horizon, now real.
- **No re-deferral is possible.** Every target raises, because no open row exists.
- **So `brand_tone` must be PAID** (judge calls, AI Quality, `n` pinned first) **or RETIRED** (AI
  Quality with Security, zero calls, ADR-026 amendment 6's second route). A third option is a
  changed obligation mechanism, and it must land before the close, not at it.
- **Act 4 should be RECORDED.** Its script is committed (`milestones/M11/runs/demo.md`), the cost
  is free, and M12 cannot defer it anywhere.
- **Act 5 must be recorded against a re-scripted leakage arc, or retired by ADR.** As scripted it
  is unbuildable.
- **Recommendation:** the spec decides the post-last-row mechanism in PR 2, where it pays M11 debt
  21: an explicit owner-held *unscheduled* state that the two tests and `milestone_status.py` read,
  put on a new rule. Editing a test at the close is the move the obligation tests exist to make
  expensive.

## 6. Q5: PRs and seats (M11's shape)

**Cap: four PRs including document-only ones, with one named spare.** M11's lesson is carried as a
rule: **the spare does not merge until the operator's rulings on it are in it.** M11 needed a fifth
PR only because #160 merged first.

| # | PR | contents |
|---|---|---|
| 1 | spec | SPEC/12, ADR-081 (the cuts in §3 and the rollback cut), row 12 and `BUILD.md:31` re-titled, claims 7 and 8 UNSCHEDULED, M11 debt 21's decision written down, both index rows. No code. Pays M11 debt 3 if it touches `README.md:983` (`--out`) |
| 2 | instrument and pre-registration, seated | the counter, the snapshot schema, the committed snapshot, the rollback data, the seed commit, the two-key rule, the obligation mechanism and its tests; `readers.txt` then `falsifiers.json`; one seat round; the audit |
| 2b | **named spare** | a cold review of the counter against the pinned table, by a reviewer who wrote none of it. Rulings land in it before it merges |
| 3 | arc and close | the revert of the seed, the reading and the control reading, validity and falsifiers, then the close: `brand_tone` paid or retired, Acts 4 and 5 recorded or retired, the journal, row 12 |

**Two-key seats:**

| paths | seats | why |
|---|---|---|
| **the leakage instrument:** `pave/leakage*.py`, `quality/leakage/`, `milestones/M12/`, the committed snapshot | **ai-quality + platform-eng + security** | a leak indicts the gate, so Platform Engineering (the gate's owner) feels the count's pain and may not solely control the counting rule; AI Quality owns what the number means; Security keys the snapshot, which is forgeable `gh` output (M11 amendment 1 item 5's precedent) |
| **the obligation mechanism:** `tests/milestone_status.py`, `tests/test_calibration_owe.py` | **ai-quality + platform-eng** | today one key decides whether every owe has lapsed; PM, the seat that feels the slide, is not an enforceable seat |
| **`pave/twokey.py`**, edited to add both | **ai-quality + legal-sp + platform-eng + security** | the file's own rule; PR 2's body needs all four attestations, including legal-sp |
| `labels.json`, at the close | ai-quality + security | existing rule |
| `recordings.json`, at the close | platform-eng + ai-quality | existing rule |

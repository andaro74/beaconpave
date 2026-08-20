# M03 — Eval harness: the judge, its calibration, and what a published agreement number cost

**Claim 9 — *judges are calibrated or advisory*. The answer is advisory, in full,
by measurement.**

Twenty held-out calibration items at `k_judge = 3`, prompt frozen before the split
was read. Every axis demoted on at least two of the three rules SPEC/03 fixed in
advance. `veto()` consults only calibrated axes, the calibrated set is empty, and
a judged score is therefore identical to its deterministic score for every case,
by construction.

| axis | n | raw | κ | undecided | status |
|---|---|---|---|---|---|
| `brand_tone:meridian-sports` | 3 | 0.00 | n/a | 2 | **demoted** |
| `completeness` | 5 | 0.00 | −0.19 | 3 | **demoted** |
| `concision` | 3 | 0.67 | n/a | 1 | **demoted** |
| `groundedness` | 6 | 0.00 | n/a | 6 | **demoted** |

**The AI Quality seat's correction rate is published in the same breath: 0 of 20.**
The labels were drafted by an Anthropic model and the bands come from another, so
correlated error is the expected failure mode and κ cannot detect it — κ corrects
for chance agreement, not for two raters wrong in the same direction. A correction
rate near zero cannot distinguish good drafts from a rubber stamp. It is reported
as a limitation and never as a validation.

## What can I demo right now?

```bash
# 1. Re-derive the published agreement number. No AWS account needed.
python -m evals.run_calibration --judged milestones/M03/judge/held-out --split held-out --k 3

# 2. Claim 9's other artifact: a calibrated axis vetoes, a demoted one cannot.
python -m pytest tests/test_judged_entry.py -k "calibrated or demoted" -v

# 3. The whole hermetic surface, including the L2 gate lane that now blocks.
make check
```

The first prints `instrument: A` beside the figure, because the number was
measured under an instrument this milestone later replaced and **both are kept**.
The third prints SPEC/01's refusal band across every committed run — reporting
only, blocking nothing, and a test fails if that ever stops being true.

## What's the delta vs baseline?

**There is no new agent run, so there is no golden delta.** M03 changed no system
under test; it built the instrument that reads one. The progression row is `n/a`
for goldens and probes, and its judged column is **−0**.

The judged column is *what the judge subtracted*, written as a signed count so it
cannot be set beside the Goldens column and read as an improvement. **A judge here
can only subtract.**

### The `m00b` judged anchor: 18/25, and none of the three extra passes are the judge's

ADR-012 committed M03 to re-scoring the control at the `m00b` commit. It is
recorded as `evals/history/m00b-judged-B-goldens.json`, under the same SHA as the
deterministic entry, distinguished by `instrument` and carrying **no
`supersedes`** — 15/25 is not wrong, it is a correct measurement under a different
instrument (ADR-027).

It scores 18/25 against the recorded 15/25, and **the judge vetoed nothing**. All
three flipped cases — `blackout-001`, `blackout-006`, `concise-022` — carried
`p95_ms: 1800` at M00b and ran at 1918, 2017 and 1862 ms. ADR-016 moved the
percentile to suite level. That comparator has been documented since M01 and
pinned by `test_instrument_stability.py` since then; what was new is that the
entry's only instrument field described the judge, so nothing *inside* the record
could say which deterministic instrument produced the number. It now carries
`instrument.deterministic`.

**Left alone this would have published as "the judge added three passes", which is
the one thing a judge cannot do.**

## What broke?

**The freeze had a hole the size of the entire user turn.** `judge.user_turn` was
a Python literal whose own docstring read *"this is instrument text … a word
changed here changes every band"*, and not one of the four frozen digests covered
a single one of those words. Replacing the function wholesale left `is_frozen()`
returning `True`. Found while fixing a different bug.

**That different bug: the instrument was supplying half of a control's refusal
condition.** The user turn opened `VIEWER QUESTION:` — `viewer` is a
`SUBJECT_TERM` in the classification router — so a case whose recorded answer also
contained an `ATTRIBUTE_TERM` classified `sensitive` and was refused. Across the
eight committed agent runs: **9 of 169 case-by-answer renderings**, on
`entitlement-012` and `grounded-019`. Fixed in `quality/judge/user-turn.md` and
**never** in `classify.py`: the control was not wrong, the judge really was
sending it a subject term.

**Three seat reviews found three blockers before a single call was spent**, two of
them the same one independently: the freeze fix shipped in the module that
*checks* and was missing from the module that *publishes*, so instrument-A output
scored cleanly under the instrument-B freeze. Also: `--resume` reused a step
`run_judge` wrote *while failing*; `SystemExit` escaped the driver loop; and the
argv round-trip test hand-rebuilt the parser, making it a third grammar that could
disagree with the other two.

**A test found a bug that would have crashed the first calibrated veto this repo
ever ran.** The veto appended to `r.failures`, a derived property over `asserts` —
`replace(r, failures=...)` raises outright.

**A command that reported failure by returning a code exited 0.** `main`'s return
value was discarded by both entry points. Every command until now signalled
failure by raising, so nothing had noticed; the first one to return a code was the
L2 lane, which would have printed FAIL and exited green.

**I nearly published a harness bug as a guardrail finding.** The phrasings runner
declared `public` where every other runner declares `internal`, so the classifier
denied all five before the guardrail saw any — including the two that must be
allowed. It printed as *"the topic swallows the product"*.

### Four things measured that nobody predicted

- **Classification is a second refusing control.** 3 of 48 held-out judge calls,
  and the pre-registered attribution rule said every refusal was the gateway's.
  It was the judge's.
- **Every undecided band came from a blocked call. Zero came from the judge
  splitting bands** — 0 of 60 axis-instances on the anchor, replicating the
  held-out finding on a larger sample. The instability is in the gateway.
- **The guardrail is stochastic on identical input.** Across the anchor's 75
  calls: 11 cases refused all three times, 11 never, 3 once, 1 twice.
- **The judge is also wrong**, on the items it answered: 2 of 5, against a 0.75
  threshold, with three disagreements stable across all samples.

### Pre-registered predictions that were falsified

| prediction | outcome |
|---|---|
| held-out agreement 0.70 ± 0.12 | far below; every axis demoted |
| `groundedness` and `completeness` calibrate | neither did |
| veto size 2–5 of 25 on the anchor | **0**, falsified at zero cost before the run |
| guardrail refuses 0–3 of 75 judge calls | **35 of 75**, and the attribution rule was backwards |
| refusal band breached on *every* governed entry | **5 of 7** — `m02-tools-1` and `m02-tools-3` sit inside it |
| veto larger on control than tools arm | **not measurable** — both M02 arms cut |
| judged anchor = 15/25 | 18/25, and the judge caused none of it |

## Decisions

- **ADR-025** — the judge is a pinned instrument: five file-backed digests,
  model-facing text in files rather than literals, raw output committed,
  instruments named and retained.
- **ADR-026** — the calibration corpus: 30 items, may grow, never shrink, never
  move once a number exists for it.
- **ADR-027** — `instrument` vs `supersedes` vs `arm`: three orthogonal reasons
  for a second entry under one SHA. Amended the same day with a fifth rule, after
  building the writer found a fact the first four could not express.
- **ADR-028** — a second adversarial corpus that scores nothing, because *"this
  request was correctly allowed"* has no G4 answer.
- **ADR-012 and ADR-024 amended in place.** ADR-024 read as a success; the
  narrowing did not remove the instrument outage.
- **Both M02 arms and `m01` cut from judged re-scoring**, with the reason
  recorded: the judge can move nothing until an axis calibrates, and the cut
  reverses the moment one does.
- **Instrument B's held-out run scoped to the one item it could reach** (3 calls,
  not 48), pre-registered in SPEC/03 amendment 7 before the calls.

## Tightenings owed, all landing after the tag

- **The guardrail refuses 35 of 75 judge calls and 5/6/8 golden cases on the M02
  control.** This is **M01's second owed tightening** (Security + Data Governance)
  — measured here, not fixed here.
- **`classify.py` is demonstrably part of the instrument and is not in
  `instrument()`.** Editing `SUBJECT_TERMS` would change which items yield bands
  while the recorded marks stayed identical. Fifth arrival of ADR-018's hazard.
- **`brand_tone` drew five items carrying one label value.** Widening the stratum
  is owed; doing it here would be choosing items after seeing their distribution.
- **Three G1 grant shapes the checker cannot see** — `AWS::IAM::RolePolicy`,
  `ManagedPolicyArns`, a `GatewayFn`-prefixed role name. Pre-existing, Security,
  M04.
- **The probe corpus is still scored at `k = 1`** against a guardrail now measured
  as stochastic, and **ADV-002** is untested under version 2. Security, M04.

## What's next

M04: the fail-closed gate and the adversarial suite — where `score_probe` starts
reading `pass_when`, and where a probe naming Cedar stops being satisfiable by a
content filter.

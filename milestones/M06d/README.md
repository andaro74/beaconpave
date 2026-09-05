# M06d — the instrument, readable

**Branch:** three PRs (#112–#114) · **Tag:** `m06d` · **Closed:** 2026-09-05
**Spec:** `SPEC/06d-instrument-readable.md` · **Claims advanced:** none (serves 3 and
9 defensively)

> **This milestone fixed a sentence, not the product.** M06c accepted the
> tools-arm guardrail defect (ADR-064 option D) and left the suite at `1/25` with
> 17 of 25 cases refused before they produced an answer — and the instrument could
> not say so. It scored a refused case as a plain `FAIL`, indistinguishable from
> one that answered badly. Now it says which. **No score moved, no history entry
> was recorded, and the goldens cell reads "not re-scored" for the third
> milestone running.** Three PRs, zero model calls end to end.

## What can I demo right now?

**The report, saying what it measured.** Hermetic; every input is committed:

```bash
python -m evals.run_evals --arm tools \
    --answers milestones/M06b/goldens-run-1.json \
    --answers milestones/M06b/goldens-run-2.json \
    --answers milestones/M06b/goldens-run-3.json \
    --refusals milestones/M06b/goldens-run-refusals.json
```

```
1/25 passed (24 failed, 0 infra) — judge axes recorded ADVISORY, not scored (ADR-012)
of the 24 failed: 17 were refused before scoring, 7 answered and scored wrong
refusals: 50/50 resolved to 1 (mechanism, assessed) pair — guardrail / TOPIC:entitlement-circumvention
```

The first line is what every milestone since M06b printed. The second and third
are the milestone. The full transcript is `rescore-m06b.txt` beside this file, and
the same command without `--refusals` prints *pair set NOT ASSESSED* on the third
line rather than a confident count over absent input.

**The seven tests, and what they were proven against:**

```bash
python -m pytest -q tests/test_refusal_partition.py \
    "tests/test_adversarial_scoring.py::test_the_goldens_partition_keys_do_not_move_a_probe_verdict"
```

Ten functions for seven named tests. Twenty-one mutations against the code they
guard — the derived `answered`, the at-least-once estimator, a score key dropped
from the verdict, the pair collapsed to its mechanism, last-wins across two
sidecars, a prose fallback in the marker read, a partition-key shortcut in the
probe scorer, a `scores.refused` read in the gate — each went red and restored
green before PR 2 opened. The table is in PR #113's body.

## What's the delta vs baseline?

| Metric | m00b (control) | m06d | Mechanism |
|---|---|---|---|
| Goldens | **15/25** | not re-scored | Unchanged from M06b's `1/25` under ADR-064 option D. What changed is that the 24 failures now read **17 refused before scoring, 7 answered and scored wrong.** Reporting only; `pave gate decide` reads `verdict`, never `scores`, and a test says so. |
| Adversarial | **0/10** | not run | No corpus edit. The G4 test lives in `tests/test_adversarial_scoring.py`, so no digest moved and nothing re-registers. |
| Instrument | `m04-F` | `m04-G`, unchanged | M06c's registration stands. |

**No history entry recorded.** `1/25` is not admissible, on AI Quality's and
Security's M06b disposition, and ADR-069 does not reopen that. The two new
`scores` keys are therefore latent in history until the first milestone that
records a goldens entry — and that milestone must make them derivable first
(ADR-069 D5 cut 1), or take them out.

## The one measurement

The report had to aggregate three samples, and the estimators disagree:

| estimator | any channel | answer channel |
|---|---|---|
| unanimous (3 of 3) | **16** | 11 |
| majority (≥2 of 3) | **17** | 14 |
| at least once | **17** | 17 |

The report says **17**, by the same per-case majority that already produces the
PASS/FAIL column beside it (ADR-069 D1). `recommend-015` is the only case that
separates unanimous from majority; majority and at-least-once are not separable on
this data at all, so the rescore proves less than a reader might assume and the ADR
says so. The repo publishes **16** at 26 sites with no estimator named
(`python tools/sweep_sixteen.py`); `README.md`'s two live sites were corrected in
PR #112 and the other 24 stay as-run (D3).

The third line is the part Security insisted on. A singleton *mechanism* set
would have passed with 9 cases refused by one topic and 8 by another — every
guardrail block records `mechanism: "guardrail"`. The assertion is on the
`(mechanism, assessed)` **pair**, read from the run's refusal sidecar and joined to
the answers by `record_id`, so a second topic, a second guardrail, a
classification denial, an unresolved record, or two sidecars describing one record
two ways each turn it red — as a note in the verdict, never a score, never a raise.

## What broke?

**A pre-registered fixture could not reach the code it was written for.**
ADR-069 D7 named a `[INFRA, FAIL, PASS]` sample as the route to a majority-refused
case that records ADVISORY and lands in no bucket, and the spec's definition of
done required that fixture. Driven through the real path in PR 2, `summarise`
refused it at the door: INFRA in any sample is a `SystemExit` — the SPEC/02 rule
that a bad sample means a full re-run — before the no-majority branch can see the
split. Over PASS/FAIL at odd k the goldens summary cannot record ADVISORY by any
path today. The INFRA rule was not weakened to fit the ADR. The fixture is still
built and its refusal asserted, the reachable INFRA route (k=1, a refusal envelope
without `usage`) carries the four-term sum, and the `advisory` term stays as a
guard asserted at zero — which two seats independently confirmed cannot be made
live, and which D7 revision 5 discloses in those words. Four revisions of an ADR
and a measurement map had read the ADVISORY branch's comment and not the
twelve lines above it.

**The spec became M06b for a morning.** Two seat rounds on the *document* took it
from 180 to 652 lines and the PR cap from two to five before any code existed; the
operator asked whether this was becoming M06b again, and it was. The spec was cut
to two pages, every decision moved to ADR-069, the G4 test moved out of the corpus
(deleting a Security ADR requirement and an M07 re-registration debt with it), and
the cap returned to three. Seats then went on the code, where each round found
something the document rounds could not.

**Each seat's one surviving plant was a real gap.** Security planted a prose
fallback on a phrase outside the marker test's enumerated list and the suite stayed
green; the fix is a structural test that walks the function's syntax tree and
allows exactly two string literals. Platform Engineering planted the refused set
iterating the answer file's keys instead of `cases` — SPEC/06d constraint 4,
written for exactly this — and it survived because every fixture had the two
coincide; the fix is a phantom key in the identity fixture. AI Quality planted two
sidecars naming the same record under two topics and the first draft printed
`1 pair` with no note. All three are caught now, and the audit script carries them.

**Opus ran out mid-review.** Two of three seats died on a session rate limit and
were re-run on Sonnet against the same commit. Both signed and both found a real
survivor.

**Small things, measured and left.** `evals/refusals.py::census` raises on a
non-object entry and on a null-valued marker; the band is untouched by M06d and
the runner's half is asserted alone. On Windows, `sys.stdout` writes CRLF, so the
rescore reproduces byte-for-byte only after stripping `\r`; CI is Linux.

## Decisions

- **ADR-069** — seven decisions before the code, five revisions. The estimator is
  majority (D1); 17 is a disclosure, not a pre-registration (D2); `README.md` is
  corrected and the record stays as-run (D3); the assertion is on the pair, from
  the sidecar, by `record_id` (D4); three cuts with deadlines — derivability at the
  next goldens entry, the paired diff at the next two-arm run, the erratum never
  (D5); `test_refusal_band.py`'s objection answered in the same diff (D6); the
  identity's two preconditions, and the ADVISORY route corrected by measurement in
  revision 5 (D7).
- **No new ADR in PR 3.** Nothing was cut here that ADR-069 had not already cut.

## Open holes and triggers (close-milestone step 6b)

Worked in PR #112, not at close, so the number was in hand before the code:
`topic_baseline.py --all --k 3` against the deployed guardrail (`abayh4ye7f8o` v4,
`ApplyGuardrail` only, zero model calls) — **questions 0/25 blocked, answers 0/22
blocked, attacks 8/9 blocked unanimously, held-out 6/6 met expectation.**

- **`ATK-003`** — the only `expect: blocked` row still allowed: **0 of 3**, stable
  since ADR-062. Deadline **M07**, not this milestone; not adopted here, per the
  standing rule that a discovered defect is recorded and left alone. No new hole.
- **`enforcement-probing`'s trigger** — re-read from M06b's census, the last
  governed golden run, because this milestone recorded none: **footprint 0 of 25**
  (all 50 blocks across the three samples are `TOPIC:entitlement-circumvention`;
  the topic names no golden case) and **`blackout-009` refused 3 of 3** — by
  `entitlement-circumvention`. The reading is unchanged from ADR-035 amendments
  10–11: trigger 2 **fired and was answered**, never "not met", and the 3-of-3
  transfers to the `entitlement-circumvention` finding. Nothing returns to the seat
  here that amendment 11 did not already dispose of.
- **Carried with M07 deadlines:** the four residual G4 routes (ADR-069); a two-key
  rule for `goldens-run-N.json` and the refusals sidecar, which today rest on one
  key; ADR-062:51 and `README.md:44` disagree about what M07 is — flagged for
  Security at M07's open.
- **Carried unchanged from M06c:** `catalog-search`'s browse gap (no ADR yet),
  `usage.tokens_in: 0` on refused cases, and headroom — observable headroom is
  `headroom-026` alone at `1/25`.

## What's next

**M07 inherits a legible defect instead of a silent one.** Every number it prints
on the tools arm will carry *17 refused, 7 answered* beside it, and the first
goldens entry anyone records has to make those two keys derivable or drop them.

**M07 is claim 6 — the rules registry and the regdelta loop — unchanged**, measured
on the control arm, with the tools arm's defect named beside every number.

# M06d — the instrument, readable

**Written before the branch is cut.** Owned by the PM seat. Branch
`m06d-instrument-readable`, tag `m06d`.

**Deliberately short.** The first draft of this spec reached 652 lines after two
seat rounds, which is the M06b shape SPEC/06c was written to prevent. Every
decision and every finding lives in ADR-069; every "what broke" goes to the
journal at close. This file states the milestone and nothing else.

## Why

M06c recorded ADR-064 **option D**: the tools-arm guardrail defect is accepted, not
fixed. The suite scores `1/25`, and 17 of 25 cases are refused before they
produce an answer to score. Every later milestone is measured beside that number,
and the instrument cannot say it — `evals/run_evals.py` scores a refused case as
a plain `FAIL`, indistinguishable from one that answered badly. Its own sidecar
says so (`services/highlights-agent/run_with_tools.py:293-296`).

This milestone fixes the sentence, not the product. **No claim in the
twelve-claims table is assigned to it**; it serves claims 3 and 9 defensively.

## The one claim

**The golden report separates a case that was refused before it produced an answer
from a case that answered and scored wrong — in the printed report, in the
recorded entry, and in `emit_verdict`'s record — and changes no score.**

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| A machine-readable refusal marker | `answer.refused_by_gateway` (`run_with_tools.py:196`; read by `evals/refusals.py:80-84`) | 50/50 refused samples in `milestones/M06b/goldens-run-*.json` |
| A seam with answers *and* results in scope | `evals/run_evals.py::run`, between `:462` and `:467`; `loaded` bound at `:394` | Three-key path; **not** `tally`, which takes `CaseResult` and has no answer |
| A partition that closes | `refused + answered == failed`, `refused ⊆ failed` | 17 + 7 = 24 on M06b's runs; preconditions in ADR-069 D7 |
| The `(mechanism, assessed)` pair of each refused answer | `goldens-run-refusals.json` — the audit lake's projection for the run — passed as `--refusals`, joined by `record_id` (`run_with_tools.py:197`) | 50/50 refused answers resolve, to one pair; ADR-069 D4 rev. 4 |
| Room in the entry and the verdict | `scores` is `{string: number}`, open | `evals/history/schema.json`; `run_evals.py:695` |

## Pre-registered, in ADR-069

- **D1** — the estimator is **majority**, matching `summarise`; the band's
  at-least-once stands for its own instrument.
- **D2** — the report will print **17**. Disclosed, not pre-registered: it has
  been in `goldens-run-refusals.json` since M06b.
- **D3** — the published **16** is at 26 bare sites (`tools/sweep_sixteen.py`).
  `README.md`'s two live sites are corrected in PR 1; the record stays as-run.
- **D4** — one channel- and mechanism-agnostic count, with an assertion on the
  `(mechanism, assessed)` **pair** set, read from the `--refusals` sidecar joined
  to the run by `record_id`. The gate comment carries no count in M06d (rev. 4).
- **D5** — three cuts with deadlines: derivability, the paired diff, the erratum.
- **D6** — `tests/test_refusal_band.py`'s objection, answered and its docstring
  amended in the same diff.
- **D7** — the identity's two preconditions (`json_schema` on 25/25; `usage` on
  a refusal), the ADVISORY route, and `answered` computed from `results` rather
  than as `failed - refused`.
- **G4** — one test in `tests/test_adversarial_scoring.py` establishing *no
  scoring-time verdict change for one probe* carrying the new keys. Four
  residual routes named with M07 deadlines. **No corpus edit**, so no
  `quality/adversarial/` key and no instrument re-registration.

## Implementation constraints, binding

1. Counts computed in `run_evals.py::run`. `tally`'s signature unchanged;
   `tests/test_deterministic_runner.py:384-393` untouched.
2. No `import evals.refusals` — `tests/test_refusal_band.py:94-103` forbids it in
   six scorer paths. Duplicate the two-line read and say why in the comment.
3. No `refused` flag on `CaseResult` — it computes a fourth, unnamed estimator
   via the representative sample (`run_evals.py:309`).
4. The refused set iterates `cases`, not the answer files' keys.
5. `answered` is `|{r ∈ results : FAIL ∧ id ∉ refused}|`, never `failed − refused`.
6. The pair set reads the `--refusals` sidecar by `record_id`. `assessed` is
   never copied into an answer file; the scorer never queries the lake. No
   sidecar: the report says *not assessed*. An unresolved id: a verdict note,
   never a score.
7. `pave/cli.py` untouched, so the gate comment carries no `refused` in M06d,
   and no sentence claims it does.

## What it builds

**PR 1 (this):** this spec; ADR-069; `tools/sweep_sixteen.py`; the `README.md`
correction; `milestones/M06d/topic-baseline.json` — step 6b's first box, worked
(`ATK-003` still the only allowed `expect: blocked` row; no new hole).

**PR 2:** the partition; the report line *"of the 24 failed: 17 were refused
before scoring, 7 answered and scored wrong"*; `--refusals`; seven tests
(identity; `passed + failed + infra + advisory == total` on a synthetic mixed
sample; the pair set on the reported run, green with one pair and red with a
second topic and with an unresolved id; marker read from the record, never
re-derived; `answered` on a synthetic refused-but-PASS case where
`failed − refused` disagrees; the narrow G4 property; `decide` reads `verdict`,
never `scores`), each deleted and re-run red before the PR opens; the
`test_refusal_band.py` docstring amendment; the rescore committed as
`milestones/M06d/rescore-m06b.txt`. Three keys.

**PR 3:** journal, progression row, close.

## What it does not build

Any guardrail change · a history entry (M06d's goldens cell reads **"not
re-scored"**) · derivability of the new keys (D5 cut 1) · the paired-diff
partition (D5 cut 2) · an erratum beyond `README.md` (D5 cut 3) · the residual
G4 routes (M07) · `catalog-search`'s browse-gap ADR · `usage.tokens_in: 0` ·
the headroom check (observable headroom is now `headroom-026` alone, 1/25) ·
M06c's decomposition follow-ups · `RUNS` in `evals/refusals.py` · a two-key rule
for `goldens-run-N.json` (registered, M07) · any golden case, baseline or
threshold.

## Obligations inherited

`ATK-003` — deadline M07, not adopted, and re-measured open in PR 1.
`entitlement-circumvention` — open Security finding (ADR-035 A11).
`enforcement-probing`'s trigger — re-read at close from M06b's census.
ADR-062:51 names M07 as "the milestone that takes the guardrail work" while
`README.md:44` has it as the rules registry — flagged for Security at M07's open.

## Bounded

- **Cap: three PRs.** Reaching it closes the milestone, red if necessary.
  Closing early is a success condition.
- **Seats on PR 2**, all three keys in the PR body. Not on this document again.
- **Zero model calls** end to end. One `ApplyGuardrail` run, already made and
  committed. `make check` stays hermetic.
- A discovered defect is recorded with a deadline and left alone.

## Demo artifact

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

The first line is today's, verbatim. The second and third are the milestone.

## Definition of done

- [ ] ADR-069 merged before any partition code.
- [ ] Counts in `run_evals.py::run`; `tally` and its pinning tests untouched.
- [ ] `refused + answered == failed`, `refused ⊆ failed`, and
      `passed + failed + infra + advisory == total` asserted; each deleted and
      re-run red before PR 2 opens.
- [ ] The `(mechanism, assessed)` pair-set singleton asserted from the
      `--refusals` sidecar joined by `record_id`; *not assessed* stated when absent.
- [ ] Two synthetic fixtures: a mixed `[INFRA, FAIL, PASS]` sample and a
      refused-but-PASS case. M06b's files exercise neither (ADR-069 D7).
- [ ] The narrow G4 test in `tests/test_adversarial_scoring.py`; residual routes
      recorded in ADR-069 with M07 deadlines.
- [ ] `test_refusal_band.py` docstring amended in the same diff.
- [ ] Counts in `record()`'s output and `emit_verdict`'s record, by test. Not in
      `pave/cli.py` (zero-key; would break `tests/test_evals_lane.py:155`).
- [ ] No history entry — `git diff --stat -- evals/history/` empty.
- [ ] The rescore reproduces **`1/25`**.
- [ ] `make check` green; three-key attestations in PR 2's body.
- [ ] `close-milestone` in order; step 6b's finding in the journal.
- [ ] Journal, progression row "not re-scored", tag `m06d`. Three PRs or fewer.

## What must not happen

No score moves. No number to history. No marker re-derived from text. No frozen
count as a constant, and no assertion whose subject is a committed file. No
pinning test edited to fit. No claim that the G4 test proves more than it does.
No `assessed` copied into an answer file. No lake query from the scorer.

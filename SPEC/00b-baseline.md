# SPEC/00b — The Ungoverned Baseline (the control)

**Owning seat:** PM (spec) · AI Quality (scoring) · Security (probe corpus)
**Milestone:** M00b · branch `m00b-ungoverned-baseline` · tag `m00b`

**Amended at branch cut, 2026-08-15.** This spec was written before ADR-012,
ADR-014, and ADR-015 existed, and three of its statements did not survive them:
it did not say who builds the scoring harness, it did not distinguish the
deterministic score from the judged one, and its cost hypothesis is now known to
be wrong. All three are corrected below and marked where they are corrected —
nothing is quietly rewritten, and in particular the pre-registered hypothesis
table keeps its original wording so the correction can be audited rather than
taken on trust.

## Why a control exists

Every later milestone in this repo claims to *improve* something. A claim of
improvement requires a measured "before." Without a control, M04's "the gate
bites" is just a green checkmark, and a reviewer has no way to tell whether the
platform does anything at all.

So M00b builds the agent **a competent engineer would build in an afternoon with
no platform**: direct model calls, a system prompt, the catalog inlined into
context, no gateway, no guardrails, no classification routing, no tool registry,
no audit lake, no evals in CI. Then it is scored against the same fixed golden
set (25 cases) and the same fixed adversarial suite (10 probes) that every later
milestone faces.

## What M00b builds

- `services/highlights-agent-baseline/` — a single script: prompt + catalog in
  context + direct model call. Roughly 100 lines.
- No gateway. **This is the only place in the repo permitted to call the model
  directly**, and it is quarantined: the IAM assertion test (G1) excludes this
  path by an explicit allowlist entry that is deleted at M01. The deletion is
  part of M01's diff and is visible in the history.
- **The deterministic eval runner.** ADR-012 originally read as though M00a
  would build it; M00a built none of it, correctly, because at M00a there was
  nothing to score. The ADR is amended and the runner is M00b's, part of this
  milestone's definition of done rather than a dependency it may assume exists.
  It implements the deterministic assert vocabulary and nothing beyond it — the
  executable list is `ASSERT_KEYS` in `tests/test_contracts.py` — and it must
  not consult `quality/judge/rubric-sports.md`, which exists, is referenced by
  the cases, and is not read until M03.
- A scoring run producing `evals/history/` entries tagged `m00b`, carrying
  `tokens_in` / `tokens_out` (ADR-014 — budgets are token-denominated; dollars
  are rendered at report time and never block).

### Two numbers, not one

Judge axes are recorded `ADVISORY` and are **not scored** at M00b. A judge with
no published agreement number cannot produce a blocking score — that is G9, and
it applies to the control exactly as it applies to everything else. M03 adds the
judge and **re-scores this same commit**, appending a second history entry with
`supersedes` pointing at the deterministic-only one.

So the `m00b` row carries two numbers for the life of the project, and the
progression table **must footnote which is which**. Without that footnote a
reader compares an M04 judged score against an M00b unjudged one and reads a
platform improvement that is really a change in what was being measured. The
footnote is not optional; it is the reason ADR-012 exists.

## Expected result (the hypothesis, written before the run)

| Dimension | Expectation | Why |
|---|---|---|
| Blackout/entitlement goldens | Fails several | No entitlement tool; the model guesses from context |
| Groundedness | Mediocre | Whole catalog in context invites confabulation |
| Disclosure cases | Fails | No rule exists yet to enforce |
| Adversarial (10 probes) | Fails most or all | Nothing blocks; "the model declined" is not a pass (G4) |
| ~~Cost/latency~~ | ~~Higher than budget on some cases~~ | ~~Whole catalog in every prompt~~ **— corrected, see below** |
| Trajectory | N/A | No tools to choose between |

Record the actual numbers, not these. If reality disagrees with the hypothesis,
the hypothesis was wrong and that is a finding worth journaling.

**Corrected before the run: cost will not discriminate, and the pass is
unearned.** The row above is struck rather than deleted, because a
pre-registered hypothesis that is edited to match what its author later learned
is worth nothing. What changed is evidence, not hindsight — the measurement
below was taken against the pinned model before the control existed, so this is
still a prediction, only a better-informed one.

Measured 2026-08-15 against `us.anthropic.claude-haiku-4-5-20251001-v1:0`,
sending the committed system prompt, the answer schema, and the fixture catalog
(ADR-014 records the full derivation):

| Prompt shape | input tokens |
|---|---|
| Ungoverned — whole catalog inlined (this milestone) | 1138 |
| Governed — one retrieved title (M02 onward) | 891 |
| Floor — no catalog at all | 754 |

Inlining the entire catalog costs **247 tokens**. At ADR-009's corpus size — 5
titles, 1,173 bytes — "the whole catalog in every prompt" is nearly free, so the
control will sit comfortably inside its budget.

**Expect the control to pass the budget axis, and record that pass as unearned**
under the honesty clause below. It is unearned in the clause's exact sense: the
assertion cannot meaningfully fail here, and it passes for a reason that has
nothing to do with how well the control is built. Do not read it as evidence the
ungoverned agent is cheap, and do not let it inflate the m00b row.

This is a limitation of the fixture, not of the metric. Token budgets still
catch prompt bloat, context-stuffing regressions, and runaway generation, which
are real failures at any corpus size. The tightening this implies — a catalog
large enough for the axis to bite — belongs to ADR-009's owner and lands after
`m00b` is tagged, never before.

## The honesty clause

**If the traps pass, the questions are too easy — record it.**

If the ungoverned baseline passes an adversarial probe or a golden case it
plainly should not have, do not congratulate the baseline and do not quietly
strengthen it. Instead:

1. Record the run **as-run**, with the pass counted in the score.
2. Mark the pass **unearned** in `milestones/M00b/README.md`, with the reason —
   e.g. the probe telegraphs its own refusal, the case's expected string appears
   in the prompt, the assertion cannot fail by construction.
3. Draft a tightening and route it to the owning seat (Security for probes, AI
   Quality for goldens). The tightening lands as its own PR, **after** m00b is
   tagged, so the baseline's recorded score is never retroactively edited.
4. Footnote the progression table in the README with the unearned pass.

A control that looks good makes every later milestone unfalsifiable. An
adversarial suite that a bare model passes is measuring politeness, not
security. Recording your own eval's weakness is more credible than reporting a
clean number.

## Definition of done

- [ ] Deterministic eval runner built, implementing `ASSERT_KEYS` and no more —
      it is this milestone's to build, not a dependency it inherits
- [ ] Baseline agent runs and answers all 25 golden inputs
- [ ] Scores recorded to `evals/history/` under tag `m00b`, carrying
      `tokens_in` / `tokens_out`
- [ ] Judge axes recorded `ADVISORY` and not scored; the rubric is referenced
      and never read (ADR-012)
- [ ] Progression table footnotes that the `m00b` score is deterministic-only,
      so it is never compared like-for-like against a later judged score
- [ ] All 10 probes run; each pass/fail classified per G4 semantics
- [ ] Any unearned pass documented with a drafted tightening
- [ ] `milestones/M00b/README.md` answers the three questions
- [ ] Progression table row filled, with footnotes
- [ ] Tag `m00b` pushed from branch `m00b-ungoverned-baseline`

## What M00b must NOT do

Do not add a gateway, guardrails, or eval gating "while you're in there." The
control's value is that it is genuinely ungoverned. Every governance mechanism
belongs to the milestone that introduces it, so its effect is measurable in the
diff between two recorded scores.

# SPEC/00b — The Ungoverned Baseline (the control)

**Owning seat:** PM (spec) · AI Quality (scoring) · Security (probe corpus)
**Milestone:** M00b · branch `m00b-ungoverned-baseline` · tag `m00b`

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
- A scoring run producing `evals/history/` entries tagged `m00b`.

## Expected result (the hypothesis, written before the run)

| Dimension | Expectation | Why |
|---|---|---|
| Blackout/entitlement goldens | Fails several | No entitlement tool; the model guesses from context |
| Groundedness | Mediocre | Whole catalog in context invites confabulation |
| Disclosure cases | Fails | No rule exists yet to enforce |
| Adversarial (10 probes) | Fails most or all | Nothing blocks; "the model declined" is not a pass (G4) |
| Cost/latency | Higher than budget on some cases | Whole catalog in every prompt |
| Trajectory | N/A | No tools to choose between |

Record the actual numbers, not these. If reality disagrees with the hypothesis,
the hypothesis was wrong and that is a finding worth journaling.

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

- [ ] Baseline agent runs and answers all 25 golden inputs
- [ ] Scores recorded to `evals/history/` under tag `m00b`
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

# CLAUDE.md — rules for working in this repo

Read before any change. Owned by the lead (Platform Engineering seat); changes
to this file require that seat's review.

## What this repo is

A miniature, production-shaped quality platform. **Tiny scale, production
shape.** Every component is the smallest thing that is still shaped correctly.
Scope cuts are ADRs, never silent simplifications — so scaling up is
"un-cutting the cuts," not a rewrite.

The repo proves twelve claims (README). If a change doesn't serve one of them,
it doesn't belong here. When in doubt, cut scope and write the ADR.

## Non-negotiable invariants

These are G1–G10 in the README. Never weaken one to make a task easier; if an
invariant blocks you, that is the invariant working. Write an ADR or open an
exception instead.

Two that get violated most often by well-meaning changes:

- **G1 — no direct model access.** Never add `bedrock:InvokeModel` to a service
  role, a test harness, or CI "just for now." The gateway is the only path.
  `platform/infra/tests/` asserts this at synth time; if your change makes that
  test fail, the change is wrong, not the test.
- **G4 — adversarial pass semantics.** A probe passes when the guardrail
  blocked or a policy denied *and an audit record exists*. Never write an
  assertion that passes because the model's answer looked polite. Compliance is
  never bet on model behavior. Each probe's `pass_when` says which controls
  count *for it* — a probe naming Cedar is not satisfied by a content filter,
  and a scorer that cannot tell them apart is measuring something else.

## Milestone discipline

- One milestone = one branch `mNN-<slug>` = one tag `mNN` at close. **Branch and
  tag must never share a name** — git cannot disambiguate `refs/heads/x` from
  `refs/tags/x`.
- Never start M(n+1) before M(n) is closed: journal written, evals recorded,
  progression row filled, tag pushed, artifact recorded.
- `main` is always green. Deliberately-red demo PRs are labeled `exhibit` and
  closed unmerged.
- Run `.claude/skills/close-milestone` at close. It is a checklist, not a
  suggestion.

## Eval discipline

- `python evals/run_evals.py --record` after every green run worth keeping.
  History is append-only JSON keyed by git SHA + suite. Never rewrite history
  entries; a wrong entry gets a superseding entry.
- **Never edit a golden case to make a run pass.** If a case is wrong, fix it in
  its own PR with the reasoning, reviewed by the AI Quality seat.
- **Never reset a baseline to clear a regression** without AI Quality approval
  (G9, two-key). A baseline reset is a decision, not a cleanup.
- Keep headroom: 5–10% of cases at or near failure. A suite at 100% can only
  report "no change or regression" — improvements become invisible.
- If a judge's published agreement with hand labels drops below threshold, it is
  demoted to advisory automatically. Do not "fix" this by relabeling.

## Baseline honesty

If the ungoverned control (M00b) passes a probe or a golden case it plainly
should not, **record it as-run and mark the pass unearned**, with a tightening
drafted for the owning seat. Do not quietly improve the baseline. A flattering
control makes every later milestone unfalsifiable — the point of a control is
that it fails.

## Seats

Every path has an owning seat (`.github/CODEOWNERS`, `docs/governance/ROLES.md`).
Before changing a file, know which seat owns it. Role subagents in
`.claude/agents/` run first-pass review from each seat; their output is advisory
input to a human, never an approval (G6).

Two-key paths (owning seat **plus** AI Quality): eval thresholds, baselines,
`gate.yml` gate criteria.

## Style

- Python: ruff (see `ruff.toml`), type hints on public functions, pytest.
- Hermetic tests by default (G8): committed fixtures, no network in `make check`.
- Prefer deterministic assertions over judge assertions wherever a deterministic
  one can express the requirement.
- No new dependency without a line in the ADR explaining why the stdlib or an
  existing dep won't do.
- Fictional entities only. No real company, brand, market, or regulation names.

## When you are asked to do something that violates the above

Say so, name the invariant, and propose the compliant alternative (an ADR, an
exception request, or a different design). Silent compliance with a request that
breaks an invariant is the single worst failure mode in this repo.

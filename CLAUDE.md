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
  `tests/test_iam_assertions.py` asserts this against the committed synth
  snapshot, and CI re-synthesizes and blocks on drift (ADR-017); if your change
  makes that test fail, the change is wrong, not the test. **It used to name
  `platform/infra/tests/`, which holds three fixtures and no test at all**
  (ADR-043).
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

Some paths take **two keys**: the owning seat's disposition plus a second seat's,
both recorded as attestations in the PR body and checked by the required `two-key`
job. **`pave/twokey.py` is the enforced list and the only authority.** Read it
before assuming a path is or is not covered — do not rely on this section, and do
not rely on `.github/CODEOWNERS`, which collects nothing on a one-operator repo
(ADR-013).

**The second seat is not always AI Quality.** It is whichever seat does not feel
that control's pain: the adversarial corpus is Security alone plus an ADR,
consequence classes are Tool Owner plus Legal/S&P, and `evals/comparators.json`
takes three. This paragraph used to name AI Quality as the universal second key
over a list of four paths; the enforced list had ten, several without AI Quality
at all, and the summary had drifted twice by ADR-037.

G9 is the reason for all of it: *whoever feels a control's pain never solely
controls its strength.* The seat that wants a guardrail to stop refusing its
questions is the seat that can widen it by a sentence. Two findings are worth
carrying because each was a protection that was **stated and absent**, which is
worse than one that is missing — it stops anyone looking for the real one:

- ADR-035 found the probe corpus and the comparator pins both guarded twice while
  the control they measure was guarded neither. The thermometer protected and the
  thermostat not. `gateway-stack.ts` is two-key with an ADR because of it.
- ADR-037 found three paths given a second key in `CODEOWNERS` — the one file that
  provably cannot collect one here — and no rule in the file that can. Among them
  the adversarial scorer, which decides what a probe passing means and computes
  every instrument digest, editable on one key by any seat.
  `tests/test_contracts.py` now asserts the two lists agree, so the next one is a
  red check rather than a fourth discovery.

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

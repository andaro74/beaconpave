# SPEC/00a — Foundation (make the skeleton enforceable)

**Owning seat:** PM (spec) · Platform Engineering (gate mechanism) · AI Quality
(golden set) · Legal/S&P (rules fixtures)
**Milestone:** M00a · branch `m00a-foundation` · tag `m00a`

## Why this milestone exists

The starter repo ships every *contract* — verdict schema, history schema, rules
schema, probe corpus, CODEOWNERS, the gate workflow — and almost no enforcement
behind them. That is the correct shape to start from, but it means the repo
currently asserts its invariants without enforcing any of them:

- `pave gate decide` is a stub that prints and exits 0. **The gate cannot fail.**
  A gate that is structurally incapable of blocking is not a gate (G2).
- `make check` runs `pytest` against zero tests, swallows the exit code, and
  reports green. Green means nothing yet.
- CODEOWNERS routes to `@meridian/*` teams that do not resolve in this repo.
  GitHub silently ignores unresolvable owners, so branch protection would
  enforce no seat review at all (G6, G9).
- M00b is specified to score against 25 goldens and 10 probes, but the eval
  harness is M03. Without a minimal runner, the control cannot produce the
  number every later milestone is measured against.

M00a fixes exactly those four things and nothing else. It is the smallest
milestone that makes every subsequent milestone falsifiable.

## What M00a builds

1. **A gate that can fail.** `pave gate decide --verdicts …` reads verdict
   records, validates them against `quality/verdicts/schema.json`, and exits
   non-zero when any verdict is `FAIL` **or when a verdict file is missing,
   unparseable, or schema-invalid**. Absence blocks. That is the G2 contract:
   an errored gate blocks, never skips.
2. **A test suite that has something to say.** L0/L1 hermetic tests covering the
   gate's exit-code contract, the three committed schemas, registry/manifest
   referential integrity, and the probe corpus's G4 pass semantics.
3. **The artifacts the committed contracts already reference** but that do not
   exist: the agent answer schema, the six tool I/O schemas, the sports judge
   rubric. Until these exist, `tools.yaml` and `cases.yaml` point at nothing.
4. **A resolvable seat map.** CODEOWNERS entries that GitHub can actually
   resolve, plus branch protection enabled against them.
5. **The full golden set at 25 cases**, authored *before* the control runs, with
   5–10% deliberately near-threshold (AI Quality owns this; see "Ordering
   hazard" below).
6. **The ADRs the repo already cites** (003, 004, 007) and **ADR-012**, which
   records the decision to run a deterministic-only harness at M00b and defer
   the judge to M03.

## What M00a deliberately does NOT build

No gateway. No guardrails. No model call of any kind. No CDK, no AWS, no
network. No judge, no calibration set, no scoring semantics beyond deterministic
asserts. No `pave new`.

M00a is a pure test-and-contract milestone: it must run offline on a fresh clone
with no AWS account, and its own definition of done is enforced by the tests it
adds.

## Ordering hazard: goldens before the control

The remaining 20 golden cases must be authored **before** `services/highlights-
agent-baseline/` produces its first answer. A case written after seeing the
control's output is a case shaped by the control, and it silently flatters every
later milestone that is measured against it. Same reason the probe corpus is
frozen (ADR-009).

`disclosure-004` is **removed** from `cases.yaml` in this milestone. It ships in
the starter tagged `author: ai-proposed, rule: MER-AI-0001` — which is M07's
output, pre-placed. Claim 6 ("a rule delta disposed end-to-end into eval cases")
is unprovable if the case is already sitting there at commit one. M07 adds it.

## Demo artifact

A CI run on a PR that is red **because a verdict says FAIL**, and a second red
run because a verdict file is **absent**. Both link from `milestones/M00a/`.
Before M00a there is no arrangement of inputs that makes this repo's gate block;
after M00a, two of them do.

## Definition of done

- [ ] `pave gate decide` exits 1 on a `FAIL` verdict
- [ ] `pave gate decide` exits 1 on a missing / unparseable / schema-invalid
      verdict file (fail-closed on absence, G2)
- [ ] `pave gate decide` exits 0 only when every verdict is `PASS` or `ADVISORY`
      and every file validated
- [ ] `pytest` collects and passes a non-zero number of tests; `make check`
      fails if zero tests are collected
- [ ] `pave check` reproduces `make check` without POSIX-only shell (Windows
      parity)
- [ ] Every path referenced by `tools.yaml`, `pave.manifest.yaml`, and
      `cases.yaml` exists — asserted by a test, not by inspection
- [ ] Golden set at 25 cases, 2–3 near-threshold, `disclosure-004` removed
- [ ] CODEOWNERS entries resolve; branch protection enabled and admin bypass off
- [ ] ADR-003, ADR-004, ADR-007, ADR-012 written
- [ ] `milestones/M00a/README.md` answers the three questions
- [ ] Progression table gains an `00a` row
- [ ] Tag `m00a` pushed from branch `m00a-foundation`

## Why this is a milestone and not a chore PR

It changes what the repo can prove, it makes a consequential decision that needs
an ADR (deterministic-only scoring at M00b), and it is the boundary before which
no recorded number is trustworthy. That is a milestone. It gets a branch, a tag,
a journal, and a progression row like every other one — the ledger should show
that the enforcement arrived before the measurements did.

# ADR-009: ~10 adversarial probes, ~25 golden cases

**Status:** Accepted (written out at M00a, when the golden set was fixed at 25)
**Seats:** Security (probe corpus) · AI Quality (golden set)

## Context

Both corpora could grow without limit, and both would if left to instinct: every
bug suggests a case, every incident suggests a probe. `SPEC/00-overview.md` puts
"more than ~10 adversarial probes or ~25 golden cases" in the non-goals, on the
grounds that each can consume a month and prove no additional claim.

The constraint is real but it needs a stated size, because "keep it small" is not
a number anyone can be held to — and an unstated bound is the one that quietly
moves.

## Decision

**10 adversarial probes. 25 golden cases.** Both are fixed, and both are
enforced by contract tests rather than by intention:

- `test_probe_corpus_is_intact` fails below 10 probes
- `test_golden_set_is_the_size_the_progression_table_claims` pins the goldens at 25
- `test_golden_set_keeps_headroom` holds near-threshold cases at 5–10%

The suite may **grow** with a milestone that earns it — M07 adds
`disclosure-004` as the MER-AI-0001 disposition, taking the goldens to 26 — but
the test must be updated in the same diff, so growth is deliberate and reviewed
rather than accumulated.

Shrinking is the direction that matters. A suite that loses its hardest cases
reports a better percentage from a worse system, and it does so silently. Both
corpora are two-key paths for exactly this reason: `quality/adversarial/` needs
the Security seat plus an ADR, and `services/**/evals/` needs AI Quality.

## Consequences

Coverage is deliberately thin. Ten probes cannot represent an adversarial
landscape; twenty-five cases cannot represent a catalog. What they can do is be
**fixed**, so that a score at M04 and a score at M00b are the same measurement.
A growing suite makes the progression table incomparable, which costs more than
the coverage gains.

The probes carry a stronger constraint than the goldens: the corpus is fetched at
run time by every service's L5 run, with no pinning and no opt-out. A probe added
here runs against every service's next CI run. That is what makes 10 sufficient —
they are 10 probes applied everywhere, not 10 probes applied once.

**At scale, replace with:** a Security-owned corpus versioned independently of
any service, and per-brand eval registries that services compose rather than
copy. The fetch-at-run-time interface already matches — only the corpus's size
and its ownership boundary change.

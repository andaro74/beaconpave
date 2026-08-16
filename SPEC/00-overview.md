# SPEC/00 — Mission

**Owning seat:** PM. Changes require PM review (CODEOWNERS on `SPEC/**`).

## Mission

Prove, at miniature scale and near-zero cost, that a media company can give
engineering teams a paved road where **quality, compliance, and adversarial
resistance are properties of the infrastructure**, not phases a team completes
before launch — and that the same substrate carries agents, web, and load
testing on one verdict schema.

## Audience

Three readers, in priority order:

1. **A platform engineer at a media company** deciding whether this pattern is
   worth adopting. They need the invariants and the ADRs.
2. **A quality/engineering leader** deciding whether it changes outcomes. They
   need the progression table, the control, and the leakage semantics.
3. **A reviewer with five minutes.** They need the README progression table and
   one recorded demo. Optimize the top of the README for this reader.

## Non-goals

Auth and multi-tenancy · real content, markets, or regulations · prompt
optimization for cost · UI beyond the static player and one dashboard · more
than ~10 adversarial probes or ~25 golden cases · any framework abstraction
layer. Each of these can consume a month and prove no additional claim.

## Definition of done (whole project)

All twelve claims in the README have a recorded artifact, `main` is green, the
control's score sits at the top of the progression table, and a stranger can
clone the repo and run `make check` offline without an AWS account.

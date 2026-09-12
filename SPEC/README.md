# SPEC

Specs are owned by the PM seat. One file per milestone, written **before** the
milestone branch is cut, so the definition of done exists before the work does.

| File | Milestone |
|---|---|
| `00-overview.md` | Mission, audience, non-goals |
| `00b-baseline.md` | The ungoverned control + honesty clause |
| `01-gateway.md` … | One per milestone; write at branch-cut time |
| `06c-instrument-repair.md` | The suite cannot score; repair it before measuring anything on it |
| `06d-instrument-readable.md` | The suite scores but cannot say what it measured; separate a refusal from a wrong answer |
| `07-guardrail-per-channel.md` | The gateway applies the guardrail per channel, so platform-internal content is not judged as a viewer's intent; claim 6 moves to M08 (ADR-070) |
| `08-budget-context-or-ceiling.md` | The tools arm's `tokens_in` budget: a census of the committed trajectories decides whether the context or the ceiling is the thing to change; claim 6 moves to M09 (ADR-073) |
| `08b-ceiling-on-fresh-samples.md` | The first fresh run since M07: the 7700 ceiling measured on samples it was not derived from, with the debts that need a run; added in place, the registry stays M09 (ADR-074) |
| `09-rules-registry-and-the-disposition.md` | A rule delta disposed into an executable control makes the deployed service fail the gate and the fix makes it pass, traceable rule → control → assert; the guardrail half is M09b and answer quality is 09c, both added in place (ADR-075) |
| `09b-the-guardrail-line-and-the-topic.md` | The guardrail line the same rule disposes into, and the topic it recalibrates: the wording is **admitted** by a rule executed before any candidate is measured — a corpus may eliminate a candidate that is worse than the deployed wording and **none may choose one** — because a topic reworded until cases pass is a threshold moved to clear a reading. Replaces the spec withdrawn on 2026-09-11, whose derivation rule had a corpus select (ADR-076 amendment 1). Carries none of the twelve (ADR-076, ADR-077) |
| `09c-answer-quality.md` | One claim: the browse gap closes at a diagnosed site and the goldens count rises above a same-deployment control run on the seven browse-gap cases, with nothing else moving; the `tokens_out` tiers and the `p95_ms` re-derivation are deliverables by rules pinned before either run; the DMA rename cut to after M11. Carries none of the twelve (ADR-078, ADR-075 amendment 8) |

A spec answers four things: what this milestone builds, what it deliberately
does not build, the definition of done as a checklist, and the demo artifact it
must produce. If a spec cannot name its demo artifact, the milestone is not
ready to start.

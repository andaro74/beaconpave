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

A spec answers four things: what this milestone builds, what it deliberately
does not build, the definition of done as a checklist, and the demo artifact it
must produce. If a spec cannot name its demo artifact, the milestone is not
ready to start.

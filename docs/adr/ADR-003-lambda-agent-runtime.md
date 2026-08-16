# ADR-003: The agent runtime is a Lambda function

**Status:** Accepted (cited by `services/highlights-agent/pave.manifest.yaml`)
**Seat:** Platform Engineering

## Context

`pave.manifest.yaml` declares `runtime: lambda | ecs | agentcore`. The miniature
has to pick one. The constraint that decides it is G10 — nothing bills while
idle — and the fact that the whole platform must cost under $5/month at rest.

## Decision

Agents run as Lambda functions behind the gateway. The manifest keeps `ecs` and
`agentcore` as declared values so the migration is a manifest edit rather than a
re-architecture, but only `lambda` is implemented.

## Consequences

Scope cut, and worth naming precisely: **there is no session isolation between
turns.** Conversation state, if it ever exists, must be passed explicitly rather
than held in the runtime. For a single-turn highlights agent that costs nothing;
for a multi-turn agent handling more than one viewer it would be a correctness
bug, not a performance one.

Cold-start latency lands in the p95 budgets in the manifest (`p95_ms: 2500`).
That budget is set with cold starts included, deliberately — a budget that only
holds when the function is warm is a budget that fails in production and passes
in CI.

**At scale, replace with:** Bedrock AgentCore Runtime, which provides per-session
isolation and removes the explicit-state-passing requirement; the interface
already matches — `runtime:` in the manifest is the only field that changes.

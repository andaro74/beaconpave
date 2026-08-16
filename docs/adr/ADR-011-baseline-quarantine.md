# ADR-011: The baseline is quarantined as the only direct-model path

**Status:** Accepted (expires at M01 by design)

## Context

G1 says no service holds direct model-invoke permission; every call transits the
gateway, asserted at synth time. But M00b — the ungoverned control — must call
the model directly, because being ungoverned is the entire point. A control that
already routes through the gateway measures nothing.

## Decision

`services/highlights-agent-baseline/` is permitted direct model access via a
single, explicitly named allowlist entry in the IAM assertion test. The entry
carries a comment naming this ADR and the milestone that removes it.

**M01 deletes that entry as part of its diff.** The deletion is the visible
proof of claim 4: before, one path could call the model directly; after, none
can, and the attempt is logged.

## Consequences

Between M00b and M01 the repo genuinely contains a G1 exception. This is
recorded, time-boxed to one milestone, and its removal is a demo artifact rather
than a cleanup. If M01 lands without deleting the allowlist entry, the M01 gate
fails — the assertion test checks for the entry's *absence* from that milestone
forward.

**At scale, replace with:** nothing — this ADR is designed to expire. The
equivalent at scale is a time-boxed exception through
`pave exception request --ttl`, which auto-expires and is dashboard-visible. The
interface already matches.

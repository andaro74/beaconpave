# ADR-007: The pager is a webhook

**Status:** Accepted (cited by `services/highlights-agent/pave.manifest.yaml`)
**Seat:** Platform Engineering

## Context

`pave.manifest.yaml` declares `oncall: webhook:sports-disc`. Several invariants
depend on something being *paged*, not merely logged: a flake score above
threshold quarantines a suite **and pages its owner**; an `INFRA` verdict pages
the platform rather than the service team; the M09 drill includes an alarm
self-test whose whole purpose is proving the alarm path works.

A real pager is a paid product with an org to provision.

## Decision

`oncall:` resolves to a webhook URL. The platform POSTs a JSON payload carrying
the verdict record that triggered it. The drill's alarm self-test fires a
synthetic page through the same path.

## Consequences

**No escalation, no acknowledgement, no schedule.** A page that nobody receives
is indistinguishable from a page that was delivered, which means the miniature
cannot prove "someone was notified" — only "a notification was sent." Claim-wise
this matters: the drill artifact can record that the alarm path fired, not that
a human responded.

That gap is why the alarm self-test exists at all. Without it, an unreachable
webhook would be silently equivalent to a working one for the entire life of the
project, and the first time anyone found out would be during a real incident.

**At scale, replace with:** PagerDuty or Opsgenie — the `oncall:` field in the
manifest takes a service key instead of a URL, and escalation, acknowledgement,
and schedules come with it. The interface already matches.

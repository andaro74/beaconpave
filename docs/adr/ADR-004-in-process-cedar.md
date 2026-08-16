# ADR-004: Cedar policies are evaluated in-process

**Status:** Accepted (cited by `README.md` repository map, `platform/policy/`)
**Seat:** Platform Engineering (mechanism) · Tool Owner (the policies themselves)

## Context

G3 requires every tool call to be authorized against the registry via policy.
Amazon Verified Permissions is the managed answer, but it is a per-request
billed service with a control plane to provision — and G10 says nothing bills
while idle.

## Decision

Cedar policies are generated from the `callers` field in
`platform/registry/tools.yaml` and evaluated **in-process**, inside the gateway,
against the committed policy set in `platform/policy/`.

Generation from `callers` is the load-bearing half. Hand-written policies drift
from the registry, and a policy that disagrees with the registry is worse than
no policy — it makes the registry look authoritative while something else
decides.

## Consequences

Policy changes ship with a deploy rather than independently, so an urgent denial
cannot be pushed without a release. In a miniature that is fine; at scale it
would be an incident-response gap, which is precisely why the scale-up path is
not optional.

There is no central audit of authorization decisions separate from the audit
lake. The gateway's own audit record is the only place a denial is written —
which makes that record load-bearing for G4, since "policy denied AND logged"
depends on the same component doing both.

**At scale, replace with:** Amazon Verified Permissions — same Cedar syntax, same
generated-from-registry pipeline, policies deployable independently of code, and
authorization decisions logged separately from the application. The interface
already matches.

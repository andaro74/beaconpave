# ADR-023: the Cedar principal comes from the deployment, not from the request

**Status:** Accepted (M02)
**Seats:** Security / Red Team (it is the authorization input) · Platform
Engineering (the gateway) · Service Team (what a caller may say about itself)

## Context

Cedar authorizes on `(principal, action, resource)`. The registry generates a
`permit` per entry in a tool's `callers` list, so the principal is what selects
which policies apply to a call — it *is* the identity half of G3.

The gateway's event already carries a `service` field. It has carried one since
M01, where it did exactly one job: label the audit record and partition the lake
key. Wiring the tool loop, it was the obvious thing to pass to Cedar. It is right
there, it names the caller, and the record and the policy would agree by
construction.

It would also have made G3 decorative. A caller that picks its own principal
picks its own policies: `service: "highlights-agent"` in the payload is a string,
and *"unregistered tools are unreachable"* would have held only for callers that
told the truth about who they were. The invariant would have been a property of
caller candour, which is the shape ADR-016 demoted `entitlement_source` for.

The honest constraint underneath: **a direct Lambda invoke carries no
server-side caller identity.** The event is the caller's. `client_context` is
the caller's. There is no field in the invocation the gateway can read and know
the platform put it there. So the choice was not between a weak identity and a
strong one; it was between an identity the caller asserts and one the caller
cannot reach at all.

## Decision

**The Cedar principal is `SERVICE_PRINCIPAL`, an environment variable set by the
stack.** The gateway never reads `service` from the event for authorization.
`service` keeps its M01 job — it labels the record and partitions the key — and
the two are allowed to disagree, because one is a claim and the other is a fact
about the deployment.

`tests/test_tool_loop.py` takes `principal` as an explicit argument to
`run_turn`, and `core/toolloop.py` says in its docstring that it is never read
off the transcript. Both halves matter: the loop cannot pick it up from the model
either, and a model that emits `{"service": "..."}` in a tool argument is not
proposing an identity.

## The cut

**One gateway deployment authorizes as one service.** The registry names
`recap-agent` as a second caller of `catalog-search`, and through this stack that
entry is unreachable rather than denied — there is no way to make a call that
authorizes as `recap-agent`, so nothing exercises the policy that permits it.

That is a scope cut and it is worth being precise about what it costs: the
*uninvited caller* half of G3 is proven hermetically
(`test_an_uninvited_caller_is_denied`, which passes an unregistered principal
straight to the plane) and not at runtime. The *unregistered tool* half is proven
both ways. The milestone's runtime artifact is the tool one, which is the claim
BUILD.md's M02 row makes.

**Un-cutting it** is the ordinary path and there are two, in increasing order of
what they buy:

1. A gateway per service. The principal stays configuration; the stack gains a
   second function and a second role. Cheap, and correct as far as it goes.
2. A caller identity the platform can verify rather than receive — the invoke
   arriving through a channel that stamps the caller (an authorizer in front, a
   per-caller alias with its own resource policy, or SigV4 with the caller's role
   read from the request context). This is what makes the principal both
   per-caller *and* unforgeable, and it is the one worth building when a second
   service actually exists.

Neither is done here, and neither is pretended to be.

## Consequences

**The audit record can carry a `service` that no policy ever saw.** A caller
sending `service: "recap-agent"` to this stack gets records labelled
`recap-agent` and calls authorized as `highlights-agent`. That is not hidden —
the record carries the label and the deployment carries the principal — but it is
a thing a reader of the lake could misread, and it is the first symptom to
recognise if a second service ever shares a gateway. Rejecting the mismatch was
considered and not done: it would refuse M01's existing callers for a
disagreement that costs nothing while there is one service, and a refusal nobody
needs is a refusal people learn to route around.

**The `Approval` interlock is the same argument, already made.** `Approval` is a
typed value the gateway constructs and never a dict the caller supplies, for the
identical reason: the publish interlock would otherwise have been one key in
caller-controlled JSON. This ADR is that decision generalised to the principal,
and the two should move together if either does.

**At scale, replace with:** the caller's own IAM identity, read from an
invocation channel that carries it, mapped to the registry's `callers` names by
the platform. The mapping belongs to the platform because the point is that the
caller does not get to write it.

# ADR-011: The baseline is quarantined as the only direct-model path

**Status:** ~~Accepted (expires at M01 by design)~~ → **Expired at M01.** The
exception is gone and nothing replaced it. See "How it actually expired" below,
which records the one way the plan below did not survive contact.

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

### The dependency this adds

The control needs `boto3`. CLAUDE.md requires a line saying why the stdlib will
not do: reaching Bedrock means SigV4-signing every request, and hand-rolling
request signing to avoid a dependency would be more code, less correct, and
security-relevant — a worse trade than the dependency by a wide margin.

It is added as the optional extra `baseline`, **not** to `dependencies`. `make
check` must still install and pass on a fresh clone with nothing present that
could reach AWS, which is G8; putting an AWS SDK in the default install would
undo the hermeticity guard added before this milestone by making the import
available to anything that reached for it.

Unlike the allowlist entry above, this dependency **outlives this ADR**: M01's
gateway Lambda needs the same SDK. So M01 deletes the allowlist entry and keeps
the extra, and this note is the record that the two were always separable.

## How it actually expired (recorded at M01, 2026-08-16)

**The allowlist entry never existed as code.** This ADR, BUILD.md, SPEC/00b, and
two files in the control all describe M01 deleting an entry from the IAM
assertion test. That test had never been written — `platform/infra/` held one
README until M01 — so the grant was carried in prose across four active files
and this ADR. There was nothing in a template to delete.

The tempting repair was to write the assertion test *with* the entry in M01's
first commit and delete it a few commits later, so the deletion would appear as a
code diff. **That was rejected on the record**, because it manufactures the proof
artifact for claim 4, and a manufactured artifact is worse than an honestly
narrower one. What M01 did instead: the assertion test landed with no exception
in it, this ADR was marked expired, the prose grants were rewritten in the past
tense, and `pave/infra.py` carries the allowlist as a one-entry tuple whose
length a test pins — so the realistic way the exception returns, a second string
added to make a failing test pass, fails loudly and names this ADR.

**The runtime half needed a principal this ADR never identified.**
`run_baseline.py` runs under the operator's IAM *user*, not a synthesized service
role, so removing a grant from a CDK template cannot make it fail. "Run the
baseline and watch it fail" would have been false. Claim 4's runtime artifact is
therefore `platform/probe/`, a deployed Lambda carrying the governed service
role. The operator's user is deliberately left unconstrained: the control's
recorded numbers must stay reproducible from the commit they were recorded
against.

**The dependency outlived the ADR exactly as predicted.** `boto3` stays as the
optional extra `baseline`; the gateway's adapter needs the same SDK. The two were
always separable and this is the record that they were.

## Consequences

Between M00b and M01 the repo genuinely contains a G1 exception. This is
recorded, time-boxed to one milestone, and its removal is a demo artifact rather
than a cleanup. If M01 lands without deleting the allowlist entry, the M01 gate
fails — the assertion test checks for the entry's *absence* from that milestone
forward.

*Held to at M01:* `tests/test_iam_assertions.py` asserts the absence, and
`tests/test_contracts.py` fails if this ADR's grant language reappears in an
active file.

**At scale, replace with:** nothing — this ADR is designed to expire. The
equivalent at scale is a time-boxed exception through
`pave exception request --ttl`, which auto-expires and is dashboard-visible. The
interface already matches.

# ADR-048: the only cross-tool negative control rested on a registry line that was never a service, and removing it left the test passing under a name it no longer tested

**Status:** Proposed. Written before the code. **Zero model calls.**
**Seats:** Tool Owner (the registry, the caller allowlist) · Security / Red Team
(G3's negative controls) · Platform Engineering (the mechanism)

Supersedes two sentences of **ADR-023**, amended in place there rather than
rewritten.

## The framing this rejects

Two readings were offered and both are wrong.

*"M05 deleted a real control."* No. The control is intact and stronger; only its
fixture moved.

*"The control was always synthetic."* Also no, and this is the more tempting one.
The **assertion** was real — cross-tool denial is a genuine property of the
generated policy set, and the test exercised it against the committed registry.

**What was never real was the subject.** `recap-agent` had no service directory,
no code, and — as ADR-023 established at M02 — no way to exist: one gateway
deployment authorizes as one service, so nothing could ever make a call that
authorized as `recap-agent`. It was a registry line, not a caller. The control
was a real assertion about a principal that could not be deployed.

## The threat

**T1 — a negative control whose fixture disappears keeps passing.** Not by
failing open, and not by being deleted: by silently becoming a *different, weaker*
assertion that the suite already makes elsewhere.

`tests/test_toolplane.py::test_an_uninvited_caller_is_denied_by_policy` asserted
that a service the registry invites to **one** tool is denied **another** —
`recap-agent`, a registered caller of `catalog-search`, denied on
`entitlement-check`. Remove `recap-agent` from the registry and the registry has
one distinct caller. **Zero cross-tool pairs are constructible.** The call becomes
"an unregistered principal is denied", which
`test_an_unregistered_tool_is_denied_by_policy_and_not_by_the_contract` already
covers, and the test passes under a name it no longer tests.

Measured on `6af17d2`:

```
# remove recap-agent from platform/registry/tools.yaml, regenerate
python -m pave.cli policy generate --check   ->   exit 0
python -m pytest -q                          ->   1881 passed, ZERO failures
distinct callers in the registry             ->   ['highlights-agent']
cross-tool negative pairs constructible      ->   []
```

Both `test_an_uninvited_caller_is_denied_by_policy` and
`test_an_uninvited_caller_is_denied` stayed green.

## Why the entry goes rather than stays

Keeping it costs more than it buys, and the cost is not hypothetical:

- **It is a phantom in the deployed authorization set.** The generated
  `tools.cedar` carried `permit(principal == Service::"recap-agent", …)` — a
  standing grant to a principal that cannot exist. Review of the registry is
  supposed to be review of what it authorizes (ADR-004); an entry authorizing
  nobody makes that review report on something that is not there.
- **It states a live fact in four documents that becomes false the moment anyone
  looks.** `platform/gateway/handler.py`, `tools/catalog-search/README.md`,
  `docs/governance/demo-script.md` and ADR-023 itself all described it as a second
  caller. **Nothing pinned any of them** — leaving all four stale reports 1881
  passed — so "corrected alongside" is a promise no check enforces.
- **M05's own demo scaffolds a service by that name.** `demo-script.md:49` is
  `pave new recap-agent …`. A registry that already names it makes the demo's
  central claim — *here is a service the platform has never seen* — false before
  the command runs.

## Decisions

**Decision 1 — `recap-agent` leaves `platform/registry/tools.yaml`, and the
generated policy set is regenerated in the same commit.** The drift gate makes
the second half non-optional: the registry edit alone is red at
`test_the_committed_policy_set_is_exactly_what_the_registry_generates`. That is
the gate working, and it means this change necessarily touches
`platform/gateway/core/cedar.py`'s four-seat rule.

**Decision 2 — the cross-tool control is re-founded on a synthetic registry
declared as an in-module literal, in the same commit.** Never a committed fixture
file. A second registry on disk is a second thing nothing regenerates from, and it
rots away from the real schema silently — a new drift surface for a control whose
entire purpose is to be independent of the committed set. `cedar.generate()` takes
a plain `list[dict]`, so no file is needed.

**Decision 3 — the control asserts the delta in both directions, in one test.**
`svc-two -> tool-a` must be **allowed** and `svc-two -> tool-b` must be **denied**.
The positive half is not decoration: without it the denial passes against a policy
set that denies everything, which is the PR #13 defect this repository has now met
in three places.

**Decision 4 — the fixture asserts its own sufficiency.**
`test_the_cross_tool_control_still_has_a_pair_to_test` requires at least two
callers, at least two tools, and at least one ungranted pair. T1 is the reason: the
failure mode here is not a control being deleted, it is a control quietly losing
the thing that made it meaningful. A fixture that can go vacuous must say so.

**Decision 5 — the four prose sites are corrected, and ADR-023 is amended in
place, not rewritten.** Its two affected sentences stay where they are, marked,
with the amendment below them — the convention `docs/adr/README.md` states, and
the reasoning in the first of them is exactly what this ADR acts on.

## What this does NOT do

**It does not make the prose sites enforceable.** They were corrected by hand and
nothing pins them; a future rename walks around all four again. The structural
answer is a registry-to-documentation check, and it is recorded as owed rather
than claimed.

**It does not restore a cross-tool pair to the committed registry.** After this,
the deployed policy set has one caller, and the property "a registered caller of
one tool is denied another" is proven against a policy set this repository
generates but does not deploy. That is a real reduction in what the *committed*
artifact witnesses, and it is the cut being recorded.

**It does not address the caller allowlist's key cost.** Adding a caller to
`publish-highlight` remains one registry line at `tool-owner` + `legal-sp`, with
no Security key, and none of ADR-044's three tool-plane guards sees it. Recorded
in ADR-044 as owed; unchanged here.

## Scale-up path

*At scale, replace the synthetic registry with a second committed service; the
interface already matches — the control takes a `list[dict]` and the committed
registry is one. M06 adds the second tool and M08 the second service, at which
point the fixture becomes a real pair again and this ADR's cut un-cuts itself.*

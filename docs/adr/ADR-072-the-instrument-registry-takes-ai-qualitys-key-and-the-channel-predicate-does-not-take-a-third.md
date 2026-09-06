# ADR-072: the instrument registry takes AI Quality's key, and the channel predicate does not take a third

**Status: PROPOSED in M07 PR 3; ACCEPTED when that PR merges. Zero model
calls; a `pave/twokey.py` change and nothing else.** ADR-070 amendment 3
recorded one owed `pave/twokey.py` decision, the operator's, and dated it to
PR 3: whether AI Quality holds a key on `quality/adversarial/instruments.json`
and on the channel predicate in `core/toolloop.py`. Decided here, in its own
record, because it touches the registry PR 3's store does not.

**Seats:** AI Quality (the rules list is its, by `pave/twokey.py`'s own
docstring) · Security (the registry sits under its corpus rule) · Platform
Engineering (the mechanism) · Legal/S&P (the rules file collects it since
ADR-053) — the four seats `pave/twokey.py` itself takes.

## The two findings

**Q2.** A historical registry row's digests edited in place passed 2557 tests
on Security's key alone. PR 2 pinned every row's digest in
`tests/test_contracts.py`, one line per row, so an edit is a visible diff; but
the second key was not PR 2's to add.

**Q6, as corrected in round 2.** The `is_request` predicate — which output of
the model is a `tool_request` and which the `answer` — is worth ten probes:
measured, one block labelled `answer` credits 10/11 and labelled `tool_request`
0/11. It sits on `(platform-eng, security)` through the gateway decision-path
rule, and inside `guardrail_sha256`. Neither gives AI Quality a key.

## Decision 1 — `instruments.json` takes AI Quality's key

A new rule, `^quality/adversarial/instruments\.json$`, seats `("ai-quality",)`,
`requires_adr` off. It **stacks** on the corpus rule (`^quality/adversarial/`,
Security alone, with an ADR), so the registry collects Security, AI Quality and
a decision record.

Why one seat and no ADR flag of its own: `evaluate` counts the ADR-requiring
rules a diff hits and demands that many decision records, so a second
`requires_adr` rule over one file would price every registration at two ADRs.
The corpus rule already brings the ADR; this rule brings the seat.

Why AI Quality: a row edited in place redefines every history entry citing the
name — ADR-018's hazard — and the seat that owns whether a before/after survives
is the one the `gateway-stack.ts` rule already collects for exactly that hazard.
The seat whose published numbers cite the names is the seat that signs a
re-registration. It does not feel the pain alone: Security holds the other key,
so G9 is satisfied in both directions.

## Decision 2 — the predicate takes no third seat

`core/toolloop.py` stays on `(platform-eng, security)`. Any change to
`is_request` moves `guardrail_sha256`, and
`tests/test_contracts.py::test_the_current_instrument_still_describes_this_tree`
— on an `(ai-quality, platform-eng)` file — makes an unregistered move red. So
the route to a scoring-relevant predicate change runs through the registry,
which now collects AI Quality. **One decision, one key, at the registry**,
rather than a third seat on every gateway change.

What this does not close, stated: a predicate change that moves the digest and
registers a successor row collects AI Quality at the registry; a predicate
change that a future digest widening happens not to cover would not. The
digest's coverage of `core/toolloop.py` is whole-file, so today there is no
such change.

## What moves with it

- `tests/test_twokey_seats.py`: the ratchet keyed on `Rule.what` gains
  `"the instrument registry"` and moves 17 → 18; `required` gains the one path
  and its total pin moves 57 → 58; `M07_SEATS` pins `instruments.json` at
  `{security, ai-quality}` and `probes.yaml` at `{security}`, so the rule is
  shown narrow — one file gained a seat, not the corpus.
- `docs/governance/ROLES.md`'s two-key table is a summary and `pave/twokey.py`
  is the authority (CLAUDE.md); the table is not edited here.

## Consequences

- The next registration (`m04-I`, whenever a digest moves) collects three
  things: Security, AI Quality, and an ADR that says what moved.
- This PR's own attestations cover the four seats the rules file takes; the
  registry is not touched by this diff, so the new rule is exercised by the
  seat pins and not by this PR's body.
- **At scale, replace with code-owner review on the same path list; the path
  list here and there are the same list — the interface already matches.**

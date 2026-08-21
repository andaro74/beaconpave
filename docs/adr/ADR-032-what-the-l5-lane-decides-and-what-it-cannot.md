# ADR-032: What the L5 lane decides, and what it provably cannot

**Status:** Accepted (M04, before the probe corpus is re-run)
**Seats:** Platform Engineering (the lane) · Security / Red Team (what a probe
outcome means, and the G4 corpus — two-key, ADR required) · AI Quality (the pins)

## Context

ADR-029 settled the L2 lane's scope: it scores **committed answers** against a
pinned comparator and calls no model, because a lane that ran the agent per pull
request would need model access in CI (which G1 refuses), would cost money on
every PR, and would return a different number every time.

The L5 lane inherits every one of those reasons, and one more: the guardrail it
would be exercising has been measured as returning different verdicts on identical
input. So M04's first design was simply L2's, with observations in place of
answers and probe results in place of case results.

**That design was falsified before it was built.** The Security seat measured what
the pins can actually see, against the committed observations M04 was about to
pin:

| planted weakening | `m01` | `m00b` | probes moved |
|---|---|---|---|
| `CEDAR_MECHANISMS` admits `classification` | 6/10 | 0/10 | none |
| `CEDAR_MECHANISMS` admits every mechanism the platform knows | 6/10 | 0/10 | none |
| the broad semantics accepts `schema` / `loop` / `routing` | 6/10 | 0/10 | none |
| **the `and logged` half of G4 deleted outright** | 6/10 | 0/10 | **none** |

Two causes.

**`CEDAR_MECHANISMS` is unreachable on the committed evidence.** `_satisfied_by`
gates on `policy_denied` before it consults the mechanism set, and ADV-008 — the
only probe declaring Cedar semantics — records `policy_denied: false`. The set can
be widened to anything without ever being read.

**The pinned observations contain no case that discriminates G4's two halves.**
Every `m01` observation carries an audit record; every `m00b` observation refuses
nothing. `refused` and `logged` therefore never disagree anywhere in the set, and
deleting the audit half of the pass condition leaves both pins exactly where they
were.

**The second is structural, not a corpus to improve.** Observations from a working
platform do not exercise the scorer's failure branches. No future run will produce
a refused-and-unlogged case unless the gateway is broken, which is precisely the
condition nobody can schedule.

So `evals/comparators.json` claimed the lane decided *"that the probe instrument
has not moved underneath a published row"*, and it did not. That is the fault
`pave/twokey.py`'s own comment names: **a stated protection is worse than an
absent one, because it stops anyone looking for the real one.**

## Decision

**The L5 lane decides two things, and the second is why it is not the L2 lane with
a different corpus.**

1. **Every pinned probe result still holds** — committed observations re-scored
   through today's `score_probe`, per probe and in total, deviation in either
   direction failing.
2. **G4 still means what `quality/adversarial/g4-semantics.yaml` says** —
   fourteen synthetic observations built to discriminate exactly the distinctions
   the committed corpora cannot.

The corpus is data rather than test assertions **because a gate cannot read a
Python test body**, and it lives under `quality/adversarial/` because it is a
statement about what a probe passing *is*, which is Security's. That path is
two-key and requires an ADR. **So widening the scorer fails the gate, and editing
the corpus to match cannot be done unattested.** The loop
`evals/comparators.json` already claimed to close for the numbers, extended to the
semantics that produce them.

**One corpus, two readers.** The cases were *moved* out of
`tests/test_adversarial_scoring.py`, not written beside it. A second list of what
G4 means is the fault ADR-030's PR spent itself closing, one level up.

### What stayed in the test file, and why

Three things a table cannot say: structural facts (`score_probe` cannot see the
model's text — asserted against the signature, so no future edit can grade an
answer without a visible diff), corpus-level facts (the control scores zero across
all ten probes), and the one observation that must be built by
`core.audit.resolve_failed` rather than written by hand — a fixture written in the
corpus would be a second opinion about the record's shape, and the point is that
the two halves agree.

## Consequences

**The lane's stated job is now true, and it was verified by planting rather than
by reasoning.** All four weakenings above block end-to-end: the lane exits 1, the
verdict records `FAIL`, `gate decide` exits 1, and the printed reason is the
case's own `why`.

**`INFRA` travels separately from `FAIL` and outranks it**, matching
`pave/gate.py`. A missing observation file establishes nothing about the system
under test, so reporting it as `FAIL` would page the service team for a harness
problem. Both block; only the pager differs.

**One weakening remains out of reach, and the corpus says so.**
`core.audit.POLICY_MECHANISMS` — which mechanisms set `policy_denied` in the first
place — is consumed at *observation-capture* time, so a corpus handing
`score_probe` an already-decided boolean cannot reach it. Widening it to admit
`loop` or `schema` (making a probe satisfiable by the attack being incompetent,
which `core/audit.py`'s own docstring argues against) passes every case in the
file.

It is caught in five places that own that boundary, and they are **named in the
corpus** rather than left implicit. The split is: this corpus owns *what a
recorded observation means*, and those tests own *what gets recorded*. Neither
covers the other, and a reader looking for the second protection must not find
only the first. Recording the gap is the whole lesson of this ADR arriving twice.

**The gate now needs Security's key on three more paths.** `evals/adversarial.py`
names Security in its own docstring and matched only `/evals/`, which is AI
Quality's section — so the module deciding whether a guardrail block counts sat
with the seat that feels a probe score rather than the seat that defends it.

**At scale, replace with:** the semantics corpus generated from the policy
engine's own decision table, so a control's implementation and the cases proving
what it means cannot drift apart at all. The interface already matches — a case
declares an observation, a semantics and an expected verdict.

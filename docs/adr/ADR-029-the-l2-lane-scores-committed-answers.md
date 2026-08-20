# ADR-029: The L2 gate lane scores committed answers against a pinned comparator, and never runs the agent

**Status:** Accepted (M03)
**Seats:** Platform Engineering (the lane and the workflow — two-key with AI
Quality on `gate.yml`) · AI Quality (the comparator, two-key)

## Context

`quality-gate.yml` has carried a commented-out L2 lane annotated
`# turns on at M03` since M00a. M03 is the milestone that either turns it on or
moves the promise, and a promise still pointing at a milestone that has closed is
how a placeholder outlives its excuse.

The obvious reading of "L2 evals vs baseline" is: run the agent against the golden
set on every pull request and compare the score to the recorded baseline. That
cannot be built here, and the reasons are invariants rather than inconvenience.

- **G1.** Running the agent means a model call, which means Bedrock access from
  CI. The gateway is the only path to a model, and giving a CI runner that path —
  even scoped, even temporarily — is the grant this repo exists to refuse.
- **G8.** `make check` and the gate are hermetic: no cloud, no network. A lane
  that calls a model breaks that for every PR, not just the ones that need it.
- **Determinism.** A model call returns a different number each time. M02
  measured an identical system returning 18, 16 and 14 across three samples. A
  gate that blocks on a stochastic number blocks arbitrarily, and teams learn to
  re-run until green — which trains exactly the reflex the gate exists to prevent.
- **Cost.** Twenty-five cases per PR, per push, forever.

## Decision

**The L2 lane scores committed answers and calls no model.**

`pave evals run <service>` re-scores the service's committed run files with the
current deterministic scorer and compares the result to
`evals/comparators.json`. It emits an `L2` / `evals` verdict that `gate decide`
reads alongside the contract and infra verdicts.

### What it decides, which nothing else did

**That the instrument has not moved underneath a published row.**

`tests/test_instrument_stability.py` pinned `m00b` at 18/25 and `m01` at 19/25
under the current scorer. **Nothing pinned M02.** An edit to a case the M02 arms
depend on, or to `evals/deterministic.py`, or to `data/catalog.json`, moved a
published number with no test to see it. The lane closes that: tools 15/25,
control 17/25, both arms, because M02's result is the paired diff and a comparator
that moved on one arm only would silently change the delta while both totals still
looked defensible (ADR-021).

### `evals/comparators.json` is a new artifact class, and not a baseline

| | `evals/history/` | `evals/comparators.json` |
|---|---|---|
| what it holds | what the answers scored **on the day** | what those same answers score **now** |
| when it changes | never — append-only | when the instrument legitimately moves |
| who decides | AI Quality (two-key) | AI Quality + Platform Eng (two-key) |

They differ today by one case: the tools arm recorded 16/25 and scores 15/25,
because the `cited_titles_in_fixture` tightening landed after `m02` was tagged.
**A lane comparing against the recorded number would fail on every legitimate
tightening**, and that is not a neutral inconvenience — it is the pressure that
gets tightenings reverted or quietly not written.

### Deviation fails in **either** direction

A drop is the obvious regression. A **rise** is the one this repo exists to catch:
the `m00b` control gained three passes when ADR-016 moved `p95_ms` to suite level,
with no improvement to any system whatsoever, and CLAUDE.md's baseline-honesty
rule is that a flattering control makes every later milestone unfalsifiable. A
lane that passed anything at-or-above the comparator would wave that through.

### The remediation path is attested

The lane's failure message tells a team the comparator moves in its own two-key
PR. **That was a fiction when the lane landed** — `evals/comparators.json` matched
no rule in `pave/twokey.py`, so the number the gate decides on could be edited in
any feature PR with no attestation, while `evals/history/`, which is immutable
anyway, was protected. Three seats found it independently in the same review.

`pave/twokey.py` now carries the rule, and `docs/governance/ROLES.md` the matching
row. `evals/deterministic.py` and `data/catalog.json` are deliberately **not**
two-key: a scorer change should be reviewable as code, and it becomes visible the
moment it moves a comparator, which now needs the second key. The property is
that **the loop cannot be closed unattested**, not that every input is gated.

## Consequences

**The lane cannot see a service team's prompt change**, and saying so plainly
matters more than it sounds. It scores frozen answers, so improving a prompt
cannot move it. Whoever trips it is editing the scorer, the golden cases, or the
catalog — platform and quality work — and "the instrument has moved" lands on
someone who does not think of themselves as touching a service's published score.
The failure message therefore names the file, the seat, the local reproduce
command, and the three inputs that could have moved.

**A second service gets no L2 coverage until someone wires it.** The workflow
hardcodes `services/highlights-agent`, and `pave new` is still a stub. When the
scaffold becomes real, `evals_run` should iterate `pinned["services"]` rather than
take one positional — the comparator file is already keyed by service, so the
interface matches today.

**Two comparator registries now exist**: `M00B_UNDER_CURRENT_INSTRUMENT` and
`M01_UNDER_CURRENT_INSTRUMENT` as Python constants in a test, and the M02 arms as
data the gate reads. Same job, two homes. Consolidating them into
`comparators.json` is owed and deliberately not done here — moving a pinned
comparator in the same milestone that first pins any of them would make the two
changes indistinguishable in the diff.

**At scale, replace with:** the suite run against a per-PR ephemeral deployment
through the gateway, with the comparator becoming a rolling window rather than a
point. The verdict interface already matches — the lane emits the same `L2`
record either way, and `gate decide` cannot tell how it was produced, which is
what makes the swap possible without touching the gate.

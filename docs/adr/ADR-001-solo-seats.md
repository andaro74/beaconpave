# ADR-001: Role subagents, with one operator playing every seat

**Status:** Accepted — **amended by ADR-013 (M00a)**

> **Amendment.** The Decision's part 1 below claims "branch protection requires
> that team's review… the operator approves wearing the relevant hat." That is
> not achievable: GitHub never lets a pull request's author approve their own PR,
> in an org or out of one. ADR-013 replaces that clause with required status
> checks — including a machine-checked two-key attestation for G9 — and states
> plainly which invariants remain conventions under one operator.
>
> Everything below about *perspective* being the real gap, and about subagents
> advising rather than approving, stands unchanged and is why this ADR is amended
> rather than superseded.

## Context

This is a miniature. A real deployment has distinct teams behind each of the
eight seats. A solo operator playing all of them risks the demo's central claim
— that governance is real — collapsing into "one person approved their own work
eight times."

## Decision

Two parts.

**1. The enforcement mechanics stay real.** GitHub teams exist, CODEOWNERS routes
each path to its owning team, branch protection requires that team's review,
admin bypass is disabled, and the approval interlock runs. The operator approves
wearing the relevant hat.

**2. Each seat gets a subagent** (`.claude/agents/`) that reads the diff from
that seat's perspective and posts findings before the human review. The Security
subagent hunts for G4 violations and stray model grants; AI Quality hunts for
threshold changes riding along in feature PRs and golden cases edited to pass;
the Service Team subagent argues for the developer whose day this friction will
cost.

Subagents **advise; they never approve** (G6). Their finding-acceptance rate is
tracked like any other curation rate: a subagent ignored 95% of the time is
miscalibrated and gets fixed or retired.

## Why this is not a shortcut that invalidates the demo

The claims are about *mechanisms*: a threshold change requires two keys, a
publish action waits on approval, a rule change flows to a named owner. Those
are enforced by infrastructure, not by having eight humans. Multiplexing the
humans changes who clicks approve, not whether approval is required.

The subagents address the real risk, which is not missing headcount but missing
*perspective*: one reviewer reads a diff once, from one angle. Seven subagents
read it from the seven angles the seats are accountable for.

## Consequences

The operator must actually run the subagents; skipping them is the failure mode.
`CONTRIBUTING.md` puts it in the PR checklist, and the demo script shows the
findings in the PR body.

**At scale, replace with:** real teams mapped to the same CODEOWNERS entries,
with subagents retained as first-pass review — the interface already matches.
You change team membership, not a line of enforcement logic.

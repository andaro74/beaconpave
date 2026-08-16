# ADR-013: What a solo operator can actually enforce, and how G9 gets enforced anyway

**Status:** Accepted (M00a). **Amends ADR-001** — does not supersede it.
**Seats:** Platform Engineering (mechanism) · AI Quality (the two-key rules)

## Context

ADR-001 says the enforcement mechanics stay real: "GitHub teams exist, CODEOWNERS
routes each path to its owning team, branch protection requires that team's
review, admin bypass is disabled, and **the operator approves wearing the
relevant hat**."

That last clause is not achievable. **GitHub does not permit a pull request's
author to approve their own pull request** — the Approve option is disabled for
the author and the API rejects the attempt. This is true in an organization and
out of one; seven teams with a single member each does not change it. So on a
one-operator repo, "Require review from Code Owners" cannot be satisfied at all:
either every PR is unmergeable, or the requirement is turned off and CODEOWNERS
becomes routing with no teeth.

The starter's `branch-protection.md` instructed exactly the unachievable setup
and told the reader it was "what makes seats real." Following it would have
produced a repo that looked governed and was not — the single worst failure mode
named in CLAUDE.md.

A second GitHub account is not a fix. GitHub's terms permit one free account per
person, and a sockpuppet approval would be a *less* honest artifact than no
approval at all.

## Decision

Split the seat model into the part a machine can enforce and the part it cannot,
and say which is which.

**Enforced, with no second human — required status checks that cannot be
bypassed:**

| Invariant | Mechanism |
|---|---|
| G2 fail-closed gate | `pave gate decide`; absent or errored verdicts block |
| **G9 two-key** | `pave gate two-key` — see below |
| G7 rules registry | `rules validate` in `pave check` |
| G8 hermetic local checks | `pave check`, committed fixtures, no network |
| G1, G3, G4 | assertion tests (M01, M02, M04) |

**Not enforced by machinery, and labelled as such:** G6's "a human seat
disposes." One operator disposing is one operator disposing. The role subagents
in `.claude/agents/` supply the missing *perspective* — which ADR-001 correctly
identifies as the real gap — but they advise and never approve.

### G9 becomes an attestation the machine checks

The second key moves from a review click to a written disposition in the PR body,
verified by a required check:

```
Two-Key-Disposition: ai-quality
Two-Key-Rationale: M03 published a judge agreement of 0.91, which supports
  raising the groundedness floor to 0.8; headroom stays at three cases
```

`pave gate two-key` blocks any PR touching a two-key path — golden cases, judge
rubric and calibration, the verdict schema, `evals/history/` baselines, gate
criteria, consequence classes, the adversarial corpus — unless every owning seat
named in `ROLES.md` has disposed, with reasoning of substance. The probe corpus
additionally requires a cited ADR that exists in the tree. **Editing the two-key
rules is itself two-key**, so the first move against G9 cannot be to quietly
delete G9's enforcement.

CODEOWNERS is kept, pointed at `@andaro74`, for routing and ownership display.
Branch protection requires the status checks and **does not require approvals**,
because a requirement that cannot be met is a requirement that gets turned off.

## Consequences

This is weaker than two humans, and the repo should say so rather than imply
otherwise. What it is not is a convention: the check is required, unbypassable,
and produces a written reason attached to the diff permanently. Compared with a
second click from the same person wearing a different hat — which is what ADR-001
imagined and what an org would have delivered at best — an attestation with a
mandatory rationale is arguably the more honest artifact, because it cannot be
satisfied without saying something.

The cost is that a determined operator can write a rationale they do not believe.
No mechanism available to one person prevents that. The mechanism prevents the
*silent* case, which is the one that actually happens: a baseline reset buried in
a feature PR, noticed by nobody, explained nowhere.

`branch-protection.md` is rewritten to the achievable setup. ADR-001 gets a
pointer to this ADR; its reasoning about subagents and perspective stands
unchanged, and is not deleted.

**At scale, replace with:** real teams on the same CODEOWNERS path list, "Require
review from Code Owners" turned on, and this check retained as a pre-review
filter that makes reviewers state their reasoning. The path list in
`pave/twokey.py` and the path list in `.github/CODEOWNERS` are the same list —
the interface already matches.

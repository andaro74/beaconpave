# Branch protection setup

Do this before M01. Without it, the gate is a suggestion.

> **This guide was rewritten at M00a.** It previously told you to create seven
> teams of one and tick "Require review from Code Owners," describing that as
> "what makes seats real." It does not work: GitHub never lets a pull request's
> author approve their own PR, so a solo operator can satisfy that setting on
> exactly zero PRs. Following the old guide produced a repo that looked governed
> and was not. See **ADR-013** for the full reasoning and for what replaced it.

## What actually enforces what

| Invariant | Enforced by | Second human needed? |
|---|---|---|
| G2 — the gate fails closed | required check `quality-gate / gate` | no |
| G9 — two-key on thresholds and baselines | required check `two-key / two-key` | no |
| G7 — rules registry validity | inside `pave check` | no |
| G8 — hermetic local checks | inside `pave check` | no |
| G1, G3, G4 | assertion tests (M01, M02, M04) | no |
| G6 — a human seat disposes | role subagents + recorded disposition | **convention with one operator** |

CODEOWNERS still routes: it auto-requests review from the owning seat and shows
ownership on every PR. It is not, here, an approval gate.

## 1. Protect `main`

Settings → Branches → Add branch protection rule for `main`:

- [x] Require a pull request before merging
- [ ] Require approvals — **leave at 0**. A requirement you cannot satisfy is a
      requirement you will end up switching off, and switching it off is how
      admin bypass gets enabled "just for now."
- [ ] Require review from Code Owners — **off**, for the same reason
- [x] Require status checks to pass before merging
  - Required: `quality-gate / gate`
  - Required: `two-key / two-key`
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings  ← **including for admins**

That last box is the one people skip. An admin bypass makes G2 false: a gate you
can merge past is not a gate. It is also the one box that is doing the heavy
lifting here — with approvals at 0, the required checks are the entire enforcement
surface, so nothing may be permitted to route around them.

Branch protection is free on public repositories. On a private repo it needs
GitHub Pro; if this repo is private and on the Free plan, none of the above is
available and the gate is advisory until that changes.

## 2. Labels

Create `exhibit` (deliberately-red demo PRs, closed unmerged) and `ai-proposed`
(AI-authored, awaiting seat curation).

## 3. Verify

Two throwaway PRs, both of which must be blocked:

```bash
# 1. the gate bites — a failing contract test must block
git checkout -b throwaway-gate && echo "assert False" >> tests/test_contracts.py
# open the PR: `quality-gate / gate` must fail and merge must be blocked

# 2. the second key bites — a threshold change with no disposition must block
git checkout -b throwaway-twokey && touch quality/judge/scratch.md
# open the PR with an empty body: `two-key / two-key` must fail
# then add to the PR body:
#   Two-Key-Disposition: ai-quality
#   Two-Key-Rationale: <a real sentence, 24+ characters>
# the check must re-run on the body edit and pass
```

If either merges, the required checks are not attached — check the exact check
names under Settings → Branches, which must match the workflow **job** ids
(`gate`, `two-key`), not the workflow names.

Close both PRs unmerged. Label them `exhibit`.

## 4. Milestone branches

```bash
git checkout -b m01-gateway        # branch: mNN-<slug>
# ... work, PR, merge to main ...
git tag m01 && git push origin m01 # tag: mNN — NEVER the same name as a branch
```

Branch and tag sharing a name makes `git push -u origin x` fail with "src
refspec matches more than one" and `git checkout x` ambiguous. Do not delete
merged milestone branches: the branch list is a visible progress ledger.

## At scale

Create the seat teams, replace `@andaro74` with them in `.github/CODEOWNERS`,
set required approvals to 1, and turn on "Require review from Code Owners." The
path list — the part that encodes the org chart — does not change, and the
two-key check is retained as a pre-review filter that makes reviewers state their
reasoning. That is the whole migration.

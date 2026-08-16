# Contributing

## Milestone workflow

**One milestone = one branch (`mNN-<slug>`) = one tag at close (`mNN`).**

```bash
git checkout -b m04-gate            # branch: mNN-<slug>
# ... work ...
git push -u origin m04-gate         # PR; the gate runs; seats review
# ... merge to main ...
git checkout main && git pull
git tag m04 && git push origin m04  # tag: mNN
```

**Branch and tag must never share a name.** Git cannot disambiguate
`refs/heads/x` from `refs/tags/x`: `git push -u origin x` fails with "src
refspec matches more than one" and `git checkout x` is ambiguous. Hence
`m04-gate` (branch) and `m04` (tag).

Do not delete merged milestone branches — the branch list is a visible progress
ledger. Do not start M(n+1) before M(n) is closed (`.claude/skills/close-milestone`).

## `main` is always green

A stranger's first impression must not be a broken build. Deliberately-red demo
PRs — the ones proving the gate bites — are labeled **`exhibit`** and **closed
unmerged**. Closed PRs persist and stay linkable forever, so the evidence
survives without poisoning `main`.

Use red-then-green in a single PR only when the fix is genuinely part of the
story (e.g. the M07 rule-disposition demo, which ends in a real fix that should
land).

## Seat review

Every path has an owning seat (`docs/governance/ROLES.md`). CODEOWNERS makes
that review mandatory. Run the relevant subagent in `.claude/agents/` for
first-pass review before requesting the human one; paste its findings into the
PR. Subagents advise — humans dispose (G6).

Two-key changes (eval thresholds, baselines, gate criteria) need the owning seat
**plus** AI Quality, and should be their own PR, never a rider on a feature.

## PR checklist

- [ ] `make check` green (hermetic — no cloud, no network)
- [ ] Evals recorded if scores moved (`--record`)
- [ ] Relevant subagent run; findings in the PR body
- [ ] ADR written if this makes a consequential choice or a scope cut
- [ ] No real company, brand, market, or regulation names — fictional only
- [ ] No new `bedrock:InvokeModel` grant outside the gateway (G1)
- [ ] No probe assertion that passes on model politeness alone (G4)

## Commit style

`mNN: <what changed>` for milestone work; `fix:`, `docs:`, `adr:` otherwise.
Reference the claim number when a commit advances one.

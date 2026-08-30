# ADR-051: an ADR was any tracked file, and the fix for that was written four times

**Status:** Proposed. **Zero model calls.**
**Seats:** Platform Engineering (the gate module) · AI Quality (the rules) ·
Security (the corpus rule this promise is the model for)

**Amended by ADR-052, and NOT completed by it:** this ADR named Security as the
seat whose corpus rule the promise is modelled on, and left the module defining
that promise on a rule not collecting Security's key — measured at 2208 passed on
two keys. ADR-052 adds the key. It also records what the key does **not** reach:
a routine `git merge main` still mints a decision record out of another author's
ADR, which is this ADR's own decision 4 surviving its fix. A "completed by" line
here would be the thing that stops the next reader looking.

Three rules in `pave/twokey.py` promise "the owning seat, plus an ADR", and
CLAUDE.md names one of them — the adversarial corpus — as the model for that
promise. Until this change the ADR half was `ADR_RE.search(body)` and
`is_file()`, which **all 374 tracked files satisfied**:

```
ADR: docs/adr/ADR-001-solo-seats.md  -> [] ACCEPTED
ADR: LICENSE                         -> [] ACCEPTED
ADR: README.md                       -> [] ACCEPTED
ADR: ruff.toml                       -> [] ACCEPTED
```

The promise was the whole of the protection.

## The finding worth more than the mechanism

This was built four times and seats defeated the first three. Each version was
verified against plants its author invented; each time a seat produced one he had
not thought to write.

- **v1** asked whether an `ADR:` line named a tracked file in the diff. Four seats
  sent it back: `in_diff` was one flag for the whole PR, so one ten-byte ADR
  discharged all three `requires_adr` rules.
- **v2** fixed that by counting. Platform Engineering defeated it by pasting the
  same `ADR:` line three times — `att.adrs` keeps duplicates and `in_diff` was a
  list. **The headline defect survived into the fix written to close it.**
- **v3** stopped asking the body and asked the diff, using `git diff --numstat`
  with `added > 0`. Both seats defeated it again: `-w` is ASCII-only, so one
  non-breaking space minted a record, and five other characters did too.

Every version asked a question that was *nearly* the right one. The pattern is not
carelessness, it is verifying against the shape you were shown instead of the
property you owe.

## Decision 1 — a rule is discharged by a record the diff WRITES

`adr_records()` asks git what this diff added under `docs/adr/`, then asks whether
what it added is reasoning. Each clause is a route somebody planted and ran:

| clause | the route it closes | measured |
|---|---|---|
| `-w --ignore-blank-lines` | `printf '\n' >> ADR-001-solo-seats.md` | 45 keystrokes, 3 rules |
| `--diff-filter=AMR` | a typechange that deletes a record | numstat `1  9` |
| `--find-renames` + `RENAME_RE` | a content-free `git mv` | paid twice |
| `seen` | `docs/adr/{a => ADR-001-old}.md` ×3 | one ADR, three records |
| `changed` | another PR's ADR credited to yours | ACCEPTED with no ADR in the diff |
| `substantive_words` | one non-blank byte; NBSP, ZWSP, BOM, U+3000, U+00AD | all clear `added > 0` |

**Two of those clauses were deleted by v3 as decoration and both were
load-bearing.** The reasoning was "remove it and the suite stays green, therefore
redundant" — which measures *test coverage*, not necessity. `--diff-filter=AMR`
was green because nothing covered typechanges; `seen` was green because nothing
covered the rename-notation collision.

## Decision 2 — the bar on what was written is SUBSTANCE, not size or structure

An earlier version accepted a 17-byte stub and recorded it as a residual, arguing
that no bar closes it because every structural bar is a shape to fill. That is true
of structure and false of substance. Measured across **all 69 content-adding ADR
edits in this repository's history**, using the same `substantive_words` the
rationale bar already uses:

```
leanest honest ADR edit:       18 substantive words
a bar of 6 refuses:             0 of 69
a bar of 10 refuses:            0 of 69

append 'x'                  ->  0        a 17-byte stub          ->  0
append U+200B / U+00A0      ->  0        a symlink's target line ->  0
```

18-to-0 with nothing in between, the same bimodal separation the rationale bar
rests on. The bar is `MIN_SUBSTANTIVE_WORDS`, already calibrated, so this
introduces no new number — and the refusal names the defect rather than the
threshold, for the reason recorded one field over.

## Decision 3 — the `ADR:` line stops discharging anything

**A reversal of v1, v2 and v3, with a measured price.** Replayed against every
merged PR through the corpus the gate actually reads — the PR **body**, which is
not the commit message v2's measurement used:

```
merged PRs owing an ADR:   19
one CITATION per rule refuses            8    3 of them regressions
one RECORD   per rule refuses            2    1 of them a regression (#40)
                                              and #24 goes BLOCK -> PASS
```

PR #28 wrote three decision records and cited one; #41 wrote two and cited one.
The gate never checked *which* ADR discharges which rule — that binding was
measured and refused, because it turns away 9 of 17 honest commit×rule pairs — so
the citation was bookkeeping the gate could not verify, priced at two honest PRs.

**PR #40 is the accepted cost.** It cited a pre-existing ADR as a
pre-registration and wrote no record; under "the diff must write one" it is
refused. That is the semantics, not an accident.

**v2's published claim is withdrawn.** It read *"14 commits, and all 14 already
carry at least one ADR per rule. It refuses none of them."* It counted ADRs
*touched* while the code enforced ADRs *cited*, over a population it undercounted,
and it refused three.

**And the replay is committed, because a seat asked why it was not.** The CRLF
corpus was put in the tree so the measurement and the gate would see the same
thing; this argument — the one that cuts the citation, which is the largest
reversal here — rested on a replay nobody else could re-run. Two evidentiary
standards in one file. `pave/tests/fixtures/adr_bar_replay.json` now records, per
merged PR that owes an ADR, what each gate decides, and a test asserts the price:
**exactly one regression, and it is #40**.

The population is not a fixed number and the fixture is the reason that is safe to
say. It was 18 when first measured and is **19** here, because #64, #65 and #66
merged while this PR was in review. A claim pinned to a count would have gone
stale between two seat rounds; a claim pinned to *which PR* does not.

## Decision 4 — the evidence and the changed-file list must describe one PR

`git diff <base>` with one revision compares base to the **working tree**, and on
`pull_request` the working tree is `refs/pull/N/merge`. Anything that landed on
`main` after the base sha was therefore credited to the PR:

```
PR changes only the corpus, writes no ADR   -> ACCEPTED
records the gate credited: ['docs/adr/ADR-051-somebody-elses-decision.md']
```

Both endpoints are passed now, and a record must also appear in the changed-file
list the workflow built. One commit of staleness minted three records before that.

## Decision 5 — the withdrawal path is CUT

v2 let a diff deleting an ADR discharge the rule it withdraws, reasoning that "a
deletion cannot be forged". Both seats forged one. Its justification also failed:
it cited a "real revert" that is the commit which **added** ADR-038; the only ADR
deletion in this repository's history is a draft retitle; and the test blessing the
path used `ADR-099`, which has never existed in any commit — the test constructed
the phantom it then asserted on.

The real problem it named is still real and is not this: `pave exception request`
is a stub that prints `(stub) would:` and exits 0. **At scale, replace with: a
real `pave exception request --ttl`, which is where a withdrawal belongs; the
interface already matches.**

## Decision 6 — the gate tells the reviewing seat what it accepted

`render` now names the records. v3 argued that judging a record's quality "belongs
to the reviewing seat" while `render` took only `(changed, problems)` — so the seat
was told what the gate accepted **only when it refused**. A delegation with no
channel.

## Residuals, stated because they are not closed

- **The gate does not check that an ADR is *about* the control it discharges.** An
  `ADR:` line proves the diff wrote a decision record; it proves nothing else. The
  binding that would fix it refuses 9 of 17 honest pairs.
- **A corpus downgrade riding on a PR that already owes an ADR costs zero marginal
  seats.** `demanded` is a set. It costs one more record now, which is one more
  ADR, but no additional key.
- **`pave/tests/test_twokey.py` collects zero keys** and holds every assertion
  added here. That is SPEC/06 A11.
- **Reverting this PR is cheaper than the control it defends.** `pave/twokey.py`
  is two-key with `requires_adr` off. Whether it should take `requires_adr` is that
  rule's seats' decision — `ai-quality` and `platform-eng` — and is not taken here.

## What this ADR does not do

It does not fix `RATIONALE_RE`, key `pave/tests/test_twokey.py`, close SPEC/06 A2,
or bind an ADR to the control it discharges. Each is named above with what it
would take.

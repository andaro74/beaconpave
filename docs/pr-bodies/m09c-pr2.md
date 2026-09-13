# 09c PR 2 — the close: RED, the claim not measured, and the contract change that took the fix out

**Zero model calls and zero AWS calls. No run, no deploy, no history entry.** No
falsifier, threshold, tier, gate, case, schema, contract, generated policy file or test
is edited. SPEC/09c's claim and falsifiers are unchanged. Its status is written into
lines 3-4 in place, so no line the milestone's documents cite moves.

`make check`: **PASS, 4724 passed, 8 skipped**, at `d8f58c5`, the head of `m09c-pr2-close` immediately
before this body was committed. It was run once, in a clean worktree at that commit. Tag
`cited-09c-close` names that commit, so the citation resolves after a rebase merge.

**Deletability audit: no new assertions; audit empty.** Every file this PR changes is
Markdown or a text record. It adds no test, no code and no check.

**Merge with a rebase merge.** The finding, the amendment, the row, the status fix and
the journal are five commits, and each later one cites an earlier one.

---

## What this PR does

| # | the ask | where it is |
|---|---|---|
| 1 | the measurement, as the milestone's finding | `milestones/M09c/contract-relaxation-blast-radius.txt` and the pytest output beside it. A scratch worktree at `e398799` relaxed `required: [query]` and regenerated the contract. **19 failed, 4688 passed, 8 skipped**, the same 19 on two separate runs, in three groups (7 / 6 / 6). Three readers' committed records stop reproducing: `context_census.py` (12 fields), `residual_differential.py` (11 fields, including its published *"grew by 23"*) and `fresh_join.py` (M08b's, M09's and the planted fixture's records, on the digest alone). M09's priced delta and headroom read 193 and 113 against 200 and 106. Every recorded tool argument still validates |
| 2 | ADR-078 amendment 1 | The diagnosis names `tools/catalog-search/schema.in.json` by quoting SPEC/02:551, :603-606 and :634-641 verbatim. The quotations are generated from SPEC/02's bytes. Those lines were committed in `ed57b2a`, an ancestor of M02's run at `4eda0d0`. **The author had already read and classified the trajectories**, so no rule authored now is admissible. The ruling: the fix is model-facing and invalidates committed measurements in M08, M08b and M09, the property that cut the DMA rename (ADR-075:1012-1017). Three earlier readings that missed it are named. The index row names the amendment |
| 3 | close RED | One claim, three terms, all **NOT MEASURED**. The cause: the intervention is a semver change on a tool contract (SPEC/02:637-638). F1–F5 **not read** and none reported clean |
| 4 | debts | Eight opened, each with an owner and a trigger: the browse gap (Tool Owner, a `catalog-search` semver bump); the era pin's second job (Platform Engineering, the same bump); the tier and `p95_ms` re-derivations (AI Quality, unscheduled, existing triggers); debt 10 (Security, the next milestone producing a goldens refusal census); the citation checker's bare-SHA blind spot (Platform Engineering); `grounded-017`; F4's *"failed 0 of 3"*. SPEC/09c's inherited register is carried row by row |
| 5 | `close-milestone` in order | below. Row 09c: **closed RED** in the milestone cell, `two PRs`, `not run`, `not judged`, `not run`, and a status cell of exactly `✅` |

## Found while writing the close — recorded, not repaired

1. **The status line shifted the spec by one line.** The first version of SPEC/09c's status
   took three lines where there had been two. Every later line moved under citations in
   the amendment and the journal. The citation check caught it before the journal
   committed, and the status is back to two lines, so SPEC/09c's numbering is `main`'s.
2. **The two M08 records move on measured estimates, not only on a digest.**
   `catalog-search`'s tool spec estimate goes 294 → 287 tokens, and the residual
   differential's published sentence changes. The three `fresh-join.json` records move
   on the digest alone.
3. **The trajectory classification behind the first diagnosis stop is not committed.** It
   ran from the session scratchpad. Nothing in the close rests on it except the
   disclosure that it was read. It is the third reading in two milestones that did not
   reach the repository (journal, *What broke* 3).
4. **The brief's *"seven milestones"* did not reproduce.** Twelve closed between tag
   `m02` and this amendment, and the amendment lists them.
5. **`docs/pr-bodies/m09c-pr1.md:5` cites `f24b7a5` bare.** It resolves only through tag
   `cited-09c-pr1`, and nothing checked that. This is debt 6's instance.

## Close-milestone, in order

Step 2, step 6b and the artifact are **NOT EXERCISED**, all for one cause: no run was
taken. This is not a deferral. The files they read do not exist, and the journal names
each one.

| step | at this close |
|---|---|
| 1 DoD | item by item in the journal. PR 1 done; PR 2 not built as specified; PR 2b, 3 and 4 not taken |
| 2 evals | **NOT EXERCISED.** No goldens run exists, so no history entry is written |
| 3 journal | `milestones/M09c/README.md` |
| 4 row | filled: **closed RED** in the milestone cell, `✅` in the status cell, a close paragraph at the head of footnote ❋ |
| 5 claims | none of the twelve, by decision; no claims-table row moves |
| 6 ADRs | ADR-078 amendment 1 |
| 6b holes and costs | **NOT EXERCISED, both halves.** `milestones/M09c/topic-baseline.json` and `milestones/M09c/control/goldens-run-refusals.json` do not exist. Debt 10 is re-triggered. Retention: not met (no calls) |
| 7 tag | `cited-09c-close` on `d8f58c5` before the merge; `m09c` after. Every other SHA this PR's documents cite by backtick is on `main` |
| 8 demo | no act in `recordings.json` is owed by 09c. SPEC/09c's artifact is **NOT EXERCISED** |

`make check` was also run with the row already flipped, before the debt table was
drafted, on the commit that flipped it: **4721 passed, 8 skipped**. The flip surfaced no
obligation.

## Two-key

`python -m pave.cli gate two-key --changed` over this PR's paths:

```
two-key: not required — this PR touches no two-key path
```

No attestation is required. `docs/adr/`, `SPEC/`, `README.md` and `milestones/M09c/` are
on no rule, which is the standing debt carried at SPEC/09c:237.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

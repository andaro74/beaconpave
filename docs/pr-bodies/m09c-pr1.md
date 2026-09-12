## 09c PR 1 — the spec and its ADR: one claim, five falsifiers, the DMA rename cut

**Documents only.** No code, no runs, no corpus edits, **zero model calls**.

**Gate on the head:** `make check` at f24b7a5 (the documents commit, before this body
commit) printed **4704 passed, 8 skipped**, then `check: PASS`, exit 0.

### What is in this PR

| file | what |
|---|---|
| `SPEC/09c-answer-quality.md` | new, in SPEC/09's shape |
| `docs/adr/ADR-078-…md` | new, decisions 1–6 |
| `docs/adr/ADR-075-…md` | **amendment 8**, appended; decisions and amendments 1–7 not rewritten |
| `README.md` | row `09c` retitled; footnote ❋ gains one closing paragraph; nothing above it edited |
| `BUILD.md`, `SPEC/README.md`, `docs/adr/README.md` | the 09c row, the spec row, the ADR-078 row and ADR-075's amendment 8 |

`SPEC/09` is **not** edited. Its line 661 is superseded by quotation in ADR-075
amendment 8 §1.

### The claim, as pre-registered

The browse gap closes at the site a zero-call diagnosis names. The goldens count (**10/25
today**) then rises above a same-deployment control run, on the seven browse-gap cases,
with nothing else moving.

**Three terms, five falsifiers:**

- **F1**, the gap persists, at any call count
- **F2**, the seven do not rise
- **F3**, `N` does not rise
- **F4**, a 3-of-3 case falls, or a 0-of-3 case outside the seven passes
- **F5**, a case newly refused by majority

**The tiers and `p95_ms` are deliverables, not terms.**

### Measured to write it, all zero-call

1. **Every falsifier reader runs today, over M09's record** (ADR-078 D2):
   - `fresh_join.py --dir milestones/M09 --check` returns OK, exit 0.
   - The paired diff M08b → M09 prints `lost 1: grounded-017`, `gained 1: entitlement-011`,
     `net +0`, which reproduces amendment 6. `git status` was clean afterwards.
   - `evals.refusals --sidecar` prints 1/25 by majority and 4/25 at least once.
   - Every field each falsifier reads is present.
2. **A naive tier move and a naive gate move both make `fresh_join.py` refuse M08b's and
   M09's committed runs** (ADR-078 D5). This was measured in a `git archive` copy, never in
   the repository. It is why an era pin must land in PR 2, before either move.
3. **Every line citation** in the three documents was checked against the committed blob.
   73 of 73 hold; three wrong ranges were found and fixed before the commit.
4. **Nothing model-facing has moved since M09 run B:** `git log 369c8ba..HEAD` over those
   paths is empty.
5. **Two-key rule gaps**, measured by matching paths against `pave.twokey.RULES`:
   `milestones/M09c/fresh-join.json` and `tools/catalog-search/search.py` match no rule.
   They are dated to PR 2.

### Read before merging: five things the operator should decide or know

1. **The DMA rename has no existing trigger.** Every register row gives it a milestone and
   none gives an event. Amendment 8 records it as owned and unscheduled, no earlier than
   M11's close, quotes amendment 1 §6's standing condition, and writes **no** trigger,
   because that is Legal/S&P and Data Governance's decision.
2. **If its condition holds, the `p95_ms` rule loosens the gate from 5200 to 6700.** At
   6700, M08b's and M09's pooled readings read *within*. That is stated up front, and
   whether the move should wait for F1 is left to the PR 2b cold review.
3. **F1 and F4 each carry two clauses.** F4's are SPEC/09:57's own clauses 2 and 3. F1's
   scope is the seven at any call count, plus four-call samples outside the seven. If a
   clause is read as a falsifier of its own, the count is seven, not five.
4. **The spare is placed after PR 2, not after PR 1**, so the cold review reads the
   executors against their clauses rather than the prose. That is lesson 6.
5. **The brief's "M09b spent nine PRs, six of them prose"** does not match its journal.
   `milestones/M09b/README.md:311-313` counts **seven** containers. ADR-078 cites the
   journal's number.

**No stop condition was met.** The claim has three terms and five falsifiers. Every
falsifier's reader exists. Nothing found makes a workstream depend on the rename: the
browse-gap tool reads neither `dmas` nor `blackouts`, and PR 2's diagnosis must stop and
report if it finds otherwise.

### Keys

`python -m pave.cli gate two-key --changed` over this PR's files returns **"two-key: not
required"**. No attestation is owed. The standing debt *"no ADR and no spec is on any
two-key rule"* is unchanged.

### Deletability audit

No new assertions, so the audit is empty. Every changed file is Markdown.

### Cap

This is **PR 1 of six**. Then PR 2 (seated), PR 2b (the spare), PR 3 (the runs), PR 4
(the deliverables and debt 10) and PR 5 (the close).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

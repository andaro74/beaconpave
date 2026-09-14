## M11 PR 2b repair: the rulings on the cold review

**This PR runs nothing.** It runs no drill and applies no plant, and it makes no deploy, model
call or AWS call. **Nothing under `pave/`, `quality/`, `drill/` or `tests/` is edited.**
- **Nothing registered moves:** no pinned value, no falsifier, no reader.
- **`readers.txt` is not re-taken,** because no code it exercises changed.

**Gate on the head:** at `b3bd132`, the head before this body commit, in a clean worktree:
- `tests/test_drill_pins.py` printed **7 passed**;
- `python -m pave.cli check` printed **5286 passed, 8 skipped in 211.46s (0:03:31)**, then
  `check: PASS (hermetic — no cloud, no network)`, and exited 0.

`b3bd132` is tagged `cited-m11-pr2b-repair`, pushed before this body was committed.

**This is M11's fourth PR.** PR 2b (#160) merged at `7c327a8` before these rulings could land
in it. ADR-080 amendment 4, item 7, amends the cap to five PRs, and PR 3 is now the fifth and
closes the milestone.

**Merge with a merge commit or a rebase merge, never a squash** (ADR-080 amendment 1, debt 7).

### The rulings

| finding | ruling | where |
|---|---|---|
| **B1** | **Repaired.** The PR 3 run key was generated outside the repository: 32 random bytes as 64 lowercase hex, with one LF and no CR. The sha256 of the 64 bytes `pave.drill.load_key` returns from `$(cat …)` is committed, with its `key_id`. Nothing else about the key is committed | `milestones/M11/pre-registration/key.sha256` |
| **B2** | **Repaired.** The seeded validity row gains: *`drill verify` on R1 exits 0 printing `signature: OK`, and `signature.key_id` equals the first 16 hex of `key.sha256`*. A failed F3 liveness check is now an INVALID run | SPEC/11's validity table; `falsifiers.json`, verbatim |
| **B3** | **Repaired.** The control and fixed rows each gain *`drill verify` exits 0* | same |
| **B4** | **Downgraded to DEBT, D19.** PR 3's arc runs in a fresh clone of its branch, stated in the PR 3 body | SPEC/11's plan for PR 3 |

**Also in this PR:**
- **The review** records D12–D21 with owner and trigger. Its D1–D7 are renumbered D12–D18,
  after the audit's D8–D11. D17's trigger is *PR 3, after the fixed run*.
- **Amendment 1's debts:**
  - debt 4 is resolved;
  - debt 6's key half is resolved;
  - debt 5 is carried as D20;
  - debt 6's CRLF half is carried as D21.
- **F3's `liveness.on_failure`** in `falsifiers.json` now reads INVALID.
- **The control run's log** (34778857665) joins `milestones/M11/pr2-audit-logs/` and its index.
- **ADR-080 amendment 4** and its index row.

**One reader to rule on.** No registered reader prints `signature.key_id`. The seeded row names
`grep '"key_id"'` on R1 and `head -c 16` on `key.sha256`, both of which exist today.

**Nothing here is a seat's disposition (G6).** The attestations below were drafted for the
operator's confirmation.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: the registration gains three verify clauses carried verbatim from the spec, a failed liveness check now reads invalid, and no pinned value, falsifier or reader moves
Two-Key-Disposition: platform-eng
Two-Key-Rationale: the diff edits no writer, reader, schema, scenario or dispatch code, commits only the run key hash under the milestone record, and adds a fresh clone procedure for the arc
Two-Key-Disposition: security
Two-Key-Rationale: the run key is generated outside the repository and only its hash and key identifier are committed, and every run must now verify under that key before any falsifier is read

🤖 Generated with [Claude Code](https://claude.com/claude-code)

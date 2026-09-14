## M11 PR 2b: the cold review of PR 2's writer and readers (the spare)

**This PR runs nothing.** It runs no drill, applies no plant, and makes no deploy and no model or
AWS call. It edits no code, no pinned value, no falsifier, no reader, no `falsifiers.json` and no
`readers.txt`. SPEC/11 is not edited.

**The reviewer wrote none of PR 2** and had no context from it. The review works by reading
`main` at `6a5fbb7`.

**Gate on the head:** `python -m pave.cli check` at `aab2e3a`, the head before this body commit,
in a clean worktree, printed **5273 passed, 8 skipped in 200.24s (0:03:20)**, then
`check: PASS (hermetic — no cloud, no network)`, and exited 0. `aab2e3a` is tagged
`cited-m11-pr2b`, pushed before this body was committed.

**Merge with a merge commit or a rebase merge, never a squash** (ADR-080 amendment 1, debt 7).

### What is in the diff

| path | what |
|---|---|
| `milestones/M11/pr2b-cold-review.md` | the review: three sections, every finding graded |
| `milestones/M11/pr2-audit-logs/` | the 39 plant runs' CI logs, one file per run id, and `INDEX.md` |
| ADR-080, amendment 3, and its index row | one sentence: the logs are committed because run logs expire, and V01–V11 joined the checklist |

**Three 12-digit runs in two logs are split with `[split]`.** They are a runner temp-dir UUID
tail and a pytest-truncated all-zeros commit, and `tests/test_no_account_identifiers.py` reads
each as an account ID. The guard is not narrowed. Deleting `[split]` restores the fetched bytes,
whose sha256 is in the index. The control run's log is not copied.

### The three questions, answered

1. **Does each reader read the field its row names?** Yes, every one. `fix_window_s` is
   computed as `fix_by − ran_at`, which is SPEC/11's own definition.
2. **Does each checklist plant fire?**
   - **39 plants read** (R03–R10, V01–V11, S01–S06, K01–K06, F01–F08): **37 fire**.
   - **R09 and S03 have no witness.** Neither reaches a PR 3 reading (D1, D2).
3. **Anything true by construction?** No schema claim value, writer default, or reader import.
   **But F3 passes on any refusal** (B2).

### The findings, for your ruling before any repair

| # | grade | finding |
|---|---|---|
| **B1** | **BLOCKING** | Three carried debts (amendment 1, debts 4–6) are triggered between B and S. Paying any there makes the seeded run INVALID, so they can only land on `main` before PR 3 branches |
| **B2** | **BLOCKING** | F3 passes on any refusal. `verify` under a key other than the writer's refuses all three copies, and a failed liveness check has no registered meaning |
| **B3** | **BLOCKING** | F2 on the control run, F4, F5, and the control and fixed validity rows read artifacts no registered check has verified |
| **B4** | **BLOCKING** | `tree_clean` is porcelain, and skip-worktree still hides the writer and the scenario. Amendment 1 closed only the fixture's bytes |
| D1–D7 | DEBT | R09 shadowed; S03 inert; 18 any-refusal writer tests and W43 shadowed; event and tier read by no reader; the CLI loads the writer; PR 3's close must land after F; `max-gap` is a writer constant |

**No repair is in this PR.**
- Every BLOCKING remedy except one route of B1 is a registration change. If a repair is
  approved, it lands here with `readers.txt` re-taken and the registration revised verbatim
  (amendment 1, item 3).
- **Nothing here is a seat's disposition (G6).** The attestations below were drafted for the
  operator's confirmation.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: the cold review grades what each registered falsifier and validity row reads, and adds logs and a review under the milestone record without moving any registered value
Two-Key-Disposition: platform-eng
Two-Key-Rationale: the diff adds a review document, audit logs and an index under the milestone record, and edits no writer, reader, schema, scenario or dispatch code
Two-Key-Disposition: security
Two-Key-Rationale: the review names two signature findings for ruling, and the committed logs split three account shaped digit runs rather than narrowing the identifier guard

🤖 Generated with [Claude Code](https://claude.com/claude-code)

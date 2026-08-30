# ADR-054: the milestone published work it did not build, and nothing asserted the label

**Status:** Accepted. **Zero model calls.**
**Seats:** Platform Engineering (the progression table and `BUILD.md`) · Service
Team (the twelve-claims table, which is the page a reader meets first)

`README.md:41` and `BUILD.md:21` published M06 as *"2nd tool + consequence
interlock"*, and claim 10 — *consequence classes gate real actions* — carried `06`
in its `M` column. M06 built none of it. `SPEC/06` says so in its own words: *"No
consequence interlock, and claim 10 is not advanced… No second tool."*

The label survived eleven spec drafts, four milestones of the table being read at
every close, and a `grep` that returns exactly one hit outside the spec. **Nothing
asserts a progression row's description against what the milestone shipped**, and
`SPEC/06` decision 2 recorded that the description and slug are free and must be
rewritten. This executes it, and takes the decision decision 2 left open.

## What was decided

**M06 is renamed to what it shipped**, and the interlock work is renumbered to a
new `06b` row rather than folded forward or renumbered upward:

| | before | after |
|---|---|---|
| `README.md` M06 | 2nd tool + consequence interlock, `m06-consequence`, `–/25`, ⬜ | Attack register + two-key gate integrity, ten PRs, **21/25**, ✅ |
| `README.md` 06b | — | 2nd tool + consequence interlock, `m06b-consequence`, `–/25`, ⬜ |
| claim 10 `M` | 06 | **06b** |
| `BUILD.md` | one row | two rows, the second carrying `entitlement-check` and `publish-highlight` |

**Why `06b` and not the two alternatives.** Folding the interlock into M07 gives
one milestone the rules registry, the regdelta loop, Act 3, claim 6 *and* claim 10
— which is how M06 came to be overloaded in the first place. Renumbering 07–10
upward rewrites every downstream id in `README.md`, `BUILD.md`, the demo script's
act ownership and `recordings.json`'s `owed_by` fields, which is a large diff
across the deferral register this milestone just built a ratchet for, taken for a
cosmetic gain. `00a`/`00b` is direct precedent for splitting a milestone in place,
and it disturbs no tag and no recorded entry's `sha`.

## What this does not do

**It does not build the interlock, and it does not make claim 10 closer.** The
work is exactly where it was; only the label now matches. A renumbering that read
as progress would be the same defect pointed the other way.

**It does not add an assertion tying a row's description to what shipped**, and
that is the residual. The defect here was not that the label was wrong — labels go
wrong — but that it was wrong for eleven drafts with nothing able to notice. A
check would have to compare prose against a diff, and the honest options are a
seat reading the row at close (which is `close-milestone` step 4, and step 4 did
not catch this either) or a machine judgement about whether a description is true.
Recorded as owed rather than solved, because the shape of the solution is not
obvious and inventing one at a close is how the last four wrong guards arrived.

**One thing it does close.** `tests/test_history_append_only.py`'s
`test_a_published_number_with_no_entry_behind_it_is_red` borrows a live README row
whose goldens cell is still `–` and whose tag `README_GOLDENS` pins to nothing. It
expired at this close, as its own comment predicted it would, and is re-pointed to
`m06b` — the second time this anchor has moved. The comment now says the anchor
expires by construction rather than reading as a stable choice.

At scale, the progression table is generated from the milestone records rather than
maintained beside them, and a row that claims work no record contains cannot be
rendered; the interface already matches, because every row's tag already names an
eval history entry and a journal directory.

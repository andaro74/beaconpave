# M09b PR 5 — the close: RED, with the deploy not taken and the claim not measured

**Zero model calls and zero AWS calls. No deploy, no sweep, no run, no history entry.**
**No falsifier, threshold, band or candidate is edited, re-read or re-scoped.**
`candidates.json`'s `set_sha256` is unchanged, and SPEC/09b's claim, falsifiers and PR
checklist are byte-identical.

`make check`: **PASS, 4692 passed, 8 skipped**, at aaa7bec, the head of `m09b-pr5-close`
immediately before this body was committed. It was run once, in a clean worktree at
that commit. No delta against another count is published.

**Deletability audit: no new assertions; audit empty.** Every file this PR changes is
Markdown. SPEC/09b constraint 10 covers new assertions, so there is nothing to delete.

**Merge with a rebase merge.** The amendment, the row and the journal are three commits,
and the journal cites the amendment.

---

## What this PR does

| # | the ask | where it is |
|---|---|---|
| 1 | ADR-077 amendment 2 | **The additive topic's candidate is REFUSED under decision 2 §3.** `candidates.json:66` and `disclosure-shapes.yaml:1-2` are quoted at line and aligned word for word. The run *a person wrote it or denies that AI* (8 words) appears in the corpus and in no other file at the tree gate 2 reads. The comparison is published as-run for **both** candidates, and it clears the recalibration. `candidates.json:31` defines a term as one word, which is narrower than ADR-024:84-88's clause, and gate 2's executor, run at the same tree, prints `presumed_drawn: []` for both. No candidate edited, and no retry available or taken (ADR-077:127, :479-481; ADR-035 amendment 4:975-978). The index row names the amendment |
| 2 | close RED | `milestones/M09b/README.md`, *The verdict*. Term 1 closed on a defect found before measurement; terms 2 and 3 not measured; F1–F5 **not read** and none reported clean. Four reasons, each at line: nothing executes gates 3–7 (ADR-077:503-506, and the admission test's own :4-11); F4's second clause reads an `inputs_sha256` that `candidates.json` does not carry; *a sample that decides F1 or F3* is defined in none of the five places it appears; *PR 4's pre-registration check* appears only in the journal notes and PR 3's body. **The deploy was not taken** |
| 3 | the debts | Ten opened at the close, each with an owner and a trigger, none repaired. The seven named, the two found while writing the close (below), and Security's re-disposition of `enforcement-probing` (debt 10, UNSCHEDULED, owed since `milestones/M09/README.md:412-415`; re-disposing on M09's census and an advisory draft were both refused). SPEC/09b's inherited register is carried row by row, each row citing its source line. No catch-all row |
| 4 | row and status | README row 09b: **closed RED** in the milestone cell, then `seven PRs`, `not run`, `not judged`, `not run`, and a status cell of exactly `✅`, plus a close paragraph at the head of footnote ❊. The status cell holds `✅` and nothing else, because `tests/test_demo_recordings.py:45` swaps that exact cell string to build its synthetic tables. A first version wrote `✅ **RED** ❊` there, and `test_the_ratchet_fires_when_a_milestone_closes` went red on it. SPEC/09b's status is written **into line 14 in place**, so its line count does not move: ADR-077, ADR-076, `fg.py` and the journal notes cite SPEC/09b at line |
| 5 | journal, body | the journal; this body |

## Found while writing the close — recorded, not repaired

1. **`milestones/M09b/pr4-cold-read.txt` does not exist.** It is on no ref, local or
   remote (`git log --all` over the path is empty). A search of the operator's home
   directory found one cold-review file, PR 1b's, in another session's scratchpad.
   Every reason in the close is re-derived at line, and none rests on it. The journal
   records it under *What broke* 5, against SPEC/09b constraint 12.
2. **Debt 8: gate 2's executor passes a candidate the rule refuses.** This is the
   one-word reading in executable form. `tests/test_m09b_admission.py` is not changed,
   because rewriting it after the disposition it would have to agree with is the check
   fitted to the outcome.
3. **Debt 9: `docs/governance/demo-script.md:157-164` points Act 3's probe beat at
   `milestones/M09b/probes-run.json`**, which M09b never produced. It re-opens the row
   PR 1 paid.
4. **The disclosure pack re-run and its comparator pin slid for a reason *Bounded*'s
   fallback does not name** (SPEC/09b:560-563), so the slide is recorded as a finding.
5. **SPEC/09b's DoD "nothing moved" is checked, not assumed.** `git diff --stat 52edc27
   HEAD` over the no-move paths returns four files. Each is an expected PR 1 or PR 1d
   change: the era pin (two files), `phrasings.yaml`'s `frozen_before`, and
   `labels.json`'s `brand_tone` owe moving `re_deferred_to` from `M09b` to `M10`. **No
   label value moved.**

## Close-milestone, in order

Step 2, step 6b and the artifact are **NOT EXERCISED**, all for one cause: the deploy
was not taken. This is not a deferral. The four files they read do not exist:
`milestones/M09b/goldens-run.json`, `probes-run.json`, `topic-baseline-post.json` and
`goldens-run-refusals.json`.

| step | at this close |
|---|---|
| 1 DoD | item by item in the journal. PR 3 partial, PR 4 not taken |
| 2 evals | **NOT EXERCISED.** `goldens-run.json` and `probes-run.json` do not exist, so no history entry is written |
| 3 journal | `milestones/M09b/README.md` |
| 4 row | filled: **closed RED** in the milestone cell, `✅` in the status cell |
| 5 claims | none of the twelve, by decision; no claims-table row moves |
| 6 ADRs | ADR-077 amendment 2 |
| 6b holes and costs | **NOT EXERCISED, both halves.** `topic-baseline-post.json` and `goldens-run-refusals.json` do not exist, and neither the pre-deploy sweep nor M09's census is read in their place. Security's re-disposition of `enforcement-probing` is debt 10. Retention: not met (no calls) |
| 7 tag | the operator's, after the merge. Every SHA this PR's documents cite by backtick is already on `main` |
| 8 demo | no act in `recordings.json` is owed by M09b. SPEC/09b's artifact is **NOT EXERCISED**: its demo block reads the two post-deploy files above |

## Two-key

`python -m pave.cli gate two-key --changed` over this PR's six paths:

```
two-key: not required — this PR touches no two-key path
```

No attestation is required. `docs/adr/`, `SPEC/`, `README.md` and `milestones/M09b/*.md`
are on no rule, which is the standing debt at SPEC/09b:512, carried unchanged.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

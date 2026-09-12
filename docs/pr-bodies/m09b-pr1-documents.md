# M09b PR 1 — the spec, the ADR, the era pin paid, and `brand_tone`'s fifth slide

**Zero model calls. No deploy. No guardrail, corpus, case, tier, ceiling,
comparator or judge instrument moved.** `make check`: **4474 passed, 8 skipped**,
PASS.

M09 closed with claim 6 **FAILED** on two falsifiers. This opens M09b, and it is
written before the branch does any work: the spec, its decision record, and the
two inherited items that are binding on PR 1 rather than schedulable by it.

## What this PR contains

| | |
|---|---|
| `SPEC/09b-the-guardrail-line-and-the-topic.md` | the milestone, written before the branch was cut: one claim, five falsifiers, the derivation rule, the character budget, the reading rules, the cap, the seats |
| `docs/adr/ADR-076-…md` | M09b's decision record — new ADR, argued in its own opening rather than assumed |
| `docs/adr/ADR-075-…md` **amendment 7** | the two facts that belong in ADR-075 and nowhere else. **Pure tail append: 156 added, 0 deleted** |
| `milestones/M08b/residual_attribution.py` + both records | **the era debt, paid** |
| `tests/test_m08b_residual.py` | the pin retired **in the diff that pays it**; two guard tests in its place |
| `docs/adr/ADR-026-…md` **amendment 5** + `labels.json` | `brand_tone` re-deferred a **fifth** time, to M10 |
| `README.md`, `BUILD.md`, `SPEC/README.md`, `docs/adr/README.md` | row 09b and its own `❊` footnote; both ADR index rows |
| `docs/governance/demo-script.md` | Act 3's **third** correction, whose trigger had already fired |

## The era debt, paid — and what was measured

M08b's published attribution is estimated against HEAD's prompt and joined to
figures its run measured, so a prompt edit re-prices it with no run taken. It
happened at M09 PR 4: **501 of 463 signed (92.9%) → 552 of 402 (78.6%)**, and
`A` and `B` did not move at all.

The reader now carries an `m08b_era_text` block on its sibling's shape. Measured,
not asserted:

```
ERA: the prompt has moved since a9cf896 (milestones/M08/context-census.json,
services/highlights-agent/evals/answer.schema.json,
services/highlights-agent/gateway_client.py). M08b published F = 501 of 463 (92.9%)
and that reading stands; what follows is HEAD's recomputation against text that run
never sent.
```

**92.9% is neither corrected nor restored.** It is carried as `published_at_m08b`
and held by test to what commit `a9cf896` actually committed, so the constant
cannot be quietly moved to match whatever the record says today — which would be
the guard becoming a number that always said the new thing.

**The pin is retired in this diff and not before.**
`PROMPT_CONSTANTS_AT_M09_PR4B` existed to force this fix; a pin outlives its
purpose the moment the fix lands, and leaving it would meet the next legitimate
prompt edit with a red check pointing at work already done. The remedy it named
as inadmissible stays inadmissible: `inputs_sha256_at_m08b` records one commit's
text and is never updated, and `identical_to_head` is supposed to be false and
stay false.

**Deletability audit — 4 mutations, at check granularity, working copies backed
up to a temp directory and never restored with `git checkout`:**

| mutation | result |
|---|---|
| `era_text()` dropped from `record()` | **RED** — the reader cannot even produce a record (`KeyError` in `render`) |
| the committed record loses its era block, reader untouched | **RED** — 3 failed |
| the digests re-pinned to HEAD (*the inadmissible remedy*) | **RED** — 1 failed |
| `published_at_m08b` quietly "corrected" to 78.6% | **RED** — 2 failed |

Collected-test set changed by exactly **2 added, 2 removed** (diffed by test id,
not by totals).

## `brand_tone`, the fifth slide — the decision that most wants a second reading

Amendment 4 re-dated the owe to M09b on the ground that *"M09b is where the judge
moves: it re-freezes for its own reasons, and two re-freezes become one."*
`SPEC/09b` decides M09b re-freezes **nothing** and holds
`quality/judge/frozen.json` byte-identical, because moving the judge instrument
inside the milestone that moves the deployed control leaves no before/after that
either instrument feeds — ADR-018's hazard, twice in one diff. Amendment 1's own
reason (*"the next milestone that adds graded content"*) never fitted M09b either:
it authors no golden case, no judge axis, no rubric line.

So it re-dates to **M10**, where a `meridian-news` axis is added and the judge must
be re-frozen anyway — the first milestone at which *"two re-freezes become one"* is
true rather than asserted. `milestone_is_closed("M10")` resolves and returns False,
checked before the edit.

**The alternative is recorded and refused, with the argument that was *for* it:**
M03 measured 3 of 8 of the judge's own calls refused by `entitlement-circumvention`,
so a judge run after M09b's recalibration would be a second independent reading of
whether it worked. That is an argument for running the judge **after** M09b, not
inside it — the reading is only independent if the instrument does not move in the
same diff as the control. Taking both buys a second reading by destroying the first.

**Counted: five.** The ratchet is the only thing that makes a slide whose *reason*
changed visible, and this is the second of those.

## Four rule gaps, measured by running the gate rather than reading the list

Recorded in ADR-076 and scheduled into M09b PR 2/PR 3 — **not closed here**, because
each belongs in the diff that creates the artifact it covers (ADR-060's precedent).

1. `pave/rules.py`'s `CONTROL_ARTIFACTS["guardrail"]` admits neither
   `gateway-stack.ts` nor the synth snapshot. **The one control the registry was
   built to carry would read `chain: NOT RESOLVED`, exit 1, on claim 6's own
   command**, in the milestone that adds it.
2. `milestones/M09b/*` and `tests/test_m09b_*` are on **no** rule — the census
   clause names `milestones/M09/` and `tests/test_m09_`, and neither reaches `M09b`.
3. `^milestones/.*/topic-baseline\.json$` is an exact filename; M09b takes two sweeps.
4. `milestones/M09b/withheld-grants.json` is on no rule, and it decides M09b's own
   **F1**. Its four-seat rule names `M08b` alone, and folding it into the census
   alternation would drop **Legal/S&P**.

And a fifth that is not a rule gap: `test_documented_commands.py` runs every `bash`
demo block against `main`, and a spec is written before its artifacts exist.
`SPEC/09b`'s block ships as `text` with the reason beside it and the `bash` form
dated to PR 4.

## What this PR does not do

No branch beyond `m09b-pr1-documents`. No claim re-registered — M09's ❌ stands and
`SPEC/09`, its falsifiers and its *Bounded* section are not edited. No debt M09
handed forward is closed except the era pin, whose trigger this PR **is**. No
answer-quality work. No number moved: `gates.budgets.p95_ms` 5200, `tokens_in`
7700, every tier, comparator and instrument digest unchanged.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: the era block makes M08b's published attribution state on its own
  face that its estimates are priced against a prompt its run never sent, and holds
  92.9% to what that commit committed rather than letting a constant drift to match
  today's record; and the brand_tone owe re-dates because M09b re-freezes nothing,
  so widening the draw there would move the judge instrument inside the milestone
  that moves the deployed control it is supposed to measure

Two-Key-Disposition: platform-eng
Two-Key-Rationale: the reader gains a guard its sibling has carried since M08 and
  this one lacked, computed from the committed inputs rather than asserted, and the
  pin that forced the fix is retired in the same diff so the next legitimate prompt
  edit does not meet a red check pointing at work already finished

Two-Key-Disposition: security
Two-Key-Rationale: re-pinning the digests to a new prompt stays refused by name and
  by test, because that is the guard being deleted by the change it exists to catch;
  and the judge instrument does not move in this milestone, so no recorded
  observation changes meaning while a control is being recalibrated

ADR: docs/adr/ADR-076-the-topic-is-reworded-under-a-rule-written-first.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

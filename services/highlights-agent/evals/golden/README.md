# Golden set — highlights-agent (Meridian Sports)

**Owning seat:** AI Quality. Two-key (`Two-Key-Disposition: ai-quality`) on every
change, enforced by the `two-key` check.

25 cases. `disclosure-004` is deliberately absent — M07 adds it as the
MER-AI-0001 disposition, which is claim 6. The gap in the numbering is the
reservation.

## The rule that matters most

**Never edit a case to make a run pass.** If a case is wrong, fix it in its own
PR with the reasoning. A case edited to accommodate an answer stops measuring the
answer.

These cases were authored at M00a, **before the control ever ran**. That ordering
is not incidental: a case written after seeing the baseline's output is a case
shaped by the baseline, and it silently flatters every milestone measured against
it afterwards.

## The evaluation clock

The suite evaluates at a fixed instant:

```
2026-09-13T18:00:00Z
```

One hour before the Jefferson Derby kicks off (t001), one week before the Cedar
Point Rowing Finals (t005). This is what makes "tonight's derby" coherent and
"hasn't started yet" true, deterministically and offline (G8). A case may
override it with a `now:` field; none currently do.

A wall-clock suite would start failing on its own after the events pass, and the
first instinct would be to edit the cases — which is the one thing this file
forbids.

## Case shape

```yaml
- id: blackout-006
  input: "..."                    # the viewer's turn, verbatim
  viewer: { plan: sports-tier, dma: port-william }   # structured context; the
                                  # tool needs values, not prose. Mirrors `input`.
  fixtures: [data/catalog.json]
  asserts: [...]                  # deterministic; these carry the blocking weight
  judge:
    axes: [groundedness, completeness]
    rubric: quality/judge/rubric-sports.md
    expect_near_threshold: false  # true marks a deliberate headroom case
  trajectory:
    expect_tool_before_answer: entitlement-check   # scored from M06
  provenance: { author: human }
```

## Assert vocabulary

This list **is** the contract the M03 harness implements. A case may not use an
assert that is not here; `tests/test_contracts.py` enforces that, so a typo'd
assert key fails the build instead of silently never running.

| Assert | Meaning |
|---|---|
| `json_schema: <path>` | the answer validates against `answer.schema.json` |
| `must_mention: <str>` | case-insensitive substring present in `answer` |
| `must_not_claim: <str>` | substring **absent** from `answer` |
| `must_cite: [<id>…]` | every id listed appears in `cited_titles` |
| `cited_titles_in_fixture: true` | **every** cited id exists in the fixture catalog. Vacuously true on an empty citation list — pair it with one of the next two |
| `cites_at_least_one: true` | the answer cites **something**. The half `cited_titles_in_fixture` cannot express: an answer that cites nothing confabulates nothing |
| `cited_titles_empty: true` | the answer cites **nothing**, because the subject is deliberately absent from the catalog. Fails if the model invents a citation |
| `entitlement: {entitled, reason}` | the structured verdict matches exactly |
| `entitlement_source: entitlement-check` | the verdict came from the tool, not the model. **Recorded, not scored, until M06** — the control claimed the tool it does not have in 10 of 11 cases (ADR-016) |
| `budget: {model, tokens_in, tokens_out, max_ms}` | per-model token ceiling (ADR-014 — **not** dollars) plus a per-request hang guard. Latency percentiles are suite-level, in the manifest (ADR-016) |

### The vacuous groundedness pass, and why the fix is additive

`cited_titles_in_fixture` computes `set(cited) - known`. On an **empty** citation
list that set is empty, so the assert passes: an answer that cites nothing
confabulates nothing, and it clears a groundedness check by not attempting to be
grounded.

SPEC/02 pre-registered this for `grounded-019` and marked the pass unearned. M02
then found the same shape doing real damage on `edge-025`: PASS in both arms and
recorded as *unchanged* by the paired diff, while the control cited `t001` and the
tools arm cited nothing. The true loss count was 4, not the 3 the diff showed —
and no check reading verdicts alone could see it.

**Three intents, so three keys rather than one redefined key.**

| the case expects | assert |
|---|---|
| specific titles | `must_cite: [t001, …]` |
| some title, unspecified | `cites_at_least_one: true` |
| no title, because the subject is not in the catalog | `cited_titles_empty: true` |

`cited_titles_in_fixture` is **not** redefined. It is referenced by all 25 cases
and by recorded history, and an assert key whose meaning changes underneath a
recorded score is ADR-016's hazard in its purest form. Each key means what its
name says, and `test_no_case_can_pass_groundedness_by_citing_nothing` fails any
case that carries the vacuous shape alone.

**The obvious fix would have been wrong.** Making an empty citation list simply
fail punishes `grounded-019` and `entitlement-012`, where the subject — the Harbor
Bay Invitational — is not in the catalog and citing nothing *is* the correct
answer. Measured on the committed runs, that version dropped `m00b` 18 → 17 and
`m01` 19 → 17, moving both comparator pins for no gain. The additive version moves
neither: it costs only `edge-025` in the M02 tools arm and `brand-021` in one
control sample, which is exactly what it was aimed at.

**What it does to two recorded unearned marks**, in opposite directions.
`grounded-019`'s pass becomes *earned* — it now clears `cited_titles_empty`, a
check that can fail — while `edge-025`'s becomes a FAIL in the tools arm. The
recorded entries are untouched; history is append-only.

### Asserts a correct answer fails

`must_mention` and `must_not_claim` are substring checks, and a negative
substring check is the easiest assert in this vocabulary to get wrong. Several
cases were authored at M00a with bans that a **correct** answer trips:

- `must_not_claim: "blackout"` on a case where the right answer is "no blackout
  here, you're set"
- `must_not_claim: "upgrade"` on a case whose right answer rules an upgrade out
- `must_not_claim: "free"` on a case whose right answer says "not available free
  in your market" (this one shipped in the starter)
- `must_not_claim: "won"` on a case whose right answer is "we don't have the
  result, so I won't guess" — and which also fires on "I wonder"

All were replaced by the structured `entitlement` verdict, which says exactly
what the case means, or by a specific phrase that can only appear in a wrong
answer. **A case a correct answer cannot pass is a broken case, not a hard one**,
and it fails in the most expensive way: it looks like a system defect.

This is not an exception to "never edit a case to make a run pass." No run has
happened. Fixing these *after* a recorded score would require its own PR with the
reasoning and an AI Quality review — which is exactly what that rule is for.

### Why the structured verdict does the heavy lifting

`cited_titles_in_fixture` is the groundedness check, and it is deterministic on
purpose. Asking a judge "did this seem grounded?" is strictly worse than checking
whether the ids the answer relied on exist. CLAUDE.md prefers a deterministic
assertion wherever one can express the requirement; this is the main place that
preference pays.

`entitlement_source` is a constant until M06, when `entitlement-check` exists —
scoring it before then produces a green number that means nothing. Same reasoning
as `expect_tool_before_answer`, and deliberate.

## What the control is expected to fail

Written before the M00b run, per SPEC/00b. Recorded outcomes go in
`milestones/M00b/`, not here.

- **Every `entitlement_source` assert.** The control has no tool; it emits
  `model-inference` by construction.
- **Most blackout and entitlement cases.** The control guesses from catalog text.
  `blackout-006` (entitled by tier, still blacked out) and `edge-024` (local
  event with no blackout) are the ones a plausible-sounding guess gets wrong in
  both directions.
- **The groundedness traps** (`grounded-017`, `grounded-018`, `grounded-019`).
  The whole catalog sits in the control's context, which is what invites
  confabulation.

If the control passes one of these, the case is too easy — record the pass
as-run, mark it **unearned**, and draft the tightening. Do not strengthen the
control and do not edit the case.

## Headroom

`headroom-005` and `headroom-026` are authored to sit near the judge threshold —
2 of 25, 8%. They are not defects. A suite at 100% can only report "no change or
regression"; improvements become invisible and the progression table stops being
able to show that anything got better.

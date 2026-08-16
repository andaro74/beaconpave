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
| `cited_titles_in_fixture: true` | **every** cited id exists in the fixture catalog |
| `entitlement: {entitled, reason}` | the structured verdict matches exactly |
| `entitlement_source: entitlement-check` | the verdict came from the tool, not the model |
| `budget: {model, tokens_in, tokens_out, p95_ms}` | per-model token and latency ceiling (ADR-014 — **not** dollars) |

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

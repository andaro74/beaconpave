# Golden set — game-recap-agent (Meridian Sports)

**Owning seat:** AI Quality, and **one key** — `Two-Key-Disposition: ai-quality`,
enforced by the `two-key` check through `^services/[^/]+/evals/`.

This file replaces the one `pave new` rendered. The template renders the
reference service's README with the heading changed, and that README describes a
25-case pack with an entitlement tool, an ungoverned control and a headroom
section naming cases that do not exist here. `cases.yaml` tells you to read this
file first, so it has to describe this pack. The template defect is Platform
Engineering's and is recorded in `docs/samples/game-recap-agent.md`.

## The rule that matters most

**Never edit a case to make a run pass.** If a case is wrong, fix it in its own
PR with the reasoning. A case edited to accommodate an answer stops measuring the
answer.

These cases were authored on 2026-09-16, **before any run of this service**. No
answers exist and nothing has been recorded to `evals/history/`. That is the one
window in which a case may be fixed without its own PR, and it was used once: the
AI Quality seat found twelve `must_not_claim` bans a correct answer could trip,
and they were replaced before the pack was ever scored.

## The evaluation clock

The suite evaluates at the same fixed instant as the reference service:

```
2026-09-13T18:00:00Z
```

One hour before the Jefferson Derby kicks off (t001), one week before the Cedar
Point Rowing Finals (t005). The Granite Falls Classic (t003) is a replay with no
result in any catalog field. A case may override the clock with a `now:` field;
none do.

## Case shape

```yaml
- id: recap-001
  input: "..."                    # the viewer's turn, verbatim
  viewer: { plan: base, dma: granite-falls }   # a real plan and a real DMA
  fixtures: [data/catalog.json]
  asserts: [...]                  # deterministic; these carry the blocking weight
  judge:
    axes: [groundedness, completeness, brand_tone:meridian-sports]
    rubric: quality/judge/rubric-sports.md
  expect_near_threshold: true     # TOP-LEVEL, only on a deliberate headroom case
  provenance: { author: human }
```

`expect_near_threshold` is a top-level key. `pave/floors.py` reads it there and
nowhere else; a flag nested under `judge:` is never seen, and the row 9 refusal
that follows names the wrong cause (ADR-045).

## Asserts this pack uses

The full vocabulary and its rules are the reference service's, in
`services/highlights-agent/evals/golden/README.md`. This pack uses eight of them:

| Assert | Used for |
|---|---|
| `json_schema: <path>` | every case; the answer validates against `answer.schema.json` |
| `cited_titles_in_fixture: true` | every case; a cited id absent from the catalog is a confabulation |
| `must_cite: [<id>…]` | a case whose question makes citing a specific title the correct answer |
| `cites_at_least_one: true` | `edge-018`, the ambiguous request |
| `cited_titles_empty: true` | `grounded-006`, a subject the catalog does not hold |
| `must_mention: <str>` | a name a correct answer must contain |
| `must_not_claim: <str>` | narrative-result phrasings, see below |
| `budget: {...}` | every case; the template's one-tool numbers |

Every case carries `must_cite`, `cites_at_least_one` or `cited_titles_empty`, so
no case passes groundedness on an empty citation list. Citation contracts are
forced by the question: a case that needs `must_cite` asks about the title in a
way a correct answer cites.

### What the bans can and cannot do

`must_not_claim` is a substring check, and any phrase that describes a result can
be negated by a correct answer: "the winner was" sits inside "the catalog doesn't
record who the winner was". So the pack bans three narrative phrasings only
(`came out on top`, `ran out winners`, `sealed the win`), which a written recap
uses and a hedge does not. They catch a recap that reads like a recap. They do
not catch every invented result, and nothing in the vocabulary can: there is no
structured "no result exists" assert. The judge's `groundedness` axis is on every
result case and is the control for the rest.

**Owed, AI Quality:** a structured assert for "the catalog holds no result for
this title", so that an invented score is caught deterministically. A vocabulary
change is two-key and lands in its own PR with `tests/test_contracts.py`.

### What this pack deliberately omits

- **No `entitlement:` verdict, no `entitlement_source`, no `trajectory`.** The
  manifest grants `catalog-search` and nothing else. An assert on a tool the
  service is not granted can never pass.
- **No `ai_disclosure` assert.** MER-AI-0001 reaches every case whose answer is a
  preview, a tile or a recommendation: `preview-010`, `preview-011`,
  `preview-012`, `recommend-013`, `brand-016`, `headroom-020`, and arguably
  `brand-015`. The rule's executable control is a disposition pack of its own
  suite, never a golden case (ADR-075 decision 4). **No such pack exists for this
  service, and no control binds the rule to it.** That is an obligation owed to
  Legal / Standards & Practices, recorded in `docs/samples/game-recap-agent.md`
  against the rule's 2026-10-01 review. It is not discharged by this file.

## What reads this pack, and what does not

`pave verify game-recap-agent` reads it for four things: the disposed-case floor
(row 8), the headroom band (row 9), unknown top-level keys (row 11) and the
budget keys (row 12).

**Nothing else reads it.** `tests/test_contracts.py` and the CI evals step are
pinned to `services/highlights-agent`. The assert-vocabulary, vacuous-groundedness,
catalog-id and viewer-vocabulary checks that protect the reference pack do not
run on this one. The AI Quality seat ran them against this pack by repointing the
test locally and every one passed, but a check that ran once on a laptop is not a
protection. Extending `tests/test_contracts.py` past its hard-coded path is
two-key (`ai-quality`, `platform-eng`) and is recorded as owed.

## Headroom

`headroom-019` and `headroom-020` are flagged, 2 of 20, **10.0%**. The band is
5–10% inclusive, so this sits on the upper edge: a third flag at twenty cases is
red, and deleting any one unflagged case (2/19) is red. Both flags are predictions
until a run exists.

# Judge rubric — Meridian Sports

**Owning seat:** AI Quality. Changes to any threshold in this file are two-key
(AI Quality **plus** the owning service team) and must be their own PR.

**Status at M00a: not in use.** The judge and its calibration set land at M03
(ADR-012). This file exists because `cases.yaml` references it; scoring against
it before the 30-case calibration run would produce a number with no published
agreement behind it, which is exactly what G9 forbids.

## Two audiences, and where the line is

**Everything from `## Axes` to `## Headroom` is sent to the model verbatim.**
`evals.judge.rubric_axes` slices exactly that range, and both digests — the whole
file and the slice — are pinned in `quality/judge/frozen.json`.

Everything outside that range is for a reader: seats, status, boundaries with
other suites, corpus policy. **Do not put reviewer commentary inside an axis.** It
becomes model-facing text the moment the judge reads the file, which is M02's tool
`description` finding in a new place — and the `## Headroom` section, which tells
the reader that some golden cases are deliberately near-threshold, is exactly the
kind of thing a judge must not be told before it scores one.

A band definition belongs in an axis. Everything else belongs here.

## What the judge is for, and what it is not for

The judge adds nuance the deterministic asserts cannot express — tone, whether
an answer is *usefully* complete rather than merely correct. It never carries the
blocking weight alone. Where a requirement can be written as a deterministic
assert, it must be (CLAUDE.md, Style). Groundedness on this service is checked by
`cited_titles` membership in the fixture catalog, not by asking a model whether
the answer seemed grounded.

A judge is **calibrated or advisory**. Its agreement with hand labels is
published in `evals/history/` as `judge_agreement`. Below threshold it is demoted
to ADVISORY automatically and cannot block a merge. Relabelling the calibration
set to recover agreement is prohibited.

### The boundary with the Security seat

**ADV-005 (off-brand-tone) is not graded here.** A probe passes when the guardrail
blocked it, not when the judge disliked the output (G4). A low tone score is a
quality signal; it is never an adversarial pass.

This used to sit inside the `brand_tone` axis, which put it in front of the model
once the judge started reading the rubric. It is a note between two seats about
which suite owns which failure, and a judge has nothing to do with it.

## Axes

### `groundedness`
Every claim traces to a cited catalog title. Invented titles, invented start
times, invented entitlement tiers all score 0 regardless of how plausible the
prose is. **Deterministic pre-check:** `cited_titles ⊆ catalog`. The judge scores
only what survives that check.

| Score | Meaning |
|---|---|
| 1.0 | Every factual claim traces to a cited title |
| 0.5 | Claims are consistent with the catalog but reach beyond what is cited |
| 0.0 | Any claim contradicted by, or absent from, the catalog |

### `completeness`
Does the answer resolve the viewer's actual question, including the part they did
not know to ask? "You can't watch it" is correct and incomplete; "you can't watch
it here tonight because of a blackout, and the replay is available tomorrow" is
complete.

| Score | Meaning |
|---|---|
| 1.0 | Answers the question and the obvious follow-up |
| 0.5 | Answers the question only |
| 0.0 | Partial, evasive, or answers a different question |

### `brand_tone:meridian-sports`
Warm, energetic, knowledgeable — a fan talking to a fan. Never cruel about rival
teams or their supporters, never hyperbolic about outcomes, never a hard sell on
an upgrade. Enthusiasm about the sport is on-brand; enthusiasm about the paywall
is not.

| Score | Meaning |
|---|---|
| 1.0 | On-brand and natural |
| 0.5 | Accurate but flat, or mildly salesy about an upgrade |
| 0.0 | Cruel, profane, hyperbolic, or reads as an advertisement |

### `concision`
Length proportional to the question. A one-line question does not get four
paragraphs.

| Score | Meaning |
|---|---|
| 1.0 | Proportionate |
| 0.5 | Padded but readable |
| 0.0 | Padded to the point of burying the answer |

### `disclosure_present`
Activates at M07, when MER-AI-0001 is disposed. AI-authored editorial copy
carries the disclosure in `ai_disclosure`. Binary: present and accurate, or 0.

## Headroom

2–3 cases in the golden set are authored to sit near this rubric's threshold
(`expect_near_threshold: true`). They are not defects to be fixed. A suite at
100% can only report "no change or regression" — improvements become invisible,
and the progression table stops being able to show that anything got better.

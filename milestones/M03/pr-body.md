# M03 — eval harness + judge calibration

**Status: in progress. Do not merge.** Opened early so `gate` and `two-key` run
on every push — workflows only fire on PRs to `main`, so a milestone branch with
no PR gets no CI at all.

Claim 9 — *judges are calibrated or advisory*. **Both artifacts now exist.** The
published agreement number is `milestones/M03/judge/held-out-report.json` and the
auto-demotion test is in `tests/test_judge.py`.

**The result is that no axis is calibrated and the judge is advisory in full.**
Twenty held-out items at `k_judge = 3`, prompt frozen before the split was read:
`brand_tone` 0.00 (n=3), `completeness` 0.00 / κ −0.19 (n=5), `concision` 0.67
(n=3), `groundedness` 0.00 (n=6). Every axis demotes on two independent rules.
The AI Quality seat's correction rate is published beside it: **0 of 20**.

**A judged score therefore cannot differ from its deterministic score.** `veto()`
consults only calibrated axes and there are none. Read the progression table's
judged column as *the judge was measured and found unfit to move this*, never as
*the judge concurred*.

## The commits, in order, because the order is the milestone

An agreement number computed on the set the judge was tuned against measures
nothing, and no test can prove label independence — only the history can. So the
spec is committed before the corpus, the corpus before the labels, and the labels
before any judge prompt exists in the tree.

| # | commit | what |
|---|---|---|
| 1 | `7900a98` | `SPEC/03-evals.md`, before any code |
| 2 | `ad12bb5` | the 30-item calibration corpus, **with no labels** |
| 3 | `18368d2` | 30 drafted labels, **before any judge prompt exists** |
| 4 | `39d4734` | a commit SHA is not a stable name for a commit |
| 5 | `a65a9f9` | the seat disposes 30 of 30; the correction-rate prediction is falsified |
| 6 | `d53eb79` | `evals/judge.py`, the hermetic half |
| 7 | `bea1f43` | `run_judge.py`, through the gateway under its own identity |
| 8 | `87d974d` | the guardrail refuses the judge; the pre-registration is off by an order of magnitude |
| 9 | `cb02310` | the narrowing is live and the judge is still refused half the time |
| 10 | `de1accc` | the corpus was sized against a threshold, not against a refusal rate |
| 11 | `6359f8f` | the freeze — untuned, and said so |
| 12 | `ef1a1af` | the held-out number, and no axis survives it |
| 13 | `eebfe06` | `instrument`, not `supersedes` |
| 14 | `c0f8759` | four seats reviewed; the test named for the defect did not test it |
| 15 | `b149572` | the guardrail version, read from the records rather than from the stack |
| 16 | `9ef9e69` | instrument B: the freeze could not see the half that was refusing the calls |
| 17 | `192ae26` | the split-aware runner, and the resume that must not mix instruments |

(SHAs 1–4 are post-rebase; the pre-rebase ones are gone, which is the fourth
finding below.)

**#21 is merged and this branch is rebased onto it.** The account-ID guard matched
any twelve-digit run, and a sha256 has roughly a 17% chance of containing one;
this branch commits thirty digests, so it could not be green until that landed.

## Decisions this PR asks the seats to read

**The thresholds are fixed in the spec, before any number exists to fit them to.**
Demotion at raw exact-band agreement below `0.75` per axis; an axis with fewer
than five *scorable* held-out items is demoted regardless; an axis with more than
20% undecided items at `k_judge = 3` is demoted regardless. Raw agreement is the
trigger and κ is the check on it, named in that order in advance.

**`supersedes` is the wrong verb for the m00b anchor.** ADR-012 committed M03 to
re-score the control and append an entry carrying `supersedes`. The entry is
warranted — a judged number is a model output nobody can regenerate, which is
what `evals/history/` is for — but `supersedes` means *corrects a wrong entry*,
and 15/25 is not wrong. `k` and `arm` do not close the gap either: same system,
same bytes, different instrument. M03 adds an `instrument` field and amends
ADR-012 in place.

**A demoted judge must not block, and the obvious implementation makes it block.**
`ADVISORY` already carries two meanings — "axes recorded, not scored" and "no
strict majority" — and the second one blocks in `emit_verdict`. A demoted judge
emitting `ADVISORY` axes would block every case it touched, which is the opposite
of the rubric's promise. Demotion is therefore implemented as *the axis does not
enter `result`*.

**The labels are ai-proposed, and the spec says what that costs.** The drafter and
the judge are both Anthropic models, so shared priors are the expected failure
mode, and they inflate agreement in a way κ cannot detect — κ corrects for chance
agreement, not for correlated error. G6 is what makes it legitimate: provenance is
`ai-proposed`, every label carries `drafted` and `final`, and the correction rate
is published beside every agreement figure in the same sentence. A rate near zero
cannot distinguish good drafts from a rubber stamp, so it is reported as a
limitation and never as a validation.

**The judge became a second instrument, and the freeze could not see it.** The
four-seat review flagged that `judge.user_turn` opened with `VIEWER QUESTION:` /
`VIEWER CONTEXT:` and that `viewer` is a `SUBJECT_TERM` in the gateway's
classifier. Reproduced: `entitlement-012`'s recorded answer says the event "may
be listed under a different name", `name` is an `ATTRIBUTE_TERM`, and the pair
classifies `sensitive`. The instrument supplied the subject half of a
personal-data refusal and the answer under test supplied the attribute half.
Swept across all eight committed agent runs it refused 9 of 169 case-by-answer
renderings, on `entitlement-012` and `grounded-019`. **The fix is in the
instrument and never in `platform/gateway/core/classify.py`** — the control was
not wrong, the judge really was sending it a subject term.

What the fix turned up is worse than the fix. `user_turn` was a Python literal
whose own docstring read *"this is instrument text … a word changed here changes
every band"*, and **not one of the four frozen digests covered a single one of
those words**: the function could be replaced wholesale and `is_frozen()` still
returned `True`. Two different instruments could have recorded one fingerprint —
precisely the confusion `instrument` was added to `evals/history/schema.json` to
make impossible, and the republished number would have carried marks identical to
the first one's. The template moves to `quality/judge/user-turn.md`,
`instrument()` gains `user_turn_sha256`, and `frozen.json` becomes **instrument
B** while recording instrument A beside it — A's four digests, its template
recovered verbatim from `b149572`, and its `user_turn_sha256` as `null` with a
note. A digest written there now would read as a pin that existed at the time.
The absence is the finding.

A's prompt, rubric, rubric-axes and rendered digests are byte-identical to B's.
Only the user turn moved, and both of its differences are recorded — the two
labels, and one trailing newline nobody expects to move a band — because the
re-run's delta has to be attributable to the whole difference and not only to the
interesting half.

## Three findings from drafting, all recorded before disposition

**`brand_tone` has zero label variance.** All five applicable items drew `0.5` and
nothing else. An axis whose labels are one value cannot produce a meaningful
agreement number: a judge answering `0.5` to everything scores 1.00 raw, and κ has
no baseline to correct against. It is a finding about the corpus rather than the
judge, and not a labelling failure either — three milestones of a governed sports
agent produced nothing cruel, hyperbolic or salesy, and nothing warm. It is
demoted on the insufficient-evidence rule anyway, so nothing published changes.
Widening the stratum is owed to AI Quality for M04; doing it here would be
choosing items after seeing their label distribution.

**A third not-applicable shape.** `m02-tools-1 / grounded-018` is a turn the
harness could not decode — `unparsed`, no `answer` field — which is neither an
answer nor a refusal. The spec named two shapes and now names three, with `cal-13`
in the corpus so the behaviour is pinned rather than assumed.

**The five-item floor counts *scorable* held-out items.** Four drawn items carry
no answer at all, so the counts are groundedness 6, completeness 5, brand_tone 3,
concision 3. Recorded explicitly because the direction matters: it makes the floor
**stricter**, and it was written before any label was disposed and before any
agreement number existed. `completeness` now sits exactly on the boundary at 5 and
is not moved to accommodate that.

## A fourth finding, from the rebase itself

**A commit SHA is not a stable name for a commit, and this milestone leaned on
one.** The calibration draw is salted with the SHA of the commit that
pre-registered the thresholds, so that choosing a salt after seeing which items it
selects is not available. The rebase onto #21 moved that commit to `815b172`, and
the salt still reads `6a851c0` — a commit not reachable from this branch and never
pushed, so no reader can look it up.

It is deliberately not updated. The salt's value *is* the draw — every item's sort
key is `sha256(SALT|run|case|axis)` — so changing it selects thirty different
items, and redrawing after the corpus and its labels are written is exactly the
re-roll the salt exists to prevent.

What was load-bearing survives: a rebase changes a commit's parents and not its
patch, so `git rev-parse 815b172:SPEC/03-evals.md` still yields the byte-identical
spec content that fixed the thresholds. Only the name is stale. The correction is
recorded in `evals/calibration.py` and the corpus README, with a test asserting a
reader arriving at either finds it — and the general lesson written down, which is
worth more than the instance: **a content hash would have survived a rebase and a
commit SHA does not.**

## What is still owed on this branch

- the instrument-B held-out re-run, and **both** numbers published — A and B, with
  the instrument named against each. The A number is not withdrawn: it is a
  correct measurement of an instrument that was really in use, and the seat that
  reads it is entitled to see what changed and what did not
- the `m00b` judged anchor at `k_judge = 3`, carrying `instrument` and **no**
  `supersedes`
- a judged history entry. `instrument`, `judge_axes` and `guardrail_refusals` are
  in `evals/history/schema.json` and **nothing writes them into `evals/history/`
  yet** — schema only
- SPEC/01's guardrail-refusal band asserted at suite level, reporting only
  (two-key: AI Quality **and** Security)
- the `m01` cut recorded, and both M02 arms cut with the reason recorded
- the progression table's judged column
- three ADRs — the judge as a pinned instrument whose raw output is committed; the
  calibration corpus size and freeze rule; `instrument` versus `supersedes` — plus
  the ADR-012 amendment, and an ADR-024 falsification amendment
- `quality-gate.yml`'s L2 evals lane, still commented `# turns on at M03`
- `milestones/M03/README.md`, the DoD ticks, and the tag

**Landed since the four-seat review:** the seat-review fixes (`c0f8759`), the
guardrail-version source (`b149572`), instrument B (`9ef9e69`), and the
split-aware runner (`192ae26`). The review ran **before** the judged runs, as
SPEC/03's own definition of done requires — and it is what found both the
`assemble()` undecided-drop and the G1-shaped hole, so the ordering earned its
place.

## Reviewing seats

AI Quality (corpus, labels, thresholds — two-key) · PM (the spec) · Platform
Engineering (the gateway path the judge will use) · Security + Data Governance
(the guardrail refusal finding this milestone measures and does not fix)

Two-Key-Disposition: ai-quality
Two-Key-Rationale: The calibration corpus and its labels are the reference every
published agreement number will be measured against, so both were fixed before any
judge prompt existed in the tree and the ordering is visible in the commit history
rather than asserted afterwards. The corpus is drawn by a committed deterministic
rule salted with the SHA of the commit that pre-registered the thresholds, so it
is reproducible by anyone and cannot be re-rolled after seeing which items it
selects; a contract test re-runs the draw on every check, so neither the rule nor
the corpus can move without the other. Items are drawn from already-committed
answers rather than authored, because agreement measured on hand-written band
anchors overstates what the judge does on real output. Labels declare themselves
ai-proposed in their own provenance block and every one carries both the drafted
and the final band, so the correction rate from this seat's disposition is a
published number rather than an unrecorded act; the judge runner will refuse to
run until all thirty are disposed. No threshold is relaxed here: the only
threshold change is the clarification that the five-item evidence floor counts
scorable held-out items, which tightens it, and it was written before any label
was disposed and before any agreement number existed. The freeze
(`quality/judge/frozen.json`) is a two-key act in its own right and is disposed
here: freezing pins the instrument so that "the prompt was not tuned against the
measured half" is a check rather than a promise, and the record says in its own
text that the prompt was frozen **untuned** — the dev pass yielded four judged
case-instances and two borderline disagreements, too little signal to tune
against, and tuning toward labels drafted by this same model family is the
circularity the 0% correction rate already flags. Re-freezing to instrument B is
disposed on the narrower ground that it changes no band definition: the prompt,
the rubric and the rubric axes are byte-identical to instrument A and the digests
of all four are recorded side by side in the file for anyone to diff. The
instrument moved because it was supplying half of a classification refusal and
because the freeze had a blind spot the size of the entire user turn; neither is a
reason to relax a threshold and none is relaxed. Instrument A is retained rather
than overwritten, and its number will be published beside B's rather than replaced
by it, because withdrawing a correct measurement of an instrument that was really
in use is exactly the history rewrite `supersedes` exists to keep visible. The
history schema change (`instrument`, `judge_axes`, `guardrail_refusals`) is
disposed on the same reasoning ADR-012's amendment records: a judged number is a
model output nobody can regenerate, so the row has to say which instrument
produced it, and `supersedes` cannot carry that because it means *corrects a wrong
entry* while a moved instrument corrects nothing. `judge_axes` and
`guardrail_refusals` are additive and reporting-only — no recorded score changes
by their presence, and `guardrail_refusals` exists so that the largest
unexplained cost in the platform is visible in the history rather than only in a
milestone README. The rubric is edited here
and the edit moves no band and no threshold: a seat-boundary note about ADV-005 is
lifted out of the brand_tone axis into the reviewer-facing half of the file,
because everything inside an axis is now sent to the model verbatim and that note
is written for two seats rather than for a judge. The judge prompt is new, is
hash-pinned together with the rubric slice it embeds, and cannot score the
held-out half until those digests are frozen in a commit.

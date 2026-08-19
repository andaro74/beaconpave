# M03 — eval harness + judge calibration

**Status: in progress. Do not merge.** Opened early so `gate` and `two-key` run
on every push — workflows only fire on PRs to `main`, so a milestone branch with
no PR gets no CI at all. The definition of done in `SPEC/03-evals.md` is mostly
unticked and the judge does not exist yet.

**#21 is merged and this branch is rebased onto it.** The account-ID guard
matched any twelve-digit run, and a sha256 has roughly a 17% chance of containing
one; this branch commits thirty digests, so it could not be green until that
landed.

Claim 9 — *judges are calibrated or advisory* — with two artifacts owed: a
published agreement number and an auto-demotion test.

## What is committed so far

| commit | what |
|---|---|
| `815b172` | `SPEC/03-evals.md`, the branch's first commit, before any code |
| `ea9ca2c` | the 30-item calibration corpus, **with no labels** |
| `647e2c3` | 30 drafted labels, awaiting the AI Quality seat's disposition |
| *this one* | the rebase correction below, and this body |

(Those SHAs are post-rebase. The pre-rebase ones are gone, which is the fourth
finding.)

**The commit ordering is the milestone.** An agreement number computed on the set
the judge was tuned against measures nothing, and no test can prove label
independence — only the history can. So the spec is committed before the corpus,
the corpus before the labels, and the labels before any judge prompt exists in
the tree. At this commit there is still no judge prompt anywhere.

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

- disposition of all 30 labels by the AI Quality seat, before the judge runs
- `evals/judge.py` (hermetic) and `run_judge.py` (through the gateway — G1)
- `instrument` and `guardrail_refusals` in the history schema
- the m00b judged anchor at `k_judge = 3`, and both M02 arms judged
- `milestones/M03/judge-agreement.json` and `tests/test_judge_demotion.py` — the
  two halves of claim 9's artifact
- the four-seat review, **before** any judged run
- the `cited_titles_in_fixture` tightening, which lands in its own PR from `main`
  first: it moves both comparator pins and makes `edge-025` the fourth loss in
  M02's paired diff, and letting it drift in here would make every judged delta
  unattributable

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
was disposed and before any agreement number existed. The rubric is edited here
and the edit moves no band and no threshold: a seat-boundary note about ADV-005 is
lifted out of the brand_tone axis into the reviewer-facing half of the file,
because everything inside an axis is now sent to the model verbatim and that note
is written for two seats rather than for a judge. The judge prompt is new, is
hash-pinned together with the rubric slice it embeds, and cannot score the
held-out half until those digests are frozen in a commit.

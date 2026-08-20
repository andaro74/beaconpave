# ADR-025: The judge is a pinned instrument, its text lives in files, and its raw output is committed

**Status:** Accepted (M03)
**Seats:** AI Quality (the judge, the rubric, the freeze — two-key) · Platform
Engineering (the gateway path the judge calls through) · Security / Red Team (the
classification interaction recorded below)

## Context

ADR-018 stated the rule this ADR is the fourth instance of: **anything that
decides a score is an instrument, and an instrument that can move without a commit
will move without anyone noticing.** ADR-012 was the judged/unjudged split,
ADR-016 the two instrument corrections, ADR-018 the `DRAFT` guardrail.

The judge is the worst case so far, for two reasons that compound.

It is the **first instrument in this repo whose output can move without any change
at all**. A guardrail moves when someone edits it in a console; a judge returns a
different band on the same input on a Tuesday. `k_judge = 3` and `majority_band`
exist for that, and they reduce the variance without removing it.

And its input is **prose**, spread across four artefacts — a system prompt, a
rubric slice embedded into it, a catalog embedded beside that, and the user turn
each case is framed by. Every one of them is model-facing text where a changed
word changes every band, and none of them looks like configuration.

M03 found out what that costs. The freeze pinned four digests and **the user turn
was not one of them**. It was a Python string literal inside `evals/judge.py`
whose own docstring read *"this is instrument text, so it lives beside the prompt
rather than in the runner: a word changed here changes every band"* — an accurate
description of a thing no digest covered. The function could be replaced wholesale
with unrelated text and `is_frozen()` still returned `True`.

That was found by fixing a different bug. The user turn opened with
`VIEWER QUESTION:` / `VIEWER CONTEXT:`, and `viewer` is a `SUBJECT_TERM` in the
classification router. ADR-018 closes by saying the router *"can tell 'who plays
for the Rovers' from 'list subscriber addresses'"* — and it can, but the judge was
prefixing every case with a subject term, so a case whose recorded answer happened
to contain an `ATTRIBUTE_TERM` classified `sensitive` and was refused. Across the
eight committed agent runs this refused 9 of 169 case-by-answer renderings. **The
instrument supplied half of a control's refusal condition, and the refusal was
then recorded as evidence about the gateway.**

Had the user turn been fixed without the digest being added, the re-run would have
published a second number carrying marks **identical** to the first one's.

## Decision

**1. The instrument is five digests, and every one of them is file-backed.**
`instrument()` records `prompt_sha256`, `rubric_sha256`, `rubric_axes_sha256`,
`rendered_sha256` and `user_turn_sha256`. `is_frozen()` checks all five.
`rendered_sha256` covers the catalog the judge grades groundedness against, which
is why editing `data/catalog.json` cannot slip past a pin on the prompt alone.

**2. Model-facing text lives in a file, never in a Python literal.** This is the
specific lesson and it generalises past the judge: a digest can pin a file, and
nothing pins a string in the middle of a module. The corollary is a convenience
rather than a principle, but it matters — the *rationale* stays in the docstring,
so explaining an instrument does not manufacture a new one. A source-level digest
would have made every clarifying comment a new instrument, and the pressure would
then be to stop writing the comments.

**3. Freezing is a recorded act, and `held_out_guard` enforces it.** Iterating the
prompt against the dev split is allowed for as long as it takes. Scoring the
held-out split before the prompt stops moving is refused, because an agreement
number computed on the set the judge was tuned against measures nothing. The guard
raises rather than warns, and it raised for real between the user turn moving and
the re-freeze — which is the only kind of evidence that a guard works.

**4. Instruments are named, retained, and never overwritten.** `frozen.json`
carries the current instrument at top level and every previous one in
`instruments`. Instrument A's entry records its four digests, its user-turn
template recovered verbatim from `b149572`, and its `user_turn_sha256` as `null`
with a note. **The null is deliberate.** Back-filling a digest there would read as
a pin that existed at the time; the absence is the finding, and a reader is
entitled to see that the first published number was measured by an instrument that
was only four-fifths pinned.

**5. A moved instrument produces a new entry carrying `instrument`, never
`supersedes`** (ADR-027). A number measured under instrument A is not wrong. It is
a correct measurement of an instrument that was really in use, and withdrawing it
is the history rewrite `supersedes` exists to keep visible.

**6. Every difference between two instruments is recorded, including the boring
ones.** Instrument B differs from A in the two labels and in one trailing newline.
Nobody expects a newline to move a band. "Nobody expects" is not a measurement,
and the re-run's delta has to be attributable to the whole difference rather than
to the interesting half of it.

**7. The raw model output is committed for every judged run.** The call is the part
nobody can regenerate. Everything after it — bands, majority, veto, agreement,
demotion — is a pure function in `evals/judge.py`, which is hermetic and inside
`HERMETIC_ROOTS`. That split is what lets a stranger with no AWS account re-derive
every published number from the tree.

**8. An instrument is fixed in the instrument, never in the control.** The `viewer`
finding is fixed in `quality/judge/user-turn.md` and **not** in
`platform/gateway/core/classify.py`. The control was not wrong — the judge really
was sending it a subject term. Weakening a live control so an instrument can
measure more comfortably is the trade this repo exists to refuse, and here it
would have been a one-word deletion from a tuple.

## Consequences

Changing any judge text now requires a re-freeze, which is a two-key act with a
disposition and a rationale in a PR body. That is the intended friction, and it is
more friction than the guardrail's version bump because prose is easier to edit
than infrastructure and just as load-bearing.

Two numbers now exist for the held-out split and both stay published. A reader has
to look at `instrument` to know which is which, which is a real cost — and it is
the cost of the alternative being a single number that silently changed meaning.

`plan.reusable()` refuses to resume a run across instruments, so an instrument
change re-spends the whole split rather than the remaining steps. That is correct
and it is not cheap: it is the difference between one report and one report
containing two instruments with nothing in the number to separate them.

The judge's own calls pass through the guardrail and the classifier under a
distinct service identity (`judge-highlights`), so its refusals are countable
separately from the agent's. M03's measured refusal rate on those calls is high
enough to be the milestone's largest unexplained cost, and it is recorded as a
finding owned by M01's second owed tightening rather than fixed here.

**At scale, replace with:** a prompt registry with versioned, content-addressed
entries — the instrument selected by version rather than by digest comparison, and
a judge whose registry entry is promoted through environments like any other
artefact. The interface already matches: `instrument()` returns the identity, the
history row carries it, and `frozen.json`'s `instruments` list is a registry with
one reader.

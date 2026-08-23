# ADR-042: append-only never constrained what a NEW row may claim, and the directory that anchors two gates takes one key

**Status:** Proposed. Written before the code. **Zero model calls.**
**Seats:** AI Quality (`evals/history/`, the recorded numbers) · Security / Red
Team (the adversarial entries, and what a probe passing means) · Platform
Engineering (the recorders, the lane that reads an entry, the workflow)

Discharges ADR-041 decision 3.

**This is the second draft, and the first one was aimed at the wrong threat.**
Four seats reviewed it, each planting and running in a worktree. All four
answered *"does any reachable input let a recorded number change with everything
green?"* with **YES**, and the cheapest route was one draft 1 did not consider.
Its central mechanism — a git-commit anchor — is **withdrawn**. What was wrong is
recorded below rather than quietly replaced.

## The threat, corrected

Draft 1 assumed the attack is **editing a committed row**. Measured by the AI
Quality seat and reproduced here: the cheaper attack is **appending a new one**.

```
appended evals/history/m01-goldens-corrected.json
  real   m01 scores: passed 19 of 25
  new    row claims: passed 24 of 25    same `sha`, schema-valid
  -> 1701 passed, pave check exit 0
```

**Append-only forbids an edit. It says nothing about what a new row may claim.**
A new file has exactly one commit by construction, so every commit-counting check
passes it by definition. Draft 1 would have shipped a control that is blind to
the first thing anyone would try.

So there are two threats and this ADR must name both:

- **T1 — a fabricated row is appended.** Untouched by draft 1. Cheapest.
- **T2 — a committed row is edited.** Draft 1's subject, addressed partially.

## What exists, measured

- **The recorders refuse to overwrite.** That guards creation of a *duplicate
  filename* and nothing else. A different filename is free.
- **Nothing reads a committed entry for change** except ADR-041's
  `HISTORY_DIGESTS`, which covers **three of eight** entries and is a snapshot: a
  ninth entry is pinned by nothing.
- **`evals/history/` takes one key** (`ai-quality`).
- **`evals/run_evals.py` — the golden recorder — is on NO two-key rule**, while
  its twin `run_adversarial.py` takes two. Draft 1 justified Platform
  Engineering's key by naming *both* recorders. A protection stated in prose and
  absent from the enforced list, arriving inside the sentence that invokes it.

### A history entry is a live gate criterion, and draft 1 said it was not

Draft 1 argued Security needed no key because *"a history entry is a record of
something that happened"* rather than a live criterion. **That is false, and the
code proving it is mine.** `pave/cli.py:900` reads an entry's `scores.total` and
feeds it to `asked_floor`, a gate **failure** condition (ADR-041 decision 5):

```
entry says scores.total = 11  ->  gate floor = 11
entry says scores.total =  7  ->  gate floor =  7
```

And `pave/floors.py:88` asserts that value *"is append-only and digest-pinned, so
it is **not a value the same PR can invent**."* **A new arm's entry is written by
the PR that records it.** That guarantee is false as shipped. It is corrected
here, and recorded against ADR-041 rather than left for a reader to find.

## Decisions

### 1. The whole of `evals/history/` takes three keys: AI Quality, Security, Platform Engineering

**ADR-030 met this exact shape and chose the union.** One path holding two
suites, and it called the union *"over-broad in the direction of more review —
the fail-closed direction."* Draft 1 met the same shape, picked the narrower set,
and did not cite it.

The measurement that settles it: a fabricated adversarial row claiming 10/10 for
`m04` needed only `ai-quality` and `platform-eng` — **never the seat that owns
what a probe passing means.** Security asked for the key formally, with that
plant as the argument. Granted.

Platform Engineering stays, but not as draft 1's "disinterested counterweight" —
that reasoning was wrong and AI Quality dismantled it. They own the recorders, so
a bad entry implicates *their* code, which gives them an interest in
dispositioning it quietly rather than permanently. **The motivating incident is
exactly that shape**: a recorder/schema change, resolved by overwriting. They hold
a key because they own the lane that reads an entry into a gate decision, and the
third key is what makes the pairwise audit come out clean.

**The whole directory, `schema.json` included, with no exclusion pattern.** Draft
1 exempted the schema as "a contract, not a measurement". It is a protection *on*
the measurements, enforced by both recorders — relaxing it on one key while the
measurements take three is a pairwise inversion, and a seat planted it green.
And draft 1's prediction 6 spelled the rule `evals/history/*-*.json`, which
requires a hyphen: implemented literally, **7 of 10 path shapes dropped to no
rule at all**, including `goldens.json`, the repo's own canonical example in
`pave/tests/test_twokey.py`. A decision that adds a key must not remove one from
a neighbour. One prefix, no exceptions, nothing to get subtly wrong.

### 2. The byte pin is primary, and it must be COMPLETE

Draft 1 made a git-commit count primary. The repository had already recorded why
that is wrong, in `tests/test_judged_entry.py:274`:

> *"The gate checks out at depth 1, so it skipped on **every CI run** and asserted
> only on a deep clone — the milestone's load-bearing arithmetic, verified
> nowhere that mattered. **A byte is reachable from a shallow clone forever, and a
> commit is not.**"*

So: **every entry's content is digest-pinned, and the set of pins must equal the
set of entries on disk.** Exact-set, never a subset.

The completeness half is what does the work, and it closes four separate holes
with one assertion:

- **T1** — an appended row is an unpinned entry. Caught.
- **A rename plus rewrite in one commit** — the new path is an unpinned entry.
  Caught. (Security measured that `git log` cannot see this at all, and that
  `--follow` fails *hardest on the largest rewrites*, because git's rename
  heuristic gives up past ~50% dissimilarity. **The bigger the lie, the more
  append-only it looks.**)
- **A ninth entry with no pin** — caught, where draft 1 left it free.
- **The whole directory deleted** — the pinned set no longer equals the empty
  set. Draft 1's git check reported PASS over zero files, which is the
  `rules_validate` hazard it cited against shallow clones and reproduced itself.

**What this buys and what it does not.** Pinning a row does not make it true — a
row added and pinned in one PR is still that PR's claim. What it buys is that
adding one is **deliberate, visible and attested by three seats**, where today it
is a file appearing in a directory nobody checks. That is ADR-013's concession
restated, and it is the honest claim.

### 3. The git check ships as a NARROW secondary, claiming only what it does

Withdrawn as an anchor; kept for the one thing four seats confirmed it does:
**it defeats the digest re-pin remedy.** Rewrite an entry and re-pin its digest,
and the commit count still moves. That is real, unremediable within the PR, and
worth having.

Everything else about it is stated as a limit rather than left to be discovered:

- **Squash-merge erases the evidence at merge.** This repo squash-merges every PR
  since #30. A create-then-rewrite inside one PR lands as one commit; CI catches
  it pre-merge on `refs/pull/N/merge`, and an audit of `main` afterwards gets a
  false clean. It is a property of the pre-merge branch, not of the repository.
- **It cannot detect its own draft-1 motivating example** under today's merge
  strategy. Two seats replayed it.
- **It is blind to T1, to rename-plus-rewrite, and to an evil merge.**

And it must not fire on honest work. Two shapes measured on draft 1's design:

- **A freshly recorded entry has ZERO commits**, so `make evals` then `make
  check` was **red**, telling an operator that an entry which has never existed
  had been rewritten.
- **CI checks out `refs/pull/N/merge`**, so an honest two-commit PR — record,
  then fix a timezone after review — was accused of rewriting append-only
  history. **The remedy a developer learns from that is *squash your branch*,
  which is exactly what hides the malignant case.** ADR-041's B-0 pattern
  returning: a false accusation, aimed at the wrong seat, from the check guarding
  the anchor.

So the check runs over **committed** entries only, tolerates an uncommitted one,
and refuses explicitly — `git rev-parse --is-shallow-repository`, a work-tree
probe, and a `FileNotFoundError` guard for a missing `git` — rather than passing
quietly. `quality-gate.yml` gains `fetch-depth: 0`; measured cost **+140 ms and
+534 KiB**, not the "real cost paid by every run" draft 1 claimed.

### 4. A second reading gets its own verb, because `supersedes` is the wrong one and unwritable besides

Draft 1's decision 5 said *"`supersedes` is already the correct verb."* Both
halves are wrong.

**Wrong verb.** ADR-027 defines `supersedes` as *the earlier entry was wrong*.
The M03 entry was not wrong — its `scores` and `cases` are byte-identical across
the rewrite. It is a **fourth** reason for a second entry that ADR-027's taxonomy
has no field for: *same system, same answers, same instrument, re-read because
the schema grew a field*. Pointing at `supersedes` mislabels a correct
measurement as a mistake, which is the precise thing ADR-027 refuses.

**Unwritable.** No recorder has a `--supersedes` flag, `run_evals.record` actively
refuses to write the field, and the filename scheme has no component
distinguishing a correction — so the append-only guard would refuse the
superseding entry too. Meanwhile two committed tests validate **every** entry
against the current schema, so the day `schema.json` gains a required field,
every entry goes red, editing is forbidden, and superseding is unbuildable. **A
wall with no door, reachable by a schema change alone.**

So ADR-027's taxonomy gains a fourth field, a recorder flag that writes it, a
filename component that lets it land, and a test that records one end to end.
`supersedes` keeps meaning what ADR-027 says it means.

### 5. What a second row under one SHA must declare

T1's floor. Two entries sharing `sha` and `suite` must differ in a **declared**
dimension — `arm`, `instrument`, or the new re-reading field. A row that shares
both and declares nothing is refused. Measured on today's schema, all of these
validate and must not:

```
PERMITTED  a second entry, same sha, 25/25, declaring nothing
PERMITTED  supersedes: "not-a-sha-at-all"     (no such commit, no such entry)
PERMITTED  an entry that supersedes ITSELF
```

### 6. Every protection this ADR adds goes on a two-key path

Draft 1's prediction 7 failed for the third time in this repository: the check
module and its only test took **no rule**, so the whole control deleted on one
key with the suite green. `pave/twokey.py` enumerates protection tests by name
already; this adds the fifth. **`evals/run_evals.py` gets the rule draft 1's
prose already claimed it had.**

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | an appended row claiming a number no run produced **fails on `main` as it stands**, once the completeness assertion exists, and passes before it | it passes after — then completeness does not close T1, which is the threat draft 1 missed |
| 2 | `set(HISTORY_DIGESTS) == set(entries on disk)` catches all four of: an appended row, a rename-plus-rewrite in one commit, a ninth unpinned entry, and the directory deleted | any survives — then one assertion is not doing the work four holes need |
| 3 | the git check catches a rewrite **whose digest was re-pinned in the same PR**, and is honestly recorded as blind to T1, to rename-plus-rewrite and to a squashed intra-PR rewrite | it catches none of what it claims, or the blindness is not written down |
| 4 | the git check does **not** fire on an uncommitted freshly-recorded entry, and does **not** fire on an honest two-commit PR under `refs/pull/N/merge` | either fires — then it teaches squashing, which is the move that hides the real attack |
| 5 | it **refuses**, with a named message, on a shallow clone, on a tree with no `.git`, and with `git` absent from PATH — never passes, never raises a bare traceback | any passes quietly — the `rules_validate` hazard. Any raises — an errored CI step is not a stated block |
| 6 | `pave gate two-key` demands **ai-quality, security AND platform-eng** for every path under `evals/history/`, `schema.json` included, and no path in that directory drops to fewer keys than today | one drops — draft 1's glob dropped 7 of 10 shapes to none |
| 7 | **no protection is deletable on fewer keys than the thing it protects, anchors included** — audited pairwise over every file this ADR touches | one is. **Failed three times: ADR-041 prediction 6, ADR-042 draft 1, and again in the seats' builds** |
| 8 | a second entry sharing `sha` and `suite` and declaring no distinguishing dimension is **refused**, and `supersedes` must resolve to a committed entry and may not be self-referential | any validates — then decision 5's floor is not enforced |
| 9 | a re-reading can be recorded end to end by a real recorder invocation, and `pave check` is green afterwards | it cannot — then decision 4 names a verb no tool can produce, which is how this defect arose the first time |
| 10 | no committed entry's `scores` or `cases` changes, and no `README.md` number moves | any moves — then this ADR edited history while claiming to protect it |

Prediction 1 is load-bearing, for ADR-037's reason. Prediction 7 has now failed
three times and is carried as a discipline, not a claim.

## What draft 1 got wrong

- **Wrong threat.** Built against editing; appending is cheaper and was untouched.
- **The "already broken" framing is WITHDRAWN.** Draft 1 opened with *"the rule
  was broken, benignly, and nothing noticed."* Both commits are inside PR #22,
  merged by `892a241`, so the entry's first form was never on `main` — and the
  repository did notice. `f7fb24e`'s own message: *"It has never been on `main` —
  append-only protects merged history, and a row that cannot resolve its own
  pre-registration is not a record of it. Score unchanged at 18/25."* That is a
  documented reading of the rule, written at the time. **The check draft 1
  proposed enforces the very reading that commit used to defend itself**, and its
  prediction 1 would have "proved" the check works by flagging a record that
  pre-emptively answered it.
- **The central premise was self-refuting.** *"There is no constant here for the
  same PR to re-pin"* — `GRANDFATHERED` is that constant; widening it silences
  the git half.
- **Decision 1's "record, not a live criterion" was false**, disproved by ADR-041
  code I wrote.
- **Prediction 4 was unfalsifiable** and would have been recorded confirmed: on a
  shallow clone every entry reports 1 commit, so seven of eight pass, and the
  only failure was the exemption firing for the wrong reason with the wrong blame.
- **Predictions 6 and 7 both created holes** rather than closing them.
- **The baseline was wrong.** 1701 at `46f0c97`, not the 1699 quoted — that was
  `main` before the ADR file added two index tests.

## Consequences

- The directory that anchors two gates stops being editable on one key.
- **T1 acquires a control for the first time.** Nothing has ever constrained what
  an appended row may claim.
- **ADR-041's `floors.py` guarantee is corrected**, not quietly. It says a value
  cannot be invented by the same PR, and it can.
- Recording an entry costs three attestations, and `close-milestone`'s step 2 —
  two bare `--record` commands — must carry the digest step, the seats, and the
  re-reading flag. CLAUDE.md calls that skill a checklist, not a suggestion.
- `evals/history/schema.json` moves from one key to three. A schema change is
  rare and consequential; both recorders enforce it.

## What this ADR does not do

It does not change a recorded number, a threshold, a baseline, a guardrail or a
probe. It does not re-score any suite, register an instrument, or spend a model
call. It does not claim the git check establishes that history is append-only —
draft 1 did, and four seats falsified it.

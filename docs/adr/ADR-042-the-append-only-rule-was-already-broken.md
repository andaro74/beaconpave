# ADR-042: the append-only rule was already broken once, nothing noticed, and the file that anchors every arm's question set takes one key

**Status:** Proposed. Written before the code. **Zero model calls** — every check
here reads committed files and git metadata.
**Seats:** AI Quality (`evals/history/`, the recorded numbers) · Platform
Engineering (the recorders, the workflow, the git anchor) · Security / Red Team
(the adversarial entries, and what an arm's question set rests on)

ADR-041 decision 3 named this with an owner and did not close it. This is that
ADR.

## The rule, and the measurement

CLAUDE.md:

> *"History is append-only JSON keyed by git SHA + suite. Never rewrite history
> entries; a wrong entry gets a superseding entry."*

ADR-027 calls `evals/history/` *"the repo's central honesty mechanism: every row
came from a real execution, and a wrong row is corrected by a new row rather than
by an edit."*

**It has already been broken.** Measured on `main` at `d9f8a3b`:

```
entry                            commits  digest-pinned
m00b-adversarial.json            1        YES
m00b-goldens.json                1        no
m00b-judged-B-goldens.json       2        no        <-- rewritten after recording
m01-adversarial.json             1        YES
m01-goldens.json                 1        no
m02-control-goldens.json         1        no
m02-tools-goldens.json           1        no
m04-adversarial.json             1        YES
```

`m00b-judged-B-goldens.json` was written by `298dfd8` and **edited by `f7fb24e`**:

```
sha         unchanged
scores      IDENTICAL          cases  IDENTICAL
recorded_at 2026-08-20T21:14:48Z -> 2026-08-20T23:18:52Z
guardrail_refusals              gained `classification: 0`
```

**No published number moved.** The entry was re-recorded two hours later under a
schema that had grown a field, and the file was overwritten instead of
superseded. `recorded_at` now names a time the original measurement was not
taken.

**That is the good case, and it is exactly when to build the protection.** The
rule was broken benignly, by the person who wrote the rule, in the milestone that
wrote it, and nothing in the repository noticed. Nothing would have noticed if
`scores.passed` had moved instead.

## What exists and what does not

- **The recorder refuses to overwrite.** `run_evals.py` and
  `run_adversarial.py` both check the path and exit rather than clobber. That
  guards *creation*.
- **Nothing guards a committed entry afterwards.**
  `test_history_stays_append_only` runs in a `tmp_path` and asserts only that
  recording twice refuses; it never reads a committed file. ADR-041 verified this.
- **Three of eight entries are digest-pinned**, by `tests/test_arm_scoping.py`,
  and only because ADR-041 needed an anchor. **The five golden entries carry the
  numbers `README.md` publishes** — 15/25, 18/25, 19/25, 17/25, 16/25 — and are
  guarded by nothing.
- **`evals/history/` takes one key** (`ai-quality`), while the protection resting
  on it takes three. ADR-041's prediction 6 named that inversion and could not fix
  it without reopening this ground.

## Decisions

### 1. Two keys on `evals/history/`: AI Quality **and** Platform Engineering

G9 is the whole reason: *whoever feels a control's pain never solely controls its
strength.* The seat that would want to reset a baseline is the seat that owns the
baselines. Platform Engineering owns the **recorders** — `run_evals.py`,
`run_adversarial.py` — and feels none of the pain of a number that moved.

`evals/history/schema.json` keeps its existing single key. It is a contract, not
a measurement, and adding a second seat to a schema edit taxes the wrong act.

**Not Security, and this is the seats' to overturn.** The adversarial entries are
Security's subject matter, and `evals/comparators.json` takes three keys under
ADR-030 precisely because it holds two suites. The counter-argument, and the one
this ADR takes: `comparators.json` holds *live criteria the gate decides on*,
while a history entry is a record of something that happened. Two keys make the
edit non-silent; a third makes every recording ceremony. If Security wants the
adversarial half, that is a narrower rule on `*-adversarial.json` and it should
be argued as one.

### 2. The anchor is **git**, not a constant

Append-only means **added once and never touched**. So `git log --oneline -- <path>`
naming more than one commit **is** the violation, directly, with nothing to
interpret.

This is strictly better than a pinned digest, and the reason is a failure mode
ADR-041 measured on itself: **a digest pin's routine remedy is "paste the new
hash in", which is a step of the attack it exists to stop.** A check whose normal
failure mode trains people to perform the forbidden move is worse than a check
that cannot be quietly satisfied. There is no constant here for the same PR to
re-pin.

Proposed by the Service Team seat in ADR-041 round 3 and verified there against a
planted rewrite.

**The digest pins stay too**, and are extended to all eight entries. They are not
redundant with the git check: a digest catches a rewrite in a working tree before
it is committed, and the git check catches one that is. They also fail
differently, which matters — a shallow clone silences the git check.

### 3. The git check must fail loudly on a shallow clone, never pass quietly

`quality-gate.yml` uses `actions/checkout@v4` with the default `fetch-depth: 1`.
`two-key.yml` already sets `fetch-depth: 0`, so the precedent and the cost are
both known.

`quality-gate.yml` gains `fetch-depth: 0`. And the check **refuses** rather than
skips when history is unavailable: a test that silently passes because it could
not look is the `rules_validate` hazard this repo names repeatedly — *a validator
reporting success over zero files reports success after somebody deletes the
directory.*

### 4. `m00b-judged-B-goldens.json` is grandfathered, by name, with the diff recorded

It cannot be un-edited. Rewriting history to hide a history rewrite is absurd, and
deleting the entry destroys a real measurement.

So the exemption is **one file, named literally**, with what changed recorded
beside it — and it is an **exact-set** pin, never a `<=`. ADR-041 measured why:
ADR-040's own population pin used `<=`, and deleting *every* `channels` key from
an arm left it passing, because that arm was already in the permitted set. A
subset check sees a population grow and is blind to a file falling into it.

The exemption covers **this file and this diff**. If it is touched again, or if
any other entry gains a second commit, the check fails.

### 5. `recorded_at` is what a re-record must not silently move

The observed edit moved `recorded_at` while `scores` and `cases` held. That is
the benign shape, and it is also the shape a re-record takes when a number *does*
move. The superseding-entry mechanism ADR-027 built exists for this and was not
used, because nothing required it.

Named here rather than mechanised: the git check makes any second write visible,
and `supersedes` is already the correct verb. What is added is that the rule now
has a check behind it.

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | the git check **fails on `main` as it stands**, naming `m00b-judged-B-goldens.json` and no other entry | it passes before the exemption exists — then it does not test the rule, and it is the decoration ADR-037 was about |
| 2 | with the exemption, `main` is green, and **adding a second commit to any other entry turns it red** | it stays green — then the exemption is broader than one file |
| 3 | touching `m00b-judged-B-goldens.json` again **also** turns it red | it does not — then the exemption is open-ended rather than pinned to one diff |
| 4 | the check **FAILS, not skips**, on a shallow clone — verified by cloning at `--depth 1` | it passes — then CI can silence the whole control by a checkout setting |
| 5 | all eight entries are digest-pinned; a content rewrite is caught by the digest **and** the git check independently, verified by disabling each | either misses — then the two are one protection wearing two names |
| 6 | `pave gate two-key` demands `ai-quality` **and** `platform-eng` for any `evals/history/*-*.json` edit, and still **one** key for `schema.json` | fewer, or the schema is caught up in it |
| 7 | **no protection is deletable on fewer keys than the thing it protects**, audited pairwise including anchors | one is — this is ADR-041's prediction 6, which held only after an audit found two violations |
| 8 | no published number in `README.md` moves, and no committed entry's `scores` or `cases` changes | any moves — then this ADR edited history while claiming to protect it |

Prediction 1 is load-bearing: a check written after an exemption that would have
passed before it has proven nothing.

Prediction 4 is the one I expect to be got wrong. A `git log` over a missing
history returns empty, and empty reads as "one commit or fewer", which passes.

## Consequences

- The repository's central honesty mechanism acquires a check. It has had a rule
  and a docstring since M03 and nothing that reads a committed file.
- **ADR-041's anchor stops being weaker than what rests on it.** That was a
  pairwise inversion of its own prediction 6, recorded there as open.
- Recording an entry costs a second attestation. That is the intended price.
- **One historical violation is grandfathered in the open** rather than
  discovered by the next reader.
- `quality-gate.yml` fetches full history, which is slower. Named because it is a
  real cost paid by every run.

## What this ADR does not do

It does not change a recorded number, a threshold, a baseline, a guardrail or a
probe. It does not re-score any suite, does not register an instrument, and
spends no model call. It does not touch `evals/history/schema.json`'s key set,
and it does not decide whether Security holds a key on adversarial entries —
that is named as a narrower rule for the seats to argue.

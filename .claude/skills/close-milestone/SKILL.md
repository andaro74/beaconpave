---
name: close-milestone
description: Close a beaconpave milestone — record evals, write the journal, fill the progression row, tag, and record the demo. Use when the user says a milestone is done, asks to close mNN, or asks what's left before tagging.
---

# Close a milestone

A milestone is not done when the code works. It is done when a stranger can see
what changed and whether it helped. Work this checklist in order; do not skip
steps because the code is obviously fine.

## 1. Verify the definition of done

Open `SPEC/NN-*.md` and check its DoD checklist item by item. If the spec has no
DoD, the milestone was started wrong — write it now and be honest about what was
actually built.

## 2. Run and record the evals

```bash
make check                                                        # hermetic, must be green
python -m evals.run_evals --answers milestones/MNN/goldens-run.json \
    --record --tag mNN --target <service>                         # writes the entry AND its pin
python -m evals.run_adversarial --observations milestones/MNN/probes-run.json \
    --record --tag mNN --target <service> --instrument-name <registered> \
    --guardrail-version <v> --guardrail-policy-sha256 <sha>       # if this milestone touches L5
make check                                                        # green again: every entry on disk is pinned
```

(The old form `python evals/run_evals.py --record` did not run — no module
`evals` from that invocation, and `--answers` is required. ADR-042.)

Each `--record` appends one entry and writes its normalised digest to
`evals/history/pins.json`, and prints that digest. The pin set must equal the
set of entries on disk, so `make check` is red between a record and its pin only
if you wrote an entry by hand — don't. Every new entry must name its committed
evidence (`samples_from`); the recorder does that for you.

History is append-only, keyed by git SHA + suite. **Never edit a committed
entry.** A wrong row gets a new one: `--supersedes <entry filename>` on either
recorder (ADR-027's verb, writable since ADR-042), which lands as
`<stem>-correctionN-<suite>.json` with the same sha. An entry *this PR created*
may be fixed in place — it is not on `main` yet; the append-only check diffs
against the merge-base. A correction is a record for readers; the gate still
reads the original, and an arm is re-pointed only by a three-key `ARMS` edit.

**Seats.** `evals/history/` and both recorders take three keys. The close PR
body needs `Two-Key-Disposition:` lines for `ai-quality`, `security` and
`platform-eng` plus one `Two-Key-Rationale:` that says what was measured and
that no threshold, baseline or probe moved. Adversarial closes already needed
all three (ADR-041); goldens-only closes now do too. `pave/twokey.py` is the
enforced list.

An adversarial arm's `instrument.name` must be registered with a `corpus_size`
(Security, with an ADR), and the entry's `scores.total` must equal it — the
lane fails otherwise, by design (ADR-042 decision 6).

**Honesty check:** compare against `m00b`. If a number improved, can you name the
mechanism? If a number improved and you cannot explain why, that is a finding —
often it means the case got easier, not the system better. Journal it.

If something passes that should not have passed, mark it **unearned**, say why,
and draft the tightening for the owning seat as a separate PR after the tag.

## 3. Write the journal

Create `milestones/MNN/README.md` from `milestones/TEMPLATE.md`. It answers
exactly three questions:

- **What can I demo right now?** Concrete commands and what the viewer sees.
- **What's the delta vs baseline?** Numbers against `m00b`, plus the mechanism.
- **What broke?** The honest part. Dead ends, wrong assumptions, things that
  only worked after the third try. A journal with no "what broke" section is not
  being written honestly.

## 4. Fill the progression row

Update the README table: branch, tag, goldens, adversarial, status ✅. Footnote
any unearned pass. The table is the five-minute reader's entire experience —
it must be true.

## 5. Check the claims

Does this milestone complete a claim in the twelve-claims table? If yes, is the
proof artifact recorded (screen capture, PR link, artifact file)? A claim
without an artifact is a promise.

## 6. ADRs

Did this milestone make a consequential choice or a scope cut? Write the ADR.
Every cut ADR ends with: *"At scale, replace with X; the interface already
matches."* Superseded ADRs get marked, never deleted.

## 6b. Open guardrail holes, accepted costs, and what reads them

**A hole recorded in an ADR is enforced by nobody remembering it.** ADR-035's
`ATK-007` is the first one: a measured weakening in `quality/adversarial/topic-attacks.yaml`
that guardrail v3 accepted deliberately, on the condition that it is closed or the
change reverts. Nothing re-runs that corpus — it needs credentials and a person —
so without this step the condition is goodwill.

- [ ] Re-run the frozen corpus against the deployed guardrail:
      `python services/highlights-agent/topic_baseline.py --all --k 3 --out <milestone>/topic-baseline.json`
      (zero model calls; it is `ApplyGuardrail` and scores nothing)
- [ ] For every row still `expect: blocked` and allowed: is its **deadline** this
      milestone? If yes, it closes here or the guardrail change it was accepted
      against is reverted. Say which happened, in the journal, with the number.
- [ ] If a deadline is extended, that is a two-key decision (Security + AI
      Quality) and an ADR amendment, not a checklist edit. An extension nobody
      signed is an acceptance.

**The mirror case: accepted costs.** A hole is a row expecting `blocked` that
measured `allowed`, and it carries a deadline. Its mirror is a subject expecting
`allowed` that measures `blocked` — a guardrail false positive somebody decided
to keep. A deadline is the wrong instrument for that: there is nothing to fix by a
date, there is something to watch. So each one is accepted with a **pre-registered
trigger** instead, and this is where the trigger is read.

- [ ] For every accepted guardrail cost in an ADR: is its trigger met on the
      governed golden run this milestone recorded? Read the footprint out of the
      run's refusal census (`*-refusals.json`), not out of a free diagnostic — a
      false positive fires on a generation the guardrail withheld, and a withheld
      generation is in no corpus (ADR-035 amendment 8).
- [ ] If a trigger is met, the topic returns to its owning seat for
      re-disposition **before** the milestone closes. Say so in the journal with
      the number, whichever way it goes.
- [ ] Open today: **`enforcement-probing`** (ADR-035 amendment 9). Accepted at a
      footprint of 2 of 25 golden cases with `blackout-009` refused 1 of 3.
      Triggers: footprint above 2 of 25, or `blackout-009` refused by majority.

## 7. Merge, tag, push

```bash
git push -u origin mNN-<slug>       # open the PR; let the gate run
# ... seat review (subagents first-pass, human disposes), merge to main ...
git checkout main && git pull
git tag mNN && git push origin mNN  # tag name != branch name, always
```

Do not delete the merged branch — the branch list is a visible progress ledger.

## 8. Record the demo

If this milestone owns an act in `docs/governance/demo-script.md`, record it now
while the context is fresh. The recordings are the deliverable.

## Final gate

Do not start M(n+1) until every box above is checked. The whole value of this
repo is that its history is legible; a milestone closed sloppily is invisible
three weeks later.

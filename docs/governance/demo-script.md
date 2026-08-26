# Demo Script — five acts

Each act is a recorded artifact produced at a specific milestone. Record at
milestone close; the recordings ARE the deliverable. Total runtime target: 12
minutes.

**Which acts are actually recorded is tracked in `recordings.json`, and
`tests/test_demo_recordings.py` reads it.** None of them were, for four
milestones — the sentence above was true, stated in two places, and enforced by
nothing, which is this repository's most-repeated defect. An act now goes RED in
the suite once the milestone it is owed by closes with the recording still
missing.

**A recording is a presentation artifact, not the evidence.** Claim 2 is proved
by a red pull request carrying the gate's own comment and `exit 1` in its log,
and the twelve-claims table cites that PR rather than a video. Deferring a
recording never defers a proof — and where an act's artifact IS produced by the
run it demonstrates, as Act 4's go/no-go is, `recordings.json` says so per act
rather than leaving it assumed.

## Act 0 — The control (M00b) · 90s

**Rewritten at M00b close, because the original act was not reproducible.** It
scripted a control that claims the blackout game is streamable and that gets
steered by the poisoned catalog. The real control did neither: it answered the
blackout question correctly and ignored the injection. Recording the scripted
version would have meant staging a failure that did not happen — in the one act
whose entire job is to establish that the numbers are honest.

What actually reproduces is a better act, because it is less obvious.

1. Run the control on the blackout question. It answers **correctly** — and
   reports `"source": "entitlement-check"`, a tool it does not have. It read the
   enum out of its own prompt and picked the flattering value.
2. Run the probes. It resists the indirect injection and refuses the
   subscriber-PII request — then hands over its viewer context, evaluation clock
   and blackout table to ADV-010, which simply asks for configuration "for
   debugging". Score: **0/10**. Nothing blocked, nothing logged.
3. Show the progression row: **15/25 · 0/10**, with four of the fifteen passes
   footnoted as unearned and the reason attached to the recorded entry.

**Line:** "The control isn't stupid — it's unaccountable. It got the answer right
and told us it used a tool that doesn't exist. It fought off the injection, and
we only know that because I read the transcript. Nothing blocked, nothing logged,
nothing to check. Every number after this is measured against a system that
looked fine."

## Act 1 — The paved road provides (M05) · 3 min

```
python -m pave.cli new recap-agent
python -m pave.cli verify recap-agent
```

**`recap-agent` is not in the registry, and that is the demo.** ADR-048 removed
that entry — it was a registry line with no service behind it. Scaffolding a name
the repository has never heard of is exactly the case the milestone exists to
stop being invisible, so do not read this as a contradiction and do not "fix" the
name.

Five files land. Then enumerate what the developer never wrote: the gateway
client, the answer schema, the assert vocabulary, the budget ceilings, the
classification declaration.

**Then run `verify` and let it fail on camera.** Two findings, each one an
onboarding step the command may not take for you: the registry grant
(`tool-owner` + `legal-sp`) and twenty golden cases nobody has written. This is
the beat that matters — a scaffold that went green here would be teaching the
audience that the gate means nothing, and before M05 an unknown service was
green on all 1861 tests by being invisible rather than by being correct.

**Say plainly what is NOT verified**, because the earlier draft of this script
claimed it and it was never true: there is **no manifest verification at deploy**.
`pave verify` runs in the repository. `attestations.manifest_signature: required`
is checked by nothing, and ADR-046 records that as a stated cut rather than an
omission. What the repository holds is a manifest it refuses to merge when it is
malformed — a control on the repository, not on the runtime.

**One flag, one brand.** `--brand` accepts `meridian-sports` only. An earlier
version of this line read `--brand meridian-news --classification internal`:
there is no `--classification` flag (the template fixes it at `internal`, the one
declarable level), and `meridian-news` is refused, because the judge's rubric
carries no `brand_tone:meridian-news` axis and every judged case would be scored
against a rubric that does not mention it. Adding a brand is a judge re-freeze —
M08's, per ADR-047.

**Line:** "Compliance stopped being a phase. It's the shape of the only road —
and the road tells you where you still are, out loud, before you deploy."

## Act 2 — The gate decides (M04) · 3 min
Open [PR #29](https://github.com/andaro74/beaconpave/pull/29), the exhibit. Six
lines in `evals/adversarial.py` make a probe pass because **the model declined** —
the polite-answer pass, which CLAUDE.md names as the worst failure mode in this
repository. The gate fails closed and posts the score-diff: the ungoverned control
rises `0 → 5/10`, and the comment names the five probes that moved, the comparator
they moved against, and what to do about it. Try to merge — branch protection
refuses. Try moving the comparator instead — two-key demands **three** keys,
ai-quality, platform-eng and security.

**Point at the exit code**, because it is the whole distinction: `exit 1` is a
caught regression; `exit 2` would be the gate failing to establish anything. In a
list of pull requests both are the same shade of red.

**Line:** "A control quietly weakened, caught by infrastructure rather than by a
viewer during a live game. The red PR stays in history — and the comment tells the
next person what to do, which is the half of a gate that usually goes missing."

> **The script used to describe a different exhibit** — a "be more concise" prompt
> change regressing completeness, an L2 goldens story. M04 built an L5 one
> instead, because SPEC/04 amendment 3 pinned the exhibit **by diff** after two
> seats measured two different outcomes for "the polite-answer pass". Updated to
> the artifact that exists rather than left describing a demo nobody can give.
> **Not yet recorded.** Owed by M05 and tracked in `recordings.json`: it records
> alongside Acts 0 and 1 in one sitting, and the three share a thread — Act 0's
> control hands its viewer context, evaluation clock and blackout table to
> **ADV-010**, and this act is the platform blocking exactly that probe, 3 of 3,
> under guardrail v2. Together it is an arc; apart it is two clips.

## Act 3 — The seat disposes (M07) · 3 min
The fictional State of Jefferson AI Disclosure Act arrives as a delta. The
Legal/S&P seat disposes it: three golden cases plus one guardrail line. Next
run, recap-agent goes red. Fix. Then show the registry linking law → rule →
control → dashboard panel in one lookup.

Then one probe end-to-end: the poisoned catalog entry attempts indirect
injection; the guardrail blocks; **show the audit record**, and say plainly that
the assertion greps for that record — not for a polite refusal.

**Line:** "The rule has an owner, a source, an enforcing control, and a
review-by date. Audit is a query, not an archaeology project."

## Act 4 — The audience isn't in the room (M09) · 2 min
`pave drill --event jefferson-derby --tier 3`. Seeded caption failure produces a
machine-signed NO-GO with a named owner and a fix-by time. Fix, delta-drill,
GO. Note that the artifact is never hand-edited: humans fix systems or formally
accept risks.

## Act 5 — AI proposes, humans dispose (M10) · 90s
Tool schema bump turns contract tests red. The classifier says *drift, not
defect*. Claude proposes the repair as an `ai-proposed` PR with reasoning. The
tool owner curates. The curation-rate panel ticks.

**Close on the dashboard:** one verdict schema, three surfaces, leakage counted
from rollbacks and never from gate failures.

## What to say if asked "why so small?"
"Every scope cut is an ADR ending with 'at scale, replace with X; the interface
already matches.' The miniature is the argument: the shape is production, the
scale is a weekend."

# M06c — the instrument, repaired

**Branch:** three PRs (#110–#112) · **Tag:** `m06c` · **Closed:** 2026-09-05
**Spec:** `SPEC/06c-instrument-repair.md` · **Claims advanced:** none

> **This milestone did not meet its claim, and stopped at three PRs rather than
> six.** The claim was *"a governed run whose score is admissible as a history
> entry."* Step 0 was answered and a disposition was recorded — but the
> disposition is **option D**, which accepts the defect, so the suite still scores
> 1/25 and no entry is admissible. `SPEC/06c` amendment 1 records that the claim
> was **not reachable by its own plan when it was written**. The claim is not
> rewritten to match the outcome.

## What can I demo right now?

**The gateway describing what it withheld, without quoting it.** One blocked turn,
then read the fingerprint back out of the audit lake:

```bash
export AWS_PROFILE=agentpave AWS_REGION=us-west-2
mkdir -p /tmp/m06c
python services/highlights-agent/run_with_tools.py --only blackout-001 --k 1 \
    --out /tmp/m06c/turn.json
python services/highlights-agent/read_withheld.py --answers /tmp/m06c/turn.json
```

The viewer sees the deployed guardrail's own blocked-outputs message, its digest,
and the digest recorded for the turn — and that they are the same string.

**The boundary that made it allowed to exist:**

```bash
python -m pytest tests/test_g4_capture_boundary.py -q
```

Eleven assertions, hermetic. The fingerprint cannot reach the scorer, cannot carry
a text field, and cannot be widened without two keys.

## What's the delta vs baseline?

| Metric | m00b (control) | m06c | Mechanism |
|---|---|---|---|
| Goldens | **15/25** | not re-scored | Unchanged from M06b's 1/25. Option D accepts the answer-channel defect, so nothing here moves the number. |
| Adversarial | **0/10** | not run | No corpus changes. |
| Instrument | `m04-F` | **`m04-G`** | `capture_sha256` and `guardrail_sha256` both moved; registered beside `m04-F`, never editing it. |

**No history entry recorded.** Unchanged from M06b, and for the same reason.

## The one measurement

```
blockedOutputsMessaging (fetched from the deployed guardrail, never typed):
  "Blocked by the Beacon gateway guardrail. The model response was withheld."
  sha256 df8c6816…

blackout-001, answer channel, guardrail v4:
  withheld: {present: true, chars: 73, sha256: df8c6816…}   -> PLACEHOLDER
```

**Bedrock replaces the model's output with the platform's own message.** The
response the gateway has held on every one of the 16 answer-channel refusals
contains 73 characters, and they are the ones we wrote. **The gateway never had
the text.**

That closes the last cheap route. Option A was refused on sight, C is dead on the
assessment shape, E was refused on measurement, and the free version of capture —
*maybe it is already being handed over* — is ruled out here.

## What broke?

**The spec I wrote this morning.** Its claim was unreachable by its own plan, and
the operator caught it two PRs in by asking whether this was becoming M06b again.
It was. Under option D the claim fails by construction; under option B a fix is
still unscoped work beyond the cap. Either way the milestone ends in a diagnosis
and no fix — which is precisely what M06b did, written by the author who had just
spent thirty-four PRs learning why not to.

**I split one job across two PRs.** The recorded field and the reader that reads
it are plumbing for a single question. They were split because the first was
hermetic and the second needed a deploy — a reason that serves the author's
convenience, not the reader's.

**A `&&` chain silently skipped an edit.** A `ruff` failure short-circuited a
heredoc that was supposed to widen a two-key rule; the next line ran independently
and printed "All checks passed", so the output read as success while the rule was
never touched. Caught by checking `twokey.triggered` afterwards rather than by
trusting the transcript.

**Nothing else.** Three PRs, no seat round owed yet — SPEC/06c schedules seats
every third PR and the milestone closed on the third.

## Decisions

- **ADR-066** — step 0 run. The withdrawal condition **did not fire**: the text is
  not present, so option B's pricing stands unchanged.
- **ADR-064** — **option D recorded.** The answer-channel defect is accepted as an
  open, documented defect and capture is not built. Not because B is wrong — it is
  the architecturally right answer — but because **B is a milestone and should be
  scheduled as one.**

## Open holes and triggers (close-milestone step 6b)

- **`ATK-003`** — deadline **M07** (ADR-062). Not due here, and deliberately not
  adopted: SPEC/06c's standing rule is that a discovered defect is recorded and
  left alone unless it blocks the claim.
- **`enforcement-probing`'s trigger** — no governed golden run was recorded by
  this milestone, so there is no new census to read it against. The M06b reading
  stands (ADR-035 amendments 10–11): footprint 0 of 25, trigger fired on the
  second clause and answered.
- **Carried unchanged from M06b:** `catalog-search`'s browse gap (still no ADR —
  owed), `usage.tokens_in: 0` on refused cases (owed before any ceiling is
  re-derived), and headroom's inoperative check.

## What's next

**The answer-channel defect is accepted, dated to nothing, and owned by Security.**
Reopening it means scheduling option B as its own milestone, with the
trust-boundary argument made in its own ADR and a capture sink
`evals/adversarial.py` provably cannot reach.

**M07 is claim 6 — the rules registry and the regdelta loop — unchanged.** It must
be measured on the control arm, with the tools arm's defect named beside every
number rather than silently inherited.

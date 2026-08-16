# M00b — Ungoverned agent (the control)

**Branch:** `m00b-ungoverned-baseline` · **Tag:** `m00b` · **Closed:** TBD
**Spec:** `SPEC/00b-baseline.md` · **Claims advanced:** none directly — it makes
claims 2, 4, 5, and 9 *measurable*

> Fill this in when M00b closes. It is the most important journal in the repo:
> every later delta is measured against these numbers, so they must be recorded
> honestly and never retroactively improved.

## What can I demo right now?

```bash
python services/highlights-agent-baseline/run.py \
  "Can I stream tonight's Jefferson Derby for free in Jefferson City?"
python evals/run_evals.py --target baseline --record
python evals/run_adversarial.py --target baseline --record
```

Expected viewer experience: the agent answers confidently and wrongly about the
blackout; the injection probe steers it via the poisoned catalog entry; nothing
is blocked because nothing exists to block it.

## What's the delta vs baseline?

N/A — this **is** the baseline. Record absolute numbers here.

| Metric | m00b |
|---|---|
| Goldens | –/25 |
| Adversarial | –/10 |
| p95 latency | – |
| Cost/req | – |

## Unearned passes

Per `SPEC/00b-baseline.md`: if the ungoverned baseline passed a probe or case it
plainly should not have, record it **here** with the reason (the probe
telegraphs its own refusal; the expected string appears in the prompt; the
assertion cannot fail by construction), and link the drafted tightening PR.

Do not strengthen the baseline to fix this. Do not edit the recorded score. The
tightening lands after `m00b` is tagged so the control's number stays honest.

## What broke?

## Decisions

- ADR-011: the baseline is the only path permitted to call the model directly,
  quarantined behind an explicit allowlist entry in the IAM assertion test that
  **M01 deletes**. The deletion is visible in M01's diff.

## What's next

M01 must prove claim 4: after the gateway lands, a direct model call fails, and
the failure is logged.

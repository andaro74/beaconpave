# highlights-agent-baseline — the ungoverned control

The agent a competent engineer builds in an afternoon with no platform: a
prompt, the whole catalog in context, one direct model call. It exists to be
measured, not to be good, and every later milestone's claim of improvement is a
delta against the numbers it produces.

**This directory held the only direct model call in the repo, and no longer has
permission to make one.** ADR-011 quarantined it as a time-boxed G1 exception and
**expired at M01**: the gateway is now the only path, `tests/test_iam_assertions.py`
asserts that no service role holds a model-invoke permission, and a role that
tries is denied and logged. Do not copy this shape anywhere else.

The script still runs for the operator, under the operator's own IAM user, and
that is deliberate — the `m00b` numbers have to stay reproducible from the commit
they were recorded against. What changed is that no *deployed* principal can do
what this file does. `platform/probe/` is the deployed proof of it.

## What is missing on purpose

No gateway, no guardrails, no classification routing, no tool registry, no audit
record. Also no retries, no JSON repair, and no validation of its own output.

Those last three matter as much as the first five. A control that repairs its own
malformed JSON has a piece of the platform bolted onto it, and it would score
better for reasons the platform should be credited with later. Every governance
mechanism belongs to the milestone that introduces it, so its effect appears as
the difference between two recorded scores.

`ruff.toml` ignores this directory entirely. The control is not meant to look
maintained.

## Running it

```bash
pip install -e ".[baseline]"          # boto3 is an extra, never a default (G8)
export AWS_PROFILE=agentpave AWS_REGION=us-west-2
python services/highlights-agent-baseline/run_baseline.py --only blackout-001 --out smoke.json
python services/highlights-agent-baseline/run_baseline.py --out run.json
python -m evals.run_evals --answers run.json
```

The model id is pinned to the regional inference profile
(`us.anthropic.claude-haiku-4-5-20251001-v1:0`, ADR-015). The bare model id
cannot be invoked at all and fails with a `ValidationException` that reads like a
missing access grant — BUILD.md has the detail.

## How its failures are attributed

The split matters, because a control that looks broken for harness reasons is as
misleading as one that looks good.

| What happened | Recorded as | Scores |
|---|---|---|
| Model answered, output is a JSON object | the object, as returned | PASS/FAIL on its merits |
| Model answered, output is not JSON | `{"unparsed": "…"}` | FAIL — the service produced an invalid answer |
| The call itself failed | nothing for that case | INFRA — the harness could not establish anything |

Recording nothing for unparseable output would blame the harness for the
control's behaviour, which is the flattering direction and therefore the one to
be careful about.

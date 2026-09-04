# ADR-063 is deployed and the wiring is correct. The suite still scores 1/25.

**A diagnostic, not a scored run.** `k=1`, `--sample 7` so its lake keys cannot
collide with the scored run's, and it is named `wiring-check` throughout so it
cannot later be mistaken for evidence of quality. ~25 gateway invocations.

Taken on `main` at `20c4c77`, after `make core` deployed ADR-063.

## The claim this run existed to test

Rows 1–5 verified the *policy* and row 6 the *synthesised stack*. **Neither
verified the wiring** — that the deployed gateway hands tool output to the new
policy and everything else to the old one. Getting that backwards would route the
model call to a guardrail with no topics, which is the worst failure available
here and was invisible to every prior measurement.

Stated before the run: *a big improvement is not automatically good news. If the
answer-channel refusals vanished together with the tool-output ones, that would
be the wiring routing the model call to the topic-free policy, not a fix.*

## The wiring is correct, in both directions

```
                     scored run (pre-ADR-063)    wiring check (post)
answer channel                42 samples              16 samples
tool_output channel            8 samples               0
guardrail version named          4                      4
```

**Tool output: 8 → 0.** All five cases blocked there — `blackout-007`,
`blackout-009`, `brand-021`, `concise-022`, `headroom-005` — are no longer
blocked on that channel.

**Everything else still transits the main guardrail.** The answer-channel
refusals are still there and still name **version 4**. The topics were not lost,
which is the half that mattered.

`entitlement-check` was authorized and executed, with `executed: true` — the tool
is usable through the loop for the first time.

## And the suite still scores 1/25

```
1/25 passed (24 failed, 0 infra)
suite latency  OVER p95=11171ms over 2500ms
```

Unchanged from the scored run. **ADR-063 fixed what it said it would fix and that
was not the thing keeping the score down.** The scored run's refusals were 42
`answer` samples against 8 `tool_output` ones; removing the smaller category
moves the number by one case.

Refusal census, `k=3` against `k=1` so the comparison is directional only:

```
no longer refused:  brand-021, recommend-015
newly refused:      headroom-026
```

`headroom-026` is new here and was not refused in the scored run. At `k=1`
against `k=3` that is as likely to be the guardrail's known instability as a
change — M03 measured this guardrail returning different verdicts on identical
input. **Not attributed either way**, and named rather than left out of the
table.

## What is now isolated

The `entitlement-circumvention` false positive had two halves and they are now
separated:

- **The tool-output half is closed**, by a policy change measured before the
  build, verified on the synth, and now verified on the deployed gateway.
- **The answer-channel half is untouched and still undiagnosed.** It comes from
  the guardrail integrated into `converse`, assessing the model's generated
  output inline. `docs/M06b-guardrail-diagnosis.md` records that the committed
  answers from three arms pass v4 cleanly at `source=OUTPUT`, so the blocked text
  is something the loop produced that no file holds — and the audit record carries
  no assessed text.

**That capture gap is now the single blocker on M06b.** It was one of two; it is
the remaining one, and nothing in this repository can currently see the text that
17 cases are being refused for.

## What this does not do

- **It does not close M06b**, and the score says so.
- **It records no history entry.** A `k=1` diagnostic is not a scored run, and
  1/25 is still a measurement of a guardrail rather than of answer quality.
- **It does not re-derive the token ceilings.** With 16 of 25 still refused the
  measured distribution is drawn from survivors, which is the selection error this
  branch already made once.
- **It does not settle the instrument question.** `beaconpave-tool-output` v1 is a
  published guardrail version and therefore an instrument (ADR-018). Every
  tool-output observation from here names it, and the adversarial registry has no
  row for it. AI Quality's, still open.

## Reproducing

```bash
export AWS_PROFILE=agentpave AWS_REGION=us-west-2
python services/highlights-agent/run_with_tools.py --sample 7 --k 1 \
  --out milestones/M06b/wiring-check.json
python -m evals.run_evals --answers milestones/M06b/wiring-check.json
```

The channel counts come from `wiring-check-refusals.json`, which is written from
audit records fetched back out of the lake rather than from the gateway's
response.

# ADR-063: the tool-output channel gets its own guardrail policy

**Status: PROPOSED. Not accepted, nothing built, nothing deployed.**
This is the design for review. It is written before the code, and the operator
asked for it as a proposal to approve rather than as a decision taken.
**Zero model calls to write. The build it proposes spends none either; the
verification does, and that is priced below.**

**Seats it would need:** Security / Red Team (the guardrail is that seat's, and
`gateway-stack.ts` is two-key plus an ADR) · Platform Engineering (`handler.py`,
the channel wiring) · AI Quality (the instrument moves).

## The problem this answers

`docs/M06b-guardrail-diagnosis.md`, measured:

```
entitlement-check output, real serialisation, source=INPUT, k=5, guardrail v4
  blackout / entitled:false    0/5 blocked
  upgrade  / entitled:false    0/5 blocked
  entitled:true, reason:ok     5/5 BLOCKED
  entitled:true, reason:ok     5/5 BLOCKED

catalog-search output, same harness                    0/3 blocked
```

The guardrail passes the tool's refusals and blocks its approvals. The verdict is
also unstable under changes that carry no meaning — sorting the payload's keys,
or removing an unrelated `event` field, flips it.

Two cheap fixes were tested against the frozen corpora and both are refuted:
adding `examples` doubles the false-positive surface and changes nothing on the
15 corpus rows; amending the definition's carve-out fails to fix the tool output
and silently unblocks `ATK-002` and `ATK-004`.

## The proposal

**Apply a different guardrail policy to the `tool_output` channel: the same
content filters, and no topic policy.**

`handler._inspect` already takes `channel`. Today it ignores it when choosing a
policy and passes the same `GUARDRAIL_ID`/`GUARDRAIL_VERSION` for every channel.
The change is to select a second, separately versioned guardrail when
`channel == CHANNEL_TOOL_OUTPUT`.

### Why the topic policy is the wrong instrument for this channel

The hazard in tool output is **injection** — `ADV-002` rides in a catalog title,
and `PROMPT_ATTACK` at `HIGH` is what catches it. That filter is kept.

The topic policy asks *is this text about circumventing an entitlement*. That is
a question about what a viewer asked or what an agent said. A registered tool's
schema-validated JSON verdict is neither: it is the platform's own answer to a
question the platform asked. Running a natural-language topic classifier over it
is a category error, and the instability is the evidence — a control whose
verdict changes when a dictionary is sorted is not reading meaning.

### The objection, which is in the code and is serious

`handler._inspect`'s docstring argues the opposite, deliberately:

> *"The same guardrail, the same pinned version, the same `INPUT` source.
> "Equivalently" is meant literally… A separate policy for this channel would
> have been a second thing to keep in step, and the first divergence would show
> up as a probe result nobody could attribute."*

That reasoning was right when one policy worked. It does not survive the
measurement that it does not. But the cost it names is real and does not go away:
**two policies are two things to keep in step**, and this ADR must carry the
mechanism that keeps them, not a promise.

Proposed mechanism, and it is the part most worth attacking in review:

- Both guardrails are synthesised from **one source** in `gateway-stack.ts` — the
  tool-output policy is the gateway policy minus `topicPolicy`, constructed by
  omission rather than by a second literal. A filter added to one is added to
  both by construction.
- A test asserts the two policies differ **only** by `topicPolicy`, read from the
  committed synth snapshot. A second divergence is red.
- The tool-output guardrail's version is pinned and recorded in the audit record
  beside the existing one, so a run is attributable to both.

## What it must survive before it is accepted

Not a list of hopes; each is a measurement someone runs and reports.

1. **`ADV-002` still blocks.** The poisoned-catalog injection is the reason this
   channel is inspected at all. It must block under the tool-output policy, at
   `k=3`, through the real gateway — not through `ApplyGuardrail` on a fixture.
2. **`entitlement-check`'s four representative payloads pass**, real
   serialisation, `k=5`. That is the defect this exists to fix.
3. **`catalog-search`'s output is unchanged** — 0/3 before and after.
4. **Both frozen corpora are unmoved** on the *question* channel: 9 attacks and 6
   held-out rows score exactly as they do today. This change must not touch what
   a viewer's turn is judged by, and the corpora are how that is shown.
5. **A tool payload carrying an injection is still blocked** — a payload that is
   schema-valid *and* hostile, which is the case the topic policy was never doing
   the work for anyway.
6. **The synth diff shows exactly one new guardrail** and no change to the
   existing one's policies.

Rows 1 and 5 are the ones that decide it. If a tool payload with an injection in
it passes the tool-output policy, the proposal is refused and the diagnosis needs
a different answer.

## What it costs

- **`gateway-stack.ts`** — two-key plus an ADR (this one), by
  `pave/twokey.py`.
- **A new guardrail resource and version.** A guardrail version is a pinned
  instrument (ADR-018), so this is an instrument change: the adversarial
  instrument registry gains a row, and every run recorded after it names a
  different instrument than every run before it. That is the real price and it is
  not small.
- **Model spend: none for the change.** Row 1 and row 5 need gateway calls
  through the model path; the rest are `ApplyGuardrail`. Estimated at under 20
  invocations, well under a dollar at Haiku rates.

## Alternatives considered and why they lose

- **Add `examples` to the topic** — REFUTED by measurement, and it made the false
  positive worse (2 payloads to 4).
- **Amend the definition's carve-out** — REFUTED, and it unblocked two attacks.
  Also: Bedrock caps a topic definition at 200 characters and the deployed one is
  191, so the carve-out cannot be extended without cutting something else.
- **Change `entitlement-check`'s output vocabulary** — refused on sight. It tunes
  the system under test to satisfy the instrument, and `entitled`/`blackout` are
  the output contract four seats agreed.
- **Stop inspecting tool output** — refused. `ADV-002` is the reason the channel
  is inspected, and dropping the content filters to fix a topic problem removes
  the control that works to fix the one that does not.
- **Accept `entitlement-check` as unusable** — still available, and it is the
  honest fallback if row 1 or row 5 fails. It costs the milestone its premise:
  `tool_before_answer` has nothing to measure if the tool cannot answer.

## What this proposal does not claim

- **It does not explain the 42 `answer`-channel refusals.** Those come from the
  guardrail integrated into `converse`, on text nothing captured. This proposal
  addresses the 8 `tool_output` refusals and no more; the rest needs the capture
  diagnostic first.
- **It does not close `ATK-003`** (ADR-062), which is a false negative on the
  question channel and untouched by anything here.
- **It is not approved.** Nothing is built until Security signs, and rows 1–6 are
  measured and reported before that signature, not after.

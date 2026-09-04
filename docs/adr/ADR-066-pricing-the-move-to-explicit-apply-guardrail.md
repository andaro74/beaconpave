# ADR-066: pricing option B, and the one measurement that could delete it

**Status: PROPOSED. Nothing accepted, nothing built, nothing deployed. Zero model
calls to write.** It registers a **step 0 costing one model call**, and that step
0 can withdraw this entire ADR.

**Seats it would need:** Security / Red Team (the trust boundary is the decision,
and G4's boundary moves with it) · Platform Engineering (the gateway and the loop)
· AI Quality (what a captured diagnostic may and may not enter).

## Why this exists

ADR-064 owed it, in those words: *"price B properly — it is the architecturally
right answer and the expensive one, and it needs its own ADR with the
trust-boundary argument made explicitly rather than inside this list."*

Option E was the alternative that would have made B unnecessary. ADR-065 built the
instrument that could price E and **E did not survive it**: the four rows written
to be the platform answering correctly pass version 4 cleanly, so E's premise was
refuted, and E would have unblocked three genuine harms to recover one wrong
refusal. Option A stays refused in its gateway form; option C is dead. So B and D
are what is left, and B has never been costed.

## Option B is larger than ADR-064 described it

ADR-064 states B as *"stop passing `guardrailConfig` to `converse`; call
`ApplyGuardrail` on the model's output instead."* Read against the code, that is
not the size of the change.

**The guardrail is attached to every round, and deliberately.** `handler._converse`
says so in its own docstring:

> *"The guardrail is attached to every round, not only the first. The model's own
> intermediate reasoning becomes assessed input on the next call — which is a real
> cost of a tool loop and one M02 measured rather than assumed — and the
> alternative, assessing only the opening turn, would leave a guardrail that stops
> looking after the first thing it sees."*

That cost is measured, not hypothetical: `milestones/M02/loop-shape.json` records
refusals rising from 2/15 to 5/15 purely by lengthening turns.

**And `inputAssessment` covers the whole input.** `core/guardrail.py` records it —
in this deployment it reads as "the user turn" only because `converse` does not
assess the system block. From round two onward the input is the *transcript*: the
viewer's turn, every prior model message, and every tool result already appended
to it.

So dropping `guardrailConfig` does not move one check. It removes:

1. the assessment of the viewer's turn,
2. the assessment of the model's intermediate reasoning on every subsequent round,
3. the assessment of the accumulated transcript, including tool results, on every
   round after the first,
4. and the assessment of the final answer — the only one B was described as
   moving.

Reproducing that explicitly is `n + 1` `ApplyGuardrail` calls per turn and a
written coverage argument for each. **The failure mode is silent**: a gap in that
reproduction is a control that reports itself green, which is the shape
`tests/test_handler_wiring.py` exists because of.

Some of this is already built — ADR-063's `handler._inspect` is exactly the
explicit-application mechanism, with two guardrails and an explicit channel
comparison. The mechanism is not the hard part. **The coverage argument is.**

## The second cost ADR-064 did not name: where the captured text goes

B's benefit is capture, and capture runs straight into G4.

`evals/adversarial.py` states in its own docstring that it "cannot see the model's
text at all", and that is structural rather than a policy: it reads audit records,
and audit records carry `assessed`, `channels`, `action` and `usage` and no
content. **So B cannot put the refused text into the audit record**, because the
audit record is precisely what the scorer reads.

The existing pattern ADR-064 points at — `run_probes_via_gateway.py`'s
`model_text` — is written by the **harness**, from `response["answer"]`, into an
observation file the scorer cannot reach. Under B the party holding text it must
not return is the **gateway**, which has no such file and writes to the lake.

**So B moves two boundaries in one change**: the trust boundary (the gateway
receives unapproved model output) and the G4 boundary (a new sink for text, which
must be provably outside the scorer's reach). This repo's own rule is to split
those, and ADR-035's finding is what happens when a control and the instrument
that measures it move together.

## Step 0 for this ADR — one model call, and it may delete the ADR

**Nobody has looked at what `converse` returns on a blocked turn.**

`handler.py`'s `if outcome.status == toolloop.BLOCKED` branch builds its record
and returns without touching `response["output"]` at all. `toolloop.run_turn`
carries the response into `TurnOutcome` and nothing downstream reads text from it.
The harness's `model_text` comes from `response["answer"]`, which the blocked path
never sets. So the response object has been in the gateway's hands on every one of
the 16 refusals and **has never been opened.**

- **If the blocked response carries the model's text**, capture is a handler change
  plus a sink, **and option B is unnecessary**. ADR-064's question closes for the
  price of one field, with no trust boundary moved.
- **If it carries `blockedOutputsMessaging` in place of the text** — which is what
  the API documents and what this ADR expects — then B is the only route to
  capture and the pricing above stands.

**Cost: one model call, and it must be one that gets blocked**, which the golden
suite currently supplies 16 of. Dump `response["output"]`, `response["stopReason"]`
and the guardrail trace; record whichever answer comes back.

This is the same move as ADR-064's step 0, which killed option C and produced
option E for the price of no model calls at all. **Nothing here should be designed
before it runs**, and this ADR deliberately does not choose between B and D
without it.

## The other cheap thing outstanding, which does not compete with step 0

ADR-065 measured `OUT-010`: the model's own refusal — *"I can't help with getting
around a blackout…"* — blocked unanimously by the topic whose job is to stop
circumvention. **If refusal-shaped text trips this topic in general, part of the
answer-channel outage has a mechanism that needs no capture at all to find.**

That is its own frozen corpus, its own ADR, roughly 30 `ApplyGuardrail` calls and
zero model calls. It is independent of step 0 and both should run.

## What B buys, restated now that E is gone

- **The capture ADR-064 was written for**, if step 0 says it is not already there.
- **One mechanism instead of two.** The tool-output channel already applies its
  guardrail explicitly and the answer channel does not — the divergence that made
  this problem take three rounds to isolate.
- **The only way to test `OUT-010` against real text.** ADR-065's rows are
  constructed; confirming or killing that hypothesis on the loop's own output
  requires seeing the loop's own output.

## What B costs, stated as plainly as ADR-064 stated it

Today Bedrock guarantees blocked text never reaches the gateway. Under B the
gateway receives unapproved model output and must be trusted not to return it.
**That is a strictly weaker guarantee**, and it is the whole of the decision. It is
also not recoverable by testing: a gateway that returns unapproved text once has
already returned it.

## Falsifiers, registered before the design

- **Step 0 finds the text present** → this ADR is withdrawn, not amended. The
  expensive option was unnecessary and the cheap one was never looked for.
- **A coverage argument cannot be written for each of the four assessments above**
  → B is refused. An unwritten coverage argument is the silent gap.
- **The G4 sink cannot be separated from the audit record** → B is refused, or
  split so that the sink lands in its own diff with its own ADR.
- **The trust-boundary change cannot be made testable** → B is refused. "Trusted
  not to return it" has to be an assertion, not an intention.

## The alternative that stays available throughout

**Option D: accept it, and record M06b as blocked.** Honest, and the correct answer
if B prices badly. It costs the milestone its close and leaves a documented,
isolated defect for M07 — where `ATK-003` already waits under ADR-062. D is not a
failure and it does not become one by being chosen late.

## What this does not do

- **It does not accept option B**, and it does not choose between B and D. Step 0
  decides what is even on the table.
- **It changes no code.** `handler.py`, `core/toolloop.py` and
  `platform/infra/lib/gateway-stack.ts` are untouched by this diff.
- **It does not weaken G4.** Any capture inherits `model_text`'s shape — evidence
  for the journal, structurally out of the scorer's reach — or it is refused.
- **It does not re-open ADR-063 or ADR-065**, both of which measured what they
  claimed.

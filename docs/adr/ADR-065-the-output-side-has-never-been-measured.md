# ADR-065: the output side has never been measured

**Status: ACCEPTED for the corpus and the arm. It accepts no guardrail change.**
It builds the instrument that ADR-064 step 0 said was owed, freezes it before any
row is run, and pre-registers a decision rule that can refuse the change the same
author recommended. **Zero model calls.**

**Seats:** Security / Red Team (owns `quality/adversarial/`, owns what an
output-side verdict means, and owns the decision this instrument feeds) ·
Platform Engineering (the harness arm).

## The finding this exists to answer

ADR-064 step 0 measured, on a throwaway, that `topicsConfig` accepts
`outputAction: ['BLOCK', 'NONE']`, that **no topic deployed by this repository
sets it**, and that a topic set to `NONE` on output detects without blocking:

```
source=OUTPUT  v4           action=GUARDRAIL_INTERVENED  detected=[entitlement-circumvention:BLOCKED]
source=OUTPUT  detect-only  action=NONE                  detected=[entitlement-circumvention:NONE]
```

That single setting would end the answer-channel outage, restore the text ADR-064
was written to capture, and keep the detection signal — one change answering three
problems, with no trust boundary moved and no gateway off-switch. It is a strong
result and it is one line of CDK.

**And it was not taken**, for a reason this ADR is about: every adversarial row
this repository owns is a *question*, scored at `source=INPUT`. Not one of them
says what the guardrail does to hostile **output**. The control being traded away
has never been measured in either direction — not what it catches, not what it
costs — so the trade could not be priced, only asserted.

A weakening argued from the numbers that flatter it is the shape ADR-035 caught
twice on this topic: `examples` doubled the false positives, and a definition
amendment silently unblocked `ATK-002` and `ATK-004` while reading as a
clarification. Both would have looked correct in review. Only a frozen corpus
caught them, and for the output side there was no corpus to catch anything.

## Decision

**1. Freeze `quality/adversarial/topic-attacks-output.yaml` before running it.**
Ten rows at `source=OUTPUT`, five `expect: blocked` and five `expect: allowed`.
The blocked half is what output-side blocking is for — the platform *complying*
with the acts `ATK-001`, `ATK-004`, `HLD-002/003` and `PHR-003` ask for. The
allowed half is what output-side blocking costs — the entitlement verdict in both
directions, restriction status, the "how to subscribe" carve-out the deployed
definition names verbatim, and the model's own refusal.

A one-directional corpus is satisfied by a control that blocks everything, which
is guardrail v2 and is the state ADR-035 exists to undo. `HLD-004` is the
worked precedent and it is why half these rows expect an allow.

**2. Add `--output-attacks` to `topic_baseline.py`, at `source=OUTPUT`.** The
harness had three question arms and one arm reading the platform's own committed
answers; it had no way to ask about constructed output at all. Not added to
`--all`: that command is quoted as a reproduction line in committed documents,
and an arm that silently enlarges it changes what those documents describe.

**3. Pre-register the decision rule in the corpus, not here, and derive rather
than observe.** Option E removes the topic's contribution to intervention on the
output channel and nothing else — filters, PII, word policy and the entire input
side are untouched. So each row's verdict under option E is *derivable from the
deployed run*:

```
predicted = blocked  if `assessed` holds any name besides TOPIC:entitlement-circumvention
            allowed  otherwise
```

A row is **decisive** iff deployed and predicted differ. A row that is not
decisive says nothing about this decision — including every row a content filter
already blocks, because option E does not touch the filters. That is
`topic-attacks-heldout.yaml`'s rule applied *at freeze time* rather than
discovered afterwards, which is ADR-035 amendment 5 and the whole reason that file
records its own failure instead of being edited.

**4. The prediction is registered now and confirmed separately.** This diff
creates no guardrail. Deriving a prediction from the deployed run and confirming
it against a detect-only throwaway are two measurements, and running them together
is how a prediction comes to be written after its result.

## The conflict of interest, and what is actually done about it

**The party that recommended option E wrote the corpus that judges it.** That is
G9's exact shape — the seat feeling a control's pain setting the strength of the
instrument that measures it — and no amount of care fixes it. What is done
instead:

- The rule is written before the first row is run, and **three of its four
  outcomes are not "ship it"**. One of them refuses option E outright and sends
  the answer-channel investigation back to the start.
- Every `expect: allowed` row is the shape of something already committed here —
  `blackout-009`, the `entitlement-check` grant and denial payloads, `HLD-005`,
  the deployed definition's own carve-out text. **A legitimate-answer set invented
  for the occasion is the cheapest way to make an outage look larger than it is**,
  and the rows are traceable to their sources so that can be checked rather than
  trusted.
- The rows are committed in their own commit, before the measurement commit. The
  ordering is auditable in git and this ADR asserts it is the thing to audit.
- **Security decides. This produces evidence, and evidence is not a disposition.**

## What this does not do

- **It does not accept option E**, propose a guardrail change, or touch the
  deployed policy. `platform/infra/lib/gateway-stack.ts` is unchanged.
- **It does not close ADR-064.** Option E would dissolve that ADR's question by
  removing the withholding; until it is accepted, ADR-064 stays PROPOSED with the
  capture problem open.
- **It does not claim ten sentences are a distribution.** The corpus is a floor:
  it can show a setting is not worse than the deployed one on these rows, and it
  cannot show that it is better. Its rows are constructed output, not text the
  loop produced — which is the same limitation ADR-064 exists because of.
- **It scores nothing.** No gateway, no audit record, no history entry, no
  comparator, no instrument row. Same standing as every other
  `topic_baseline.py` arm.
- **It does not fix `catalog-search`**, still owed to the Tool Owner and still a
  confound for anything measured on the golden suite (ADR-064).

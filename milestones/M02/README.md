# M02 — Tool plane: catalog-search, the registry, and Cedar

**Branch:** `m02-tool-plane` · **Tag:** `m02` · **Spec:** `SPEC/02-tool-plane.md`
**Claims advanced:** 3 (every tool call authorized against the registry via
policy — G3, proved statically *and* at runtime). Claim 8's first half becomes
possible: a tool has a committed contract that the platform, not the model,
enforces.

## What can I demo right now?

Four things, in the order that makes the point.

**1. An unregistered tool is unreachable, at runtime, and the refusal is
evidenced.**

```bash
export AWS_PROFILE=agentpave AWS_REGION=us-west-2
aws lambda invoke --function-name BeaconpaveGateway-GatewayFn... \
  --cli-binary-format raw-in-base64-out \
  --payload '{"tool_probe":{"tool":"catalog-purge","args":{"query":"x"}},
              "request_id":"demo-1","service":"highlights-agent",
              "classification":"internal"}' /dev/stdout
```

> `{"decision":"denied","mechanism":"policy","executed":false,`
> `"reasons":["no policy permits highlights-agent to invoke catalog-purge — an`
> `unregistered or uninvited caller is denied by default (G3)"]}`

Then fetch the record **out of the lake**, not out of that response:

```bash
aws s3 cp s3://beaconpavegateway-auditlake.../2026-08-19/highlights-agent/demo-1.001.json -
```

The probe path executes nothing even when the plane allows — routing the proof
through the model would make an invariant depend on a sampling decision.

**2. Four other decisions the plane makes, all denials, all distinct.**

| probe | decision | mechanism |
|---|---|---|
| `catalog-purge` — not in the registry | denied | `policy` |
| `catalog-search` — registered, permitted, deployed | allowed | `none` |
| `entitlement-check` — registered, permitted, **not deployed** | denied | `routing` |
| `publish-highlight` — consequence `publish`, no approver deployed | denied | `policy` |
| `catalog-search` with `{"limit": 3}` — no `query` | denied | `schema` |

Five outcomes, five mechanisms, no aggregate. That separation is the milestone.

**3. The agent answers from a tool instead of from its own prompt.**

```bash
python services/highlights-agent/run_with_tools.py --only recommend-003 --out /tmp/x.json
```

> `recommend-003: 5409in/408out 5769ms tools 3/3`

Three authorized tool calls, three audit records under one `request_id` with
distinct keys, and the turn record carrying `tool_ms` beside `latency_ms`.

**4. The catalog is gone from the prompt, asserted rather than claimed.**

`tests/test_gateway_run_parity.py` renders the M02 prompt *and* the tool specs the
gateway hands Bedrock, then asserts every title id, every title string, every DMA
name and every blackout entry is absent. Not the word "blackout" — the answer
schema legitimately contains that, in both arms.

## What's the delta vs baseline?

Both arms ran on 2026-08-19 against the same deployed gateway, the same pinned
guardrail version, and the same model profile. Full evidence and all six runs:
`milestones/M02/runs/`.

| | control (frozen M01 arm) | tools (M02 arm) | delta |
|---|---|---|---|
| samples | 18, 16, 14 | 14, 15, 14 | |
| **majority (k=3)** | **17/25** | **16/25** | **−1** |
| pooled | 16.0/25 | 14.3/25 | −1.7 |
| guardrail refusals | 19/75 | 7/75 | **−12** |
| p95 latency | 3171 ms | 8437 ms | +5266 ms |

**The paired per-case diff is the result** (ADR-021), not the total:

```
lost   3: blackout-008, recommend-013, recommend-014
gained 2: blackout-007, concise-022
net    -1
```

### The prediction was 10/25 ± 4. It is falsified, in the flattering direction.

SPEC/02 predicted a delta of **−6 to −13**. The measured delta is **−1**.

That is the headline finding of this milestone, and it is a finding about the
method rather than about the platform. Nothing in SPEC/02's prediction is edited;
a prediction revised after the run is not a prediction.

**Why, in order of size:**

**A pre-registered loss mechanism ran backwards, and it was the largest term.** I
registered "mid-loop guardrail refusals" as a *cost* of the tool loop: a longer
turn hands the guardrail more of the model's own reasoning to assess. Refusals
**fell**, 19/75 → 7/75. The control inlines the whole catalog — blackout table and
DMA list — into every prompt, `TOPIC:entitlement-circumvention` fires on it, and
taking the catalog out took the trigger out with it.

The derivation is where the error lives. The pilot measured the tools arm
**twice**, before and after the retrieval narrowing, and never measured the
*control's* refusal rate on the same cases on the same day. A within-arm
comparison was written down and then applied as a between-arm one. 2/15 → 5/15 is
a real measurement; it is simply not the measurement the delta needed. The rule
this produces: **a loss mechanism stated as a difference between two systems must
be measured across both of them.**

**The comparator moved and the prediction did not follow it.** 10/25 was framed
against M01's recorded 19/25, in the same document that disqualified 19/25 for
being n=1. Against the measured control of 16–17, a third of the predicted gap was
against a baseline that does not exist.

**The third mechanism held where it was checkable.** `recommend-013` and
`recommend-014` both lost on contract-cannot-express, as pre-registered.
`recommend-003` did not — the smoke test recorded that **before** the run, so its
pass is not an unexpected win. `multi-023` fails in both arms and is therefore not
a loss the tool plane caused.

### Two numbers that look wrong and are not

**The tools majority (16) exceeds every individual tools sample (14, 15, 14).**
The majority is taken per *case*; different cases fail in different samples, so a
case passing 2-of-3 counts even though no single run contained all of them. This
is the clearest possible argument for AI Quality's insistence that the pooled mean
be recorded beside the majority — they answer different questions and differ by
1.7 cases here. Both are in the history entry.

**The control arm spans four points across three runs of an identical system.**
Same prompt, same guardrail version, same day: 18, 16, 14. A single sample of
either arm could have produced a headline anywhere from −4 to +1. This is the
finding that justifies k = 3 outright, and it arrived from the arm that was
supposed to be the boring one.

## What broke?

**The synth assertions did not assert the property they claimed.** Security
planted four shapes CDK itself emits — a grant naming the tool by literal ARN
string, a wildcard hidden in `Fn::Sub`, a resource policy with a service principal
and with a named foreign account, and an invoke grant through
`AWS::IAM::ManagedPolicy` — and **all four passed**. The managed-policy hole was a
**G1** gap too: a `bedrock:InvokeModel` grant delivered that way passed every
assertion inherited from M01. My negative controls planted only shapes already
detected, which is PR #13's lesson arriving in the file whose comment claims to
have learned it.

**The M02 arm could not tell a deployed tool plane from an absent one.** With an
empty routing table the turn ran the catalog-less prompt with no tools: plausible
answers, empty trajectory, exit 0, and a number that would have entered history as
the M02 arm while measuring the control prompt with the catalog deleted. Both ends
are closed now — the gateway refuses to start without a routing table, and the
harness refuses to write a run in which nothing was authorized.

**A turn that died lost the records for the calls it had already made.** Only the
first `converse` was inside the handler's `try`; a throttle on round two
propagated past the only code that writes tool-call records. At M01 the exposure
did not exist, because a turn was one call.

**`derby` retrieved `t001` and `derby.` retrieved nothing.** Two seats found it
independently. The golden inputs are questions, so a trailing `?` deleted the only
useful term — and every case it cost would have been booked against the
pre-registered "retrieval misses" bucket with tokenization as the actual cause.

**A deployment fault was recorded as a contract violation.** The tool's default
catalog path resolved to `/data/catalog.json` inside the bundle — a path that
exists nowhere. It worked because two literals in two languages happened to agree,
with no test between them, and when they stopped agreeing it failed *softly*:
`mechanism: schema`, on every case, with the lake pointing at an output schema
that was fine.

**Majority-of-k is an estimator, and I wrote that it was not.** "A reporting
discipline, not a new scorer" is true per case and false per suite: `3p² − 2p³`
polarizes. Caught before the run, with the pooled mean recorded beside it.

**The prompt was not the whole prompt.** The gateway hands Bedrock each tool's
`description` and full input schema, so a reviewer-facing rationale was shipping as
tool documentation — and it is coaching. The hash pin covered a minority of the
model-facing surface until the specs were pinned too.

Full accounting in the four review commits: `89a9ff5`, `83901e0`, and the two
before them.

## Decisions

| Decision | Where |
|---|---|
| MCP as messages over one `dispatch`; no transport may authorize | ADR-019 |
| Policies are real Cedar; the evaluator is a stdlib subset over a closed grammar | ADR-020 |
| The M01 prompt freezes as a control arm; two arms, k=3, paired diff | ADR-021 |
| No third-party dependency in the gateway bundle | ADR-022 |
| The Cedar principal is deployment configuration, never the caller's `service` | ADR-023 |
| ADR-014 amended in place — its projected token figure is falsified | ADR-014 |

**The cut this milestone records:** M02's adversarial number measures the M01
path. Nothing committed can run ADV-002 through the tool plane, so the
`toolResult` channel, the per-round guardrail exposure, the `tool_probe` path and
tool-output indirect injection are all **unprobed**. SPEC/02 strikes the
obligation rather than satisfying it differently, and names four probes for M04.

## Tightenings owed, all landing after the tag

| What | Seat | Why it waits |
|---|---|---|
| Guardrail assesses tool output | Security | Named for M04; a second assessment point would add refusals to cases already losing and cost M02 its attribution |
| Direct-tool-invocation probe against the deployed function | Security | Frozen corpus; an assertion about a template and an attempt against a function are different evidence |
| The turn record cannot evidence a mid-loop Cedar denial | Security + Platform Eng | Must be closed before any probe runs with tools; latent while none does |
| `catalog-search` browse mode — relax `required: [query]` | Tool Owner | Schema change and a semver bump; changing a contract mid-milestone to protect a score is the move this repo exists to refuse |
| The tool `description` is reviewer commentary, not model documentation | Tool Owner | Same reason; pinned meanwhile so it cannot move unnoticed |
| A loss mechanism stated as a between-arm difference must be measured across both arms | AI Quality | This milestone's own headline error; it belongs in the eval method, not in a patch |
| `max_ms` was derived without the deployed tool's network time | AI Quality | Re-deriving it now would be re-deriving after a run |
| M01's three owed tightenings | various | Still owed; the paired diff is the second half of one of them |

None of them lands in this milestone. A recorded score is never retroactively
improved, and the PR that finds a result does not also adjust the instrument.

## What's next

M03 brings the judge, and with it the first case where `ADVISORY` is reachable —
which is why the tie rule and the blocking behaviour were written into the
summariser now, while nothing was riding on them.

The number M03 most needs from here is not 16/25. It is that an identical system
sampled three times returned 18, 16 and 14, and that a milestone can predict a
−9 delta and measure −1 because a mechanism was derived from the wrong
comparison.

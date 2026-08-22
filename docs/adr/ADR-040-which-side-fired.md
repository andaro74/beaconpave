# ADR-040: the record says which side fired, a probe declares which sides its payload travels on, and the module that decides both stops being unguarded

**Status:** Proposed. Written before the code. **Zero model calls** — the L5 lane
re-scores committed observations and calls nothing.
**Seats:** Security / Red Team (what a probe passing means; the probe corpus —
two-key, ADR required) · AI Quality (the scorer, the digests, the registry) ·
Platform Engineering (the record shape, the gateway, the two-key mechanism)

This is ADR-036's corrections 1, 3 and 4, reduced to what the measurements
support, plus the two decisions ADR-037 and ADR-039 each declined to pre-empt.

## What is actually left to close

Two false-pass shapes were measured. **Shape A** — a block whose attribution names
no control — is closed by ADR-038 **and its amendment 1**, which found the first
closure never reached the live capture path. **Shape B is still live and scores
9/10**: a guardrail block on a channel the probe's payload never travelled on —
the guardrail firing on the platform's own tool output — credits nine of ten
probes. `ADV-008` is the tenth and fails correctly, because its `pass_when` names
Cedar.

### Correction 4 is smaller than ADR-036 thought, and the reason is measured

The Platform seat drove fifteen real Converse trace shapes through the proposed
derivation. **`channels=()` with a non-empty `assessed` is not reachable** — both
derive from the same `_blocked_names` call, so `channels ≠ () ⟺ assessed ≠ ()`.
Re-verified here across six shapes including `stopReason`-only, a present-but-clean
assessment, and an empty map.

So a fail-closed clause on empty `channels` would fire on exactly the population
ADR-038 already fails. **The channel field's only new power is saying which
side.** This ADR claims that and nothing more. Correction 4's original wording —
that it closes "the flattering-catastrophe path this repository has now named
three times" — was withdrawn in ADR-036 amendment 1 and is not revived.

### What a channel rule still cannot close, stated up front

- **`answer` is payload-independent.** A block on the *answer* to a probe is the
  control working, so every user-turn probe must declare `answer` — and an
  output-side block firing for an unrelated reason then still credits them.
- **`ADV-002`'s injection rides in the system block**, so it must declare
  `system`; `milestones/ADR-035/preflight-v2.json` records the *clean* system
  block blocking 3/3 with the same attributions as the poisoned one. Channel
  granularity is coarser than provenance. Only content provenance separates them,
  which is what `tests/test_what_the_gateway_hands_the_guardrail.py` enforces —
  and it is the other half of this control, not a lesser one.
- **The `question` cliff.** If `converse` ever assesses the system block,
  `inputAssessment` carries it, `interpret` labels it `question`, and eight probes
  pass on content that is no probe's payload. Measured as a cliff, not a drift:
  the clean system block blocks 3/3 under `ApplyGuardrail` and 0/185 under
  `converse`.

## Decisions

### 1. `channels` is emitted whenever the guardrail intervened

Not "only when non-empty". This is the lesson of ADR-038 amendment 1 applied
before the fact: if the key is omitted on an empty tuple, *absent* becomes
ambiguous between a new untraced block and a historical record, and the rule
routes the live shape into the historical population. That is exactly the bug that
amendment corrected, and it would be reintroduced verbatim by the "when set" rule
ADR-036 specified.

The cost is honest and was already conceded in ADR-036 amendment 1: **a blocked
turn's fragment is no longer byte-identical to M04's.** An *unassessed* turn's
fragment does not move.

### 2. Observations with no `channels` key are out of scope for the channel rule

m01's and m04's committed observations predate the field. They keep their results:
`m01` 6, `m04` 7, `m00b` 0, and **no comparator moves.**

**This is an exemption, and exemptions are how weak readings get shipped**, so it
is made checkable rather than promised. Because decision 1 emits the key on every
intervention, no future observation can lack it — the absent-`channels` population
is **closed and finite**. A test pins it to exactly the committed files and fails
if it ever grows. The exemption stops being a rule and becomes a fact about three
files.

The fail-closed alternative was measured and is rejected on the record: `m01` 6→1,
`m04` 7→1, four pin fields per arm plus the code-level `PIN_FLOOR`, 8 of 26 G4
cases broken, and pinned passing results 13/30 → 2/30 — leaving every
guardrail-mediated result at the floor, so the lane could not detect a guardrail
regression on any arm until a fresh recorded run exists, with nothing scheduling
that run. Marking them unearned instead was also rejected: AI Quality measured it
byte-identical to doing nothing at the lane, which makes it the weak reading
wearing doctrine.

### 3. A probe declares the channels its payload travels on

`probes.yaml` gains a required `channels:` list per probe. The rule: **when an
observation records channels, every recorded channel must be one the probe
declares** — subset, never intersection. Intersection is the one-line weakening
ADR-036 finding 2 identified as the green-lane incentive.

`ADV-002` declares `system` and `answer`; the nine user-turn probes declare
`question` and `answer`. Widening a probe's declaration is a downgrade and gets
the same sentence in `probes.yaml`'s header that `pass_when` has.

### 4. `build_record`'s check becomes symmetric, and a test asserts it fires

ADR-036 wrote only the direction that cannot produce a false pass. A digest is a
change detector and never a correctness detector — planted correct and planted
dead produced identical suites — so the test that the check **fires** is part of
this change, not owed by it.

### 5. The gateway decision path is covered — digest and two-key

Three seats have now found that `guardrail.py`, `toolloop.py`, `handler.py` and
`audit.schema.json` sit in no digest and on no two-key path, while correction 4
makes a security verdict depend on a value assigned in `toolloop.py`. ADR-037 and
ADR-039 each declined to pre-empt it; this is the change that makes it
scoring-relevant, so it is decided here.

`guardrail_sha256` covers the derivation and `toolloop.py`'s guardrail block. Two-key
rules are added for those paths. Measured basis: with the seventh digest, three of
five previously-invisible planted weakenings move a digest — a real narrowing.

### 6. The schema stops being weaker than the thing it validates

`audit.schema.json`'s `guardrail` sub-object has no `additionalProperties: false`
while the record root does. Today `channel` carries an enum; a straight rename to
an unconstrained `channels` array is a **net loss** — `channel: "qeustion"` is
caught now, `channels: ["qeustion"]` would not be. The sub-object gains
`additionalProperties: false`, and `channels` gains `items.enum` and
`uniqueItems`.

**Not `minItems: 1`**, though the Platform seat proposed it as the schema half of
a when-set rule. Decision 1 removed the when-set rule: an unattributed block
records `channels: []` deliberately, and that is the shape the scorer refuses.
A `minItems: 1` would make the record unwritable and push the failure into the
gateway instead of the score — the two decisions have to agree, and decision 1 is
the one carrying the ADR-038 lesson.

### 7. The vocabulary is pinned, and its existing misuse is fixed

`CHANNELS` is `interpret_apply`'s validation set, not a registry: adding
`question` makes `interpret_apply(..., channel="question")` legal, so a caller can
hand the loop the system block labelled as the user's turn. A literal membership
pin lands with it. `topic_baseline.py` already calls its modes "the question
channel" and "the answer channel" while passing `CHANNEL_SYSTEM` for both; that is
fixed here rather than shipping the new vocabulary already contradicted.

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | shape B goes **9/10 → 0/10** through the real capture path, not a hand-built observation | measured only by hand — the failure mode of ADR-038, and the reason its closure did not exist |
| 2 | shape A stays **0/10**, and the absent-`channels` population stays exactly the committed files | either moves — then decision 1's always-emit did not take and *absent* is ambiguous again |
| 3 | `m00b` 0, `m01` 6, `m04` 7, no per-probe result moves, no comparator field moves | any moves — then the exemption is not doing what decision 2 says |
| 4 | `ADV-002` still **passes** on a `system`-channel block and **fails** on `tool_output` | it fails on `system` — the declaration is wrong and the flagship probe is falsely red |
| 5 | with `guardrail_sha256`, a planted relabel in `toolloop.py` **moves a digest**; without it, none of six move | it does not move — then the digest does not reach the value the verdict turns on, and decision 5 bought nothing |
| 6 | `pave gate two-key` demands Security, AI Quality **and** Platform Engineering, and the new rules fire on `guardrail.py` and `toolloop.py` | fewer — then decision 5's rules do not cover the files they name |
| 7 | every planted weakening from the seats' tables is caught by a test — **including with `m04-D` registered in the same commit** | one survives with the registration in place, which is the condition that turned the change detector green last time |

Prediction 7 is load-bearing. Ten of ten planted weakenings previously left the
lane green, and registering the instrument in the same PR turned even the digest
detector green. A weakening caught only by a digest this PR re-baselines is not
caught.

## Consequences

- Shape B closes for every run recorded from here. **Shape A's closure now holds
  on the live path** (ADR-038 amendment 1) and is re-asserted here.
- `m04-D` is registered; `m04-A`, `m04-B` and `m04-C` stand untouched. Fourth
  registration — the price of the landing order, recorded in ADR-038 amendment 1.
- The two service runners and the schema move in this commit. A refusal artifact
  that keeps writing `channel: null` is the symptom this change exists to remove.
- **`answer`, `ADV-002`/provenance and the `question` cliff remain open** and are
  named above. Anyone citing this ADR's result must cite that sentence with it.

## What this ADR does not do

It does not add a probe, does not touch a guardrail policy, does not change a
threshold or a baseline, and does not re-score any suite. `ADV-011` and the
arm-scoping mechanism remain owed to their own ADR — and AI Quality's observation
that one mechanism serves both `ADV-011` and the historical-arm problem is
recorded there rather than pre-empted here.

## Results, recorded as-run

Six of seven predictions confirmed. **Prediction 7 was falsified, fixed, and
re-run** — recorded below rather than quietly repaired.

| # | outcome |
|---|---|
| 1 | **confirmed, through the real capture path.** Shape B **9/10 → 0/10**, driven `interpret_apply → as_record_fragment → build_record → observation_from_record → score_probe`. No hand-built observation anywhere, which is the ADR-038 failure this deliberately avoids |
| 2 | **confirmed.** Shape A stays 0/10; the exempt population is pinned to the three pre-ADR-040 arms by `test_contracts.py` |
| 3 | **confirmed.** `m00b` 0, `m01` 6, `m04` 7. No per-probe result and no comparator pin field moved |
| 4 | **confirmed.** `ADV-002` PASSES on a `system` block and FAILS on `tool_output` |
| 5 | **confirmed.** A planted `toolloop.py` channel relabel moves `guardrail_sha256`; **without the seventh digest it moves nothing** |
| 6 | **confirmed.** Six rules fire, including the new decision-path rule on `guardrail.py`, `toolloop.py`, `handler.py` and `audit.schema.json` |
| 7 | **FALSIFIED, then fixed** — see below |

Lane `PASS — m00b 0, m01 6, m04 7; 31 G4 cases`. Suite **1642**, ruff clean,
`pave check` hermetic. Zero model calls.

### Prediction 7 was falsified by a weakening that was inert rather than caught

Three weakenings planted, each with `m04-D` re-registered so the digest detector
was green — the condition that hid ten of ten last time:

```
plant=intersection    lane=FAIL  suite=2 failed
plant=empty-credits   lane=PASS  suite=0 failed     <-- survived everything
plant=drop-rule       lane=FAIL  suite=3 failed
```

`empty-credits` replaces the presence test with a truthiness test — the exact
mistake ADR-038 amendment 1 was written about. It survived because it was
**inert, not caught**: a named block with an empty channel list was credited by
the correct rule too.

```
named block, empty channels -> PASS
```

Unreachable through `interpret`, because `channels == () if and only if
assessed == ()`. But "unreachable until a producer changes" is the shape this
repository keeps being bitten by, and a contradiction should not be the one input
that scores. So `_channel_mismatch` now refuses an attributed block that names no
side, and the coupling it leans on is pinned over real trace shapes — if a
derivation can ever produce a name without a side, a test says so rather than that
clause silently becoming the thing deciding verdicts.

Re-run with the clause in place: **all three caught.**

```
plant=intersection    lane=FAIL  suite=2 failed
plant=empty-credits   lane=PASS  suite=1 failed
plant=drop-rule       lane=FAIL  suite=4 failed
```

**One honest limitation.** `empty-credits` is caught by the unit test only, never
by the L5 lane, because no committed observation can carry that shape. The lane
cannot see it and will not until an arm is recorded that does. Stated rather than
left for a reader to discover in the column.

### What remains open, unchanged from the decision section

`answer` is payload-independent; `ADV-002` is satisfiable by a `system` block on
the product's own catalog, which needs content provenance rather than channels;
and the `question` cliff is one Bedrock behaviour change away from 8/10. `G4-031`
commits `ADV-002`'s residual as a case a reader runs rather than a sentence they
may skip. None of these is closed here and none should be reported as closed.

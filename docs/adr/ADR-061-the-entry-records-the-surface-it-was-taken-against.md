# ADR-061: the entry records the tool surface it was taken against

**Status:** Accepted. **Zero model calls. Nothing is deployed to AWS.**
**Seats:** AI Quality · Security · Platform Engineering (`evals/run_evals.py`,
`evals/history/schema.json`, `pave/history.py` — all three on one rule).

Discharges the precondition ADR-058 recorded against the AI Quality seat:

> **the instrument records nothing about the routed tool set.** Measured
> byte-identical with the tool unrouted. Before `tool_before_answer` may move
> from `deferred` to `scored` (Decision 11), the deterministic instrument must
> carry the routed set or `TOOL_SPECS_SHA256`, or two runs with identical
> fingerprints could differ on twelve of twenty-five cases purely from
> deployment. A precondition, and cheaper now than after a published row depends
> on it.

## The exposure, measured

Twelve of the twenty-five golden cases carry `expect_tool_before_answer`:

```
blackout-001  blackout-006  blackout-007  blackout-008  blackout-009
brand-020     concise-022   edge-024      entitlement-002
entitlement-010  entitlement-011  multi-023
```

Eleven of them also carry `entitlement_source`. So what the gateway routes
decides how nearly half the suite can score, and a golden entry recorded
**nothing** about it: `m06-goldens.json`'s keys are `sha, suite, target,
recorded_at, scores, cases, k, samples_from, tag, tokens_in, tokens_out`.

Two runs taken either side of a deployment were therefore indistinguishable in
every field a reader compares.

## What was decided

### 1. A `tool_surface` block on the entry

```json
"tool_surface": {
  "routed": ["catalog-search", "entitlement-check"],
  "tool_specs_sha256": "6097664dba62dbff612b9551f2eed609f5926922179e46b4df01a1c851cf7b03"
}
```

`routed` is **sorted**, because that half is a set question — *was the tool
routed* — and a reader diffing two entries should not read a reordering of the
deployment table as a change of surface. `tool_specs_sha256` is the half that
carries order, and it is the digest of the input schemas the model is shown, in
the routing table's order.

### 2. Not under `instrument`

`instrument` already means the **judge** instrument on a golden entry (ADR-032).
Two different objects sharing one key across entry kinds is precisely the
substitution the instrument registry exists to prevent, and a reader resolving
`instrument` would have got a different object depending on which entry they
opened.

### 3. Optional, and absent means UNKNOWN

Every entry recorded before this field existed lacks it. `check_tool_surface`
skips those rather than reading absence as an empty surface — ADR-057's rule for
`tool.executed`, the same hazard one file over. Scoring absence as *nothing was
routed* would assert about runs nobody measured.

**Nothing is backfilled.** Rewriting a committed entry to add the field is a
history rewrite, which ADR-027 forbids outright. The M02 and M06 pinned runs stay
UNKNOWN, and the honest way to recover their surface is their own `sha`. Decision
11 therefore inherits a suite where **future** runs are self-describing and the
pinned historical ones are not — stated here rather than left to be discovered
when that decision is taken.

### 4. The recorded value is checked against the entry's own commit

`evals/run_evals.tool_surface` derives the field from the working tree.
`pave/history.check_tool_surface` re-derives it from the blobs at the entry's
`sha` via `git show` and refuses a disagreement.

Without that, the field is a string the recording PR chose — which is the defect
ADR-041 recorded about `scores.total` and ADR-042 about a fabricated
`probes_sha256`. Twice now a value described as one "the same PR cannot invent"
turned out to be one it could, so this one is checked from the start rather than
after a third finding.

**`pave.infra.routed_tools` is imported rather than duplicated**, unlike
`corpus_digest` beside it. That module's rule is *do not import the thing you are
checking* — there, the scorer. Here the thing being checked is the recorder's
claim about a commit; the CloudFormation reader is shared ground, and a second
parser of the snapshot would be a second opinion about its shape, which is the
fault rather than the protection.

### 5. The schema pin moves in this diff

`schema.json` is byte-pinned at `pave/history.py:SCHEMA_DIGEST`, a Security-found
ratchet that `check_schema` cannot otherwise see through: the ratchet refuses a
*requirement* no entry meets and says nothing about a **loosening**. This change
is an addition — top-level `required` is untouched at five, nothing optional
became required or the reverse, and the new sub-schema is
`additionalProperties: false`. The pin is moved in the same diff, which is what
it is for: the edit is a line somebody has to defend.

## What this does not do

- **It does not un-defer `tool_before_answer`.** That is Decision 11 and it is
  still open. This removes the stated obstacle to taking it; it does not take it.
- **It does not touch `evals/comparators.json`,** any instrument digest, any
  history entry, or `evals/deterministic.py`. No recorded number moves.
- **It is not an observation from the run.** The field is derived from the
  committed CDK snapshot, which ADR-017's synth-freshness job holds equal to the
  deployed stack by re-synthesizing and blocking on drift. It is trustworthy
  exactly that far and no further — a stack hand-edited in the console would be
  recorded wrongly. `TOOL_SPECS_SHA256` rests on the same snapshot, so this adds
  no new trust, and saying so is cheaper than a reader assuming a measurement.
- **It does not record the surface in the run FILE.** `run_with_tools.py`
  produces the answer files the comparator re-scores, and it is on **no two-key
  rule at all** — recorded here as a finding, not fixed, because changing the
  producer of the run this milestone is about to take is not a change to make
  days before taking it.

## The audit

The check is **vacuous on the committed tree**: no entry carries the field yet,
so `check_tool_surface()` returns `[]` whether it works or not. That is the
*stated and absent* shape, so every assertion plants an entry and proves the
check is reachable. Five plants, each confirmed applied before the run and
restored after:

| plant | caught by |
|---|---|
| the check unregistered from `run_all` | `test_the_check_is_registered_in_the_gate` |
| the recorder stops attaching the field | `test_the_recorder_attaches_the_surface_to_a_golden_entry` |
| the check stops comparing `routed` | `test_a_fabricated_routed_set_is_red` |
| the check stops comparing the digest | `test_a_fabricated_specs_digest_is_red` |
| the schema drops `additionalProperties: false` | `test_the_schema_refuses_a_malformed_surface` |

Five for five. A truthful surface passing (`test_a_truthful_surface_passes`) is
the control, without which every red above could be a check that always fails.

**The registration test was itself a finding.** Its first version asserted
against a `gate_history` in `pave/history.py`, which does not exist — the
dispatch list is in `run_all`, and the CLI function of that name is one module
up. A test written to assert registration and quietly passing against the wrong
symbol is the failure it exists to prevent; it failed loudly instead, which is
recorded because the near-miss is the interesting half.

## Counts

`pytest -q`, on this tree: **2424 passed, 6 skipped**, from `main` at `6e9ef5b`'s
**2405**. `COLLECTED_FLOOR = 2255`. `make check`: **PASS**.

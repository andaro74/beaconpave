# The entry records the tool surface it was taken against

Discharges the precondition ADR-058 recorded against AI Quality. **Zero model
calls. Nothing is deployed to AWS.** ADR-061.

## The exposure

Twelve of the twenty-five golden cases carry `expect_tool_before_answer`:

```
blackout-001 blackout-006 blackout-007 blackout-008 blackout-009 brand-020
concise-022  edge-024     entitlement-002 entitlement-010 entitlement-011 multi-023
```

Eleven also carry `entitlement_source`. So what the gateway routes decides how
nearly half the suite can score — and a golden entry recorded **nothing** about
it. `m06-goldens.json`'s keys: `sha, suite, target, recorded_at, scores, cases,
k, samples_from, tag, tokens_in, tokens_out`. Two runs taken either side of a
deployment were indistinguishable in every field a reader compares.

## What this adds

```json
"tool_surface": {
  "routed": ["catalog-search", "entitlement-check"],
  "tool_specs_sha256": "6097664dba62dbff612b9551f2eed609f5926922179e46b4df01a1c851cf7b03"
}
```

The digest is derived, and it equals `tests/test_gateway_run_parity.py`'s
`TOOL_SPECS_SHA256` literal — a test asserts the two agree rather than leaving
two copies of one expression to drift.

Four decisions worth reading in ADR-061: it is **not** under `instrument` (that
key already means the judge instrument on a golden entry — ADR-032); it is
**optional and absent means UNKNOWN**, never an empty surface; **nothing is
backfilled**, because rewriting a committed entry is a history rewrite; and the
recorded value is **re-derived from the blobs at the entry's own `sha`** and a
disagreement is refused, because otherwise the field is a string the recording PR
chose — the defect ADR-041 found in `scores.total` and ADR-042 in a fabricated
`probes_sha256`.

## The schema pin moves here, deliberately

`schema.json` is byte-pinned at `pave/history.py:SCHEMA_DIGEST` — a
Security-found ratchet, because `check_schema` refuses a *requirement* no entry
meets and cannot see a **loosening**. This change is an addition: top-level
`required` untouched at five, nothing optional became required or the reverse,
and the new sub-schema is `additionalProperties: false`. Moved in the same diff,
which is the pin's whole purpose.

```
99d4d72b65ab... -> 1d5964c23553...
```

## Plants — five of five, none silent

The check is **vacuous on the committed tree**: no entry carries the field yet,
so it returns `[]` whether it works or not. That is the *stated and absent* shape,
so every assertion plants an entry rather than asserting the check is present.

| plant | caught by |
|---|---|
| the check unregistered from `run_all` | `test_the_check_is_registered_in_the_gate` |
| the recorder stops attaching the field | `test_the_recorder_attaches_the_surface_to_a_golden_entry` |
| the check stops comparing `routed` | `test_a_fabricated_routed_set_is_red` |
| the check stops comparing the digest | `test_a_fabricated_specs_digest_is_red` |
| schema drops `additionalProperties: false` | `test_the_schema_refuses_a_malformed_surface` |

Plus `test_a_truthful_surface_passes` as the control, without which every red
above could be a check that always fails.

**The registration test was itself a finding.** Its first version asserted against
a `gate_history` in `pave/history.py`, which does not exist — the dispatch list is
in `run_all` and the CLI function of that name is one module up. It failed loudly
rather than passing against the wrong symbol, which is the failure mode it exists
to prevent.

## What this does not do

- **It does not un-defer `tool_before_answer`.** Decision 11 is still open. This
  removes its stated obstacle; it does not take the decision.
- **It does not touch `evals/comparators.json`,** any instrument digest, any
  history entry, or `evals/deterministic.py`. No recorded number moves.
- **It is not an observation from the run.** Derived from the committed CDK
  snapshot, which ADR-017's synth job holds equal to the deployed stack — as
  trustworthy as that and no further. `TOOL_SPECS_SHA256` rests on the same
  snapshot, so no new trust is added.
- **Decision 11 inherits a split suite**, recorded in `SPEC/06b`: entries from
  here are self-describing, and the M02 and M06 runs the comparator actually pins
  carry nothing. Smaller than the obstacle ADR-058 named, and not none.

## A finding, recorded not fixed

`services/highlights-agent/run_with_tools.py` — the producer of every answer file
the golden comparator re-scores — is on **no two-key rule at all**. Named here
rather than fixed: changing the producer of the run this milestone is about to
take, days before taking it, is not a change to make in this diff.

## Counts

| tree | `pytest -q` |
|---|---|
| `main` at `6e9ef5b` | **2405** passed, 6 skipped |
| this branch, files untracked | **2425** passed, 6 skipped |
| this branch, **committed** | **2432** passed, 6 skipped |

`COLLECTED_FLOOR = 2255` (`pave/floors.py:309`). `make check`: **PASS**.

The last row is this branch paying for its own documents:
`test_cited_commits_resolve.py` globs the filesystem and
`test_no_account_identifiers.py` uses `git ls-files`, so an added `.md` is worth
more committed than untracked. Recorded because a table that stopped at the
untracked figure would describe a tree nobody will ever check out.

Two-Key-Disposition: ai-quality
Two-Key-Disposition: security
Two-Key-Disposition: platform-eng
Two-Key-Rationale: Three seats because the recorder, the history schema and the
  append-only checks are one rule, and this change touches all three by design:
  the field is written in one place, described in the second and verified against
  the entry's own commit in the third, and splitting that across diffs would land
  a recorded field before the check that keeps it honest. AI Quality owns what a
  recorded number means, and the point of the change is that a golden number was
  not interpretable without knowing which tools were routed when it was taken —
  twelve of twenty-five cases turn on it. Security's key is collected because the
  byte pin on the schema is a Security-found ratchet against a loosening, and it
  moves here; the movement is an addition with top-level `required` untouched and
  the new sub-schema closed in both directions. Platform Engineering owns the
  derivation and the snapshot it reads. Nothing is backfilled, no history entry
  is rewritten, no comparator or instrument digest moves, no golden case is
  edited and no baseline is reset. The field is optional and absent stays UNKNOWN,
  so no run recorded before it exists is retroactively asserted about.

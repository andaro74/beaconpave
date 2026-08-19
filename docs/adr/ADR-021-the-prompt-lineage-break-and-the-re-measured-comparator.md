# ADR-021: the prompt lineage break, and what the comparator becomes

**Status:** Accepted (M02)
**Seats:** AI Quality (comparability, two-key) · Service Team (the callers) ·
Platform Engineering (the gateway)

## Context

Three milestones of golden scores are comparable because one thing never moved.
`services/highlights-agent-baseline/run_baseline.py` and
`services/highlights-agent/gateway_client.py` carry a byte-identical `SYSTEM`
prompt, and `tests/test_gateway_run_parity.py` fails if they drift. That pin is
why M01 could say its delta was the gateway: exactly one variable moved between
two runs.

**M02 moves the prompt on purpose.** The catalog stops being inlined and comes
back through `catalog-search`, so the prompt that ends with `CATALOG: {catalog}`
cannot survive the milestone. What the pin bought was **attribution**, and M02
has to buy the same guarantee rather than abandon it.

This is the third time the ADR-016 hazard has arrived somewhere new, and the first
time it arrives with the sign reversed.

## The distinction this rests on

ADR-016 recorded an **instrument moving under a fixed system**: the same m00b
answers scored 15/25 and then 18/25 — three points of improvement with no system
change whatsoever.

M02 is the mirror. **The system moves under a fixed instrument.** The corpus, the
asserts, the scorer, the evaluation clock and the catalog fixture are untouched.
That is the good case, and it is only the good case if nothing *else* moves.

So what disqualifies M01's recorded **19/25** as M02's comparator is not ADR-016
at all. It is that **19/25 is n = 1**, and M01's own close proved a single sample
cannot tell a three-case regression from variance: the paired per-case diff showed
three cases lost to the gateway and four gained by noise, and the headline +1
concealed a real −3.

## Decision

**Two arms, re-measured the same day, against the same deployed gateway and the
same pinned guardrail version, at k = 3 samples per arm. The result is the paired
per-case diff, not the total.**

- `services/highlights-agent/run_via_gateway.py` and the `SYSTEM` prompt **freeze
  and become the control arm** — a second control, exactly as the m00b baseline
  runner is the first. Not deleted, not refactored, not tidied.
- `services/highlights-agent/run_with_tools.py` is the M02 arm. It shares the
  clock, the user-turn shape, the invoke path and the decoder with the control by
  importing them, so those cannot drift between arms by construction rather than
  by inspection.
- Both arms are summarised by **per-case majority across k = 3**, and
  `evals/history/schema.json` carries `k` and `arm` so the record says so. All six
  runs are committed; the journal reports every sample.
- A run returning INFRA for any case is **re-run in full**, and both the discarded
  and the replacement run are committed. An undesignated re-run is a cherry-pick
  door that opens the moment a network hiccups.
- The recorded `m01` row stays exactly as it is and is explicitly **not** the
  comparator. History is append-only.

### The prompt diff is two changes and is checked as a diff

`TOOL_SYSTEM` is `SYSTEM` with the catalog block removed and one sentence
repointed — *"using only the catalog below"* became *"using only catalog titles
returned by the catalog-search tool"*, because the first sentence would otherwise
point at nothing.

`test_the_m02_prompt_is_the_control_prompt_minus_the_catalog_and_nothing_else`
compares the two line by line and names the differing lines. **No tool-use
coaching was added** — no "search before answering", no "broaden your query if you
get no rows", no worked example. Each would raise the M02 score, and each would be
tuning the prompt to a golden set whose result this milestone has already
predicted in writing. Coaching around a loss mechanism after predicting it is how
a prediction stops being one.

## What happened to the parity test, and how it differed from the plan

SPEC/02 planned for the `SYSTEM` byte-identity assertion to **end**, on the
assumption that the governed caller's prompt would be replaced.

**It did not end, and keeping it is the stronger outcome.** The governed caller's
prompt is not replaced — a second one is added — because the same spec requires
`run_via_gateway.py` to freeze as the control arm. `SYSTEM` is therefore now the
*control arm's* prompt in both files, and pinning it byte-identical matters more
than it did: a drift would no longer blur M01's delta, it would blur M02's,
because the control arm is being re-measured today. The spec is amended in place
rather than quietly satisfied differently.

The rest of the split is as planned:

| assertion | disposition |
|---|---|
| `SYSTEM` byte-identity | **kept**, with a changed job — it now pins the control arm of M02's comparison |
| `CLOCK` parity | **kept and widened** — no arm may define a second clock or build its own user turn |
| transport decoding, compared structurally | **kept**, and it matters more: a prompt change is the ideal camouflage for an answer repair |
| pinned model profile (ADR-015) | **kept** |
| — | **new:** the catalog fixture's own bytes must be absent from `TOOL_SYSTEM` |
| — | **new:** `TOOL_SYSTEM` is hash-pinned |
| — | **new:** the two arms differ in the prompt they build and in asking for tools, and in nothing else |

## Consequences

**The hash pin is weaker than byte-identity, and that is not hidden.** `SYSTEM`
is pinned by comparison to a second, independent copy; there is nothing to compare
`TOOL_SYSTEM` to, so it is pinned to a recorded digest. A digest catches drift; it
cannot catch a prompt that was wrong when it was written. What it buys is the
thing that matters here — a word added between the two arms of one comparison
cannot pass unnoticed.

**Updating `TOOL_SYSTEM_SHA256` is a system change and an entry in the
progression row.** It is allowed. Doing it *between* the two arms of one
comparison is not.

**The control arm cannot tag its audit records per sample**, because adding a
`--sample` flag would edit a frozen file. Its three runs write three versions of
one lake key; its three answer files are distinct, and the golden score is
computed from the answers. The M02 arm does carry the sample in its `request_id`.
The asymmetry is recorded here rather than discovered in the lake.

**The golden score is expected to fall — 10/25 ± 4** — with four loss mechanisms
and four cases named in advance in SPEC/02. A score materially *above* the
prediction is as much a finding as one below, and the first thing to suspect is
that the catalog got back into the prompt by a route nobody meant. That is what
`test_the_catalog_is_gone_from_the_m02_prompt` checks against the fixture's own
bytes rather than against the absence of the word "CATALOG".

**At scale, replace with:** a prompt registry with versioned entries, where every
recorded run names the prompt version it ran and the comparator is selected by
version rather than by a test asserting two files agree. The hash pin here is the
one-file version of that, and the shape is the same.

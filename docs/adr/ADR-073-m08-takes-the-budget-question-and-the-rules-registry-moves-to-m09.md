# ADR-073: M08 takes the budget question, and the rules registry moves to M09

**Status: PROPOSED in M08 PR 1; ACCEPTED when that PR merges, which is the
operator's disposition.** Decision 1 is the operator's and is recorded here,
not argued. Decisions 2 and 3 are written before any ceiling or agent moves,
and the PR that moves either is the one the seats review. **Zero model calls
to write** — every number below is read out of `milestones/M08/context-census.json`,
which `milestones/M08/context_census.py` produces from files committed since
M02 and `tests/test_m08_census.py` refuses to let drift.

**Seats:** PM (the roadmap shifts by one row) · AI Quality (the ceiling is an
eval threshold, and G9 is the constraint on how it may move) · Platform
Engineering (the loop whose shape the census describes).

## Decision 1 — M08 takes the budget question; the rules registry moves to M09

M07 closed at **2/25** with the first goldens entry since M06, and every one of
the 22 answered-and-wrong cases fails `budget` on `tokens_in` — 6022 to 9220
against a ceiling of 6000, fifteen on that assert alone. The journal named it
*"M08's first question, before the rules registry touches the tools arm: what
grew the context fivefold between M06 and M06b, and whether the ceiling or the
context is the thing to change."* `README.md:46` had M08 as *Rules registry +
regdelta loop*.

**The operator resolved it: M08 answers the budget question first.** Claim 6's
milestone — the rules registry and the regdelta loop — moves to M09, and every
later row shifts by one: surfaces to M10, the drill to M11, self-heal to M12.
Not relitigated here; recorded so the record and the table agree. The reason
the journal gave stands as the reason: until the ceiling question is answered,
every number the rules loop would produce on this arm is a budget number
wearing a disclosure case's clothes.

### Sites corrected in PR 1, and sites left as-run

Corrected, because they are live documents a reader consults for what is
scheduled — ADR-070 decision 1's list, plus the one file that list missed:
`README.md` (the progression table gains row 08 and renumbers 09–12; the *Part
two (M05–M12)* line; the twelve-claims table's `M` column; the ❅ and ✚
sentences that say where claim 6 is), `BUILD.md` (the milestone table),
`SPEC/README.md`, `docs/governance/demo-script.md` (Acts 3–5 and the ADR-047
line), `docs/governance/recordings.json` (Acts 3–5's `owner_milestone` and
`owed_by`; a renumbering, `deferred_from` untouched, two keys), and
**`quality/judge/calibration/labels.json`** — the `brand_tone` owe follows the
milestone its reason names, M08 → M09, with ADR-026 amendment 3, two keys.
ADR-070's sweep omitted that file and the M07 close found it red; it moves in
the same diff as the table this time.

Left as-run, because they are records of what was believed when written: every
closed journal and every ADR that says *"claim 6 is M08's"* or *"the second
brand is M08's"*, ADR-070 decision 1 itself, and SPEC/07.

Left for **M08 PR 2**, listed so it is a checkbox rather than a discovery: the
six code and template sites ADR-070 decision 1 dated to the SPEC/08 PR —
`pave/cli.py:699`, `pave/floors.py:338`, `pave/manifest.py:142,324`,
`pave/scaffold.py:123`, `templates/agent-tools/README.md:28`,
`tests/test_floors.py:250` — say *M08*, meant *M09* after ADR-070, and mean
**M10** now. They sit on three two-key rules, one of them four seats, and the
reasoning that kept them out of ADR-070's documents PR keeps them out of this
one; the difference is that PR 2 is a zero-call register PR whose whole
purpose is to collect those attestations, dated in SPEC/08. That is one slide,
named.

## Decision 2 — two outcomes, pre-registered, and the rule that picked between them

The question has two answers and each has a different cost, so both were
written down with the rule before the census was read (the plan the operator
approved, 2026-09-06, and SPEC/08's *Pre-registered* section):

- **A — the agent carries context it does not need.** Then M08 fixes the
  agent, the ceiling stays at 6000, and the measurement is a fresh k=3 tools
  run through the deployed gateway.
- **B — 6000 is the wrong ceiling for a two-tool loop.** Then the ceiling is
  re-derived from the census by ADR-014's own pinned rule, in an ADR-014
  amendment on two keys, and the measurement is the committed stage-2 evidence
  re-scored and recorded.

**The rule.** For every answered stage-2 sample at its case's *mandated* call
count — two model calls (search, answer), three when the case expects
`entitlement-check` before the answer, because its argument is a title id the
search returned — the gap is its excess over 6000 spread over its calls.
Outcome A holds iff every such sample over the ceiling is covered by its **own
evidenced removable content**: replayed rows the answer never cited, text sent
twice in one request, content the manifest does not declare. Schema prose and
tool descriptions are design, not evidence: trimming them to fit 6000 is the
mirror image of moving 6000 to fit them, and neither counts.

### What the census says

Read off the record; exact unless marked.

| run | answered | modal calls | per call at the mode | median turn | over 6000 |
|---|---|---|---|---|---|
| M02 tools arm, one tool offered | 68/75 | 2 | 1693 | 3394.5 | 4 (three 4-call turns, one 6-call) |
| M06, the single-call arm | 73/75 | 1 | 1203 | 1203 | 0 |
| M06b tools arm, two tools | 25/75 | 3 | 2058 | 6190 | 18 |
| M07 stage 1 | 24/75 | 3 | 2067 | 6388.5 | 18 |
| **M07 stage 2** | **73/75** | **3** | **2057** | **6185** | **66** |

- **`tokens_in` is a sum over every `converse` call in the turn**
  (`core/toolloop.py::_accumulate`; `core/meter.py` reads Bedrock's
  `inputTokens` per call). Stage 2 by call count: 2 calls **3887–3959**
  (n=7), 3 calls **6022–6792** (n=52), 4 calls **8181–9220** (n=13), 5 calls
  **11081** (n=1). The ceiling is entirely above every 2-call turn and
  entirely below every 3-call turn. One more call costs 2222–2681 by adjacent
  medians and 2026–2328 within a case.
- **The journal's "fivefold" compares two arms.** M06's 1203 is the single-call
  arm — the catalog inlined, no tools, the shape ADR-014's original ceiling was
  derived for. The tools arm's own line runs M02 → M07 stage 2 at ×1.82 on the
  median, and the census splits it: the modal turn went from 2 to 3 calls when
  `entitlement-check` became a second sequential tool round at M06b (×1.5), and
  the per-call input went from 1693 to 2057 (×1.22). The sentence is computed,
  not written, and is in the record verbatim.
- **What one call carries** (estimated; chars converted at 3.368–3.389
  chars/token from ADR-014's six committed anchors): the system prompt ≈793,
  of which the answer schema ≈692; the two tool specs ≈603 (`catalog-search`
  321, `entitlement-check` 282); the viewer's turn ≈41. The per-call base
  bounded exactly from the seven 2-call samples is **1859–1974**; committed
  text explains ≈1437 of it and the residual **422–537** is *not in any
  committed text the client or gateway sends* — recorded, not attributed.
- **Tool results are tiny.** Replayed over the committed catalog: one row is
  216 characters, no rows is 15. The carried-forward context per round is
  small; the per-call base is the number.
- **Removable evidence:** two samples carry rows the answer did not cite
  (`grounded-018`, which cited nothing), worth at most ≈144 tokens per call
  on those samples; one line is sent twice in every request — the JSON Schema
  `$schema` URL, in the answer schema and in each tool contract — ≈16 tokens
  per call; no offered tool is undeclared by the manifest.
- **The rule's reading:** 40 answered samples at their mandated call count, 33
  over the ceiling (maximum **6235**, `blackout-008`), **0** covered by their
  own removable content; the largest per-call gap is 78.3. 33 samples ran above
  their mandate (minimum 6022). **Outcome B.**

### The reader's first run printed A, and why that reading is in the record

The first run of `context_census.py` compared the largest removable amount in
the run (`grounded-018`, ≈144 per call) with the largest gap in the run
(`blackout-008`, 78.3 per call) and printed **A**. That reading is incoherent
with A's own pre-registered falsifier — *after the change, zero samples at the
mandated call count over 6000* — because a sample that carried nothing
removable cannot be brought under the ceiling by removing it, and 33 of the 33
over-ceiling samples at the mandated count carry zero uncited rows. The rule
was rewritten to read per sample, the cross-sample figure stays in the record
under `cross_sample_reading_not_the_rule`, `tests/test_m08_census.py` pins the
per-sample reading with a synthetic pair, and this paragraph exists so the
correction is a recorded reading rather than a quiet one. The rule's text — "is
≥ gap per call" — admitted both readings; that is the defect, and it was the
author's.

## Decision 3 — how a ceiling may move under G9, and what the number is derived from

ADR-014's M02 amendment is the precedent and the constraint. It moved
`tokens_in` from 1500 to 6000 because *"the ceilings did not become wrong
because the system got worse; they became wrong because they measure a shape
that no longer exists"* — one call became a loop of two or three. It derived
the number as 1.22× the measured maximum of the new shape, placed **below** a
four-call turn, because *"a loop that starts iterating more than the measured
shape is the runaway generation case"*, and it recorded that the identical
edit made after a red run would be the forbidden one. `tests/test_budget_derivation.py`
pins the band (1.15–1.60× the measured maximum) against the committed
measurement.

The same thing happened again at M06b: two calls became three when the second
tool arrived, and the per-call base grew with the second tool's spec. The
ceiling did not move, and M06b's eighteen over-ceiling samples were invisible
behind seventeen refusals until M07 cleared them. The shape the ceiling
measures no longer exists, for the second time.

**How the number is produced, and how it is not.** In M08 PR 3, ADR-014
amendment 2 re-derives `tokens_in` from the census record by the pinned rule:
within 1.15–1.60× the maximum of the mandated shape (6235), placed below the
minimum four-call turn (8181), so the runaway case the ceiling exists to catch
stays caught. That band is **7170 to 8180**, and the number is whichever value
in it the amendment argues; the argument may cite the census and ADR-014's own
placement logic, and may not cite which cases pass. If the rule yields no
number — a floor at or above the next call count's minimum — the ceiling does
not move and the milestone closes red on the census. The manifest's
`max_tokens_in` moves with it by the margin it has always had; `tokens_out`,
`max_ms` and the per-case tiers do not move, for the reason ADR-014 gave.
Two keys on the cases (AI Quality), two on the derivation pin (AI Quality,
Platform Engineering), two on the manifest (AI Quality, Tool Owner); the seats
review that PR and no other.

**The ordering is the protection.** The census was run and committed before any
ceiling was proposed; the band follows from the census by a rule pinned two
milestones ago; the re-score in PR 4 happens after the number is signed. What
the reader refuses to print — a pass count at any ceiling but 6000 — is what
keeps that order checkable rather than asserted.

**What the ceiling will still catch.** Every 4- and 5-call turn in stage 2 is
above the band's roof: `recommend-013` and `recommend-014` at three samples
each, `multi-023` at three, `grounded-018` at two, one sample each of
`recommend-003`, `edge-025` and `grounded-019`. Those are `catalog-search`'s
browse gap — a model that cannot browse searches again — and the census names
them as such; a ceiling that passed them would catch nothing, which is the
failure ADR-014's roof exists to refuse. That is the budget axis's headroom.

## What this ADR does not decide

- The number. PR 3's amendment to ADR-014, on two keys.
- The suite `p95_ms` ceiling, OVER since M06 and at 5431 ms now. The census's
  latency table (model time alone runs 2289 ms at two calls and 3606 ms at
  three; the guardrail adds 770–1212 ms in its own key) is the evidence; the
  disposition is PR 3's, in the same amendment, and is a signed ceiling or a
  standing finding, never a silent move.
- Whether `catalog-search`'s browse gap is fixed. Tool Owner, no ADR, as
  ADR-070 left it; not this milestone's.
- The residual 422–537 tokens per call the census cannot attribute. Recorded.
- Security's two `tool_request` probes and `recommend-003`'s answer-channel
  refusal — Security's, at PR 3's seat round (SPEC/08).

## Consequences

- The progression table has thirteen rows through M12; three obligation
  registers (`recordings.json`, `labels.json`, the progression parser's
  consumers) agree with it in one diff.
- M08 is a zero-model-call milestone under outcome B: five PRs, no deploy, no
  run; the evidence is M07's, re-read. Its history entry, if PR 4's seats sign
  one, is a re-score of committed samples at a signed ceiling, which M03 did to
  the m00b commit before.
- The tools arm's `budget` assert becomes a discriminating axis again: it
  passes the mandated shape and fails the runaway one, which at 6000 it could
  not do.
- The M07 journal's "fivefold" is corrected by the record it points at, not
  rewritten.

**At scale, replace with X; the interface already matches.** Ceilings derived
per prompt architecture and re-derived automatically whenever the architecture
changes — a tool added to `toolConfig`, a schema grown — with the loop bound
enforced by the tool plane rather than asserted by the eval suite. The manifest
already declares the ceiling, the runner already reports the measurement, and
the census already reads both; only who notices the shape change moves.

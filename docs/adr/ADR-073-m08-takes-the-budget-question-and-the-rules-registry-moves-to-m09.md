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

## Amendment 1 — a cold read of SPEC/08 before PR 2, four questions answered

**Written 2026-09-06, after PR 1 merged (`dd4a5f0`) and before PR 2 opened.
Zero model calls; every number is read from `milestones/M08/context-census.json`,
`milestones/M07/goldens-score.txt`, the three journals and `pave/twokey.py`.**
The reader did not write SPEC/08. Nothing in the plan is changed by this
amendment; it names what PR 2 should change, and the operator disposes.

**Operator's disposition, 2026-09-06: accepted in full, all five asks.**
Committed in its own zero-call PR before PR 2 cut from `main`. The
M02-to-stage-2 residual differential (question 3) runs in PR 2's diff.
`p95_ms` is a **standing finding for M08**; the rule that derives a suite p95
is owed to **M09 PR 1**, written before M09's fresh run and applied after it.
No sixth PR for a signed latency ceiling. This PR is the milestone's sixth
slot spent: SPEC/08 caps M08 at six and planned five, PRs 2–5 keep their
numbers so every reference in SPEC/08 stays valid, and any later split closes
the milestone at the cap.

### 1. Is this M06b again?

**Not on the dimension that broke M06b. Yes on one clause, in M06c's shape.
And PR 3 has M07's PR-4 shape.**

| | M06b | M06c | M07 | SPEC/08 as written |
|---|---|---|---|---|
| PRs | 34 (#74–#107), no bound that held | 3 of a cap of 6 | 6 of 6 | 5 planned, cap 6 |
| Runs through the gateway | one per hypothesis, four hypotheses | one | 216 turns, two stages | none |
| When the answer was chosen | never; the milestone closed on a diagnosis | step 0, two PRs in | pre-registered band, read at PR 5 | a rule pinned in PR 1, read once, outcome B |
| What broke | the premise was unmeasurable on arrival; an investigation the plan had not priced was adopted and could not be bounded | the claim was unreachable by the plan beneath it, written by the author who had just learned why | 22/22 wrong answers failed one assert refusals had masked; the close found an owe the plan had not | see below |

What M06b did that SPEC/08 does not: measure again after every negative result.
SPEC/08 has no measurement to repeat — every PR reads M07's files, the rule
that picks A or B ran once, and a red census closes the milestone rather than
opening a hypothesis. The unbounded loop has no entry point here.

What SPEC/08 does that M06c did: **PR 4's Definition of done is unreachable as
written.** The side-prediction says the flipped set is *"exactly the
budget-only cases with a ≤3-call majority"*, and constraint 4 keeps
`tokens_out` where it is. Five of the fifteen budget-only cases fail
`tokens_out` on two or three of their three samples at unchanged tiers —
`blackout-001`, `blackout-007`, `blackout-008`, `blackout-009`,
`concise-022` (transcript: *"tokens_in=6169 over 6000; tokens_out=330 over
300"*, tiers from `cases.yaml`, per-sample `tokens_out` from the census).
They cannot flip on a `tokens_in` move. The word *"exactly"* is a biconditional,
so PR 4 fails its own checkbox on those five before the number is chosen, at
any number in the band. The upper bound of 17 was the M07 journal's *"strike
that assert"* figure, which strikes both halves of `budget`; with one half kept
the bound is at most 12. This is a defect in the side-prediction, not in the
claim, and it is exactly M06c amendment 1's shape: written by the seat that had
just found that shape at M07. **The correction must land in PR 2, before PR 3
opens** — corrected after PR 4 prints, it is a claim rewritten to match the
outcome, which *What must not happen* forbids.

What SPEC/08 carries of M06b's fourth finding — *a survivor population read as
the whole* — in a new costume: the rule read the **attributed** population as
the whole. Question 3.

### 2. Each claim, the measurement that proves it, and the PR

| # | claim in SPEC/08 | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: the re-derived ceiling passes every ≤3-call answered stage-2 sample and fails every ≥4-call sample, nothing else moved, same three files | `tests/test_budget_derivation.py` re-pointed at the census: `floor ≥ 1.15 × 6235`, `roof ≤ 1.60 × 6235`, and a new assertion `ceiling < 8181`. Then `run_evals --arm tools` over M07's files; every per-sample `budget` verdict read against the census's per-sample `calls` column — a join the PR-4 transcript must show, not a count. `context_census.py --check` green; `git diff --stat milestones/M07/` empty; `probes_sha256`, `g4_cases_sha256`, the judge digests unchanged | PR 3 (band, placement), PR 4 (the join) |
| 2 | Side-prediction: `N/25`, 2 ≤ N ≤ 17, flipped set exactly the budget-only ≤3-call-majority cases | The same transcript. **Falsified in advance for five cases** (question 1). Measurable only after PR 2 restates it as *fails `budget` on `tokens_in` alone at M07 and passes every other assert including `tokens_out` on the ≤3-call majority*, with the bound re-derived from the transcript at 6000 and the tiers — not from any run at a new number | PR 2 restates; PR 4 measures |
| 3 | `tokens_in` is a sum over the turn's `converse` calls | `tests/test_m08_census.py::test_the_client_constants_are_read_off_the_source_the_client_defines`; `core/toolloop.py::_accumulate` | PR 1, done |
| 4 | Every 2-call turn under 6000, every 3-call turn over it | census `8_decision_rule.mandated_shape_tokens_in.by_calls` (2: max 3959; 3: min 6068) and `1_by_milestone` (3-call min 6022 across all 52) | PR 1, done |
| 5 | The modal turn went 2 → 3 when `entitlement-check` became a second sequential round at M06b; per-call 1693 → 2057 | census `5_attribution`, exact, for the two factors. The causal clause — *because* the second tool is sequential — is `mandated_calls()`'s reading of the case asserts, pinned by `test_the_mandated_call_count_follows_the_case_asserts`. The step is measured; the cause is design read off the code | PR 1, done, with that split stated |
| 6 | The per-call base is 1859–1974, of which committed text explains ≈1437; residual 422–537 | Bounded from seven 2-call turn totals; the *explained* half is an estimate at 3.368–3.389 chars/token from six single-call, no-tools anchors. **No PR in this plan measures it.** Per-call `inputTokens` are not in any committed file (`_accumulate` sums them), and a calibration call with tools offered is a model call. Question 3 |  none |
| 7 | No sample over the ceiling at its mandated count carries evidenced removable content | census `8_decision_rule` (33 of 33 uncovered; `gap_per_call_max` 78.3); `test_the_decision_rule_reads_per_sample` with a synthetic pair | PR 1, done — within the three evidence categories the rule admits, and no further |
| 8 | The pre-registered rule picked B | The record's `outcome`, and `cross_sample_reading_not_the_rule` holding the reading that printed A | PR 1, done. The rule's text was rewritten after its first reading and before any number; ADR-073 D2 says so |
| 9 | The number sits in [7170, 8180], below 8181, argued from the census and not from which cases pass | The derivation test for the band. The *not from which cases pass* half is measured only by ordering: `test_the_reader_offers_no_other_ceiling`, and the PR-3 body citing no count. A seat can also check the amendment cites no case id | PR 3 |
| 10 | Nothing else moved: no case, prompt, tool, topic or other assert | `--check`, `git diff` of M07, the three digest families — and one check the plan does not name: the PR-3 diff to `cases.yaml` is exactly 25 hunks, each `tokens_in: 6000` → the number, shown by `git diff -U0 -- services/highlights-agent/evals/golden/cases.yaml \| grep '^[-+] ' \| grep -vc tokens_in` printing 0 in the PR body | PR 3 and PR 4, each |
| 11 | The ceiling will still catch every 4- and 5-call turn, which are `catalog-search`'s browse gap | The PR-4 join (claim 1) measures the first half: fourteen samples on seven cases fail. The second half — that they *are* the browse gap — is an attribution nothing in this plan measures; Tool Owner, no ADR | PR 4 (first half); none (second) |
| 12 | The budget axis becomes discriminating again: passes the mandated shape, fails the runaway one (ADR-073 *Consequences*) | Overstated by the plan's own data. Nineteen answered samples ran **above their mandate** at three calls (six 2-mandate cases: `brand-021`, `entitlement-012`, `grounded-017/018/019`, `headroom-005/026`, `recommend-015`, `edge-025`; 6022–6792) and every one passes at any number in the band. The ceiling is uniform; the mandate is per case; the axis discriminates **call count ≥ 4**, not *more calls than the shape*. PR 4 can print this row; the sentence should say it | PR 4, with the consequence reworded in PR 3's amendment |
| 13 | The census's latency table: model time 2289 ms at two calls, 3606 at three; guardrail 770–1212 | census `6_latency`, exact | PR 1, done |
| 14 | Security's arm answer: no deployed arm can plant a model-authored tool name, so the probes credit nothing on every arm under ADR-041 | A reading of `handler.py`'s two arms and the loop test M07 PR 2 wrote. **No PR measures it**; it is a disposition, and it needs Security's key, not a run | PR 2 (question 4) |
| 15 | M08 makes claim 6's suite scorable on the tools arm | Only M09's first fresh run. Not in this plan; say so where the sentence stands | none |
| 16 | Zero model calls, no deploy, all milestone | `test_the_reader_imports_no_network_module`; `make check` hermetic; no new file under `milestones/M08/` carrying `usage`; the PR bodies. Asserted more than measured, and that is acceptable for a negative | every PR |

Three of sixteen have no measurement in the plan (6, 11's second half, 15).
Rows 6 and 11 are the same unknown from two sides: what a call carries that no
committed text shows, and why a model searches twice. Neither is the claim.
Row 2 is the one that must move before the number.

### 3. Does any PR move the ceiling before the census has said the context cannot be reduced?

**Yes. PR 3 does, and the census has not said that.** It said no sample over
the ceiling at its mandated count carries *evidenced* removable content, where
evidence is three enumerated categories: uncited replayed rows, text sent
twice, tools the manifest does not declare. Outcome B is *not-A on the
evidence admitted*, and the amendment that moves the ceiling has to say so in
those words.

**The residual is the size of the question, not a footnote to it.** 422–537
tokens per call is 22.7–27.2 % of the per-call base. On a 3-call turn that is
1266–1611 tokens per turn. The largest mandated-shape excess over 6000 is
**235** (`blackout-008`, 6235); the largest per-call gap the rule saw is 78.3.
If one fifth of the residual were content the agent sends and could stop
sending, every mandated-shape sample would sit under 6000 and the rule would
have printed A. The rule decided B on a question it could not see. That is
M06b's fourth finding again: the attributed population read as the whole.

The census cannot separate three explanations, and the amendment should list
them rather than pick one:

- **Estimation error.** The ≈1437 *explained* is chars ÷ 3.37, and the six
  anchors that gave 3.37 are near-identical prose-plus-catalog prompts
  (3.368–3.389, a band that covers only text of that kind). Tool specs and the
  answer schema are JSON; a JSON-heavy text tokenises denser, so *explained*
  is more likely an underestimate than the residual is a discovery. Removable
  by nobody.
- **Provider-side tool-use framing** — the `tool_use` and `tool_result`
  blocks and whatever the provider prepends when `toolConfig` is present.
  Design; removable by nobody the repo controls.
- **Content the agent sends that no committed text shows.** Removable, and
  the only explanation under which A was right.

Zero-call work can narrow this and the plan does not schedule it: M02's
one-tool per-call figure (1693, `loop-shape.json`) against stage 2's two-tool
figure (2057) is a differential across one added spec whose size is known
(≈282); a residual that grows with the spec points at the first two
explanations, one that does not points at the third. The measurement that
settles it is per-call `inputTokens` in the answer file plus one calibration
call with tools offered — the first is a `run_with_tools.py` / `_accumulate`
change constraint 5 forbids in M08, the second is a model call constraint 6
forbids. Both are legitimately M09 PR 1's, beside the fresh run M09 takes
anyway.

**Debt or exclusion?** Today it is an exclusion: SPEC/08 lists it under *What
it does not build* and gives it no row in *Obligations inherited*; ADR-073
lists it under *does not decide* as *"Recorded."* — no owner, no date. SPEC/08
*Bounded* says *"a discovered defect is recorded with a deadline and left
alone"*; this is a discovered unknown recorded without one, and CLAUDE.md's
rule that scope cuts are never silent simplifications is met in letter (it is
written) and not in the part that matters (nothing will come looking for it).
**It becomes a dated debt in PR 2**: owed to Platform Engineering (the loop's
shape) with AI Quality (the ceiling it may move), dated **M09 PR 1**, paid by
per-call usage in the answer file and one calibration call, with the
differential above run at zero cost in the same PR-2 diff if the operator
wants the narrowing now.

**Does it weaken the derivation?** Not the arithmetic. The band is a function
of exact turn totals — 6235 and 8181 — and no attribution enters it. What it
weakens is the *warrant* for moving at all, and that is repaired by one clause
in ADR-014 amendment 2, written before the number: *the ceiling is re-derived
for the shape as measured, a quarter of whose per-call base is unattributed;
if that residual is later attributed to content the agent sends and can stop
sending, the ceiling is re-derived by this same rule in the milestone that
removes it, downward, on the same keys.* A ceiling with its own re-derivation
trigger is a decision; the same ceiling without one is a number that will be
defended.

### 4. PR 3 carries five decisions on one seat round

**Yes, it is M07's PR-4 shape.** ADR-070 amendment 1 named it — *the stage-1
run, the probe suite, step 6b, the `ATK-003` disposition with two keys and an
ADR-062 amendment, and a new two-key rule; that is the PR that splits* — and
amendment 4 resolved it by moving the two zero-call, deadline-bound items to
the earlier PR, where their keys were already being collected. The same move
is available here, in the same direction.

The five, with the keys each actually needs under `pave/twokey.py`:

| item | files it touches | rule and seats | relation to the number |
|---|---|---|---|
| The `tokens_in` ceiling | `cases.yaml` (25 lines), `pave.manifest.yaml` `max_tokens_in`, `tests/test_budget_derivation.py`, ADR-014 amendment 2 | `services/*/evals/` (AI Quality); manifest (AI Quality, Tool Owner); derivation pin (AI Quality, Platform Engineering); no rule on `docs/adr/` | **is** the number |
| The suite `p95_ms` disposition | `pave.manifest.yaml` `gates.budgets.p95_ms` if moved; prose if not | manifest (AI Quality, Tool Owner) if moved; nothing if not | same file, different instrument, **no pinned rule** — `BANDS` covers `tokens_in` and `max_ms` only |
| Security's two `tool_request` probes | `quality/adversarial/` if written; prose if declined | Security alone, plus an ADR | none |
| `recommend-003`'s held text against `DEC-001` | none; a reading of the store through `read_withheld.py --show`, then prose | none; Security's seat | none |
| ADR-071 decision 4, Data Governance's answer | prose; any code change is a gateway change constraint 5 forbids until M09 | **no rule in `pave/twokey.py` names `data-governance`** — its key is an attestation line wherever it is written | none |

Three of the five touch nothing the ceiling touches and need no seat that PR 2
is not already collecting: PR 2 carries `pave/twokey.py` (AI Quality, Legal,
Platform Engineering, Security) and `tests/test_twokey_seats.py` (those plus
Tool Owner), so every enforced seat attests on PR 2 already, and Data
Governance's key is unenforced everywhere. **The probes' disposition, the
held-text reading, and decision 4's answer ride PR 2**, as three written
dispositions with their attestation lines and an ADR paragraph each — ADR-070
amendment 8 is already in that diff for the probes, ADR-071 amendment 1 for
decision 4. They do not ride PR 5: M07 dated its ADR index to PR 6 and it slid
to SPEC/08's PR, and the same close found the `labels.json` owe nobody had
listed. A debt dated to the close is a debt dated to the next milestone.

The `p95_ms` disposition is the one that should **not** be moved as it stands,
because it is not yet a disposition. SPEC/08 says *"a signed ceiling or a
standing finding"*, undecided. A signed ceiling needs a pinned rule to be
derived by, the way `tokens_in` has ADR-014's band, and none exists; deriving
a new rule and applying it in the PR that moves the number — with 5431 in view
— is the sequence constraint 1 exists to refuse for `tokens_in`, and it does
not become legitimate for latency because the file is already open. The M07
journal also recorded the latency direction as *"wrong twice, not explained"*;
a ceiling derived from an unexplained measurement is a number, not a
derivation. **Decide it now, in this amendment, as a standing finding for M08**
— the census's table is the evidence that 2500 is breached by the shape (model
time alone is 3606 ms at three calls) and not by a regression, the gate costs
no case, and the rule that derives a suite p95 is owed to M09 PR 1, written
before M09's fresh run and applied after it. Written that way it changes no
file on a rule, and rides PR 2 beside the other three. If the operator wants a
signed ceiling in M08 instead, it takes the spare sixth PR with its own rule
and its own round, and PR 3 stays the number.

**What PR 3 then is:** twenty-five identical line edits, one manifest value,
one test re-pointed, one ADR amendment — and one question for the seats: *is
this number produced by the rule from the record and by nothing else?* That
is what *"Seats review this PR and no other"* should be able to mean.

### What this amendment asks PR 2 to carry, beyond what SPEC/08 lists

1. The side-prediction restated: *cases that fail `budget` on `tokens_in`
   alone at M07 and pass every other assert, `tokens_out` included, on the
   ≤3-call majority*; the bound re-derived from the transcript at 6000 and
   the unchanged tiers; PR 4's checkbox reworded to match. SPEC/08 amendment 1,
   with the five case ids and the reason.
2. The residual as a dated debt row: Platform Engineering with AI Quality,
   M09 PR 1, per-call usage plus one calibration call; the M02-to-stage-2
   differential run in the same diff if wanted.
3. Security's two probes disposed, the held text read against `DEC-001`,
   Data Governance's answer on decision 4 — three written dispositions with
   attestation lines; ADR-070 amendment 8 and ADR-071 amendment 1.
4. The suite `p95_ms` disposition as a standing finding for M08 with the
   derivation rule owed to M09 PR 1; SPEC/08's PR-3 paragraph and obligations
   table re-dated accordingly.
5. The wording for ADR-014 amendment 2 pre-registered here so PR 3 cannot
   soften it: the *not-A on admitted evidence* sentence, the re-derivation
   trigger, and the *discriminates call count ≥ 4, not calls above mandate*
   statement, with the nineteen above-mandate samples named.

### What this amendment does not change

The claim. The band [7170, 8180] and the placement below 8181. The rule and
its outcome. Constraints 1–8. The cap. Outcome A stays where D2 put it.

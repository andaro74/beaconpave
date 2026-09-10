# M09 — the rule is disposed, and the service goes red for a reason a reader can trace

**Written before the branch is cut.** Owned by the PM seat. Branch `m09-rules`,
tag `m09`. M09 as inherited was two milestones; the guardrail half is **M09b**, a
row added in place between 09 and 10, and answer quality is **09c**. Nothing
below row 09 shifts (ADR-075 decisions 1 and 2).

**Deliberately short**, in SPEC/08b's shape. Every decision lives in ADR-075;
every "what broke" goes to the journal at close. This file states the milestone
and nothing else.

## Why

Claim 6 — *rules have owners and dispositions* — is the only claim in the twelve
whose proof artifact is a **diff**: *a rule delta disposed end-to-end into eval
cases*. `rules/MER-AI-0001.yaml` has sat `proposed` and undisposed since M00a on
purpose, and its own header says why: shipped enforced with a control that
already existed, the delta has already happened at commit one and the claim is
unprovable.

M08b finished the work that had to precede it. The arm is measured: a fresh k=3
run through the deployed gateway, per-call `inputTokens` and the call count in
every verdict, the answer-channel question read by a rule written before the run,
and the 7700 ceiling proven per sample on samples it was not derived from. That
is the pre-disposition baseline ADR-073 said the loop could not produce a
meaningful number without.

What M08b also handed over was too much for one cap. Four spend events, one
deploy, two seat rounds on two different controls, and thirteen dated items. **A
red after a disposition *and* a new guardrail line is unattributable between the
two controls** — and claim 6's whole content is that a reader can trace the red to
the rule. ADR-075 decision 1 splits them: **this milestone takes the disposition
and the control that needs no deploy; M09b takes the guardrail line and the topic
it recalibrates.**

## The one claim

**A rule delta disposed by its owning seat into an executable control makes the
deployed service fail a gate for a reason a reader can trace from the rule to the
failing assert; and the fix, made where the rule points, makes it pass, with
nothing else moving.** Measured through the deployed gateway at the guardrail
versions M08b read, at k=3, majority against majority — never on a stand-in and
never on a hand-built fixture.

This advances **claim 6** in the twelve-claims table, and it is the only claim
this milestone advances.

### The five falsifiers, pre-registered

Any one of them fails the claim and closes the milestone red with the case named.

| | falsifier | what it would mean |
|---|---|---|
| **F1** | any **positive** disclosure case **passes before the fix** | the delta was not a delta — the control was already satisfied, which is the rule file's own recorded hazard and the reason it shipped undisposed |
| **F2** | any positive disclosure case **fails after the fix** | the fix, made where the rule points, did not make it pass |
| **F3** | `pave.gate decide` does not exit **1** on the pre-fix verdict, or does not exit **0** on the post-fix one | a claim about a gate that is never run against the gate is prose |
| **F4** | the goldens control run shows a ≤3-call answered sample **over 7700** that was under it at M08b; **or a case that passed 3-of-3 at M08b fails by majority; or a case that failed 0-of-3 at M08b passes by majority** | the fix moved something else; the prompt is in every request of every run this milestone takes |
| **F5** | the **negative** case carries a disclosure after the fix | a fix that discloses on every answer passes the positive half against nothing (ADR-048 decision 3) |

**F1 is scoped to the positive half, and the scoping is a correction.** As first
written it read *any disclosure case passes before the fix*. The negative case
asserts the field is **not** disclosed, and the service already does not disclose
— every committed M08b sample carries `ai_disclosure: null` — so it passes run A
in **every possible world**. Unscoped, F1 would fire on it whatever the system
did and close the milestone red by construction, which is a falsifier that
measures nothing. The plan-walk table below already said the narrower thing
(*"every positive case fails before the fix"*); the three sites now agree
(ADR-075 amendment 2).

**F4 carries the direction falsifiers and no longer carries the count, and the
two were the wrong way round.** `N` is a sum over 25 cases and is insensitive to
compensating movement: three cases newly failing and three newly passing leaves
`N` exactly where it was, inside the band, with six cases having moved on a
prompt change. The per-case predicates detect that and are the ones this
repository has already learned to trust — at M08b the count moved 12 → 10 while
**no** direction falsifier fired, and the journal's own conclusion was that *"a
k=3 majority on a one-sample margin is not a stable instrument for a two-case
prediction."* A band the milestone has recorded as unstable was doing
claim-deciding work while two stable per-case predicates did side-prediction
work. **The count `N` in [8, 12] is a side-prediction in all three places** —
this table, *Beside the claim*, and PR 4b's Definition-of-done box — which is
what the other two already said (ADR-075 amendment 1 §5, ask 3).

**A red claim stops the claim's reading and nothing else.** The remaining PRs
proceed as planned: dropping them re-dates their debts to M09b's first PR, which
is the pile ADR-075 decision 1 exists to refuse. The close writes ❌ and names the
case.

### What the pack must contain, and why the negative half is not decoration

The pack carries cases where a disclosure **is** required by the rule and at
least one where it is **not** — a factual entitlement question carrying no
AI-authored editorial copy. Without it, a fix that emits a disclosure on every
answer passes the whole pack. The positive and negative halves are asserted in
one run, in both directions, which is ADR-048 decision 3's shape; and the pack
asserts its own sufficiency (at least one of each) so that it cannot go vacuous
silently, which is ADR-048 decision 4's.

The pack is **not** a graded suite and does not carry the 5–10% headroom rule:
it is a disposition witness, and a witness at 100% after the fix is the outcome,
not a defect. Recorded here rather than left for a seat to discover, because
CLAUDE.md's headroom rule is written for the goldens.

### The prompt delta, priced before it is spent

The fix changes `TOOL_SYSTEM` in `services/highlights-agent/gateway_client.py`,
which is in **every request of every run this milestone takes**. That is the one
way this milestone can break M08b's standing per-sample claim, and it is
measurable with no model call, because the prompt is committed.

*Every request of every **arm*** was the earlier wording and it was wrong:
`TOOL_SYSTEM` is the **tools** arm's prompt, the control arm sends `SYSTEM`
through `build_prompt`, and `test_the_control_arm_is_untouched_by_this_milestone`
holds. Nothing in M09 runs the control arm, so the sentence was harmless — but it
is what made the bound below look sufficient.

**PR 2 computes the added `tokens_in` cost from the committed prompt by the
census's own estimator and asserts, over M08b's answered ≤3-call samples:**

> `max(sample.tokens_in + delta × len(sample.calls)) ≤ 7700`

**The admissible delta is 306 tokens per call, not 918.** The bound this file
shipped — `6782 + delta < 7700`, published as *918 tokens of headroom* — compares
a per-sample total against a per-call delta. `usage.tokens_in` is the **sum
across calls** (checked: total equals the sum of `usage.calls[].tokens_in` in
**70 of 70** answered M08b samples), and 6782 is `headroom-005` sample 3 at
**three** calls; the system block is re-sent every round, so a delta of *d* lands
*n* times in an *n*-call sample. The shipped form admits **delta ≤ 917**, three
times what the claim survives. A 400-token disclosure sentence passes it and puts
`headroom-005` at **7982** — the F4 event the test exists to prevent before a
call is spent. That is a stated protection that is absent, which CLAUDE.md ranks
worse than a missing one (ADR-075 amendment 1 fact 2, ask 2).

Computed, both sides of the boundary: delta 300 → 7682 under; **306 → 7700, which
passes** because `evals/deterministic.py` compares `got > limit`; 307 → 7703
over; 400 → 7982 over. The bound is the **minimum over the population**, not over
the single largest sample — a two-call sample can bind tighter than a three-call
one.

The delta is measured over the **rendered** tool prompt —
`TOOL_SYSTEM.format(schema=answer.schema.json)` — because both of the fix's
model-facing sites are inside that string and `TOOL_SYSTEM_SHA256` pins only the
template, one level above where a schema edit lands.

A delta that does not fit is a finding about the fix **before a single call is
spent**, and the fix is rewritten; the ceiling does not move for it (constraint
1).

**What this measures, and what it does not.** It measures **budget** — whether
the fix breaches a ceiling — and it is not a content measurement. Nothing
hermetic can measure a prompt's effect on content. The hermetic content guard on
this fix is the line-by-line assert in `tests/test_gateway_run_parity.py`, which
**names** what the prompt gained and is the ADR-021 standard the M02 arm was
built on; the measured content guards are F4's two direction falsifiers, read at
PR 4b.

### The `p95_ms` rule's premise, disposed by a condition a test evaluates

M08b's finding: the mandated shape's own p95 went **3769 → 5241**, 41 ms over the
5200 ceiling derived from it, so the rule's premise — *the mandated shape's tail
is stable across runs* — is what failed, and the pooled reading isolates no
share. Re-deriving from the fresh population is the obvious move and it is the
one that must not be made blind: M08b published pooled **6633**, and a point
re-derived from 5241 lands above it, so the last published OVER reading would
become *within*. **A gate moved to clear a reading is the trade G9 refuses.**

The rule, written here and executed by PR 2's test (ADR-075 decision 5 §4):

> `p95_ms` moves only if the point ADR-014's unchanged rule derives from the most
> recent fresh mandated-shape population **still leaves the run that population
> came from OVER the gate**. PR 2's test reads M08b's answered mandated-shape
> samples through `context_census.mandated_calls()`, computes p95, floor `1.15×`,
> roof `1.60×`, the midpoint and the point rounded to the nearest 100, and
> evaluates the condition. If it holds, the manifest moves to that point and
> **every record digesting the manifest is re-produced in the same diff** —
> `milestones/M08/context-census.json` and `milestones/M08b/fresh-join.json` both
> carry `services/highlights-agent/pave.manifest.yaml` in `inputs_sha256`. If it
> does not hold, **`p95_ms` stays 5200**, ADR-014's stability sentence is
> withdrawn, the gate is re-described as a fixed ceiling with a recorded
> derivation, and the re-derivation is dated to the first milestone with a
> mandated-shape population not in view.

### The condition, executed: the gate does not move

Computed from the answer files through `context_census.mandated_calls()` and
`evals.deterministic.suite_latency` — the scorer's own percentile, so the test
and the gate cannot disagree about what a p95 is:

| population | n | p95 | floor 1.15× | roof 1.60× | midpoint | point |
|---|---|---|---|---|---|---|
| mandated shape (**the rule**) | 38 | **5241** | 6027.15 | 8385.60 | 7206.375 | **7200** |
| as-run ≤3 call | 58 | 5683 | 6535.45 | 9092.80 | 7814.125 | 7800 |
| pooled | 70 | **6633** | 7627.95 | 10612.80 | 9120.375 | 9100 |
| above mandate | 32 | 7223 | 8306.45 | 11556.80 | 9931.625 | 9900 |
| ≥4 call | 12 | 8437 | 9702.55 | 13499.20 | 11600.875 | 11600 |

n = 38 at 5241 and n = 70 at 6633 reproduce ADR-074 amendment 3 exactly, so the
population is the one M08b read. **The condition holds under none of the five.**

**So `gates.budgets.p95_ms` stays 5200**, ADR-014's stability sentence is
**withdrawn** (ADR-014 amendment 4), the gate is re-described there as a fixed
ceiling with a recorded derivation rather than a share-of-population instrument,
and the re-derivation is dated to **09c** — the first scheduled milestone that
both re-runs the goldens and does not read its own p95 against a number it just
chose. The manifest does not move, so **neither digesting record is
re-produced**, and constraint 1's conditional clause resolves to its stricter
branch.

**Which reading of *the run reads OVER*, because the sentence admits two.** It
means **the number the gate actually prints** — `suite_latency` over the whole
run, the pooled p95 in `suite latency OVER p95=6633ms over 5200ms`. Under that
reading the condition says something worth saying: the gate may move only if
`pooled > 1.375 × mandated`. Here 6633 against 7206.375, so it does not.

Under the *same-population* reading it is **unsatisfiable by construction**: the
point is the midpoint of `[1.15·p95, 1.60·p95]`, which is `1.375·p95`, strictly
above the p95 it came from — so the run that population came from can never read
OVER it, and a rule that cannot fire is not a rule. (Strictly: unconditional on
the **unrounded** midpoint; on the rounded point it holds for every p95 ≥ 134,
below which rounding to the nearest 100 can collapse it. Every latency this
repository has recorded is three orders of magnitude above that floor, so it
changes nothing here — but the property was asserted more broadly than it holds
and is corrected rather than left. PR 2's test sweeps both.)

**And the finding that is stronger than the outcome.** ADR-014 amendment 3
recorded the fact that made the last derivation survivable: *"The rule takes the
only population under which the run in view fails the gate."* **Here there is no
such population** — all five read *within*. The rule's own selection criterion
has no solution on this data, which is what a failed premise looks like when you
try to re-apply the rule that rested on it. It belongs in ADR-014 amendment 4
beside the withdrawal, and it is why the answer is *the gate does not move* rather
than *the gate has not moved yet*.

**No number in this section was approved in conversation.** The population is read
from the answer files, never from a journal sentence; a disagreement between the
test's number and any number quoted in prose is a finding about the prose.

### Beside the claim, and not it

Each is a finding about the side-prediction when it misses, never a failure of
the claim.

- **The goldens control count.** `N/25` with **8 ≤ N ≤ 12**, predicted **10** —
  M08b's measured 10, plus or minus the two cases M08b itself moved on a
  one-sample margin (`entitlement-002` at 307 and `entitlement-011` at 308
  against a tier of 300), which is the only movement this run has a reason to
  reproduce. Falsifier of the side-prediction: **N outside the band**, and that
  alone. The two direction predicates — a case that passed 3-of-3 at M08b failing
  by majority, a case that failed 0-of-3 passing by majority — **moved into F4**,
  where they decide the claim, because they are the stable instrument and the
  count is not (see the falsifier table). A miss on `N` is a finding about the
  band and does not fail the claim.
- **Refusals.** Refused by majority **0–2 of 25** on the goldens run (SPEC/01's
  band, at the ceiling M08b measured); falsifier 3 or more. On the disclosure
  pack, **0** — nothing about the guardrail moves here, and a refused disclosure
  question is a new topic false positive, recorded as a finding for Security and
  handed to M09b rather than diagnosed.

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| A rule that is a real delta — proposed, undisposed, with a control the service does not already satisfy | `rules/MER-AI-0001.yaml` as it stands since M00a: `status: proposed`, one `no-control` record, `review_by: 2026-10-01` | PR 4: F1 read from run A — every positive case fails before the fix. If any passes, the delta was not one and the milestone closes red |
| The rule bound to a service that can be deployed | **The scope moved in PR 2, and it moved because a measurement forced it.** MER-AI-0001 governed AI-generated *recaps*; `data/catalog.json` carries no outcome for any title and `grounded-017` requires the agent not to narrate one, so a recap-shaped case could only ever have failed for a reason that was not the control. Legal/S&P re-scoped the rule to the editorial copy the bound service actually authors, recorded as a `scope` record carrying `covers`, `excludes` and `revives` — the recap sense is excluded and **not retired**, with the three conditions that bring it back. `recap-agent` left the registry at ADR-048 and by ADR-023 can never be a caller | PR 2: the `scope` record, on `^rules/` = `(legal-sp, security)` with `requires_adr=True`; a test that no positive case asks for an outcome and that the catalog still carries none. PR 4: `status` and the control, and a test walking `disposition.controls[].ref` to a file that exists |
| A control that is executable and deterministic | `services/highlights-agent/evals/answer.schema.json` already carries `ai_disclosure`; the pack asserts **key presence and shape** on the positive cases and **key presence and null** on the negative one. The field is not in the schema's `required` and the answer object is `additionalProperties: false`, so an assert testing truthiness rather than presence is satisfied by a model that never emits the key at all. **No judge axis**, so the frozen instrument does not move (CLAUDE.md's deterministic-first rule) | PR 2: the asserts tested on planted answers each way, under `tests/`, including the never-emitted-key plant; `quality/judge/frozen.json` and every instrument digest unchanged across the milestone |
| A suite the gate reads, that is not the twenty-five | A `disclosure` suite: its own cases file, its own runner path (`run_with_tools.py --cases`), its own verdict record (`quality/verdicts/schema.json` types `suite` as a free string, so the gate costs nothing), its own history entry (`evals/history/schema.json`'s `suite` enum gains `disclosure`, three keys, and `pave/history.py`'s `SCHEMA_DIGEST` moves in the same diff). **No comparator pin** — see PR 4b | PR 2: `pave.gate decide` over a planted FAIL verdict with `suite: "disclosure"` exits 1; the enum plant is red; `pave gate history` accepts the shape and forces no `README_GOLDENS` row |
| The goldens denominator held at 25 | A test that counts the golden cases file and refuses any disclosure-prefixed id in it | PR 2: the plant — one disclosure case added to the golden file — is red **by name** |
| `disclosure-004`'s reservation resolved | **Four sites, not the two this file first named.** `evals/golden/README.md` **and `templates/agent-tools/evals/golden/README.md.tmpl`** — which every future service inherits, and which the scaffold's round-trip check couples byte for byte to the first — are rewritten to say where a disposed rule's pack lives. `evals/golden/cases.yaml`'s header and `answer.schema.json`'s `ai_disclosure` description are **dated to PR 4**: both are digested by `milestones/M08/context-census.json` and through it by `milestones/M08b/fresh-join.json`, and the second is model-facing. The id is **not reused** — the pack numbers from 101 | PR 2: a test that the README and its template are withdrawn together, that no case anywhere is `disclosure-004`, and that the two dated sites are named with their PR rather than left silent; PR 4: the remaining two, with the records they move |
| A traceable chain, not a claimed one | A reader that walks `rules/MER-AI-0001.yaml` → `disposition.controls[].ref` → the pack → the failing assert, with no step supplied by hand | PR 2 (the reader, tested on the committed rule and on a planted broken ref), PR 4 (run over the real record) |
| The run, on the real path | `run_with_tools.py --cases` at k=3 through the deployed gateway; the pre-flight before the first call | PR 4: run A and run B committed as-run under `milestones/M09/`; the pre-flight header names the deployed function, both guardrail versions and bundle digests equal to the tree at PR 2's merge |
| The gate actually run | `python -m pave.cli gate decide` over each run's verdict, its exit code and its rendered output captured | PR 4: exit **1** on run A, exit **0** on run B, both transcripts committed |
| The fix, where the rule points | One disclosure sentence in `TOOL_SYSTEM`, `services/highlights-agent/gateway_client.py` — caller-side, not in the deployed bundle, so no deploy and no bundle digest moves — **and `answer.schema.json`'s `ai_disclosure` description**, the stale-M07 site the model actually reads (*"Null until M07 disposes that rule"*, text telling the model to leave the field null) | PR 2: the file joins a `(platform-eng, security)` rule **before** the PR that edits it, and the prompt-delta test prices both sites; PR 4: the diff is the two model-facing sites, the pins and records they move, and nothing else |
| Proof the fix moved nothing else | The goldens arm re-run at k=3 after the fix, read by M08b's committed `fresh_join.py` at the same 7700 ceiling | **PR 4b**: F4 — no ≤3-call answered sample over 7700 that was under it at M08b, no 3-of-3 pass failing by majority, no 0-of-3 fail passing by majority; the entry, its `README_GOLDENS` row and the row's bold `N/25` **in the same PR**, because `pave/history.py::check_readme` refuses a goldens entry whose row is pinned to none. It is read in a PR that is about F4, and it cannot precede the fix, so this is a split forward rather than a re-ordering |
| Nothing else moved before the run | `git diff` of the guardrail, `platform/gateway/policy/`, `quality/adversarial/`, `data/catalog.json`, the tiers and every topic file between PR 1's merge and PR 4's branch point, **empty with no carve-out** — the DMA rename leaves the milestone, so the market vocabulary does not move and F4's comparator differs from M08b's run by the fix alone. The two model-facing sites move in PR 4 and **are** the fix | PR 4, in the PR body |

## Pre-registered, in ADR-075

- **D1** — two milestones; the disposition first, without a deploy; M09b in
  place. What Act 3 costs and why it stays in M09.
- **D2** — answer quality scheduled as `09c`, serving claim 2 defensively with
  its claim question left to its own spec; the two `M10`s separated by name.
- **D3** — MER-AI-0001 disposed against `highlights-agent` by a deterministic
  assert; the scope text on two keys and an ADR; the demo script corrected.
- **D4** — the disclosure pack is its own **suite**; the goldens denominator
  stays 25 and is pinned by name; `disclosure-004`'s reservation withdrawn by
  name and the id unused.
- **D5** — the claim and its five falsifiers; the prompt-delta test; the `p95_ms`
  condition; both bands; and the reading handed to M09b for what count reads the
  topic fix as having worked.
- **D6** — the order of the debts, the cap, **the spare named for the cold
  review**, and the one pre-authorised slide.
- **Amendment 1** — the cold read, taken at PR 1b. Ten facts run over committed
  code, eleven asks. All eleven land in **PR 2's diff**, and three findings of
  PR 2's own land beside them: F1 unscoped fires on the negative case in every
  world; the reservation is in **four** sites, the fourth being the scaffold
  template every future service inherits; and both remaining sites are digested
  by `milestones/M08/context-census.json` and through it by
  `milestones/M08b/fresh-join.json`, so PR 4's own Definition-of-done clause was
  unreachable as written.
- **Amendment 2** — PR 2's decision record, which `^rules/`'s `requires_adr` rule
  makes it owe in its own diff: *no immortal rules* built, *orphan rule* defined
  in one sense, and the dispositions of the above.

## Implementation constraints, binding

1. **No guardrail, policy, corpus, topic wording, catalog, tier or token ceiling
   moves in this milestone.** `tokens_in` stays 7700; `tokens_out` and `max_ms`
   and every tier stay where ADR-014 put them. **`data/catalog.json` does not move
   at all** — the DMA rename leaves the milestone (see *What it does not build*),
   so there is no carve-out anywhere in this file. `gates.budgets.p95_ms` **does
   not move**: PR 2 executed the condition and it holds under none of five
   populations, so the number stays 5200 and neither digesting record is
   re-produced.
2. **The only change to what the model sees is the fix**, in PR 4, after run A.
   It is **two sites, not one**: the disclosure sentence in `TOOL_SYSTEM`, and
   `answer.schema.json`'s `ai_disclosure` description — which is rendered into the
   prompt through `{schema}` and today reads *"Null until M07 disposes that
   rule"*, text instructing the model to leave the field null. Both are priced
   together by PR 2's prompt-delta test, which measures the **rendered** prompt.
   No deploy: both are caller-side and the bundle digests must equal the tree at
   PR 2's merge in both runs' pre-flights.
3. **The disclosure pack is authored before the disposition and never edited to
   make a run pass.** A case that is wrong is fixed in its own PR with the
   reasoning, reviewed by AI Quality (CLAUDE.md's eval discipline), and the run
   is re-taken whole.
4. **The DMA rename is not in this milestone at all** (withdrawn; ADR-075
   amendment 1 §6, amendment 2). A consistent rename **refuses M08b's own
   committed run** through `fresh_join.py --check` — recorded trajectories carry
   tool arguments the renamed contract rejects — so the three ways out are
   re-producing nine milestones of trajectory records, editing committed evidence,
   or sliding. The first is unpriced work with no cap slot; the second is
   forbidden by *committed as-run* and by CLAUDE.md's eval discipline. It also
   moves `services/highlights-agent/evals/golden/cases.yaml`, which *What must not
   happen* forbids, and collects five two-key rules this file never named. And it
   confounds F4: with the rename in, an F4 miss is attributable to the disclosure
   sentence or to the market vocabulary and to nothing in particular. **It
   re-dates to `09c`, re-scoped**: a rename of the market vocabulary is a change
   to the system under measurement, not a documentation tidy, and that sentence is
   what four slides were hiding. The slide is recorded as a **finding** in the
   close's journal, since this milestone pre-authorises only ADR-053's.
5. **Three runs, k=3, committed as-run, majority against majority.** SPEC/07
   constraint 9's INFRA rule, unchanged: a sample with an INFRA case is re-run
   whole, once, with the bad sample committed beside it as `*-infra.json` and
   passed to nothing; a second INFRA sample closes the milestone with what it
   has. No re-run selection, no case edit, no baseline reset.
6. **The pre-flight before the first call of each run**, as SPEC/07's Definition
   of done fixed it: the deployed function, both guardrail versions read from its
   configuration, the bundle digests equal to the tree. A run whose records name
   any other version is not a reading.
7. **Seats on PR 2 only, planned as two rounds** — the second on the first's
   fixes — before the PR opens, on M08b constraint 7's measurement: a round on
   nine items produces M08 PR 3's seventeen findings with the fixes in the same
   PR. The seats are told what to plant, not what to read: a disclosure assert
   that passes on `null`; a negative case whose absence assert is vacuous; a
   chain reader that supplies a step itself when the ref is broken; a p95 test
   whose population is the pooled one; a denominator test that counts rows
   instead of cases; a comparator pin that admits any suite name; **a prompt-delta
   test that compares a per-sample total against a per-call delta; and a
   comparator pin for a suite no lane reads** (the two the cold read named but did
   not run, ADR-075 amendment 1 ask 11). Attestations wherever `pave/twokey.py`
   demands them, on every PR — including the **decision record** `^rules/`'s
   `requires_adr` rule makes PR 2 owe in its own diff.
8. **Model calls in PR 4 and PR 4b only.** PR 4: run A and run B over the
   disclosure pack at k=3. PR 4b: the goldens control run at k=3 over 25 cases,
   plus headroom of one whole-sample re-run for an INFRA sample. **Ceiling 180
   turns across both**, all through the deployed gateway. PRs 1, 1b, 2 and 5 are
   zero. `make check` stays hermetic. **No probe run**: no guardrail, policy,
   corpus or scoring path moves, and the disclosure assert is read by no
   adversarial scorer.
9. **A discovered defect is recorded with a deadline and left alone**, unless it
   blocks the claim.
10. **The deletability audit is a standing step on every PR.** Every check the PR
    adds is deleted in turn, from a working copy backed up to a temp directory and
    **never restored with `git checkout`**, and the suite re-run; the PR body names
    each one and whether it went red. A silent check gets a test before merge, or
    the check comes out.
11. **Every PR's citations are held to `tests/test_cited_commits_resolve.py`
    before it merges** — a commit reachable only from a remote-tracking branch is
    unreachable, so a document cites only what `main` or a `cited-*` tag reaches
    (`close-milestone` step 7). A red on a later PR's run of the rule over an
    earlier PR's text is a finding about that earlier PR.

## What it builds

**PR 1 (this):** ADR-075; this spec; rows **09b** and **09c** in `README.md` with
their footnotes and row 09 rewritten to what this milestone builds; `BUILD.md`;
`SPEC/README.md`; the ADR index row, and ADR-026's row corrected to *four*
amendments; **ADR-026 amendment 4 and `labels.json`'s `re_deferred_to` moved to
`M09b` in this same diff** — the fourth counted re-deferral, moved in the diff
that creates the row rather than found by a later `make check`;
`docs/governance/demo-script.md`'s Act 3 corrected. Zero model calls, no code, no
rule, no case, no threshold, no deploy.

**PR 1b — the spare, named for the cold review.** A cold read of this spec by a
reader who did not write it, before PR 2 opens: run the checks this file names
rather than reading it, and answer in an amendment to ADR-075. Zero model calls,
no code, no deploy. **This is the sixth slot**; taking it spends the cap, and the
fallback in *Bounded* fires. PRs 2–5 keep their numbers whether or not it is
taken, so every reference in this file stays valid (M08b's precedent).

**PR 2 — the instrument before the run. Seats review this PR and no other, in
two rounds.** The disclosure suite: the pack authored with both halves and its
sufficiency assert, the runner path (`run_with_tools.py --cases`, default
unchanged), the scoring lane and the verdict, the history `suite` enum with
`pave/history.py`'s `SCHEMA_DIGEST` moved in the same diff. **No comparator
pin** — nothing reads one and there is no committed disclosure run to pin until
PR 4, so it re-dates to PR 4b and `pave/cli.py` gains no generic suite lane
(ADR-075 amendment 1 fact 8, ask 9). The goldens denominator pinned by name.
`disclosure-004`'s reservation withdrawn in `evals/golden/README.md` **and its
scaffold template, together** — the round-trip check couples them — with the two
digested sites named and dated to PR 4; the id refused everywhere. The chain
reader (`pave/rules.py`, with `pave/cli.py` carrying only the dispatch line) and
its pin. The corrected prompt-delta test. The `p95_ms` condition executed: it
holds under **none** of five populations, so the gate stays 5200 and neither
digesting record is re-produced. `rules/schema.json`: `source.effective` required
— *no immortal rules* — with ADR-053's own plant red by name. *Orphan rule*
**defined** in the schema's `description` and in the check's docstring, one
sense, with a plant per sense. `services/highlights-agent/gateway_client.py`,
`platform/gateway/core/classify.py`, the chain reader, and M09's own readers,
records and pins on `pave/twokey.py` rules, each with a `_blocked_for` plant, and
the seat-set pin moved in the same diff. **ADR-075 amendment 2**, the decision
record `^rules/`'s `requires_adr` rule makes this PR owe in its own diff, and
**ADR-014 amendment 4**, the stability sentence's withdrawal. Zero model calls.

**There is no PR 3.** Its slot is vacated: the DMA rename cannot land in this
milestone at all (constraint 4), and §3 of ADR-075 amendment 1 spends the slot on
PR 4b. The six are **PR 1, PR 1b, PR 2, PR 4, PR 4b, PR 5**, and PRs 4 and 5 keep
their numbers so every reference in this file stays valid.

**PR 4 — the disposition, the fix and the two disclosure runs.** The rule's scope
text and its disposition — `status: proposed → enforced`, the `no-control` record
replaced by the eval-pack control — on two keys citing ADR-075. Run A (the pack,
pre-fix) and `pave gate decide` at exit 1. **The fix, in two model-facing sites**:
the disclosure sentence in `TOOL_SYSTEM`, and `answer.schema.json`'s
`ai_disclosure` description, whose *"Null until M07"* text is the one stale site
the model reads. Run B (the pack, post-fix) and `pave gate decide` at exit 0. The
chain reader run over the real record. F1, F2, F3 and F5 read; the pack's refusal
reading.

**Two pins and FIVE records this PR moves, and the count has been wrong twice**
(ADR-075 amendment 1 fact 3, ask 4; amendment 2 §3; PR 2 seat round 1). Editing
`TOOL_SYSTEM` goes red on `TOOL_SYSTEM_SHA256` and on the line-by-line assert in
`tests/test_gateway_run_parity.py` — `(platform-eng, security)`, and its own
docstring calls updating it *an ADR-021 event: say so in the progression row*.

The two model-facing edits then re-produce **five** committed records, each on the
census rule's three keys:

| record | reached |
|---|---|
| `milestones/M08/context-census.json` | digests the cases file, the schema and the client directly |
| `milestones/M08/residual-differential.json` | the same input list |
| `milestones/M08/rescore-join.json` | digests the cases file directly |
| `milestones/M08b/residual-attribution.json` | digests the cases file directly |
| `milestones/M08b/fresh-join.json` | digests the cases file **and** the census record |

Amendment 1 named **one** of these; this file's own first correction named
**three**. Both were hand-written, one hop deep, in a document. **The set is
therefore computed, not listed**:
`tests/test_m09_goldens_denominator.py::test_the_records_the_fix_moves_are_derived_and_not_listed`
takes the transitive closure over every `inputs_sha256` in `milestones/`, and
`test_the_spec_names_every_record_the_cascade_moves` fails if this table and the
closure disagree. A sixth record lands on both the day it is written.

All five are re-produced in PR 4's diff and the prompt move is recorded in the
progression row.

**PR 4b — the goldens control run, in a PR that is about F4.** The goldens arm
re-run at k=3 after the fix, read by M08b's committed `fresh_join.py` at the same
7700 ceiling; **F4** read against all three of its clauses; its history entry, its
`README_GOLDENS` row and row 09's bold `N/25` **in this one diff**, because
`check_readme` refuses a goldens entry whose row is pinned to none. The count band
and both refusal readings as side-predictions. The disclosure comparator pin, if
it is taken, lands here — where committed disclosure runs exist for it to pin.
ADR-075 amended with the numbers in decision 5's sentences, citing only what
`main` or a tag reaches. Its keys are its own: `^evals/history/` at three seats
and `^milestones/.*/goldens-run*.json` at two, neither of which PR 4 needs
otherwise. It cannot precede the fix, so this is a split forward.

**PR 5 — close.** Journal; step 6b read from PR 4's evidence; **Act 3 recorded**
(`recordings.json` needs no edit — act 3's `owner_milestone` and `owed_by` are
both `M09` and `deferred_from` is empty, and recording it in this milestone keeps
it empty); the progression row's ✅; tag `m09`; the artifact recorded.

## What it does not build

The guardrail line MER-AI-0001 also disposes into, and any seat round on it
(M09b) · the `entitlement-circumvention` recalibration (M09b, riding that deploy;
ADR-075 decision 5 §5 pre-registers what reads it as having worked) · Security's
two round-one probes for the corpus (M09b) · the `brand_tone` widening, its judge
run and its re-freeze (M09b; ADR-026 amendment 4) · the dashboard panel of the
registry lookup (M09b — the `dashboards/` directory holds a README and nothing
else, and building this repository's first dashboard inside the milestone that
proves claim 6 is the overload ADR-075 decision 1 refuses) · a judge axis for
disclosure, and any move of `quality/judge/rubric-sports.md`'s existing
`disclosure_present` axis · a second brand, a `meridian-news` pack or a
`meridian-news` judge axis (surfaces, M10; ADR-046, ADR-047) · a fix for the
browse gap or any `tokens_out` tier move (**09c**) · a re-derivation of
`tokens_in` · a `p95_ms` number chosen from any pooled p95 or from any run in view
· **the DMA rename** (SPEC/06b A21), re-dated to `09c` and re-scoped as a change
to the system under measurement with its own ADR at Legal/S&P plus Data
Governance, because a consistent rename refuses M08b's own committed run and
confounds F4 (constraint 4) · a probe run · a judged entry · `recap-agent`
returning to the registry ·
**a case edited, a threshold moved, or a baseline reset to make any run pass.**

## Obligations inherited, each with a date

| debt | owed to | date |
|---|---|---|
| MER-AI-0001's target service and surface, *"the first thing SPEC/09 must answer"* (ADR-074 D4) | Legal/S&P | **PR 1** (ADR-075 D3), executed **PR 4** |
| ADR-053 *no immortal rules* — `source.effective` optional, so a rule can switch off its own clock | Legal/S&P + Security | **PR 2** |
| ADR-053 *no orphan rules* — owed since M07 with its term meaning two things | Legal/S&P + Security | **PR 2**; the one pre-authorised slide if the cap is reached (*Bounded*) |
| The `p95_ms` rule's premise failed — the mandated shape's own p95 went 3769 → 5241, 41 ms over a ceiling derived from it | Platform Engineering | **PR 2, discharged**: the condition was executed, holds under none of five populations, the gate stays 5200, and ADR-014 amendment 4 withdraws the stability sentence. The re-derivation dates to **09c** |
| The DMA rename (SPEC/06b A21), **fifth slide, a finding rather than a pre-authorised slide** — it refuses M08b's committed run through `fresh_join --check`, edits a golden case, collects five unnamed two-key rules, and confounds F4 | Legal/S&P + Data Governance | **`09c`**, re-scoped as a change to the system under measurement, with its own ADR. Recorded as a finding in the close's journal |
| **The registry cannot detect a rule disposed against a service that produces no instance of its subject.** `pave rules validate` checks a rule's fields and its control refs; nothing reads the rule's subject against what the bound service can actually produce. MER-AI-0001 sat disposed-in-plan against `highlights-agent` for a milestone before a case-writing exercise found that the catalog grounds no recap — the registry reported it valid throughout | Legal/S&P + AI Quality | **unscheduled, owned.** Legal/S&P owns what a rule's subject means; AI Quality owns whether a pack can express it. Recorded at M09 PR 2 |
| `platform/gateway/core/classify.py`, G5's router, on no `pave/twokey.py` rule | Data Governance | **PR 2, done**: `(data-governance, security)`, the first rule naming that seat — which forced `data-governance` onto the seat-set pin's own rule by mechanism, as `legal-sp` was forced at ADR-053 |
| `services/highlights-agent/gateway_client.py` — the system prompt every governed run sends — on no `pave/twokey.py` rule, while its five siblings are covered. Found reading for this spec; PR 4 edits it, so it joins a rule first | Platform Engineering + Security | **PR 2, done**: `^services/[^/]+/gateway_client\.py$` at `(platform-eng, security)`. The scaffold renders that file, so a scaffolded team's onboarding seat count moved 3 → 5 — the count is computed from `twokey.RULES` at print time, so it followed |
| The `brand_tone` widening, owed to M04 and re-deferred three times | AI Quality (+ Security, the `quality/judge/` rule) | **M09b**, moved in **PR 1** in the same diff as the row, counted as the **fourth** |
| `milestones/M08/context_census.py`'s `sys.path.insert` leaking a tool path into the session | Platform Engineering | **undated.** The trigger was *the next PR that opens the file — PR 2, if the p95 condition yields a move*, and the condition did not, so PR 2 opens it read-only and paying it would edit a file under `milestones/M08/` that nothing else in this milestone touches. Re-dated to the next PR that edits that file for a reason of its own |
| `milestones/M08b/fresh_join.py`'s render path raising `UnicodeEncodeError` on a cp1252 console (`--check` unaffected) | Platform Engineering | **PR 4b**, which opens the file to read the goldens control run |
| The stronger ADR-index predicate: a row naming its ADR's highest amendment is red on 10 of 12 amended ADRs; the weak predicate ships with a ≤10 ratchet | PM | **owned, ratcheted**; ADR-026's row is corrected in PR 1 and the ratchet does not move |
| The seven browse-gap cases; the `tokens_out` cases, widened from five to twelve | Tool Owner; AI Quality | **09c**, scheduled here for the first time (ADR-075 D2); read, not diagnosed |
| Security's two `tool_request` probes; the `enforcement-probing` trigger, fired twice | Security | **M09b** |
| Retention on the withheld store (ADR-071 amendment 1) | Data Governance | step-6b trigger, read at PR 5 |
| ADR-069 D5 cut 2, the paired diff's partition | the next two-arm run | unchanged; one arm runs here |
| `usage.tokens_in: 0` on refused answers | – | unchanged |
| 30 stale worktrees; 191 CRLF files against an LF index (no committed byte depends on it) | Platform Engineering | checkout hygiene |
| No budget is per model; the manifest's `p95_ms` takes AI Quality + Tool Owner while the rule deriving it takes AI Quality + Platform Engineering | AI Quality | standing observations |

## Bounded

- **Cap: six PRs. The spare was taken, so the cap is spent.** The six are
  **PR 1, PR 1b, PR 2, PR 4, PR 4b, PR 5** — there is no PR 3, its slot having
  been vacated by the DMA rename leaving the milestone and spent on PR 4b (§3 of
  ADR-075 amendment 1). PRs 4 and 5 keep their numbers, so every reference in
  this file stays valid. Reaching the cap again closes the milestone, red if
  necessary.
- **The fallback fired, and then was not needed.** Taking PR 1b spent the cap, so
  *Bounded*'s fallback armed by name: **ADR-053's *no orphan rules* half** would
  re-date to **M09b**. PR 2 built it anyway — the definition was ADR-shaped, and
  ADR-075 amendment 2 is a record PR 2 owed regardless under `^rules/`'s
  `requires_adr` rule, so the definition rode a document PR 2 had to write. **The
  fallback is therefore recorded as armed and unspent**, and *no immortal rules*
  never gave way. **Any other slide is a finding**, and the DMA rename's fifth is
  recorded as exactly that.
- **Seats on PR 2 only, two rounds.**
- **Model calls in PR 4 and PR 4b only, ceiling 180 turns across both.**
- A discovered defect is recorded with a deadline and left alone.

## Demo artifact

```bash
python -m pave.cli rules trace MER-AI-0001
python -m pave.cli gate decide milestones/M09/verdict-pre-fix.json  ; echo "exit $?"
python -m pave.cli gate decide milestones/M09/verdict-post-fix.json ; echo "exit $?"
```

Predicted, not yet measured — the shape the run must produce, with `D`, `P` and
`N` left as letters:

```
MER-AI-0001  AI-generated recaps must carry a visible disclosure
  source     regulation - Fictional State of Jefferson AI Disclosure Act, 2026
  owner      legal-sp        status enforced        review_by 2026-10-01
  control    eval_pack  services/highlights-agent/evals/disclosure/cases.yaml  L3
  binds      highlights-agent
  cases      D  (P require a disclosure, 1 requires its absence)

  [BLOCK] milestones/M09/verdict-pre-fix.json (disclosure L3): suite reported FAIL
exit 1
  [PASS] milestones/M09/verdict-post-fix.json (disclosure L3): suite reported PASS
exit 0
```

**The first command exists from PR 2** and prints the chain as far as the
registry actually goes. Today that is:

```
MER-AI-0001  AI-generated recaps must carry a visible disclosure
  source     regulation - Fictional State of Jefferson AI Disclosure Act, 2026 (demo artifact)
  owner      legal-sp        status proposed        review_by 2026-10-01
  control    no-control  none yet ...  <-- no enforcing control yet — the walk stops here

chain: NOT RESOLVED
```

exit **1**, and that is correct rather than a defect: the rule is undisposed
until PR 4, and a lookup reporting a resolved chain over the undisposed state
would be reporting success over the very thing this milestone exists to change.
The two verdict files do not exist until PR 4.

The goldens control run's line is `N/25` with 8 ≤ N ≤ 12 and 10 predicted — a
**side-prediction** — read at PR 4b by `python milestones/M08b/fresh_join.py
--check` over M09's answer files at the same ceiling.

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: the disposed rule makes the deployed service fail the gate, and the fix makes it pass, with nothing else moving | the two disclosure runs at k=3 through the deployed gateway; `pave gate decide` over each verdict, exit 1 then exit 0; the goldens control run against F4 | PR 4 |
| 1a | …traceable from the rule to the failing assert | the chain reader walks rule → `controls[].ref` → case → assert with no step supplied by hand; a planted broken ref is red | PR 2 (reader), PR 4 (over the real record) |
| 1b | …on the real path, at the deployment M08b read | the pre-flight header on both runs: deployed function, both guardrail versions, bundle digests equal to the tree at PR 2's merge; the audit record ids | PR 4 |
| 1c | …with nothing else moving | `git diff` over the guardrail, policy, corpus, **catalog**, tiers and topics between PR 1's merge and PR 4's branch point, **empty with no carve-out**; the two model-facing sites move only in PR 4 and **are** the fix | PR 4 |
| 2 | **F1** — no disclosure case passes before the fix | run A's per-case verdicts | PR 4 |
| 3 | **F2, F5** — every positive case passes and the negative carries no disclosure after the fix | run B's per-case verdicts | PR 4 |
| 4 | **F3** — the gate blocks then permits | the two `pave gate decide` transcripts and their exit codes, committed | PR 4 |
| 5 | **F4** — the 7700 per-sample claim survives the prompt delta, and no case moved in either direction | the goldens control run joined to `usage.calls`, read at the same ceiling by M08b's committed reader; the two per-case direction predicates against M08b's | PR 4b |
| 6 | The prompt delta fits the headroom **before** any call | a test over the committed **rendered** prompt by the census estimator: `max(tokens_in + delta × len(calls)) ≤ 7700` over M08b's answered ≤3-call samples — **delta ≤ 306**, not the 917 the per-sample form admitted | PR 2 |
| 7 | The goldens count in [8, 12] (**side-prediction**); refusals 0–2 on goldens and 0 on the pack | the score transcript; `evals.refusals --sidecar` | PR 4b (goldens), PR 4 (the pack) |
| 8 | The goldens denominator is 25 and the pack is not in it | a test counting the golden file's cases; a planted disclosure id in it is red **by name** | PR 2 |
| 9 | `disclosure-004`'s reservation withdrawn, the id unused | a test over the golden README **and its scaffold template, together**, plus the id refused everywhere; the two digested sites named with their PR | PR 2 (two sites), PR 4 (the two digested ones) |
| 10 | The gate reads a disclosure verdict and blocks | `pave gate decide` over a planted FAIL verdict with `suite: "disclosure"`, exit 1 | PR 2 |
| 11 | The disclosure entry is recordable | `pave gate history`; the `suite` enum plant; a planted entry forces no `README_GOLDENS` row | PR 2 (enum), PR 4 (entries). **The comparator pin is PR 4b's or nobody's** — nothing reads one today and no committed run exists to pin |
| 12 | The goldens entry, its `README_GOLDENS` row and the bold `N/25` in **one** PR | `pave gate history`, which runs `check_readme` | PR 4b |
| 13 | *No immortal rules* | `rules/schema.json` requires `source.effective`; ADR-053's own plant is red by name | PR 2 |
| 14 | *No orphan rules*, one sense | the definition in the schema and the check's docstring; a plant per sense | PR 2 |
| 15 | The `p95_ms` condition evaluated and the manifest at what it yields | the derivation test: population, p95, floor, roof, midpoint, point, the condition's outcome; every constant planted red; both digesting records re-produced if it moves | PR 2 |
| 16 | `gateway_client.py` and `classify.py` on two-key rules | a `_blocked_for` plant per rule | PR 2 |
| 17 | ~~The DMA rename~~ — **cut from this milestone**, re-dated to `09c` and re-scoped, because a consistent rename refuses M08b's committed run and confounds F4 | measured in `09c`, against a baseline taken after it | — |
| 18 | `brand_tone` re-deferred to M09b in the same diff as the row, counted as the fourth | `tests/test_calibration_owe.py` green with row 09b present; the `deferred_from` arithmetic in ADR-026 amendment 4 | **PR 1** |
| 19 | Act 3 recorded before the row is flipped | `tests/test_demo_recordings.py` green with `recorded` set and `deferred_from` still empty | PR 5 |
| 20 | Zero model calls outside PR 4 and PR 4b; the two within 180 turns | the PR bodies; no file under `milestones/M09/` carrying `usage` outside those two — PR 2's planted answers live under `tests/` for that reason | every PR |
| 21 | Citations resolve from `main` or a tag | `tests/test_cited_commits_resolve.py` run over each PR's text before it merges | every PR |
| 22 | The deletability audit | the PR body names every check added and whether it went red when deleted | every PR |

Every row names the PR whose measurement proves it, on the real path. **Three
claims were cut for having no measurement** and are recorded in ADR-075 rather
than carried: the *dashboard panel* half of the registry lookup (the lookup is
kept and measured at row 1a; the panel is M09b's), the phrase *the regdelta loop*
(it names no artifact; everything measurable in it is rows 1 and 1a), and *a seat
round on the guardrail* (M09 moves no guardrail).

## Definition of done

- [ ] **PR 1:** ADR-075 merged with rows `09b` and `09c` in `README.md`, row 09
      rewritten, `BUILD.md`, `SPEC/README.md` and the ADR index row in one diff;
      ADR-026 amendment 4 and `labels.json`'s `re_deferred_to: "M09b"` in the
      **same** diff as the row, on two keys (AI Quality, Security); ADR-026's
      index row corrected to four amendments with the ≤10 ratchet unmoved;
      `docs/governance/demo-script.md`'s Act 3 corrected; `make check` green with
      the new rows; **nothing below row 09 renumbered and none of the seven `M10`
      code and template sites touched.**
- [ ] **PR 1b** (taken): the cold read committed as ADR-075 amendment 1; zero
      model calls; the cap spent and the fallback armed by name. **Its eleven asks
      land in PR 2's diff**, on this box's own precedent — a Definition of done
      corrected after its PR prints is a checkbox rewritten to match the
      outcome.
- [ ] **PR 2:** the disclosure suite built — pack, sufficiency assert, runner
      path, lane, verdict, `suite` enum with `SCHEMA_DIGEST` moved beside it — and
      the gate proved to block on it; **no comparator pin**, with the reason
      recorded; the goldens denominator pinned by name; the reservation withdrawn
      in `evals/golden/README.md` **and its scaffold template in the same diff**,
      with the two digested sites named and dated to PR 4; the chain reader in
      `pave/rules.py` with `pave/cli.py` holding only the dispatch line; the
      prompt-delta test green at **`max(tokens_in + delta × len(calls)) ≤ 7700`,
      delta ≤ 306**; the `p95_ms` condition executed and found to hold under
      **none** of five populations, so the gate stays 5200 and **neither
      digesting record is re-produced**; `rules/schema.json` requiring
      `source.effective` with ADR-053's plant red by name; *orphan rule* defined
      in one sense and checked, with a plant per sense; `gateway_client.py`,
      `classify.py`, the chain reader and M09's readers on rules with their
      `_blocked_for` plants and the seat-set pin moved beside them; **ADR-075
      amendment 2 and ADR-014 amendment 4 in this diff**, the decision record
      `^rules/` demands; two seat rounds' findings in the PR body; attestations
      per `pave/twokey.py`; **the deletability audit in the PR body, every new
      check named with its result.**
- [ ] **PR 4:** the pre-flight printed before the first call of each run; run A,
      the fix and run B committed as-run under `milestones/M09/`; both `pave gate
      decide` transcripts with their exit codes; the rule disposed on two keys
      citing ADR-075; **F1, F2, F3 and F5** read, and the pack's refusal reading;
      the chain reader run over the real record; **`TOOL_SYSTEM_SHA256`, the
      line-by-line parity assert, `milestones/M08/context-census.json`,
      `milestones/M08/residual-differential.json` and
      `milestones/M08b/fresh-join.json` all named, moved and attested in this
      diff**, with the prompt move recorded in the progression row as the ADR-021
      event the pin's docstring calls it; the disclosure entries; **the
      deletability audit.**
- [ ] **PR 4b:** the goldens control run committed as-run; **F4 read against all
      three of its clauses**; the goldens entry with `README_GOLDENS` and row 09's
      bold `N/25` **in this one diff**; the count band and the goldens refusal
      reading (**side-predictions** — a miss is a finding about the
      side-prediction and does not fail PR 4's box); ADR-075 amended with decision
      5's numbers, citing only commits `main` or a tag reaches; **the deletability
      audit.**
- [ ] **PR 5:** `close-milestone` in order; the journal, **recording the DMA
      rename's fifth slide as a finding and the `no orphan rules` fallback as
      armed and unspent**; step 6b read from PR 4's evidence; **Act 3 recorded,
      `deferred_from` still empty**; the progression row's ✅ and its goldens cell;
      tag `m09` (branch `m09-rules`, never the same name); the artifact recorded.
- [ ] Nothing under `milestones/M07/` changed. **Nothing under `milestones/M08/`
      or `milestones/M08b/` changed before PR 4; in PR 4, exactly the five records
      the cascade reaches are re-produced — `milestones/M08/context-census.json`,
      `milestones/M08/rescore-join.json`,
      `milestones/M08/residual-differential.json`,
      `milestones/M08b/residual-attribution.json` and
      `milestones/M08b/fresh-join.json` — and nothing else under those directories
      moves.** The set is the one
      `test_the_records_the_fix_moves_are_derived_and_not_listed` computes, and
      `test_the_spec_names_every_record_the_cascade_moves` refuses this clause if
      the two disagree. The `p95_ms` condition did not fire, so no record moves for
      the manifest. *(This clause has been wrong twice. As first written it forbade
      any change under `milestones/M08b/` outright — unreachable whatever PR 4
      does. Its first correction named three records and was short by two, in the
      diff written to fix exactly that defect. Both errors were hand-listed
      consequences of a digest graph, which is why the third version computes them.
      ADR-075 amendment 1 §2 found four clauses of this shape; this is the fifth,
      and it is the one that decides whether PR 4 can merge.)*
- [ ] No case, tier, token ceiling, guardrail, policy, corpus, catalog or topic
      moved at any point; **every instrument digest, the judge's included, is what
      PR 1 left it** — the DMA rename leaves the milestone, so nothing is
      re-frozen.

## What must not happen

No guardrail line, no topic wording, no probe, no corpus row, no deploy. No
second brand and no judge axis wired for disclosure. No disclosure case added to
the twenty-five, and no `N/26` published anywhere. No case edited, no threshold
moved, no baseline reset, and no golden case edited to make a run pass. No
`p95_ms` number derived from a pooled p95 or from a population under which the
run it came from would read *within* — the gate does not move to clear a reading,
and on this data **no population meets the rule's own selection criterion at
all**. No re-derivation of `tokens_in`; if the prompt delta does not fit the
**306-token** headroom, the **fix** is rewritten. No re-run selection and no
sample read at any ceiling but 7700. No history entry edited and none rewritten.
**No DMA rename anywhere in this milestone.** No re-seating of the prompt-delta
test's pre-fix baseline in the PR that moves the prompt — that erases the
measurement. **And no claim rewritten to match the outcome:** if a positive
disclosure case passes before the fix, or fails after it, or the negative case
discloses, or the gate does not block, or a case moves direction on the goldens
control run, the claim failed, the case is named, and the milestone closes red.

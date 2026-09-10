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
| **F1** | any disclosure case **passes before the fix** | the delta was not a delta — the control was already satisfied, which is the rule file's own recorded hazard and the reason it shipped undisposed |
| **F2** | any positive disclosure case **fails after the fix** | the fix, made where the rule points, did not make it pass |
| **F3** | `pave.gate decide` does not exit **1** on the pre-fix verdict, or does not exit **0** on the post-fix one | a claim about a gate that is never run against the gate is prose |
| **F4** | the goldens control run shows a ≤3-call answered sample **over 7700** that was under it at M08b, **or a case that passed 3-of-3 at M08b fails by majority, or a case that failed 0-of-3 at M08b passes by majority** | the fix moved something else; the prompt is in every request of every governed run this milestone takes |
| **F5** | the **negative** case carries a disclosure after the fix | a fix that discloses on every answer passes the positive half against nothing (ADR-048 decision 3) |

**A red claim stops the claim's reading and nothing else.** The remaining PRs
proceed as planned: dropping them re-dates their debts to M09b's first PR, which
is the pile ADR-075 decision 1 exists to refuse. The close writes ❌ and names the
case.

**What F4 guards, corrected before PR 2 (ADR-075 amendment 1 §5).** As first
written F4 read *a ≤3-call sample over 7700, or the count outside [8, 12]*, and the
count appeared a second time below as a **side-prediction** whose miss is a finding
and not a failure — two answers in this file about the sentence that decides a red
close. The count is the half that gives way, and the reason is measured rather than
argued: `N` is a sum over twenty-five cases and is insensitive to compensating
movement, so three cases newly failing and three newly passing leaves it where it
was with six cases moved on a prompt change. At M08b the count moved **12 → 10
while no direction falsifier fired**, and that journal's own conclusion was that a
k=3 majority on a one-sample margin is not a stable instrument for a two-case
prediction. **So the two per-case direction predicates move into F4, and `N` in
[8, 12] is a side-prediction in every place this file names it.**

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
which is in **every request of every governed run this milestone takes** — run A,
run B and the goldens control run are all `run_with_tools.py`. That is the one way
this milestone can break M08b's standing per-sample claim, and it is measurable
with no model call, because the prompt is committed.

**Not *every arm*, which is what this said first (ADR-075 amendment 1 §5).**
`TOOL_SYSTEM` is the **tools** arm's prompt; the control arm sends `SYSTEM` through
`build_prompt` and the baseline a byte-identical copy, and
`test_the_control_arm_is_untouched_by_this_milestone` holds across the fix. Nothing
in M09 runs the control arm, so the sentence was harmless and the phrase was not:
*every arm* is what made a single-delta assert look sufficient. The variant that
would make it literally true — putting the requirement in `answer.schema.json`'s
`ai_disclosure` description, which **both** prompts render through `{schema}` — is
named and refused here: it lands on one key (`^services/[^/]+/evals/`, AI Quality
alone) and would move the control arm's prompt for the first time since M01.

**PR 2 computes the added `tokens_in` cost of the prompt delta from the committed
prompt by the census's own estimator and asserts that no M08b answered ≤3-call
sample would breach the ceiling once the delta is charged to every call it makes:**

> `max(sample.tokens_in + delta × len(sample.usage.calls)) ≤ 7700` over M08b's
> answered samples at three calls or fewer, read from the answer files, with
> `evals/deterministic.py`'s own comparison — `got > limit`, so a sample landing
> exactly on 7700 passes.

A delta that does not fit is a finding about the fix **before a single call is
spent**, and the fix is rewritten; the ceiling does not move for it (constraint 1).

**The form is per-sample, and the reason is arithmetic (ADR-075 amendment 1 §5).**
As first written this section asserted `6782 + delta < 7700` and named **918
tokens** of headroom. `usage.tokens_in` is the **sum across a sample's calls** —
checked, 70 of 70 answered M08b samples — and the published ≤3-call maximum 6782 is
`headroom-005` sample 3 at **three** calls. The system block is re-sent every
round, so a delta of *d* tokens lands *d × n* times in an *n*-call sample. The
old assert admitted **delta ≤ 917** where the claim survives **delta ≤ 306**: a
400-token disclosure sentence passed it and put `headroom-005` at **7982**,
falsifying F4 on the run the test exists to protect. **A stated protection that is
absent is worse than a missing one** — it stops anyone looking for the real one —
so the number 918 is withdrawn from this file and the population replaces the
sentence about it.

**And this test measures budget, not content.** It says the fix fits the ceiling;
it says nothing about what the fix does to an answer, and nothing hermetic can.
The content guards are F4's two direction predicates, read at PR 4b, and — at zero
cost and before any call — the line-by-line assert in
`tests/test_gateway_run_parity.py`, which **names** what the prompt gained and
holds it to ADR-021's standard: no tool-use coaching, no worked example, no case
vocabulary. That assert goes red when the fix lands (constraint 12), and updating
it is where PR 4 states what changed.

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

**No number is written in this file and none is approved in conversation.** The
population is read from the answer files, never from a journal sentence; a
disagreement between the test's number and any number quoted in prose is a
finding about the prose.

#### The condition, executed at PR 1b: it holds under no population

The rule above is unchanged and is what PR 2's test executes. What is added is its
**outcome**, computed at PR 1b from the committed answer files through
`context_census.mandated_calls()` and `evals.deterministic.suite_latency` — the
scorer's own percentile, so the test and the gate cannot disagree about what a p95
is (ADR-075 amendment 1 §4). It is carried here on ADR-074 amendment 1 §4's
precedent, which put the populations and the number in the spec rather than leaving
them in an ADR.

| population | n | p95 | floor 1.15× | roof 1.60× | midpoint | point |
|---|---|---|---|---|---|---|
| mandated shape (**the rule**) | 38 | **5241** | 6027.15 | 8385.60 | 7206.375 | **7200** |
| as-run ≤3 call | 58 | 5683 | 6535.45 | 9092.80 | 7814.125 | 7800 |
| pooled | 70 | **6633** | 7627.95 | 10612.80 | 9120.375 | 9100 |
| above mandate | 32 | 7223 | 8306.45 | 11556.80 | 9931.625 | 9900 |
| ≥4 call | 12 | 8437 | 9702.55 | 13499.20 | 11600.875 | 11600 |

n = 38 at 5241 and n = 70 at 6633 reproduce ADR-074 amendment 3 exactly, so the
population is the one M08b read. **The condition holds under none of the five.**

**So: `gates.budgets.p95_ms` stays 5200, and it does not move in PR 2 or anywhere
in this milestone.** ADR-014's stability sentence is withdrawn in an ADR-014
amendment on that file's two keys; the gate is re-described as a fixed ceiling with
a recorded derivation rather than as a share-of-population instrument; and the
re-derivation is dated to **09c**, the first scheduled milestone that re-runs the
goldens and does not read its own p95 against a number it has just chosen.

**Which reading of *the run reads OVER* the condition means, stated because it
decides the reason and not the answer.** Under the *same-population* reading the
condition is **unsatisfiable by construction**: the point is the midpoint of
`[1.15·p95, 1.60·p95]`, which is `1.375·p95` rounded and strictly above the p95 it
came from, so that run can never read OVER the point derived from it. The condition
is meaningful only under the *printed* reading — the number the gate actually
emits, `suite_latency` over the whole run, which is the **pooled** p95 in
`suite latency OVER p95=6633ms over 5200ms`. Under that reading it says something
worth saying: the gate may move only if `pooled > 1.375 × mandated`. Here 6633
against 7206.375, so it does not. **This file means the printed reading.**

**And the finding is larger than the outcome.** At M07 the rule took *"the only
population under which the run in view fails the gate"*, and that was the fact that
made an in-view derivation survivable. **Here no population does that** — the
rule's own selection criterion has no solution on this data, which is what a failed
premise looks like when the rule that rested on it is re-applied. That belongs in
the ADR-014 amendment beside the withdrawal, not in a journal.

Two consequences this file must carry rather than leave to a later `make check`:

- **PR 2 re-produces neither `milestones/M08/context-census.json` nor
  `milestones/M08b/fresh-join.json`**, because the manifest does not move. The
  Definition of done's conditional clause resolves to its stricter branch, which is
  what makes constraint 12's two record movements breaches rather than permitted
  ones.
- **`tests/test_budget_derivation.py::test_the_suite_p95_ceiling_is_the_number_the_rule_produces_from_the_mandated_shape`
  is not replaced.** It asserts 5200 from M07's population and
  `gates.p95_ms == produced`, and it stays green. PR 2 adds the condition's test
  beside it, not in place of it.
- **`milestones/M08/context_census.py`'s `sys.path.insert` debt loses its date.**
  It was dated *"PR 2, if the p95 condition yields a move"*; the condition yields
  none, so it is re-dated to **09c** beside the p95 re-derivation, by name, rather
  than becoming undated.

### Beside the claim, and not it

Each is a finding about the side-prediction when it misses, never a failure of
the claim.

- **The goldens control count.** `N/25` with **8 ≤ N ≤ 12**, predicted **10** —
  M08b's measured 10, plus or minus the two cases M08b itself moved on a
  one-sample margin (`entitlement-002` at 307 and `entitlement-011` at 308
  against a tier of 300), which is the only movement this run has a reason to
  reproduce. **The only falsifier of this side-prediction is N outside the band**,
  and a miss is a finding about the band. The two per-case direction predicates
  that used to sit here are **F4's**, and a miss of either fails the claim: they
  are the statements that detect compensating movement, which a sum cannot.
- **Refusals.** Refused by majority **0–2 of 25** on the goldens run (SPEC/01's
  band, at the ceiling M08b measured); falsifier 3 or more. On the disclosure
  pack, **0** — nothing about the guardrail moves here, and a refused disclosure
  question is a new topic false positive, recorded as a finding for Security and
  handed to M09b rather than diagnosed.

## The plan, walked to the claim

| The claim needs | Provided by | Verified |
|---|---|---|
| A rule that is a real delta — proposed, undisposed, with a control the service does not already satisfy | `rules/MER-AI-0001.yaml` as it stands since M00a: `status: proposed`, one `no-control` record, `review_by: 2026-10-01` | PR 4: F1 read from run A — every positive case fails before the fix. If any passes, the delta was not one and the milestone closes red |
| The rule bound to a service that can be deployed | The scope text moves: `title` and `source.ref` bind the rule to Meridian Sports' AI-authored highlight copy, and the disposition names `highlights-agent`. `recap-agent` left the registry at ADR-048 and by ADR-023 can never be a caller | PR 4: `^rules/` is `(legal-sp, security)` with `requires_adr=True`, citing ADR-075 decision 3; a test walks the rule's `disposition.controls[].ref` to a file that exists |
| A control that is executable and deterministic | `services/highlights-agent/evals/answer.schema.json` already carries `ai_disclosure`; the pack asserts its **presence as a key** and shape on the positive cases and its absence on the negative one — presence, not truthiness, because the field is **not in `required`** and an answer that never emits it validates. The same file is rendered into the prompt through `TOOL_SYSTEM`'s `{schema}`, so its description — *"Null until M07 disposes that rule"* — is model-facing text telling the model to leave the field null, and it is a **third** stale-M07 site rewritten in PR 2 beside the other two (ADR-075 amendment 1 ask 10). **No judge axis**, so the frozen instrument does not move (CLAUDE.md's deterministic-first rule) | PR 2: the asserts tested on planted answers each way, under `tests/`; `quality/judge/frozen.json` and every instrument digest unchanged across the milestone |
| A suite the gate reads, that is not the twenty-five | A `disclosure` suite: its own cases file, its own verdict record (`quality/verdicts/schema.json` types `suite` as a free string, so the gate costs nothing), its own history entry (`evals/history/schema.json`'s `suite` enum gains `disclosure`, three keys) | PR 2: `pave.gate decide` over a planted FAIL verdict with `suite: "disclosure"` exits 1; the enum plant is red; `pave gate history` accepts the shape. **The comparator pin is not PR 2's**: `pave/cli.py` calls `_suite_pin` with two literals, `goldens` and `adversarial`, so no lane reads a disclosure pin, and a comparator is *what committed runs score today* — there are none until PR 4. The pin lands in **PR 4b** with the runs, and with the lane that reads it, or it does not land at all (ADR-075 amendment 1 ask 9) |
| The goldens denominator held at 25 | A test that counts the golden cases file and refuses any disclosure-prefixed id in it | PR 2: the plant — one disclosure case added to the golden file — is red **by name** |
| `disclosure-004`'s reservation resolved | The reservation sentence removed from `evals/golden/cases.yaml` and `evals/golden/README.md`, rewritten to say where the disclosure cases live; the id **not reused** in the pack | PR 2: a test that neither file carries the reservation sentence and that no case anywhere is `disclosure-004` |
| A traceable chain, not a claimed one | A reader that walks `rules/MER-AI-0001.yaml` → `disposition.controls[].ref` → the pack → the failing assert, with no step supplied by hand | PR 2 (the reader, tested on the committed rule and on a planted broken ref), PR 4 (run over the real record). **The reader goes on a two-key rule in the diff that creates it**: `pave.twokey.triggered` over PR 2's file list returns **no rule** for `pave/cli.py`, `pave/rules.py` or their pins, and the reader is what decides what *traceable* means (ADR-075 amendment 1 ask 8) |
| The run, on the real path | `run_with_tools.py` at k=3 through the deployed gateway; the pre-flight before the first call | PR 4: run A and run B committed as-run under `milestones/M09/`; the pre-flight header names the deployed function, both guardrail versions and bundle digests equal to the tree at PR 2's merge |
| The gate actually run | `python -m pave.cli gate decide` over each run's verdict, its exit code and its rendered output captured | PR 4: exit **1** on run A, exit **0** on run B, both transcripts committed |
| The fix, where the rule points | One disclosure sentence in `TOOL_SYSTEM`, `services/highlights-agent/gateway_client.py` — caller-side, not in the deployed bundle, so no deploy and no bundle digest moves | PR 2: the file joins a two-key rule **before** the PR that edits it; PR 4: the diff is the prompt and nothing else |
| Proof the fix moved nothing else | The goldens arm re-run at k=3 after the fix, read by M08b's committed `fresh_join.py` at the same 7700 ceiling | **PR 4b**: F4 — no ≤3-call answered sample over 7700 that was under it at M08b, no 3-of-3 pass failing by majority, no 0-of-3 fail passing by majority; N in [8, 12] as a side-prediction; the entry, its `README_GOLDENS` row and the row's bold `N/25` **in the same PR**, because `pave/history.py::check_readme` refuses a goldens entry whose row is pinned to none. **In its own PR, not PR 4's**: the A/B pair is one measurement and stays together, while F4's control run has no twin in this milestone and deserves the PR that is about it (ADR-075 amendment 1 §3) |
| Nothing else moved before the run | `git diff` of the guardrail, `platform/gateway/policy/`, `quality/adversarial/`, `data/catalog.json`, the tiers and every topic file between PR 1b's merge and PR 4's branch point, **empty with no carve-out** — the DMA rename is withdrawn (constraint 4), so nothing in that list moves at any point. The system prompt moves in PR 4 and **is** the fix; what the fix drags with it is constraint 12 | PR 4, in the PR body |

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
- **Amendment 1** — the cold read, taken at PR 1b, and the operator's disposition
  of its eleven asks. What it changed in this file: F4's contents and the count's
  status; the prompt-delta test's form; the `p95_ms` condition's executed outcome;
  PR 3 vacated and the DMA rename re-dated to `09c`; the goldens control run split
  to PR 4b; constraint 12; and the three claims it found with no measurement.

## Implementation constraints, binding

1. **No guardrail, policy, corpus, topic wording, catalog, tier or token ceiling
   moves in this milestone.** `tokens_in` stays 7700; `tokens_out` and `max_ms`
   and every tier stay where ADR-014 put them. **`data/catalog.json` does not move
   at all** — the DMA rename is withdrawn from this milestone (constraint 4).
   **`gates.budgets.p95_ms` stays 5200 and moves in no PR**: the condition was
   executed at PR 1b and holds under no population, so PR 2 evaluates it, records
   the outcome and moves nothing.
2. **The only change to what the model sees is the fix**, and it is one sentence
   in `TOOL_SYSTEM`, in PR 4, after run A, sized by the prompt-delta test's
   per-sample bound. No deploy: the prompt is caller-side and the bundle digests
   must equal the tree at PR 2's merge in every run's pre-flight. What the fix
   moves besides the prompt is constraint 12, and it is not optional.
3. **The disclosure pack is authored before the disposition and never edited to
   make a run pass.** A case that is wrong is fixed in its own PR with the
   reasoning, reviewed by AI Quality (CLAUDE.md's eval discipline), and the run
   is re-taken whole.
4. **The DMA rename is withdrawn from this milestone and PR 3 is vacated**
   (ADR-075 amendment 1 §6, the operator's disposition). It cannot land here, and
   the reason is measured rather than argued: a consistent rename — the enum in
   `tools/entitlement-check/schema.in.json`, the generated
   `platform/gateway/policy/tools.contracts.json`, `data/catalog.json` and the
   `viewer.dma` values the golden cases send — makes
   **`milestones/M08b/fresh_join.py --check` refuse M08b's own committed run**
   (*"edge-024 sample 1: trajectory step 2 carries args entitlement-check's
   contract refuses"*), because recorded trajectories carry market names the
   renamed contract rejects. The three ways out are re-producing the trajectory
   records of nine milestones, editing committed evidence, and sliding; the first
   is unpriced work with no cap slot behind it and the second is forbidden in as
   many words. It also moves the golden cases file, which *What must not happen*
   forbids, and collects five two-key rules this file does not name — including
   `quality/adversarial/tool-plane-probes.yaml` at Security alone with
   `requires_adr`, in a milestone whose constraint 1 says no corpus moves. And it
   confounds F4's comparison to M08b, which is the reason it should not precede
   the run even if it could. **Re-dated to `09c` by name, with its own ADR at
   Legal/S&P plus Data Governance, re-scoped as a change to the system under
   measurement rather than a documentation tidy** — which is what four earlier
   slides were hiding. This is A21's fifth slide and the milestone pre-authorises
   only ADR-053's, so it is **recorded as a finding in the close's journal**.
   `brand_tone`'s re-freeze is **M09b's** and rides nothing here.
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
   PR. **PR 2 as scoped collects all five enforced seats**, checked by running
   `pave.twokey.triggered` over its file list: thirteen rules, and `^rules/` among
   them with `requires_adr`. The seats are told what to plant, not what to read: a
   disclosure assert that passes on `null`; a negative case whose absence assert is
   vacuous — the field is not `required`, so a model that never emits the key
   satisfies it; a chain reader that supplies a step itself when the ref is broken;
   a p95 test whose population is the pooled one; a denominator test that counts
   rows instead of cases; a comparator pin that admits any suite name; **a
   prompt-delta test that compares a per-sample total against a per-call delta**;
   and **a comparator pin for a suite no lane reads**. The last two are the plants
   the PR 1b reading did not run and could not: they are the two defects it found
   by other means, and a round that reproduces them from the code is worth more
   than this file's word for them. Attestations wherever `pave/twokey.py` demands
   them, on every PR.
8. **Model calls in PR 4 and PR 4b only.** PR 4: run A and run B over the
   disclosure pack at k=3. PR 4b: the goldens control run at k=3 over 25 cases,
   plus headroom of one whole-sample re-run for an INFRA sample. **Ceiling 180
   turns across the two**, all through the deployed gateway and all on the tools
   arm. PRs 1, 1b, 2 and 5 are zero; there is no PR 3. `make check` stays
   hermetic. **No probe run**: no guardrail, policy, corpus or scoring path moves,
   and the disclosure assert is read by no adversarial scorer.
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
    earlier PR's text is a finding about that earlier PR. **A PR's own commits are
    named by their role and never by sha**, because a squash merge destroys them
    (ADR-074 amendment 3 §9); where a sha must be named, the merge commit on `main`
    is preferred to a tag, and a tag is the rescue when no merge commit exists yet.
12. **What the fix moves besides the prompt, named before PR 4 opens.** Measured
    at PR 1b by planting one disclosure sentence into `TOOL_SYSTEM`: it goes red on
    `tests/test_gateway_run_parity.py::test_the_m02_prompt_is_hash_pinned`
    (`TOOL_SYSTEM_SHA256`), on
    `test_the_m02_prompt_is_the_control_prompt_minus_the_catalog_and_nothing_else`
    (the line-by-line assert whose `only_tool` multiset must equal the one forced
    line), and on
    `tests/test_m08_census.py::test_the_record_is_what_the_committed_inputs_produce`,
    because `milestones/M08/context-census.json` digests
    `services/highlights-agent/gateway_client.py`. **PR 4 names all three in its
    diff**, collects `(platform-eng, security)` for the parity file and the census
    rule's three keys for the record, and **records the prompt move in the
    progression row as the ADR-021 event the pin's own docstring calls it**. None
    can move to an earlier PR: a pin cannot be updated before the thing it pins
    moves.

## What it builds

**PR 1 (this):** ADR-075; this spec; rows **09b** and **09c** in `README.md` with
their footnotes and row 09 rewritten to what this milestone builds; `BUILD.md`;
`SPEC/README.md`; the ADR index row, and ADR-026's row corrected to *four*
amendments; **ADR-026 amendment 4 and `labels.json`'s `re_deferred_to` moved to
`M09b` in this same diff** — the fourth counted re-deferral, moved in the diff
that creates the row rather than found by a later `make check`;
`docs/governance/demo-script.md`'s Act 3 corrected. Zero model calls, no code, no
rule, no case, no threshold, no deploy.

**PR 1b — the spare, taken.** A cold read of this spec by a reader who did not
write it, before PR 2 opens: run the checks this file names rather than reading
it, and answer in an amendment to ADR-075. Zero model calls, no code, no deploy.
**This is the sixth slot**; taking it spent the cap and the fallback in *Bounded*
fired. It is ADR-075 amendment 1, and the operator accepted all eleven of its asks;
**the corrections it names land in its own diff, which is this file's, before PR 2
cuts** — the Definition-of-done box below says so, and a Definition of done
corrected after its PR prints is a checkbox rewritten to match the outcome
(ADR-074 amendment 1 §1). PRs 2, 4 and 5 keep their numbers whatever else moves, so
every reference in this file stays valid (M08b's precedent).

What the slot bought, and why it is worth its own line: the `p95_ms` condition
executed and found to hold under **no** population; the prompt-delta assert wrong
by the call count; three committed checks the fix goes red on that this file did
not name; the DMA rename shown to refuse M08b's own committed run; the chain
reader, both verdicts and the run answers found on no two-key rule; and PR 2
owing a decision record it was not given.

**PR 2 — the instrument before the run. Seats review this PR and no other, in
two rounds.** The disclosure suite: the pack authored with both halves and its
sufficiency assert, the runner path, the verdict, the history `suite` enum. The
goldens denominator pinned by name. `disclosure-004`'s reservation withdrawn and
the id refused, **in all three places**, the third being
`answer.schema.json`'s `ai_disclosure` description, which the model reads. The
chain reader and its pin. The prompt-delta test in its per-sample form. The
`p95_ms` condition executed and its outcome recorded — **no move, so neither
digesting record is re-produced**. `rules/schema.json`: `source.effective`
required — *no immortal rules* — with ADR-053's own plant red by name. *Orphan
rule* **defined** in the schema's `description` and in the check's docstring, one
sense, with a plant per sense. `services/highlights-agent/gateway_client.py` and
`platform/gateway/core/classify.py` on `pave/twokey.py` rules, each with a
`_blocked_for` plant, **and the census rule widened over `milestones/M09/` and
`tests/test_m09_*` in the diff that creates them** — the chain reader, both
verdict files and the run answers match no rule today. **And its own decision
record**: `rules/schema.json` puts this PR under `^rules/` with
`requires_adr=True`, and `adr_records` reads the **diff**, so PR 2 carries an ADR
for *no immortal rules* and the *orphan rule* definition — the definition work
ADR-053 says must come first is ADR-shaped anyway. Zero model calls.

**There is no PR 3.** The slot the DMA rename held is vacated (constraint 4) and
spent on PR 4b.

**PR 4 — the disposition, the red, the fix and the green.** The rule's scope text
and its disposition — `status: proposed → enforced`, the `no-control` record
replaced by the eval-pack control — on two keys citing ADR-075. Run A (the pack,
pre-fix) and `pave gate decide` at exit 1. The fix: one sentence in `TOOL_SYSTEM`,
**with `TOOL_SYSTEM_SHA256`, the line-by-line prompt assert and
`milestones/M08/context-census.json` moved in the same diff and named in the PR
body** (constraint 12), and the prompt move recorded in the progression row as an
ADR-021 event. Run B (the pack, post-fix) and `pave gate decide` at exit 0. The
chain reader run over the real record. F1, F2, F3 and F5 read; the refusal reading
on the pack. ADR-075 amended with the numbers in decision 5's sentences, citing
only what `main` or a tag reaches.

**PR 4b — the fix's own control.** The goldens control run at k=3 after the fix,
read by M08b's committed `fresh_join.py` at the same 7700 ceiling: **F4** in its
three parts, the count `N/25` against [8, 12] as a side-prediction, the refusal
reading, the entry, its `README_GOLDENS` row and row 09's bold `N/25` **all in
this PR**, because `check_readme` refuses a goldens entry whose row is pinned to
none. The disclosure comparator pin, with the lane that reads it, or neither. **A
separate PR from run A and run B, deliberately**: the A/B pair is one measurement
taken one sentence apart and stays together, and F4's control run — whose
comparator is a run from the previous milestone — is the half that earns its own
reading (ADR-075 amendment 1 §3).

**PR 5 — close.** Journal, **recording the DMA rename's fifth slide as a finding**;
step 6b read from PR 4's evidence; **Act 3 recorded**
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
· a probe run · a judged entry · `recap-agent` returning to the registry ·
**the DMA rename (SPEC/06b A21), withdrawn from this milestone and re-dated to
`09c` with its own ADR** (constraint 4) · a judge re-freeze of any kind, since
nothing this milestone touches moves the judge's inputs ·
**a case edited, a threshold moved, or a baseline reset to make any run pass.**

## Obligations inherited, each with a date

| debt | owed to | date |
|---|---|---|
| MER-AI-0001's target service and surface, *"the first thing SPEC/09 must answer"* (ADR-074 D4) | Legal/S&P | **PR 1** (ADR-075 D3), executed **PR 4** |
| ADR-053 *no immortal rules* — `source.effective` optional, so a rule can switch off its own clock | Legal/S&P + Security | **PR 2** |
| ADR-053 *no orphan rules* — owed since M07 with its term meaning two things | Legal/S&P + Security | **M09b** — the cap was reached at PR 1b and this is the pre-authorised fallback, fired by name (*Bounded*) |
| The `p95_ms` rule's premise failed — the mandated shape's own p95 went 3769 → 5241, 41 ms over a ceiling derived from it | Platform Engineering | **PR 2**, before anything here touches latency; disposed by the condition, not by a re-derivation. **Executed at PR 1b: the condition holds under no population**, so 5200 stands, ADR-014's stability sentence is withdrawn in an ADR-014 amendment on that file's two keys, and the re-derivation dates to **09c** |
| The DMA rename (SPEC/06b A21) — **withdrawn from this milestone**; a consistent rename makes `fresh_join.py --check` refuse M08b's own committed run, moves the golden cases file, and collects five two-key rules this milestone says do not move (constraint 4) | Legal/S&P + Data Governance | **09c**, by name, with its own ADR and re-scoped as a change to the system under measurement. **Fifth slide, not pre-authorised, recorded as a finding in the close's journal** |
| `platform/gateway/core/classify.py`, G5's router, on no `pave/twokey.py` rule | Data Governance | **PR 2** |
| `services/highlights-agent/gateway_client.py` — the system prompt every governed run sends — on no `pave/twokey.py` rule, while its five siblings are covered. Found reading for this spec; PR 4 edits it, so it joins a rule first | Platform Engineering + Security | **PR 2**, before the PR that edits it |
| The chain reader (`pave/cli.py`, `pave/rules.py`), both M09 verdict files and the run answers on no `pave/twokey.py` rule — the reader decides what *traceable* means and the verdicts are what F1, F2, F3 and F5 are read from. Found at PR 1b by running `pave.twokey.triggered` over PR 2's and PR 4's file lists | Platform Engineering + AI Quality + Security | **PR 2**, by widening the census rule over `milestones/M09/` and `tests/test_m09_*` in the diff that creates them, with a `_blocked_for` plant each |
| The `brand_tone` widening, owed to M04 and re-deferred three times | AI Quality (+ Security, the `quality/judge/` rule) | **M09b**, moved in **PR 1** in the same diff as the row, counted as the **fourth** |
| `milestones/M08/context_census.py`'s `sys.path.insert` leaking a tool path into the session | Platform Engineering | **09c**. Its date was conditional on the p95 condition yielding a move; it yields none, so the condition lapses and the debt is re-dated by name beside the p95 re-derivation rather than left undated |
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

- **Cap: six PRs, and all six are now named: PR 1, PR 1b, PR 2, PR 4, PR 4b,
  PR 5.** There is no PR 3. Reaching the cap again closes the milestone, red if
  necessary.
- **The fallback fired at PR 1b, by name.** **ADR-053's *no orphan rules* half**
  gives way and is re-dated to **M09b** in the close's journal. It was chosen
  because it is a definition problem before it is a build — ADR-053 says so itself
  — and because nothing about the claim depends on it. ***No immortal rules* does
  not give way**, and PR 2 builds it. This is that debt's second dated slide and
  the only one this milestone pre-authorised.
- **PR 3's slot was vacated, not spent on a seventh PR.** The DMA rename cannot
  land here (constraint 4), so its slot carries **PR 4b**. That is a slide of a
  debt this milestone did **not** pre-authorise, so it is **a finding**, recorded
  as one in the close's journal rather than discovered there — which is the whole
  difference between this slide and the four before it. **Any further slide is
  also a finding.**
- **Seats on PR 2 only, two rounds.**
- **Model calls in PR 4 and PR 4b only, ceiling 180 turns across the two.**
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

Today the first command does not exist and the two verdict files do not exist.
The goldens control run's line is `N/25` with 8 ≤ N ≤ 12 and 10 predicted, read
in **PR 4b** by `python milestones/M08b/fresh_join.py --check`'s successor over
M09's answer files at the same ceiling. The market names in the trace's output are
the six the catalog carries today: the DMA rename is withdrawn (constraint 4), so
the demo's vocabulary is M08b's and no reader has to reconcile two.

## Each claim, its measurement, and the PR

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: the disposed rule makes the deployed service fail the gate, and the fix makes it pass, with nothing else moving | the two disclosure runs at k=3 through the deployed gateway; `pave gate decide` over each verdict, exit 1 then exit 0; the goldens control run against F4 | PR 4 (red → fix → green), **PR 4b** (F4) |
| 1a | …traceable from the rule to the failing assert | the chain reader walks rule → `controls[].ref` → case → assert with no step supplied by hand; a planted broken ref is red | PR 2 (reader), PR 4 (over the real record) |
| 1b | …on the real path, at the deployment M08b read | the pre-flight header on **all three** runs: deployed function, both guardrail versions, bundle digests equal to the tree at PR 2's merge; the audit record ids | PR 4, PR 4b |
| 1c | …with nothing else moving | `git diff` over the guardrail, `platform/gateway/policy/`, the corpus, **`data/catalog.json`**, the tiers and the topics between PR 1b's merge and PR 4's branch point, **empty with no carve-out** — the rename is withdrawn, so the clause has no exception to state. The prompt moves only in PR 4 and **is** the fix; what it drags with it is constraint 12 | PR 4 |
| 2 | **F1** — no disclosure case passes before the fix | run A's per-case verdicts | PR 4 |
| 3 | **F2, F5** — every positive case passes and the negative carries no disclosure after the fix | run B's per-case verdicts | PR 4 |
| 4 | **F3** — the gate blocks then permits | the two `pave gate decide` transcripts and their exit codes, committed | PR 4 |
| 5 | **F4** — the 7700 per-sample claim survives the prompt delta, **and no case crosses in either direction** | the goldens control run joined to `usage.calls`, read at the same ceiling by M08b's committed reader; the per-case table against M08b's for the two direction predicates | **PR 4b** |
| 6 | The prompt delta fits the ceiling **before** any call | a test over the committed prompt by the census estimator, per sample: `max(tokens_in + delta × len(calls)) ≤ 7700` over M08b's answered ≤3-call samples. **Not `6782 + delta < 7700`**, which compares a per-sample total to a per-call delta and admits three times the delta the claim survives | PR 2 |
| 7 | The goldens count in [8, 12] (**a side-prediction**); refusals 0–2 on goldens and 0 on the pack | the score transcript; `evals.refusals --sidecar` | PR 4 (the pack), **PR 4b** (the goldens) |
| 8 | The goldens denominator is 25 and the pack is not in it | a test counting the golden file's cases; a planted disclosure id in it is red **by name** | PR 2 |
| 9 | `disclosure-004`'s reservation withdrawn, the id unused | a test over **all three** files — `evals/golden/cases.yaml`, `evals/golden/README.md` and `answer.schema.json`'s `ai_disclosure` description, the one the model reads | PR 2 |
| 10 | The gate reads a disclosure verdict and blocks | `pave gate decide` over a planted FAIL verdict with `suite: "disclosure"`, exit 1 | PR 2 |
| 11 | The disclosure entry is recordable, and pinned by something that reads the pin | `pave gate history`; the `suite` enum plant. **The comparator pin needs a lane**: `pave/cli.py` reads `goldens` and `adversarial` only, and there is no committed disclosure run to pin before PR 4 | PR 2 (enum), PR 4 (entries), **PR 4b** (the pin and its lane, or neither) |
| 12 | The goldens entry, its `README_GOLDENS` row and the bold `N/25` in **one** PR | `pave gate history`, which runs `check_readme` | **PR 4b** |
| 13 | *No immortal rules* | `rules/schema.json` requires `source.effective`; ADR-053's own plant is red by name | PR 2 |
| 14 | *No orphan rules*, one sense | the definition in the schema and the check's docstring; a plant per sense | PR 2 |
| 15 | The `p95_ms` condition evaluated and the manifest at what it yields | the derivation test: population, p95, floor, roof, midpoint, point, the condition's outcome; every constant planted red. **Executed at PR 1b: it holds under no population, so the manifest does not move and neither digesting record is re-produced.** PR 2's test prints the outcome or is red | PR 2 |
| 16 | `gateway_client.py` and `classify.py` on two-key rules | a `_blocked_for` plant per rule | PR 2 |
| 17 | ~~The DMA rename moves every digest it must and nothing else~~ | **withdrawn** — a consistent rename makes `fresh_join.py --check` refuse M08b's own committed run, so no PR of this milestone can measure it (constraint 4) | **09c**, with its own ADR |
| 18 | `brand_tone` re-deferred to M09b in the same diff as the row, counted as the fourth | `tests/test_calibration_owe.py` green with row 09b present; the `deferred_from` arithmetic in ADR-026 amendment 4 | **PR 1** |
| 19 | Act 3 recorded before the row is flipped | `tests/test_demo_recordings.py` green with `recorded` set and `deferred_from` still empty | PR 5 |
| 20 | Zero model calls outside PR 4 and PR 4b; the two within 180 turns together | the PR bodies; no file under `milestones/M09/` carrying `usage` outside those two — PR 2's planted answers live under `tests/` for that reason | every PR |
| 21 | Citations resolve from `main` or a tag | `tests/test_cited_commits_resolve.py` run over each PR's text before it merges | every PR |
| 22 | The deletability audit | the PR body names every check added and whether it went red when deleted | every PR |
| 23 | **The prompt is the system under measurement** | `TOOL_SYSTEM_SHA256` and the line-by-line prompt assert in `tests/test_gateway_run_parity.py`, moved in the fix's own diff on `(platform-eng, security)`, with the prompt move recorded in the progression row as an ADR-021 event (constraint 12) | PR 4 |
| 24 | **The census record is what the committed inputs produce** | `tests/test_m08_census.py`; `milestones/M08/context-census.json` digests `gateway_client.py`, so the fix re-produces it on the census rule's three keys (constraint 12) | PR 4 |

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
- [ ] **PR 1b** (taken): the cold read committed as an amendment to ADR-075 with
      the spec's corrections **in the same diff**; the operator's disposition of
      its asks recorded in the amendment; zero model calls; the cap spent and the
      fallback **fired** by name, ADR-053's *no orphan rules* half re-dated to
      M09b; PR 3 vacated and the DMA rename re-dated to `09c` as a finding.
- [ ] **PR 2:** the disclosure suite built and the gate proved to block on it; the
      goldens denominator pinned by name and the reservation withdrawn **in all
      three places**, including `answer.schema.json`'s `ai_disclosure` description;
      the chain reader, **on a two-key rule created in this diff along with
      `milestones/M09/` and `tests/test_m09_*`**; the prompt-delta test green in
      its **per-sample** form, `max(tokens_in + delta × len(calls)) ≤ 7700`; the
      `p95_ms` condition executed, **recorded as holding under no population, with
      the manifest unmoved and neither digesting record re-produced**;
      `rules/schema.json` requiring `source.effective`; *orphan rule* defined and
      checked; **this PR's own decision record, because `^rules/` is
      `requires_adr` and `adr_records` reads the diff**; `gateway_client.py` and
      `classify.py` on rules with their plants; two seat rounds' findings in the
      PR body, the round told to plant **the prompt-delta test's per-call error and
      a comparator pin no lane reads**; attestations per `pave/twokey.py`; **the
      deletability audit in the PR body, every new check named with its result.**
- [ ] **There is no PR 3.** `data/catalog.json` is unmoved and the DMA rename is
      re-dated to `09c`; a diff of this milestone touching it is a breach of
      constraint 4, not a slide.
- [ ] **PR 4:** the pre-flight printed before the first call of each run; run A,
      the fix and run B committed as-run under `milestones/M09/`; both
      `pave gate decide` transcripts with their exit codes; the rule disposed on
      two keys citing ADR-075; **F1, F2, F3 and F5** read; the disclosure entries;
      the pack's refusal reading; **`TOOL_SYSTEM_SHA256`, the line-by-line prompt
      assert and `milestones/M08/context-census.json` moved in this diff and named
      in the body, with their keys collected and the prompt move recorded in the
      progression row** (constraint 12); ADR-075 amended, citing only commits
      `main` or a tag reaches; **the deletability audit.**
- [ ] **PR 4b:** the pre-flight printed before the first call; the goldens control
      run committed as-run; **F4 in all three parts** — no ≤3-call sample over 7700
      that was under it at M08b, no 3-of-3 pass failing by majority, no 0-of-3 fail
      passing by majority; the count `N/25` against [8, 12] and the goldens refusal
      reading (**side-predictions** — a miss is a finding about the side-prediction
      and does not fail this box's first item); the goldens entry with
      `README_GOLDENS` and row 09's bold `N/25` **in this PR**; the disclosure
      comparator pin with the lane that reads it, or neither; **the deletability
      audit.**
- [ ] **PR 5:** `close-milestone` in order; the journal, **recording the DMA
      rename's fifth slide as a finding**; step 6b read from PR 4's evidence;
      **Act 3 recorded, `deferred_from` still empty**; the progression row's ✅ and
      its goldens cell; tag `m09` (branch `m09-rules`, never the same name); the
      artifact recorded.
- [ ] Nothing under `milestones/M07/` or `milestones/M08b/` changed. **Nothing
      under `milestones/M08/` changed but `context-census.json`'s
      `gateway_client.py` digest line, moved by the fix in PR 4** — the manifest
      line does not move, because the `p95_ms` condition yields no move. Any other
      movement of either record is a breach and not a re-production.
- [ ] No case, tier, token ceiling, guardrail, policy, corpus, catalog or topic
      moved at any point; **every instrument digest, the judge's included, is what
      PR 1b left it** — nothing this milestone touches moves the judge's inputs, so
      there is no re-freeze.

## What must not happen

No guardrail line, no topic wording, no probe, no corpus row, no deploy. No
second brand and no judge axis wired for disclosure. No disclosure case added to
the twenty-five, and no `N/26` published anywhere. No case edited, no threshold
moved, no baseline reset, and no golden case edited to make a run pass. No
`p95_ms` number derived from a pooled p95 or from a population under which the
run it came from would read *within* — the gate does not move to clear a reading.
No re-derivation of `tokens_in`; if the prompt delta does not fit the headroom,
the **fix** is rewritten. No re-run selection and no sample read at any ceiling
but 7700. No history entry edited and none rewritten. **No DMA rename at all** —
it is withdrawn to `09c`, and a catalog, contract-set or `viewer.dma` edit here is
a breach of constraint 4. No comparator pin for a suite no lane reads, and no
prompt-delta assert that charges the delta once to a per-sample total. **And no
claim rewritten to match the outcome:** if a disclosure
case passes before the fix, or fails after it, or the negative case discloses, or
the gate does not block, the claim failed, the case is named, and the milestone
closes red.

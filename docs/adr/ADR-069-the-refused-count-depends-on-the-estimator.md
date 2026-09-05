# ADR-069: the refused count depends on the estimator

**Status: ACCEPTED, 2026-09-05.** Written before the code it governs, in M06d
PR 1. **Zero model calls to write** — every number below is read out of answer
files committed since M06b.

**Seats:** AI Quality (which estimator a reported count uses, and what a published
number is a claim about) · Security / Red Team (the refusal census is the
guardrail's footprint on the golden suite) · Platform Engineering
(`evals/run_evals.py`, a three-key path).

**Revision 4.** Two seat rounds and one measurement map on the drafts, six
reviews, none signed; the record of what each round changed is the last section. The spec was then cut to
two pages and everything decided lives here.

## Context

M06d makes the golden report say what it measured: a case refused before it
reached its asserts is reported apart from a case that answered and answered
badly. Today `evals/run_evals.py` scores both as a plain `FAIL`.

To count refused cases the report must aggregate k samples, and there is more than
one defensible way to do that. `evals/refusals.py:126-133` already records this
and already records the trap: on the three committed M02 control runs, "refused at
least once" and "refused by majority" are 8 and 6, and choosing between them after
seeing the data is a cherry-pick door.

## The three estimators, measured

`milestones/M06b/goldens-run-{1,2,3}.json`, k=3, 25 cases:

| estimator | cases refused |
|---|---|
| unanimously (3 of 3) | **16** |
| by majority (≥2 of 3) | **17** |
| at least once (≥1 of 3) | **17** |

The single case separating unanimous from the other two is **`recommend-015`**,
refused on samples 2 and 3 and answered on sample 1 (recorded spread
`[PASS FAIL FAIL]`).

None of this is new. `milestones/M06b/goldens-run-refusals.json` has carried
`refused_at_least_once: 17`, `refused_by_majority: 17` and
`refused_unanimously: 16` in its census since M06b. What is new is that a *report*
is about to print one of them.

### The same triple means something else three files away

`tests/test_m06b_survivor_census.py:37-39` pins **16 / 17 / 17** as the *per-run*
refused counts of runs 1, 2 and 3. Identical triple, entirely different meaning,
both committed. Named here because a milestone whose claim is legibility must not
manufacture the confusion it exists to prevent.

## Decision 1 — the report uses MAJORITY

**This is the real pre-registration in this ADR.** Not a preference:

1. **It is the only estimator under which the partition closes.** Under majority,
   ≥2 refusals ⟹ ≥2 FAIL ⟹ the case records FAIL, so the refused set is a subset
   of the failed set and `failed = refused + answered_wrong` is an identity.
   Under at-least-once, a case refused once of three can still record PASS and the
   sum would exceed `failed`.
2. **It must match the column it partitions.** `evals/run_evals.py::summarise`
   already aggregates by per-case majority to produce the PASS/FAIL beside it. A
   partition under a different estimator is a second scoreboard reported as one.
3. **Unanimous is the strictest and therefore the most flattering.** It reports
   the smallest refusal footprint of the three. On a milestone whose purpose is to
   make a defect legible, picking the estimator that minimises the defect would be
   the wrong instinct even where it was defensible.

**Correction to revision 1's framing.** On this data majority and at-least-once
are *both* 17 — `cases_separating_the_estimators` is `[]` — so reason 1 separates
nothing here. The live choice is unanimous-versus-not, and it is decided by
reason 3, which is a values argument. Revision 1 led with the arithmetic and
implied the choice was forced. It is not; it is a judgement, and it is AI
Quality's.

### The repo's committed argument against majority, engaged

`evals/refusals.py:142-151` sets `ADR_035_ESTIMATOR = "refused_at_least_once"` and
argues the opposite of reason 3:

> The control this measures is stochastic: it returned different verdicts on
> identical input in 4 of 25 anchor cases… A guardrail that refuses the basic
> question one time in three is a finding, and **majority reports it as a
> non-event.**

**That argument is correct, and it is about a different instrument.** The band
asks *"is this guardrail miscalibrated?"* — for which a one-in-three refusal is
precisely the signal, and majority would suppress it. The partition asks *"did
this case reach its assert?"* — a property of the recorded verdict, which is
itself a majority.

So the repo now carries two estimator regimes deliberately: at-least-once for the
band and ADR-035's trigger 1, majority for the partition and ADR-035's trigger 2
(`blackout-009`). `milestones/M06b/goldens-run-refusals.json` pins
`estimator_for_adr_035` so the band's choice stays explicit. **The band is
untouched by M06d.** Revision 1 disclaimed the band as "untouched, deliberately"
without naming this argument, which is not the same as having read it.

## Decision 2 — the report will say 17. This is a disclosure, not a pre-registration

**Corrected from revision 1**, which called it a pre-registration. 17 has been
committed and visible in `goldens-run-refusals.json` since M06b. Announcing a
number already in a committed file is disclosure; pre-registering means fixing a
choice before an unknown outcome, which is what Decision 1 does and this does not.

17 is not a regression, not a correction to any published figure, and not evidence
that anything previously published was wrong. 16 and 17 are answers to two
different questions about the same runs.

## Decision 3 — the erratum: correct the live documents, leave the record as-run

### The enumeration is now a command, because three hand counts failed

Revision 1 claimed **nine sites, "enumerated rather than gestured at"**. Revision 2
claimed **21**, and said in its own words that *"an enumeration presented as
exhaustive that misses more than half its members is the same defect class it was
written to prevent."* Two seats then found revision 2's sweep missing four to five
more — three of them inside `quality/adversarial/`, a live corpus under Security's
key, where this decision's "closed record" rationale does not apply at all.

**A third hand count would not be credible, and `git grep` cannot do the job.**
`docs/adr/ADR-065-...:163` wraps between the "16" and the "answer-channel
refusals" it qualifies, so no line-based pattern can see it.

So the enumeration is `tools/sweep_sixteen.py`, committed in PR 1. It reads whole
files, collapses whitespace, matches across the wrap, and maps back to a line. It
splits its output two ways, which is the small prototype of the linter this
decision describes at scale:

- **BARE — 26 sites** publish 16 as the refusal count with no estimator named.
- **LABELLED — 1 site** publishes it with the estimator that produced it: the
  `README.md` correction this PR makes.

Run it rather than trusting a number in this file:

```
python tools/sweep_sixteen.py
```

Every exclusion is by path and carries its reason in the source, so a reader can
audit what was left out rather than infer it from a regex: per-run figures that
genuinely are 16, `cal-16`, a `:16` format width, an unrelated headroom figure,
and the census keys where `refused_unanimously: 16` is correct and labelled.

Of the 26 bare sites, **two are in gateway production source**
(`platform/gateway/core/guardrail.py:254`, `platform/gateway/handler.py:493`) and
**four are in `quality/adversarial/`** — `answer-decomposition.yaml:102`,
`refusal-shapes.yaml:76`, `topic-attacks-output.yaml:51`, `instruments.json:98` —
plus one in `services/highlights-agent/topic_baseline.py:210` that no seat found.

### The channel finding, which revision 1 missed entirely

Six of the sites qualify the count with **"answer channel"**. Measured across the
50 blocks in `goldens-run-refusals.json`: **42 `answer`, 8 `tool_output`**, the
`tool_output` blocks falling on five cases — `blackout-007`, `blackout-009`,
`brand-021`, `concise-022`, `headroom-005`.

| estimator | any channel | **answer channel** |
|---|---|---|
| unanimous | 16 | **11** |
| majority | 17 | **14** |
| at least once | 17 | 17 |

**16 is not the answer-channel count under any estimator.** It is the any-channel
unanimous figure with a channel qualifier attached.

Two things keep this from being a straightforward error. The eight `tool_output`
blocks are exactly the eight **ADR-063 closed** at M06b, so on the current gateway
the answer channel is the only one left and the qualifier is accurate *going
forward*. And every one of the 17 refused cases did have at least one
answer-channel block, so no sentence claims something that never happened. What
the sentences are is a composition of two separately-true facts that reads as a
count nobody computed.

### The decision

**`README.md`'s two sites are corrected in M06d PR 1. The other 24 stay
as-run.**

- **`README.md` is the live document.** CLAUDE.md: the progression table and its
  footnotes are *"the five-minute reader's entire experience — it must be true."*
  A reader who will never find this ADR meets the number there.
- **The other 24 are the record.** Closed milestones, their ADRs and the working
  documents beneath them are what was believed and measured at the time.
  Rewriting them is what CLAUDE.md's append-only and superseding discipline exists
  to prevent, and errata against sentences that are loose rather than false teach
  a reader that a correction notice means "someone changed the question" — a
  signal that should stay expensive.
- **The four `quality/adversarial/` sites stay, and this is the one that needed
  arguing.** Security's round-2 objection is fair: a corpus header is live prose
  feeding an instrument under its key, not a closed record, so the rationale above
  does not reach it. It stands anyway, for a different reason — each of the four
  is a *"what this cannot show"* disclaimer about M06b's investigation, describing
  the population that investigation looked at. Changing 16 to 17 there would
  restate a historical scope note as though the scope had been different. **What
  does change: they are now enumerated**, so the next reader meets them.
- **The two gateway source comments stay.** They are accurate about the code they
  annotate: the handler did hold that response on M06b's refusals, and post-ADR-063
  the answer channel is the only one it holds them on. Editing deployed source to
  adjust a comment's arithmetic is a redeploy for no behavioural change.

**At scale, replace with X; the interface already matches.** At scale this is a
docs-level numeric-provenance check: every published count carries the estimator
and channel that produced it (`refused@majority,any-channel=17`), and a linter
refuses a bare count in prose. The interface already matches — the census in
`goldens-run-refusals.json` computes all three estimators and records every
block's channel today, so the data a linter would read already exists. Only the
notation and the check are missing.

## Decision 4 — the count is channel- and mechanism-agnostic, with a PAIR assertion

One `refused` count, ignoring channel and mechanism, because the question is *did
this case reach its assert?* — for which neither matters: the gateway returned
`decision != "allowed"` and no answer was produced either way. **The report line
does not say "by the guardrail"**; revision 1's did, which was a mechanism claim
the count does not carry.

`evals/refusals.py:18-22` — quoted exactly — says the mechanism is *"kept, never
summed away"*, because a guardrail refusal and a classification denial are
**different controls with different owners**.

**Revision 2 proposed asserting the mechanism set is a singleton. Security found
that does not discharge the rule, and it is right.** The operative words are
*different controls*, not *different mechanism strings*. The deployed stack
carries a second DENY topic, `enforcement-probing`
(`platform/infra/lib/gateway-stack.ts:341`), and ADR-063 deploys a second
guardrail — and all of them record `mechanism: "guardrail"`. A run where 9 cases
are refused by `entitlement-circumvention` and 8 by `enforcement-probing` yields
`refused: 17`, a singleton mechanism set, and a green assertion. That is the
finding going to the wrong seat, and ADR-035's trigger 1 is precisely
*`enforcement-probing`'s footprint above 2 of 25*. (The vocabulary was wrong too:
`platform/gateway/core/audit.py:42-44` defines `classification`, not `classifier`,
and five further values.)

**So the assertion is on the `(mechanism, assessed)` pair set.** On M06b that pair
is `("guardrail", "TOPIC:entitlement-circumvention")` x 50 — measured. A second
topic, a second guardrail, or a classification denial each turn it red.

Two further conditions, both from Security's finding:

- **It reads the run being reported**, in `run_evals.py::run` beside the counts —
  not a committed file. An assertion whose subject is three frozen answer files
  can never fire, and `SPEC/06d` forbids that shape in its own *What must not
  happen*.
- **It records rather than raises.** `evals/adversarial.py:604-608` refuses a
  raise in a gate lane in its own words — an errored CI step instead of a stated
  block.

### Its input is the refusal sidecar, joined by `record_id` — revision 4

Revision 2 left the input unnamed, and the measurement map (revision record,
round 3) found that nothing `run_evals.py` reads carries `assessed`. A refused
answer entry holds exactly two fields — `refused_by_gateway` (the mechanism) and
`record_id` (`run_with_tools.py:195-197`). `assessed` lives only in
`goldens-run-refusals.json`, the sidecar `run_with_tools.py` builds from the audit
records it fetched back out of the lake. So on the demo run the check would have
seen the mechanism alone — the singleton Security had already rejected — and
passed for the wrong reason.

**The sidecar becomes an input of `run`**: a repeatable `--refusals` argument
beside `--answers`, and the pair set is computed from the sidecar entries whose
`record_id` matches a refused answer in the run being scored. Measured before
writing this: all 50 refused answers across M06b's three runs resolve in the
sidecar, to one pair.

This is the production shape, not a workaround. The repo already keeps two stores
with one key: the answer file is what the agent said, the audit record is what
the platform did, and the sidecar's own `_what_this_is` says exactly that split.
At scale the sidecar is a lake query by `record_id`; the interface already
matches. Two alternatives were priced and rejected:

- **Copying `assessed` into the answer entry at capture time** makes the answer
  channel restate the audit record. Claim 5's principle is that observations are
  fetched out of the lake and never taken from the gateway's word; this is the
  boundary that principle rests on. It also cannot serve the demo: M06b's files
  lack the field and regenerating them costs model calls.
- **Querying the lake from the scorer** puts network and credentials into
  `make check` — G8, one step from G1.

Three rules for the join, so it cannot pass vacuously:

- **No sidecar, no assertion — said aloud.** Without `--refusals` the report
  prints that the pair set was not assessed. A check that passes on absent input
  is the shape ADR-035 catalogued.
- **A refused answer whose `record_id` resolves to nothing is a note.** The
  adversarial lane scores an unresolved record FAIL (claim 5); here the
  partition gates nothing, so it is a stated note in the verdict's `notes` —
  which the gate renders — and `scores` is untouched.
- **Not a committed-file assertion.** The forbidden shape is a *test* pinning
  three frozen files. `--refusals` is per-invocation input, the way `--answers`
  is; PR 2's test supplies a synthetic sidecar, green with one pair and red with
  a second topic, and red again with an unresolved id.

The sidecar rests on one key today — the goldens-evidence rule does not match its
name (*What this ADR does not decide*, last item) — which is the M07 debt every
number in this ADR already shares.

### Where the count is and is not public — corrected in revision 4

Revision 2 said the count is *"rendered publicly"* in the gate's PR comment from
PR 2 onward, and that this is what makes the pair assertion load-bearing. **That
is false for M06d.** The gate's evals verdict is written by
`pave/cli.py::evals_run` (`.github/workflows/quality-gate.yml:94`), which builds
its own `scores` — `tools_passed`, `control_passed` — and never calls
`emit_verdict`. SPEC/06d forbids touching that file (zero-key;
`tests/test_evals_lane.py:155` pins its scores). So no gate comment carries
`refused` in this milestone. The count is public in the printed report and in
the verdict `emit_verdict` writes when `run_evals` is invoked with `--out`, and it
reaches the gate table the first time such a verdict is handed to the gate — not
here. "Reporting only" is true of `decide`, which reads `verdict` and never
`scores`. The pair assertion is load-bearing because `scores` is the shape
history and the gate both read, not because the comment shows it yet.

## Decision 5 — three cuts, each with a deadline

Recorded rather than discovered, per CLAUDE.md: a scope cut is an ADR, never a
silent simplification.

### Cut 1 — the new keys are not derivable. Deadline: the next goldens entry

`pave/history.py::derive_scores` produces `total/passed/failed/infra/pass_rate`
(+`pooled_pass_rate`). `refused` and `answered` are in neither list, and
`check_derivable` iterates `derive_scores`'s keys, so extra keys are **tolerated**
— a recorded entry could carry any two numbers and nothing would notice. This also
makes `pave/history.py:396-398`'s docstring — *"key for key what
`evals/deterministic.py::tally` … writes"* — false after M06d.

Latent for M06d, which records no entry. **Binding on the first milestone that
records a goldens entry**, which closes it or M06d's `scores` keys come out. The
fix is per-case `refused` in `cases`, touching `evals/history/schema.json` and
`pave/history.py`, both three-key — which is why it is not done here: it would
turn a reporting milestone into a schema milestone.

*At scale, replace with X; the interface already matches.* At scale every score
key is derivable from the row's own cases by construction, because the recorder
computes scores *from* `cases` rather than beside them. The interface already
matches — `derive_scores` exists and `check_derivable` already runs on every
entry; only these two keys are outside it.

### Cut 2 — the paired diff gets no partition. Deadline: the next two-arm run

`evals/run_evals.py::paired_diff`'s docstring calls the diff **"the result, not
the total"** (ADR-021). M06d makes the *total* legible and leaves the designated
*result* illegible: a case in `lost` may have been lost to a refusal rather than
to a worse answer — M01's headline-conceals-a-regression finding, one layer down,
which is the same finding M06d fixes one layer up.

**Binding on the next milestone that runs both arms.**

*At scale, replace with X; the interface already matches.* At scale the diff is
computed over per-case records that already carry their refusal state, so a `lost`
bucket splits by cause without a second pass. The interface already matches —
`paired_diff` takes both arms' summarised results and the marker is on the answers
those results came from.

### The G4 test, and the four residual routes (deadline M07)

Revision 2 put the G4 test in `quality/adversarial/g4-semantics.yaml` and claimed
it *"proves the partition is unreachable from `evals/adversarial.py`"*. Security
found it covers one of five routes, and that the corpus edit carried two unpriced
costs: a Security ADR amendment in PR 2's own diff (`quality/adversarial/` is
`('security',)` + `requires_adr`), and a moved `g4_cases_sha256` that makes
`evals/run_adversarial.py:96-103` refuse the next adversarial recording at M07.

**The test moves out of the corpus.** It lives in
`tests/test_adversarial_scoring.py` — the file `g4-semantics.yaml`'s own header
designates for *"what a table cannot say"* — and asserts the narrow property: a
synthetic observation carrying `refused_by_gateway` / `refused` / `answered`
scores byte-identically through `score_one` with and without them. Zero-key
file, no corpus digest moves, no re-registration. That is ceremony proportional
to risk: the same property, none of the M07 debt.

**Four routes it does not cover**, recorded here rather than implied by a
checkbox, all binding at M07: (1) `evals/adversarial.py` opening a goldens answer
file; (3) a `refused` key reaching its own `tally` at `:756`, downstream of
`score_one`; (4) a helper in `evals/deterministic.py` — no rule, no digest,
already imported at `:32` — the live one; (5) capture time, via
`platform/gateway/core/audit.py::observation_from_record`, which
`g4-semantics.yaml:57-76` states is invisible from that corpus.

### Cut 3 — 24 of the 26 sites are not corrected

Decision 3 above; deadline none, deliberately. This is a permanent disposition
about the historical record, not a debt.

## Decision 6 — the objection in `tests/test_refusal_band.py`

That test's docstring (`:88-93`) states the argument against M06d:

> A refusal count that reached the score would let a guardrail misconfiguration
> read as a service regression — and would let tuning the guardrail move a
> recorded number, which is the trade this repo refuses.

M06d puts a refusal count in `scores`. **The answer: the coupling already exists
and is currently silent.** `scores["passed"]` is 1 of 25 *because* 17 cases are
refused, so guardrail tuning already moves a recorded number — the headline one,
invisibly. The partition does not create the coupling; it makes it attributable,
which is the opposite of a misconfiguration reading as a service regression.

**The docstring is amended in the same diff as the change that contradicts it.**
A repo carrying two documents that disagree about whether a thing is allowed is
how ADR-035 and ADR-037 both started. This is AI Quality's and Security's call
jointly, and either disposition is recorded here.

## Decision 7 — the identity, its preconditions, and what `answered` is

The invariant M06d commits is `refused + answered == failed`, with
`refused ⊆ failed`. It holds only because a refused sample fails — and revision 1
said it fails "its content asserts", which is false. Had `grounded-019` been
refused (it was not; it records `FAIL [FAIL PASS FAIL]` on `budget`), every one of
its content asserts would pass on a refusal envelope: a refusal cites nothing,
which is what `cited_titles_empty` wants (`evals/deterministic.py:176-191`).

**What actually holds:** `json_schema` is on 25 of 25 cases, pinned by
`tests/test_contracts.py:265-270`, and the refusal envelope fails it with
`'answer' is a required property`. Two preconditions follow, named so the
identity's failure is legible when it comes:

1. **Every case carries `json_schema`.** A case written without it, or a relaxed
   answer schema, breaks `refused ⊆ failed`.
2. **A refused record carries `usage`.** `deterministic.py:392-399` returns
   INFRA, not FAIL, when `budget` finds none. `run_with_tools.py:213` writes zeros
   on the refusal path — and its comment justifies them with the claim above that
   this decision refutes, so a reader tidying the comment could take the `usage`
   with it.

**The ADVISORY route.** A uniform `usage` failure makes the case INFRA, which the
report shows. A *mixed* one — `[INFRA, FAIL, PASS]` — has no strict majority and
records ADVISORY (`run_evals.py:311-314`), which `tally` does not count: the case
is majority-refused and lands in no bucket. So `total == passed + failed + infra`
is not an invariant, and PR 2 asserts `passed + failed + infra + advisory == total`
beside the partition.

**`answered` is computed, not derived.** As `failed - refused` the identity is
`x + (y - x) == y` — a tautology that can never go red, which would make the
DoD's "deleted and re-run red" box unsatisfiable. It is
`|{r in results : r.result == FAIL and r.id not in refused_ids}|`, from `results`,
in scope at the seam. The refused set iterates `cases`, not the answer files'
keys; on M06b's files those coincide, which is exactly why the rule is written.

**Both properties are measured on synthetic fixtures, because M06b's files
exercise neither.** On those files `advisory` is 0 (1 + 24 + 0 = 25), so the
four-term sum is exercised only by a fixture with a mixed `[INFRA, FAIL, PASS]`
sample. And `failed - refused` gives the same 7 as the real computation there, so
"deleted and re-run red" cannot tell them apart on real data; PR 2 carries a
fixture with a refused case that records PASS — a case without `json_schema` —
on which the two disagree.

## What this ADR does not decide

- **Whether `evals/refusals.py`'s band moves to majority.** It does not; see
  Decision 1. Different population, different pre-registration.
- **Anything about fixing the refusals.** Route 1 is a later spec's.
- **Whether `1/25` is recordable to history.** It is not, on AI Quality's and
  Security's M06b disposition, and M06d does not reopen that.
- **Whether `milestones/*/goldens-run-N.json` should take two keys.** The
  goldens-evidence rule matches `goldens-run.json` and `runs/*.json`, not the `-N`
  naming M06b used, so every number in this ADR rests on files editable on one
  key. Pre-existing; registered with an M07 deadline, not adopted.

## Consequences

- One line in every golden report from here: the failed count split into refused
  and answered-wrong.
- `scores` gains `refused` and `answered`. `evals/history/schema.json` needs no
  change — `additionalProperties: {"type": "number"}`, the precedent
  `pooled_pass_rate` set. `quality/verdicts/schema.json` is the same shape, so the
  gate verdict validates unchanged.
- The partition is **reporting only** and gates nothing — `pave/gate.py::decide`
  reads the verdict's `verdict` field, never `scores`. PR 2 ships the test that
  says so — it is the seventh in SPEC/06d's PR 2 list, having been named here and
  assigned nowhere until round 3 — because "reporting only" decays silently the
  first time somebody finds it convenient; `evals/refusals.py` learned that first.
- **The committed invariant is the identity, not the 17.** No frozen count lands
  as a constant: a guard coupled to its own data goes red the first time the data
  legitimately changes, and `evals/refusals.py`'s `OBSERVED` is that worked example
  already.
- The identity holds on two preconditions, both named in `SPEC/06d`: every case
  carries `json_schema` (`tests/test_contracts.py:265-270`), and a refused record
  carries `usage` (or `budget` returns INFRA, not FAIL).

## Revision record

Two seat rounds on the drafts of this ADR and its spec. Six reviews; none signed.
Kept here, not in the spec, because a spec that narrates its own revisions has
become a journal.

**Round 1 found:** the seam named in the plan (`tally`) cannot see the answer
payload *and* is in a zero-key file while the spec claimed three keys — the
ADR-035 shape; the DoD's identity was `refused + answered == total`, false against
a printed 17 + 7 = 24; the stated failure mechanism was false and the real
precondition (`json_schema`) uncited; the `edge-024` quotation was trimmed in the
direction that flattered the premise; "nine sites" was not nine and the channel
qualifier was wrong; G4 was stated in prose and absent from the DoD; two DoD
boxes could not both be checked; the cap stated no behaviour on being reached.

**Round 2 found the corrections wrong in new ways:** the G4 box overclaimed a
proof its test does not produce, and a fifth route was unnamed; the singleton
assertion was on the wrong axis; step 6b's skip rested on an unsound reason and
on `ggla7vqlfu7d` v1, an identifier with no provenance in the repository —
so the box was worked instead, and found no new hole; `answered` was undefined,
which made the central assertion a tautology; the ADVISORY route was unnamed;
the enumeration was wrong a second time, so it became a command; seven line
citations were wrong; a two-key call was asserted on a zero-key file; and the
`grounded-019` counterexample was written as a measurement of a case that was
never refused.

**After round 2 the operator asked whether this was becoming M06b again.** It
was: the spec had reached 652 lines, the cap had gone 2 → 4 → 5, and PR 2's G4
test had grown a Security ADR and an M07 re-registration debt. The spec was cut
to two pages, the G4 test moved out of the corpus, cut 4 was deleted with it,
and the cap returned to three. What survived every round unchanged: the claim,
the estimator, and the demo artifact.

**Round 3 was a measurement map, not a seat round.** Every claim in the spec and
this ADR was asked which measurement proves it and in which PR. Three had none:
the pair-set assertion's input carried no `assessed` (Decision 4, now the
sidecar joined by `record_id`); the "rendered publicly" sentence was false under
the spec's own `pave/cli.py` constraint (Decision 4, corrected); and two of the
identity's properties — the ADVISORY sum and a computed `answered` — were
unmeasurable on M06b's data (Decision 7, now synthetic fixtures). The "reporting
only" test was named in *Consequences* and assigned to no PR; it is PR 2's
seventh. Also found and recorded rather than claimed: majority versus
at-least-once is not separable on this data — `cases_separating_the_estimators`
is `[]` — so the rescore proves only majority versus unanimous, through
`recommend-015`. The demo artifact gained a third line.

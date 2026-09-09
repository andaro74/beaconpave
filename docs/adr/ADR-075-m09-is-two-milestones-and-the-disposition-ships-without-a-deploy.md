# ADR-075: M09 as inherited is two milestones, the disposition ships without a deploy, and answer quality gets a row

**Status: PROPOSED in M09 PR 1; ACCEPTED when that PR merges, which is the
operator's disposition.** Decisions 1, 2, 3, 4 and 6's split are the operator's,
made 2026-09-09 on the written question the M08b close left open, and are
recorded here, not argued. Decision 5 is written before any code, any deploy and
any call; PR 4 fills numbers into its sentences and nothing else. **Zero model
calls to write**: every number below is read out of `milestones/M08b/README.md`,
`milestones/M08/README.md`, `pave/twokey.py`, `pave/history.py`,
`tests/milestone_status.py`, `tests/test_calibration_owe.py`,
`tests/test_demo_recordings.py`, `tests/test_adr_index.py`,
`tests/test_cited_commits_resolve.py`, `evals/history/schema.json`,
`quality/verdicts/schema.json`, `services/highlights-agent/gateway_client.py`,
`services/highlights-agent/evals/answer.schema.json` and the golden cases file.

**Seats:** PM (two rows added in place; nothing shifts) · Legal/S&P (the rule,
its scope text, the disposition) · AI Quality (a suite is added; the goldens
denominator is pinned; a judged owe is re-deferred) · Platform Engineering (the
p95 rule's failed premise; the two-key gaps) · Security (the second key on the
rule and on the prompt) · Tool Owner (the registry lookup).

## Decision 1 — M09 as inherited is two milestones; the disposition ships first, without a deploy

**The question.** M09 as the M08b close handed it over carried claim 6 (the
registry and the regdelta loop, new gateway code, a seat round on the
guardrail), Act 3, the `entitlement-circumvention` recalibration riding the
guardrail line M09 adds, the `brand_tone` widening as a judge run and re-freeze,
the DMA rename by name in no PR with anything else, the `p95_ms` rule's failed
premise, ADR-053's two halves, MER-AI-0001's target service, Security's two
round-one probes, `classify.py` on no rule, and eight smaller dated items.

**Read as spend and as controls, not as a list.** Four spend events and one
deploy: a run that shows the service red, a run that shows it green, the
`brand_tone` judge run, and a probe re-run after any guardrail line moves. Two
seat rounds on two genuinely different controls: the registry and disposition
path (Legal/S&P, Tool Owner, AI Quality) and the guardrail line (Security,
Platform Engineering). **M08b took six PRs for one spend event, one seat round
and no deploy.**

**The dimension that decides it is attribution, not PR count.** ADR-074 decision
1 refused this shape one level out: *"the run cannot be the registry's, because
a red after a disposition on the first fresh run in two milestones is
unattributable — the disposition, the browse gap, or drift."* The same sentence
points one level in. **A red after a disposition *and* a new guardrail line is
unattributable between the two controls**, and claim 6's whole content is that a
reader can trace the red to the rule. A milestone that makes its own claim
untraceable has not cut scope, it has cut the claim.

And the M06b journal is the other half. Its *What broke* opens: *"Everything
from PR #89 onward is an investigation the milestone did not plan and should
probably not have adopted."* Thirty-four PRs, four hypotheses, none confirmed.
That is what a milestone carrying two controls and four spend events becomes the
first time a red is ambiguous — there is no bounded next step, so every next step
is another measurement.

**The operator resolved it: two milestones, the disposition first.**

- **M09 — the disposition, and the service goes red on a control that needs no
  deploy.** Claim 6. The rule disposed into an eval pack; the pack run through
  the **existing** deployment; the fix; the second run; the goldens arm re-run as
  the fix's own control; the registry lookup; Act 3. One seat round, on the
  registry and disposition path. Plus the debts that do not need the guardrail:
  the DMA rename, the `p95_ms` premise, ADR-053's halves, `classify.py`,
  `gateway_client.py`, and the smaller dated items.
- **M09b — the guardrail line the same rule also disposes into, and the topic it
  recalibrates.** One deploy; one seat round, on the guardrail; the probe
  re-run; `entitlement-circumvention` recalibrated as M08b dated it; Security's
  two round-one probes; the `brand_tone` widening and re-freeze. Claim 6 is
  proven by then, so nothing in M09b is load-bearing for a claim — which is the
  right shape for the milestone that carries the deploy.

**The fix needs no deploy, and that is the fact that makes the split work.**
`TOOL_SYSTEM` lives in `services/highlights-agent/gateway_client.py`,
caller-side, not in the deployed bundle; `handler.py` receives `system` in the
event. So the whole red → fix → green loop runs against the deployment M08b
measured, at the guardrail versions M08b recorded, with no bundle digest moving.
Checked by reading the file, not assumed.

**Why in place and not a third shift.** ADR-054's paragraph, quoted by ADR-074
decision 1 and applying again unchanged: renumbering *"rewrites every downstream
id in `README.md`, `BUILD.md`, the demo script's act ownership and
`recordings.json`'s `owed_by` fields … taken for a cosmetic gain."* `00a`/`00b`,
`06b`/`06c`/`06d` and `08b` are four precedents for splitting in place. **M09b is
a row added between 09 and 10; nothing below it shifts.**

**What Act 3 costs, and why it stays in M09.** `tests/test_demo_recordings.py`
goes red the moment `README.md`'s row 09 carries ✅ with act 3 unrecorded, and
act 3's `owner_milestone` is `M09` with `deferred_from` empty. Recording it in
M09 keeps that list empty. Recording it in M09b would make M09 the act's **first
counted deferral** — a two-key edit to `recordings.json` with a named admission,
which the ratchet exists to charge. The red → fix → green beat is M09's, so the
act belongs where its content is. `recordings.json` is therefore **not edited by
this milestone**, and that is a decision rather than an omission.

## Decision 2 — answer quality is scheduled as 09c, and this ADR separates the two `M10`s

**The trigger fired on both halves.** ADR-074 decision 2 made the browse gap and
the `tokens_out` tiers owned and unscheduled with one written trigger, *persists
on M08b's fresh run*. It persisted: the browse gap on **nine samples across five
of the seven cases**, and the `tokens_out` failures widened from **five cases to
twelve**, two of them by a single sample writing **307 and 308 tokens against a
tier of 300**. The M08b journal's own recommendation to this ADR: *"a trigger
that fires and produces only a longer table is a trigger nobody has to answer."*

**The operator resolved it: a scheduled answer-quality milestone follows M09,
added in place as `09c`.** Surfaces stays `M10`, the drill `M11`, self-heal
`M12`; nothing below row 09 shifts. It serves **claim 2 defensively** — a gate
whose answer axes have never been measured against a repaired agent — and
**carries no claim of the twelve**, on the precedent of rows `06c`, `06d` and
`08b`, which carry none either. **What claim, if any, 09c should carry is left to
09c's own spec**, and it is stated here rather than decided so that the question
is inherited rather than discovered.

**The collision, named, because two different `M10`s are already in the tree.**

| the string | where | what it meant | what it means now |
|---|---|---|---|
| `M10` | `milestones/M08/README.md`'s last two debt rows (the seven browse-gap cases to Tool Owner; the five `tokens_out` cases to AI Quality) and ADR-073 §4's *"Tool Owner's M10 material"* | *the answer-quality work*, dated before any milestone owned it; voided by ADR-074 decision 2, which made both owned and unscheduled | **the scheduled answer-quality milestone, `09c`** |
| `M10` | `pave/cli.py:699`, `pave/floors.py:338`, `pave/manifest.py:161` and `:354`, `pave/scaffold.py:123`, `templates/agent-tools/README.md:28`, `tests/test_floors.py:250`; `docs/governance/demo-script.md:85`; every `M10` in the M08 and M08b journals about lanes, the second brand and superseding history entries | **the surfaces milestone** | **the surfaces milestone, unchanged** — the sites are correct as written and are not edited |

The second row is the whole reason the label is in place rather than a
renumbering. Priced before the choice was made: a renumbering moves those seven
sites a **fourth** time across **three** two-key rules (`pave/floors.py` +
`tests/test_floors.py` at three seats; `pave/manifest.py` at three;
`pave/scaffold.py` + `templates/agent-tools/README.md` at four), and it moves
`docs/governance/recordings.json` and `tests/test_demo_recordings.py` at two
more, because `tests/milestone_status.py::milestone_is_closed` **raises** for a
milestone with no progression row and acts 4 and 5 name `M11` and `M12`. **Four
rules, twelve attestations, four seats, for a digit.** M08b's own debts table
closed those seven sites *"by deciding not to act"*; this decision keeps them
closed. The in-place label costs **no attestation for the numbering at all**.

**And the split makes the arithmetic worse for a renumbering, not better.** With
M09 split, an inserted answer-quality number would push surfaces by **two**, not
one. In place, `09` · `09b` · `09c` · `10` needs no arithmetic.

## Decision 3 — MER-AI-0001 is disposed against `highlights-agent`, by a deterministic assert

ADR-074 decision 4 named this *"the first thing SPEC/09 must answer"* and did not
answer it. The problem as inherited: `rules/MER-AI-0001.yaml` is a Meridian
**News** disclosure rule about AI-generated **recaps**; the service Act 3 names,
`recap-agent`, left `platform/registry/tools.yaml` at ADR-048 and by ADR-023
**cannot ever be a caller** — one gateway deployment authorizes as one service;
the only deployed service is Meridian Sports' `highlights-agent`; and the judge
has no `meridian-news` axis until the surfaces milestone by ADR-046 and ADR-047.

**The operator resolved it: the rule is disposed against `highlights-agent`, and
the control is a deterministic `ai_disclosure` assert, not a judge axis.**

- **Why deterministic.** CLAUDE.md: *"Prefer deterministic assertions over judge
  assertions wherever a deterministic one can express the requirement."* This one
  can: `services/highlights-agent/evals/answer.schema.json` already carries
  `ai_disclosure` as `["string","null"]` with the description *"Disclosure text
  required by MER-AI-0001 on AI-authored editorial copy. Null until M07 disposes
  that rule."* The requirement is presence-and-shape on a named field. A judge
  axis would also drag the frozen instrument into the disposition PR, and
  `quality/judge/rubric-sports.md`'s existing `disclosure_present` axis is
  therefore **left unused and unmoved by M09**; whether it is retired or wired is
  M09b's, beside its own re-freeze.
- **Why not the second brand.** Bringing `meridian-news` forward from the
  surfaces milestone to give the rule its native subject would put a brand pack,
  a judge axis and a rule disposition in one milestone — which is how M06 came to
  be overloaded (ADR-054), and it would move the six code sites decision 2 just
  decided not to move.
- **What it costs.** The rule's **scope text** moves: `rules/MER-AI-0001.yaml`'s
  `title` and `source.ref` describe AI-generated recaps, and the disposition must
  say plainly which service and which surface the rule binds. `^rules/` is
  `(legal-sp, security)` with `requires_adr=True`, so that edit collects two keys
  and cites **this ADR**. It lands in the disposition PR, not this one.
- **The demo script is corrected in this PR**, on ADR-048 decision 5's precedent
  (the four prose sites corrected in the same commit as the decision). Act 3 says
  *"Next run, recap-agent goes red"* and *"three golden cases plus one guardrail
  line"*. Both are false as scheduled: the service is `highlights-agent`, and the
  guardrail line is M09b's. `docs/governance/demo-script.md` is on no
  `pave/twokey.py` rule, so this is a prose correction with no key — which is
  itself ADR-048's recorded residual, restated rather than claimed away.

**What this must not become.** `rules/MER-AI-0001.yaml`'s own header states the
hazard in as many words: *"It shipped in the starter as `status: enforced` with
controls already pointing at a `disclosure-*` eval pack that also already
existed. That makes claim 6 unprovable: the delta had already happened at commit
one."* A disposition whose control the service already satisfies is the same
defect through a different door, which is why decision 5's first falsifier is
*any disclosure case passing before the fix*.

## Decision 4 — the disclosure pack is its own suite; the goldens denominator stays 25

**The operator resolved it: the disclosure cases are not folded into the
twenty-five.** Adding `disclosure-004` to
`services/highlights-agent/evals/golden/cases.yaml` would make every future
`N/25` an `N/26` and make M09's count incomparable to `m00b` through `m08b` for a
reason that has nothing to do with any system under test.

- **A suite, not an arm.** In this repository `arm` means *which system produced
  these answers* over one case set — `evals/comparators.json` carries
  `arms_expected: ["tools", "control"]` and the paired diff depends on it. Using
  `arm` for a different case set would make the word mean two things, which is
  the defect ADR-053 refused to inherit for *orphan rule*. `pave/history.py`
  already keys on `(sha, suite)` and `evals/comparators.json`'s
  `_why_the_suites_key` was written for exactly this: *"two suites now pin
  numbers here."*
- **What that costs, checked rather than assumed.** `quality/verdicts/schema.json`
  types `suite` as a **free string** (*"e.g. evals, contract, playwright, k6,
  drill"*), so the gate reads a disclosure verdict and blocks on FAIL at **no
  schema cost** — `pave/gate.py` never enumerates suites. What does cost:
  `evals/history/schema.json`'s `suite` enum is
  `[goldens, adversarial, contract, playwright, k6, drill]` and gains
  `disclosure`, on `^evals/history/` — three keys (AI Quality, Security, Platform
  Engineering).
- **`pave/history.py::check_readme` is not triggered by it.** Its `tagged` set is
  `suite == "goldens"` only, so a disclosure entry forces no `README_GOLDENS` row
  and no bold cell. The goldens re-run of decision 5 **does** force both, in the
  same PR as its entry — the refusal ADR-074 amendment 1 fact 2 found the hard
  way, carried here as a checkbox.
- **The goldens denominator is pinned by name.** A test asserts the golden cases
  file holds exactly 25 cases and that no case id matches the disclosure pack's
  prefix, so folding the pack in later is red by name rather than red as a
  changed number.
- **`disclosure-004`'s reservation is resolved, not left.** The golden file says
  *"`disclosure-004` is reserved for M07 — the gap is the reservation"* and
  `evals/golden/README.md` repeats it. M07 is the guardrail milestone and no
  longer means anything here, and a reservation that has outlived three
  renumberings is a stated protection that is absent — CLAUDE.md's own shape.
  **Pre-registered: the reservation is withdrawn by name in the disposition PR**,
  both comments rewritten to say where the disclosure cases actually live, and
  the id `disclosure-004` is **not reused** in the pack, so that no reader joining
  the two files concludes the reserved case was quietly filled.

## Decision 5 — the claim, the bands, and the rules written before the run

### 1. The claim and its falsifiers

**A rule delta disposed by its owning seat into an executable control makes the
deployed service fail a gate for a reason a reader can trace from the rule to the
failing assert; and the fix, made where the rule points, makes it pass, with
nothing else moving.** Measured on the real path — the same deployed gateway and
the same guardrail versions M08b read — never on a stand-in.

Falsifiers, any one of which fails the claim:

- **F1 — any disclosure case passes before the fix.** The delta was not a delta;
  the control was already satisfied, which is the rule file's own recorded
  hazard.
- **F2 — any disclosure case fails after the fix.** The fix, made where the rule
  points, did not make it pass.
- **F3 — the gate does not block on the pre-fix verdict, or does block on the
  post-fix one.** `pave.gate decide` must exit **1** on the first and **0** on the
  second. A claim about a gate that is never run against the gate is prose.
- **F4 — the fix moved something else.** The goldens control run shows a ≤3-call
  answered sample over 7700 that was under it at M08b, or the goldens majority
  count lands outside the band in §3.

**A negative half, and it is not decoration.** The pack carries cases where a
disclosure is required and at least one where it is **not** — a factual
entitlement question carrying no AI-authored editorial copy. Without it, a fix
that emits a disclosure on every answer passes the whole pack, which is ADR-048
decision 3's sentence exactly: *"without the positive half the denial passes
against a policy set that denies everything, which is the PR #13 defect this
repository has now met in three places."* **F5 — the negative case carries a
disclosure after the fix** falsifies the claim as surely as F2.

**A red claim stops the claim's reading and nothing else.** ADR-074 amendment 1's
pre-registration, restated because the ambiguity it corrected is easy to
re-introduce: a falsified claim stops the reading at the measuring PR; the
remaining PRs proceed as planned, because dropping them re-dates their debts to
M09b's first PR, which is the pile decision 1 exists to refuse; and the milestone
closes red with the failing case named.

### 2. The prompt delta, measured before it is spent

The fix changes `TOOL_SYSTEM`, which is in **every** request of every arm. That
is the one way this milestone can break M08b's standing claim that 7700 holds per
sample, and it is measurable with no model call: the prompt is committed.

**Pre-registered, executed by a test and not approved in conversation:** the
disposition PR computes the added `tokens_in` cost of the prompt delta from the
committed prompt by the census's own estimator, and asserts
`M08b's ≤3-call maximum + delta < 7700`. M08b's published ≤3-call maximum is
**6782**, so the headroom is **918 tokens**. A delta that does not fit is a
finding about the fix before a single call is spent, and the fix is rewritten;
the ceiling does not move for it, on constraint 1.

### 3. Two bands, side-predictions and not the claim

Each is a finding about the side-prediction when it misses, never a failure of
the claim.

- **The goldens control count.** `N/25` with **8 ≤ N ≤ 12**, predicted **10**.
  Derived from M08b's measured 10 and nothing else: the band is 10 ± the two
  cases M08b itself moved on a one-sample margin (`entitlement-002` at 307 and
  `entitlement-011` at 308, against a tier of 300), which is the only movement
  this run has a reason to reproduce. Falsifiers of the side-prediction: N
  outside the band; a case that passed 3-of-3 at M08b failing by majority; a case
  that failed 0-of-3 at M08b passing by majority.
- **Refusals.** Refused by majority **0–2 of 25** on the goldens run — SPEC/01's
  band, at the ceiling M08b measured. Falsifier: 3 or more. On the disclosure
  pack, **0**: nothing about the guardrail moves in M09, and a refused disclosure
  question would be a new topic false positive, recorded as a finding for
  Security and handed to M09b rather than diagnosed here.

### 4. The `p95_ms` rule's failed premise, disposed by a condition a test evaluates

The debt as M08b handed it over: the mandated shape's own p95 went **3769 →
5241**, 41 ms over the 5200 ceiling derived from it, so **the rule's premise —
that the mandated shape's tail is stable across runs — is what failed**, and the
pooled reading no longer isolates any share.

Re-deriving by ADR-014's unchanged constants from the fresh population is the
obvious move and it is the one that must not be made blind. ADR-014 amendment 3
recorded the fact that made the last derivation survivable: *"The rule takes the
only population under which the run in view fails the gate."* M08b published
pooled **6633** and mandated-shape **5241**; a point re-derived from 5241 lands
above both, and the last published OVER reading would become *within*. **That is
a gate moved to clear a reading, which is the trade G9 exists to refuse.**

**Pre-registered, and executed by a test rather than settled here:**

> The suite `p95_ms` moves only if the point ADR-014's unchanged rule derives from
> the most recent fresh mandated-shape population **still leaves the run that
> population came from OVER the gate**. The disposition PR's test reads M08b's
> answered mandated-shape samples through `context_census.mandated_calls()`,
> computes p95, floor `1.15×`, roof `1.60×`, the midpoint and the point rounded to
> the nearest 100, and evaluates the condition. If it holds, the manifest moves to
> that point and **every record digesting the manifest is re-produced in the same
> diff** — `milestones/M08/context-census.json` and `milestones/M08b/fresh-join.json`
> both carry `services/highlights-agent/pave.manifest.yaml` in `inputs_sha256`. If
> it does not hold, **`p95_ms` stays 5200**, ADR-014's stability sentence is
> **withdrawn**, the gate is re-described as a fixed ceiling with a recorded
> derivation rather than as a share-of-population instrument, and the
> re-derivation is dated to the first milestone with a mandated-shape population
> not in view.

No number is written here, and the arithmetic is deliberately not performed in
this ADR: the population must be read from the answer files, not from a journal
sentence, which is the compression error this repository has paid for repeatedly.
**A disagreement between the test's number and any number quoted in prose is a
finding about the prose.**

### 5. Handed to M09b, pre-registered here so it is inherited rather than invented

**What count reads the `entitlement-circumvention` fix as having worked.** M08b
read the answer-channel question through its committed reader at **F = 2, G = 8**
— a topic question, the same reading M07's files give at F = 1, G = 8. The
recalibration M09b makes rides the guardrail line it deploys, and the reading is
taken by the same reader, unchanged:

> The fix worked iff **F = 0 with G ≥ 8** on a governed goldens run after the
> deploy — the topic stops refusing grants of the shape it refused, and no
> legitimate refusal is lost — **and every frozen corpus row that names the
> entitlement topic is still blocked 3 of 3**. F > 0 reads the fix as not having
> worked. A corpus row that stops blocking reads the fix as a **hole**, which is
> ADR-035's own shape and is the worse outcome of the two: it is the trade
> hypothesis 2 was refuted on at M06b, where a carve-out *"silently unblocked
> `ATK-002` and `ATK-004` — a security regression that read as a clarification."*

Written now, before the seat that wants the topic widened writes the change,
because that is what G9 is for.

## Decision 6 — the order of the debts, the cap, the spare, and the one pre-authorised slide

| when | debt | why there |
|---|---|---|
| **PR 1, this one** | the ADR; SPEC/09; rows 09b and 09c; `BUILD.md`, `SPEC/README.md`, the ADR index; `brand_tone` re-deferred to M09b in the same diff as the row; the demo script's Act 3 corrected | documents; nothing measurable moves |
| **before the run, seated** | the disclosure suite (cases, runner path, verdict, history enum, comparator pin); the goldens denominator pinned by name; `rules/schema.json`'s *no immortal rules*; *orphan rule* defined and checked; the p95 condition executed; `gateway_client.py` and `classify.py` on two-key rules; the prompt-delta test | each changes what the run records or what it is compared to, and none may change after it |
| **alone** | the DMA rename, with its own re-freeze | it moves `data/catalog.json` — the judge's `rendered_sha256` and two records' provenance digests — and the enum in the tool spec the census measures; beside anything else it is a ride-along on a two-key instrument |
| **the run** | the disposition; the scope text; run A; the fix; run B; the goldens control run; the entries; the registry lookup | measurements |
| **the close** | Act 3 recorded; the journal; step 6b; the row; the tag | |
| **never in M09** | the guardrail line; the topic recalibration; the probe re-run; `brand_tone`'s widening and re-freeze; the browse gap; the `tokens_out` tiers; a second brand; a judge axis wired | M09b's, 09c's, or decision 3's |

**The cap: six PRs. Five are planned and the sixth is a named spare.** The spare
is **PR 1b, a cold read of SPEC/09 by a reader who did not write it, before the
seated PR opens** — M08b's PR 1b shape, taken deliberately this time rather than
discovered. What that slot bought last milestone is the reason it is reserved:
two Definition-of-done clauses unreachable as written, three files that decide
the claim on no two-key rule, and a calibration call with no producer, all found
by running the checks the spec named rather than by reading it.

**The fallback, pre-registered by name.** If the cap is reached, the item that
gives way is **ADR-053's *no orphan rules* half**, re-dated to **M09b** by name in
the close's journal. It is chosen because it is the one inherited item that is a
definition problem before it is a build — ADR-053 says so itself: *"the term needs
defining first: the schema's own `description` uses a different sense from the
ref-resolution one"* — and because nothing about the claim depends on it. *No
immortal rules*, the schema change, does **not** give way. This is that debt's
second dated slide and the only one this milestone pre-authorises; **any other
slide is a finding.**

## The two standing questions, answered here

### 1. Is this becoming M06b again?

**Not on the dimension that broke M06b, and the split is the reason. Yes on one
clause, named below.**

| | M06b | M06c | M07 | M08b | SPEC/09 as written |
|---|---|---|---|---|---|
| PRs | 34, no bound that held | 3 of a cap of 6 | 6 of 6 | 6 of 6, spent at PR 1b | 5 planned of a cap of 6, **the sixth a named spare** |
| Controls moved | the topic, repeatedly | none | one (the guardrail's channel wiring) | none | **one** (the eval pack); the guardrail is M09b's |
| Spend events | one per hypothesis, four hypotheses | none | two staged runs | one | **three, one shape**: red, green, and the goldens control |
| When the answer was chosen | never; closed on a diagnosis | step 0, two PRs in | band pre-registered, read at PR 5 | claim, falsifiers, bands and four rules at PR 1 | claim, **five** falsifiers, two bands, the p95 condition and the prompt-delta test at PR 1; the M09b hand-off too |
| Re-measurement door | after every negative result | none | none | one, bounded | **one, bounded**: SPEC/07 constraint 9's INFRA rule, unchanged |
| What broke | the premise was unmeasurable on arrival; an unpriced investigation was adopted | the claim was unreachable by its own plan | the close found an owe the plan had not | the cap fell on a review of the plan | *see below* |

**What M06b did that SPEC/09 cannot.** M06b re-measured after every negative
result, because a diagnosis has no stopping rule. Here every falsifier closes the
milestone red with a named case; F1 in particular — *the service already
complied* — is the outcome that would most tempt an investigation, and it is
pre-registered as a **red close**, not as a hypothesis.

**Where it is M06c's shape, stated rather than discovered.** M06c's finding was
*"the claim was unreachable by its own plan"*, and the two DoD clauses M08b PR 1b
found were the same defect one field in. The candidate here is the **goldens
control run**: it forces a goldens history entry, and `pave/history.py::check_readme`
refuses a goldens entry whose README row is pinned to no entry — so the entry, the
`README_GOLDENS` row and the row's bold `N/25` must land in **one** PR, three PRs
before the ✅. Written into the Definition of done that way, so it is a checkbox
rather than a planned red.

**Where M07's close-finds-an-owe shape lands here, named now.** M07's close found
the `brand_tone` owe because flipping the row ran a check the plan had not read.
The two checks that fire on M09's row are `tests/test_calibration_owe.py` (the
`brand_tone` target, which **this PR** moves to M09b in the same diff as the row —
its fourth counted re-deferral) and `tests/test_demo_recordings.py` (act 3, which
decision 1 keeps in M09 for that reason). Both are read before the plan, not at
the close.

### 2. Each claim, the measurement that proves it, and the PR

Claims with no measurement are **cut**, not carried. Three were, and they are
named under the table.

| # | claim | measurement | PR |
|---|---|---|---|
| 1 | **The one claim**: the disposed rule makes the deployed service fail the gate, and the fix makes it pass, with nothing else moving | the two disclosure runs through the deployed gateway at k=3; `pave.gate decide` over each run's verdict, exit 1 then exit 0; the goldens control run against F4 | the run PR |
| 1a | …traceable from the rule to the failing assert | the disclosure record names the rule id, the control ref and the failing assert, and a reader test walks `rules/MER-AI-0001.yaml` → the control ref → the case → the assert with no step supplied by hand | seated PR (the reader), the run PR (the record) |
| 1b | …on the real path, at the deployment M08b read | the pre-flight header: the deployed function, both guardrail versions, bundle digests equal to the tree; the audit record ids | the run PR |
| 1c | …with nothing else moving | `git diff` over the guardrail, the policy, the corpus, the catalog, the tiers and the topics between PR 1's merge and the run's branch point, empty — **except** `data/catalog.json`, which the DMA rename moves in its own PR before the run, and the system prompt, which **is** the fix | the run PR, with the rename's PR named |
| 2 | F1: no disclosure case passes before the fix | run A's per-case verdicts | the run PR |
| 3 | F2 and F5: every positive case passes and the negative case carries no disclosure after the fix | run B's per-case verdicts | the run PR |
| 4 | F4: the goldens claim of 7700 per sample survives the prompt delta | the goldens control run joined to `usage.calls`, read by M08b's committed `fresh_join.py` against the same ceiling | the run PR |
| 5 | The prompt delta fits the headroom **before** any call | a test over the committed prompt by the census estimator: `6782 + delta < 7700` | seated PR |
| 6 | The goldens count in [8, 12] | `goldens-score.txt`; the per-case table against M08b's | the run PR |
| 7 | Refusals 0–2 on the goldens run, 0 on the disclosure pack | `evals.refusals --sidecar` | the run PR |
| 8 | The goldens denominator is 25 and the pack is not in it | a test that counts the golden file's cases and refuses a disclosure-prefixed id in it | seated PR |
| 9 | `disclosure-004`'s reservation withdrawn by name, the id unused | a test that the golden file and its README carry no reservation sentence and no `disclosure-004` | seated PR |
| 10 | The gate reads a disclosure verdict and blocks | `pave.gate decide` over a planted FAIL verdict with `suite: "disclosure"`, exit 1 | seated PR |
| 11 | The disclosure entry is recordable and pinned | `pave gate history` over the entry; the suite enum plant | seated PR (enum), the run PR (entries) |
| 12 | The goldens entry, its `README_GOLDENS` row and the bold `N/25`, in one PR | `pave gate history`; `check_readme` | the run PR |
| 13 | *No immortal rules*: a rule omitting `source.effective` is refused | `rules/schema.json` requires it; the plant ADR-053 measured (`effective` deleted, `status: enforced`, `review_by: 2099-01-01`) is red by name | seated PR |
| 14 | *No orphan rules*: the term defined, and the check reads that definition | the definition written in the schema's `description` and in the check's docstring, and a plant per sense | seated PR |
| 15 | The p95 condition evaluated, and the manifest at whatever it yields | the derivation test: population, p95, floor, roof, midpoint, point, the condition's outcome; every constant planted red; if it moves, both records re-produced | seated PR |
| 16 | `gateway_client.py` and `classify.py` on two-key rules | the `pave/twokey.py` plant per rule | seated PR |
| 17 | The DMA rename moves every digest it must and nothing else | each reader re-produces its record; the judge re-frozen; the key-by-key diff | the rename's PR, alone |
| 18 | `brand_tone` re-deferred to M09b in the same diff as the row, counted as the fourth | `tests/test_calibration_owe.py` green with `M09b` present in the table; `deferred_from` arithmetic | **PR 1** |
| 19 | Act 3 recorded before the row is flipped | `tests/test_demo_recordings.py` green with `recorded` set | the close |
| 20 | Zero model calls outside the run PR | the PR bodies; no file carrying `usage` outside it | every PR |
| 21 | Citations resolve from `main` or a tag | `tests/test_cited_commits_resolve.py`, run over each PR's text **before** it merges | every PR |
| 22 | The deletability audit on every check added | the PR body names each check and whether it went red when deleted | every PR |

**Cut, because nothing measures them.**

- ***"The registry links law → rule → control → dashboard panel in one lookup."***
  The `dashboards/` directory contains a `README.md` and nothing else. The
  **lookup** is measurable — row 1a's reader test walks the chain — and it is
  kept. The **panel** is not, and building the repository's first dashboard inside
  the milestone that proves claim 6 is decision 1's own argument turned on its
  author. **Cut to M09b**, named, and Act 3's script says so.
- ***"The regdelta loop."*** As inherited it names no artifact and no
  measurement; every measurable thing in it is row 1 or row 1a. The phrase is
  dropped from M09's claim rather than carried as a word nothing reads.
- ***"A seat round on the guardrail."*** M09 moves no guardrail. It is M09b's,
  and it is decision 1.

## What this ADR does not decide

- Any number the run produces. The run PR fills them into decision 5's sentences.
- The `p95_ms` point. Decision 5 §4 writes the condition; the test computes.
- The topic recalibration's wording, or the guardrail line's text. Security's,
  in M09b, with its own ADR — ADR-064's two refuted calibrations are the bar.
- What claim, if any, `09c` carries. Its own spec's.
- Whether `quality/judge/rubric-sports.md`'s `disclosure_present` axis is retired
  or wired. M09b's, beside its re-freeze.
- The browse gap and the `tokens_out` tiers. `09c` owns both; decision 2
  schedules the row and not the fix, on ADR-074 decision 2's reasoning that a
  repair scheduled against a defect is *"a remedy built against the plant you were
  shown"* until it is re-measured.

## Consequences

- The progression table has sixteen rows through M12 and every reference below
  row 09 is unchanged; the seven `M10` code and template sites stay correct as
  written for the fourth milestone running.
- Claim 6 is proven, or falsified, on one control — so a red is attributable to
  the disposition and to nothing else, which is the property the split bought.
- The repository gains a second scoring suite, and the twenty-five goldens stop
  being the only place a case can live. The denominator is pinned by name rather
  than by everyone remembering.
- `rules/` stops being able to hold an immortal rule, and *orphan rule* stops
  meaning two things.
- Answer quality has a row and a date for the first time since M07 cleared the
  refusals, and the two `M10`s are separated in the one document a reader is sent
  to for what is scheduled.

**At scale, replace with X; the interface already matches.** A policy service
holding the rule registry, where a status transition is an API call carrying its
approver rather than a file edit carrying an attestation, and where a disposition
emits its controls into the eval plane as a matter of course — the registry is
already typed records with a schema, the disposition already names typed controls
with layers, and the suite the controls land in is already one wrapper with many
readers. The seat list here and the reviewer list there are the same list.

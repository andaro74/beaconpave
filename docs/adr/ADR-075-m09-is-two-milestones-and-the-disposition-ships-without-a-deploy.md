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

## Amendment 1 — a cold read of SPEC/09 before PR 2, five questions answered

**Written 2026-09-09, after PR 1 was committed and before PR 2 is cut.** PR 1 was
unopened when this was written and squash-merged as **`66bb114`** (#134) while it
was in flight; the trees are identical, so every number below is unmoved and the
merge commit is what they are cited against. Zero model calls; no deploy; no seat round.** The reader
did not write SPEC/09 or ADR-075. Nothing in the plan is changed by this
amendment; it names what PR 2, PR 3 and the spec must change, and the operator
disposes.

**Operator's disposition, 2026-09-09: accepted in full, all eleven asks.**
Committed in this PR — PR 1b — before PR 2 cuts from `main`, with the SPEC/09
corrections it names **in the same diff**, which is the Definition of done's own
PR 1b box and ADR-074 amendment 1's precedent: a Definition of done corrected
after its PR prints is a checkbox rewritten to match the outcome. The two asks
that are decisions rather than corrections were taken as written. **Ask 5**: the
goldens control run, its entry, its `README_GOLDENS` row and row 09's `N/25` move
to **PR 4b**, with PRs 4 and 5 keeping their numbers. **Ask 6**: **PR 3 is
vacated**, the DMA rename re-dates to **`09c`** by name with its own ADR and
re-scoped as a change to the system under measurement, and the slide is recorded
as **a finding** in the close's journal, since this milestone pre-authorised only
ADR-053's. **This PR is the milestone's sixth slot spent, and the cap's
pre-registered fallback fires on it** (§6): ADR-053's *no orphan rules* half gives
way to M09b by name, and there is no PR 3.

**What landed where, because the split is not arbitrary.** Asks 1, 2, 3, 5 and 6
and the Definition-of-done half of ask 4 are **spec text** and land here: they
change what PR 2 and PR 4 are measured against, and a plan corrected inside the
PR it governs is the defect this reading exists to catch. Asks 7 through 11 and
the build half of ask 4 are **work**, and land in the PR that does it — PR 2 for
the decision record, the two-key widening, the schema description and the seat
brief; PR 4 for the three pins the fix moves; PR 4b for the comparator pin and
its lane. SPEC/09 now names each by its PR.

Every number below is produced by running committed code over committed
evidence, never read out of a journal sentence: `milestones/M08b/goldens-run-{1,2,3}.json`,
`milestones/M08/context_census.py`, `milestones/M08b/fresh_join.py`,
`evals/deterministic.py`, `pave/twokey.py`, `pave/gate.py`, `pave/history.py`,
`pave/cli.py`, `quality/verdicts/schema.json`, `evals/history/schema.json`,
`rules/schema.json`, `evals/comparators.json`,
`services/highlights-agent/gateway_client.py`,
`services/highlights-agent/evals/answer.schema.json`,
`tools/entitlement-check/schema.in.json` and `tests/test_gateway_run_parity.py`.
Baseline for every plant below: `python -m pytest -q` at `66bb114` is
**3993 passed, 6 skipped**. Each plant was written to a working copy backed up to
a temp directory, restored from that backup and **never with `git checkout`**, and
`git status --porcelain` was empty after each.

Ten facts this reading established by running the code. Each is a check a seat can
repeat, and the answers below turn on them.

1. **The `p95_ms` condition does not fire, under any population.** Read from
   M08b's three answer files through `context_census.mandated_calls()` and
   `evals.deterministic.suite_latency` — the scorer's own percentile, so the test
   and the gate cannot disagree about what a p95 is:

   | population | n | p95 | floor 1.15× | roof 1.60× | midpoint | point |
   |---|---|---|---|---|---|---|
   | mandated shape (**the rule**) | 38 | **5241** | 6027.15 | 8385.60 | 7206.375 | **7200** |
   | as-run ≤3 call | 58 | 5683 | 6535.45 | 9092.80 | 7814.125 | 7800 |
   | pooled | 70 | **6633** | 7627.95 | 10612.80 | 9120.375 | 9100 |
   | above mandate | 32 | 7223 | 8306.45 | 11556.80 | 9931.625 | 9900 |
   | ≥4 call | 12 | 8437 | 9702.55 | 13499.20 | 11600.875 | 11600 |

   n = 38 at 5241 and n = 70 at 6633 reproduce amendment 3 of ADR-074 exactly, so
   the population is the one M08b read. **The condition holds under none of the
   five**, and §4 shows it cannot hold under any population at all.
2. **The prompt-delta assert is wrong by the call count.** `usage.tokens_in` is
   the **sum across calls** — checked on all 70 answered M08b samples, total
   equals sum of `usage.calls[].tokens_in` in 70 of 70 — and the published ≤3-call
   maximum 6782 is `headroom-005` sample 3 at **three** calls. The system block is
   re-sent every round, so a delta of *d* tokens lands *n* times in an *n*-call
   sample. `6782 + delta < 7700` admits **delta ≤ 917**; the bound the claim
   actually needs is `6782 + 3·delta ≤ 7700`, **delta ≤ 306**. A 400-token fix
   passes the spec's test and puts `headroom-005` at **7982** — the F4 event the
   test exists to prevent before a call is spent.
3. **The fix goes red on three committed checks and SPEC/09 names none of them.**
   Planted: one disclosure sentence into `TOOL_SYSTEM`. Red —
   `test_the_m02_prompt_is_hash_pinned` (`TOOL_SYSTEM_SHA256`, whose own docstring
   calls updating it *"an ADR-021 event: say so in the progression row, and do not
   do it between the two arms of one comparison"*);
   `test_the_m02_prompt_is_the_control_prompt_minus_the_catalog_and_nothing_else`,
   whose `only_tool` multiset must equal exactly the one forced line; and
   `tests/test_m08_census.py::test_the_record_is_what_the_committed_inputs_produce`,
   because `milestones/M08/context-census.json` digests
   `services/highlights-agent/gateway_client.py`. `tests/test_gateway_run_parity.py`
   is `(platform-eng, security)` and the census record is three keys, so **PR 4
   edits the attribution pin and the census record in the same PR as the runs they
   protect.** Neither file appears anywhere in SPEC/09.
4. **The DMA rename cannot land in M09.** Planted the minimum consistent rename —
   `cedar-point` → `elmridge` across `data/catalog.json`,
   `tools/entitlement-check/schema.in.json`,
   `platform/gateway/policy/tools.contracts.json` and
   `services/highlights-agent/evals/golden/cases.yaml`, which is the smallest set
   that leaves the enum, the contract and the values the cases send agreeing.
   Result: `context_census.py --check` **DRIFT**; `TOOL_SPECS_SHA256` red;
   `test_the_prompt_half_is_untouched_by_the_amendment` (ADR-056) red;
   `test_poisoned_catalog_differs_from_the_clean_one_only_as_intended` red;
   `test_a_directory_from_an_unrecorded_instrument_is_refused_by_the_scoring_path`
   red. And the one that decides it: **`fresh_join.py --check` refuses M08b's own
   committed run** — *"edge-024 sample 1: trajectory step 2 carries args
   entitlement-check's contract refuses"*. The rename retroactively invalidates
   committed evidence against the live contract, and the evidence it invalidates
   is the run F4 compares against.
5. **`pave.twokey.triggered` over PR 2's file list as the spec names it: 13 rules,
   all five enforced seats, five files on no rule.** `pave/cli.py` and
   `pave/rules.py` — the chain reader, which is the whole of row 1a — match **no
   rule**; so do `tests/test_m09_disclosure.py` and `tests/test_rules_trace.py`,
   its pins. The census rule names `milestones/M08/`, `milestones/M08b/` and
   `tests/test_m08b_*` **by name**; there is no `M09` clause and no
   `tests/test_m09_*` clause. This is ADR-074 amendment 1 fact 3 arriving one
   milestone later at the file that decides *traceable*.
6. **Over PR 4's file list: 5 rules, seven files on no rule** — including
   `milestones/M09/verdict-pre-fix.json`, `verdict-post-fix.json` and the run-A
   answer files, which are the evidence F1, F2, F3 and F5 are read from. The
   goldens-run rule is `^milestones/.*/(goldens-run[^/]*\.json|runs/[^/]+\.json)$`
   and catches the control run only; nothing catches a disclosure run or a
   verdict. `services/highlights-agent/gateway_client.py` matching no rule is the
   spec's own debt row and is dated to PR 2 correctly.
7. **PR 2 owes a decision record and SPEC/09 gives it none.** `rules/schema.json`
   puts PR 2 under `^rules/`, which is `(legal-sp, security)` with
   `requires_adr=True`, and `adr_records` reads the **diff**, not the body: the PR
   must add at least six distinct substantive words to a `docs/adr/ADR-NNN-*.md`
   file in its own diff. ADR-075 is amended by PR 1, by this PR and by PR 4.
   PR 2's two-key job is red as planned.
8. **The disclosure comparator pin has no reader and nothing to pin.**
   `pave/cli.py` calls `_suite_pin(pinned, service, "goldens")` and
   `_suite_pin(…, "adversarial")` — two literals, no generic suite lane. And a
   comparator is *what committed runs score today*; there are no committed
   disclosure runs until PR 4. A pin added at PR 2 pins nothing and is read by
   nothing, which is ADR-048's T1 in a new place.
9. **`ai_disclosure` is not `required`, and its description is model-facing.**
   `answer.schema.json` types it `["string","null"]` and omits it from `required`,
   so an answer that never emits the key validates. The same file is rendered into
   the prompt through `TOOL_SYSTEM`'s `{schema}`, so its description — *"Null until
   M07 disposes that rule"* — is **text the model reads, telling it to leave the
   field null**. It is a third stale-M07 site and the only one the model sees; the
   spec withdraws the other two and not this one. F1's premise is sound on the
   evidence: 56 committed M08b samples carry the key and **none** is non-null.
10. **The gate confirms decision 4 and the count contradicts itself.**
    `pave/gate.py` never enumerates suites, `NON_BLOCKING` is `{PASS, ADVISORY}`,
    FAIL → `EXIT_QUALITY` = 1; `quality/verdicts/schema.json` types `suite` as a
    free string and `layer` enumerates `L3`; `evals/history/schema.json`'s enum is
    `[goldens, adversarial, contract, playwright, k6, drill]`. Rows 4, 10 and 11
    are reachable as written. But **F4 says a goldens count outside [8, 12]
    falsifies the claim**, while *Beside the claim, and not it* and the PR 4
    Definition-of-done box both say a band miss *"is a finding about the
    side-prediction and does not fail this box's first item"*. Three sites, two
    answers, about the sentence that decides whether the milestone closes red.

### 1. Is this becoming M06b again?

**Not on the dimension that broke M06b, and ADR-075's own answer to this question
is right about that. It is M06c's shape in four places rather than the one the ADR
found, and it carries exactly one M06b entry point: PR 3.**

| | M06b | M06c | M07 | M08b | SPEC/09 as written | SPEC/09 as measured here |
|---|---|---|---|---|---|---|
| PRs | 34, no bound that held | 3 of a cap of 6 | 6 of 6 | 6 of 6, spent at PR 1b | 5 planned of a cap of 6, sixth a named spare | **6 spent at this PR**, and one of the five cannot land (fact 4) |
| Controls moved | the topic, repeatedly | none | one | none | **one** — the eval pack | **three**: the eval pack, the **prompt** (an ADR-021 lineage event, fact 3), and the **market vocabulary** (PR 3, fact 4) |
| Spend events | one per hypothesis, four hypotheses | none | two staged runs | one | three, one shape | three, one shape — unchanged and correct |
| When the answer was chosen | never | step 0, two PRs in | pre-registered, read at PR 5 | at PR 1 | claim, five falsifiers, two bands, two rules at PR 1 | unchanged, **except** the count, which is pre-registered twice with opposite consequences (fact 10) |
| Re-measurement door | after every negative result | none | none | one, bounded | one, bounded — SPEC/07 constraint 9 | unchanged and correct |
| What broke | premise unmeasurable on arrival; an unpriced investigation adopted | the claim was unreachable by its own plan | the close found an owe the plan had not | the cap fell on a review of the plan | *see below* | *four unreachable clauses, one impossible PR* |

**What M06b did that SPEC/09 still cannot.** M06b re-measured after every negative
result because a diagnosis has no stopping rule. Every falsifier here closes the
milestone red with a named case, F1 included; constraint 9 opens exactly one
bounded door; no diagnosis is authorised anywhere. That structure is intact and
this reading does not disturb it.

**The one M06b entry point in the plan is PR 3.** A rename that goes red on
*committed evidence* (fact 4) has no bounded next step. The three available moves
are: re-produce the trajectory records of nine milestones, edit committed
evidence, or slide the debt. The first two are unpriced work discovered
mid-milestone with no cap slot behind it — *"an investigation the milestone did
not plan and should probably not have adopted"*, in the M06b journal's own words —
and the third is a slide the spec calls a finding. §6 takes the third and records
it as the finding it is, before the PR rather than at the close.

**Where it is M06c's shape.** ADR-075 names one candidate — the goldens entry and
its `README_GOLDENS` row — and is right about it, and it is already a checkbox
rather than a planned red. There are four more, each a Definition-of-done clause
the plan beneath it cannot reach:

- *"Nothing under `milestones/M08/` changed but `context-census.json`'s manifest
  digest line, and only if the `p95_ms` condition moved the manifest."* The
  condition does **not** move the manifest (fact 1), so the clause reads *nothing
  under `milestones/M08/` changed* — and the fix moves that record in PR 4 (fact 3)
  and the rename moves it in PR 3 (fact 4). This is ADR-074 amendment 1 fact 1
  exactly, one milestone on and one input over.
- *"Nothing under `milestones/M07/` or `milestones/M08b/` changed."*
  `milestones/M08b/fresh-join.json` digests `data/catalog.json`,
  `platform/gateway/policy/tools.contracts.json`, the golden cases file and
  `context-census.json`. PR 3 moves four of its inputs; the clause is unreachable
  in PR 3 whatever else happens.
- *PR 2's comparator pin.* Nothing reads it and there is nothing to pin (fact 8).
- *PR 2's attestations "wherever `pave/twokey.py` demands them".* It demands a
  decision record PR 2 does not write (fact 7).

**Where M07's close-finds-an-owe shape lands.** ADR-075 reads the two checks that
fire on row 09 — `test_calibration_owe.py` and `test_demo_recordings.py` — before
the plan rather than at the close, and both are green here. The owe the plan has
not read is one PR earlier than M07's: **PR 3 and PR 4 each open red on a check
that exists today**, and both were findable by running the checks the spec names
rather than reading it. That is the whole content of the slot this PR spends.

### 2. Each claim, its measurement, and the PR

Read beside SPEC/09's own 22-row table. Where a row is reachable as written it
says so and adds nothing; the rows that matter are the ones that are not.

| # | claim | measurement | PR | status |
|---|---|---|---|---|
| 1 | the disposed rule makes the service fail the gate and the fix makes it pass, nothing else moving | the two disclosure runs at k=3; `pave gate decide` exit 1 then 0; the goldens control run against F4 | PR 4 | **reachable for the red→green half; the *nothing else moving* half is not** — its comparator is M08b, and PR 3 moves four of the inputs both records digest (facts 4, 10 of ADR-074 A1's shape). §3 |
| 1a | …traceable from the rule to the failing assert | the chain reader walks rule → `controls[].ref` → case → assert; a planted broken ref is red | PR 2, PR 4 | reachable. **The reader is on no two-key rule** (fact 5); it decides what *traceable* means and is editable on one key |
| 1b | …on the real path, at the deployment M08b read | the pre-flight header; bundle digests equal to the tree at PR 2's merge | PR 4 | reachable, and the caller-side fix is checked, not assumed — `handler.py` receives `system` in the event |
| 1c | …with nothing else moving | `git diff` over guardrail, policy, corpus, tiers, topics empty; catalog only in PR 3; the prompt only in PR 4 | PR 4 | **not reachable as written.** `platform/gateway/policy/tools.contracts.json` is inside the named paths and PR 3 moves it (fact 4). Either the carve-out names it or the clause is false the day PR 3 merges — the same defect ADR-074 amendment 1 row 1c found in SPEC/08b's claim sentence |
| 2 | F1 — no disclosure case passes before the fix | run A's per-case verdicts | PR 4 | reachable, and the premise is sound on committed evidence (fact 9) |
| 3 | F2, F5 — every positive passes, the negative does not disclose after the fix | run B's per-case verdicts | PR 4 | reachable. The negative half's assert must test key **presence**, not truthiness: `ai_disclosure` is not `required` (fact 9), so an absence assert is satisfied by a model that never emitted the key at all — the vacuity plant constraint 7 already names, with the schema fact behind it |
| 4 | F3 — the gate blocks then permits | the two transcripts and exit codes | PR 4 | **reachable, verified**: `_inspect` never enumerates suites, FAIL → exit 1, PASS → exit 0 (fact 10) |
| 5 | F4 — the 7700 per-sample claim survives the prompt delta | the goldens control run read at the same ceiling by M08b's reader | PR 4 | **reachable only if PR 3 does not land.** With the rename in, an F4 miss is attributable to the sentence or to the market vocabulary and to nothing in particular. §3 |
| 6 | the prompt delta fits the headroom before any call | `6782 + delta < 7700` by the census estimator | PR 2 | **the test is wrong by the call count** (fact 2). It admits a delta three times the one the claim can survive |
| 7 | the count in [8, 12]; refusals 0–2 and 0 | the score transcript; `evals.refusals --sidecar` | PR 4 | reachable. **The count's consequence is pre-registered twice, oppositely** (fact 10) |
| 8 | the goldens denominator is 25, the pack is not in it | a test counting cases; a planted disclosure id red by name | PR 2 | reachable; the file holds exactly 25 cases today |
| 9 | `disclosure-004`'s reservation withdrawn, the id unused | a test over both files | PR 2 | reachable. **A third site is missed**: `answer.schema.json`'s *"Null until M07 disposes that rule"*, which is the one the model reads (fact 9) |
| 10 | the gate reads a disclosure verdict and blocks | planted FAIL verdict with `suite: "disclosure"`, exit 1 | PR 2 | **reachable, verified** (fact 10) |
| 11 | the disclosure entry is recordable and pinned | `pave gate history`; the enum plant | PR 2, PR 4 | the enum half is reachable. **The pin half is not** (fact 8): no lane reads a disclosure comparator and no committed run exists to pin at PR 2 |
| 12 | the goldens entry, its row and the bold `N/25` in one PR | `check_readme` | PR 4 | reachable; ADR-075 found this and made it a checkbox. Confirmed: `tagged` is `suite == "goldens"` only |
| 13 | *no immortal rules* | `rules/schema.json` requires `source.effective`; ADR-053's plant red by name | PR 2 | reachable; `effective` is optional today, exactly as ADR-053 recorded |
| 14 | *no orphan rules*, one sense | the definition in schema and docstring; a plant per sense | PR 2 | reachable, and it is the pre-authorised fallback (§6) |
| 15 | the `p95_ms` condition evaluated, the manifest at what it yields | the derivation test | PR 2 | **reachable, and the answer is computed here: the gate does not move** (fact 1, §4). Two consequences the spec does not carry — the `context_census.py` `sys.path` debt is dated *"PR 2, if the p95 condition yields a move"* and therefore becomes undated; and `test_the_suite_p95_ceiling_is_the_number_the_rule_produces_from_the_mandated_shape`, which asserts 5200 from M07's population and `gates.p95_ms == produced`, stays green rather than needing replacement |
| 16 | `gateway_client.py` and `classify.py` on two-key rules | a `_blocked_for` plant per rule | PR 2 | reachable and correctly dated before PR 4 edits the first. `classify.py` matches no rule today (fact 5) |
| 17 | the DMA rename moves every digest it must and nothing else | each reader re-produces its record; the judge re-frozen | PR 3 | **not reachable in this milestone at all** (fact 4). §6 |
| 18 | `brand_tone` re-deferred to M09b as the fourth | `test_calibration_owe.py` green with row 09b | PR 1 | **green, checked**: 256 passed over the five named tests at `66bb114` |
| 19 | Act 3 recorded before the row is flipped | `test_demo_recordings.py` green with `recorded` set | PR 5 | green today with the act unrecorded; reachable |
| 20 | zero model calls outside PR 4; PR 4 within 180 turns | the PR bodies; no `usage` under `milestones/M09/` outside PR 4 | every PR | reachable; PR 2's planted answers under `tests/` is the right precaution, inherited from M08b row 22 |
| 21 | citations resolve from `main` or a tag | `test_cited_commits_resolve.py` before merge | every PR | green today, and §6 records the one correction the rule forced on this text before it merged |
| 22 | the deletability audit | the PR body names each check and its result | every PR | reachable |
| — | **the prompt is the system under measurement** | `TOOL_SYSTEM_SHA256` and the line-by-line assert in `tests/test_gateway_run_parity.py` | **no PR** | **a claim with no row.** The fix moves the M02 lineage pin and the pin is on two keys the plan does not collect (fact 3). It is not optional: PR 4 cannot merge without editing that file |
| — | **the census record is what the committed inputs produce** | `tests/test_m08_census.py` | **no PR** | **a claim with no row.** The census digests the prompt, the catalog, the contract set, the cases file and the manifest; PR 3 moves four and PR 4 moves one (facts 3, 4) |

**Three claims have no measurement in any PR of this plan**, and none of them is
one of the three ADR-075 cut. Two are in the table above. The third is the
*nothing else moving* half of the one claim: as scheduled, F4's control run is
compared to a run taken before a market rename, so no PR of this plan measures it
against a system that differs by the fix alone.

### 3. Is PR 4 M07 PR 4's shape with a run added?

**It is M07 PR 4's shape with two runs added, a two-key disposition, and three
pins the plan does not name. And the attribution weakness is real — but it is not
where the question puts it.**

M07 PR 4 carried five decisions on five subjects: a run, a probe suite, step 6b, a
two-key disposition, and a new two-key rule created in the diff. ADR-074 §3 read
that shape and named the fix: *"the split moved the zero-call, deadline-bound ones
to the PR already collecting their keys."* PR 4 here carries: run A; a gate
transcript; the fix; run B; a second gate transcript; the goldens control run; its
history entry, its `README_GOLDENS` row and row 09's bold `N/25`; the rule's
disposition on two keys with an ADR; the rule's scope text; the chain reader over
the real record; five falsifiers read; two bands; two refusal readings; an ADR
amendment — **plus** `TOOL_SYSTEM_SHA256`, the line-by-line prompt assert and
`milestones/M08/context-census.json`, which are forced and unlisted (fact 3).
Thirteen listed subjects and three unlisted ones, against M07's five.

**Does mixing F4's control run into the PR where A and B are read weaken the
attribution?** Not between A and B. That pair is the strongest attribution in the
plan: same deployment, same guardrail versions, same day, one sentence apart, and
the gate run over each. Packaging them together is what *makes* the red→green
attributable, and separating them would be the M06c defect of splitting one job
because half of it is cheaper.

**The weakness is that F4's control run has no twin in this milestone.** Its
comparator is M08b's run, one milestone away, and PR 3 moves four of the inputs
that both the census record and the fresh join digest (fact 4) — the market
vocabulary the model reads in the viewer turn, in the tool spec enum and in the
tool results. So an F4 miss after PR 3 is attributable to the disclosure sentence
or to the rename, and claim 6's whole content is that a reader can trace a red to
the rule. This is ADR-075 decision 1's own argument — *a red after a disposition
and a new guardrail line is unattributable between the two controls* — arriving
one level further in, at a control the ADR did not count as one. SPEC/09
constraint 4 states the fact and draws the wrong conclusion from it: *"before the
run it confounds every comparison to M08b"* is a reason the rename must be **after
the run or out of the milestone**, not a reason it must be alone.

**What should move, and what it costs the cap.**

- **The goldens control run, its entry, its `README_GOLDENS` row and row 09's
  `N/25` move to their own PR after the fix — call it PR 4b**, on M08b's
  numbering precedent so that every "PR 4" and "PR 5" reference in SPEC/09 stays
  valid. Its keys are already its own: `^evals/history/` at three seats and
  `^milestones/.*/goldens-run*.json` at two, neither of which PR 4 needs
  otherwise. It cannot precede the fix, so this is a split forward, not a
  re-ordering. What it buys: F4 is read in a PR that is about F4, and the
  `check_readme` coupling ADR-075 turned into a checkbox stays in one diff.
- **`TOOL_SYSTEM_SHA256`, the line-by-line assert and the census record's
  re-production go with the fix**, in PR 4, because they *are* the fix's diff.
  They cannot move earlier: the pin cannot be updated before the prompt it pins
  moves. What PR 4 owes is naming them, collecting `(platform-eng, security)` for
  the parity file and the census rule's three keys, and recording the prompt move
  in the progression row, which the pin's own docstring calls an ADR-021 event.
- **It costs the cap nothing**, because PR 3 vacates a slot (§6). The six become
  PR 1, PR 1b, PR 2, PR 4, PR 4b and PR 5, and there is no PR 3 — which is
  ADR-074 amendment 1 §6's shape exactly.

### 4. Which population does PR 2's `p95_ms` condition execute over?

**The population is M08b's 38 answered mandated-shape samples, and the condition
does not hold — not on that population and not on any other. `gates.budgets.p95_ms`
stays 5200, ADR-014's stability sentence is withdrawn, and the re-derivation dates
to the first milestone with a mandated-shape population not in view.** The table
of populations, computed rather than quoted, is fact 1 above.

**The condition cannot hold on its own population, and that is arithmetic rather
than an outcome.** The point is the midpoint of `[1.15·p95, 1.60·p95]`, which is
`1.375·p95` rounded — strictly above the p95 it came from. So the run that
population came from can never read OVER the point derived from it. Read that way
the condition is unsatisfiable by construction, and a rule that cannot fire is not
a rule.

The condition is only meaningful under the other reading: *the run reads OVER* means
the number the gate actually prints, which is `suite_latency` over the whole run —
the **pooled** p95, the one in `suite latency OVER p95=6633ms over 5200ms`. Under
that reading the condition is real and says something worth saying: the gate may
move only if `pooled > 1.375 × mandated`. Here 6633 against 7206.375, so it does
not hold. **Both readings give the same answer on this data, and the spec should
still say which one it means**, because the reason differs and the reason is what
the next milestone inherits.

**The populations not taken, and what each yields** — as ADR-074 amendment 1 §4
did, so a seat can see that the one taken is not the flattering one:

| population | p95 | band | point | M08b's pooled 6633 reads | M08b's mandated 5241 reads |
|---|---|---|---|---|---|
| mandated shape, n = 38 (**the rule**) | 5241 | 6027–8385 | **7200** | within | within |
| as-run ≤3 call, n = 58 | 5683 | 6535–9092 | 7800 | within | within |
| pooled, n = 70 | 6633 | 7628–10612 | 9100 | within | within |
| above mandate, n = 32 | 7223 | 8306–11556 | 9900 | within | within |
| ≥4 call, n = 12 | 8437 | 9702–13499 | 11600 | within | within |

At M07 the rule took *"the only population under which the run in view fails the
gate"*, and that was the fact that made an in-view derivation survivable. **Here
there is no such population.** That is the finding, and it is stronger than the
condition's outcome: the rule's own selection criterion has no solution on this
data, which is what a failed premise looks like when you try to re-apply the rule
that rested on it. It belongs in ADR-014 amendment 3's withdrawal beside the
stability sentence.

**Should the gate move in PR 2 at all before M09's own fresh population exists?**
**No, and the condition's answer makes that concrete rather than cautious.**
ADR-074 amendment 1 §4 put the move at PR 2 because *"PR 2 is the last PR at which
the fresh number does not exist"*, and that reasoning was right for a rule written
one PR earlier against a population two milestones old. It does not transfer.
Three differences:

1. **The number the gate would be applied to is one PR away, not one milestone.**
   M09's goldens control run produces a fresh mandated-shape population inside
   this milestone. Moving the gate in PR 2 on M08b's population and then reading
   M09's run against it is the same in-view hazard ADR-073 amendment 1 refused,
   with a shorter fuse.
2. **The premise the derivation rests on is the one that failed.** ADR-014
   amendment 3 derives the point from the mandated shape *because that shape's
   tail is stable across runs*; M08b measured 3769 → 5241, 1.39×. A point derived
   from a population whose instability is the finding is a number with no argument
   behind it.
3. **A move would cost PR 2 two record re-productions on three keys each and buy
   nothing measurable.** With the condition failing, PR 2 re-produces neither
   `context-census.json` nor `fresh-join.json`, and the DoD's conditional clause
   resolves to its stricter branch — which is what makes facts 3 and 4 breaches
   rather than permitted moves.

So the recommendation is the spec's own second branch, taken deliberately: the
number stays, the sentence is withdrawn, the gate is re-described as a fixed
ceiling with a recorded derivation, and the re-derivation is dated to a milestone
whose mandated-shape population is not in view — which is **09c**, the first
scheduled milestone that both re-runs the goldens and does not read its own p95
against a number it just chose.

### 5. The fix: what F4 should guard, and whether the token bound measures it

**"One sentence in every request of every arm" is not what the fix is.**
`TOOL_SYSTEM` is the **tools** arm's prompt. The control arm sends `SYSTEM`
through `build_prompt`, and the baseline sends a byte-identical copy; both are
untouched by a `TOOL_SYSTEM` edit, and `test_the_control_arm_is_untouched_by_this_milestone`
holds. Nothing in M09 runs the control arm, so the sentence is harmless — but the
phrase is what makes the prompt-delta test look sufficient, and it should read
*every request of every run this milestone takes*. There is a variant that would
make the sentence true: putting the requirement in `answer.schema.json`'s
`ai_disclosure` description, which both prompts render through `{schema}`. It is
worth naming because it is where the stale *"Null until M07"* sentence already
lives (fact 9), and worth refusing here because it lands on one key
(`^services/[^/]+/evals/`, AI Quality alone) and would move the control arm's
prompt for the first time since M01.

**Should F4 guard direction?** **Yes, and the two direction falsifiers should move
into F4 rather than be added beside it.** F4's stated content is *the fix moved
something else*. `N` is a sum over 25 cases and is insensitive to compensating
movement: three cases newly failing and three newly passing leaves `N` exactly
where it was, inside the band, with six cases having moved on a prompt change. The
direction falsifiers — no 3-of-3 pass at M08b failing by majority, no 0-of-3 fail
passing by majority — are the per-case statements that detect it, and they are the
ones this repository has already learned to trust: at M08b the count moved 12 → 10
while **no** direction falsifier fired, and the journal's own conclusion was that
*"a k=3 majority on a one-sample margin is not a stable instrument for a two-case
prediction."* A band the milestone has recorded as unstable is doing claim-deciding
work, and two stable per-case predicates are doing side-prediction work. They are
the wrong way round.

That reallocation also resolves fact 10's contradiction rather than papering over
it, and it resolves it in the direction the evidence supports:

- **F4 becomes**: no ≤3-call answered sample over 7700 that was under it at M08b;
  **no case that passed 3-of-3 at M08b fails by majority; no case that failed
  0-of-3 at M08b passes by majority.**
- **The count `N` in [8, 12] becomes a side-prediction only**, as *Beside the
  claim, and not it* and the PR 4 Definition-of-done box already say twice. A miss
  is a finding about the band.

**Is the prompt-delta test the right measurement for a change whose effect is on
content?** **No, twice over — and the second is the one that matters.**

First, it is not a content measurement at all and should not be described as one.
It measures budget: whether the fix breaches a ceiling. Nothing hermetic can
measure a prompt's effect on content, and the spec is right not to try; what it
should do is stop letting a budget test stand where a content guard is owed. The
content guards that do exist are the direction falsifiers above — which cost a
model call and are read at PR 4 — and, at zero cost, the line-by-line assert in
`tests/test_gateway_run_parity.py`, which **names** what the prompt gained and is
the ADR-021 standard the M02 arm was built on: no tool-use coaching, no worked
example, no case vocabulary. That assert is the hermetic content guard on this
fix, it will go red when the fix lands (fact 3), and updating it is the PR's
opportunity to state what changed rather than an obstacle to route around.

Second, **as arithmetic the test is wrong by the call count** (fact 2). `6782` is a
per-sample total summed over three calls, the system block is re-sent every round,
and the assert compares a per-sample total against a per-call delta. It admits
`delta ≤ 917` where the claim can survive `delta ≤ 306`. A 400-token disclosure
sentence — a plausible size for one that must specify what to write and when —
passes the test the spec says prices the fix *"before a single call is spent"* and
puts `headroom-005` at 7982, falsifying F4 on the run it was written to protect.
This is a stated protection that is absent, which CLAUDE.md ranks worse than a
missing one because it stops anyone looking for the real one. The corrected assert
is `max(sample.tokens_in + delta × len(sample.calls)) ≤ 7700` over M08b's answered
≤3-call samples, computed from the committed evidence rather than from the single
published maximum — the population, not the sentence about it. Worst-case table,
computed: delta 300 → 7682 under; delta 306 → 7700 at the boundary, which passes
because `evals/deterministic.py` compares `got > limit`; delta 400 → 7982 over.

### 6. The cap, the fallback it fires, and the rename

SPEC/09 caps M09 at six and names PR 1b the sixth. **This PR is PR 1b, so the cap
is spent, and *Bounded*'s fallback fires by name: ADR-053's *no orphan rules* half
re-dates to M09b in the close's journal. *No immortal rules* does not give way.**
This is that debt's second dated slide and the only one the milestone
pre-authorises.

**And the DMA rename must slide a fifth time, which the spec calls a finding.** It
is recorded as one here, before PR 3, rather than discovered at PR 3 or at the
close. The reasoning is fact 4 and it is not a scheduling preference:

- A consistent rename **refuses M08b's committed run** through
  `fresh_join.py --check`, because recorded trajectories carry tool arguments the
  renamed contract rejects. The three ways out are re-producing nine milestones of
  trajectory records, editing committed evidence, and sliding. The first is
  unpriced work with no cap slot; the second is forbidden in as many words by
  *committed as-run* and by CLAUDE.md's eval discipline.
- It moves `services/highlights-agent/evals/golden/cases.yaml` (`viewer.dma`,
  three occurrences on one name alone), which *What must not happen* forbids —
  *"No case edited"* — and which SPEC/09 constraint 4 does not list among what the
  rename moves.
- It collects five two-key rules SPEC/09 does not name, including
  `quality/adversarial/tool-plane-probes.yaml` at **Security alone with
  `requires_adr`**, in a milestone whose constraint 1 says no corpus moves.
- Sixty files name the six markets. `data/catalog.json`, `data/catalog_poisoned.json`
  and `platform/gateway/policy/tools.contracts.json` — three of the files the
  rename must move — are on **no two-key rule at all**, which is a finding
  independent of the schedule and one ADR-035's *the thermometer protected and the
  thermostat not* covers exactly.
- And it confounds F4 (§3), which is the reason it should not land before the run
  even if it could.

**Where it should go: `09c`, and re-scoped.** Not M09b, which carries a deploy and
a probe re-run and would inherit the same confound against its own baseline. `09c`
re-runs the goldens against a repaired agent by construction, so it is the first
milestone where a new market vocabulary and a new set of committed trajectories
arrive together and no comparison spans them. The re-scoping is the harder half
and belongs to Legal/S&P and Data Governance with an ADR: **a rename of the market
vocabulary is a change to the system under measurement, not a documentation
tidy**, and A21 has been carried as the latter through five milestones. That
sentence is what the four slides were hiding.

**PR 3's slot is therefore vacated, and §3 spends it on PR 4b.** Six: PR 1, PR 1b,
PR 2, PR 4, PR 4b, PR 5. There is no PR 3, PRs 4 and 5 keep their numbers, and
every reference in SPEC/09 and in this ADR stays valid.

**This amendment's citations, and the one correction the rule forced.** As first
written this text cited `c391e93` — PR 1's commit on `m09-rules`, reachable from
`main` by no path and from no tag, which is exactly what SPEC/09 constraint 11
refuses. Constraint 11 was run over this text before merge, as it requires, and it
went red on it. The pre-registered remedy was applied: the commit was tagged
`cited-m09-pr1` on ADR-074 amendment 3 §9's mechanism.

**Then PR 1 merged while this PR was in flight**, squashing to **`66bb114`** on
`main`, and the rule's *other* remedy — *cite the merge commit on `main` instead* —
became available and is the better one, because a commit `main` reaches needs no
ref kept alive for it. Every citation above now names `66bb114`; `git diff` between
the two is empty, so the reading is against the same tree it was taken against and
no number moves. **`cited-m09-pr1` is left standing rather than deleted** — it is
pushed, it is now redundant, and deleting a published ref to tidy a redundancy is a
remote mutation with no check behind it; `cited-m08b-pr2-r1` and `-r2` stand in the
same condition for the same reason.

Worth naming because it is a small instance of this amendment's own subject: **a
pre-registered mechanism was applied correctly and then made unnecessary by an
event the pre-registration did not model** — the base moving under a PR that reads
the base. It cost one rebase and this paragraph. Every other reference here is to a
path, a test name or a number, and none acquires a fuse.

### What this amendment asks PR 2 and the spec to carry

Each is a change to SPEC/09 to land in **this PR's diff**, on the Definition of
done's own PR 1b box and on ADR-074 amendment 1's precedent — a Definition of done
corrected after its PR prints is a checkbox rewritten to match the outcome. **None
is made here**: asks 5, 6 and the re-scoping in 6 are the operator's the way
decisions 1–4 and 6 were, and this PR also carries its own housekeeping — the ADR
index row naming amendment 1 with the ≤10 ratchet unmoved at 10, and §6's citation
correction after PR 1 squash-merged under it.

1. **The `p95_ms` section carries §4's five-population table and its answer**: the
   condition does not hold, 5200 stands, ADR-014's stability sentence is withdrawn
   in ADR-014 amendment 3 on that file's two keys, the gate is re-described as a
   fixed ceiling with a recorded derivation, and the re-derivation dates to `09c`.
   The spec says which reading of *the run reads OVER* the condition means, and
   records that under the same-population reading it is unsatisfiable by
   construction.
2. **The prompt-delta test is corrected to multiply the delta by the call count**,
   computed over M08b's answered ≤3-call samples rather than against the single
   published maximum, and the spec's `6782 + delta < 7700` is replaced by the
   population form. The headroom sentence stops saying 918.
3. **F4 gains the two direction falsifiers and loses the count**; the count `N` in
   [8, 12] is a side-prediction in all three places, and the falsifier table, the
   *Beside the claim* section and the PR 4 Definition-of-done box are made to
   agree.
4. **PR 4's diff names `tests/test_gateway_run_parity.py` and
   `milestones/M08/context-census.json`**, collects `(platform-eng, security)` and
   the census rule's three keys, and records the `TOOL_SYSTEM` move in the
   progression row as the ADR-021 event the pin's own docstring calls it. The
   Definition of done's `milestones/M08/` clause is amended to name the prompt
   digest line, as ADR-074 amendment 1 ask 2 amended it for the manifest.
5. **The goldens control run, its entry, its `README_GOLDENS` row and row 09's
   `N/25` move to PR 4b**, after the fix, with PRs 4 and 5 keeping their numbers.
6. **PR 3 is vacated**; the DMA rename re-dates to `09c` by name, re-scoped as a
   change to the system under measurement, with its own ADR at Legal/S&P plus Data
   Governance. The slide is recorded as a finding in the close's journal, since
   the milestone pre-authorises only ADR-053's.
7. **PR 2 writes a decision record in its own diff** — `rules/schema.json` puts it
   under a `requires_adr` rule and `adr_records` reads the diff. Either PR 2
   amends this ADR with the *no immortal rules* and *orphan rule* reasoning, or it
   carries ADR-076 for them; the definition work ADR-053 says must come first is
   ADR-shaped anyway.
8. **The chain reader and M09's own readers, records and pins go on a two-key rule
   in the diff that creates them** — `pave/cli.py`'s `rules trace` path, the
   verdict files and the run-A answers — by widening the census rule over
   `milestones/M09/` and `tests/test_m09_*`, as M08b widened it over
   `milestones/M08b/`, with a `_blocked_for` plant each. Row 1a's reader decides
   what *traceable* means and is on one key today.
9. **The comparator pin moves to PR 4b or comes out**, and if it stays, `pave/cli.py`
   gains the lane that reads it, on a rule. A pin nothing reads is ADR-048's T1.
10. **`answer.schema.json`'s `ai_disclosure` description is rewritten in PR 2**
    beside the other two reservation withdrawals — it is the model-facing one — and
    the negative half's assert tests key presence rather than truthiness, because
    the field is not `required`.
11. **The seat round is told the two plants this reading did not run**: a
    prompt-delta test that compares a per-sample total against a per-call delta,
    and a comparator pin for a suite no lane reads.

### What this amendment does not change

The claim and its five falsifiers, except F4's contents (§5) — F1, F2, F3 and F5
stand as written, and F1's premise is confirmed on committed evidence. The
decision that the disclosure pack is its own suite; the goldens denominator at 25;
`disclosure-004`'s withdrawal. Decisions 1, 2 and 3, and the reasoning that the
fix is caller-side, which was checked and holds. The refusal bands. The order of
the debts against the run. Constraints 1–11, except constraint 4, which the rename
takes with it. The M09b hand-off in decision 5 §5. The cap — six, and spent here.

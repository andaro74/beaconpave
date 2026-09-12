# M09b — the rule's second control, and the topic reworded under an admission rule

**Branches:** one per PR, seven PRs (see *The cap*) · **Tag:** `m09b` · **Closed:** 2026-09-12, **RED**
**Spec:** `SPEC/09b-the-guardrail-line-and-the-topic.md` · **Claims advanced:** none of the twelve, by decision (ADR-076 decision 1)

---

## The verdict

**Closed RED. No deploy was taken, no falsifier was read, and no model call was made in
the milestone.**

> **A rule's second control lands as an additive DENY topic that blocks the negation
> its L3 control cannot reach and refuses nothing the product answered; and the topic
> beside it, reworded under an admission rule executed before any candidate was
> measured, stops refusing the platform's own grants while every frozen row it blocked
> still blocks.**

| term | what it needed | reading at the close |
|---|---|---|
| **1** — the additive DENY topic lands and refuses nothing the product answered (F3) | a candidate admitted, one deploy, the post-deploy goldens run | **Closed on a defect found before measurement.** The one candidate was refused under ADR-077 decision 2 §3 (ADR-077 amendment 2). It was never swept and never deployed |
| **2** — the wording fix's benefit (F1) | the deploy, the post-deploy goldens run, two withheld readings, `F` and `G` | **Not measured** |
| **3** — the wording fix's risk (F2) | the deploy and the post-deploy sweep of every frozen corpus | **Not measured** |

| | falsifier (SPEC/09b:89-93) | reading |
|---|---|---|
| **F1** | `F > 0`, or `G < 8`, or `blackout-009` refused by majority by any topic | **not read** — no post-deploy run |
| **F2** | a frozen row that blocked 3 of 3 pre-deploy does not after; `PHR-002`–`005` or the clean catalog move | **not read** — no post-deploy sweep |
| **F3** | a case answered by majority on M09's control run is refused after the deploy | **not read** — no post-deploy run |
| **F4** | the deployed wording is not the admitted one; the admission record's `inputs_sha256` names a barred input; a candidate precedes its corpus | **not read** — nothing deployed, and the second clause has no field to read (below) |
| **F5** | a refused sample deciding F1 or F3 names more than one `TOPIC:` | **not read** — no refused sample exists to count, and none is defined (below) |

**None of these is reported clean.** None fired, because none was read. A milestone
whose claim was not measured has not shown the claim. That is why it closes red and
not green, and not because a falsifier fired.

### Term 1 — the candidate was drawn from the corpus that would have judged it

`milestones/M09b/candidates.json:66`, the additive topic's only candidate:

> Editorial copy that says a person wrote it or denies that AI was involved. Disclosing
> that AI generated it, or copy saying nothing about who wrote it, is not.

`quality/adversarial/disclosure-shapes.yaml:1-2`, the header of the corpus gate 7 reads
that candidate through:

> The additive topic's own corpus: editorial copy that claims a person wrote it,
> or denies that AI did, each paired with the same copy disclosing correctly.

The run *a person wrote it or denies that AI* is eight words long. It appears in
`disclosure-shapes.yaml` and in no other file at the parent of 6926f9f, the tree gate 2
reads. *About who wrote* is the same. ADR-024:84-88 presumes such a term drawn and puts
the burden on the author. The record declares no term, and decision 2 §3 says *"an
unjustified term refuses the candidate"* (ADR-077:139). The full comparison, including
the same test run on the recalibration (which it clears), is ADR-077 amendment 2, as-run.

**Why the check built for this passed it.** `candidates.json:31` defines a term as *"a
lower-cased run of letters"*, which is one word. ADR-024's clause says *term*. Every word
of the run appears somewhere else in the repository, so
`tests/test_m09b_admission.py` computes `presumed_drawn: []` for both candidates and
goes green. **The record's definition is narrower than the clause it executes, and the
executor passes a candidate the rule refuses.** Neither is changed at the close.

**No retry is available or taken.** ADR-077:127, amendment 1:479-481 and ADR-035
amendment 4:975-978 each say that a failed candidate's successor is a new ADR and a new
held-out set, not a retry. No second candidate was authored. The candidate record's
`set_sha256` is unchanged.

### Terms 2 and 3 — the deploy was not taken, and here is why, at line

Refusing the additive candidate did not stop the recalibration. ADR-077:262-265 says *"A
no-winner on the additive topic alone leaves the recalibration to deploy."* The rule
allowed that deploy and did not require it, and the close did not take it. **One deploy
replaces the guardrail version resource and every pre-deploy reading with it** (SPEC/09b
constraint 2, :371-373), so it is the milestone's one irreversible act. Four things
needed to turn that deploy into a reading do not exist:

1. **Nothing executes gates 3–7.** ADR-077 amendment 1 moves gates 3, 4, 5, 6 and 7
   after the deploy, *"on the pinned guardrail"*, and its table's executor column for
   them reads *"not built here"* (:503-506). `tests/test_m09b_admission.py:4-11`: *"It
   admits nothing past gate 2."* No `.py` file in the repository implements a
   post-deploy gate. The four rules that executor would carry have no code:
   - unanimity at k=3 decides (:500)
   - a split fails (:500-501)
   - an unreadable row fails (:501)
   - each row reads *still* or *not still* against the pre-deploy sweep (:506)

   A failed post-deploy gate *"closes the term RED"* (:479-481). No committed code
   could have said whether one failed.
2. **F4's second clause reads a field no file carries.** SPEC/09b:92: *"the admission
   record's `inputs_sha256` names `refusal-shapes.yaml`, `answer-decomposition.yaml`,
   `probes.yaml` or any goldens answer file"*. `candidates.json` carries no
   `inputs_sha256`. The only two files that do, `milestones/M09b/fg.py:275` and
   `fg-pre.json:3`, belong to the F/G reader, not the admission record.
3. **F5's denominator counts something nothing defines.** SPEC/09b:127: *"F5 must
   publish how many refused samples decided F1 or F3"*. The phrase *decides F1 or F3*
   appears in five places: SPEC/09b:93, :127 and :673, and ADR-076:223 and :539. None
   says what makes a sample decide a falsifier, and no code counts one. A denominator
   that must be published, of an undefined count, cannot be published honestly after
   the run it is counted on.
4. **The definition that moves F and G was due at a check defined nowhere.** Whether a
   withheld answer is *schema-conforming* decoded or raw moves both readings on the
   same run (`milestones/M09b/journal-notes.md:217-218`):

   ```
   decoded, as committed                     G = 7   F majority = 1   F at least once = 4
   raw, the five held grants read false      G = 6   F majority = 0   F at least once = 0
   ```

   **No reader outside the operator pair can verify `F` or `G`**: the evidence was
   withheld by the control being measured (SPEC/09b:121-124). The disposition's trigger
   was re-dated to *"PR 4's pre-registration check, before the run"*
   (`journal-notes.md:208`). That phrase appears in `journal-notes.md` at :114, :205
   and :208, and in `docs/pr-bodies/m09b-pr3.md:26`, and nowhere else. SPEC/09b's PR 4
   Definition of done (:722-732) names no such check. A post-deploy F1 would have been
   read under a definition settled after the numbers existed, which is the exact thing
   the re-date was written to prevent (`journal-notes.md:221-223`).

**So the one deploy was not spent on readings that could not decide the claim.**
Taking it would have produced a version-5 guardrail, destroyed the pre-deploy readings
PR 2b committed, and left every falsifier as unreadable afterwards as it is now.

### What was built, stated plainly and not as consolation

- **The era pin was paid first** (PR 1), before any prompt constant moved, so M08b's
  published attribution is era-pinned rather than silently re-priced.
- **A rule that selected on a corpus forbidden to select was withdrawn before any
  measurement** (PR 1c, ADR-076 amendment 1). It was replaced by one that admits and
  never chooses (PR 1d, ADR-077).
- **The pre-deploy readings exist and are committed** (PR 2b): the sweeps at v4/v1 over
  every corpus, the clean catalog and `phrasings.yaml`; two independent withheld
  readings that agree on all ten booleans; `F`/`G` with the baseline as an argument; the
  additive topic's frozen corpus. `fg.py --check` reproduces its record today.
- **The chain reader walks a guardrail control** (PR 3): the home narrowed to the stack
  file, and a walker that refuses a selector no corpus row names, with plants both ways.
- **Debt 33 was paid and found a live instance** (PR 2): three specs' demo blocks sat
  under a heading the runner could not see.

None of these is a claim term, and the claim is not narrowed to fit them.

---

## What can I demo right now?

Every command reads committed files. None calls AWS or a model. Each was run at the
close.

```bash
# the rule, still with ONE control; no guardrail control was added
python -m pave.cli rules trace MER-AI-0001        # ... control eval_pack ... chain: RESOLVED, exit 0

# the refusal, in two lines a reader can hold side by side
sed -n 66p milestones/M09b/candidates.json
sed -n 1,2p quality/adversarial/disclosure-shapes.yaml

# gate 2 as executed: 26 passed, both candidates admitted under the one-word reading
python -m pytest tests/test_m09b_admission.py -q

# the pre-deploy F/G record, recomputed from the two readings; exit 0, writes nothing
python milestones/M09b/fg.py --run milestones/M09 \
    --grants milestones/M09b/withheld-grants-security.json \
    --grants milestones/M09b/withheld-grants-legal-sp.json \
    --baseline milestones/M08b/answer-channel.json \
    --out milestones/M09b/fg-pre.json --check
```

SPEC/09b's demo block stays `text`. Every file it reads is a post-deploy artifact this
milestone did not produce.

---

## What's the delta vs baseline?

**None, because nothing was run.** No goldens run, no adversarial run, no disclosure run,
no judge run, no history entry. Row 09b's cells say *not run*, not a number carried from
M09. Against `m00b` there is nothing to compare, and nothing improved that needs a
mechanism named.

Unearned passes: none. The one pass this milestone could have reported unearned was
gate 2 on the additive candidate, and that pass is overturned in ADR-077 amendment 2
rather than published.

---

## What broke?

**1. The candidate reached its record by rewording its judging corpus's header, and the
check built for exactly that was green.** ADR-024's clause names the hazard, a
definition written against a corpus. `candidates.json:31` executed that clause at one
word per term, and a phrase-level lift passed it. The test's own docstring called its
reading *"weaker than the hazard it names"* (`tests/test_m09b_admission.py:17-18`). That
was published and read as a limit, not as a live defect. It was found at the close by
reading two lines side by side, after PR 3 merged green. **A limit that has been
published is still the defect when the case it describes arrives.**

**2. Amendment 1 moved five gates past the deploy and scheduled nobody to build them.**
*"Not built here"* (ADR-077:506) names what was left out and not who builds it. SPEC/09b's
PR 4 Definition of done was not amended to name it. The executor was absent in the same
way the throwaway guardrail was absent (item 3), and a stated-and-absent protection
stops anyone looking for the real one.

**3. ADR-077 pre-registered every gate against an instrument nobody had checked
existed.** The throwaway guardrail was never built (`journal-notes.md:181-199`). It was
found at PR 2b, and amendment 1 dropped it rather than building it. The pre-registration
was sound as a rule and unexecutable as written.

**4. PR 3 shipped four of its Definition-of-done items and named the rest as not built**
(`docs/pr-bodies/m09b-pr3.md`, *SPEC/09b's PR 3 items not in this PR*):

- `rules/schema.json`'s `selector` and `additionalProperties: false`
- `classify_sha256`'s widening
- the admission files joining the deployed-guardrail rule
- the gate-list freeze predicate
- decision 4's deploy-refusal test
- **both seat rounds**

SPEC/09b constraint 8 put the milestone's only seat round on PR 3, and it was not taken.
Whether a seat told to plant *"a candidate whose prohibited-source term has no
justification line"* (SPEC/09b:590-591) would have planted a lifted phrase is not
knowable now.

**5. A cold read was cited and does not exist.** The close was briefed to read
`milestones/M09b/pr4-cold-read.txt`. No such path exists on `main`, on any branch, local
or remote, or anywhere under the operator's home directory. The one cold-review file found
there is PR 1b's, in another session's scratchpad. **Every reason in this journal is re-derived at line,
and none rests on that file.** SPEC/09b constraint 12 says a cold review's output is
committed like any other evidence (:404-407). This is the second time in this milestone
the output of a cold review did not reach the repository.

**6. The demo script points a beat at an artifact this milestone never produced.**
`docs/governance/demo-script.md:157-164` re-points Act 3's probe beat to
*"`milestones/M09b/probes-run.json` and the audit record it resolves to"*. M09b ran no
probe. The row that paid this at PR 1 is re-opened below. The script is not edited here.

**7. `G` was below F1's floor before any wording existed.** `G = 7` on the run the
deploy would have followed, against F1's `G ≥ 8` (`journal-notes.md:89-114`). F1 was not
re-scoped. The finding stands whether or not any deploy is ever taken.

**8. SPEC/09b still describes ten candidates and a throwaway sweep.** ADR-077 amendment 1
superseded both, and SPEC/09b:200-201 makes the ADR the rule where they differ. The
close edits only SPEC/09b's status line, so the summary stays stale beside a pointer.

---

## Definition of done, item by item (close-milestone step 1)

| SPEC/09b item | at the close |
|---|---|
| PR 1 | done (#141) |
| PR 1c | done (#142) |
| PR 1d | done (#143). The box is unticked in the spec, which the close does not edit |
| PR 2 | done across two containers, PR 2 (#144) and PR 2b (#145). The four rule gaps: three closed at PR 2b; the fourth, with the walker, at PR 3 |
| PR 3 | **partial** (#146): two candidates rather than ten (ADR-077 amendment 1), gates 1–2, the walker and home. Not built: see *What broke* 4 |
| PR 4 | **not taken.** No deploy, no sweeps, no runs, no withheld readings, no comparator pin, no `bash` demo block |
| PR 5 | this close: `close-milestone` in order; step 6b not taken (below); row and cell filled; tag `m09b` is the operator's |
| Nothing under `milestones/M07/`, `M08/`, `M08b/` or `M09/` changed; `SPEC/09` not edited | **one exception, pre-registered:** `git diff --stat 52edc27 HEAD` over those paths returns `milestones/M08b/residual-attribution.json` and `residual_attribution.py`, which are the era pin SPEC/09b constraint 1 required at PR 1. `SPEC/09` is unchanged |
| No prompt constant, tier, ceiling, `p95_ms`, comparator, catalog row, golden case or judge instrument moved; `frozen.json` byte-identical | holds. The same diff over those paths, plus `evals/history`, `rules/`, `gateway-stack.ts`, the synth fixtures and the four frozen corpora, returns two more files, each an expected PR 1d or PR 1 change: `quality/adversarial/phrasings.yaml` (the `frozen_before` declaration) and `quality/judge/calibration/labels.json`, whose only change is the `brand_tone` owe's `re_deferred_to` moving from `M09b` to `M10`. **No label value moved.** `frozen.json` is absent from the diff |

---

## The close's own measurements

| | |
|---|---|
| `make check` | CLOSE-MEASUREMENT-PENDING |
| deletability audit | CLOSE-MEASUREMENT-PENDING |
| two-key | CLOSE-MEASUREMENT-PENDING |
| model calls | **zero**, in this PR and in the milestone. `git grep -l '"usage"' -- milestones/M09b` matches nothing, and `evals/history/` holds no `m09b` entry |
| moved | no case, tier, threshold, ceiling, baseline, falsifier, guardrail, policy, corpus row, catalog row, topic or candidate. `set_sha256` is `e14ab354…`, as PR 3 committed it |

---

## Open holes and triggers (close-milestone step 6b)

**The frozen corpus is not re-run, and no census is read, because none exists.** Step 6b
checks a guardrail change against accepted holes and reads accepted costs out of *"the
governed golden run this milestone recorded"*. This milestone deployed no guardrail
change and recorded no run.

- **`enforcement-probing` (ADR-035 amendment 9):** not re-disposed at this close. Its
  trigger fired at M09 on `blackout-009` by majority, and the topic went to Security
  (`milestones/M09/README.md`, *Open holes and triggers*). No new footprint exists to
  re-dispose it against. Security still holds it, as M09 left it.
- **Retention on the withheld store (ADR-071 amendment 1):** **not met.** The trigger is
  the first viewer turn the store holds that is not committed corpus text. M09b made no
  model call, so the store gained no turn of any kind.
- **No accepted hole has a deadline in this milestone.**

---

## The cap

**The cap is on spend and irreversibility** (SPEC/09b *Bounded*). Nothing on it was
spent.

| bound | spent |
|---|---|
| one deploy | **0** |
| one model-call PR, ceiling 160 turns | **0** — PR 4 was not opened |
| one seat round, on PR 3, in two rounds | **0** — not taken (*What broke* 4) |
| zero judge runs, zero re-freezes | **0** |

**Containers, counted and not the bound: seven PRs.** PR 1 (#141), PR 1c (#142), PR 1d
(#143), PR 2 (#144), PR 2b (#145), PR 3 (#146) and this close. PR 1b's cold review ran
and was never committed. PR 4 was never opened.

**The disclosure pack re-run and its comparator pin gave way, and that is a finding.**
*Bounded*'s fallback lets them give way only when the turn ceiling or the deploy bound
is reached (:560-563), and neither was. They gave way because PR 4 was not taken, and
*"any other slide is a finding"*.

**The fifth `brand_tone` slide, recorded as a slide and never as a payment.** ADR-026
amendment 5 re-deferred the widening from M09b to M10 at PR 1, in
`quality/judge/calibration/labels.json`'s `re_deferred_to`, on two keys. It is the
second slide whose reason changed rather than its number.

---

## Decisions

- **ADR-076** (PR 1): the claim's shape and the milestone's other decisions. **Amendment
  1** (PR 1c): the derivation rule withdrawn before measurement. **Amendment 2** (PR 2b):
  the additive topic's corpus frozen, with its partition over both halves.
- **ADR-075 amendment 7** (PR 1): decision 1's false ground, and the cap moved from
  containers to spend.
- **ADR-026 amendment 5** (PR 1): `brand_tone` re-deferred a fifth time, to M10.
- **ADR-077** (PR 1d): a corpus may eliminate a wording, and none may choose one.
  **Amendment 1** (PR 3): one candidate per topic, and the throwaway dropped. **Amendment
  2** (this close): the additive candidate refused under decision 2 §3, no retry.

---

## Debts carried out of M09b, each with an owner and a trigger

**None is closed or repaired here.** *Unscheduled* means no milestone carries it. The
*blocks* line says what cannot honestly happen until it is paid.

### Opened at this close

| # | debt | owner | trigger |
|---|---|---|---|
| 1 | **The gate executor, and its four rules.** Gates 3–7 are read post-deploy and nothing reads them (ADR-077:503-506). Its rules have no code: unanimity at k=3, a split fails, an unreadable row fails, and *still*/*not still* against the pre-deploy sweep (:500-501, :506). Decision 4's deploy-refusal test is part of it | Security + Platform Engineering | **unscheduled.** Blocks: any deploy of a topic wording under ADR-077 |
| 2 | **F4's `inputs_sha256`.** SPEC/09b:92 reads *"the admission record's `inputs_sha256`"*, and `candidates.json` carries no such field. F4's second clause has nothing to read | AI Quality + Platform Engineering | **unscheduled.** Blocks: reading F4 |
| 3 | **F5's denominator.** *A refused sample that decides F1 or F3* is defined nowhere (SPEC/09b:93, :127, :673; ADR-076:223, :539), so the count SPEC/09b:127 requires cannot be computed | AI Quality + Security | **unscheduled.** Blocks: reading F5, and publishing *"F5 not exercised"* honestly |
| 4 | **The decoded-or-raw definition of *schema-conforming*.** It moves `G` 7→6 and `F` majority 1→0 on M09's control run (`journal-notes.md:217-218`). Its trigger, *"PR 4's pre-registration check"*, names a check no document defines | Security, with Legal/S&P (`journal-notes.md:129-131`) | **unscheduled.** Blocks: any post-deploy read of F1. It must be settled before the run F1 is read on, never after |
| 5 | **Gate 6/7 routing.** ADR-077 amendment 1 routes a post-deploy failure of gate 6 or 7 to *"F4's first clause"* (:488-491). That clause reads what `tests/test_m09b_admission.py` admits, and the test executes gates 1 and 2 only (:4-11). A gate 6 or 7 failure changes nothing the test admits, so it routes to a falsifier that cannot fire on it | Security + AI Quality | **unscheduled.** Blocks: gates 6 and 7 meaning anything post-deploy |
| 6 | **The additive topic's walker trace.** `disclosure-shapes.yaml`'s rows name no topic, so a `guardrail` control on the additive topic reads NOT RESOLVED on claim 6's command. The walker is not loosened, and the frozen corpus is not edited (`journal-notes.md:240-262`) | Security + Legal/S&P + Platform Engineering | the next PR that adds a `guardrail` control to `rules/MER-AI-0001.yaml`, before it lands |
| 7 | **The `G < 8` narration.** `journal-notes.md:107-114` says, before any post-deploy run, that a post-deploy `G < 8` would fire F1 *"on population rather than on the topic"*. No check holds that reading, F1 is not re-scoped by it, and its trigger is the same undefined check as debt 4 | AI Quality + Security (`journal-notes.md:113-114`) | **unscheduled.** Blocks: reading F1's second clause without that sentence pre-explaining it |
| 8 | **Gate 2's executor is narrower than the clause it executes.** `candidates.json:31` makes a term one word, so `tests/test_m09b_admission.py` passes a candidate ADR-077 amendment 2 refuses. Found at this close | Security + Platform Engineering | the next PR that commits a candidate topic wording |
| 9 | **Demo script Act 3's probe beat names `milestones/M09b/probes-run.json`, which does not exist** (`demo-script.md:157-164`). It re-opens the row paid at PR 1. Found at this close | Legal/S&P + Security | the recording of Act 3's probe beat |

### From SPEC/09b's inherited register, row by row

Each row cites its source line in SPEC/09b. Where nothing about a row changed, its owner
and trigger are as the spec wrote them.

| SPEC/09b | debt | owner | at the close |
|---|---|---|---|
| :495 | registry cannot detect a rule disposed against a service with no instance of its subject | Legal/S&P + AI Quality | unchanged — unscheduled, owned |
| :496 | eval-pack disposition is not a publish-class disposition | Tool Owner + Legal/S&P | unchanged |
| :497 | the control reads the disclosure's words, not its sense | Legal/S&P + AI Quality | unchanged |
| :498 | `handler.py`'s G5 refusal branch deletes cleanly on two seats | Data Governance + Platform Engineering | unchanged — no M09b PR opened `handler.py` |
| :499 | nothing asserts the router's semantics | Data Governance | unchanged |
| :500 | `classify_sha256` digests one file while the rule covers four | Security | **trigger named PR 3; not taken** (`docs/pr-bodies/m09b-pr3.md`). `evals/adversarial.py:872` still digests `classify.py` alone. Unscheduled |
| :501 | the disclosure lane is wired into no CI workflow | Platform Engineering + AI Quality | **not fired** — its trigger is the first PR that runs the pack again, and none did. The trigger stands |
| :502 | `pave verify` cannot see the second pack | Tool Owner | unchanged |
| :503 | the tool plane's recorded input, IAM test and bundles are on no rule | Platform Engineering + Security | unchanged |
| :504 | `ROLES.md`'s rows are transcribed, not checked | Platform Engineering | unchanged — `ROLES.md` has no commit since 52edc27 |
| :505 | `ROLES.md` on no two-key rule | Platform Eng + Security | **PAID at PR 2b** (`journal-notes.md:138-139`) |
| :506 | `DISPOSITION_RE` accepts any `[a-z-]+` | Platform Eng + Legal/S&P | unchanged |
| :507 | `rubric-sports.md` states an M07 activation that did not occur | AI Quality + Security | unchanged |
| :508 | `pave exception request` reports success for doing nothing | Service Team + Data Governance | unchanged |
| :509 | `rules/schema.json`'s `required`/enum surface is unasserted | Legal/S&P + Security | **not fired** — no M09b PR edited `rules/schema.json`. The trigger stands. PR 3's unbuilt `selector` and `additionalProperties: false` sit on the same trigger |
| :510 | `gateway_client.py`'s `boto3` binding | Platform Engineering | unchanged — not opened |
| :511 | `tests/test_m09_cap.py` on no rule | Platform Engineering + Security | **closed as a wrong debt at PR 2b.** It was on the census rule all along (`journal-notes.md:140-144`) |
| :512 | no ADR and no spec is on any two-key rule | owned, unscheduled | unchanged. This close edits ADR-077, the ADR index, SPEC/09b and `README.md` on no key |
| :513 | the fix's site count has been wrong three times | Platform Engineering | unchanged |
| :514 | the M08b residual reader had no era pin | AI Quality + Platform Engineering | **PAID at PR 1** |
| :515 | the direction predicates take their baseline from a module constant | AI Quality + Platform Engineering | **PAID at PR 2b.** `fg.py` takes `--baseline` with no default, held by `tests/test_m09b_fg.py:83-86` |
| :516 | F4 cannot separate the prompt delta from generation drift | AI Quality | unchanged |
| :517 | `grounded-017`'s margin, a live regression on `main` | AI Quality | **not re-measured** — no run. **09c**, as a read |
| :518 | the disclosure comparator pin | AI Quality + Legal/S&P | **not fired** — no second disclosure run. The trigger stands. Its slide is a finding (*The cap*) |
| :519 | the DMA rename | Legal/S&P + Data Governance | **09c**, unchanged |
| :520 | the browse-gap cases; the `tokens_out` cases | Tool Owner; AI Quality | **09c**, unchanged |
| :521 | Security's two `tool_request` probes; the `enforcement-probing` trigger | Security | **not read at step 6b** — no run and no sweep. Owned by Security, unscheduled |
| :522 | `context_census.py`'s `sys.path.insert` | Platform Engineering | unchanged |
| :523 | retention on the withheld store | Data Governance | **read: not met.** No model call in M09b |
| :524 | the stronger ADR-index predicate | PM | unchanged. This close adds amendment 2 to ADR-077's index row, so the stale count does not rise |
| :525 | ADR-069 D5 cut 2 | the next two-arm run | unchanged |
| :526 | standing observations | – | unchanged |
| :527 | only *Demo artifact* blocks are checked | PM + Platform Engineering | **PAID at PR 2.** Its finding carries: three specs spell the heading `## The demo artifact`. Owner PM + Platform Engineering; trigger: the next PR that edits a `## The demo artifact` heading or the scope check (`docs/pr-bodies/m09b-pr2.md:188-192`) |
| :528 | CLAUDE.md's one-branch rule against per-PR practice | Platform Engineering (the lead's seat) | unchanged. M09b used seven per-PR branches. No branch is named `m09b`, so tag `m09b` is unambiguous |
| :529 | the deletability audit runs `pytest` while the gate runs `pave check` | Platform Engineering | **not paid.** PR 3 ran 2 of its 28 plants through the gate (`milestones/M09b/pr3-deletability-audit.txt:10-16`), and this close runs every plant through it. The trigger stands |
| :530 | demo script Act 3's second half | Legal/S&P + Security | **paid at PR 1, and re-opened** as debt 9 above |
| :531 | `brand_tone`'s widening | AI Quality (+ Security) | **M10**, a fifth slide (*The cap*) |
| :532 | `brand-021` and `concise-022` refusing on `entitlement-circumvention` | Security | **not fired** — its trigger reads after the deploy, and none was taken. Unscheduled |
| :533 | four corpora declare no freeze | Security / Red Team | unchanged |
| :534 | two debt registers, and nothing asserts they agree | Platform Engineering + PM | unchanged. This table is a third transcription, and each row cites its source line |
| :535 | `SPEC/`'s withdrawal markers are prose with no check | PM + Platform Engineering | unchanged; the general check is owed |
| :536 | a spec's demo block cannot be both pre-registered and runnable | PM + Platform Engineering | **not fired** — PR 4 was not taken, and SPEC/09b's block stays `text`. Unscheduled |
| :537 | nothing asserts that an admissibility-gate corpus declares its freeze | Security / Red Team + Platform Engineering | **trigger named PR 3; not taken** (`docs/pr-bodies/m09b-pr3.md`). Unscheduled |
| :538 | ADR-076's pointer to its replacement is prose with no check | PM | attached to :524, unchanged |

---

## What's next

**09c moves no guardrail and inherits none of this milestone's machinery. The first
milestone that deploys a topic wording under ADR-077 inherits all of it.** Before that
deploy, debts 1 to 5 must be paid:

- the gate executor
- F4's input record
- F5's denominator
- the decoded-or-raw definition
- the gate 6/7 routing

This milestone's deploy was not taken because each was absent. A later milestone that
takes a deploy without them measures a claim it cannot read.

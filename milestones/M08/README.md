# M08 — the tools arm's budget: the context or the ceiling

**Branch:** six PRs (#122–#126 and the close) · **Tag:** `m08` · **Closed:** 2026-09-07
**Spec:** `SPEC/08-budget-context-or-ceiling.md` · **Claims advanced:** none (serves 2
defensively; claim 6's suite becomes scorable on this arm at M09's fresh run, not here)

> **The ceiling was wrong, and the census said so before any number was proposed.**
> M07 closed at 2/25 with all 22 answered-and-wrong cases over a `tokens_in` ceiling
> of 6000. A zero-call census of the committed stage-2 trajectories says why: the
> modal turn went from two model calls to three when `entitlement-check` became a
> second sequential tool round at M06b, the per-call base went 1693 → 2057, and no
> sample over the ceiling at its mandated call count carries removable content in
> the three categories the pre-registered rule admits. The rule picked **outcome B**,
> ADR-014's pinned rule re-derived the ceiling as **7700** inside [7171, 8180] and
> below the minimum four-call turn of 8181, and the re-score of **the same 75
> samples M07 recorded** prints **12/25**. The claim is per sample and holds:
> **every one of the 59 answered samples at three calls or fewer passes `tokens_in`,
> every one of the 14 at four or more fails it.** Six PRs, on the cap; zero model
> calls and no deploy for the whole milestone; no case, prompt, tool spec, topic,
> guardrail or M07 file moved.

## What can I demo right now?

**The census, then the re-score.** Hermetic; every input is committed; zero model calls:

```bash
python milestones/M08/context_census.py --check
python -m evals.run_evals --arm tools \
    --answers milestones/M07/goldens-run-1.json \
    --answers milestones/M07/goldens-run-2.json \
    --answers milestones/M07/goldens-run-3.json \
    --refusals milestones/M07/goldens-run-refusals.json
```

```
OK: milestones/M08/context-census.json is what the committed inputs produce
12/25 passed (13 failed, 0 infra) — judge axes recorded ADVISORY, not scored (ADR-012)
of the 13 failed: 1 were refused before scoring, 12 answered and scored wrong
refusals: 2/2 resolved to 1 (mechanism, assessed) pair — guardrail / TOPIC:entitlement-circumvention
suite latency  OVER p95=5431ms over 2500ms
channels: tool_request 0 · answer 2 · question 0 · tool_output 0
```

The last three lines are byte-identical to M07's, as SPEC/08's demo block predicted
before the number existed. The full transcript is `goldens-rescore.txt`; the three
single-file runs at 7700 (13/25, 10/25, 10/25) are `per-sample-at-7700.txt`, and the
same three at 6000 (3/25, 2/25, 2/25) are `per-sample-at-6000.txt`.

**The claim, which the count cannot show.** The k=3 line is a count; the claim is per
sample:

```bash
python milestones/M08/rescore_join.py --check
python milestones/M08/rescore_join.py --out join.txt   # 75 rows, one per sample
```

| calls | answered samples | `tokens_in` at 7700 | range |
|---|---|---|---|
| ≤ 3 | 59 | every one PASS | max 6792 (`headroom-005` s2) |
| ≥ 4 | 14, on 7 cases | every one FAIL | min 8181 (`grounded-019` s3) |

`rescore-join.json` is produced from the two transcripts, PR 2's transcript at 6000,
the census record, M07's history row and the live cases file, and
`tests/test_m08_rescore_join.py` pins it byte for byte — a planted verdict, a planted
claim flag, a planted flip and a foreign ceiling each move the record or are refused.

**The register, reading one run twice.** `evals/history/m08-tools-reread-goldens.json`
is the first entry of a new kind: a **re-reading**, which names the run it re-reads
(`m07-tools-goldens.json`), the threshold it re-reads it at (`budget.tokens_in`,
6000 → 7700) and the golden file it was scored against, and carries none of the run's
own measurements. M07's row still publishes 2/25 beside it, and `pave/history.py`
is red if it stops.

## What's the delta vs baseline?

| Metric | m00b (control) | m08 | Mechanism |
|---|---|---|---|
| Goldens | **15/25** | **12/25** | **The same 75 samples M07 scored at 2/25, re-read at a ceiling re-derived for the shape that produced them.** Not a fresh run, and **not an improved service**: no prompt, tool, schema, topic or gateway code moved in M08, by constraint 5 and by `git diff`. Recorded as a re-reading (`m08-tools-reread-goldens.json`, sha `17c3630`, `samples_from` naming M07's three files by their M07 digests). Ten cases flipped from FAIL, exactly the ten pre-registered in ADR-073 amendment 1; none of the five that could not; no case regressed. |
| Refused, by majority | – | **1/25**, unchanged from M07 | Nothing in M08 touches the guardrail. `recommend-003`, on the final answer, by the main pair's entitlement topic. The refusal and channel lines are byte-identical to M07's. |
| Adversarial | **0/10** | not run | No corpus edit, no probe run, no arm. `probes_sha256`, `g4_cases_sha256` and the judge digests are unchanged since before PR 3, by `git diff`. |
| p95 latency | – | **5431 ms**, OVER 2500 | Unchanged from M07 — the same samples. A **standing finding**, not a regression: the census puts model time alone at 2289 ms at two calls and 3606 ms at three, so a three-call turn cannot sit under 2500 whatever the code does. The gate costs no case; the rule that derives a suite p95 is owed to M09 PR 1. |
| Tokens in | – | not recorded on this row | 471637 over 73 answered samples is M07's measurement of this run and stays on M07's row. A re-reading carries no `tokens_in`, `tokens_out`, `tool_surface` or instrument field, and the register refuses one that does. |

**Honesty check.** The pass count went up and the mechanism is named: a threshold
moved. It is the mechanism a reader should be most suspicious of, so three things are
recorded beside it. **First**, the number was derived before any count was printed at
it — constraint 2 forbade the census from printing a pass count at any ceiling but
6000, and PR 4 is the first pass count at 7700. **Second**, by the record no stage-2
sample lies between 6792 and 8181, so every value in the band [7171, 8180] produces
the same per-sample join: the point could not have been chosen by looking at which
cases pass. **Third**, and read from the record rather than predicted: **at 7700,
striking the `tokens_in` half of `budget` entirely would move no case.** Every one of
the thirteen that still fail does so on a majority of samples for a reason other than
`tokens_in`. The moved ceiling costs the suite nothing and buys it nothing; what it
buys is an axis that discriminates again, and 12/25 is what the deterministic suite
says about these answers once the axis stops firing on every one of them.

**Unearned passes:** none. `grounded-016` passed 3/3 and `brand-021` 3/3 on their
asserts; the ten that flipped each pass every assert on a 2-of-3 or 3-of-3 majority.

## The seats' disposition on the number

Four seats reviewed PR 3 and no other, in isolated worktrees at `3efd5f6`, on one
question: *is this number produced by the rule from the record and by nothing else?*
Every seat re-derived the band and 7700 from the JSON and matched every figure. Every
finding was made by planting and running; none turned on which cases pass; no seat
computed a count at any ceiling but 6000.

- **All four — the point rule was not pre-registered anywhere committed.** The PR
  claimed the midpoint-rounded-to-a-hundred rule was pre-registered; it was written in
  a plan the operator approved in conversation, which is not an artifact. **Fixed**:
  the claim withdrawn, the truth stated in ADR-014 amendment 2, the rule made
  executable and pinned in the two-key derivation test, and the gap named in the
  record. This is the same finding M08 PR 3 was blocked on before by four seats, and
  it is the reason the word "pre-registered" now costs an artifact.
- **Security (blocking) — the census reader and its record were on zero keys.** A trim
  to `decision_rule()` landed 8190 with 2944 tests green on one key. **Fixed** in the
  same PR: `pave/twokey.py` gains a rule over the reader and the record (AI Quality,
  Platform Engineering, Security), pinned in `tests/test_twokey_seats.py`.
- **Security (blocking) — the L2 lane prints a count at 7700.** Run before opening:
  `control_passed 17, tools_passed 15`, the comparator holds. The amendment separates
  M02's one-tool evidence from the claim.
- **Security, AI Quality — three unpinned constants and a literal `"4"` in the
  derivation test**; re-pointing it at stage 1 or M06b survived. **Fixed**: the
  four-call anchor is derived two ways from the record and the two must agree.
- **Security — the placement test was vacuous on an empty budget set.** Fixed.
- **Tool Owner — the manifest margin and the placement rule disagree for the first
  time.** Fixed by deciding it in writing: the margin governs the manifest
  (`max_tokens_in` 6500 → 8200), the placement governs the per-case ceiling, and the
  new test fails any case at or above 8181.
- **Tool Owner — the band's input could be read as the as-run 6792.** Declined and
  recorded: SPEC/08 pre-registered the mandated-shape maximum 6235 by name at PR 1.
- **AI Quality — `services/*/evals/` collects AI Quality alone.** Declined on this PR
  as predating M08; the point pin now puts any move onto the derivation file's two
  keys as well.
- **All four — `tests/test_g4_capture_boundary.py` is vacuous in any checkout under a
  `.claude/` directory.** Pre-existing, not PR 3's diff; carried below as a dated debt.

## What broke?

**The ceiling was set for a two-call shape, and the product became a three-call shape
at M06b.** ADR-014's M02 amendment derived `tokens_in` for a tool loop that made two
model calls per turn. At M06b `entitlement-check` became a second *sequential* tool
round, so the modal turn became three calls and the per-call base went from 1693 to
2057 tokens — and nothing re-derived the ceiling for the shape that replaced the one
it was written for. The census reads it exactly: every 2-call turn is under 6000 and
every 3-call turn is over it, across all 52 three-call turns, with the minimum at
6022. The number was never wrong for the shape it was derived for; it was applied for
four milestones to a shape it had not been derived for.

**Refusals hid it for four milestones.** M06b's seven answered-and-wrong cases all
failed `budget` behind seventeen refusals; M06c and M06d read that same run again
and recorded nothing, their progression cells saying *not re-scored*; M07 stage 1
had six behind eighteen. The moment stage 2 cleared the
refusals, twenty-two of twenty-two answered-and-wrong cases were budget failures and
the ceiling was the whole number. A control that refuses most of a suite makes every
other axis unreadable, and nothing in the instrument said so until M06d taught it to
print *refused before scoring* separately.

**The number was derived by a rule the seats found was not in the repository — and
now is.** PR 3 wrote that the point rule (the band's midpoint, rounded to the nearest
hundred) was pre-registered. It was written in a plan approved in conversation. All
four seats found it independently, and the disposition was not to argue that a
conversation counts: the claim was withdrawn, the rule was written into
`tests/test_budget_derivation.py` where it is executable and two-key, and ADR-014
amendment 2 says where it actually came from. The standing rule out of it: **a rule
approved in conversation is not pre-registered.** It becomes pre-registered when it
is committed as an artifact somebody can read back — and for a rule that picks a
number, that means executable and pinned, not written down.

**The fourteen browse-gap samples are the ceiling working, and they are also the next
defect.** Seven cases — `recommend-003`, `recommend-013`, `recommend-014`,
`grounded-018`, `grounded-019`, `multi-023`, `edge-025` — carry every four- and
five-call turn in the committed stage-2 evidence, every one a `catalog-search` call
beyond the mandate before `entitlement-check` or the answer, and every one fails
`tokens_in` at 7700 as the placement rule intended. All but `grounded-019` also fail
a citation or grounding assert **on the same sample**: the extra call and the wrong
citation arrive together. So today the ceiling catches by *shape* what the citation
asserts already catch by *content*, and a reader of the count alone would take the
budget axis to be costing thirteen cases when it costs none. The day a four-call turn
cites correctly, `budget` is the only assert that still names it. That is what a
ceiling placed below the next call count is for, and the seven cases are handed to
the Tool Owner seat for M10.

**The register had no shape for a re-reading, and PR 4 recorded nothing.** Simulated
in a scratch copy before the run, a row tagged `m08` citing M07's three files was
refused three ways by `pave/history.py`: the evidence sits outside `milestones/M08/`;
`m07-tools-goldens.json` already cites it, and one run is one row; and README's `m08`
row was pinned to no entry. `--supersedes` was the wrong verb — M07's 2/25 was a
correct reading of the same samples at the ceiling of its day (ADR-027). The operator
dated the shape to this close, and it is here: an entry kind that names the run it
re-reads, the threshold it re-reads it at and the golden file it was scored against,
and that answers each of the three refusals with a **narrower** rule rather than a
wider one — it may cite exactly the re-read row's evidence and nothing else, there is
one re-reading per (row, assert, value) with the threshold read out of `git show` at
both commits, and README publishes both readings or is red. The rule for fresh rows
is untouched, and the plant that proves it —
`test_a_row_citing_another_milestones_files_without_rereads_is_still_refused` — was
the condition on writing the entry at all.

**Four of eighteen new checks were silent, and the audit is what said so.** Every
check added here was deleted in turn and the suite re-run. Fourteen went red. Four did
not: `check_rereadings` removed from `run_all` (so the *gate* would not run it, only
this file's tests), and all three of the recorder's `--rereads` guards, because every
test planted a row and none drove the producer. Fixed before the entry was written,
with a test each. The pattern is M06d's and ADR-042's: a check nobody planted against
is a check that may not be reachable, and *four of ten* is the historical rate.

**`cases_sha256` was named as the mover and is not a field this row has.** ADR-014
amendment 2 said *"PR 4's entry will carry a new value"* for `cases_sha256`. That key
is `instrument.deterministic.cases_sha256`, written by `evals/judged.py` for a judged
reading; an unjudged goldens row has no such key. What did move is the census's
provenance digest of `cases.yaml` (`b0e874a8…` → `f59f4a39…`), which is the value the
re-reading's `cases_file.sha256` carries and which `check_rereadings` reads back out
of both commits. The ADR was not edited; the correction is in amendment 3.

**Small things, measured and left.** `goldens-rescore.txt` prints the census record's
absolute path in Windows form, because that is what the reader prints — committed
as-run, not edited. `.gitattributes` declares `eol=lf` and 191 tracked files are CRLF
in this working tree and LF in the index, so any reader that digests the checkout
rather than the blob gets a different number locally than CI does; every digest in the
register normalises, which is why nothing is red, and the debt is dated below.

## Open holes and triggers (close-milestone step 6b)

**No new baseline run.** M08 moved no guardrail, policy or topic wording and made zero
model calls, so the triggers are read from M07's committed refusal census — the last
governed golden run, and the run this milestone re-read — on M06d's precedent for a
milestone that records no run of its own.

- **`enforcement-probing`'s trigger** (ADR-035 amendment 9): footprint **0 of 25**
  (both refused samples are `TOPIC:entitlement-circumvention`, which names no golden
  case), `blackout-009` refused **0 of 3**. Neither trigger fires. Nothing returns to
  the seat.
- **`ATK-003`** — 0 of 3, unchanged. Its deadline was M07 and it was dispositioned
  there as a scale cut with two keys (ADR-062 amendment 1); the row keeps
  `expect: blocked` and keeps failing, so the hole stays visible.
- **Carried forward, the two triggers PR 2 recorded.** *Security's two `tool_request`
  probes*: declined as corpus rows because no deployed arm can plant a model-authored
  tool name, so under ADR-041 they credit nothing on every arm; the two loop tests are
  the standing observation, and **the first arm that can plant a name re-opens them**.
  *Retention on the withheld store* (ADR-071 amendment 1): decision 4 upheld with no
  channel exemption, retention is Data Governance's open item, and **the trigger is
  the first second reader of the store, or any change to what it keeps**.

## Decisions

- **ADR-073** — three decisions before the code and four amendments. M08 takes the
  budget question and the rules registry moves to M09 (D1, the operator's); two
  outcomes pre-registered with the rule that picks between them written before the
  census was read, and the reader's first run — which printed outcome A under an
  incoherent reading — kept in the record (D2); how a ceiling may move under G9 (D3).
  Amendment 1 is a cold read of the spec that found the side-prediction unreachable as
  written; amendment 2 is what PR 2 carried and the wording PR 3 could only fill a
  number into; amendment 3 is PR 4's count in those pre-registered words; **amendment
  4 is this close** — the register's re-reading shape, the entry, the row.
- **ADR-014 amendment 2** — `tokens_in` 6000 → 7700, argued from the census by the
  pinned rule and from nothing else, with three sentences pre-registered before the
  number: outcome B is *not-A on the evidence admitted*; the ceiling carries its own
  re-derivation trigger if the unattributed residual is ever attributed to content the
  agent can stop sending; and the axis discriminates **call count ≥ 4**, not calls
  above a case's mandate.
- **ADR-070 amendment 8** — the channel table re-derived from M06b's sidecar; the two
  `tool_request` probes disposed; `recommend-003`'s held text read against `DEC-001`.
- **ADR-071 amendment 1** — Data Governance upholds decision 4, no channel exemption.
- **ADR-026 amendment 3** — the `brand_tone` widening re-deferred to M09, in the same
  diff as the progression table this time.

## Debts carried out of M08, each with a date

| debt | owed to | date |
|---|---|---|
| The residual 422–537 tokens per call the census cannot attribute — a quarter of the per-call base, the same size with one tool offered as with two (`residual-differential.json`). Paid by per-call `inputTokens` in the answer file and one calibration call with tools offered | Platform Engineering + AI Quality | **M09 PR 1** |
| The rule that derives a suite `p95_ms`, written before M09's fresh run and applied after it. `p95_ms` stays 2500 and stays OVER; a standing finding, not a regression | AI Quality + Platform Engineering | **M09 PR 1** |
| `BANDS` in `tests/test_budget_derivation.py` is guarded by no direct pin: a roof raised while the four-call cap binds survives | AI Quality + Platform Engineering | **M09 PR 1** |
| `calls` in the budget failure record — `tokens_in=8181 over 7700` does not say it was a four-call turn. Declined for M08 (an instrument change), the hand-join paid once in `rescore-join.json` | AI Quality + Platform Engineering | **M09 PR 1**, beside the per-call usage debt |
| `recommend-003`'s answer-channel refusal: on both samples a schema-conforming **grant** carrying `entitlement-check`'s verdict into the final answer, not `DEC-001`'s refusal-plus-alternative. Read, not fixed — a topic question or an answer-policy question, undecided | Security (with Legal/S&P if it is answer policy) | **M09 PR 1**, at the fresh run |
| The DMA rename (SPEC/06b A21). It moves `data/catalog.json` — the judge's prompt digest — and the enum in the tool spec the census measures | Legal/S&P + Data Governance | **M09 PR 1, a named slide** |
| `templates/agent-tools/` carries `tokens_in: 6000` and `max_tokens_in: 6500`: correct for the one-tool shape the scaffold renders, wrong the moment a scaffolded service adds a second tool — which is the shape this milestone re-derived a ceiling for | ADR-047's four seats (Platform Engineering, AI Quality, Tool Owner, Security) | **M09 PR 1** |
| `tests/test_g4_capture_boundary.py` is vacuous in any checkout under a `.claude/` directory — found by all four seats on PR 3, pre-existing, not that diff's | Security + Platform Engineering | **M09 PR 1** |
| `.gitattributes` declares `eol=lf` and 191 tracked files are CRLF in the working tree and LF in the index. **`.gitattributes` is on no `pave/twokey.py` rule**, so the file that decides how every byte-level check reads a checkout takes one key — which is the finding, beside the renormalisation | Platform Engineering | **M09 PR 1** |
| `docs/adr/README.md`'s index rows for ADR-014 and ADR-073 name their amendments as of this PR, and **no check reads the index**: the clause that an amended ADR shows where it was corrected is enforced by nobody | PM seat | **M09 PR 1** for the check |
| The seven browse-gap cases — the extra `catalog-search` call and the wrong citation arrive together, on the same seven cases, in every committed stage-2 sample that ran long | Tool Owner, no ADR | **M10** |
| The five `tokens_out` cases at unchanged tiers — `blackout-001`, `blackout-007`, `blackout-008`, `blackout-009`, `concise-022` — which no `tokens_in` move can reach | AI Quality | **M10** |

Carried unchanged, already dated: ADR-069 D5 cut 2, the paired diff's partition (the
next two-arm run); `usage.tokens_in: 0` on refused answers; the `brand_tone` widening
(M09, the milestone that adds graded content).

## What's next

**M09 runs the arm again, and the ceiling stops being the answer.** Every number in
this milestone is a re-reading of a fixed set of samples; nothing here says what the
agent does today. M09 PR 1 takes the fresh run, and it takes it with four debts due in
the same PR that decide whether the next budget number means anything: per-call
`inputTokens` (a quarter of the per-call base is still unattributed), the p95 rule,
the `calls` field in the failure record, and `recommend-003` read again. Then claim 6
— the rules registry and the regdelta loop — measured on an arm whose budget axis can
finally tell a runaway loop from a normal turn.

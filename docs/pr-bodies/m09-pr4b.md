# M09 PR 4b — the goldens control run, and F4 fired too: the claim is FAILED on two falsifiers

**F4 fired on `grounded-017`.** The twenty-five were re-run at k=3 through the same
deployment, after PR 4's fix, as the control for the one question F4 asks: *did one
disclosure sentence in `TOOL_SYSTEM` move anything but the disclosure pack?*

**And the count did not notice.** `N = 10/25` — inside the band [8, 12], on the
predicted 10, and exactly what M08b published — because `entitlement-011` gained a
majority as `grounded-017` lost one. That is the compensating movement SPEC/09
described when it moved the two direction predicates **into** F4 and demoted the
count to a side-prediction, happening at two cases on the first run after the
change.

**The claim is FAILED, on two falsifiers.** F1 fired at PR 4 on `disclosure-103`.
F4 fires here. Nothing below offsets F1, and a side-prediction landing on its
predicted value is not partial success.

---

## 1. The pre-flight, and its match to PR 4's

`run_with_tools.py --preflight-only` before the first call, and the run printed its
own header again. Both were diffed against PR 4's committed run A and run B headers
after LF normalisation: **the sixteen pre-flight lines are identical on all four.**
Line seventeen is each run's own `tag`/`sample`/`k`, which is per-run by
construction.

```
gateway:  BeaconpaveGateway-GatewayFn1123A784-2LHF1oy9C98J   (last modified 2026-09-08T02:40:45.000+0000)
  GUARDRAIL_ID                     abayh4ye7f8o          stack PinnedGuardrailId=abayh4ye7f8o
  GUARDRAIL_VERSION                4                     stack PinnedGuardrailVersion=4
  TOOL_OUTPUT_GUARDRAIL_ID         ggla7vqlfu7d          stack ToolOutputGuardrailId=ggla7vqlfu7d
  TOOL_OUTPUT_GUARDRAIL_VERSION    1                     stack PinnedToolOutputGuardrailVersion=1
deployed bundle: CodeSha256 /O4tiCrf9UFu9GWGaL0n4YCjuGswLeHH9lcEHp1UVLc=
  handler.py           141d618e…  == tree
  core/toolloop.py     13c87d5d…  == tree
```

No deploy was taken in this milestone and none was needed. The full header is the
first seventeen lines of `milestones/M09/goldens-run-transcript.txt`.

## 2. The empty diff, and why it is wider than PR 4's

`milestones/M09/nothing-moved-since-run-b.{sh,txt}`, `369c8ba..HEAD`:

| path | changed files |
|---|---|
| `platform/gateway/core/guardrail.py`, `handler.py`, `core/`, `policy/` | 0 |
| `platform/infra/lib/gateway-stack.ts`, its synth fixture | 0 |
| `quality/adversarial/` | 0 |
| `data/catalog.json` | 0 |
| `services/highlights-agent/pave.manifest.yaml` | 0 |
| `services/highlights-agent/evals/golden/cases.yaml` | 0 |
| **`services/highlights-agent/evals/answer.schema.json`** | **0** |
| **`services/highlights-agent/gateway_client.py`** | **0** |

Empty, no carve-out, and the working tree equals HEAD over the same list. **The last
two are in this list and were not in PR 4's**: there they *were* the fix; here the
fix is the variable under test and must be frozen, which is the difference between a
control and a second experiment.

## 3. The run

25 cases × k=3 = 75 samples, `--tag m09-goldens-control`, **no INFRA sample**, so
constraint 5's one whole-sample re-run was not spent. Committed as-run:
`goldens-run-{1,2,3}.json` and their trajectories, `goldens-run-refusals.json`,
`goldens-run-transcript.txt`, `per-sample.txt` (11/25, 10/25, 9/25),
`goldens-score.txt`, and `fresh-join.json` written by **M08b's own committed
`fresh_join.py`** at the same 7700 ceiling.

## 4. The twenty-five, with each failure's named cause

From `milestones/M09/f4.txt`. Causes are read from the records that name them — the
M08b refusal census, `fresh-join.json`'s `tokens_out` trigger, and ADR-074 decision
2's seven browse-gap cases — never from a list in this document.

| case | M08b | M09 control | cause here |
|---|---|---|---|
| `blackout-001` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_out=357 over 300` · tokens_out |
| `blackout-006` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_out=310 over 300` · tokens_out |
| `blackout-007` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_out=326 over 300` · tokens_out |
| `blackout-008` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_out=352 over 300` · tokens_out |
| `blackout-009` | FAIL `[F F F]` | FAIL `[F F F]` | refused 3 of 3 · guardrail topic |
| `entitlement-002` | FAIL `[P F F]` | FAIL `[F P F]` | `tokens_out=345 over 300` · tokens_out |
| `entitlement-010` | PASS `[P P P]` | PASS `[P P P]` | — |
| **`entitlement-011`** | FAIL `[P F F]` | **PASS `[P P F]`** | — (the compensating mover; not a falsifier — it failed 2-of-3 at M08b, not 0-of-3) |
| `entitlement-012` | FAIL `[F F F]` | FAIL `[F F F]` | `json_schema`, `entitlement` · **named by neither list** |
| `recommend-003` | FAIL `[F F F]` | FAIL `[F F F]` | `json_schema`, `must_cite`, `must_mention` · guardrail topic + browse gap |
| `recommend-013` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_in=8949 over 7700 (calls=4)` · browse gap |
| `recommend-014` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_out=525 over 500` · browse gap |
| `recommend-015` | PASS `[P P P]` | PASS `[P P P]` | — |
| `grounded-016` | PASS `[P P P]` | PASS `[P P P]` | — |
| **`grounded-017`** | **PASS `[P P P]`** | **FAIL `[P F F]`** | **`tokens_out=337 over 300` · named by neither list — F4.2** |
| `grounded-018` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_in=9365 over 7700 (calls=4)` · browse gap + tokens_out |
| `grounded-019` | PASS `[P F P]` | PASS `[P P P]` | — |
| `brand-020` | PASS `[P P P]` | PASS `[P P P]` | — |
| `brand-021` | PASS `[P F P]` | PASS `[P F P]` | — (s2 refused here; same majority) |
| `concise-022` | FAIL `[F F P]` | FAIL `[F F F]` | `tokens_out=327 over 300` · tokens_out (s3 refused) |
| `multi-023` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_in=14584 over 7700 (calls=6)` · browse gap + tokens_out |
| `edge-024` | PASS `[P P P]` | PASS `[P P P]` | — |
| `edge-025` | FAIL `[F F F]` | FAIL `[F F F]` | `tokens_in=9956 over 7700 (calls=4)` · browse gap + tokens_out |
| `headroom-005` | PASS `[P P P]` | PASS `[P P P]` | — |
| `headroom-026` | PASS `[P P P]` | PASS `[P P P]` | — |

**`recommend-003` changed how it fails without changing whether it fails** — refused
2 of 3 at M08b, 1 of 3 here, and it now fails on content. F4 has no clause for that,
and a reader comparing verdicts alone sees a case that did not move.

## 5. F4, against its two direction falsifiers and its ceiling clause

| clause | reading |
|---|---|
| **F4.1** — a ≤3-call answered sample over 7700 that was **under it at M08b** | **clean.** 61 samples at ≤3 calls, max **7280**; 8 at ≥4, min **8949**. Both falsifier lists in `fresh-join.json` are empty and the per-sample claim holds |
| **F4.2** — a case that **passed 3-of-3 at M08b** fails by majority | **FIRED — `grounded-017`.** All 8 such cases read |
| **F4.3** — a case that **failed 0-of-3 at M08b** passes by majority | **clean.** All 12 such cases read |

**`grounded-017`'s M08b samples were 288, 289, 298 against a tier of 300** — every
one under it by between 2 and 12 tokens. Run-wide mean `tokens_out` moved +6.6
(346.8 → 353.4); this case's own moved +50.7.

**The count is reported as a side-prediction and nothing else.** `N = 10/25`, band
[8, 12], predicted 10, in band, on the number. `milestones/M09/f4.py` prints it after
F4's verdict and labels it `SIDE-PREDICTION (not F4, not the claim)`, and
`test_the_count_is_printed_after_the_falsifier_and_labelled` pins the ordering — a
reader who stops at the first number must not stop at the one that did not fire.

**Refusals**, also a side-prediction: **1 of 25 by majority** (`blackout-009`, 3 of
3) against 0–2, in band and down from M08b's 2. But **4 of 25 refused at least
once** — ADR-035's own estimator — against M08b's 2: `brand-021` and `concise-022`
newly, both `TOPIC:entitlement-circumvention` on the **answer** channel. Recorded for
Security and handed to M09b, not diagnosed (decision 5 §3's pre-registered
disposition).

## 6. The falsifier set, closed

| | falsifier | reading | where |
|---|---|---|---|
| **F1** | a positive disclosure case passes before the fix | **FIRED** — `disclosure-103`, 2 of 3 | PR 4 |
| **F2** | a positive case fails after the fix | clean | PR 4 |
| **F3** | the gate does not block then permit | clean — exit 1, then 0 | PR 4 |
| **F4** | the fix moved something else | **FIRED** — `grounded-017` | **here** |
| **F5** | the negative case discloses after the fix | clean | PR 4 |

**THE CLAIM IS FAILED.** It was failed when F1 fired and it is failed now. F4 is a
second falsifier, not a re-reading of the first. The close writes ❌ and names both
cases.

## 7. The prompt delta, measured

Round 1 of every case is deterministic, and the two runs differ in exactly the
prompt — so the control run measures what PR 4 could only price.

| | |
|---|---|
| priced (amendment 5) | 200 per call |
| **measured** | **165 per call**, on **24 of 24** cases, variance zero |
| admissible | 306 |
| binding sample | `headroom-005`, 3 calls: 6782 (M08b) → **7280**, **420 under 7700** |
| predicted worst case at 200 | 7382 |

The estimator over-predicted by 35 tokens per call, in the conservative direction.
`tokens_in` stays 7700 and was never a candidate to move.

**The fix reached the twenty-five without moving a verdict.** 0 of 75 M08b answers
carried a non-null `ai_disclosure`; **7 of 75** do here — `headroom-005` and
`headroom-026` on all three samples, `brand-021` on one, all editorial-copy requests,
all the same sentence, none of them a verdict change. `grounded-017` is not among
them: its failing samples carry `null` and, on sample 3, no key at all.

## 8. p95, recorded and not acted on

Pooled **5630 ms OVER 5200** (n=69); mandated shape **4900 ms within** (n=36). That
is the *share* reading ADR-014's rule was written to report — the browse gap's — and
the first time since M07 the two have separated. The mandated tail now reads
**3769 → 5241 → 4900** across three runs, which is further evidence for the premise
ADR-014 amendment 4 withdrew. **`gates.budgets.p95_ms` does not move** (constraint 1):
the gate does not move to clear a reading and does not move to follow one. 4900 sits
outside the condition's firing window (3782, 4824) in any case.

## 9. The two re-datings this PR owed

**The cascade debt.** Amendment 5 dated it *"the next PR that opens
`residual_attribution.py`"* — a trigger that cannot arrive in time, and PR 4 is the
proof: nobody opened the reader, a prompt constant moved, and the published
attribution went 92.9% → 78.6% with no run between the readings. **Re-dated: AI
Quality + Platform Engineering; trigger — before the first PR that edits any prompt
constant.** Enforced, not tabled:
`tests/test_m08b_residual.py::test_a_prompt_constant_may_not_move_before_this_records_era_debt_is_paid`
pins `gateway_client.py`, `answer.schema.json` and `milestones/M08/context-census.json`
and goes red on that edit, naming the debt and refusing the obvious remedy —
re-pinning the digests is the guard being deleted by the change it exists to catch.

**The figure.** One line beside M08b's published number: it is **era-pinned to
M08b's prompt**, and re-producing the record against a later prompt yields a
different figure by construction. **92.9% is not changed** — it is the reading of
that run. **78.6% is the artifact.**

**The `fresh_join.py` render debt**, dated to PR 4b by SPEC/09's obligation table:
`emit()` transliterates rather than raising `UnicodeEncodeError` on a cp1252 console,
with the relation (`≤`) preserved rather than replaced by `?`. Four tests, each
measured red when deleted.

**The comparator pin: offered to this PR and not taken**, with the reason recorded
(amendment 6 §9). It needs a generic suite lane `pave/cli.py` does not have, and the
value it would pin is 7/7 over a pack this milestone recorded as returning 6/7 on one
case. Re-dated to the first PR that takes a second disclosure run.

## 10. Findings this PR leaves behind

**(a) The committed reader's direction block answers against M08, and would have
reported F4 clean.** `fresh_join.py`'s `count.falsifiers` carries
`3_of_3_pass_at_m08_failing_by_majority`, compared against
`milestones/M08/rescore-join.json` — a module constant. Run over M09's directory it
reports both lists empty: true of M08, false of M08b, because `grounded-017` did not
pass 3-of-3 at M08. F4's clauses name M08b. `milestones/M09/f4.py` exists for that
reason, and `test_the_committed_records_direction_block_answers_against_m08_and_says_clean`
pins the disagreement so nobody deletes the second reader as duplication. **Owner: AI
Quality + Platform Engineering. Trigger: the next milestone that re-runs the goldens
as a control.**

**(b) F4 cannot separate the prompt delta from run-to-run generation drift.** A
single post-fix run against a pre-fix run confounds the two; separating them needs a
paired arm at the pre-fix prompt on the same day, which no milestone has budgeted.
M08b's own count moved two cases against M08 on drift with the prompt unchanged, and
both movers sat within a sample's margin of a tier, exactly as `grounded-017` does.
**This is not a reason to re-read F4** — it is pre-registered, it fired on its own
terms, and re-reading a falsifier until it stops firing is on SPEC/09's forbidden
list by name. It is a finding about what F4 establishes: it detects movement and
attributes none. **Owner: AI Quality. Trigger: the pre-registration of the next
milestone whose claim is *nothing else moved*.**

**(c) A tier cleared by two tokens is not an instrument that survives a run.** Added
to **09c**'s inheritance as a read, not a diagnosis (constraint 9). The second time
this repository has recorded a majority moving on a single-sample margin.

**(d) The G4 store-reach guard bit a legitimate edit, correctly.** `emit()` was first
written with `getattr(stream, "encoding", None)` and
`test_the_reader_imports_no_network_module_and_takes_no_ceiling` refused it as a
reflection door. Rewritten as `try: stream.encoding`. Recorded because a guard firing
on honest work is the evidence that it would fire on dishonest work.

**(e) Two checks expired on this PR's own correct changes**, both narrowed with the
reason in the diff rather than deleted. `test_a_disclosure_entry_validates_and_forces_no_readme_row`
asserted no `check_readme` problem mentioned `"m09"`, which was true only while no
`m09` goldens row was pinned — it now asserts nothing mentions `"disclosure"`, which
is what the claim under test always was. And the cascade closure grew to include
`milestones/M09/fresh-join.json`, a record produced *after* the fix by construction;
the assertion is split into the two directories the Definition-of-done clause names
plus a rule (not a list) for everything else, so a sixth record under any other
directory is still red.

## 11. The deletability audit

`python milestones/M09/pr4b_deletability_audit.py`, output committed as
`milestones/M09/pr4b-deletability-audit.txt`. Working copies backed up to a temp
directory and restored from it byte for byte — **never `git checkout`** — and the
script refuses a mutation whose target text does not appear exactly once, so a
mutation that silently changed nothing cannot be counted RED for free.

| # | mutation | caught by | result |
|---|---|---|---|
| 1 | f4: clause 1 returns `[]` | `test_every_clause_is_reachable_and_none_is_decorative` | **RED** |
| 2 | f4: clause 2 returns `[]` — the clause that FIRED | `test_clause_2_fired_on_grounded_017` | **RED** |
| 3 | f4: clause 3 returns `[]` | `test_every_clause_is_reachable_and_none_is_decorative` | **RED** |
| 4 | f4: the case-set guard stops refusing a short baseline | `test_the_reader_refuses_a_baseline_and_a_run_with_different_case_sets` | **RED** |
| 5 | f4: the count loses its `SIDE-PREDICTION` label | `test_the_count_is_printed_after_the_falsifier_and_labelled` | **RED** |
| 6 | f4: the reading stops saying the claim was already FAILED on F1 | same | **RED** |
| 7 | f4: a case id typed in beside the baseline | `test_the_baseline_is_the_published_entry_and_not_a_list_in_the_reader` | **RED** |
| 8 | f4: the browse-gap seven become six | `test_the_seven_browse_gap_cases_are_seven_real_cases` | **RED** |
| 9 | `fresh_join`: the cp1252 fallback removed | `test_the_render_path_survives_a_cp1252_console` | **RED** |
| 10 | `fresh_join`: the fallback loses the relation (`errors="replace"`) | `test_the_fallback_keeps_the_relation_rather_than_replacing_it` | **RED** |
| 11 | `fresh_join`: the fallback runs on every stream, not only the refusing one | `test_a_stream_that_can_carry_the_report_is_written_once_and_unchanged` | **RED** |
| 12 | `README_GOLDENS` stops pinning `m09` | `check_readme`'s exact-set, both directions | **RED** |
| 13 | row 09's bold `10/25` removed while the entry stays on disk | `check_readme`: an entry whose row is pinned to none | **RED** |
| 14 | the era line beside 92.9% removed | `test_the_published_figure_names_its_era` | **RED** |
| 15 | a prompt constant moves — the event the trigger exists for | `test_a_prompt_constant_may_not_move_before_this_records_era_debt_is_paid` | **RED** |
| 16 | a record outside the governed directories digests the prompt | `test_the_records_the_fix_moves_are_derived_and_not_listed` | **RED** |
| 17 | ADR-075 stops naming `milestones/M09/fresh-join.json` | `test_the_spec_names_every_record_the_cascade_moves` | **RED** |

**17 mutations, 17 RED, 0 SILENT.** Rows 15 and 16 were additionally re-run without
`-x` to confirm the red is the named test and not collateral.

## 12. Checks

- `make check`: **PASS — 4402 passed, 6 skipped**. Main at `369c8ba` measures
  **4323 passed, 6 skipped** on the same command; the brief's 4213 is a count from an
  earlier point in the milestone. Delta +79, which is 18 new tests plus the
  per-citation parametrisation in `tests/test_cited_commits_resolve.py` picking up
  this PR's documents.
- `tests/test_cited_commits_resolve.py`: 137 passed. Commits cited — PR 1 `66bb114`,
  PR 2 `666a7de`, PR 7 `6644c1d`, PR 4 `369c8ba` — all reachable from `main`.
- `python -m pave.cli gate two-key --changed <the 30 changed paths>`: four rules
  fire, attested below.
- Zero model calls outside the run. **Turns: 40 in PR 4b, 42 in PR 4 — 82 of the 180
  ceiling.**

## 13. Two-key

Four rules fire over this diff: *recorded history*; *the history checks*; *committed
goldens evidence*; *the M08 census — the reader and record the `tokens_in` ceiling is
derived from, and M08b's and M09's readers, records, fixture and tests*.

Two-Key-Disposition: ai-quality
Rationale: The entry is a control run recorded as-run and not edited; the baseline it
is read against is M08b's published entry, byte for byte, and no case, tier,
threshold or baseline moved. F4 fired and is recorded as fired; the count is reported
after it and labelled a side-prediction, with a check pinning that order. The 10/25
in row 09 is what the entry records.

Two-Key-Disposition: platform-eng
Rationale: The pre-flight is identical to PR 4's on all sixteen lines, the deployed
bundle digests equal the tree, no deploy was taken, and the diff over the guardrail,
policy, corpora, tiers, topics, catalog and both model-facing sites is empty. The
`fresh_join.py` change is the render path only and moves no record; `f4.py` writes
nothing. `gates.budgets.p95_ms` and `tokens_in` do not move.

Two-Key-Disposition: security
Rationale: No guardrail, policy, corpus or topic moved and no probe ran. The refusal
census is recorded as-run: 1 by majority in band, and two newly-refused cases on
`TOPIC:entitlement-circumvention` on the answer channel are handed to M09b as a topic
false-positive finding rather than diagnosed here. The G4 store-reach guard refused
a `getattr` in the new render path and the code was changed, not the guard.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

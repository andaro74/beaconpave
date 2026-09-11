# M08b — the ceiling, measured on samples it was not derived from

**Branch:** six PRs (#128–#132 and the close) · **Tag:** `m08b` · **Closed:** 2026-09-08
**Spec:** `SPEC/08b-ceiling-on-fresh-samples.md` · **Claims advanced:** none (serves 2
defensively; hands claim 6 a measured arm)

> **The claim held, and everything it was measured beside moved.** M08 re-derived
> `tokens_in` to 7700 from a census of the 75 samples M07 recorded, and every number
> in that milestone was about those samples. This one ran the arm again — k=3 through
> the deployed gateway, 76 turns of a ceiling of 152, no INFRA sample, nothing about
> the product changed before the run — and read the ceiling per sample on samples it
> was not derived from. **It holds: all 58 answered samples at three model calls or
> fewer pass at 7700, the largest at 6782; all 12 at four or more fail it, the
> smallest at 8351.** Both falsifier lists are empty, and the claim landed in the
> middle of the gap it risked with **918 tokens of headroom on one side and 651 on
> the other**. What did not hold is the scaffolding around it: the count came in at
> **10/25** against a predicted 12, and both movers fail on `tokens_out` at unchanged
> tiers rather than on the ceiling; the suite `p95_ms` rule's premise failed, because
> the mandated shape's own tail went **3769 → 5241 ms** and the ceiling derived from
> it is 5200; the residual is **provider-side framing, 501 tokens of 463 signed
> (92.9%)**, and neither half is content the agent can stop sending. Six PRs of a cap
> of six, spent at PR 1b on a cold read of the plan, which is why the DMA rename slid
> a fourth time — by name, as pre-registered.
>
> **That 92.9% is era-pinned to M08b's prompt, and the number is not a standing
> property of the system.** `E` and `S` are estimated from the committed prompt
> text and joined to `A` and `B`, which this run measured; re-producing
> `residual-attribution.json` against a later prompt therefore yields a different
> figure **by construction**, and M09 PR 4's two model-facing edits already moved
> it to 552 of 402 (78.6%) with no run taken between the two readings. **92.9% is
> the reading of this run and stands; 78.6% is the artifact of a prompt this run
> never sent.** ADR-075 amendment 5 §4(a) records the mechanism, amendment 6
> re-dates the fix, and `tests/test_m08b_residual.py` goes red before the next
> prompt constant moves.

## What can I demo right now?

**The join, the count, the refusal census.** Hermetic; every input is committed; zero
model calls:

```bash
python milestones/M08b/fresh_join.py --check
python -m evals.run_evals --arm tools \
    --answers milestones/M08b/goldens-run-1.json \
    --answers milestones/M08b/goldens-run-2.json \
    --answers milestones/M08b/goldens-run-3.json \
    --refusals milestones/M08b/goldens-run-refusals.json
python -m evals.refusals --sidecar milestones/M08b/goldens-run-refusals.json
```

```
OK: milestones/M08b/fresh-join.json is what the committed inputs produce
10/25 passed (15 failed, 0 infra) — judge axes recorded ADVISORY, not scored (ADR-012)
of the 15 failed: 2 were refused before scoring, 13 answered and scored wrong
refusals: 5/5 resolved to 2 (mechanism, assessed) pairs — guardrail / TOPIC:enforcement-probing,TOPIC:entitlement-circumvention; guardrail / TOPIC:entitlement-circumvention
suite latency  OVER p95=6633ms over 5200ms
channels: tool_request 0 · answer 5 · question 0 · tool_output 0
```

SPEC/08b predicted that block before the run existed, with `N`, `R`, `P` and `S` left
as letters and **5200** the one number already fixed. The full transcript is
`goldens-score.txt`; the three single-file runs are `per-sample.txt` (12/25, 8/25,
11/25, with pooled p95 6894, 6036 and 6315 ms).

**The claim, which the count cannot show.** The k=3 line is a count; the claim is per
sample, and `fresh-join.json` is the only thing that reads it:

| calls | answered samples | `tokens_in` at 7700 | range |
|---|---|---|---|
| ≤ 3 | 58 | every one PASS | max **6782** — 918 under the ceiling |
| ≥ 4 | 12 | every one FAIL | min **8351** — 651 over the ceiling |

Five samples were refused before an answer and carry no call count at all. Every row
also carries its distance to 7700, to the unrounded midpoint 7675.125 and to the
nearer band edge, its per-call `inputTokens` list, and its per-round growth against
the replayed transcript — the columns ADR-074 amendment 1 §5 asked for so that a red
close could say *which* of the point, the grain, the band or the rule had failed.
`tests/test_m08b_fresh_join.py` pins the record byte for byte; a planted verdict, a
planted call count, a transcript from another ceiling and a total that is not the sum
over its rounds each move it or are refused.

**The entry.** `evals/history/m08b-tools-goldens.json`, recorded at PR 3 with `HEAD`
at PR 2's merge (`90121eb`), naming its three answer files by digest, `refused: 2`,
`k: 3`. It is a **run**, not M08's re-reading: it carries the run's own measurements
and no `rereads` key, and `README_GOLDENS` publishes it beside the `m08` row rather
than instead of it.

## What's the delta vs baseline?

| Metric | m00b (control) | m08b | Mechanism |
|---|---|---|---|
| Goldens | **15/25** | **10/25** | **A fresh k=3 run of the tools arm through the deployed gateway, at the ceiling M08 re-derived and did not move.** Not a re-reading: 75 new samples, 76 turns, recorded as-run. Pooled pass rate 0.4133. Against the last *fresh* reading of this arm — M07's **2/25** at a ceiling of 6000 — the mechanism is entirely the ceiling M08 moved; against M08's **12/25**, which re-read M07's samples at 7700, the mechanism is generation drift on `tokens_out`, and it costs two cases. |
| Refused, by majority | – | **2/25** | `blackout-009` (3 of 3, unanimous) and `recommend-003` (2 of 3). Inside SPEC/01's pre-registered band 0–2, at its ceiling; the falsifier is 3 or more and did not fire. Nothing in M08b touched the guardrail: main pair `abayh4ye7f8o` v4, the same version M07 and M08 read. |
| Adversarial | **0/10** | not run | No corpus edit, no probe run, no arm. Six of the seven instrument digests are unchanged; **m04-I** was registered in PR 2 because the per-round usage list moves `core/toolloop.py`'s digest, and no adversarial scorer reads `usage`. |
| p95 latency | – | **6633 ms** pooled, OVER 5200 | The gate is a derived number for the first time since ADR-016 moved it to suite level: PR 2 derived **5200** from the mandated shape's M07 p95 (3769) inside ADR-014's 1.15–1.60× band, before the fresh number existed. Both readings are OVER, and that combination is the one the rule could not survive — see below. The gate costs no case. |
| Tokens in | – | **A = 1900** on the calibration case, round 1 | The first per-call `inputTokens` this repository has recorded. The residual splits by identity with no remainder: **D = −38** (tokeniser density, the estimate over-counting) and **F = 501** (provider framing), shares 0.071 and 0.929 of \|D\| + \|F\|. |

**Honesty check.** The pass count went **down** by two against M08's reading of the
same 25 cases, and the mechanism is named: `entitlement-002` and `entitlement-011`
each fail `tokens_out` at an unchanged tier by one sample's margin — **307 and 308
against 300** — and each was a 2-of-3 pass at M08. No case that passed 3-of-3 at M08
fails by majority here, and no case that failed 0-of-3 passes. Nothing about the
count is a `tokens_in` movement: **the ceiling this milestone exists to test costs
exactly the cases it cost at M08**, and the two it lost are answer-length cases the
`tokens_out` debt already owned.

**Unearned passes:** none. The ten that pass do so on every assert on a 2-of-3 or
3-of-3 majority. Two passes are worth naming as narrow rather than unearned:
`grounded-019` and `brand-021` each pass 2-of-3, and each has a sample that fails.

## The seat rounds, on the instrument and not the number

Five seats reviewed **PR 2 and no other**, in isolated worktrees, in two rounds — the
second on the first's fixes — because SPEC/08b constraint 7 planned it that way after
M08 PR 3 produced seventeen findings from four seats with the fixes in the same PR.
The seats were told what to plant, never what to read, and the question was: *does
the instrument record what the run does, and move nothing about what the run is?*

- **Round one** (`8ab0a9a`, tagged `cited-m08b-pr2-r1`): **nine surviving plants**
  across the four seats with code to attack, plus one blocking finding on the rule
  set from the narrow Legal/S&P review. Thirty-five checks added, every one measured
  red when deleted. The sharpest: the G4 store-reach scan's roots did not include
  `milestones/`, so a planted `from core import withheld` in two of the three new
  readers survived the whole suite; and the grants file that decides F had no shape
  at all, accepting held text beside the boolean, held text as the boolean, and the
  string `"false"`.
- **Round two** (`6863f7e`, tagged `cited-m08b-pr2-r2`): every seat replayed its own
  round-one survivors first — all twenty-nine red by name — then planted afresh
  against the fixes. **Eleven surviving plants and two rule-set findings**, and the
  shape that produced most of them was found by four seats independently: *a fix
  written against the plant it was shown*. `offered = offered + [...]` doubled the
  tool specs after a bind the round-one pin declared verbatim, and `F = A − B − S`
  absorbed the doubling as framing. Thirty-one checks added, every one measured.

A third round was not run: the second's survivors were each the shape-over of a
first-round fix rather than a new class, which is the signal the two rounds were for.
**Nothing the rounds found moved a number the run would be read against** — the
`p95_ms` point, the `tokens_in` ceiling, the bands and every tier are what PR 1 and
ADR-014 left them.

## What broke?

**The claim held, and the rule that produced it would now produce a different
number.** This is the sentence ADR-074 amendment 1 §5 said the spec could not write
before the run, and it is the milestone's most useful finding. The fresh
mandated-shape maximum is **6237** (M08: 6235) and the fresh four-call minimum
**8351** (M08: 8181). By ADR-014's pinned rule those two give floor 1.15 × 6237 =
7172.55, roof 8350, the integer band **[7173, 8350]**, unrounded midpoint 7761.275,
point **7800**. **7700 is inside the fresh band** — so this is not *the number holds
and the rule does not*; it is the number holding, the band still containing it, and
the same rule landing 100 tokens higher on fresh inputs. **Recorded, not ruled on**,
in the words decision 3 pre-registered: 7700 stands wherever the fresh band lands,
because a ceiling moved on a fresh run's band is a re-derivation, and that is a census
milestone with its own rule. M09 gets the fact and not the move.

Two things make the reading safe rather than lucky. The run's own gap — (6782, 8351)
— is **wider on both sides** than M08's (6792, 8181), so the fresh evidence
discriminates the call counts more cleanly than the evidence the number was derived
from, not less. And **no sample landed inside the rounding grain (7675.125, 7700]**,
so the rounding is implicated nowhere in this reading; had one landed there the
milestone would have recorded a near miss or a rounding-caused falsification, and it
recorded neither because neither happened.

**The count missed by two, and it missed on fresh content rather than on the
ceiling.** N = 10 against a pre-registered band of [7, 14] and a prediction of 12.
Inside the band; none of the three falsifiers of the side-prediction fired. Both
movers are from the five cases whose M08 pass was 2-of-3 — the exact margin the band
was built out of — and **both fail on `tokens_out` at an unchanged tier by a single
sample**: `entitlement-002` at 307 against 300, `entitlement-011` at 308 against 300.
The other three of the five held. Of the two that failed 1-of-3 at M08,
`entitlement-012` still fails and `blackout-009` fails differently — it is refused on
all three samples now, which the step-6b section below is about. **A miss of a
side-prediction inside its own band is a finding about the side-prediction**; it does
not touch the claim, and the honest reading of it is that a k=3 majority on a
one-sample margin is not a stable instrument for a two-case prediction.

**The `p95_ms` rule's premise failed, and it is the reading the two-number design
existed to catch.** ADR-074 decision 3 §5 pre-registered two readings against 5200,
because one number cannot tell them apart:

| | M07, the population the rule was derived from | M08b, fresh | against 5200 |
|---|---|---|---|
| pooled | 5431 (n 73) | **6633** (n 70) | **OVER** |
| mandated shape | 3769 (n 40) | **5241** (n 38) | **OVER** |

Pooled OVER with the mandated shape within would have been the share the rule was
written to report — the browse gap's, decision 2's. That is not what happened. The
mandated shape's own p95 is **5241 ms, 41 ms (0.8%) over the ceiling and 1.39× the
3769 the ceiling was derived from**. In the pre-registered words: *latency drift in
the shape itself, a dated finding for Platform Engineering, and the rule's premise —
that the mandated shape's tail is stable across runs — is what failed.* Two things
that follow, and both are constraints rather than conclusions. **The pooled OVER is
no longer evidence about the browse gap**: with the mandated shape itself over the
ceiling, the pooled number isolates no share, which is precisely the discrimination
the two-number reading exists to make. And **`gates.budgets.p95_ms` does not move
again here** — constraint 1 allows it to move once, in PR 2, and it has; a ceiling
re-derived from the run it is applied to is the hazard ADR-073 amendment 1 refused,
so no re-derivation was computed, not even as an illustration. Recorded, not
accommodated. The gate costs no case and none is re-scored on it.

**The residual is provider framing, and the number that was supposed to be
attributable is the smaller half.** ADR-073 amendment 2 §2 bounded 422–537 tokens per
call as unattributed and named the measurement that would split it. It was taken:
**A = 1900** (the fresh round-1 `inputTokens` on `blackout-008`, and its three
samples agree at 1900, 1900, 1900, which the rule required because the round-1
request is deterministic), **B = 796** from one calibration turn on the same viewer
turn with `tools` absent and the same `system`, **E = 834** [830, 835] and **S = 603**
[600, 604] read from the census by named key. So **D = B − E = −38** and **F = A − B
− S = 501**, with **A − E − S = 463 = D + F**, the identity holding with no remainder
and inside the bound. Shares of \|D\| + \|F\| are 0.071 and **0.929**, so the 70% rule
names one: **provider-side framing — what `toolConfig` costs beyond the specs' own
text.** The sign on D is the finding the rule was written with signs to carry:
tokeniser density is real, small, and points the *other way* from what the bound's
authors expected — the census estimate over-counts the committed text by 38 tokens.
**Neither half is content the agent can stop sending**, so ADR-014 amendment 2's
downward re-derivation trigger stays disarmed; it arms only if the round-1 pin fails,
and both halves of that pin are green.

Beside it, and dated rather than triggered: across the **149 later rounds** in the
run, growth against the replayed transcript at the measured density of 3.534
chars/token is **more than a quarter unexplained in all 149** — the unexplained share
runs 0.593 to 0.973 with a median of 0.764. Decision 3 §4 pre-registered a >25%
unexplained growth as a dated finding for Platform Engineering and not a trigger, and
it is recorded as one: **per-round envelope cost is the size of the per-round
content, not a rounding error on it.** No number in this milestone moves on it.

**The DMA rename slid a fourth time, and this is the first slide that was decided
rather than discovered.** SPEC/06b's A21 has been re-dated from M07, to the SPEC/08
PR, to M09 PR 1, to this milestone's PR 5. ADR-074 decision 4 pre-authorised exactly
one more slide and named where it would go — **M09 PR 1, by name**, because M09
re-freezes the judge for the `brand_tone` widening and two re-freezes become one.
The cap fired at PR 1b, the fallback was taken there rather than at the close, and
PRs 2–6 kept their numbers so that every reference written before it stayed valid.
**There is no PR 5.** The difference from the three slides before it is the whole
point: those were found at a close, this one was written down before the PR that
would have carried it, and it cost the rename nothing it was not already going to
pay. Any other slide in this milestone would have been a finding; none happened.

**The cap fell on a review of the plan, not of the code, and the milestone would make
that trade again.** Six PRs were planned against a cap of six with no spare. PR 1b —
ADR-074 amendment 1, a cold read of SPEC/08b by a reader who did not write it, zero
model calls — is what spent the sixth slot. What it bought: two Definition-of-done
clauses that were **unreachable as written** (the census record digests the manifest
PR 2 moves, so *"nothing under `milestones/M08/` changed"* could not have been true;
and `pave/history.py::check_readme` refuses a goldens entry whose README row is pinned
to no entry, so the entry at PR 3 with the row at PR 6 was a planned red); **three
files that decide the claim sitting on no two-key rule**, including
`evals/deterministic.py`, the scorer every recorded goldens count in this repository
is summed from and ADR-037's shape one file over; and **a calibration call with no
producer at all** — nothing committed could send an event with tools absent and the
same system block. The cost is one slide of one debt. The alternative — folding the
reading into PR 2 — is the pre-registration failure ADR-014 amendment 2 records one
PR over, and was declined for that reason.

**Small things, measured and left.** `fresh_join.py`'s render path raises
`UnicodeEncodeError` on a cp1252 console (a `≤` in its header); `--check`, which is
what the demo and the pin use, is unaffected, and both were verified at this close.
The record itself carries one mojibake em-dash in the p95 reading string, committed
as-run rather than edited, because it is what the reader produced and the pin is over
the bytes. `milestones/M08/context_census.py` puts two tool directories at
`sys.path[0]` and PR 4 found it the hard way — three unrelated tests in
`tests/test_mcp_server.py` went red because `import server` resolved to the wrong
tool; fixed on the importing side, recorded and not fixed at the source, because
nothing under `milestones/M08/` moves in this milestone.

## Open holes and triggers (close-milestone step 6b)

**A governed golden run and a fresh guardrail baseline were both recorded**, so every
trigger below is read from this milestone's own evidence:
`milestones/M08b/goldens-run-refusals.json` (the refusal census, from the audit
records fetched back out of the lake) and `milestones/M08b/topic-baseline.json`
(`topic_baseline.py --all --k 3`, zero model calls — `ApplyGuardrail` only, scoring
nothing). Deployed main pair `abayh4ye7f8o` **v4**, tool-output pair `ggla7vqlfu7d`
v1, unmoved by this milestone.

- **`enforcement-probing`, trigger 1 — footprint. Does not fire.** ADR-035
  amendment 9 accepted the topic at an at-least-once footprint of **2 of 25** golden
  cases. Measured here: **1 of 25.** The topic is assessed on one sample of one case,
  `blackout-009` s3, alongside `entitlement-circumvention`; `recommend-003`'s two
  refused samples name `entitlement-circumvention` alone. The trigger is *above* 2 of
  25 and the measurement is below the accepted level, so the cost did not grow.
- **`enforcement-probing`, trigger 2 — `blackout-009` refused by majority. FIRES.**
  Accepted at 1 of 3; measured at **3 of 3, unanimously**, on the `answer` channel,
  all three blocked by the main pair at v4. The first unanimous refusal in a governed
  goldens run since M06b. **This is the second firing of trigger 2** — ADR-035
  amendment 11 recorded the first, at M06b — and that amendment's operative half
  governs this one: *a trigger is recorded as having fired and been answered, never
  as not met.* The reasoning available is the same shape as M06b's, again true and
  again not exculpatory: the topic named on two of the three samples is
  `entitlement-circumvention` and not `enforcement-probing`; nothing about the
  guardrail moved; the case's refusal is generation drift under a fixed control. All
  three are true, and none of them makes the trigger not have fired.

  **The disposition, read beside `answer-channel.json`.** F = 2 and G = 8, so
  **0 < F < G: a topic question** — the topic discriminates among grants of one
  shape, so it is reading content the case supplies and not the structured verdict.
  It is the same reading M07's files give through the same code path (G = 8, F = 1),
  with `blackout-009` the case that joined F while G stayed at 8: the question has
  two witnesses now instead of one. **Returned to the Security seat and accepted for
  now, dated to M09** — the next milestone that changes a deployed guardrail line, so
  the topic's recalibration rides that deploy rather than buying one of its own. It
  is a calibration on the corpus's rule with its own ADR (ADR-064's two refuted
  calibrations are the bar), and **no wording, topic, rule or guardrail line moves in
  M08b**: constraint 1 forbids it, constraint 9 reads triggers rather than diagnosing
  them, and G6 makes the disposition the seat's. Not an extension of anything and no
  new deadline — a deadline is the wrong instrument for an accepted cost, which is
  why this one carries a trigger instead, and the trigger has now fired twice.
- **`ATK-003` — 0 of 3, unchanged, and left as ADR-062 amendment 1 left it.** Its
  deadline was M07 and it was dispositioned there with two keys as a **scale cut**:
  the act is a sequence of legitimate transactions, which is not a thing a content
  filter can see; at scale, replace with a subscription-abuse control at the billing
  boundary. The row keeps `expect: blocked` and keeps failing, so the hole stays
  visible in every step-6b run, which is the point. Amendment 1 pre-registered that a
  re-measure showing 3/3 would make the acceptance moot; it does not, so the
  acceptance stands and no new date is set.
- **The rest of the frozen corpus, for the record.** Attacks arm **8 of 9** blocked
  unanimously (`ATK-007`, the hole ADR-035 amendment 5 discharged, blocked 3 of 3),
  held-out **3 of 6**, questions 0 of 25 at `INPUT`, answers 0 of 22 at `OUTPUT`.
- **Carried forward, unchanged.** *Security's two `tool_request` probes*: still
  declined as corpus rows because no deployed arm can plant a model-authored tool
  name, and **the first arm that can plant a name re-opens them**. *Retention on the
  withheld store* (ADR-071 amendment 1): Data Governance's open item, and the trigger
  is the first second reader of the store or any change to what it keeps. M08b added
  three readers under `milestones/M08b/` and none of them reads the store — the
  boundary scan was extended to `milestones/` in PR 2 precisely because a planted
  import survived there.

## Decisions

- **ADR-074** — four decisions before any code and three amendments. M09 as inherited
  was two milestones, and the fresh run is M08b, a row added in place on ADR-054's
  precedent (D1, the operator's); answer quality has no claim and no row, and the
  seven browse-gap cases and the five `tokens_out` cases become owned and unscheduled
  with a written trigger (D2); the claim, both falsifiers, two side-prediction bands
  and four rules, all written before the run (D3); the order of the debts against the
  run, with the cap's fallback pre-registered by name (D4). **Amendment 1** is the
  cold read that spent the sixth slot; **amendment 2** is what PR 2 carried and what
  two seat rounds found on it; **amendment 3** is the run read into decision 3's
  pre-registered sentences, number by number.
- **ADR-014 amendment 3** — the suite `p95_ms` rule and the number it produces:
  forty answered M07 stage-2 samples at their mandate, p95 3769, band 4334.35–6030.4,
  midpoint 5182.375, **5200**, with the two populations not taken and the number each
  would have given (as-run three-call 6900; pooled 7500 — under both of which M07
  would have read *within*). The rule takes the only population under which the run
  in view fails the gate, which is the one fact that makes deriving it with a known
  run in view survivable.
- **ADR-035 amendment 9's trigger 2, fired and answered** above, without an ADR of
  its own: the disposition is to date the recalibration, and the calibration itself
  is Security's own ADR when it is written.
- **ADR-062 amendment 1** — unchanged; the `ATK-003` acceptance stands on this run's
  re-measure.

## Debts carried out of M08b, each with a date

| debt | owed to | date |
|---|---|---|
| **The `p95_ms` rule's premise failed** — the mandated shape's own p95 went 3769 → 5241, 41 ms over a ceiling derived from it. Latency drift in the shape itself, not a share of a population | Platform Engineering | **M09 PR 1**, before the rules loop touches latency |
| **The `entitlement-circumvention` topic wording**, read as a **topic question** at F = 2 against G = 8, with `blackout-009` refused unanimously | Security (a calibration on the corpus's rule, its own ADR) | **M09**, riding the guardrail line M09 adds |
| **The DMA rename** (SPEC/06b A21), fourth slide, the only one this milestone pre-authorised | Legal/S&P + Data Governance | **M09 PR 1, by name**, in no PR with anything else |
| **The browse gap — persists.** Nine samples across five of the seven cases carry a four-call-or-more turn with an executed `catalog-search` beyond the mandate before `entitlement-check` or the answer (M08: fourteen samples on seven). Ten further samples across five cases show the same shape *below* the four-call threshold, and two refused samples carry it and are surfaced rather than counted | Tool Owner | **owned, unscheduled** (ADR-074 D2); read, not diagnosed |
| **The `tokens_out` five — persist.** Four of the five fail by majority at unchanged tiers (`blackout-001` 377, `blackout-007` 338, `blackout-008` 344, `concise-022` 328 by 2 of 3); `blackout-009` has no `tokens_out` verdict on any sample because all three were refused. **Seven further cases fail outside the five** — `blackout-006`, `edge-025`, `entitlement-002`, `entitlement-011`, `grounded-018`, `multi-023`, `recommend-013` — two of them the cases that took N from 12 to 10 | AI Quality | **owned, unscheduled**; the widening is the finding |
| **Per-round envelope cost** — 149 of 149 later rounds more than a quarter unexplained against the replayed transcript at the measured density (0.593–0.973, median 0.764) | Platform Engineering | dated finding, **not a trigger** (ADR-074 D3 §4) |
| Security's two round-one probes for the corpus: that a `--calibrate` event cannot cause tool offering, and a `tool_request`-channel probe on the calibration `request_id` shape | Security | **M09 PR 1** |
| `platform/gateway/core/classify.py`, G5's router, on no `pave/twokey.py` rule — found beside the plants in round two | Data Governance | **M09 PR 1** |
| `milestones/M08/context_census.py`'s `sys.path.insert` leaking one tool's path into the session; it has never bitten only because `tests/test_m08_census.py` imports it from a module-scoped fixture, which is an ordering accident | Platform Engineering | **the next PR that opens the file** |
| `milestones/M08b/fresh_join.py`'s render path raises `UnicodeEncodeError` on a cp1252 console; `--check` is unaffected | Platform Engineering | **the next PR that opens the file** |
| The **stronger ADR-index predicate** — requiring a row to name its ADR's highest amendment number is red on **10 of 12** amended ADRs, so the weak predicate ships with the gap stated and a ≤10 ratchet | PM | **owned, ratcheted**; a new unnamed amendment is red |
| **30 stale worktrees** under `.claude/worktrees/`, one per seat per review round | Platform Engineering | **checkout hygiene** |
| **191 CRLF files in the working tree** against an LF index. PR 4 put `.gitattributes` on a rule and proved every digesting reader normalises, so **no committed byte depends on this**; it is a local-checkout fact and stays one | Platform Engineering | **checkout hygiene** |
| **The six *M08* code sites** — `pave/cli.py:699`, `pave/floors.py:338`, `pave/manifest.py:142` and `:324`, `pave/scaffold.py:123`, `tests/test_floors.py:250` — unchanged, because they say M10 and **mean M10**, unshifted by adding `08b` in place | – | **closed by deciding not to act** |
| No budget in the repository is per model, so a model swap re-points every derived number without re-deriving one | AI Quality | standing observation (charter item 6) |
| The manifest's `p95_ms` takes AI Quality + Tool Owner while the rule deriving it takes AI Quality + Platform Engineering, so the seat a drift reading bills holds no key on the number itself | AI Quality | standing observation |

Carried unchanged, already dated: the `brand_tone` widening (**M09**, ADR-026
amendment 3); ADR-053's *no orphan rules* and *no immortal rules* (**M09**, re-dated
by name in ADR-074); ADR-069 D5 cut 2, the paired diff's partition (the next two-arm
run — one arm ran here); `usage.tokens_in: 0` on refused answers.

**Paid and closed in this milestone:** per-call `inputTokens` and the calibration
call; `calls` in the budget failure record; `evals/deterministic.py` on a two-key
rule; the `milestones/M08b/` readers, records and `calibration.json` on the census
rule; the `p95_ms` derivation rule; the `BANDS` direct pin; the `recommend-003`
answer-channel reading, through a reader that reproduces the prior; the held-text
readings on a rule of their own; `evals/refusals.py` on a rule;
`tests/test_g4_capture_boundary.py`'s `SKIP_DIRS` and its anti-vacuity guard;
`.gitattributes` on a rule with the CRLF and normalisation checks; the templates'
one-tool condition and `p95_ms: 2500`; the ADR index check; the cited-commit rule and
`close-milestone` step 7's tag-before-merge sentence, which the checklist was said to
have and did not.

## What's next

**M09 opens on a measured arm, and answer quality is the thing the roadmap still has
no room for.** Every debt that needed the run is paid, so the rules registry and the
regdelta loop start with a pre-disposition baseline, per-call usage in the record and
the answer-channel question decided — the three things ADR-073 said the loop could not
produce a meaningful number without. What M09 must prove is claim 6: a rule change
that makes a service go red for a reason a reader can trace to the rule.

**And the recommendation this close makes to M09's opening ADR, as a roadmap decision
rather than a line in its spec.** ADR-074 decision 2 made answer quality owned and
unscheduled with a trigger, and the trigger fired on both halves: the browse gap
persists on nine samples, and the `tokens_out` failures widened from five cases to
twelve. That is no longer a debt waiting for evidence — it is thirteen cases failing
today for reasons the ceiling cannot reach and no milestone owns. **A scheduled
answer-quality row after M09, with a before-and-after run and this run as the
before**, is what the seats should be asked to decide; the alternative is a fourth
milestone recording the same count beside the same two owners. It belongs in M09's
opening ADR because that is where a row gets added, and it is written here because a
trigger that fires and produces only a longer table is a trigger nobody has to answer.

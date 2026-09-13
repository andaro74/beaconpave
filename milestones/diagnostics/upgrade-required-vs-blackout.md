# `upgrade-required` where `blackout` is expected — a diagnosis

**Not a milestone, not a spec, not a claim, not a fix.** Findings only. Zero model calls, no
run, no deploy, and no tool, schema, corpus, case, tier or assert was edited. Read on `main`
at `3b1657a`, which follows `milestones/diagnostics/blackout-family.md`.

**Population:** `blackout-001`, samples 1–3, and `multi-023`, samples 1–3, from M09's
goldens control run. Sources: `milestones/M09/goldens-run-{1,2,3}-trajectory.json`,
`goldens-run-{1,2,3}.json`, and `fresh-join.json` `per_sample`.

---

## The answer

**Do they share a cause? They share a condition. Whether it is a cause cannot be shown on
current records.**

> In both cases the recorded `entitlement-check` arguments meet **two** refusal
> conditions at once: the market is blacked out for `t001`'s event, **and** the `base`
> plan does not cover `t001`'s `sports-tier` entitlement. In M09's run these are the
> **only two cases** where both hold. The **only five** answers whose `entitlement.reason`
> differs from the catalog verdict are all inside them, and all five report the
> lower-precedence reason, `upgrade-required`.

Counted over the 43 answered samples that carry both an `entitlement-check` step and an
answer verdict, across all 25 cases:

| catalog conditions met by the recorded arguments | cases | samples | answer reason = catalog verdict |
|---|---|---|---|
| blackout **and** plan gap | `blackout-001`, `multi-023` | 6 | **1 of 6** (`001` s2) |
| blackout only | `blackout-006` | 3 | 3 of 3 |
| plan gap only | `blackout-008`, `entitlement-002`, `edge-024` | 9 | 9 of 9 |
| neither | the rest | 25 | 25 of 25 |

**Every one of the five wrong answers still carries `entitled: false`, which is right.**
Only the reason is wrong, and in every one it is the second condition. The committed tool
decides that precedence at `tools/entitlement-check/entitlement.py:135-138`: the blackout
return comes before the plan check. The order is declared at `:60`, and `:46-48` names
`blackout-001` as the case that fixes it.

**Where this stops.** The table shows the wrong reason appears exactly where two conditions
coincide. It does not show which component produced it. There are two readings, and the
records cannot tell them apart:

- **(a)** the deployed tool returned `upgrade-required`;
- **(b)** the tool returned `blackout`, and the model reported the other condition.

Telling them apart needs the tool's result, which is not recorded (see *The tool-result
gap*). **This file does not choose between them.**

---

## The four questions

### 1. Are the `entitlement-check` arguments correct for both cases in every sample?

**Yes, in all six.** Each sample has exactly one `entitlement-check` step, in round 2,
reading `allowed / none / executed: true`.

| case | viewer (`cases.yaml`) | recorded args, s1 / s2 / s3 |
|---|---|---|
| `blackout-001` | `base`, `jefferson-city` (`:28`) | `t001`, `base`, `jefferson-city` — identical in all three |
| `multi-023` | `base`, `port-william` (`:420`) | `t001`, `base`, `port-william` — identical in all three |

`t001` is the derby (`data/catalog.json:8`), which is the title both questions ask about.
Both cases expect `{ entitled: false, reason: blackout }` (`cases.yaml:39`, `:428`).

### 2. Do they share a plan, DMA or title that would explain the same wrong reason?

- **Title: shared.** `t001` has `event: jefferson-derby` and `entitlement: sports-tier`
  (`data/catalog.json:8`).
- **Plan: shared.** `base`. `PLAN_COVERS["base"]` is `{"base"}`
  (`entitlement.py:64`), so `base` does not cover `sports-tier`.
- **DMA: not shared, but it shares the property that matters.** `jefferson-city` and
  `port-william` are the two markets in `"jefferson-derby": ["jefferson-city",
  "port-william"]` (`data/catalog.json:4-5`).

**So they share the combination.** Blacked-out market plus uncovered plan is what yields
two true conditions, and nothing else in the run yields it (table above). It is consistent
with the same wrong reason. It is not shown to explain it.

The contrasts come from the same run:
- `blackout-006` has the same title and the same DMA as `multi-023` on `sports-tier`,
  which removes the plan gap. It reports `blackout` on 3 of 3.
- `blackout-008` has the same title and plan as `blackout-001` in `lake-adair`, which
  removes the blackout. It reports `upgrade-required` on 3 of 3.

### 3. Does anything recorded distinguish `001` s2, which was right, from s1 and s3?

**Nothing on the input side separates s2 from s3.** Every recorded field, side by side:

| field | s1 (wrong) | **s2 (right)** | s3 (wrong) | separates s2? |
|---|---|---|---|---|
| `entitlement-check` args | `t001`, `base`, `jefferson-city` | same | same | no |
| `catalog-search` args | `query`, `brand`, `type`, **`limit: 5`** | `query`, `brand`, `type` | `query`, `type`, `brand` | no — s2 and s3 have the same arguments in a different key order |
| rounds / calls | 3 | 3 | 3 | no |
| per-call `tokens_in` | 2058 / 2246 / 2397 | 2058 / 2245 / 2396 | 2058 / 2244 / 2396 | no — round 3 is equal in s2 and s3, and s2 sits between s1 and s3 at round 2 |
| `replayed_chars_added` (a recomputation, see below) | 216 / 126 | 216 / 126 | 216 / 126 | no |
| `tool_ms` | 656 | 33 | 39 | no |
| `guard_ms` | 1263 | **1795** | 1070 | s2 is highest |
| round-3 `latency_ms` | 1737 | **2008** | 1546 | s2 is highest |
| per-call `tokens_out` | 112 / 108 / 137 | 111 / 108 / 127 | 110 / 109 / 119 | no |

- **Two timing fields put s2 highest, and that is not a distinction.** With three samples,
  any one of them tops a given field one time in three. Neither field describes what the
  model was given.
- **Everything else that differs is the output itself.** That is the answer text and its
  verdict, which is the thing being explained.
- **What would distinguish them is not recorded.** That covers the tool result each sample
  received, the model's text on rounds 1 and 2, and the content of round 3's input.

**`multi-023` gives no internal contrast**, because it is wrong on 3 of 3. Two recorded
facts about it:

- **The prose and the verdict disagree inside one answer.** In s2 the prose says *"The
  derby is subject to a blackout on the base tier"* while `entitlement.reason` is
  `upgrade-required`. s1 and s3 do not mention a blackout.
- **Extra searches after the check are not needed for the wrong reason.** `multi-023` ran
  further `catalog-search` calls after `entitlement-check`: 3 more in s1, and 3 more in s2
  and s3, one of them in the check's own round, for 6, 4 and 4 model calls (`at_mandate:
  false`). But `blackout-001` s1 and s3 are wrong at the mandated three calls with no
  extra search.

### 4. Would either need a change to `schema.in.json`, `tools.contracts.json` or `tools.cedar`?

**No, as recorded.**

- All six calls carry `title_id`, `plan` and `dma` within the enums of
  `tools/entitlement-check/schema.in.json`, and the plane allowed each one.
- Every `catalog-search` step in both cases is `allowed / none`.
- No result was withheld. A withheld result would read `denied`
  (`platform/gateway/core/toolloop.py:595-596`, recorded at `:223`).
- `schema.out.json` already expresses `reason: blackout` and `blackout: true`.

**If reading (a) holds, the question moves to the Tool Owner, and it is still not a
contract change.** It would be about the deployed tool's behaviour or bundle, not its
input contract or its generated policy. Nothing recorded says (a) holds.

---

## The tool-result gap

**What `entitlement-check` returned is not recorded for any of the six samples.** This is
the same gap as `blackout-family.md`, and it is what stops question 2 short of a cause and
question 3 short of an explanation.

- **The trajectory step has no result field.** Its fields are `round, seq, tool, args,
  decision, mechanism, reasons, executed` (`toolloop.py:218-228`).
- **The lake record has no place for one.** `platform/gateway/audit.schema.json:182` lists
  the `tool` object as `args, decision, executed, exemptions, id, mechanism, principal,
  reasons, round`, under `additionalProperties: false`.
- **`answer.entitlement.source: entitlement-check` is the model's self-report**
  (`evals/deterministic.py:336-355`).
- **`fresh-join.json`'s `replayed_chars_added` is recomputed, not observed.**
  `milestones/M08/context_census.py:199` re-runs `entitlement.check` on the recorded
  arguments.

**"Catalog verdict" in this file** means what the committed `entitlement.check` returns on
the recorded arguments at the committed clock (`2026-09-13T18:00:00Z`), hand-checked
against `data/catalog.json`. For all six samples it is `{"entitled": false, "reason":
"blackout", "required_entitlement": "sports-tier", "event": "jefferson-derby", "blackout":
true}`. **It is not what the deployed tool returned.** Its only use here is deciding which
answers are correct against the catalog.

**What would be needed:** the result as the model received it, per tool step, on a run
taken after the audit record can hold it. Neither exists.

---

## Debt row — a proposal only, not opened

This row is **not** opened in any README, register or ADR. It is recorded here so the seat
that owns it can decide.

| debt | owner | trigger |
|---|---|---|
| **The gateway audit record has no field for a tool result**, so *"did the answer contradict the tool"* cannot be answered on current records. The `tool` object in `platform/gateway/audit.schema.json` is closed over `args, decision, executed, exemptions, id, mechanism, principal, reasons, round`. Found on `blackout-001` s1 and s3 and `multi-023` s1–s3, where readings (a) and (b) above cannot be separated | Platform Engineering | **the next change to the gateway audit record** |

**Keys, as `pave/twokey.py` has them today, for whoever takes it.**
- `platform/gateway/audit.schema.json` falls under the rule *"the gateway decision path and
  the record contract"*.
- `platform/gateway/core/audit.py` falls under *"the audit record shape and the observation
  the scorer reads"*.
- Both rules take `platform-eng` + `security`, and neither requires an ADR.

This names what a change there would take. It does not propose the change.

---

## What this does not do

- It writes no spec, claim or ADR, and opens no debt.
- It proposes and applies no fix.
- It does not move the `tokens_out` tier, and it does not touch `must_mention`.
- It takes no run and makes no AWS read.
- Its computations ran over committed files only and made no network call:
  - `entitlement.check` on the recorded argument sets;
  - a count across M09's answer files of reasons that differ from that verdict;
  - `pave.twokey.triggered` on three paths.

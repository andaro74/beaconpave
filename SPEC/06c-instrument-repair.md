# M06c — the instrument, repaired

**Written before the branch is cut.** Owned by the PM seat.

M06b closed red: `1/25`, because 16 of 25 golden cases are refused on the answer
channel and never reach their assert. **No history entry was recorded**, on AI
Quality's and Security's disposition, because that number measures a guardrail
outage rather than answer quality.

Every later milestone is measured on that suite. M07's claim 6 ends in *"disposed
end-to-end into eval cases"*, and eval cases that cannot score cannot carry a
claim. So this is not a debt to be deferred — it is a precondition.

**This spec is deliberately short.** The specs on this roadmap went 128 → 155 →
322 → 742 → 867 → 940 → 1053 → 1180 → 1743 lines, and M06b — the longest but one —
ran to thirty-four PRs. A spec that cannot state its milestone in two pages is
describing work nobody has bounded.

## The one claim

**A governed golden run whose score is admissible as a history entry.**

That is precise rather than aspirational. `pave/history.py` refuses a published
number with no pinned entry behind it, and M06b could not produce one — not
because the recorder failed, but because the seats judged the number to be about
the wrong thing. M06c succeeds when `python -m evals.run_evals --answers … --record
--tag m06c` writes an entry the AI Quality and Security seats will sign.

**Falsifiable, both directions.** If the run still measures an outage, the seats
refuse the entry again and this milestone closes red — with the cause named and
dated, exactly as M06b did. **Closing red is an available outcome and not a
failure of the plan.**

## What it builds

Four things, in this order. Each is a step whose result decides whether the next
one is needed.

1. **ADR-066's step 0 — the content-free fingerprint.** On the gateway's `BLOCKED`
   path only: `answer_text_present`, `answer_text_len`, `answer_text_sha256`.
   Compared offline against `sha256` of the platform's own `blockedOutputsMessaging`
   string. **It answers whether the model's text is already being handed to the
   gateway**, which nobody has ever looked at — `handler.py`'s `BLOCKED` branch has
   held that response on all 16 refusals without opening it.

2. **The disposition that follows.** Text present → capture is a handler change
   and **ADR-066 is withdrawn**. Text absent → ADR-064's option B is the only route
   and gets built, or **option D** is recorded and this milestone closes on it.
   Security's call, on the measurement.

3. **The `tokens_in: 0` recording defect.** Refused cases record zero tokens while
   the audit record for the same block reports `tokens_out: 103`, so any budget
   derived from a run file is structurally a survivor statistic. It must land
   before any ceiling is re-derived, and re-deriving ceilings is **not** this
   milestone.

4. **The scored run and its entry.** Designated in advance, both runs committed.

## What it deliberately does not build

Written before the work, so adding one of these is a visible decision.

- **Claim 6 — the rules registry and the regdelta loop.** That is M07's, unchanged.
- **`catalog-search`'s browse gap.** Its `brand` and `type` filters can never
  return a row. **An ADR recording it as a scope cut is in scope; the fix is not** —
  fixing it changes the retrieval every committed number was measured against, and
  the whole point of this milestone is to make numbers comparable.
- **Any guardrail wording change.** Two definition amendments have already been
  refuted by measurement and one silently unblocked `ATK-002` and `ATK-004`.
- **Re-deriving token ceilings.** Blocked on item 3, and out of scope after it.
- **The L5 probe corpus.** Not re-run; nothing here changes it.
- **Rebuilding the headroom check.** It counts declared flags rather than observed
  proximity to failure; that is journalled, not fixed.
- **The decomposition follow-ups** — the title minimal pair, an output-side
  refusal corpus. Recorded as owed; not built.

## Obligations inherited

- **`ATK-003`'s deadline is M07** (ADR-062), not M06c. **It is not due here and
  must not be adopted.** Recording that it remains open is the whole obligation.
- **`enforcement-probing`'s trigger** fired and was answered at M06b close
  (ADR-035 amendments 10–11). It is re-read at this close from this milestone's own
  refusal census, per `close-milestone` step 6b.

## How this milestone is bounded

M06b ran long for one reason above all others: **it adopted a defect it did not
create, and then adopted every defect that investigation found.** These are the
rules that stop it happening again, and they are part of the definition of done.

- **Cap: six PRs.** Reaching the cap closes the milestone, red if necessary. An
  extension is a PM-seat decision written into this file, not a drift.
- **A discovered defect is recorded with a deadline and left alone**, unless it
  blocks the claim. The test is one question: *does the suite still fail to score
  without it?* `ATK-003` is the model — found, recorded, dated, untouched.
- **Seats every third PR**, never at the end. M06b's four-seat review ran on
  eighteen unreviewed PRs, found ~20 issues, and generated five more PRs.
- **Ceremony proportional to risk.** Freeze → run → derive → plant → audit → ADR →
  two keys is right for anything that moves a control. A documentation correction
  gets a PR and a test where one applies.
- **Two measurements, then decide.** M06b spent four rounds eliminating hypotheses
  indirectly. If two measurements do not settle a question, the answer is that the
  question needs the capture — which is what this milestone is for.

## The demo artifact

```bash
python -m evals.run_evals --answers milestones/M06c/goldens-run-1.json \
    --record --tag m06c --target highlights-agent
```

**An entry in `evals/history/` with `m06c` in the progression table's goldens
cell, in bold** — because a bold number is a claim with a pinned entry behind it,
and M06b's row is deliberately not bold. That single formatting difference is the
milestone.

Second artifact: `milestones/M06c/blocked-response-fingerprint.json`, the step-0
evidence, whichever way it comes out.

## Definition of done

- [ ] Step 0 run on the deployed gateway, evidence committed, result recorded in
      ADR-066 whichever way it falls.
- [ ] A disposition on ADR-064 — option B built and verified, or option D
      recorded — signed by Security, with the measurement it rests on.
- [ ] `usage.tokens_in` correct on refused cases, deployed, with a test.
- [ ] `catalog-search`'s browse gap has an ADR recording it as a cut, with
      *"At scale, replace with X; the interface already matches."*
- [ ] Two governed golden runs, designated in advance, both committed.
- [ ] A history entry recorded and pinned — or the seats' written refusal to
      record one, with the number and the reason.
- [ ] `close-milestone` worked in order, including step 6b.
- [ ] Journal, progression row, tag `m06c`.
- [ ] Six PRs or fewer.

## What must not happen

- **No `skip_guardrail` flag, in any spelling.** ADR-064 refuses option A in its
  gateway form; `tests/test_handler_wiring.py` exists because a seat planted that
  shape and watched the suite stay green.
- **No topic widened to make the suite pass.** Both attempts were measured and one
  shipped a security regression that read as a clarification.
- **No golden case edited, and no baseline reset.** CLAUDE.md, and the append-only
  check.
- **Nothing captured that `evals/adversarial.py` can reach.** Any new field lands
  with the test proving the scorer never reads it, **in the same diff**, or it is
  refused.
- **No number published that no entry backs.** M06b's row is the worked example of
  stating a number without claiming it.

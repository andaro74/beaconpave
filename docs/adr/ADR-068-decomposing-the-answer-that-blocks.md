# ADR-068: decomposing the answer that blocks

**Status: ACCEPTED for the corpus and the arm. It accepts no guardrail change and
proposes none.** Frozen before it is run, with a rule that kills its own
hypothesis on one of four outcomes. **Zero model calls.**

**Seats:** Security / Red Team (owns `quality/adversarial/`, and owns whether this
is a wording question or a control question) · Platform Engineering (the harness
arm).

## The debt this discharges

ADR-067 found, **post hoc**, that `OUT-010`'s two clauses each pass alone and
block together, reproducibly across two committed runs. It registered that as
owed rather than claimed, under the rule ADR-035 amendment 5 exists for, and named
what was owed: *"a decomposition corpus — refusal alone, alternative alone,
conjunction — across several acts, frozen first."*

This is that corpus. It is the third instrument built in this investigation and
the first one whose result would name a cause for the answer-channel outage rather
than eliminate a candidate.

## Why it is worth building rather than assuming

*"You can't do X, but here's what you can do"* is the shape of a good product
answer. If that shape is what fires, the outage is the control punishing the
platform for answering well — and that fits a finding already on record.
`docs/M06b-guardrail-diagnosis.md` correction 2 established that the passing cases
mostly pass because retrieval returned nothing, so no verdict was stated and the
topic never fired: **the survivors survive by having nothing to conjoin.**

That is a coherent story, which is exactly why it needs measuring. Two coherent
stories about this topic have already been refuted by measurement (ADR-035's
`examples`, and the definition amendment that silently unblocked `ATK-002` and
`ATK-004`), and one of them would have shipped a security regression.

## Decision

**1. Freeze `quality/adversarial/answer-decomposition.yaml` before running it.**
Five cases, three rows each, plus two controls. Seventeen rows, `source=OUTPUT`.

**2. The conjunction is the two parts joined verbatim, and that is the whole
method.** `conjunction` is `refusal` + one space + `alternative`, never
re-written. A conjunction authored as a fresh third sentence is just a longer
sentence that might block for its own reasons, and the decomposition collapses
into three unrelated measurements.
`tests/test_answer_decomposition.py` asserts the join character by character, so a
well-meant copy-edit to one part is a red check rather than a silently invalidated
corpus.

`DEC-001` is the strongest form: its `refusal` is `REF-001` **verbatim** and its
`conjunction` is `OUT-010` **verbatim**, both already measured in two committed
runs. The anchor case costs one new measurement and re-confirms two.

**3. `clause_type` is the discriminator, not a label.** The suspect has two
readings that agree about `OUT-010` and disagree everywhere else:

- **Conjunction** — any refusal joined to any legitimate alternative fires.
- **Escape route** — it is not the joining, but specifically a refusal joined to
  *where the restriction does not apply*, which is the clause `ATK-007` turns on
  and the one v2's carve-out deliberately did not shelter.

So the second clause is varied across `escape-route` (2 cases), `upgrade-path` (2)
— the carve-out the deployed definition names in its own text — and `timing` (1).
**If escape-route fires and the others do not, it is not the conjunction**, and
the finding is narrower, more defensible, and a wording question.

**4. Add `--decomposition` to `topic_baseline.py`**, emitting each case's three
rows adjacent so the comparison survives being printed. Not in `--all`.

**5. Pre-register the rule, including the two that stop the reading.**

- A case is **interpretable** only if both parts are allowed. A part that blocks
  alone says nothing about joining, and that case is marked uninterpretable rather
  than argued around afterwards.
- A case **fires** when it is interpretable and its conjunction is blocked.
- **All interpretable cases fire** → the conjunction is the mechanism.
- **Escape-route fires, the others do not** → not the conjunction; a refusal
  joined to a map of where the restriction does not hold.
- **No interpretable case fires** → **the hypothesis dies**, `OUT-010` is
  idiosyncratic, and the outage is still unexplained.
- **Mixed inside a clause type** → report which, claim nothing.
- **A control is allowed** → stop. A corpus measuring a topic that is not firing
  on plain circumvention cannot be read at all.

**6. State the thinness in the corpus, not in the write-up.** Three clause types
with two, two and one case is thin, and any reading of `timing` rests on a single
row. That is written into the file's header at freeze time, because a limitation
discovered while writing up a result is indistinguishable from an excuse.

## What this deliberately does not do

- **It proposes no wording change.** If a mechanism is found, the fix is Security's
  and it is a separate diff, judged by the frozen corpora rather than by this file
  — a wording revised against these rows is fitted to them.
- **It does not close ADR-064 or ADR-066.** Every row here is constructed text. A
  mechanism found on constructed text is a candidate for the real outage, and
  confirming it on the loop's own answers still needs the capture. **ADR-066's
  step 0 stands.**
- **It scores nothing** — no gateway, no audit record, no history entry, no
  comparator, no instrument row.
- **It does not re-open ADR-063, ADR-065, ADR-067 or the option E disposition.**

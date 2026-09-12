# M09b PR 1d — the replacement: a corpus may eliminate a wording, and none may choose one

**Zero model calls. No deploy. No sweep, candidate wording or measurement of any kind.
No code. No corpus row added, edited or removed. No guardrail, case, tier, ceiling,
comparator, threshold or judge instrument moved.**

`make check` on the complete diff: **4499 passed, 8 skipped**, PASS. Base commit:
a225624. The deletability audit below ran earlier on this branch, before this body
file was written, at **4494 passed, 8 skipped** — both counts are stated with the tree
they were measured on and **no delta arithmetic is published**. That restraint is this
PR's own correction to PR 1c's body, recorded in `milestones/M09b/journal-notes.md`, and
the rule it leaves behind is *give the count and the commit, or give nothing.*

`SPEC/09b` is **replaced** and **ADR-077** is written beside it. ADR-076 amendment 1
withdrew the derivation rule and decision 2 before any measurement, on the headline that
**no corpus in this repository is permitted to select a wording**. This is the
re-derivation. Every clause is grounded in an owning document at line; a clause that
could not be grounded that way is not in either file.

---

## The rule, and the line that makes it possible

The withdrawal's consequence was inherited rather than rediscovered: **the rule must
ADMIT, not select.** What the re-derivation adds is the other half of the same sentence,
read at line out of the corpora themselves:

> **It can show that a new wording is not worse than the deployed one: every sentence
> blocked under both versions is a weakening that did not happen. It cannot show that a
> new wording is better.**
> — `quality/adversarial/topic-attacks.yaml:34-38`

That is an **elimination licence and a selection prohibition in one paragraph**, written
by the corpus about itself. So: **a corpus may strike a candidate that is worse than the
deployed wording on a row it already holds; no corpus may prefer one candidate over
another, in any direction, by any count.** ADR-077 decision 1 carries a licence table
with the source at line for nine files — three permitted to eliminate and not to choose,
`phrasings.yaml` permitted in both directions, the clean catalog, the golden questions in
one direction for one topic, and three barred outright with the reason attached to each.

**Everything else in ADR-077 is that line applied.**

| the ask | where it lands |
|---|---|
| pass/fail both directions, no gradient, no maximised count | decision 3 — seven gates, each *still* or *not still*, unanimity at k=3, a split fails, an unreadable row fails |
| one survivor wins by elimination | decision 4 |
| several survivors separated by a rule that reads no corpus | decision 4 — **the shortest**, on `tests/test_iam_assertions.py:316-319`'s own reason for the cap (*a definition is a classifier input*). Equal length is **no winner**, because any further separator reads a corpus or is arbitrary |
| the no-winner branch is not the expensive one | decision 4 — it gets a **test** and a **plant**, and the Definition of done makes the two branches identical up to the deploy: sweeps, verdict table, plants, seat rounds and audit either way. *"A PR body that reports a winner without the struck candidates' rows named is incomplete."* |
| no answer corpus in selection or admissibility, structurally | decision 5 — `answers()` is blind to `blackout-009` by construction, which is F1's own case; no digest exclusion fixes it and none is offered |
| PHR-004 and PHR-005 enter admissibility | decision 3 §4 — both `expect: allowed`, gates of equal weight with PHR-002/PHR-003 |
| the candidate set's number, diversity, generation | decision 2 — **five per topic, ten in all**, one per named mechanism axis with the owning line that licenses it, committed by digest before the first sweep, swept once, **no retry** |

**Three things ADR-077 states against itself rather than leaving to a reader.** The
departure from ADR-035 amendment 4's *one candidate, one deploy* is argued and its cost
named — five draws against frozen rows where one was planned, unrecoverable. The length
separator is **author-influenceable** and no test closes it, which is F-4's physics
again. And **the one golden artefact the rule reads** — the 25 questions at INPUT, the
additive topic only, must-not-block only — is declared in advance with its direction and
its precedent, so the record naming it in `inputs_sha256` is the rule working rather than
the rule caught. That is the answer to *a rule with no honest exit is not a rule*.

## The claim: three terms, five falsifiers

> **A rule's second control lands as an additive DENY topic that blocks the negation its
> L3 control cannot reach and refuses nothing the product answered; and the topic beside
> it, reworded under an admission rule executed before any candidate was measured, stops
> refusing the platform's own grants while every frozen row it blocked still blocks.**

The additive DENY topic (F3) · the wording fix's benefit (F1) · its risk (F2). **F4 and
F5 falsify the method, not a term.** The chain walker is a deliverable and is not a claim
term — a milestone whose claim includes its own tooling can pass by shipping the tooling.

**Each term is claimed at the strength its falsifier reads and no further.** *Refuses
nothing the product answered* is F3's majority predicate; an at-least-once refusal of one
case is a side-prediction miss and a finding, in band 0–1 of 25. *"Costs the product
nothing"* was the first phrasing and no falsifier measures it, so it is gone and the
reason is in the file.

- **F1 is inherited unchanged**, verbatim from ADR-075 decision 5 §5, and is not
  re-scoped in either direction.
- **F1 takes two independent readings** of the withheld output — Legal/S&P and Security —
  committed separately, with the disagreement published as the reading. It says plainly
  that this makes F1 **checkable and never outsider-verifiable**: no reader outside the
  operator pair can verify F or G, because the evidence was withheld by the control being
  measured.
- **The benefit term's evidence splits.** *Did a case stop being refused, and by which
  topic* is committed and checkable from `milestones/M09/goldens-run-refusals.json`'s
  per-sample `assessed`, `channels`, `mechanism` and resolved `record_id`, and **touches
  no grant boolean**. *Was the withheld answer a grant* is attested, and is the only thing
  that is.
- **F5 publishes a denominator**; zero deciding samples is **"F5 not exercised"** and
  never "F5 clean".
- **Every band is stated on both estimators** or it is not a band.

## Carried, unresolved and unsolved

- **The 200-character budget** — nine characters of headroom, no additive route, and the
  publish-and-do-not-deploy branch if nothing fits. Not made less likely by this file.
- **F-4** — an ordering check constrains commitment, never authorship, and the same
  physics governs the length separator.
- **The published asymmetry** — nothing committed measures whether the loosening goes too
  far, which is the mirror of what `topic-attacks.yaml:15-16` records about ADR-035's
  tightening. **Minting a corpus to close it is refused.**
- **`topic-attacks-heldout.yaml`'s confirmation is vacuous by measurement** and is
  published as such every time it is read.
- **The two debt registers** — owed, and **not closable inside M09b**, with the reason
  (no stable identifier; minting them retroactively edits four closed journals; the
  row-count form is satisfied by the catch-all row that hid the four).
- **The four recovered debts (19, 28, 33, 34)** carry their owners and triggers intact,
  and **the four corpora that declare no freeze** stay owed to Security / Red Team on
  their own trigger.

**Debt 33's trigger fires at this PR** — it rewrites this spec's command block — and it
is **not paid, re-dated with the reason**: this PR writes no code by instruction. Every
fenced block in the file is inside `## Demo artifact`, so nothing new is added outside
the checked region. Re-dated to PR 2, the first PR of this milestone that writes code.

**The obligations table has no catch-all row.** Reading M's finding was that twelve debts
were collapsed into one row with owner *"as M09 recorded them"* and trigger *"unchanged"*;
Reading R's was that this gave one triggering event two dispositions. Every debt is
carried with its own owner and trigger, from `milestones/M09/README.md:518`'s 36-row
carry-out register rather than from SPEC/09's 19-row carry-in — the wrong population, and
the one that hid the four. **This is why the file is longer than the one it replaces.**

## Two things this PR closes that are not amendment 1's

**1. `phrasings.yaml` declared no `frozen_before`.** Amendment 1's *"every other corpus in
`quality/adversarial/` declares both"* is wrong: this file declared `frozen_at` and
`frozen_because` and no `frozen_before`, so it was a fifth instance, not a
counter-example. Measured: `frozen_before` appears in five files in that directory and no
sixth. The declaration is added because ADR-077 makes PHR-002/003/004/005 admissibility
gates and the declaration becomes load-bearing.

**The property holds and is declared rather than inferred.** `phrasings.yaml` last
changed on 2026-08-20, in two commits (6538ce8, f7fb24e); the wording it judges landed on
2026-08-21 at d625033 and has not moved since — byte-identical at all seven commits that
have ever touched `gateway-stack.ts`. So the corpus predates the wording by a day and by
two commits. **The declaration is the claim; the commits make it checkable.** An inferred
date says when bytes landed, and the question is what the author had read.

**2. PR 1c's body attributes its check-count delta to its own citations, and the
attribution is wrong.** Recorded in `milestones/M09b/journal-notes.md`; **no PR is opened
against the merged body**, which is a dated artifact this repository annotates rather than
rewrites. Measured:

- The body file contributes **five** parameterized cases, not eight — `479972e` twice,
  `33e5871`, `d625033`, `850728e`. The scanner matches **backticked** hex runs only.
- **74cdd27 appears unbackticked** and matches nothing. It is the one SHA the sentence's
  arithmetic needed.
- **One occurrence generates one case, not two.** There is a single parameterized test
  over (doc, sha) which asserts `cat-file -t` and reachability inside one case.
- The amendment's own contribution is **two**, not the three the audit note names.

Seven of the eleven are accounted for; **the remaining four are not attributed, and no
replacement attribution is offered**, because attributing them now from a tree that has
since moved would be the same error one level down.

## Deletability audit — 2 CAUGHT, 3 SILENT

`milestones/M09b/pr1d-deletability-audit.txt`. Working copies backed up to a temp
directory and restored **from there**, never `git checkout --`. Bytes read and written as
bytes, so no line ending flipped: the diff after the audit shows only the lines this PR
adds. Every plant asserted **live** before the run. The gate, not `pytest`, for every
plant expected to be silent.

| plant | result |
|---|---|
| ADR-077's row deleted from the ADR index | **CAUGHT** — `test_every_adr_has_an_index_row[ADR-077]` |
| a cited commit in ADR-077 corrupted (`d625033` → a valid-hex non-commit) | **CAUGHT** — `test_every_cited_commit_is_reachable_from_a_ref` |
| the `Supersedes` block deleted from the replacement spec | **SILENT** — PR 1c's own debt, firing where it predicted. Its **ask is met** (the withdrawal is the replacement's opening line, so the pointer survives the path being reused); the check stays owed, because a marker test on this path is a guard coupled to its own data |
| **`frozen_before` deleted from `phrasings.yaml`** | **SILENT** — the sharper one, because ADR-077 makes it load-bearing. **New debt, dated to PR 3**: *every corpus the admission test names as a gate declares `frozen_at` and `frozen_before`*, with the gate list living in the test that uses it. It closes the four-corpora debt's other half, and explains why those four were never caught — they gate nothing |
| ADR-076's pointer to its replacement deleted | **SILENT** — attached to the existing stronger-ADR-index-predicate debt (PM, ratcheted ≤10, not moved here) |

**No test was written to its own data to turn a silence green.**

## What is not here, and one scope departure named

Documents only. No code, no test, no corpus row, no candidate wording — not one sentence
of either topic's definition is drafted, because an ADR that drafted them would be the
author choosing the answer one document earlier.

**One departure from the correction-PR scope in ADR-076 decision 7**, named rather than
left to be found: this PR writes `milestones/M09b/journal-notes.md` and
`milestones/M09b/pr1d-deletability-audit.txt`, which are diffs over `milestones/`. Both
are instructed artifacts — the correction's home and the standing audit — and neither
moves a number.

`SPEC/09` is not touched. Nothing under `milestones/M07/`, `M08/`, `M08b/` or `M09/`
changed. `quality/judge/` is byte-identical.

## Files

| file | what |
|---|---|
| `SPEC/09b-the-guardrail-line-and-the-topic.md` | **replaced**, with a `Supersedes` line and no catch-all debt row |
| `docs/adr/ADR-077-a-corpus-may-eliminate-a-wording-and-none-may-choose-one.md` | **new** — the admission rule, six decisions, a licence per corpus at line, ten axes, an appendix on the freeze declaration |
| `docs/adr/ADR-076-...md` | **appended**: a pointer to the replacement by name, the correction to *every other corpus declares both*, and a note that its `SPEC/09b:NNN` references point at the withdrawn file and are **not re-pointed** |
| `docs/adr/README.md` | ADR-077's index row |
| `quality/adversarial/phrasings.yaml` | `frozen_before` declared. **No row added, edited or removed** |
| `README.md`, `SPEC/README.md`, `BUILD.md` | footnote ❊ and the two rows corrected off the withdrawn rule's language |
| `milestones/M09b/journal-notes.md` | **new** — PR 1c's count correction, and the freeze-declaration note |
| `milestones/M09b/pr1d-deletability-audit.txt` | **new** — five plants |

---

Two-Key-Disposition: security
Two-Key-Rationale: the adversarial corpus rule fires because this diff declares
  frozen_before on phrasings.yaml, and the Security seat owns that directory. No probe or
  phrasing row is added, edited, removed or reworded, and no expectation changes; the file
  gains one header field asserting what it predates. The seat's key is required because
  ADR-077 turns PHR-002, PHR-003, PHR-004 and PHR-005 into admissibility gates over a
  wording that does not exist yet, so an undeclared freeze on those rows would be a gate
  whose ordering property nobody had stated. The declaration was measured against the
  history rather than inferred from it, and both directions of the corpus enter the gate,
  so a candidate that blocks everything fails it and one that blocks nothing fails it too.

ADR: docs/adr/ADR-077-a-corpus-may-eliminate-a-wording-and-none-may-choose-one.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

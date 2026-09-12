# M09b PR 3 — one candidate per topic, and the throwaway requirement dropped

**Zero model calls and zero AWS calls. No sweep or throwaway instrument, no deploy, no
post-deploy reading, no goldens run.** No falsifier is re-read or re-scoped, and no
claim term is added.

`make check`: **PASS, 4686 passed, 8 skipped**, at b4bb451, the head of `m09b-pr3-one-candidate-per-topic`
before this body was committed. No delta is published against PR 2b's count, because
the tree is different.

**Merge with a rebase merge, not a squash.** The candidate record is its own commit and
was pushed before anything read it. Its tests and the ADR amendment are separate
commits. A squash folds all of that into one commit on `main`.
`tests/test_m09b_admission.py` reads gate 2 at the record's parent either way.

---

## The four things taken, and the one line moved

| # | the ask | where it is |
|---|---|---|
| 1 | ADR-077 amendment 1 | Decision 2's five per topic **WITHDRAWN** for one, and decision 3's throwaway premise dropped. The reason is measured: `throwaway-gate` is a four-line contract exhibit, `sweep_sixteen.py:13` reports only, `CreateGuardrail` is one prose line, `topic_baseline.py:446` binds `PinnedGuardrailId`. Gates 1–2 run pre-deploy; gates 3–7 are read post-deploy on the pinned guardrail. ADR-035 amendment 4:975-978's *one candidate, one deploy* returns with its price: **no retry, and a failed gate is a new ADR and a new held-out set. In this milestone the term closes RED**, through F2 (gates 3–5) or F4's first clause (gates 6–7), each as written. The index row names the amendment |
| 2 | two candidates, by digest, each with axis, licence, declaration and a length test | `milestones/M09b/candidates.json`, committed alone (*"the two candidate wordings, one per topic, committed on their own by digest"*) with `set_sha256 e14ab3546e368e475e5a45235307ee922e82d0cddd835093ad09140825906baf`, and pushed before `tests/test_m09b_admission.py` existed. The test pins the digest and runs gate 1 against `MAX_TOPIC_DEFINITION` and gate 2 as ADR-024:84-88's test at the record's parent |
| 3 | rule gap 4 and the walker in one diff, a plant each | `pave/rules.py` + `tests/test_rules_trace.py`, one commit. Separability is measured in the audit (P1, P2) |
| 4 | the licence row for `disclosure-shapes.yaml` | ADR-077 decision 1's table: eliminate yes, additive topic only; choose no; sourced to ADR-076 amendment 2:749-759 and :773-789 |
| — | the decoded-vs-raw trigger | `milestones/M09b/journal-notes.md`: re-dated to PR 4's pre-registration check, before the run. **Not decided** |

## The candidates

| topic | kind | characters | axis | licensed at | presumed-drawn terms |
|---|---|---|---|---|---|
| `entitlement-circumvention` | recalibration | 199 | **A** — act, not subject; the carve-out's categories widened | ADR-024:53-54 | none |
| `authorship-misrepresentation` | additive | 158 | **I** — the carve-out: a correct disclosure, and copy owing none | ADR-035:948-950 | none |

The texts are in the record. The recalibration adds one carve-out category, *to whom*
something is restricted. Its DENY clause is byte-identical to the deployed definition in
the synth snapshot, and a test holds that. The additive candidate names both disjuncts
of ADR-076:151-153's subject. With one candidate, a candidate on axis F or G alone would
be half that subject.

**Neither has been swept against any guardrail.** Both are admitted **only through gate
2**. A green `tests/test_m09b_admission.py` is not admission.

## Findings — recorded, not resolved

1. **The brief's "G is 7 or 2" does not reproduce.** On M09's control run, both readings
   give decoded G 7, F majority 1, F at least once 4. Raw, with the five held grants read
   false, they give G 6, F 0, F 0. `tests/test_m09b_fg.py` holds both rows. A
   strict-bytes G over the *answered* half would need raw bytes no committed file
   carries, so it is not published. The re-date's reason holds on the measured
   numbers: the definition moves F and G both.
2. **The walker reaches no row for the additive topic.** `disclosure-shapes.yaml`'s
   rows carry no `topic` or `act` field, so a guardrail control on
   `authorship-misrepresentation` reads NOT RESOLVED on claim 6's command. The walker is
   not loosened and the frozen corpus is not edited. Owner: Security + Legal/S&P +
   Platform Engineering. Trigger: PR 4, before `rules/MER-AI-0001.yaml` gains the
   control.
3. **`platform/gateway/` is dropped from the guardrail home, not kept beside the stack
   file.** The walker reads topic definitions from whatever the home admits, so a wider
   home lets a topic defined outside the synthesized stack walk clean (plants P3, P4).
4. **979fbb2 was cited backticked and the resolver refused it**, here unbackticked for the same reason. Only the
   `throwaway-gate` branch holds it. This branch's first commit went in over that red,
   because a pipe hid pytest's exit code. That is corrected in a following commit, not
   by an amend.
5. **SPEC/09b still summarises five candidates and the throwaway sweeps.** It is not
   edited. SPEC/09b:200-201 makes ADR-077 the rule where the two differ.

## SPEC/09b's PR 3 items not in this PR

Per the brief, only four items are taken. These are not built here, and none is
dispositioned here:

- `rules/schema.json`'s `selector` and `additionalProperties: false`. The walker reads
  `selector`, and the schema does not declare it yet.
- `evals/adversarial.py`'s `classify_sha256` widening, a debt row whose trigger names PR 3.
- `candidates.json` and `tests/test_m09b_admission.py` joining the deployed-guardrail
  rule. They collect `(ai-quality, platform-eng, security)` on the census rule, with no
  ADR requirement.
- The gate-list freeze predicate, a debt row whose trigger names PR 3.
- The two seat rounds.
- Decision 4's deploy-refusal test for a pre-deploy no-winner. This PR has no deploy
  step to attach it to.

## Deletability audit

`milestones/M09b/pr3-deletability-audit.txt` — **26 property plants, 26 CAUGHT**: 14 on the walker and its home, 11 on the record and gates 1–2, and 1 on the raw-G count. **P11 was SILENT on its first run.** A docstring *sentence* naming a corpus never equals the file name, so the docstring exclusion was never reached. It got a test, and the check was not deleted. **2 gate plants, both red** under `python -m pave.cli check`: the widened home without the walker, and the walker without the widened home. So rule gap 4 and the walker are not separable. Every restore was byte-identical.

## Two-key

The diff triggers two rules and neither requires an ADR. The census rule
`(ai-quality, platform-eng, security)` covers `candidates.json`,
`test_m09b_admission.py` and `test_m09b_fg.py`. The chain reader rule
`(legal-sp, security, platform-eng)` covers `pave/rules.py` and `test_rules_trace.py`.

Two-Key-Disposition: security
Two-Key-Disposition: ai-quality
Two-Key-Disposition: platform-eng
Two-Key-Disposition: legal-sp
Two-Key-Rationale: security owns whether a topic wording is admissible and what the
  guardrail blocks, and neither candidate has been swept, so nothing here weakens a
  deployed control. ai-quality owns what the admission record and the fg reader's
  counts mean, and the digest is pinned in a later commit than the record.
  platform-eng owns the walker and the home, which land together because each alone
  is the defect ADR-076 decision 4 names. legal-sp holds the registry reader's key,
  and the walker makes a guardrail control resolve or fail and never read as walked.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

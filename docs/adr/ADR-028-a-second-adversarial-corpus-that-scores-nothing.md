# ADR-028: A second corpus under `quality/adversarial/` that scores nothing

**Status:** Accepted (M03)
**Seats:** Security / Red Team (the corpus and what its outcomes mean — two-key) ·
AI Quality (that it stays outside every score)

## Context

SPEC/01 pre-registers a teaching-to-the-test clause: a guardrail topic added
during the milestone it is measured in proves nothing, because whoever added it
had read the corpus. M01 defended two topics — `medical-advice` and
`entitlement-circumvention` — with five sentences that appear nowhere in
`probes.yaml`: three that must be blocked and two that must be allowed.

The defence was sound and the evidence was real. It was also **a comment** in
`milestones/M01/unearned.yaml`, produced by one hand-run under guardrail version
1.

ADR-024 then narrowed `entitlement-circumvention` from naming the subject to
naming the act. That is precisely the change that could have invalidated the
defence — two of the three blocked phrasings are entitlement cases — and **nobody
re-ran them**, because a comment cannot be re-run. The evidence for a live
control's calibration sat frozen against a policy that no longer existed, for two
milestones.

The obvious fix is to add the five phrasings to `probes.yaml`. That is the wrong
fix, and the reason is the point of this ADR.

## Decision

**The phrasings become their own corpus, `quality/adversarial/phrasings.yaml`,
and it scores nothing.**

A probe passes under G4: the guardrail blocked **or** a policy denied, **and** an
audit record exists. That is a statement about controls doing their job on a
hostile input. These five are a different kind of object — a **calibration check
on the topics themselves**, asking two questions no probe asks:

- **Do the topics generalize?** Text the corpus never contained is still caught.
- **Do the topics swallow the product?** Two entirely legitimate questions are
  still allowed.

The second question has no G4 answer at all. "This request was *not* blocked" is
not a probe result; it is the opposite of one. Merging these into `probes.yaml`
would put five rows in a scored corpus that the scorer cannot score, and the only
way to make them scoreable would be to define passing as *not blocked* for two of
them — a probe whose pass condition is that no control fired.

**They live under `quality/adversarial/` anyway, and that is deliberate.** The
path is Security's under CODEOWNERS and two-key under G9. A calibration check on
the guardrail's topics belongs to the seat that owns the guardrail's topics, and
filing it somewhere unowned to avoid the second key would be choosing a directory
to dodge a review.

**Three prose claims become tests** (`tests/test_phrasings.py`), because the
failure this ADR exists to prevent is prose that could have been checked and was
not:

- no phrasing appears in `probes.yaml`, verbatim or as an eight-word run;
- no phrasing carries instruction-override vocabulary;
- the committed run agrees with every declared expectation.

**A blocked phrasing must fire the topic it names.** The audit record's `assessed`
field is fetched back and checked against the phrasing's declared topic. Without
that, a `medical-advice` sentence stopped by `entitlement-circumvention` counts as
agreement while proving nothing about the topic under test — which is ADV-008's
defect stated generally: *an assert satisfiable by something other than the thing
it names*.

### Why this corpus is unconfounded and `probes.yaml` is not

ADV-006 and ADV-009 both fire `PROMPT_ATTACK` independently of any topic. Whatever
the topics do or do not do, those probes pass — so neither can isolate whether
`entitlement-circumvention` is doing anything at all. The five phrasings carry no
instruction-override language of any kind, which is what makes them the only
evidence in this repository that can answer the question ADR-024 raised.

## Consequences

Guardrail changes now have a check that re-runs rather than a comment that ages.
The cost is five model calls per guardrail change, which is the cheapest evidence
in the repo.

**The check ran under version 2 and all five agree.** Both entitlement phrasings
still fire the narrowed topic; both legitimate questions are allowed and assess
nothing at all. ADR-024's narrowing cut past the subject matter without cutting
past the behaviour, and the M01 defence survives the change that threatened it.

**This settles less than it might appear to.** It does not test ADV-002, whose
poisoned payload was subject-shaped under version 1 and act-shaped under version
2. It does not re-run the probe corpus, which is still scored at `k = 1` against
a guardrail this milestone measured as stochastic — 4 of 25 anchor cases returned
different verdicts across three identical inputs. Both remain owed to Security and
both remain M04's.

**At scale, replace with:** a calibration suite per denied topic, run on every
guardrail version bump before the version is promoted, with the topic's
generalization and its false-positive surface reported as two separate numbers.
The interface already matches — a phrasing declares an expectation and a topic,
and the runner reports agreement on both.

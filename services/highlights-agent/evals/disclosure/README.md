# The disclosure pack — highlights-agent

**Owning seat:** AI Quality (the pack) · Legal/S&P (the rule it discharges).
Two-key (`Two-Key-Disposition: ai-quality`) on every change, enforced by the
`two-key` check through `^services/[^/]+/evals/`.

This pack is `MER-AI-0001`'s executable control. The rule has sat `proposed` and
undisposed since M00a **on purpose** — its own header says why: it shipped in the
starter as `enforced` with controls already pointing at a `disclosure-*` pack
that also already existed, so the delta had happened at commit one and claim 6
was unprovable. M09 disposes it, and the diff that does so *is* the claim.

## What this is, and what it is not

| | |
|---|---|
| **A suite** | `disclosure`. Its own cases file, its own verdict record, its own history entry. `arm` means *which system produced these answers* over one case set, so a second case set is a suite, not an arm (ADR-075 D4) |
| **Not part of the twenty-five** | the goldens denominator stays **25**, pinned by name, so M09's `N/25` stays comparable to `m00b` through `m08b`. `tests/test_m09_goldens_denominator.py` refuses a `disclosure`-prefixed id in the golden file **by name** |
| **Not a graded suite** | CLAUDE.md's 5–10% headroom rule is the goldens'. This is a disposition witness: at 100% after the fix, that is the outcome |
| **Not judged** | no judge axis. `quality/judge/rubric-sports.md`'s existing `disclosure_present` axis is left unused and unmoved, and every instrument digest is what PR 1 left it |

## The two asserts

| assert | passes when |
|---|---|
| `ai_disclosure: required` | the key is **present** and holds a non-empty, non-whitespace string |
| `ai_disclosure: not_required` | the key is **present** and is `null` |

**Both test key presence rather than truthiness, and that is the whole of the
negative half's value.** `ai_disclosure` is not in `answer.schema.json`'s
`required` list, and the answer object is `additionalProperties: false`, so an
answer that never emits the key validates cleanly. A negative assert written as
"no disclosure text is present" would therefore be satisfied by a model that
stopped emitting the field altogether — a vacuous pass, and one that would read
as the fix working. `not_required` demands the agent say *no disclosure is owed
here* rather than say nothing.

The measured basis: of the 56 committed M08b samples that carry the key, **none**
is non-null. So the positive half fails today by construction, which is what
makes the delta a delta — and it is F1's premise, confirmed on committed evidence
rather than assumed.

## Sufficiency, asserted rather than trusted

`evals/deterministic.py::disclosure_sufficiency` refuses a pack that has lost
either half — at least one `required` case and at least one `not_required` case,
or the suite reports **INFRA**, never PASS. ADR-048 decision 4's shape: a pack
that has gone vacuous must not be able to do it silently, and deleting the single
negative case is the cheapest way to make a disclose-on-everything fix look
correct.

## Why every case carries exactly two asserts

`json_schema` is the floor; the disclosure assert is the control; nothing else.
The agent stands at 10/25 on the goldens, so a disclosure case carrying a
groundedness assert or an entitlement verdict could fail run A for a reason that
is not the disclosure control, and pass run B for a reason that is not the fix.
Claim 6's whole content is that a reader can trace the red to the **rule**.

## The rule that matters most

**Never edit a case to make a run pass.** A case that is wrong is fixed in its
own PR with the reasoning, reviewed by AI Quality, and the run is re-taken whole
(SPEC/09 constraint 3). These cases were authored **before** the disposition and
before either run.

## Where `disclosure-004` went, and the two sites still carrying it

The golden set reserved `disclosure-004` for M07. M07 is the guardrail milestone
and the reservation outlived three renumberings — a stated protection that is
absent, which CLAUDE.md ranks worse than a missing one. It is **withdrawn by
name**, not filled, and the id is **not reused**: this pack numbers from 101 so
that no reader joining the two files can conclude the reserved case was quietly
filled (ADR-075 D4).

**The reservation was in four places, not the two ADR-075 D4 named.** The fourth
is `templates/agent-tools/evals/golden/README.md.tmpl`, which every future
service inherits and which the golden README's round-trip check couples to it —
found by running that check rather than by reading. Withdrawn in PR 2 alongside
`evals/golden/README.md`, in the same diff, because the round-trip admits no
other order.

Two sites still carry the withdrawn wording and are **dated to the PR that
carries the fix**:

| site | why not here |
|---|---|
| `../golden/cases.yaml`'s header comment | `milestones/M08/context-census.json` digests the golden cases file, and `milestones/M08b/fresh-join.json` digests both that file and the census record. Editing a comment in it re-produces **three** committed records under `milestones/`, which this milestone's Definition of done reserves to the PR that moves them anyway |
| `../answer.schema.json`'s `ai_disclosure` description | the same cascade, **plus** it is model-facing: the file is rendered into both arms' prompts through `{schema}`, and it is the one stale-M07 site the model actually reads — *"Null until M07 disposes that rule"*, text telling the model to leave the field null. SPEC/09 constraint 2 reserves a change to what the model sees to the fix, so it moves **as part of** the fix and its cost is priced by the prompt-delta test |

Both are asserted as still-carrying by
`tests/test_m09_goldens_denominator.py::test_the_two_digested_sites_are_named_with_their_pr_rather_than_left_silent`,
so the day they are withdrawn that test is what tells the PR to update this
table — a pointer to a paid debt is the same stale sentence one milestone later.

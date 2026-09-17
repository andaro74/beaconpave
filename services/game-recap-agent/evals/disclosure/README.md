# The disclosure pack — game-recap-agent

**Owning seats:** AI Quality (the pack) · Legal/S&P (the rule it discharges).
**Two keys on every change** — `ai-quality` and `legal-sp` — enforced by the
`two-key` check through `^services/[^/]+/evals/disclosure/`.

This pack is `MER-AI-0001`'s executable control for this service, bound by the
rule's second `controls` entry (ADR-082). The reference service's pack under
`services/highlights-agent/evals/disclosure/` is the first, and its README holds
the reasoning this one does not repeat: why the assert reads whole words and
any-of, why it strips format characters before deciding visibility, why the
phrasings are policy and not mechanism, and why `not_required` demands the key
present and null rather than absent. Read that file for the assert; read this one
for what is different here.

## What is different here

| | |
|---|---|
| **Bound and unrun** | the reference pack was scored against a deployed service, and its positive half failed before the fix, which is what made ADR-075's delta a delta. This service has no deployment to score and no committed answers, so this control can fail the day a run exists and has not been read against one. The rule's third `limits` entry records that boundary, and `pave rules trace MER-AI-0001` prints it above the controls |
| **Outside the M09b guardrail** | the gateway disclosure guardrail is scoped to the deployed principal, which is the reference service. This service has an answer-side control and no guardrail line; the rule's fourth limit records it, owed to Security |
| **Catalog-fact negatives, not entitlement** | the reference pack's negative half is two entitlement lookups. This service grants `catalog-search` only, so its factual answers are a kick-off time (`disclosure-105`) and the plan tier a title carries in the catalog (`disclosure-107`). The rule's `covers` records that reading beside its text: a fact read off the catalog and stated as a fact is not a publishable summary of what a title is, and live-versus-replay, which the first draft of 107 asked, is such a summary and stays in scope |
| **No recap case, by the rule's own exclusion** | `scope.excludes` keeps the recap sense out, and `scope.revives` now carries a dated reading against this service: it is granted no source but the catalog, which carries no outcome, so it has nothing to author post-event copy from, and its golden pack scores an invented result as a failure. The state that would fire the clause on its own is written there too |
| **Its own suite** | `suite: disclosure`, scored by `python -m pave.cli evals disclosure game-recap-agent --answers …`. Not part of this service's twenty goldens. The headroom exemption ADR-075 decision 4 attaches to this suite by name applies here; this pack cites that decision and makes no exemption of its own |

## What reads this pack without a run

`tests/test_m09_disclosure.py` parametrises its pack-quality checks over every
pack the rule binds: exactly two asserts per case and no judge block, both
grammatical moods on both halves, no positive case asking for an outcome the
catalog cannot ground, every positive case naming its tokens, every assert in
the documented vocabulary. `tests/test_rules_trace.py` holds the properties
that only make sense across packs: both halves present by the lane's own
sufficiency check, at least five `required` cases, the same accepted phrasings
as every other bound pack, the headroom exemption load-bearing and cited, every
schema path pointing at this service, and this README naming the rule. It also
pins the sentences that make the binding honest, the bound-and-unrun limit and
the `revives` reading, because the Security seat struck each one and nothing
went red.

Planted one at a time before this pack merged, each caught by name: a weak
token in every positive case, the reference pack copied over this one, a judge
block, a positive asking who won, the question-shaped positive reworded, this
README deleted, an undocumented assert key, the limit deleted, the reading
deleted.

**What this cannot catch.** A positive case reworded into a factual lookup that
is not a summary keeps its `required` mode and passes every check above; the
tests read shape and words, not authorship, and only a run reads authorship.
That is the reason the pack takes two keys.

## Shape

Seven cases, five `required` and two `not_required`, each carrying exactly two
asserts: `json_schema` as the floor and `ai_disclosure` as the control. Each
grammatical mood appears on both halves (`disclosure-106` is a question that is
editorial; `disclosure-107` is an imperative that is not), so mood and authorship
are not confounded. `disclosure-102` is the case nearest the excluded sense, and
its comment says what keeps it a title summary.

## Never edited to make a run pass

A case that is wrong is fixed in its own PR with the reasoning, reviewed by AI
Quality, and the run is re-taken whole. No run exists yet. Before the first
run, two seat rounds moved 104 and 105 to an entitled viewer outside the
blackout markets, so the likeliest answer is about the copy or the fact and not
about access, and replaced 107's input for the reason in the table above.

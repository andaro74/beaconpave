# ADR-082: MER-AI-0001 binds to a second service, and a bound, unrun control is a control, not a claim

**Status: PROPOSED with the PR that carries it, 2026-09-16. ACCEPTED when that PR
merges**, which is the operator's disposition. Written with zero model calls and
zero AWS calls, on `main` at `b95f7cb`.

## Context

PR #167 committed `game-recap-agent`, a second service that authors previews,
tile blurbs and home-screen copy about catalog titles. `rules/MER-AI-0001.yaml`
is `enforced`, `blocking`, and its `scope.covers` reaches exactly that copy; it
is *"not narrowed by brand"* and *"binds to the service"*. Its only control was
the disclosure pack under `services/highlights-agent/`, so a second service
authoring in-scope copy had no control at all. `pave rules trace MER-AI-0001`
printed `binds highlights-agent` and nothing else, and `_binds`'s own docstring
had pre-registered the failure: *"a reader that inferred the only deployed
service would print the right answer today and a wrong one the day there are
two."*

The Legal/S&P seat found it in the sample PR's review, the PR recorded it as an
obligation owed against the rule's 2026-10-01 `review_by`, and this ADR
discharges it. Four things had to be decided, and each is a decision rather
than an edit. Two seat rounds on the PR changed three of them; what they changed
is recorded under each decision, because the first draft was wrong in ways the
next reader would otherwise repeat.

## Decision 1 — the rule gains a second `eval_pack` control, bound to the second service's own pack

`services/game-recap-agent/evals/disclosure/cases.yaml` is added: seven cases,
five `required` and two `not_required`, each carrying `json_schema` and
`ai_disclosure` and nothing else, on the reference pack's shape and for the
reference pack's reasons (ADR-075 decisions 3 and 4). It is its own suite. It
does not join the service's twenty goldens and moves no denominator. The
headroom exemption ADR-075 decision 4 attaches to `suite: disclosure` by name
applies to it by that decision's terms; this ADR relies on that and adds no
exemption.

`disposition.controls` lists it second. `pave rules trace` walks both, prints
`binds highlights-agent` and `binds game-recap-agent`, and
`tests/test_rules_trace.py`'s pin on the committed rule expects two `eval_pack`
controls, both resolving, in that order, by list equality rather than by count.

**The negative half differs, and the difference is a reading of `covers` that
is now written beside it.** The reference pack's negatives are entitlement
lookups. This service grants `catalog-search` only, so its non-editorial answers
are catalog facts: a kick-off time, and the plan tier a title carries in the
catalog. `scope.covers` now carries a dated paragraph saying so, because the
Legal/S&P seat found the reading recorded in this ADR and a README and nowhere
the registry reader prints. The same round found the first draft's second
negative, live-versus-replay, sitting inside *"publishable summaries of what a
title is"*; a `not_required` case inside the scope asserts that in-scope copy
must not disclose, which is the inversion `pave/twokey.py` names as the reason
this directory takes two keys. It was replaced.

## Decision 2 — `scope.revives` is read against this service, in the field, and is not triggered

The clause names *"a service that authors post-event copy joining the registry
as a caller"*. A service named `game-recap-agent` joined the registry as a caller
in PR #167, and the clause is worded as a mechanical trigger. Read on substance,
by the seat the clause assigns it to: the service is granted `catalog-search`
and no other tool, so its only source is `data/catalog.json`, which carries no
outcome for any title. It has nothing to author post-event copy from, and its
golden pack scores an invented result as a failure, by narrative-result bans on
its recap cases and by the judge's groundedness axis on every result case. Its
answer to a recap request is the refusal to confabulate `excludes` already
names.

**The first draft grounded this on a sentence that was false of the pack**,
that the golden pack *"forbids narrating a result on every recap case"*. Two
of its recap-shaped cases carry no ban at all, by design, because every phrasing
of a result can be hedged; the control for those is the judge. The Legal/S&P
seat struck the sentence, and the reading now rests on the service's tool grant
and its data source, which are facts of the registry and the catalog, with the
pack's scoring as the second leg rather than the first.

**The reading is recorded in the `revives` field itself, dated, and
`scope.decided_on` stays at 2026-09-10.** The first draft wrote it as a YAML
comment beside the clause and claimed `pave rules trace` would print it; the
trace reads fields and discards comments, so the claim was false and the
reading was deletable in silence. The second draft moved `decided_on` to the
reading's date; the Legal/S&P seat measured that as lossy, since the registry
would stop saying when the operative sentences were decided while the M09 close
artifact still prints that date, and both readings carry their own date inline.
So the field keeps the date of the sentences it dates, and each reading dates
itself. `covers` and `excludes` keep their operative sentences; `excludes` is
untouched. The `revives` field also names the state in which the second
disjunct fires on its own, without the catalog moving: a service granted a tool
that exposes outcomes from any source joining the registry as a caller. The
first disjunct is unchanged and still open. `tests/test_rules_trace.py` pins the
substantive sentences of both readings, not only their citations, because the
same seat measured that the sentences could go with the citation left behind.

**The reading's falsifier, named before it stands (ADR-080).** The reading is
false the day `game-recap-agent` is granted a second tool, one that could expose
an outcome. The Security seat granted it a registry-backed results tool and
measured `pave verify` PASS, the trace still printing NOT triggered, and every
test green: a narrowing of a live revival clause on an enforced blocking rule
that nothing could detect. So the premise is now a check, not a sentence.
`test_the_revives_readings_premise_holds_in_the_registry_and_the_manifest`
asserts that the service's manifest declares `catalog-search` alone and that
the registry grants it nothing else, and fails citing the reading. The command
that detects the false state is `python -m pytest tests/test_rules_trace.py`;
the day it fails, the reading is re-taken on Legal/S&P's key, not the assertion
loosened. What a substring pin cannot hold is the conclusion itself: the same
seat rewrote NOT triggered to TRIGGERED around the pinned strings, silently.
The premise pin is what holds the conclusion, and that limit is stated in the
test's docstring rather than papered over.

## Decision 3 — the control is bound and unrun, and that is stated as a limit, not sold as a disposition read

ADR-075's disposition of this rule was a delta someone read: run A failed every
positive case, one sentence fixed it, run B passed. That reading is what made
claim 6 a claim. It cannot be repeated here. `game-recap-agent` has no
deployment, because the gateway principal is fixed to the reference service
(ADR-048 amendment 1), and no committed answers. The lane exists,
`python -m pave.cli evals disclosure game-recap-agent --answers …`, and has
nothing to score. No gate runs that lane for either service; a run is a
decision someone takes.

So the second control is **bound and unrun**. It can fail the day a run exists;
it has not been read against one. That is a third `limits` entry on the
disposition, owed to Legal/S&P, AI Quality, Platform Engineering and Security,
the seats that can close its trigger, and dated to the milestone that deploys a
second principal, so that `pave rules trace` prints the boundary beside the
chain rather than a reader inferring a delta that was never taken. A fourth
limit, owed to Security, records that the service also sits outside the M09b
gateway guardrail, which is scoped to the deployed principal, and names the
probe to write when a principal exists. `tests/test_rules_trace.py` pins both
limits, because the Security seat struck the third and nothing went red.

**Why that is still worth binding.** The alternative, leaving the rule bound to
one service until a second can be deployed, is the orphan the trace reader was
written to expose: an enforced blocking rule whose scope reaches a committed
service and whose registry says nothing about it. A bound control with a stated
limit is a protection a reader can find and a run can exercise. An unbound
service is a protection that is stated in the rule's scope and absent from its
disposition, which CLAUDE.md ranks below a missing one.

## Decision 4 — the properties a pack must have are asserted over every pack the rule binds

`tests/test_m09_disclosure.py` asserted exactly-two-asserts, mood crossing,
no-outcome positives, named tokens and the assert vocabulary against one
hard-coded pack. The Security seat planted seven defects in the second pack and
each was silent; the AI Quality seat ran the same tests against it by hand and
each passed, which is coverage nobody has. Those tests now parametrise over the
rule's `eval_pack` controls, and `tests/test_rules_trace.py` holds what only
makes sense across packs: both halves and no toothless case by the lane's own
sufficiency check, at least five `required` cases (ADR-075 decision 3), the
same accepted phrasings in every bound pack, the exemption load-bearing and
cited, every schema path pointing at its own service, and a README naming the
rule.

**The phrasings are held two ways.** `disclosure_sufficiency` refuses
`required: []` and nothing refuses `required: [a]`; the Security seat scored the
second pack 7/7 PASS against the answer `"a"`. The reference pack is protected
from that by three hermetic scoring tests in `tests/test_m09_disclosure.py`
that were hard-scoped to it, not by its run as the first draft of this ADR
said; the same seat measured that. Those three tests now parametrise over every
bound pack, so a weak token in the second pack fails its own scoring test
directly. Equality with the reference's list stays as the cross-pack check, so
the two packs cannot drift from one policy without a decision. Neither changes
the scorer, which would be a different two-key rule and a different PR.

## What this does NOT do

- **It does not read a delta.** No run, no claim, no history entry, no
  progression row. Claim 6 is proven once, on the reference service, and this
  ADR does not say it is proven twice.
- **It does not change the phrasings, the assert, or the scorer.** The pack
  reuses the reference's accepted phrasings verbatim. `evals/deterministic.py`
  is untouched.
- **It does not change what `covers` or `excludes` cover.** `covers` and
  `revives` each gain a dated reading; `excludes` is untouched; no operative
  sentence moves. The line the `covers` reading draws is summary versus bare
  fact, never the subject: live-versus-replay asked for as publishable copy is
  in scope, and as a bare lookup it is a fact like a kick-off time.
- **It does not close three gaps the Legal/S&P seat named, and records them
  here rather than as limits, because each is a decision for the operator.**
  The rule's scope is *"not narrowed by brand"* and names news copy as in scope,
  and both bound services are sports-brand with no news case in either pack.
  Limit 1 names `publish-highlight` as the action that puts copy in front of
  viewers, and the second service declares no publish-class tool, so its
  in-scope copy has no governed publication route at all. And limits 3 and 4
  are dated to a milestone that deploys a second principal, which is not
  scheduled, while the rule's `review_by` is 2026-10-01; that review is where
  the operator decides whether the dates stand.
- **It does not add the second pack to CI.** The gate scores committed answers
  for the reference service only, and there are none here to score.
- **It does not make the scaffold emit a disclosure pack.** `pave new` renders
  five files and none under `evals/disclosure/`, so the next service arrives
  with no control for a rule that binds to the service, and `orphan_rules`
  cannot see an absent control. ADR-045 already records the `services/*`
  enumeration debt this belongs to; the scale-up path below is its repair.

## Scale-up path

*At scale, a rule that binds to the service binds by manifest declaration rather
than by a hand-listed control per service: the manifest names the rules it is
subject to, the scaffolder renders the disposition pack the rule requires, and
`pave verify` refuses a service whose manifest names a rule its tree carries no
control for. `_binds` already reads the service off the control path, and
`RENDERED` already lists what the scaffold emits; the interface already matches.*

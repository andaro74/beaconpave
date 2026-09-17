# Sample: `game-recap-agent`, onboarded through `pave new`

A second Meridian Sports service, created with the scaffolder and carried through
the onboarding steps the scaffold refuses to take for a team. This is a record of
what happened, not a claim. Claim 1 (*one command to a governed service*) is
INCOMPLETE in the README for two stated reasons, and this record bears on both
without moving either: it shows what the second reason (the authorship left
behind) looks like in files, and it runs into the first (nothing deploys) at the
registry. Moving that row is a milestone with a pre-registered falsifier
(ADR-080), and this document does not do it.

**Owning seats.** The manifest is AI Quality plus Tool Owner; the golden pack and
its README are AI Quality; the registry line is Tool Owner plus Legal/S&P. The
rendered `gateway_client.py` collects no key: the rule that protects the
reference copy is pinned to `services/highlights-agent/`, and the template rule
covers `templates/`, so a rendered copy in a new service falls between them. This
document collects no key.

## What the service is

A viewer asks for a recap or a preview of a game, and the agent answers from the
catalog through `catalog-search`, the one tool the manifest declares. The catalog
holds three Meridian Sports titles and no results: `t003` is a replay of a finished
game with no score in any field, `t001` kicks off one hour after the evaluation
clock, `t005` is a week away. So a true recap cannot be written from the data the
service has, and the pack is built around that: the correct answer says what the
catalog knows, points at the replay, and invents nothing.

## The commands, in order

Every command runs from the repository root.

```
python -m pave.cli new game-recap-agent --brand meridian-sports
```

Rendered five files into `services/game-recap-agent/` and printed the two steps it
cannot take, numbered **1. register the service as a caller** (refusal row 3) and
**2. write your golden cases** (refusal row 8). The banner's computed seat count
was **3: ai-quality, legal-sp, tool-owner**, read from `pave/twokey.py` at the
moment of the run.

```
python -m pave.cli verify game-recap-agent
```

Before any edit, two refusals, rows 3 and 8. This record takes the banner's two
steps in the **reverse** order, pack first, because that shows the one-finding
intermediate state a team will meet; the banner's numbering is the one to follow
when reproducing.

**The pack (the banner's step 2).** The three `author: pave-template` rows were
replaced by twenty cases, and the rendered golden README was replaced too, for the
reason in the next section. With the pack in place and the registry untouched,
`verify` reported one finding, row 3, and `make check` reported one failure,
`tests/test_manifest_verify.py::test_every_committed_service_verifies_clean`, on
the same row. That is the scaffold failing its own gate by design (ADR-047
decision 4).

**The registry (the banner's step 1).** One line in `platform/registry/tools.yaml`,
under the entry beginning `- id: catalog-search`:

```
callers: [highlights-agent, game-recap-agent]
```

Then the policy the registry decides, and the suite:

```
python -m pave.cli policy generate
python -m pave.cli policy generate --check
python -m pave.cli verify --all
make check
```

The generator wrote one new Cedar permit, `Service::"game-recap-agent"` invoking
`Tool::"catalog-search"`, and nothing else. `tools.contracts.json` did not change:
contracts are keyed per tool on consequence and schemas and carry no callers, so a
caller addition is not a contract event, which is why the banner's instruction to
stage it had nothing to stage. `verify --all` reported PASS for both services and
`make check` was green. `publish-highlight` was not touched; its consequence class
is `publish` and a caller there is a Tool Owner plus Legal/S&P decision, not a
scaffolding step.

## What the registry line is, stated plainly

The gateway's Cedar principal is fixed in `platform/infra/lib/gateway-stack.ts`
to the reference service. So the new permit is a **standing grant to a principal
the deployed stack cannot assume**. ADR-048 removed a registry caller of exactly
that shape (`recap-agent`) because it was *"a phantom in the deployed
authorization set"* and *"was never a service"*. The difference here is the second
half: `game-recap-agent` is a committed, verified service with a manifest and a
pack, which is the state ADR-048's own scale-up path names as the point at which
*"this ADR's cut un-cuts itself"*. The un-cut is real at the registry and not at
the runtime, and that is recorded in ADR-048 amendment 1 rather than left for the
next reader to discover. The Tool Owner prose site the ADR named,
`tools/catalog-search/README.md`, is corrected in the same change; the
`platform/gateway/handler.py` docstring that describes the one-caller state is
keyed to the gateway and is left as it stands, named here as stale.

## The rendered golden README, and why it was replaced

`pave new` renders `evals/golden/README.md` from a template that is the reference
service's README with the heading changed. Rendered into this service it claimed
the cases were authored at M00a before a control ran, that the pack had 25 cases
with headroom at 2 of 25, that an entitlement tool and a trajectory expectation
were part of the vocabulary here, and that `tests/test_contracts.py` enforces the
assert vocabulary on this pack. None of that is true of this service, and
`cases.yaml` tells a team to read that file first. It was replaced by a README
that describes this pack. The template is Platform Engineering's, is four-seat,
and is not changed here; the defect is recorded rather than fixed.

## The pack, measured

| | game-recap-agent | highlights-agent (reference) |
|---|---|---|
| cases | 20 | 25 |
| lines | 446 | 510 |
| content lines (no comments, no blanks) | 300 | not stated |
| asserts | 118 | 138 |
| cases with a `judge:` block | 20 | 25 |
| `must_not_claim` asserts | 27 | 4 |
| `must_mention` asserts | 11 | not counted |
| `entitlement:` verdicts / `entitlement_source` asserts | 0 / 0 | 12 / 11 |
| headroom cases (`expect_near_threshold`) | 2 (10.0%) | 2 (8%) |

The reference cells marked with a number were counted from
`services/highlights-agent/evals/golden/cases.yaml` on the day; the README's own
M05 measurement states 510 lines, 25 cases and 138 asserts, and the rest is not
in it. The pack leans on negative bans seven times harder than the reference,
against a recorded base rate of four bans in the reference's twenty-five cases
that a correct answer tripped. The first draft here had twelve such bans; the AI
Quality seat found them before any run and they were replaced by three narrative
phrasings, with the residual risk and the vocabulary gap stated in the pack
header and its README.

Two of twenty is 10.0%, the upper edge of the 5–10% band. A third flag at twenty
cases is red, and so is deleting any one unflagged case.

**What the cases do.** Five recaps over titles with no result. Four groundedness
traps: a fixture not in the catalog (`cited_titles_empty`, where citing nothing is
the right answer), a second leg that never happened, scorers, and season records.
Five previews and recommendations, the half of the job the catalog can support.
Four cover brand tone, concision, a two-part question and a bare *"Recap the
game."* Two are headroom.

**What the cases deliberately omit.** No `entitlement:` verdict, no
`entitlement_source`, no `trajectory` expectation: the manifest grants one read
tool. No `ai_disclosure` assert: MER-AI-0001's control is a disposition pack of
its own suite (ADR-075 decision 4), and the cases it reaches are listed in the
pack header.

**Authored before any run.** No answers exist for this service and nothing has been
recorded to `evals/history/`. The pack has not been scored, so no number here is a
score.

## What this sample does not show

- **No deploy.** The CDK app deploys the gateway and the audit trail, not a
  second agent, and the gateway principal is fixed to the reference service. A
  request from this service has no deployed runtime to arrive through. ADR-047
  lists *"it does not deploy"* as a stated cut, and this sample leaves it where
  it found it.
- **No time measurement.** The authorship was done by an assistant with the
  catalog, the assert vocabulary and the repository's history already in hand,
  which is exactly the knowledge claim 1's thirty minutes assumes a developer
  does not have. The number claim 1 is short on was not measured here. The
  pack's size is recorded above so that a later measurement has something to
  compare against.
- **The contract tests read the pack, since the PR after this one.** When the
  sample merged, `pave verify` read four rows of it and `tests/test_contracts.py`
  was pinned to the reference service, so the vocabulary, vacuity, catalog-id and
  viewer checks never ran on this pack. That file now discovers every committed
  service's pack and asserts the discovery's own sufficiency; three planted
  defects in this pack were each caught by name before it merged. The CI evals
  step still scores committed answers for the reference service only, and this
  service has none to score.
- **A disclosure control, bound and unrun (ADR-082).** MER-AI-0001 is `enforced`,
  binds to the service, and its `covers` reaches previews, tiles and home-screen
  blurbs, which this service writes. When the sample merged its only control
  bound to `highlights-agent`. The rule now lists this service's own disclosure
  pack as a second control, reads its `revives` and `covers` clauses against
  this service in the fields the trace prints, and records in its limits that
  the control has no run to be read against, because nothing can deploy this
  service yet, and that the service sits outside the M09b guardrail. The
  disclosure pack-quality checks in `tests/test_m09_disclosure.py` and the
  cross-pack checks in `tests/test_rules_trace.py` run over this pack. A bound
  control with stated limits; not a second reading of claim 6.
- **No second brand.** `--brand meridian-sports` is the only value the judge can
  score.
- **One frozen file.** Onboarding touched nothing under `pave/`, and could not
  have: `tests/test_drill_pins.py` requires the last commit on `pave/cli.py` to
  be an **ancestor** of the commit that last changed the M11 readers transcript.
  It reads ancestry, not dates, so a later commit with any content on that path
  fails it, and so does a revert. Any edit there is an M11 pre-registration
  event. A scaffolded service never needs one, which is worth knowing before a
  team reaches for the CLI to fix its own help text.

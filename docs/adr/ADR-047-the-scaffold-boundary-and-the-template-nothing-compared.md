# ADR-047: the scaffold's boundary — five files of fourteen, two of them wrongly specified as verbatim, and a template directory nothing had ever compared to the service it copies

**Status:** Proposed. **Zero model calls.**
**Seats:** Platform Engineering (the mechanism) · Service Team (what a team meets
first) · Tool Owner (the declared tool set) · AI Quality (the case floor and the
scaffold pack) · Security / Red Team (the wire text and the omitted probe runner)

`pave new` was a stub that printed a sentence and exited 0, advertising four things
it did not do. `templates/agent-tools/` was one README. This ADR records what the
scaffold renders, what it deliberately refuses to render, and the two things it
cannot do on a team's behalf.

## Decision 1 — five files, and the omission with a governance reason

The reference service is fourteen files. Nine are M01–M04 measurement harnesses
(`inspect_context.py`, `run_judge.py`, `run_phrasings.py`, `run_split.py`,
`run_via_gateway.py`, `run_with_tools.py`, `topic_baseline.py`,
`verify_guardrail_pin.py`, `run_probes_via_gateway.py`) that a new service needs
none of.

**The probe runner's omission is not a scope decision.**
`^services/[^/]+/run_probes(_via_gateway)?\.py$` is on a `(security, platform-eng)`
rule, so emitting one would hand every team a file it could never edit alone. The
Tool Owner seat found the sharper half of this by walking a second service through
onboarding: `pave/cli.py`'s adversarial lane told a service with no comparator to
run `services/<svc>/run_probes_via_gateway.py --k 3` — **a file `pave new` does not
render and the team cannot write.** The first instruction the adversarial lane gave
a scaffolded service was unfollowable. That message now names the constraint instead
of inventing a path.

## Decision 2 — all five files are `.tmpl`, and two of them were specified as verbatim

SPEC/05 listed `evals/answer.schema.json` and `evals/golden/README.md` as rendered
**verbatim**. Both carry the reference service's identity:

| file | what it carries |
|---|---|
| `answer.schema.json:3` | `"$id": "https://beaconpave/services/highlights-agent/evals/answer.schema.json"` |
| `answer.schema.json:4` | `"title": "highlights-agent answer"` |
| `evals/golden/README.md:1` | `# Golden set — highlights-agent (Meridian Sports)` |

Two services rendered verbatim would have shared one `$id` — the field a JSON-Schema
resolver keys on. Found by the Platform Engineering seat, which had already applied
the identical reasoning to `gateway_client.py.tmpl` one row up in the same table.

**The templates are derived, not retyped**, and that is what makes decision 3
possible.

## Decision 3 — the pairwise check is a round-trip, which is stronger than "byte-identical"

A template is a copy, and a copy of a living file is wrong the moment the original
moves. **Nothing in this repository compared `templates/agent-tools/` to
`services/highlights-agent/` before this ADR** — the directory held one README, so a
template could have drifted for four milestones with nothing red.

SPEC/05 asked for "byte-identical" on two pairs. That cannot hold: a template
carries placeholders, so it can never equal the reference. What is asserted instead:

> rendering the template **with the reference service's own values** reproduces the
> reference file byte for byte.

That catches an edit on either side and is only expressible because the templates
were derived. The other three pairs use the normalisation their content admits — key
set and nesting for the manifest, `ast.JoinedStr` skeletons for the client, the
closed case vocabulary for the pack. `test_the_pair_list_covers_every_rendered_file`
asserts all five are covered, because four pairwise tests over five files leaves one
template comparable to nothing, and that is the one that drifts.

**The client pair is the load-bearing one.** `gateway_client.py.tmpl` carries
`user_turn`, the wire text of every observation every scaffolded service will ever be
judged on — and **no instrument digest covers the transport** (ADR-048). A template
that drifted there would silently give every future service a payload shape different
from the one the platform's own numbers were measured with, with nothing else going
red.

## Decision 4 — the scaffold does not pass its own gate

`pave verify <service>` refuses a freshly rendered service with **exactly two**
findings, and the row set is asserted exactly rather than as "some findings":

| row | finding | why `pave new` may not fix it |
|---|---|---|
| 3 | declares `catalog-search`, is not in its `callers:` | the registry line is a `tool-owner` + `legal-sp` decision. A scaffolder that granted itself tool access would be the authorization hole the tool plane exists to close, arriving through the front door |
| 8 | 0 disposed cases against a floor of 20 | nobody has written a golden case yet, and the template's three are marked `pave-template` |

Draft 4's definition of done implied the scaffold is green, **which proves nothing**:
an unknown service was 1861 passed before ADR-046 — invisible rather than correct. A
scaffold that verified clean would teach a team that the gate means nothing.

Asserting the exact row set matters as much as asserting failure: a scaffold failing
for a *third* reason has a defect in it, and "not green" would hide that.

## Decision 5 — three worked examples, not twenty scaffolded rows

The pack teaches by example: one deterministic-only case (the shape CLAUDE.md's style
rule prefers), one judged case, one headroom case. Twenty scaffolded rows would be an
invitation to edit the author field twenty times; three is enough to show the
vocabulary and too few to mistake for a pack.

**The residual, stated rather than discovered:** the floor counts *disposition*, and
disposition is a claim. A team can flip `provenance.author` on template rows without
reading them and the repository cannot tell. `disposed()` makes the default honest and
the lie deliberate; it does not make the lie impossible. The scaffold pack says so in
its own comments rather than leaving a team to find it.

## Decision 6 — the sports cut, as a check rather than a sentence

SPEC/05 said *"M05 scaffolds a sports service"* and left `--brand` enforced by a
`print()`; `meridian-sports → meridian-news` measured **1889 passed**. Row 14 and
`scaffold.check` now refuse it against `floors.SUPPORTED_BRANDS`.

**And the cut itself was stated wrongly, which the Service Team seat measured.** The
blocker is not the *brand*: a **fictional sports** title with an event, a start time
and `sports-tier` is the identical **16 failures**, because the catalog is embedded
model-facing in the judge prompt and digested into `quality/judge/frozen.json`. The
cascade is the judge freeze and it is **brand-blind**.

So the real cut is narrower and is now checked:

> A scaffolded service may reuse the committed catalog titles. **Any service needing
> its own content is blocked, for any brand**, until a judge re-freeze (two-key
> `ai-quality`) plus superseding history entries.

`test_the_scaffold_cites_only_committed_catalog_titles` asserts the scaffold pack
cites only `meridian-sports` titles that exist — and goes red the day one is renamed,
which is exactly when the scaffold would otherwise start emitting a pack whose first
run fails for a reason nobody caused.

## Decision 7 — the onboarding seat count is computed, not written down

SPEC/05's banner named **five** seats. The Service Team and Tool Owner seats
independently measured **three**: `ai-quality`, `legal-sp`, `tool-owner`. `security`
and `platform-eng` entered that count solely through the probe-runner rule, and this
command renders no probe runner.

Over-stating is not the safe direction. `twokey.evaluate()` reports only **missing**
seats, so two surplus dispositions pass silently — a banner over-stating the cost
teaches every team to attest past rules it never triggered, which is the habit G9
depends on nobody having.

`onboarding_seats()` therefore computes the list from `pave/twokey.py` at print time.
Adding a rule that touches a rendered path changes the banner with no edit here.

## Decision 8 — the registry instruction anchors on `- id:`, never on a line

Draft 4 said *"names the tool id **and the line**"*. A line number shifts when any
tool is added, and after ADR-048 removed `recap-agent` **all three `callers:` lines
are byte-identical** — so quoting the line's content is ambiguous too.

The load-bearing half is the refusal, because during the SPEC/05 review a seat
following the vaguer instruction **granted itself the publish-class tool**. The
banner now says, at the same volume as the instruction, not to add oneself under
`- id: publish-highlight`.

`test_the_banner_anchors_on_an_id_and_never_on_a_line_number` asserts the `callers:`
lines are still indistinguishable, so if that stops being true the reasoning is
revisited rather than the instruction silently becoming safe by accident.

## Decision 9 — the rendered client's comments are rewritten, not carried

The reference's `SYSTEM` comment says it is *"BYTE-IDENTICAL to
`services/highlights-agent-baseline/run_baseline.py`, and
`tests/test_gateway_run_parity.py` fails if the two drift."* **That is false of a
scaffolded service**, which has no recorded control and no such pin — and a comment
claiming a protection that does not exist is the pattern this repository has now
recorded nine times. The template says instead that the prompt is the team's, that
nothing pins it, and what may still not be done to it.

The same applies to the two docstrings describing M01/M02 lineage decisions that
belong to `highlights-agent`.

## The deletability audit — 19 mutations, one silent

| mutation | result |
|---|---|
| a file dropped from `RENDERED` | CAUGHT |
| `highlights-agent` put back into the schema template's `$id` | CAUGHT |
| `render()`'s leftover-placeholder check disabled | CAUGHT |
| the brand check disabled | CAUGHT |
| creates-only disabled | CAUGHT |
| the `-baseline` suffix check disabled | CAUGHT |
| the service-name check disabled | CAUGHT |
| `onboarding_seats()` hardcoded to five seats | CAUGHT |
| the scaffold pack cites a title id that does not exist | CAUGHT |
| the scaffold pack cites a `meridian-news` title | CAUGHT |
| the headroom example removed from the pack | CAUGHT |
| `user_turn` reworded in the template | CAUGHT |
| `gates.budgets.p95_ms` erased from the manifest template | CAUGHT |
| the manifest template declares no tool | CAUGHT |
| the banner's `publish-highlight` warning replaced with "add yourself wherever you need access" | CAUGHT |
| the two-key regex narrowed to `templates/agent-tools/[^/]+` (dropping everything under `evals/`) | CAUGHT |
| `security` dropped from the scaffold rule's seat set | CAUGHT |
| `pave new`'s refusal path returning exit 0 | CAUGHT |
| **the template's `provenance.author` changed from `pave-template`** | **SILENT, 2053 passed** |

**The silent one, and why prediction 8's test could not see it.** With three rows
counting as disposed the pack is still 3 against a floor of 20 — so row 8 still
fires, the row set is still `[3, 8]`, and the refusal's message names
`pave-template` because that string is a constant in the message either way. The
test was reading the **tally** and the defect was in the **marking**: "a count sees
arithmetic, not identity", the shape ADR-045 recorded, arriving in the check written
against it.

What it would have cost is worse than a wrong number. `disposed()` exists so that the
honest default is "nobody has stood behind this yet" and a false claim has to be
made deliberately. A template shipping pre-disposed rows inverts that on day one, for
every service anyone ever scaffolds. `test_every_scaffolded_row_is_marked_as_scaffolding`
now asserts `floors.disposed(pack) == []` on the **rendered** pack.

## Two gaps found before the audit, both by writing the test rather than reading

1. **Nothing exercised the CLI wrapper.** `tests/test_scaffold.py` called
   `scaffold.create` directly, so `pave new`'s exit codes were untested — precisely
   the gap that produced ADR-046's one silent mutation one component over, where
   `pave/verify.py` returning 0 on findings was invisible at 1982 passed. Writing the
   test first meant `cli-refusal-exits-zero` was CAUGHT rather than discovered.
2. **`relative_to` raised in the one command that promises named messages.**
   `scaffold_new` printed `path.relative_to(ROOT)`, which raises `ValueError` for a
   path outside the repository — a traceback in the first command a team ever runs.
   Found by the new test, not by reading.

## What this does NOT do

- **It does not deploy.** *"Deployed, traced, metered, guarded agent in minutes"* was
  the demo script's line and it was never true; Act 1 is rewritten to run `verify` and
  let it fail on camera.
- **It does not verify at deploy**, and the demo script now says so out loud. That is
  ADR-046 decision 4.
- **It does not enable a second brand.** M08's.
- **It does not scaffold a probe runner, a `gate.yml` or a CODEOWNERS entry.**
- **It does not make a template fix reach an existing service.** `pave new` is
  creates-only; there is no `pave update`, and a service that has diverged is a
  service whose team owns the divergence. At scale that is a template-version field
  and a migration command — `template: agent-tools@0.1.0` is already in every rendered
  manifest, unread.
- **It cannot tell a real disposition from a flipped field.** Decision 5.

## Scale-up path

*At scale, `templates/agent-tools/` becomes a versioned template repository the
scaffolder resolves by the `template:` field the manifest already carries, and the
round-trip test becomes that repository's conformance suite against a reference
service; `RENDERED` is already a list of `(source, destination)` pairs and `render()`
already takes a values dict — the interface already matches.*

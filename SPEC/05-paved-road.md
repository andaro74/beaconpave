# SPEC/05 — The paved road, and the manifest nothing verifies

**Owning seat:** PM (spec) · Platform Engineering (`pave new`, the template, the
verifier, the synth binding) · Service Team (the developer who runs one command
and lives with what it produced) · Data Governance (`classification`, the field
G5 routes on) · Tool Owner (`tools:` and the registry's `callers`) · AI Quality
(`gates.*` — the ceilings and the case floor are gate criteria) · Security /
Red Team (`gateway-stack.ts`, two-key with an ADR)
**Milestone:** M05 · branch `m05-paved-road` · tag `m05`

## Why this milestone exists

Claim 1 — *one command → governed service* — is the only claim in the table
whose **proof artifact is a command that prints a sentence and exits 0**:

```
$ python -m pave.cli new recap-agent --brand meridian-news --classification internal
[pave new] (stub) would: scaffold service ['recap-agent', ...] from templates/agent-tools
  implement in the component referenced in README.md's repository map.
$ echo $?
0
```

That is the self-nomination `pave evals dryrun` carried into M03 and
`pave adversarial` carried into M04, arriving a third time.
`templates/agent-tools/` — *"the scaffold every service is born from"* in the
README's repository map — is one README file saying that the contract "is
already committed elsewhere in the repo."

But the stub is the smaller half. The larger half is what the stub would have
produced.

**`pave.manifest.yaml` is a ten-field declaration that nothing verifies, and six
of its ten fields can be deleted outright with the whole suite green.** It
declares the classification G5 routes on, the tools G3 authorizes, the budgets
the gate ceilings come from, and the case floor that enforces *"no unevaluated
agents"*. Measured on `07e8cd1`, deleting each top-level key in turn and running
the full suite:

| deleted key | result |
|---|---|
| `apiVersion` | **1795 passed** |
| `template` | **1795 passed** |
| `brand` | **1795 passed** |
| `owners` | **1795 passed** |
| `runtime` | **1795 passed** |
| `attestations` | **1795 passed** |
| `service` | 1 failed — `test_manifest_service_matches_its_directory` |
| `classification` | 1 failed — `test_manifest_classification_is_not_sensitive` |
| `tools` | 1 failed — `KeyError` inside `test_manifest_tools_are_all_registered` |
| `gates` | 6 failed — four `KeyError`s and two ceiling pins |

Four keys are read at all, and three of those four fail on a missing-key lookup
rather than on a rejected value. **Changing a value rather than removing it is
green in every case that matters:**

- `classification: internal` → `public`: **1795 passed.**
- `gates.eval_min_cases: 20` → `0`: **1795 passed.** The floor that enforces
  "no unevaluated agents" is a number the service that must clear it writes for
  itself, and lowering it to zero moves nothing.
- delete `entitlement-check` from `tools:`: **1795 passed.**

And the field the manifest itself describes as the deploy-time control:

```yaml
attestations:                      # written by CI, verified at deploy
  gate_verdict: required
  manifest_signature: required
```

Nothing writes either one. Nothing verifies either one. Deleting the block is
**1795 passed**. This repository has a name for that shape and CLAUDE.md states
it: a protection that is *stated and absent* is worse than one that is missing,
because it stops anyone looking for the real one. This is its ninth recorded
arrival and the first one in a file a service team owns.

M05 fixes exactly that, and builds the command that produces it.

## What M05 builds

1. **`pave new <name> --brand <b> --classification <c>` — a real scaffold from a
   real template.** Renders `templates/agent-tools/` into `services/<name>/`:
   the manifest, a starter golden pack, the answer schema, the gateway-client
   wiring, and a service README. It writes only files the service team owns, and
   **prints — rather than writes — the two edits that belong to other seats**
   (the registry `callers` entry, tool-owner + legal-sp; the comparator pin,
   three keys). A scaffold that can write another seat's file is a key-forging
   tool wearing a paved road's clothes.

2. **`pave/manifest.py` — the verifier, as functions, in one module.** Every
   check this milestone adds lives here, for ADR-042 decision 3's reason: the
   instance that decides cannot be a pytest, because `tests/conftest.py` and
   `pyproject.toml` control the harness on zero keys. The module takes the same
   keys as the files it protects.

3. **`pave verify [<service>|--all]` and the `manifest` gate lane.**
   `pave gate manifest --out verdict-manifest.json` joins the `--verdicts` list
   `gate decide` reads, so an absent verdict blocks exactly as every other lane's
   does. `pave check` runs the same functions locally.

4. **The manifest becomes deployment configuration.** `SERVICE_PRINCIPAL`, the
   declared classification and the tool set stop being TypeScript literals in
   `gateway-stack.ts` and come from the verified manifest at synth time. The
   manifest's normalised digest is carried in the synthesized template, so the
   freshness lane that already blocks (`verdict-infra.json`, ADR-017) is what
   makes `attestations.manifest_signature` true. **That requires narrowing
   `pave/infra.py:normalize`, which today erases it** — see pre-flight finding 8.

5. **Scaffold parity, as a test.** The template rendered with the reference
   service's own parameters must reproduce the committed
   `services/highlights-agent/pave.manifest.yaml`. Template drift becomes red
   rather than becoming a lie in Act 1 — the Platform seat's sixth review
   question, which has had nothing to ask it of since the repo began.

6. **Two keys on the manifest and on the template.** `gates.*` and
   `classification` are gate criteria written by the seat that must clear them.
   See pre-flight finding 3: two tests already tell their reader this path is
   two-key, and it is on no rule.

7. **The three recordings owed by this milestone** — Acts 0, 1 and 2 — or a
   deliberate, reasoned re-deferral in `docs/governance/recordings.json`.
   `tests/test_demo_recordings.py` turns red the moment M05's progression row is
   marked ✅ with any of them still unrecorded, and that is the check working.

## What M05 deliberately does NOT build

**No second committed service.** `pave new` is exercised into `tmp_path` by the
hermetic suite and into a scratch directory for the recording. A committed
`recap-agent` would double the comparator registry, the arm set, the golden
pack, the CODEOWNERS block and the L2 lane to prove a command that a test can
prove for free — and a scaffolded service is *supposed* to be red until its team
governs it, which `main` may never be.

**No new deployed compute, and therefore no agent Lambda.** Claim 1's proof
artifact says *"repo → deployed agent under 30 min"* and this milestone will not
deploy an agent. The reason is recorded rather than skipped, and it is the
load-bearing decision below.

**No model calls. Zero.** M05 changes no prompt, no catalog, no guardrail, no
probe and no scorer. Every check it adds is deterministic and hermetic.

**No re-score of either suite**, for M04's stated reason (⊕): M05 changes no
system the golden set or the probe corpus measures. A number re-recorded here
would have moved for no cause, or not moved and been read as evidence of
something.

**No brand pack for `meridian-news`**, though Act 1's own command asks for one.
See pre-flight finding 7; the cut is recorded and `--brand` is verified against
what exists rather than against what the comment promises.

**No `pave exception`, no drill, no selfheal.** Still stubs, still naming their
milestones.

## The load-bearing decision: what "verified at deploy" can honestly mean here

BUILD.md's row for this milestone reads *"`pave new` + template + manifest
verify at deploy."* Three of those four things have somewhere to land. The
fourth does not, and pretending otherwise is how a claim becomes a promise.

**There is no per-service deploy in this repository.** `make core` is
`cdk deploy --all` over two stacks. `services/highlights-agent/` is a directory
of scripts an operator runs from a laptop; nothing packages it, nothing deploys
it, and ADR-003's *"agents run as Lambda functions"* is a declared migration
target with no implementation. The CDK app reads neither the registry nor any
manifest — `grep readFileSync platform/infra/lib/*.ts` returns nothing.

And the identity the gateway authorizes as is **deployment configuration by
design**, not request data. `handler.py` is explicit, and the cut is already
recorded there:

> The cut this makes: one gateway deployment authorizes as one service, so the
> registry's second caller (`recap-agent`) is unreachable through this stack
> rather than denied by it.

So "deploy a second governed agent" at this scale means "deploy a second gateway
stack" — a second guardrail version against a per-guardrail version cap, a
second audit lake, a second set of functions. That is not a miniature of
anything; it is three times the infrastructure to prove a command.

**The decision: the manifest becomes the deployed stack's configuration, and the
lane that already blocks on template drift is what verifies it.**

Concretely — `SERVICE_PRINCIPAL`, the service's declared classification and its
tool set are read from the verified manifest at synth. A manifest that does not
verify cannot synth. A manifest edited after the snapshot was recorded produces
a different template, and `pave infra snapshot --check` is a required lane that
emits `verdict-infra.json` and blocks. That is `manifest_signature: required`,
made real through a control that exists, rather than a new one nobody re-runs.

**What this buys, said precisely.** The manifest stops being a document and
becomes an input to the artifact that gets deployed. What it does **not** buy:
it does not deploy an agent, and it does not make a second service reachable.
Claim 1's row is corrected in the same PR to cite what exists — *`pave new`:
repo → verified, gated, deploy-bound service* — with the ADR beside it saying
what the missing half costs and what replaces it at scale. A milestone that
quietly renames its own claim to match what it built is the failure this
repository exists to avoid; a milestone that corrects a claim in writing, with
the measurement that forced it, is the repository working.

**This is the decision most likely to be wrong, and it is pre-registered as
such.** If the seat review finds an agent Lambda cheap enough that the claim can
be discharged as written, the claim stays as written and this section is what
got it wrong.

## Pre-flight findings (measured 2026-08-23, before any code)

All measured on `07e8cd1`, `main`, 1795 tests green, in a detached worktree.

### 1. Every manifest check in the repository names one file

```python
MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"
```

— `evals/run_evals.py:59`, `tests/test_contracts.py:24`,
`tests/test_budget_derivation.py:29`. There is no enumerator. A second service
directory is invisible.

Measured: `services/recap-agent/pave.manifest.yaml` written with
`apiVersion: pave/v99`, `service: not-recap-agent` (disagreeing with its own
directory), `template: nonexistent-template@9.9.9`, `brand: acme-corp`,
**`classification: sensitive`** — the level G5 refuses by design —
`runtime: mainframe`, an unregistered tool `exfiltrate-everything@^0`,
`eval_min_cases: 0`, and `attestations: {gate_verdict: not-required}`.

**1795 passed.** Not one check fired. This is ADR-042 decision 2's enumerator
lesson one directory over: *"an entry on disk"* had to be defined before the
completeness assertion could mean anything, and *"a service on disk"* has never
been defined at all.

### 2. `services/highlights-agent-baseline/` has no manifest, and it is the control

The naive enumerator — every directory under `services/` must carry a verified
manifest — is red on the ungoverned baseline the day it lands, and the baseline
is the one service that must **stay** ungoverned. The enumerator needs a
definition, and the control needs to be excluded by name and for a stated
reason, not by a glob that happens to miss it. Recorded here so the check is not
written twice.

### 3. Two tests tell their reader the manifest is two-key. It is on no rule.

`tests/test_budget_derivation.py`, three places:

- module docstring: *"(the ceilings — two-key)"*
- line 124: *"`gates.budgets` is a two-key path; a number that moves there
  without a written derivation is the change this rule exists to make visible"*
- line 150, inside a **failure message** the developer reads when it fires:
  *"this path is two-key for that reason (G9)"*

Measured: `twokey.triggered(["services/highlights-agent/pave.manifest.yaml"])`
returns `[]`. So does the scaffolded path, and so does `templates/agent-tools/`.

This is ADR-035's finding and ADR-037's finding arriving in a third file: a
protection stated in the one place a reader would look for it, and absent. The
G9 reading is direct — `eval_min_cases` is the floor the service team must
clear, `gates.budgets` are the ceilings its cases are scored against, and the
service team writes both, alone. Measured above: `20 → 0`, 1795 green.

The partial mitigation that exists is worth naming precisely so nobody
double-counts it. `test_the_manifest_ceilings_that_moved_are_pinned_too` and
`test_the_suite_percentile_budget_was_not_raised` pin `max_tokens_in`, `max_ms`,
`max_tokens_out` and `p95_ms` **by duplicating the literals in a test file** —
the deliberate duplication `PIN_FLOOR` uses. That covers four numbers in one
service's manifest. It does not cover `eval_min_cases`, it does not cover
`classification`, and it covers no manifest that does not exist yet.

### 4. `pave new` is a stub that exits 0, and the template is one README

Measured: the command above prints two lines and returns 0.
`templates/agent-tools/` contains `README.md` and nothing else.
`template: agent-tools@0.1.0` in the reference manifest names a version that
appears nowhere in the tree — `grep -rn "agent-tools"` returns four hits, three
of them prose.

The comment beside it reads *"only governed templates deploy."* There is no
governed template, and nothing deploys.

### 5. The declared classification is read by nothing, and at runtime it is the caller's claim

`platform/gateway/handler.py:309`:

```python
declared = event.get("classification", "internal")
```

G5's `route(declared, text)` is exact and well-tested, and it raises on an
unknown level rather than defaulting — *"a typo in a manifest must not silently
become the most permissive reading"* (`classify.py`). The manifest it names is
consulted by no code path. The value the router actually applies arrives in the
request, from the caller, with a default.

Changing the manifest to `classification: public` is 1795 green and changes
nothing at runtime, which is the same fact said twice.

### 6. The registry authorizes a service that does not exist — and the cut is recorded

`platform/registry/tools.yaml` lists `callers: [highlights-agent, recap-agent]`
for `catalog-search`, and `platform/gateway/policy/tools.cedar` therefore
carries a deployed `permit(principal == Service::"recap-agent", ...)`.
`recap-agent` has no manifest, no goldens, no owner, no comparator pin and no
eval lane — and it is the exact service Act 1 scaffolds.

**This is not an unrecorded hole**, and the spec says so rather than banking it:
`handler.py`'s `SERVICE_PRINCIPAL` docstring names `recap-agent` and calls it
*"unreachable through this stack rather than denied by it."* What the recorded
cut does not cover is the generator: `pave policy generate` emits a permit for
any string typed into `callers`, and nothing requires that string to resolve to
a service anybody has verified. The registry is Tool Owner + Legal/S&P; the
manifest is nobody's. A permit exists today whose principal no seat ever
declared.

### 7. Act 1's own command names a brand with no pack

`docs/governance/demo-script.md:49` is
`pave new recap-agent --brand meridian-news --classification internal`. The
manifest comment says `brand` *"selects L3 brand pack + judges."* `quality/judge/`
contains `rubric-sports.md`. There is no news rubric and no brand registry; the
only enumeration of the two brands in the repository is an `enum` inside
`tools/catalog-search/schema.in.json`.

### 8. The freshness lane cannot see a manifest digest, because `normalize` erases it

This is the finding that would have made decision 4 a stated-and-absent
protection, and it was found before the code rather than after.

`pave/infra.py` rewrites **every** 64-hex string anywhere in the template to
`<ASSET_HASH>` before comparing:

```python
ASSET_HASH = re.compile(r"\b[0-9a-f]{64}\b")
...
if isinstance(template, str):
    return ASSET_HASH.sub(ASSET_PLACEHOLDER, template)
```

Measured on the committed fixture, hermetically: two templates identical but for
`MANIFEST_SHA256` — one the digest of an honest manifest, one of a weakened one
— normalise **equal**. Drift invisible. A `sha256:` prefix does not help: `\b`
matches at the colon, so the hex is still rewritten and the two still normalise
equal.

Measured on the same tree: the raw synthesized `BeaconpaveGateway.template.json`
contains **six** 64-hex strings, all of them asset digests, at three
`Properties/Code/S3Key` positions and three `Metadata/aws:asset:path` positions
— and `Metadata` is dropped before the rewrite ever runs. The committed
snapshots contain **zero**, because they are stored normalised.

So the blanket rewrite has exactly three legitimate targets, all at one
structural position, and its only other possible effect is to erase a digest
somebody deliberately put in a template. It is narrowed to those positions here,
by the Platform seat, with a test that plants a digest and asserts the drift is
seen.

### 9. A new service gets no L2 lane, and nothing goes absent

`pave evals run services/recap-agent` prints *"no goldens comparator pinned for
'recap-agent'; emitting nothing"* and returns **0**. That is correct behaviour
and deliberately so — an absent verdict blocks in CI. But `quality-gate.yml`
names `services/highlights-agent` as a literal in both the L2 and the L5 step,
so a second service produces no lane, no verdict and no absence. The gate is
per-repository and the claim is per-service.

### 10. The scaffold would need three other seats' keys on its first PR

Measured with `twokey.triggered` over the file list a `pave new` PR produces:

| path | rule |
|---|---|
| `services/<new>/evals/**` | ai-quality |
| `services/<new>/run_probes_via_gateway.py` | security + platform-eng |
| `platform/registry/tools.yaml` | tool-owner + legal-sp |
| `services/<new>/pave.manifest.yaml` | **no rule** |
| `templates/agent-tools/**` | **no rule** |

The two files that describe what the service *is* take no keys; the three that
describe what it may *do* take five seats across three rules. That is the right
direction for the second group and the wrong count for the first, and it is why
the scaffold must print those three edits rather than make them.

### 11. Three recordings come due at this milestone's close

`docs/governance/recordings.json` owes Acts **0**, **1** and **2** to M05, and
`tests/test_demo_recordings.py::test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed`
reads the README progression table — so marking M05's row ✅ with any of them
unrecorded turns the suite red. Act 1 is not recordable until `pave new` runs at
all, which is this milestone. Recorded here as a DoD item rather than discovered
at close.

## Pre-registered predictions

Written before any M05 code. Each says what falsifies it.

| # | prediction | what falsifies it |
|---|---|---|
| 1 | The pre-flight finding 1 tree — a second service declaring `classification: sensitive`, an unregistered tool, a name disagreeing with its directory and `eval_min_cases: 0` — **fails the manifest lane with a named problem per fault**, and passes before the lane exists | it passes after, or reports one problem for four faults — then the verifier enumerates services but not their faults |
| 2 | `services/highlights-agent-baseline/` is **not** red: the control is excluded **by name**, with its reason in the constant, and a test asserts a *different* unmanifested directory under `services/` is red | a glob excludes it, or nothing is red — then the enumerator is decoration |
| 3 | `eval_min_cases: 20 → 0` is red after this milestone, and the message names the platform floor rather than the service's own number | it is green, or the message quotes the value the PR wrote — then the floor is still the PR's number, which is ADR-042 decision 6 one directory over |
| 4 | `classification: internal → public` is red, and `→ sensitive` is red with a different message | either is green, or both give the same message — then G5's level is still unverified, or the verifier cannot tell "wrong" from "refused by design" |
| 5 | Every check in `pave/manifest.py` is **deletable only loudly**: neutering each in turn produces at least one named failure, audited by neutering each in turn and running the full suite | any is silent — this is ADR-042 prediction 7b carried forward as the discipline it has become; it failed for four of ten checks on ADR-042's first implementation |
| 6 | `twokey.triggered` demands keys for `services/*/pave.manifest.yaml` and `templates/`, no path under either drops to fewer keys than today, and the seat-set test is red when a seat is removed | one drops, or the removal is green — then prediction 7 of ADR-042 has failed a fifth time |
| 7 | Rendering `templates/agent-tools/` with the reference service's parameters reproduces the committed reference manifest exactly under normalisation; a one-field edit to either side is red | it does not reproduce, or the edit is green — then Act 1 shows a template that is not the one the reference service came from |
| 8 | A manifest edited after `make snapshot` makes `pave infra snapshot --check` **fail**, with `normalize` narrowed; with today's `normalize` the same edit passes | it passes after — then decision 4 is a stated-and-absent protection and finding 8 caught nothing |
| 9 | `pave gate manifest`'s verdict is in `gate decide`'s `--verdicts` list, and deleting the workflow step makes the gate exit **2** (absent verdict, pages the platform) rather than 0 | it exits 0 — then the lane is a report |
| 10 | `pave new <name>` writes **only** files under `services/<name>/`, prints the registry and comparator edits it did not make, and a test asserts the produced file set is disjoint from every two-key path owned by another seat | it writes one — then the paved road forges keys |
| 11 | A scaffolded service, freshly produced and unmodified, **fails** the manifest lane on its starter golden count and **passes** every other check | it passes wholesale — then the road leads somewhere ungoverned, which is exactly what M04's journal handed forward; it fails on something else — then the scaffold ships broken |
| 12 | No recorded number moves: no entry in `evals/history/` changes, no README progression number moves, `evals/comparators.json` is byte-identical, `pins.json` gains nothing | any moves — then a scaffolding milestone touched the instrument |
| 13 | Zero model calls, and `make check` stays hermetic: `tests/test_hermeticity.py` green, no new dependency | either fails — then G8 paid for a convenience |

Prediction 5 is the one carried from ADR-042 and the one this milestone is most
likely to fail, because it has failed on first implementation every time it has
been measured.

## The cuts, each with its reason and its owner

| cut | reason | owner | ADR |
|---|---|---|---|
| No deployed agent function | One gateway deployment authorizes as one service (`handler.py`); a second governed agent is a second stack, which is three times the infrastructure to prove a command | Platform Engineering | yes — with the scale-up sentence |
| No second committed service | `main` is always green and a scaffolded service is meant to be red until governed; the suite proves the scaffold into `tmp_path` for free | PM | in the same ADR |
| No brand registry; `--brand` verified against the rubric files that exist | A brand pack is L3 content and M07's neighbourhood; inventing one here to satisfy a comment is scope with no claim | AI Quality | in the same ADR |
| Claim 1's proof-artifact wording corrected | The alternative is leaving "deployed agent" beside a milestone that deployed none | PM + Platform Engineering | in the same ADR, with the measurement |

Every one of these ends the way CLAUDE.md requires: *at scale, replace with X;
the interface already matches.*

## Definition of done

- [ ] `SPEC/05` reviewed by four seats, each planting and running in its own
      worktree, with what each draft got wrong recorded in the ADR rather than
      quietly replaced.
- [ ] The ADR is written **before the code**, states zero model calls, and
      carries its own "what draft N got wrong" section.
- [ ] `pave new <name> --brand <b> --classification <c>` produces a service
      directory; a hermetic test scaffolds into `tmp_path` and verifies the
      result.
- [ ] `pave verify --all` enumerates every service on disk by one function, with
      the control excluded by name and with its reason.
- [ ] Every check lives in `pave/manifest.py` and is reachable from the workflow
      step, not only from pytest.
- [ ] `pave gate manifest --out verdict-manifest.json` is a step in
      `quality-gate.yml` and its verdict is in both `gate comment`'s and
      `gate decide`'s lists.
- [ ] `services/*/pave.manifest.yaml` and `templates/` are on two-key rules, the
      seat sets are asserted by a test, and `ROLES.md` gains the rows.
- [ ] `pave/infra.py:normalize` is narrowed to the positions asset hashes
      occupy, with a planted-digest test.
- [ ] `gateway-stack.ts` reads the verified manifest; `make snapshot`
      re-recorded; the IAM assertions still pass and `MODEL_INVOKE_ROLE_PREFIXES`
      still has exactly one entry.
- [ ] **Deletability audited**: every check neutered in turn, each producing at
      least one named failure, with the audit recorded in the journal.
- [ ] A violating-tree test per check, not only an honest-tree assertion. An
      assertion that a check passes proves nothing about the check existing.
- [ ] `make check` green, hermetic, no new dependency, zero model calls.
- [ ] `milestones/M05/README.md`: what I can demo, the delta, **what broke**.
- [ ] Progression row filled; claim 1's row updated to what exists.
- [ ] Acts 0, 1 and 2 recorded — or re-deferred in `recordings.json` with a
      reason over 60 characters, which is what the test requires and what an
      honest deferral looks like.
- [ ] `.claude/skills/close-milestone` worked in order, including step 6b.

## Sequencing

1. Seat review of this spec. Redesign. Repeat until a round comes back clean.
2. The ADR, with what each killed draft got wrong.
3. `pave/manifest.py` + its violating-tree tests. Deletability audit.
4. The two-key rules and the seat-set test — before the checks they protect are
   worth anything.
5. `templates/agent-tools/` and the parity test, against the reference service.
6. `pave new`, against the template.
7. `normalize`'s narrowing, with its planted-digest test.
8. `gateway-stack.ts`, `make snapshot`, the IAM assertions.
9. The gate lane and the workflow step.
10. Seat review **of the code**, planting against the implementation. Repeat.
11. Journal, progression, claim row, recordings, tag.

Steps 7 and 8 are last among the code because they are the only ones touching a
file that requires Security's key and an ADR, and because a synth re-record over
an unverified verifier records the wrong template.

## What M05 must NOT do

- **Must not call a model.** Not for a scaffolded service's smoke test, not for
  a starter golden case, not once.
- **Must not edit a golden case, a comparator, a threshold, a probe or a
  recorded entry.** If the manifest lane and a committed number disagree, the
  number is right and the lane is wrong until an ADR says otherwise.
- **Must not lower `eval_min_cases` to make the scaffolded service verify.**
  That is the exact move the floor exists to make visible, and doing it inside
  the milestone that builds the floor would be this repository's best
  self-parody.
- **Must not let `pave new` write another seat's file.**
- **Must not reformat `data/catalog.json`.** Its raw text is interpolated into
  the judge prompt; whitespace moves `prompt_sha256` and unregisters the
  instrument.
- **Must not mark the progression row ✅ before the recordings are recorded or
  deliberately re-deferred.**

## The demo artifact

`milestones/M05/` carries, all reproducible offline except the recordings:

- **`scaffold-transcript.txt`** — `pave new recap-agent --brand meridian-news
  --classification internal`, timed, and the file list it produced.
- **`manifest-verify-witness.json`** — `pave verify --all` against the
  scaffolded service: red, with one named problem per fault, then green after
  the three edits the scaffold printed. The red half is the artifact; the green
  half is the road.
- **`verdict-manifest.json`** — the lane's own verdict, in the gate's list.
- **The three recordings**, or their re-deferral with its reason.

Act 1's line stays what the demo script already says: *"Compliance stopped being
a phase. It's the shape of the only road."* What changes is that the road exists.

## Why this is a milestone and not a chore PR

Because a scaffold is a claim about what a team cannot remove, and this
repository currently cannot say what that is. The manifest names the
classification, the tools, the ceilings and the case floor — and a service can
delete six of its ten fields, halve its own floor to zero, and declare a
classification the gateway is required to refuse, with 1795 tests green and no
seat's key required.

The command that would have produced that file prints a sentence and exits 0.
Fixing the command without fixing the file it writes would give the paved road a
sign and no surface.

# SPEC/05 — The paved road, and the manifest nothing verifies

**Owning seat:** PM (spec) · Platform Engineering (`pave new`, the template, the
verifier, the lane) · Service Team (the developer who runs one command) · Data
Governance (`classification`, the level vocabulary) · Tool Owner (`tools:`, the
registry, the generator, the tool schemas) · AI Quality (`gates.*`, the case
floor, the headroom band) · Security / Red Team (the keys, and the invariant
holes this milestone walked into)
**Milestone:** M05 · branch `m05-paved-road` · tag `m05` · **four pull requests**

**This is the third draft.** Six seats reviewed draft 1 and all six returned
"draft 2" with thirty-nine blocking findings. The same six reviewed draft 2 and
all six returned "draft 3" with thirty-one more. Two of them **corrected their
own round-1 findings downward**, and one of draft 2's own corrections was itself
wrong. What each draft got wrong is recorded below rather than replaced. Drafts
1 and 2 are preserved at `scratchpad/SPEC-05-draft{1,2}.md`.

The premise has survived three rounds unchallenged: every seat has re-measured
the manifest-key deletion table and confirmed it. What has not survived is
almost every mechanism proposed to fix it. Draft 1 proposed verification at
deploy; draft 2 cut that and proposed a minimal deployment binding; **draft 3
cuts the binding too**, and for the first time the milestone claims only what
was measured to work.

## Why this milestone exists

Claim 1 — *one command → governed service* — is the only claim whose proof
artifact is a command that prints a sentence and exits 0. And
`templates/agent-tools/` — *"the scaffold every service is born from"* — is one
README file saying the contract lives elsewhere.

But the stub is the smaller half. **`pave.manifest.yaml` is a ten-field
declaration that nothing verifies, and six of its ten fields can be deleted
outright with the whole suite green.** Measured on `07e8cd1` and re-measured
independently by five seats:

| deleted key | result |
|---|---|
| `apiVersion`, `template`, `brand`, `owners`, `runtime`, `attestations` | **1795 passed** each |
| `service`, `classification`, `tools` | 1 failed each, all on a missing-key lookup |
| `gates` | 6 failed, four of them `KeyError` |

Changing a value rather than removing it is green everywhere it matters:
`classification: internal → public` (1795), `→ confidential` (1795),
`gates.eval_min_cases: 20 → 0` (1795), `runtime: → mainframe` (1795),
`template: → nonexistent@9.9.9` (1795), dropping a declared tool (1795).

And the field the manifest calls the deploy-time control — `attestations:
{gate_verdict: required, manifest_signature: required}`, commented *"written by
CI, verified at deploy"* — is written by nothing, verified by nothing, and
deletable at **1795 passed**.

**The review found six more of the same shape, four of them live invariant
holes on `main` today.** They are in the pre-flight findings because a milestone
that builds a verifier while standing on them would be the shape it exists to
remove.

## What draft 2 got wrong

- **Build item 5 (`DECLARED_CLASSIFICATION`) is unimplementable as drafted, and
  its cheapest implementation is the failure mode it fixes.** The CDK app has no
  YAML parser — confirmed by `require.resolve` for both `yaml` and `js-yaml`,
  including transitively — so the value comes from a regex. Platform probed
  fifteen legal YAML forms and found five where PyYAML (the verifier) and a
  regex (the stack) disagree. The reachable one is a duplicate key:

  ```
  classification: sensitive
  classification: internal
      PyYAML (the verifier) -> internal      # green
      regex  (the stack)    -> sensitive     # 25/25 allowed, the most permissive declaration
  ```

  That is `classify.py`'s own sentence — *"a typo in a manifest must not
  silently become the most permissive reading"* — defeated by the fix for it.
- **Its cost was under-counted, the same way draft 1 under-counted finding 10.**
  Draft 2 said "two keys." Measured over the file list: `gateway-stack.ts` is
  `("security","ai-quality")` **with `requires_adr=True`**, so the item costs
  **three seats and an ADR**.
- **Prediction 10's rule is inverted.** It guards *declaring above*, which Data
  Governance measured buys an attacker **zero** additional requests, and permits
  *declaring below*, which is the 10/11 finding below.
- **Prediction 12's "red" half is unachievable for G1 by draft 2's own DoD.**
  Putting `MODEL_INVOKE_ROLE_PREFIXES` and the test that pins it on the *same*
  rule means one diff, one attestation set, **1795 passed**. A rule makes it
  key-collecting; only a second assertion elsewhere makes it red.
- **Prediction 12's `policy ⊆ registry` is satisfiable while claim 10 dies.**
  Claim 10 is a *forbid* property. A subset check passes verbatim and reports
  nothing while `publish-highlight` becomes reachable with no approval.
- **Prediction 15's remedy is wrong for two of the nine `m05` literals.** Two of
  them read the live README table, and `milestone_is_closed` **raises by design**
  on an unlisted milestone — so an unclaimable tag is unavailable there. Moving
  them to `m06` re-arms the trap one milestone later.
- **Finding 18 overstates `classify.py`'s exposure, and two seats said so.** It
  is not "a change detector in the next recorded run": any byte moves
  `classify_sha256`, and `test_the_current_instrument_still_describes_this_tree`
  runs on every `make check` — **15–17 red at commit time**, with a remedy that
  is a `quality/adversarial/` edit (Security + ADR). Over-stating an exposure
  leads to over-keying, which is its own harm. Corrected downward.
- **Finding 18's ADV-008 clause is false.** It repeats the schema's own claim
  that the absent skip-approval field *"is what ADV-008 probes"*. Measured:
  ADV-008's `pass_when` is `cedar_denied_or_approval_required_and_logged`, no
  probe inspects a schema, and nothing anywhere asserts the absence. The finding
  is **stronger** than draft 2 states.
- **Finding 6 quotes a number that does not reproduce.** It says removing the
  phantom `recap-agent` grant gives *"1799 passed"*. Measured twice, by two
  seats and again here: **1795**. Removing a caller cannot add four tests. In a
  repo that audits its own numbers this is the defect it exists to prevent.
- **The digest count is stated as six in one place and seven in two others.**
  `m04-A/B/C` carry six digest kinds; `m04-D/E` carry seven. The live instrument
  is `m04-E`, so **seven**.
- **One of the decision-4 cut's three reasons is soft.** *"`node_modules` is
  absent in a fresh worktree while `npm ci` needs the network"* — measured, a
  directory junction is instant and `npm ci --offline` from a warm cache is 14 s
  at exit 0. The re-record loop is the reason that kills it; the other is
  padding, and padding beside a hard reason is how draft 1's agent-Lambda
  decision got reopened.
- **Three of prediction 6's nine paths had no named seats** — the same
  ADR-037-shaped omission draft 2 indicts draft 1 for, on a shorter list.

## What draft 1 got wrong

Carried forward unchanged, because it is the record: *"`sensitive` is the level
G5 refuses by design"* (false — it is the maximally permissive declaration);
*"`classification: public` changes nothing at runtime"* (false — 0/25 served);
*"four ceilings are pinned"* (false — both halves of that duplication are
one-key, so the true count is zero); decision 4 measured not to block;
predictions 10 and 11 falsified by draft 1's own build list; no seat sets named;
`pave/manifest.py` given no rule.

## What M05 builds — in four pull requests

`main` is always green and stacked PRs get zero CI, so each lands independently.

### PR 1 — the keys, and the sentinels

Nothing after this is worth anything without it, and PR 1 touches files PRs 2–4
depend on.

1. **Two-key rules, with seats named** (below), plus a **seat-set test** and a
   **pairwise test**: for every (guard, guarded) pair this milestone creates,
   `seats(guard) ⊇ seats(guarded)`. Draft 2 satisfied that by count and violated
   it by membership — its verifier could rewrite the `classification` check
   without Data Governance and the `tools` check without Tool Owner.
2. **The four invariant holes are closed** (findings 12–15).
3. **The `m05` sentinels are fixed**: seven literals move to `mzz`, one repoints
   to `m06`, and the vacuity guard is **restructured to name no milestone at
   all** — it asserts the parser discriminates (both the closed and open sets
   non-empty), which survives every future close.

### PR 2 — the verifier and the lane

4. **`pave/manifest.py`, holding mechanism only.** Every criterion it applies is
   *imported* from the path that already carries its content owner's key:
   `DECLARABLE_LEVELS` from `classify.py`, the tool set from the registry, the
   case floor and the headroom band from `pave/floors.py`. That is what makes
   `("ai-quality","security","platform-eng")` correct rather than a count. The
   import of `classify` must be **function-scoped** — `evals/adversarial.py`
   records that a module-scope `sys.path.insert` of the gateway directory broke
   hermeticity.
5. **A duplicate-key-rejecting loader**, 17 lines, PyYAML only. Duplicate keys
   make every manifest field ambiguous to a reviewer, and nothing in the repo
   rejects them.
6. **`pave verify` runs from `pave check` as a non-pytest step, and from the
   lane** — not only from a pytest. Measured: `collect_ignore` in
   `tests/conftest.py`, a zero-key file, silently drops **1795 → 1656** collected
   tests with `pave check` printing *"All checks passed!"* at exit 0. `pave check`
   defeats the `addopts` route and fails on `deselected`, but **non-collection is
   neither**, and its only count guard is "zero collected is a failure." A
   **collected-count floor** lands with it.
7. **`pave gate manifest --out verdict-manifest.json`** joins `gate decide`'s
   list. Every malformed input is a named FAIL, never a traceback.
8. **`policy ⊆ registry` AND `registry ⊆ policy`, plus the gated half** — every
   `consequence: publish` tool carries a forbid guarded by `approval_granted` —
   parsed with `cedar.parse`, never `generate()`, refusing to evaluate at all
   against a duplicated registry id.

### PR 3 — the template and the command

9. **`templates/agent-tools/` and manifest-only parity**, normalisation named.
10. **`pave new`, creates-only**: it writes only paths that did not exist, only
    under `services/<name>/`, and edits no existing file.

### PR 4 — the close

11. Journal, progression row, claim-1 footnote, recordings.

## What M05 deliberately does NOT build

**No deploy-time verification, and no deployment binding.** Draft 1's decision 4
and draft 2's build item 5 are both cut. `make core` gains a two-line
`pave verify --all` guard — Python-only, offline, measured to stop
`cdk deploy` — because that restores BUILD.md's third word at this scale for two
lines. **It does not make `manifest_signature` true and must not be sold as
such**, and `Makefile` joins a rule so the two lines do not come off on one key.

*At scale, replace with a signed attestation checked by the deployment pipeline
before it admits an image; the `attestations` block already matches.*

**G5's declared level stays unenforced, and the manifest's comment is
corrected.** `handler.py:309` keeps taking `declared` from the event. What
`pave verify` gives is a *declaration* check, not enforcement, and the spec says
so in those words.

**No agent Lambda** — 43 free lines, but it deploys the service that existed
before `pave new`, and ADR-023 makes a scaffolded service unreachable through
this stack. **No second committed service. No per-service L2/L5 lanes** (M08).
**No model calls. Zero. No re-score of either suite.**

**No transport fix.** `gateway_client.py:125`'s `Viewer plan=…` prefix is what
makes ordinary questions classify `sensitive` (finding 16). Data Governance
priced the fix at **zero moved digests and 1795 passed** — and then found the
same sentence duplicated, byte-identical and unpinned, in
`services/highlights-agent-baseline/run_baseline.py:94`, which is **not** in the
parity test's loop. Changing one silently splits every governed arm from the
`m00b` control: ADR-016's comparability hazard, offline-invisible. So the fix is
out, the duplicate is recorded as a finding, and the ADR carries both
measurements. Data Governance reversed its own round-1 preference on this and
said why.

## The load-bearing decision: verification is a lane and a key

BUILD.md's row reads *"`pave new` + template + manifest verify at deploy."* M05
builds the first two, gates `make core`, and **cuts deploy-time verification**.

The reason is measured, not argued, and it is the same finding twice. Platform
built draft 1's decision 4 and measured the full loop: weaken the manifest →
freshness lane red → run the one command the error prints (`pave infra
snapshot`) → **exit 0, 1795 passed, weakening merged**. The lane compares a
fresh synth against a committed snapshot the same PR re-records. Then draft 2's
smaller binding was measured to disagree with its own verifier on five legal
YAML forms, one of them resolving to the maximally permissive value.

So what makes a manifest hard to weaken is the pair this milestone does build: a
**lane** that reads every manifest on disk and blocks on an absent verdict, and
a **key** that makes the diff collectable. Nothing else measured as a control.

## Seat sets, named

| path | seats | why |
|---|---|---|
| `services/*/pave.manifest.yaml`, `tests/test_budget_derivation.py` | `ai-quality`, `data-governance`, `tool-owner` | one file, three governed field classes: `gates.*` (thresholds, ROLES §2), `classification` (ROLES §5), `tools` (G3). **Not `platform-eng`** — ROLES §1 says it explicitly does not own gate thresholds, and adding the seat that owns the scaffold to the rule guarding what the scaffold writes is G9 read backwards |
| `templates/agent-tools/**` | `platform-eng`, `ai-quality`, `data-governance`, `tool-owner` | the superset of what it renders — a template edit sets the default floor, level and tool set for every service that does not exist yet. This is the milestone's strongest G9 case |
| `pave/manifest.py`, `tests/test_manifest_verify.py` | `ai-quality`, `security`, `platform-eng` | `pave/history.py`'s precedent — **valid only because the module holds mechanism and imports every criterion** |
| `pave/infra.py`, `tests/test_iam_assertions.py` | `security`, `platform-eng`, **ADR** | G1's allowlist and the assertions defending it |
| `platform/gateway/core/cedar.py`, `tests/test_cedar_policy.py`, `tools/*/schema.(in\|out).json` | `platform-eng`, `security`, `tool-owner` | the generator's own docstring names Platform Engineering (mechanism) and Tool Owner (the policies); Security holds G3. **Not `legal-sp`** — it is on the registry rule because consequence classes are a legal judgement, and nothing in the generator is one |
| `services/*/gateway_client.py` | `security`, `platform-eng` | joins the rule that already names `run_probes_via_gateway.py` (finding 20) |
| `Makefile` | `platform-eng` | it now carries the `make core` guard |
| `pave/gate.py` | `ai-quality`, `platform-eng` | the decider, on zero keys today, and not in draft 2's list |

Every seat string is asserted to be one of ROLES.md's seven — nothing checks
that today, and a typo'd seat is an unsatisfiable rule with no diagnostic.

## Pre-flight findings (measured 2026-08-23)

Findings 1–11 are draft 1's, corrected where the review refuted them. 12–20 are
the review's. All on `07e8cd1`, 1795 green.

**1. Every manifest check names one file.** Three hard-coded `MANIFEST`
constants, no enumerator. The rogue second manifest — `classification: sensitive`,
unregistered tool, name disagreeing with its directory, `eval_min_cases: 0` —
is **1795 passed**. Confirmed by five seats.

**2. The control has no manifest, so the enumerator is directory-driven**, with
the control excluded **by name**, its reason in the constant, and **the exclusion
set pinned by a test** — `MODEL_INVOKE_ROLE_PREFIXES`'s precedent. A
manifest-file-driven enumerator misses `pave.manifest.yml` and a nested manifest.

**3. Three tests tell their reader the manifest is two-key. It is on no rule —
and neither is the pin.** All four ceilings **and** their four pins moved in one
diff: **1795 passed, two-key NOT REQUIRED**. Deleting both pinning tests:
**1793 passed, zero failures**. Tightening is caught relationally; loosening —
the only direction G9 exists for — is caught solely by the deletable literal.

**4. `pave new` is a stub that exits 0**, `templates/agent-tools/` is one README,
`template: agent-tools@0.1.0` names a version that exists nowhere, and the stub's
own text advertises writing **CODEOWNERS**. `pave new "../../platform"
--classification sensitive` exits 0.

**5. The declared classification is the caller's claim, and `public` is an
outage.** Over all 25 goldens in wire form: `public` **0/25**, `internal` 25/25,
`confidential` 25/25, `sensitive` 25/25. `test_manifest_classification_is_not_sensitive`
refuses the no-op and accepts the outage. G5 holds by the *detected* level, never
the declared one.

**6. The registry authorizes a service that does not exist.** `recap-agent` — the
name Act 1 scaffolds — has a live Cedar permit and no manifest. **Removing it is
1795 passed with zero tests depending on it** (draft 2's "1799" was wrong).

**7. Act 1's own command names a brand with no pack**, and appending one
`meridian-news` catalog title turns **16 tests red** with a message naming no
file and a remedy that needs model calls.

**8. `normalize` erases a 64-hex digest, and the digest was the wrong idea.**
Uppercase hex survives untouched; plain strings survive and read themselves in a
diff; a 64-hex *service name* is accepted by `cedar.IDENTIFIER`. The verifier
bounds `service:` so it cannot take an asset-hash shape.

**9. A new service gets no L2 lane, and nothing goes absent.** Recorded as a cut
with an owner: per-service lanes are M08's. M05 must not let a reader believe the
twenty cases it requires are scored.

**10. The onboarding PR cost, measured across drafts.** Draft 1: 5 rules / 5
seats. Draft 2: 3 rules / 4 seats at PR #1, **2 seats** at a steady-state PR, and
**0 seats** for an ordinary code change to a team's own service. That last number
is the one that decides whether teams stay on the road.

**11. Three recordings come due at this milestone's close.**

**12. `m05` is a "never happened" sentinel in nine places, and it is about to
happen.** `milestones/M05/` → `FileExistsError` in a three-key file; the ✅ row →
two failures including `assert True is False`. ADR-041's F2 one level out.

**13. G1's allowlist and every assertion defending it merge on zero keys.**
Widening `MODEL_INVOKE_ROLE_PREFIXES` and relaxing its own pin in one diff →
**1795 passed, two-key NOT REQUIRED** — against two prose statements that this
needs the Security seat and an ADR. **And CLAUDE.md:26's pointer is wrong**:
`platform/infra/tests/` holds three fixtures and a README, no test.

**14. G3: a Cedar permit for a principal no registry entry names, on zero keys.**
`permit(principal == Service::"attacker-svc", …)` reaches the deployed policy set;
`pave policy generate --check` exits **0**; 1795 passed; the two-key registry
untouched. The drift gate is `generate(REGISTRY) == COMMITTED`, both sides
calling the same function.

**15. Claim 10 dies on three zero-key files and `pave check` prints "All checks
passed!"** — a `cedar.py` condition dropping the publish-class forbid, a
`collect_ignore` line, and a regenerated policy set. `publish-highlight` reachable
with no approval, **exit 0**. Independently: `collect_ignore` alone drops
**1795 → 1656** collected tests, unremarked.

**16. The transport supplies the subject half of a personal-data classification
on every request.** *"What is the name of the anchor presenting the late
edition?"* → `internal` bare, **`sensitive` refused** in wire form. On a realistic
20-case `meridian-news` pack: **4 of 20 refused** while `pave verify` says PASS.
`quality/judge/frozen.json` records this hazard verbatim for the judge, which got
an instrument-B fix; the transport never did.

**17. A zero-key tool-schema edit reaches the deployed contract set.** Deleting
`ai_generated` — the MER-AI-0001 disclosure flag — and adding `skip_approval` to
`tools/publish-highlight/schema.in.json`: `policy generate --check` **exit 0**,
suite green, two-key not required. **And the schema's own claim that this absence
"is what ADV-008 probes" is false** — no probe inspects a schema.

**18. `classify.py` is transitively three-key protected, and draft 2 said
otherwise.** Any byte moves `classify_sha256` → **15–17 red on every `make
check`**, remedy is a Security + ADR registration. Cutting its rule is right.
`tests/test_no_account_identifiers.py` is on no rule and enumerates by
`git ls-files`, so a scaffolded service is invisible to it until `git add` — a
second enumerator disagreeing with the one M05 builds, in the safe direction.

**19. Corpus growth is a ratchet in eight places, not one.** One appended golden
case → 8 failures; relaxing the `== 25` equality still leaves seven, the real one
being the comparator's own count.

**20. `gateway_client.py` composes every observation's wire text, is in no digest
and on no rule.** `run_probes_via_gateway.py` is two-key **and** half of
`capture_sha256`; it does `import gateway_client as gw`. Rewording the prefix
changes what every observation means and moves **zero** digests. Draft 2 excludes
the digested caller from the template and ships the undigested callee into every
future service.

**21. A misdeclared service scores 10/11 on the adversarial suite.** Measured
through `evals.adversarial.score_probe`: `declared=public` denies **11/11**
probes with `mechanism: classification`, which is in `POLICY_MECHANISMS`, so
`policy_denied` is true and every record resolves. Ten of eleven probes ask only
for *blocked-or-denied-and-logged*. **A service that answers nothing scores
10/11, against a best recorded arm of 7/10.** Live today; no committed arm hits
it because every arm declares `internal`.

This is ADR-038's shape one level out — that ADR stopped crediting *a block that
names no control*; this is *a denial that names no attack*. **It is not M05's to
fix.** It is a G4 semantics question owned by Security, recorded here with the
measurement and handed over, because the alternative is that it is found a
fourth time by someone reading a flattering number.

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | The finding-1 tree fails the lane with one named problem per fault, each naming value, expected set, owning seat and next command | it passes, or any message omits a remedy |
| 2 | The enumerator is directory-driven: `.yml`, nested, a manifest that is a *directory*, and a plain unmanifested directory are each red; the control is excluded by name and **the exclusion set is pinned** | any is missed, or the exclusion set extends with the suite green |
| 3 | `eval_min_cases: 20 → 0` is red naming the platform floor and its seat; the floor is in `pave/floors.py`; lowering it below `smallest_pack_that_can_hold_headroom()` is red; **and the band it derives from has exactly one definition, in `pave/floors.py`, imported by `tests/test_contracts.py` rather than duplicated** | the floor is lowerable to any value ≥ 1 with the suite green, **or the band moves in a file the floor's seats do not hold** — a three-key floor with a one-key denominator is finding 3 reproduced inside its own fix |
| 4 | **Four** distinct messages: `public` names the measured 0/25 outage; `sensitive` names that it is the most permissive declaration; `confidential` is **refused** naming a level no control applies; an unknown or mis-cased level is refused naming `DECLARABLE_LEVELS` | any two share a message, or `confidential` is accepted — accepting it puts a level in the file every seat reviews that no code applies, which is the shape this milestone exists to remove |
| 5 | Every check and every threshold literal is deletable only loudly, audited by neutering each in turn — **and the audit's stated residual is that a deleted test file is invisible to pytest**, owned by its rule and not by another check | any is silent, or the residual is left unstated |
| 6 | Every path in the seat table carries its named seats; no path drops below today's keys; the seat-set test is red when any seat is removed; **and the pairwise test asserts `seats(guard) ⊇ seats(guarded)` for every pair this milestone creates** | one drops, or a pair is disjoint — draft 2 satisfied the property by count and violated it by membership |
| 7 | Parity covers `pave.manifest.yaml` only, under a named normalisation that does **not** erase `gates.budgets`; `run_probes_via_gateway.py` and `gateway_client.py` are not rendered for the reference service; the **seven** live digests are unchanged | parity reaches a digest input, any `*_sha256` moves, or the normalisation erases the four ceilings this milestone puts keys on |
| 8 | `pave new` creates files and edits none; `../../platform`, `a/b`, `.`, an absolute path, an existing service name and `highlights-agent-baseline` are refused | any is written |
| 9 | The lane's verdict is in `gate decide`'s list; **and the checks are reachable from `pave check` as a non-pytest step**, so `collect_ignore` in `tests/conftest.py` changes nothing about the result; a collected-count floor is red at 1656 | a `conftest.py` line makes the lane green, or the count drop is unremarked |
| 10 | All nine malformed manifests plus a duplicate key, an anchor bomb, a NUL byte, UTF-16-with-BOM and a `!!python/object/apply` tag produce named FAIL notes, zero tracebacks, verdict written, exit 1 | any raises, or the duplicate key is accepted |
| 11 | A scaffolded service fails on exactly the faults the spec names, and **no case in any verified pack classifies `sensitive` in wire form** — over the twenty the team writes, not the three the scaffold ships | it fails on something else, or the check is scoped to the starter pack — draft 2's version measured 4 of 20 green |
| 12 | The G3 hole closes: `policy ⊆ registry` **and** `registry ⊆ policy` **and** every gated tool carries a forbid guarded by `approval_granted`, parsed rather than generated, refusing to evaluate against a duplicated registry id; the G1 hole becomes **key-collecting**, and the word "red" is dropped because a self-pinning constant cannot be made red by a rule | a subset-only check reports clean while the interlock dies, or the duplicate-id path reports clean |
| 13 | No recorded number moves: no history entry, `pins.json` gains nothing, no README bold `n/m` row moves. **The comparator's byte-identity is a DoD command, not a prediction** — nothing pins it | any moves |
| 14 | Zero model calls; hermetic; no new dependency (semver is stdlib — but it is **three** caret rules, not one: `^0`, `^0.1` and `^0.1.0` have different upper bounds and the repo's own manifest uses the loosest) | any fails |
| 15 | The sentinels are fixed: seven literals move, **one repoints to `m06` because it needs a tag with a README row**, and the vacuity guard is restructured to name no milestone — red against a parser that always says True and against one that always says False | a moved sentinel is red, or the guard still names a milestone that will close |

Prediction 5 is ADR-042's discipline, which has failed on first implementation
every time it has been measured. Prediction 12 is the one that says a milestone
about verifying declarations did not ship standing on live invariant holes.

## The cuts

| cut | reason | owner |
|---|---|---|
| **Deploy-time verification** | Measured: the freshness lane compares synth to a snapshot the same PR re-records. *At scale, a signed attestation checked by the deployment pipeline; the `attestations` block already matches* | Platform Eng |
| **The deployment binding** (`DECLARED_CLASSIFICATION`) | No YAML parser in the CDK app; a regex disagrees with the verifier on five legal forms, one resolving to the most permissive value; the snapshot-literal alternative drags Node onto the road for every classification change; three seats and an ADR | Platform Eng + Data Governance |
| **`manifest_signature` stays unbuilt, and the comment is corrected** | Leaving *"verified at deploy"* beside a field nothing writes is this milestone's own premise | Platform Eng |
| **No agent Lambda** | 43 free lines, but it deploys the service that existed before `pave new` (ADR-023) | Platform Eng |
| **No transport fix** | Free at the suite and digest level; expensive at the measurement level — the prefix is duplicated unpinned in the ungoverned control and changing one splits every governed arm from `m00b` | Data Governance + AI Quality |
| **The 10/11 universal-denial gap** (finding 21) | A G4 semantics question, not a scaffolding one. Recorded with the measurement and handed to Security | Security |
| **No second committed service; no per-service lanes; no brand registry** | as drafts 1–2 | PM / AI Quality |
| **No `pave exception`** — and the route is a **global floor move**, not an exception | The honest statement: an ADR cannot make `pave verify` green; the only reachable move is lowering `PLATFORM_EVAL_MIN_CASES`, which is permanent, global, and not what `ROLES.md` describes. AI Quality must know that is what it is being asked to sign | Service Team + AI Quality |
| **No PII/test-data guard**, but the starter pack **declares its provenance** | `tests/test_calibration_corpus.py` has the exact precedent — a provenance block that says `human` about generated content makes a number look like something it is not. Measured: relabelling all 25 committed cases is 1795 green | Data Governance + AI Quality |

## Definition of done

- [ ] Draft 3 reviewed; what each draft got wrong recorded in the ADR.
- [ ] The ADR written before the code, zero model calls, with the nine cut rows.
- [ ] **PR 1**: rules with named seats; seat-set test; **pairwise test**; seat
      vocabulary asserted against ROLES.md; findings 12–15 and 17, 20 closed;
      CLAUDE.md:26's pointer corrected.
- [ ] **PR 2**: `pave/manifest.py` (mechanism only, every criterion imported);
      duplicate-key loader; `pave verify` reachable from `pave check` as a
      non-pytest step; collected-count floor; the lane; both policy directions
      plus the gated half.
- [ ] **PR 3**: template, manifest-only parity, `pave new` creates-only.
- [ ] **PR 4**: journal, progression, claim-1 footnote (**INCOMPLETE, wording
      not edited** — the proof-artifact column is the claim's falsifier and
      `README.md` is on no rule), recordings.
- [ ] `recap-agent` removed from the registry; the reference manifest declares
      `publish-highlight@^0` with its approver (the alternative strands the
      repo's only publish-class caller and deletes claim 10's live exercise).
- [ ] Deletability audited across checks **and threshold literals**.
- [ ] `make check` green, hermetic, no new dependency, zero model calls.
- [ ] `git diff --name-only <base>..HEAD -- evals/comparators.json evals/history/`
      is **empty**.
- [ ] Acts 0, 1 and 2 recorded or re-deferred with a reason over 60 characters.
- [ ] `close-milestone` worked in order, with a **"this milestone records
      nothing"** branch for step 2. Step 6b's census half **runs and is clean** —
      `topic_baseline.py --all --k 3` reports 6/6 met, `enforcement-probing`'s
      trigger not met at 0 of 25 on guardrail v4 — and the journal says which
      close steps are offline and which are not.

## What M05 must NOT do

Call a model. Edit a golden case, comparator, threshold, probe or recorded entry,
or touch any input to the **seven** instrument digests — which rules both
`run_probes_via_gateway.py` and `classify.py` out of scope. Lower
`eval_min_cases` to make the scaffold verify. Let `pave new` edit an existing
file. Reformat `data/catalog.json`. Reword claim 1's proof artifact. Mark the
progression row ✅ before the recordings are settled.

## The demo artifact

`milestones/M05/` — `scaffold-transcript.txt` (timed); `manifest-verify-witness.json`
(red with one named problem per fault, then green after the two hand edits a
developer can make with no credentials and no model call — the golden pack and
the registry `callers` entry, the latter now real because `recap-agent`'s phantom
grant is gone); `verdict-manifest.json`; `invariant-holes.md` carrying findings
12–15, 17, 20 and 21 as measured, with the diffs that closed the first six and
the handoff for the last; and the three recordings or their re-deferral. Act 1's
script says *"the manifest verification at deploy"* is what a developer cannot
remove — the script is corrected in the same PR to match what was built.

## Why this is a milestone and not a chore PR

A scaffold is a claim about what a team cannot remove, and this repository cannot
currently say what that is. A service can delete six of its ten manifest fields,
halve its own case floor to zero, and declare a classification that either does
nothing or takes it down completely, with 1795 tests green and no seat's key.

And because three rounds of six seats found that the file describing what a
service *is* takes no keys; the module that would judge it takes none; the
allowlist naming the one role permitted to reach a model takes none; the
generator producing the deployed authorization policy takes none; the tool schema
carrying a regulated disclosure flag takes none; one line in a zero-key
`conftest.py` removes 139 tests while the gate prints "All checks passed!"; and a
service configured to answer nothing scores better on the compliance suite than
any system this repo has ever built.

The command that would have produced the manifest prints a sentence and exits 0.
Fixing the command without fixing the file it writes would give the paved road a
sign and no surface.

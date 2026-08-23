# SPEC/05 — The paved road, and the manifest nothing verifies

**Owning seat:** PM (spec) · Platform Engineering (`pave new`, the template, the
verifier, the lane) · Service Team (the developer who runs one command and lives
with what it produced) · Data Governance (`classification`) · Tool Owner
(`tools:`, the registry, the generator) · AI Quality (`gates.*` — the ceilings
and the case floor are gate criteria) · Security / Red Team (the keys, and the
two live invariant holes this milestone walked into)
**Milestone:** M05 · branch `m05-paved-road` · tag `m05`

**This is the second draft.** Draft 1 was reviewed by six seats, each planting
and running in its own worktree, and **all six returned "draft 2"** with
thirty-nine blocking findings between them. Three of draft 1's statements of
fact were measured false, all three in the direction that flattered the
platform; two of its thirteen predictions were falsified by its own build list
before a line of code existed; and its load-bearing decision was built by the
Platform seat and measured not to block the thing it existed to block. What
draft 1 got wrong is recorded in its own section below rather than quietly
replaced. Draft 1 is preserved at
`scratchpad/SPEC-05-draft1.md` and its text is quoted where it was wrong.

The premise survived. Every seat re-measured the manifest-key deletion table and
confirmed it. What did not survive is draft 1's account of what already protects
the manifest, what verification would buy, and where the checks may live.

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
the full suite — **and re-measured independently by four of the six seats**:

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
- `classification: internal` → `confidential`: **1795 passed.** (Draft 1 did not
  test this one; the Platform seat added it.)
- `gates.eval_min_cases: 20` → `0`: **1795 passed.**
- `runtime: lambda` → `mainframe`, `template:` → `nonexistent@9.9.9`: **1795
  passed** each.
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
because it stops anyone looking for the real one.

**The six-seat review found five more of the same shape, three of them live
invariant holes, and two of those three are on `main` today.** They are in the
pre-flight findings below because a milestone that builds a verifier while
standing on them would be the shape it exists to remove.

## What draft 1 got wrong

Recorded here rather than silently corrected, because a spec that reads as
though it had always been right is worth less than one that shows where it was
corrected (ADR README).

- **"`classification: sensitive` — the level G5 refuses by design."** Stated
  three times. **False.** `route()` refuses on the level it *detects*, never on
  the level a service *declares* (`classify.py:124`). Measured over all 25
  golden cases in wire form: `declared=sensitive` → **25/25 allowed**.
  Declaring `sensitive` is the *maximally permissive* declaration. Found by
  Data Governance and the Platform seat independently; the manifest's own
  comment (`# G5 routing; sensitive is refused by design`) is wrong the same
  way and is corrected in this milestone.
- **"Changing the manifest to `classification: public` … changes nothing at
  runtime, which is the same fact said twice."** **False, and dangerous.**
  `public` is the *only* declared value that reaches `route()`'s escalation
  branch, and it denies every golden case: **0/25 allowed**. The one value the
  existing contract test refuses is a behavioural no-op; one of the three it
  accepts is a total outage. The check draft 1 proposed to lift into the
  verifier and put two keys on **is inverted**.
- **"`test_the_manifest_ceilings_that_moved_are_pinned_too` … pins four numbers
  — the deliberate duplication `PIN_FLOOR` uses."** **False.** `PIN_FLOOR` lives
  in `tests/test_instrument_stability.py`, which **is** on the three-key rule.
  `tests/test_budget_derivation.py` is on **no rule**. Both halves of the
  duplication are one-key, so the duplication buys nothing. Measured by AI
  Quality and re-measured here: all four ceilings **and** their four pins moved
  in one diff → **1795 passed, two-key NOT REQUIRED**. Draft 1 credited four
  protected numbers; the true count is zero.
- **Decision 4 did not do what it said.** The Platform seat *built it* — manifest
  read at synth, digest in the template, `normalize` narrowed — and measured that
  a developer weakening `eval_min_cases` to 0 gets a red freshness lane, runs the
  one command the error message tells them to run (`pave infra snapshot`), and
  is green at 1795 with the weakening merged. The freshness lane compares synth
  against a committed file the same PR re-records. **It has never been a manifest
  control and cannot become one by carrying a manifest's digest.**
- **Prediction 10 contradicted build item 1.** The scaffold cannot both write a
  starter golden pack and produce a file set disjoint from other seats' two-key
  paths: `services/<new>/evals/**` is ai-quality's rule. Found by Service Team
  and AI Quality independently.
- **Prediction 11 was refuted three separate ways** before any code: the
  headroom band is unsatisfiable below ten cases (AI Quality), the `Viewer`
  transport prefix makes ordinary starter questions classify `sensitive` (Data
  Governance), and the **reference** manifest already fails the verifier draft 1
  proposed (Tool Owner).
- **It named no seat sets.** The DoD said the paths go on rules and a test
  asserts the seat sets, and the document never said which seats. That is
  ADR-037's finding with the list left blank, and five seats named it.
- **It put every check in `pave/manifest.py` and gave that module no rule** —
  ADR-042 prediction 7 failing a fifth time, inside the spec that quotes it.
  Named by five of six seats.
- **Its cut table had four rows and none was the one the measurements
  required.** `pave exception` was cut in a sentence, outside the table, in the
  milestone that builds the first floor a team can legitimately fail on day one.
- **Its agent-Lambda reasoning was wrong and its conclusion was right.** The
  Platform seat priced it: 17 lines of `gateway-stack.ts`, a 26-line handler, a
  38-line snapshot delta, **1795 passed**, zero new IAM, nothing that bills at
  idle. Draft 1's stated reason — "a second stack, three times the
  infrastructure" — answers a different question. The cut stands for a different
  reason, below.

## What M05 builds

1. **`pave new <name> --brand <b> --classification <c>` — a real scaffold that
   creates files and never edits one.** It renders `templates/agent-tools/` into
   `services/<name>/` — manifest, starter golden pack, answer schema, gateway
   client, service README — and **refuses to modify any file that already
   exists.** The registry entry, the CODEOWNERS block and the comparator pin are
   *printed*, with the seats each will need.

   This replaces draft 1's rule, which was unimplementable. The danger was never
   key-forging — `twokey.triggered` keys on the path, so a scaffolded
   `services/<new>/evals/` still collects ai-quality's key whoever wrote it. The
   danger is a scaffold reaching into shared, global, other-seat files where a
   bug corrupts grants that belong to services it has never heard of. So:
   **creates-only, under `services/<name>/` only.**

2. **`pave/manifest.py` — the verifier, on `("ai-quality", "security",
   "platform-eng")`.** The same three seats as `pave/history.py`, for the same
   reason, stated by five seats: the module deciding what "verified" means may
   not take fewer keys than the declarations it judges. Its violating-tree test
   file joins the enumerated `tests/(…)` rule.

3. **`pave verify [<service>|--all]` and the `manifest` gate lane.**
   `pave gate manifest --out verdict-manifest.json` joins the `--verdicts` list.
   **Every malformed input is a named FAIL, never a traceback** — the Platform
   seat measured 8 of 9 malformed manifests raising out of the smallest honest
   implementation, which is ADR-042's six-tracebacks finding arriving a second
   time in a module written after it.

4. **The platform floor lives in `pave/floors.py`, and its own floor is
   derived.** `pave/floors.py` already takes three keys and its docstring
   already draws this line. `eval_min_cases` is bounded by
   `PLATFORM_EVAL_MIN_CASES`, and the constant is ratcheted by
   `smallest_pack_that_can_hold_headroom()` — because
   `test_golden_set_keeps_headroom` requires `0.05 <= near/n <= 0.10` with
   `near >= 1`, which **no pack under ten cases can satisfy**. Measured: a floor
   of 19 or 10 is silent (a policy choice), 9 and below is red. That answers the
   question draft 1 could not: a platform floor of `1` satisfied draft 1's
   prediction 3 verbatim.

5. **G5's declared level becomes enforceable, minimally.** `gateway-stack.ts`
   emits `DECLARED_CLASSIFICATION` from the manifest; `handler.py` reads it
   without a default, exactly as it reads `SERVICE_PRINCIPAL` and
   `GUARDRAIL_VERSION`, and a request may not declare above it. **No digest, no
   `normalize` narrowing, no synth-time subprocess** — the Platform seat measured
   that a plain level string survives today's `normalize` unchanged and reads
   itself in a snapshot diff, where a 64-hex digest is erased and, once
   un-erased, is an opaque delta a reviewer cannot read. Costs two keys
   (`handler.py` is already `platform-eng + security`) and **moves no instrument
   digest** — `handler.py` is in none of the six.

6. **Two live invariant holes this milestone discovered are closed here.** Both
   are stated-and-absent, both are on `main`, and both sit on paths M05 touches:

   - **G1.** `pave/infra.py`'s `MODEL_INVOKE_ROLE_PREFIXES` — whose own comment
     says adding an entry *"needs an ADR and the Security seat rather than a
     commit"* — and `tests/test_iam_assertions.py`, whose failure message says
     *"Adding another is a G1 exception (Security seat + ADR), not a test fix"*,
     are both on **no rule**. Measured: widening the allowlist and relaxing its
     own pin in one diff → **1795 passed, two-key NOT REQUIRED**.
   - **G3.** `platform/gateway/core/cedar.py` — the generator — is on no rule,
     and the drift gate is `generate(REGISTRY) == COMMITTED`, both sides calling
     the same function. Measured: a `permit(principal == Service::"attacker-svc",
     …)` reaches the deployed policy set, `pave policy generate --check` exits
     **0**, **1795 passed**, two-key **NOT REQUIRED**, and the two-key registry
     is never touched.

7. **Scaffold parity, scoped to the manifest only**, with the normalisation
   named. The template rendered with the reference service's parameters must
   reproduce `services/highlights-agent/pave.manifest.yaml`. It does **not**
   cover `run_probes_via_gateway.py`: that file is half of `capture_sha256`, and
   the Platform and Security seats each measured that touching it de-registers
   instrument `m04-E` and turns 15 tests red — which this milestone forbids.

8. **The three recordings owed by this milestone** — Acts 0, 1 and 2 — or a
   deliberate re-deferral in `docs/governance/recordings.json`.

## What M05 deliberately does NOT build

**No deploy-time verification. The whole of draft 1's decision 4 is cut**, and
this is the largest change between drafts. The Platform seat built it and
measured its protection value at *"the manifest's content becomes visible in the
reviewed diff of a re-recorded snapshot"* — a review aid, not a gate. The
blocking controls are the lane and the keys. Two further costs it would have
carried, both measured: `cdk synth` would need either a Python subprocess
(coupling the TypeScript build to the Python package) or a YAML parser (the CDK
app has **none** in its dependencies, so a new dependency and an ADR line); and
`node_modules` is absent in a fresh worktree while `npm ci` needs the network,
so every manifest edit would move a service-team file onto a road needing Node,
npm, the network and Python. `make check` stays hermetic either way, so G8 was
never at risk — the cost is the road.

*At scale, replace with a signed attestation checked by the deployment pipeline
before it admits an image; the `attestations` block already matches.*

**No second committed service.** The scaffold is exercised into `tmp_path` and
into a scratch directory for the recording.

**No agent Lambda — and the reason is not the one draft 1 gave.** It is 43 free
lines and bills nothing at idle. It is cut because **it would deploy the service
that existed before `pave new`, and claim 1 is about the service `pave new`
scaffolds.** `handler.py`'s recorded cut (ADR-023) makes a scaffolded service
*"unreachable through this stack rather than denied by it"*, so deploying
`highlights-agent` proves nothing about the road. *At scale, a gateway
deployment per service or a caller identity the platform verifies rather than
receives; the interface already matches.*

**No model calls. Zero.** No re-score of either suite, for M04's stated reason
(⊕).

**No brand pack for `meridian-news`.** `--brand` is verified against the rubric
files that exist. Recorded in the cuts table with its owner.

**No `pave exception`** — now in the cuts table, with what a blocked team does
instead.

## The load-bearing decision: verification is a lane and a key, not a deploy

BUILD.md's row reads *"`pave new` + template + manifest verify at deploy."*
M05 builds the first two and **cuts the third, in writing.**

The reason is measured rather than argued. There is no per-service deploy:
`make core` is `cdk deploy --all` from a laptop, which runs no gate, collects no
key and opens no PR. The one deploy-adjacent control that blocks — the synth
freshness lane — compares a fresh synth against a committed snapshot **that the
same pull request re-records**, and the Platform seat measured the full loop
with decision 4 implemented: weaken the manifest → lane red → run the remedy the
error prints → **exit 0, 1795 passed, weakening merged**.

So what actually makes a manifest hard to weaken is the pair this milestone
does build: a **lane** that reads every manifest on disk and blocks on an absent
verdict, and a **key** that makes the diff collectable. Draft 1 credited the
freshness lane with work only those two do. This draft says so, and the honest
sentence goes in the ADR rather than in a footnote.

**What this costs, stated:** `attestations.manifest_signature: required` stays
unimplemented after this milestone. Rather than leave a comment claiming
otherwise — the shape this milestone exists to remove — the manifest's own
comment is corrected to say the field is declared and unbuilt, and the ADR
carries the scale-up sentence.

## Pre-flight findings (measured 2026-08-23, before any code)

All on `07e8cd1`, `main`, 1795 green. Findings 1–11 are draft 1's, corrected
where the seats refuted them. Findings 12–20 are the review's.

### 1. Every manifest check in the repository names one file

`MANIFEST = ROOT / "services" / "highlights-agent" / "pave.manifest.yaml"` —
`evals/run_evals.py:59`, `tests/test_contracts.py:24`,
`tests/test_budget_derivation.py:29`. Exactly three readers, all hard-coded, no
enumerator. Confirmed by four seats.

A planted `services/recap-agent/pave.manifest.yaml` with `apiVersion: pave/v99`,
`service: not-recap-agent`, `template: nonexistent-template@9.9.9`,
`brand: acme-corp`, `classification: sensitive`, `runtime: mainframe`, an
unregistered tool, `eval_min_cases: 0` and `attestations: not-required`:
**1795 passed.** Not one check fired.

### 2. The control has no manifest, and the enumerator must be directory-driven

`services/highlights-agent-baseline/` carries no manifest and must stay
ungoverned. The Platform seat measured that a manifest-file-driven enumerator
cannot see `services/x/pave.manifest.yml` (one letter) or
`services/x/inner/pave.manifest.yaml`, and that a directory-driven one sees
both. **A service is a directory under `services/`**, with the control excluded
**by name**, its reason in the constant, and — new in this draft — **the
exclusion set pinned by a test**, on `MODEL_INVOKE_ROLE_PREFIXES`'s precedent.
An unpinned exclusion constant in a zero-key module is one line from making any
service invisible to the lane forever.

A directory-driven enumerator also closes the rename bypass: a service whose
manifest is renamed away is red for having no manifest, rather than merely
invisible.

### 3. Three tests tell their reader the manifest is two-key. It is on no rule — and neither is the pin.

`tests/test_budget_derivation.py` says it in its docstring, at line 124, and at
line 150 **inside a failure message**: *"this path is two-key for that reason
(G9)."*

`twokey.triggered(["services/highlights-agent/pave.manifest.yaml"])` → `[]`.
So does `templates/agent-tools/`. **And so does `tests/test_budget_derivation.py`
itself** — which is the half draft 1 got wrong. Measured by AI Quality:

```
p95_ms 2500→9999, max_ms 12000→99000, max_tokens_in 6500→65000,
max_tokens_out 800→8000, and the four matching test literals, one diff
  → 1795 passed;  two-key: NOT REQUIRED
```

Deleting both pinning tests outright: **1793 passed, zero failures.** The
duplication draft 1 called `PIN_FLOOR`'s is not `PIN_FLOOR`'s: that constant
sits in `tests/test_instrument_stability.py`, which is on the three-key rule.
Here both halves are one-key.

The asymmetry is the tell. *Tightening* a ceiling is caught relationally
(`test_budgets_stay_within_the_service_manifest` — per-case budgets must sit
under the manifest's). *Loosening* — the only direction G9 exists for — is
caught solely by the deletable literal.

### 4. `pave new` is a stub that exits 0, the template is one README, and the stub advertises the forbidden behaviour

`templates/agent-tools/` contains `README.md` and nothing else.
`template: agent-tools@0.1.0` names a version that appears nowhere.

And the stub's own text says it would write **CODEOWNERS** — another seat's
file. The Security seat measured that it also accepts
`pave new "../../platform" --classification sensitive` and exits 0. The string
is deleted in the same PR so no implementer follows it.

### 5. The declared classification is the caller's claim — and `public` is an outage

`platform/gateway/handler.py:309` is `declared = event.get("classification",
"internal")`. The manifest is consulted by no runtime path.

**Draft 1 stopped here and drew the wrong conclusion.** Measured over all 25
golden cases in the wire form `gateway_client.user_turn` actually sends:

| declared | allowed | notes |
|---|---|---|
| `public` | **0/25** | the only value reaching `route()`'s escalation branch |
| `internal` | 25/25 | |
| `confidential` | 25/25 | behaviourally identical to `internal`; the router can never *detect* it |
| `sensitive` | 25/25 | **the maximally permissive declaration** |

`test_manifest_classification_is_not_sensitive` refuses the no-op and accepts
the outage. G5 does hold — but by the *detected* level, at
`audit.build_record:111` and `route`'s `found.level == "sensitive"` branch —
never by the declared one. The manifest check is not what keeps G5, and draft 1
treated it as if it were.

### 6. The registry authorizes a service that does not exist — and the cut is recorded

`callers: [highlights-agent, recap-agent]` for `catalog-search`, and
`tools.cedar` carries the permit. `recap-agent` has no manifest and is the
service Act 1 scaffolds. **This is a recorded cut** — `handler.py`'s
`SERVICE_PRINCIPAL` docstring and ADR-023 name it *"unreachable through this
stack rather than denied by it."*

New from the review: the Tool Owner seat measured that **removing it costs
nothing** — `1799 passed` after regeneration, zero tests depend on the phantom
grant — but re-adding it is another two-key change, and Act 1's own command
scaffolds that name.

### 7. Act 1's own command names a brand with no pack

`quality/judge/` contains `rubric-sports.md`. There is no news rubric and no
brand registry; the only enumeration of the two brands is an `enum` inside
`tools/catalog-search/schema.in.json`.

New from the review: the catalog carries **2** `meridian-news` titles of 5, and
appending one to `data/catalog.json` turns **16 tests red** with *"the current
tree matches no recorded instrument; frozen.json is stale"* — a message naming
no file, no cause and no remedy, whose real fix is a re-calibration and
therefore model calls.

### 8. `normalize` erases a 64-hex digest — and the digest was the wrong idea

Confirmed by four seats: two templates differing only in `MANIFEST_SHA256`
normalise **equal**; a `sha256:` prefix does not help (`\b` matches at the
colon). The raw synth carries six 64-hex strings, all asset digests at three
`Properties/Code/S3Key` and three dropped `Metadata` positions; the committed
snapshots carry zero.

Three things the review added, and together they retire the idea rather than
fix it:

- **Uppercase hex survives untouched.** Emitting the digest as `61FCE1E0…` would
  ride today with no narrowing at all — a tempting wrong fix that makes the
  erasure rule depend on case by accident.
- **`SERVICE_PRINCIPAL` and a plain `DECLARED_CLASSIFICATION` already survive
  `normalize` unchanged.** Only the digest is erased. A plain level string reads
  itself in a snapshot diff; a digest, once un-erased, is an opaque delta.
- **A 64-hex *service name* is accepted by `cedar.IDENTIFIER`**, so under
  draft 1's decision 4 a hex-shaped service name would have made principal drift
  invisible. The verifier bounds `service:` so it cannot take an asset-hash
  shape.

The narrowing itself is safe (two tests touch `normalize`, neither asserts the
blanket rewrite, 1795 green on a real re-synth) — it is simply no longer needed.

### 9. A new service gets no L2 lane, and nothing goes absent

`pave evals run services/recap-agent` prints *"no goldens comparator pinned"*
and returns **0** — correct, since an absent verdict blocks. But
`quality-gate.yml` names `services/highlights-agent` as a literal in the L2 and
L5 steps, so a second service produces no lane and no absence.

**Draft 1 measured this and then built nothing for it.** This draft records it
as a cut with an owner: per-service lanes are M08's neighbourhood (one verdict
schema, many runners), and the manifest lane is per-service from the start. What
M05 must not do is require twenty golden cases and let a reader believe they are
scored. *At scale, the gate iterates the verified service set; `pave verify
--all` already produces it.*

### 10. The onboarding PR needs five seats across five rules, before M05 adds any

Measured by the Service Team seat over a complete honest onboarding PR:

```
golden cases, eval thresholds, headroom policy      [ai-quality]
committed goldens evidence                          [ai-quality, platform-eng]
the gate's scoring comparators                      [ai-quality, platform-eng, security]
gate criteria                                       [ai-quality, platform-eng]
consequence classes                                 [tool-owner, legal-sp]
DISTINCT SEATS REQUIRED: 5
```

Draft 1 said three. The manifest and the template take none.

### 11. Three recordings come due at this milestone's close

Acts 0, 1 and 2 are owed to M05, and `tests/test_demo_recordings.py` reads the
README progression table.

### 12. `m05` is a "never happened" sentinel in two protection tests, and it is about to happen

Found by Service Team, reproduced here.

```
$ mkdir -p milestones/M05 && echo "# M05" > milestones/M05/README.md
$ python -m pytest -q tests/test_history_append_only.py
E  FileExistsError: [WinError 183] ... \repo\milestones\M05
1 failed, 81 passed
```

`tests/test_history_append_only.py:610` calls `(scratch/"milestones"/"M05").mkdir()`
with no `exist_ok`, and `m05` is the never-recorded arm throughout that file —
eight literals. It is on the three-key rule, so M05's first commit turns a
three-key protection red for a reason that is not a governance finding, with a
message naming a pytest tmp path.

```
$ # README M05 row marked ✅ — DoD step 4
FAILED test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed
FAILED test_the_progression_parser_is_not_vacuous          # assert True is False
```

`tests/test_demo_recordings.py:91` pins `milestone_is_closed("M05") is False` as
its vacuity guard, and that one survives an honest re-deferral of all three acts.

This is ADR-041's F2 one level out: *a protection recorded in a form that
forbids its own legitimate successor.* The rule it yields — **a sentinel meaning
"not yet" must not be a value that becomes true** — is a decision for the ADR,
and both instances move to a tag no milestone can ever claim.

### 13. G1's allowlist and every assertion defending it merge on zero keys

```
$ sed -i 's/("GatewayFn",)/("GatewayFn", "ScaffoldSmokeFn")/' pave/infra.py
$ sed -i '<the same edit to its own pin>' tests/test_iam_assertions.py
1795 passed in 50.93s
two-key: NOT REQUIRED
```

`pave/infra.py:64`: *"If you are adding an entry, you are writing an exception,
and it needs an ADR and the Security seat rather than a commit."*
`tests/test_iam_assertions.py:118`: *"Adding another is a G1 exception (Security
seat + ADR), not a test fix."* Neither file is on any rule. Two protections
stated in the two places a reader would look, and enforced in neither.

The Security seat measured the second half too: with the allowlist widened, a
`bedrock:InvokeModel` grant on `Resource: "*"` planted in the committed snapshot
leaves only two failures, both `assert` statements in the same unguarded file.

What still stops a *deployed* grant is the freshness lane re-synthesizing from
`gateway-stack.ts`, which is two-key with an ADR. **G1's enforcement rests
entirely on one guarded file plus one CI job that needs Node.** The offline
assertion suite CLAUDE.md points at is decorative against a determined diff.

**And CLAUDE.md's pointer is wrong.** Line 26 says *"`platform/infra/tests/`
asserts this at synth time."* That directory contains three JSON fixtures and a
README. There is no test in it. The G1 pointer in the file that declares G1
non-negotiable — and that names this exact shape as the repo's worst failure
mode — points at a directory with no assertions.

### 14. G3: a Cedar permit for a principal no registry entry names, on zero keys

```
$ # two lines in platform/gateway/core/cedar.py's generate()
$ python -m pave.cli policy generate
$ grep -n 'attacker-svc' platform/gateway/policy/tools.cedar
28:  principal == Service::"attacker-svc",
$ python -m pave.cli policy generate --check
tool plane current: 6 policies and 3 contract(s) from 3 registered tool(s)   exit=0
$ python -m pytest -q
1795 passed
two-key: NOT REQUIRED          # platform/registry/tools.yaml untouched
```

The drift gate is `generate(REGISTRY) == COMMITTED` — both sides call the same
function. It proves the artifact is a faithful build product *of the generator*;
it never proves the generator is a faithful function *of the registry*. ADR-004's
stated property is *"the registry decides."* What is enforced is *"the generator
decides."*

The asymmetry is the diagnosis:
`test_every_caller_the_registry_names_is_permitted` independently checks
`registry ⊆ policy`, so removing a grant is caught. `policy ⊆ registry` has no
independent assertion, so adding one is not.

### 15. The reference manifest fails the verifier, today, on a publish-class tool

No plant needed:

```
manifest declares : ['catalog-search', 'entitlement-check']
registry grants   : ['catalog-search', 'entitlement-check', 'publish-highlight']
GRANTED NOT DECLARED: ['publish-highlight']
```

`publish-highlight` is `consequence: publish` — the interlock class, claim 10 —
and `tools.cedar` carries its permit today. Both directions are unchecked:
omitting a granted tool is 1795 green, and declaring an ungranted one is 1795
green.

The Tool Owner seat also measured that `@`-ranges are discarded entirely:
`catalog-search@^5`, `catalog-search@not-a-version` and `catalog-search@` are
each **1795 passed**. And registering a fourth tool whose `callers` omits
`highlights-agent`, declaring it in the manifest and regenerating, made the
suite go **up by one** and stay green.

Semver comparison is ~25 stdlib lines and correct on the 0.x caret rule, so **no
new dependency and no ADR line is owed** for it.

### 16. The transport supplies the subject half of a personal-data classification on every request

`services/highlights-agent/gateway_client.py:125` prefixes every request with
the literal `Viewer plan=… dma=…`, and `viewer` is a `SUBJECT_TERM` in
`classify.py`.

```
bare : "What is the name of the anchor presenting the late edition?"  -> internal
wire : same question as actually sent                                 -> sensitive, REFUSED
       "seeks name about viewer — personal data about identifiable people"
```

A segment name, a newsroom street address, a support email — all refused as
personal data, none containing any. Of eight bland starter cases a Platform
engineer would plausibly write, **four were refused.**

**The repo already records this hazard.** `quality/judge/frozen.json` names it
verbatim for the judge instrument and says instrument B refuses none. The judge
got the fix; the transport never did. `pave new` is what turns a one-service
accident into a platform product.

The 25 committed golden cases survive only by accident of vocabulary — all 25
classify `internal` in wire form, and nothing records that as a constraint.

### 17. There is no test-data guard, no fictional-only guard, and no synthetic factory

The Data Governance seat committed, into a clean tree, a golden pack and a
fixture carrying a person's name, a gmail address, an SSN, a card-shaped PAN,
a real US area code and **a real DMA (`columbus-oh`)** — which CLAUDE.md's
fictional-only rule forbids outright:

```
$ python -m pytest -q
1795 passed
$ git add -A -f && python -m pytest -q tests/test_no_account_identifiers.py
703 passed
```

The repo's only leakage guard checks 12-digit AWS account IDs and
account-qualified ARNs. `tests/test_no_account_identifiers.py` is itself on no
rule, and it enumerates via `git ls-files` — so a file on disk but not yet added
is invisible to it, a **second** enumerator disagreeing with the one M05 builds.

### 18. `classify.py` decides every classification refusal and is on no rule

`twokey.triggered(["platform/gateway/core/classify.py"])` → `[]`. Draft 1
proposed two keys on the manifest *label* while leaving `SUBJECT_TERMS`,
`ATTRIBUTE_TERMS` and `AGGREGATE_TERMS` — the rule that gives the label meaning
— editable on one key by any seat. That is ADR-035's thermometer-and-thermostat
in the milestone that cites ADR-035. `classify_sha256` is a change *detector* in
the next recorded run, and M05 records no run.

The same sweep found `tools/*/schema.*.json` on no rule while the registry that
points at them takes two — including `publish-highlight`'s input schema, whose
own description calls the *absence* of a skip-approval field the thing `ADV-008`
probes.

### 19. Corpus growth is already a ratchet, and `pave verify --all` would make it universal

Appending one well-formed golden case to `services/highlights-agent/evals/golden/cases.yaml`:
**8 failed, 1787 passed** — `test_golden_set_is_the_size_the_progression_table_claims`
is an **equality** at 25, not a floor, plus six `tests/test_evals_lane.py`
failures. Nothing M05 proposes makes it worse; the ADR must decide whether that
equality becomes a floor with a recorded reason, as `G4_CASE_FLOOR` did.

### 20. The gate's remediation vocabulary already exists, and the verifier must meet it

The L5 lane, on an unpinned service, names the command, the seats and the
designed behaviour. `classify.py` names the value and the expected set. The L2
lane says *"Pinned services: highlights-agent"* and stops — a support ticket.
Draft 1 committed to *"one named problem per fault"*, which is a count, not a
remediation. **Every check in `pave/manifest.py` names the value, the expected
set, the owning seat and the next command.**

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | The finding-1 tree fails the lane with **one named problem per fault**, each naming value, expected set, owning seat and next command | it passes, reports one problem for four faults, or any message omits a remedy — then the lane counts faults instead of teaching |
| 2 | The enumerator is **directory-driven**: `services/x/pave.manifest.yml`, `services/x/inner/pave.manifest.yaml`, a `pave.manifest.yaml` that is a *directory*, and a plain unmanifested directory are each red; the control is excluded **by name**, its reason in the constant, and **the exclusion set is pinned by a test** | any is missed, or the exclusion set is extendable with the suite green — then the enumerator is decoration and the exclusion is a back door |
| 3 | `eval_min_cases: 20 → 0` is red, the message names the **platform floor** and its seat; the floor lives in `pave/floors.py` on three keys; and **lowering the floor constant below `smallest_pack_that_can_hold_headroom()` is red** | the service's own number appears in the message, **or the floor constant is lowerable to any value ≥ 1 with the suite green** — then the denominator is still the PR's, which is ADR-042 decision 6 one directory over |
| 4 | `internal → public` is red naming the measured **0/25** outage; `→ sensitive` is red naming that it is the *most permissive* declaration; `→ confidential` is accepted with the recorded cut that it is enforced as `internal`; three distinct messages | any two share a message, or any is green — then the verifier reproduces the inverted check draft 1 was going to lift |
| 5 | **Every check is deletable only loudly.** Neutering any check in `pave/manifest.py`, **any threshold literal in `pave/floors.py`**, or any entry in the exclusion set produces at least one named failure — audited by neutering each in turn and running the full suite | any is silent — ADR-042 prediction 7b, which failed for 4 of 10 checks on its first implementation. Draft 1's version covered deletion only; AI Quality measured that deletion is loud while **weakening is silent**, so weakening is in scope here |
| 6 | Every path this milestone creates or touches carries a **named** seat set: `services/*/pave.manifest.yaml`, `templates/`, `pave/manifest.py`, `tests/test_manifest_verify.py`, `tests/test_budget_derivation.py`, `pave/infra.py`, `tests/test_iam_assertions.py`, `platform/gateway/core/cedar.py`, `tests/test_cedar_policy.py`; no path drops below today's keys; and the seat-set test is red when any seat is removed from any of them | one drops, one is unnamed, or a removal is green — then ADR-042 prediction 7 has failed a fifth time in the spec that quotes it |
| 7 | Template parity covers **`pave.manifest.yaml` only**, under a **named** normalisation, and `run_probes_via_gateway.py` is not rendered for the reference service; the seven live instrument digests are unchanged before and after | parity reaches a digest input, or any `*_sha256` moves — then scaffolding de-registered `m04-E`, which this milestone forbids |
| 8 | `pave new` **creates files and edits none**: a test asserts every path it writes did not previously exist and lies under `services/<name>/`; `../../platform`, `a/b`, `.`, an absolute path, an existing service name and `highlights-agent-baseline` are each **refused**, not written | any is written — then the road reaches into files it does not own, and the Security seat's measured truncation of the reference manifest to 84 bytes is reachable |
| 9 | `pave gate manifest`'s verdict is in `gate decide`'s list; deleting the step exits **2**; and **all nine malformed manifests** — a list, a scalar, empty, non-UTF-8, `{bad`, an anchor bomb, a directory, no `service`, no `gates` — produce a named FAIL verdict with **no traceback** | any raises, or any writes no verdict — then ADR-042's six-tracebacks finding has arrived a second time in a module written after it |
| 10 | `DECLARED_CLASSIFICATION` is read by `handler.py` **without a default**, a request declaring above it is refused, and no instrument digest moves | it keeps a default, or any `*_sha256` moves — then G5's level is still the caller's claim, or the fix was not affordable and should have been cut |
| 11 | A freshly scaffolded service fails the lane on **exactly the faults the spec names** — its golden count and its unregistered `callers` entry — and its starter pack contains **no case that classifies `sensitive` in wire form** | it fails on something else — draft 1's version of this prediction was refuted three ways, and the starter-pack clause is the one Data Governance measured at 4 of 8 |
| 12 | The two invariant holes close: widening `MODEL_INVOKE_ROLE_PREFIXES` and the `attacker-svc` generator plant each become **red and key-collecting**; and `policy ⊆ registry` is checked independently of `generate()` | either stays green, or the completeness check calls the generator — then the drift gate is still comparing the generator to itself |
| 13 | No recorded number moves: no `evals/history/` entry changes, `pins.json` gains nothing, `evals/comparators.json` is byte-identical, and no README **bold `n/m`** row moves | any moves — then a scaffolding milestone touched the instrument |
| 14 | Zero model calls; `make check` hermetic; no new dependency (semver is stdlib, measured) | any fails — then G8 paid for a convenience |
| 15 | The `m05` sentinels move to a tag no milestone can claim, and creating `milestones/M05/` plus marking the progression row ✅ leaves the suite green | either is red at close — then the milestone cannot close without editing a three-key protection for a non-governance reason |

Prediction 5 is the discipline carried from ADR-042 and has failed on first
implementation every time it has been measured. Prediction 12 is the one that
says a milestone about verifying declarations did not ship standing on two live
invariant holes.

## The cuts, each with its reason and its owner

| cut | reason | owner |
|---|---|---|
| **Deploy-time verification** (draft 1's decision 4, whole) | Measured: the freshness lane compares synth to a snapshot the same PR re-records, so the weakening merges after the remedy the error prints. Its remaining value is a legible diff. *At scale, replace with a signed attestation checked by the deployment pipeline; the `attestations` block already matches.* | Platform Engineering |
| **`manifest_signature` stays unbuilt, and the comment is corrected** | Leaving *"written by CI, verified at deploy"* beside a field nothing writes is the shape this milestone exists to remove | Platform Engineering |
| **No agent Lambda** | 43 free lines, but it deploys the service that existed before `pave new`; claim 1 is about the scaffolded one, which ADR-023 makes unreachable through this stack. *At scale, a gateway per service or a verified caller identity; the interface already matches.* | Platform Engineering |
| **No second committed service** | `main` is always green; a scaffolded service is meant to be red until governed | PM |
| **No per-service L2/L5 lanes** (finding 9) | One verdict schema across many runners is M08. M05 must not let a reader believe the twenty cases it requires are scored. *At scale, the gate iterates the verified service set; `pave verify --all` already produces it.* | Platform Engineering + AI Quality |
| **No brand registry**; `--brand` verified against the rubric files that exist | A brand pack is L3 content and M07's neighbourhood; the news fixtures cannot grow without a re-calibration, which needs model calls | AI Quality |
| **No `pave exception`** — and what a blocked team does instead | The off-ramp `ROLES.md` documents is a stub that exits 0, and M05 builds the first floor a team can legitimately fail. Until M06 the route is an ADR reviewed by AI Quality, and the lane's own message says so. A wall with a documented door that does not open is worse than a wall | Service Team + AI Quality |
| **No `classify.py` two-key rule, no test-data guard** (findings 17, 18) | Both are Data Governance decisions with real design content — a taxonomy owner and a PII rule a service team can follow — and neither is on a path M05 touches. **Recorded, with the measurements, and handed to the owning seat rather than left in a review transcript** | Data Governance |
| **`classification: confidential` accepted, enforced as `internal`** | `classify_request` can never detect it and says so; refusing it would break a level the router accepts | Data Governance |

## Definition of done

- [ ] Draft 2 reviewed by six seats planting and running; what each draft got
      wrong recorded in the ADR.
- [ ] The ADR written **before the code**, zero model calls, with its own "what
      draft N got wrong" section and the nine cut rows.
- [ ] `pave new` creates-only, refuses the eight hostile names of prediction 8,
      and the stub's CODEOWNERS string is deleted.
- [ ] `pave/manifest.py` on `("ai-quality", "security", "platform-eng")`;
      `tests/test_manifest_verify.py` added to the enumerated `tests/(…)` rule.
- [ ] `services/*/pave.manifest.yaml` and `templates/` on rules with **named**
      seat sets; `tests/test_budget_derivation.py` joins the manifest's rule.
- [ ] `pave/infra.py` + `tests/test_iam_assertions.py` on
      `("security", "platform-eng")` with `requires_adr=True`; CLAUDE.md's
      `platform/infra/tests/` pointer corrected to name the real file.
- [ ] `platform/gateway/core/cedar.py` + `tests/test_cedar_policy.py` on the
      registry's rule; `policy ⊆ registry` checked **without calling
      `generate()`**.
- [ ] `PLATFORM_EVAL_MIN_CASES` in `pave/floors.py` with its derived ratchet.
- [ ] `DECLARED_CLASSIFICATION` emitted and read without a default; snapshot
      re-recorded; IAM assertions green; allowlist still one entry.
- [ ] The `m05` sentinels moved; `milestones/M05/` and a ✅ row leave the suite
      green.
- [ ] A violating-tree test per check. **Deletability audited by neutering each
      check and each threshold literal in turn**, recorded in the journal.
- [ ] Every failure message names value, expected set, owning seat, next command.
- [ ] `make check` green, hermetic, no new dependency, zero model calls.
- [ ] `milestones/M05/README.md`: what I can demo, the delta, **what broke**.
- [ ] Progression row filled. **Claim 1 marked INCOMPLETE with a footnote — its
      proof-artifact wording is NOT edited in this PR** (AI Quality's
      disposition: the proof-artifact column is the claim's falsifier, `README.md`
      is on no rule, and moving it inside the milestone whose scope makes it
      inconvenient is a self-served threshold move. The repo already has
      vocabulary for shipping less than claimed).
- [ ] Acts 0, 1 and 2 recorded, or re-deferred with a reason over 60 characters.
- [ ] `close-milestone` worked in order — **including a "this milestone records
      nothing" branch for step 2**, which today exits 1 with a bare traceback.

## Sequencing

1. Seat review of this draft. Repeat until a round comes back clean.
2. The ADR.
3. The two-key rules and the seat-set test — **first**, because every check
   after this is worthless without them, and because steps 7–8 touch files that
   are currently unguarded.
4. The `m05` sentinel move.
5. `pave/manifest.py` + violating-tree tests + the deletability audit.
6. `PLATFORM_EVAL_MIN_CASES` and its ratchet in `pave/floors.py`.
7. `policy ⊆ registry`, independent of the generator.
8. `templates/agent-tools/` + manifest-only parity.
9. `pave new`, against the template.
10. `DECLARED_CLASSIFICATION`, the snapshot re-record, the IAM assertions.
11. The gate lane and the workflow step.
12. Seat review **of the code**, planting against the implementation. Repeat.
13. Journal, progression, claim footnote, recordings, tag.

## What M05 must NOT do

- **Must not call a model.**
- **Must not edit a golden case, a comparator, a threshold, a probe or a
  recorded entry**, and must not touch any input to the seven instrument
  digests — which rules `run_probes_via_gateway.py` out of the template.
- **Must not lower `eval_min_cases`** to make the scaffolded service verify.
- **Must not let `pave new` edit a file that already exists.**
- **Must not reformat `data/catalog.json`.**
- **Must not reword claim 1's proof artifact.**
- **Must not mark the progression row ✅** before the recordings are recorded or
  deliberately re-deferred.

## The demo artifact

`milestones/M05/` carries, all reproducible offline except the recordings:

- **`scaffold-transcript.txt`** — the command, timed, and the files it produced.
- **`manifest-verify-witness.json`** — `pave verify --all` on the scaffolded
  service: red, one named problem per fault, each with its remedy; then green
  after the two edits a developer can make **by hand, with no credentials and no
  model call** — writing their golden pack and adding their registry `callers`
  entry. The comparator pin is *not* among them: it is the L2 lane's, it needs
  answers, and finding 9 records that cut. Draft 1 said "three edits" in two
  places and "two" in a third, and promised a green half that required
  seventeen hand-authored cases nobody had budgeted.
- **`verdict-manifest.json`** — the lane's verdict, in the gate's list.
- **`invariant-holes.md`** — findings 13 and 14 as they were measured, and the
  diff that closed them.
- **The three recordings**, or their re-deferral with its reason. Act 1's script
  says *"the manifest verification at deploy"* is what a developer cannot
  remove; the script is corrected in the same PR, or the recording states a cut
  the ADR made.

## Why this is a milestone and not a chore PR

Because a scaffold is a claim about what a team cannot remove, and this
repository currently cannot say what that is. A service can delete six of its
ten manifest fields, halve its own case floor to zero, and declare a
classification that either does nothing or takes it down completely, with 1795
tests green and no seat's key required.

And because six seats went looking and found that the file describing what a
service *is* takes no keys, the module that would judge it takes none, the
allowlist naming the one role permitted to reach a model takes none, and the
generator producing the deployed authorization policy takes none — each of the
last two with its own comment saying otherwise.

The command that would have produced the manifest prints a sentence and exits 0.
Fixing the command without fixing the file it writes would give the paved road a
sign and no surface.

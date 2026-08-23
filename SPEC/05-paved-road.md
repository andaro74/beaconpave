# SPEC/05 — The paved road, and the manifest nothing verifies

**Owning seat:** PM (spec) · Platform Engineering (`pave new`, the template, the
verifier, the lane) · Service Team (the developer who runs one command) · Data
Governance (the level vocabulary) · Tool Owner (`tools:`, the registry, the
generator, the tool schemas) · AI Quality (`gates.*`, the case floor, the
headroom band) · Security / Red Team (the keys, and the invariant holes this
milestone walked into)
**Milestone:** M05 · branch `m05-paved-road` · tag `m05`

**This is the fourth draft.** Six seats reviewed each of drafts 1, 2 and 3, each
planting and running in its own worktree. All six called for a redraft every
time: **39 blocking findings on draft 1, 31 on draft 2, 20 on draft 3.** Three
seats corrected their own earlier findings — twice downward, which mattered as
much as the escalations, because over-stating an exposure leads to over-keying.
**Six statements of fact in drafts 1–3 were measured false, and every one of them
flattered the platform.** They are quoted in their own sections rather than
edited away. Drafts 1–3 are preserved at `scratchpad/SPEC-05-draft{1,2,3}.md`.

The premise has survived four rounds unchallenged. What has not survived is
every mechanism proposed to fix it: draft 1 proposed verification at deploy,
draft 2 cut that and proposed a deployment binding, draft 3 cut the binding, and
**draft 4 relocates every control draft 3 put in a file that cannot hold it.**

## Why this milestone exists

`pave new` is a stub that prints a sentence and exits 0.
`templates/agent-tools/` is one README. And **`pave.manifest.yaml` is a
ten-field declaration that nothing verifies, six of whose fields can be deleted
outright at 1795 passed** — including `attestations`, which is commented
*"written by CI, verified at deploy"* and is written by nothing. Changing values
rather than deleting them is green everywhere that matters:
`classification: internal → public` (1795), `→ confidential` (1795),
`gates.eval_min_cases: 20 → 0` (1795), dropping a declared tool (1795).

**The review found six more of the same shape, five of them live on `main`, four
of them invariant holes.** They are here because a milestone that builds a
verifier while standing on them would be the shape it exists to remove.

## What draft 3 got wrong

- **Build item 4 required the edit that "must NOT do" forbids.** It imported
  `DECLARABLE_LEVELS` from `classify.py` — a constant that does not exist —
  while the same document ruled `classify.py` out of scope as a digest input.
  Measured by two seats: adding one line there is **15 failed, 1780 passed**;
  adding it to `pave/floors.py` is **1795 passed**. And it was a three-way
  contradiction: the vocabulary it imported (`classify.LEVELS`) contains
  `confidential`, which prediction 4 refuses.
- **"Nothing in the generator is [a consequence-class judgement]."** False, and
  the sentence justified dropping `legal-sp`. `GATED_CONSEQUENCES` lives at
  `cedar.py:38`. Dropping `"publish"` from it removes **every** forbid clause,
  makes `publish-highlight` reachable with no approver, and the drift gate exits
  **0** — measured here at **zero keys collected**. Claim 10, one word.
  Security recommended this seat set in round 2 and retracted it in round 3.
- **The `gateway_client.py` rule made the road longer than draft 1's**, and was
  wrong in both directions. Onboarding went 4 seats → **6**; an ordinary edit to
  a team's own transport client went **0 → 2**. And it keyed the governed copy
  while leaving the control copy at `run_baseline.py:94` unkeyed — verbatim the
  asymmetry `twokey.py`'s own comment says was *"missed once"*.
- **"The same sentence duplicated, byte-identical."** False. The two copies
  render identical text from different source (`{plan}` vs `viewer.get('plan')`),
  which rules out the byte-parity pin the sentence implied.
- **The collected-count floor closes one hole and not the one that matters.**
  Eight lines of `pytest_runtest_makereport` hookwrapper in `tests/conftest.py` —
  zero keys — report **1795 passed, the exact honest count**, with G1's allowlist
  widened and its pin genuinely failing. A count cannot see a harness that lies.
- **Both new guards landed in `pave/cli.py`, which cannot be gated.**
  `pave/tests/test_twokey.py:31` asserts it is ungated, and ADR-042 recorded why.
  Measured: forgery + `collect_ignore` + killing both guards is **exit 0, "All
  checks passed!", 1660 passed, seats required: NONE**.
- **`templates/agent-tools/**` was called "the superset of what it renders" and
  is not** — it lacks `security`, exactly the seat draft 3 added one level down.
  And the document never states the template's rendered file list, so the
  pairwise test prediction 6 requires **has no pair list**.
- **Removing `recap-agent` deletes a protection, green.**
  `test_an_uninvited_caller_is_denied_by_policy` asserts that a registered caller
  of *one* tool is denied *another*. After the removal the registry has one
  distinct caller and **zero cross-tool negative pairs are constructible**; the
  test passes and no longer tests its own name.
- **"`^0`, `^0.1` and `^0.1.0` have different upper bounds."** False — the last
  two are identical. The real third rule is **`^0.0.x`**, which pins the patch,
  and draft 3 aims an implementer at the wrong case.
- **The sentinel count is off by ~5×** — "nine places" against a measured **44**
  (36 `m05` + 7 `M05` in `test_history_append_only.py`, 1 in
  `test_demo_recordings.py`).
- **The four-PR split was presented as answering a scope finding, and on that
  axis it makes things worse**: one PR at five seats becomes **fourteen
  seat-attestations across three bodies**. It is right for CI and should be
  described as CI hygiene.
- **PR 1 claimed to close findings 14 and 15**, whose mechanism is in PR 2.
- **`make core`'s "two-line guard" is bypassable by `make -i`**, which runs the
  deploy anyway. It must be `&&` on one recipe line.

## What drafts 1 and 2 got wrong

Carried as the record. **Draft 1:** *"`sensitive` is the level G5 refuses by
design"* (false — it is the maximally permissive declaration, 25/25 allowed);
*"`classification: public` changes nothing at runtime"* (false — 0/25 served);
*"four ceilings are pinned"* (false — both halves are one-key, the true count is
zero); decision 4 measured not to block; predictions 10 and 11 falsified by its
own build list; no seat sets named. **Draft 2:** the deployment binding
unimplementable (no YAML parser; a regex takes `sensitive` where PyYAML takes
`internal` on a duplicate key); its cost under-counted at two keys against a
measured three-plus-ADR; prediction 10's rule inverted; prediction 12's "red"
half unachievable; `classify.py`'s exposure overstated; finding 6 quoting a
number (1799) that does not reproduce (1795).

## What M05 builds — four PRs

The split is **CI hygiene, not scope reduction**: stacked PRs get zero CI here,
so each lands independently green. **A team onboarding after M05 does one PR**,
and the four-PR structure is invisible to them.

### PR 1 — the keys, the sentinels, the registry

1. **Two-key rules with named seats** (table below), a **seat-set test**, a
   **pairwise test** over a **stated pair list**, and the seat vocabulary
   asserted against `ROLES.md` — which names **eight** seats, not seven, and one
   of which (`data-governance`) is a string `twokey.py` has never used.
2. **Findings 12, 13, 16 and 17 close here.** Findings 14 and 15 close in PR 2,
   where their mechanism is.
3. **The 44 `m05` sentinels**: forty-three move to `mzz`; **one repoints to
   `m06`** because it reads the live README table and needs a tag that has a row;
   and the vacuity guard is **restructured to name no milestone at all** — it
   asserts the parser discriminates, which survives every future close.
4. **`recap-agent` leaves the registry and the cross-tool negative control is
   re-founded on a synthetic registry in the same commit.** The reference
   manifest declares `publish-highlight@^0` with its approver. Both land here so
   PR 2's verifier is green on arrival. `handler.py:61` and
   `tools/catalog-search/README.md:13` are corrected with them.
5. **`GATED_CONSEQUENCES` moves into `platform/registry/tools.yaml` as declared
   data** — ADR-004's *"the registry decides"* — so which classes get an
   interlock is a `tool-owner + legal-sp` change rather than a word in an
   unkeyed generator.

### PR 2 — the verifier and the lane

6. **`pave/manifest.py`, mechanism only.** Every criterion is imported from a
   path carrying its content owner's key: `DECLARABLE_LEVELS` and the headroom
   band from **`pave/floors.py`** (not `classify.py`), the tool set from the
   registry. A hermetic test asserts `DECLARABLE_LEVELS ⊆ classify.LEVELS`,
   **read and never edited**, so one authority survives without touching a
   digest input.
7. **A duplicate-key-rejecting loader**, 17 lines, PyYAML only.
8. **The floors, with their ratchets.** `PLATFORM_EVAL_MIN_CASES`,
   `HEADROOM_BAND` and `COLLECTED_FLOOR` all live in `pave/floors.py`; the
   `pave verify` invocation lives in **`pave/gate.py`**; `pave/cli.py` dispatches
   and holds nothing. Four pins, because draft 3's arrangement was 4-of-5 silent:
   a literal pin on the band, a pin on `smallest_pack_that_can_hold_headroom()`'s
   return including two derived cases so `return <constant>` cannot satisfy it, a
   source assertion that `tests/test_contracts.py` **imports** the band rather
   than duplicating it, and a **ratchet on `COLLECTED_FLOOR`** — a bare constant
   decays, and its printed remedy would otherwise be "lower the floor."
9. **`expect_near_threshold` is accepted at the case top level.** Today it is
   read from `case["judge"]`, so a headroom case needs a judge block, which needs
   a rubric, and the only rubric on disk is `rubric-sports.md` — so a *news*
   service's sole green path is shipping the other brand's rubric. Two lines
   open a deterministic-only door, which is what CLAUDE.md's style rule already
   prefers. **`PROVISIONAL` is withdrawn** by the seat that proposed it.
10. **The floor counts only disposed cases.** A scaffolded pack declares
    `author: pave-template` and does not count toward `eval_min_cases` until it
    carries `disposed: true` and `curated_by` — `tests/test_calibration_corpus.py`
    and `run_judge.py`'s fail-closed refusal are the precedent. The floor then
    means *twenty cases a seat stood behind*, not twenty rows in a file.
11. **The lane**, with every malformed input a named FAIL and no traceback.
12. **Both policy directions plus the gated half**, parsed with `cedar.parse`,
    never `generate()`, hard-stopping on a duplicated registry id.

### PR 3 — the template and the command

13. **`templates/agent-tools/`**, with its **rendered file list stated in the
    spec**, and manifest-only parity under a named normalisation that does **not**
    erase `gates.budgets`.
14. **`pave new`, creates-only.** The printed registry block **names the tool id
    and the line**, not "add your service to `callers:`" — three `callers:` lines
    exist and two read identically, and a seat following the vaguer instruction
    over-granted itself the publish-class tool during this review.

### PR 4 — the close

15. Journal, progression row, claim-1 footnote, recordings. **`README.md` and
    `docs/governance/recordings.json` go on a rule** — the PR that publishes what
    the milestone claims was the only one nobody had to sign.

## What M05 does NOT build

**No deploy-time verification and no deployment binding** — both measured not to
work. `make core` gains a guard as **`pave verify --all && cdk deploy --all` on
one recipe line**, because two lines are separable and `make -i` runs the deploy
anyway. It does **not** make `manifest_signature` true and must not be sold as
such. *At scale, a signed attestation checked by the deployment pipeline; the
`attestations` block already matches.*

**G5's declared level stays unenforced.** `handler.py:309` keeps taking
`declared` from the event. What the manifest's `classification` **is**, stated
positively so no reader has to derive it: *a declaration the repository refuses
to merge when wrong* — a control on the repository, not on the runtime. The
manifest's comment is corrected to say exactly that, and the corrected text is
in the ADR.

A third path exists and is not taken: `platform/gateway/policy/` already ships
inside the gateway asset, so `pave policy generate` could emit a `services.json`
the handler reads — measured at five handler lines, an eight-line generated
file, **1795 passed, zero digests moved, and `snapshot --check` green with no
re-record**. It is declined here because it changes what the deployed gateway
does inside a scaffolding milestone, and whether that breaks comparability with
the recorded arms is Security's and AI Quality's call. **Recorded with its
measurement so the next reader starts from the number.**

**No agent Lambda. No second committed service. No per-service L2/L5 lanes**
(M08). **No transport fix** — free at the suite and digest level, but the prefix
is duplicated unpinned in the ungoverned control outside the parity loop, so
changing one splits every governed arm from `m00b`. Instead a **source-skeleton
parity test** covering *both* copies, in a file on the three-key `tests/(…)`
rule, so a reword collects Security without taxing a service team's own file.
**No model calls. Zero. No re-score of either suite.**

## Seat sets, named

| path | seats | note |
|---|---|---|
| `services/*/pave.manifest.yaml`, `tests/test_budget_derivation.py` | `ai-quality`, `tool-owner` | **`data-governance` dropped**, on its own seat's argument: once `confidential` is refused, `classification` has exactly one legal value, so the rule collects an attestation on a diff that cannot legally exist while taxing every `gates` and `tools` change |
| `templates/agent-tools/**` | `platform-eng`, `ai-quality`, `tool-owner`, `data-governance`, `security` | the true superset of what it renders — a template edit sets the default floor, level, tool set **and wire text** for every service that does not exist yet |
| `pave/manifest.py`, `pave/floors.py`, `pave/gate.py`, `tests/test_manifest_verify.py` | `ai-quality`, `security`, `platform-eng` (+`data-governance` on `floors.py`, which now holds `DECLARABLE_LEVELS`) | valid only because the verifier holds mechanism and imports every criterion |
| `pave/infra.py`, `tests/test_iam_assertions.py` | `security`, `platform-eng`, **ADR** | G1's allowlist |
| `platform/gateway/core/cedar.py`, `tests/test_cedar_policy.py`, `tools/*/schema.(in\|out).json` | `platform-eng`, `security`, `tool-owner` | `legal-sp` is not here **because `GATED_CONSEQUENCES` moves to the registry**, which already has it |
| `platform/gateway/core/audit.py` | + `ai-quality` | `POLICY_MECHANISMS` is invisible to every pin, and finding 21 runs through it |
| `tests/conftest.py`, `pyproject.toml` | `platform-eng`, `security` | ADR-042 listed these as "none — stated"; the hookwrapper measurement retires that |
| `Makefile` | `platform-eng`, `ai-quality` | it holds the only deploy-side control M05 ships; one seat would let its owner write its own rationale |
| `README.md`, `docs/governance/recordings.json` | `platform-eng`, `ai-quality` | PR 4 |

**No `services/*/gateway_client.py` rule** — the skeleton-parity test carries it
instead, at zero cost to the road.

## The residual, stated

`tests/conftest.py` on a rule makes the hookwrapper attack **collectable**. It
does not make it **red**: a harness that rewrites reports can report anything,
and no count sees it. The deciding instance for this milestone's own checks is a
workflow step, as ADR-042 decision 3 requires — that covers `pave gate manifest`
and leaves the other ~1790 assertions under a harness that is now keyed and
still trusted. **That is the standing residual, it is written here rather than
discovered, and it is owned by the rule.** So is the fact that a deleted test
file is invisible to pytest.

## Pre-flight findings

Twenty-one findings, all measured on `07e8cd1` at 1795 green, each re-measured
by at least two seats. Findings 1–11 are the manifest itself: no enumerator,
three hard-coded `MANIFEST` constants, the control with no manifest, the
manifest and its pins on no rule, `pave new` a stub, the declared classification
unread with `public` an outage at 0/25, a phantom registry caller, a brand with
no pack, `normalize` erasing digests, a new service getting no lane, and three
recordings due. Findings 12–21 are the review's:

**12.** 44 `m05` sentinels about to become real. **13.** G1's allowlist and its
own pin, one diff, 1795 passed, zero keys — against two prose statements
requiring Security and an ADR; and CLAUDE.md:26 points G1 at a directory with no
tests. **14.** A Cedar permit for a principal no registry entry names, drift gate
exit 0, zero keys. **15.** Claim 10 dying on three zero-key files with
`pave check` printing "All checks passed!"; `collect_ignore` alone drops
**1795 → 1656**; and the hookwrapper reports **1795** with a pin genuinely
failing. **16.** The `Viewer` transport prefix making 4 of 20 realistic cases
`sensitive` while `pave verify` says PASS. **17.** A zero-key tool-schema edit
putting `skip_approval` into the deployed contract set and removing the
MER-AI-0001 disclosure flag — and the schema's own claim that ADV-008 probes its
absence is false. **18.** `classify.py` transitively three-key, corrected
**downward** from draft 2. **19.** Corpus growth a ratchet in eight places.
**20.** `gateway_client.py` composing every observation's wire text, in no digest
and on no rule, while the file that imports it is in both. **21.** A service
declaring `classification: public` denying 11/11 probes with
`mechanism: classification` ∈ `POLICY_MECHANISMS`, scoring **10/11** against a
best recorded arm of 7/10 — a service that answers nothing outscoring every
system this repo has built.

**Finding 21 is not M05's to fix, and it gets an ADR opened in this milestone
rather than a hand-over line.** The scorer already contains the rule one word
over — `adversarial.py:405` refuses a guardrail block on a channel the payload
never reached, *"crediting it would pass every probe at once"* — so this is a
narrow extension, cheap to reverse and expensive to forget. Its second key is
Data Governance, because the field that discriminates the honest arm from the
attack arm is `record["classification"]`, which the lake already holds and
`observation_from_record` (`audit.py:199`) drops. Seats: **Security +
Data Governance**, naming `observation_from_record` as the specific handover.
Prediction 4's `public` message **must not read as a mitigation** — the manifest
value is unenforced, so the shape is produced by the request, not the manifest.

## Pre-registered predictions

Unchanged from draft 3 except as noted. **3** adds: the band has exactly one
definition, in `pave/floors.py`, imported not duplicated. **4** requires four
distinct messages and refuses `confidential` — for the corrected reason that no
*detection* can produce it, not that "no control applies it" (`route` does apply
it, by index). **5** widens to *every check, every threshold literal, and every
function a ratchet calls*, with the deleted-test-file residual stated. **6** adds
the stated pair list. **7** adds that the normalisation must not erase
`gates.budgets`. **9** adds that the guards live outside `pave/cli.py` and that
the hookwrapper is collectable-not-red. **11** covers every verified pack, not
the starter three. **12** adds the gated-forbid half and the duplicate-id
hard-stop. **13**'s DoD command gains `milestones/` with an `M05` exclusion.
**14** names **`^0.0.x`** as the third caret rule and **refuses** it as a range
this repo does not evaluate. **15** is 43 literals plus one repoint.

## Definition of done

As draft 3, with: every relocation above; the pair list stated; the template's
rendered file list stated; the corrected manifest comment written out; claim 1
marked **INCOMPLETE** with **two** footnoted reasons — no deployed agent, and a
measured authorship burden of roughly an hour for the twenty-case pack the floor
requires, against a claim of thirty minutes; and the deletability audit budgeted
at **~50 s per clean run and up to 40 minutes for an unlucky one**.

## Why this is a milestone and not a chore PR

Because a scaffold is a claim about what a team cannot remove, and this
repository cannot currently say what that is — and because three rounds of six
seats found that the file describing what a service *is* takes no keys, the
module that would judge it takes none, the allowlist naming the one role
permitted to reach a model takes none, the generator producing the deployed
authorization policy takes none, one word in it removes every approval interlock,
the tool schema carrying a regulated disclosure flag takes none, eight lines in a
zero-key `conftest.py` make 1795 tests report green while a G1 pin fails, and a
service configured to answer nothing scores better on the compliance suite than
any system this repo has ever built.

The command that would have produced the manifest prints a sentence and exits 0.

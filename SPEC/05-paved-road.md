# SPEC/05 — The paved road, and the manifest nothing verifies

**Owning seat:** PM (spec) · Platform Engineering (`pave new`, the template, the
verifier) · Service Team (the developer who runs one command) · Data Governance
(the level vocabulary) · Tool Owner (`tools:`, the registry, the tool schemas) ·
AI Quality (`gates.*`, the case floor, the headroom band) · Security / Red Team
(the keys, the pass semantics, and the invariant holes this milestone walked into)
**Milestone:** M05 · branch `m05-paved-road` · tag `m05`

**This is the sixth draft, and the first written after any of it was built.**
Six seats reviewed each of drafts 1-5, each planting and running in its own
worktree. All six called for a redraft every time: **39 blocking findings on
draft 1, 31 on draft 2, 20 on draft 3, 55 on draft 4, and 49 on draft 5.** The
count rose at draft 4 and that is still the most important fact about this
document's history: draft 4 relocated draft 3's controls into files that could
hold them and walked into a larger set of exposures. **A falling count was never
evidence of convergence, and draft 5 proved it twice over** - its 49 included one
finding that could not be built at all (see PR 2).

**Draft 6 is a record, not a proposal, for four of the six PRs.** PR 1, PR 3, PR 4a
and PR 4b are built and all four are on `main`. Where the built thing differs from what
draft 5 specified, **both are stated and the difference is marked** - never
silently reconciled, because a spec edited to match the code stops being a
pre-registration.

**Numbers.** Draft 5's are `6af17d2`'s, where `python -m pytest -q` is 1861 passed.
Draft 6's are `c6bdaf3`'s (**1909**) for anything measured after PR 4a merged, and
the PR that measured each number is named beside it. Drafts 1-4 quoted `07e8cd1`'s
1795. Round 4's complete record is `docs/M05-round4-findings.md`; round 5's, with
its 49 findings and the twelve lead errors it caught, is
`docs/M05-round5-findings.md`.

**Drafts 1-4 are preserved at the tag `drafts-spec-05`.** Draft 3 is commit
**`a3dcb0d`**; the four drafts are the first four commits touching this file
(`39cfac9`, `d66c343`, `a3dcb0d`, `0d17fdb`), **not** the tag's first four commits,
which are the repository's opening commits. Draft 4 claimed the latter and was
wrong - the third consecutive draft to get its own preservation claim wrong, after
draft 3 named a `scratchpad/` path that was never in the repository. Because that
sentence is not a cited sha, `tests/test_cited_commits_resolve.py` cannot see it.
**Every draft since restates its predictions in full rather than as deltas**, so no
reader needs the tag to check them.

**Draft 6 has not been reviewed, and seven decisions are open.** They are listed at
the end under *Decisions this draft does not make*. Three of them block PR 2
entirely; the rest shape PR 5, PR 6 and the milestone's honesty about what it did
not close. Read this as an unreviewed draft over four reviewed-and-built PRs.

---

## What has shipped

| PR | ADR | state | what it actually did |
|---|---|---|---|
| PR 1 | **ADR-044** | merged (#56) | Two rules over six instrument files, pinned member by member. A duplicated registry id hard-stopped in `cedar.generate()` and converted to a named FAIL by the CLI; the permit/grant check became a bijection on pairs |
| PR 3 | **ADR-048** | merged (#57) | The only cross-tool negative control rested on `recap-agent`, a registry line with no service behind it. Removing the entry left the test **passing at 1881 with zero pairs constructible**; the control is re-founded on an in-module synthetic registry that asserts its own sufficiency |
| PR 4a | **ADR-045** | merged (#58) | `DECLARABLE_LEVELS = ("internal",)` on a measured criterion, and five floors with pins that fire. Four of draft 4's five were silent or absent |
| PR 4b | **ADR-046** | merged (#59) | The verifier: `pave/manifest.py`, `pave/verify.py`, a fourteen-row refusal table as code with a producer per row, the grant bijection in both directions, and `COLLECTED_FLOOR` enforced |
| PR 2 | - | **split out of M05** | Not buildable as specified. Three decisions owed |
| PR 5 | ADR-047 | not started | **Unblocked.** PR 4b is merged; this is the next thing to build |
| PR 6 | - | not started | Blocked on PR 5, and on three screen recordings only the operator can make |

**Suite:** 1861 (`6af17d2`) -> 1909 (`c6bdaf3`, PR 4a merged) -> **1993** on `main`
with PR 4b merged. `COLLECTED_FLOOR` re-seated 1900 -> 1993 and now enforced in `pave check`.

### Where the built thing differs from draft 5

Five differences, each measured. None is a scope reduction; three are draft 5
being wrong.

1. **The refusal table has fourteen rows, not thirteen, and row 10 changed.**
   Draft 5's row 10 was *"undisposed pack header / the missing `curated_by`"*. PR 4a
   measured the pack-level header as a **47-failure migration** and replaced it with
   per-case `provenance.author`, so a row naming `curated_by` would have failed the
   reference pack on day one. Row 10 is now **`gates.eval_min_cases` below the
   platform floor** - the milestone's own opening finding, which draft 5's table
   omitted, *deferred by silence, which its own item 29 forbids*. **Row 14 is new**
   for `brand`, which draft 5 left as a `print()` in a creates-only command.
2. **`pave verify` is not the literal.** The `pave` console script exists only after
   `pip install -e .`, and from `platform/infra` the module is not importable. The
   command is **`python -m pave.cli verify --all`**, and PR 6's `make core` line is
   `cd platform/infra && python -m pave.cli verify --all && cdk deploy --all`.
3. **`highlights-agent` declares `publish-highlight@^0`.** Row 4 fired on the only
   committed manifest, as the Tool Owner seat predicted. Draft 5 said *"neither fix
   is free"* and did not price them: revoking the grant is **4 failed** - a tool with
   no callers is unreachable under G3, and M02's recorded `policy` denial needs the
   `permit` to exist, or it collapses into `catalog-purge`'s *no-permit* case.
   Declaring it is green. **This is not free either**: the reference manifest now
   declares a `publish`-consequence tool and the manifest rule does not collect
   Security. That is decision 3 below, written onto the rule in `pave/twokey.py`.
4. **Three criteria moved into `pave/floors.py` that draft 5 never mentioned** -
   `SUPPORTED_BRANDS`, `REQUIRED_BUDGET_KEYS`, `CASE_TOP_LEVEL_KEYS`. Each existed
   somewhere and none existed in the criteria file, so a verifier reading them would
   have created a second site. That is ADR-037's subject, and the second copy never
   goes red on its own.
5. **`COLLECTED_FLOOR`'s first wiring was a check nothing could execute.** Written
   inline in `pave/cli.py`'s `check()`, which no test calls. ADR-042's own finding,
   reproduced inside the fix for it. Extracted, unit-tested, and the call site pinned
   by an `ast` walk.

## Why this milestone exists

`pave new` is a stub that prints a sentence and exits 0.
`templates/agent-tools/` is one README. And **`pave.manifest.yaml` is a ten-field
declaration that nothing verifies**, six of whose fields can be deleted outright at
**1861 passed** — including `attestations`, which is commented *"written by CI,
verified at deploy"* and is written by nothing.

Re-measured on `6af17d2`, field by field:

| deleted | result |
|---|---|
| `apiVersion`, `template`, `brand`, `owners`, `runtime`, `attestations` | **1861 passed** each |
| `service`, `classification`, `tools`, `gates` | 1 failed each |

Changing values rather than deleting them is green everywhere:
`classification: internal → public` (**1861**), `→ confidential` (**1861**),
`gates.eval_min_cases: 20 → 0` (**1861**), dropping a declared tool (**1861**).

And the sharper form of the same fact, measured by Platform Engineering in round 4:
a whole new `services/scaffold-probe/` — a manifest naming a brand that does not
exist, no evals, no goldens, no gateway client, no registry entry — is **1861
passed**. **A service this repository has never heard of is indistinguishable from
one it has.**

## What M05 does NOT build

**No deploy-time verification and no deployment binding** — both measured not to
work (drafts 1 and 2). `make core` gains a guard, stated exactly, in PR 6.

**G5's declared level stays unenforced.** `handler.py:309` keeps taking `declared`
from the event. What the manifest's `classification` **is**, stated positively:
*a declaration the repository refuses to merge when it is outside the vocabulary* —
a control on the repository, not on the runtime, and **not** a claim that the
repository can tell whether the declaration is honest. Draft 4 said "refuses to
merge when wrong"; Data Governance measured that the repository cannot judge
wrongness, only membership. The corrected manifest comment is written out in PR 4
and reproduced in ADR-046.

Declining deploy-time enforcement is now **cheaper to justify than draft 4 knew**.
Data Governance measured that the event-supplied `declared` **cannot widen access**:
`route` short-circuits on `found.level == "sensitive"` at `classify.py:124`, before
the index comparison at `:127`, so G5's refusal is independent of `declared`
entirely and the comparison can only refuse, never permit. Exhaustively,
`declared ∈ {internal, confidential, sensitive}` are indistinguishable (25/25
golden, 1/11 probes) and `public` is strictly more restrictive. **The event field is
a self-restriction dial.** What stays unenforced is the *declaration*, not the
*refusal*, and the exposure is scoring integrity — which PR 2 closes.

A third path exists and is not taken: `pave policy generate` could emit a
`services.json` the handler reads — measured at five handler lines, an eight-line
generated file, **1861 passed, zero digests moved**, `snapshot --check` green with
no re-record. Declined because it changes what the deployed gateway does inside a
scaffolding milestone. **Recorded with its measurement in ADR-045 so the next reader
starts from the number.**

**No agent Lambda. No second committed service. No per-service L2/L5 lanes** (M08).
**No transport fix** — a source-skeleton parity test instead (PR 3). **No model
calls. Zero.** PR 2 re-scores *committed observations*, which is arithmetic over
files already in the tree.

**`GATED_CONSEQUENCES` does not move.** Draft 4 moved it into the registry, and
Tool Owner measured that as a **net de-keying**: `cedar.py` carries four seats today
(`platform-eng, security, tool-owner, legal-sp`) and `tools.yaml` carries two
(`legal-sp, tool-owner`), so the move drops **Security and Platform Engineering**
from the constant that decides whether any approval interlock exists. G9 is the
reason it stays: Security is precisely the seat that feels an interlock's pain.

The move's stated justification — *"a word in an unkeyed generator"*, *"measured
here at zero keys collected"* — was `07e8cd1`'s, before ADR-043 (#54). On `6af17d2`
that path collects four dispositions. **The entire premise for the move is a number
the tree no longer produces.**

Two further measurements retire it. Taken literally — a top-level key, since
`GATED_CONSEQUENCES` is a property of *classes* and not of tools — the registry's
top level stops being a list: **21 failed, 1840 passed** across seven files, and
`policy generate --check` emits a raw `TypeError` traceback out of the deploy-path
gate. Taken additively (`gated: true` per tool) it is **1861 passed** and clean —
and then un-declaring the field leaves
`test_every_gated_tool_in_the_registry_carries_a_forbid` **passing against a policy
set with zero forbid clauses**, because once "gated" is read from the file the loop
iterates, the loop is vacuous. Before the move the same attack was **15 failed
including that test**. The move converts an independent oracle into a
self-referential one, and the check it destroys is the one whose docstring reads
*"A tool promoted to `publish` without gaining a forbid would read as governed and
behave as ungoverned."*

**`legal-sp` stays on the Cedar and schema row.** Draft 4 dropped it. Security and
Tool Owner both measured the drop and both refuse it: `^platform/registry/tools\.yaml$`
does not match `tools/publish-highlight/schema.in.json`, the MER-AI-0001 disclosure
flag `ai_generated` lives at `schema.in.json:14` and travels into
`tools.contracts.json:228` inside the gateway bundle, and neither moves anywhere.
Today that path is BLOCKED without `legal-sp`; under draft 4's row it is SATISFIED.
Applying the row is **4 failed, 1857 passed**, and one of the four —
`test_editing_a_tool_schema_collects_the_tool_owner_and_legal_sp` — exists
specifically to prevent it. `tests/test_twokey_seats.py:238-241` records that
**Security recommended this seat set in round 2 and retracted it in round 3**;
draft 4 re-proposed the retracted recommendation and Security refused it a second
time in round 4.

**`README.md` does not go on a rule.** Draft 4's table put it there. Platform
Engineering measured that `pave/tests/test_twokey.py:32` is
`assert twokey.evaluate(["pave/cli.py", "README.md"], "") == []` — it names **two**
files, and draft 4 moved every guard out of the one on the left while putting a rule
on the one on the right. That assertion is this repository's only machine statement
that an ordinary contributor pays nothing to open a PR. PR 6's obligation is carried
by `docs/governance/recordings.json` plus the existing `check_readme` pins instead.

**`data-governance` does not enter `twokey.RULES`.** See PR 4 — once
`DECLARABLE_LEVELS` is a singleton the seat's own argument for dropping itself
becomes true, and the cost it avoids is real: Data Governance and Platform
Engineering both measured that the first rule naming the seat turns
`test_this_file_is_itself_on_a_rule_that_carries_securitys_key` red, and that the
obvious two-line fix is forbidden *by name* by
`test_the_seat_sets_adr043_decided_are_exactly_these`: *"Changing a rule's seat set
is a G9 decision — amend the ADR, do not edit this constant to match the code."*
The price of the seat is an ADR-043 amendment plus a **six-seat** rule on
`tests/test_twokey_seats.py`, so every future seat-set change would collect all six.

## Already closed — what draft 4 billed as work

Five seats measured these independently. All are on `6af17d2` today and **none is
M05's to build**:

- **G1's allowlist** (draft-4 finding 13): `pave/twokey.py:461` →
  `(security, platform-eng)` + ADR. The CLAUDE.md half is also stale —
  `CLAUDE.md:23-30` already names `tests/test_iam_assertions.py` and records
  `platform/infra/tests/` as the *former* pointer, citing ADR-043.
- **The test harness** (finding 15): `pave/twokey.py:539`, and the live rule is
  **five entry points wider** than draft 4's two-file row
  (`conftest.py|pyproject.toml|.pytest.ini|tox.ini|setup.cfg`). Writing the narrow
  version into a table invites a redraft that *shrinks* it.
- **The tool schemas** (finding 17): keyed at four seats **and red at three
  assertions** — planting the edit is 3 failed, 1858 passed. Its sub-clause about
  ADV-008 describes a defect ADR-043 already corrected (`ADR-043:409`).
- **The seat vocabulary assertion**: `tests/test_twokey_seats.py:143` already reads
  ROLES.md and asserts `used ⊆ known`.
- **The Cedar generator is not unkeyed**: four seats.

---

# What M05 builds — six PRs

The split is **CI hygiene, not scope reduction**: stacked PRs get zero CI here
(both workflows are `on: pull_request: branches: [main]` only), so each lands
independently green, cut from `main` **after** its predecessor merges. **A team
onboarding after M05 does one PR carrying five attestations** — see PR 5 — and the
six-PR structure is invisible to them.

**Stated rather than discovered: this milestone touches every key-holding seat in
the repository, and PR 3 alone touches most of them.** The split does not reduce the
attestation count and is not offered as doing so.

## PR 1 — the instruments nothing guarded

**LANDED as ADR-044 (#56, merged).** Items 1-9 below are draft 5's text. Two
corrections the build made: item 3's fix does close the attack and its assertion
is not vacuous, because it lands in the four-key file where sixteen assertions
still fire (`tests/test_cedar_policy.py:471-472` is the guard); and item 4's
hard-stop is converted to a named FAIL by the CLI rather than emitting the
traceback draft 5 used to condemn the registry move.

**This is first because every pin the later PRs propose is reachable through it at
zero keys.** AI Quality: *"the one thing I would build first, ahead of anything in
item 8."* Two seats found it independently and it is in none of draft 4's
twenty-one findings.

1. **`tests/test_contracts.py`, `tests/test_calibration_corpus.py` and
   `tests/test_judge.py` go on a rule** — `(ai-quality, platform-eng)`. All three
   return `NONE` from `twokey.evaluate` today. One diff — delete
   `test_golden_set_keeps_headroom` (the repo's **only** headroom check), flip both
   headroom cases to `false`, delete `test_a_disposition_is_all_or_nothing` — is
   **1859 passed, zero failures, zero keys**. `tests/test_contracts.py` is cited by
   four modules as "the file that pins X" (`adversarial.py:37,292`, `audit.py:256`,
   `guardrail.py:200`, `g4-semantics.yaml:66,488`). Verbatim the ADR-035 shape the
   repository already knows: thermometer protected, thermostat not.
2. **`tests/test_tool_loop.py` joins the same rule.** Security measured it as the
   second of the four files that catch a `POLICY_MECHANISMS` widening, also on no
   rule.
3. **`tests/test_contracts.py:71` imports its authority instead of duplicating it.**
   It holds `gated = {"publish", "irreversible"}` — a **sixth definition site** that
   grep for `GATED_CONSEQUENCES` does not find, and the file also holds the **only**
   assertion in the repository that a publish-class tool declares an approver.
   Measured: change that literal to `{"irreversible"}` and delete
   `approval: stepfn:editorial-approver` from the registry, regenerate →
   `policy generate --check` **exit 0**, the deployed policy set ships
   **"Declared approver: none"**, and the suite is **1861 passed**. Keys collected:
   `legal-sp, tool-owner`, from the registry line alone.
4. **The duplicate-registry-id hard-stop lands here, in `cedar.generate()` and
   `policy generate --check`** — the deploy path, not the manifest verifier.
   Measured: a second `- id: catalog-search` with `callers: [attacker-svc]`
   regenerates to 6 policies, `--check` **exit 0**, `attacker-svc` at
   `tools.cedar:54`, **1861 passed**, and **two keys, neither Security**. This is
   the same phantom-principal permit ADR-043 put four seats on, reachable through
   the registry at half the keys without touching the generator. It is not among
   draft 4's twenty-one. It goes in PR 1 because PR 3 lands registry edits and a
   verifier that only runs on a manifest never sees a registry-only diff.
5. **The surjectivity assertion**: every principal appearing in
   `platform/gateway/policy/tools.cedar` is a caller `platform/registry/tools.yaml`
   names. This is what closes draft-4 finding 14, which build item 12 did **not** —
   Security measured two lines added to `generate()` emitting
   `permit(principal == Service::"attacker-svc", …)` for every tool: the committed
   set ships it including on `publish-highlight`, `--check` exits **0**, suite
   **1861 passed**. A manifest-side check verifying a service's *own* permits never
   enumerates a principal no manifest names.

**Seats:** `ai-quality, platform-eng` (the new rule), `platform-eng, security,
tool-owner, legal-sp` (`cedar.py`), `ai-quality, security, platform-eng`
(`test_twokey_seats.py` pin edits).

## PR 2 — what a block has to have done — **SPLIT OUT OF M05**

**Draft 5 specified this and round 5 proved it cannot be built as specified.** The
premise is unchanged and is still the sharpest finding in the document: *a service
that answers nothing outscores every system this repository has built.* Under
identical blanket denial of 11/11 probes,

| mechanism | adversarial score |
|---|---|
| `classification` | 10/11 |
| `iam` | 10/11 |
| `policy` | **11/11** |

against the best honest arm at **6/10** — and 6/10 is the number, not the 7/10
draft 5 quoted three times, because `expected_passed` and `recorded_passed` are
different fields and the predictions never said which they meant.

**Why it is not buildable, in one sentence each.** These are round 5's findings,
kept because each is a reason and not an obstacle:

- **Predictions 12 and 13 cannot both hold.** A lenient predicate leaves the
  blanket-denial `policy` arm at 11/11, which is prediction 12 failing. A strict one
  takes the recorded arms to `m01` 5/10 and `m04` 6/10, which is prediction 13
  failing. There is no predicate that satisfies both.
- **The field the predicate needs is in no committed observation.** Not one of the
  50 recorded observations carries `classification`, and the audit records are not
  in this repository. Re-deriving the arms means a lake fetch, which is a network
  operation and breaks G8.
- **The `policy` case is not closable by any per-record predicate at all.** Blanket
  denial is a property of the *corpus of responses*, not of any one record.
  `quality/adversarial/probe-controls.yaml` is the corpus-level instrument that
  could close it, and draft 5 mentions that file **zero times**.
- **Draft 5's item 7 named the wrong store.** Observations do not persist to
  `evals/history/*.json`; they live in `milestones/<TAG>/probes-run.json`, which is
  worse — it already carries `model_text` verbatim in a public repository.
- **Item 6's register-first ordering is unbuildable**, and prediction 13's remedy is
  refused by the machinery by name.

**What splitting it out costs, stated rather than buried.** G4's *"and logged"* half
still credits a refusal without examining what refused, so **the milestone ships with
its own headline finding open**. That is a worse outcome than closing it and is a
better outcome than shipping a predicate that cannot be right. The three decisions
that unblock it are 1-3 under *Decisions this draft does not make*.

**Not deferred by silence.** M05's journal and the claim-1 footnote must both say
this, and `docs/M05-round5-findings.md` holds the complete measurement.

## PR 3 — the keys, the sentinels, the registry

**LANDED as ADR-048 (#57, merged).** Item 13's `recap-agent` removal turned out to
be a fifth scope cut needing its own ADR, and it got one: the entry was the only
foundation for the cross-tool negative control, and removing it left that test
**passing at 1881 with zero pairs constructible**. Item 13's stated key cost was
also wrong - the minimal commit is **two** keys, not four; both generated
artifacts are on no rule.

10. **Two-key rules with named seats**, the table below, plus a **seat-set test**
    and a **pairwise test over the pair list stated in this document**.
11. **The 45 `m05` sentinels.** Draft 4 said 44 and Platform Engineering confirmed
    that count three ways — 36 `m05` + 7 `M05` in `test_history_append_only.py`,
    1 in `test_demo_recordings.py:91`. **There is a forty-fifth and it is not a
    string literal**, so no grep in four rounds found it:
    `tests/test_history_append_only.py:624` is
    `(scratch / "milestones" / "M05").mkdir()` with no `exist_ok`. The moment
    `milestones/M05/` exists on disk that test raises `FileExistsError` — measured
    at **1 failed, 121 passed** from writing one file into that directory — and the
    failure names an arm-scoping lane, not a directory, so the next reader debugs
    the wrong thing. **PR 6 cannot record its evidence without tripping it.**
    Therefore: forty-three literals move to `mzz`, **one repoints to `m06`**
    (`test_a_published_number_with_no_entry_behind_it_is_red`, which reads the live
    README table and needs a tag with a row — `README.md:41` has one), the
    forty-fifth gains `exist_ok=True`, and **the migration audits `mkdir`, `is_dir`,
    `exists` and `iterdir` against `milestones/`**, because grep for the literal
    cannot find that class of sentinel.
    **The sentinel is `mzz` / `Mzz`, not `MZZ`.** `pave/history.py:563`
    `_milestone_dir` uppercases **only the first character** — `m05 → M05` works by
    luck because the rest are digits. The naive find-and-replace a reasonable
    implementer would run is red at
    `test_a_row_citing_another_milestones_evidence_is_red`. With `Mzz`, Platform
    Engineering ran the whole migration: **1861 passed.**
12. **The vacuity guard is restructured, and its horizon is stated.** It has **two**
    literals, not one — `milestone_is_closed("M04") is True` and `("M05") is False`
    — and only the second is among the 45, while the first is load-bearing. The
    restructure (read the live progression rows, assert the returned set is exactly
    `{True, False}`) is green at **1861**, but it is unsatisfiable when M10 closes
    and no row returns `False`. That is **one milestone later than the literal it
    replaces, not "every future close"**, which draft 4 asserted. Stated as a
    horizon rather than asserted away.
13. **`recap-agent` leaves the registry and the cross-tool negative control is
    re-founded on a synthetic registry in the same commit.** The claim is confirmed
    exactly: with `callers: [highlights-agent]`, distinct callers is 1,
    **zero cross-tool negative pairs are constructible**, and both
    `test_an_uninvited_caller_is_denied_by_policy` and
    `test_an_uninvited_caller_is_denied` **pass** — the tests no longer test their
    own names. **There are eleven sites in eight files**, not draft 4's three:
    `tools.yaml:12`, `handler.py:61`, `tools/catalog-search/README.md:13`,
    `tests/test_toolplane.py:192` (the control that dies),
    `tests/test_tool_loop.py:218` (docstring only — its principal is
    `ledger-service`, so it survives), `docs/governance/demo-script.md:49` **and
    `:89`**, **`platform/gateway/policy/tools.cedar:22`** (generated — regenerate in
    the same commit or the drift gate is red, which pushes this item into
    `cedar.py`'s four-seat rule), and **`docs/adr/ADR-023:49, 51, 77-78`**, whose
    worked example *is* `recap-agent` and whose lines 49–51 state a live fact that
    becomes false. **Nothing pins any prose site** — leaving three of them stale
    reports 1861 passed — so "corrected with them" is a promise no check enforces
    and the pairwise test below covers what it can.
14. **The source-skeleton parity test**, covering both transport copies. Finding 20
    reproduces at full strength: rewording `gateway_client.py:124`'s `user_turn`
    alone is **1 file changed, 1861 passed, zero keys**, because
    `test_gateway_run_parity.py:64` is built on `module_constants()` walking
    module-level `ast.Assign` and **structurally cannot see a `def`**. This is a G4
    exposure and not only a comparability one: `user_turn` composes the wire text of
    every governed adversarial observation, and `instrument_digests`
    (`adversarial.py:808`) does not cover the transport.
    **The technique, stated:** collect every `ast.JoinedStr` in both files, render
    constant segments with interpolations elided, and assert the wire-text skeleton
    appears identically in both — **locating by content, never by function name**,
    because the two files share exactly one function name and it is the wrong one
    (`build_prompt`), while the control inlines the text in `ask`
    (`run_baseline.py:91-95`). Measured, the skeletons are byte-identical:
    `['Viewer plan={?} dma={?}. Evaluation clock {?}.\n{?}']` in both.
    **Its failure message must state that editing the ungoverned control is not the
    fix.** `run_baseline.py` is also zero keys, so it is the cheapest way to green a
    red parity test, and CLAUDE.md's baseline-honesty rule forbids it.
    **The file is `tests/test_transport_parity.py` and it is added to the
    enumerated `tests/(…)` alternation by name.** Three seats independently measured
    that this rule is a **five-filename alternation, not a directory prefix**, so a
    new file lands unkeyed wherever it is put. Note Security holds no key on
    `pave/twokey.py` itself (`ai-quality, platform-eng`), so this costs a
    `twokey.py` diff plus a five-seat pin edit and that is the price of the home.

## PR 4 — the verifier

**LANDED as two PRs. PR 4a is ADR-045 (#58, merged); PR 4b is ADR-046 (built,
unmerged).** Items 15-29 below are draft 5's text and are kept as written. Where
the build differs, the difference is in *Where the built thing differs from
draft 5* above and in the ADR - **not edited into the item**. Item 27's
pack-level `provenance` header is the largest such difference and was
**withdrawn**: 47 failed, and ADR-045 decision 4 records why.

15. **`pave/manifest.py`, mechanism only**, importing every criterion from a path
    carrying its content owner's key.
16. **`pave/verify.py` holds the `pave verify` invocation and nothing else.**
    Draft 4 put it in `pave/gate.py`. Platform Engineering confirmed that works
    mechanically (50 passed, `test_ordinary_pr_is_not_gated` intact) and refused it
    anyway: `gate.py`'s own docstring line 25 draws the seat boundary the row would
    erase — *"Platform Engineering (mechanism only — the criteria that produce a
    FAIL are AI Quality's)"* — and the row leaves `pave/tests/test_gate.py`, 21.7 KB
    holding the entire pin on the exit-code contract, at **zero keys** while the
    file it pins takes three. That is ADR-043 decision 1's "weakened together or not
    at all," arriving again. A file holding one invocation can be gated without
    teaching anyone to attest past a rule they did not read.
17. **It is an assertion, not a lane.** `tests/test_manifest_verify.py` reaches the
    gate through `verdict-contract.json`, which `pave check` (`pave/cli.py:1174`)
    already emits. **No `quality-gate.yml` edit, no new verdict, no attestation
    cost.** Draft 4 said "the lane" and named no CI path at all — and
    `.github/workflows/quality-gate.yml` decides on a **closed** `--verdicts` list,
    so a verdict not on it is not "absent and blocking", it is not consulted. The
    free path is what this repository already does for G3 and G7 and what CLAUDE.md's
    style rule prefers: *"deterministic assertions over judge assertions wherever a
    deterministic one can express the requirement."*
18. **A duplicate-key-rejecting YAML loader**, PyYAML only, no new dependency.
19. **`DECLARABLE_LEVELS = ("internal",)`, in `pave/floors.py`.**
    The relocation out of `classify.py` is confirmed correct — one line appended to
    `classify.py` is **15 failed, 1846 passed** (all `test_adversarial_entry.py`,
    because it moves `classify_sha256`); the same line in `pave/floors.py` is
    **1861 passed**.
    The *contents* are Data Governance's round-4 correction. Draft 4 proposed
    `("public", "internal")` on the reasoning that no *detection* produces
    `confidential`. Both halves of that verified — the only `Classification(...)`
    literals `classify_request` constructs are `internal` and `sensitive`, and
    `route` does apply `confidential` by index at `classify.py:127` — **but the same
    criterion condemns `public`, which no detection produces either.** Measured over
    all 25 committed goldens and all 11 probes:

    | declared | golden allowed | probes denied pre-invoke |
    |---|---|---|
    | `public` | **0/25** | 11/11 |
    | `internal` | 25/25 | 1/11 |
    | `confidential` | 25/25 | 1/11 |
    | `sensitive` | 25/25 | 1/11 |

    `confidential` is behaviourally identical to `internal`; **`public` is the
    outage**. Draft 4 refused the no-op and admitted the outage. `public` re-enters
    the vocabulary the day `classify_request` can return it — a scope cut, recorded
    in **ADR-046** per CLAUDE.md rather than left as a silent simplification.
20. **The guard on that vocabulary is equality plus behaviour, never subset.**
    Draft 4's `DECLARABLE_LEVELS ⊆ classify.LEVELS` returns PASS for the empty
    tuple — a vocabulary that refuses every manifest — for `("public",)`, and for
    the full pre-refusal vocabulary including both levels it exists to refuse. It
    witnesses nothing. Instead, hermetic and reading `classify.py` without editing
    it: assert **equality** against the enumerated set; assert that for every
    `L in DECLARABLE_LEVELS`, `route(L, <an ordinary request>).allowed is True` —
    the assertion that excludes `public`, which subset containment can never make;
    and assert that for every `L`, `route(L, <a request for subscriber personal
    data>).allowed is False`, pinning G5 across the whole vocabulary. Nothing on
    `main` pins either level's behaviour today: `tests/test_gateway_core.py` has
    exactly four `route` tests and none names `public` or `confidential`.
21. **The manifest declares a tool the registry grants it.** This is the hole
    neither draft 4 nor `main` closes, and it is the one a developer meets first:
    revoking `highlights-agent`'s grant on `entitlement-check` and regenerating
    cleanly leaves the manifest declaring `- id: entitlement-check@^0` with nothing
    red. `tests/test_contracts.py:83` does `entry["id"].split("@")[0]` and checks
    only that the id exists in the registry. Draft 4's *"the tool set from the
    registry"* is satisfied by that existing check. **The verifier asserts
    `manifest.service ∈ registry[tool].callers` for every declared tool, and the
    reverse for every grant.**
22. **`@range` and `semver:` are decorative, and the spec says so instead of
    theorising about them.** Draft 4's prediction 14 refused `^0.0.x` as "a range
    this repo does not evaluate." Tool Owner measured that the same is true of every
    form: `grep -rn '"semver"' --include=*.py .` returns **no matches**, the only
    site parsing `@` throws the range away, and a manifest reading
    `catalog-search@not-a-range-at-all` with `semver:` **deleted from every registry
    entry** is `--check` exit 0 and **1861 passed**. Worse, the refusal singled out
    the *safe* form: under the 0.x convention every minor bump is breaking, so `^0`
    is the **widest** caret and `^0.0.x` the **tightest** — and the reference
    manifest pins all three tools at `^0`. **M05 builds no range evaluator and adds
    no dependency** (CLAUDE.md would require an ADR line for one). The verifier
    checks the id and states in its own output that the range is not evaluated.
    Building one is M06's, with the registry's `semver:` field, or the field goes.
23. **The floors, with their ratchets — five pins, not four.**
    - **`PLATFORM_EVAL_MIN_CASES` gets the pin draft 4 forgot.** AI Quality built
      draft 4's exact four pins and then moved this floor **20 → 0**:
      **1867 passed, zero failures.** That is the milestone's own opening finding
      (`gates.eval_min_cases: 20 → 0` green) reproduced one level up, inside the file
      M05 builds to fix it, and `pave/floors.py`'s own docstring is the rule broken:
      *"A floor is only half a floor without its ratchet."* Two-sided: tied to
      `smallest_pack_that_can_hold_headroom()` below and the smallest verified pack
      above.
    - **`HEADROOM_BAND`** keeps its literal pin, which fires (1 failed) when the
      lower bound is removed.
    - **`smallest_pack_that_can_hold_headroom()`** keeps its return pin including two
      derived cases; `return 10` fires it, so draft 4's *"`return <constant>` cannot
      satisfy it"* **holds**. It is structurally blind to the band's lower bound, and
      the `PLATFORM_EVAL_MIN_CASES` ratchet is what gives it a consumer.
    - **The band must be shown APPLIED, not imported.** Draft 4's pin 3 asserted
      `tests/test_contracts.py` *imports* the band rather than duplicating it.
      Measured: import it, replace the band assertion with `assert ratio >= 0.0`,
      flip both headroom cases to `false` — **1864 passed**. An import line satisfies
      a source assertion that looks for an import line. The pin calls the headroom
      check against a synthetic pack that violates the band and requires it to raise.
    - **`COLLECTED_FLOOR` is two-sided, and `>=` is the half that works.** Deleting
      `tests/test_calibration_owe.py` (8 tests): no floor → 1853 passed;
      `n <= COLLECTED_FLOOR`, the `G4_CASE_FLOOR` shape draft 4 cites → **1856
      passed, zero failures**; `n >= COLLECTED_FLOOR` → **1 failed**, *"8 test(s)
      vanished"*.
24. **`COLLECTED_FLOOR` is justified as the deleted-test-file closer and must not be
    sold as a harness defence.** Draft 4's residual section is right that a count
    cannot see a harness that lies — reproduced: eight lines of
    `pytest_runtest_makereport` in `tests/conftest.py` plus a second G1 role prefix
    reports **1861 passed**, the exact honest count, with the G1 pin genuinely
    failing. Adding a deleted file and a failing headroom pin under the same
    hookwrapper is **1856 passed**. But draft 4 then files "a deleted test file is
    invisible to pytest" as a standing residual three paragraphs from the mechanism
    that closes it: `rm tests/test_adversarial_scoring.py` is **1801 passed** with
    `pave check` PASS at exit 0 today, and 1801 is below any floor set at 1861.
    **What the floor does not close is deletion plus padding — a count sees
    arithmetic, not identity** — and that is the residual, correctly stated.
    Also worth naming: `collect_ignore` on three files is **1746 passed** with
    `pave check` PASS at exit 0, and one of them,
    `tests/test_adversarial_scoring.py`, is what `evals/comparators.json:40` names as
    the only live protection on `CEDAR_MECHANISMS` and G4's `and logged` half. One
    line removes it and the checker says PASS. `tests/conftest.py` already carries
    its rule (ADR-043); the residual is that the key makes this **collectable, not
    red**, and the deciding instance is a workflow step per ADR-042 decision 3.
25. **`expect_near_threshold` is accepted at the case top level.** Two lines at
    `tests/test_contracts.py:130` reading both locations, plus the flag moved on
    `headroom-005`: **1861 passed**, band checks intact. Justified on CLAUDE.md's
    deterministic-first style rule alone.
    **Draft 4's justification for it was false and is withdrawn.** It claimed a
    headroom case needs a judge block "which needs a rubric". Removing
    `rubric: quality/judge/rubric-sports.md` from `headroom-005` with axes kept is
    **1861 passed** — `tests/test_contracts.py:113-115` guards the rubric behind
    `if rubric:`. What is load-bearing is **axes**, and that check is
    highlights-specific. For a genuinely new service neither is checked at all:
    `judge: { expect_near_threshold: true }` alone is green. The real cost of
    today's location is a `judge:` block that invokes no judge — smaller and
    different from the claim, and over-stating an exposure is what leads to
    over-keying.
26. **A closed top-level case-key vocabulary ships with it.** There is none for the
    golden set today (`KNOWN_CASE_KEYS` at `evals/adversarial.py:659` covers the
    *adversarial* corpus only). At today's N=25 a typo (`expect_near_threshhold`) is
    red. **At `PLATFORM_EVAL_MIN_CASES = 20` the legal near-counts are exactly
    {1, 2} and both sit on a band boundary** (1/20 = 0.05, 2/20 = 0.10, both exact
    in IEEE double), so a 20-case pack that loses one to a typo lands at 1/20 and is
    **still legal**. The typo is silently absorbed at precisely the pack size the
    platform floor mandates. `test_no_case_uses_an_undocumented_assert`'s docstring
    already names this failure mode: *"the harness skips what it does not recognise,
    so the case reports PASS while checking nothing."*
27. **The floor counts cases a seat stood behind, at pack level.** Draft 4 put
    `disposed: true` and `curated_by` on every case. Its own cited precedents are
    **file-level**: `quality/judge/calibration/labels.json:3-9` is one
    `provenance` header for the whole corpus, and both
    `tests/test_calibration_corpus.py:265-271` and `run_judge.py:99` read
    `labels["provenance"]["disposed"]`. Per case it is 40 identical lines across a
    20-case pack. And measured, the reference pack — the only committed pack in the
    repository, the one this verifier must be green against — carries
    **`disposed` on 0 cases and `curated_by` on 0 cases against a floor of 20**,
    which draft 4 never mentions migrating.
    So: a **pack-level** `provenance: { disposed: true, curated_by: <seat> }` header,
    with `author: pave-template` per case as the scaffold marker, and the count is
    over cases whose `provenance.author != "pave-template"` — a field all 25 cases
    already carry. Two controls already back it: `services/*/evals/` is two-key
    `ai-quality`, so a template pack cannot land without written rationale.
28. **The headroom denominator is stated: the disposed set.** Under a per-row rule
    with the ratio taken over all rows, a compliant pack (20 disposed, 1 near = 5%)
    goes **red** at 1/25 = 4% the moment a team scaffolds five more rows, because
    scaffolded rows never carry `expect_near_threshold` and only push the ratio
    toward the low-end failure. Unstated, `pave new` emits a scaffold that fails its
    own headroom gate as the team fills it in.
29. **Every malformed input named below is a named FAIL with no traceback.** Draft 4
    said "every" in one place and pinned "four" in another. Service Team enumerated
    thirteen a real team produces. **The table in "The lane's refusals" below is the
    commitment**; anything not in it is deferred by name, not by silence.

**Seats:** `ai-quality, security, platform-eng` on
`pave/manifest.py`, `pave/floors.py`, `pave/verify.py`, `tests/test_manifest_verify.py`.

## PR 5 — the template and the command

30. **`templates/agent-tools/`, whose rendered file list is stated here.** Draft 3
    was killed for omitting it; draft 4 asserted the spec stated it and still
    omitted it, and **three seats found that independently.** The reference service
    is 14 files; nine are M01–M04 measurement harnesses no scaffold should emit
    (`inspect_context.py`, `run_judge.py`, `run_phrasings.py`,
    `run_probes_via_gateway.py`, `run_split.py`, `run_via_gateway.py`,
    `run_with_tools.py`, `topic_baseline.py`, `verify_guardrail_pin.py`).

    **`pave new <service>` renders exactly five files, and nothing else:**

    | rendered path | source | notes |
    |---|---|---|
    | `services/<svc>/pave.manifest.yaml` | `templates/agent-tools/pave.manifest.yaml.tmpl` | `service`, `brand`, `owners` interpolated; `classification: internal` fixed |
    | `services/<svc>/gateway_client.py` | `templates/agent-tools/gateway_client.py.tmpl` | verbatim but for the service name |
    | `services/<svc>/evals/answer.schema.json` | `templates/agent-tools/evals/answer.schema.json` | verbatim, 40 lines |
    | `services/<svc>/evals/golden/cases.yaml` | `templates/agent-tools/evals/golden/cases.yaml.tmpl` | scaffold pack, `author: pave-template` per case |
    | `services/<svc>/evals/golden/README.md` | `templates/agent-tools/evals/golden/README.md` | verbatim, 174 lines — the assert vocabulary |

    **It renders no `run_probes*.py`.** Draft 4's implied scaffold did, and that
    file is on an existing `(security, platform-eng)` rule
    (`^services/[^/]+/run_probes(_via_gateway)?\.py$`), so the scaffold would have
    handed every team a file it could never edit alone. A service that never runs
    adversarial probes needs none, and M08 is where per-service lanes arrive.

    **The pair list, as `(template, reference, normalisation)` triples**, which is
    what the pairwise test iterates:

    | template | reference | normalisation |
    |---|---|---|
    | `pave.manifest.yaml.tmpl` | `services/highlights-agent/pave.manifest.yaml` | key set and nesting only; **values not compared**, and **`gates.budgets` keys are compared and must not be erased** |
    | `gateway_client.py.tmpl` | `services/highlights-agent/gateway_client.py` | `ast.JoinedStr` skeletons, interpolations elided — the same technique as PR 3's parity test |
    | `evals/answer.schema.json` | `services/highlights-agent/evals/answer.schema.json` | byte-identical |
    | `evals/golden/cases.yaml.tmpl` | `services/highlights-agent/evals/golden/cases.yaml` | top-level key set of each case, against the closed vocabulary from item 26 |
    | `evals/golden/README.md` | `services/highlights-agent/evals/golden/README.md` | byte-identical |

31. **`pave new` is creates-only, and the spec states the second command it cannot
    run.** Draft 4 called it creates-only and stopped. Measured: adding the caller
    to the registry and *not* regenerating is **3 failed, 1858 passed**, and of the
    three messages only `test_cedar_policy.py:50` names the command to run. A
    first-time onboarder meets three red checks of which one explains itself.
32. **The printed registry block anchors on `- id:`, never on a line number.**
    Draft 4 said "names the tool id **and the line**". A line number shifts when any
    tool is added — and **after item 13 removes `recap-agent`, all three `callers:`
    lines are byte-identical** (today `:12` differs), so quoting the line content is
    ambiguous too. Item 13 removes the only thing that distinguished one of them.
    The load-bearing half is the refusal, because a seat following the vaguer
    instruction **over-granted itself the publish-class tool during this review**:

    ```
    Register <service> as a caller of each tool it needs.

    In platform/registry/tools.yaml, find the entry beginning `- id: catalog-search`
    and add <service> to THAT entry's callers list:

        - id: catalog-search
          ...
          callers: [highlights-agent, <service>]

    There are three `callers:` lines in that file and they read alike. Match on the
    `- id:` above the line, never on the line itself.

    Do NOT add yourself under `- id: publish-highlight`. Its consequence class is
    `publish`: adding a caller there grants your service a gated tool, and that edit
    takes tool-owner + legal-sp dispositions. It is not a scaffolding step.

    Then regenerate the policy the registry decides, and commit both files:

        python -m pave.cli policy generate
        git add platform/gateway/policy/tools.cedar \
                platform/gateway/policy/tools.contracts.json

    Skip this and `make check` is red with 3 failures, only one of which
    tells you this was the cause.

    Your PR will require FIVE seat attestations: ai-quality, tool-owner,
    security, platform-eng, legal-sp. See docs/governance/ROLES.md.
    ```
33. **The `pave new` stub's replacement text is stated.** Today
    `pave/cli.py:1441-1443` advertises `gate.yml`, CODEOWNERS, "wire SDK" and
    "enable tracing". M05 builds no per-service lane, ADR-013 records that CODEOWNERS
    collects nothing here, and writing to `.github/CODEOWNERS` contradicts
    creates-only. The replacement names the five rendered files and the two manual
    steps.
34. **The demo script's service name is reconciled.** `docs/governance/demo-script.md:49`
    scaffolds `recap-agent` and `:89` has it going red — while item 13 removes
    `recap-agent` from the registry. Scaffolding a name the registry no longer knows
    is correct and is what the demo wants; the script is corrected to say so
    explicitly, so the next reader does not read it as a contradiction.

## PR 6 — the close

35. Journal, progression row, claim-1 footnote, recordings, and the `Makefile`
    guard.
36. **`make core` becomes one recipe line, with the `cd` draft 4 dropped:**
    `cd platform/infra && pave verify --all && cdk deploy --all`. Platform
    Engineering measured the premise on GNU Make 4.3 and it **holds**: with two
    recipe lines, `make -i` prints the deploy and exits 0; with `&&` on one line the
    deploy never runs. Draft 4's literal omitted the `cd`, which would have run
    `cdk` from the repository root. **And the guarded target now exits 0 under
    `make -i` having run neither the gate nor the deploy** — an unsupported
    invocation whose exit code means nothing, stated here because a silent success is
    the `|| echo` shape the Makefile's own header records this repository shipping
    for its entire life. This does **not** make `manifest_signature` true and must
    not be sold as such; that is ADR-045's subject.
37. **Claim 1 is marked INCOMPLETE with two footnoted reasons**: no deployed agent,
    and an authorship burden **well over an hour** against a claim of thirty minutes.
    Draft 4 said "roughly an hour" and Service Team measured that as too **low**:
    510 lines over 25 cases (~15.6 content lines each), **138 asserts** (mean 5.5),
    six top-level keys per case with 12 of 25 adding `trajectory`, 18 of 25
    requiring memorised catalog ids, and a ~180-line assert vocabulary — so twenty
    cases is ~310 content lines and ~110 asserts. The decisive number is in the
    pack's own README: **4 of the 25 starter cases** were written with negative
    substring bans a *correct* answer trips, by the author of the vocabulary. **A
    16% authoring-defect rate, each defect presenting first as a platform bug.**
    Understating this flatters the platform exactly as drafts 1–3 did.
38. **`docs/governance/recordings.json` goes on a rule** — `(platform-eng,
    ai-quality)`. Acts 0, 1 and 2 are owed by M05. **Act 1 cannot be recorded until
    PR 5 lands**, so this is the last step of the milestone, and if the acts are
    re-deferred that is a decision requiring a stated reason longer than 60
    characters, which that file's own test enforces.

---

## Seat sets, named

Rows marked **LANDED** are on `6af17d2` already and are listed so no reader
re-derives them. Rows marked **new** are PR 1's and PR 3's work.

| path | seats | note |
|---|---|---|
| `tests/(test_contracts\|test_calibration_corpus\|test_judge\|test_tool_loop)\.py` | `ai-quality`, `platform-eng` | **new, PR 1.** The largest measured exposure in round 4 and in none of draft 4's twenty-one: 1859 passed, zero keys, with the only headroom check and the only approver assertion deleted |
| `services/*/pave.manifest.yaml` | `ai-quality`, `tool-owner` | **new.** `data-governance` is not here because item 19 makes `classification` a singleton — its own seat's argument, now true |
| `tests/test_budget_derivation.py` | `ai-quality`, `platform-eng` | **new**, split from the row above because the file's own docstring names *"AI Quality (the ceilings) · Platform Engineering (the loop bound)"*. Draft 4 paired it with `tool-owner`, contradicting the file. It closes a stated-and-absent protection: `:124` asserts in prose that `gates.budgets` is two-key while `twokey.evaluate` returns NONE |
| `templates/agent-tools/**` | `platform-eng`, `ai-quality`, `tool-owner`, `security` | **new.** A template edit sets the default floor, tool set and wire text for every service that does not exist yet. `data-governance` is not here for the same reason as the manifest row, and because draft 4 keyed the template while un-keying the instance it renders — the asymmetry it condemns in draft 3 |
| `pave/manifest.py`, `pave/floors.py`, `pave/verify.py`, `tests/test_manifest_verify.py` | `ai-quality`, `security`, `platform-eng` | **new.** Valid only because the verifier holds mechanism and imports every criterion |
| `tests/test_transport_parity.py` | `ai-quality`, `security`, `platform-eng` | **new**, added to the enumerated `tests/(…)` alternation by name |
| `Makefile` | `platform-eng`, `ai-quality` | **new.** Justified on `evals:` and `adversarial:` — the two `--record` entrypoints and the `OBSERVATIONS` guard, an append-only-history control — **not** on `core:`, which is a deploy gate whose pain AI Quality does not feel. Draft 4 cited `core:` |
| `docs/governance/recordings.json` | `platform-eng`, `ai-quality` | **new, PR 6.** `README.md` is **not** on this row — it breaks `test_ordinary_pr_is_not_gated` |
| `platform/gateway/core/audit.py` | `platform-eng`, `security`, **+`ai-quality`** | **amended, PR 2**, justified on `observation_from_record` being the G4 observation the scorer reads and PR 2's named handover. Draft 4's stated reason — *"`POLICY_MECHANISMS` is invisible to every pin"* — is **false**: widening it is 20–21 failed across four files plus the instrument digest, it is pinned literally at `test_contracts.py:395`, and it sits inside `semantics_sha256`. This is a **third** key, and it is only worth having once PR 1 keys the files that catch it |
| `platform/gateway/core/cedar.py`, `tests/test_cedar_policy.py`, `tools/*/schema.(in\|out).json` | `platform-eng`, `security`, `tool-owner`, `legal-sp` | **LANDED, unchanged.** Draft 4 dropped `legal-sp`; two seats measured 4 failed and refused |
| `pave/infra.py`, `tests/test_iam_assertions.py` | `security`, `platform-eng`, ADR | **LANDED** (`twokey.py:461`) |
| `(.*/)?conftest\.py`, `pyproject.toml`, `.pytest.ini`, `tox.ini`, `setup.cfg` | `platform-eng`, `security` | **LANDED** (`twokey.py:539`) — five entry points, wider than draft 4's two-file row |
| `platform/registry/tools.yaml` | `tool-owner`, `legal-sp` | **LANDED, unchanged.** `GATED_CONSEQUENCES` does not move here |

**No `services/*/gateway_client.py` rule.** The parity test carries it, and the
zero-cost claim is **confirmed**: `twokey.evaluate(["services/highlights-agent/gateway_client.py"], "")`
returns `[]`. Draft 3 took an ordinary edit to a team's own transport client from
0 keys to 2; draft 4 removed that cost rather than moving it, and this draft keeps
it removed.

## The lane's refusals — **as built, fourteen rows**

The commitment from item 29. Each row is a named FAIL with no traceback, and each is
**produced by code with a violating input beside it**: `manifest.ROWS` holds the
table, `tests/test_manifest_verify.py`'s `PRODUCERS` holds one input per row, and the
two sets are asserted equal **in both directions** — so a row with no producer is red
and a producer for a row nobody wrote down is red. `MUST_NAME` turns the third column
into assertions.

Two rows differ from draft 5's thirteen. Both are marked.

| # | input | message names |
|---|---|---|
| 1 | duplicate YAML key | the key and both line numbers |
| 2 | tool id not in registry | the id and the registry path |
| 3 | **declared tool the service is not a `caller:` of** | the tool, the service, and the `- id:` block to edit |
| 4 | **grant with no matching declaration** | the tool and the manifest path. *Fired on the only committed manifest* |
| 5 | missing required field | the field and **what reads it** |
| 6 | `classification` outside `DECLARABLE_LEVELS` | the value, the legal set, and **for `public`: that it serves 0 of 25 — never phrased as a mitigation**, because the manifest value is unenforced and the shape is produced by the request |
| 7 | `service` ≠ directory name | both |
| 8 | pack below the floor | disposed count, floor, and that scaffolded rows do not count |
| 9 | pack outside the headroom band | ratio, band, denominator |
| 10 | **CHANGED. `gates.eval_min_cases` below the platform floor** | the declared value, the platform floor, and that a service may demand more of itself and not less. *Draft 5's row 10 was "undisposed pack header / the missing `curated_by`" and is **withdrawn**: ADR-045 measured the pack-level header as a 47-failure migration and replaced it with per-case `provenance.author`, so that row would have failed the reference pack on day one. The finding this row now covers — `20 → 0` green — is the milestone's own opening finding, and draft 5's table omitted it* |
| 11 | unknown top-level case key | the key and the closed vocabulary |
| 12 | `gates.budgets` missing a key | the key |
| 13 | duplicated registry id | two producers: `cedar.generate()` at `policy generate --check` (**PR 1**), and `manifest.grants()`, because the verifier reads `callers:` to decide rows 3 and 4 and a registry with two entries for one id has two answers |
| 14 | **NEW. `brand` outside the set the judge can score** | the value, the supported set, and that a brand is supported when the rubric carries its `brand_tone:` axis. *Draft 5 left `brand` enforced by a `print()` in a creates-only command; `meridian-sports → meridian-news` measured **1889 passed*** |

**Deferred by name, not by silence** — and printed by the command on **every** run,
including green ones, because a tool that lists its limits only when it fails is a
tool whose limits are read by nobody who passed:

1. **range evaluation** (item 22),
2. **brand-with-no-pack** (item 39),
3. **whether the declaration is honest** — `classification` is a declaration the
   repository refuses to merge when it is outside the vocabulary, and nothing more.

## The second brand, stated

`docs/governance/demo-script.md:49` scaffolds a **news** service, and the repository
can only judge **sports**. The chain verifies: the only rubric on disk is
`rubric-sports.md`, `evals/judge.py:46` hard-codes it, and `judge.py:110-111` raises
unless `brand_tone:meridian-sports` is present.

**Draft 4 offered item 25 as the fix and it fixes the wrong half.** The blocker is
the **fixture**, not the rubric: `data/catalog.json` holds two `meridian-news`
titles, neither with an event, a start time, or a non-`base` entitlement, and 18 of
25 committed cases lean on `must_cite`. Adding one fictional news title is
**16 failed, 1845 passed**, because the catalog is embedded model-facing in the
judge prompt (`judge.py:130`) and digested into `quality/judge/frozen.json` — so a
second brand runs through a re-freeze (two-key `ai-quality`) and superseding history
entries.

39. **M05 scaffolds a sports service.** `--brand` accepts `meridian-sports` until
    M08, and `pave new` says so in its own output rather than letting a team
    discover the other sixteen failures. A deterministic-only pack is a real green
    path (item 25); a *news* pack is not, and that is a fixture decision owned by
    AI Quality and Legal/S&P, not a scaffolding one.

## The ADRs M05 writes — **and the numbers draft 5 got wrong**

Draft 4 made five scope cuts, named **zero** ADR numbers, and used the definite
article twice for a document with no number. CLAUDE.md:12 forbids exactly that, and
`test_citing_a_nonexistent_adr_blocks` means an unwritten ADR cannot be attested
against.

**Draft 5 named four numbers and three of them went elsewhere.** This is recorded
rather than corrected in place, because an ADR number is a citation and a spec that
silently renumbers its own is the drift ADR-037 is about.

| draft 5 said | what was written | why |
|---|---|---|
| ADR-044 — *what a block has to have done* (PR 2) | **ADR-044 — the instruments that measured and were guarded by nothing** (PR 1) | PR 1 landed first and needed the number; PR 2 was then split out and holds **no number yet** |
| ADR-045 — *the deploy-verification cut* | **ADR-045 — the criteria a manifest is verified against** (PR 4a) | The verifier split into criteria and mechanism, and the criteria half landed first. The deploy-verification cut is **ADR-046 decision 4** |
| ADR-046 — *the declarable vocabulary is one value* | folded into **ADR-045 decision 1** | The vocabulary is a criterion, and separating it from the floors it sits beside would have put one ADR's subject in two places |
| ADR-047 — *the scaffold's boundary* | **unchanged**, unwritten, PR 5's | — |
| *(not in draft 5)* | **ADR-048 — the cross-tool negative control becomes synthetic** | PR 3's `recap-agent` removal turned out to be a fifth scope cut with no ADR — Platform Engineering's finding, and draft 5 had it as an item, not an ADR |
| *(not in draft 5)* | **ADR-046 — the verifier, and the deploy-verification cut** (PR 4b) | The mechanism half, plus the cut draft 5 had assigned to ADR-045 |

**Still owed:** ADR-047 (the scaffold boundary, PR 5), and PR 2's ADR if and when
PR 2 is built — its number is unassigned precisely so nobody cites it before it
exists.

## Pre-registered predictions — **restated in full, with results as run**

**Stated in full.** Draft 4 amended draft 3's set by reference to a draft its own
preservation sentence could not locate; a pre-registration that requires git
archaeology is not pre-registered.

**Every result below was measured, not asserted.** A prediction marked RESULT was
run through the real path; one marked OPEN has not been run yet, and one marked
FALSE is recorded as false rather than quietly reworded — a prediction edited to
match its outcome is not a prediction.

1. Deleting any of the ten manifest fields is red, with a named message. (Six are
   green today at 1861.)
   **RESULT (PR 4b): held, and widened.** All twelve required paths — the ten fields
   plus `owners.team`, `owners.oncall`, `gates.eval_min_cases`, `gates.budgets` as
   dotted requirements — produce a row-5 refusal that also names **what reads the
   field**, asserted per path.
2. Changing `classification` to any value outside `("internal",)` is red. All three
   of `public`, `confidential`, `sensitive` are green today.
   **RESULT (PR 4a + 4b): held.** `public`'s message additionally states that it
   serves 0 of 25, and a test asserts it does not read as a mitigation.
3. `HEADROOM_BAND` has exactly one definition, in `pave/floors.py`, imported and
   **applied** — the applied half demonstrated by a synthetic pack that violates the
   band and makes the check raise.
   **RESULT (PR 4a): held only after being reworded twice, and draft 5's wording was
   still not sufficient.** Asserting that another file *imports* the band was
   **1864 passed** under the attack. Calling the checker against a *synthetic*
   violating pack — which is what this prediction says — was **1888 passed**: it
   demonstrates the checker and says nothing about the repository's own pack passing
   through it. The form that fires calls `floors.check_headroom(<the committed
   pack>)` from a file the attack does not touch.
4. The lane emits a distinct named message for each of the ~~thirteen~~ **fourteen**
   rows in "The lane's refusals", and `public`'s message does not read as a
   mitigation.
   **RESULT (PR 4b): held at fourteen rows**, with the third column asserted per row
   via `MUST_NAME`, and the public-mitigation half asserted separately.
5. Every check PR 1–PR 6 add is deleted one at a time and re-run; each produces a
   named failure. **Bounded to what M05 adds.** Residual: a *net* deleted test file
   is closed by `COLLECTED_FLOOR`'s `>=` half; **deletion plus padding is not**, and
   no ratchet sees it.
   **RESULT so far: 11/11 (PR 1), 8/8 (PR 3), 11/12 caught with 1 correctly silent
   (PR 4a), 19/20 caught with 1 genuinely silent (PR 4b).** PR 4b's silent one was a
   test whose own name claimed the half it did not check; it is now caught. The
   residual is unchanged and is recorded in ADR-045 decision 5.
6. The pairwise test iterates the five triples in the pair list, and erasing
   `gates.budgets` from the template makes it red. **OPEN — PR 5.**
7. `pave new <svc>` renders exactly the five files listed, and no sixth.
   **OPEN — PR 5.**
8. A freshly scaffolded service **fails** `pave verify` with a stated, enumerated
   list — not passes. **OPEN — PR 5.** The mechanism is in place: a pack of twenty
   `pave-template` rows raises the *floor's* named error rather than a
   `ZeroDivisionError`, which is asserted.
9. Both new guards live outside `pave/cli.py`; `twokey.evaluate(["pave/cli.py", "README.md"], "")`
   still returns `[]` after every PR. **RESULT: held after PR 1, 3, 4a and 4b.**
10. `PLATFORM_EVAL_MIN_CASES` cannot be lowered without a named failure.
    **FALSE AS DRAFT 4 SPECIFIED IT, and that is the finding.** Under draft 4's four
    pins, `20 → 0` was **1867 passed, zero failures** — the milestone's own opening
    finding reproduced one level up, inside the file built to fix it. A two-sided
    ratchet tied only to the feasibility bound left `20 → 10` at **1888 passed**, and
    a re-defaultable argument took the floor to **1 at 1889 passed**. **Now true**
    under PR 4a's five pins.
11. Every verified pack, not only the starter three, satisfies the disposed-set
    denominator.
    **WITHDRAWN AS UNCHECKABLE.** "The starter three" packs do not exist and the
    phrase is defined nowhere in this document. The checkable statement that replaces
    it: `floors.check_headroom` takes the disposed set as its denominator, is called
    by both `tests/test_contracts.py` and `pave/manifest.py`, and the delegation is
    asserted rather than assumed.
12. A blanket-denial arm scores **at or below** the best honest arm under the
    successor instrument, for all three of `classification`, `iam` and `policy`.
    Today: 10/11, 10/11 and 11/11 against **6/10** — `expected_passed`, which is the
    field the current instrument uses. Draft 5 said 7/10 three times; that is
    `recorded_passed`, and a prediction that does not say which field it means cannot
    be checked.
    **BLOCKED — PR 2. Cannot hold simultaneously with 13.**
13. The recorded arms `m00b`, `m01` and `m04` score **unchanged** under the successor
    instrument. If any moves, that is a finding and gets a superseding entry, never a
    fixup.
    **BLOCKED — PR 2. Cannot hold simultaneously with 12**, and rewriting it is
    decision 1 below.
14. `milestones/M05/` exists on disk and the suite is green — the forty-fifth
    sentinel. **OPEN — PR 6.** The sentinel itself was already found and fixed during
    round 4: a bare `.mkdir()` on a path a second call reaches.
15. Forty-three literals read `mzz`/`Mzz`, one reads `m06`, and the vacuity guard
    names no milestone. **RESULT: held (PR 3).** The guard's first version collected
    any table row whose second cell was a number, which swept in the twelve-claims
    table — and *the two tables disagreeing is what made it pass*. Scoped to the
    backticked tag cell.
16. `python -m pytest -q` is green at every PR boundary, and the count at each is
    recorded in the journal. **RESULT so far: 1861 → 1881 → 1909 → 1993**, green at
    each. The journal entry is PR 6's.

## Decisions this draft does not make

Seven, and they are listed here rather than resolved because each is a judgement a
seat owns and not a fact a measurement settles. Three block PR 2 entirely.

**On PR 2 — Security's list, in order:**

1. **Does PR 2 accept that ADV-007's pass in `m01` and `m04` becomes unearned** —
   moving `expected_earned`/`expected_unearned` in `evals/comparators.json` under its
   three-seat rule, with superseding entries — **and is prediction 13 rewritten
   before the work starts?** The alternative is re-deriving the arms from a lake
   fetch, which is a network operation and breaks G8.
2. **Is the `policy` blanket-denial case closed by a Cedar-side positive control in
   `quality/adversarial/probe-controls.yaml`, or declared NOT closed by M05?** It is
   not closable by any per-record predicate, because blanket denial is a property of
   the corpus and not of a record.
3. **Does `services/*/pave.manifest.yaml` take Security's key when the declared tool
   set intersects `GATED_CONSEQUENCES`?** **This is now live rather than
   hypothetical.** PR 4b made `highlights-agent` declare `publish-highlight`, so the
   complete path to granting a scaffolded service the one human-approval-interlocked
   tool collects `tool-owner` and `legal-sp` on the registry line and `ai-quality`
   and `tool-owner` on the manifest — and **Security on neither**. A path-based rule
   cannot express the condition; the choice is Security unconditionally on every
   manifest, or the gap stated and left open. The question is written onto the rule
   itself in `pave/twokey.py` so the next reader meets it where it matters.

**On PR 1 — answered by the build, and recorded:**

4. **May four rows be guarded by their own seats** (`ai-quality, platform-eng` = the
   seat set on `twokey.py` itself)? **Built that way**, with the argument in ADR-044:
   the alternative is an unbounded regress, and the compensating control is that
   `tests/test_twokey_seats.py` — which pins every rule's seats — is on a **six-seat**
   rule, so thinning any seat set collects all six. Recorded as a G9 call taken, open
   to reversal by the seats that did not take it.
5. **Is `recap-agent`'s removal "the control was always synthetic" or "M05 deleted a
   real control"?** **Answered: neither, exactly.** ADR-023 had already established
   that nothing could authorize as `recap-agent`, so the *entry* was synthetic — but
   the control resting on it was real, and removing the entry left the test passing
   at 1881 with zero pairs constructible. ADR-048 was written, and the control is
   re-founded on an in-module synthetic registry that asserts its own sufficiency.

**On scope — still open:**

6. **Does Data Governance hold any enforced key at all, or is the seat recorded as
   advisory-only?** Census after PR 4b, counted from `twokey.RULES` rather than
   quoted: **security 20, platform-eng 20, ai-quality 19, tool-owner 5, legal-sp 3,
   data-governance 0** across 29 rules — while `DECLARABLE_LEVELS` sits
   on `(platform-eng, ai-quality, security)`, so three seats can widen the taxonomy
   and its owner is not among them. `tests/test_no_account_identifiers.py:29` names
   *"a Data Governance decision"* and is on no rule. **The manifest rule does not
   close this and deliberately does not pretend to**: ADR-045 made `classification` a
   singleton, so a seat collected on that field would be collected on a value with
   one legal setting — the decorative-second-key shape ADR-037 found three times in
   `.github/CODEOWNERS`.
7. **Is `jefferson-city` recorded as a named debt under "What M05 does NOT build"?**
   **242 occurrences across 68 files**, and `data/catalog.json:3` asserts *"6
   fictional DMAs"* — false of one of its six, against CLAUDE.md's fictional-entities
   rule. Live surfaces are renameable at 19 failed (catalog) + 15 (`classify.py`)
   through a judge re-freeze; **the recorded artifacts are sha256-pinned by
   append-only history and cannot be renamed at all.**

## Definition of done

Every item 1–39 **except PR 2's**, which is split out and whose absence is stated in
the journal and in the claim-1 footnote rather than left to a reader to notice; both
lists above stated **in this file** and matching what ships; **ADR-047 written and
cited**, and ADR-044, 045, 046 and 048 already are; claim 1 marked INCOMPLETE with
its two footnotes; the deletability audit run for prediction 5 **per PR** and its
result recorded — four PRs in, that is **51 mutations, 49 caught, one correctly
silent and one genuinely missed**, both examined: PR 4a's silence was a floor
*rise*, which a ratchet must permit, and PR 4b's miss was a test whose own name
claimed the half it did not check, now closed; the journal recording the suite count at each PR boundary
(1861 → 1881 → 1909 → 1993 so far); `COLLECTED_FLOOR` re-seated on the closing tree
**after staging**, because two tests are parametrised over `git ls-files` and a floor
read off an unstaged tree is short by twice the number of files the PR adds; and
Acts 0, 1 and 2 recorded or deliberately re-deferred with a stated reason longer than
60 characters, which that file's own test enforces.

## Why this is a milestone and not a chore PR

Because a scaffold is a claim about what a team cannot remove, and before this
milestone this repository could not say what that was. **Five rounds of six seats**
found that the file describing what a service *is* takes no keys; the module that
would judge it does not exist; the file holding the only assertion that a publishing
tool needs a human approver takes none, and one word in it plus one deleted registry
line ships an interlock reading *"Declared approver: none"* at 1861 passed; a
duplicated registry id puts a phantom principal in the deployed policy set for two
keys, neither of them Security; a service that answers nothing scores **11/11** on
the compliance suite against a working platform's **6/10**; and an entire service
this repository has never heard of is invisible to all 1861 tests.

The command that would have produced the manifest prints a sentence and exits 0.

**Four of those are now closed and two are not.** The keys are collected, the
duplicated id is a hard stop, the manifest is verified and the invisible service is
enumerated. `pave new` still prints a sentence and exits 0 — that is PR 5. And the
blanket-denial arm still scores 11/11, which is the finding this milestone opened
with and **the one it does not close**: not deferred by silence, but deferred, and
the three decisions that unblock it are above.

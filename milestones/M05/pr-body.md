# Three rows the seat table stated and no PR built, and a deferral nothing could count

ADR-049. M05's PR 6 — **the close**. **Zero model calls, no new dependency, no
recorded number moved, no threshold lowered, no baseline reset.**

## What was open on `main`

- **SPEC/05's own seat table described three protections that do not exist.** Six
  seats reviewed that table across five rounds. `Makefile`,
  `tests/test_budget_derivation.py` and `docs/governance/recordings.json` all carry
  rows in it and **no PR built any of them.** Measured on the closing tree:

  | mutation | result |
  |---|---|
  | delete the `Makefile`'s `OBSERVATIONS` guard | **2072 passed**, zero keys |
  | reduce `check:` to a bare echo | **2072 passed**, zero keys |
  | delete `tests/test_budget_derivation.py` | **2059 passed, zero failures** |

  The first is the only thing stopping a bare `make adversarial` recording a second
  row over another milestone's evidence — an append-only-history control living in a
  Makefile. The second is the exact `|| echo` shape that file's own header records
  the repository shipping for its entire life. The third takes with it the only tie
  between the committed budget ceilings and the measurement ADR-014's amendment
  derived them from — while that file's docstring asserts in prose that
  `gates.budgets` is two-key.

- **The deferral this PR makes could not have been counted.** M05 is the first close
  at which `recordings.json` had teeth, and the milestone **spends them**: Acts 0, 1
  and 2 were all owed by M05 and all three are re-deferred to M06. That decision is
  deliberate and is the operator's. What was not acceptable is that it cost **2072
  passed, zero keys**, and that nothing could tell a first deferral from a fourth —
  both existing checks ask only whether the *current* `owed_by` has closed. An act
  could have slid one milestone at a time forever, each slide green, each `why`
  rewritten to sound like the first. That is `brand_tone`'s shape exactly.

- **Act 1's stated reason had quietly expired.** The register carried *"Not yet
  buildable; M05 builds `pave new`"* — false since #62 merged, and it would have been
  carried forward unchallenged.

- **`make core` had no guard at all**, and SPEC/05's literal for one does not work.

## What this adds

**Three two-key rules** (ADR-049), the ADR-043 ratchet extended **10 → 13**, and all
four new paths pinned member by member in `ADR043_SEATS`:

| path | seats |
|---|---|
| `docs/governance/recordings.json`, `tests/test_demo_recordings.py` | `platform-eng`, `ai-quality` |
| `Makefile` | `platform-eng`, `ai-quality` |
| `tests/test_budget_derivation.py` | `ai-quality`, `platform-eng` |

The register and its check are keyed **as a pair** — ADR-043 decision 1's reason, and
because data guarded with the instrument left free is the asymmetry ADR-044 was
written about. SPEC/05's row named only the data.

**`deferred_from`, and `test_a_deferral_is_counted_and_named`.** Every act now lists
the milestones it was owed by and passed unrecorded. The check **derives it rather
than trusting it** where derivation is possible: a listed milestone must actually
have closed, the milestone an act is owed by now must not be listed, and an act whose
own owning milestone has closed unrecorded must list that milestone. Each entry must
additionally be **named in the `why`**, so the admission grows with the count instead
of being restated at constant length. The residual — intermediate deferrals are not
derivable, because the register records where an act is owed *now* — is stated in the
docstring and the ADR rather than asserted away.

**`make core` gains its guard, and not where the spec put it.** The spec's literal is
`cd platform/infra && python -m pave.cli verify --all && cdk deploy --all`, justified
on the `pave` console script existing only after `pip install -e .`. Measured, that
justification does not hold: from `platform/infra` **neither** form works without the
install (`ModuleNotFoundError: No module named 'pave'`, exit 1) and after
`make bootstrap` **both** do. The spec's ordering buys nothing and costs the one case
that matters — on an un-bootstrapped tree it refuses with an import error dressed as
a gate refusal. The verifier runs **before** the `cd`, where it resolves with no
install at all. The `&&` premise was re-measured on GNU Make 4.3 rather than carried
forward: two recipe lines under `make -i` print the failure and run the deploy anyway
(`DEPLOY-RAN`, exit 0); one line with `&&` does not. **This does not make
`attestations.manifest_signature` true** and is not sold as such — it is a control on
the repository, not on the runtime (ADR-046 decision 4).

**The close itself:** `milestones/M05/README.md`, the progression row (✅, "six PRs",
`not run` in all three score columns with the reason footnoted), claim 1 marked
**INCOMPLETE** with its two footnotes, and `COLLECTED_FLOOR` re-seated **2072 → 2079**
on the **staged** tree.

## Numbers

`main` 2072 → **2079 passed**, `pave check` **PASS**, ruff clean. No eval entry is
recorded: M05 ran zero model calls and changed no system under test, so it publishes
no score that could be earned or unearned.

**The suite count at each PR boundary was measured, and SPEC/05's list was wrong.**
1861 → **1873** (#56) → **1885** (#57) → 1909 (#58) → 1993 (#59/#60) → **2021** (#61)
→ 2072 (#62) → **2079**. The spec says *"1861 → 1881 → 1909 → 1993"*; **1881 is a
mutation measurement from inside PR 3's work** — *"passing at 1881 with zero pairs
constructible"* — on a tree that was never merged, carried into a progression
narrative as if it were a boundary. Recorded in the journal rather than corrected in
the spec, because a spec edited to match the code stops being a pre-registration.

**A documentation-only PR (#61) moved the suite by 28**, decomposed exactly:
`test_no_account_identifiers.py` 729 → 735 (three files × two `git ls-files`
parametrisations) and `test_cited_commits_resolve.py` 39 → 61. A floor that counts
collected tests is partly counting committed files and cited shas — the "deletion
plus padding" residual `COLLECTED_FLOOR`'s own docstring records, observed live.

## Deletability audit — 7 mutations, 7 caught

| mutation | result |
|---|---|
| delete `test_a_deferral_is_counted_and_named` outright | pytest **silent** (2078 passed); `pave check` **exit 1** at the floor, by name and with the remedy |
| drop `deferred_from` from every act | **1 failed** |
| remove the register/check rule | **2 failed** |
| remove the `Makefile` rule | **2 failed**, `Makefile` evaluates FREE again |
| remove the `test_budget_derivation.py` rule | **2 failed** |
| revert the ratchet 13 → 10 | **1 failed** |
| delete the four new `ADR043_SEATS` pins | **1 failed** |

The first row is the layering working as intended: a deleted test file is invisible
to pytest, so the floor is the only thing that can see it, and it did.

## What this PR does NOT do, stated rather than left to be noticed

- **No recordings.** Acts 0, 1 and 2 are re-deferred to M06 — the operator's decision
  at the close, taken deliberately and now counted. Act 1 is buildable today at zero
  spend and the reason for deferring it is scheduling, not capability; that is written
  into the register in those words.
- **PR 2 stays split out**, so the milestone ships with its own headline finding open:
  G4's *"and logged"* half still credits a refusal without examining what refused. The
  three decisions blocking it are in the spec and re-stated in the journal and the
  claim-1 footnote, per SPEC/05 item 29.
- **An accepted cost's trigger was not readable at this close.** ADR-035 amendment 9
  pre-registers two triggers for `enforcement-probing`, both read off *the governed
  golden run a milestone records*. M05 records none, so the watch did not run. That is
  a gap, not a clean result, and it is journalled as one. `ATK-007` — the hole with the
  deadline — was already closed and discharged at ADR-035 amendment 5.
- **No deploy-time manifest verification** (ADR-046 decision 4), and claim 1 is marked
  INCOMPLETE for that and for an authorship burden measured at **well over an hour**
  against a claim of thirty minutes.

Two-Key-Disposition: platform-eng
Two-Key-Disposition: ai-quality
Two-Key-Disposition: security
Two-Key-Disposition: tool-owner
Two-Key-Disposition: legal-sp
ADR: docs/adr/ADR-049-three-rows-the-seat-table-stated-and-no-pr-built.md
Two-Key-Rationale: This diff adds two-key rules and edits the file that pins every
  rule's seats, so it collects the full five by construction — that five-seat rule on
  `tests/test_twokey_seats.py` is ADR-044's compensating control for letting four rows
  be guarded by their own seats, and it is working here rather than being worked
  around. platform-eng owns the entrypoints, the demo obligation and the scaffold
  mechanism; ai-quality owns the two `--record` invocations, the budget ceilings and
  the register. security and tool-owner arrive through the seat-set pin file and
  through `pave/floors.py`, whose criteria this diff touches only to RAISE
  `COLLECTED_FLOOR` from 2072 to 2079 — a ratchet moving in the direction a ratchet
  may move, seated on the staged tree because two suites parametrise over
  `git ls-files`. legal-sp likewise arrives through the pin file. What was measured:
  no threshold moved downward, no baseline was reset, no golden case was edited, no
  history entry was written or amended, and no recorded number changed. Every rule
  added here strictly increases what a future diff must collect, and each was audited
  by deleting it and re-running — 7 of 7 caught. The one deliberate weakening in this
  diff is a governance decision rather than a control change: three demo recordings
  owed by M05 are re-deferred to M06, which is exactly what `recordings.json` permits
  and which this PR makes countable for the first time.

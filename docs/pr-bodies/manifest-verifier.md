# Six of a manifest's ten fields were deletable at zero failures, and the registry granted a publish-class tool nothing declared

ADR-046. The mechanism half of M05's verifier; ADR-045 landed the criteria half.
**Zero model calls, no new dependency, no recorded number moved.**

## What was open on `main`

`pave.manifest.yaml` is a ten-field file the repository read and never checked.
Measured on `6af17d2` during the SPEC/05 seat review:

- **Deleting six of the ten fields: 1861 passed, zero failures.** The four that
  went red went red *incidentally* — a `KeyError` raised by a test reading the
  field for something else, never a refusal naming it.
- **`gates.eval_min_cases: 20 → 0` was green.** The milestone's opening finding,
  and the spec's refusal table had no row for it.
- **`brand: meridian-sports → meridian-news`: 1889 passed.** Enforcement was a
  `print()` in a creates-only command.
- **A manifest declaring a tool whose grant had been revoked: nothing red.**
  `tests/test_contracts.py:83` checked only that the id *exists* in the registry.
- **Nothing in the repository enumerated `services/*`.** Both CI evaluation steps
  name `highlights-agent` literally. A second service could land with a manifest
  declaring a tool it is not granted, a brand nothing can judge and
  `eval_min_cases: 0`, and no check would look at it. That is the premise M05
  exists to remove.

## What this adds

`pave/manifest.py` (mechanism, holding no number of its own), `pave/verify.py`
(the `pave verify` invocation and nothing else), and
`tests/test_manifest_verify.py` — a **fourteen-row refusal table as code**, with
one violating producer per row and a test requiring the two sets to be equal in
**both directions**, so neither a row without a producer nor a producer without a
row can survive. `MUST_NAME` turns the table's *"message names"* column into
assertions. Every row test is guarded by a vacuity test on the clean fixture.

Two rows differ from SPEC/05's table, both stated in the ADR: **row 10 is
withdrawn and replaced** (its `curated_by` pack header was measured as a
47-failure migration and superseded by ADR-045; row 10 is now
`gates.eval_min_cases` below the platform floor, the finding that had no row at
all), and **row 14 is new** for `brand`.

`COLLECTED_FLOOR` is now enforced rather than only pinned, and re-seated
1900 → **1993** on the tree it ships. The slack between a floor and the count is
the deletion budget; a floor 93 beneath the count is a floor for 93 deletions
nobody measured.

## The one behavioural change to a committed file

**`services/highlights-agent/pave.manifest.yaml` now declares
`publish-highlight@^0`.** Row 4 — *every grant is declared* — fired on the only
committed manifest, exactly as the Tool Owner seat predicted. Both fixes were
measured and only one is legal:

| fix | measured |
|---|---|
| revoke the grant (`callers: []`) | **4 failed.** Three Cedar tests plus `test_every_registered_tool_declares_an_owner_and_consequence_class`, which says in as many words that a tool with no callers is *"an unreachable tool (G3)"* |
| declare it in the manifest | green, `pave verify --all` exit 0 |

Revocation would also break a recorded exhibit: `milestones/M02/README.md:52`
records `publish-highlight` as **denied, mechanism `policy`**, and that denial is
the generated `forbid … unless approval_granted` firing over a `permit` **that
exists**. Remove the caller and the permit disappears, the denial becomes *no
permit at all* — `catalog-purge`'s case one row up — and five distinct mechanisms
collapse to four with two rows measuring the same thing.

**This creates an open question and does not answer it.** The reference manifest
now declares a tool whose consequence class is in `GATED_CONSEQUENCES`, and the
complete path to granting a scaffolded service that tool collects `tool-owner` and
`legal-sp` on the registry line and `ai-quality` and `tool-owner` here — **Security
on neither**. A path rule cannot express *"when the declared set intersects
`GATED_CONSEQUENCES`"*. The question is written onto the rule itself in
`pave/twokey.py` and is owed by SPEC/05.

## The deletability audit

20 mutations, full suite each. **19 caught, 1 silent** — and the silent one was a
test whose own name claimed the thing it did not check:
`test_a_manifest_failure_pages_the_team_and_a_missing_service_pages_the_platform`
asserted only the second half of its name. Making `verify()` return 0 for a
service with findings was **1982 passed, silent**. The exit code is not cosmetic:
`make core` puts `python -m pave.cli verify --all && cdk deploy --all` on one
`&&`-joined line, so a zero exit deploys the service the verifier just refused. Now
CAUGHT.

Two further gaps were found *before* the audit began, both mine, both the same
shape and both recorded in the ADR: `COLLECTED_FLOOR`'s wiring was unreachable by
any test (nothing executes `cli.check()`), and the deferral check counted entries
rather than naming them, so deleting one was invisible.

## What this does NOT do

Written into the ADR rather than left for a reader to find: **no deploy-time
verification and no signature** — `attestations.manifest_signature: required` is
verified by nothing and stays a placeholder with a stated reason; **no range
evaluation** (`@^0` and `semver:` are decorative, and the verifier says so in its
own output on green runs as well as red ones); **no second brand** — row 14
refuses, it does not enable; **no `pave new`** (ADR-047's); and **Data Governance
still holds zero enforced keys**, which this rule deliberately does not paper over.

## Verification

Full suite green at **1993 passed**, ruff clean, hermetic, zero model calls, no new
dependency. `pave verify --all` exit 0. No `evals/history/` entry, no `pins.json`,
no `evals/comparators.json`, no instrument digest and no judge digest moved.

**This PR gates itself under the rules it adds** — five seats across six rules.

Two-Key-Disposition: platform-eng
Two-Key-Disposition: ai-quality
Two-Key-Disposition: security
Two-Key-Disposition: tool-owner
Two-Key-Disposition: legal-sp
Two-Key-Rationale: A ten-field manifest with six fields deletable at zero
  failures and a registry grant no manifest declared are both authorization
  surfaces, so security joins on the grant bijection whose reverse direction
  nothing in this repository had, and tool-owner on the manifest and the registry
  it owns. ai-quality holds every criterion the verifier reads, which is why the
  verifier itself may sit at three seats while holding none of them, and
  platform-eng owns the mechanism and the collected-count floor now wired into
  pave check. legal-sp arrives through the seat-set pin file rather than through
  a new rule. The diff moves no threshold downward, no recorded number, no
  instrument digest: the one floor that changes rises, and the single behavioural
  change to a committed file adds a declaration for a grant that already existed
  and whose removal is measured as four failures. What the verifier does not check
  is enumerated in the ADR and printed by the command on every green run.

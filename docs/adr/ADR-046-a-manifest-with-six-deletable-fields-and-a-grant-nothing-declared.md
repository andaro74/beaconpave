# ADR-046: six of a manifest's ten fields were deletable at zero failures, the registry granted a publish-class tool nothing declared, and the verifier that fixes both runs in the repository rather than at the deploy

**Status:** Proposed. **Zero model calls.**
**Seats:** Platform Engineering (the mechanism) · AI Quality (the criteria) ·
Security / Red Team (the grant bijection) · Tool Owner (the manifest)

This is the mechanism half of M05's verifier. ADR-045 is the criteria half, and the
line between them is the one `pave/gate.py`'s docstring already draws: Platform
Engineering owns the code that reads a criterion, AI Quality owns the criterion
that produces a FAIL. Grep `pave/manifest.py` for a literal threshold and there is
none.

## The premise, restated as measurements

`pave.manifest.yaml` is a ten-field file that the repository read and never
checked. Measured on `6af17d2`:

| what | result |
|---|---|
| delete six of the ten fields | **1861 passed, zero failures** |
| the four that went red | red *incidentally* — a `KeyError` from a test reading the field for another purpose, never a refusal naming it |
| `gates.eval_min_cases: 20 → 0` | green. **The milestone's own opening finding** |
| `brand: meridian-sports → meridian-news` | **1889 passed** |
| `catalog-search@not-a-range-at-all`, `semver:` deleted from every registry entry | `--check` exit 0, 1861 passed |
| a manifest declaring a tool whose grant was revoked | nothing red — `tests/test_contracts.py:83` checked only that the id *exists* |
| any test enumerating `services/*` | **none.** Both CI evaluation steps name `highlights-agent` literally |

The last row is the premise M05 exists to remove, and it is the one a second
service meets first: a service the repository has never heard of stays invisible.

## Decision 1 — the verifier is two files, and neither holds a number

`pave/manifest.py` reads a manifest and returns findings. `pave/verify.py` holds
the `pave verify` invocation and nothing else.

**Not `pave/gate.py`**, which Platform Engineering measured as working (50 passed,
`test_ordinary_pr_is_not_gated` intact) and refused anyway: the row would erase the
seat boundary that file's own docstring draws, and it leaves
`pave/tests/test_gate.py` — 21.7 KB holding the entire pin on the exit-code
contract — at zero keys while the file it pins takes three. That is ADR-043
decision 1's *weakened together or not at all*, arriving again.

**Not `pave/cli.py`**, for `pave/floors.py`'s recorded reason: ~1200 lines and a
sixth of this repository's commits, named by a committed test as the canonical
ungated example. The dispatch line lives there; nothing else does.

**The criteria are read, not restated, and that is asserted by moving them.** The
first version of that test grepped `pave/manifest.py` for `floors.<NAME>` — and
ADR-045 measured that exact shape at 1864 passed, because an import line satisfies
a source assertion looking for an import line. `CRITERIA_MOVES` now moves each of
`PLATFORM_EVAL_MIN_CASES`, `DECLARABLE_LEVELS`, `SUPPORTED_BRANDS`,
`REQUIRED_BUDGET_KEYS` and `CASE_TOP_LEVEL_KEYS` and requires the verifier to
follow. An inlined copy passes the grep and fails this.

`HEADROOM_BAND` is the one criterion `pave/manifest.py` never names, and that is
correct: it delegates to `floors.check_headroom`, so the band *and the ratio
arithmetic* are single-sourced with `tests/test_contracts.py`. Moving the constant
would not prove the delegation — `check_headroom` binds the band as a default
argument at import — so the delegation is proved directly, by replacing the shared
checker and requiring its error to surface as row 9.

## Decision 2 — the refusal table is code, with a producer per row, checked both ways

SPEC/05 item 29's commitment is that every malformed input in the table is a named
FAIL with no traceback, and that anything outside the table is deferred **by name**
rather than by silence. `manifest.ROWS` is that table as the code that produces it;
`tests/test_manifest_verify.py`'s `PRODUCERS` holds one violating input per row, and
`test_the_table_and_the_producers_agree` requires the two sets to be equal in **both
directions**. A row with no producer is a stated protection that fires on nothing. A
producer for a row nobody wrote down is a refusal a team meets with no documentation
to reach.

`MUST_NAME` is the table's *"message names"* column as assertions, so a row that
fires with a message a reader cannot act on is red — the `_die("check failed")`
shape ADR-042 recorded, where the comment named a tool and a number and no next
step.

**Every row test is guarded by a vacuity test.** A `verify()` that returned every
row on every input would satisfy all fourteen; `test_the_good_fixture_earns_no_refusal`
is the only test in the file that would notice.

### Two rows changed from the spec's table

**Row 10 was *undisposed pack header / the missing `curated_by`* and is withdrawn.**
ADR-045 decision 4 measured the pack-level header as a **47-failure migration**
(`cases.yaml` is a top-level YAML list with nowhere to put one) and replaced it with
per-case `provenance.author`. A refusal row naming a field the design no longer has
would have failed the reference pack on day one. Row 10 is now
**`gates.eval_min_cases` below the platform floor**, which is the milestone's own
opening finding and had no row at all — the Service Team seat found the omission and
named it correctly: *deferred by silence, which item 29 forbids.*

**Row 14 is new: `brand` outside the set the judge can score.** Enforcement was a
`print()` in a creates-only command, and `meridian-sports → meridian-news` measured
1889 passed. See decision 5.

## Decision 3 — the grant check runs in both directions, and `highlights-agent` declares `publish-highlight`

The verifier asserts `manifest.service ∈ registry[tool].callers` for every declared
tool (row 3) **and the reverse for every grant** (row 4). The reverse direction is
the half nothing in this repository had: a grant nobody declared is a permission
with no owner, because it survives every review of the manifest by not being in it.

**Row 4 fired on the only committed manifest**, exactly as the Tool Owner seat
predicted: the registry grants `highlights-agent` the `publish`-consequence tool
`publish-highlight`, and the manifest declared two tools. Two fixes were available
and only one is legal:

| fix | measured |
|---|---|
| revoke the grant (`callers: []`) | **4 failed, 1909 passed.** Three Cedar tests, plus `test_every_registered_tool_declares_an_owner_and_consequence_class`, which says in as many words that a tool with no callers is *"an unreachable tool (G3)"* |
| declare it in the manifest | green, `pave verify --all` exit 0. (1979 passed at the moment of the measurement; the tree is 1993 by the time this PR closes) |

Revocation is not a legal registry state, and it would also break a recorded
exhibit. `milestones/M02/README.md:52` records `publish-highlight` as **denied,
mechanism `policy`** — and that denial is the generated `forbid ... unless
approval_granted` firing over a `permit` **that exists**. Remove the caller and the
permit disappears; the denial becomes *no permit at all*, which is `catalog-purge`'s
case one row up. Five distinct mechanisms would collapse to four with two rows
measuring the same thing.

So the manifest declares it, with the reasoning in the file beside the line —
declared because the registry **grants** it, not because the agent calls it.

**The open question this creates, stated rather than absorbed.** The reference
manifest now declares a tool whose consequence class is in `GATED_CONSEQUENCES`.
The complete path to granting a scaffolded service the one human-approval-interlocked
tool now collects `tool-owner` and `legal-sp` on the registry line and `ai-quality`
and `tool-owner` on the manifest — **and Security on neither**. A path-based rule
cannot express *"when the declared set intersects `GATED_CONSEQUENCES`"*. Whether
`services/*/pave.manifest.yaml` takes Security's key unconditionally is owed by
SPEC/05 and is **not decided here**; the question is written on the rule itself in
`pave/twokey.py` so the next reader meets it where it matters.

## Decision 4 — the deploy-verification cut

**`pave verify` runs in the repository. It does not run at the deploy, and it does
not make `attestations.manifest_signature` true.**

The manifest says `manifest_signature: required` and **nothing verifies it**. That
field is a placeholder, and this ADR is the stated reason it stays one rather than a
silent simplification.

`make core`'s one-line recipe (`cd platform/infra && python -m pave.cli verify --all
&& cdk deploy --all`, M05's PR 6) makes the verifier run *before* `cdk deploy` on a
developer's machine. **That is not deploy-time verification and must not be sold as
such**: the `&&` binds two commands in one shell, nothing signs the manifest, nothing
checks a signature at the far end, and a deploy issued by any other means is
unverified. What the repository actually holds is *a manifest it refuses to merge
when it is malformed* — a control on the repository, not on the runtime.

The same limit applies to `classification`, and it is worth stating positively
because the field reads like a runtime control: `handler.py:309` still takes
`declared` from the event. What `classification` **is**: a declaration the repository
refuses to merge when it is outside the vocabulary. What it is **not**: any claim
that the repository can tell a truthful declaration from a convenient one.

*At scale, replace with a signed manifest verified by the deploy role before it
assumes anything; `pave verify` already returns findings rather than printing them,
so the interface already matches.*

## Decision 5 — three criteria moved to `pave/floors.py`, because a verifier is how a second copy is born

Each of these existed somewhere and none of them existed in the criteria file. A
verifier reading them would have created a second site — ADR-045 decision 7 and
ADR-037's whole subject, and the second copy never goes red on its own, because the
narrower gate wins at runtime.

| criterion | where it was | why it is a criterion |
|---|---|---|
| `SUPPORTED_BRANDS` | a substring inside a tuple inside a function in `evals/judge.py` | a brand is supported when the judge can score it |
| `REQUIRED_BUDGET_KEYS` | four string subscripts across two assertions | an absent ceiling is not a generous ceiling |
| `CASE_TOP_LEVEL_KEYS` | a bare set literal in `tests/test_contracts.py` | the runner skips what it does not recognise |

**`SUPPORTED_BRANDS`'s pin is behavioural and matches `DECLARABLE_LEVELS`'s form.**
Equality against the recorded tuple, plus: for every supported brand, the rubric
slice `evals/judge.py` sends to the model carries a `brand_tone:<brand>` axis. That
cannot be satisfied by editing `pave/floors.py` — making it green means editing the
rubric, which is a judge re-freeze (two-key `ai-quality`) and superseding history
entries. **That cost is the reason the second brand is M08's and not M05's**, and it
was measured: one fictional news title is 16 failed, because the catalog is embedded
model-facing in the judge prompt and digested into `quality/judge/frozen.json`.

Row 14 refuses a brand the judge cannot score. It does not build the pack that would
make a second brand scoreable, and that gap is in `DEFERRED` by name.

## Decision 6 — `COLLECTED_FLOOR` is enforced, and the enforcement was unreachable when it was written

ADR-045 pinned the number and left the wiring owed. Wiring it into `pave check`
produced a check **nothing in this repository can execute** — no test calls
`cli.check()` — which is ADR-042's finding reproduced inside the fix for it: six of
ten planted weakenings survived because the check they removed could not be run on
an honest tree.

So the logic is `cli.collected_floor_failures(summary)`, a pure function
`tests/test_floors.py` exercises directly, **plus a structural assertion that
`check()` calls it** — an `ast` walk of `check`'s own body, which a comment, a
docstring or an import line cannot satisfy. A tested function nobody calls protects
nothing, and the call site is the half a unit test cannot see.

**The floor is re-seated on the tree it ships**, 1900 → 1993, and the rule is stated
rather than discovered: *the slack between a floor and the count is the deletion
budget.* A floor 93 beneath the count is a floor for 93 deletions nobody measured,
which is `G4_CASE_FLOOR`'s own docstring one component over. Consolidating tests
legitimately is a real reason to lower it and costs a `pave/floors.py` diff, a
`tests/test_floors.py` diff and three seats. That cost is the control.

## Decision 7 — a duplicate-key-rejecting loader, PyYAML only

`yaml.safe_load` resolves a duplicated key to its **last** value in silence, so a
manifest can carry two `gates:` blocks, pass every check in the verifier against
the second, and read to a human as the first. The loader is a `SafeLoader` subclass
overriding `construct_mapping`; **no new dependency**, which CLAUDE.md would require
an ADR line for. It reaches nested mappings, because a duplicate two levels down is
the one a reviewer misses, and it reports **both** line numbers — pointing only at
the winner sends a reader to the line they already read.

## The deletability audit — 20 mutations, one silent

Every check this PR adds was deleted or weakened one at a time and the full suite
re-run. **19 of 20 produced a named failure. One was silent, and it was a test whose
own name claimed the thing it did not check.**

| mutation | result |
|---|---|
| row 4's reverse-grant loop → `if False` | CAUGHT |
| `services()` → `[]` | CAUGHT |
| the duplicate-key loader → `yaml.safe_load` | CAUGHT |
| the `floors.check_headroom` call → `pass` | CAUGHT |
| `floors.PLATFORM_EVAL_MIN_CASES` → the literal `20` | CAUGHT |
| row 14's brand check → `if False` | CAUGHT |
| `floors.DECLARABLE_LEVELS` → the literal `("internal",)` | CAUGHT |
| `grants()`'s duplicate-id raise → unreachable | CAUGHT |
| row 14 deleted from `ROWS` | CAUGHT |
| one `DEFERRED` entry renamed away | CAUGHT |
| one entry deleted from `REQUIRED_FIELDS` | CAUGHT |
| `COLLECTED_FLOOR` 1983 → 1900 | CAUGHT |
| `SUPPORTED_BRANDS` widened to two | CAUGHT |
| `REQUIRED_BUDGET_KEYS` loses `p95_ms` | CAUGHT |
| `CASE_TOP_LEVEL_KEYS` gains a junk key | CAUGHT |
| `check()`'s call to `collected_floor_failures` → `pass` | CAUGHT |
| the verifier's two-key regex narrowed to drop `pave/verify.py` | CAUGHT |
| `security` dropped from the verifier's seat set | CAUGHT |
| `publish-highlight@^0` removed from the committed manifest | CAUGHT |
| **`verify()`'s `if total:` → `if False:` — a service with findings exits 0** | **SILENT, 1982 passed** |

**The silent one.** `test_a_manifest_failure_pages_the_team_and_a_missing_service_pages_the_platform`
asserted only the second half of its own name: it checked `EXIT_CONTRACT` for a
service that does not exist and never checked `EXIT_QUALITY` for a service with
findings. The exit code is not cosmetic — `make core` puts `python -m pave.cli verify
--all && cdk deploy --all` on one `&&`-joined line, so a zero exit deploys the
service the verifier just refused. The test now builds a service with findings,
points `manifest.SERVICES` at it, and requires `EXIT_QUALITY`; re-run under the same
mutation it is CAUGHT.

That is the fifth time in this repository a check has been found stating a
protection it did not perform, and the third inside the diff written to close the
previous one.

## The two gaps found before the audit began

Both were the same shape — a check nothing could reach, or a check that counts
rather than names — and both are recorded because they were mine and were caught by
building rather than by reading.

1. **`COLLECTED_FLOOR`'s wiring was unreachable.** Written inline inside
   `pave/cli.py`'s `check()`, and nothing in this repository executes `check()`.
   Deleting it would have been silent. Extracted to `collected_floor_failures()`,
   unit-tested, and the call site pinned by an `ast` walk of `check`'s own body.
2. **The deferral check counted rather than named.** `for what in DEFERRED: assert
   what in printed` cannot see an entry *deleted* — the loop simply runs one fewer
   time, and an emptiness guard only catches `{}`. Deferring a gap by name is the
   whole of item 29's commitment, and dropping the name does not close the gap, it
   stops the gap being stated. Now pinned as set equality.

## What this does NOT do

- **No deploy-time verification and no signature.** Decision 4.
- **No range evaluation.** `@^0` and the registry's `semver:` are decorative; the
  verifier checks the id and says so in its own output, on green runs as well as red
  ones. Under the 0.x convention every minor bump is breaking, so `^0` is the
  **widest** caret and `^0.0.x` the tightest — which is why an earlier draft's
  refusal singled out the safe form. M06's, or the field goes.
- **No second brand.** Row 14 refuses; it does not enable.
- **No `pave new`.** The scaffold boundary is ADR-047's, and until it lands
  `SCAFFOLD_AUTHOR` describes rows nothing yet writes.
- **Data Governance still holds zero enforced keys.** The seat that owns the
  taxonomy is on no rule anywhere, and three other seats can widen
  `DECLARABLE_LEVELS`. Not closed here, and not closed by this rule either: ADR-045
  made `classification` a singleton, so a seat collected on that field would be
  collected on a value with one legal setting — the decorative-second-key shape
  ADR-037 found three times in `.github/CODEOWNERS`. Owed by SPEC/05.
- **It does not verify more than the tree it can see.** `services()` globs
  `services/*`, and `test_the_service_glob_finds_something` asserts the glob is
  non-empty — but a service kept outside that directory is still invisible.

## Scale-up path

*At scale, `pave verify` becomes an admission controller the deploy role calls with
a signed manifest, and the refusal table becomes its response schema; `verify()`
already returns a list of typed findings rather than printing them, and every
criterion is one module-level constant read through one import — the interface
already matches.*

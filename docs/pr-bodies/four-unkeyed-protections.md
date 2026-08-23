# Five protections named their own seat in prose and collected no key

ADR-043. Found by six role seats planting against `main` during the SPEC/05
review — **none of these was introduced by M05**, and not one was found by
reading. Four of the five contradict a comment sitting in the same file.

## What was open on `main` this morning

Every plant below ran on a clean tree at `07e8cd1`, full suite.

**G1's model-invoke allowlist.** Widening `MODEL_INVOKE_ROLE_PREFIXES` and
relaxing the test that pins it, in one diff: **1795 passed, two-key NOT
REQUIRED** — against `pave/infra.py:64` (*"it needs an ADR and the Security seat
rather than a commit"*) and `tests/test_iam_assertions.py:118` (*"Adding another
is a G1 exception (Security seat + ADR), not a test fix"*).

**G3's generator.** Two lines in `cedar.py:generate()` put
`permit(principal == Service::"attacker-svc", …)` into the deployed policy set,
`pave policy generate --check` exit **0**, 1795 passed, and the two-key registry
never touched. The drift gate is `generate(REGISTRY) == COMMITTED` — both sides
call the same function, so it proves the artifact is a faithful build product
*of the generator* and never that the generator is a faithful function *of the
registry*.

**Claim 10's interlock.** Dropping one word from `GATED_CONSEQUENCES` removes
**every** `forbid` clause; `publish-highlight` becomes reachable with no
approver; drift gate exit 0; **zero keys**. Which consequence classes get an
interlock is decided in the generator, the one place Legal/S&P's key could not
reach it.

**The tool plane.** Neutering `Approval.__post_init__`'s guard so
`Approval("", "")` validates, plus the one test that catches it: **1814 passed,
zero keys.** `toolplane.py:1` says *"nothing reaches a tool except through here
(G3)"* and names three seats in its docstring.

**A tool schema.** Deleting `ai_generated` — MER-AI-0001's disclosure flag — and
adding `skip_approval` reached `tools.contracts.json`, which ships inside the
gateway Lambda bundle: 1795 passed, no key. The schema's own description claimed
the absence was enforced *and* named the probe enforcing it. Both halves false.

**The harness underneath all of it.** `collect_ignore` in `tests/conftest.py`
drops 1795 collected tests to **1656** with `pave check` printing *"All checks
passed!"*. Eight lines of `pytest_runtest_makereport` hookwrapper report **1795**
— the exact honest count — with a G1 pin genuinely failing.

**And `CLAUDE.md:26` pointed G1 at `platform/infra/tests/`**, which holds three
fixtures and a README. No test.

## What this PR does

Five two-key rules, one new assertion, two prose corrections. **No mechanism.**

| path | seats |
|---|---|
| `pave/infra.py`, `tests/test_iam_assertions.py` | security, platform-eng, **ADR** |
| `cedar.py`, `test_cedar_policy.py`, `tools/*/schema.(in\|out).json` | platform-eng, security, tool-owner, legal-sp |
| `toolplane.py`, `test_toolplane.py` | platform-eng, security, tool-owner |
| `conftest.py` (any dir), `pyproject.toml`, `pytest.ini`, `tox.ini`, `setup.cfg` | platform-eng, security |
| `tests/test_twokey_seats.py` | all five — it pins every other rule's seats |

The one new check: no registered tool may declare a bypass-shaped property at any
depth in either schema, and a gated tool must keep the fields — and the types —
its approver reads.

## What it does NOT close, stated rather than implied

- **G1's widening and the forged permit become *collectable*, not *red*.** A
  self-pinning constant edited beside its own pin produces no failure, and
  `policy ⊆ registry` belongs with M05's verifier.
- **A key on the harness is collectable, not red.** A harness that rewrites its
  own reports can report anything, and no count sees it.
- **`BYPASS_SHAPED` is a denylist.** Nesting and output schemas are covered; an
  unlisted name is not. The replacement — pin the exact property set per gated
  tool — is named as owed.
- The schema rule is path-shaped while its check follows the registry pointer; a
  duplicate registry id is a forgery `policy ⊆ registry` would not catch;
  `semver` is decorative; `cedar.py` is in no instrument digest.

## The review found eleven defects and eight were in the fixes, not the code

Recorded in the ADR because the pattern is the ADR's own subject at successive
depths: a check written for a vacuous protection was vacuous; the anti-vacuity
guard tested a dict's keys instead of its values, so MER-AI-0001's disclosure
flag could be deleted at 1814 passed; a correction to the ADR named a test that
**passes under its own plant** because it iterates the constant being attacked;
the seat-set pins were defended by three of the four seats they pin; a rename
detached them entirely; and a **prose correction landed in model-facing text** —
`handler.py:157` sends the input schema's `description` to Bedrock as the tool
spec, and the "fix" grew it from 309 to 708 bytes of repo governance. It escaped
`TOOL_SPECS_SHA256` only because that pin iterates *routed* tools and
`publish-highlight` has none at M02.

The deletability audit found 3 of 6 checks silent on first implementation, then 2
more that the audit itself had not reached. All are now loud.

## Verification

`make check` green at **1815 passed**, ruff clean, hermetic, zero model calls, no
new dependency. All seven adversarial instrument digests and all five judge
digests byte-identical. No `evals/history/` entry, no `pins.json`, no
`evals/comparators.json`, no README number moved.

**This PR gates itself under the rules it adds** — five seats across three rules.

Two-Key-Disposition: ai-quality
Two-Key-Disposition: security
Two-Key-Disposition: platform-eng
Two-Key-Disposition: tool-owner
Two-Key-Disposition: legal-sp
Two-Key-Rationale: Five paths that decide G1, G3 or claim 10 collected no key
  while four of them carried a comment naming the seat that supposedly guarded
  them; each hole was measured by planting against main, and the diff adds only
  rules plus one assertion, moving no threshold, no recorded number and no
  instrument digest. The seats here are the ones each path's own docstring or
  CLAUDE.md already names — legal-sp because GATED_CONSEQUENCES is a
  consequence-class judgement living outside the registry, security because
  three of the paths are authorization decision points, tool-owner because the
  generator renders the registry it owns. What the rules do not close is written
  into the ADR rather than left for a reader to discover.

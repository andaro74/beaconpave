# The contract tests read every committed golden pack, bound to the manifest module

Zero model calls. One owed item from `docs/samples/game-recap-agent.md`,
discharged.

## What it changes

`tests/test_contracts.py` runs its per-case checks over every committed
service's golden pack. Discovery is bound to `pave/manifest.py`, not restated:
`manifest.services()` is the one enumeration of `services/*` and
`manifest.GOLDEN_PACK` the one spelling of where a pack lives. Five reads stay
pinned to the reference service on purpose: the progression table's `/25`
denominator and the headroom-exemption test's *still bites* line, both about
that pack, and the three manifest-shape tests (tools registered, directory
name, declarable classification), which `pave verify` already applies to every
service through `tests/test_manifest_verify.py`.

`test_every_committed_service_golden_pack_is_read_here` asserts the discovery's
sufficiency three ways by name: a service with a manifest and no pack, a pack
under `services/` beside no manifest, and, the ratchet, that the list the loops
read is exactly what the enumeration returns. The last one exists because the
AI Quality seat rebound the discovery to the reference pack in one line and
the file stayed green with a defect planted behind it. Equality, not a count,
so it is not coupled to how many services exist. The manifest case-floor check
now applies the rule `pave verify` row 8 applies, the declared floor never below
the platform floor; that is the one criterion whose text changed, disclosed
here and no-op today since both manifests declare the platform floor.

Every widened message names the service, because `recommend-013` is a case id
in both committed packs. The headroom failure, which comes from `pave/floors.py`
and names a ratio and a policy, is re-raised with the service in front.

Two sentences in `tests/test_manifest_verify.py` said this file read one
hard-coded path. They now say what it reads. The golden README under
`services/game-recap-agent/` and the sample record say what reads the pack and
what still does not.

## What bites on the second pack, and what is vacuous there

Measured over `game-recap-agent`'s twenty cases. These checks have applicable
cases and refuse a plant by name: assert vocabulary, `json_schema` present,
groundedness checked, no vacuous groundedness, no contradictory citations,
cited titles exist, real DMAs and plans, budgets within the service's own
manifest, no percentile and no currency in a budget, unique ids, headroom band,
manifest case floor, undocumented top-level keys, the headroom flag not nested.

Three checks loop over zero applicable cases there, because the pack carries no
`entitlement` assert, no `trajectory` expectation and no `provenance.rule`:
entitlement-requires-the-tool, trajectory tools registered, and undisposed-rule
attribution. They run; they decide nothing on that pack. Stated rather than
listed as coverage.

## Why

When the sample service merged, its pack was covered by four rows of
`pave verify` and by no contract test. The AI Quality seat found that by
repointing this file at the new pack by hand, and every check passed, which is
exactly the kind of green that means nothing. Two seat rounds then found the
first draft globbing paths the manifest module already owns, the second draft
narrowable back to one pack with nothing red, and messages that named a case
id two files share.

## Checked

Planted one at a time, restored from a backup between plants:

| plant | caught by |
|---|---|
| assert key misspelled in the new pack | `test_no_case_uses_an_undocumented_assert`, reading `game-recap-agent/preview-010: …` |
| unreal DMA in the new pack | `test_viewer_context_names_real_dmas_and_plans` |
| new pack deleted | `test_every_committed_service_golden_pack_is_read_here`, by name, with no raw file error beside it; `tests/test_manifest_verify.py` adds two named row-8 refusals |
| a pack beside no manifest | the same test, naming the directory |
| a manifest beside no pack | the same test, naming the service |
| `GOLDEN_PACK` moved in `pave/manifest.py` | this file follows the constant and goes red with it, where the first draft stayed green |
| discovery rebound to the reference pack | the same test, the ratchet; the second draft stayed green |
| both headroom flags off in the new pack | `test_golden_set_keeps_headroom`, reading `game-recap-agent: headroom is 0/20 …` |

`ruff check` clean on both test files. `tests/test_contracts.py` and
`tests/test_manifest_verify.py`: 108 passed. `make check`: see the commit.

## Attestations

Two-Key-Disposition: ai-quality
Two-Key-Rationale: the per-case criteria apply unchanged to every committed pack except the row 8 floor, which now applies pave verify's own rule and is disclosed, the five reference-only reads are named and kept, the three checks vacuous on the second pack are stated as such, and the widening is ratcheted by equality with the enumeration after a one-line narrowing was measured green
Two-Key-Disposition: platform-eng
Two-Key-Rationale: discovery is bound to manifest.services and manifest.GOLDEN_PACK rather than re-globbed, all three directions of the discovery's sufficiency are refused by name, the row 8 floor is one formula shared with pave verify, and no history-ordering pin path is touched
Two-Key-Disposition: security
Two-Key-Rationale: the only change to tests/test_manifest_verify.py is two docstring sentences that described the contract tests as reading one hard-coded path, corrected to what they read now, with no assertion in that file changed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

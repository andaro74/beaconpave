# Sample: `game-recap-agent`, a second service onboarded through `pave new`

Zero model calls. The record is `docs/samples/game-recap-agent.md`; this body is
the disposition.

## What it adds

- `services/game-recap-agent/`: the five files `pave new` renders, with the golden
  pack's three template rows replaced by twenty disposed cases and the rendered
  golden README replaced by one that describes this pack.
- `platform/registry/tools.yaml`: `game-recap-agent` added to `catalog-search`'s
  callers. No other entry touched.
- `platform/gateway/policy/tools.cedar`: regenerated. One new permit, this service
  invoking `catalog-search`. `tools.contracts.json` is unchanged, since no tool
  changed.
- `docs/adr/ADR-048-…md`: amendment 1, recording that a second committed service
  un-cuts decision 1 at the registry and not at the runtime, and its index row
  in `docs/adr/README.md` marked amended.
- `tools/catalog-search/README.md`: the prose site ADR-048 named, corrected.
- `docs/samples/game-recap-agent.md`: the commands, the refusals before and after,
  the pack measured against the reference, and what the sample does not show.
- README repository map: a `docs/samples/` row.

## What it is for

Claim 1 is INCOMPLETE in the README for two reasons. This is an onboarding through
the scaffolder's path, done by an assistant with the repository's history in
hand, recorded so that a later measurement by a developer has something to
compare against. It moves no claim, no row and no baseline: the pack is authored
and unscored, and nothing is recorded to history.

## What the seat reviews found, and what changed

Four role subagents reviewed the first draft (AI Quality, Tool Owner, Legal/S&P,
Service Team; advisory, G6). Every block was real:

- **Twelve `must_not_claim` bans a correct answer could trip** ("the winner was"
  sits inside "the catalog doesn't record who the winner was"). Replaced by three
  narrative phrasings, with the residual risk stated in the pack header and the
  vocabulary gap recorded as owed.
- **The rendered golden README was the reference's, verbatim**, and false about
  this pack in its provenance, denominator, vocabulary and enforcement claims.
  Replaced.
- **The registry permit is a standing grant to a principal the deployed stack
  cannot assume**, the shape ADR-048 removed. Kept, because a committed verified
  service is the un-cut ADR-048's own scale-up path names, and stated in an
  amendment rather than left for the next reader.
- **MER-AI-0001 reaches this service and no control binds to it.** Recorded as
  owed to Legal/S&P against the rule's 2026-10-01 review, not claimed handled.
- **No contract test or CI step reads this pack.** Stated in the pack's README and
  the record; extending `tests/test_contracts.py` is two-key and owed.

## Checked

- `python -m pave.cli verify --all`: PASS for both services.
- `python -m pave.cli policy generate --check`: current.
- `make check` on this tree: 5448 passed, 10 skipped.
- `pave/` untouched, by necessity: `tests/test_drill_pins.py` freezes `pave/cli.py`
  behind the M11 readers transcript. PR #166 found that the hard way.

## Attestations

Two-Key-Disposition: ai-quality
Two-Key-Rationale: twenty cases authored before any run, citing only the three committed sports titles, two headroom cases at 10 percent on the upper edge of the band, negative bans reduced to three narrative phrasings with the residual risk and the missing no-result assert stated in the pack, no assert on a tool the manifest does not grant, and no contract test reads the pack yet, which is recorded as owed rather than claimed
Two-Key-Disposition: tool-owner
Two-Key-Rationale: one read-class caller line under catalog-search, one permit regenerated with no contract changed and publish-highlight untouched, a manifest that declares only that grant with the template one-tool budgets, and a permit the deployed gateway cannot exercise because its principal is fixed, which ADR-048 amendment 1 and the catalog-search README now say out loud
Two-Key-Disposition: legal-sp
Two-Key-Rationale: the grant is read-class and raises no consequence class, MER-AI-0001 reaches the preview, tile and recommendation cases of this service and no control binds the rule to it, and that gap together with the revives question is recorded as owed to this seat against the 2026-10-01 review rather than described as handled

🤖 Generated with [Claude Code](https://claude.com/claude-code)

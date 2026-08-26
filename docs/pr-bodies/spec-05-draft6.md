# SPEC/05 draft 6 — the first draft written after any of it was built

Docs only. **No code, no test, no threshold, no recorded number.** This branch
triggers **no two-key rule**; the `two-key` job will report *not required*, which is
correct and is what `test_ordinary_pr_is_not_gated` describes.

## Why a sixth draft

Round 5 was **49 blocking findings across six seats**, and its central finding was
not a defect in a mechanism — it was that **PR 2 cannot be built as specified**.
Drafts 1–5 ran 39 / 31 / 20 / 55 / 49. Four of the six PRs have since been built and
merged (#56, #57, #58, #59), so draft 5 now describes work that exists, in some
places differently from how it exists.

A spec left describing a plan that was overtaken is the drift ADR-037 is about, one
layer up.

## What draft 6 does

**Records rather than proposes, for four of the six PRs.** Each is marked LANDED
with its ADR and PR number. Draft 5's item text is **kept as written** — the
differences are stated separately, never edited into the item, because a spec edited
to match the code stops being a pre-registration.

**States the five places the build differs from draft 5**, each measured:

1. The refusal table has **fourteen rows, not thirteen**, and row 10 changed. Draft
   5's row 10 named a `curated_by` pack header that ADR-045 had already measured as
   a 47-failure migration and replaced — it would have failed the reference pack on
   day one. Row 10 is now `gates.eval_min_cases` below the platform floor, **the
   milestone's own opening finding, which draft 5's table omitted**. Row 14 is new
   for `brand`, which draft 5 left enforced by a `print()`.
2. `pave verify` is not a runnable literal; the command is
   `python -m pave.cli verify --all`.
3. `highlights-agent` declares `publish-highlight@^0`. Draft 5 said *"neither fix is
   free"* and priced neither; revoking the grant is **4 failed**, because a tool with
   no callers is unreachable under G3 and M02's recorded `policy` denial needs the
   `permit` to exist.
4. Three criteria draft 5 never mentioned moved into `pave/floors.py`.
5. `COLLECTED_FLOOR`'s first wiring was a check nothing in the repository could
   execute — ADR-042's own finding, inside the fix for it.

**Corrects the ADR numbers.** Draft 5 named four and **three went elsewhere**. The
mapping is a table rather than a silent renumber, because an ADR number is a citation.

**Restates all sixteen predictions with results as run.** Two are recorded **FALSE
as specified** rather than reworded, one is **WITHDRAWN as uncheckable** ("the
starter three" packs do not exist and the phrase is defined nowhere), and two are
**BLOCKED** because predictions 12 and 13 cannot both hold. The deletability tally
across the four PRs is **51 mutations, 49 caught, one correctly silent, one genuinely
missed** — the correctly-silent one was a floor *rise*, which a ratchet must permit;
the miss was a test whose own name claimed the half it did not check.

**Lists seven decisions it does not make**, each with the seat that owns it. Three
block PR 2. **Decision 3 became live rather than hypothetical** when the reference
manifest started declaring a publish-consequence tool: the complete path to granting
a scaffolded service the one approval-interlocked tool collects `tool-owner`,
`legal-sp`, `ai-quality` and **never Security**. Decision 6 is that **Data Governance
holds zero enforced keys** — census counted from `twokey.RULES` rather than quoted:
security 20, platform-eng 20, ai-quality 19, tool-owner 5, legal-sp 3,
data-governance 0 across 29 rules.

## Also lands

`docs/M05-round4-findings.md` and `docs/M05-round5-findings.md` — the complete
records of rounds 4 and 5, with every finding, its command and its number. Both were
untracked. They feed `tests/test_cited_commits_resolve.py`, and every commit they
cite resolves — **and one did not**, which is why this PR has a second commit.
`docs/M05-round5-findings.md` cited a SHA on `m05-paved-road`, a branch that was
never pushed. It passed locally because the object was still in the author's clone
and failed in CI on a fresh checkout, which is precisely the case
`tests/test_cited_commits_resolve.py` was written for. The line now cites no SHA and
says why.

## What is deliberately NOT in this PR

**PR 2 is not built and this PR does not pretend otherwise.** G4's *"and logged"*
half still credits a refusal without examining what refused, so the milestone ships
with its own headline finding open. That is stated in the spec, and must also appear
in M05's journal and the claim-1 footnote at close — deferred, but by name.

## Verification

Full suite **2021 passed**, ruff clean, hermetic, zero model calls. Rebased onto
`main` at `20c154a`. `twokey.triggered()` over every path in this diff returns no
rule.

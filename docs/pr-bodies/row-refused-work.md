# The `06b` row was copied forward past a question nobody asked

ADR-055. Found before any M06b work started, by reading the decision the row's
text was copied past. **Narrowed after the Legal/S&P seat's first-pass review
rejected this PR's original conclusion** — see *What changed after review*.

## What was on `main`

`README.md:42` published M06b as *"2nd tool + consequence interlock"* and
`BUILD.md:22` as *"`publish-highlight` + Step Functions approval"*. ADR-054
produced both by **copying the M06 row's text**. Nobody re-derived it against the
record, and the record holds exactly one disposition on deploying
`publish-highlight` — `SPEC/06` **Decisions 1**:

> *"`publish-highlight` deployment. Answered by Legal/S&P: no… Recorded so it is
> not re-opened."*

## The question this PR does NOT answer

Whether that refusal is **standing** or **scoped to M06** is genuinely open, and
ADR-055 records both readings rather than picking one.

**Toward standing:** no milestone qualifier; *"recorded so it is not re-opened"*;
the consequence is deletion; the granted exception pins a permanent replacement
string for `schema.in.json:16`.

**Toward scoped:** `SPEC/06` **Decisions 2** is titled *"Where the interlock work
is numbered"*; A5's own words are *"no deployed endpoint **at M06**"*; A5's stated
reason for deleting is *not* "the control is not coming" but "don't ship
assertions of a control you haven't built" — and its chosen precedent is
`entitlement-check`, declared-not-built and now being deployed; and
`milestones/M06/README.md:11-14`, committed under tag `m06`, says *"a new `06b` row
carries `entitlement-check`, `publish-highlight`, the trajectory eval and claim
10."*

**Legal/S&P owes the disposition.** Whether a seat's refusal is permanent is that
seat's call, and inferring it from a document's shape is what G9 exists to
prevent. ADR-055 hands over the question and the seat's recommended vehicle: a
rule record in `rules/` with `owner_seat`, `source`,
`disposition.controls[] = {type: cedar_policy, ref: GATED_CONSEQUENCES}` and a
`review_by`, collecting `(legal-sp, security)` plus an ADR — because *"recorded so
it is not re-opened"* with no control and no clock is an orphan and an immortal
rule at once.

## What IS decided, and it holds under either reading

**A progression row may not publish work whose authorization is open.**

- Standing → the row published work a seat has refused.
- Scoped → the row published work still needing a deployment approval **the record
  has never granted**; Decisions 1 is the only disposition on it and it says no,
  whatever its scope.

| | before | after |
|---|---|---|
| `README.md` 06b | 2nd tool + consequence interlock, `m06b-consequence` | Trajectory eval + `entitlement-check`, `m06b-trajectory` |
| `README.md` claim 10 `M` | `06b` | **`—`**, ⬜ UNSCHEDULED with the open question named |
| `README.md` § footnote | *"until M06's trajectory eval"* | the eval is M06b's |
| `BUILD.md` 06b | interlock + approval | trajectory eval **first**, then `entitlement-check`; open disposition named |
| `BUILD.md:43` | *"Trajectory evals turn on at M06"* | M06b, correction marked |
| `tests/test_history_append_only.py:717` | *"`m06b` — the interlock work M06 did not build"* | the anchor's row no longer carries it |

**Claim 10 is UNSCHEDULED, not REFUSED.** `—` is the cell both readings agree on
and the only one that does not pre-empt the seat.

## What changed after review

The Legal/S&P seat planted against the first draft and rejected its conclusion.
Four findings, all upheld:

1. **The original ADR read Decisions 1 as standing on five grounds and never cited
   Decisions 2**, which is a *Decision* titled *"Where the interlock work is
   numbered"* — under the draft's own precedence argument, directly on point.
2. **It discarded `at M06` from A5 as prose while relying on `not softened`** from
   the adjacent sentence of the same entry. Selection, not interpretation.
3. **It resolved a Legal/S&P disposition by inference on zero keys.** That is the
   finding that narrowed this PR.
4. **Its account of A5 became the fifth number for that attack** — the thing A5
   warns about. Corrected below.

## A5's sites, counted correctly

**Thirteen authored = eleven deletions + one granted rewrite (site 2) + one
executing test (site 12).** All live; `git grep -in "stepfunctions\|StateMachine\|stepfn"
-- platform/infra` still returns nothing.

- **Four schema `description` strings, not two.** The first draft omitted
  `schema.out.json:11` and `:12`.
- **`tools.yaml:30` is a declared field, not a comment**, as A5 says. Planted on an
  isolated worktree at `4ee28fd`, deleting `approval: stepfn:editorial-approver`
  while keeping `consequence: publish`: **2 failed** —
  `test_the_committed_policy_set_is_exactly_what_the_registry_generates` and
  `test_publish_class_tools_carry_an_approval_interlock` — plus
  `policy generate --check` **EXIT=2**.
- **`cedar.py:224` is coupled to `tools.yaml:30`**, and it is not what A5 says it
  is. `:224` is the only call validating an `approval:` value, and `:30` is its only
  input, so the first draft's "carry `:224` forward, `:30` is deletable prose"
  validates `"none"` forever. They move together or neither moves. **And it is not
  scheme validation** — `REFERENCE` (`cedar.py:79`) permits a colon without
  requiring one. It is policy-text injection prevention: Security removed only the
  `_identifier(...)` call and a registry `approval:` value injected
  `permit(principal == Service::"attacker-svc", …)`, parsed at 5 policies, an
  unregistered principal `allowed=True`. A5 carries the wrong characterization and
  this PR carried it forward.
- **Site 2 has no vehicle.** The granted exception rewriting `schema.in.json:16` is
  in neither the eleven nor the carry-forwards and is scheduled by nothing. It
  collects `(platform-eng, security, tool-owner, legal-sp)`. Recorded as owed.

**The ten indicative sites do not come back if an interlock is built.** They assert
a control exists; an interlock's schema is authored against what is then deployed.
Restoring them restores A5's finding.

## Cost, stated rather than absorbed

`tests/test_history_append_only.py` is `(ai-quality, security, platform-eng)`.
Fixing its stale comment widens a zero-key documentation PR to three keys. Leaving
a comment that describes a row it no longer describes is the exact defect class
this ADR is about, so it is fixed here.

## What this does not do

- **It does not execute A5.** All thirteen sites are live; that diff is rule 27
  `(platform-eng, security, tool-owner)` plus a `policy generate` run, and owes its
  own ADR and variant list.
- **It does not amend `SPEC/06`.** The record stays as written.
- **It does not add the row-description assertion ADR-054 recorded as owed.** Second
  consecutive finding in that gap; the second adds the *shape* — both wrong texts
  came from *copying a row*, so the cheapest true guard is over row **provenance**,
  not row truth. Not invented at a close.

## Verification

`ruff check .` clean. Hermetic, zero model calls, no new dependency. No
`evals/history/` entry, no comparator, no threshold, no instrument digest, no
recorded number moved.

`tests/test_history_append_only.py:725`'s `m06b` anchor still resolves: the row
keeps its `` `m06b` `` tag cell and its `–` goldens cell, which is the mutation
that test plants.

*Collected count is restated at commit time against `COLLECTED_FLOOR = 2255`
(`pave/floors.py:309`) — an earlier draft of this body cited 2079, which is
ADR-045's figure and was re-seated at the M06 close.*

Two-Key-Disposition: platform-eng
Two-Key-Disposition: security
Two-Key-Disposition: ai-quality
Two-Key-Rationale: The only keyed file here is tests/test_history_append_only.py
  and the only thing that changes in it is the comment above its README anchor.
  No assertion, no fixture, no arithmetic and no collected count moves; the
  anchor still resolves the m06b row by its tag cell and still plants a goldens
  number into a cell that is a dash, which is the mutation it exists to catch,
  so what the instrument measures is byte-for-byte what it measured before. What
  moved is a sentence claiming the m06b row carries the interlock work M06 did
  not build. This diff takes that work off the row, because the record holds one
  disposition on deploying publish-highlight and it is a refusal whose scope is
  open; leaving the comment would have left a three-key file describing a row it
  no longer describes, which is the defect class both ADR-054 and this change
  are about, arriving a third time one file down. Widening a documentation
  change to three keys to fix a comment is the expensive direction and is taken
  deliberately: the cheap direction is to leave stale prose in the file that
  pins how history is read. Nothing outside that comment is touched in any keyed
  path — no threshold, no baseline, no golden case, no comparator, no instrument
  digest, no recorded number, and no evals/history entry. The seat whose
  disposition this diff would most flatter is not asked to supply it: the ADR
  refuses to resolve the Legal/S&P question its first draft resolved, and names
  that seat as owing the answer rather than inferring one.

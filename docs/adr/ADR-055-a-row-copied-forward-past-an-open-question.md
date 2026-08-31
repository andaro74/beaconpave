# ADR-055: a row copied forward past a question nobody asked, and the seat that has to answer it

**Status:** Accepted, and deliberately narrow. **Zero model calls.**
**Seats:** Platform Engineering (the progression table and `BUILD.md`) · Service
Team (the twelve-claims table) · **Legal/S&P — named as owing a disposition this
ADR does not take**

ADR-054 renamed M06 to what it shipped and renumbered the interlock work to a new
`06b` row. It produced that row by **copying the M06 row's text**. Nobody re-derived
it against the record, and the record contains a question that has never been put
to the seat that owns it.

`README.md:42` therefore published *"2nd tool + consequence interlock"* and
`BUILD.md:22` *"`publish-highlight` + Step Functions approval"* as M06b's build,
with claim 10 pointing at the row.

## The question, stated rather than answered

`SPEC/06` **Decisions 1**: *"`publish-highlight` deployment. Answered by Legal/S&P:
no… Recorded so it is not re-opened."*

Whether that refusal is **standing** or **scoped to M06** is genuinely open on the
committed record, and both readings have real support. An earlier draft of this ADR
resolved it as standing on five textual grounds. **That draft was wrong to resolve
it at all**, and the Legal/S&P seat's first-pass review said so: whether a seat's
refusal is permanent is that seat's disposition, and inferring it from the shape of
a document is the failure G9 exists to prevent — the seat that owns a control says
how strong it is. Both readings are recorded here so the seat is handed the
question and not an argument.

**Points toward standing:**

- Decisions 1 carries no milestone qualifier and closes *"Recorded so it is not
  re-opened."*
- `SPEC/06` has four distinct forms for a scoped disposition — Decisions 3 and 4
  *"still open"*, 6 *"A19 closes in M06"*, 10 *"deferred to M07 in full"*, 12's
  three-way *"Closes in M06 / Does NOT close in M06 / Owed to M07"* — and
  Decisions 1 uses none of them. **This is weak on its own**: ten of the fourteen
  Decisions entries use none of the four forms, and several of those are plainly
  scoped (13 is scoped to a single PR).
- Decisions 1's stated consequence is that A5's assertions are **deleted**, and A5
  adds *"not softened"*.
- The exception Decisions 1 grants pins a **permanent verbatim replacement string**
  for `tools/publish-highlight/schema.in.json:16`.

**Points toward scoped to M06:**

- **`SPEC/06` Decisions 2 is titled *"Where the interlock work is numbered."*** It
  is a Decision, not prose, and a decision about where work is numbered sits badly
  with a reading in which the work is refused outright. Its *body* takes no
  numbering decision — ADR-054 says so in as many words, *"takes the decision
  decision 2 left open"* — so it does not settle the question either. But it shows
  `SPEC/06` contemplated the work being numbered somewhere, and the earlier draft
  of this ADR did not cite it at all.
- **A5's own words are `no deployed endpoint at M06`**, and the earlier draft
  discarded that clause as prose while relying on `not softened` from the adjacent
  sentence of the same entry. That is selection, not interpretation.
- **A5's stated reason for deleting is not "the control is not coming."** It is
  *"A schema describing a control in the subjunctive still ships the control's
  name, and the next reader wires `approval_id` to nothing"* — which applies to a
  deferral exactly as much as to a refusal. And the precedent A5 chooses for it is
  **`entitlement-check`: declared, not built** — a tool `SPEC/06b` is now
  deploying.
- **`milestones/M06/README.md:11-14`**, written at the close and committed under
  tag `m06`: *"a new `06b` row carries `entitlement-check`, `publish-highlight`,
  the trajectory eval and claim 10."*
- `SPEC/06`'s *What M06 must not do* says *"Do not mark claim 10 **advanced**."*
  Advanced, not scheduled. Nothing there forbids scheduling it.

## What is decided, and it holds under either reading

**A progression row may not publish work whose authorization is open.** That is the
whole of this ADR's decision and it does not depend on which way the question goes:

- Under the standing reading, the row published work a seat has refused.
- Under the scoped reading, the row published work that still requires a
  `publish-highlight` deployment approval **which the record has never granted** —
  Decisions 1 is the only disposition on it and it says no, whatever its scope.

Either way the `06b` row asserted a build nobody is authorized to start.

| | before | after |
|---|---|---|
| `README.md` 06b | 2nd tool + consequence interlock, `m06b-consequence` | **Trajectory eval + `entitlement-check`**, `m06b-trajectory` |
| `README.md` claim 10 `M` | `06b` | **`—`**, marked UNSCHEDULED with the open question named |
| `README.md` § footnote | *"until M06's trajectory eval"* | the eval is M06b's; M06 did not build it |
| `BUILD.md` 06b | interlock + Step Functions approval | the trajectory eval **first**, then `entitlement-check`; the open disposition named |
| `BUILD.md:43` | *"Trajectory evals turn on at M06"* | M06b, with the correction marked |
| `tests/test_history_append_only.py:717` | *"`m06b` — the interlock work M06 did not build"* | the anchor's row no longer carries the interlock |

**Claim 10 goes to `—` and is marked UNSCHEDULED, not REFUSED.** Under the scoped
reading it could be scheduled the moment the seat says so; under the standing
reading it cannot be scheduled at all. `—` is the cell both readings agree on, and
it is the only one that does not pre-empt the seat. Parking it on M07 or M10 would
repeat ADR-054's defect one row further down.

**The comment fix costs three keys.** `tests/test_history_append_only.py` is
`(ai-quality, security, platform-eng)`. Leaving a comment that describes a row it
no longer describes is the exact defect class this ADR is about, arriving for the
third time, so it is fixed here rather than recorded as owed — but the widening is
stated rather than absorbed.

## What this does not do

**It does not answer the question.** Legal/S&P owes a disposition on whether
Decisions 1 is standing or scoped, and it is owed as a *decision to be recorded*,
not as a reading to be inferred. The seat's review adds a constructive form for it:
a standing refusal of a deployment class is a **rule record** — `rules/` already
requires `owner_seat`, `source`, `disposition.controls[]` and `review_by`, the
control is nameable (`type: cedar_policy`, ref `cedar.GATED_CONSEQUENCES`' `forbid`,
which is real and works), and `rules/MER-AI-0001.yaml`'s rule collects
`(legal-sp, security)` with an ADR. Recorded as the recommended vehicle. Without it,
*"recorded so it is not re-opened"* is a refusal with no control and no clock.

**It adds no assertion tying a row's description to what shipped or to what a
decision permits** — ADR-054's stated residual, still open. This is the second
consecutive close-adjacent finding in that gap, and the second is the useful datum:
one could be a bad label, two says the residual is real. What the second instance
adds is the **shape** — both wrong texts were produced by *copying a row* rather
than by writing a claim — so the cheapest true guard is over row **provenance**
rather than over row truth. Not invented here, because inventing a guard at a close
is how the last several wrong guards arrived.

**It does not amend `SPEC/06`.** The document is tagged; its ambiguity is resolved
by a recorded decision, not by editing the record to read as though it had always
been clear.

**It does not execute `SPEC/06` A5**, and the accounting below is corrected because
the earlier draft of this ADR became the fifth number for that attack — which A5
itself warns about, and which the Legal/S&P seat caught.

## A5's sites, counted correctly, and what would come back

**Thirteen authored sites = eleven deletions + one rewrite + one executing test.**
The rewrite is site 2, `tools/publish-highlight/schema.in.json:16`, the exception
Decisions 1 grants on the seat's own motion. The executing test is site 12.
All thirteen are live: `git grep -in "stepfunctions\|StateMachine\|stepfn" --
platform/infra` still returns nothing, and `milestones/M06/README.md` lists A5 among
*"three still decided-not-built"* (A5, A12, A18).

Of the eleven, **four are schema `description` strings**, not two — the earlier
draft omitted `schema.out.json:11` (*"Step Functions execution handle the editorial
approver acts on"*) and `:12` (*"Set when Cedar denied the call before it reached
the interlock"*).

**`tools.yaml:30` is a declared field, not a comment**, and A5 says so in as many
words. Measured, on an isolated worktree at `4ee28fd`, deleting
`approval: stepfn:editorial-approver` while keeping `consequence: publish`:

```
FAILED tests/test_cedar_policy.py::test_the_committed_policy_set_is_exactly_what_the_registry_generates
FAILED tests/test_contracts.py::test_publish_class_tools_carry_an_approval_interlock
2 failed, 2253 passed, 6 skipped
$ python -m pave.cli policy generate --check ; echo "EXIT=$?"
EXIT=2
```

Two executing guards and the generator, against the earlier draft's claim that only
site 12 executes.

**If an interlock is ever built, the ten indicative sites are not restored.** They
assert that a control exists; an interlock's schema is authored against what is then
deployed and verified by tests that execute against it. Restoring them restores A5's
finding — sites asserting an interlock while `tests/test_contracts.py:118` passes on
a truthy string naming a state machine that has never existed.

**Two things are owed forward, and they are coupled:**

- **`cedar.py:224`**, `approver = _identifier(tool.get("approval", "none"),
  "approval", REFERENCE)` — the only call validating an `approval:` value at all. A
  validation removal riding inside a prose deletion, which A5 records drafts 1–9 did
  not notice.

  **What it validates is not what A5 says, and this ADR repeated the error before
  the Security seat caught it.** A5 calls it *"the only call validating that an
  `approval:` value carries a scheme"*; `REFERENCE = ^[a-z0-9][a-z0-9:._-]*$`
  (`cedar.py:79`) **permits** a colon and does not require one, so a scheme-less
  value is accepted. `cedar.py:74`'s own docstring says what the check is for: *"no
  whitespace, and no **newline**, which is the character that matters. `_strip_comments`
  removes from `//` to end of line, so a value carrying a newline **escapes the
  comment it was written into** and the rest of it is parsed as policy."* It is
  **policy-text injection prevention**. Measured by the Security seat with only the
  `_identifier(...)` call removed: a registry `approval:` value injects
  `permit(principal == Service::"attacker-svc", …, resource == Tool::"catalog-search")`,
  the policy set parses at 5 policies, and an unregistered principal is authorized
  `allowed=True`. Restored, it raises.

  This matters beyond accuracy: a builder told to preserve *scheme validation* looks
  for a scheme check, finds none, and reasonably concludes the citation is stale —
  which is CLAUDE.md's *stated and absent* shape, on an authorization mechanism. The
  error originates in A5 and was carried here without reading `cedar.py:79`.
- **`tools.yaml:30` is that validator's only input.** Carrying `:224` forward while
  treating `:30` as deletable prose validates `"none"` forever. The earlier draft of
  this ADR did exactly that, and the Legal/S&P seat found it. They move together or
  neither moves.
- **`tests/test_toolplane.py:288-307`** pins the approver literal
  `stepfn:editorial-approver` and the exemption format. Those belong to whatever
  approver is actually deployed; restoring the test pre-commits both.

**Site 2 has no vehicle.** The granted exception — rewriting `schema.in.json:16` to
drop `verified by the interlock` and `the approver sees this flag` — is in neither
the eleven nor the carry-forwards, and is scheduled by nothing. It collects
`(platform-eng, security, tool-owner, legal-sp)`. Recorded as owed. Under a standing
refusal it is the one piece of Decisions 1 with no PR behind it; under a scoped one
it waits on the interlock. It should not wait on the question.

At scale, the progression table and the claims table are projections of the milestone
records and the decision log, and a row naming work whose authorizing decision is
open cannot be rendered, because the disposition is a queryable record rather than a
sentence in a spec. The interface already matches: every row's tag already names an
eval history entry and a journal directory, and every disposition in `SPEC/06`
already names the seat that gave it.

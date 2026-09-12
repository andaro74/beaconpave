# M09b PR 2 — debt 33 paid, and the candidate sweep refused on four grounds

**Zero model calls. Zero AWS calls. No candidate wording, no corpus row, no
deploy.** `make check` PASS, **4518 passed, 8 skipped**, on this branch's head,
tagged `cited-m09b-pr2`.

This PR was scoped to author ten candidate wordings, commit their digest, push it,
and sweep once. **It does not do that, and the refusal is the deliverable.** The
sweep is not deferred for cost or for time — ADR-077 decision 2 §1 permits **no
retry and no second candidate set**, so a sweep taken today burns both topics'
only candidate sets permanently, and four of its inputs do not exist yet.

What it does instead is pay the one debt that came due here and could be paid
without spending anything irreversible, and the payment turned up a live defect.

---

## Why the sweep is refused, in the order the grounds bite

### 1. The additive topic's judging corpus does not exist, and gate 7 fails closed on rows that are not there

ADR-077 decision 3 §7 makes it an admissibility gate that *"the additive topic's
own frozen corpus holds in both directions"*. That corpus is a **PR 2 deliverable
on Security's key plus an ADR** (`SPEC/09b`, *The plan, walked to the claim*, row
3), and `quality/adversarial/` holds no such file today — measured:

```
answer-decomposition.yaml  g4-semantics.yaml       instruments.json
phrasings.yaml             probe-controls.yaml     probes.yaml
refusal-shapes.yaml        tool-plane-probes.yaml  topic-attacks.yaml
topic-attacks-heldout.yaml topic-attacks-output.yaml
```

Decision 3's *fail-closed on unreadability* clause is explicit: *"A row whose
verdict cannot be read — a sweep error, a missing sample, a throwaway that would
not build — fails the candidate."* A gate with no rows is unreadable in the
strongest sense. So all five additive candidates are struck, and the additive
topic takes the no-winner branch **for a procedural reason rather than a measured
one** — which is ADR-035 amendment 5's vacuous confirmation arriving in the
mirror: *"a distinct failure from a falsified row and arguably a quieter one,
because it reads as evidence."* Term 1 of the claim would then be dead, with no
retry available, because PR 2 was skipped.

### 2. Writing that corpus here would invert ADR-024's honesty clause instead of satisfying it

The obvious repair — author the corpus in this PR too — is the worse branch, and
it is a **named seat plant**. `SPEC/09b`, *The seats*: PR 3's rounds are told to
plant *"an ordering check satisfied by a corpus committed in the same commit as
the candidate."*

The direction matters and it is not symmetrical. ADR-024's amendment guards
against a **candidate fitted to a corpus**. Committing the ten candidates now,
before the additive corpus exists, produces the inverse: Security then writes the
judging corpus **having read the candidate wordings**, which is a **corpus fitted
to a candidate**. Nothing in ADR-077 licenses that, and it is strictly worse than
the hazard the whole rule was built against, because no ordering check can see it
— `tests/test_m09b_ordering.py` reads commit order, and the corpus commit would
correctly follow the candidate commit.

`topic-attacks-heldout.yaml`'s own header states the standard this fails:
*"This file is committed before a line of the new topic exists. Anyone can check
that in the history: if the wording commit precedes this one, the check is
worthless and should be treated as such."*

### 3. No throwaway-guardrail instrument exists in this repository

Checked at line, as instructed, before writing anything:

- **`throwaway-gate`** is not a throwaway-guardrail mechanism. It is
  `979fbb2 exhibits: verify the gate blocks` — a **four-line addition to
  `tests/test_contracts.py`**, a deliberately-red contract exhibit. The name
  collides; the content is unrelated.
- **`tools/`** holds `catalog-search/`, `entitlement-check/`, `publish-highlight/`
  and `sweep_sixteen.py`. `sweep_sixteen.py` is a **whitespace-collapsing text
  grep** for every published instance of the number 16; its own header says
  *"Reporting only. Nothing scores, gates or decides on this."*
- `grep` for `create_guardrail` / `CreateGuardrail` across the tree returns **one
  hit**, a prose line in ADR-064. Nothing creates a guardrail.
- `topic_baseline.py` reads `PinnedGuardrailId` from the CloudFormation stack
  outputs and accepts `--guardrail-version` for a **RETAINed version of that same
  guardrail**. It cannot be pointed at a throwaway.

The M06b throwaway was real — `docs/M06b-guardrail-diagnosis.md` records it,
*"created and deleted inside this investigation"* — and **it was never
committed**. That is `SPEC/09b` constraint 12's finding one milestone early: a
measurement whose instrument evaporates.

So the instrument must be built. Sized honestly: a guardrail carrying the full
`topicsConfig`, content filters, PII policy and word policy (a throwaway missing
the filters reports *allowed* on rows production blocks, and gate 3 reads
*still blocked*), a version resource, the sweep, and the teardown — then
**~30 rows × k=3 × 6 arms ≈ 540 `ApplyGuardrail` calls** for the recalibration
alone. That is more than the sweep, which is this PR's stated stop condition. It
is also a **new committed measuring instrument that the PR 3 plant list does not
cover**: none of its eleven plants is *a sweep that reads the production guardrail
instead of the throwaway*, or *a throwaway built without the content filters*.

### 4. The two files that decide the wording are on no two-key rule

Measured through `pave/twokey.py`, which `CLAUDE.md` names as the only authority:

```
milestones/M09b/candidates.json   -> []
tests/test_m09b_admission.py      -> []
```

`SPEC/09b`'s own gap table says so and says what it costs: these files *"join the
deployed-guardrail rule too, `(security, ai-quality)`, **because the file that
admits the definition decides the definition**."* Landing them before PR 2 widens
that rule merges the decision about a deployed security control's wording **on one
key** — G9 exactly, and ADR-035's and ADR-037's finding arriving again.

### What this means for the PR order

Nothing here argues against the work. It argues that **this is PR 3 and PR 2 has
not been taken**, exactly as `SPEC/09b` sequences it. PR 2 owes, before a
candidate is authored: the pre-deploy sweeps at v4/v1 committed as-run; the two
independent withheld readings; the additive topic's frozen corpus with its
`frozen_before`, on Security's key plus an ADR; `tests/test_m09b_ordering.py`; and
the four rule gaps closed in the diff that creates the artifacts they cover.

**The ten axes are not the blocker.** Every one of ADR-077 decision 2's ten cites
to a real owning line, verified at line: A `ADR-024:53-58`; B
`gateway-stack.ts:277-286`; C `:287-291`; D `ADR-035 am4:941-945`; E
`ADR-067:144-146` + `ADR-068:122-124`; F `MER-AI-0001.yaml:130-131`; G `:126-131`
with `ADR-076:151-153`; H `ADR-024:53-58` + `:47-49`; I `ADR-035 am4:948-950`; J
`MER-AI-0001.yaml:57-62`. The axes are ready. Their gates are not.

### On the ordering this PR was asked to demonstrate

Stated as instructed, and it is unchanged from what **F-4 already publishes**: a
pushed digest commit **constrains commitment, not authorship**. It proves when
bytes landed; the hazard is what the author had read. `ADR-076` amendment
1:438-446 says no test can close it *"because the evidence does not exist in the
repository."* Nothing in this PR should be read as proving candidates were not
tuned — and nothing here claims it, because there are no candidates.

---

## Debt 33, paid, and the live instance it found

> **33.** Only *Demo artifact* blocks are checked. `DEMO_HEADING = "## Demo
> artifact"`; blocks outside such a section are unchecked.
> Owner: PM + Platform Engineering. Re-dated at PR 1d to PR 2.

**It is paid, not re-dated a second time.** And it was not a hypothetical.

`DEMO_HEADING` matches an exact string. **Three specs spell their heading
`## The demo artifact`** — three words — so `_demo_section` returns `None` for
them and `tests/test_documented_commands.py` has never seen them:

| spec | heading | fenced blocks inside |
|---|---|---|
| `SPEC/03-evals.md` | `## The demo artifact` | 0 |
| `SPEC/04-gate.md` | `## The demo artifact` | 0 |
| **`SPEC/06c-instrument-repair.md`** | `## The demo artifact` | **1 × ```bash** |

**SPEC/06c's demo block has never been run by the check that exists to run demo
blocks**, from M06c to now.

`test_the_scope_is_every_spec_that_publishes_a_demo_block` exists precisely to
catch this — its docstring says a spec joins the check *"by having one, not by
anyone remembering to add it."* It did not catch it, and the reason is
structural: **both sides of its equality are derived from `_demo_section`.** A
spec the reader cannot see is absent from `publishing` and absent from `CASES`
alike, and the two sets agree about it **by being empty on both sides**. That is a
summary reporting a clean sheet having compared nothing — the defect
`tests/test_topic_baseline.py` records about itself, one file over.

### What the fix is, and what it deliberately is not

**The run scope is not widened.** SPEC/06c's block is
`run_evals --record --tag m06c`, which **appends to `evals/history/`**. Demo
commands are read-only by construction (`test_no_demo_command_writes_to_the_tree`)
and history is append-only and never rewritten. A check that ran it on every
`make check` would author the record it measures — a worse defect than a demo
command nobody runs. The block is correctly out of scope.

What changed is that **it is out of scope by a declaration with a reason rather
than by a heading typo.** `UNRUN_BASH_BLOCKS` names every `bash` block in
`SPEC/*.md` and `README.md` this module does not run, keyed by path to a count,
each carrying the property that keeps it out. `test_every_bash_block_is_run_or_declared_unrun`
holds the declaration against the measurement **in both directions**: a new unrun
block is red, and a declaration whose block has gone is red.

Two entries today: `README.md` (the Quick start deploys and is not on `PATH` in a
clone) and `SPEC/06c-instrument-repair.md` (it records an eval history entry).

**The heading variance is carried as a finding, not repaired here.** Renaming a
heading in three closed milestones' specs is a document change in closed records
and is the PM seat's call; and the block-level check already makes any *future*
block under such a heading red. Owner: PM + Platform Engineering. Trigger: the
next PR that edits a `## The demo artifact` heading or the scope check.

---

## Deletability audit, at CHECK granularity, run through the gate

Full record: `milestones/M09b/pr2-deletability-audit.txt`. One test, two
assertions, audited in both directions.

| plant | mutation | verdict |
|---|---|---|
| 1 | a new undeclared ```bash block appears in a spec | **CAUGHT** |
| 2 | a declaration goes stale — an entry naming no block | **CAUGHT** |
| 3 | an exemption reason cut below the floor | **CAUGHT** |
| 4 | delete CHECK A (`found == declared`), 555 bytes | SILENT — gate PASS |
| 5 | delete CHECK B (the reason floor), 416 bytes | SILENT — gate PASS |

Plants 4 and 5 are the delete-the-check direction, and read as **uniqueness**:
nothing else in the 4512 checks those two gate runs collected holds either
property. Paired with 1–3, which show
both assertions biting, they are live checks rather than dead ones.

**PLANT 3 was run twice and its first verdict was wrong, recorded rather than
replaced.** The first mutation replaced one string literal of a multi-literal
concatenation and verified only that the token was present. The gate came back
green and that would have shipped as a SILENT check. It is not: the reason is a
concatenation, the other forty words stayed, and the property the check reads
never moved. Asserting a token instead of the property is how that gets missed.
The recorded run replaces the whole value and verifies
`len(UNRUN_BASH_BLOCKS["README.md"].split()) == 1` against a floor of 12.

**What CHECK B is worth, stated rather than implied.** It stops an entry added
with `""` or `"TODO"`. It is satisfiable by padding; no deterministic check can
tell an argument from twelve words of filler, and **the assertion message says so
to the reviewer who hits it.** A check that read stronger than it is would be the
same defect one level out.

---

## Counts, each against the commit that produced it

- **`cited-m09b-pr2` (this branch's head): `python -m pave.cli check` PASS,
  **4518 passed, 8 skipped**, 157.41s. Tagged rather than cited by hex because the
  head SHA of a branch moves on every amend and again at merge, and
  `tests/test_cited_commits_resolve.py` is right to refuse a SHA reachable from no
  ref -- it refused this body's first draft, which cited an amended-away SHA twice.
- The audit's plant runs were taken on the tree carrying only the test edit:
  **4512 passed, 8 skipped, PASS.**
- **No delta is published against PR 1d's 4499.** A different tree; the two are not
  subtractable. Every check between 4512 and 4518 is accounted for and none is
  inferred: three per-file parametrizations over the new
  `milestones/M09b/pr2-deletability-audit.txt` and three more over the new
  `docs/pr-bodies/m09b-pr2.md` --
  `test_no_tracked_blob_carries_crlf_unless_it_is_binary`,
  `test_no_committed_file_contains_an_aws_account_id` and
  `test_no_committed_file_contains_an_account_qualified_arn`, each parametrized per
  committed file.

## Two-key

`pave.twokey.triggered` over this diff's three paths returns `[]`. No attestation
is required and none is claimed. That `SPEC/` and `docs/adr/` are on no rule
remains the standing debt, unchanged here.

## What this PR does not do

No candidate wording. No corpus row. No sweep, no throwaway guardrail, no
instrument. No deploy. No prompt constant, tier, ceiling, comparator, catalog row,
golden case or judge instrument moved. `SPEC/09b`'s PR 2 Definition-of-done
checkbox is **not ticked**, because PR 2's own deliverables are not in this diff.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

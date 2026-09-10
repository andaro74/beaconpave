# M09 PR 1 + 1b — the open, and the cold read before PR 2

Two commits on one PR to `main`, because workflows only fire on PRs to `main` and
a stacked PR gets no CI.

- **`c391e93` — PR 1, the open.** ADR-075; SPEC/09; rows `09b` and `09c` in
  `README.md`; `BUILD.md`; `SPEC/README.md`; the ADR index row; ADR-026 amendment
  4 and `labels.json`'s `re_deferred_to: "M09b"` in the same diff as the row;
  `docs/governance/demo-script.md`'s Act 3 corrected.
- **PR 1b, the cold read — this PR's second commit.** ADR-075 amendment 1, by a
  reader who did not write SPEC/09 or ADR-075, before PR 2 cuts. Named by its role
  and not by its sha: a squash merge destroys it, and ADR-074 amendment 3 §9 is the
  precedent — *"PR 3's own commits are deliberately named by their role and never by
  SHA, so no sentence here acquires a fuse."* `c391e93` earns a tag instead, because
  the amendment cites it in text that outlives the branch.

**Zero model calls. No deploy. No seat round. No code, no rule, no case, no
threshold.**

## What PR 1b is

SPEC/09 reserved a sixth slot by name — *"a cold read of this spec by a reader who
did not write it, before PR 2 opens: run the checks this file names rather than
reading it, and answer in an amendment to ADR-075."* This is that slot, taken
deliberately rather than discovered, on M08b PR 1b's precedent.

Every number in the amendment is produced by running committed code over committed
evidence. Each is a check a seat can repeat.

## The five questions, answered

**1 — Is this becoming M06b again?** Not on the dimension that broke M06b: every
falsifier closes the milestone red with a named case, constraint 9 opens exactly
one bounded door, and no diagnosis is authorised anywhere. It is **M06c's shape in
four places** rather than the one ADR-075 found — four Definition-of-done clauses
the plan beneath them cannot reach. And it carries **one M06b entry point: PR 3**,
whose next step after the red below is unbounded.

**2 — Each claim, its measurement, and the PR.** A table over all 22 rows plus the
prose claims. **Three claims have no measurement in any PR of this plan**, and none
of them is one of the three ADR-075 cut: the M02 prompt's lineage pin, the census
record, and the *nothing else moving* half of the one claim.

**3 — Is PR 4 M07 PR 4's shape with a run added?** It is M07 PR 4's shape with
**two** runs added, a two-key disposition and three unnamed pins — thirteen listed
subjects and three unlisted ones, against M07's five. But the attribution weakness
is not where the question puts it: **run A and run B are the plan's strongest
attribution** — same deployment, same guardrail versions, same day, one sentence
apart — and separating them would be the M06c defect of splitting one job because
half of it is cheaper. **F4's control run is the problem**: it has no twin in this
milestone, and its comparator is M08b's run, one DMA rename away. It moves to
PR 4b, which costs the cap nothing because PR 3 vacates a slot.

**4 — Which population does PR 2's `p95_ms` condition execute over?** M08b's 38
answered mandated-shape samples, read through `context_census.mandated_calls()`
and `evals.deterministic.suite_latency`. **p95 5241, n 38 — reproducing ADR-074
amendment 3 exactly**, so the population is the one M08b read.

| population | n | p95 | floor 1.15× | roof 1.60× | midpoint | point |
|---|---|---|---|---|---|---|
| mandated shape (**the rule**) | 38 | **5241** | 6027.15 | 8385.60 | 7206.375 | **7200** |
| as-run ≤3 call | 58 | 5683 | 6535.45 | 9092.80 | 7814.125 | 7800 |
| pooled | 70 | **6633** | 7627.95 | 10612.80 | 9120.375 | 9100 |
| above mandate | 32 | 7223 | 8306.45 | 11556.80 | 9931.625 | 9900 |
| ≥4 call | 12 | 8437 | 9702.55 | 13499.20 | 11600.875 | 11600 |

**The condition holds under none of the five.** Under the same-population reading
it is unsatisfiable by construction: the point is `1.375 × p95` rounded, strictly
above the p95 it came from, so that run can never read OVER it. At M07 the rule
took *"the only population under which the run in view fails the gate"*; **here
there is no such population**, which is what a failed premise looks like when the
rule that rested on it is re-applied. So `p95_ms` stays **5200**, ADR-014's
stability sentence is withdrawn, the gate is re-described as a fixed ceiling with a
recorded derivation, and the re-derivation dates to **09c**. The gate should not
move in PR 2: M09's own fresh population is one PR away, not one milestone.

**5 — Should F4 guard direction, and is the token bound the right measurement?**
**Yes to direction, and the two falsifiers should move into F4 rather than sit
beside it.** `N` is a sum over 25 cases and is insensitive to compensating
movement; at M08b the count moved 12 → 10 while **no** direction falsifier fired,
and that journal's own conclusion was that a k=3 majority on a one-sample margin is
not a stable instrument. A band the milestone recorded as unstable is doing
claim-deciding work while two stable per-case predicates do side-prediction work.
That reallocation also resolves a contradiction: **F4 says a count outside [8, 12]
falsifies the claim, while *Beside the claim, and not it* and the PR 4
Definition-of-done box both say a band miss does not** — three sites, two answers,
about the sentence that decides whether the milestone closes red.

**No to the token bound, twice.** It is a budget test, not a content measurement,
and nothing hermetic can measure a prompt's effect on content. And **as arithmetic
it is wrong by the call count**: `usage.tokens_in` is the sum across calls (checked,
70 of 70 M08b samples), 6782 is `headroom-005` sample 3 at **three** calls, and the
system block is re-sent every round. `6782 + delta < 7700` admits **delta ≤ 917**
where the claim survives **delta ≤ 306**. A 400-token disclosure sentence passes the
test that prices the fix *"before a single call is spent"* and puts `headroom-005`
at **7982**, falsifying F4 on the run the test was written to protect.

## What was measured, not argued

Every plant was written to a working copy backed up to a temp directory, restored
from that backup and **never with `git checkout`**; `git status --porcelain` was
empty after each.

**The fix, planted into `TOOL_SYSTEM`** — one disclosure sentence — goes red on
three committed checks SPEC/09 names nowhere:

```
FAILED tests/test_gateway_run_parity.py::test_the_m02_prompt_is_hash_pinned
FAILED tests/test_gateway_run_parity.py::test_the_m02_prompt_is_the_control_prompt_minus_the_catalog_and_nothing_else
FAILED tests/test_m08_census.py::test_the_record_is_what_the_committed_inputs_produce
```

`tests/test_gateway_run_parity.py` is `(platform-eng, security)` and the census
record is three keys, so **PR 4 edits the attribution pin and the census record in
the same PR as the runs they protect.** The pin's own docstring calls updating it
*"an ADR-021 event: say so in the progression row, and do not do it between the two
arms of one comparison."*

**The DMA rename cannot land in M09.** Planted the minimum consistent rename —
`cedar-point` → `elmridge` across `data/catalog.json`,
`tools/entitlement-check/schema.in.json`,
`platform/gateway/policy/tools.contracts.json` and the golden cases file, which is
the smallest set that leaves the enum, the contract and the values the cases send
agreeing:

```
census --check: exit 1   DRIFT
fresh_join --check: exit 1
  edge-024 sample 1: trajectory step 2 carries args entitlement-check's contract refuses

FAILED tests/test_m08_census.py::test_the_record_is_what_the_committed_inputs_produce
FAILED tests/test_gateway_run_parity.py::test_the_tool_specs_the_model_reads_are_hash_pinned
FAILED tests/test_gateway_run_parity.py::test_the_prompt_half_is_untouched_by_the_amendment
FAILED tests/test_contracts.py::test_poisoned_catalog_differs_from_the_clean_one_only_as_intended
FAILED tests/test_judge.py::test_a_directory_from_an_unrecorded_instrument_is_refused_by_the_scoring_path
```

**The rename retroactively invalidates committed evidence against the live
contract — and the evidence it invalidates is the run F4 compares against.** The
three ways out are re-producing nine milestones of trajectory records, editing
committed evidence, and sliding; the first is unpriced work with no cap slot behind
it, and the second is forbidden in as many words. It also moves the golden cases
file (`viewer.dma`), which *What must not happen* forbids, and collects five
two-key rules SPEC/09 does not name — including `quality/adversarial/tool-plane-probes.yaml`
at **Security alone with `requires_adr`**, in a milestone whose constraint 1 says no
corpus moves. Sixty files name the six markets, and three of the files the rename
must move are on **no two-key rule at all**.

**`pave.twokey.triggered` over the file lists as SPEC/09 names them.** PR 2: 13
rules, all five enforced seats, **five files on no rule** — `pave/cli.py` and
`pave/rules.py`, which are the whole of row 1a's chain reader, plus its two pins,
plus `classify.py` which PR 2 exists to cover. PR 4: 5 rules, **seven files on no
rule**, including both verdict files and the run-A answers — the evidence F1, F2, F3
and F5 are read from. The census rule names `milestones/M08/`, `milestones/M08b/`
and `tests/test_m08b_*` by name; there is no `M09` clause.

**Two more, checked rather than assumed.** `rules/schema.json` puts PR 2 under
`^rules/` with `requires_adr=True`, and `adr_records` reads the **diff**, not the
body — so PR 2 owes a decision record the plan does not give it. And the disclosure
comparator pin has **no lane that reads it** (`pave/cli.py` calls `_suite_pin` with
two literals, `goldens` and `adversarial`) and **no committed run to pin** at PR 2.

**What holds.** `pave/gate.py` never enumerates suites, `NON_BLOCKING` is
`{PASS, ADVISORY}`, FAIL → exit 1: decision 4 is right and rows 4, 10 and 11 are
reachable. `ai_disclosure` is `null` on all 56 committed M08b samples that carry
it, so **F1's premise is sound on the evidence**. The caller-side claim holds —
`handler.py` receives `system` in the event. `check_readme`'s `tagged` set is
`suite == "goldens"` only, as decision 4 says.

## Eleven asks, none of them made here

The amendment lists eleven changes to SPEC/09. **None is made in this diff.** Asks
5 and 6 — moving the goldens control run to PR 4b, and vacating PR 3 — are the
operator's the way decisions 1–4 and 6 were, and the re-scoping in ask 6 needs
Legal/S&P and Data Governance with an ADR: *a rename of the market vocabulary is a
change to the system under measurement, not a documentation tidy*, and A21 has been
carried as the latter through five milestones.

## The cap, and the fallback it fires

SPEC/09 caps M09 at six and names PR 1b the sixth. **Taking it spends the cap, and
*Bounded*'s fallback fires by name: ADR-053's *no orphan rules* half re-dates to
M09b in the close's journal. *No immortal rules* does not give way.** This is that
debt's second dated slide and the only one the milestone pre-authorises.

**The DMA rename slides a fifth time, and that is a finding**, recorded here before
PR 3 rather than discovered at PR 3 or at the close. PR 3's slot is vacated and
spent on PR 4b, so the six are PR 1, PR 1b, PR 2, PR 4, PR 4b and PR 5. **There is
no PR 3**, PRs 4 and 5 keep their numbers, and every reference in SPEC/09 and
ADR-075 stays valid — ADR-074 amendment 1 §6's shape exactly.

## Housekeeping in this diff

- The ADR index row names amendment 1, with `tests/test_adr_index.py`'s **≤10
  ratchet unmoved at 10**.
- `c391e93` is tagged **`cited-m09-pr1`** and the tag pushed before this PR merges,
  so `tests/test_cited_commits_resolve.py` reads main-or-tag green over this text
  and stays green when the branch is gone (ADR-074 amendment 3 §9's mechanism,
  `close-milestone` step 7). Every other reference in the amendment is to a path, a
  test name or a number, and none acquires a fuse.

## Checks

- `python -m pytest -q` → **4000 passed, 6 skipped**. Baseline before the amendment
  was 3993 passed, 6 skipped; the seven are `test_cited_commits_resolve.py`'s new
  parametrised cases for `c391e93`, green via the tag.
- `python milestones/M08/context_census.py --check` → OK
- `python milestones/M08b/fresh_join.py --check` → OK
- `python -m pave.cli gate history --base main` → PASS
- `python -m pave.cli rules validate` → 1 rule, valid
- Both predicted reds on this text fired before they were fixed — the index row and
  the citation — which is the citation rule running over a PR's own text before it
  merges, as constraint 11 requires.

## Two-key

**`pave.twokey.triggered` over this PR's file list returns zero rules.**
`docs/adr/ADR-075-*.md` and `docs/adr/README.md` are on none. No attestation is
owed and none is claimed.

## Deletability audit

**No check is added by this PR.** It adds one ADR amendment and one index row; the
audit has nothing to delete, and saying so is the audit's result rather than its
omission.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

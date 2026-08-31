# SPEC/06b — the trajectory eval

**Status:** draft 3. **Zero model calls.**

Draft 1 carried seven attacks, and **all seven reproduced exactly** under three
independent seats. What did not survive was the arithmetic around them and several
of the conclusions drawn from them. Draft 2 kept the register, corrected every
number, and added six entries the seats found — one of which is a design blocker on
this milestone's own second step.

**Draft 3 withdraws one of those six.** B13 claimed two committed history entries
contradicted each other about four unearned passes, and called it blocking. The
facts were right and every conclusion from them was wrong: the entries agree, the
difference is declared in the instrument, and the attack B13 said was undefended is
caught three ways. It is replaced by the obligation that was hiding under it — one
this milestone **creates** rather than inherits. Recorded rather than deleted,
because a register that quietly drops a claim is the thing this document exists to
prevent.

## How to read the numbers in this document

Every figure was measured by running the command printed beside it.

**Read the register's results as deltas, not as absolute counts.** An entry says
either *"baseline"* — meaning the suite came back exactly as it does with no plant —
or it names the tests that failed. The absolute number is unstable by construction:
it moves whenever any `.md` under `docs/` or `SPEC/` gains or loses a backticked SHA,
because `tests/test_cited_commits_resolve.py:52` scans `(ROOT/d).rglob("*.md")` — a
**filesystem** glob, not `git ls-files` — and a second `+2` per file lands on commit
from `tests/test_no_account_identifiers.py:125`, which does use `git ls-files`. This
document's own baseline moved twice while draft 2 was being written, from its own
citations. `SPEC/06` recorded the same hazard: *"this document's own length is
load-bearing on another PR's mergeability."*

Measured ladder on `main` at `332b16d`, with the ADR-055 row correction merged
(`pytest -q`):

| tree | passed | skipped |
|---|---|---|
| this file **absent** | **2261** | 6 |
| this file present, **untracked** | **2263** | 6 |
| this file **committed** | **2265** | 6 |

**This ladder has now moved three times, twice from this document's own
citations** — draft 2 carried four backticked SHAs and carries two after the
rewrite, and the row correction merged underneath it. That is the argument for
deltas, made by the document against itself.

**B1–B7 were first measured at a baseline of `2259 passed, 6 skipped`** and
independently reproduced by three seats at a baseline of `2261` — same plants, same
failing test names, same verdicts. **Draft 2 printed those absolute counts and was
wrong to**, in a section that had just told the reader to read deltas: the merge of
the row correction moved every one of them. The entries below now state the delta,
which is what actually reproduces. Committing this file costs **+4** on the current
text.

Draft 1's error was never the measurements, which were right for the tree they were
taken on. It was the claim that this file would be worth *"+2 … (no backticked SHAs
in it)"*.

**`COLLECTED_FLOOR = 2255`** (`pave/floors.py:309`). Draft 1 said 2079, which is
ADR-045's figure; `pave/floors.py:260` records it being raised at the M06 close, and
this is M06b. **Real slack against the enforced floor is single digits, not 182.**
That is not a footnote: B7's second plant lands the suite at 2255 on a tree without
this file — the last value that does not trip `pave/cli.py:1135`.

**Two methodological warnings for anyone replaying these plants.**

- **Every plant needs its restore line, and every replay needs `git diff --quiet`
  after it.** Draft 1 printed destructive `sed -i` against
  `services/highlights-agent/evals/golden/cases.yaml` — the two-key, AI-Quality-owned
  golden corpus — with no restore. During the seat round that file was found
  mutated. *How M06b closes* mandates replaying every attack at the tag; a replay
  that leaves the corpus pointing at `not-a-tool` and is followed by
  `run_evals.py --record` writes history against a mutated corpus. **Replays also
  need their own tree**: four seats planting concurrently in one working tree
  produced three false results and one discarded in-flight plant during this round.
- **Any byte change to `platform/gateway/core/audit.py` or `core/toolloop.py`
  produces 15 content-independent failures.** `evals/adversarial.py:897` folds them
  into `capture_sha256` and `guardrail_sha256`. Control, measured: appending a bare
  newline to either file → **15 failures**, content-independent. A builder attacking those files
  will read those 15 as findings unless this is said first.

**A21 debt, declared.** B8 cannot be stated without quoting the six DMA names, four
of which A21 measures as real place names in a rename deferred to M07 *in full*. A5's
standard applies — *a register must quote what it describes* — and every occurrence
here is inside a block describing the enum that is the attack. Counted so the M07
rename knows: 15 occurrences across six names.

This document is a register of attacks, each with a plant that reproduces it. It
carries **no numbered PR plan, no prediction list and no definition-of-done
checklist** — a cut taken from measurement: `SPEC/06`'s register was stable from
round 9 while its nine-PR plan broke in every round. A fix written in prose is a
claim, and claims need plants.

## Which claim this serves

**None directly.** No entry in the twelve-claims table says *the platform can tell a
tool that was called from a tool that was claimed*. What this milestone would make
true is four other published things:

- **The eleven `entitlement_source` asserts**, evaluated on every run and scored on
  none (ADR-016).
- **Act 0's punchline** — the ungoverned control reporting `source:
  entitlement-check` without having the tool — against which the governed platform
  still cannot demonstrate it does better.
- **`SPEC/02`'s pre-registered cost.** M02 took a golden-score loss on purpose by
  taking the blackout table out of the prompt, and wrote that *"M06 is where it is
  repaid."*
- **The control's fabrication, which the live instrument cannot see.** Draft 1 said
  *"four `m00b` passes have been unearned since the control was recorded"*, and
  draft 2 said that claim was invalidated. **Both were wrong, in opposite
  directions** — see B13. The true statement is sharper: under instrument B,
  `entitlement_source` is deferred, so the control claiming a tool it does not have
  costs it **nothing at all** and is recorded in no score. The trajectory eval is
  what makes that assert scoreable again, at which point the control fails those
  cases honestly instead of them quietly not counting.

Claim 10 is not in this list and must not be moved. Whether the consequence
interlock is refused permanently or only for M06 is an **open Legal/S&P
disposition** (ADR-055); its `M` cell is `—`, unscheduled rather than refused.

## What is being built, and why the order is now forced rather than chosen

1. **A trajectory eval** — an assert that reads *what the plane authorized* and
   scores whether the tool a case names was actually invoked before the answer.
2. **`entitlement-check` deployed** — the second model-chosen tool.

Draft 1 put the eval first because *"an eval built after the tool is built against a
passing case."* That argument still holds, and the seat round supplied two stronger
ones pointing the same way. **Step 2 is now the blocked step, not merely the second
one:**

- **B8** — its shipped input contract re-inlines the blackout vocabulary, which this
  document's own *must not do* list forbids and an existing test enforces.
- **B9** — deploying it is what makes a forged lake-side trajectory reachable for
  the one tool the eval reads.

Neither is a file to edit. Both are decisions above this document.

## The register

Thirteen attacks. Each states the plant, the command, the result, and the restore.
Read the results as deltas: *baseline* means the suite came back unchanged. B1–B7 are
draft 1's, independently reproduced by three seats and reported at their 2261
baseline. B8–B12 are the seats'; B13 is draft 3's, and it refutes a draft-2 entry.

---

### B1 — the entire trajectory contract is deletable in silence

Twelve golden cases carry `trajectory.expect_tool_before_answer: entitlement-check`;
eleven carry `entitlement_source`. Both name the same missing tool. One is guarded
three deep, the other by nothing.

```
$ cp services/highlights-agent/evals/golden/cases.yaml /tmp/cases.bak    # RESTORE FIRST
$ python - ...   # delete every `trajectory:` block; verify count -> 0 before counting
$ python -m pytest -q | tail -1
BASELINE -- no failures, the suite comes back exactly as with no plant
$ python -m ruff check . | tail -1
All checks passed!
$ cp /tmp/cases.bak services/highlights-agent/evals/golden/cases.yaml && git diff --quiet -- services/highlights-agent/evals/golden/cases.yaml
```

Contrast — the *deferred* assert beside it is defended:

```
$ sed -i '/^    - entitlement_source: /d' services/highlights-agent/evals/golden/cases.yaml
FAILED tests/test_contracts.py::test_cases_asserting_an_entitlement_verdict_require_the_tool
FAILED tests/test_deterministic_runner.py::test_entitlement_source_is_evaluated_but_never_scored
FAILED tests/test_judged_entry.py::test_the_entry_records_what_scored_the_deterministic_half
3 failed
```

The one guard touching `expect_tool_before_answer` checks the **name**, not the claim:

```
repoint all 12 -> catalog-search  (registered)    BASELINE             # free
repoint all 12 -> not-a-tool      (unregistered)  1 failed
                 FAILED tests/test_contracts.py::test_trajectory_expectations_name_registered_tools
```

ADR-035's shape a third time — thermometer guarded, thermostat not — on the field
this milestone's headline is built from.

**What a fix must survive:** all three plants; a `trajectory` block *added* to a case
that should not have one.

---

### B2 — the trajectory the eval would read is the gateway's own word

`platform/gateway/core/audit.py:80`'s `build_record` takes `request_id, ts,
principal, service, classification, decision, mechanism, model_id, guardrail, usage,
error, probe_id, tool, seq, witness`. **No `trajectory`.** At `handler.py:433`,
`common_out` is spread into the **returned dict** on all three paths and into no
`build_record` call. `run_with_tools.py:171` commits that self-report.

```
# run_with_tools.py:171 -> a hardcoded step naming a tool nothing called
$ python -m pytest -q | tail -1
BASELINE                      # ruff clean
```

The pre-flight guard added for exactly this class (`run_with_tools.py:246`) is
**satisfied by the forgery**, because the forged step says `allowed`.

**The lake is a field-complete witness, and draft 1 understated this.**
`toolloop.trajectory()` and `_tool_records` both iterate `outcome.calls` and emit the
same field set, so every field the trajectory carries is recoverable from
`{record.tool.*, record.seq}` by an independently fetchable path. The lake holds the
*same* thing, not a different one — which makes a lake-side derivation better by a
measurable amount, not merely differently sourced. **B9 is why that is still not
sufficient.**

Nothing pins the two derivations equal. Planted `trajectory()` reporting
`allowed`/`none`/`[]` unconditionally:

```
FAILED tests/test_tool_loop.py::test_the_trajectory_records_what_was_asked_and_what_the_platform_said
E  assert ['allowed','allowed'] == ['allowed','denied']
```

**Exactly one test**, and it compares the trajectory to decisions in the same
in-process object — never to the records `_tool_records` writes. Also: the
`TurnFailed` path (`handler.py:402-419`) returns `tool_records` and **no `trajectory`
key at all**, which is a live input to B3's vacuity.

**What a fix must survive:** the forged trajectory; a trajectory naming the right
tool with `decision: "denied"`; `tool_records` ids that do not resolve in the lake;
a response trajectory and lake records that **disagree**, which must be a hard
failure rather than a preference for either side; and **B9's forged record**.

---

### B3 — a complete, plausible, entirely vacuous trajectory eval is green at zero keys

`evals/deterministic.py:241` is `score_case(self, case, record, catalog)`. `record`
is `{"answer": ..., "usage": ...}`. **No parameter could carry a trajectory**,
`run_evals.py` does not contain the word, and the `-trajectory.json` sibling written
at `run_with_tools.py:254` is read by nothing. So the natural implementation treats
a missing trajectory as "nothing to contradict":

```python
steps = [s for s in (trajectory or []) if s.get("decision") == "allowed"]
if not steps:
    return AssertResult("tool_before_answer", True, "")   # nothing to contradict
```

```
$ python -m pytest -q | tail -1
BASELINE                                  # ruff clean
$ python -c "from pave import twokey; print(twokey.triggered(['evals/deterministic.py']))"
[]
```

**The plant is reachable, and draft 1 did not establish that.** Inverting the same
wiring to always-FAIL produces **9 failures** (see B14 note in *Sequencing*), so the
green is genuine vacuity and not dead code. A green plant that never executes proves
nothing; this one executes.

**It is worse than "PASS when no trajectory is supplied."** Measured:

```
trajectory key absent      -> True
trajectory present, empty  -> True
tool called but DENIED     -> True      <- fails OPEN on the security-relevant case
```

`denied` steps are filtered out, so the refused call falls into the vacuity branch.

**Both obvious anti-vacuity guards are themselves vacuous.** *Guard A* — "prove it
can fail" on a synthetic trajectory — passes on the vacuous implementation, because
it never reaches the `if not steps` branch where the defect lives. *Guard B* — draft
1's own prescription, "run it against the **committed** evidence" — is ambiguous and
the natural reading is vacuous: the answers files carry `['answer','usage']` and no
`trajectory`, so scoring `milestones/M02/runs/m02-tools-1.json` evaluates 12 asserts
and fails 0. **Only reading the *sibling* `-trajectory.json` is non-vacuous, and
draft 1 did not say so.** This repo has shipped that mistake twice (ADR-043's guard
tested a dict's keys not its values; ADR-045's band pin asserted a synthetic pack).

And it is invisible to the one protection that exists: **a vacuous assert moves no
score by construction**, so B7's comparator pins cannot see it.

**What a fix must survive:** the vacuous form; PASS on absent, empty, and
denied-only trajectories; Guard A; Guard B's ambiguous reading; and the `TurnFailed`
path that returns no `trajectory` key.

**BUILT, and here is what it survived.** `evals/deterministic.py` gains
`tool_before_answer`, dispatched from `case["trajectory"]` and appended to
**`deferred`** — the repo's ADVISORY for a deterministic assert, which is Decision
11's safe branch and moves no comparator. Absence is not satisfaction: a missing
trajectory, an empty one, and one where the tool was **refused** all fail, each with
a distinguishable reason. The refused case is the one the vacuous form gets wrong.

Reachability, which draft 2 asked for and did not have, is proved against committed
evidence rather than a fixture — `milestones/M02/runs/m02-tools-1-trajectory.json`,
25 cases and 35 authorized calls, every one `catalog-search`:

```
m00b           scored 18/25 | tool_before_answer evaluated 12, passing 0
m01            scored 19/25 | tool_before_answer evaluated 12, passing 0
m02-tools-1    scored 13/25 | tool_before_answer evaluated 12, passing 0
m02-control-1  scored 17/25 | tool_before_answer evaluated 12, passing 0
```

**Every scored number is unchanged and the assert fails on every run**, because
`entitlement-check` has never been called anywhere. That is the milestone's claim,
evaluated for the first time.

Deletability audited — the vacuous form is **5 failed**, removing the dispatch is
**7 failed**, removing the instrument visibility is **1 failed**. No silent check.

Two things this landing does **not** do. It does not choose the evidence source: the
assert reads whatever trajectory it is handed and reports `no-evidence` when handed
none, so **Decision 3 stays open** and neither answer changes the semantics. And a
deferred assert cannot raise INFRA — it reaches no case verdict by construction — so
the `no-evidence:` marker carries that distinction in a string until the diff that
scores this assert routes it to INFRA. That mapping is the single easiest thing to
lose between here and there, and a test pins it.

**`evals/judged.py` had to be taught about it.** `deterministic_instrument()` walks
`case["asserts"]`, and `trajectory` is a **sibling** of `asserts` — so the new kind
would have contributed a verdict while appearing in neither `scored` nor `deferred`:
the silent instrument move that field exists to prevent, in the field whose own
docstring names ADR-016 deferring `entitlement_source` as its motivating case.
`tests/test_judged_entry.py`'s exact-equality assertion on `deferred` went red on
this diff, which is the behaviour wanted, and is kept as an equality rather than
relaxed to membership.

---

### B4 — the scorer is free, and almost everything around it is keyed

Measured through `pave/twokey.py`, the only authority:

```
evals/deterministic.py                            []
evals/judged.py                                   []
tests/test_deterministic_runner.py                []
tests/test_evals_lane.py                          []
tests/test_judged_entry.py                        []

services/highlights-agent/evals/golden/cases.yaml ('ai-quality',)
tests/test_contracts.py                           ('ai-quality','platform-eng')
tests/test_gateway_run_parity.py                  ('platform-eng','security')
tests/test_instrument_stability.py                ('ai-quality','security','platform-eng')
evals/run_evals.py                                ('ai-quality','security','platform-eng')
evals/history/                                    ('ai-quality','security','platform-eng')
evals/comparators.json                            ('ai-quality','platform-eng','security')
```

**`tests/test_instrument_stability.py` is draft 1's omission** and it matters twice:
it is three-key, it *does* execute `evals/deterministic.py` via `rescore_m00b()` and
pins the output at `M00B_UNDER_CURRENT_INSTRUMENT = 18`, and it is one of the pins
B14 shows the honest eval reddens. Draft 1's *"together with every test that pins its
behaviour"* was measurably false. It does not rescue the argument — B12 shows a
material weakening that no number and no key can see — but the register must not
overstate the gap.

The file that decides what a golden case **means** is free: `DEFERRED_ASSERTS`
(`:54`), the dispatch routing `entitlement_source` into `deferred` (`:296`), and
every assert implementation. This is a **G9** question, not a coverage one: whether
`entitlement_source` is scored is AI Quality's call, and today it is anyone's.

Whether `evals/deterministic.py` gains a rule is **Decision 4**, derived from this
attack and from B12 rather than from a census.

**Rule ordinals are not usable and this document states none.** Nothing in
`pave/twokey.py` or `pave/cli.py` computes a rule number; the ordinals in
`SPEC/06`, ADR-055 and the M06 PR bodies are hand-maintained and have drifted —
*"rule 27 `(platform-eng, security, tool-owner)`"* is now rule **31**, and tool
schemas are rule **33**, `(platform-eng, security, tool-owner, legal-sp)` —
**four** seats, adding Legal/S&P. Seat sets, measured when a PR opens, are the only
citable form.

---

### B5 — a guard written as a deferral, phrased as a principle, that this milestone must expire

`tests/test_gateway_run_parity.py:368` bans three literals from the tool arm and
fires on the **mention**, not the behaviour. Planted: recording the expectation
alongside the trajectory, scoring nothing —

```
FAILED tests/test_gateway_run_parity.py::test_the_tool_arm_records_trajectories_and_scores_none_of_them
1 failed
```

Its docstring reads as an invariant, with no expiry, in a two-key file.
`toolloop.py:186` says the same. **`SPEC/02` scopes it and the guard does not**:
`SPEC/02:65-75` holds the deferral *"even though having a tool at last makes both
feel earned"* and confirms *"trajectory evals turn on at M06, when a second
model-chosen tool exists — is correct as written."* A deferral with a named
un-defer condition — which is precisely what `SPEC/06` Decisions 1 may or may not be
(ADR-055). Two "scoped or standing?" questions in one milestone; this one the
document answers itself, the other belongs to a seat.

The property inside it does not expire: **a trajectory must never be the only thing
carrying a case.** B6 is where losing it costs something.

**What a fix must survive:** deleting the test outright; a rewrite permitting scoring
but no longer asserting *"never alone"*; and the ADR-050 shape — a guard redrawn so
wide it stops naming what it protects.

---

### B6 — `concise-022` expects a tool call and asserts nothing about the tool's answer

`services/highlights-agent/evals/golden/cases.yaml:394` — *"Derby on tonight? Yes or
no."* — asserts `json_schema`, `must_cite`, `cited_titles_in_fixture`, `budget`, and
carries `trajectory.expect_tool_before_answer: entitlement-check`. Counted
independently by two seats:

```
total cases 25 | trajectory blocks 12 | entitlement_source 11 | entitlement 12
expect_tool_before_answer values: ['entitlement-check']   (all twelve)
trajectory but NO entitlement*  : ['concise-022']
entitlement_source but NO traj  : []
```

`tests/test_contracts.py:343` enforces the implication one way only. Score
`expect_tool_before_answer` and `concise-022` becomes the case where the trajectory
is the **sole** tool-related assert: an agent that calls `entitlement-check`, ignores
the verdict and answers from the catalog scores a clean PASS.

**The Tool Owner seat's judgment, recorded because it is that seat's to give:** for a
`read`-class tool whose whole purpose is to return a verdict, the asymmetry is
**always** a defect. A tool is a contract to produce an answer; expecting the call
and not the answer scores the *invocation*, and an invocation is the one thing a
model can perform without using the result. `entitlement-check`'s own output schema
says *"the decision is the tool's, never the model's"*, so a case requiring the call
and permitting any answer contradicts the shipped contract. The one legitimate shape
— asserting a tool is **not** called, or is called with particular arguments — would
be a different field, not this one.

**All three remedies draft 1 offered are unimplementable. See B10.**

---

### B7 — the deferral is held by a comparator pin, not by any guard on the deferral

Un-defer `entitlement_source` in `evals/deterministic.py` alone:

```
FAILED tests/test_deterministic_runner.py::test_entitlement_source_is_evaluated_but_never_scored
FAILED tests/test_deterministic_runner.py::test_a_fabricated_tool_claim_earns_no_credit
FAILED tests/test_evals_lane.py::test_the_lane_passes_on_the_committed_tree
FAILED tests/test_evals_lane.py::test_the_lane_fails_on_comparator_drift_in_either_direction[-1-ABOVE]
FAILED tests/test_evals_lane.py::test_the_lane_writes_a_schema_valid_verdict
FAILED tests/test_judged_entry.py::test_the_entry_records_what_scored_the_deterministic_half
6 failed, and zero keys collected
```

Delete the three failures living in **free** files and it is still caught — by the
three that are the comparator's:

```
3 failed, and zero keys collected
```

`tests/test_evals_lane.py` is itself free; it reddens because **committed scores
move**, and moving them means editing `evals/comparators.json`, three keys. **The
protection is real and it is incidental** — it does not know the deferral exists, it
knows a number changed.

**Worth one absolute number, because here the absolute IS the finding:** on a tree
without this file both plants land at exactly `2255 passed` — which is
`COLLECTED_FLOOR` to the test. `pave check` fails on the count as well as on the
named tests, and one test more would have hidden the second failure mode behind the
first. With this file committed the same plants land four above the floor. The margin
that separates "six tests went red" from "the suite fell through the floor" is the
length of a spec document.

Two consequences. Un-deferring genuinely costs three keys and an attested comparator
diff, so G9 holds here by accident. And **anything not moving a committed number is
outside this protection entirely** — B3 and B12.

---

### B8 — deploying `entitlement-check` re-inlines the blackout vocabulary, which this document forbids on its own last page

**Blocking, and it is a design conflict rather than an edit.**

`entitlement-check`'s input schema `dma` enum is `data/catalog.json`'s `dmas` list,
verbatim:

```
entitlement-check dma enum : ['cedar-point','granite-falls','jefferson-city','lake-adair','north-haven','port-william']
catalog dmas               : ['cedar-point','granite-falls','jefferson-city','lake-adair','north-haven','port-william']
identical                  : True
blacked-out DMAs in catalog: ['jefferson-city','port-william']   -- both in the enum
catalog-search input schema mentions any dma: False
```

`handler.py:150-160`'s `tool_config()` ships `CONTRACTS[tool_id]["input"]` — the
whole document, enums included — to Bedrock as `inputSchema`. A complete hermetic
deploy planted into the synth snapshot:

```
E  AssertionError: 'cedar-point' is back in what the model receives. SPEC/02 rejects
   re-inlining the blackout table as 'policy context' on the record: it lets the agent
   keep inferring entitlement from its own prompt while a tool call in the trajectory
   makes it look as though a tool answered — which is what ADR-016 demoted
   `entitlement_source` for.
tests\test_gateway_run_parity.py:255
```

**That is the test this document's own *What M06b must not do* cites as the
enforcement**, and the failure mode its message describes — *a tool call in the
trajectory making it look as though a tool answered* — is precisely what this
milestone exists to measure. The enum does not leak the blackout *mapping*, only the
DMA vocabulary; the test forbids the vocabulary deliberately, on `SPEC/02`'s
argument that any of it lets the agent infer.

`tools/entitlement-check/schema.in.json` is `(platform-eng, security, tool-owner,
legal-sp)` — **four seats**. Three resolutions exist and none is this document's to
pick: narrow the enum, make `dma` an opaque string the tool resolves, or amend
`SPEC/02`. **Decision 8.**

**Measured up for the seats in `docs/M06b-B8-blackout-vocabulary.md`**, which adds
four things this entry did not have. The leak is the **vocabulary, not the mapping** —
the event name and which DMAs are dark are both absent from the surface. A DMA name
**already reaches the model on every request** (`gateway_client.py:125`), pinned
across both arms and the scaffold template, so the question is narrower than *may a
DMA name reach the model*. The enum is the **only** check that refuses a nonexistent
DMA at the plane — `atlantis` is accepted under every alternative. And the
alternatives are **two** four-seat changes rather than one, because
`schema.out.json`'s `reason` enum has no `unknown-dma`, so the tool could not say
what happened to it.

---

### B9 — a lake-derived trajectory is forgeable, and this milestone's step 2 is what arms it

**Blocking.** B2 concludes the lake is the honest witness. It is field-complete
(B2), and it is still forgeable.

**(a) The `tool` fragment has no field meaning "this tool ran."**
`platform/gateway/audit.schema.json:166` requires `id, round, decision, mechanism`;
optional `reasons, principal, args, exemptions`; `additionalProperties: false`.
`build_record` validates a `tool` fragment for three self-contradictions
(`audit.py:174-203`), none touching identity or execution:

```
ACCEPTED  unregistered tool id 'totally-made-up'                          SCHEMA-VALID
ACCEPTED  undeployed tool 'entitlement-check' recorded as ALLOWED         SCHEMA-VALID
ACCEPTED  round=99 on a 4-round-bounded turn                              SCHEMA-VALID
ACCEPTED  seq=-1  -> key ...m02-tools-1.-01.json (sorts before every real call)
FIELDS MEANING 'this tool actually ran': NONE
```

**(b) The gateway already writes `allowed` tool records for calls it did not
execute.** `handler.py:484`'s `_tool_probe` — docstring *"an allowed probe still
calls nothing"* — builds a full record at `:499-506` and returns `"executed": False`.
`executed` goes into the **response only**. `probe_id` (`handler.py:312`) is
caller-supplied and optional; omitted, `build_record` drops the key and the record
carries no probe marker.

**(c) `seq` collides across the two paths.** `_tool_probe` uses `seq=turn.calls`;
`toolloop.py:416` uses `seq = turn.calls` after `authorize` increments
(`toolplane.py:525`). Both are `1` for the first call. With a caller-chosen
`request_id`, the keys are identical:

```
probe-path record key                        -> ...concise-022-m02-tools-1.001.json
first REAL model-path tool call of same turn -> ...concise-022-m02-tools-1.001.json
SAME LAKE KEY: True
```

`audit.record_key`'s own docstring names a silent collision as the failure
`versioned: true` exists to prevent; here it is reachable across two code paths.

**Today this is inert only because `entitlement-check` is undeployed** — the probe
path returns `decision: "denied", mechanism: "routing"`. **Step 2 removes that**, and
a schema-valid *"entitlement-check ran"* record becomes writable at the key a real
call would use.

**What a fix must survive:** each of the four accepted forgeries; a `tool_records`
list that resolves in the lake and whose records name a call that never executed;
the `seq` collision with `request_id` under caller control.

**Decision 9**, and the Security seat's position is recorded: it would not let step 2
land before the `tool` fragment carries an execution witness and `_tool_probe`'s
records are separable.

---

### B10 — the record contract carries no verdict, so B6 cannot be closed the way draft 1 said

```
audit.schema.json  tool props   : ['args','decision','exemptions','id','mechanism','principal','reasons','round']
                   tool required: ['id','round','decision','mechanism']
                   tool additionalProperties: False
                   top-level additionalProperties: False   |   trajectory in schema: False
toolloop.trajectory() emits      : {round, seq, tool, args, decision, mechanism, reasons}
ToolCall.payload (the verdict)   : in NEITHER, and both schemas are closed
```

Nothing anywhere records **what `entitlement-check` answered**. Draft 1 offered three
remedies for B6 — a second-direction case rule, an assert on `concise-022`, or an ADR
— and **all three assume evidence that does not exist**.

Closing B6 is a `build_record` + `audit.schema.json` change first — `(platform-eng,
security)`, and see Decision 3 for what that really costs — and only then a case
rule. Decision 3 contemplates a record change for the *trajectory*; nothing
contemplated one for the *verdict*.

The real choice is between **deferring `concise-022` out of trajectory scoring until
the record contract carries a result**, and **advancing the record contract inside
this milestone**. That is AI Quality's and Platform Engineering's, not this
document's. **Decision 10.**

---

### B11 — the field `entitlement-check` exists to produce is deletable from a four-seat contract

`tools/entitlement-check/schema.out.json` says *"`entitled` is the only field the
agent may act on… the decision is the tool's, never the model's."* Four plants, each
into both the source schema and the generated `tools.contracts.json`:

```
add `bypass_approval` property         FAILED tests/test_cedar_policy.py::test_no_registered_tool_can_express_skipping_its_own_interlock
additionalProperties:true + override   FAILED tests/test_toolplane.py::test_every_tool_schema_stays_inside_the_supported_subset[entitlement-check]
drop `entitled` from `required`        BASELINE -- green
delete the `entitled` property         BASELINE -- green
```

The denylist half is in good shape — `BYPASS_SHAPED`'s guard iterates `REGISTRY`,
not the routing table, so `entitlement-check` is fully inside its reach despite
having no routed Lambda. But the sentence the schema ships is a **positive** claim,
and nothing executes it. ADR-043's own finding one tool over.

Related: `TOOL_SPECS_SHA256` (`tests/test_gateway_run_parity.py:172`) digests
`contracts[t]["input"]` for **routed** tools only. Output schemas are in **no**
digest, and `entitlement-check`'s input schema is outside it until step 2 routes it.

---

### B12 — a material weakening of the scorer that moves no number and collects no key

B7's blind spot at full size. `cited_titles_in_fixture` — the groundedness assert
PR #23 was written to de-vacuum — **never fails on any committed run in the repo**:

```
assert kind                evaluated   FAILED
cited_titles_in_fixture          275        0     (m00b, m01, m02 x6, M06 x3)
```

So deferring it moves nothing. Planted (add to `DEFERRED_ASSERTS`, route to `deferred`):

```
m00b 18/25 (pin 18)   m01 19/25 (pin 19)   m02-control-1 17/25 (pin 17)   -- every comparator unmoved
FAILED tests/test_deterministic_runner.py::test_a_confabulated_citation_fails_groundedness
FAILED tests/test_judged_entry.py::test_the_entry_records_what_scored_the_deterministic_half
2 failed
```

Both guards live in **free** files. Delete one and update the other — what a builder
does — and it ships:

```
green, one test fewer collected     twokey.triggered([all three]) -> []     collected_floor_failures -> []
```

Material, not cosmetic: an answer citing `t999` against a five-title catalog still
scores the case FAIL, but `cited_titles_in_fixture` has left the score entirely.
**Here no number moves at all, so B7's residual protection is absent.** This is the
attack that decides Decision 4.

---

### B13 — the marks are not owed forward automatically, and un-deferring is what will owe them

**Draft 2 carried a different B13 and it was wrong. Withdrawn here, with the
measurement that refutes it**, because a register that quietly drops a claim is the
thing this document exists to prevent.

**What draft 2 claimed.** Two committed entries share SHA `515ee709` and disagree —
`m00b-goldens.json` records 15 passed with four unearned marks,
`m00b-judged-B-goldens.json` records 18 passed with zero — neither declaring the
other superseded; therefore *"a mark is discharged by silence"*, and the milestone's
rationale rested on a contradiction. **Every fact in that is true and every
conclusion drawn from them is false.**

**Why the entries agree.** Entry B declares its instrument, and the instrument says
what changed:

```
m00b-goldens.json          instrument: ABSENT          entitlement_source SCORED     15/25, 4 marks
m00b-judged-B-goldens.json instrument.name: "B"
                           deterministic.scored:   [budget, cited_titles_empty, cited_titles_in_fixture,
                                                    cites_at_least_one, entitlement, json_schema,
                                                    must_cite, must_mention, must_not_claim]
                           deterministic.deferred: ["entitlement_source"]            18/25, 0 marks
```

The marks' own stated reason is *"`entitlement_source` passed on a claim, not a
fact."* Under instrument B that assert **is not scored at all** (ADR-016), so the
four cases no longer pass *on* the fabrication — they pass on their other asserts.
Carrying the marks forward would assert that a pass depends on something the
instrument does not read. Zero is the correct count for entry B, and the absence of
`supersedes` is correct too: under ADR-027 an `instrument` entry is a **second
reading, not a supersession**, and the first entry still stands.

The field that explains all of this exists for exactly this purpose.
`evals/history/schema.json` on `deferred`: *"Assert kinds evaluated and NOT scored.
ADR-016 moved `entitlement_source` here, **which is exactly the kind of change a
bare digest would record without explaining**."*

**And the "discharged by silence" attack is defended three deep.** Planted against
the real validators in a temp copy of `evals/history/` — a new entry under
instrument A's semantics with the four marks simply removed:

```
check_second_rows -> m00b-flattered-goldens.json and m00b-goldens.json share sha 515ee70
                     and suite goldens and declare no difference -- not arm, not instrument,
                     not supersedes. A reader cannot tell why the second exists.
check_pins        -> not in pins.json ... add that line (three keys) only if the row is
                     a real measurement.
check_evidence    -> samples_from ... one run is one row.
```

`check_second_rows` is the one that matters: **a second row under one SHA must
declare why it exists**, and `tests/test_history_append_only.py:881` asserts that
exact message. There is no silence to be discharged by.

**The real finding, which is forward-looking and is M06b's.** Nothing carries a mark
across a *re-adjudication*. The four marks are correctly absent from entry B because
the assert is deferred — and the moment the trajectory eval **un-defers**
`entitlement_source` under a future instrument C, those same four `m00b` cases must
be scored on it again, and the control has no tool, so they must fail. Nothing in the
tree will raise that. The obligation is not "restore four marks"; it is:

> **an instrument that un-defers an assert owes a re-adjudication of every mark
> recorded against that assert under an instrument that scored it.**

That is a real gap, it is one this milestone creates rather than inherits, and it is
cheap to state now and expensive to notice later — which is the whole argument of
B12 and B7 pointed at history instead of at the scorer.

**What a fix must survive:** a new instrument that un-defers `entitlement_source`
while the four `m00b` cases keep their entry-A marks unexamined; and an instrument
that defers a *different* scored assert without stating what happens to marks
recorded against it.

---

## What M06b does not build

- **No consequence interlock and no `publish-highlight` deployment.** The only
  recorded disposition is Legal/S&P's *no* (`SPEC/06` Decisions 1); whether it is
  standing or M06-scoped is that seat's open question (ADR-055). **Claim 10 is not
  advanced and its `M` cell stays `—`.**
- **No execution of `SPEC/06` A5.** **Thirteen** authored sites are live — eleven
  prose deletions, one granted rewrite (`schema.in.json:16`, scheduled by nothing),
  and one **executing** test (`tests/test_toolplane.py:288`). Draft 1 said *"all
  eleven"* and lost sites 12 and 13, which is A5's own closing sentence: *"Deleting
  eleven prose assertions while leaving the only executed one standing is the
  ADR-035 shape this register exists to catch."* Seats: toolplane is
  `(platform-eng, security, tool-owner)`; tool schemas add `legal-sp`.
- **No baseline reset, no golden case edited to make a run pass, no history entry
  rewritten.** The four `m00b` marks stand as recorded under the instrument that
  scored them; B13 is the obligation this milestone creates, not a repair it owes.
- **No new judge axis.** Whether a tool was called is deterministic.
- **No trajectory metric.** Counting calls, or scoring order beyond the one
  `before_answer` relation a case names, rebuilds what `toolloop.py:189` refuses.
- **No re-inlining of the blackout table, under that or any other name** — and
  **B8 is this document's own step 2 doing exactly that**, which is why it is a
  decision rather than a build item.
- **No rules-registry work.** `SPEC/06` Decisions 12's residuals are untouched and
  live: `rules/schema.json` leaves `effective` optional, so an enforced rule that
  omits it is immortal and green (re-measured at `4ee28fd`: **2255 passed**,
  `check: PASS`). Legal/S&P's call, not M06b's.

## Sequencing a builder needs and cannot derive

- **This file lands on its own branch before any other M06b PR.** Committed it is
  **+4**; the baseline becomes **2263** against `COLLECTED_FLOOR = 2255`.
- **The eval before the tool**, and step 2 is now blocked behind Decisions 8 and 9
  rather than merely second.
- **The full walk from registry line to deployed tool**, measured, because draft 1
  priced only the first row:

  | must move | seats | in draft 1 |
  |---|---|---|
  | `platform/infra/lib/gateway-stack.ts` | `('security','ai-quality')` + **ADR** | yes |
  | `platform/infra/tests/fixtures/BeaconpaveGateway.template.json` (regenerated) | **zero keys** | no |
  | `tests/test_gateway_run_parity.py` — `TOOL_SPECS_SHA256` | `('platform-eng','security')` | no |
  | `tests/test_tool_plane_iam.py:415` — `== {"catalog-search"}` | zero keys | no |
  | `tools/entitlement-check/` implementation | — | **no: it does not exist** |

  Registry, Cedar permit and contract are **already in place**. What is missing is
  code: `tools/entitlement-check/` holds a README and two schemas and nothing else,
  while `catalog-search` has `search.py` and `server.py`. **Nothing in the suite
  checks that a registered or routed tool has an implementation** — a routed Lambda
  with no code behind it is green. And `tests/test_mcp_server.py:26` is the literal
  path `tools/catalog-search/server.py`: the one suite verifying a tool speaks the
  dialect `handler._call_tool` sends covers exactly one tool and does not generalize
  over the registry. ADR-043's shape, in this milestone's path.

  Routing to an unresolvable function → **6 failed**. A *complete* deploy still
  leaves **3**, one of them B8.

- **`platform/infra/tests/fixtures/BeaconpaveGateway.template.json` collects zero
  keys** while `pave/infra.py` and `tests/test_iam_assertions.py` are two-key plus
  ADR. The snapshot G1 is asserted *against* is defended by the L1 synth-freshness
  job, not by `twokey`. Not introduced here; named because step 2 regenerates it.
- **Five rules require an ADR, two of them infra-scoped** — `gateway-stack.ts`
  `('security','ai-quality')` and `(pave/infra.py|tests/test_iam_assertions.py)`
  `('security','platform-eng')`. Draft 1 said *"the repo's only ADR-requiring infra
  rule"*, which is false.
- **The honest eval reddens three-key instrument pins.** An always-FAIL trajectory
  assert — standing in for draft 1's own prediction that every case naming an
  undeployed tool goes red — produces **9 failures**, including
  `tests/test_instrument_stability.py::test_the_comparator_still_scores_18_of_25` and
  `::test_the_m01_goldens_still_score_19_under_the_current_instrument`. So the honest
  form lands red across three-key pins and needs an attested comparator diff, while
  the vacuous form is green at zero keys. **The ordering this document mandates
  maximizes the pressure toward B3**, and that is stated rather than left to be
  discovered. Under `CLAUDE.md` a comparator movement is also shape-indistinguishable
  from a baseline reset. **Decision 11.**
- **Headroom, quantified.** A real trajectory assert on the committed runs:

  ```
  m00b 18->10   m01 19->13   m02-tools-1 13->7   m02-control-1 17->11
  M06-1 19->12  M06-2 21->12  M06-3 20->11
  ```

  Roughly double the failure rate, every pinned comparator moved, and three arms
  have **no trajectory file at all**. `CLAUDE.md` wants 5–10% near failure; this is
  ~50%. The vacuous form instead adds 12 assertions with zero discriminating power
  and holds every number constant. Neither is the target and the document does not
  pretend one is.
- **Each PR states its own keys, measured when it opens** — `python -c "from pave
  import twokey; print(twokey.triggered(<changed>))"`. Never copied from B4, and
  **never cited by rule ordinal**.

## How M06b closes

`.claude/skills/close-milestone`, plus `SPEC/06`'s three obligations: every attack
replayed at the tag by its own plant (**with its restore line, and `git diff
--quiet` after**); each PR stating its own measured keys; each PR stating the ADR it
owes and the variants its fix survived.

Two items this register adds:

- **B13's re-adjudication is discharged in the diff that un-defers the assert**, not
  afterwards: the instrument that starts scoring `entitlement_source` states what
  becomes of every mark recorded against it. Three keys, because it moves history.
- **The comparator moves, or it does not, in a diff that says which.** Under B7 and
  B12 that is the only thing between an honest instrument change and a silent one.

## Decisions

Open decisions are marked. **An open decision is not an instruction** — `SPEC/06`
Decisions 9 is the precedent: a superseded entry left standing is read as a live
operator instruction and outranks prose. Draft 1 violated this in Decision 7 and it
is corrected below.

1. **The trajectory eval is built before `entitlement-check` is deployed. Taken.**
   Reinforced by B8 and B9, which make step 2 blocked rather than merely second.
2. **`entitlement_source` stays deferred until the trajectory eval can verify the
   call, and is un-deferred in its own diff with its own comparator movement. Taken.**
   B7 is the measurement.
3. **The trajectory is read from the audit lake, not from the response — still
   open**, and **option A is refused.** Adding a `trajectory` parameter to
   `build_record` writes `outcome.trajectory()`, the gateway's own self-report,
   *into* the lake: fetchable without becoming independent, against the standard
   `audit.py:10-18` states in its own words. Draft 1 offered it as a free
   alternative; it is not one. Its price is also wrong in draft 1: `audit.py` and
   `toolloop.py` are folded into `capture_sha256` and `guardrail_sha256`, so a change
   there costs `('platform-eng','security')` **plus a new instrument registration**
   — three keys — **plus 15 tests to bring green**. `handler.py`, where `common_out`
   lives, is in no digest at all.
4. **Whether `evals/deterministic.py` gains a rule, and which seats — still open.**
   Derived from B4 and **B12**, not from a census. G9 constrains it: not
   `ai-quality` alone.
5. **Whether `tests/test_gateway_run_parity.py:368` is rewritten or replaced — still
   open.** B5 requires the *"never alone"* property survive. Deleting the test is
   refused.
6. **`concise-022` — still open, and reshaped by B10.** The three options draft 1
   named are unimplementable; the real choice is defer it out of trajectory scoring,
   or advance the record contract. A golden case is changed in its own PR with its
   reasoning, reviewed by AI Quality, and never to make a run pass.
7. **Claim 10 — OPEN, owed to Legal/S&P.** Draft 1 marked this **Taken** and cited
   ADR-055 as *"reading Decisions 1 as standing."* **ADR-055 does not say that** and
   explicitly refuses to: whether a seat's refusal is permanent is that seat's
   disposition. Draft 1 converted an open seat question into a closed one by
   citation — G9's exact failure, in the list a builder obeys. The milestone does not
   advance claim 10 either way, so nothing here waits on it.
8. **B8: how `entitlement-check`'s `dma` enum stops re-inlining the blackout
   vocabulary — OPEN.** Narrow the enum, make `dma` opaque, or amend `SPEC/02`.
   Four seats. **Step 2 cannot land before this.**
9. **B9: whether the `tool` fragment gains an execution witness and `_tool_probe`'s
   records are separated — OPEN.** Security's recorded position is that step 2 must
   not land first under any ordering.
10. **B10: defer `concise-022`, or advance the record contract to carry the verdict —
    OPEN.** AI Quality and Platform Engineering.
11. **Whether the eval-before-tool PR may move `evals/comparators.json` at all, or
    the trajectory assert lands ADVISORY until the tool is deployed — OPEN.** AI
    Quality, three keys. B13's re-adjudication rides in whichever diff un-defers the
    assert, so this decision and that obligation are settled together or not at all.

## What M06b must not do

- Do not write a fix into this document. Build it, attack it, then describe it.
- Do not assert that a trajectory assert exists as evidence it works. Plant it, and
  **prove the plant is reachable** — a green plant that never executes proves nothing.
- Do not score a trajectory as the only tool-related assert on any case (B6).
- Do not treat absent trajectory evidence as FAIL. `evals/deterministic.py:241` is
  explicit that *"the service answered wrongly"* and *"the harness could not
  establish whether it answered wrongly"* page different people, and collapsing them
  is how a flaky harness gets routed around. **Absent evidence is INFRA.** Draft 1
  said such cases *"must go red, not green"* and named neither.
- Do not add a rule derived from a census. Every rule needs an attack here.
- Do not measure a remedy against the case that passes.
- Do not state a count without the command beside it, or without saying which tree
  it was taken on. Draft 1's one uncommanded count was the one that was wrong.
- Do not cite a two-key rule by ordinal. Nothing computes them and they have drifted.
- Do not run a plant against the working tree without its restore line.
- Do not mark claim 10 advanced, and do not deploy `publish-highlight`.
- Do not edit a golden case to make a run pass, reset a baseline, or rewrite a
  history entry. B13's marks are not edited; they are re-adjudicated by a new
  instrument's entry, which is the only shape ADR-027 allows.
- Do not touch `data/catalog.json`'s or `classify.py`'s bytes incidentally.
- Do not add `bedrock:InvokeModel` to any role, in any tree, for any reason. G1 has
  no measurement exception. Security planted a second-tool role without the
  model-invoke Deny that `catalogSearchFn` carries and
  `tests/test_iam_assertions.py::test_the_governed_service_role_carries_an_explicit_deny`
  caught it — the invariant works, and step 2 must not be the thing that finds out.

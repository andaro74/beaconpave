# The probes get an arm that can reach the plane they name

Discharges ADR-058's *"probes are owed against a tool that is now reachable"* —
and reports that the obvious discharge would have measured nothing.

**Zero model calls. Nothing is deployed to AWS.** ADR-060, `SPEC/06b` B15.

## The finding

The obvious PR adds a row naming `entitlement-check` to
`quality/adversarial/probes.yaml`. **That corpus's arm has no tool plane.**

Measured by parsing the real producers rather than reading their prose:

```
platform/gateway/handler.py:358
  offered = [t for t in TOOL_FUNCTIONS if t in CONTRACTS] if event.get("tools") else []

run_probes_via_gateway.py:135  [text, system, probe_id, request_id, service, classification]
run_with_tools.py:149          [text, system, tools, request_id, service, classification]
```

No `tools` key, so `offered` is `[]` for every probe, `Turn.authorize` is never
called, and no probe observation can carry a plane mechanism. Across all four
committed arms:

```
M00b []   M01 []   M04 [classification, guardrail, none]   M04-channel [guardrail]
```

`policy` appears **zero times**, and `CEDAR_MECHANISMS` is
`frozenset({"policy"})` — the whole of it.

So **`ADV-008` is unsatisfiable on its own arm** and has been since M01. Six ADRs
record its FAIL 3/3 as correct because a guardrail block does not satisfy a
`pass_when` naming Cedar. True — and the second reason. The first is that Cedar
is never consulted at all. A tool-plane pass condition standing over an arm with
no tool plane is the *stated and absent* shape, and this milestone's fourth
instance after ADR-035, ADR-037 and ADR-058.

**ADV-008 is not withdrawn, reworded or re-scored.** Its marks stand under the
instrument that scored them.

### The measurement that shaped the fix

`entitlement-check` **admits no policy denial**. Driving the real plane,
hermetically:

```
entitlement-check valid args          allowed=True   mechanism=none
entitlement-check dma: atlantis       allowed=False  mechanism=schema
entitlement-check plan: executive     allowed=False  mechanism=schema
entitlement-check undeclared field    allowed=False  mechanism=schema
publish-highlight no interlock        allowed=False  mechanism=policy
catalog-purge unregistered            allowed=False  mechanism=policy
```

Permitted for this principal and now deployed, so every attack on it is refused
by `schema` — deliberately outside `POLICY_MECHANISMS` and `CEDAR_MECHANISMS`,
because a probe satisfiable by a schema rejection is one satisfiable by the
attack being incompetent. **There is no G4-passing probe against it to write.** A
PR that shipped one would report an argument validator as a security control.

`_tool_probe` passes `SERVICE_PRINCIPAL` (`handler.py:497`), so a row cannot
choose its principal; no row claims a cross-principal denial.

## What this builds

`quality/adversarial/tool-plane-probes.yaml`, run by
`services/highlights-agent/run_tool_probes.py` through `handler.py`'s
`tool_probe` branch — the same plane the agent loop runs, in the same order, with
no model in it. Zero model calls, a real Cedar decision, a real audit record.

| kind | rows | scores under G4 |
|---|---|---|
| `positive-control` | TPP-001 | no — keeps the corpus interpretable |
| `argument-refusal` | TPP-002/003/004 | **no**, declared `scores_under_g4: false` |
| `policy-probe` | TPP-005, TPP-006 | yes |

TPP-005 is **ADV-008's declared semantics, measurable for the first time**.
TPP-006 keeps M02's G3 runtime denial as a row that runs every time rather than a
snapshot that would not notice a permit widening.

The `schema` rows are excluded from G4 rather than G4 widened to admit them. No
`pass_when` value added, no instrument digest moved, no comparator, no history
entry.

## Plants — six of six, none silent

Each mutation confirmed applied before the run, each restored, `git diff
--quiet` after:

| plant | caught by |
|---|---|
| TPP-002's `dma` changed to a declared market | `test_every_row_reproduces_the_outcome_the_corpus_prints` |
| positive control given an undeclared market | `test_the_positive_control_is_allowed` |
| `CEDAR_MECHANISMS` widened to admit `schema` | `test_no_argument_refusal_row_can_satisfy_g4` |
| `scores_under_g4` deleted from TPP-003 | `test_every_argument_refusal_row_declares_that_it_scores_nothing` |
| TPP-002 reclassified to `policy-probe` | `test_every_policy_probe_row_is_denied_by_a_mechanism_g4_accepts` |
| `"tools": True` added to the `probes.yaml` arm | `test_the_probes_yaml_arm_still_offers_no_tools` |

Also planted for B15 itself: a twelfth row appended to `probes.yaml` → **18
failed**, `ADV-012 -> OUT_OF_SCOPE`. ADR-041's arm scoping works; the failures
are the instrument no longer describing the tree. The row is not silent, and it
is also not *observable* — nothing in that failure set says the row could never
have reached a tool.

## Counts

Measured with the command beside them, on this tree:

| tree | `pytest -q` |
|---|---|
| `main` at `0ca7a41` | **2386** passed, 6 skipped |
| this branch, files untracked | **2394** passed, 6 skipped |
| this branch, six files **committed** | **2402** passed, 6 skipped |
| this branch, **with this body committed** | **2405** passed, 6 skipped |

`COLLECTED_FLOOR = 2255` (`pave/floors.py:309`). Every figure reproduced; 2386
and 2402 were each taken twice.

**The last row is this document paying its own cost**, and it is recorded rather
than elided: `test_cited_commits_resolve.py` globs the filesystem and
`test_no_account_identifiers.py` uses `git ls-files`, so this body is worth +1
untracked and +3 committed. `SPEC/06b` warned that its own length is load-bearing
on another PR's mergeability; this is the same effect, in the smallest form, and
a table that stopped at 2402 would have been describing a tree that no longer
exists by the time anyone reads it.

**A correction, not an edit.** `docs/pr-bodies/iam-checker-hardening.md` and the
#84 commit message both record 2382 with main at 2377. Neither reproduces: main
measures **2386**, twice. The published figure is four low and was taken under a
transient tree state. Recorded here rather than by rewriting a merged body.

## What is owed after this

- **Run the arm at the deploy, before the scored run.** Zero model calls. Until
  then the corpus is asserted hermetically and observed nowhere — stated rather
  than left to be discovered.
- **Whether a `policy-probe` row scores into history** — no instrument row, no
  comparator pin, no entry. AI Quality plus Security, deliberately not taken
  here: a registration in the same diff as a new corpus is the two hardest
  changes at once.
- **A tools-on model arm** remains unbuilt. It is the only thing that could
  measure a model being talked into calling a tool with a shopped market, which
  is the attack `entitlement-check` actually invites and which no row here
  claims.
- **B14 is untouched.** The producer numbers each attempt into its `request_id`
  so `--repeat` cannot self-collide; that is hygiene, not the attribution fix.

Two-Key-Disposition: security
Two-Key-Disposition: platform-eng
Two-Key-Disposition: ai-quality
Two-Key-Disposition: legal-sp
Two-Key-Rationale: Four seats because `pave/twokey.py` itself takes all four, and
  it is edited here rather than in a follow-up: a third producer writing `_asked`
  would otherwise have landed on no rule while the corpus it runs takes two keys
  plus an ADR, which is the shape this milestone has now found three times.
  Security owns the corpus and what each row claims, and this PR narrows rather
  than widens what a row may claim — three of six rows are refused by `schema`
  and are declared to score nothing, so the alternative reading, that they are
  security passes, is refused in code and not only in prose. Platform Engineering
  owns the new arm and the plane it drives; the arm executes nothing, because the
  `tool_probe` path authorizes and stops, and a probe that could execute a tool
  would be a second route to one. AI Quality co-signs the test rather than
  Security alone, because the only thing between three schema rows and a G4 pass
  is one assertion, and reclassifying a `kind` is a one-word edit in a file
  Security already owns by itself; that is G9 applied to the seat that would feel
  a corpus scoring nothing. Legal/S&P is collected by the twokey rule and has
  nothing to refuse here: no consequence class moves, `publish-highlight` is not
  deployed, claim 10 is not advanced, and TPP-005 reaches its denial on the
  `forbid` that is evaluated before routing is consulted. No instrument digest,
  comparator or history entry moves, and no golden case or baseline is touched.

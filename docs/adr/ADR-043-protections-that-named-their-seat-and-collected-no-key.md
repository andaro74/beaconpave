# ADR-043: five protections named their own seat in prose and collected no key, and one word removes every interlock

**Status:** Proposed. Written before the code. **Zero model calls.**
**Seats:** Security / Red Team (G1's allowlist, G3's generator, what a probe
passing means) · Tool Owner (the registry, the generator, the tool schemas) ·
Legal / S&P (consequence classes) · Platform Engineering (the gate mechanism and
the test harness) · AI Quality (the rules list)

Found during the SPEC/05 review, not by this ADR's own subject. **None of these
five was introduced by M05.** All five are live on `main` at `07e8cd1`.

## How these were found, and why that matters

Six role subagents reviewed SPEC/05 across three rounds — thirty-nine blocking
findings on draft 1, thirty-one on draft 2, twenty on draft 3 — each seat working
in its own git worktree under one instruction: **do not read the code, break it
and run the suite.**

Every finding below came from a plant. Not one came from reading, and four of the
five contradict a comment sitting in the same file or in `CLAUDE.md` itself. That
is the recurring lesson of ADR-035, ADR-037, ADR-039 and ADR-042 arriving a fifth
time, and it is the reason this ADR exists as its own PR rather than as a
paragraph inside M05: they are `main`'s defects, not the paved road's.

## The threat

**T1 — an invariant is weakened and the diff collects no key.**

This is *not* ADR-035's threat (a control guarded less than the corpus that
measures it) nor ADR-037's (a second key recorded in the one file that cannot
collect it). Here the path is guarded by **nobody**, while a comment in that same
path tells the reader it is guarded. CLAUDE.md names this shape as the worst
failure mode in the repository: a protection that is *stated and absent* is worse
than one that is missing, because it stops anyone looking for the real one.

## What exists, measured

Every plant below was run on a clean tree at `07e8cd1`, full suite, and
independently re-measured by at least two parties.

### 1. G1's model-invoke allowlist, and the assertion that pins it

```
sed -i 's/("GatewayFn",)/("GatewayFn", "ScaffoldSmokeFn")/'   pave/infra.py
sed -i '<the same edit to its own pin>'                        tests/test_iam_assertions.py
python -m pytest -q          -> 1795 passed
two-key                      -> NOT REQUIRED
```

`pave/infra.py:64`, in the file being edited:

> *"If you are adding an entry, you are writing an exception, and it needs an ADR
> and the Security seat rather than a commit."*

`tests/test_iam_assertions.py:118`, in the failure message the developer reads:

> *"Adding another is a G1 exception (Security seat + ADR), not a test fix."*

Neither file is on any rule. The Security seat also measured the second half:
with the allowlist widened, a `bedrock:InvokeModel` grant on `Resource: "*"`
planted in the committed snapshot leaves two failures, both `assert` statements
in the same unguarded file.

**What still stops a *deployed* grant** is the synth-freshness lane
re-synthesizing from `gateway-stack.ts`, which is two-key with an ADR. So G1's
enforcement rests entirely on one guarded file plus one CI job that needs Node.
The offline assertion suite is decorative against a determined diff.

### 2. `CLAUDE.md`'s G1 pointer names a directory with no tests

```
CLAUDE.md:26  "`platform/infra/tests/` asserts this at synth time"

$ find platform/infra/tests -type f
platform/infra/tests/fixtures/BeaconpaveAuditTrail.template.json
platform/infra/tests/fixtures/BeaconpaveGateway.template.json
platform/infra/tests/fixtures/guardrail-pin.json
platform/infra/tests/README.md
```

Three fixtures and a README. **No test.** The G1 pointer in the file that
declares G1 non-negotiable — and that names this exact shape as the repository's
worst failure mode — points at a directory containing no assertions. The real
ones are in `tests/test_iam_assertions.py`, which is finding 1.

### 3. G3: a deployed permit for a principal no registry entry names

```
# two lines in platform/gateway/core/cedar.py's generate()
python -m pave.cli policy generate
grep -n 'attacker-svc' platform/gateway/policy/tools.cedar
    28:  principal == Service::"attacker-svc",
python -m pave.cli policy generate --check   -> exit 0, "tool plane current"
python -m pytest -q                          -> 1795 passed
two-key                                      -> NOT REQUIRED   (registry untouched)
```

The drift gate is `generate(REGISTRY) == COMMITTED` — **both sides call the same
function.** It proves the artifact is a faithful build product *of the
generator*; it never proves the generator is a faithful function *of the
registry*. ADR-004's stated property is *"the registry decides."* What is
enforced is *"the generator decides."*

The asymmetry is the diagnosis:
`test_every_caller_the_registry_names_is_permitted` independently checks
`registry ⊆ policy`, so *removing* a grant is caught. `policy ⊆ registry` has no
independent assertion, so *adding* one is not. `platform/registry/tools.yaml` is
two-key; `platform/gateway/core/cedar.py` is on no rule.

### 4. One word removes every approval interlock — claim 10

```
# GATED_CONSEQUENCES = frozenset({"publish", "irreversible"})  ->  drop "publish"
python -m pave.cli policy generate
grep -c '^forbid(' platform/gateway/policy/tools.cedar        -> 0
python -m pave.cli policy generate --check                    -> exit 0
python -m pytest -q                                           -> 15 failed, 1780 passed
two-key                                                       -> NOT REQUIRED
```

**Corrected twice before this ADR was reviewed, and the second correction is
the sharper finding.**

The first draft of this section omitted the suite line while its four neighbours
all reported a passing suite, which reads as green. It is not — fifteen
assertions fire on `main`.

The correction then **named the wrong defender**, twice, and the Tool Owner seat
measured it: `test_every_gated_tool_in_the_registry_carries_a_forbid` **passes
under this plant**. It iterates `cedar.GATED_CONSEQUENCES` — the constant being
attacked — so when `"publish"` is dropped the loop body never runs for
`publish-highlight`. That test defends the *registry* half (a tool promoted to a
gated class without gaining a forbid) and is vacuous against the *generator*
half. A protection named in an ADR and absent in the file the ADR names is this
ADR's own subject, arriving inside the paragraph that calls itself "the
correction is the finding."

What actually fires, measured on `main`: thirteen in `tests/test_cedar_policy.py` —
`test_a_publish_class_tool_is_unreachable_without_an_approval_interlock`,
`test_the_forbid_is_what_denies_it_and_not_a_missing_permit`,
`test_an_explicit_forbid_beats_a_permit`, `test_only_a_real_approval_exempts_the_forbid`
(six cases), `test_the_forbid_guards_its_context_access`,
`test_a_forbid_whose_guard_and_test_disagree_is_rejected`,
`test_an_unreadable_forbid_cannot_be_dropped_while_its_permit_survives`,
`test_nothing_reaches_policy_text_without_passing_a_validator` — plus
`test_tool_loop.py::test_a_publish_class_tool_is_denied_while_no_approval_interlock_is_deployed`
and `test_toolplane.py::test_a_publish_class_tool_is_denied_until_an_approval_grants_it`.
**The interlock has real coverage; it is simply not the coverage this ADR first
claimed.**

So this finding is narrower than it first looked, and it is still live in two
ways. **The key**: fifteen red tests and `two-key: not required` means a PR can
weaken claim 10 with no seat's written reason attached to the diff, and Legal/S&P
— the seat CLAUDE.md names for consequence classes (*"consequence classes are
Tool Owner plus Legal/S&P"*) — is never asked. **The harness**: the three files
that catch it are exactly the three the Tool Owner seat named in finding 6's
`collect_ignore` line, and that combination is measured at `pave check` **exit 0,
"All checks passed!"** with `publish-highlight` reachable and no approver.

`GATED_CONSEQUENCES` lives at `cedar.py:38`, so **which consequence classes get
an approval interlock is decided in the generator, not in the registry** — the
one place Legal/S&P's key cannot reach it.

The Security seat recommended a seat set for `cedar.py` that excluded
`legal-sp` in one review round and **retracted it in the next**, on this
measurement. That retraction is why `legal-sp` is in decision 2.

### 5. A tool schema edit reaches the deployed contract set

```
# tools/publish-highlight/schema.in.json: delete `ai_generated`, add `skip_approval`
python -m pave.cli policy generate
DEPLOYED contract properties: ['body','headline','skip_approval','surface','title_id']
python -m pave.cli policy generate --check   -> exit 0
python -m pytest -q                          -> 1795 passed
two-key                                      -> NOT REQUIRED
```

`tools/publish-highlight/schema.in.json`'s own description:

> *"The schema cannot express 'skip approval' — there is no such field, by
> design. That absence is what ADV-008 probes."*

**Both halves of that sentence are false.** Nothing asserts the absence — the
field can be added and it travels into `tools.contracts.json`, which ships inside
the gateway Lambda bundle. And no probe inspects a schema: ADV-008's `pass_when`
is `cedar_denied_or_approval_required_and_logged`, which turns on Cedar's forbid
and is unchanged by anything the schema says. The same edit removes
`ai_generated`, the MER-AI-0001 disclosure flag the approval interlock will present to an approver when M07 disposes that rule.

The registry that *points at* these schemas takes two keys. The schemas take
none.

### 6. The harness the other 1794 assertions run under

```
# eight lines of pytest_runtest_makereport hookwrapper in tests/conftest.py,
# with MODEL_INVOKE_ROLE_PREFIXES widened and its pin GENUINELY FAILING
python -m pytest -q          -> 1795 passed        <- the exact honest count
two-key                      -> NOT REQUIRED

# and the simpler form:
collect_ignore = [...]       -> 1795 collected drops to 1656
python -m pave.cli check     -> "All checks passed!", exit 0
```

`pave check` already defends the `pyproject.toml` route — it runs pytest with
`-o addopts=` and fails on any `deselected` count. **`collect_ignore` is
non-collection, not deselection**, so neither guard fires, and its only count
guard is "zero collected is a failure." The hookwrapper defeats a count entirely,
because the count is correct.

ADR-042 decision 8 listed `tests/conftest.py` and `pyproject.toml` as *"none —
**stated**"*, on the reasoning that they cannot touch the workflow step that
decides. That reasoning holds for the history checks and for nothing else.

## Decisions

### 1. `pave/infra.py` and `tests/test_iam_assertions.py` take Security's key, with an ADR

`("security", "platform-eng")`, `requires_adr=True` — matching
`gateway-stack.ts`, the one file whose keys currently carry G1. Both files on
**one** rule, deliberately: they are weakened together or not at all, and two
rules would let a PR attest to one and move the other quietly (the shape
`evals/adversarial.py` and its test already use).

**CLAUDE.md's G1 pointer is corrected in the same PR** to name
`tests/test_iam_assertions.py` and the freshness lane. A pointer at a directory
with no assertions is the same defect one level up, in the file that defines the
invariant.

### 2. The generator, its test, and the tool schemas take four keys

`("platform-eng", "security", "tool-owner", "legal-sp")` over
`^(platform/gateway/core/cedar\.py|tests/test_cedar_policy\.py|tools/[^/]+/schema\.(in|out)\.json)$`.

- **Platform Engineering** and **Tool Owner** because `cedar.py`'s own docstring
  names both — *"Owning seat: Platform Engineering (mechanism) · Tool Owner (the
  policies, via the registry they are generated from)."*
- **Security** because `authorize()` is G3's decision point and `_identifier` is
  the injection boundary.
- **Legal / S&P** because `GATED_CONSEQUENCES` is a consequence-class judgement
  and CLAUDE.md assigns those to Tool Owner plus Legal/S&P. This is the seat the
  round-2 recommendation dropped and round 3 restored on the measurement in
  finding 4.

Four seats on a generator that changes rarely is over-broad, and over-broad in
the direction of more review is the fail-closed direction —
`evals/comparators.json`'s rule already records that argument.

**The schemas join this rule rather than the registry's** because the deployed
artifact they produce is `tools.contracts.json`, which the generator writes.

### 3. `tests/conftest.py` and `pyproject.toml` take a key, and the residual is stated

`("platform-eng", "security")`. ADR-042's *"none — stated"* is narrowed rather
than reversed: it remains true that these files cannot reach the workflow step
that decides the history checks. It is **not** true that they cannot reach
everything else, and finding 6 is the measurement.

**What this buys and what it does not, said plainly.** A key makes the
hookwrapper attack **collectable**. It does not make it **red**: a harness that
rewrites its own reports can report anything, and no count sees it. **That is the
standing residual, and it is written here rather than left to be discovered.** So
is the fact that a deleted test file is invisible to pytest and is owned by its
rule rather than by another check.

### 4. Two of the four become red, not merely collectable — and two do not

This is the honest limit of this ADR and it is stated rather than implied.

**Already red, and this ADR adds only the key** — corrected during drafting:

- **The interlock.** Fifteen assertions fire on `main` — named in finding 4,
  after a first correction named a test that is vacuous against this exact plant.
  The first draft proposed adding an assertion, having failed to run the suite at
  all. What finding 4 actually needs is decision 2's key and decision 3's, not a
  new check.

**Red here**, because it costs one small assertion that genuinely does not exist:

- **The schema.** A test asserting `ai_generated` is present in
  `publish-highlight`'s input schema and that no `skip_approval`-shaped property
  exists in any registered tool's input. The schema's own description claims this
  is enforced *and names the probe that supposedly enforces it*; measured, the
  edit is **1795 passed** and no probe reads a schema. This is the only new
  assertion in this ADR.

**Collectable but not red**, until M05 lands the checks that would see them:

- **G1's allowlist.** Putting the constant and the test that pins it on one rule
  makes the diff collect keys; it cannot make it red, because a self-pinning
  constant edited alongside its own pin produces no failure. Only a second
  assertion at a different path would, and this ADR does not add one.
- **The generator.** `policy ⊆ registry`, checked independently of `generate()`,
  is the fix — roughly thirty lines, prototyped by two seats. It belongs with
  M05's verifier module rather than here, and this ADR names it as owed rather
  than pretending the key closes it.

### 5. The seat sets are asserted, and the seat vocabulary with them

A test asserts, for every path shape this ADR adds, that the rule's seats are
exactly the set decided above — so removing `legal-sp` or `security` from any of
them is red rather than silent. A seat stripped from a three-seat rule previously
produced one failure, in a zero-key file.

It also asserts every seat string in `RULES` is one of the seats `ROLES.md`
lists. `ROLES.md`'s own heading says **eight**, and `pave/twokey.py` uses five
today; nothing checks that a rule's seat is a real seat, so a typo is an
unsatisfiable rule with no diagnostic.

## What the code got wrong, found by planting against it

Four seats reviewed the implementation in their own worktrees, forbidden from
touching AWS or any deploy path. Each finding below was measured, fixed, and
given a test.

- **This ADR's own anti-vacuity guard was vacuous one level in.** It tested
  `set(GATED_REQUIRED_PROPERTIES)` — a dict's *keys* — so
  `{"publish-highlight": set()}` satisfied it while the check it guards skipped
  on `if not wanted: continue`. **MER-AI-0001's disclosure flag deleted from the
  deployed contract set at 1814 passed.** Found by Legal/S&P, whose requirement
  it protects. Falsified prediction 5 in this ADR's single new assertion.
- **The seat-set pins were defended by three of the four seats they pin.**
  `tests/test_twokey_seats.py` sat on the enumerated protection-test rule, so
  ai-quality, security and platform-eng could drop `legal-sp` from decision 2's
  rule *and* edit the pin in one diff, with the seat losing its key never asked.
  ADR-037's shape on the rule this ADR added to close it. It now carries its own
  rule with the union of every seat it pins.
- **`ADR043_SEATS = {}` was silent at 1814 passed** — every pin decision 5 rests
  on, deleted by one token. Now ratcheted against `twokey.RULES`: each pattern
  this ADR adds must have a representative path pinned.
- **The harness rule named two entry points and the harness has five.** A
  repo-root `conftest.py` is an ancestor of both testpaths, so its hookwrapper
  applies to every item (1814 passed, G1 pin genuinely red); a new
  `pave/tests/conftest.py` drops the two-key mechanism's own test (1743 passed);
  a root `pytest.ini` outranks `[tool.pytest.ini_options]` entirely (1734
  passed). All three collected nothing. `tox.ini` and `setup.cfg` are the same
  precedence chain and are covered rather than measured.
- **A "prose correction" landed in model-facing text.** `handler.py:157` hands
  the input schema's `description` to Bedrock as the tool's spec. The correction
  grew that field from 309 to 568 characters of repo governance — naming the enforcing
  test file to the model. It escaped `TOOL_SPECS_SHA256` only because that pin
  iterates *routed* tools and `publish-highlight` has no routed Lambda at M02, so
  prediction 7 held by a coverage gap rather than by inertness. The description
  is now main's text minus the one false sentence, 274 characters, and the record
  lives here and in the test. `$comment` was tried and correctly refused by
  `test_every_tool_schema_stays_inside_the_supported_subset`.
- **The bypass check read only top-level input properties.** A nested
  `options.properties.skip_approval` reached `tools.contracts.json` at 1814
  passed carrying the literal blacklisted name, and output schemas were never
  read though the rule covers them. Now a recursive walk over both, with the
  traversal itself ratcheted — the first fix ratcheted the constants and left
  the code path that reads them silently revertible.
- **The disclosure flag's TYPE was unpinned** — `boolean` → `string` with
  `default: "no"` shipped green. Pinned.

**Owed, not fixed here**, each named by a seat with a measurement: the denylist
in `BYPASS_SHAPED` is defeated by a **differently-named** field — the nested and
output-schema forms the Security seat measured are closed by a recursive walk over
both schemas, and only the naming half survives, with `preapproved` measured
reaching `tools.contracts.json` green; the replacement is to pin the exact
property set per gated tool, which `additionalProperties: false` makes exact; **an unrouted tool's description is outside `TOOL_SPECS_SHA256`** and becomes
model-facing at M06 with no pin having watched it; the schema *rule* is path-shaped while the *check* follows the registry
pointer, so a schema moved out of `tools/<id>/` leaves the rule; a duplicate
registry id is a working forgery that `policy ⊆ registry` would not catch;
`ai_generated` is **not in `required`** and nothing reads its value, so what is defended is its declaration and its type, never that a caller sent it — M07's disposition is what makes the flag live; `semver` in the registry is decorative; and `cedar.py` is in no instrument
digest while ADV-008's `pass_when` turns on what it emits.

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | Each of the five plants, re-run after this ADR, **collects the keys named in decisions 1–3** — G1's widening, the `attacker-svc` permit, the `GATED_CONSEQUENCES` word, the schema edit, and the `conftest.py` hookwrapper | any still reports "two-key: not required" |
| 2 | The schema plant is **red** with a named failure and a remedy; the interlock plant was **already** red at 15 failures and this ADR adds only its key | the schema plant stays green — then decision 4's one new assertion is a claim rather than a check |
| 3 | G1's plant and the generator's plant remain **green and key-collecting**, and this ADR says so rather than implying otherwise | the ADR is read as closing them — the residual must survive review in the text |
| 4 | `--no-renames` (ADR-042 decision 4) collects the key on `git mv pave/infra.py pave/iam.py` + edit, and on `cedar.py` moved out of `core/` | either escapes — then the new rules are bypassable exactly as every pre-ADR-042 rule was |
| 5 | **Every check this ADR adds is deletable only loudly** — neutering each in turn produces at least one named failure, audited by neutering each in turn | any is silent — ADR-042 prediction 7b, which failed for four of ten checks on its first implementation |
| 6 | The seat-set test is red when any seat is removed from any of the three new rules, and the vocabulary assertion is red on a typo'd seat | either is green — then ADR-037's finding has a sixth arrival waiting |
| 7 | **No recorded number moves**: no entry in `evals/history/`, `pins.json` unchanged, `evals/comparators.json` byte-identical, no README `n/m` row moved, and the seven live instrument digests unchanged | any moves — then a rules PR touched the instrument |
| 8 | Zero model calls; `make check` green and hermetic; no new dependency | any fails |

Prediction 3 is the one that matters most for honesty. Two of these four holes
are closed by this ADR and two are made *expensive* rather than closed, and a
reader who takes the wrong impression from it would be exactly the reader
CLAUDE.md's "stated and absent" rule exists to protect.

## Consequences

- Four paths that decide an invariant stop being editable on zero keys, and the
  two whose prose claimed a seat now collect that seat.
- **Claim 10's existing protection acquires a key and a keyed harness.** The
  interlock is defended by fifteen assertions across three test files — real
  coverage, corrected in drafting after this ADR first implied otherwise — and
  all three are reachable only through a harness that one zero-key line disables.
  Decisions 2 and 3 close the key and the harness; the assertions were never the
  gap.
- **`ADV-008`'s stated relationship to the tool schema is corrected in the
  schema.** It was false in both halves and it was the reason given for deferring
  this rule.
- The G1 pointer in `CLAUDE.md` names a file that contains assertions.
- `pave check` gains no new step, and the gate gains no new lane. **This ADR adds
  keys and two assertions; it adds no mechanism.** The mechanisms that would make
  findings 1 and 3 red are M05's, and are named as owed.
- A residual is written down that was previously unstated: the test harness can
  report anything, a key makes that collectable rather than red, and a deleted
  test file is invisible to pytest.

**At scale, replace with:** branch protection requiring code-owner review on the
same path list, plus an org SCP that makes the G1 assertion redundant rather than
merely enforced; the path list here and the path list there are the same list —
the interface already matches.

## What this ADR does not do

It does not fix **finding 21** — a service declaring `classification: public`
denies 11/11 probes with a mechanism that counts as a policy denial and scores
**10/11**, against a best recorded arm of 7/10. That is a G4 semantics question
owned by Security, it moves `semantics_sha256` and therefore needs an instrument
registration, and it gets its own ADR. It is recorded in `SPEC/05` with the
measurement.

It does not build `pave new`, does not verify a manifest, does not add a gate
lane, does not change a threshold, a baseline, a probe, a guardrail or a recorded
number, and spends no model call.

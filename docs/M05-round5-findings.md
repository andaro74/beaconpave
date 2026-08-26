# SPEC/05 draft 5 — seat review round 5

**All six seats reported. Every one returned `VERDICT: redraft`. 49 blocking.**

Baseline: branch `m05-paved-road` at its draft-5 commit, `python -m pytest -q` =
**1881 passed**. **No SHA is cited here, deliberately.** That branch was never
pushed, so every commit on it — including the one this round was measured against —
is reachable from no ref in any other clone. An earlier version of this line cited
one, and `tests/test_cited_commits_resolve.py` caught it in CI while passing locally,
which is the whole reason that test exists: the object was still in the author's
clone and in no one else's. The tree itself is not lost — draft 5's text is the
parent content of draft 6.
(The round-5 brief said 1879. That was the lead's error; four seats caught it
independently by re-measuring, as instructed.)

| round | blocking |
|---|---|
| 1 | 39 |
| 2 | 31 |
| 3 | 20 |
| 4 | 55 |
| **5** | **49** — ST 11 · AIQ 11 · Sec 9 · PE 6 · DG 6 · TO 6 |

Round 4's record is `docs/M05-round4-findings.md`.

## The pattern, named by AI Quality

> Draft 4's failure mode was controls that were **stated and absent**. Draft 5's is
> narrower and harder to see — controls that are **stated, present, and demonstrated
> against the wrong subject**. Each would pass a review that read the mechanism and
> did not run it.

Three instances, all the lead's: pin 4 demonstrates the checker instead of the
application; pin 1 demonstrates a feasibility bound instead of a quality bound;
prediction 13 demonstrates arithmetic over observations that cannot contain the
field the predicate reads.

---

# PR 2 is the problem. It cannot be built as specified.

Five of the nine Security findings and four of the eleven AI Quality findings land
on PR 2 alone. It is the newest and most entangled part of the milestone, and it
entered because of the decision to fix the 11/11 case inside M05.

## S1 (BLOCKING — the finding of the round). Predictions 12 and 13 cannot both hold.

Security wrote both candidate predicates and re-scored. Each fails one prediction.

The exposure reproduces exactly, through the real path:
```
blanket-denial [classification] 10/11   [iam] 10/11   [policy] 11/11
detected levels: 10 x internal + ADV-007 sensitive
```

**Lenient** (absent field → PASS unearned, the ADR-038 precedent):
```
python -m pytest -q  ->  18 failed, 1863 passed
  test_the_marks_the_m01_pin_declares_match_the_milestone_that_recorded_them
m01 expected_earned 1->0 ; m04 expected_unearned [] -> ["ADV-007"]
blanket [policy] STAYS 11/11   <- prediction 12 FAILS
```
**Strict** (absent field → FAIL):
```
blanket [classification] 1/11  [iam] 0/11  [policy] 0/11   <- prediction 12 HOLDS
recorded M00b 0/10  M01 5/10  M04 6/10                     <- prediction 13 FAILS
```

**Root cause, not fixable inside PR 2.** Not one committed observation carries
`classification`. Measured by two seats independently:

| arm | obs | `mechanism` | `classification` |
|---|---|---|---|
| M00b | 10 | absent | **absent** |
| M01 | 10 | absent | **absent** |
| M04 | 30 | present | **absent** |

The underlying audit records are **not in the repository** — `grep -rln "ADV-007-m04-1"`
hits only `milestones/M04/probes-run.json`. The honest arm's one genuine policy
denial is ADV-007, `mechanism: classification`, and the detected level that would
credit it exists only in a lake `make check` may not reach (G8).

Prediction 13 as written pre-commits the milestone to treating its own correct
behaviour as a defect.

## S2. Item 7's load-bearing sentence is false.

*"`classification` is a required field of `audit.schema.json`, so this needs none of
the presence-versus-truthiness machinery."* Required in the **record**; absent from
**every committed observation**, which is what the scorer reads. This is ADR-038
amendment 1 arriving a third time — *"measured on an observation built by hand in a
test, not on one the capture path produces."*

## S3. Item 7 carries one field; the predicate needs three.

`classification` **plus** `witness` (an `iam` denial is claim 4's artifact) **plus**
the `tool` fragment (a Cedar decision is over `(principal, action, resource)`).
Two of three mechanisms are unclosable with what PR 2 proposes to carry.

## S4. The `policy` 11/11 case is not closable by any per-record predicate.

A blanket `forbid(principal, action, resource);` genuinely denies ADV-008's publish
call by Cedar; ADV-008's declared semantics is satisfied. **No property of that
single record distinguishes it from the honest interlock firing.** Security's strict
rule only worked because its blanket arm emitted no tool fragment — an attacker's
deployment emits whatever it likes.

What separates examined-from-refuses-everything is a **negative control**, which is
corpus-level, and **the repository already owns it**:
`quality/adversarial/probe-controls.yaml`, whose header states the argument verbatim
— *"A corpus of nothing but `expect: blocked` proves only that a control is strict,
never that it is right."* **Draft 5 mentions it zero times.** It holds one row
(CTL-011), guardrail-path only, and says *"This corpus scores nothing."*

## S5. Item 6's register-first ordering is unbuildable.

A register-first commit can only write **pre-change** digests. Security registered
`m05-A` with current digests: **1881 passed** — and it is a byte-identical duplicate
of `m04-D` under a second name, which **nothing in the suite objects to**. Then the
scorer change lands and `test_the_current_instrument_still_describes_this_tree`
fails, with the only remedies forbidden by ADR-034.

`instruments.json:4`'s "precondition" means **content ordering within one commit**,
which is what `m04-B/C/D` did. Item 6 must say: one commit, registering the
successor with **post-change** digests, moving the code together. Add a check that
no two registered rows share a digest set.

## AIQ8 / AIQ9. Prediction 13's remedy is refused by the machinery, by name.

`pave/history.py:527` — *"a different instrument is a second reading, not a
correction."* The only passing variant **omits** the instrument, which is false by
construction. The correct store is `evals/comparators.json`'s `expected_passed`,
three-key, which item 9 already names. **Prediction 13's second sentence contradicts
item 9 in the same document.**

---

# PR 1 — findings are specific and fixable

## S6. Item 5's surjectivity is set-level and misses cross-grants.

Built at set level as worded. Catches round 4's `attacker-svc` plant (RED). Then a
plant with **no phantom principal, only phantom grants** — every registered caller
granted every tool: `--check` exit 0, **surjectivity green**, `recap-agent` holding
the publish-class tool. The one test that catches it is `tests/test_toolplane.py:192`
— **the control item 13 removes in this same milestone.**

Fix: **bijection on pairs.** *Every `(principal, resource)` a `permit` names is a
grant the registry makes, and every grant is permitted.* Measured RED on the plant,
green clean.

**Items 4 and 5 are genuinely independent** — the duplicate-id plant is green under
both set and pairwise forms. Draft 5 has that right.

**Strengthen item 4:** the phantom-caller case is the weaker half. A duplicate
`- id: publish-highlight` with `consequence: read` and substituted schema paths
**overwrites the real entry**: consequence `publish → read`, and `ai_generated` gone
from the deployed bundle **without `schema.in.json` being touched** — `--check`
exit 0.

## S7. Item 3's fix closes the attack and makes the assertion vacuous.

The attack reproduces (2 keys, 1881 passed, *"Declared approver: none"*), and the
import closes it (2 failed). **But** dropping `"publish"` from `GATED_CONSEQUENCES`
then gives `tests/test_contracts.py` → **47 passed**: the loop iterates
`{"irreversible"}`, no tool carries it, the body never runs. **Verbatim the vacuity
draft 5 uses to refuse the registry move eight paragraphs earlier.**

Fix: add `assert GATED_CONSEQUENCES == {"publish", "irreversible"}` and
`assert gated` in the same file — equality plus non-emptiness, exactly the argument
item 20 makes for `DECLARABLE_LEVELS`. Name `tests/test_cedar_policy.py:472` as the
compensating guard on a different rule.

## TO3. Item 4's hard-stop emits the traceback the spec uses to condemn the registry move.

Built at the named location, the refusal works (`--check` exit 1, honest registry
1861). But the `ValueError` is uncaught: exit **1** not `EXIT_CONTRACT = 2`;
`pave check` catches only `SystemExit`, so it aborts with a traceback, runs no other
check, and **writes no verdict** — the outcome `pave/cli.py:1137-1141` exists to
prevent. Five-line fix: `_die(str(exc), gate_mod.EXIT_CONTRACT)` in `policy_generate`.

## PE1. The nine new rules are pinned by nothing, and four are self-guarded.

`ADR043_SEATS` pins fifteen paths; **none of draft 5's nine rows**. And the PR-1
instruments row, `test_budget_derivation.py`, `Makefile` and `recordings.json` all
carry `(ai-quality, platform-eng)` — byte-for-byte `pave/twokey.py`'s own seat set.
One diff deleting the PR-1 rule *and* the only headroom check *and* item 27's cited
precedent collects those two seats and reports **1879 passed, no failure**.
**ADR-035's shape inside the PR that cites ADR-035.**

## PE2. The parity test's home can be un-keyed in one token.

Deleting four characters — `_lane` — takes `tests/test_adversarial_lane.py` from
three keys to **zero, silently, 1881 passed**. Nothing pins that alternation's
membership. The lead's stated price ("a `twokey.py` diff plus a five-seat pin edit")
is wrong in both directions: no pin edit is required, and no pin exists.

---

# The remaining blocking findings, by seat

## Service Team (11)

1. **Onboarding is THREE seats, not five** — `ai-quality, legal-sp, tool-owner`.
   Both `security` and `platform-eng` entered draft 4's count solely via the
   probe-runner rule, which item 30 removes. *(Tool Owner computed the same
   independently.)* `evaluate()` reports only *missing* seats, so extra dispositions
   pass silently — the banner would teach every team to attest past rules they never
   triggered.
2. **`gates.eval_min_cases: 20 → 0` has no refusal row.** Still **1881 passed**. The
   milestone's headline defect, deferred by silence, which item 29 forbids.
3. **Row 9 raises `ZeroDivisionError` on a fresh scaffold** — disposed count 0, and
   the division precedes both asserts.
4. **Row 10 names `curated_by` for a pack whose `curated_by` is present** (`disposed:
   false` fires the same row).
5. **Item 39's sports cut does not open a green path.** A *fictional sports* title
   with event, start time and `sports-tier` is **the identical 16 failures**. The
   cascade is the judge freeze and it is **brand-blind**. Two facts were welded. The
   real cut: a scaffolded service may reuse the five committed titles; any service
   needing its own content is blocked, for any brand.
6. **`brand:` gets no verify-time refusal** — enforcement is a `print()` in a
   creates-only command. *(AI Quality measured `meridian-sports → meridian-news` at
   1889 passed.)*
7. **Two cedar messages don't teach and one misdirects** —
   `test_every_caller_the_registry_names_is_permitted` says "unregistered or
   uninvited" for a caller the registry **does** invite. Free to fix: PR 1 already
   lands in that file at four keys.
8. **No off-ramp.** `grep -i exception` on the spec returns nothing; `pave exception`
   is a stub; `ROLES.md:138-142` promises it and closes *"Paved roads without
   off-ramps breed dirt roads."*
9. **`pave evals dryrun` cannot be pointed at a scaffolded pack** — ignores `argv`,
   loads a module constant for `highlights-agent`. The cheapest road-shortener in
   the document, on a function that already discards its arguments.
10. **Steady-state cost unstated**, and the manifest rule reinstates 2 seats for a
    `p95_ms` bump. File-level, so `tool-owner` is collected for `owners.oncall`.
11. **The template's `tools:` value is unspecified**, and the pair list's
    normalisation ("values not compared") cannot pin it — while item 32's worked
    example depends on it.

**Answered clean:** item 30's five files **are enough**. Built
`services/sportscast-agent/`, added the caller, regenerated: **1881 passed**, and
exactly three files touched outside the service directory.

## AI Quality (11)

1. **Pin 1 does not stop a 50% cut.** `20 → 10` and `20 → 25` are both **1888
   passed**. The lower tie is a feasibility bound. **Prediction 10 is false as
   specified**, and 10 is the boundary-exact size item 26 flags.
2. **Pins 1+3: a default-argument diff takes the floor to 1** at **1889 passed**.
   Not circular, but defeatable. Pin 1 must pass `HEADROOM_BAND` explicitly.
3. **Pin 4 is silent against the exact round-4 attack it answers** — **1888 passed**.
   The form that fires calls `floors.check_headroom(<the committed pack>)` from a
   file other than the one under attack. **Prediction 3 must be reworded with it.**
4. **Item 27's pack-level header is a 47-failure migration.** `cases.yaml` is a
   top-level YAML **list**; restructuring is **47 failed, 1824 passed, plus a
   collection error** (raw `TypeError`). The cited precedent `labels.json` is a JSON
   *object*, where a header is free. **Refusal row 10 fails the reference pack today.**
5. **Two counting rules — unanswered and unmentioned.** `grep` for `:311` returns
   nothing. Measured divergence: rows 25 / disposed 19 / floor 20 → the row-counting
   test **passes** while the disposed floor is breached and the disposed ratio is 0%.
6. **Item 28's denominator is 0/0 for the guaranteed first input.**
7. **Item 26's vocabulary does not close the N=20 absorption**, because item 25 keeps
   the nested location and the vocabulary is top-level only. N=21 catches twice; N=20
   top-level-only once; **N=20 with nesting zero times.** Either drop
   `judge.expect_near_threshold` in the same PR, or set the floor to 21.
8. See AIQ8 above.
9. See S1/S2 above (found independently).
10. **Item 39's deferral is RIGHT and M05 does not owe the second brand** — but the
    cut needs a check, not a sentence.
11. **Prediction 11 is uncheckable** — "the starter three" packs do not exist and the
    phrase is never defined. The same undefined set anchors pin 1's upper tie.

## Data Governance (6)

1. **The key drop is right** — planted `brand`, a publish-class declaration, and
   `owners.oncall`: all **1881 passed**, none of them this seat's after M05.
   **But the seat now holds zero keys anywhere.** Census: security 18, platform-eng
   17, ai-quality 16, tool-owner 4, legal-sp 3, **data-governance 0** — while
   `DECLARABLE_LEVELS` sits on `(ai-quality, security, platform-eng)`, so three seats
   can widen it back and the taxonomy's owner is not among them.
   `tests/test_no_account_identifiers.py:29` names *"a Data Governance decision"* and
   is on no rule.
2. **Item 20's G5 pin is satisfied by the branch that is not G5.** Deleting
   `classify.py:124-125` leaves the new pin **3 passed**. The only live
   G5-by-design witness passes `declared="sensitive"` — the value item 19 makes
   undeclarable. The loop must be over `classify.LEVELS`, not `DECLARABLE_LEVELS`.
3. **"Exactly four `route` tests" is five** — and `:283` is the sole G5 witness.
4. **ADR-046's re-entry condition is insufficient.** Made it true — added a branch so
   `classify_request` returns `public` — and declaring `public` is **still an
   outage**. The right condition is item 20's own behavioural pin.
5. **Item 7 names the wrong store.** Observations do not persist to
   `evals/history/*.json`; they live in `milestones/<TAG>/probes-run.json`, which is
   **worse** — it already carries `model_text` verbatim in a public repo.
6. **The `error` refusal is incomplete**: also `tool.args`, `tool.reasons`,
   `principal`, and `error.message` on an `iam` denial (verbatim AWS error = account
   ARN). *(Security reached the same list from the predicate side — S3.)*

**Coupling neither ADR states:** the predicate is exact only while `classify_request`
returns two levels. ADR-044 must pin the literal `"sensitive"` and name ADR-046's
re-entry as the event requiring revisit.

**`jefferson-city`, corrected upward:** **242 occurrences across 68 files**, and
`data/catalog.json:3` asserts *"6 fictional DMAs"* — false of one of its six. Live
surfaces renameable at 19 failed (catalog) + 15 (classify.py) through a judge
re-freeze; **the recorded artifacts are sha256-pinned by append-only history and
cannot be renamed at all.** Belongs under "What M05 does NOT build".

## Tool Owner (6)

1. **Item 21's reverse direction FAILS on the only committed manifest.**
   `highlights-agent` declares two tools; the registry grants three. Reverse
   violations: `['publish-highlight']`, consequence `publish`. **The manifest PR 4's
   verifier must be green against fails.** Neither fix is free.
   Item 22's *"all three tools at `^0`"* is **two** — a round-4 **plant** carried
   forward as a present-tense fact.
2. Onboarding is three seats *(= ST1)*.
3. See TO3 above.
4. **The registry row still needs Security.** With all PR 1 guards installed, adding
   `attacker-svc` to `publish-highlight`'s `callers:` is `--check` exit 0, **1862
   passed**, `['legal-sp','tool-owner']`. And the grant is real: **the forbid gates
   *when*, the permit gates *who***, so `attacker-svc` reaches the tool on the same
   approval context. Neither PR 1 guard sees it.
5. **`pave/cli.py:746` sends every scaffolded service to
   `services/<svc>/run_probes_via_gateway.py`** — a file `pave new` never renders and
   the team cannot write without two seats. The first instruction the adversarial
   lane gives a scaffolded service is unfollowable.
6. **Item 13's key cost is false.** Both generated artifacts are on **no rule**; the
   minimal commit is **two keys**. The four come from `handler.py` and
   `test_toolplane.py`.

**Non-blocking of note:** a decorative `semver:` is **worse than no field**; the
synthetic registry must be an **in-module literal, not a committed fixture**;
item 3's import is safe *because* it lands in the four-key file where 16 assertions
still fire, with `test_cedar_policy.py:471-472` as the guard — **name it**.

## Platform Engineering (6)

1, 2 — see PE1, PE2 above.
3. **`pave verify` is not a runnable command.** The `pave` console script exists only
   after `pip install -e .`, and from `platform/infra` the module is not importable.
   Correct literal: `python -m pave.cli verify --all && cd platform/infra && cdk deploy --all`.
4. **The two "verbatim" template files carry `highlights-agent`'s identity** —
   `answer.schema.json:3`'s `$id` (two scaffolded services collide) and the golden
   README's title. The same reasoning was applied to `gateway_client.py.tmpl` one row
   up.
5. **Nothing makes the verifier iterate services.** No test enumerates `services/*`;
   both CI eval steps are hard-coded. The premise sentence is closed by nothing unless
   `test_manifest_verify.py` globs and asserts the glob is non-empty.
6. **`recap-agent`'s removal is a fifth scope cut with no ADR** — 1881 passed, zero
   failures, two tests passing under names they no longer test.

**Confirmed:** the whole seat table transcribes at **1881 passed, zero failures**
(draft 4's was 2 failed). **Item 17 verified end to end** — `pave check` exit 1 →
`verdict-contract.json` FAIL → `gate decide` BLOCK exit 1. **No workflow edit, no
attestation cost; the lane was not necessary.** The `mkdir`/`is_dir`/`exists`/
`iterdir` audit found **no forty-sixth sentinel**, but did find a working ratchet at
`test_contracts.py:661` an implementer might "fix" into silence.

---

# Settled — do not re-litigate

- **`GATED_CONSEQUENCES` does not move.** Security checked for a hole the move would
  have fixed and found none: a consequence downgrade is **16 failed**, ratcheted.
  Withdrawal correct.
- **`legal-sp` stays** on the Cedar and schema row. Fully closed.
- **`README.md` off the rules**; `data-governance` not in `twokey.RULES` — both
  withdrawals leave no hole (PE, DG).
- **Item 17: assertion, not lane.** Verified end to end.
- **`pave/verify.py` is the right home** — `pave/gate.py` and `pave/tests/test_gate.py`
  both stay at zero keys, so the asymmetry is avoided rather than relocated.
- **The five rendered files are enough** — 1881 passed, three files outside the
  service dir.
- **The eleven `recap-agent` sites are complete**; the `- id:` anchors are unambiguous.
- **Items 4 and 5 are independent** — neither subsumes the other.
- **Item 24's residual is correct in both directions.** Deletion-plus-padding
  measured at **1883 passed**, *above* baseline, with G4's scoring protection gone.
- **The second brand is M08's, not M05's** (AI Quality, explicit).
- **`DECLARABLE_LEVELS` relocation, the four-level table, detected-vs-declared
  separation** — all re-confirmed exact.
- **G1 clean in this diff**; G8 and G10 clean.

# Lead errors this round, for the record

1. Brief said **1879**; the tree is **1881**. Four seats caught it.
2. **"Five attestations"** — it is three. Two seats, independently.
3. **Item 22's "all three tools at `^0`"** — two. A round-4 plant carried forward as
   fact about the tree.
4. **Item 39's sports cut** welded a brand-specific fact to a brand-agnostic one.
5. **Item 7's store name** — `evals/history/` holds no observations.
6. **Item 7's "required field"** — true of the record, false of the observation.
7. **"Exactly four `route` tests"** — five.
8. **Item 13's key cost** — two, not four.
9. **`test_calibration_owe.py` "(8 tests)"** — it collects four.
10. **Item 36's recipe** does not run the verifier.
11. **The parity test's stated price** — wrong in both directions.
12. **`m01` is 6/10** under the current instrument, not 7/10 (`expected_passed` vs
    `recorded_passed`). Predictions 12 and 13 must say which number they mean.

# Decisions a human owes before draft 6

**On PR 2 (all three are Security's list, in order):**

1. **Does PR 2 accept that ADV-007's pass in `m01` and `m04` becomes unearned** —
   moving `expected_earned`/`expected_unearned` in `evals/comparators.json` under its
   three-seat rule with superseding entries — **and prediction 13 is rewritten before
   the work starts?** The alternative is re-deriving the arms from a lake fetch, which
   is a network operation and breaks G8.
2. **Is the `policy` blanket-denial case closed by a Cedar-side positive control in
   `quality/adversarial/probe-controls.yaml`, or declared NOT closed by M05 in
   ADR-044?** It is not closable by any per-record predicate.
3. **Does `services/*/pave.manifest.yaml` take Security's key when the declared tool
   set intersects `GATED_CONSEQUENCES`?** Today the complete path to granting a
   scaffolded service the one human-approval-interlocked tool collects
   `ai-quality, tool-owner, legal-sp` across two diffs and **never Security**.

**On PR 1:**

4. **May four rows be guarded by their own seats** (`ai-quality, platform-eng` = the
   seat set on `twokey.py` itself)? G9 call; the seats in question are two of the
   three that would decide it.
5. **Is `recap-agent`'s removal "the control was always synthetic" or "M05 deleted a
   real control"?** Determines whether a fifth ADR is written.

**On scope:**

6. **Does Data Governance hold any enforced key at all**, or is the seat recorded as
   advisory-only? It currently holds zero, and it owns the taxonomy three other seats
   can widen.
7. **Is `jefferson-city` recorded as a named debt** under "What M05 does NOT build"?

# Recommendation

**Split PR 2 out and build PR 1 now.** PR 1's findings are specific, measured and
have stated remedies (S6, S7, TO3, PE1, PE2). PR 2's are structural: two predictions
that cannot both hold, a field that exists in no committed observation, and one of
three mechanisms that no per-record predicate can close. That is a milestone's worth
of design, not a build item, and it is what Security's three decisions are about.

PR 1 is also the piece two seats called the highest-value thing in the document —
`tests/test_contracts.py` holds the only assertion that a publish-class tool declares
an approver, and it is on no rule.

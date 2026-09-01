# M06b Decisions 3 and 11, measured up for the seats

**This document decides nothing.** It measures two open decisions so the seats
that own them decide on evidence rather than on the register's prose. **Zero
model calls. Nothing is deployed.** `twokey.triggered` on this file and the SPEC
annotation beside it returns `[]`.

Both decisions were taken to be independent. **They are not**, and the coupling
is the finding: Decision 11 asks whether un-deferring may move the comparator,
and the measurement below says the assert cannot pass on any evidence that
exists, whichever way Decision 3 goes. So Decision 11 is not ripe, and saying so
is more useful than answering it.

Every figure was measured on `main` at `6e9ef5b` with the command beside it.

---

## The state of the assert, measured rather than quoted

`evals/deterministic.py:365` dispatches `tool_before_answer` from
`case["trajectory"]` and reads its evidence from `record.get("trajectory")`.

```
$ grep -c trajectory evals/run_evals.py
0
$ grep -n "def score_suite" evals/deterministic.py
412:    def score_suite(self, cases: list, answers: dict, catalog: dict) -> list[CaseResult]:
```

`record` is the answers-file entry, which carries `['answer', 'usage']`. **No
parameter on the path from the lane to the assert can carry a trajectory**, so on
every run the lane re-scores, the assert's input is `None` and its verdict is
`no-evidence`. That is B3's finding, still true, and it is the premise of both
decisions.

The evidence does exist. `run_with_tools.py:254` writes a sibling
`-trajectory.json`, read by exactly one test
(`tests/test_deterministic_runner.py:106`) and by nothing in the lane:

```
milestones/M02/runs/m02-control-{1,2,3}.json      records 45/44/42   with trajectory 0
milestones/M02/runs/m02-tools-{1,2,3}.json        records 47/47/47   with trajectory 0
milestones/M02/runs/m02-tools-1-trajectory.json   records 25         with trajectory 25
milestones/M02/runs/m02-tools-2-trajectory.json   records 25         with trajectory 24
milestones/M02/runs/m02-tools-3-trajectory.json   records 25         with trajectory 25
```

### The fact both decisions turn on

**No committed run carries a single execution witness.**

```
$ grep -ro '"executed": *true' milestones/ | wc -l
0
$ grep -ro '"executed"' milestones/ | wc -l
3          # all in g3-runtime-denial.json (false) and prose
```

`tool_before_answer`'s pass condition is
`step.get("decision") == "allowed" and step.get("executed") is True`
(`deterministic.py:265`). `executed` arrived with **ADR-057**, after every pinned
run was taken. So even a lane wired to the sibling trajectory file scores
`no-evidence: authorized but nothing witnesses that it ran` on all 25 cases of
every tools-arm run, and `no-evidence: no trajectory recorded` on every
control-arm case.

**The assert cannot return PASS on any committed evidence, under any of Decision
3's options.** That is not an argument against any of them; it is the reason
Decision 11 cannot be taken yet.

---

## Decision 3 — where the trajectory assert reads its evidence

Owner: unassigned in the register. The evidence path touches Platform
Engineering (the capture path) and AI Quality (what the assert may claim);
`SPEC/06b` Decision 3 records option A as **refused** already.

### Option A — a `trajectory` parameter on `build_record` — REFUSED, and the refusal holds

Writes `outcome.trajectory()`, the gateway's own self-report, *into* the lake.
Fetchable without becoming independent, against the standard `audit.py:10-18`
states in its own words.

Price, as the register records it: `audit.py` and `toolloop.py` are folded into
`capture_sha256` and `guardrail_sha256`, so a change there is
`('platform-eng','security')` **plus a new instrument registration** — three keys
— **plus 15 tests to bring green**. Nothing in this document disturbs that
refusal.

### Option B — read the sibling `-trajectory.json`

Plumb a trajectories mapping through `run_evals` → `score_suite` → `score_case`.

- **Cheapest by a wide margin.** No digest moves, no instrument registration; the
  file already exists and is already committed beside every tools-arm run.
- **It is still the gateway's self-report.** B2 planted a hardcoded step naming a
  tool nothing called: suite BASELINE, ruff clean, and the pre-flight guard at
  `run_with_tools.py:246` is *satisfied by the forgery* because the forged step
  says `allowed`.
- **It does not help the control arm at all**, which writes no trajectory file —
  so 12 of its cases stay `no-evidence` permanently, and the M02 control is the
  arm every later delta is measured against.
- **It changes what the comparator's pinned runs mean** without any new run being
  taken, which is Decision 11's whole concern arriving through the back door.

### Option C — derive the trajectory from the audit lake

- **The lake is a field-complete witness, and B2 measured this**:
  `toolloop.trajectory()` and `_tool_records` iterate the same `outcome.calls`
  and emit the same field set, so every field the trajectory carries is
  recoverable from `{record.tool.*, record.seq}` by an independently fetchable
  path. The lake holds the *same* thing, not a weaker one.
- **A derivation must remap before it sees anything.** `as_record_fragment` keys
  the tool as `id`; `Scorer.tool_before_answer` reads `step["tool"]`. B14
  amendment 1 records that "fails closed" was measured on a shape returning *no
  evidence* because it matched nothing.
- **B14 is unfixed and fails OPEN one step out.** `request_id` is caller-supplied
  and `executed` does not attribute a run to a turn, so a second invocation
  reusing a `request_id` inherits the first one's witness and the assert returns
  PASS for an invocation that called nothing. A lake derivation is the option
  that *arms* that hole, which is why B14 was left open deliberately rather than
  folded into ADR-057.
- **It cannot be applied retroactively either.** The pinned runs' records predate
  `executed`, so the derivation returns UNKNOWN for all of them.

### Option D — require both and refuse a disagreement

B2's own "what a fix must survive" list ends with: *a response trajectory and
lake records that **disagree**, which must be a hard failure rather than a
preference for either side.* Option D is the only one that implements that
sentence.

- Strictly stronger than B or C alone: the forgery B2 planted is caught, because
  the lake does not corroborate it.
- Costs both plumbings, and inherits B14 from option C.
- **Its failure mode is an outage**, not a false pass — a lake fetch that
  throttles becomes a disagreement, so the INFRA mapping has to be right before
  this is safe. That mapping is Decision 11's business, which is the second place
  these two decisions touch.

### What the seats are actually choosing between

Not four options but two questions, and the register conflates them:

1. **Is the assert allowed to read a self-report at all?** A says yes and is
   refused. B says yes with an extra hop. C and D say no.
2. **Must the evidence be independent, or merely present?** Only C and D make it
   independent, and both are blocked behind B14's attribution hole for anything
   stronger than "the tool ran somewhere in this prefix".

**A recommendation, offered as one:** B is cheap and does not answer question 1
honestly; C is right and is not safe while B14 stands; D is right and expensive.
Nothing needs deciding *this milestone* — see Decision 11 — so the useful move is
to take Decision 3 **after** the scored run produces the first evidence carrying
`executed`, when C and D become testable against real records instead of
reasoned about.

---

## Decision 11 — may un-deferring move `evals/comparators.json`?

Owner: AI Quality, three keys.

### First, a mechanical finding the register does not record

**`DEFERRED_ASSERTS` is a declaration that nothing enforces.**

```
$ grep -rn DEFERRED_ASSERTS --include=*.py .
evals/deterministic.py:54          the dict
evals/judged.py:121-122            builds the instrument's scored/deferred lists
evals/run_evals.py:494             prints the reason
tests/test_judged_entry.py:272     asserts the list
```

`Scorer.score_case` never consults it. The deferral is hardcoded — 
`deferred.append(...)` at `deterministic.py:365` and `:385`. So:

- Removing `tool_before_answer` from the dict scores nothing. Measured: **2
  failed**, both about the *declaration* (`test_the_instrument_names_the_new_kind…`,
  `test_the_entry_records_what_scored_the_deterministic_half`).
- Changing `deferred.append` to `results.append` scores it while the dict still
  declares it deferred. Measured: **18 failed**.

The two can disagree, and only the second is the real un-deferral. For
`entitlement_source` the disagreement is caught by consequence (**5 failed**,
including the lane) because scoring it moves numbers — not by any check on the
declaration itself. Worth a rule of its own; not proposed here.

### What un-deferring costs today

```
$ sed -i 's/deferred.append(self.tool_before_answer/results.append(self.tool_before_answer/' evals/deterministic.py
$ python -m pytest -q | tail -1
18 failed, 2387 passed, 6 skipped
$ cp <backup> evals/deterministic.py && git diff --quiet     # restored
```

| pin | today | scored | keys |
|---|---|---|---|
| goldens, tools arm `expected_passed` | 15 | **9** | three |
| goldens, control arm `expected_passed` | 17 | **12** | three |
| `M00B_UNDER_CURRENT_INSTRUMENT` | 18 | **10** | three |
| `M01_UNDER_CURRENT_INSTRUMENT` | 19 | **13** | three |

`SPEC/06b`'s headroom table predicted `m00b 18->10` and `m01 19->13`. **Both
reproduce exactly.** The register's "9 failures" figure was for an always-FAIL
stand-in; the real un-deferral is 18.

### Why the number is not the point

**Every one of those movements is `no-evidence`.** Not one is a case where the
platform was asked for a tool call and did not make one. Two independent reasons,
either alone sufficient:

1. The lane passes no trajectory at all, so the input is `None` (Decision 3).
2. No committed run carries `executed: true`, so even wired to the sibling file
   the verdict is `no-evidence: authorized but nothing witnesses that it ran`.

And `no-evidence` **must be INFRA, not FAIL**. `deterministic.py:248` says so in
its own words — *"the service answered wrongly"* and *"the harness could not
establish whether it answered wrongly"* page different people — and `SPEC/06b`'s
*What M06b must not do* repeats it. A deferred assert reaches no case verdict, so
that mapping does not exist yet; the diff that scores this assert is the diff
that must build it.

**So un-deferring today would record roughly six cases per arm as FAIL when the
honest verdict is INFRA, and move four three-key pins to do it.** That is not a
comparator movement anyone should attest to.

### The answer the measurement supports

**Decision 11 is not ripe, and the register's framing — "may it move the
comparator, or land ADVISORY" — is a false choice.** Both branches assume the
assert can say something true about the runs being scored. It cannot, on any
committed run, under any of Decision 3's options.

What makes it ripe is a run whose records carry `executed`, which means: deploy,
then take the scored run through the ADR-057 gateway. At that point

- the assert can PASS, so a movement is a measurement rather than an artifact;
- B13's re-adjudication has something to adjudicate;
- and the comparator diff can state which cases moved *because the platform did
  something different*, which is the only kind of movement `CLAUDE.md` lets a
  baseline change on.

**Recommendation:** take neither decision this milestone. Record Decision 11 as
**blocked on evidence** rather than open, with the unblocking condition named —
one scored run carrying `executed` — and take Decision 3 immediately after it,
when C and D can be measured instead of argued.

That ordering costs nothing: M06b does not advance claim 10 either way, and
`SPEC/06b` Decision 2 already commits `entitlement_source` to staying deferred
until the trajectory eval can verify the call.

---

## What this document does not claim

- **It does not take either decision**, and no seat is bound by the
  recommendations. It collects no keys precisely so it cannot.
- **It does not measure a lake derivation**, because none exists to measure —
  B14 amendment 1 records that "fails closed" was itself measured on a shape that
  matched nothing.
- **It does not re-open ADR-057 or B14.** B14 stays open; option C is simply the
  branch that would arm it.
- **The `DEFERRED_ASSERTS` finding is reported, not fixed.** A declaration the
  scorer never reads is worth a rule; proposing one inside a document that exists
  to decide nothing would be the shape this repository keeps finding.

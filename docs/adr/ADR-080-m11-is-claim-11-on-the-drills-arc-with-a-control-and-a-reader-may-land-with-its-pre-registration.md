# ADR-080: M11 is claim 11 on the drill's arc, with a control; the go/no-go artifact has its own schema; and a reader may land with its pre-registration

**Status: PROPOSED at M11 PR 1, 2026-09-13. ACCEPTED when that PR merges**, which is the
operator's disposition. It was written before any drill code, scenario, fixture or run, with
zero model calls and zero AWS calls.

**What the operator set, and this ADR records rather than argues:**
- the scope: the `README.md:52` row;
- the claim: the arc, with a control;
- the artifact's own schema;
- the cap, four PRs with a named spare;
- the CLAUDE.md amendment.

Everything else is derived below, at line.

**Seats:**
- PM: the spec.
- AI Quality: the falsifiers and the schema.
- Platform Engineering: the writer, the readers and CLAUDE.md.
- Service Teams: the owner and the window named in the artifact.
- Security: the signature, and debt 10.

---

## Decision 1 — the feasibility rule, applied, and amended in one line

**The check, taken at `8ac2aaa` before this was written.**
- **The false state is today's tree.** `drill/` holds one stub README.
  `python -m pave.cli drill --event jefferson-derby --tier 3` printed
  *"[pave drill] (stub) would: … emit a machine-signed go/no-go artifact"* and exited 0.
  `make drill` (`Makefile:65-66`) did the same, and `git status` stayed clean.
- **No existing command detected it:**
  - `gate decide` reads verdict records only. Their schema is closed
    (`quality/verdicts/schema.json:7`) and has no owner, fix-by or signature field.
  - None of the eleven committed `*schema*.json` files is a go/no-go schema.
  - No test reads a go/no-go artifact.
  - `tests/test_documented_commands.py:102-105` never runs `pave drill`.
- **The verdict:** not pre-registerable as written.

**The verdict stands, and the rule was too strict.** The rule required the detecting command
to exist before the spec. So a claim about a component that does not yet exist could never
be pre-registered, even when its readers are small and can ship before anything is read.

**The amendment** (CLAUDE.md, *Milestone discipline*): the command may exist today, or it may
land in the same PR as the pre-registration, shown emitting a value before the claim is
committed.

What the amendment keeps:
- **The ordering.** A reader's output is observed before the claim is fixed.
- **Two refusals, unchanged.** A claim with no nameable false state is still not
  pre-registerable, and so is a term true by construction.

**Where the pre-registration sits.** SPEC/11 proposes the claim and pins every value. PR 2
commits the claim as `milestones/M11/pre-registration/falsifiers.json`, after
`readers.txt` in the same PR. `git log` order is the evidence. A test in PR 2 holds the
committed record equal to SPEC/11's pins, so the proposal and the registration cannot drift.

## Decision 2 — the claim is the arc; each term's false state; the one half that is true by construction

**Conformance is not a term.** The writer validates before writing, so no non-conforming
artifact is ever written and a conformance term cannot fire. ADR-079 amendment 2 is the
reason, and it is not repeated here.

**Each term, a state of the world in which it is false, and what keeps it from being true by
construction:**

| term | false when | why nothing upstream forces it |
|---|---|---|
| **F1**, seeded is NO-GO for the seeded gap | the threshold is read as 5.000 s with `>`, so the seeded 5.000 s gap is no finding; the parser drops a cue whose timestamp has an hour field; the writer hashes and checks different files | the schema may hold no finding (SPEC/11 constraint 2) |
| **F2**, the pinned owner and window | the writer falls back to a default owner, such as `pave new`'s `webhook:<service>` (`pave/cli.py:1268`); the window defaults to a whole day; the tier arrives as a string and misses the table | each pinned value differs from those defaults (decision 3); the schema holds none; the writer has no default (constraint 3) |
| **F3**, a hand edit is refused | the signature covers some fields and not others; `verify` compares `key_id` only; `verify` returns 0 on an exception | see below |
| **F4**, the control stays NO-GO | the delta drill re-checks only paths changed since the prior's commit: C differs from S by the committed seeded artifact alone, so this defect writes GO; the delta suppresses findings already in its prior; the delta treats a named owner as acceptance | the control is its own run, at a different commit, reading the prior |
| **F5**, the fix yields GO | the check reads a cached copy or the prior's inputs; the fix does not restore the bytes | the fixture's bytes are pinned to PR 2's |

**F3 has one half that is true by construction, and it is not counted.** The writer and
`verify` share one key and one canonical form, so `verify` accepting the unaltered artifact
is guaranteed. It is run first as the plant's liveness and is not evidence.

The refusals count. Two design rules keep them honest:
- **The signature is checked before the schema** (constraint 5). Flipping `decision` to `GO`
  while findings remain may break a schema rule. A `verify` that validated first would then
  refuse the copy for that reason. It would refuse even when the signature did not cover
  `decision` at all, so the edit would exercise the wrong door.
- **Two of the three edits keep the artifact schema-valid**: `owner.oncall` and `fix_by`'s
  year. Even a verifier in the wrong order meets those two on the signature alone.

**Why the control holds the caption bytes constant, and what that costs.** The operator's
wording is *"the delta drill run WITHOUT the fix applied"*, so the control's fixture is the
seeded one, byte for byte. That separates a GO the fix caused from a GO the delta machinery
produces on its own. That second GO is the vacuous confirmation of ADR-035 amendment 5
(:1073-1077).

**The cost is one unexercised defect.** A delta drill that says GO on *any* change to the
failing input passes all five falsifiers, because the fix is the only edit to the fixture.
Separating it would need a second control, a non-fixing edit. The scope is one claim and
five falsifiers, so that check is **a PR 2 test, not a sixth falsifier**, and SPEC/11 names
it under *what a GO does not show*.

**The writer decides, and here that is the thing measured.** M10's row 16 (D1) found
falsifiers that read a writer's mapping in place of the envelope they claimed to measure.
Claim 11 is about the drill's decision, so reading `decision` reads the claim's own subject.

The arc and the control separate a decision taken on the captions from two wrong decisions:
- **A constant decision** fails F1 or F5.
- **A delta that decides by construction** fails F4.

## Decision 3 — the pinned values, and why each is that value

- **Threshold > 4.000 s, cues of 5.000 s, contiguous.** The clean fixture has no gap, so it
  yields no finding. Deleting one cue is the smallest seed that crosses the threshold, and
  it leaves a 1 s margin either way.
- **`service-team` and `webhook:player-captions`.**
  - Service Teams are ROLES.md seat 7. Captions belong to the surface a service team runs.
  - The oncall value differs from the default `pave new` writes, `webhook:<service>`
    (`pave/cli.py:1268`). A writer that falls back to that default cannot pass F2.
- **129600 s, 36 hours.** It is not a whole number of days, so a writer that defaults to 24,
  48 or 72 hours fails F2.
- **HMAC-SHA256, from the standard library, and no new dependency.**
  - The declared dependencies are `pyyaml` and `jsonschema` (`pyproject.toml`).
    `cryptography` 49.0.0 happens to import in this checkout, but it is not declared, so
    Ed25519 would be a new dependency.
  - **This is a MAC, not a digital signature.** Anyone holding the key can produce a valid
    one.
  - **The cut:**
    - The key lives in `BEACONPAVE_DRILL_KEY` and is not committed before the last reading.
    - PR 3 publishes it after that reading, so a stranger can re-run F3.
    - Once published, the signature proves nothing further; git history carries the
      artifacts from that commit on.
  - **At scale, replace with** an asymmetric KMS key that only the drill's role may sign
    with. `alg` and `key_id` already carry the interface.
- **The fixture lives under `drill/fixtures/`, not `surfaces/web-player/`.**
  - Why: M10's row 20 leaves `surfaces/web-player/` for the first claim-3 spec to keep or
    remove, and a fixture there would tie claim 11's evidence to that decision.
  - At scale, replace with a check against the event's published caption track. The
    scenario file's mapping from an event to its caption source is the interface.
- **The canonical form and the on-disk form are pinned.** F3's edits are text substitutions,
  so the file's layout is part of the plant.

## Decision 4 — scope: the `README.md:52` row, one scenario, no deploy

- **Claim 11 only.** Not claims 7, 8 or 12, and not the self-heal classifier. No deploy and
  no model or AWS call.
- **`BUILD.md:30` named three scenarios. M11 builds the caption check alone.** The other two
  are cut, and `BUILD.md:30` says so in this PR.
  - **Blackout sweep.** Its ground truth is `entitlement-check`, a deployed tool
    (`platform/infra/lib/gateway-stack.ts:58`), and the milestone deploys nothing. Owner:
    Tool Owner. Unscheduled.
  - **Alarm self-test.** ADR-007's webhook has no receiver in the repository, and the artifact
    could record only that a request was sent (ADR-007:24-28). Owner: Platform Engineering.
    Unscheduled.
- **Risk acceptance is cut.** Act 4 says humans *"formally accept risks"*
  (`docs/governance/demo-script.md:172-173`), but `pave exception` stays a stub
  (`pave/cli.py:1732-1734`).
- **No gate lane.** `gate decide` does not read the artifact.
  - `pave/verdict.py:4-5` still says the drill emits a verdict record. That is M10's row 21,
    and it is not edited.
  - At scale, replace with a gate lane that reads the go/no-go artifact beside verdict
    records; the artifact's own schema is that lane's contract.
- **The event id `jefferson-derby` is already in use** at `Makefile:66`,
  `docs/governance/demo-script.md:170` and `data/catalog.json:5` and `:8`. M11 adds uses of
  it, which widens the DMA rename's blast radius (ADR-075 amendment 8). M11 does not rename
  it.

## Decision 5 — the cap, and the spare

**Four PRs in all, including this one: PR 1, PR 2, PR 2b (the spare) and PR 3.**
- **The arc and the close share PR 3**, because four slots hold three planned PRs and a
  spare.
- **Every PR opened against `main` counts, including an exhibit.** M10's close found two
  counts of one cap because exhibits were uncounted by precedent (ADR-079 amendment 2,
  *The cap*). So PR 2's deletability audit runs through a local `pave check`, not an
  exhibit.

**The spare is a cold review of PR 2's writer and readers against SPEC/11's pinned table,
before PR 3 runs.** The reviewer must have written neither. The review has four limits:
- Its repairs land in the spare.
- It moves no pinned value.
- It adds or drops no falsifier.
- It runs nothing.

If it is not taken, the slot is not spent on anything else.

## Decision 6 — carried in, and none resolved

- **Debt 10** (`milestones/M10/README.md:328`, row 30) is unsigned at M10's close. It is
  carried. M11 produces no goldens refusal census, so that trigger does not fire. The
  signature route stays open to any PR, and M11 does not schedule it.
- **M10's rows 1–29 are carried unchanged.**
  - **Row 28 fires** when PR 2 edits `pave/twokey.py`. PR 2 records the firing and does not
    pay it.
  - **Rows 20, 21, 23, 27 and 29** go unedited under SPEC/11 constraint 8.
  - **Row 22** is not paid: CLAUDE.md's rule stays prose after this amendment.
- **Row 31, `brand_tone`**, is `re_deferred_to: M11` (`quality/judge/calibration/labels.json:355`).
  `tests/test_calibration_owe.py:53-59` goes red when M11 closes unpaid. PR 3 pays it or
  re-defers it on two keys, and this ADR does not choose which.
- **09c's debt 1** (the browse gap, Tool Owner, on a `catalog-search` semver bump) and
  **debt 3** (the `tokens_out` tiers, AI Quality) are not touched. 09c's other rows carry
  unchanged.
- **Act 4's recording** is `owed_by: M11` (`docs/governance/recordings.json:49-56`), a close
  obligation for PR 3.

## What this ADR does not decide

- the spare's findings;
- `brand_tone`, paid or re-deferred;
- whether Act 4 is recorded or deferred;
- debt 10's signature;
- where the drill key lives beyond M11;
- when the blackout sweep or the alarm self-test is scheduled.

## Consequences

**If the arc holds**, claim 11 carries a proof of what its row says: a drill that goes red on
a seeded fault, stays red when nothing was fixed, and goes green when something was.

**It is still narrower than a readiness drill:**
- one scenario;
- a committed fixture, not a live system;
- a MAC in place of a signature;
- no page and no human.

Each of those is a cut above with its at-scale line.

**If any falsifier fires or any run is INVALID, M11 closes RED** with the falsifier or the
run named, and nothing is re-run.

**At scale, replace with** drills scheduled against staging for every event tier. Each would
run all three scenarios against the deployed packager, entitlement tool and pager, and write
an artifact signed by a KMS key and read by a gate lane. The artifact's schema, `mode`,
`prior_sha256` and `signature.alg`/`key_id` already carry that interface.

---

## Amendment 1 (2026-09-13, M11 PR 2, after the seat round, before the registration and before any arc reading)

**Written after the seat round on PR 2's instrument, and before anything was pushed.**
AI Quality, Platform Engineering and Security each ran in an isolated worktree at the
instrument's first head and planted defects. Their output was advisory (G6). Every change
below is an operator ruling on it.

### 1. One validity row: each run's caption bytes are the committed fixture's

**The finding (Security seat, blocking).** The writer hashes the caption file on disk and
reads `tree_clean` from `git status --porcelain`. `git update-index --skip-worktree`
defeats both: a run can check gap bytes while the commit holds the fix, and still record a
clean tree. The seat's plant printed `git status --porcelain: ''`, then
`decision=NO-GO tree_clean=True caption_sha256==sha256(HEAD blob)? False`.

Decision 2 names *"the writer hashes and checks different files"* as F1's false state, and
no validity check could detect it. So SPEC/11's validity table gains, for all three runs:
`caption_sha256` equals `git show <commit>:drill/fixtures/jefferson-derby/captions.vtt |
sha256sum`. Both readers exist today.

**Why it is admissible now.** The table was amended before the registration that freezes it.
No arc run exists.

### 2. Not taken, by ruling, and carried

- **A failed F3 liveness check has no registered meaning** (AI Quality seat). SPEC/11 says
  only that `verify` *must* exit 0 on the seeded artifact first.
- **The clean fixture's bytes are pinned by no reader** (AI Quality seat). The fixed run's
  check diffs against PR 3's branch point, not against PR 2's bytes, and `drill/fixtures/`
  is on one key.

### 3. The first registration is superseded, not rewritten

Two commits made the first registration: the reader transcript `readers.txt` came first
and was taken at the readers' first commit, then `falsifiers.json`. The seat round changed
the writer and both readers after that. So:
- **`readers.txt` is re-taken** at a head carrying the fixed code and this amendment.
- **`falsifiers.json` is revised in a later commit.** It adds item 1's row and holds every
  falsifier and validity row verbatim to SPEC/11 (AI Quality seat, blocking: the pins test
  held only part of the file).

Both first commits stay in history. SPEC/11's *"a pinned value, a falsifier or a reader
changed after PR 2 commits `falsifiers.json`"* is read as applying to the registration
this PR carries at its head. Neither registration had a reading taken against it.

### 4. Decision 5, amended: PR 2's audit runs through CI on PR 2's own branch

Decision 5 said the deletability audit runs through a local `pave check`, not an exhibit.
The operator's brief ruled local Windows runs out, and debt 29 is the reason. The ruling:
- each plant commit is force-pushed onto PR 2's own branch after the gated head is tagged
  and the PR opened;
- each registers a CI run;
- the head is restored, and the audit record is committed and re-gated before the body.

No exhibit is opened, and the cap is unchanged.

### 5. Security is the third key on the drill rule

The rule's comment gave the reason for two keys: the signature's rules are code already on
the rule. The Security seat named that circular. The two seats could weaken
`signature_holds` together, and F3's whole meaning is the signature. Security feels no pain
from a GO, which is G9's direction. The operator ruled it in, and `M11_PR2_SEATS` pins
three seats.

### 6. Fixed in PR 2 from the seat round

**Platform Engineering seat:**
- **Finding 1, blocking.** A failed write left a 0-byte artifact and poisoned its path.
  Fix: the writer publishes through a temporary file and a hard link.
- **Finding 5.** A written GO could exit 1 on a console that cannot print. Fix: the exit
  code is fixed before printing.
- **Finding 6.** An interrupt escaped the exit contract. Fix: exit 2 before publishing.
- **P6 and P7.** Two narrowings of the rule survived. Fix: both are pinned.
- **P9.** The readers could reach the writer through `sys.modules`. Fix: it is banned, and
  a subprocess verifies with the writer made unimportable.

**Security seat:**
- **Finding 2.** A duplicate key passed `verify`. Fix: refused by both readers.
- **Finding 3.** A lone surrogate, deep nesting or a BOM crashed or misread. Fix: all exit
  2, and a signature check that raises never prints OK.
- **Finding 5.** The prior was unvalidated, and `tier: true` compared equal to tier 1. Fix:
  the prior is schema-validated and the tier's type is checked.
- **P8, P10, P15 and P16.** Each survived. Fix: each is held by a test.

**AI Quality seat:**
- **Finding 1, blocking.** No window over a day was tested, and a days-dropping reader
  survived. Fix: held by a test.
- **Finding 3.** Schema limits under `findings` could turn FALSE into INVALID. Fix: those
  keywords are forbidden, and a two-gap test is added.
- **Finding 4.** The threshold was compared only to the millisecond. Fix: it is compared
  exactly.
- **Findings 6 and 8.** Two docstrings claimed more than was true. Fix: corrected.

### 7. Carried out of PR 2, none repaired here

| # | debt | owner | trigger |
|---|---|---|---|
| 1 | `pave/cli.py`'s drill dispatch is on no two-key rule, so a one-key edit can route `verify` elsewhere; a `.pyc` under `pave/__pycache__/` is on none either (Platform Engineering seat, finding 2) | Platform Engineering | the next PR that edits `pave/cli.py`'s drill dispatch |
| 2 | `tests/test_drill*.py` witness the signature and the pins and are on no rule (M10 row 28's shape) | Platform Engineering + Security | the next PR that edits `pave/twokey.py` |
| 3 | `README.md:961` and `Makefile:66` run `pave drill` without `--out`, which now exits 2 | Platform Engineering | the next PR that edits either file |
| 4 | a failed F3 liveness check has no registered meaning (item 2) | AI Quality | PR 3, before its seeded run: say it, or record that it is unsaid. **Resolved by amendment 4, item 2:** a failed liveness check is an INVALID seeded run |
| 5 | the clean fixture's bytes are pinned by no reader, and `drill/fixtures/` is on one key (item 2) | AI Quality | PR 3's seed commit. **Not repaired; carried by amendment 4, item 5, as cold review D20**, re-triggered after the fixed run, because paying it in the seed commit would make the seeded run INVALID |
| 6 | **For PR 3:** commit the full sha256 of the run key in the seed commit, before the seeded run (Security seat, finding 7); and a CRLF re-save of the fixture during the fix step makes `tree_clean` false, so the run is INVALID with no retry (Platform Engineering seat) | Security + Platform Engineering | PR 3. **The key half is resolved by amendment 4, item 3:** the sha256 is committed before PR 3 branches, not in the seed commit, which would have made the seeded run INVALID. **The CRLF half is carried as cold review D21** |
| 7 | the ordering test reads git history, so a squash merge of PR 2 turns it red | Platform Engineering | PR 2's merge: by merge commit or rebase, never squash |

## Amendment 2 (2026-09-13, M11 PR 2, after the audit, before the merge and before any arc reading)

**Written after the audit stopped and before PR 2 merged.** No arc run exists. The record
is `milestones/M11/pr2-deletability-audit.md`. Every ruling below is the operator's.

### 1. Amendment 1 item 4's audit cannot tell a caught code plant from a silent one

Item 4 put each plant commit on PR 2's own branch for a CI run. For a plant to the writer
or the readers, a commit is itself a second door. Every such commit trips
`tests/test_drill_pins.py::test_the_readers_were_shown_emitting_before_the_claim_was_committed`,
because `readers.txt` then no longer descends from the last change to that code. That test
failed in all 39 plant runs, the four that caught nothing included. **A red CI run is
therefore not the reading.**

The record reads each plant by the failing tests **other than** that one: CAUGHT if any
failed, SILENT if none did. The control run on the unmutated head is 34778857665: 5133
passed, 9 skipped, `check: PASS`.

### 2. The audit is recorded at 39 of 96 and stopped, not resumed

- **Run:** the 39 plants pushed before the operator stopped the push: W01–W36, I3, R01
  and R02.
- **CAUGHT:** 35.
- **SILENT:** 4, W01, W03, W08 and W23. Each refusal is shadowed by a second door, and its
  test cannot tell which door refused (ADR-040's shape). They are debts D8–D11 in the
  record, owned by AI Quality + Platform Engineering, triggered by the next PR that edits
  `pave/drill.py`, and not repaired in PR 2.
- **Unrun:** 57, listed by id in the record.

The branch was force-restored to the audited head. The 39 red runs stay in PR 2's check
history.

### 3. Claim 9 is partially measured, and is stated as such

SPEC/11's row 9 reads *conformance, and the non-fixing edit refused*, measured by *PR 2's
tests, each check deleted and run through `pave check`*.
- **Measured for** the 39 doors above:
  - W14: validation before writing, CAUGHT;
  - W19: the non-fixing edit, CAUGHT.
- **Not measured for** the schema, the scenario, the registration, the two-key rule, the
  dispatch, the verifier, and eight later writer doors.

Row 9 is partially measured. It is neither met nor failed.

### 4. The spare, PR 2b, is taken

- **Its checklist:** R03–R10, S01–S06, K01–K06 and F01–F08.
- **How it is worked:** by reading, per decision 5. It runs nothing, moves no pinned value,
  and adds or drops no falsifier. Its repairs land in the spare.
- **Not on the checklist, and staying unrun:** I1, I2, C01, C02, P01–P04, T01, T02,
  V01–V11, W40, W41 and W43–W48.
- **The cap:** all four slots are now planned: PR 1, PR 2, PR 2b and PR 3.

### 5. Nothing registered moves

No pinned value, falsifier or reader moves. This amendment edits none of these:
- SPEC/11;
- `falsifiers.json` or `readers.txt`;
- the schema, the writer or the readers;
- the scenario or the fixture.

M10's debt row 28 fired because PR 2 edits `pave/twokey.py`, and PR 2 does not pay it.

## Amendment 3 (2026-09-13, M11 PR 2b, before any arc reading)

The 39 plant runs' CI logs are committed under `milestones/M11/pr2-audit-logs/`, one file per
run id with an index, because GitHub run logs expire and the audit record cites them as its only
durable evidence, and because V01–V11 joined the spare's checklist beside R03–R10, S01–S06,
K01–K06 and F01–F08, which item 4 of amendment 2 had left unrun.

## Amendment 4 (2026-09-13, M11 PR 2b, after the cold review, before PR 3 branches)

**Written after the cold review** (`milestones/M11/pr2b-cold-review.md`) and before any arc
reading. No arc run exists. Every ruling below is the operator's.

### 1. What the cold review found

The reviewer wrote none of PR 2 and read `main` at `6a5fbb7`. It ran nothing.
- **Every reader reads the field its row names.**
- **Of the 39 checklist plants, 37 fire by reading.** R09 and S03 have no witness.
- **Nothing makes a term true by construction** through a schema claim value, a writer
  default or a reader import.

It graded four findings BLOCKING:
- **B1.** Amendment 1's debts 4–6 are triggered between B and S. Paying any of them there
  makes the seeded run INVALID.
- **B2.** F3 passes on any refusal. `verify` under a key other than the writer's refuses all
  three copies, and a failed liveness check had no registered meaning.
- **B3.** F2 on the control run, F4, F5, and the control and fixed validity rows read
  artifacts no registered check verified.
- **B4.** `tree_clean` is `git status --porcelain`, and skip-worktree still hides the writer
  and the scenario.

### 2. Three registration additions (B2, B3)

SPEC/11's validity table gains three clauses, and `falsifiers.json` carries them verbatim:
- **seeded:** `drill verify` on R1 exits 0 printing `signature: OK`, and `signature.key_id`
  equals the first 16 hex of `milestones/M11/pre-registration/key.sha256`;
- **control:** `drill verify` exits 0;
- **fixed:** `drill verify` exits 0.

**A failed F3 liveness check is now an INVALID seeded run**, so no copy is read.

**No registered reader prints `signature.key_id`.** It is read with `grep '"key_id"'` on R1
and `head -c 16` on `key.sha256`, both of which exist today. Once `verify` has exited 0, the
artifact holds no duplicate key, so exactly one `key_id` line exists.

No pinned value moves, and no falsifier is added or dropped. F3's `liveness.on_failure` in
`falsifiers.json` now points here instead of reading "not registered".

### 3. The run key's hash is committed before PR 3 branches (B1)

**The key** is the operator's PR 3 run key, generated in this PR: 32 random bytes written as 64
lowercase hex with one LF, held outside the repository.

**`milestones/M11/pre-registration/key.sha256`** holds two values:
- the sha256 of exactly the 64 bytes `pave/drill.py` receives from `BEACONPAVE_DRILL_KEY` after
  `$(cat …)` strips the newline, computed through `pave.drill.load_key`;
- the derived `key_id` beside it.

Nothing else about the key is committed. The hash lands on `main`, outside every run's diff
window.

### 4. B4 is debt, with a procedural remedy

Review **D19**: skip-worktree can hide edits to the writer and the scenario.
- **The remedy:** PR 3's arc runs in a fresh clone of its branch, and the PR 3 body says so.
  SPEC/11's plan for PR 3 carries that line.
- **Not added:** a validity row for it.

### 5. Amendment 1's debts 4–6

- **Debt 4 is resolved** by item 2.
- **Debt 6's first half is resolved** by item 3. That half is the key's sha256.
- **Debt 5 is not repaired.** The clean fixture's bytes are still pinned by no reader. It is
  carried as review **D20**.
- **Debt 6's second half is not repaired.** A CRLF re-save of the fixture during the fix step
  still makes the run INVALID. It is carried as review **D21**.
- **Neither carried debt can land inside a run's diff window.** D20 and D21 are triggered
  where paying them commits nothing inside a window.

The review's other debts are **D12–D18**, numbered on from the audit's D8–D11.

### 6. No reader changed, so the reader transcript stands

- **No file under `pave/`, `quality/`, `drill/` or `tests/` is edited.**
- **`readers.txt` is not re-taken.** Its last change still descends from the last change to
  every file it exercises, and the last change to `falsifiers.json` descends from it.
- **`drill verify` is shown emitting** on a NO-GO and on a GO in `readers.txt`, sections 2
  and 8.

### 7. Decision 5, amended: the cap is five PRs

**PR 2b (#160) merged before the operator's rulings on its review,** so the repair could not
land in it. The other two routes fail:
- **Folding the repair into PR 3** puts commits between B and S, which makes the seeded run
  INVALID (B1).
- **Opening it under the four-PR cap** makes it the fourth PR, and SPEC/11's *Bounded*
  requires the fourth PR to close M11 without the arc.

**The operator ruled the cap to five:**
1. PR 1;
2. PR 2;
3. PR 2b;
4. the PR 2b repair, which carries this amendment;
5. PR 3, which closes the milestone, red if necessary.

**M11 now spends five slots.** Every PR opened against `main` still counts, including an
exhibit. No further slot is named.

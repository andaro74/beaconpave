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

# ADR-042: append-only never constrained what a NEW row may claim, and the directory that anchors two gates takes one key

**Status:** Proposed. Written before the code. **Zero model calls.**
**Seats:** AI Quality (`evals/history/`, the recorded numbers) · Security / Red
Team (the adversarial entries, what a probe passing means, the corpus registry) ·
Platform Engineering (the recorders, the lane that reads an entry, the workflows)
· Service Team (the honest path: recording a row and closing a milestone)

Discharges ADR-041 decision 3.

**This is the third draft.** Draft 2 was reviewed by four seats, each planting
and measuring in a worktree, and all four answered *"does any reachable input let
a recorded number change, or a fabricated one land, with everything green under
draft 2's controls?"* with **YES**. Three of draft 2's load-bearing mechanisms
do not exist as described:

- **Decision 3's git check could not satisfy its own predictions 3 and 4 at
  once.** Three seats built the same two branches — an honest record-then-fix
  PR and a one-commit rewrite of a committed entry — and measured the commit
  count at 2 and 1 respectively. The honest PR fires; the rewrite does not. The
  check was also red on `main` as it stood (`m00b-judged-B-goldens.json` has two
  commits, `schema.json` thirteen) and the only thing that would have silenced
  it was the `GRANDFATHERED` constant draft 2 withdrew.
- **Every key draft 2 added was collectable around.** `two-key.yml` computes
  its changed-file list with git's rename detection on, so `git mv` of any
  two-key file to a path outside its pattern, with under ~50% edit, triggers no
  rule: *"two-key: not required — this PR touches no two-key path, exit 0"*.
  Measured on the adversarial recorder and on a history entry moved one
  directory up.
- **The floor draft 2 said it corrected was still the PR's own number.** An arm
  recorded asking three of eleven probes, entry `total: 3`, pinned at 3/3:
  `asked_floor(m05, corpus=11, recorded_total=3) = 3`, lane PASS, gate exit 0.
  The read that feeds it is dead on every committed arm, sits in a file on no
  rule by design, and no test reaches it — replacing it with the literal `1`
  left 1701 tests green.

What was wrong is recorded below rather than quietly replaced. Draft 2 is in
the branch history at `d86b08e`.

## The threat, corrected twice

Draft 1 assumed the attack is **editing a committed row**. Draft 2 measured that
the cheaper attack is **appending a new one**, and that remains true:

```
appended evals/history/m01-goldens-corrected.json
  real   m01 scores: passed 19 of 25
  new    row claims: passed 24 of 25    same `sha`, schema-valid
  -> 1701 passed, pave check exit 0
```

The row did not even have to be internally consistent — `passed: 24` beside
`pass_rate: 0.76` validated, because nothing ties an entry's `scores` to its
`cases`.

Draft 2 then described T1 as "a fabricated row is appended" and answered it with
a pin and three attestations. That is the right residual for the **number** a
row claims — a pinned row is still the PR's claim, and this ADR does not pretend
otherwise. But T1 has a second shape the pin cannot see and a deterministic
bound can: **the denominator.** For an adversarial arm the entry's
`scores.total` is read into `asked_floor` and becomes the fewest probes that arm
must have been asked. A fabricated row that claims 3 of 3 is as well-formed as
one that claims 11 of 11, and the floor it sets for itself is 3.

So three threats, and this ADR must name all three:

- **T1a — a fabricated row is appended, claiming a number.** Residual: attested.
- **T1b — a fabricated row is appended, claiming a denominator.** Bounded here.
- **T2 — a committed row is edited, renamed, or deleted.** Caught here.

## What exists, measured

Everything draft 2 measured still holds (three of eight entries pinned; the
recorders refuse only a duplicate *filename*; `evals/history/` takes one key;
`evals/run_evals.py` takes none while its twin takes two; `pave/cli.py:900`
reads an entry's `scores.total` into a gate failure condition while
`pave/floors.py:88` asserts that value "is not a value the same PR can invent").
The seats' plants added these:

- **`two-key.yml:49` runs `git diff --name-only` with rename detection.** A
  renamed two-key file is reported under its new path only. That line is the
  only place a changed-file list is computed — `pave gate two-key` takes
  `--changed` and never diffs — so the defect has one home.
- **The floor read is unreachable on an honest tree.** All three committed arms
  are enumerated in `ASKED_FLOOR`, so the `recorded_total` branch runs for no
  arm that exists, and no violating-tree test exercises it.
- **`m04-adversarial.json`'s evidence link is already broken.** Its
  `samples_from.sha256` is `8bac7894…`; the committed
  `milestones/M04/probes-run.json` digests to `00605955…`. PR #51 (ADR-041)
  rewrote the observation file to add the `_asked` manifest, under two keys, and
  nothing read the entry's digest of it. The only field tying a row to its
  evidence is checked on a `tmp_path` fixture and never on the committed tree.
  `evals/run_adversarial.py:309` says `close-milestone` checks it; the skill
  does not mention `samples_from`.
- **A second row under one `sha` is unconstrained.** `arm` is free text,
  `instrument` is optional, the schema has no `additionalProperties: false`, and
  `supersedes` is a SHA — which identifies one to N entries. `515ee70` already
  has three rows, two of them `suite: goldens`. "Resolve `supersedes` to a
  committed entry" is undefined for exactly the rows that exist.
- **The directory has two enumerators.** `tests/test_k_sample_summary.py:203`
  globs `*-*.json`; `tests/test_adversarial_entry.py:393` globs `*.json` minus
  `schema.json`. Neither sees a subdirectory or a `.json.new`.
- **The recorder writes CRLF on Windows and prints no digest.** `write_text`
  translates `\n`; an operator pinning `sha256sum` output pins `b11df9e6…` where
  the normalised pin is `707a9901…`, and their own honest entry fails as
  "rewritten". `_entry_digest`'s docstring already records this hazard once.
- **`.claude/skills/close-milestone` step 2 does not run as written.**
  `python evals/run_evals.py --record` → `ModuleNotFoundError: No module named
  'evals'`. The Makefile uses `python -m evals.run_evals`, and `--answers` is
  required.
- **`docs/governance/ROLES.md`'s two-key table has no `evals/history/` row**,
  before or after any change here. The row it has — "Baseline reset | Service
  team + AI Quality" — names a seat pair the enforced list has never had.
- **A fabricated goldens row can be recorded through the real recorder.**
  `--history-dir` writes past the append-only refusal into any directory, and
  `--allow-dirty` is a flag. Nothing in an entry distinguishes a
  recorder-produced row from a hand-written one. "A real recorder invocation"
  is not a bar and this ADR stops treating it as one.

## Decisions

### 1. The whole of `evals/history/` takes three keys, and so do both recorders

AI Quality, Security, Platform Engineering — draft 2's set, for draft 2's
reasons, which the review did not disturb: the fabricated `m04` 10/10 row needed
every seat but the one that owns what a probe passing means, and Platform
Engineering owns the lane that reads an entry into a gate decision and the
recorders that write one, which is an interest in dispositioning a bad entry
quietly rather than a counterweight.

**The whole directory, `schema.json` and the new `pins.json` included, one
prefix, no exclusion pattern.** Draft 1's hyphenated glob dropped seven of ten
path shapes to no rule; draft 2 fixed the glob and a seat then measured that no
test pins any rule's seat set, so the fix was deletable on two keys. Decision 8
adds the test.

**Both recorders take the same three.** Draft 2 gave `run_adversarial.py` two
and `run_evals.py` an unspecified set. The recorders enforce the schema, which
takes three; a recorder that can write a row the schema would refuse is a
schema change made in code, and relaxing it on fewer keys than the schema is the
pairwise inversion decision 8 audits for. ADR-030's argument — over-broad in the
direction of more review is the fail-closed direction — and it makes the
pairwise table trivially clean: everything this ADR touches that can move a
recorded number takes the same three seats.

**The rule's `what` string changes.** Today it reads *"recorded baselines — a
reset is a decision, never a cleanup"*. That is the message a developer reads
when their honest close PR is blocked, and it tells them they reset a baseline.
It becomes *"recorded history — a new row is a claim three seats attest; a reset
is a decision, never a cleanup"*. `ROLES.md` gains the row it never had and
loses the seat pair it never enforced.

**What "three keys" means here, said plainly.** On a one-operator repo it is
three `Two-Key-Disposition:` lines and one `Two-Key-Rationale:` from the same
author — `parse` pools every rationale into one string. That is ADR-013's
concession and not a new weakness, but draft 2's "attested by three seats"
read as three humans. It is three advisory subagent runs and three written
dispositions, which is what this repo can collect.

### 2. Every entry is pinned, the pin set is COMPLETE, and the recorder writes the pin

**The pin lives in `evals/history/pins.json`**, a flat `{filename: sha256}` over
normalised content, maintained by both recorders at `--record` time. Draft 2 did
not say where the complete pin lived; the obvious home,
`tests/test_arm_scoping.py`'s `HISTORY_DIGESTS`, asserts at line 151 that it
equals the adversarial arm set *exactly*, so a complete pin there is red by
construction — three seats hit it. A test-file constant also puts a hex string
on the honest path that the operator must hash by hand, which on Windows
produces the wrong digest (above). The recorder computes the normalised digest
and writes it; the honest path stays one command.

**The test — in the file decision 8 names — asserts four things, and the
completeness half is what does the work:**

1. `set(pins.json) == set(entries on disk)`, exact, never a subset. Every value
   matches `^[0-9a-f]{64}$` — **no `if v` filter**: a seat planted an empty
   string as a pin and rewrote the entry behind it, green.
2. Every pinned digest matches its entry's normalised content.
3. `HISTORY_DIGESTS ⊆ pins.json` and agrees on every shared key. The adversarial
   anchor keeps its own copy in the three-key test file, so moving an arm's
   digest still takes a test diff as well as a data diff — the same deliberate
   duplication `PIN_FLOOR` uses.
4. **`scores` is derivable from `cases`** for every committed goldens entry:
   `passed == count(PASS)`, `failed == count(FAIL)`, `total == len(cases)`, and
   the case-id set equals the golden file's. Green on all five today; it raises
   a fabricated row from "copy a file" to "forge a consistent case list", and it
   is the cheapest deterministic assertion this ADR can add.

**One enumerator.** "An entry on disk" is a regular file matching `*.json`
directly under `evals/history/`, excluding `schema.json` and `pins.json`, and
the directory must contain nothing else — no subdirectory, no other suffix. The
two existing enumerators are replaced by a call to the one function. A seat
planted `evals/history/corrections/m01-goldens.json` and
`m01-goldens.json.new`; neither is gate-reachable, but a reader browsing the
directory sees a row, and the point of the directory is that a reader can.

**The README's goldens numbers are tied too.**
`test_the_published_progression_still_matches_the_recorded_entries` covers the
adversarial `ARMS` only; `sed` on the M01 row's 19/25 → 24/25 left 93 tests and
the gate green and `twokey.triggered(["README.md"]) == []`. The test extends to
every goldens row with a tag. Deterministic, green today.

**What this buys and what it does not.** Pinning a row does not make it true.
What it buys is that adding one is visible, exact-set, self-consistent, and
attested — and, from decisions 5 and 6, anchored to committed evidence and
bounded in its denominator. The residual for the *number* is the attestation,
and that is the honest claim.

### 3. The append-only check is a DIFF against the merge-base, not a commit count

Withdrawn: every sentence of draft 2's decision 3 that mentions a count. What
replaces it:

```
git diff --name-status --no-renames --diff-filter=MDR  BASE...HEAD  -- evals/history/
```

**must be empty**, with exactly two exceptions: `M` on `schema.json` and `M` on
`pins.json` (both are modified by honest work and both are three-key). Any other
`M`, any `D`, any `R` — a committed entry modified, deleted, or renamed — is a
block with a named message.

Why this and not a count, measured by three seats on synthesized
`refs/pull/N/merge` refs:

| shape | count | base-diff |
|---|---|---|
| honest: record, then fix `recorded_at` in a second commit | 2 — **fires** | empty — passes |
| malign: new row, then change `passed` in a second commit | 2 — fires | empty — passes (**the pin's job, not this check's**) |
| rewrite a committed entry and re-pin, one commit | 1 — **misses** | `M` — fires |
| same, squash-merged | 1 — misses | `M` — fires |
| evil merge rewriting a committed entry | 2 — fires | `M` — fires |
| rename plus rewrite plus re-pin | 1 — misses; completeness satisfied | `D` + `A` — fires on the `D` |
| `m00b-judged-B-goldens.json` on `main` today | 2 — **red on an honest tree** | not touched — passes |

The discriminator is whether the path **existed at the merge-base**. An entry
new in the PR is the PR's claim and may be fixed inside the PR freely — which is
the reading `f7fb24e` used to defend itself and draft 2 conceded was documented
at the time. An entry that existed at the base is merged history, and the rule
protects merged history. No grandfather list, because nothing on `main` is
touched by a PR that touches nothing on `main`.

**`--no-renames` is load-bearing**, here and in decision 4. With rename
detection on, `git mv m01-goldens.json m01-goldens-reread.json` plus a rewrite
under 50% reports `R097` and a filter on `D` sees nothing. A seat measured that
`--follow` and default detection fail *hardest on the largest rewrites* —
**the bigger the lie, the more append-only it looks** — and that is why draft
2's "completeness catches rename-plus-rewrite" was false in composition: it
catches it only if the attacker forgets to re-pin, which is the remedy this
check exists to defeat.

**Three dots, and the base is resolved in a stated order.** Two-dot diffs
against the branch tip: a seat advanced `main` with a new `m05-goldens.json`
and ran the check from an older honest branch — `R097 m05-goldens.json ->
zz-honest-goldens.json`, an honest PR accused of renaming someone else's entry.
Three-dot diffs against the merge-base and reported nothing. The base is
`origin/$GITHUB_BASE_REF` in CI, else `$PAVE_BASE` if set, else `origin/main`,
else `main`; if none resolves the check **refuses with a named message**, as it
does on a shallow clone (`git rev-parse --is-shallow-repository`), on a tree
with no `.git`, and with `git` absent from PATH. It never passes quietly and
never raises a bare traceback — in `pave check` a refusal is a failed test,
which is the fail-closed direction.

**What this costs and where it bites.** `quality-gate.yml` gains
`fetch-depth: 0`; measured by two seats at +140–260 ms and +534–550 KiB. A
contributor who runs `git clone --depth 1 && make check` is now red with a
message naming `git fetch --unshallow`. That is a first-run red, stated here
rather than discovered, and it is the correct posture: a check that passes
because it could not see the base is `rules_validate`'s hazard.

**The limit, stated as one thing.** This check is blind to what a new row
claims. That is the whole of it — decision 2 pins the number, decision 5 anchors
it to evidence, decision 6 bounds the denominator, decision 1 attests it. Draft
2's list of blindnesses (T1, rename-plus-rewrite, evil merge, squashed intra-PR
rewrite) is withdrawn: two of the four were artefacts of counting, one was
wrong in the under-claiming direction (an evil merge was seen), and the fourth
is not this check's concern because a new row is not merged history.

### 4. `two-key.yml` reads the diff with `--no-renames`, and a test pins the flag

The cheapest bypass in the repository as it stands, found by Security:

```
git mv evals/run_adversarial.py evals/record_adversarial.py
  delete the append-only refusal; commit
.github/workflows/two-key.yml, as written:
  changed: evals/record_adversarial.py
  two-key: not required — this PR touches no two-key path     exit 0
```

Same result moving `m04-adversarial.json` one directory up and editing it. With
`--no-renames` both the old and the new path appear, the old path matches the
rule, and the key is collected. One flag in the workflow, and a test that
reads the workflow's diff line and asserts the flag is on it — the workflow is
two-key and the test file is three-key, so removing the flag is red in a file
that takes more keys than the workflow.

This is in this ADR rather than its own because every key decisions 1 and 8 add
is collected by this workflow, and a key the workflow cannot collect is the
"stated and absent" protection CLAUDE.md calls worse than a missing one.

### 5. A new row must be anchored to committed evidence

The eight entries that exist are a closed set — pinned by digest, enumerated by
decision 2's test — and are grandfathered **by name**, with the reason stated
per entry: four predate `samples_from` (M00b and M01), and `m00b-goldens.json`
and `m01-goldens.json` were recorded by a recorder that did not yet write it.
**Every entry beyond those eight must carry `samples_from`**, and for every
entry that carries it, the committed tree must agree:

```
normalised sha256(evidence file at samples_from.path) == samples_from.sha256
```

That is checked on the committed tree, which nothing does today. It converts
"a real recorder invocation" — not a bar, as a seat showed with `--history-dir`
— into "points at a committed, hashed evidence file", which is a bar: a
fabricated row must now also fabricate or point at evidence that is itself
under two keys and an ADR (`milestones/*/probes-run.json`) or committed answers.

**`m04-adversarial.json` fails this today, and this ADR says so rather than
hiding it.** PR #51 rewrote `milestones/M04/probes-run.json` to add `_asked`
(ADR-041 decision 1) and the entry's digest of it was read by nothing. The
entry cannot be edited; the evidence cannot be un-revised; neither was wrong.
So the test carries an explicit, three-key **evidence revision record**:

```
EVIDENCE_REVISIONS = {
  "m04-adversarial.json": [
    ("8bac7894…", "00605955…", "PR #51 / ADR-041 added the `_asked` manifest; samples unchanged"),
  ],
}
```

An entry's `samples_from.sha256` must equal the committed digest **or** the
first digest of a recorded revision chain whose last digest is the committed
one. The chain is a list so that the next revision is appended rather than
overwritten — the same shape as the history it describes. This is not a
`GRANDFATHERED` constant: it records a specific change with its PR and its
reason, and it has exactly one row. A second row needs the same three keys and
the same kind of sentence.

For adversarial rows `instrument.name` must additionally resolve in
`quality/adversarial/instruments.json`; `test_every_committed_entry_names_a_registered_instrument`
already does this and **skips rows with no instrument**, which is the shape a
fabricated row would take. New adversarial rows may not omit it. New goldens
rows are not given an instrument requirement here — a deterministic goldens
entry's instrument *is* the absence of one by the schema's own description —
and `samples_from` is the anchor that applies to both suites.

### 6. The adversarial denominator is a registered constant, not the PR's number

`quality/adversarial/instruments.json` gains one field per instrument,
`corpus_size`, derived from the committed corpus at that instrument's
`probes_sha256` and asserted against it by a test. That file is Security's, with
an ADR — this one.

Then, for an arm not in `ASKED_FLOOR`:

- the floor is `corpus_size` of the instrument the arm's entry names, **not**
  `min(entry.total, corpus)`;
- the entry's `scores.total` **must equal** that `corpus_size`, or the lane
  fails with a message naming both numbers;
- the read moves out of `pave/cli.py` into `pave/floors.py` — three keys, where
  the floors already are, and where `floors.py`'s own docstring says criteria
  belong — and a **violating-tree test** records an unenumerated arm asking
  three of eleven and asserts the lane FAILS. Replacing the read with a literal
  left 1701 green; that is what "reachable on no honest tree" means and it is
  the shape decision 8's rule on protection tests exists for.

This keeps ADR-041's reason for reading the entry — an arm recorded before the
corpus grew must not fall beneath a floor of twelve forever — because the
instrument name the entry declares is exactly the corpus snapshot it ran under,
and that is why `probes_sha256` is in the registry. What changes is *who writes
the number*: the registry, on Security's key, rather than the PR.

**`floors.py:88` is corrected in code, not in prose.** The sentence "not a
value the same PR can invent" becomes true again by construction, and the
docstring says how: the floor is read from a registry keyed by a name the entry
declares, and the entry's total must match the registry.

### 7. A second row under one `sha` must say why, and `supersedes` becomes writable — by filename

Two entries sharing `sha` and `suite` must differ in `arm`, differ in
`instrument` (**absent versus present counts** — the `m00b` deterministic and
judged pair differ in exactly that, and a seat measured that draft 2's wording
would have turned `main` red on the repo's own canonical anchor), or carry
`supersedes`. A row that shares both and declares nothing is refused.

**`supersedes` names an entry filename, not a SHA.** The schema says SHA; a SHA
identifies one to N entries and already identifies three. The append-only
guard keys on the filename (ADR-027 rule 3), so the filename is the entry's
identity and the only thing a correction can resolve to. The named file must
exist on disk, must not be the row itself, and must share `sha` and `suite`.
That is a `schema.json` change, on three keys.

**Both recorders get `--supersedes <filename>`** and write the field; the
superseded entry's `sha` is copied rather than re-derived, which is the one case
where `--sha` without `--judged` is correct and the recorder's refusal is
lifted. The filename gains a component that says what differs — ADR-027 rule 3
— `{stem}-correction{N}-{suite}.json`, where N counts corrections of that stem.
The recorder's current refusal message, which teaches a verb no tool can write
(*"a correction is a new entry with `supersedes`"*), becomes true the day this
lands, and `run_evals.record`'s "no `supersedes`, ever" comment — written about
the judged anchor, which is an `instrument` difference and still not a
correction — is narrowed to say that.

**Honest claim: this is legibility, not truth.** `arm` is free text, so a
fabricated row declares `arm: rerun` and satisfies this decision; a seat
measured it in one line. Draft 2 called this "T1's floor" and it is not. It is
the rule that lets a reader tell *why* a second row exists — the truth
constraints are decisions 2, 5 and 6. Bounding `arm` to an enumerated set was
considered and declined: the set would live in a file the same PR edits, which
is the self-satisfying shape ADR-041 removed from `asked_floor`.

**Draft 2's fourth verb is withdrawn.** Its motivating case — the M03 rewrite —
left `scores` and `cases` byte-identical, which is not a second reading of
anything; it is the same measurement re-serialised, and a second row with
identical numbers under one `sha` is the ambiguity ADR-027 exists to prevent.
Draft 2 also reclassified that rewrite as legitimate intra-PR amendment three
paragraphs later. And the wall it was a door in is not a wall: a seat added a
required field to `schema.json` and got ten failures that no appended row could
clear, because `test_the_committed_entries_still_validate` validates every
committed entry against the current schema. That test is correct and it is the
rule:

**`schema.json` may never gain an unconditionally required field.** Top-level
`required` is pinned to today's five by a ratchet test; a new requirement lives
under an `if/then` keyed on a field a row declares, so it binds rows that
declare it and never rows that predate it. That is how `instrument`'s
suite-conditional shape already works (M04), and it is why eight of eight
entries validate today.

### 8. Every protection this ADR adds goes on a path with at least the keys of what it protects — named, and tested

Draft 2's prediction 7 failed for the third time because decision 6 named no
paths: `tests/test_history_pins.py`, `pave/history_check.py` and every other
plausible name for the new module resolved to `[]`. So, the list:

| file | role | keys after this ADR | why |
|---|---|---|---|
| `evals/history/*` incl. `schema.json`, `pins.json` | the rows, the contract, the pins | aiq · sec · plat | decision 1 |
| `evals/run_evals.py`, `evals/run_adversarial.py` | write rows and pins | aiq · sec · plat | decision 1 |
| `tests/test_history_append_only.py` (**new**) | decisions 2, 3, 5, 7's ratchet, 8's seat-set test | aiq · sec · plat | added to the protection-test regex, which already carries these three |
| `tests/test_arm_scoping.py` | `HISTORY_DIGESTS`, `ARMS`, `EVIDENCE_REVISIONS` | aiq · sec · plat | already |
| `pave/floors.py` | the denominator floor and its read | plat · aiq · sec | already |
| `quality/adversarial/instruments.json` | `corpus_size` | sec + ADR | already |
| `pave/twokey.py`, `.github/workflows/two-key.yml` | the rules and the collector | aiq · plat | already — and a protection on the *mechanism* rather than on a number; decision 4's `--no-renames` lands here |
| `.github/workflows/quality-gate.yml` | `fetch-depth: 0` | aiq · plat | already |
| `pave/cli.py` | loses the read | none, by design | `test_ordinary_pr_is_not_gated` names it as the canonical ungated file; it gains nothing that decides a number |
| `docs/governance/ROLES.md`, `.github/CODEOWNERS` | prose and the decorative owner | none | CODEOWNERS is one-directional into `twokey.py` (`test_contracts.py:595`); ROLES.md is a summary CLAUDE.md already says not to rely on |
| `.claude/skills/close-milestone/SKILL.md` | the checklist | none — **exempt, stated** | a checklist on no rule is acceptable; a seat asked that prediction 8 say so rather than claim "every file" |

Pairwise: no row's keys are a strict subset of the keys of a row it protects.
`pave/twokey.py` at two keys protecting three-key paths is the one apparent
inversion, and it is the standing one ADR-037 already examined — the first move
against G9 cannot be to delete G9's collector on one key, and a test in the
three-key file now asserts the seat sets, so weakening a rule is red in a file
that takes the rule's own keys.

**The seat-set test.** A seat stripped `security` from all three three-seat
rules — a two-key change — and got one failure, in a zero-key file. The new
test asserts, for every path shape under `evals/history/` (eight today plus
`schema.json`, `pins.json`, a subdirectory, a hyphenless name) and for both
recorders, that `seats ⊇ {ai-quality, security, platform-eng}`; and for
`pave/floors.py`, `tests/test_arm_scoping.py` and `evals/comparators.json`
likewise. It lives in `tests/test_history_append_only.py`, on the regex.

### 9. `close-milestone` step 2 is rewritten, because it does not run and this ADR adds to it

The Service Team seat walked a hypothetical M05 close. Today an adversarial
close already needs three seats (via `tests/test_arm_scoping.py`,
`evals/comparators.json` and `milestones/*/probes-run.json`); a goldens-only
close needs one and touches no pin. After this ADR both need three, the
recorder writes the pin, and the operator's path is:

```bash
make check                                                         # hermetic, green
python -m evals.run_evals --answers milestones/MNN/goldens-run.json \
    --record --tag mNN --target <service>                          # writes the entry and its pin
python -m evals.run_adversarial --observations milestones/MNN/probes-run.json \
    --record --tag mNN --target <service> --instrument-name <registered> \
    --guardrail-version <v> --guardrail-policy-sha256 <sha>        # if L5; values from verify_guardrail_pin.py
make check                                                         # green again: every entry on disk is pinned
```

with the rules stated beside it: never edit a committed entry; a wrong row gets
`--supersedes <entry>`; an entry *this PR created* may be fixed in place, because
it is not on `main` yet; the close PR body carries three dispositions and one
rationale. When `make check` is red between a record and its pin — which can
only happen if an entry was written by hand — the failure prints the normalised
digest line and names `pins.json`, and a *pinned-but-missing* entry gets a
different message, because "history has been rewritten" for both is ADR-041's
B-0 false accusation.

## Pre-registered predictions

| # | prediction | what falsifies it |
|---|---|---|
| 1 | an appended row claiming a number no run produced **fails on `main` as it stands** once decision 2's completeness assertion exists, and passes before it | it passes after — then completeness does not close T1a's visibility, which is the threat draft 1 missed |
| 2 | `set(pins.json) == set(entries on disk)` plus the 64-hex check catches all of: an appended row, an empty-string pin over a rewrite, a ninth unpinned entry, a subdirectory or non-`.json` file, the directory deleted | any survives — then one assertion is not doing the work five holes need |
| 3 | the base-diff check fires on: a one-commit rewrite of a committed entry with its digest re-pinned; the same squash-merged; an evil merge; a rename-plus-rewrite (`D` seen because `--no-renames`); a deletion | any is missed — then the count was not the only thing wrong with decision 3 |
| 4 | the base-diff check does **not** fire on: an honest two-commit PR under `refs/pull/N/merge`; an intra-PR edit of an entry the PR created; an honest branch behind an advanced `main` that added an entry; `main` as it stands with `m00b-judged-B-goldens.json`'s two commits | any fires — then it teaches squashing or rebasing, and rebasing is how ADR-041's B-0 arrived |
| 5 | it **refuses**, with a named message, on a shallow clone, on a tree with no `.git`, with `git` absent from PATH, and with no resolvable base — never passes, never raises a bare traceback | any passes quietly — the `rules_validate` hazard; any raises — an errored step is not a stated block |
| 6 | `two-key.yml`'s diff with `--no-renames` collects the key on `git mv evals/run_adversarial.py evals/record_adversarial.py` + edit, and on a history entry moved out of the directory; without the flag neither is collected; and the test that pins the flag is red when it is removed | the flag does not collect it — then rename detection was not the whole of the bypass |
| 7 | `pave gate two-key` demands **ai-quality, security AND platform-eng** for every path shape under `evals/history/` and for both recorders, and no path in the directory drops to fewer keys than today; the seat-set test is red when `security` is removed from any three-seat rule | one drops, or the removal is green — then prediction 7 of draft 2 has failed a fourth time |
| 8 | with `corpus_size` registered, an unenumerated arm recorded asking three of eleven **FAILS the lane** with a message naming 3 and 11, and replacing the floor read with a literal is red | it passes, or the literal is green — then the denominator is still the PR's number |
| 9 | `samples_from.sha256` matches the committed evidence for every entry that carries it, via the `m04` revision row and no other exemption; and a new row without `samples_from` is refused by the committed-tree test | a second exemption is needed — then the revision record is a grandfather list with a better name |
| 10 | a second entry sharing `sha` and `suite` and declaring no distinguishing dimension is refused; `supersedes` must name a file on disk, not itself, with matching `sha` and `suite`; the `m00b` deterministic/judged pair (instrument absent vs present) is **not** refused | any validates that should not, or the canonical pair is refused — then decision 7's floor is either zero or aimed at honest rows |
| 11 | a correction can be recorded end to end by a real `--supersedes` invocation of each recorder, lands under a `-correctionN-` filename, and `pave check` is green afterwards with the new row pinned | it cannot — then decision 7 names a verb no tool can produce, which is how this defect arose the first time |
| 12 | adding a top-level required field to `schema.json` is red in the ratchet test, and adding a conditional one under `if/then` keyed on a declared field keeps eight of eight entries valid | the ratchet is green, or a conditional field invalidates a committed entry — then decision 7's schema rule is wrong in one direction or the other |
| 13 | `scores == derive(cases)` holds for every committed goldens entry and the README's goldens rows match their entries; a one-field edit to either is red | either is green — then the self-consistency and the public claim are not tied |
| 14 | no committed entry's `scores` or `cases` changes, no `README.md` number moves, and `m04-adversarial.json` is byte-identical before and after | any moves — then this ADR edited history while claiming to protect it |

Prediction 1 is load-bearing, for ADR-037's reason. Prediction 7 is draft 2's
prediction 7, which has failed three times and is carried as a discipline.
Prediction 8 is the G4 prediction: it is the one that says a probe count cannot
be invented by the PR that reports it.

## What draft 2 got wrong

- **Decision 3's mechanism did not exist.** "Commit count" could not satisfy
  predictions 3 and 4 at once (three seats, same two branches), was red on
  `main` today, needed the constant draft 2 had withdrawn, and the remedy it
  taught was squashing — the exact failure it said it avoided. Replaced by a
  merge-base diff, which satisfies 3, 4 and 5 and needs no exemption list.
- **Its blindness list was wrong in both directions.** It claimed blindness to
  an evil merge (seen, count 2) and to rename-plus-rewrite (true, but claimed
  caught by completeness, which a re-pin defeats).
- **"Completeness catches rename-plus-rewrite" was false in composition.** Only
  if the attacker forgets to re-pin. `--no-renames` on a merge-base diff is what
  catches it.
- **Every key it added was bypassable by `git mv`**, because the workflow that
  collects keys reads the diff with rename detection on. Not a draft-2 defect
  so much as a standing one it did not find; it is in this ADR because
  decisions 1 and 8 are worthless without it.
- **It said `floors.py`'s guarantee was corrected and never stated the
  corrected guarantee.** Under draft 2 the floor for a new arm was still the
  PR's number, attested. Decision 6 makes it a registered constant.
- **Decision 5 was "T1's floor" and had zero height.** `arm: rerun` clears it.
  Reclassified as legibility; the truth constraints are elsewhere.
- **`supersedes` could not resolve to a committed entry** because it was a SHA
  and a SHA is not an entry's identity. Now a filename.
- **Decision 4's fourth verb had no use case that survives.** Its motivating
  case had identical numbers and was legitimate intra-PR amendment by draft 2's
  own account; the "wall" it opened a door in is the correct behaviour of a test
  that validates committed entries. Withdrawn; replaced by a schema rule.
- **The complete pin had no home**, and the obvious one was red at line 151.
- **Prediction 9's "real recorder invocation" was not a bar.** `--history-dir`.
  Replaced by committed-evidence anchoring.
- **It did not find that `m04`'s evidence link was already broken**, by a
  two-key PR, under an entry it proposed to make three-key.
- **It said "three seats" and meant three lines.** Stated now.
- **It left the honest path red on Windows** — no digest printed, CRLF written —
  and the checklist that drives it non-runnable.

## Consequences

- The directory that anchors two gates stops being editable on one key, and
  the recorders that write it take the same keys as the rows.
- **T1b acquires a deterministic control** — the denominator an arm reports
  must equal the corpus its instrument registers — and T1a acquires an anchor to
  committed evidence plus self-consistency, on top of the attestation that
  remains its honest residual.
- **T2 acquires a check that fires on nothing honest**, including the one
  rewrite on `main` today, and on every dishonest shape four seats could build.
- The two-key collector stops being bypassable by a rename. This is the change
  with the widest effect outside this ADR's subject.
- `ADR-041`'s `floors.py` guarantee becomes true by construction and its
  docstring says why; the `m04` entry's broken evidence digest is recorded with
  its cause rather than left for a reader.
- A goldens-only milestone close moves from one seat to three. An adversarial
  close already needed three. `close-milestone` step 2 says which commands, and
  runs.
- A contributor on a depth-1 clone sees one named red on first `make check`.
- `schema.json` can never again gain a field that invalidates a committed
  entry, and the test that would have refused one is now the stated rule rather
  than an obstacle.

## What this ADR does not do

It does not change a recorded number, a threshold, a baseline, a guardrail or a
probe. It does not re-score any suite, register an instrument, or spend a model
call. It does not claim that a pinned, anchored, attested row is *true* — it
claims that landing a false one now takes a forged evidence file under two
keys, a consistent forged case list, a corpus size Security registered, and
three written dispositions, where draft 1 found it took a file appearing in a
directory nobody checked.

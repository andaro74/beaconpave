# SPEC/06b — the trajectory eval

The M06b spec, on its own branch before any other M06b PR, per `SPEC/06`'s own
sequencing rule. **Draft 2, after one round of four seats. Zero model calls.**

## What the milestone is for

The platform cannot tell a tool that was **called** from a tool that was
**claimed**. Four `m00b` passes and eleven `entitlement_source` asserts have been
waiting on that since the control was recorded, and Act 0's punchline is the
ungoverned control reporting `source: entitlement-check` without having the tool
while the governed platform still cannot demonstrate it does better.

## What this document is, and what it deliberately is not

A register of thirteen attacks, each with a plant that reproduces it.

**No numbered PR plan, no prediction list, no definition-of-done checklist.** That
is a cut taken from measurement, not taste: `SPEC/06`'s register was stable from
round 9 while its nine-PR plan with sixteen predictions and eleven DoD boxes broke
in every round and was cut. A fix written in prose is a claim, and claims need
plants.

## The seat round

Four seats planted against draft 1. **All seven of its attacks reproduced exactly,
under three independent seats** — same plants, same failing test names, same
verdicts. What did not survive was the arithmetic around the register and several
conclusions drawn from it. That is the inverse of `SPEC/06`'s history, where the
register held and the plan broke, and it is the reason the register form is kept.

Draft 2 corrects every number, adds six entries the seats found, and reopens one
decision draft 1 had no business marking taken.

### Blocking, and neither is a file to edit

- **B8 — deploying `entitlement-check` re-inlines the blackout vocabulary.** Its
  input schema's `dma` enum is `data/catalog.json`'s `dmas` list verbatim, and
  `handler.py:150-160` ships the whole input contract to Bedrock as `inputSchema`.
  A complete hermetic deploy trips `tests/test_gateway_run_parity.py:255` — **the
  test draft 1's own *must not do* list cites as the enforcement.** The milestone's
  step 2 does the thing its spec forbids. Four seats own that schema; three
  resolutions exist and none is this document's to pick.
- **B9 — a lake-derived trajectory is forgeable, and step 2 is what arms it.** The
  audit `tool` fragment has **no field meaning "this tool ran"**; `_tool_probe`
  already writes `decision: "allowed"` records for calls it explicitly does not
  execute; `probe_id` is caller-supplied and optional; and `seq` **collides** with
  the model path's first call at an identical lake key. Inert today only because
  `entitlement-check` is undeployed.

Both point the same way as draft 1's ordering, for stronger reasons than draft 1
had: **step 2 is blocked, not merely second.**

### The rest of what the seats found

- **B10** — neither the trajectory nor the audit record carries the tool's
  **answer**, and both schemas are closed. All three remedies draft 1 offered for
  B6 assume evidence that does not exist.
- **B11** — `entitled`, the field `entitlement-check` exists to produce, is
  deletable from a four-seat contract on a green suite.
- **B12** — `cited_titles_in_fixture` is evaluated 275 times across every committed
  run and fails **zero** times, so deferring it moves no comparator and collects no
  key. B7's blind spot at full size, and the attack that decides Decision 4.
- **B13** — two committed history entries share SHA `515ee709` and disagree about
  whether four `m00b` passes are earned; neither declares the other superseded.
  **This invalidates draft 1's own lead rationale** and is not M06b's to fix.

### Corrections carried into draft 2

- **`COLLECTED_FLOOR` is 2255, not 2079.** Draft 1 cited ADR-045's figure;
  `pave/floors.py:260` records it re-seated at the M06 close. Slack is single
  digits, not 182.
- **Decision 7 reverts to OPEN.** Draft 1 marked it *"Taken, by ADR-055, reading
  Decisions 1 as standing."* ADR-055 says the opposite and explicitly refuses to
  take that disposition. In a Decisions list a builder obeys, that converted an
  open seat question into a closed one by citation — G9's failure a second time.
- **Decision 3's option A is refused, not offered.** Adding `trajectory` to
  `build_record` writes the gateway's self-report *into* the lake — fetchable
  without becoming independent, against the standard `audit.py:10-18` states in its
  own words. Its price was also wrong: three keys plus a new instrument
  registration plus 15 tests, not two keys.
- **Absent trajectory evidence is INFRA, not FAIL.** `deterministic.py:241` is
  explicit that "answered wrongly" and "could not establish whether it answered
  wrongly" page different people. Draft 1 said such cases "must go red" and named
  neither.
- **A5 is thirteen sites, not eleven** — eleven deletions, one granted rewrite with
  no vehicle, one **executing** test. Draft 1 lost the last two, which is A5's own
  closing sentence.
- **B4 gains `tests/test_instrument_stability.py`** — three keys, and it does pin
  the scorer's output. Draft 1's "every test that pins its behaviour" was false.
- **Rule ordinals are unusable.** Nothing computes them; *"rule 27"* is now 31, and
  tool schemas are 33 with four seats. The document cites seat sets only.
- **Headroom quantified.** An honest trajectory assert takes m00b 18→10 and M06
  21→12 — roughly double the failure rate, every pinned comparator moved, and three
  arms have no trajectory file at all.

### Two methodological items the register now carries

- **Every plant has its restore line, and every replay needs its own tree.** Draft 1
  printed destructive `sed -i` against the two-key golden corpus with no restore,
  and during the seat round that file was found mutated. Four seats planting
  concurrently in one working tree produced three false results and one discarded
  in-flight plant.
- **Any byte change to `core/audit.py` or `core/toolloop.py` produces 15
  content-independent failures** via `capture_sha256` and `guardrail_sha256`.
  Control measured with a bare newline. A builder replaying these attacks reads
  those 15 as findings unless it is said first.

### And the document's own rule, applied to itself

Draft 2 said *"read the register's results as deltas, not absolute counts"* and then
printed sixteen absolute counts. Merging the row correction moved every one of them.
**The entries now state the delta**, which is what reproduces; three absolute numbers
remain, each because the absolute *is* the finding and each naming its tree.

## Verification

```
$ python -m pytest -q     # SPEC/06b absent from main      2261 passed, 6 skipped
$ python -m pytest -q     # SPEC/06b present, untracked    2263 passed, 6 skipped
$ python -m pytest -q     # SPEC/06b committed             2265 passed, 6 skipped
$ python -m pytest -q     # THIS PR (both files)           2268 passed, 6 skipped
$ python -m ruff check .  All checks passed!
$ python -c "from pave import twokey; print(twokey.triggered([<both files>]))"
[]
```

The last two lines differ by three, not two, and the reason is this body: it cites a
commit SHA, so `tests/test_cited_commits_resolve.py` collects one more case on top
of `test_no_account_identifiers.py`'s two. **The PR body is part of the count it
reports.** That is the instability the spec's own preamble is about, arriving in the
document announcing it.

Against `COLLECTED_FLOOR = 2255`. Hermetic, zero model calls, no new dependency. No
`evals/history/` entry, no comparator, no threshold, no golden case, no instrument
digest and no recorded number moved. Two files: `SPEC/06b-trajectory.md` and this
body. No code path is touched.

**A21 debt declared rather than incurred silently:** B8 cannot be stated without
quoting the six DMA names, four of which A21 measures as real place names in a
rename deferred to M07 in full. 15 occurrences, counted so the rename knows.

## What this PR does not do

**It builds nothing.** It is the spec, and it lands first so the attacks are on the
record before any fix is written against them.

**It leaves four decisions open and takes none of them** — B8's enum conflict
(four seats), B9's execution witness (Security's position: step 2 must not land
first under any ordering), B10's defer-or-advance-the-record-contract (AI Quality
and Platform Engineering), and whether the eval PR may move `evals/comparators.json`
at all (AI Quality, three keys).

**It does not resolve B13**, which is a history-integrity question at
`(ai-quality, security, platform-eng)` and must not be fixed inside feature work.

**It does not advance claim 10**, whose `M` cell is `—` pending the Legal/S&P
disposition ADR-055 names as owed.

# ADR-045: the declarable vocabulary is one value, and four of the five floors a verifier needs had either no pin or a pin that could not fire

**Status:** Proposed. Written before the code. **Zero model calls.**
**Seats:** AI Quality (the criteria) · Data Governance (the level vocabulary) ·
Security / Red Team (the G5 pin) · Platform Engineering (the mechanism)

This is the criteria half of M05's verifier. The mechanism — `pave/manifest.py`,
`pave/verify.py`, the loader and the refusal table — is a separate PR, because the
numbers that produce a FAIL are AI Quality's and the code that reads them is
Platform Engineering's, which is the line `pave/gate.py`'s docstring already draws.

**Everything here was measured by building it and attacking it.** An earlier
arrangement of four pins was constructed in full and weakened one at a time: two
were silent and one floor had no pin at all.

## Decision 1 — `DECLARABLE_LEVELS = ("internal",)`

The criterion for admitting a level is **that a service declaring it can serve the
request population it exists to serve.** Measured over all 25 committed golden
cases and all 11 probes, through the real composition (`gateway_client.user_turn`
→ `classify.route`):

| declared | golden allowed | probes denied pre-invoke |
|---|---|---|
| `public` | **0/25** | 11/11 |
| `internal` | 25/25 | 1/11 |
| `confidential` | 25/25 | 1/11 |
| `sensitive` | 25/25 | 1/11 |

`sensitive` is refused by G5. `confidential` is **behaviourally identical to
`internal`** and no detector can produce it — the only levels `classify_request`
constructs are `internal` and `sensitive`. And `public` is an **outage**: a service
declaring it serves nothing, because `route` refuses every request that classifies
above the declaration.

**An earlier draft admitted `("public", "internal")`**, on the reasoning that no
detection produces `confidential`. The same criterion condemns `public` — no
detection produces that either. That draft refused the no-op and admitted the
outage, and it is recorded here rather than corrected silently.

**Re-entry condition, stated so it can be acted on.** `public` becomes declarable
when `route("public", <an ordinary request>).allowed` is True — that is, when the
behavioural pin passes with `public` in the tuple. The weaker condition an earlier
draft stated — *"the day `classify_request` can return it"* — is **not sufficient
and was measured**: a branch was added so the detector returns `public`, and
declaring it was still an outage. The pin the same milestone builds is a stronger
test than the prose beside it, so the prose is corrected to match.

Re-entry also costs more than a `floors.py` edit: the change is in `classify.py`,
which moves `classify_sha256` (measured: 15 failed) and requires a successor
instrument registration.

## Decision 2 — equality plus behaviour, never containment

The first guard was `DECLARABLE_LEVELS ⊆ classify.LEVELS`. Measured, that predicate
returns PASS for:

- `()` — a vocabulary that refuses every manifest;
- `("public",)` — the outage alone;
- the full four-level pre-refusal vocabulary, **including both levels it exists to
  refuse**.

It witnesses nothing. The guard is now equality against the recorded tuple, plus
containment in `classify.LEVELS` (one authority for the taxonomy, read and never
edited — a constant appended to `classify.py` is 15 failed), plus two behavioural
pins.

**The behavioural pin for G5 loops over `classify.LEVELS`, not
`DECLARABLE_LEVELS`, and that is the load-bearing detail.** Looping over the
declarable vocabulary is a loop over one element, and deleting G5's dedicated
short-circuit at `classify.py:124-125` left that version **3 passed** — because at
`declared="internal"` the index comparison at `:127` refuses independently. The pin
could not distinguish *refused by design* from *the index happened to agree*.

The repository's one live witness of G5-by-design passes `declared="sensitive"` —
a value `DECLARABLE_LEVELS` will never contain. `tests/test_gateway_core.py:283`
holds it, it is load-bearing, and the new pin generalises it across the taxonomy
rather than superseding it.

## Decision 3 — five floors, five pins, and what each replaced

| floor | the weakening, measured |
|---|---|
| `PLATFORM_EVAL_MIN_CASES` | **had no pin at all.** `20 → 0` was **1867 passed, zero failures** — the milestone's own opening finding (`gates.eval_min_cases: 20 → 0` green) reproduced one level up, inside the file built to fix it |
| `HEADROOM_BAND` | fine as a literal pin; kept |
| `smallest_pack_that_can_hold_headroom` | the return pin held (`return 10` fires it), but the function had a **default argument** and the ratchet called it with the default: re-defaulting to `(0.0, 1.0)` took the floor to **1** at 1889 passed |
| the band, applied | the pin asserted another file *imports* it. An import line satisfies a source assertion looking for an import line: **1864 passed** with the band imported, unused, and both headroom cases off |
| `COLLECTED_FLOOR` | the cited precedent points the wrong way — see decision 5 |

**The two-sided ratchet's lower tie must not be the feasibility bound.**
`smallest_pack_that_can_hold_headroom(HEADROOM_BAND)` is **10**, and it answers
"can a pack this size express the band at all", not "is a pack this size worth
trusting". Tying the floor to it alone left `20 → 10` at **1888 passed, zero
failures** — and 10 is precisely one of the two sizes whose legal near-counts are
all on a band boundary. So the ratchet pins the recorded value as a lower bound
(**may rise, may not fall**) *and* requires it to clear the feasibility bound.

**The applied pin calls the checker against the committed pack, from a file the
attack does not touch.** A pin that calls the checker against a *synthetic
violating* pack demonstrates the checker and says nothing about the repository's
own pack passing through it — the same category error one step over, measured at
**1888 passed** under the identical attack. `tests/test_floors.py` and
`tests/test_contracts.py` now both call `floors.check_headroom` on the committed
pack, so gutting either leaves the other.

## Decision 4 — the floor counts disposed cases, per case, on a field that already exists

A scaffolded pack is twenty rows in a file and zero cases anybody has read, so a
row count lets `pave new` satisfy the floor it exists to impose. A case counts once
its `provenance.author` is not `pave-template`.

**Per case, not a pack-level header**, and the header shape was measured first:
`cases.yaml` is a top-level YAML list with nowhere to put one, and restructuring it
to `{provenance: …, cases: […]}` is **47 failed, 1824 passed, plus a collection
error** across eight test files including both instrument-stability pins. The
precedent that suggested a header — `quality/judge/calibration/labels.json` — is a
JSON *object*, where a header costs nothing. All 25 committed cases already carry
`provenance: { author: human }`, so this needs no migration.

**The denominator for headroom is the disposed set**, and an **empty** disposed set
raises the floor's error rather than a ratio error. That is the guaranteed first
input: a freshly scaffolded pack is entirely `pave-template`, the ratio is 0/0, and
`pave verify`'s refusal contract promises a named FAIL with no traceback — which a
`ZeroDivisionError` is not.

Over all rows rather than the disposed set, a compliant pack (20 disposed, 1 near =
5%) goes **red at 1/25 = 4%** the moment a team scaffolds five more, because
scaffolded rows never carry the flag and only push the ratio toward the low-end
failure. `pave new` would emit a scaffold that fails its own headroom gate as the
team fills it in.

**One counting rule ships, not two.** `test_case_count_clears_the_manifest_gate`
counted rows while the floor counted disposed cases. Measured divergence: 25 rows,
19 disposed, floor 20 — the row-counting test **passed** while the floor was
breached and the disposed-set ratio was 0%. Two counting rules for one number is
how ADR-037 happened.

## Decision 5 — `COLLECTED_FLOOR` is `>=`, and it closes the deleted-test-file case

The `<=` shape — `G4_CASE_FLOOR`'s, and correct there, because a corpus must not
outgrow its floor — buys nothing here. Measured by deleting a test file:

```
no floor at all      ->  1853 passed, zero failures
n <= COLLECTED_FLOOR ->  1856 passed, zero failures
n >= COLLECTED_FLOOR ->  1 failed, "8 test(s) vanished"
```

**What it closes:** net deletion. `rm tests/test_adversarial_scoring.py` is 1821
passed with `pave check` PASS at exit 0 — and that file is what
`evals/comparators.json:40` names as the only live protection on `CEDAR_MECHANISMS`
and G4's "and logged" half.

**What it does not close, stated rather than discovered:** deletion plus padding.
The same deletion with one 60-case parametrised file added measured **1883 passed —
above the baseline** — with the entire G4 scoring protection gone. **A count sees
arithmetic, not identity.** An earlier draft filed this as a standing residual three
paragraphs from the mechanism that closes half of it; both halves are stated here.

## Decision 6 — `expect_near_threshold` moves to the case top level, and only there

Two lines, justified on CLAUDE.md's deterministic-first style rule alone: a headroom
case previously needed a `judge:` block, and the real cost of that was **a `judge:`
block invoking no judge** — not the rubric-shaped story an earlier draft told.
That story was measured false: removing the rubric is `if rubric:`-guarded and left
1861 passed.

**One location, not two**, and a closed top-level key vocabulary ships with it.
There was no top-level vocabulary check for the golden set — `KNOWN_CASE_KEYS`
covers the *adversarial* corpus only — and
`test_no_case_uses_an_undocumented_assert`'s own docstring names the failure mode:
*"the harness skips what it does not recognise, so the case reports PASS while
checking nothing."*

At today's N=25 a typo'd flag is caught by the band (1/25 = 4%). **At the platform
floor of 20 it is not:** the legal near-counts are exactly {1, 2}, both exactly on
a band boundary, so a 20-case pack losing one flag to a typo lands at 1/20 = 5% and
stays legal. Accepting both locations would leave the nested one outside the
vocabulary, where nothing sees it at all.

## Decision 7 — a second vocabulary site closed on the way past

`tests/test_contracts.py` held `{"public", "internal", "confidential"}` as a bare
set literal — three values against the authority's one, findable by no `grep
DECLARABLE_LEVELS`. Nothing would have gone red, because the narrower gate wins at
runtime, which is exactly what makes that shape durable. It now reads the authority,
the same move ADR-044 made for `GATED_CONSEQUENCES` one file over.

## What this does NOT do

**It does not enforce any of these floors.** They are criteria; `pave verify` reads
them and is a separate PR. `COLLECTED_FLOOR` in particular is pinned here and wired
into `pave check` there.

**It does not verify more than one service.** No test in this repository enumerates
`services/*`, and both CI evaluation steps are hard-coded to `highlights-agent`. The
verifier's own test must glob the tree and assert the glob is non-empty, or a
service the repository has never heard of stays invisible — which is the premise
M05 exists to remove. Recorded as owed by the mechanism PR.

**It does not make the declared level mean anything at runtime.** `handler.py:309`
still takes `declared` from the event. What `classification` **is**, positively: *a
declaration the repository refuses to merge when it is outside the vocabulary* — a
control on the repository, not on the runtime, and not a claim that the repository
can tell whether the declaration is honest.

## Scale-up path

*At scale, the floors move to a policy service the gate queries, and the pins become
that service's own conformance suite; the interface already matches — every
criterion is a module-level constant read through one import, and no caller
computes one.*

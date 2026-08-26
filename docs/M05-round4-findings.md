# SPEC/05 draft 4 — seat review round 4

**All six seats reported. Every one returned `VERDICT: redraft`. Nothing is approved (G6).**

- Branch: `m05-paved-road`, cut from `origin/main` (`6af17d2`), tree identical, clean.
- Baseline: `python -m pytest -q` → **1861 passed**. Every number below is measured
  on this tree. The spec's numbers are `07e8cd1`'s (1795) and are left as recorded
  per the eval-discipline convention.
- **Blocking count: 55.** Data Governance 5 · Service Team 11 · Platform Eng 8 ·
  Security 8 · AI Quality 9 · Tool Owner 14.
- Rounds 1–3 were 39 / 31 / 20. **The trend did not continue.** Draft 4 relocated
  draft 3's controls into files that could hold them and, in doing so, walked into
  a larger set of exposures than draft 3 had. Draft 5 is required.

## Re-measured premise (lead, before the round)

The headline reproduces identically on this tip. Six manifest fields deletable at
**1861 passed** (`apiVersion`, `template`, `brand`, `owners`, `runtime`,
`attestations`); four detected (`service`, `classification`, `tools`, `gates`).
All four value changes green at **1861**: `classification: internal→public`,
`→confidential`, `gates.eval_min_cases: 20→0`, dropping a declared tool.
Only the total moved: 1795 → 1822 → 1861. **The milestone's premise is sound.**

---

# The seven findings that change the milestone's shape

## A. A deny-everything Cedar policy scores 11/11 on the compliance suite (Security 1)

`POLICY_MECHANISMS` has three members (`audit.py:39`). Under identical blanket
denial of 11/11 probes:

| mechanism | score |
|---|---|
| `classification` | 10/11 — the spec's finding 21 |
| `iam` | 10/11 — **not in the spec**; `record["classification"]` cannot discriminate it |
| `policy` | **11/11 — perfect**, ADV-008 included |

Best working arm is 7/10 (`m04`, `m01`); `m00b` is 0/10. **Zero of these passes is
marked `unearned`**, and `score_probe` returns the literal `"blocked and logged"`
for a record where nothing was blocked and nothing was examined.

The defect is not the classification field — `_satisfied_by`
(`evals/adversarial.py:320-352`) credits **refusal without examination**. The
correct rule already exists one branch over in `_channel_mismatch`
(`adversarial.py:405`), scoped to guardrail blocks by a deliberate comment.

**Consequence:** the finding-21 disposition (ADR, Security + Data Governance,
scoped to `observation_from_record` and `record["classification"]`) closes one
third of the exposure **and would read as having closed all of it**. Security does
not approve deferring this, and notes the spec's own sentence about "a milestone
that builds a verifier while standing on them" was written about the four findings
that *did* get keyed.

**Also:** the fix moves `capture_sha256` (`adversarial.py:877-880` says so
explicitly), and `instruments.json:4` states registration is "a PRECONDITION for
any scorer change, not a successor to it." Real cost: three rules, four seats, an
ADR — not the spec's "narrow extension, cheap to reverse."

## B. Build item 5 is a net de-keying that drops Security (Tool Owner 1, 2, 3, 4, 5)

The whole justification for moving `GATED_CONSEQUENCES` into the registry is
"a word in an **unkeyed generator**" and "**zero keys collected**". Both were
`07e8cd1`'s numbers. On this tree `pave/twokey.py:502` puts
`platform/gateway/core/cedar.py` on **four seats**
(`platform-eng, security, tool-owner, legal-sp`).

| path | seats |
|---|---|
| `platform/gateway/core/cedar.py` (today) | legal-sp, platform-eng, **security**, tool-owner |
| `platform/registry/tools.yaml` (destination) | legal-sp, tool-owner |

**Four seats to two, dropping Security and Platform Eng** — from the constant that
decides whether any approval interlock exists at all. G9 is "whoever feels a
control's pain never solely controls its strength," and Security is precisely the
seat that feels an interlock's pain. The spec presents this as a strengthening.

Of the spec's four claims about dropping `"publish"`: removing every forbid clause
**confirmed** (`grep -c 'forbid(' tools.cedar` → 1 before, 0 after);
`publish-highlight` reachable with no approver **confirmed**
(`Decision(allowed=True, reasons=())`); drift gate exits 0 **corrected** — it exits
**2** on the word alone and 0 only after the regeneration its own error text
instructs; zero keys **corrected** — four.

**Taken literally the move is an unversioned breaking change.** `GATED_CONSEQUENCES`
is a property of *classes*, so a top-level key requires the registry's top level to
stop being a list: **21 failed, 1840 passed** across seven files, and
`policy generate --check` emits a raw `TypeError` traceback out of the deploy-path
gate — the exact thing build item 11 forbids. Six call sites iterate the result as
a list and the registry carries no version field.

**The additive per-tool form (`gated: true`) is fully green at 1861 — and it
silently kills the one check whose name describes the hole.** Un-declaring
`gated: true` and regenerating gives 0 forbids, `DRIFT=0`, 16 failed — but
`test_every_gated_tool_in_the_registry_carries_a_forbid` **passes**, because once
"gated" is read from the same file the loop iterates, the loop goes vacuous. Its
docstring: *"A tool promoted to `publish` without gaining a forbid would read as
governed and behave as ungoverned."* Before the move, the same attack produced
**15 failed including that test**. The move converts an independent oracle into a
self-referential one. `tests/test_cedar_policy.py:472` survives only if it is
**re-based, not removed**.

## C. `tests/test_contracts.py` is on no rule and holds four load-bearing things (Tool Owner 7, 8; AI Quality 3)

`twokey.triggered(["tests/test_contracts.py"])` → **seats []**. Found independently
by two seats. It holds:

1. **The only assertion in the repo that a publish-class tool declares an
   approver** (`:71`) — and it holds a **sixth, undiscovered literal duplicate of
   the gated set**, `gated = {"publish", "irreversible"}`, which grep for the
   constant name does not find. **Plant:** change that to `{"irreversible"}` and
   delete `approval: stepfn:editorial-approver` from the registry, regenerate →
   `DRIFT=0`, the deployed policy ships **"Declared approver: none"**, and the
   suite reports **1861 passed**. Keys collected: `legal-sp, tool-owner` — from the
   registry line alone; `test_contracts.py` contributes nothing.
2. **ADR-037's own agreement assertion** (`:598-622`) — the CODEOWNERS/`twokey.py`
   check CLAUDE.md names as what makes the next drift "a red check rather than a
   fourth discovery."
3. **The manifest→registry check that discards the caret range** (`:84`).
4. **The headroom band assertion** (`:130`) — the repo's only headroom check.

AI Quality's plant: delete `test_golden_set_keeps_headroom`, flip both headroom
cases to `false`, and delete `test_a_disposition_is_all_or_nothing` (item 10's own
cited precedent) — **1859 passed, zero failures, zero keys.** `test_contracts.py`
is cited by four modules as "the file that pins X" (`adversarial.py:37,292`,
`audit.py:256`, `guardrail.py:200`, `g4-semantics.yaml:66,488`). Verbatim the
ADR-035 shape: thermometer protected, thermostat not.

`tests/test_calibration_corpus.py` and `tests/test_judge.py` are also **NONE**.

**This is a larger measured exposure than any row the seat table proposes**, and
the table has no row for it. AI Quality: *"the one thing I would build first, ahead
of anything in item 8."*

## D. The seat table is 2 failed / 1859 passed as written (Platform Eng 1, 2, 3)

Platform Eng transcribed all seven non-landed rows into `pave/twokey.py` verbatim.

1. **`README.md` on a rule breaks `pave/tests/test_twokey.py:32`** —
   `assert twokey.evaluate(["pave/cli.py", "README.md"], "") == []`. It names
   **two** files. Draft 4 moved every guard out of the file on the left and put a
   rule on the file on the right. The spec cites that line number while reading
   only half of it. That test is the repo's only machine statement that an ordinary
   PR pays nothing; editing it is a governance event, not a fix.
2. **`data-governance` entering `twokey.RULES` requires an ADR-043 amendment.**
   Data Governance found the first failure
   (`test_this_file_is_itself_on_a_rule_that_carries_securitys_key`); Platform Eng
   ran the cascade to `test_the_seat_sets_adr043_decided_are_exactly_these`, whose
   message forbids the two-line fix by name: *"Changing a rule's seat set is a G9
   decision — amend the ADR, do not edit this constant to match the code."* Price:
   an ADR-043 amendment plus `tests/test_twokey_seats.py` becoming a **six-seat**
   rule, so every future seat-set change collects all six. The spec proposes the
   seat without pricing it.

The rest of the table is clean — the useful half of the measurement.

## E. Three seats independently refuse the `legal-sp` drop (Security 2; Tool Owner 9, 10)

`^platform/registry/tools\.yaml$` does not match `tools/publish-highlight/schema.in.json`.
The MER-AI-0001 `ai_generated` flag lives at `schema.in.json:14` and travels into
`tools.contracts.json:228` inside the gateway bundle. **Neither moves to the
registry.** Today that path is BLOCKED without `legal-sp`; under the proposed row
it is SATISFIED.

Applying the row: **4 failed, 1857 passed**, including
`test_editing_a_tool_schema_collects_the_tool_owner_and_legal_sp` and
`test_dropping_publish_from_the_gated_consequences_collects_legal_sp`.
`tests/test_twokey_seats.py:238-241` records that **Security made this exact
recommendation in round 2 and retracted it in round 3**. Draft 4 re-proposes the
retracted recommendation. Security is not repeating it.

Tool Owner ran the full finding-17 diff — delete `ai_generated`, add
`skip_approval`, relax both catching constants, all four files on the same rule the
spec strips: `DRIFT=0`, `skip_approval` at `tools.contracts.json:228` in the
deployed bundle, **1861 passed**. Under the spec's row **no other rule reaches
`legal-sp`** — the disclosure flag becomes editable with no Legal/S&P key anywhere
in the path.

**Resolution:** split the row. `cedar.py` may lose `legal-sp` *iff* the class list
genuinely moves and the registry gains `security`. `tools/*/schema.(in|out).json`
and `tests/test_cedar_policy.py` **keep `legal-sp`** — what they carry is a
disclosure obligation, not a consequence class.

## F. A manifest can declare a tool Cedar denies it, and nothing notices (Service Team 5)

Revoking `highlights-agent`'s grant on `entitlement-check` and regenerating cleanly
leaves the manifest declaring `- id: entitlement-check@^0`. **Nothing checks that
the declaring service appears in that tool's `callers:`.** `test_contracts.py:83`
does `entry["id"].split("@")[0]` and checks only that the id exists.

Build item 6's "the tool set from the registry" is satisfied by the existence check
that already ships, so **as written it does not close this**. Needs its own build
item: `manifest.service ∈ registry[tool].callers` for every declared tool, and the
reverse for every grant.

## G. Every floor M05 builds is weakenable, including the one item 8 forgets (AI Quality 1, 2, 4, 11)

AI Quality built all three floors plus `smallest_pack_that_can_hold_headroom()` and
the spec's exact four pins, then attacked each.

- **`PLATFORM_EVAL_MIN_CASES = 20 → 0`: 1867 passed, zero failures.** Item 8 names
  three floors and four pins, and **none of the four touches this one.** The
  milestone's own opening finding (`gates.eval_min_cases: 20 → 0` green) reproduced
  one level up, inside the file M05 builds to fix it. `pave/floors.py`'s own
  docstring is the rule being broken: *"A floor is only half a floor without its
  ratchet."*
- **Pin 3 is silent.** Band in `floors.py`, `test_contracts.py` importing it, the
  band assertion replaced with `assert ratio >= 0.0`, both headroom cases flipped
  to `false`: **1864 passed.** An import line satisfies a source assertion that
  looks for an import line. Pin 3 must assert the band is **applied**.
- **Pin 4's cited precedent points the wrong way.** Deleting
  `tests/test_calibration_owe.py` (8 tests): no floor → 1853 passed; `n <=
  COLLECTED_FLOOR` (the cited `G4_CASE_FLOOR` shape) → **1856 passed, zero
  failures**; `n >= COLLECTED_FLOOR` → **1 failed** *"8 test(s) vanished"*. The
  `>=` half is the entire value.
- **Pins 1 and 2 work**, within limits — pin 2 is structurally blind to the band's
  lower bound, and nothing consumes the function it pins.

**Scoreboard: 2 of 4 pins silent, plus one entirely unpinned floor.** The spec
replaces draft 3's "4-of-5 silent" with an arrangement it has not measured.

---

# Blocking findings by seat

## Data Governance — 5 blocking (1, 2, 3, 4, 5)

1. **Withdraws its own key-drop argument.** "Exactly one legal value" is false.
   `test_contracts.py:96` admits **three** today; refusing `confidential` leaves
   **two**. Measured over 25 goldens and 11 probes: `public` 0/25 served, 11/11
   denied · `internal` 25/25, 1/11 · `confidential` 25/25, 1/11 · `sensitive`
   25/25, 1/11. `internal→public` is 1861 passed and `rules=0`. **A seat is removed
   from a two-key path on a count off by one, in the direction that removes the
   seat.** *(Found independently by Service Team 11 and AI Quality 13 — three
   seats.)*
2. **The vocabulary drops the harmless value and keeps the harmful one.** Verified
   both halves of prediction 4: the only `Classification(...)` literals
   `classify_request` constructs are `internal` and `sensitive`; `route` does apply
   `confidential` by index (`classify.py:127`). But no detection produces `public`
   either, and `confidential` is behaviourally identical to `internal` while
   `public` is the 0/25 outage. **Proposal: `DECLARABLE_LEVELS = ("internal",)`**,
   `public` re-entering the day `classify_request` can return it (CLAUDE.md
   scope-cut-as-ADR). Prediction 4's four messages become four *refusals*.
3. **The anti-drift test is vacuous.** `DECLARABLE_LEVELS ⊆ classify.LEVELS`
   returns PASS for `()`, `("public",)`, and the full pre-refusal vocabulary. Needs
   **equality** plus two behavioural pins through `route`. Nothing on `main` pins
   either level's behaviour — `test_gateway_core.py` has four `route` tests and
   none names `public` or `confidential`.
   *Relocation premise confirmed:* one line appended to `classify.py` → **15
   failed, 1846 passed** (same 15 as the spec, all `test_adversarial_entry.py`);
   same line in `pave/floors.py` → **1861 passed**. Relocation right, guard wrong.
4. **Finding 21's attack needs no manifest edit.** The level is a hard-coded event
   literal in three harnesses — `run_probes_via_gateway.py:144`,
   `run_via_gateway.py:157`, `run_with_tools.py:155` — and `handler.py:309` is
   `event.get("classification", "internal")`. Key coverage: the first collects
   `(security, platform-eng)`; **the other two collect zero.**
5. **The template gets the key and the rendered instance loses it** — verbatim the
   asymmetry draft 4 condemns in draft 3. `templates/agent-tools/README.md` →
   `rules=0` today. Both or neither.

**Non-blocking.** (6) Declining the `services.json` path is right but for the
weaker reason — measured, event-supplied `declared` **cannot widen access**
(`route` short-circuits on `sensitive` at `classify.py:124` before the index
comparison), so it is a self-restriction dial and the exposure is scoring
integrity, not exfiltration. (7) The corrected manifest comment still over-claims —
the repo refuses a value outside the vocabulary, not one that is *wrong*.
(8) Finding 21's handover verified exact: `classification` and `error` both dropped
by `observation_from_record`; honest and attack observations byte-identical without
it; `classification` is a **required** field of `audit.schema.json` so no
presence-vs-truthiness machinery is needed; the record's value is the **detected**
level (`handler.py:327`), not the declared one. (9) `error.message` must **not** be
copied across — it renders request-derived text into `evals/history/`, a store with
different retention. (10) **`jefferson-city` is a real market name**, forbidden by
CLAUDE.md, 39 occurrences across 30 files including `classify.py:17`; a rename moves
`classify_sha256` (15 failed) and needs a new instrument registration. **Not a
ride-along — its own PR.** (11) Downward: the taxonomy is not defenceless (deleting
the attribute terms is 2 failed); what has no behavioural pin is the *declarable
vocabulary*.

## Service Team — 11 blocking (1–11)

1. **Rendered file list and pair list are claimed stated and stated nowhere.** Four
   sentences promise them; none is the list. Draft 3 was killed for the omission;
   draft 4 asserts it is fixed and still omits it. *(Found independently by three
   seats.)* Consequence: onboarding swings between 3 and 5 attestations on a list
   the spec declines to write.
2. **Onboarding is 5 seats, not "one PR."** Measured by writing the proposed rules
   into `twokey.RULES` and evaluating the demo script's own command:
   `ai-quality, legal-sp, platform-eng, security, tool-owner`, 4 blocking reasons.
   Draft 1 was 4, draft 3 was 6, **draft 4 is 5** — genuinely shorter than draft 3,
   still longer than draft 1. `legal-sp` arrives only because `callers:` shares a
   file with `GATED_CONSEQUENCES`, so build item 5 makes **every future team's
   one-word caller edit collect Legal/S&P forever.**
3. **The scaffold hands the team files it cannot edit alone, forever.**
   `^services/[^/]+/run_probes(_via_gateway)?\.py$` → `(security, platform-eng)` is
   an existing rule, and `pave new` renders that file into the team's directory.
   Bumping your own `p95_ms` costs two seats. The spec states onboarding cost and
   never steady-state cost.
4. **"creates-only" is insufficient — there is a mandatory second command.** Adding
   the caller and not regenerating: **3 failed, 1858 passed**. Of the three
   messages, one teaches (`test_cedar_policy.py:50` names the exact command), two
   do not.
5. **See F above.**
6. **`--brand meridian-news` is blocked by the fixture, not the rubric.** Chain
   verified: only rubric on disk is `rubric-sports.md`; `evals/judge.py:46`
   hard-codes it; `judge.py:110-111` raises unless `brand_tone:meridian-sports` is
   present. But `data/catalog.json` has **two** `meridian-news` titles, neither with
   an event, a start time or a non-`base` entitlement, and 18 of 25 committed cases
   lean on `must_cite`. Adding one fictional news title: **16 failed, 1845 passed** —
   the catalog is embedded model-facing in the judge prompt (`judge.py:130`) and
   digested into `frozen.json`, so a second brand runs through a re-freeze (two-key
   `ai-quality`) and superseding history entries. Not in M05's scope, not named.
7. **Item 9 makes the headroom band vacuous.** `test_contracts.py:130` **counts a
   flag**; it does not measure proximity. A case stripped of `axes` and `rubric`,
   keeping only `expect_near_threshold: true`, still passes
   `test_golden_set_keeps_headroom`. A deterministic-only pack marks 2 of 20 and
   satisfies 5–10% with **zero real headroom** — CLAUDE.md's "a suite at 100% can
   only report no change or regression." **Route to AI Quality before building.**
8. **Item 10's per-case disposition is ceremony.** The cited precedent
   (`labels.json:3-9`) is **file-level**, one header block. Item 10 applies it per
   row: 40 identical lines across a 20-case pack. Two controls already catch the
   defect — `services/*/evals/` is two-key `ai-quality`, and every case already
   carries `provenance: {author: human}`. **`provenance.author != "pave-template"`
   is a sufficient discriminator using a field that exists.**
9. **The DoD's "roughly an hour" is too LOW.** Measured: 510 lines / 25 cases =
   ~15.6 content lines each; **138 asserts**, mean 5.5; 6 top-level keys per case,
   12 of 25 add `trajectory`; 18 of 25 require memorised catalog ids; a ~180-line
   assert vocabulary. Twenty cases ≈ 310 content lines and ~110 asserts. Decisive:
   the README's own section records **4 of the 25 starter cases** written with
   negative substring bans a *correct* answer trips — a **16% authoring-defect
   rate**, by the author of the vocabulary, each defect presenting first as a
   platform bug. Understating this flatters the platform exactly as drafts 1–3 did.
10. **Item 11 says "every", prediction 4 pins "four."** Enumerated **13** malformed
    inputs a real team produces. Four is not enough and the spec never says which
    four, so an implementer pins four and prediction 4 goes green over a lane that
    teaches nothing for two-thirds of its inputs.
11. Corroborates Data Governance 1 independently.

**Non-blocking.** (12) The `tests/(…)` rule is a **five-filename alternation, not a
prefix** — `test_manifest_verify.py` and the parity test land **unkeyed** unless
written into it. *(Found independently by three seats.)* (13) **The
`gateway_client.py` zero-cost claim HOLDS** — `twokey.evaluate` returns `[]`,
draft 3's 0→2 regression fully gone, cost removed not moved. Two residuals: the
parity test's normalisation is unstated, and **the cheapest way to green a red
parity test is to edit the ungoverned control** (`run_baseline.py`, also 0 keys),
which CLAUDE.md's baseline-honesty rule forbids — the failure message must say so.
(14) Feedback latency is fine, 53–62s, no finding. (15) The `pave new` stub
advertises `gate.yml` and CODEOWNERS, neither of which M05 builds. (16) Downward:
the entitlement `reason` vocabulary is machine-checked and discoverable — withdrawn.

## Platform Engineering — 8 blocking (1–8)

1, 2, 3 — see **D**. 4 — see **"Already closed"** below. 5, 6 — see **"pave verify"**
below.

7. **Rendered file list and pair list absent** (third independent finding). For
   reference: `services/highlights-agent` is 14 files, of which only
   `pave.manifest.yaml`, `gateway_client.py`, `evals/answer.schema.json`,
   `evals/golden/cases.yaml`, `evals/golden/README.md` are plausibly
   template-rendered; the other nine are M01–M04 measurement harnesses no scaffold
   should emit. State that split, and state pairs as
   `(template file, reference file, normalisation)` triples.
8. **Five scope cuts, zero ADR numbers.** The spec names only ADR-004, 042, 043 —
   none that M05 writes — yet says "**the** ADR" twice. CLAUDE.md:12 forbids exactly
   that, and `test_citing_a_nonexistent_adr_blocks` means an unwritten ADR cannot be
   attested against. Minimum: an ADR for the deploy-verification cut, one for the
   declined `services.json` path carrying its measurement, the finding-21 handover,
   and the ADR-043 amendment if the seat table stands.

### `pave verify`: no CI path, and the wrong home (Platform Eng 5, 6)

`.github/workflows/quality-gate.yml` decides on a **closed** `--verdicts` list. A
verdict not on it is not "absent and blocking" — it is not consulted. **No build
item names that file and the seat table omits it.**

The cheap honest answer is unstated: `pave check` (`pave/cli.py:1174`) already runs
pytest and emits `verdict-contract.json`, so `tests/test_manifest_verify.py`
reaches the gate for free — what the repo already does for G3 and G7, and what
CLAUDE.md's style rule prefers. The alternative is a real lane, which costs a
`quality-gate.yml` edit (+2 attestations) and a seat-table row.

`pave/gate.py` is the wrong home for the invocation. It works mechanically
(50 passed with the row planted, `test_ordinary_pr_is_not_gated` intact), but its
own docstring line 25 draws the boundary the row erases, and the row leaves
`pave/tests/test_gate.py` — 21.7 KB, the whole pin on the exit-code contract — at
**zero keys** while the file it pins takes three. Proposal: a new `pave/verify.py`
holding only the invocation, gated as
`^(pave/(manifest|floors|verify)\.py|tests/test_manifest_verify\.py)$`.

**Non-blocking.** (9) **The `make -i` claim is CONFIRMED** — GNU Make 4.3, two
lines let the deploy run (`exit=0`, deploy printed), `&&` on one line stops it
(`exit=0`, deploy never printed). Two corrections: the spec's literal **drops the
`cd platform/infra`**, and `make -i core` now exits **0** having run neither the
gate nor the deploy — the same silent-success shape the Makefile's header records
this repo shipping for its whole life. (10) The four-PR CI premise is confirmed
(both workflows are `on: pull_request: branches: [main]` only), but "each lands
independently green" is true only **serially**, and **PR 1 alone touches every
key-holding seat in the repo.** (11) `recap-agent` removal is **not green alone** —
2 failed; the Cedar set must be regenerated in the same commit, which pushes item 4
into `cedar.py`'s four-seat rule. The spec's claim that
`test_an_uninvited_caller_is_denied_by_policy` still passes and no longer tests its
own name is **confirmed**. (12) **A whole new service is invisible to the suite** —
`services/scaffold-probe/` with a manifest declaring a nonexistent brand, no evals,
no goldens, no client, no registry entry: **1861 passed**. Strongest single argument
for the milestone, and it means the DoD's implicit "the scaffold is green" proves
nothing; state what `pave verify --all` **FAILS with** on fresh output.

### The sentinel migration — performed, measured, reverted, 1861 passed

(13) `mzz` is safe three ways (no tag, no ref, one grep hit in the spec itself) and
invisible to `check_readme`'s `` `(m\d\d[a-z]?)` `` row regex (`history.py:773`).
Count reproduces exactly: 36 `m05` + 7 `M05` in `test_history_append_only.py`, 1 in
`test_demo_recordings.py:91` = **44**. **But the substitution is not mechanical:**
`pave/history.py:563` `_milestone_dir` uppercases **only the first character**, so
`m05`→`M05` works by luck (the rest are digits) and `mzz`→**`Mzz`**, not `MZZ`. The
naive find-and-replace is red (`test_a_row_citing_another_milestones_evidence_is_red`).
With `Mzz` corrected: **1861 passed.**
(14) The `m06` repoint works; cell indices line up (`cells[5]` / `goldens_cell`'s
`cells[4]`) and the message builds generically.
(15) **The vacuity guard has TWO literals, not one** — `M04 is True` and
`M05 is False`; only the second is in the 44, and `M04` is load-bearing. The
restructure is green (1861) but has a horizon the spec asserts away: **when M10
closes, no row returns `False`** and the guard is unsatisfiable again — one
milestone later, not "every future close."
(16) Downward: six more `m05` occurrences outside the 44 are all inert prose or the
distinct string `m05-never-recorded`. **The spec's 44 is right.**

## Security — 8 blocking (1–8)

1 — see **A**. 2 — see **E**. 3, 4 — see **"Already closed"**. 8 — the
`capture_sha256` precondition, in **A**.

5. **The parity test cannot land where the spec says** (third independent finding).
   Note **Security has no key on `twokey.py` itself** (`ai-quality, platform-eng`),
   so a new alternation entry costs a `twokey.py` diff plus a 5-seat pin edit.
6. **Finding 20 is a G4 exposure, not only comparability.** Rewording the governed
   `user_turn` only (`gateway_client.py:124`): **1 file changed, 1861 passed, zero
   keys.** The pin at `test_gateway_run_parity.py:64` covers `SYSTEM` and `CLOCK`
   only and is built on `module_constants()` walking module-level `ast.Assign` — it
   **structurally cannot see a `def`**. `user_turn` composes the wire text of every
   governed adversarial observation, and `instrument_digests` (`adversarial.py:808`)
   does not cover the transport. An instrument change invisible to the instrument
   registry.
   **The fix is cheaper than the spec implies:** the two files share exactly one
   function name and it is the wrong one (`build_prompt`), but their **f-string
   skeletons are byte-identical** — `['Viewer plan={?} dma={?}. Evaluation clock
   {?}.\n{?}']` in both. Technique: collect every `ast.JoinedStr`, render constant
   segments with interpolations elided, assert the skeleton appears in both,
   **locating by content not function name** (the control inlines it in `ask`,
   `run_baseline.py:91-95`).
7. **Finding 14 is not closed by build item 12.** Two lines in `generate()` emitting
   `permit(principal == Service::"attacker-svc", …)`: the committed policy set ships
   it on all three tools including `publish-highlight`, `policy generate --check`
   exits **0**, suite **1861 passed**. Item 12 verifies a manifest's *own* service in
   both directions, so it never enumerates a phantom principal. The assertion that
   closes it is **surjectivity** on the generator side — every principal in
   `tools.cedar` is a caller the registry names.

**New probe owed, on this seat (do NOT write in M05):** `ADV-008` is verified to
carry `pass_when: cedar_denied_or_approval_required_and_logged`, but **no probe in
the corpus inspects a schema and none tests `ai_generated`.** If M07 makes the
disclosure flag live, nothing asks whether a publish-class call omitting it is
refused. Record as owed: `ADV-012 — a publish-class call omitting the required
disclosure flag is refused by the interlock and logged`.

**Non-blocking, both corrections downward.** (9) **"`POLICY_MECHANISMS` is invisible
to every pin" is FALSE** — widening it is **21 failed, 1842 passed** across four
files plus the instrument digest; it is pinned literally at `test_contracts.py:395`
and sits inside `semantics_sha256` via `_policy_mechanisms` (`adversarial.py:869`).
**The real hole nearby: two of the four catching files (`test_contracts.py`,
`test_tool_loop.py`) are on NO RULE**, and that is not among the twenty-one.
(10) The hookwrapper residual is correctly stated and reproduced — 8 lines of
`pytest_runtest_makereport` plus a second G1 role prefix reports **1861 passed**,
the exact honest count, with the pin genuinely failing when the hookwrapper alone
is removed. `collect_ignore` on three files: **1746 passed** and `pave check`
**PASS, EXIT=0**. Worth adding: one of those files,
`tests/test_adversarial_scoring.py`, is what `evals/comparators.json:40` names as
the **only live protection on `CEDAR_MECHANISMS` and G4's `and logged` half** — one
`collect_ignore` line removes it and `pave check` says PASS. **The deleted-file half
is mis-stated in both directions:** `rm tests/test_adversarial_scoring.py` → **1801
passed**, `check: PASS, EXIT=0` — true today, but `COLLECTED_FLOOR` closes the
net-deletion case. What it does not close is **deletion plus padding**. Say "a count
sees arithmetic, not identity."

## AI Quality — 9 blocking (1, 2, 3, 4, 6, 8, 9, 12, 13; +17 on process)

1, 2, 4, 11 — see **G**. 3 — see **C**. 13 — corroborates Data Governance 1.

6. **Item 9's justification chain has a false middle link.** Removing
   `rubric: quality/judge/rubric-sports.md` from `headroom-005`'s judge block, axes
   kept: **1861 passed.** `test_contracts.py:113-115` guards the rubric behind
   `if rubric:` — **conditional. A judge block does not need a rubric.** What *is*
   load-bearing is **axes** (removing those breaks
   `test_the_committed_corpus_is_what_the_rule_draws`, 1 failed) — and that draw is
   highlights-specific. For a genuinely new service neither is checked:
   `judge: { expect_near_threshold: true }` alone is green. The real cost of today's
   location is a `judge:` block that invokes no judge — smaller and different from
   the claim. **The fix itself checks out**: one changed line at
   `test_contracts.py:130` reading both locations, plus the flag moved to top level,
   **1861 passed**, band checks intact. **Keep item 9** — CLAUDE.md's
   deterministic-first style rule justifies it alone — and replace the rubric
   sentence with the measured one.
8. **Item 10 makes the repo's only committed pack count zero.** Measured on
   `cases.yaml`: 25 cases, `provenance` shapes `{('author',): 25}`, authors
   `{'human': 25}`, **carrying `disposed`: 0, carrying `curated_by`: 0**, against
   `eval_min_cases: 20`. Under item 10 the reference service — the pack PR 2's
   verifier must be green against — counts **0 disposed cases against a floor of
   20**, and the spec never mentions migrating them. The precedents
   (`test_calibration_corpus.py:265-271`, `run_judge.py:99`) both read
   `labels["provenance"]["disposed"]` — **corpus-level, one per file**. And the
   interaction with `test_contracts.py:311` (`len(...) >= eval_min_cases`, counting
   rows) is unresolved. **Two counting rules for one number is how ADR-037
   happened.**
9. **The headroom denominator under item 10 is undefined, and scaffolding can turn a
   compliant pack red.** With the disposed floor at 20: a compliant pack (20
   disposed, 1 near = 5%) goes **red** at 1/25 = 4% the moment a team scaffolds 5
   more rows, because scaffolded rows never carry `expect_near_threshold` and only
   push the ratio toward the low-end failure. State the denominator explicitly — it
   must be the disposed set, or `pave new` emits a scaffold that fails its own
   headroom gate as the team fills it in.
12. **The `audit.py` row's stated justification is measurably false.** Widening
    `POLICY_MECHANISMS` by one member: **20 failed, 1842 passed**. Dropping
    `mechanism in POLICY_MECHANISMS` from `observation_from_record`: **15 failed,
    1846 passed**. And `audit.py` **already takes two keys**. The row asks for a
    **third** on a false premise — over-keying by this seat's own measurement.
    Justify it on `observation_from_record` being the G4 observation the scorer
    reads and finding 21's named handover, and say plainly it is a third key.
17. **The predictions are amended by reference to a draft the document cannot
    locate.** The spec says drafts 1–3 are preserved at tag `drafts-spec-05`,
    "whose **first four commits are the drafts in order**." Measured: those are the
    repository's opening commits (`b6457ef Initial commit`, then three `m00a`
    commits). The real drafts are the first four commits touching
    `SPEC/05-paved-road.md`: `39cfac9`, `d66c343`, **`a3dcb0d` (draft 3)**,
    `0d17fdb`. **This is the same sentence draft 4 already corrected once** — it
    used to name a `scratchpad/` path — and `tests/test_cited_commits_resolve.py`
    does not cover it, because a tag plus an ordinal is not a cited sha. **The
    correction landed one level short of the claim.** Because every prediction
    amendment is a delta against draft 3, an unresolvable reference makes the
    amended set uncheckable — which defeats pre-registration. Cite `a3dcb0d` by sha
    and **restate the amended predictions in full**.

**Non-blocking.** (5) **`COLLECTED_FLOOR` is worth building — the spec undersells it
and contradicts itself.** The hookwrapper residual is real (hookwrapper + deleted
file + failing headroom pin → **1856 passed**, zero failures), so the floor is
**not** a hookwrapper defence and must not be sold as one. But finding 4 measures
its `>=` half closing the deleted-test-file hole suite-wide (1853 green → red) — and
the spec files that exact hole as a standing residual three paragraphs away.
**Build it, two-sided, re-justified as the deleted-test-file closer.** Also
`tests/conftest.py` **already carries the rule**; the row proposing it describes
something ADR-043 already did. (7) **Item 9 opens a top-level key with no closed
vocabulary.** There is no top-level case-key vocabulary test for the golden set
(`KNOWN_CASE_KEYS` covers the *adversarial* corpus only). At today's N=25 a typo
(`expect_near_threshhold`) is red. **At `PLATFORM_EVAL_MIN_CASES = 20` the legal
near-counts are exactly {1, 2}, both on a band boundary**, so a 20-case pack that
loses one to a typo lands at 1/20 = 0.05 — still legal. **The typo is silently
absorbed at precisely the pack size the platform floor mandates.** Ship a closed
top-level key vocabulary alongside the two lines. (10) **Downward: 20 and the band
are consistent** — `smallest_pack_that_can_hold_headroom((0.05, 0.10)) = 10`, every
N in 10..40 admits a legal near-count, N=20 admits {1, 2}. No contradiction. But 10
and 20 are the only sizes in range whose legal counts are **all on a band
boundary** — zero interior tolerance, which is what makes the typo absorption
possible. Either derive the floor as the smallest pack with an *interior* legal
count, or state plainly that 20 is boundary-exact and accepted. (14) The
`test_budget_derivation.py` row **is right** and closes a real "stated and absent"
protection (`:124` asserts in prose that `gates.budgets` is two-key while
`twokey.evaluate` returns NONE) — but the file's own docstring names *"AI Quality …
· **Platform Engineering** (the loop bound)"* and the row says `ai-quality`,
`tool-owner`. **Pick one and correct the other in the same PR, or this is the next
ADR-037.** (15) The `Makefile` row is justified by the wrong target — `core:` is a
deploy gate, platform-eng's and security's pain, not AI Quality's. What *is* this
seat's: `evals:` and `adversarial:`, the two `--record` entrypoints, and
`adversarial:`'s `OBSERVATIONS` guard. Same key, defensible reason. (16) `README.md`
yes (`:33-45` is the progression table), `recordings.json` thin — split the row.
(18) Prediction 5's widening is unbounded ("every check" against 1861 tests ≈ 26
hours vs the DoD's ~50 s), its stated residual is falsified by item 8 itself, and
"every function a ratchet calls" is undefined for a ratchet whose only callee is a
`pytest --collect-only` subprocess.

**AI Quality's note for the human:** four statements of fact in draft 4 measured
false here (6, 12, 13, 17). **Unlike drafts 1–3, these do not all flatter the
platform — 6 and 12 flatter the *problem*, arguing for controls the measurement
does not support.** That is a different failure mode and worth naming, because the
spec's preamble only warns about the first kind.

## Tool Owner — 14 blocking (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 14, 16, 17)

1, 2, 3, 4, 5 — see **B**. 7, 8 — see **C**. 9, 10 — see **E**.

11. **`recap-agent` has eleven sites in eight files**, not three (spec) and not six
    (lead). The removal claim itself is **exactly right**: registry reduced to
    `[highlights-agent]`, regenerated, `DRIFT=0`, **1861 passed**, distinct callers
    `['highlights-agent']`, **cross-tool negative pairs constructible: []**, and
    both `test_an_uninvited_caller_is_denied_by_policy` and
    `test_an_uninvited_caller_is_denied` **pass**. The full list adds:
    `tests/test_tool_loop.py:218` (docstring only — the test principal is
    `ledger-service`, so it survives), **`docs/governance/demo-script.md:89`** (a
    second one the spec and the lead both missed),
    **`platform/gateway/policy/tools.cedar:22`** (generated — must be regenerated in
    the same commit or the drift gate is red), and
    **`docs/adr/ADR-023:49, 51, 77-78`**, whose worked example *is* `recap-agent`
    and whose lines 49–51 state a live fact that becomes false. **Nothing pins any
    prose site** — leaving `README.md:13`, `handler.py:61` and the demo script stale
    reports **1861 passed**, so "corrected with them" is a promise no check
    enforces. The synthetic-registry re-founding is the right call and is sufficient
    *for the control*, not for the eleven sites.
12. **Build items 4 and 14 collide inside PR 1.** Item 14's rationale is "three
    `callers:` lines exist and **two read identically**" — correct today (`:12`
    differs). **After item 4 removes `recap-agent`, all three are byte-identical**,
    and `:31` is `publish-highlight`'s — the publish-class tool a seat over-granted
    itself during this review. Item 4 removes the only thing that made one line
    distinguishable, which also rules out "quote the line content" as the
    disambiguator.
14. **The caret semver claim is correct; the *reason* for refusing `^0.0.x` is not;
    and the whole argument is about a field nothing reads.** Semantics confirmed:
    `^0` → `>=0.0.0 <1.0.0`, `^0.1` ≡ `^0.1.0` → `>=0.1.0 <0.2.0`, `^0.0.3` →
    `>=0.0.3 <0.0.4`. But the only site that parses `@` is `test_contracts.py:84`,
    which splits the range off and throws it away, and `grep -rn '"semver"'
    --include=*.py .` returns **no matches** — **nothing reads the registry's
    `semver` field.** Plant: manifest `catalog-search@not-a-range-at-all` with
    `semver:` **deleted from every registry entry** → `DRIFT=0`, **1861 passed**.
    So "a range this repo does not evaluate" is true of every form equally. Worse,
    the refusal **singles out the safe form and ships the wide one**: under the 0.x
    convention every minor bump is breaking, so `^0` is the **widest** caret and
    `^0.0.x` the **tightest** — and item 4 adds `publish-highlight@^0`, the
    publish-class tool on the loosest available range. Either build the evaluator in
    PR 2, or state plainly that `@range` and `semver:` are both decorative today and
    drop prediction 14's caret taxonomy.
16. **The duplicate-id hard-stop is genuinely needed, is not among the 21 findings,
    and item 12 puts it in the wrong component and the wrong PR.** Appending a
    second `- id: catalog-search` with `callers: [attacker-svc]` and regenerating:
    6 policies, `DRIFT=0`, `attacker-svc` at `tools.cedar:54`, **1861 passed**,
    **keys `['legal-sp', 'tool-owner']` — two, and no Security.** This is the *same*
    `permit(principal == Service::"attacker-svc", …)` in the deployed policy set
    that ADR-043 finding 14 put four seats on, reachable through the registry at
    half the keys without touching the generator. **The hard-stop goes in
    `cedar.generate()` / `policy generate --check` — the deploy path — in PR 1**,
    because PR 1 lands registry edits first and a verifier that only runs on a
    manifest never sees a registry-only diff.
17. **A line number is the wrong anchor for item 14's printed block** — adding one
    tool shifts every number below it, and after item 4 all three `callers:` lines
    are byte-identical. The only stable anchor is the `- id:` block. Full proposed
    text is in the transcript; its load-bearing paragraph is the explicit "Do NOT
    add yourself under `- id: publish-highlight`" with the consequence class and the
    seats named.

**Non-blocking.** (6) `test_cedar_policy.py:472` **does** survive the move, but only
if **re-based, not removed** — it is the last surviving anti-vacuity guard on the
gating declaration. (13) **M05's own demo script scaffolds a service named
`recap-agent` while M05's PR 1 removes `recap-agent`** (`demo-script.md:49`, `:89`).
PR 4 records the demo. Pick one name. (15) **Build item 12 is feasible** —
`cedar.parse` evaluates both directions plus the gated half from committed text with
no `generate()` call, and adding `- id: publish-highlight@^0` to the reference
manifest is **1861 passed**, legal today and under item 12. One flag: that manifest
edit collects `ai-quality, tool-owner` under the spec's own first table row —
**granting a service a publish-class tool takes no Security and no Legal/S&P key.**

---

# Already closed — the spec bills four pieces of finished work

*(Platform Eng 4, Security 3 and 4, AI Quality 5, Tool Owner 1 — five seats.)*

- **Finding 13 (G1 allowlist):** keyed at `pave/twokey.py:461` →
  `(security, platform-eng)` + ADR. The CLAUDE.md half is also false —
  `CLAUDE.md:23-30` already names `tests/test_iam_assertions.py` and records
  `platform/infra/tests/` as the *former* pointer, citing ADR-043.
- **Finding 15 (conftest):** keyed at `pave/twokey.py:539`, and the live rule is
  **five entry points wider** than the spec's two-file row
  (`conftest.py|pyproject.toml|.pytest.ini|tox.ini|setup.cfg`). Writing the narrow
  version into the table invites a redraft that *shrinks* it.
- **Finding 17 (tool schema):** keyed at four seats **and red at three assertions**
  (3 failed, 1858 passed). Its ADV-008 sub-clause describes a defect ADR-043 already
  corrected (`ADR-043:409`); the false sentence is gone from the schema.
- **Build item 1's "seat vocabulary asserted against ROLES.md"** already exists at
  `tests/test_twokey_seats.py:143`.
- **`platform/gateway/core/cedar.py` is not an "unkeyed generator"** — four seats.

---

# Decisions a human owes before draft 5 is written

1. **Does M05 build a verifier while a deny-everything policy scores 11/11?**
   Security does not approve the deferral. (**A**)
2. **Is `public` declarable?** Data Governance says no; that decision determines
   whether its key comes off the manifest rule. Its findings 1 and 2 interlock.
3. **`README.md` on a rule, or not** — it costs `test_ordinary_pr_is_not_gated`,
   the repo's only machine statement that an ordinary PR is free. (**D1**)
4. **Is `data-governance` in `twokey.RULES` worth an ADR-043 amendment and a
   six-seat rule on `tests/test_twokey_seats.py`?** (**D2**)
5. **Does `GATED_CONSEQUENCES` move at all?** If yes, the registry must gain
   `security` in the same commit and the forbid ratchet needs a named second
   authority outside the registry. (**B**)
6. **Where does `pave verify` live, and is it a lane or an assertion?**
7. **Which ADRs does M05 write?** Five cuts, no numbers, CLAUDE.md:12 forbids it.
8. **Is the instrument-registration precondition inside M05's budget, or is that
   itself why the finding-21 fix belongs in M06?** (**A**)

---

# Settled — carry into draft 5

- **The milestone's premise.** A whole new service is invisible to the suite at
  1861 passed. Six manifest fields deletable, four value changes green.
- **`mzz`/`Mzz` sentinel migration:** sound, 1861 passed, count of 44 correct, `m06`
  repoint works. Fix the instruction (`Mzz`, not `MZZ`) and the two-literal guard.
- **`make -i`:** claim confirmed. Add the `cd platform/infra` and the exit-0 caveat.
- **`gateway_client.py` NOT on a rule:** cost removed, not moved. Keep.
- **`recap-agent` removal deletes a protection silently:** confirmed; re-founding on
  a synthetic registry is right; regenerate `tools.cedar` in the same commit; eleven
  sites.
- **`DECLARABLE_LEVELS` relocating to `pave/floors.py`:** confirmed correct
  (15 failed in `classify.py` vs 1861 in `floors.py`). Only its guard is wrong.
- **`legal-sp` stays** on the schema paths.
- **Item 9's two-line fix works** (1861 passed, band checks intact) — keep it, on
  CLAUDE.md's deterministic-first rule, with the rubric sentence corrected.
- **`COLLECTED_FLOOR`:** build it two-sided, justified as the deleted-test-file
  closer, never as a hookwrapper defence.
- **`test_budget_derivation.py` row:** justified; fix the seat pair.
- **Build item 12 is feasible** via `cedar.parse` without `generate()`.
- **20 and the 5–10% band are consistent** (`smallest_pack…() = 10`).

# Owed beyond M05

- **`ADV-012`** — a publish-class call omitting the required disclosure flag is
  refused by the interlock and logged. Security's, not M05's.
- **`jefferson-city` is a real market name** (CLAUDE.md forbids), 39 occurrences in
  30 files including `classify.py:17`. A rename moves `classify_sha256` and needs a
  new instrument registration. Its own PR.
- **Acts 0, 1 and 2 recordings** are owed by M05 in `docs/governance/recordings.json`
  and `tests/test_demo_recordings.py` goes red at close if unpaid. **Operator work —
  no agent can produce these.** Alternative: a deliberate re-deferral with a stated
  reason, which that file's own rule requires be longer than 60 characters.

# Next actions

1. Put decisions 1–8 to the operator.
2. Write draft 5. Preserve drafts 1–4 at a tag, citing draft 3 by sha (`a3dcb0d`)
   rather than "first four commits", and restate the predictions in full.
3. Run round 5 against draft 5 — the goal state is one seat coming back clean.
4. Only then cut PR 1.

---

# Finding 45 — found by the lead while saving this file

The round counted **44** `m05`/`M05` sentinels, all string literals, and Platform
Eng confirmed that count three ways. **There is a forty-fifth, and it is not a
string literal, so no grep in this round could find it.**

`tests/test_history_append_only.py:624`

```python
    (scratch / "milestones" / "M05").mkdir()
```

`.mkdir()` with no `exist_ok=True`. The scratch repo is copied from the real tree,
so **the moment `milestones/M05/` exists on disk, this test raises
`FileExistsError`.** Measured: writing one `.md` file into `milestones/M05/` gives

```
FAILED tests/test_history_append_only.py::test_the_lane_fails_an_unenumerated_arm_that_asked_three_of_eleven
1 failed, 121 passed
```

and removing the directory returns it to `1 passed`.

M05 is the first milestone to own a `milestones/MNN/` directory whose creation is
also a sentinel value in a test. **PR 4 cannot record its evidence without tripping
this**, and the failure names an arm-scoping lane, not a directory — so the next
reader debugs the wrong thing.

Add to build item 3: the sentinel count is **45**, and the forty-fifth is a
directory-existence assumption at `test_history_append_only.py:624` that needs
`exist_ok=True` or a `mzz` scratch path. Then widen the search: `grep` for the
literal cannot find this class of sentinel, so the migration must also audit
`mkdir`, `is_dir`, `exists` and `iterdir` calls against `milestones/`.

**This file therefore lives at `docs/M05-round4-findings.md`, not under
`milestones/M05/`.**

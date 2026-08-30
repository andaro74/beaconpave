# M06 register mapping — 28 attacks against `main`

*Mapped at `1173aee`; A26 and A27 added at `09a67fa` and reproduced there.*

Close evidence, written before the tag. `SPEC/06-consequence.md` requires every
register entry to be **replayed at the tag, by the plant in its own entry**. This
says which entries are already closed, which are decided-and-not-built, and which
will reproduce — so the replay obligation is executed against a known list rather
than discovered during it.

## Method, so this is reproducible rather than asserted

1. Entries extracted mechanically from `SPEC/06-consequence.md` in **both** formats
   it uses: `### A<n> — …` headings, and `- **A<n> — …**` bullets in the
   *Registered round 7* section.
2. Every path an entry names in backticks checked against the live rule set:
   `twokey.triggered([path])`, not against any written-down list.
3. Every `## Decisions` entry that says a thing *closes in M06* checked against the
   tree for whether it was built.

**Two corrections this produced, both to assumptions held before it was done.** The
register had **26** entries and not 20 — A11–A17 are bullets, not headings, and a
scan for headings alone misses seven. And the merged ADRs barely cite attack ids, so
mapping by citation returns a confidently wrong answer; see A2 and A24 below.

## Closed, verified against the tree — 5

| id | what it was | how it closed |
|---|---|---|
| **A1** | `requires_adr` accepted any tracked file — `ADR: LICENSE` discharged it, and all 374 tracked files passed | ADR-051: the record must be one the diff **wrote** |
| **A13** | one `ADR:` line discharged all three `requires_adr` rules | ADR-051: `len(records) < adr_rules_hit` — N rules need N records |
| **A11** | `pave/tests/` unguarded; deleting `test_twokey.py` was 2036 passed, zero failures | ADR-052: now `ai-quality, platform-eng, security` |
| **A19** | the judge freeze refrozen on one key — the cheap route *satisfies* the guards rather than attacking them | ADR-053: `quality/judge/` gains `security` |
| **A14** *(key half only)* | `proposed → enforced` switched off the rule's own review clock at 2079 passed, no keys | ADR-053: `rules/` gains `(legal-sp, security)` + an ADR. The immortal-rule and orphan-rule halves stay open by decision 12 |

## Decided, and not built — 3

Each carries an operator decision saying it closes in M06. None has been built.

| id | the decision | what the tree says |
|---|---|---|
| **A5** | D1 — Legal/S&P answered *no*; the consequence is deleting eleven interlock assertions | `publish-highlight` still asserted across five test files |
| **A12** | D5 own PR and ADR · D8 delete the exemption, do not clause-scope it · D11 `classify.py` gains `(data-governance, security)` with an ADR | `platform/gateway/core/classify.py` → **NO KEYS** |
| **A18** | D7 — folds into the PR that keys the mechanism behind the published claims | the G1 template fixture → **NO KEYS** |

A decision recorded and not executed is the **stated-and-absent** failure this
register exists to catch: to the next reader it is indistinguishable from a thing
already handled, and it stops them looking for the real one.

## Closability still undecided — 3

D3 leaves these open by name — *"all three are larger than they look"*:

- **A7** — the floor is a count, and counts are paddable
- **A9** — the deployment route: `BEACONPAVE_CATALOG` is read first, with no diff at all
- **A16** — `milestones/M04/probes-run-channel.json` is free

A7 is the entry the floor re-seat touches, and its own measurements record the gate
already stopping one of its three routes.

## Deferred to M07 by decision — 1

**A21** — D10, *in full*, after both grounds for splitting it were measured false.

## Open, no decision — 16

A2 · A3 · A4 · A6 · A6b · A8 · A10 · A15 · A17 · A20 · A22 · A23 · A24 · A25 ·
**A26** · **A27**

Two of these were touched by merged M06 work **without being closed**, and matching
on citations rather than on subject would have recorded both as done:

- **A2** — one rationale discharges every seat. ADR-051 says so itself: *"It does
  not fix `RATIONALE_RE`, key `pave/tests/test_twokey.py`, close SPEC/06 A2."* The
  bar is still checked once per PR rather than per rule. The `test_twokey.py` half
  of that same sentence **is** now done, by ADR-052 — one sentence, two clauses,
  opposite answers.
- **A24** — ADV-002's marker sits inside the payload it guards. The PR that landed
  the visibility fix says its own defect *"is SPEC/06 A24's shape exactly"*. Same
  shape, different instance; A24 is untouched.

D9 marks the remedy for **A10** and **A22** as *superseded* by round 11, so those
two are open with their prior remedy withdrawn rather than open and unexamined.

## Consequences for the close

**23 of 28 will reproduce at the tag.** That is not by itself a blocker — the
obligation is to replay and record, not to close everything, and an entry recorded
as reproducing with its measurement is the register working. It does settle what
remains:

1. **The five decided-not-built entries** are where the milestone has already said
   what it will do. They are the cheapest remaining honesty, and the most expensive
   thing to leave.
2. ~~Two findings from the ADR-052 review rounds are in no register entry at all.~~
   **Closed: they are now A26 and A27**, reproduced against `main` at `09a67fa` with
   their own measurements rather than the reviewing seat's. `setup.py` widened G1's
   allowlist and relaxed its own pin at **2238 passed, no keys**; the verdict rewrite
   took `gate decide` from exit 1 to exit 0 at the same baseline, on keys excluding
   Security. Neither is fixed — being registered means the replay obligation can now
   see them.
3. **`COLLECTED_FLOOR` is re-seated last**, on the tree that ships, per *How M06
   closes*.

# M09b PR 1c — the withdrawal: the derivation rule assumed a selector the repository had already refused

**Zero model calls. No deploy. No sweep, candidate, wording or measurement of any
kind. No guardrail, corpus, case, tier, ceiling, comparator or judge instrument
moved.** `make check`: **4492 passed, 8 skipped**, PASS — against **4481 on `main`
at 74cdd27**, both measured this session rather than carried from a handoff. The
+11 are all `test_cited_commits_resolve`: three cases from the SHAs the amendment
cites, eight more from this body file, each SHA generating a resolve and a
reachability case. No other suite gained or lost a test.

`SPEC/09b`'s derivation rule and ADR-076 decision 2 are **withdrawn**. Rule 3
selects on `quality/adversarial/refusal-shapes.yaml`, whose owning ADR-067 forbids
that file from judging a candidate fix — *"any candidate wording is judged by the
frozen corpora, never by this file"*, under the heading **It cannot judge a fix** —
while rule 4 excludes `answer-decomposition.yaml` by citing that same sentence,
which belongs to ADR-068. Inverting the two does **not** repair it: ADR-068 carries
the identical prohibition, so both are barred. The general fact behind the specific
one is the headline: **no corpus in this repository is permitted to select a
wording, and the withdrawn rule assumed one existed.** The milestone stopped
**before any measurement** — no sweep was taken, no candidate wording written, no
number produced under the rule — so nothing downstream rests on it and nothing here
is a threshold moved to clear a reading.

## What this PR contains

| | |
|---|---|
| `docs/adr/ADR-076-…md` **amendment 1** | the withdrawal record. **Pure tail append: 347 added, 0 deleted.** 45% of the 674-line spec it withdraws — a withdrawal record longer than its subject is one nobody reads, and four of the debts recovered here were lost inside a catch-all row for exactly that reason |
| `SPEC/09b-the-guardrail-line-and-the-topic.md` | a 12-line **WITHDRAWN** header at the top, naming the inverted citation and ADR-076 decision 2 *by its own title*. Nothing else in the spec is touched |
| `docs/adr/README.md` | ADR-076's index row records the amendment |
| `milestones/M09b/pr1c-deletability-audit.txt` | both plants and both results, including the silent one. PR 1 committed no audit; M09 committed four |

**Amendment, not a new ADR**, on ADR-067's own precedent — that ADR recorded its
withdrawn overclaim at the end of itself *"because this ADR is where the overclaim
was made"* — and ADR-012's, whose Amendment corrects its own Decision under the norm
*"this index marks superseded reasoning instead of deleting it."* A new ADR would
leave decision 2 standing as accepted pre-registration with its withdrawal one
document away: the **stated and absent** shape `CLAUDE.md` names as worse than a
missing protection, and the shape ADR-035 and ADR-037 were both written about.

## Two sessions, no contact, three of the same holes — carried unmerged

The cold review read the rule text outward; the rewrite read the owning ADRs inward.
Both independently found the inverted citation, the goldens leak, and the objective
rewarding blocking least. They are recorded as **pairs**: two derivations of one
hole is evidence about the method, and merging them destroys that evidence.

## Published as not closable

- **An ordering check constrains commitment and never authorship.** `git log` proves
  when bytes landed; the hazard is what the author had read. No test closes this.
- **A rule with no honest exit is not a rule.** Rule 3's selector is a goldens
  answer file and F4 fires on *"any goldens answer file"*, so running the rule
  honestly fires F4 at PR 3 and omitting the file from `inputs_sha256` is
  concealment. There is no third option.
- **No answer corpus may enter selection or admissibility** — structural, not a
  scoping preference. `goldens-run.json` holds 25 records, `answers()` skips the
  three refused, 22 are emitted, and `blackout-009` is one of the three. ADR-035
  amendment 7 measured it: *"the diagnostic coverage is anti-correlated with risk"*;
  amendment 8: *"a blocked answer is never committed… it must not be recorded as
  closing this."*
- **Nothing committed measures whether the loosening goes too far**, mirroring
  `topic-attacks.yaml:15` on the tightening. Minting a corpus mid-milestone to close
  it is **refused** — a corpus written after the gap is known is chosen after seeing
  a result.

## The gate, as measured

```
$ python -m pave.cli gate two-key --changed \
    SPEC/09b-…md docs/adr/ADR-076-…md docs/adr/README.md \
    milestones/M09b/pr1c-deletability-audit.txt
two-key: not required — this PR touches no two-key path
```

Run, not assumed. All four files match **NO RULE**, checked individually against
`twokey.RULES`. **That is debt 18 — *no ADR and no spec is on any two-key rule*,
70 ADRs and 17 specs editable on one key — carried unchanged and NOT closed here.**
A document withdrawing a pre-registration is exactly the class that rule would cover,
and it collects nothing. No attestation blocks appear below because none is
collected; writing them would be decoration.

## Deletability audit — both plants, both results

Working copies backed up to a temp directory and restored from there, never
`git checkout --`, which would delete the uncommitted change the audit exists to test.

| mutation | result |
|---|---|
| the `**Amendment 1**` clause deleted from ADR-076's index row | **CAUGHT** — `test_an_amended_adrs_row_says_it_was_amended[ADR-076]`, 1 failed / 86 passed |
| `SPEC/09b`'s 12-line WITHDRAWN header deleted | **SILENT** — 4484 passed, nothing fires |

Plant 1's check caught **this PR's own first omission**: the amendment was appended
and the index row was not updated, and `pave check` went red on exactly that test
before anything was committed. A check that catches its own author is the only
evidence it works.

**No test was added for plant 2, and the reason is recorded rather than left looking
like an oversight.** A guard asserting that this path carries a WITHDRAWN marker is
coupled to its own data: the replacement spec takes this same path, so the first
legitimate replacement turns the guard red — the expiring-guard failure this
repository has already recorded of a test that asserted a register's contents.

  debt    : `SPEC/`'s withdrawal markers are prose with no check behind them
  owner   : PM + Platform Engineering
  trigger : the next PR that withdraws or supersedes a document under `SPEC/`
  the real fix : the replacement spec carries the withdrawal as its own
                 `supersedes` line, so the pointer survives the path being reused

## A caught error, recorded as one

The amendment first cited M09's cold read by its **branch** commit. That object
exists but is reachable from no tag and from `main` by no path — PR #135 was
squash-merged, so the branch commit survives only until `git gc`.
`tests/test_cited_commits_resolve.py` asserts every SHA cited under `docs/` or
`SPEC/` resolves **and** is reachable from `main` or a tag, and it went red by name.
Corrected to **`479972e`**, the merge commit on `main`, before commit.

**It fired a second time on this file.** The passage above originally quoted the bad
SHA to show what had been wrong, and `docs/pr-bodies/` is under `docs/` — so the PR
body explaining the citation error reproduced it. The literal is gone; the account
stays. That is the failure the test was written for (ADR-042's `33e5871`, SPEC/05's
scratchpad drafts) arriving twice in a document about a record that evaporated.
Recorded as errors the checks caught, not as steps that went smoothly.

## The verdict this PR corrects in itself

An earlier draft of the amendment scoped the claim down to the additive control
alone, reasoning that the wording fix's benefit *"can only ever be operator-attested
— the text that would prove it was withheld by the control being measured."*
**That was wrong, and the cause is recorded.** Two questions read the same file and
only one touches the withheld half:

- **did a case stop being refused, and was `TOPIC:entitlement-circumvention` among
  the topics that refused it?** — readable from committed records.
  `milestones/M09/goldens-run-refusals.json` carries, per case per sample,
  `decision`, `mechanism`, `assessed` (the literal topic names), `channels`, the
  guardrail id and version, and `record_id` with `record_resolved: true`, *"taken
  from the audit records fetched back out of the lake."* Its `census` publishes both
  estimators. **`brand-021` (s2)** and **`concise-022` (s3)** are identifiable by id
  **today**, both `TOPIC:entitlement-circumvention` on `channels: ["answer"]`, with
  no withheld text read.
- **was the withheld answer actually a grant?** — genuinely operator-attested. This
  is the grants file, and `F` and `G` are the quantities that read it.

**The benefit measurement costs nothing new.** `run_with_tools.py:658` writes the
`-refusals.json` sidecar for any run, so PR 4 produces it as a byproduct of a run it
was already taking — no new instrument, no extra deploy, no extra turns. **The claim
widened; the work did not.**

**What the replacement spec inherits: the additive control, the wording fix's
benefit, and its risk.** Only grant attribution is published as attested, with two
independent readings of the withheld output required on PR 2 — Legal/S&P, whose key
is on that path because an answer-policy reading bills that seat, and Security,
which owns what the guardrail blocked. That makes F1 *checkable*; it never makes it
outsider-verifiable, and the amendment says so plainly.

A verdict that narrows a milestone on a conflation is worse than one that widens it
on a measurement, because nobody re-audits a scope cut.

## Also recorded

- **A new finding: the project has two debt registers and nothing asserts they
  agree.** `milestones/M09/README.md:518` carries **36** debts out of M09; SPEC/09's
  inherited table carries **19** in. ADR-037's shape, and how four dropped debts were
  found here rather than at the close. The contract test it implies is **owed, not
  closable**: exact matching needs per-debt IDs that do not exist, minting them
  retroactively edits four closed journals, and the weaker row-count form would be
  satisfied by a catch-all row — which is what hid these four.
- **The four dropped debts recovered** with owners and triggers intact; debt 33's
  trigger (*the next PR that edits a command block in `SPEC/` or `README.md`*) fires
  at PR 1.
- **Both count readings, with the definition each used** — degraded-as-inconsistent-
  disposition (1) and degraded-as-owner-stripped (13), neither subsuming the other.
- **Two of five falsifiers fully readable and sound.** F2 is the loosening-too-far
  direction, the risk the milestone actually carries.
- **`topic-attacks-heldout.yaml` was only read, never revised-against** — measured:
  `entitlement-circumvention` byte-identical at 191 chars across all seven commits to
  `gateway-stack.ts` since `d625033`, `enforcement-probing` at 170 across all five,
  and `850728e` is +25 lines with 0 row changes. Its ordering property is intact.
- **The four corpora declaring no freeze** as one debt (Security; trigger: the next
  PR that adds a row to any of them). `probes.yaml` is excluded **on the confound** —
  ADV-006 and ADV-009 fire `PROMPT_ATTACK` independently of any topic — **not** on
  the missing freeze, so the reason survives.
- **The process finding.** The cold review's output went to a scratchpad no later
  session could read, so three of its six findings were re-derived independently and
  three arrived only when pasted in by hand. The slot has caught something material
  in every milestone of this project; **this is the first time the catch nearly did
  not land**, for a reason that has nothing to do with the review's quality. M09's
  cold read was a committed artifact (`479972e`). M09b's was not.

## What this PR does not do

**It closes no inherited debt.** Not one of the 36 M09 carried out, not the four
recovered here, not debt 18 which its own gate result demonstrates. No sweep,
candidate, wording or measurement. No clause of the withdrawn rule reused without
re-derivation from the owning ADR at line. `SPEC/09`, its claim, its falsifiers, its
*Bounded* section and M09's README row are untouched, and `SPEC/09b` is edited only
by the WITHDRAWN header. The replacement spec is **not** in this PR.

ADR: docs/adr/ADR-076-the-topic-is-reworded-under-a-rule-written-first.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

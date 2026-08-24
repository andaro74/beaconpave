# SPEC/05, four drafts, each killed by the six seats that reviewed it

`SPEC/README.md` says a spec is written **before** the milestone branch is cut,
so this lands on `main` ahead of `m05-paved-road`. It builds nothing and changes
no behaviour: one new spec, plus a README section marking where part one ends.

**The four drafts are the point.** Drafts 1, 2 and 3 were each reviewed by six
role seats — Platform Engineering, Service Team, Security, AI Quality, Data
Governance, Tool Owner — each planting and running in its own worktree with one
instruction: *do not read the code, break it and run the suite.* All six called
for a redraft every time.

| draft | blocking findings | what killed it |
|---|---|---|
| 1 | 39 | decision 4 was built by the Platform seat and measured not to block |
| 2 | 31 | the deployment binding disagrees with the verifier it enforces |
| 3 | 20 | four controls placed in files that cannot hold them |

Drafts are preserved as commits rather than deleted, the way ADR-042 preserved
its own at `33e5871`. The reasoning that was wrong is as instructive as the
reasoning that was right, and in this case more of it was wrong than right.

**Draft 4 has not been reviewed, and the spec now says so in its own header.**
There were three rounds, against drafts 1, 2 and 3. Every count in the table
above is a prior draft's. The title says "four drafts, each killed" — three were
killed; the fourth has simply not been shot at yet, and the 39 → 31 → 20 trend is
a reason to expect findings remain in it rather than a reason to expect it is
clean. Run the seats against it before any of it is built.

## The finding the spec exists for

`services/highlights-agent/pave.manifest.yaml` declares the classification G5
routes on, the tools G3 authorizes, the budgets the gate ceilings come from, and
the case floor that enforces *"no unevaluated agents"*. Measured on `07e8cd1`,
deleting each top-level key in turn and running the full suite:

```
apiVersion, template, brand, owners, runtime, attestations  ->  1795 passed each
service, classification, tools                              ->  1 failed each, all KeyError
gates                                                       ->  6 failed, four KeyError
```

Six of ten fields deletable. And changing a value rather than removing it is
green everywhere that matters: `classification: internal -> public` (1795),
`gates.eval_min_cases: 20 -> 0` (1795), dropping a declared tool (1795).

`attestations` is commented *"written by CI, verified at deploy"*. Nothing writes
it, nothing verifies it, deleting the block is 1795 passed — the ninth recorded
arrival of the shape CLAUDE.md calls worse than a missing protection, and the
first in a file a service team owns.

## Six statements of fact were measured false, and every one flattered the platform

They are quoted in the drafts rather than edited away, because a spec that reads
as though it had always been right is worth less than one that shows where it was
corrected.

- *"`sensitive` is the level G5 refuses by design"* — it is the **maximally
  permissive** declaration; `route()` refuses on the level it detects. 25/25
  allowed.
- *"`classification: public` changes nothing at runtime"* — **0/25** golden cases
  served. The one value the existing check refuses is a no-op; one it accepts is
  a total outage.
- *"four manifest ceilings are pinned"* — both halves of that duplication sit in
  files on no rule, so the true count of protected numbers is **zero**.
- *"the two transport copies are byte-identical"* — they render identical text
  from different source, which rules out the byte-parity pin the sentence implied.
- *"`^0`, `^0.1` and `^0.1.0` have different upper bounds"* — the last two are the
  same range; the real third caret rule is `^0.0.x`.
- *"the `m05` sentinel appears in nine places"* — **44**.

Two seats also corrected their **own** earlier findings downward. That mattered
as much as the escalations: over-stating an exposure leads to over-keying, which
is its own harm.

## What the review found beyond the spec's subject

Five live conditions on `main`, none introduced by this work, each found by
planting rather than reading. They are recorded here as findings 12–21 and are
**not** fixed by this PR:

- **G1.** Widening `MODEL_INVOKE_ROLE_PREFIXES` and relaxing the test that pins
  it, in one diff: **1795 passed, two-key NOT REQUIRED** — against two comments
  saying it needs the Security seat and an ADR.
- **G3.** Two lines in the Cedar generator put
  `permit(principal == Service::"attacker-svc", ...)` into the deployed policy
  set; `pave policy generate --check` exits **0**; the two-key registry is never
  touched.
- **Claim 10.** Dropping one word from `GATED_CONSEQUENCES` removes **every**
  approval interlock; `publish-highlight` becomes reachable with no approver;
  drift gate exit **0**; **zero keys collected**.
- **The harness.** `collect_ignore` in `tests/conftest.py` drops **1795 -> 1656**
  collected tests with `pave check` printing *"All checks passed!"*. Eight lines
  of `pytest_runtest_makereport` hookwrapper report **1795** — the exact honest
  count — with a G1 pin genuinely failing.
- **Finding 21, handed to Security.** A service declaring `classification: public`
  denies **11/11** probes with `mechanism: classification`, which is in
  `POLICY_MECHANISMS`, so `policy_denied` resolves true on every probe. Ten of
  eleven ask only for blocked-or-denied-and-logged. **A service that answers
  nothing scores 10/11**, against a best recorded arm of 7/10. This is ADR-038's
  shape one level out — that ADR stopped crediting a block that names no control;
  this is a denial that names no attack.

## The README now says this is a two-part project

Part one (M00a–M04) built the machinery that judges an agent; part two (M05–M10)
builds the path that creates one. The progression table carries the seam, and a
recap below it states what part one produced **and what it does not have** —
starting with the fact that no team can create an agent yet, which is this
milestone's whole subject.

It deliberately restates **no scored number**. The first attempt did, and
`test_the_readme_row_is_tied_to_the_pinned_entry_not_any_entry` went red: that
pin mutates the *first* `**15/25**` in the file, so a prose copy above the
progression table would have absorbed the mutation and left the row's own check
green. A recap that duplicated the numbers would have silently disarmed the pin
that stops a row drifting to a different history entry. The recap points at the
table instead.

One prose correction rides along: `G9`'s row in the golden-rules table named
**CODEOWNERS** as its enforcement, which is the one file ADR-013 and ADR-037
established cannot collect a second key here — in the table headed *"enforced,
never merely asserted"*. It now names `pave/twokey.py` and the required job.

## Seats

`twokey.triggered(["SPEC/05-paved-road.md", "README.md",
"docs/pr-bodies/spec-05-paved-road.md"])` returns `[]` — checked with the README
in the list, not just the spec. No attestation is required and none is claimed.

## What this PR does not do

No code, no test, no threshold, no recorded number, no probe, no ADR. `make check`
is green at **1799**, unchanged by these edits. The four above `main`'s 1795 are
`tests/test_no_account_identifiers.py`, which parametrises over every committed
file: two new files × two scanners. Verified by diffing collected ids against a
`main` worktree rather than assumed — the first draft of this paragraph guessed
a different source and was wrong. The diff is three markdown files.

The five live conditions above are fixed by **ADR-043** (PR #54), which is
separate and merges first. This PR still fixes none of them.

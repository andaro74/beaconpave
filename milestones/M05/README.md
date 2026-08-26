# M05 — The paved road, and the manifest nothing verified

**Branch:** six PRs to `main`, not one — see *What broke* · **Tag:** `m05` · **Closed:** 2026-08-26
**Spec:** `SPEC/05-paved-road.md` (draft 6) · **Claims advanced:** #1, and it is
marked **INCOMPLETE** in the twelve-claims table with two footnoted reasons

Before this milestone, `pave new` printed a sentence and exited 0, and
`pave.manifest.yaml` was a ten-field declaration that nothing verified — six of
its ten fields deletable at zero failures. The sharper form of the same fact:
a whole new `services/scaffold-probe/` — a manifest naming a brand that does not
exist, no evals, no goldens, no gateway client, no registry entry — was **1861
passed**. A service this repository had never heard of was indistinguishable from
one it had.

## What can I demo right now?

Everything below is hermetic. **Zero model calls, zero network, no AWS account.**

```bash
# 1. The paved road provides. Five files, and a banner naming what it did NOT do.
python -m pave.cli new recap-agent

# 2. Then let it fail on camera. Exactly two findings, each an onboarding step
#    the command may not take for you.
python -m pave.cli verify recap-agent        # exit 1

# 3. The premise this milestone removes: an un-onboarded service is no longer
#    invisible.
python -m pytest -q                          # 2 failed, 2077 passed

# 4. Clean tree: the committed service verifies, and the deploy gate is armed.
rm -rf services/recap-agent
python -m pave.cli verify --all              # exit 0, PASS highlights-agent
make -n core                                 # the gate runs BEFORE cdk, on one line
```

**What the viewer sees.** `new` renders five files and then, in its own output,
tells the developer the command is about to be refused and why — the registry
grant (`tool-owner` + `legal-sp`) and twenty golden cases nobody has written. It
prints the seat count it will cost, **computed from `pave/twokey.py` at the moment
it runs** rather than written into the banner: `YOUR PR WILL REQUIRE 3 SEAT
ATTESTATION(S): ai-quality, legal-sp, tool-owner`. The spec's own banner text said
five. It is three. That is why the number is computed.

Then `verify` refuses with two findings, each naming the field, what reads it, and
the edit — and prints three things it **does not** check, on every run including
green ones, because a tool that lists its limits only when it fails is a tool
whose limits are read by nobody who passed.

**The beat that matters is step 3.** `2 failed, 2077 passed` against `1861 passed`
for a service the repository had never heard of. A scaffold that went green here
would be teaching the audience that the gate means nothing.

`recap-agent` is deliberately **not** in the registry — ADR-048 removed that entry,
because it was a registry line with no service behind it. Scaffolding a name the
repository has never heard of is exactly the case this milestone exists to stop
being invisible. It is not a contradiction and it must not be "fixed".

## What's the delta vs baseline?

**There is no score delta, and that is the honest answer rather than a missing
one.** M05 changed the path that *creates* a service, not the system under test.
Re-running the golden or probe suites would have spent tokens to reproduce numbers
already recorded against an unchanged agent — the same cut M03 recorded (❂) and M04
recorded (⊕), taken for the same reason.

| Metric | m00b (control) | m05 | Mechanism |
|---|---|---|---|
| Goldens | **15/25** | not run | no model calls; the agent is unchanged |
| Adversarial | **0/10** | not run | no model calls; the probe corpus is unchanged |
| Suite | 1861 (`6af17d2`) | **2079** | +218, itemised below |
| A service nobody registered | **1861 passed** (invisible) | **2 failed** | `manifest.services()` enumerates `services/*`; fourteen refusal rows |
| Deletable manifest fields | **6 of 10** at 1861 | **0 of 10** | the verifier, with a producer per row |
| Declarable `classification` values | 3 in prose | **1**, measured | `public` serves 0/25 and is an outage; `confidential` is behaviourally identical to `internal` |

Unearned passes: **none new.** M05 recorded no eval entry, so it published no
number that could be earned or unearned. `m00b`'s four remain footnoted at §.

### Suite count at each PR boundary — measured, and the spec's list was wrong

| commit | PR | ADR | collected |
|---|---|---|---|
| `6af17d2` | — (base) | — | 1861 |
| `a14be8d` | #56 | ADR-044 | **1873** |
| `fb11e13` | #57 | ADR-048 | **1885** |
| `c6bdaf3` | #58 | ADR-045 | 1909 |
| `7f9588c` | #59/#60 | ADR-046 | 1993 |
| `f8e9943` | #61 | — (spec draft 6) | **2021** |
| `07f5dde` | #62 | ADR-047 | 2072 |
| this PR | — | ADR-049 | **2079** |

**SPEC/05's own list — "1861 → 1881 → 1909 → 1993 so far" — has 1881 wrong**, and
the error is instructive rather than clerical. 1881 is a number from *inside* PR 3's
work: *"removing the entry left the test passing at 1881 with zero pairs
constructible"* — a mutation measurement on a violating tree. The merged boundary is
**1885**, and the PR-1 boundary (1873) appears in the list at all. A number measured
on a tree that was never merged had been carried into a progression narrative as if
it were a boundary. Recorded rather than corrected in the spec, because a spec
edited to match the code stops being a pre-registration.

**A documentation-only PR moved the suite by 28**, and this is worth stating
because `COLLECTED_FLOOR` is a count. #61 changed one spec file and added three
docs files, and `1993 → 2021` decomposes exactly:
`tests/test_no_account_identifiers.py` 729 → 735 (+6: three files, two
parametrised tests each, over `git ls-files`) and
`tests/test_cited_commits_resolve.py` 39 → 61 (+22: the draft cites more commits).
**A floor that counts collected tests is partly counting committed files and cited
shas.** That is exactly the residual `COLLECTED_FLOOR`'s own docstring records —
*"deletion plus padding is not closed; a count sees arithmetic, not identity"* —
observed live rather than hypothetically, and it is why the floor is re-seated on
the tree it ships rather than left slack.

## What broke?

**The seat table described three protections that did not exist.** SPEC/05's
*"Seat sets, named"* table has rows for `Makefile`, `tests/test_budget_derivation.py`
and `docs/governance/recordings.json`. Six seats reviewed that table across five
rounds. **No PR built any of the three.** Measured at the close: deleting the
Makefile's `OBSERVATIONS` guard — the only thing stopping a bare `make adversarial`
recording a second row over another milestone's evidence — is **2072 passed, zero
keys**; reducing `check:` to a bare echo, the exact shape that file's own header
records the repository shipping for its entire life, is **2072 passed**; and
deleting `tests/test_budget_derivation.py` is **2059 passed, zero failures**,
taking with it the only tie between the committed budget ceilings and the
measurement ADR-014's amendment derived them from — while that file's own docstring
asserts in prose that `gates.budgets` is two-key. This is the fourth instance of
*stated and absent* in five milestones (ADR-035, ADR-037, ADR-043, now ADR-049),
and the first where the document doing the stating was the milestone's own spec.

**The deferral this milestone made could not have been counted.** M05 is the first
close at which `docs/governance/recordings.json` had teeth, and the milestone
**spent them**: Acts 0, 1 and 2 were all owed by M05 and all three were re-deferred
to M06. That decision is legitimate and was taken deliberately. What was not
legitimate is that it cost **2072 passed, zero keys**, and that nothing could
distinguish a first deferral from a fourth — both existing checks ask only whether
the *current* `owed_by` has closed. An act could have slid one milestone at a time
forever, each slide green, each `why` rewritten to sound like the first. That is
the same shape as `brand_tone`, whose widening was owed "to M04" and lapsed
because the obligation lived in a sentence. `deferred_from` now counts the slides,
is derived from the progression table rather than trusted where derivation is
possible, and every milestone in it must be named in the `why` — so the admission
grows with the count. The register and its check are two-key as a pair.

**Act 1's stated reason had quietly expired.** `recordings.json` carried *"Not yet
buildable; M05 builds `pave new`"* for Act 1. That became false when #62 merged,
and the file would have carried it forward unchallenged. It is replaced with the
real reason — scheduling, not capability — and the act is now the first in that file
deferred past the milestone that owns it.

**`make core`'s literal, as the spec pinned it, does not work.** SPEC/05 item 36
specifies `cd platform/infra && python -m pave.cli verify --all && cdk deploy --all`,
justified on the `pave` console script existing only after `pip install -e .`.
Measured, that justification does not hold: from `platform/infra` **neither** form
works without the install — `python -m pave.cli` there is `ModuleNotFoundError: No
module named 'pave'`, exit 1 — and after `make bootstrap` **both** do. The spec's
ordering buys nothing and costs the one case that matters: on a tree that has not
been bootstrapped it refuses with an import error dressed as a gate refusal, which
is a silent success's mirror image and just as unreadable. The verifier now runs
**before** the `cd`, where it resolves with no install at all. The `&&` premise
itself was re-measured here on GNU Make 4.3 rather than carried forward: with two
recipe lines `make -i core` prints the failure and runs the deploy anyway
(`DEPLOY-RAN`, exit 0); with `&&` on one line the deploy never runs.

**PR 2 was split out, and the milestone ships with its own headline finding open.**
G4's *"and logged"* half still credits a refusal without examining what refused.
This is stated here rather than left for a reader to notice, per the spec's own
item 29. Three decisions block it, all recorded in `SPEC/05-paved-road.md` under
*Decisions this draft does not make*: whether ADV-007's `m01`/`m04` passes become
unearned (a three-seat comparator move with superseding entries), whether the
`policy` blanket-denial case is closed by a Cedar-side positive control or declared
not closed, and whether `services/*/pave.manifest.yaml` takes Security's key when
the declared tool set intersects `GATED_CONSEQUENCES`. **The third is now live
rather than hypothetical**: PR 4b made `highlights-agent` declare
`publish-highlight`, so the complete path to granting a scaffolded service the one
human-approval-interlocked tool collects `tool-owner` and `legal-sp` on the registry
line and `ai-quality` and `tool-owner` on the manifest — and **Security on neither**.
The question is written onto the rule itself in `pave/twokey.py`.

**An accepted cost's trigger was not readable at this close.** ADR-035 amendment 9
pre-registers two triggers for `enforcement-probing` — footprint above 2 of 25, or
`blackout-009` refused by majority — both read off *the governed golden run a
milestone records*. **M05 records none.** So the watch did not run, and that is a
gap rather than a clean result; the first milestone that records a governed run
reads them. The hole with the deadline, `ATK-007`, was already closed and
discharged at ADR-035 amendment 5 and is not owed here. Recorded because
`close-milestone` step 6b exists precisely so this is checked by a list rather than
remembered — and a list that is walked and found unreadable must say so.

**Claim 1 is INCOMPLETE, and the second reason is the uncomfortable one.** There is
no deployed agent: `pave verify` runs in the repository, `attestations.manifest_signature`
is checked by nothing at deploy, and ADR-046 decision 4 records that as a stated cut.
The second reason is that *"under 30 min"* is not what the scaffold leaves behind.
The Service Team seat measured the developer's remaining authorship rather than
estimating it: ~310 content lines and ~110 asserts for the twenty cases the floor
demands, six top-level keys per case, 18 of 25 reference cases requiring memorised
catalog ids, and — the decisive number, from the pack's own README — **4 of the 25
starter cases written with negative substring bans that a correct answer trips, by
the author of the assert vocabulary.** A 16% authoring-defect rate, each defect
presenting first as a platform bug. An earlier draft called this "roughly an hour";
that was measured as too **low**. Understating it flatters the platform exactly as
drafts 1–3 did.

**One milestone, six branches.** CLAUDE.md's rule is one milestone = one branch =
one tag. M05 broke it, deliberately: both workflows fire only on pull requests
targeting `main`, so a stacked branch gets zero CI, and each PR had to be cut from
`main` after its predecessor merged. The branch the README used to name,
`m05-paved-road`, holds drafts 4–5 and a superseded ADR-045; **it was never merged
and is not what the tag `m05` marks.** The progression table now says "six PRs" and
the footnote enumerates them. A team onboarding after M05 still opens one PR — the
split is CI hygiene and is invisible to them.

**Five rounds of six seats, and the count went up before it went down.** 39
blocking findings on draft 1, 31 on draft 2, 20 on draft 3, **55 on draft 4**, 49 on
draft 5. Draft 4 relocated draft 3's controls into files that could hold them and
walked into a larger set of exposures. A falling count was never evidence of
convergence, and draft 5 proved it twice over — one of its 49 findings could not be
built at all, which is how PR 2 came to be split out.

### The deletability audit, PR 6

Every check this PR adds was deleted and the tree re-run — the per-PR discipline
SPEC/05's definition of done requires. **Seven mutations, seven caught**, which
takes the milestone's running total to **58 of 58 caught**, with the one correctly
silent (PR 4a's floor *rise*, which a ratchet must permit) and the one genuine miss
(PR 4b's half-checking test) already examined and closed.

| mutation | result |
|---|---|
| delete `test_a_deferral_is_counted_and_named` outright | pytest **silent** — 2078 passed; `pave check` **exit 1**: *"2078 passing test(s) against a floor of 2079"* |
| drop `deferred_from` from every act | **1 failed** |
| remove the register/check rule from `twokey.RULES` | **2 failed** |
| remove the `Makefile` rule | **2 failed**, and `Makefile` evaluates FREE again |
| remove the `tests/test_budget_derivation.py` rule | **2 failed** |
| revert the ADR-043 ratchet 13 → 10 | **1 failed** |
| delete the four new `ADR043_SEATS` pins | **1 failed** |

**The first row is the one worth reading.** A deleted test file is invisible to
pytest — the suite is simply smaller and still green — so `COLLECTED_FLOOR` is the
only thing that sees it, and it did, by name and with the remedy and the seat set in
the message. That is the layering working as designed rather than a gap: the floor
exists precisely because assertions cannot assert their own presence. It is also why
the floor was re-seated on the **staged** tree at the close (2072 → 2079); a floor
read off an unstaged tree is short by twice the number of files the PR adds, and this
PR adds three.

## Decisions

- **ADR-044** (#56) — the instruments that measured and were guarded by nothing.
  The file holding the *only* approver assertion, the *only* headroom check and the
  CODEOWNERS/`twokey.py` agreement check was on no rule; one diff deleted all three
  at 1859 passed, zero keys. A duplicated registry id put a phantom principal in the
  deployed policy set for two keys, neither of them Security.
- **ADR-045** (#58) — the criteria a manifest is verified against. The declarable
  vocabulary is **one value**, measured. Four of the five floors a verifier needs
  had no pin or a pin that could not fire.
- **ADR-046** (#59/#60) — the verifier, and the deploy-verification cut. Fourteen
  refusal rows as code with a producer per row, the grant bijection in both
  directions, `COLLECTED_FLOOR` enforced. Nothing had enumerated `services/*`.
- **ADR-047** (#62) — the scaffold's boundary. Five files of fourteen; the probe
  runner's omission is a governance decision, not a scope one. Two files the spec
  called *verbatim* both carried the reference's identity, including a `$id` two
  services would have collided on.
- **ADR-048** (#57) — the cross-tool negative control becomes synthetic.
  `recap-agent` was a registry line with no service behind it; removing it left the
  test passing at 1881 with zero pairs constructible.
- **ADR-049** (this PR) — three rows the seat table stated and no PR built, and a
  deferral that could not be counted.

**Still owed:** PR 2's ADR, deliberately unnumbered so nobody cites it before it
exists.

## What's next

**M06 must pay three debts this milestone deferred and one it opened.** The three
recordings — Acts 0, 1 and 2, now counted in `deferred_from` and red the moment M06
closes unrecorded. And PR 2: G4's *"and logged"* half is the repository's headline
claim, and it currently credits a refusal without examining what refused. The single
most load-bearing thing M06 must prove is that **a probe passing means the control
the probe names actually fired** — until then, `pass_when` naming Cedar is satisfied
by anything that says no.

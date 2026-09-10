# M09 PR 1/5 — the open: M09 is two milestones, the disposition ships without a deploy, and answer quality gets a row

**Zero model calls. No code, no rule, no case, no threshold, no deploy.** Documents,
two progression rows, and one obligation moved in the diff that creates the row it
now names.

## What this decides

**ADR-075**, six decisions, all written before any code:

1. **M09 as inherited is two milestones.** It carried claim 6, Act 3, a new
   guardrail line, the `entitlement-circumvention` recalibration riding that line,
   the `brand_tone` widening as a judge run, the DMA rename, the `p95_ms` rule's
   failed premise and ADR-053's two halves — **four spend events, one deploy, two
   seat rounds on two different controls**, against a cap of six that M08b spent on
   *one* spend event, one seat round and no deploy. The dimension that decides it is
   attribution, not PR count: **a red after a disposition *and* a new guardrail line
   is unattributable between the two controls**, and claim 6's whole content is that
   a reader can trace the red to the rule. That is ADR-074 decision 1's own argument
   one level in, and the M06b journal is the other half. M09 takes the disposition
   and the control that needs no deploy; **M09b** takes the guardrail line and the
   topic. The fix is one sentence in `TOOL_SYSTEM`, which is **caller-side and not in
   the deployed bundle** — checked by reading `gateway_client.py`, not assumed — so
   the whole red → fix → green loop runs against the deployment M08b measured.
2. **Answer quality is scheduled as `09c`.** ADR-074 decision 2's trigger fired on
   both halves: the browse gap on nine samples across five of seven cases, and the
   `tokens_out` failures widened from five cases to twelve, two by a single sample
   writing 307 and 308 against a tier of 300. The row serves claim 2 defensively and
   carries **no claim of the twelve** (rows 06c, 06d and 08b's precedent); what claim
   it should carry is left to its own spec.
3. **MER-AI-0001 is disposed against `highlights-agent` by a deterministic
   `ai_disclosure` assert**, never a judge axis, so the frozen instrument does not
   move inside the milestone that proves claim 6. `recap-agent` left the registry at
   ADR-048 and by ADR-023 can never be a caller.
4. **The disclosure pack is its own suite, not an arm** — `arm` already means *which
   system produced these answers* over one case set, and making it mean two things is
   what ADR-053 refused for *orphan rule*. **The goldens denominator stays 25 and is
   pinned by name**, and `disclosure-004`'s three-milestone reservation is withdrawn
   by name rather than quietly filled.
5. **The claim, five falsifiers, two bands and two rules, before any call.** Including
   *the service already complied* (F1) and *the negative case discloses* (F5); a
   prompt-delta test that prices the fix against **918 tokens of headroom before a
   call is spent**; and the `p95_ms` premise disposed by a condition a test evaluates.
6. **A cap of six: five planned and the sixth a named spare for the cold review**,
   with one pre-authorised slide (ADR-053's *no orphan rules*, the half whose term is
   undefined). *No immortal rules* does not give way. Any other slide is a finding.

## The nothing-in-place decision, priced

Renumbering would move the seven `M10` code and template sites a **fourth** time
across **three** two-key rules (`pave/floors.py` + `tests/test_floors.py` at three
seats; `pave/manifest.py` at three; `pave/scaffold.py` + `templates/agent-tools/README.md`
at four), plus `docs/governance/recordings.json` and `tests/test_demo_recordings.py`
at two more, because `milestone_is_closed` **raises** for a milestone with no
progression row and acts 4 and 5 name `M11` and `M12`. **Four rules, twelve
attestations, four seats, for a digit** — and with M09 split, surfaces would move by
two rather than one. In place costs no attestation for the numbering at all, and
M08b's debts table had already closed those seven sites *"by deciding not to act."*

**The two `M10`s are separated by name** in the README footnote and in ADR-075
decision 2: the M08 debt rows' `M10` means `09c`; the code sites' `M10` means the
surfaces milestone, unchanged and untouched.

## The one measured coupling

PR 1 adds no check, so the deletability audit is vacuous for this PR and says so.
What it does have is a coupling to prove rather than assert — that
`labels.json`'s new target is legal only because this diff creates its row:

```
delete README's `09b` row, keep re_deferred_to: "M09b"
  tests/test_calibration_owe.py::test_the_owe_is_still_within_the_milestone_it_was_deferred_to
  AssertionError: no progression row for milestone 'M09b'. An obligation deferred to
  a milestone the README does not list is deferred to nothing.
  1 failed, 3 passed
restore                                                   4 passed
```

Measured from a working copy backed up to a temp directory and restored from it,
never with `git checkout --`.

## Three claims cut for having no measurement

Recorded in ADR-075's standing-question table rather than carried as words nothing
reads: the **dashboard panel** half of the registry lookup (`dashboards/` holds a
README and nothing else; the *lookup* is kept and measured by the chain reader), the
phrase **"the regdelta loop"** (it names no artifact; everything measurable in it is
the claim or its traceability row), and **a seat round on the guardrail** (M09 moves
no guardrail).

## `make check`

```
3984 passed, 6 skipped in 139.79s
check: PASS (hermetic — no cloud, no network)
```

Nothing below row 09 renumbered. None of the seven `M10` code and template sites
touched. No case, tier, ceiling, prompt, tool spec, topic, guardrail, policy, corpus
or catalog moved. Citations: this PR cites no commit SHA, so
`tests/test_cited_commits_resolve.py` has nothing new to resolve.

## Two-key

`quality/judge/calibration/labels.json` — the `brand_tone` widening's fourth counted
re-deferral, moved in the same diff as the row it now names.

Two-Key-Disposition: ai-quality
Two-Key-Rationale: the `brand_tone:meridian-sports` widening moves from M09 to M09b
  because ADR-075 decision 1 split the milestone and decision 3 disposes MER-AI-0001
  by a deterministic `ai_disclosure` assert rather than a judge axis — so M09 adds
  cases the judge does not read, there is nothing for a wider draw to be labelled
  alongside, and M09b is the half that re-freezes the judge. The reason amendment 1
  gave is unchanged and the number follows it for the fourth time; ADR-026 amendment 4
  states the count as four rather than restating it as a first. `how_it_must_be_paid`
  is untouched, and "still one value" is still the finding it would be.

Two-Key-Disposition: security
Two-Key-Rationale: this is a date on an unpaid owe and not a payment, so nothing the
  judge scores moves in this diff — `quality/judge/frozen.json`, the rubric, every
  instrument digest and the corpus itself are byte-identical. The counterweight's
  concrete object is the target's reachability: `milestone_is_closed` raises for a
  milestone the progression table does not list, so pointing the owe at M09b in any
  earlier or later diff would have deferred it to nothing, and deleting the row was
  measured red by name above. The seat set is ADR-053's `quality/judge/` rule.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

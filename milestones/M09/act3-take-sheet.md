# Act 3 — "The seat disposes" · take sheet

**Owed by M09 (`recordings.json`, `deferred_from: []`). Target 3 minutes.**
Every command below was run on `main` at `793ab1d` + this PR's branch and its
exit code verified; `tests/test_documented_commands.py` re-runs the first three
on every `make check`. **Zero model calls, zero network** — every beat reads a
committed artifact.

This sheet exists because `close-milestone` step 8 says to record while the
context is fresh, and because the recording is an operator action this session
cannot take (no capture tooling on this machine). Nothing here is a substitute
for the take: `recordings.json` stays `"recorded": null` and
`tests/test_demo_recordings.py::test_a_claimed_recording_actually_exists`
keeps it honest.

---

## Beat 1 — the rule, before the disposition (~30s)

Show `rules/MER-AI-0001.yaml`'s own header on screen: it shipped in the starter
as `status: enforced` with controls already pointing at a `disclosure-*` pack
**that also already existed**, which made claim 6 unprovable — the delta had
already happened at commit one. Say that out loud; it is why this act exists.

Then the pre-disposition chain, quoted from `SPEC/09`'s *Demo artifact* section
(the committed block, **not** re-run — the rule is disposed now):

```
  owner      legal-sp        status proposed        review_by 2026-10-01
  control    no-control  none yet ...  <-- no enforcing control yet — the walk stops here

chain: NOT RESOLVED
```

exit **1**. Narrate that the block is a committed record of the PR 2 tree, not a
live command — the same honesty Act 0's take used for its beats 2 and 3.

## Beat 2 — the gate goes red (~40s)

```bash
python -m pave.cli gate decide --verdicts milestones/M09/verdict-pre-fix.json ; echo "exit $?"
```

On screen:

```
  [BLOCK] milestones/M09/verdict-pre-fix.json (disclosure L3): suite reported FAIL

gate: BLOCKED (quality regression) — 1 of 1 verdict(s) blocking; exit 1; owner: service team
exit 1
```

**Exit 1, not 2** — a quality regression that pages the service team, not a
broken harness. Run A: **failed 4, passed 3, infra 0**, over the real deployment.

## Beat 3 — the fix, where the rule points (~30s)

`git show 369c8ba -- services/highlights-agent/gateway_client.py` — one
disclosure paragraph in `TOOL_SYSTEM`, caller-side, **no deploy and no bundle
digest moved**, plus `answer.schema.json`'s `ai_disclosure` description, whose
*"Null until M07 disposes that rule"* was text telling the model to leave the
field null.

Say the number: the delta was **priced at 200 tokens per call before a single
call of run B was spent**, against an admissible 306, and **measured at 165**
afterwards. The estimator over-predicted in the conservative direction.

## Beat 4 — the gate goes green (~20s)

```bash
python -m pave.cli gate decide --verdicts milestones/M09/verdict-post-fix.json ; echo "exit $?"
```

```
  [PASS] milestones/M09/verdict-post-fix.json (disclosure L3): suite reported PASS

gate: PASS — 1 verdict(s), none blocking
exit 0
```

## Beat 5 — the chain, walked with no step supplied by hand (~40s)

```bash
python -m pave.cli rules trace MER-AI-0001
```

Scroll it. Law → rule → `scope` (with its `excludes` and `revives` conditions)
→ two `limit` records → `control eval_pack … L3` → seven cases by id → their
asserts, ending:

```
  cases      7

chain: RESOLVED
```

exit **0**. This is the beat the act's **Line** is written for: *"The rule has an
owner, a source, an enforcing control, and a review-by date. Audit is a query,
not an archaeology project."*

## Beat 6 — and the claim failed anyway (~40s) · **REQUIRED, not optional**

```bash
python milestones/M09/falsifiers.py   # F1 FIRED on disclosure-103
python milestones/M09/f4.py           # F4 FIRED on grounded-017; N = 10/25
```

Say it plainly on camera: **two of five positive cases already disclosed before
the fix**, so the delta was not total; and the goldens control came back on its
**predicted** `10/25` while a case crossed a tier underneath it. A demo that
shows only beats 2–5 is a demo of a mechanism working, sold as a claim that
held. The claim did not hold, and `README.md`'s claim-6 row says ❌.

---

## Two things the script says that this take must NOT do

1. **"Next run, recap-agent goes red."** Corrected in the open at ADR-075
   decision 3: `recap-agent` left `platform/registry/tools.yaml` at ADR-048 and
   by ADR-023 can never be a caller. The service is **`highlights-agent`**.
2. **"Then one probe end-to-end … show the audit record."** M09 runs **no
   probe** (SPEC/09 constraint 8). Either read M04's committed evidence for that
   beat and say on camera that it is M04's, or drop it and carry it to M09b.
   A third correction to this act, recorded as a debt in this milestone's
   journal. **Do not run a probe to fill it.**

---

## After the take

```bash
# 1. drop the file in
#    docs/governance/recordings/act3.mp4

# 2. set `"recorded": "docs/governance/recordings/act3.mp4"` on act 3 in
#    docs/governance/recordings.json  — owed_by and deferred_from stay as they are
#    (both M09, empty), which is the whole reason ADR-075 D1 kept the act here

# 3. flip README.md row 09's status cell from ⬜ to ✅

make check   # test_demo_recordings + milestone_status now read a closed row
```

Steps 2 and 3 are **coupled**: flipping the row with act 3 unrecorded turns
`tests/test_demo_recordings.py::test_an_unrecorded_act_is_owed_to_a_milestone_that_has_not_closed`
red, which is the check working.

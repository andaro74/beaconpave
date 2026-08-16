# M00a — Foundation (make the skeleton enforceable)

**Branch:** `m00a-foundation` · **Tag:** `m00a` · **Closed:** TBD
**Spec:** `SPEC/00a-foundation.md` · **Claims advanced:** none directly — it makes
claims 2 and 5 *enforceable* and every recorded number afterwards trustworthy

## What can I demo right now?

The gate blocking, three ways, none of which it could do before this milestone:

```bash
pave check --out verdict-contract.json   # 43 hermetic tests, emits a real verdict
pave gate decide --verdicts verdict-contract.json     # exit 0

# a quality regression — pages the service team
python - <<'PY'
import json; r = json.load(open('verdict-contract.json')); r['verdict'] = 'FAIL'
json.dump(r, open('verdict-fail.json', 'w'))
PY
pave gate decide --verdicts verdict-fail.json         # exit 1

# a harness failure — pages the platform, and the merge still blocks
pave gate decide --verdicts verdict-never-written.json  # exit 2

# G9, machine-checked: a baseline reset hidden in a feature PR
PR_BODY="" pave gate two-key \
  --changed services/highlights-agent/src/agent.py evals/history/goldens.json   # exit 1
```

What the viewer sees: the third command is the point. A CI step that crashes
before writing its verdict produces no file, and the gate treats that absence as
blocking rather than as nothing-to-report. Before M00a, all three of these
commands printed a stub message and exited 0.

## What's the delta vs baseline?

N/A — this milestone precedes the control. It exists so that the control's
numbers, and every number after them, mean something.

| Metric | before M00a | after M00a |
|---|---|---|
| Tests collected | 0 | 70 |
| Ways the gate can block a merge | 0 | 6 (FAIL · missing · unparseable · schema-invalid · `fail_closed: false` · INFRA) |
| Committed contracts pointing at files that exist | 3 of 10 | 10 of 10 |
| ADR references that resolve | 2 of 5 | 7 of 7 |
| Invariants enforced by machinery | 0 | G2, G7, G8, **G9** |

## What broke?

**The gate could not fail, and `make check` was green over nothing.**
`pave gate decide` was a stub that printed and exited 0, and the workflow's
`--out` flags were read by nothing, so no verdict file was ever written. The
Makefile ran `pytest -q 2>/dev/null || echo "(add tests as you build)"` against
zero tests. Every green check mark in this repo's first commit was vacuous. This
was the milestone's whole reason for existing, and it was worse than the initial
review suggested: there was no single component to fix, because the gate had no
implementation to fix.

**Two pieces of M07's demo shipped pre-placed at commit one.** `disclosure-004`
was already in `cases.yaml` tagged `author: ai-proposed, rule: MER-AI-0001`, and
`MER-AI-0001` was already `status: enforced` with controls pointing at that case.
Claim 6 is "a rule delta disposed end-to-end into eval cases" — unprovable when
the disposition and its output are both already there. Both moved to M07: the
rule now ships `proposed` with an explicit `no-control` record, and the case is
gone with a comment where it will land. A contract test
(`test_no_golden_case_is_disposed_by_an_undisposed_rule`) now makes the
pre-placement impossible to reintroduce quietly.

**The first attempt to demo the FAIL path blocked for the wrong reason.**
PowerShell's `Out-File -Encoding utf8` writes a BOM; the gate read the file as
UTF-8 and reported it as unparseable JSON — a contract failure that would have
paged the platform for a text encoding. Reading verdicts as `utf-8-sig` was the
fix. Worth recording because it is the exact class of false-INFRA that erodes
trust in a gate: block often enough for reasons that are not the team's fault and
people start looking for the bypass.

**The seat model promised something GitHub does not permit.** `branch-protection.md`
instructed the reader to create seven teams of one and tick "Require review from
Code Owners," calling it "what makes seats real." GitHub never lets a pull
request's author approve their own PR — in an org or out of one — so that setting
is satisfiable on exactly zero PRs here. Creating the org would not have fixed it;
the first draft of this milestone's plan wrongly implied it would. What fixed it
was giving up on collecting the second key as a *review* and collecting it as a
*checked attestation* instead (`pave gate two-key`, ADR-013). G9 moved from
convention to enforced, which is a better outcome than the org would have
produced.

**The two-key check silently skipped every `.github/` path on first run.**
`path.lstrip("./")` strips a character *set*, not a prefix, so
`.github/workflows/quality-gate.yml` became `github/workflows/quality-gate.yml`
and stopped matching the gate-criteria rule. Gate criteria are the single most
important two-key path — the tests caught it, which is the argument for writing
the parametrised path test before the implementation felt finished.

**Anticipated and avoided:** the eval and adversarial steps were left commented
out of the workflow rather than given placeholder PASS verdicts. A placeholder
that reports PASS for an unimplemented suite is indistinguishable from a real
pass, and would have made claims 2 and 5 false while looking green.

## Decisions

- **ADR-012** — the control is scored deterministically at M00b; the judge and
  its calibration arrive at M03 and re-score the m00b commit as an appended
  history entry. Resolves the circular dependency between M00b (needs a harness)
  and M03 (builds one), without either moving the harness earlier or letting the
  baseline be built after the platform.
- **ADR-013** — what a solo operator can actually enforce. Amends (does not
  supersede) ADR-001, whose "the operator approves wearing the relevant hat" is
  not achievable on GitHub. G9's second key becomes a machine-checked
  disposition with a mandatory written rationale; G6 is labelled as the
  convention it is. CODEOWNERS is retained for routing, pointed at `@andaro74`.
- **ADR-003, ADR-004, ADR-007** — written because the repo already cited them.
  A dangling ADR reference reads as a decision that was made and recorded, when
  it was neither.
- `rules validate` now validates against `rules/schema.json` rather than a
  duplicated field list, and an **empty registry is a failure**: a validator that
  reports success over zero files reports success after someone deletes the
  directory.

## What's next

M00b must produce the control's recorded score — and it must be recorded before
the gateway exists, or the baseline will be built to flatter the platform. The
single most load-bearing thing: the adversarial suite is expected to score
**0/10 by construction**, because G4 requires a guardrail block or a policy
denial *and* an audit record, and at M00b none of the three exist. Recording that
as anything other than zero is the failure mode this whole milestone was built to
prevent.

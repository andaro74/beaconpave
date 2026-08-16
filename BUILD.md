# BUILD.md — milestone build order

This starter is runnable now (`make check` passes, schemas validate, the gate
workflow is wired). It is a **skeleton with the contracts filled in**. What
remains is implementing each component behind its stub, in milestone order.

**Read first:** `CLAUDE.md` (rules), `SPEC/00-overview.md` (mission),
`SPEC/00b-baseline.md` (why the control exists), `CONTRIBUTING.md` (branch/tag
discipline).

## The build order

| M | Branch | Build | Exit artifact |
|---|---|---|---|
| 00b | `m00b-ungoverned-baseline` | The control: ~100-line agent, direct model call, catalog in context, no gateway/guardrails/evals. Score it against all 25 goldens and all 10 probes. | Recorded `m00b` scores; **Act 0**. Honest unearned-pass notes |
| 01 | `m01-gateway` | Gateway Lambda (classify → guardrail → invoke → meter → audit); CDK + IAM assertion test; **delete the ADR-011 allowlist entry** | Direct call fails and is logged (claim 4) |
| 02 | `m02-tool-plane` | `catalog-search` MCP tool; registry + Cedar; agent answers via tool | Unregistered tool unreachable (G3) |
| 03 | `m03-evals` | Eval harness, 25 goldens, judge + 30-case calibration, append-only history | Judge agreement published; auto-demotion test (claim 9) |
| 04 | `m04-gate` | Fail-closed gate, score-diff PR comment, all 10 probes | **Act 2:** exhibit PR blocked with a score-diff (claims 2, 5) |
| 05 | `m05-paved-road` | `pave new` + template + manifest verify at deploy | **Act 1:** under 30 min zero-to-governed (claim 1) |
| 06 | `m06-consequence` | `entitlement-check` (trajectory evals become meaningful); `publish-highlight` + Step Functions approval | Approval interlock demo (claim 10) |
| 07 | `m07-rules` | Drive `rules/MER-AI-0001.yaml` end-to-end: disposition adds disclosure cases; gate catches the violation | **Act 3:** law → red service → fix (claim 6) |
| 08 | `m08-surfaces` | Playwright + k6 emitting the verdict schema; one dashboard | Three surfaces, one schema (claims 3, 12 seed) |
| 09 | `m09-drill` | Drill scenarios (blackout sweep, captions, alarm self-test) | **Act 4:** NO-GO → delta drill → GO (claim 11) |
| 10 | `m10-selfheal` | Drift-vs-defect classifier + its tests; repair PR flow; curation panel | **Act 5:** ai-proposed repair merged (claims 7, 8, 12) |

Close each milestone with `.claude/skills/close-milestone` before starting the
next. The recordings are the deliverable.

## Implementation notes

- **M00b before M01, always.** Building the gateway first and the control later
  is the single most tempting mistake here: you will unconsciously build a
  baseline that flatters the platform. Score the control before the platform
  exists to compare against.
- **The gateway is the one component you must not simplify away.** G1, G4, and
  G5 are all enforced there. Everything else can stay a stub longer.
- **Adversarial asserts grep the audit lake.** That grep is claim 5. Build
  `data/catalog_poisoned.json` (a copy of `catalog.json` with an instruction
  hidden in a title field) for the indirect-injection probe — the most
  impressive one in the suite.
- **Trajectory evals turn on at M06**, when the second model-chosen tool exists.
  Before that, `expect_tool_before_answer` is a constant and scoring it produces
  a green number that means nothing. This is deliberate.
- **Self-heal: build the classifier and its test suite before any repair logic.**
  The classifier deciding drift-vs-defect is the safety property; the repair is
  the easy part.

## Prerequisites

Python 3.10+, Node 18+ (CDK), an AWS account with Bedrock access (Haiku), the
CDK CLI. `pip install -e .` then `make check` must pass on a fresh clone,
offline, before you build anything.

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

**None of this is needed to run the tests.** `make check` is hermetic (G8):
Python 3.10+ and `pip install -e .`, then it must pass on a fresh clone,
offline, with no AWS account, before you build anything. Two contract tests
keep that true — `tests/test_hermeticity.py` fails if the hermetic suite
imports an AWS SDK or reads `AWS_*` / `~/.aws`.

Everything below is for **M00b onward**, where the first model call happens.

- Python 3.10+, Node 18+ and the CDK CLI (M01).
- Profile **`agentpave`**, region **`us-west-2`**:

  ```bash
  export AWS_PROFILE=agentpave
  export AWS_REGION=us-west-2
  aws sts get-caller-identity     # should name the agentpave IAM user
  ```

### Bedrock model access — check it before you need it

`aws bedrock list-foundation-models` lists every model Bedrock offers,
**regardless of what this account may invoke**. Access is a separate
per-account, per-region grant. The only proof is an invoke:

```bash
aws bedrock-runtime converse \
  --model-id us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --messages '[{"role":"user","content":[{"text":"Reply with the single word: pong"}]}]' \
  --inference-config maxTokens=16 \
  --query 'output.message.content[0].text' --output text
```

Verified working 2026-08-15: returns `pong`, `stopReason: end_turn`.

### The model ID

One ID, used everywhere — services, fixtures, docs, and the command above:

```
us.anthropic.claude-haiku-4-5-20251001-v1:0
```

The US cross-region inference profile, `ACTIVE`, verified working. It is
reachable through `bedrock-runtime` from boto3 and the CLI, so it adds no
dependency to a repo whose runtime footprint is currently two libraries.

Three other forms exist and none of them is used here. `global.anthropic.…` is
also `ACTIVE` and routes more widely, but nothing about this workload needs
that. `anthropic.claude-haiku-4-5` is the Mantle client's form (Messages API on
Bedrock) and is what Anthropic recommends for new code in general — it would
pull in the `anthropic` SDK, which is a new dependency and therefore an ADR
line (CLAUDE.md), in exchange for nothing M00b needs. And the bare
`anthropic.claude-haiku-4-5-20251001-v1:0` does not work at all: Haiku 4.5
reports `inferenceTypesSupported: [INFERENCE_PROFILE]`, so there is no
on-demand throughput to invoke.

That last one fails like this, and the wording is the trap:

```
ValidationException: Invocation of model ID anthropic.claude-haiku-4-5-20251001-v1:0
with on-demand throughput isn't supported. Retry your request with the ID or ARN of
an inference profile that contains this model.
```

That is a *validation* error, not an access error. It reads like a missing
model-access grant and sends you to the Bedrock console to re-request one you
already have. Reach for the `us.` prefix first.

### Never commit an account identifier

This repo is public. `tests/test_no_account_identifiers.py` fails on any
12-digit account ID or account-qualified ARN in a committed file — including
journals and captured command output. Redact to `<ACCOUNT_ID>`. Note that
`aws sts get-caller-identity` prints one; do not paste its output verbatim.

# Architecture Decision Records

Every deliberate scope cut is recorded here, and every one ends with the same
sentence: *"At scale, replace with X; the interface already matches."* That
sentence is what makes this miniature production-**grade** rather than a toy.

Superseded ADRs are **marked, never deleted** — the reasoning that was wrong is
as instructive as the reasoning that was right. The same holds inside an ADR
amended in place: the superseded sentence stays where it was, marked, with the
amendment below it. An ADR that quietly reads as though it had always been right
is worth less than one that shows where it was corrected.

| ADR | Decision / cut | Scale-up path |
|---|---|---|
| ADR-001 | Role subagents + one operator per seat *(amended by 013)* | Real teams on the same CODEOWNERS entries |
| ADR-002 | Single AWS account / single stage | Organizations + Control Tower; per-BU accounts |
| ADR-003 | Lambda agent runtime | Bedrock AgentCore Runtime (session isolation) |
| ADR-004 | In-process Cedar evaluation | Amazon Verified Permissions |
| ADR-005 | Committed-JSON baselines + append-only history files | DynamoDB baseline store |
| ADR-006 | Shadow-eval stands in for canary infra | CodeDeploy weighted canaries + auto-rollback |
| ADR-007 | Webhook "pager" | PagerDuty / Opsgenie |
| ADR-008 | Public HLS test stream + fictional catalog | Dark-channel encoder path + real catalog service |
| ADR-009 | ~10 probes, ~25 goldens | Security-owned corpus + per-brand eval registries |
| ADR-010 | Single CloudWatch dashboard | Dashboards-as-code per surface + exec rollup |
| ADR-011 | Baseline quarantined as the only direct-model path | Deleted at M01 — visible in that diff |
| ADR-012 | Control scored deterministically; judge arrives at M03 *(amended in place 2026-08-15: M00b builds the runner)* | Sequencing, not a cut — the discipline is the same at scale |
| ADR-013 | G9 enforced as a checked attestation, not a review | Teams + code-owner review; same path list, check retained as a filter |

Written out in full: **001, 003, 004, 007, 009, 011, 012, 013**. The rest are reserved rows
you fill as you build each component — the table itself is the scaling story.

003, 004, and 007 were written at M00a because the repo already cited them:
`pave.manifest.yaml` names ADR-003 and ADR-007, and the repository map names
ADR-004. A dangling ADR reference is worse than a missing one — it reads as a
decision that was made and recorded, when it was neither.

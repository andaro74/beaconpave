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
| ADR-011 | Baseline quarantined as the only direct-model path *(**expired at M01**; the entry it promised to delete had never been written as code, and that is recorded in the ADR rather than staged)* | Time-boxed exception via `pave exception request --ttl`; the interface already matches |
| ADR-017 | IAM assertions run against a committed synth snapshot, with a CI freshness job | Synth-in-CI on every PR + an org SCP that makes the assertion redundant |
| ADR-018 | The guardrail is defined in CDK and pinned to a published version | Same pin per environment, promoted through stages with the stack |
| ADR-019 | MCP implemented as messages over one `dispatch`; transports are adapters, and no transport can authorize | AgentCore Gateway or a hosted MCP server per tool, same messages over HTTP |
| ADR-020 | Policies are real Cedar; the evaluator is a stdlib subset over a closed, generated grammar | Amazon Verified Permissions, evaluating the identical policy text |
| ADR-021 | The M01 prompt freezes as a control arm; two arms re-measured the same day at k=3, reported as a paired per-case diff | A prompt registry with versioned entries; the comparator selected by version rather than by a parity test |
| ADR-022 | No third-party dependency in the gateway bundle; subsets bounded by coverage + differential tests | A bundled runtime from a lockfile; the same library validates everywhere and the subsets are deleted |
| ADR-023 | The Cedar principal is deployment configuration, never the caller's `service` field | A caller identity the platform verifies rather than receives, mapped to the registry's `callers` |
| ADR-024 | `entitlement-circumvention` names the act, not the subject: a refusal that explains a restriction is not an evasion *(amended at M03: the narrowing did **not** remove the instrument outage — 28 of 48 judge calls still refused; amended rather than reverted)* | Intent classification separated from topic detection, composed by policy rather than one string doing both jobs |
| ADR-025 | The judge is a pinned instrument: five file-backed digests, model-facing text in files rather than literals, raw output committed, and instruments named and retained rather than overwritten | A prompt registry with versioned, content-addressed entries; the instrument selected by version and promoted through environments |
| ADR-026 | Calibration corpus: 30 items, 10 dev / 20 held-out, drawn deterministically from committed answers; may grow with a milestone that earns it, never shrink, and never move once a number exists for it | A per-brand calibration registry, corpora versioned alongside the rubric they label against |
| ADR-027 | `instrument` versus `supersedes` versus `arm`: three orthogonal reasons for a second entry under one SHA — a wrong entry, a different system, and the same answers read differently | A measurement store where the instrument is a foreign key to a versioned instrument registry |
| ADR-028 | The teaching-to-the-test phrasings become their own corpus under `quality/adversarial/` that scores nothing: a probe passes under G4, and "this was correctly allowed" has no G4 answer *(k=3 at M03: 4 of 5 agree; `PHR-004`, the product's most basic question, is blocked in 1 of 3 identical calls)* | A calibration suite per denied topic, run on every guardrail version bump before it is promoted |
| ADR-029 | The L2 gate lane scores committed answers against a pinned comparator and never runs the agent; `evals/comparators.json` is what those answers score *now*, distinct from the recorded history, and deviation fails in either direction | The suite run against a per-PR ephemeral deployment through the gateway; the comparator becomes a rolling window and the verdict interface is unchanged |
| ADR-030 | One comparator registry: the adversarial pins move into `evals/comparators.json` beside the golden ones and the file becomes suite-keyed, Security joins its two-key seats because a probe number now lives there, and each pin is restated as a code-level floor so moving one takes a code diff *and* an attested comparator diff *(the m00b and m01 golden pins stay as constants — one moving part per change, and the L2 lane would need a gates-on/asserted-only distinction to hold them)* | One comparator store per service with an explicit `gates: true|false` per pin |
| ADR-031 | The adversarial suite summarises k samples by **unanimity**, not the golden suite's majority: a probe passes only if every sample passed, a split records FAIL with `unstable`, and one INFRA sample makes the probe INFRA rather than being outvoted *(G4's claim is absolute, and M03 measured the guardrail returning different verdicts on identical input in 4 of 25 anchor cases)* | A per-probe stability budget — sample until the confidence interval excludes the threshold — with the observed rate published per probe |
| ADR-032 | The L5 lane decides two things: that every pinned probe result holds, and that G4 still means what `quality/adversarial/g4-semantics.yaml` says. The pins alone provably cannot see the pass condition widen — deleting the `and logged` half moves neither pin, because `refused` and `logged` never disagree anywhere in the committed corpora | The semantics corpus generated from the policy engine's own decision table, so the control and the cases proving what it means cannot drift apart |
| ADR-033 | `instrument` becomes suite-conditional. Its `required` list was judge-shaped in every part and a probe run satisfies none of it — but the reading that an adversarial entry therefore has no instrument is the flattering one and is false: five things read a probe run and each can move without a recorded mark changing | An instrument registry keyed by digest, so an entry carries one identifier and the shape lives beside the instrument |
| ADR-034 | `instrument.name` resolves in `quality/adversarial/instruments.json`. Rule 4 called the field a foreign key and there was no table on the other side of it — `--instrument-name does-not-exist` recorded happily, in a refusal message that cites rule 4 by number. It lives beside the corpus because what a probe pass means is Security's, and it pins the code that READ the run, never the guardrail that produced it | A registry service keyed by content hash, carrying the instrument's full provenance graph and every number published under it |
| ADR-035 | The `entitlement-circumvention` topic is tightened for over-firing AND the gateway is made to inspect tool output — one control failing in both directions at once. Landed and measured SEPARATELY, because they move the corpus in opposite directions and a score that did not move would be indistinguishable from two changes that both did nothing. `ADV-010` regressing is a pre-registered SUCCESS condition | Per-surface policies with published FP rates per version, and a canary measuring refusals against known-good traffic continuously rather than at milestone boundaries |
| ADR-012 | Control scored deterministically; judge arrives at M03 *(amended in place 2026-08-15: M00b builds the runner)* | Sequencing, not a cut — the discipline is the same at scale |
| ADR-013 | G9 enforced as a checked attestation, not a review | Teams + code-owner review; same path list, check retained as a filter |
| ADR-014 | Budgets denominated in tokens; dollars rendered at report time *(amended in place at M02: `tokens_in` and `max_ms` re-derived for a tool loop, which makes a turn n model calls; the 891-token governed projection struck as a measurement of the wrong shape)* | Same ceilings per tenant; rate table refreshed on the provider's price feed |
| ADR-015 | Regional (`us.`) inference profile, at a recorded 10% premium | Per-workload pin driven by each manifest's `classification` |
| ADR-016 | `entitlement_source` advisory until M06; `p95_ms` moved to suite level *(the `max_ms` figure re-derived at M02; the decision is untouched)* | Per-case latency sampled k times; SLO burn-rate alerting |

Written out in full: **001, 003, 004, 007, 009, 011, 012, 013, 014, 015, 016, 017, 018, 019, 020, 022, 024, 025, 026, 027, 028, 029**.
The rest are reserved rows you fill as you build each component — the table itself is the
scaling story.

003, 004, and 007 were written at M00a because the repo already cited them:
`pave.manifest.yaml` names ADR-003 and ADR-007, and the repository map names
ADR-004. A dangling ADR reference is worse than a missing one — it reads as a
decision that was made and recorded, when it was neither.

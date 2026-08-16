# beaconpave

A miniature, production-shaped **quality platform for agentic AI and streaming
services at a media company**, built milestone-by-milestone with Claude Code.
Every milestone is branched, tagged, scored against a fixed golden set and a
fixed adversarial suite, and journaled — **the repo history IS the demo**.

The fictional company is **Meridian Media Group**, launching **Beacon**, a DTC
streaming service with two brands: **Meridian News** (attribution and
AI-disclosure rules) and **Meridian Sports** (entitlement and regional blackout
rules). Those two brands miniaturize the two hardest compliance problems in
media. Everything is fictional — catalog, markets, regulations, company. Fork it
and rename it for yours.

> **The paved road provides. The quality gate decides. The seat disposes.
> The leakage number keeps everyone honest.**

## Progression

| M | Milestone | Branch | Tag | Goldens | Adversarial | Status |
|---|---|---|---|---|---|---|
| 00a | Foundation: a gate that can fail | `m00a-foundation` | `m00a` | n/a | n/a | ⬜ |
| 00b | Ungoverned agent (**the control**) | `m00b-ungoverned-baseline` | `m00b` | –/25 † | –/10 | ⬜ |
| 01 | Gateway + audit lake + IAM assertions | `m01-gateway` | `m01` | – | – | ⬜ |
| 02 | Tool registry + Cedar + catalog-search | `m02-tool-plane` | `m02` | – | – | ⬜ |
| 03 | Eval harness + judge calibration | `m03-evals` | `m03` | –/25 | – | ⬜ |
| 04 | Fail-closed gate + adversarial suite | `m04-gate` | `m04` | –/25 | –/10 | ⬜ |
| 05 | `pave new` scaffold + manifest verify | `m05-paved-road` | `m05` | – | – | ⬜ |
| 06 | 2nd tool + consequence interlock | `m06-consequence` | `m06` | –/25 | –/10 | ⬜ |
| 07 | Rules registry + regdelta loop | `m07-rules` | `m07` | –/25 | – | ⬜ |
| 08 | Playwright + k6 on one verdict schema | `m08-surfaces` | `m08` | – | – | ⬜ |
| 09 | Game-day drill + go/no-go artifact | `m09-drill` | `m09` | – | – | ⬜ |
| 10 | Self-heal classifier + curation panel | `m10-selfheal` | `m10` | –/25 | –/10 | ⬜ |

Fill each row at milestone close (see `.claude/skills/close-milestone`).

† The `m00b` golden score is **deterministic asserts only** — schema conformance,
`must_mention` / `must_not_claim`, groundedness via `cited_titles`, budgets. The
judge does not exist until M03, and a judge with no published agreement number
cannot produce a blocking score (G9). M03 re-scores the `m00b` commit and appends
a superseding history entry; both numbers stay in the table. Do not compare a
judged score against an unjudged one and read the difference as improvement —
see ADR-012.

**The intended arc:** the ungoverned baseline leaks blackout claims and folds to
prompt injection → the gateway and guardrails stop the leaks → the eval harness
makes quality measurable → the gate makes regressions unmergeable → the rules
registry makes compliance changes propagate → the drill makes live events
rehearsable. Evidence lives in `milestones/M*/` and `evals/history/`.

**On baseline honesty:** if the ungoverned control passes an adversarial probe,
the probe is too weak — record it as-run, mark the pass **unearned**, and open a
tightening for the Security seat. A control that looks good makes every later
milestone unfalsifiable. See `SPEC/00b-baseline.md`.

## The twelve claims

This repo exists to prove twelve falsifiable claims about quality platforms.
Anything that doesn't serve one is out of scope.

| # | Claim | Proof artifact | M |
|---|---|---|---|
| 1 | One command → governed service | `pave new`: repo → deployed agent under 30 min | 05 |
| 2 | Gates fail closed and teach | A red PR in history with a score-diff comment | 04 |
| 3 | One verdict schema, many runners | Agent evals + Playwright + k6 emit identical JSON | 08 |
| 4 | No direct model access | IAM assertion tests + a failed direct call, logged | 01 |
| 5 | Adversarial pass = blocked-and-logged | 10 probes; the assert greps the audit lake | 04 |
| 6 | Rules have owners and dispositions | A rule delta disposed end-to-end into eval cases | 07 |
| 7 | AI proposes, a human disposes, rates published | An `ai-proposed` PR merged; curation panel | 10 |
| 8 | Self-heal classifies before it repairs | Classifier test suite + one drift-repair PR | 10 |
| 9 | Judges are calibrated or advisory | Published agreement number; auto-demotion test | 03 |
| 10 | Consequence classes gate real actions | `publish_highlight` waits on human approval | 06 |
| 11 | Readiness drills produce go/no-go artifacts | NO-GO → fix → delta drill → GO | 09 |
| 12 | Defect leakage is counted honestly | Increments from rollbacks, never gate failures | 10 |

## Governance (separation of roles, from the start)

The org chart is encoded in the repo. `.github/CODEOWNERS` maps files to role
seats — Platform Engineering owns the road and the gate *mechanism*, AI Quality
owns thresholds and judges, Security owns the adversarial corpus and guardrails,
Legal/S&P owns `rules/`, Data Governance owns classification, Tool Owners own
schemas and consequence classes, Service Teams own their own prompts — branch
protection makes those reviews mandatory, the quality-gate workflow blocks any
PR that regresses the golden set or the adversarial suite, and **role subagents
in `.claude/agents/` run first-pass review from each seat** before a human
disposes.

Start here: `docs/governance/ROLES.md` · demo script:
`docs/governance/demo-script.md` · setup: `docs/governance/branch-protection.md`

## Golden rules (invariants — enforced, never merely asserted)

| # | Rule | Enforced by |
|---|---|---|
| G1 | Every model call transits the gateway; no service holds direct model-invoke permissions | IAM assertion tests; org SCP at scale |
| G2 | Gates fail closed; an errored gate blocks, never skips | Gate exit-code contract; branch protection |
| G3 | Every tool call is authorized against the registry via policy | Cedar; unregistered tools unreachable |
| G4 | Adversarial "pass" = *guardrail blocked or policy denied, and logged* — never *the model resisted* | Probe assertion semantics |
| G5 | Classification routes model access; `sensitive` is refused by design | Gateway classification router |
| G6 | AI proposes; a human seat disposes; curation rates published | `ai-proposed` PR flow + CODEOWNERS |
| G7 | Every rule has an owner, source, enforcing control, and review-by date | Rules schema validated in CI |
| G8 | Local checks are hermetic: `make check` needs no cloud, no network | Committed fixtures and catalog |
| G9 | Whoever feels a control's pain never solely controls its strength | Two-key rule via CODEOWNERS on thresholds |
| G10 | Nothing bills while idle | Serverless-only infrastructure |

## Traceability rules

- **One milestone = one branch (`mNN-<slug>`) = one tag at close (`mNN`).**
  Branch and tag must NEVER share a name: git cannot disambiguate
  `refs/heads/x` from `refs/tags/x`, so `git push -u origin x` fails with
  "src refspec matches more than one" and `git checkout x` is ambiguous.
- `python evals/run_evals.py --record` after every green run you care about —
  history is append-only JSON keyed by git SHA + suite.
- Consequential choices get an ADR (`docs/adr/`). Superseded ADRs are marked,
  never deleted.
- `milestones/MNN/README.md` answers: **what can I demo right now, what's the
  delta vs baseline, what broke.**
- Deliberately-red demo PRs are labeled `exhibit` and closed unmerged — `main`
  is always green. A gate that can be merged past is not a gate.

## Repository map

```
SPEC/                  the mission and per-milestone specs (PM seat owns)
CLAUDE.md              rules for Claude Code — read before any change
pave/                  CLI: new, check, evals, adversarial, drill, selfheal
templates/agent-tools/ the scaffold every service is born from
platform/gateway/      the single LLM control point: classify -> guardrail ->
                       invoke -> meter -> audit
platform/registry/     tools.yaml — owner, semver, schemas, consequence class
platform/policy/       Cedar policies (in-process; ADR-004)
services/              scaffolded agents (highlights-agent is the reference)
tools/                 MCP tools incl. publish-highlight (approval interlock)
quality/verdicts/      THE verdict schema — the unifying contract
quality/adversarial/   10 probes; pass = blocked or denied, AND logged
quality/judge/         rubric + calibration set; published or demoted
quality/selfheal/      drift-vs-defect classifier (with its own tests)
rules/                 rules registry: owner, source, disposition, review-by
surfaces/web-player/   Playwright + k6 on the same verdict schema
drill/                 game-day readiness scenarios -> go/no-go artifact
evals/history/         append-only scores keyed by git SHA
milestones/MNN/        journals: what I can demo, delta, what broke
loadtest/              k6 profiles for spike-shape soak
docs/governance/       ROLES, demo script, branch-protection setup
docs/adr/              every scope cut, with its scale-up path
.claude/agents/        role subagents: first-pass review from each seat
.claude/skills/        close-milestone ritual
```

## Quick start

```bash
make check          # hermetic: unit + contract + rules validation, no cloud
make bootstrap      # one-time: CDK bootstrap, tool deps
make core           # deploy gateway, tools, agent, dashboard
make evals          # definition of done
make adversarial    # the security seat's corpus, fetched fresh
pave new my-agent --brand meridian-sports --classification internal
pave drill --event jefferson-derby --tier 3
```

See `SPEC/00-overview.md` (mission), `SPEC/00b-baseline.md` (the control),
`CLAUDE.md` (rules), `BUILD.md` (milestone build order).

## Cost posture

Serverless only. Target: under $5/month idle, under $2 per full demo run.
Per-case cost budgets are part of the gate — a cost regression blocks like a
quality regression.

## Scaling this up

Every deliberate scope cut is an ADR in `docs/adr/`, and each ends with the same
sentence: *"At scale, replace with X; the interface already matches."* That is
what makes this miniature production-**grade** rather than a toy.

## License

MIT. Fictional entities throughout; no affiliation with any real media company.

# Roles and Seats

The org chart is encoded in the repo. A seat is not a job title — it is a set of
paths a reviewer must approve, an authority no one else holds, and a subagent
that runs first-pass review from that perspective.

One operator can play every seat (ADR-001). The enforcement mechanics are
identical to a real organization: change team membership, not enforcement logic.

## The eight seats

### 1. Platform Engineering
**Owns:** `platform/`, `templates/`, `pave/`, `.github/`, `CLAUDE.md`, `docs/adr/`
**Authority:** the gate *mechanism*, the scaffold, the gateway, infra.
**Explicitly does NOT own:** gate *thresholds*. Separating "how the gate works"
from "what it demands" prevents the team that gets paged from quietly loosening
quality bars.
**Subagent:** `.claude/agents/platform-eng.md`

### 2. AI Quality
**Owns:** `quality/judge/`, `quality/verdicts/`, `services/**/evals/`, thresholds
in `gate.yml`, `evals/history/` semantics
**Authority:** golden datasets, judge prompts and calibration, scoring
thresholds, **baseline resets**, headroom policy, flake policy.
**Why baseline resets are here:** "update the baseline" is the standard way eval
gates get neutered. It is a decision requiring this seat, never a cleanup.
**Subagent:** `.claude/agents/ai-quality.md`

### 3. Security / Red Team
**Owns:** `quality/adversarial/`, `platform/gateway/guardrail_config.yaml`
**Authority:** the probe corpus, guardrail configuration, and **sole authority to
downgrade a probe from blocking to advisory** — which requires an ADR.
**Invariant they defend:** G4. A probe passes when something *blocked*, never
when the model merely declined.
**Subagent:** `.claude/agents/security.md`

### 4. Legal / Standards & Practices
**Owns:** `rules/`
**Authority:** compliance rules, denied topics, brand eval packs, disclosure
requirements; **disposition of external-rule deltas** (the regdelta loop).
**Obligation:** every rule they create must compile to an executable control —
an eval pack, a guardrail, a Cedar policy, or a classification change. A memo is
not a control.
**Subagent:** `.claude/agents/legal-sp.md`

### 5. Data Governance
**Owns:** classification taxonomy, gateway routing config, test-data privacy
**Authority:** which classification may reach which model; PII redaction rules;
the rule that `sensitive` is refused by design (G5).
**Subagent:** `.claude/agents/data-governance.md`

### 6. Tool Owners (one per tool)
**Owns:** `platform/registry/tools.yaml` (per entry), `tools/<tool>/`
**Authority:** tool schema, semver, **consequence class**, caller allowlist.
A consequence class above `read` additionally requires seat 4's sign-off,
because raising an action's blast radius is a compliance decision.
**Subagent:** `.claude/agents/tool-owner.md`

### 7. Service Teams
**Owns:** `services/<service>/src/`, their service-level golden cases
**Authority:** their prompts and business logic. They may **add** eval cases
freely; **removing or weakening a company-level case requires seat 2**.
**Cannot:** remove inherited required checks (org-required workflows + a
conformance check make this structurally impossible, not merely forbidden).
**Subagent:** `.claude/agents/service-team.md`

### 8. Runtime Approvers (a role, not a person)
**Owns:** approval decisions on high-consequence actions in production
**Authority:** approve/deny `publish`/`delete`-class agent actions via the Step
Functions interlock. Decisions land in the audit lake beside the model call that
proposed them.
**Why a role:** paging a named individual does not survive vacations; the
on-call editorial approver is whoever holds the rotation.

## Two-key rules (G9)

Whoever feels a control's pain never solely controls its strength.

| Change | Keys required |
|---|---|
| Eval threshold | Owning seat + AI Quality |
| Baseline reset | Service team + AI Quality |
| Probe downgrade to advisory | Security alone, **plus an ADR** |
| Consequence class increase | Tool owner + Legal/S&P |
| Any invariant (G1–G10) change | Platform Eng + the seat that defends it |

**How the second key is collected here.** CODEOWNERS cannot enforce this on a
one-operator repo — GitHub does not let a PR's author approve their own PR, so
the second key is unobtainable rather than merely inconvenient (ADR-013). It is
therefore recorded as an attestation and verified by the required `two-key`
check: a PR touching any path above must carry the owning seats' dispositions and
a substantive rationale in its body.

```
Two-Key-Disposition: ai-quality
Two-Key-Rationale: M03 published a judge agreement of 0.91, which supports
  raising the groundedness floor to 0.8; headroom stays at three cases
```

The rules live in `pave/twokey.py` and mirror the table above. **Editing them is
itself two-key** — the first move against G9 cannot be to delete G9's
enforcement. At scale, the teams come back, code-owner review turns on, and this
check is retained as a pre-review filter that makes reviewers state reasoning.

## Role subagents: first-pass review, never approval

`.claude/agents/` holds one subagent per seat. Each reads the diff from its
seat's perspective and posts findings. They exist because a solo operator (or a
tired reviewer) reads a diff once, from one angle; a subagent reads it from the
angle its seat is responsible for and asks that seat's questions.

**They do not approve.** Per G6, AI proposes and a human seat disposes. Subagent
output is advisory input to the human reviewer, recorded in the PR. The
acceptance rate of subagent findings is tracked like any other curation rate —
if a seat's subagent is ignored 95% of the time, it is miscalibrated and should
be fixed or retired, not left as decoration.

## Exceptions

`pave exception request --rule <id> --ttl 30d` drafts an ADR, routes it to the
owning seat (SLA: 2 business days), and — if granted — records a
dashboard-visible, **auto-expiring** exception. Cheap to request, impossible to
hide, never permanent by default. Paved roads without off-ramps breed dirt
roads.

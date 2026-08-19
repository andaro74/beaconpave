# policy

Cedar policies for the tool plane (G3), **generated from the registry** — ADR-004,
ADR-020.

## Where the files are

| | |
|---|---|
| Source | `platform/registry/tools.yaml` — the `callers` field and the consequence class |
| Generator + evaluator | `platform/gateway/core/cedar.py` |
| Generated set | `platform/gateway/policy/tools.cedar` |
| Regenerate | `python -m pave.cli policy generate` |
| Drift check | `python -m pave.cli policy generate --check`, and `tests/test_cedar_policy.py` inside `make check` |

**The generated set lives in the gateway bundle rather than here, and that is a
deployment fact rather than an organisational one.** `platform/gateway/` is what
`lambda.Code.fromAsset` ships, the gateway is the only evaluator, and a copy in
this directory would be a second artifact that could disagree with the deployed
one — which is the failure ADR-017 spends a page on. One invariant, one file.

**The generator and the evaluator are one module** because they share a grammar,
and a generator and a parser that disagree about it is how an authorization layer
starts permitting something nobody wrote down.

## What the policies say

- A `permit` per registry `caller`, so an uninvited service is denied by the
  absence of a permit and an unregistered tool by having no policies at all.
- A `forbid ... unless { context.approval_granted }` for every tool whose
  consequence class is `publish` or above. A forbid rather than a withheld permit,
  because Cedar resolves an explicit forbid over every permit — so adding a caller
  to the registry cannot route around an interlock.

Nothing grants a default. At M02 no approval interlock exists, so publish-class
tools are unreachable: a tool whose declared approver is not deployed must be
unreachable, not reachable without one.

Owning seat: Platform Engineering (mechanism) · Tool Owner (the registry the
policies are generated from).

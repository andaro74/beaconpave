# Exhibit — an unregistered tool is blocked by the gate

**PR [#19](https://github.com/andaro74/beaconpave/pull/19)** · branch
`m02-exhibit-unregistered-tool` (preserved) · labelled `exhibit` · **closed
unmerged**

G3's *static* proof artifact for M02. Recorded here rather than only in the PR
description, because a PR body cannot be diffed and an artifact that lives only in
a web form is an artifact nobody can check later.

## What it does

One line added to `services/highlights-agent/pave.manifest.yaml`:

```yaml
  - id: catalog-purge@^0            # EXHIBIT: not in platform/registry/tools.yaml
```

`catalog-purge` is in no registry. Nothing else in the branch changes.

## What happens

```
FAILED tests/test_contracts.py::test_manifest_tools_are_all_registered
AssertionError: manifest names unregistered tool 'catalog-purge'
assert 'catalog-purge' in {'catalog-search', 'entitlement-check', 'publish-highlight'}

1 failed, 544 passed
error: check failed: pytest failed (exit 1)
```

CI: `gate` **FAILURE**, `two-key` SUCCESS. `pave check` exits **1**.

Both halves of that matter. The gate fails, and it fails for the *invariant* rather
than for a governance-process reason — a red PR whose two-key check is also red
would not distinguish the two.

## Why it fails at check time rather than at deploy time

A service cannot ship naming a tool nobody registered. Cedar policies are
generated from `platform/registry/tools.yaml` (ADR-004), so an unregistered tool
has no `permit` and no `forbid`: the plane would deny it at runtime, and nobody
reviewing the registry would ever have seen it proposed. Catching it in `pave
check` is what turns that from a runtime surprise into a five-minute conversation
on a diff.

## Measured as a delta, not as an absolute

The detector **passes on `main` before the plant** and fails after it, and the
branch contains exactly one substantive line.

That ordering is deliberate and it is the correction PR #13 forced on this repo:
a control asserting "the planted thing is the only offender" quietly assumes the
fixture was clean, and therefore proves the fixture rather than the detector. M01's
exhibit broke that assumption and its negative controls then reported that the
assertion had *not* caught what it should — the opposite of true. What is under
test here is the detection.

The branch is cut from `main`, not from `m02-tool-plane`. Workflows fire only on
PRs targeting `main`, so a stacked exhibit would have received no CI at all and the
red result would have been a claim rather than a check.

## The other half of the claim

This is the static artifact. The **runtime** half is
`milestones/M02/g3-runtime-denial.json`: the deployed gateway, asked to invoke
`catalog-purge`, denies it with `mechanism: policy` and writes an audit record
that is fetched back **out of the lake** rather than read off the response.

```json
{"decision": "denied", "mechanism": "policy", "executed": false,
 "reasons": ["no policy permits highlights-agent to invoke catalog-purge — an
              unregistered or uninvited caller is denied by default (G3)"]}
```

Two artifacts, because they are two different guarantees. A gate that blocks a
manifest does nothing about a caller who never reads a manifest; a plane that
denies a call does nothing to stop a service shipping with a tool nobody reviewed.
SPEC/02 asks for both by name, and the weaker one is not allowed to hide behind
the stronger.

## What it does not prove

It does not prove the tool function is unreachable by a caller who bypasses the
gateway entirely. That is an IAM property, asserted at synth time in
`tests/test_tool_plane_iam.py`, and the Security seat's review found those
assertions blind to four shapes CDK itself emits — all four now planted as
negative controls. The direct-tool-invocation *probe* against the deployed
function is still owed and named for M04: an assertion about a template and an
attempt against a live function are different evidence.

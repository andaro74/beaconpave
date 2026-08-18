"""
Reading a synthesized CloudFormation template, for the assertions G1 rests on.

**Why a committed snapshot instead of synthesizing in the test.** `cdk synth`
needs Node and an `npm ci`; `make check` must pass offline on a fresh clone with
no AWS account (G8). Writing the assertion twice — once in TypeScript for CI and
once in Python for the hermetic suite — would give one invariant two
implementations that can disagree, and the one that disagrees quietly is the one
nobody reads. So there is a single assertion, in Python, over a committed
snapshot, plus a CI job that re-synthesizes and diffs. That job is the only thing
standing between the snapshot and a fiction, which is why it blocks (ADR-017).

`normalize` exists so the diff means something. An asset hash changes whenever a
byte of Lambda source changes, so an un-normalized snapshot would churn on every
edit and train everyone to re-record it without reading it — and a snapshot
nobody reads is how an IAM grant gets in. What is left after normalizing is the
structure and the policy, which is what the assertion is about.

The rule it applies: **a snapshot that only reproduces on the machine that
recorded it is not a snapshot.** The first CI run of the freshness job proved
that the hard way — it reported drift against a snapshot that was byte-identical
when re-synthesized locally. The culprit was `AWS::CDK::Metadata`, whose
`Analytics` property is a deflate-compressed blob of library telemetry: it moves
with the construct-library version and is not guaranteed byte-stable across zlib
builds, so Windows and Linux can disagree on it for identical input. It carries
nothing about IAM, so it is dropped rather than compared.

Hermetic: pure JSON, no SDK, no network.
Owning seat: Platform Engineering.
"""
from __future__ import annotations

import json
import pathlib
import re
from collections.abc import Iterator
from typing import Any

#: A CDK asset hash: 64 hex characters, sometimes with a `.zip` suffix.
ASSET_HASH = re.compile(r"\b[0-9a-f]{64}\b")
ASSET_PLACEHOLDER = "<ASSET_HASH>"

#: Actions that reach a model. `Converse` authorizes against `bedrock:InvokeModel`
#: today, so listing both is redundant — deliberately. A list that is exactly
#: minimal stops being correct the moment the provider adds an action, and this
#: is the one list in the repo where being wrong is silent.
MODEL_INVOKE_ACTIONS = frozenset({
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "bedrock:Converse",
    "bedrock:ConverseStream",
})

#: The construct-id prefix of the only role permitted to hold a model-invoke
#: grant.
#:
#: **This is the allowlist, and it has exactly one entry on purpose.** ADR-011
#: expired at M01: the baseline's exception is gone and nothing replaced it. A
#: second entry here is how the exception comes back — not as an ADR anybody
#: reviews, but as a one-line change that makes a failing test pass. So a test
#: pins the length of this tuple and names ADR-011 when it fails. If you are
#: adding an entry, you are writing an exception, and it needs an ADR and the
#: Security seat rather than a commit.
MODEL_INVOKE_ROLE_PREFIXES = ("GatewayFn",)


def load(path: str | pathlib.Path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


#: Resource types that are telemetry rather than infrastructure. Dropped whole:
#: `AWS::CDK::Metadata` carries a deflate-compressed analytics blob that moves
#: with the library version and is not byte-stable across platforms, so comparing
#: it makes the snapshot machine-specific without asserting anything.
TELEMETRY_TYPES = frozenset({"AWS::CDK::Metadata"})


def _drop_telemetry(resources: dict) -> dict:
    return {
        logical_id: resource
        for logical_id, resource in resources.items()
        if not (isinstance(resource, dict) and resource.get("Type") in TELEMETRY_TYPES)
    }


def normalize(template: Any) -> Any:
    """Strip everything that changes without the infrastructure changing.

    Removes per-resource `Metadata` (which carries `aws:asset:path` and the CDK
    construct path), drops telemetry-only resources, and rewrites asset hashes to
    a placeholder. What survives is resource types, properties, and policy
    documents — the things the G1 assertion is actually about."""
    if isinstance(template, dict):
        if "Resources" in template and isinstance(template["Resources"], dict):
            template = dict(template)
            template["Resources"] = _drop_telemetry(template["Resources"])
        return {
            key: normalize(value)
            for key, value in template.items()
            if key not in ("Metadata",)
        }
    if isinstance(template, list):
        return [normalize(item) for item in template]
    if isinstance(template, str):
        return ASSET_HASH.sub(ASSET_PLACEHOLDER, template)
    return template


def _as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _referenced_roles(refs: Any) -> list[str]:
    """Logical ids of the roles a policy attaches to."""
    names = []
    for ref in _as_list(refs):
        if isinstance(ref, dict) and "Ref" in ref:
            names.append(ref["Ref"])
        elif isinstance(ref, str):
            names.append(ref)
    return names


def statements(template: dict) -> Iterator[dict]:
    """Every IAM statement in the template, with the roles it binds to.

    Covers both shapes CDK emits: a standalone `AWS::IAM::Policy` naming its
    roles, and inline `Policies` on an `AWS::IAM::Role`. Missing the second shape
    would leave a grant that reads exactly like the first one invisible."""
    for logical_id, resource in template.get("Resources", {}).items():
        kind = resource.get("Type")
        properties = resource.get("Properties", {})

        if kind == "AWS::IAM::Policy":
            roles = _referenced_roles(properties.get("Roles"))
            for statement in _as_list(properties.get("PolicyDocument", {}).get("Statement")):
                yield {"policy": logical_id, "roles": roles, "statement": statement}

        elif kind == "AWS::IAM::Role":
            for policy in _as_list(properties.get("Policies")):
                for statement in _as_list(policy.get("PolicyDocument", {}).get("Statement")):
                    yield {"policy": logical_id, "roles": [logical_id], "statement": statement}


def actions_of(statement: dict) -> set[str]:
    return set(_as_list(statement.get("Action")))


def model_invoke_grants(template: dict) -> list[dict]:
    """Every statement that ALLOWS a model-invoke action."""
    found = []
    for entry in statements(template):
        statement = entry["statement"]
        if statement.get("Effect") != "Allow":
            continue
        if actions_of(statement) & MODEL_INVOKE_ACTIONS:
            found.append(entry)
    return found


def model_invoke_denials(template: dict) -> list[dict]:
    """Every statement that explicitly DENIES model-invoke actions.

    Absence of a grant already denies. An explicit Deny is recorded separately
    because it survives a later careless grant, and because it makes the
    resulting CloudTrail event say why the call failed."""
    found = []
    for entry in statements(template):
        statement = entry["statement"]
        if statement.get("Effect") != "Deny":
            continue
        if actions_of(statement) & MODEL_INVOKE_ACTIONS:
            found.append(entry)
    return found


def is_gateway_role(logical_id: str) -> bool:
    return logical_id.startswith(MODEL_INVOKE_ROLE_PREFIXES)


def roles(template: dict) -> list[str]:
    return [
        logical_id
        for logical_id, resource in template.get("Resources", {}).items()
        if resource.get("Type") == "AWS::IAM::Role"
    ]

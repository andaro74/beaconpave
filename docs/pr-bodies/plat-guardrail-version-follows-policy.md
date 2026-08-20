# Platform Engineering: the guardrail version must follow the policy it pins

**ADR-024 deployed successfully and changed nothing.** `cdk deploy` reported
`UPDATE_COMPLETE`, `DRAFT` carried the narrowed definition, and the gateway went
on enforcing **version 1 with the old one**. Nothing failed. Nothing printed
differently. The stack was green and the change was live nowhere.

## Why

A guardrail version is an immutable snapshot. The version resource carried a fixed
description:

```ts
new bedrock.CfnGuardrailVersion(this, 'GuardrailVersion', {
  guardrailIdentifier: guardrail.attrGuardrailId,
  description: 'Pinned for M01 probe and golden runs.',   // never changes
});
```

CloudFormation had no reason to replace it, so no new version was ever published.

**This is ADR-018's failure with the sign reversed.** ADR-018 pinned the gateway to
a published version so the enforced policy could not drift away from the committed
one. The same pin, unexamined from the other side, meant the committed policy could
fail to reach the enforced one. **A pin that only holds in the direction you
happened to test is not a pin** — and the untested direction here is the one where
a security control silently does not change.

## The fix

The version's description is derived from a digest of the policy it pins, so the
resource replaces itself exactly when the policy changes and never otherwise:

```ts
description: `Pinned to policy ${policyDigest}.`
```

The digest covers the content filters, topics, PII entities and the blocked
messaging — not the id or the ARN, which move for reasons that are not policy
changes and would defeat the pin from the other side.

## Two checks, and they are not the same check

- **`test_the_guardrail_version_follows_the_policy_it_pins`** — synth time,
  hermetic. Asserts the description carries a digest rather than a fixed string.
  It checks the *template*, and a template is a statement of intent.
- **`services/highlights-agent/verify_guardrail_pin.py`** — after every deploy.
  Fetches the pinned version's policy out of Bedrock and diffs it against the
  committed snapshot. **Only the deployed policy is the policy.**

The second is the same argument `gateway_client.fetch_record` makes about audit
records: the gateway's word for what it wrote is a self-report, and the harness
fetches the object independently. ADR-016 demoted an assert for being a
self-report. A stack status is one too.

Run against the current deploy, it reports the drift and exits 1 — which is how
this was found:

```
pinned guardrail version: 1

  DRIFT entitlement-circumvention
        committed: Helping a viewer defeat a regional blackout, paywall or ...
        deployed:  Helping a viewer reach content they are not entitled to: ...
  OK    medical-advice
```

## After this merges

Deploy again, then run the verifier. **No probe run and no recorded score against
this gateway until it passes** — every number would be attributed to a policy that
is not the one in the diff.

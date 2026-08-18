# ADR-017: G1 is asserted against a committed synth snapshot

**Status:** Accepted (M01)
**Seats:** Platform Engineering (assertion mechanism) · Security (the invariant)

## Context

CLAUDE.md says `platform/infra/tests/` asserts at synth time that no service role
holds `bedrock:InvokeModel`, and that a change breaking that test is the thing
that is wrong. M01 is the milestone that has to make it true.

Two repo rules collide on the way there:

- **G8** — `make check` is hermetic. It must pass on a fresh clone, offline, with
  no AWS account. A stranger has to be able to run it.
- **G1's enforcement point is a CDK synth**, which needs Node, an `npm ci`, and
  therefore a network.

## Options considered

1. **Synthesize inside the test.** Truest to "at synth time", and it breaks G8 on
   the first fresh clone that has no Node.
2. **Assert in TypeScript in CI, using the CDK assertions module.** Idiomatic,
   and it leaves `make check` unable to enforce G1 at all — the invariant would
   hold only where CI runs.
3. **Both.** One invariant with two implementations, in two languages. They can
   disagree, and the one that disagrees quietly is the one nobody reads.
4. **A committed snapshot plus a freshness job.** Chosen.

## Decision

`cdk synth` output is normalized and committed to
`platform/infra/tests/fixtures/`. `tests/test_iam_assertions.py` reads it and
runs the G1 assertions hermetically. A CI job re-synthesizes, diffs, and emits a
verdict the gate blocks on.

Three details carry the weight:

- **Normalization.** Asset hashes change whenever a byte of Lambda source
  changes. An un-normalized snapshot would churn on every edit and train
  everybody to re-record it without reading it — and a snapshot nobody reads is
  precisely how an IAM grant gets in. `pave.infra.normalize` strips per-resource
  metadata and rewrites asset hashes, leaving structure and policy, which is what
  the assertion is about.
- **The freshness job blocks.** It is the only thing standing between the
  snapshot and a fiction. It emits a verdict rather than failing its own step, so
  `gate decide` remains the single decider (G2) and drift blocks by the same
  mechanism as every other suite.
- **Environment-agnostic synth.** No `env` is set on the app, so account and
  region stay CloudFormation pseudo-parameters. The committed snapshot therefore
  carries no account identifier — which this public repo's
  `tests/test_no_account_identifiers.py` requires — and the freshness job needs
  no AWS credentials.

## Consequences

The assertion is one step removed from reality: it proves things about a template
that CI proves matches the app. That gap is real and is the price of G8. It is
bounded by the freshness job, and the job failing is louder than the assertion
being subtly wrong.

A snapshot recorded but never re-read is the failure mode to watch for. The
negative controls in `tests/test_iam_assertions.py` are the mitigation: they
plant a forbidden grant in a copy of the snapshot, in both shapes CDK emits, and
require the checker to find it. Without them the suite would prove that the
current template is compliant, not that the test would notice if it stopped
being.

**At scale, replace with:** synth-in-CI on every PR, plus an org SCP denying
`bedrock:InvokeModel` outside the gateway's role — at which point the assertion
becomes a fast local pre-check rather than the enforcement point. The interface
already matches: the same assertions run against the same template shape, and
only where the template comes from changes.

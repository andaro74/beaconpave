#!/usr/bin/env node
/**
 * The beaconpave CDK app.
 *
 * **Synthesized environment-agnostic, deliberately.** No `env` is set, so the
 * account and region stay CloudFormation pseudo-parameters rather than being
 * baked into the template. Two things follow, and both are load-bearing:
 *
 *  1. The committed synth snapshot carries no account identifier. This repo is
 *     public and `tests/test_no_account_identifiers.py` fails on any 12-digit
 *     account id in a committed file — a snapshot synthesized against a real
 *     account would trip it, and redacting a template by hand would make it
 *     stop matching what `cdk synth` produces.
 *  2. `cdk synth` needs no credentials, so the freshness job in CI can re-synth
 *     and diff without an AWS role.
 *
 * Two stacks rather than one, also deliberately: the trail carries M01's one
 * unverified assumption (that Bedrock model invocations are selectable as
 * CloudTrail data events). Isolating it means that assumption failing costs the
 * evidence path and its ADR, not the gateway.
 */
import * as cdk from 'aws-cdk-lib';
import { AuditTrailStack } from '../lib/audit-trail-stack';
import { GatewayStack } from '../lib/gateway-stack';

const app = new cdk.App();

new GatewayStack(app, 'BeaconpaveGateway', {
  description: 'Gateway, audit lake, guardrail, and the direct-call probe (M01)',
});

new AuditTrailStack(app, 'BeaconpaveAuditTrail', {
  description: 'CloudTrail witness for direct-call denials (M01, claim 4)',
});

app.synth();

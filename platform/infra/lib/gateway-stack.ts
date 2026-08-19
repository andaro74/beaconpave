import * as fs from 'fs';
import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

/**
 * ADR-015: the regional inference profile, at a recorded 10% premium over
 * `global.`. The bare model id cannot be invoked at all — Haiku 4.5 is
 * INFERENCE_PROFILE only.
 */
const MODEL_ID = 'us.anthropic.claude-haiku-4-5-20251001-v1:0';

/**
 * The foundation model the profile routes to, in each region it may route into.
 * Invoking a cross-region profile authorizes against the profile ARN *and* the
 * underlying model ARN in whichever region served the request, so granting only
 * the profile produces an AccessDenied that reads like a missing model grant —
 * the same misdiagnosis BUILD.md warns about for the bare model id.
 */
const PROFILE_REGIONS = ['us-east-1', 'us-east-2', 'us-west-2'];
const FOUNDATION_MODEL = 'anthropic.claude-haiku-4-5-20251001-v1:0';

/**
 * Model-invoking actions, denied as a set on every non-gateway role.
 *
 * `Converse` authorizes against `bedrock:InvokeModel` today, so naming both is
 * redundant — and deliberately so. A deny list that is exactly minimal stops
 * being correct the moment a provider adds an action, and this is the one list
 * in the repo where being wrong is silent.
 */
const MODEL_INVOKE_ACTIONS = [
  'bedrock:InvokeModel',
  'bedrock:InvokeModelWithResponseStream',
  'bedrock:Converse',
  'bedrock:ConverseStream',
];

/** Repository root, from `platform/infra/lib`. */
const REPO = path.join(__dirname, '..', '..', '..');

/**
 * The registry id, used verbatim as the Cedar resource, the MCP tool name, and
 * the model-facing name in `toolConfig`. One identifier end to end, so there is
 * no mapping layer to get out of step (ADR-019).
 */
const CATALOG_SEARCH = 'catalog-search';

/**
 * Stage the tool's Lambda bundle: its own source, plus the catalog fixture it
 * serves.
 *
 * **Local bundling, so `cdk synth` needs no Docker** and CI's freshness job keeps
 * working on a runner with none. It is a file copy; the reason it exists at all
 * is that `data/catalog.json` lives outside the tool directory and must not be
 * duplicated into it — two copies of a fixture is two things to update, and the
 * deployed one would be the stale one.
 *
 * The catalog lands at the bundle root and `BEACONPAVE_CATALOG` points at it, so
 * the deployed tool reports it through `serverInfo` exactly as the local one
 * does. **Which catalog is served is deployment configuration**, never a request
 * parameter: a tool whose data source can move per call is an instrument that can
 * move without a commit (ADR-018), and the adversarial fixture is reached by
 * deploying it, not by asking for it.
 */
function stageToolBundle(source: string, outputDir: string): boolean {
  fs.cpSync(source, outputDir, {
    recursive: true,
    filter: (from) => !from.includes('__pycache__'),
  });
  fs.copyFileSync(path.join(REPO, 'data', 'catalog.json'), path.join(outputDir, 'catalog.json'));
  return true;
}

function toolCode(toolDir: string): lambda.AssetCode {
  const source = path.join(REPO, 'tools', toolDir);
  return lambda.Code.fromAsset(source, {
    // Hashed on the OUTPUT, not the source: the catalog is copied in from
    // outside the source directory, so a source hash would not move when the
    // fixture did — and the deployed tool would go on serving the old one with
    // nothing printing differently.
    assetHashType: cdk.AssetHashType.OUTPUT,
    bundling: {
      image: lambda.Runtime.PYTHON_3_12.bundlingImage,
      local: { tryBundle: (outputDir: string) => stageToolBundle(source, outputDir) },
    },
  });
}

export class GatewayStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // --- the audit lake ----------------------------------------------------
    // Versioned because an audit record must not be silently replaced: the
    // record is the evidence half of G4, and evidence that can be overwritten
    // in place is not evidence. RETAIN for the same reason — a `cdk destroy`
    // that takes the audit trail with it would erase the proof of every probe
    // run that ever passed.
    const auditLake = new s3.Bucket(this, 'AuditLake', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // --- the guardrail -----------------------------------------------------
    // Defined here rather than adopted from the console. A hand-made guardrail
    // is untracked state that every recorded probe result depends on; a stranger
    // who clones this repo and deploys must get the same instrument or the
    // scores are not reproducible (ADR-018).
    //
    // Configured from the brand packs and `rules/`, never from the probe corpus
    // — SPEC/01's honesty clause. The corpus is frozen (ADR-009) and this is the
    // thing it is aimed at, so a policy written to a probe's wording measures
    // how well we read the corpus rather than how well the gateway resists.
    const guardrail = new bedrock.CfnGuardrail(this, 'Guardrail', {
      name: 'beaconpave-gateway',
      description: 'The single guardrail every model call on the paved road transits.',
      blockedInputMessaging:
        'Blocked by the Beacon gateway guardrail. This request was not sent to a model.',
      blockedOutputsMessaging:
        'Blocked by the Beacon gateway guardrail. The model response was withheld.',
      contentPolicyConfig: {
        filtersConfig: [
          // PROMPT_ATTACK is input-only by design of the service: an attack is a
          // property of what was asked, not of what came back.
          { type: 'PROMPT_ATTACK', inputStrength: 'HIGH', outputStrength: 'NONE' },
          { type: 'HATE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
          { type: 'INSULTS', inputStrength: 'MEDIUM', outputStrength: 'MEDIUM' },
          { type: 'VIOLENCE', inputStrength: 'MEDIUM', outputStrength: 'MEDIUM' },
          { type: 'SEXUAL', inputStrength: 'HIGH', outputStrength: 'HIGH' },
          { type: 'MISCONDUCT', inputStrength: 'MEDIUM', outputStrength: 'MEDIUM' },
        ],
      },
      // A topic `definition` is a classifier input, not documentation: Bedrock
      // feeds it to the model that decides whether a turn is on-topic, and it is
      // capped at 200 characters. The first draft of these carried the policy
      // justification inline and was rejected at deploy — which was the right
      // rejection for the wrong-looking reason. Rationale belongs in a comment
      // and in ADR-018; a definition padded with reasoning is a worse classifier
      // input, not just a longer one.
      //
      // WHY THESE TWO, in policy terms rather than probe terms (SPEC/01's
      // honesty clause):
      //   medical-advice — Meridian is a media company. Individualized medical
      //     guidance is outside every brand's remit and carries consequence
      //     beyond the product.
      //   entitlement-circumvention — entitlement and blackout rules are
      //     Meridian Sports' core compliance surface, so helping a viewer around
      //     them is a policy matter, not a content-quality one.
      //
      // `tests/test_iam_assertions.py` pins the length against the snapshot, so
      // the next one over the limit fails in `make check` rather than at deploy.
      topicPolicyConfig: {
        topicsConfig: [
          {
            name: 'medical-advice',
            type: 'DENY',
            definition:
              'Diagnosing a condition, recommending a medication or a dosage, or otherwise ' +
              'giving individualized medical guidance to a viewer.',
          },
          {
            name: 'entitlement-circumvention',
            type: 'DENY',
            definition:
              'Helping a viewer reach content they are not entitled to: bypassing a regional ' +
              'blackout, a paywall, or a subscription tier, or supplying credentials or links ' +
              'that would.',
          },
        ],
      },
      // NAME and ADDRESS are deliberately NOT blocked here, and the omission is
      // a decision rather than an oversight. A sports highlights agent has to be
      // able to say a player's name and a venue's address; blocking the PII
      // entity would fire on most legitimate answers in the golden set. Requests
      // for personal data about *subscribers* are refused a step earlier, by the
      // classification router (G5) in `platform/gateway/core/classify.py`, which
      // can tell "who plays for the Rovers" from "list subscriber addresses".
      sensitiveInformationPolicyConfig: {
        piiEntitiesConfig: [
          { type: 'EMAIL', action: 'BLOCK' },
          { type: 'PHONE', action: 'BLOCK' },
          { type: 'CREDIT_DEBIT_CARD_NUMBER', action: 'BLOCK' },
          { type: 'US_SOCIAL_SECURITY_NUMBER', action: 'BLOCK' },
        ],
      },
    });

    // Pinned. The gateway refuses to start without a version and never uses
    // DRAFT: a DRAFT guardrail can be edited outside a commit and silently
    // change every recorded probe result, and nothing would print differently
    // when it happened.
    const guardrailVersion = new bedrock.CfnGuardrailVersion(this, 'GuardrailVersion', {
      guardrailIdentifier: guardrail.attrGuardrailId,
      description: 'Pinned for M01 probe and golden runs.',
    });

    // --- the gateway -------------------------------------------------------
    const gatewayFn = new lambda.Function(this, 'GatewayFn', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', '..', 'gateway'), {
        exclude: ['__pycache__', '**/__pycache__', 'README.md'],
      }),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        AUDIT_LAKE_BUCKET: auditLake.bucketName,
        GUARDRAIL_ID: guardrail.attrGuardrailId,
        GUARDRAIL_VERSION: guardrailVersion.attrVersion,
        MODEL_ID,
      },
    });

    // The only grant of a model-invoking action anywhere in this app. The IAM
    // assertion test asserts exactly that, against the committed synth snapshot.
    gatewayFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel'],
        resources: [
          `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/${MODEL_ID}`,
          ...PROFILE_REGIONS.map((r) => `arn:aws:bedrock:${r}::foundation-model/${FOUNDATION_MODEL}`),
        ],
      }),
    );
    gatewayFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:ApplyGuardrail'],
        resources: [guardrail.attrGuardrailArn],
      }),
    );
    auditLake.grantPut(gatewayFn);

    // --- the governed service's role ---------------------------------------
    // Held by the agent from M02 and by the direct-call probe now. The explicit
    // Deny matters more than the absence of a grant: absence already denies, but
    // a Deny survives a later careless grant, and it makes the resulting
    // CloudTrail event unambiguous about *why* the call failed.
    const serviceRole = new iam.Role(this, 'HighlightsAgentRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Execution role for governed services. Reaches models only through the gateway.',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    serviceRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.DENY,
        actions: MODEL_INVOKE_ACTIONS,
        resources: ['*'],
      }),
    );
    gatewayFn.grantInvoke(serviceRole);

    // --- claim 4's runtime artifact ----------------------------------------
    // --- the tool plane's one deployed tool (M02) --------------------------
    // Its own function, with its own role. The process boundary that matters is
    // not the one around an MCP subprocess — ADR-019 rejected that — it is this
    // one: the tool's role is separate from the gateway's, so the gateway holds
    // `lambda:InvokeFunction` on exactly the tools the registry names, and the
    // tool holds nothing at all.
    const catalogSearchFn = new lambda.Function(this, 'CatalogSearchFn', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'server.handler',
      code: toolCode(CATALOG_SEARCH),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      environment: {
        // Deployment configuration, and the only way the served catalog moves.
        BEACONPAVE_CATALOG: '/var/task/catalog.json',
      },
    });

    // The tool reaches no model, and says so explicitly rather than relying on
    // the absence of a grant. Same argument as the service role below: absence
    // already denies, but a Deny survives a later careless grant — and a tool
    // that could call a model would be a second control point, which is the one
    // thing G1 is a singular noun about.
    catalogSearchFn.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.DENY,
        actions: MODEL_INVOKE_ACTIONS,
        resources: ['*'],
      }),
    );

    // G3 at the infrastructure layer. Until this line, G3 rested entirely on the
    // plane: a caller that could reach the tool function directly would be a
    // route nobody authorized, and ADR-019 said so in as many words while the
    // grant did not yet exist. Narrow by construction — `grantInvoke` names this
    // one function, so a tool added to the registry and not deployed is not
    // reachable by a wildcard that happened to already cover it.
    catalogSearchFn.grantInvoke(gatewayFn);

    // The routing table, and the gateway derives its offered tool set from it, so
    // it cannot advertise a tool it has no way to call.
    gatewayFn.addEnvironment('TOOL_FUNCTIONS', cdk.Fn.toJsonString({
      [CATALOG_SEARCH]: catalogSearchFn.functionName,
    }));

    // The Cedar principal, from the stack rather than from the request. See
    // `SERVICE_PRINCIPAL` in `platform/gateway/handler.py`: a caller that picks
    // its own principal picks its own policies.
    gatewayFn.addEnvironment('SERVICE_PRINCIPAL', 'highlights-agent');

    const probeFn = new lambda.Function(this, 'DirectCallProbeFn', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'direct_call.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', '..', 'probe'), {
        exclude: ['__pycache__', '**/__pycache__'],
      }),
      role: serviceRole,
      timeout: cdk.Duration.seconds(30),
      environment: { MODEL_ID },
    });

    new cdk.CfnOutput(this, 'AuditLakeBucket', { value: auditLake.bucketName });
    new cdk.CfnOutput(this, 'GatewayFunctionName', { value: gatewayFn.functionName });
    new cdk.CfnOutput(this, 'DirectCallProbeFunctionName', { value: probeFn.functionName });
    // Published so a harness can *attempt* the direct tool invocation the plane
    // is supposed to make pointless. Security pre-registered that probe for M04
    // against the frozen corpus; the name is here because discovering a resource
    // from stack outputs beats pasting one that still resolves after a redeploy.
    new cdk.CfnOutput(this, 'CatalogSearchFunctionName', { value: catalogSearchFn.functionName });
    // Output ids must not collide with construct ids in the same stack, which is
    // why this is not simply `GuardrailVersion`.
    new cdk.CfnOutput(this, 'PinnedGuardrailId', { value: guardrail.attrGuardrailId });
    new cdk.CfnOutput(this, 'PinnedGuardrailVersion', { value: guardrailVersion.attrVersion });
  }
}

import * as cdk from 'aws-cdk-lib';
import * as cloudtrail from 'aws-cdk-lib/aws-cloudtrail';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

/**
 * The independent witness for claim 4.
 *
 * The direct-call probe reports its own refusal, and a principal reporting its
 * own refusal is exactly the shape ADR-016 ruled out when it demoted
 * `entitlement_source`: the system under test attesting to its own compliance,
 * with the assert crediting the attestation. A trail is a witness the calling
 * principal cannot write to, which is the whole difference.
 *
 * **This stack carries M01's one unverified assumption.** The account's existing
 * `management-events` trail selects `eventCategory = Management` only, and
 * Bedrock model invocation is a *data* event — so nothing today would witness
 * the denial. Whether `AWS::Bedrock::Model` is selectable as a data-event
 * resource type is verified at first deploy, not assumed here.
 *
 * It is a separate stack for that reason. If the resource type is rejected, the
 * gateway still deploys, the fallback in SPEC/01 is taken — the probe couriers
 * the raw AccessDenied, which AWS authors and the probe only carries — and the
 * gap is named in the milestone journal and owed an ADR. What is not acceptable
 * is the probe asserting its own denial and the journal calling that a witness.
 *
 * A pre-existing account trail is deliberately left alone: it is infrastructure
 * outside this repo, and a repo that quietly reconfigures its host account is
 * not one anybody should clone.
 */
export class AuditTrailStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const trailBucket = new s3.Bucket(this, 'TrailBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [
        // G10 is about idle cost, and a trail bucket is the one thing here that
        // grows without anybody invoking it. Ninety days outlives any milestone
        // that would need to re-read an event.
        { expiration: cdk.Duration.days(90) },
      ],
    });

    trailBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        sid: 'AWSCloudTrailAclCheck',
        principals: [new iam.ServicePrincipal('cloudtrail.amazonaws.com')],
        actions: ['s3:GetBucketAcl'],
        resources: [trailBucket.bucketArn],
      }),
    );
    trailBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        sid: 'AWSCloudTrailWrite',
        principals: [new iam.ServicePrincipal('cloudtrail.amazonaws.com')],
        actions: ['s3:PutObject'],
        resources: [`${trailBucket.bucketArn}/AWSLogs/${this.account}/*`],
        conditions: { StringEquals: { 's3:x-amz-acl': 'bucket-owner-full-control' } },
      }),
    );

    // L1 rather than the L2 `Trail`: advanced event selectors are what express a
    // Bedrock data event, and the L2 construct's `addEventSelector` only knows
    // S3 objects and Lambda functions.
    const trail = new cloudtrail.CfnTrail(this, 'GatewayTrail', {
      isLogging: true,
      s3BucketName: trailBucket.bucketName,
      includeGlobalServiceEvents: false,
      isMultiRegionTrail: false,
      enableLogFileValidation: true,
      advancedEventSelectors: [
        {
          name: 'Bedrock model invocations',
          // `equalTo` rather than `equals`: the CDK renames CloudFormation's
          // `Equals` field because it collides with `Object.equals`. It emits as
          // `Equals` in the template.
          fieldSelectors: [
            { field: 'eventCategory', equalTo: ['Data'] },
            { field: 'resources.type', equalTo: ['AWS::Bedrock::Model'] },
          ],
        },
      ],
    });
    trail.node.addDependency(trailBucket.policy!);

    new cdk.CfnOutput(this, 'TrailBucketName', { value: trailBucket.bucketName });
    new cdk.CfnOutput(this, 'TrailName', { value: trail.ref });
  }
}

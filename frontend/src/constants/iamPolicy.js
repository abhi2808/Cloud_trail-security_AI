export const IAM_POLICIES = [
  {
    id: 1,
    label: "CloudSec_Policy-1",
    description: "CloudTrail, IAM, STS, EC2",
    policy: {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "CloudTrailReadOnly",
          "Effect": "Allow",
          "Action": [
            "cloudtrail:LookupEvents",
            "cloudtrail:GetTrail",
            "cloudtrail:GetTrailStatus",
            "cloudtrail:ListTrails",
            "cloudtrail:GetEventSelectors"
          ],
          "Resource": "*"
        },
        {
          "Sid": "IAMReadOnly",
          "Effect": "Allow",
          "Action": [
            "iam:ListUsers",
            "iam:ListRoles",
            "iam:ListGroups",
            "iam:ListPolicies",
            "iam:GetPolicy",
            "iam:GetPolicyVersion",
            "iam:ListAttachedUserPolicies",
            "iam:ListAttachedRolePolicies",
            "iam:ListAttachedGroupPolicies",
            "iam:ListUserPolicies",
            "iam:GetUserPolicy",
            "iam:ListRolePolicies",
            "iam:GetRolePolicy",
            "iam:ListGroupsForUser",
            "iam:GetGroup",
            "iam:GetUser",
            "iam:GetRole",
            "iam:ListAccessKeys",
            "iam:GetInstanceProfile",
            "iam:ListInstanceProfiles",
            "iam:SimulatePrincipalPolicy",
            "iam:GenerateServiceLastAccessedDetails",
            "iam:GetServiceLastAccessedDetails"
          ],
          "Resource": "*"
        },
        {
          "Sid": "STSReadOnly",
          "Effect": "Allow",
          "Action": ["sts:GetCallerIdentity"],
          "Resource": "*"
        },
        {
          "Sid": "EC2MetadataReadOnly",
          "Effect": "Allow",
          "Action": [
            "ec2:DescribeInstances",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeSecurityGroupRules",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DescribeFlowLogs",
            "ec2:DescribeTags",
            "ec2:DescribeImages",
            "ec2:DescribeInstanceAttribute",
            "ec2:DescribeKeyPairs",
            "ec2:DescribeRegions",
            "ec2:DescribeRouteTables",
            "ec2:DescribeInternetGateways",
            "ec2:DescribeNatGateways"
          ],
          "Resource": "*"
        }
      ]
    }
  },
  {
    id: 2,
    label: "CloudSec_Policy-2",
    description: "CloudWatch, Lambda, Config, SSM",
    policy: {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "CloudWatchMetrics",
          "Effect": "Allow",
          "Action": [
            "cloudwatch:GetMetricData",
            "cloudwatch:GetMetricStatistics",
            "cloudwatch:DescribeAlarms",
            "cloudwatch:DescribeAlarmHistory",
            "cloudwatch:ListMetrics",
            "cloudwatch:ListDashboards"
          ],
          "Resource": "*"
        },
        {
          "Sid": "CloudWatchLogsScopedOnly",
          "Effect": "Allow",
          "Action": [
            "logs:DescribeLogStreams",
            "logs:FilterLogEvents",
            "logs:StartQuery",
            "logs:GetQueryResults",
            "logs:StopQuery",
            "logs:GetLogEvents"
          ],
          "Resource": [
            "arn:aws:logs:*:*:log-group:/aws/cloudtrail*",
            "arn:aws:logs:*:*:log-group:/aws/cloudtrail*:*",
            "arn:aws:logs:*:*:log-group:CloudTrail*",
            "arn:aws:logs:*:*:log-group:CloudTrail*:*"
          ]
        },
        {
          "Sid": "CloudWatchLogsDescribe",
          "Effect": "Allow",
          "Action": ["logs:DescribeLogGroups"],
          "Resource": "*"
        },
        {
          "Sid": "LambdaMetadata",
          "Effect": "Allow",
          "Action": [
            "lambda:ListFunctions",
            "lambda:GetFunction",
            "lambda:GetFunctionConfiguration",
            "lambda:GetPolicy",
            "lambda:ListTags",
            "lambda:ListAliases",
            "lambda:ListVersionsByFunction",
            "lambda:GetAccountSettings"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenyLambdaExecution",
          "Effect": "Deny",
          "Action": ["lambda:InvokeFunction", "lambda:InvokeAsync"],
          "Resource": "*"
        },
        {
          "Sid": "ConfigReadOnly",
          "Effect": "Allow",
          "Action": [
            "config:GetResourceConfigHistory",
            "config:DescribeConfigRules",
            "config:DescribeConfigRuleEvaluationStatus",
            "config:GetComplianceDetailsByResource",
            "config:GetComplianceDetailsByConfigRule",
            "config:ListDiscoveredResources",
            "config:DescribeDeliveryChannels",
            "config:DescribeConfigurationRecorders",
            "config:BatchGetResourceConfig"
          ],
          "Resource": "*"
        },
        {
          "Sid": "SSMNamesOnly",
          "Effect": "Allow",
          "Action": ["ssm:DescribeParameters", "ssm:ListTagsForResource"],
          "Resource": "*"
        },
        {
          "Sid": "DenySSMValues",
          "Effect": "Deny",
          "Action": [
            "ssm:GetParameter",
            "ssm:GetParameters",
            "ssm:GetParametersByPath",
            "ssm:GetParameterHistory"
          ],
          "Resource": "*"
        }
      ]
    }
  },
  {
    id: 3,
    label: "CloudSec_Policy-3",
    description: "S3, KMS, Secrets, RDS, Bedrock, SageMaker",
    policy: {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "S3Metadata",
          "Effect": "Allow",
          "Action": [
            "s3:ListAllMyBuckets",
            "s3:GetBucketPolicy",
            "s3:GetBucketAcl",
            "s3:GetBucketPublicAccessBlock",
            "s3:GetBucketLocation",
            "s3:GetBucketLogging",
            "s3:GetBucketVersioning",
            "s3:GetEncryptionConfiguration"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenyS3Data",
          "Effect": "Deny",
          "Action": [
            "s3:GetObject",
            "s3:GetObjectVersion",
            "s3:GetObjectAcl",
            "s3:GetObjectTagging",
            "s3:GetObjectAttributes",
            "s3:ListBucket",
            "s3:ListBucketVersions"
          ],
          "Resource": "*"
        },
        {
          "Sid": "KMSMetadata",
          "Effect": "Allow",
          "Action": [
            "kms:ListKeys",
            "kms:ListAliases",
            "kms:DescribeKey",
            "kms:GetKeyPolicy",
            "kms:GetKeyRotationStatus",
            "kms:ListKeyPolicies",
            "kms:ListGrants",
            "kms:ListResourceTags"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenyKMSDataOps",
          "Effect": "Deny",
          "Action": [
            "kms:Decrypt",
            "kms:Encrypt",
            "kms:GenerateDataKey",
            "kms:ReEncryptFrom",
            "kms:ReEncryptTo"
          ],
          "Resource": "*"
        },
        {
          "Sid": "SecretsMetadata",
          "Effect": "Allow",
          "Action": [
            "secretsmanager:ListSecrets",
            "secretsmanager:DescribeSecret",
            "secretsmanager:ListSecretVersionIds",
            "secretsmanager:GetResourcePolicy"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenySecretsValue",
          "Effect": "Deny",
          "Action": ["secretsmanager:GetSecretValue"],
          "Resource": "*"
        },
        {
          "Sid": "RDSMetadata",
          "Effect": "Allow",
          "Action": [
            "rds:DescribeDBInstances",
            "rds:DescribeDBClusters",
            "rds:DescribeDBSubnetGroups",
            "rds:DescribeDBSnapshots",
            "rds:DescribeDBClusterSnapshots",
            "rds:ListTagsForResource",
            "rds:DescribeDBLogFiles"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenyRDSData",
          "Effect": "Deny",
          "Action": [
            "rds:DownloadDBLogFilePortion",
            "rds:DownloadCompleteDBLogFile"
          ],
          "Resource": "*"
        },
        {
          "Sid": "BedrockMetadata",
          "Effect": "Allow",
          "Action": [
            "bedrock:GetModelInvocationLoggingConfiguration",
            "bedrock:ListFoundationModels",
            "bedrock:GetFoundationModel",
            "bedrock:ListCustomModels"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenyBedrockInvoke",
          "Effect": "Deny",
          "Action": [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream"
          ],
          "Resource": "*"
        },
        {
          "Sid": "SageMakerMetadata",
          "Effect": "Allow",
          "Action": [
            "sagemaker:ListEndpoints",
            "sagemaker:DescribeEndpoint",
            "sagemaker:ListTrainingJobs",
            "sagemaker:DescribeTrainingJob",
            "sagemaker:ListModels",
            "sagemaker:DescribeModel",
            "sagemaker:ListNotebookInstances",
            "sagemaker:DescribeNotebookInstance",
            "sagemaker:ListDomains"
          ],
          "Resource": "*"
        },
        {
          "Sid": "DenySageMakerExec",
          "Effect": "Deny",
          "Action": [
            "sagemaker:InvokeEndpoint",
            "sagemaker:InvokeEndpointAsync",
            "sagemaker:CreateTrainingJob"
          ],
          "Resource": "*"
        }
      ]
    }
  }
];

export const IAM_SETUP_STEPS = [
  { step: 1, title: "Open IAM Console", description: "Go to AWS Console → IAM → Users → Select or create a dedicated user for CloudSec Investigator." },
  { step: 2, title: "Create 3 Inline Policies", description: "Under the user's 'Permissions' tab → 'Add permissions' → 'Attach policies directly' → 'Create policy' → JSON tab. Repeat for each of the 3 policies below." },
  { step: 3, title: "Generate Access Keys", description: "Under the user's 'Security credentials' tab → Create access key → choose 'Application running outside AWS' → copy both keys." },
  { step: 4, title: "Add Account Here", description: "Paste the Access Key ID and Secret Access Key into the form above and save." },
];

// Legacy export kept for backward compatibility
export const IAM_POLICY_JSON = IAM_POLICIES[0].policy;

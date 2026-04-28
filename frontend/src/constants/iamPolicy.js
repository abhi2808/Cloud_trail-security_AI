export const IAM_POLICY_JSON = {
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
        "iam:ListUsers", "iam:ListRoles", "iam:ListGroups", "iam:ListPolicies",
        "iam:GetPolicy", "iam:GetPolicyVersion",
        "iam:ListAttachedUserPolicies", "iam:ListAttachedRolePolicies", "iam:ListAttachedGroupPolicies",
        "iam:ListUserPolicies", "iam:GetUserPolicy", "iam:ListRolePolicies", "iam:GetRolePolicy",
        "iam:ListGroupsForUser", "iam:GetGroup", "iam:GetUser", "iam:GetRole",
        "iam:ListAccessKeys", "iam:GetInstanceProfile", "iam:ListInstanceProfiles",
        "iam:SimulatePrincipalPolicy",
        "iam:GenerateServiceLastAccessedDetails", "iam:GetServiceLastAccessedDetails"
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
        "ec2:DescribeInstances", "ec2:DescribeSecurityGroups", "ec2:DescribeSecurityGroupRules",
        "ec2:DescribeVpcs", "ec2:DescribeSubnets", "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeFlowLogs", "ec2:DescribeTags", "ec2:DescribeImages",
        "ec2:DescribeInstanceAttribute", "ec2:DescribeKeyPairs", "ec2:DescribeRegions",
        "ec2:DescribeAvailabilityZones", "ec2:DescribeRouteTables",
        "ec2:DescribeInternetGateways", "ec2:DescribeNatGateways"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchMetricsReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics",
        "cloudwatch:DescribeAlarms", "cloudwatch:DescribeAlarmHistory",
        "cloudwatch:ListMetrics", "cloudwatch:ListDashboards"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsCloudTrailOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogStreams", "logs:FilterLogEvents",
        "logs:StartQuery", "logs:GetQueryResults", "logs:StopQuery", "logs:GetLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/cloudtrail*",
        "arn:aws:logs:*:*:log-group:/aws/cloudtrail*:*",
        "arn:aws:logs:*:*:log-group:CloudTrail*",
        "arn:aws:logs:*:*:log-group:CloudTrail*:*"
      ]
    },
    {
      "Sid": "CloudWatchLogsDescribeAll",
      "Effect": "Allow",
      "Action": ["logs:DescribeLogGroups"],
      "Resource": "*"
    },
    {
      "Sid": "S3MetadataOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets", "s3:GetBucketPolicy", "s3:GetBucketAcl",
        "s3:GetBucketPublicAccessBlock", "s3:GetBucketLocation", "s3:GetBucketLogging",
        "s3:GetBucketVersioning", "s3:GetBucketNotification", "s3:GetEncryptionConfiguration",
        "s3:GetBucketObjectLockConfiguration", "s3:GetLifecycleConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyS3DataAccess",
      "Effect": "Deny",
      "Action": [
        "s3:GetObject", "s3:GetObjectVersion", "s3:GetObjectAcl",
        "s3:GetObjectTagging", "s3:GetObjectAttributes",
        "s3:ListBucket", "s3:ListBucketVersions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "KMSMetadataOnly",
      "Effect": "Allow",
      "Action": [
        "kms:ListKeys", "kms:ListAliases", "kms:DescribeKey",
        "kms:GetKeyPolicy", "kms:GetKeyRotationStatus",
        "kms:ListKeyPolicies", "kms:ListGrants", "kms:ListResourceTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyKMSDataOperations",
      "Effect": "Deny",
      "Action": [
        "kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey",
        "kms:GenerateDataKeyWithoutPlaintext", "kms:ReEncryptFrom", "kms:ReEncryptTo"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManagerMetadataOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:ListSecrets", "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds", "secretsmanager:GetResourcePolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenySecretsData",
      "Effect": "Deny",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "*"
    },
    {
      "Sid": "RDSMetadataOnly",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances", "rds:DescribeDBClusters", "rds:DescribeDBSubnetGroups",
        "rds:DescribeDBSecurityGroups", "rds:DescribeDBParameterGroups",
        "rds:DescribeDBSnapshots", "rds:DescribeDBClusterSnapshots",
        "rds:ListTagsForResource", "rds:DescribeDBLogFiles"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyRDSDataAccess",
      "Effect": "Deny",
      "Action": ["rds:DownloadDBLogFilePortion", "rds:DownloadCompleteDBLogFile"],
      "Resource": "*"
    },
    {
      "Sid": "LambdaMetadataOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions", "lambda:GetFunction", "lambda:GetFunctionConfiguration",
        "lambda:GetPolicy", "lambda:ListTags", "lambda:ListAliases",
        "lambda:ListVersionsByFunction", "lambda:GetAccountSettings"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyLambdaExecution",
      "Effect": "Deny",
      "Action": ["lambda:InvokeFunction", "lambda:InvokeAsync"],
      "Resource": "*"
    },
    {
      "Sid": "ConfigReadOnly",
      "Effect": "Allow",
      "Action": [
        "config:GetResourceConfigHistory", "config:DescribeConfigRules",
        "config:DescribeConfigRuleEvaluationStatus",
        "config:GetComplianceDetailsByResource", "config:GetComplianceDetailsByConfigRule",
        "config:ListDiscoveredResources", "config:DescribeDeliveryChannels",
        "config:DescribeConfigurationRecorders", "config:BatchGetResourceConfig"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BedrockMetadataOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock:GetModelInvocationLoggingConfiguration",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel",
        "bedrock:ListCustomModels",
        "bedrock:GetCustomModel",
        "bedrock:ListProvisionedModelThroughputs"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyBedrockInvocation",
      "Effect": "Deny",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": "*"
    },
    {
      "Sid": "SageMakerMetadataOnly",
      "Effect": "Allow",
      "Action": [
        "sagemaker:ListEndpoints", "sagemaker:DescribeEndpoint",
        "sagemaker:ListEndpointConfigs", "sagemaker:DescribeEndpointConfig",
        "sagemaker:ListTrainingJobs", "sagemaker:DescribeTrainingJob",
        "sagemaker:ListModels", "sagemaker:DescribeModel",
        "sagemaker:ListTags", "sagemaker:ListNotebookInstances",
        "sagemaker:DescribeNotebookInstance", "sagemaker:ListDomains",
        "sagemaker:DescribeDomain", "sagemaker:ListUserProfiles"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenySageMakerExecution",
      "Effect": "Deny",
      "Action": [
        "sagemaker:InvokeEndpoint", "sagemaker:InvokeEndpointAsync",
        "sagemaker:CreateTrainingJob", "sagemaker:StopTrainingJob"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SSMParameterNamesOnly",
      "Effect": "Allow",
      "Action": ["ssm:DescribeParameters", "ssm:ListTagsForResource"],
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenySSMParameterValues",
      "Effect": "Deny",
      "Action": [
        "ssm:GetParameter", "ssm:GetParameters",
        "ssm:GetParametersByPath", "ssm:GetParameterHistory"
      ],
      "Resource": "*"
    }
  ]
};

export const IAM_SETUP_STEPS = [
  { step: 1, title: "Open IAM Console", description: "Go to AWS Console → IAM → Users → Create User" },
  { step: 2, title: "Set Username", description: "Name it: cloudtrail-ai-readonly. Disable console access." },
  { step: 3, title: "Attach Policy", description: "Choose 'Attach policies directly' → Create inline policy → paste the JSON below" },
  { step: 4, title: "Create Access Key", description: "Go to the user → Security Credentials → Create Access Key → Choose 'Application running outside AWS'" },
  { step: 5, title: "Copy Credentials", description: "Copy the Access Key ID and Secret Access Key. The secret is shown only once." }
];

export const INVESTIGABLE_SERVICES = [
  "CloudTrail", "IAM", "STS", "EC2", "CloudWatch", "S3",
  "KMS", "Secrets Manager", "RDS", "AWS Config", "Lambda",
  "Bedrock (metadata)", "SageMaker (metadata)", "SSM Parameters (names only)"
];

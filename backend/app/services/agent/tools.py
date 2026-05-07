"""
Tool definitions and execution router for the agentic ReAct loop.

TOOL_DEFINITIONS is injected into the agent system prompt so the AI
knows what tools exist. execute_tool() routes tool_name → service call.
All write APIs are structurally absent from the router — read-only by design.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.models.query import ExtractedIntent
from app.services.cloudtrail import lookup_events
from app.services import (
    iam_reader,
    ec2_reader,
    cloudwatch,
    s3_reader,
    kms_reader,
    secrets_reader,
    rds_reader,
    # config_reader,  # ← Re-enable when AWS Config is activated on the account
    bedrock_reader,
    sagemaker_reader,
    eks_reader,
)
from app.services import cost_explorer

logger = logging.getLogger(__name__)

# ─── Tool Definitions (injected into agent prompt) ───────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "search_cloudtrail",
        "description": (
            "Search CloudTrail audit logs for API events. "
            "Use to answer: who performed an action, when did something happen, "
            "what was done to a specific resource, what actions did a user take."
        ),
        "parameters": {
            "event_name": "str | None  — AWS EventName e.g. TerminateInstances",
            "resource_id": "str | None — resource ID e.g. i-1234, arn:...",
            "username": "str | None   — IAM username or assumed role session name",
            "start_time": "str | None — ISO 8601 datetime, derive from natural language",
            "end_time": "str | None   — ISO 8601 datetime",
            "region": "str | None     — specific AWS region, or 'all' for all regions",
        },
        "when_to_use": (
            "Whenever the question involves past actions, who did what, "
            "timeline of events, or specific resource history."
        ),
    },
    {
        "name": "get_iam_user_permissions",
        "description": (
            "Get complete IAM permissions for a specific user. "
            "Use to answer: what can this user access, what services does "
            "this user have permissions for, blast radius if compromised."
        ),
        "parameters": {
            "username": "str — IAM username (not ARN, just the name)",
        },
        "when_to_use": (
            "When you need to understand what a user is capable of doing, "
            "or assess blast radius of a compromised identity."
        ),
    },
    {
        "name": "get_iam_role_permissions",
        "description": (
            "Get complete IAM permissions for a specific role. "
            "Use to understand what an EC2 instance, Lambda, or assumed role can access."
        ),
        "parameters": {
            "role_name": "str — IAM role name (not ARN)",
        },
        "when_to_use": (
            "When investigating what an AWS service or assumed role can access. "
            "Use after describe_ec2_instance returns an iam_instance_profile."
        ),
    },
    {
        "name": "list_iam_users",
        "description": (
            "List all IAM users in the account with basic info. "
            "Use to get an overview of identities or find a username when only partial info is known."
        ),
        "parameters": {},
        "when_to_use": "When you need to enumerate users or find who exists in the account.",
    },
    {
        "name": "simulate_iam_permissions",
        "description": (
            "Check whether a specific IAM principal is allowed to perform "
            "specific actions on a resource."
        ),
        "parameters": {
            "principal_arn": "str      — full ARN of user or role",
            "actions": "list[str]      — list of AWS actions e.g. ['ec2:TerminateInstances']",
            "resource_arn": "str       — defaults to '*'",
        },
        "when_to_use": (
            "When you need a definitive yes/no answer on whether a principal "
            "CAN perform a specific action."
        ),
    },
    {
        "name": "check_access_keys",
        "description": (
            "List access keys for an IAM user. Shows key age, status, "
            "and flags stale keys (>90 days old)."
        ),
        "parameters": {
            "username": "str — IAM username",
        },
        "when_to_use": (
            "When investigating credential hygiene or checking if a user "
            "has active/stale access keys."
        ),
    },
    {
        "name": "describe_ec2_instance",
        "description": (
            "Get full metadata for an EC2 instance including security groups, "
            "IAM role, network config, tags, and whether IMDSv1 is enabled (a security risk)."
        ),
        "parameters": {
            "instance_id": "str — e.g. i-0abc1234def56789",
        },
        "when_to_use": (
            "Whenever an EC2 instance ID appears in findings. Always call this "
            "to understand instance context before forming conclusions."
        ),
    },
    {
        "name": "describe_security_group",
        "description": (
            "Get inbound and outbound rules for a security group. "
            "Identifies rules open to the public internet (0.0.0.0/0)."
        ),
        "parameters": {
            "sg_id": "str — e.g. sg-0abc1234",
        },
        "when_to_use": (
            "When checking if an EC2 instance is exposed to the internet, "
            "or validating network access paths."
        ),
    },
    {
        "name": "list_ec2_instances",
        "description": "List all EC2 instances in the account with their state, IPs, and tags.",
        "parameters": {},
        "when_to_use": (
            "When you need an overview of running infrastructure or to find "
            "an instance when only partial info is known."
        ),
    },
    {
        "name": "get_cloudwatch_alarms",
        "description": (
            "List CloudWatch alarms currently in ALARM state. "
            "Use as a quick health check to find actively firing alerts."
        ),
        "parameters": {},
        "when_to_use": "When asked about current issues, health status, or what is actively alerting.",
    },
    {
        "name": "get_metric_anomalies",
        "description": (
            "Fetch a CloudWatch metric over a time window and detect anomalies "
            "(values > 2x the average). Supports EC2 CPU, network, Lambda errors/throttles."
        ),
        "parameters": {
            "resource_id": "str   — instance ID, function name, bucket name etc",
            "metric_name": "str   — CPUUtilization | NetworkOut | Errors | Throttles | Invocations",
            "resource_type": "str — ec2 | lambda | s3",
            "start_time": "str    — ISO 8601",
            "end_time": "str      — ISO 8601",
        },
        "when_to_use": (
            "When investigating unusual behavior, spikes, or performance anomalies "
            "on a specific resource."
        ),
    },
    {
        "name": "list_s3_buckets",
        "description": (
            "List all S3 buckets with public access status. "
            "Flags buckets where public access block is not enabled."
        ),
        "parameters": {},
        "when_to_use": "When checking for exposed S3 buckets or assessing data exposure risk.",
    },
    {
        "name": "get_s3_bucket_policy",
        "description": "Check if an S3 bucket has a public policy or permissive ACL.",
        "parameters": {
            "bucket_name": "str — S3 bucket name",
        },
        "when_to_use": "When a specific S3 bucket needs deeper inspection for public exposure.",
    },
    {
        "name": "get_caller_identity",
        "description": (
            "Get the AWS account ID and identity of the credentials being used. "
            "Call this first if you need the account ID to construct ARNs."
        ),
        "parameters": {},
        "when_to_use": "Call first if you need to verify which account the agent is operating in.",
    },
    {
        "name": "list_kms_keys",
        "description": (
            "List all customer-managed KMS encryption keys with rotation status and security findings. "
            "Identifies keys with disabled rotation or unexpected grants."
        ),
        "parameters": {},
        "when_to_use": "When investigating encryption posture, checking for disabled rotation, or finding externally accessible keys.",
    },
    {
        "name": "get_kms_key_details",
        "description": (
            "Get full details of a specific KMS key including its policy, grants, and rotation status. "
            "Flags external access and public access automatically."
        ),
        "parameters": {
            "key_id": "str — KMS key ID or alias (e.g. alias/my-key)",
        },
        "when_to_use": (
            "When a specific KMS key needs deeper investigation, especially after CloudTrail "
            "shows kms:* events on that key."
        ),
    },
    {
        "name": "list_secrets",
        "description": (
            "List all Secrets Manager secrets with rotation status and last accessed date. "
            "Identifies secrets with disabled rotation or stale credentials. NEVER returns secret values."
        ),
        "parameters": {},
        "when_to_use": "When checking credential hygiene, finding unrotated secrets, or investigating who last accessed a secret.",
    },
    {
        "name": "get_secret_details",
        "description": (
            "Get metadata and security analysis for a specific secret. Returns rotation history, "
            "access policy, and security findings. Never returns the secret value itself."
        ),
        "parameters": {
            "secret_name": "str — secret name or ARN",
        },
        "when_to_use": "When a specific secret needs investigation, especially after CloudTrail shows GetSecretValue events.",
    },
    {
        "name": "get_secrets_security_summary",
        "description": (
            "Get an account-wide security summary across ALL secrets: rotation status, "
            "overdue rotation count, and high-risk secrets list."
        ),
        "parameters": {},
        "when_to_use": "When asked for an overview of secrets hygiene across the account.",
    },
    {
        "name": "list_rds_databases",
        "description": (
            "List all RDS database instances with security findings: publicly accessible, "
            "unencrypted storage, deletion protection status."
        ),
        "parameters": {},
        "when_to_use": "When checking database security posture or investigating database-related CloudTrail events.",
    },
    {
        "name": "get_rds_database_details",
        "description": (
            "Get full security details for a specific RDS instance including backup retention, "
            "IAM authentication, and parameter groups."
        ),
        "parameters": {
            "db_identifier": "str — RDS DB instance identifier",
        },
        "when_to_use": "When a specific database needs investigation after appearing in CloudTrail events.",
    },
    {
        "name": "list_rds_snapshots",
        "description": (
            "List RDS snapshots and flag any that are publicly shared. "
            "A public RDS snapshot is a critical data exposure finding."
        ),
        "parameters": {},
        "when_to_use": (
            "When checking for data exposure via shared snapshots, or investigating "
            "ModifyDBSnapshotAttribute events in CloudTrail."
        ),
    },
    # ── AWS Config tools (disabled — AWS Config not enabled on this account) ──────
    # To re-enable: activate AWS Config in your AWS account, then uncomment this block
    # and uncomment `config_reader` in the imports at the top of this file.
    #
    # {
    #     "name": "get_resource_config_history",
    #     "description": (
    #         "Get historical configuration snapshots for any AWS resource (the time machine). "
    #         "Shows what a resource looked like at any point in the past. "
    #         "Answers: what did this S3 bucket policy look like before it was changed?"
    #     ),
    #     "parameters": {
    #         "resource_type": (
    #             "str — AWS Config format: AWS::EC2::Instance | AWS::S3::Bucket | "
    #             "AWS::IAM::Role | AWS::RDS::DBInstance | AWS::Lambda::Function | AWS::KMS::Key"
    #         ),
    #         "resource_id": "str — the resource identifier",
    #     },
    #     "when_to_use": (
    #         "When investigating changes to a resource over time, especially after CloudTrail "
    #         "shows a modification event and you want to see the before/after configuration."
    #     ),
    # },
    # {
    #     "name": "list_noncompliant_resources",
    #     "description": (
    #         "List all resources currently failing AWS Config compliance rules. "
    #         "Quick way to surface known misconfigurations across the account."
    #     ),
    #     "parameters": {},
    #     "when_to_use": (
    #         "When asked for a compliance overview or when looking for known misconfigurations "
    #         "across the account."
    #     ),
    # },
    # {
    #     "name": "get_resource_relationships",
    #     "description": (
    #         "Get all AWS resources connected to a specific resource according to AWS Config. "
    #         "Shows what an EC2 instance is attached to, what a security group is used by, etc."
    #     ),
    #     "parameters": {
    #         "resource_type": "str — AWS Config format e.g. AWS::EC2::Instance",
    #         "resource_id": "str — the resource identifier",
    #     },
    #     "when_to_use": (
    #         "When you need to understand blast radius or resource dependencies "
    #         "without querying each service individually."
    #     ),
    # },
    # ── End AWS Config tools ──────────────────────────────────────────────────
    {
        "name": "get_bedrock_security_summary",
        "description": (
            "Get a security summary of Amazon Bedrock usage: custom models, invocation logging status. "
            "Flags if model invocation logging is disabled (AI calls unaudited)."
        ),
        "parameters": {},
        "when_to_use": "When investigating AI/ML security posture or checking if Bedrock usage is audited.",
    },
    {
        "name": "list_bedrock_foundation_models",
        "description": "List available Bedrock foundation models with provider and capability info.",
        "parameters": {},
        "when_to_use": "When checking which AI models are available or in use in the account.",
    },
    {
        "name": "get_sagemaker_security_summary",
        "description": (
            "Get a security summary of SageMaker: endpoints, notebooks, and training jobs. "
            "Flags notebooks without network isolation or endpoints without KMS encryption."
        ),
        "parameters": {},
        "when_to_use": "When investigating AI/ML workload security or SageMaker data exposure risk.",
    },
    {
        "name": "list_sagemaker_endpoints",
        "description": "List SageMaker inference endpoints with status. Use to find exposed ML model serving endpoints.",
        "parameters": {},
        "when_to_use": "When checking ML inference exposure or CloudTrail shows SageMaker endpoint events.",
    },
    # ── EKS tools ──────────────────────────────────────────────────────────
    {
        "name": "list_eks_clusters",
        "description": (
            "List all EKS Kubernetes clusters in the account with security metadata. "
            "Flags clusters with public API endpoints, missing KMS secrets encryption, "
            "or disabled control-plane audit logging."
        ),
        "parameters": {},
        "when_to_use": (
            "When investigating Kubernetes workload security, checking for exposed cluster "
            "API endpoints, or as part of a broad account security sweep."
        ),
    },
    {
        "name": "describe_eks_cluster",
        "description": (
            "Get full security details for a specific EKS cluster including node groups, "
            "Fargate profiles, add-ons, endpoint exposure, logging config, and KMS encryption. "
            "Auto-flags critical findings like public 0.0.0.0/0 API endpoints."
        ),
        "parameters": {
            "cluster_name": "str — EKS cluster name",
        },
        "when_to_use": (
            "When a specific EKS cluster needs investigation, especially after CloudTrail "
            "shows eks:CreateCluster, eks:UpdateClusterConfig, or eks:DeleteCluster events."
        ),
    },
    # ── End EKS tools ─────────────────────────────────────────────────────────
    # ── Cost Explorer tools ──────────────────────────────────────────────────
    {
        "name": "get_cost_summary",
        "description": (
            "Get AWS cost breakdown by service for a date range. Shows total spend, "
            "per-service costs, and identifies the most expensive service. "
            "Use for general cost overview questions."
        ),
        "parameters": {
            "start_date": "str — YYYY-MM-DD format",
            "end_date": "str — YYYY-MM-DD format",
            "granularity": "str — 'DAILY' or 'MONTHLY', default DAILY",
        },
        "when_to_use": (
            "When asked about overall AWS spend, cost breakdown by service, "
            "or what is costing the most in a given period."
        ),
    },
    {
        "name": "get_cost_spike",
        "description": (
            "Detect cost spikes by comparing recent spend to baseline. "
            "Automatically calculates spike factor and severity. "
            "The primary tool for 'why did my bill increase?' questions."
        ),
        "parameters": {
            "service": "str | None — specific AWS service or null for all",
            "lookback_days": "int — default 14",
        },
        "when_to_use": (
            "ALWAYS call this first when user mentions a cost spike, unexpected bill, "
            "or sudden increase. Call with service=null to scan all services, then "
            "use get_service_cost_timeline to drill into the highest spike service."
        ),
    },
    {
        "name": "get_cost_anomalies",
        "description": (
            "Get AWS-detected cost anomalies from Cost Anomaly Detection monitors. "
            "AWS's own ML flags these automatically. More reliable than manual spike "
            "detection for production accounts."
        ),
        "parameters": {},
        "when_to_use": (
            "Call alongside get_cost_spike for any billing investigation. "
            "AWS anomalies are pre-validated findings — treat them as high confidence."
        ),
    },
    {
        "name": "get_service_cost_timeline",
        "description": (
            "Get detailed daily cost breakdown and usage types for one specific AWS service. "
            "Shows peak spending day and what usage types drove the cost. "
            "Use AFTER identifying which service spiked."
        ),
        "parameters": {
            "service": (
                "str — exact AWS service name e.g. 'Amazon EC2', 'AWS Lambda', "
                "'Amazon S3', 'Amazon Bedrock'"
            ),
            "start_date": "str — YYYY-MM-DD",
            "end_date": "str — YYYY-MM-DD",
        },
        "when_to_use": (
            "After get_cost_spike identifies the spiking service, call this for the "
            "detailed timeline. Then combine with search_cloudtrail on the peak day "
            "to find who caused it."
        ),
    },
    # ── End Cost Explorer tools ──────────────────────────────────────────────
    {
        "name": "finish",
        "description": (
            "Call this when you have sufficient evidence to answer the user's question. "
            "Do not call more tools after deciding to finish."
        ),
        "parameters": {
            "answer": "str           — complete analyst-style answer",
            "severity": "str         — NONE | LOW | MEDIUM | HIGH | CRITICAL",
            "evidence": "list[str]   — key findings that support the verdict",
            "recommended_actions": "list[str] — specific next steps",
        },
        "when_to_use": (
            "When you have enough information. 4-6 tool calls is usually sufficient. "
            "Never exceed 8 tool calls."
        ),
    },
]

TOOL_NAMES = {t["name"] for t in TOOL_DEFINITIONS}


# ─── Tool Executor ────────────────────────────────────────────────────────────

async def execute_tool(
    tool_name: str,
    params: dict,
    session,
    account_id: str,
    user_id: str,
    query_region: str = "all",
) -> dict | list:
    """
    Route tool_name to the correct service function.
    All calls are read-only by design — write APIs are not mapped.
    Returns dict/list on success, {"error": str} on failure.
    """
    try:
        # ── CloudTrail ──────────────────────────────────────────────────────
        if tool_name == "search_cloudtrail":
            start = _parse_dt(params.get("start_time"))
            end = _parse_dt(params.get("end_time"))
            region_override = params.get("region") or query_region
            # Guard: agent sometimes passes username as a list — always coerce to str
            username_raw = params.get("username")
            if isinstance(username_raw, list):
                username_raw = username_raw[0] if username_raw else None
            intent = ExtractedIntent(
                event_name=params.get("event_name"),
                resource_id=params.get("resource_id"),
                username=username_raw,
                start_time=start,
                end_time=end,
                aws_region=region_override,
            )
            events = await lookup_events(intent, account_id=account_id, user_id=user_id)
            return [e.model_dump(mode="json") for e in events]

        # ── IAM ─────────────────────────────────────────────────────────────
        elif tool_name == "get_iam_user_permissions":
            # Guard: coerce list → first element
            uname = params["username"]
            if isinstance(uname, list):
                uname = uname[0] if uname else ""
            return await iam_reader.get_user_permissions(session, uname)

        elif tool_name == "get_iam_role_permissions":
            return await iam_reader.get_role_permissions(session, params["role_name"])

        elif tool_name == "list_iam_users":
            return await iam_reader.list_users(session)

        elif tool_name == "simulate_iam_permissions":
            return await iam_reader.simulate_permissions(
                session,
                params["principal_arn"],
                params.get("actions", []),
                params.get("resource_arn", "*"),
            )

        elif tool_name == "check_access_keys":
            return await iam_reader.list_access_keys(session, params["username"])

        elif tool_name == "get_caller_identity":
            return await iam_reader.get_caller_identity(session)

        # ── EC2 ─────────────────────────────────────────────────────────────
        elif tool_name == "describe_ec2_instance":
            return await ec2_reader.describe_instance(session, params["instance_id"])

        elif tool_name == "describe_security_group":
            return await ec2_reader.describe_security_group(session, params["sg_id"])

        elif tool_name == "list_ec2_instances":
            return await ec2_reader.list_instances(session)

        # ── CloudWatch ───────────────────────────────────────────────────────
        elif tool_name == "get_cloudwatch_alarms":
            return await cloudwatch.list_active_alarms(session)

        elif tool_name == "get_metric_anomalies":
            start = _parse_dt(params.get("start_time")) or (
                datetime.now(timezone.utc) - timedelta(hours=24)
            )
            end = _parse_dt(params.get("end_time")) or datetime.now(timezone.utc)
            namespace, dimensions = cloudwatch.resolve_namespace_and_dimensions(
                params["resource_id"],
                params.get("resource_type", "ec2"),
            )
            return await cloudwatch.get_metric_data(
                session,
                namespace=namespace,
                metric_name=params.get("metric_name", "CPUUtilization"),
                dimensions=dimensions,
                start_time=start,
                end_time=end,
            )

        # ── S3 ───────────────────────────────────────────────────────────────
        elif tool_name == "list_s3_buckets":
            return await s3_reader.list_buckets_summary(session)

        elif tool_name == "get_s3_bucket_policy":
            return await s3_reader.get_bucket_policy_summary(session, params["bucket_name"])

        # ── KMS ──────────────────────────────────────────────────────────────
        elif tool_name == "list_kms_keys":
            return await kms_reader.list_keys(session)

        elif tool_name == "get_kms_key_details":
            return await kms_reader.get_key_details(session, params["key_id"])

        # ── Secrets Manager ──────────────────────────────────────────────────
        elif tool_name == "list_secrets":
            return await secrets_reader.list_secrets(session)

        elif tool_name == "get_secret_details":
            return await secrets_reader.get_secret_details(session, params["secret_name"])

        elif tool_name == "get_secrets_security_summary":
            return await secrets_reader.get_secrets_security_summary(session)

        # ── RDS ───────────────────────────────────────────────────────────────
        elif tool_name == "list_rds_databases":
            return await rds_reader.list_databases(session)

        elif tool_name == "get_rds_database_details":
            return await rds_reader.get_database_details(session, params["db_identifier"])

        elif tool_name == "list_rds_snapshots":
            return await rds_reader.list_snapshots(session)

        # ── AWS Config (disabled — AWS Config not enabled on this account) ──────────
        # To re-enable: uncomment this block and the config_reader import at the top.
        #
        # elif tool_name == "get_resource_config_history":
        #     return await config_reader.get_resource_config_history(
        #         session,
        #         params["resource_type"],
        #         params["resource_id"],
        #     )
        #
        # elif tool_name == "list_noncompliant_resources":
        #     return await config_reader.list_noncompliant_resources(session)
        #
        # elif tool_name == "get_resource_relationships":
        #     return await config_reader.get_resource_relationships(
        #         session,
        #         params["resource_type"],
        #         params["resource_id"],
        #     )
        # ── End AWS Config ────────────────────────────────────────────────────────

        # ── Bedrock ──────────────────────────────────────────────────────
        elif tool_name == "get_bedrock_security_summary":
            return await bedrock_reader.get_bedrock_security_summary(session)

        elif tool_name == "list_bedrock_foundation_models":
            return await bedrock_reader.list_foundation_models(session)

        # ── SageMaker ──────────────────────────────────────────────────
        elif tool_name == "get_sagemaker_security_summary":
            return await sagemaker_reader.get_sagemaker_security_summary(session)

        elif tool_name == "list_sagemaker_endpoints":
            return await sagemaker_reader.list_endpoints(session)

        # ── EKS ──────────────────────────────────────────────────────
        elif tool_name == "list_eks_clusters":
            return await eks_reader.list_clusters(session)

        elif tool_name == "describe_eks_cluster":
            return await eks_reader.describe_cluster(session, params["cluster_name"])

        # ── Cost Explorer ────────────────────────────────────────────────
        elif tool_name == "get_cost_summary":
            return await cost_explorer.get_cost_summary(
                session,
                params["start_date"],
                params["end_date"],
                params.get("granularity", "DAILY"),
            )

        elif tool_name == "get_cost_spike":
            return await cost_explorer.get_cost_spike(
                session,
                params.get("service"),
                params.get("lookback_days", 14),
            )

        elif tool_name == "get_cost_anomalies":
            return await cost_explorer.get_cost_anomalies(session)

        elif tool_name == "get_service_cost_timeline":
            return await cost_explorer.get_service_cost_timeline(
                session,
                params["service"],
                params["start_date"],
                params["end_date"],
            )

        else:
            return {"error": f"Unknown tool: {tool_name}", "tool": tool_name}

    except Exception as e:
        logger.error(f"execute_tool({tool_name}): {type(e).__name__}: {e}")
        return {"error": str(e), "tool": tool_name}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _parse_dt(value) -> datetime | None:
    """Safely parse an ISO datetime string."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

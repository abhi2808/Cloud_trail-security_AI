"""
AWS Config reader — resource configuration history, compliance, and relationships.
Read-only. Never calls any mutating Config APIs.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Common AWS Config resource type strings for reference
COMMON_RESOURCE_TYPES = {
    "ec2_instance":   "AWS::EC2::Instance",
    "s3_bucket":      "AWS::S3::Bucket",
    "iam_role":       "AWS::IAM::Role",
    "iam_user":       "AWS::IAM::User",
    "rds_instance":   "AWS::RDS::DBInstance",
    "lambda":         "AWS::Lambda::Function",
    "kms_key":        "AWS::KMS::Key",
    "security_group": "AWS::EC2::SecurityGroup",
    "vpc":            "AWS::EC2::VPC",
}


async def get_resource_config_history(
    session,
    resource_type: str,
    resource_id: str,
    limit: int = 10,
) -> dict:
    """
    Get historical configuration snapshots for any AWS resource.
    This is the 'time machine' — shows what a resource looked like at any point in the past.
    resource_type must be in AWS Config format e.g. AWS::EC2::Instance
    """
    try:
        client = session.client("config")
        resp = client.get_resource_config_history(
            resourceType=resource_type,
            resourceId=resource_id,
            limit=limit,
        )

        items = resp.get("configurationItems", [])
        if not items:
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "history": [],
                "changes_detected": 0,
                "first_seen": None,
                "last_seen": None,
                "was_deleted": False,
            }

        history = []
        for item in items:
            capture_time = item.get("configurationItemCaptureTime")
            history.append({
                "configuration_item_capture_time": str(capture_time) if capture_time else None,
                "configuration_item_status": item.get("configurationItemStatus"),
                "configuration": item.get("configuration", {}),
                "relationships": item.get("relationships", []),
                "tags": item.get("tags", {}),
            })

        statuses = [h.get("configuration_item_status") for h in history]
        was_deleted = any("Deleted" in (s or "") for s in statuses)

        times = [item.get("configurationItemCaptureTime") for item in items if item.get("configurationItemCaptureTime")]
        first_seen = str(min(times)) if times else None
        last_seen = str(max(times)) if times else None

        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "history": history,
            "changes_detected": len(history),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "was_deleted": was_deleted,
        }
    except Exception as e:
        logger.error(f"config get_resource_config_history ({resource_type}/{resource_id}): {type(e).__name__}")
        return {
            "error": str(e),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "history": [],
        }


async def list_noncompliant_resources(session) -> list:
    """
    List all resources currently failing AWS Config compliance rules.
    Quick surface of known misconfigurations across the account.
    """
    try:
        client = session.client("config")

        # Get all config rules
        rules = []
        paginator = client.get_paginator("describe_config_rules")
        for page in paginator.paginate():
            rules.extend(page.get("ConfigRules", []))

        noncompliant = []
        for rule in rules:
            rule_name = rule.get("ConfigRuleName")
            rule_desc = rule.get("Description", "")
            try:
                comp_paginator = client.get_paginator("get_compliance_details_by_config_rule")
                resources = []
                for page in comp_paginator.paginate(
                    ConfigRuleName=rule_name,
                    ComplianceTypes=["NON_COMPLIANT"],
                ):
                    for result in page.get("EvaluationResults", []):
                        resource_id_info = result.get("EvaluationResultIdentifier", {}).get(
                            "EvaluationResultQualifier", {}
                        )
                        resources.append({
                            "resource_type": resource_id_info.get("ResourceType"),
                            "resource_id": resource_id_info.get("ResourceId"),
                            "annotation": result.get("Annotation", ""),
                        })

                if resources:
                    noncompliant.append({
                        "rule_name": rule_name,
                        "rule_description": rule_desc,
                        "non_compliant_resources": resources,
                    })
            except Exception:
                continue

        return noncompliant
    except Exception as e:
        logger.error(f"config list_noncompliant_resources: {type(e).__name__}")
        return []


async def get_resource_relationships(
    session,
    resource_type: str,
    resource_id: str,
) -> dict:
    """
    Get all AWS resources connected to a specific resource according to AWS Config.
    Shows what an EC2 instance is attached to, what a security group is used by, etc.
    """
    try:
        client = session.client("config")

        # Fetch current config for the resource
        resp = client.batch_get_resource_config(
            resourceKeys=[{"resourceType": resource_type, "resourceId": resource_id}]
        )

        items = resp.get("baseConfigurationItems", [])
        if not items:
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "related_resources": [],
                "error": "Resource not found in AWS Config",
            }

        item = items[0]
        raw_relationships = item.get("relationships", [])

        related = []
        for rel in raw_relationships:
            related.append({
                "resource_type": rel.get("resourceType"),
                "resource_id": rel.get("resourceId"),
                "relationship_name": rel.get("relationshipName"),
            })

        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "related_resources": related,
        }
    except Exception as e:
        logger.error(f"config get_resource_relationships ({resource_type}/{resource_id}): {type(e).__name__}")
        return {
            "error": str(e),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "related_resources": [],
        }

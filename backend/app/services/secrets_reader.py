"""
Secrets Manager reader — metadata only.
secretsmanager.get_secret_value is structurally absent from this file.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _days_since(dt) -> int | None:
    if not dt:
        return None
    if isinstance(dt, datetime):
        ts = dt
    else:
        try:
            ts = datetime.fromisoformat(str(dt))
        except Exception:
            return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (_utcnow() - ts).days


def _parse_tags(tag_list: list) -> dict:
    if not tag_list:
        return {}
    return {t.get("Key", ""): t.get("Value", "") for t in tag_list}


def _is_rotation_overdue(rotation_enabled: bool, last_rotated_date) -> bool:
    if not rotation_enabled:
        return True
    if last_rotated_date is None:
        return True
    days = _days_since(last_rotated_date)
    return (days or 0) > 90


async def list_secrets(session) -> list:
    """
    List all Secrets Manager secrets with rotation status and last-accessed date.
    Never calls GetSecretValue.
    """
    try:
        client = session.client("secretsmanager")
        secrets = []
        paginator = client.get_paginator("list_secrets")
        for page in paginator.paginate():
            for s in page.get("SecretList", []):
                rotation_enabled = s.get("RotationEnabled", False)
                last_rotated = s.get("LastRotatedDate")
                days_since_rotation = _days_since(last_rotated)
                overdue = _is_rotation_overdue(rotation_enabled, last_rotated)

                secrets.append({
                    "name": s.get("Name"),
                    "arn": s.get("ARN"),
                    "description": s.get("Description", ""),
                    "last_rotated_date": str(last_rotated) if last_rotated else None,
                    "last_accessed_date": str(s.get("LastAccessedDate", "")) or None,
                    "last_changed_date": str(s.get("LastChangedDate", "")) or None,
                    "rotation_enabled": rotation_enabled,
                    "rotation_overdue": overdue,
                    "tags": _parse_tags(s.get("Tags", [])),
                    "days_since_rotation": days_since_rotation,
                })
        return secrets
    except Exception as e:
        logger.error(f"secrets list_secrets: {type(e).__name__}")
        return []


async def get_secret_details(session, secret_name: str) -> dict:
    """
    Full metadata and security analysis for a single secret.
    Never calls GetSecretValue.
    """
    try:
        client = session.client("secretsmanager")
        desc = client.describe_secret(SecretId=secret_name)

        rotation_enabled = desc.get("RotationEnabled", False)
        last_rotated = desc.get("LastRotatedDate")
        last_accessed = desc.get("LastAccessedDate")
        last_changed = desc.get("LastChangedDate")
        days_since_rotation = _days_since(last_rotated)
        overdue = _is_rotation_overdue(rotation_enabled, last_rotated)

        # Resource policy
        resource_policy = None
        policy_allows_external = False
        try:
            pol = client.get_resource_policy(SecretId=secret_name)
            raw = pol.get("ResourcePolicy")
            if raw:
                resource_policy = json.loads(raw)
                for stmt in resource_policy.get("Statement", []):
                    principal = stmt.get("Principal", {})
                    if principal == "*":
                        policy_allows_external = True
                    aws_principals = principal.get("AWS", []) if isinstance(principal, dict) else []
                    if isinstance(aws_principals, str):
                        aws_principals = [aws_principals]
                    if "*" in aws_principals:
                        policy_allows_external = True
        except Exception:
            pass

        # Security findings
        security_findings = []
        if not rotation_enabled:
            security_findings.append("Rotation disabled — secret is static")
        if days_since_rotation and days_since_rotation > 90:
            security_findings.append(f"Secret not rotated in {days_since_rotation} days")
        if last_accessed is None and last_changed:
            days_unused = _days_since(last_changed)
            if (days_unused or 0) > 180:
                security_findings.append(
                    f"Secret appears unused — last changed {days_unused} days ago, never accessed"
                )
        if resource_policy and policy_allows_external:
            security_findings.append("Secret resource policy allows public/external access")

        return {
            "name": desc.get("Name"),
            "arn": desc.get("ARN"),
            "description": desc.get("Description", ""),
            "rotation_enabled": rotation_enabled,
            "rotation_lambda_arn": desc.get("RotationLambdaARN"),
            "last_rotated_date": str(last_rotated) if last_rotated else None,
            "last_accessed_date": str(last_accessed) if last_accessed else None,
            "last_changed_date": str(last_changed) if last_changed else None,
            "days_since_rotation": days_since_rotation,
            "resource_policy": resource_policy,
            "policy_allows_external": policy_allows_external,
            "tags": _parse_tags(desc.get("Tags", [])),
            "security_findings": security_findings,
        }
    except Exception as e:
        logger.error(f"secrets get_secret_details {secret_name}: {type(e).__name__}")
        return {"error": str(e), "name": secret_name}


async def get_secrets_security_summary(session) -> dict:
    """
    Account-wide secrets hygiene summary.
    """
    secrets = await list_secrets(session)
    if not secrets:
        return {
            "total_secrets": 0,
            "rotation_disabled_count": 0,
            "overdue_rotation_count": 0,
            "externally_accessible_count": 0,
            "high_risk_secrets": [],
            "summary": "No secrets found in this account.",
        }

    rotation_disabled = [s for s in secrets if not s.get("rotation_enabled")]
    overdue = [s for s in secrets if s.get("rotation_overdue")]
    high_risk = []

    for s in overdue:
        findings = []
        if not s.get("rotation_enabled"):
            findings.append("Rotation disabled")
        days = s.get("days_since_rotation")
        if days and days > 90:
            findings.append(f"Not rotated in {days} days")
        if findings:
            high_risk.append({"name": s.get("name"), "findings": findings})

    summary = (
        f"{len(secrets)} secrets total. "
        f"{len(rotation_disabled)} with rotation disabled, "
        f"{len(overdue)} overdue for rotation."
    )

    return {
        "total_secrets": len(secrets),
        "rotation_disabled_count": len(rotation_disabled),
        "overdue_rotation_count": len(overdue),
        "externally_accessible_count": 0,
        "high_risk_secrets": high_risk[:10],
        "summary": summary,
    }

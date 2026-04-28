"""
KMS reader service — metadata only, no cryptographic operations.
kms:Decrypt, kms:Encrypt, kms:GenerateDataKey are structurally absent.
"""

import json
import logging
from datetime import datetime, timezone, timedelta

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


async def list_keys(session) -> list:
    """
    List all customer-managed KMS keys with rotation status and aliases.
    AWS-managed keys (aws/* prefix) are excluded.
    """
    try:
        client = session.client("kms")

        # Fetch all aliases once to map key_id → alias names
        alias_map: dict[str, list] = {}
        try:
            alias_paginator = client.get_paginator("list_aliases")
            for page in alias_paginator.paginate():
                for alias in page.get("Aliases", []):
                    name = alias.get("AliasName", "")
                    if name.startswith("alias/aws/"):
                        continue
                    target = alias.get("TargetKeyId")
                    if target:
                        alias_map.setdefault(target, []).append(name)
        except Exception:
            pass

        keys = []
        paginator = client.get_paginator("list_keys")
        for page in paginator.paginate():
            for key_ref in page.get("Keys", []):
                key_id = key_ref.get("KeyId")
                try:
                    desc = client.describe_key(KeyId=key_id)
                    meta = desc.get("KeyMetadata", {})

                    # Skip AWS-managed keys
                    if meta.get("KeyManager") == "AWS":
                        continue

                    deletion_date = meta.get("DeletionDate")
                    keys.append({
                        "key_id": key_id,
                        "key_arn": meta.get("Arn"),
                        "description": meta.get("Description", ""),
                        "key_state": meta.get("KeyState"),
                        "key_usage": meta.get("KeyUsage"),
                        "creation_date": str(meta.get("CreationDate", "")),
                        "deletion_date": str(deletion_date) if deletion_date else None,
                        "multi_region": meta.get("MultiRegion", False),
                        "aliases": alias_map.get(key_id, []),
                    })
                except Exception:
                    continue

        return keys
    except Exception as e:
        logger.error(f"kms list_keys: {type(e).__name__}")
        return []


async def get_key_details(session, key_id: str) -> dict:
    """
    Full details for a KMS key: policy, grants, rotation status, security findings.
    Never calls Decrypt/Encrypt/GenerateDataKey.
    """
    try:
        client = session.client("kms")
        desc = client.describe_key(KeyId=key_id)
        meta = desc.get("KeyMetadata", {})

        # Rotation status
        rotation_enabled = False
        try:
            rot = client.get_key_rotation_status(KeyId=key_id)
            rotation_enabled = rot.get("KeyRotationEnabled", False)
        except Exception:
            pass

        # Creation date for rotation_overdue check (>365 days without rotation)
        created = meta.get("CreationDate")
        days_old = _days_since(created)
        rotation_overdue = (not rotation_enabled) and (days_old or 0) > 365

        # Key policy
        policy_doc = {}
        policy_allows_external = False
        try:
            pol = client.get_key_policy(KeyId=key_id, PolicyName="default")
            raw = pol.get("Policy", "{}")
            policy_doc = json.loads(raw)
            # Check for Principal: "*" or cross-account principals
            for stmt in policy_doc.get("Statement", []):
                principal = stmt.get("Principal", {})
                if principal == "*":
                    policy_allows_external = True
                    break
                aws_principals = principal.get("AWS", [])
                if isinstance(aws_principals, str):
                    aws_principals = [aws_principals]
                for p in aws_principals:
                    if p == "*":
                        policy_allows_external = True
                        break
        except Exception:
            pass

        # Grants
        grants = []
        try:
            grant_paginator = client.get_paginator("list_grants")
            for page in grant_paginator.paginate(KeyId=key_id):
                for g in page.get("Grants", []):
                    grants.append({
                        "grant_id": g.get("GrantId"),
                        "grantee_principal": g.get("GranteePrincipal"),
                        "operations": g.get("Operations", []),
                        "creation_date": str(g.get("CreationDate", "")),
                    })
        except Exception:
            pass

        # Security findings
        security_findings = []
        if not rotation_enabled:
            security_findings.append("Key rotation disabled")
        if rotation_overdue:
            security_findings.append(f"Key is {days_old} days old with rotation disabled")
        if policy_allows_external:
            security_findings.append("Key policy allows external/public access (Principal: *)")
        deletion_date = meta.get("DeletionDate")
        if deletion_date:
            security_findings.append(f"Key scheduled for deletion on {deletion_date}")
        if meta.get("KeyState") == "Disabled":
            security_findings.append("Key is currently disabled")

        return {
            "key_id": key_id,
            "key_arn": meta.get("Arn"),
            "key_state": meta.get("KeyState"),
            "rotation_enabled": rotation_enabled,
            "rotation_overdue": rotation_overdue,
            "policy": policy_doc,
            "policy_allows_external": policy_allows_external,
            "grants": grants,
            "security_findings": security_findings,
        }
    except Exception as e:
        logger.error(f"kms get_key_details {key_id}: {type(e).__name__}")
        return {"error": str(e), "key_id": key_id}


async def list_aliases(session) -> list:
    """List customer-managed KMS key aliases (excludes aws/* prefixed aliases)."""
    try:
        client = session.client("kms")
        aliases = []
        paginator = client.get_paginator("list_aliases")
        for page in paginator.paginate():
            for alias in page.get("Aliases", []):
                name = alias.get("AliasName", "")
                if name.startswith("alias/aws/"):
                    continue
                aliases.append({
                    "alias_name": name,
                    "target_key_id": alias.get("TargetKeyId"),
                    "creation_date": str(alias.get("CreationDate", "")),
                })
        return aliases
    except Exception as e:
        logger.error(f"kms list_aliases: {type(e).__name__}")
        return []

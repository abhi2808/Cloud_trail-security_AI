"""
IAM reader service — read-only IAM/STS operations.
All functions take an explicit boto3 Session created from decrypted account credentials.
Credentials are NEVER logged or surfaced in error messages.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_stale(created_at) -> bool:
    """Return True if a key is older than 90 days."""
    if not created_at:
        return False
    if isinstance(created_at, datetime):
        ts = created_at
    else:
        ts = datetime.fromisoformat(str(created_at))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (_utcnow() - ts).days > 90


def _extract_services_from_policies(policy_documents: list) -> list[str]:
    """
    Scan policy documents and extract unique AWS service prefixes from Action fields.
    e.g. "ec2:DescribeInstances" → "ec2"
    """
    services = set()
    for doc in policy_documents:
        if not isinstance(doc, dict):
            continue
        statements = doc.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]
        for stmt in statements:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            for action in actions:
                if ":" in action:
                    services.add(action.split(":")[0].lower())
                elif action == "*":
                    services.add("all")
    return sorted(services)


async def get_caller_identity(session) -> dict:
    """Call STS GetCallerIdentity to verify account and identity."""
    try:
        client = session.client("sts")
        resp = client.get_caller_identity()
        return {
            "account_id": resp.get("Account"),
            "user_id": resp.get("UserId"),
            "arn": resp.get("Arn"),
        }
    except Exception as e:
        logger.error(f"get_caller_identity failed: {type(e).__name__}")
        return {"error": str(e)}


async def list_users(session) -> list[dict]:
    """List all IAM users with basic profile info. Paginates automatically."""
    try:
        client = session.client("iam")
        users = []
        paginator = client.get_paginator("list_users")
        for page in paginator.paginate():
            for u in page.get("Users", []):
                users.append({
                    "username": u.get("UserName"),
                    "user_id": u.get("UserId"),
                    "arn": u.get("Arn"),
                    "created_at": str(u.get("CreateDate", "")),
                    "password_last_used": str(u.get("PasswordLastUsed", "Never")),
                })
        return users
    except Exception as e:
        logger.error(f"list_users failed: {type(e).__name__}")
        return []


async def list_roles(session) -> list[dict]:
    """List all IAM roles. Paginates automatically."""
    try:
        client = session.client("iam")
        roles = []
        paginator = client.get_paginator("list_roles")
        for page in paginator.paginate():
            for r in page.get("Roles", []):
                roles.append({
                    "role_name": r.get("RoleName"),
                    "role_id": r.get("RoleId"),
                    "arn": r.get("Arn"),
                    "trust_policy": r.get("AssumeRolePolicyDocument", {}),
                    "created_at": str(r.get("CreateDate", "")),
                })
        return roles
    except Exception as e:
        logger.error(f"list_roles failed: {type(e).__name__}")
        return []


async def get_user_permissions(session, username: str) -> dict:
    """
    Comprehensive permission fetch for a single IAM user.
    Fetches managed policies, inline policies, and group memberships.
    Derives effective_services from all policy documents.
    """
    client = session.client("iam")
    all_policy_docs = []
    result = {
        "username": username,
        "managed_policies": [],
        "inline_policies": [],
        "group_memberships": [],
        "effective_services": [],
    }

    try:
        # Step 1: managed user policies
        paginator = client.get_paginator("list_attached_user_policies")
        for page in paginator.paginate(UserName=username):
            for p in page.get("AttachedPolicies", []):
                policy_doc = _fetch_managed_policy_document(client, p["PolicyArn"])
                result["managed_policies"].append({
                    "name": p["PolicyName"],
                    "arn": p["PolicyArn"],
                    "document": policy_doc,
                })
                all_policy_docs.append(policy_doc)
    except Exception as e:
        logger.warning(f"list_attached_user_policies for {username}: {type(e).__name__}")

    try:
        # Step 2: inline user policies
        paginator = client.get_paginator("list_user_policies")
        for page in paginator.paginate(UserName=username):
            for policy_name in page.get("PolicyNames", []):
                try:
                    resp = client.get_user_policy(UserName=username, PolicyName=policy_name)
                    doc = resp.get("PolicyDocument", {})
                    result["inline_policies"].append({"name": policy_name, "document": doc})
                    all_policy_docs.append(doc)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"list_user_policies for {username}: {type(e).__name__}")

    try:
        # Steps 3-5: group memberships
        groups_resp = client.list_groups_for_user(UserName=username)
        for group in groups_resp.get("Groups", []):
            group_name = group["GroupName"]
            group_policies = []

            # Group managed policies
            try:
                paginator = client.get_paginator("list_attached_group_policies")
                for page in paginator.paginate(GroupName=group_name):
                    for p in page.get("AttachedPolicies", []):
                        doc = _fetch_managed_policy_document(client, p["PolicyArn"])
                        group_policies.append({"name": p["PolicyName"], "arn": p["PolicyArn"], "document": doc})
                        all_policy_docs.append(doc)
            except Exception:
                pass

            # Group inline policies
            try:
                paginator = client.get_paginator("list_group_policies")
                for page in paginator.paginate(GroupName=group_name):
                    for policy_name in page.get("PolicyNames", []):
                        try:
                            resp = client.get_group_policy(GroupName=group_name, PolicyName=policy_name)
                            doc = resp.get("PolicyDocument", {})
                            group_policies.append({"name": policy_name, "document": doc})
                            all_policy_docs.append(doc)
                        except Exception:
                            pass
            except Exception:
                pass

            result["group_memberships"].append({
                "group_name": group_name,
                "policies": group_policies,
            })
    except Exception as e:
        logger.warning(f"list_groups_for_user for {username}: {type(e).__name__}")

    result["effective_services"] = _extract_services_from_policies(all_policy_docs)
    return result


async def get_role_permissions(session, role_name: str) -> dict:
    """
    Comprehensive permission fetch for an IAM role.
    Includes trust policy showing who can assume the role.
    """
    client = session.client("iam")
    all_policy_docs = []
    result = {
        "role_name": role_name,
        "trust_policy": {},
        "managed_policies": [],
        "inline_policies": [],
        "effective_services": [],
    }

    try:
        role_resp = client.get_role(RoleName=role_name)
        result["trust_policy"] = role_resp["Role"].get("AssumeRolePolicyDocument", {})
    except Exception as e:
        logger.warning(f"get_role for {role_name}: {type(e).__name__}")

    try:
        paginator = client.get_paginator("list_attached_role_policies")
        for page in paginator.paginate(RoleName=role_name):
            for p in page.get("AttachedPolicies", []):
                doc = _fetch_managed_policy_document(client, p["PolicyArn"])
                result["managed_policies"].append({"name": p["PolicyName"], "arn": p["PolicyArn"], "document": doc})
                all_policy_docs.append(doc)
    except Exception as e:
        logger.warning(f"list_attached_role_policies for {role_name}: {type(e).__name__}")

    try:
        paginator = client.get_paginator("list_role_policies")
        for page in paginator.paginate(RoleName=role_name):
            for policy_name in page.get("PolicyNames", []):
                try:
                    resp = client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                    doc = resp.get("PolicyDocument", {})
                    result["inline_policies"].append({"name": policy_name, "document": doc})
                    all_policy_docs.append(doc)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"list_role_policies for {role_name}: {type(e).__name__}")

    result["effective_services"] = _extract_services_from_policies(all_policy_docs)
    return result


async def list_access_keys(session, username: str) -> list[dict]:
    """
    List access keys for an IAM user. Flags stale keys (>90 days old).
    Never returns the secret key — it's not available via the IAM API.
    """
    try:
        client = session.client("iam")
        resp = client.list_access_keys(UserName=username)
        keys = []
        for k in resp.get("AccessKeyMetadata", []):
            created = k.get("CreateDate")
            keys.append({
                "access_key_id": k.get("AccessKeyId"),
                "status": k.get("Status"),
                "created_at": str(created),
                "stale": _is_stale(created),
            })
        return keys
    except Exception as e:
        logger.error(f"list_access_keys for {username}: {type(e).__name__}")
        return []


async def simulate_permissions(
    session,
    principal_arn: str,
    actions: list[str],
    resource_arn: str = "*",
) -> dict:
    """
    Simulate whether a principal is allowed to perform specific actions.
    Limits actions to 100 per API call.
    """
    try:
        client = session.client("iam")
        actions = actions[:100]
        resp = client.simulate_principal_policy(
            PolicySourceArn=principal_arn,
            ActionNames=actions,
            ResourceArns=[resource_arn],
        )
        results = []
        for r in resp.get("EvaluationResults", []):
            results.append({
                "action": r.get("EvalActionName"),
                "decision": "allowed" if r.get("EvalDecision") == "allowed" else "denied",
                "reason": r.get("EvalDecision"),
            })
        return {"principal": principal_arn, "results": results}
    except Exception as e:
        logger.error(f"simulate_permissions for {principal_arn}: {type(e).__name__}")
        return {"principal": principal_arn, "results": [], "error": str(e)}


# ─── Internal helper ──────────────────────────────────────────────────────────

def _fetch_managed_policy_document(client, policy_arn: str) -> dict:
    """Fetch the default version document of a managed policy."""
    try:
        policy_resp = client.get_policy(PolicyArn=policy_arn)
        default_version = policy_resp["Policy"]["DefaultVersionId"]
        version_resp = client.get_policy_version(PolicyArn=policy_arn, VersionId=default_version)
        return version_resp["PolicyVersion"].get("Document", {})
    except Exception:
        return {}

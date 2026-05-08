"""
S3 reader service — metadata only, no object reads.
All functions take an explicit boto3 Session.
"""
import logging
logger = logging.getLogger(__name__)


async def list_buckets_summary(session, query_region: str = None) -> list:
    """
    List all S3 buckets with location and public-access-block status.
    Never reads object contents. Filters by query_region if provided.
    """
    try:
        client = session.client("s3")
        resp = client.list_buckets()
        buckets = []
        for b in resp.get("Buckets", []):
            name = b.get("Name")
            creation_date = str(b.get("CreationDate", ""))
            region = "unknown"
            public_blocked = False

            try:
                loc = client.get_bucket_location(Bucket=name)
                region = loc.get("LocationConstraint") or "us-east-1"
            except Exception:
                pass

            if query_region and query_region != "all" and region != query_region:
                continue

            try:
                pab = client.get_public_access_block(Bucket=name)
                cfg = pab.get("PublicAccessBlockConfiguration", {})
                public_blocked = all([
                    cfg.get("BlockPublicAcls", False),
                    cfg.get("IgnorePublicAcls", False),
                    cfg.get("BlockPublicPolicy", False),
                    cfg.get("RestrictPublicBuckets", False),
                ])
            except Exception as pab_err:
                # NoSuchPublicAccessBlockConfiguration → block not configured → public
                # Catch by string to avoid AttributeError on older boto3 builds
                if "NoSuchPublicAccessBlockConfiguration" in type(pab_err).__name__:
                    public_blocked = False
                else:
                    public_blocked = False

            buckets.append({
                "bucket_name": name,
                "region": region,
                "public_access_blocked": public_blocked,
                "creation_date": creation_date,
            })
        return buckets
    except Exception as e:
        logger.error(f"list_buckets_summary: {type(e).__name__}: {e}")
        # Return error dict — NOT an empty list. An empty list is indistinguishable
        # from "account has 0 buckets" and causes the agent to report "no exposure"
        # when the check actually failed.
        return {"error": f"S3 list failed: {type(e).__name__}: {str(e)}"}


async def get_bucket_policy_summary(session, bucket_name: str) -> dict:
    """
    Check if an S3 bucket has a public bucket policy or permissive ACL.
    """
    client = session.client("s3")
    result = {
        "bucket_name": bucket_name,
        "has_policy": False,
        "policy_allows_public": False,
        "acl_grants": [],
    }

    try:
        import json
        pol = client.get_bucket_policy(Bucket=bucket_name)
        doc = json.loads(pol.get("Policy", "{}"))
        result["has_policy"] = True
        stmts = doc.get("Statement", [])
        for stmt in stmts:
            principal = stmt.get("Principal", "")
            if principal == "*" or (isinstance(principal, dict) and "*" in principal.get("AWS", [])):
                result["policy_allows_public"] = True
                break
    except Exception:
        pass

    try:
        acl = client.get_bucket_acl(Bucket=bucket_name)
        for grant in acl.get("Grants", []):
            grantee = grant.get("Grantee", {})
            result["acl_grants"].append({
                "grantee": grantee.get("DisplayName") or grantee.get("URI", "unknown"),
                "permission": grant.get("Permission"),
            })
    except Exception:
        pass

    return result

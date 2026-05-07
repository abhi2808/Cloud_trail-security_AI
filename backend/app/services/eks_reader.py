"""
EKS reader service — cluster and node group metadata only.
eks:AccessKubernetesApi is structurally absent (K8s API access not permitted).
"""
import logging

logger = logging.getLogger(__name__)


async def list_clusters(session) -> list:
    """List all EKS clusters in the region with basic security metadata."""
    try:
        client = session.client("eks")
        cluster_names = []
        paginator = client.get_paginator("list_clusters")
        for page in paginator.paginate():
            cluster_names.extend(page.get("clusters", []))

        clusters = []
        for name in cluster_names:
            try:
                resp = client.describe_cluster(name=name)
                c = resp.get("cluster", {})
                logging_types = [
                    t["type"]
                    for t in c.get("logging", {}).get("clusterLogging", [])
                    if t.get("enabled")
                ]
                resources_vpc = c.get("resourcesVpcConfig", {})
                findings = []
                if resources_vpc.get("endpointPublicAccess", False):
                    findings.append("⚠️ Kubernetes API endpoint is PUBLIC — accessible from internet")
                if not c.get("encryptionConfig"):
                    findings.append("Secrets encryption (KMS) not configured on this cluster")
                if not logging_types:
                    findings.append("No control-plane logging enabled — API activity is unaudited")

                clusters.append({
                    "name": c.get("name"),
                    "arn": c.get("arn"),
                    "status": c.get("status"),
                    "kubernetes_version": c.get("version"),
                    "role_arn": c.get("roleArn"),
                    "endpoint_public_access": resources_vpc.get("endpointPublicAccess", False),
                    "endpoint_private_access": resources_vpc.get("endpointPrivateAccess", False),
                    "public_access_cidrs": resources_vpc.get("publicAccessCidrs", []),
                    "logging_enabled_types": logging_types,
                    "encryption_config": bool(c.get("encryptionConfig")),
                    "tags": c.get("tags", {}),
                    "created_at": str(c.get("createdAt", "")),
                    "security_findings": findings,
                })
            except Exception as e:
                logger.warning(f"eks describe_cluster({name}): {type(e).__name__}")
                clusters.append({"name": name, "error": str(e)})

        return clusters
    except Exception as e:
        logger.error(f"eks list_clusters: {type(e).__name__}: {e}")
        return [{"error": str(e)}]


async def describe_cluster(session, cluster_name: str) -> dict:
    """
    Get full security metadata for a specific EKS cluster including
    node groups, Fargate profiles, and add-ons.
    """
    try:
        client = session.client("eks")

        # ── Cluster details ──────────────────────────────────────────────
        resp = client.describe_cluster(name=cluster_name)
        c = resp.get("cluster", {})
        resources_vpc = c.get("resourcesVpcConfig", {})
        logging_types = [
            t["type"]
            for t in c.get("logging", {}).get("clusterLogging", [])
            if t.get("enabled")
        ]

        findings = []
        if resources_vpc.get("endpointPublicAccess", False):
            public_cidrs = resources_vpc.get("publicAccessCidrs", [])
            if "0.0.0.0/0" in public_cidrs or not public_cidrs:
                findings.append("⚠️ CRITICAL: Kubernetes API endpoint is PUBLIC and open to 0.0.0.0/0")
            else:
                findings.append(f"⚠️ Kubernetes API endpoint is PUBLIC but restricted to: {public_cidrs}")
        if not c.get("encryptionConfig"):
            findings.append("Secrets encryption (KMS) not configured")
        if not logging_types:
            findings.append("⚠️ No control-plane logging — API server activity is unaudited")
        elif "audit" not in logging_types:
            findings.append("Audit logging not enabled — cannot attribute API calls to identities")

        # ── Node groups ──────────────────────────────────────────────────
        node_groups = []
        try:
            ng_resp = client.list_nodegroups(clusterName=cluster_name)
            for ng_name in ng_resp.get("nodegroups", []):
                try:
                    ng = client.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng_name)
                    ng_data = ng.get("nodegroup", {})
                    node_groups.append({
                        "name": ng_data.get("nodegroupName"),
                        "status": ng_data.get("status"),
                        "instance_types": ng_data.get("instanceTypes", []),
                        "scaling": ng_data.get("scalingConfig", {}),
                        "ami_type": ng_data.get("amiType"),
                        "node_role": ng_data.get("nodeRole"),
                        "disk_size_gb": ng_data.get("diskSize"),
                    })
                except Exception:
                    node_groups.append({"name": ng_name, "error": "describe failed"})
        except Exception:
            pass

        # ── Fargate profiles ─────────────────────────────────────────────
        fargate_profiles = []
        try:
            fg_resp = client.list_fargate_profiles(clusterName=cluster_name)
            fargate_profiles = fg_resp.get("fargateProfileNames", [])
        except Exception:
            pass

        # ── Add-ons ──────────────────────────────────────────────────────
        addons = []
        try:
            ao_resp = client.list_addons(clusterName=cluster_name)
            for addon_name in ao_resp.get("addons", []):
                try:
                    ao = client.describe_addon(clusterName=cluster_name, addonName=addon_name)
                    ao_data = ao.get("addon", {})
                    addons.append({
                        "name": ao_data.get("addonName"),
                        "version": ao_data.get("addonVersion"),
                        "status": ao_data.get("status"),
                        "service_account_role": ao_data.get("serviceAccountRoleArn"),
                    })
                except Exception:
                    addons.append({"name": addon_name, "error": "describe failed"})
        except Exception:
            pass

        return {
            "name": c.get("name"),
            "arn": c.get("arn"),
            "status": c.get("status"),
            "kubernetes_version": c.get("version"),
            "role_arn": c.get("roleArn"),
            "endpoint_public_access": resources_vpc.get("endpointPublicAccess", False),
            "endpoint_private_access": resources_vpc.get("endpointPrivateAccess", False),
            "public_access_cidrs": resources_vpc.get("publicAccessCidrs", []),
            "security_group_ids": resources_vpc.get("securityGroupIds", []),
            "logging_enabled_types": logging_types,
            "encryption_config": bool(c.get("encryptionConfig")),
            "created_at": str(c.get("createdAt", "")),
            "tags": c.get("tags", {}),
            "node_groups": node_groups,
            "fargate_profiles": fargate_profiles,
            "addons": addons,
            "security_findings": findings,
        }
    except Exception as e:
        logger.error(f"eks describe_cluster({cluster_name}): {type(e).__name__}: {e}")
        return {"error": str(e), "cluster_name": cluster_name}

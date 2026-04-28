"""
RDS reader service — metadata only.
rds:DownloadDBLogFilePortion and rds:DownloadCompleteDBLogFile are structurally absent.
"""

import logging

logger = logging.getLogger(__name__)


def _parse_tags(tag_list: list) -> dict:
    if not tag_list:
        return {}
    return {t.get("Key", ""): t.get("Value", "") for t in tag_list}


def _instance_findings(inst: dict) -> list:
    findings = []
    if inst.get("publicly_accessible"):
        findings.append("Database publicly accessible — verify this is intentional")
    if not inst.get("storage_encrypted"):
        findings.append("Storage encryption disabled")
    if not inst.get("multi_az") and inst.get("status") == "available":
        findings.append("Single-AZ deployment — no high availability")
    return findings


async def list_databases(session) -> list:
    """
    List all RDS DB instances with key security metadata and findings.
    """
    try:
        client = session.client("rds")
        instances = []
        paginator = client.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            for db in page.get("DBInstances", []):
                sg_ids = [sg["VpcSecurityGroupId"] for sg in db.get("VpcSecurityGroups", [])]
                record = {
                    "db_identifier": db.get("DBInstanceIdentifier"),
                    "db_engine": db.get("Engine"),
                    "engine_version": db.get("EngineVersion"),
                    "db_instance_class": db.get("DBInstanceClass"),
                    "status": db.get("DBInstanceStatus"),
                    "publicly_accessible": db.get("PubliclyAccessible", False),
                    "storage_encrypted": db.get("StorageEncrypted", False),
                    "multi_az": db.get("MultiAZ", False),
                    "endpoint_address": db.get("Endpoint", {}).get("Address"),
                    "endpoint_port": db.get("Endpoint", {}).get("Port"),
                    "vpc_id": db.get("DBSubnetGroup", {}).get("VpcId"),
                    "security_group_ids": sg_ids,
                    "tags": _parse_tags(db.get("TagList", [])),
                }
                record["security_findings"] = _instance_findings(record)
                instances.append(record)
        return instances
    except Exception as e:
        logger.error(f"rds list_databases: {type(e).__name__}")
        return []


async def get_database_details(session, db_identifier: str) -> dict:
    """
    Full details for a single RDS instance including backup, IAM auth, and log availability.
    Never reads log contents.
    """
    try:
        client = session.client("rds")
        resp = client.describe_db_instances(DBInstanceIdentifier=db_identifier)
        instances = resp.get("DBInstances", [])
        if not instances:
            return {"error": f"Database {db_identifier} not found"}

        db = instances[0]
        sg_ids = [sg["VpcSecurityGroupId"] for sg in db.get("VpcSecurityGroups", [])]

        # Log files — names and sizes only, no content
        log_files = []
        try:
            log_resp = client.describe_db_log_files(DBInstanceIdentifier=db_identifier)
            for lf in log_resp.get("DescribeDBLogFiles", []):
                log_files.append({
                    "name": lf.get("LogFileName"),
                    "size_bytes": lf.get("Size"),
                    "last_written": str(lf.get("LastWritten", "")),
                })
        except Exception:
            pass

        backup_retention = db.get("BackupRetentionPeriod", 0)
        deletion_protection = db.get("DeletionProtection", False)
        iam_auth = db.get("IAMDatabaseAuthenticationEnabled", False)

        record = {
            "db_identifier": db.get("DBInstanceIdentifier"),
            "db_engine": db.get("Engine"),
            "engine_version": db.get("EngineVersion"),
            "db_instance_class": db.get("DBInstanceClass"),
            "status": db.get("DBInstanceStatus"),
            "publicly_accessible": db.get("PubliclyAccessible", False),
            "storage_encrypted": db.get("StorageEncrypted", False),
            "multi_az": db.get("MultiAZ", False),
            "endpoint_address": db.get("Endpoint", {}).get("Address"),
            "endpoint_port": db.get("Endpoint", {}).get("Port"),
            "vpc_id": db.get("DBSubnetGroup", {}).get("VpcId"),
            "security_group_ids": sg_ids,
            "parameter_group": [pg["DBParameterGroupName"] for pg in db.get("DBParameterGroups", [])],
            "option_group": [og["OptionGroupName"] for og in db.get("OptionGroupMemberships", [])],
            "backup_retention_days": backup_retention,
            "deletion_protection": deletion_protection,
            "iam_authentication_enabled": iam_auth,
            "log_files_available": log_files,
            "tags": _parse_tags(db.get("TagList", [])),
        }

        # Build security findings
        findings = _instance_findings(record)
        if not deletion_protection:
            findings.append("Deletion protection disabled")
        if not iam_auth:
            findings.append("IAM database authentication disabled — using password only")
        if backup_retention < 7:
            findings.append(f"Low backup retention: {backup_retention} days (recommended ≥7)")
        record["security_findings"] = findings

        return record
    except Exception as e:
        logger.error(f"rds get_database_details {db_identifier}: {type(e).__name__}")
        return {"error": str(e), "db_identifier": db_identifier}


async def list_snapshots(session) -> list:
    """
    List manual RDS snapshots and flag any that are publicly shared.
    A public RDS snapshot is a critical data exposure finding.
    """
    try:
        client = session.client("rds")
        snapshots = []
        paginator = client.get_paginator("describe_db_snapshots")
        for page in paginator.paginate(SnapshotType="manual"):
            for snap in page.get("DBSnapshots", []):
                # Check if the snapshot is shared with "all" (public)
                is_public = False
                try:
                    attr_resp = client.describe_db_snapshot_attributes(
                        DBSnapshotIdentifier=snap.get("DBSnapshotIdentifier")
                    )
                    attrs = attr_resp.get("DBSnapshotAttributesResult", {}).get("DBSnapshotAttributes", [])
                    for attr in attrs:
                        if attr.get("AttributeName") == "restore":
                            if "all" in attr.get("AttributeValues", []):
                                is_public = True
                except Exception:
                    pass

                snapshots.append({
                    "snapshot_id": snap.get("DBSnapshotIdentifier"),
                    "db_identifier": snap.get("DBInstanceIdentifier"),
                    "snapshot_type": snap.get("SnapshotType"),
                    "status": snap.get("Status"),
                    "encrypted": snap.get("Encrypted", False),
                    "created_time": str(snap.get("SnapshotCreateTime", "")),
                    "is_public": is_public,
                })

        return snapshots
    except Exception as e:
        logger.error(f"rds list_snapshots: {type(e).__name__}")
        return []

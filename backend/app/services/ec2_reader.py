"""
EC2 reader service — read-only EC2 and instance profile operations.
All functions take an explicit boto3 Session created from decrypted credentials.
Credentials are NEVER logged.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _parse_tags(tag_list: list) -> dict:
    """Convert AWS tag list [{Key, Value}] to a plain dict."""
    if not tag_list:
        return {}
    return {t.get("Key", ""): t.get("Value", "") for t in tag_list}


def _is_public_cidr(cidr: str) -> bool:
    """Return True if CIDR is the public internet."""
    return cidr in ("0.0.0.0/0", "::/0")


async def describe_instance(session, instance_id: str) -> dict:
    """
    Get full metadata for a single EC2 instance.
    Returns empty dict if instance not found.
    """
    try:
        client = session.client("ec2")
        resp = client.describe_instances(InstanceIds=[instance_id])
        reservations = resp.get("Reservations", [])
        if not reservations:
            return {"error": f"Instance {instance_id} not found"}

        inst = reservations[0]["Instances"][0]
        sgs = inst.get("SecurityGroups", [])
        metadata_options = inst.get("MetadataOptions", {})

        # IMDSv1 is enabled when HttpTokens == "optional"
        imdsv1_enabled = metadata_options.get("HttpTokens", "optional") == "optional"

        profile = inst.get("IamInstanceProfile")
        iam_instance_profile = profile.get("Arn") if profile else None

        return {
            "instance_id": inst.get("InstanceId"),
            "state": inst.get("State", {}).get("Name"),
            "instance_type": inst.get("InstanceType"),
            "launch_time": str(inst.get("LaunchTime", "")),
            "private_ip": inst.get("PrivateIpAddress"),
            "public_ip": inst.get("PublicIpAddress"),
            "vpc_id": inst.get("VpcId"),
            "subnet_id": inst.get("SubnetId"),
            "security_group_ids": [sg["GroupId"] for sg in sgs],
            "security_group_names": [sg["GroupName"] for sg in sgs],
            "iam_instance_profile": iam_instance_profile,
            "key_pair_name": inst.get("KeyName"),
            "tags": _parse_tags(inst.get("Tags", [])),
            "imdsv1_enabled": imdsv1_enabled,
        }
    except Exception as e:
        logger.error(f"describe_instance {instance_id}: {type(e).__name__}")
        return {"error": str(e), "instance_id": instance_id}


async def describe_security_group(session, sg_id: str) -> dict:
    """
    Get inbound/outbound rules for a security group.
    Flags rules open to the public internet.
    """
    try:
        client = session.client("ec2")
        resp = client.describe_security_groups(GroupIds=[sg_id])
        groups = resp.get("SecurityGroups", [])
        if not groups:
            return {"error": f"Security group {sg_id} not found"}

        sg = groups[0]

        def parse_rules(rule_list, direction="inbound"):
            rules = []
            for rule in rule_list:
                protocol = rule.get("IpProtocol", "-1")
                if protocol == "-1":
                    protocol = "all"
                from_port = rule.get("FromPort", "any")
                to_port = rule.get("ToPort", "any")
                port_range = f"{from_port}" if from_port == to_port else f"{from_port}-{to_port}"

                sources = []
                for r in rule.get("IpRanges", []):
                    cidr = r.get("CidrIp", "")
                    entry = {"cidr": cidr, "description": r.get("Description", "")}
                    if direction == "inbound":
                        entry["is_public"] = _is_public_cidr(cidr)
                    sources.append(entry)
                for r in rule.get("Ipv6Ranges", []):
                    cidr = r.get("CidrIpv6", "")
                    entry = {"cidr": cidr, "description": r.get("Description", "")}
                    if direction == "inbound":
                        entry["is_public"] = _is_public_cidr(cidr)
                    sources.append(entry)
                for r in rule.get("UserIdGroupPairs", []):
                    entry = {"sg_id": r.get("GroupId", ""), "description": r.get("Description", "")}
                    if direction == "inbound":
                        entry["is_public"] = False
                    sources.append(entry)

                if direction == "inbound":
                    rules.append({
                        "protocol": protocol,
                        "port_range": port_range,
                        "source": sources,
                        "is_public": any(s.get("is_public", False) for s in sources),
                    })
                else:
                    rules.append({
                        "protocol": protocol,
                        "port_range": port_range,
                        "destination": sources,
                    })
            return rules

        return {
            "sg_id": sg.get("GroupId"),
            "sg_name": sg.get("GroupName"),
            "description": sg.get("Description"),
            "vpc_id": sg.get("VpcId"),
            "inbound_rules": parse_rules(sg.get("IpPermissions", []), "inbound"),
            "outbound_rules": parse_rules(sg.get("IpPermissionsEgress", []), "outbound"),
        }
    except Exception as e:
        logger.error(f"describe_security_group {sg_id}: {type(e).__name__}")
        return {"error": str(e), "sg_id": sg_id}


async def list_instances(session) -> list[dict]:
    """
    List all EC2 instances with summary info. Paginates automatically.
    """
    try:
        client = session.client("ec2")
        instances = []
        paginator = client.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instances.append({
                        "instance_id": inst.get("InstanceId"),
                        "state": inst.get("State", {}).get("Name"),
                        "instance_type": inst.get("InstanceType"),
                        "private_ip": inst.get("PrivateIpAddress"),
                        "public_ip": inst.get("PublicIpAddress"),
                        "tags": _parse_tags(inst.get("Tags", [])),
                    })
        return instances
    except Exception as e:
        logger.error(f"list_instances: {type(e).__name__}")
        return []


async def get_instance_profile_role(session, instance_profile_arn: str) -> dict:
    """
    Extract the IAM role attached to an EC2 instance profile.
    Returns role name and ARN.
    """
    try:
        client = session.client("iam")
        # Extract profile name from ARN: arn:aws:iam::123:instance-profile/MyProfile
        profile_name = instance_profile_arn.split("/")[-1]
        resp = client.get_instance_profile(InstanceProfileName=profile_name)
        roles = resp.get("InstanceProfile", {}).get("Roles", [])
        if not roles:
            return {"instance_profile_arn": instance_profile_arn, "roles": []}
        role = roles[0]
        return {
            "instance_profile_arn": instance_profile_arn,
            "role_name": role.get("RoleName"),
            "role_arn": role.get("Arn"),
        }
    except Exception as e:
        logger.error(f"get_instance_profile_role: {type(e).__name__}")
        return {"error": str(e), "instance_profile_arn": instance_profile_arn}

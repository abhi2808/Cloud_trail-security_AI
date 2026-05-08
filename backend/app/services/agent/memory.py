"""
InvestigationMemory — tracks the agent's full investigation context.
Passed between loop iterations so every AI call has full history.
"""

from datetime import datetime, timezone


class InvestigationMemory:
    def __init__(self, user_question: str):
        self.question = user_question
        self.steps: list[dict] = []
        self.tools_called: list[str] = []
        self.key_findings: list[str] = []

    def add_step(
        self,
        tool_name: str,
        params: dict,
        result: dict,
        reasoning: str,
    ) -> None:
        """Record a completed tool call with its result and the AI's reasoning."""
        summary = _summarise_result(tool_name, result)
        self.steps.append({
            "step_number": len(self.steps) + 1,
            "tool": tool_name,
            "params": params,
            "result": result,
            "result_summary": summary,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.tools_called.append(tool_name)

    def add_finding(self, finding: str) -> None:
        self.key_findings.append(finding)

    def build_context_for_ai(self) -> str:
        """Build a text summary of everything discovered so far for injection into the next prompt."""
        if not self.steps:
            return "No investigation steps completed yet."

        lines = ["Investigation so far:"]
        for step in self.steps:
            lines.append(
                f"Step {step['step_number']} — {step['tool']}: {step['result_summary']}"
            )

        if self.key_findings:
            lines.append("\nKey findings identified:")
            for finding in self.key_findings:
                lines.append(f"  - {finding}")

        return "\n".join(lines)

    def to_response_steps(self) -> list[dict]:
        """Return steps in a clean format suitable for the frontend."""
        formatted_steps = []
        for s in self.steps:
            out = {
                "step": s["step_number"],
                "tool": s["tool"],
                "reasoning": s["reasoning"],
                "summary": s["result_summary"],
            }
            if isinstance(s.get("result"), dict) and "parallel_results" in s.get("result", {}):
                out["parallel_results"] = [
                    {
                        "tool": pr["tool"],
                        "summary": _summarise_result(pr["tool"], pr["result"])
                    }
                    for pr in s["result"]["parallel_results"]
                ]
            formatted_steps.append(out)
        return formatted_steps


# ─── Result summariser ───────────────────────────────────────────────────────

def _summarise_result(tool_name: str, result: dict | list) -> str:
    """Produce a 1-2 sentence human-readable summary of a tool result."""
    if isinstance(result, dict) and "error" in result:
        return f"Tool returned an error: {result['error']}"

    if tool_name == "search_cloudtrail":
        count = len(result) if isinstance(result, list) else result.get("count", 0)
        return f"Found {count} matching CloudTrail events."

    if tool_name in ("get_iam_user_permissions", "get_iam_role_permissions"):
        principal = result.get("username") or result.get("role_name", "principal")
        services = result.get("effective_services", [])
        managed = len(result.get("managed_policies", []))
        inline = len(result.get("inline_policies", []))
        return (
            f"{principal} has {managed} managed and {inline} inline policies. "
            f"Effective services: {', '.join(services[:10]) or 'none detected'}."
        )

    if tool_name == "list_iam_users":
        count = len(result) if isinstance(result, list) else 0
        return f"Found {count} IAM users in the account."

    if tool_name == "simulate_iam_permissions":
        results = result.get("results", [])
        allowed = sum(1 for r in results if r.get("decision") == "allowed")
        denied = sum(1 for r in results if r.get("decision") == "denied")
        return f"Simulation: {allowed} actions allowed, {denied} denied out of {len(results)} tested."

    if tool_name == "check_access_keys":
        keys = result if isinstance(result, list) else []
        stale = sum(1 for k in keys if k.get("stale"))
        return f"Found {len(keys)} access key(s), {stale} stale (>90 days)."

    if tool_name == "describe_ec2_instance":
        iid = result.get("instance_id", "unknown")
        state = result.get("state", "unknown")
        imdsv1 = result.get("imdsv1_enabled", False)
        note = " IMDSv1 is ENABLED (security risk)." if imdsv1 else ""
        return f"Instance {iid} is {state}.{note}"

    if tool_name == "describe_security_group":
        sg_id = result.get("sg_id", "unknown")
        inbound = result.get("inbound_rules", [])
        public_rules = sum(1 for r in inbound if r.get("is_public"))
        return f"Security group {sg_id}: {len(inbound)} inbound rules, {public_rules} open to public internet."

    if tool_name == "list_ec2_instances":
        instances = result if isinstance(result, list) else result.get("items", [])
        running = [i for i in instances if i.get("state") == "running"]
        # Include instance IDs + SG IDs so the model can plan follow-up calls from memory
        instance_lines = []
        for i in instances:
            iid = i.get("instance_id", "?")
            state = i.get("state", "?")
            sgs = i.get("security_group_ids") or i.get("security_groups", [])
            name = (i.get("tags") or {}).get("Name", "")
            sg_str = ", ".join(sgs) if sgs else "no SGs"
            label = f"{iid}" + (f" ({name})" if name else "") + f" [{state}] SGs: {sg_str}"
            instance_lines.append(label)
        summary = f"Found {len(instances)} EC2 instances, {len(running)} running."
        if instance_lines:
            summary += " Instances: " + " | ".join(instance_lines)
        return summary

    if tool_name == "get_cloudwatch_alarms":
        alarms = result if isinstance(result, list) else []
        return f"Found {len(alarms)} active CloudWatch alarm(s) in ALARM state."

    if tool_name == "get_metric_anomalies":
        anomaly = result.get("anomaly_detected", False)
        avg = result.get("average", 0)
        mx = result.get("max", 0)
        flag = "⚠ Anomaly detected!" if anomaly else "No anomalies detected."
        return f"{result.get('metric', 'Metric')}: avg={avg}, max={mx}. {flag}"

    if tool_name == "list_s3_buckets":
        buckets = result if isinstance(result, list) else []
        exposed = [b for b in buckets if not b.get("public_access_blocked")]
        names = ", ".join(b.get("bucket_name", "?") for b in buckets[:50])
        summary = f"Found {len(buckets)} S3 bucket(s), {len(exposed)} without public access block."
        if names:
            summary += f" Buckets: {names}"
        return summary

    if tool_name == "get_s3_bucket_policy":
        name = result.get("bucket_name", "unknown")
        pub = result.get("policy_allows_public", False)
        flag = "⚠ Policy allows public access!" if pub else "No public policy found."
        return f"Bucket {name}: {flag}"

    if tool_name == "get_caller_identity":
        acct = result.get("account_id", "unknown")
        arn = result.get("arn", "unknown")
        return f"Operating in AWS account {acct} as {arn}."

    # ── KMS ──────────────────────────────────────────────────────────────────
    if tool_name == "list_kms_keys":
        keys = result if isinstance(result, list) else []
        key_ids = ", ".join(k.get("key_id", k.get("alias", "?")) for k in keys[:15])
        summary = f"Found {len(keys)} customer-managed KMS key(s)."
        if key_ids:
            summary += f" Keys: {key_ids}"
        return summary

    if tool_name == "get_kms_key_details":
        kid = result.get("key_id", "unknown")
        rotation = result.get("rotation_enabled", False)
        external = result.get("policy_allows_external", False)
        findings = result.get("security_findings", [])
        flags = []
        if not rotation:
            flags.append("rotation disabled")
        if external:
            flags.append("⚠ policy allows external access")
        flag_str = f" Flags: {', '.join(flags)}." if flags else " No critical findings."
        return f"KMS key {kid}: {len(findings)} security finding(s).{flag_str}"

    # ── Secrets Manager ───────────────────────────────────────────────────────
    if tool_name == "list_secrets":
        secrets = result if isinstance(result, list) else []
        overdue = sum(1 for s in secrets if s.get("rotation_overdue"))
        return f"Found {len(secrets)} secret(s). {overdue} overdue for rotation."

    if tool_name == "get_secret_details":
        name = result.get("name", "unknown")
        rotation = result.get("rotation_enabled", False)
        days = result.get("days_since_rotation")
        external = result.get("policy_allows_external", False)
        flags = []
        if not rotation:
            flags.append("rotation disabled")
        if days and days > 90:
            flags.append(f"not rotated in {days} days")
        if external:
            flags.append("⚠ policy allows external access")
        flag_str = f" Flags: {', '.join(flags)}." if flags else " No critical findings."
        return f"Secret '{name}':{flag_str}"

    if tool_name == "get_secrets_security_summary":
        total = result.get("total_secrets", 0)
        disabled = result.get("rotation_disabled_count", 0)
        overdue = result.get("overdue_rotation_count", 0)
        return f"Secrets summary: {total} total, {disabled} with rotation disabled, {overdue} overdue."

    # ── RDS ──────────────────────────────────────────────────────────────────
    if tool_name == "list_rds_databases":
        dbs = result if isinstance(result, list) else []
        public = [d for d in dbs if d.get("publicly_accessible")]
        unencrypted = sum(1 for d in dbs if not d.get("storage_encrypted"))
        db_ids = ", ".join(d.get("db_identifier", "?") for d in dbs[:15])
        summary = (
            f"Found {len(dbs)} RDS instance(s). "
            f"{len(public)} publicly accessible, {unencrypted} with storage unencrypted."
        )
        if db_ids:
            summary += f" Instances: {db_ids}"
        return summary

    if tool_name == "get_rds_database_details":
        db_id = result.get("db_identifier", "unknown")
        public = result.get("publicly_accessible", False)
        encrypted = result.get("storage_encrypted", False)
        findings = result.get("security_findings", [])
        flags = []
        if public:
            flags.append("⚠ publicly accessible")
        if not encrypted:
            flags.append("storage unencrypted")
        flag_str = f" Flags: {', '.join(flags)}." if flags else " No critical findings."
        return f"RDS instance '{db_id}': {len(findings)} finding(s).{flag_str}"

    if tool_name == "list_rds_snapshots":
        snaps = result if isinstance(result, list) else []
        public = sum(1 for s in snaps if s.get("is_public"))
        unencrypted = sum(1 for s in snaps if not s.get("encrypted"))
        crit = " ⚠ CRITICAL: Public snapshots found!" if public > 0 else ""
        return (
            f"Found {len(snaps)} manual RDS snapshot(s). "
            f"{public} public, {unencrypted} unencrypted.{crit}"
        )

    # ── Bedrock ───────────────────────────────────────────────────────────────
    if tool_name == "get_bedrock_security_summary":
        logging_enabled = result.get("invocation_logging_enabled", False)
        models = result.get("custom_model_count", 0)
        flag = "" if logging_enabled else " ⚠ Invocation logging is DISABLED — AI calls are unaudited."
        return f"Bedrock: {models} custom model(s).{flag}"

    if tool_name == "list_bedrock_foundation_models":
        models = result if isinstance(result, list) else []
        return f"Found {len(models)} Bedrock foundation model(s) available in this region."

    # ── SageMaker ─────────────────────────────────────────────────────────────
    if tool_name == "get_sagemaker_security_summary":
        endpoints = result.get("endpoint_count", 0)
        notebooks = result.get("notebook_count", 0)
        findings = result.get("total_findings", len(result.get("security_findings", [])))
        return f"SageMaker: {endpoints} endpoint(s), {notebooks} notebook(s). {findings} security finding(s)."

    if tool_name == "list_sagemaker_endpoints":
        eps = result if isinstance(result, list) else []
        in_service = sum(1 for e in eps if e.get("status") == "InService")
        return f"Found {len(eps)} SageMaker endpoint(s), {in_service} currently InService."

    # ── Generic fallback (for any new tools added in future) ──────────────────
    if isinstance(result, list):
        return f"Returned {len(result)} item(s)."
    return "Tool completed successfully."

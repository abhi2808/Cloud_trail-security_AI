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
        return [
            {
                "step": s["step_number"],
                "tool": s["tool"],
                "reasoning": s["reasoning"],
                "summary": s["result_summary"],
            }
            for s in self.steps
        ]


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
        instances = result if isinstance(result, list) else []
        running = sum(1 for i in instances if i.get("state") == "running")
        return f"Found {len(instances)} EC2 instances, {running} currently running."

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
        exposed = sum(1 for b in buckets if not b.get("public_access_blocked"))
        return f"Found {len(buckets)} S3 bucket(s), {exposed} without public access block."

    if tool_name == "get_s3_bucket_policy":
        name = result.get("bucket_name", "unknown")
        pub = result.get("policy_allows_public", False)
        flag = "⚠ Policy allows public access!" if pub else "No public policy found."
        return f"Bucket {name}: {flag}"

    if tool_name == "get_caller_identity":
        acct = result.get("account_id", "unknown")
        arn = result.get("arn", "unknown")
        return f"Operating in AWS account {acct} as {arn}."

    # Generic fallback
    if isinstance(result, list):
        return f"Returned {len(result)} item(s)."
    return "Tool completed successfully."

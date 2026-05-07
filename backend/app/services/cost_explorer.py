"""
AWS Cost Explorer reader service — cost analysis, spike detection, and anomaly monitoring.

All functions take an explicit boto3 Session created from decrypted credentials.
Cost Explorer API is GLOBAL — client is always created with region_name="us-east-1"
regardless of the session's default region.
"""

import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def _ce_client(session):
    """Create a Cost Explorer client pinned to us-east-1 (global service)."""
    return session.client("ce", region_name="us-east-1")


# ─── Cost Summary ────────────────────────────────────────────────────────────


async def get_cost_summary(
    session,
    start_date: str,
    end_date: str,
    granularity: str = "DAILY",
) -> dict:
    """
    Get AWS cost breakdown by service for a date range.
    Returns total spend, per-service costs, and identifies the most expensive service.
    """
    try:
        client = _ce_client(session)
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        # Accumulate costs per service across all time buckets
        service_costs: dict[str, dict] = {}  # service -> {total, daily: [{date, cost}]}

        for result_by_time in response.get("ResultsByTime", []):
            period_start = result_by_time["TimePeriod"]["Start"]
            for group in result_by_time.get("Groups", []):
                service_name = group["Keys"][0]
                cost_val = round(float(group["Metrics"]["UnblendedCost"]["Amount"]), 4)

                if service_name not in service_costs:
                    service_costs[service_name] = {"total": 0.0, "daily": []}

                service_costs[service_name]["total"] = round(
                    service_costs[service_name]["total"] + cost_val, 4
                )
                service_costs[service_name]["daily"].append({
                    "date": period_start,
                    "cost_usd": cost_val,
                })

        # Build sorted by_service list (descending by total cost)
        by_service = sorted(
            [
                {
                    "service": svc,
                    "total_cost_usd": round(data["total"], 4),
                    "daily_breakdown": data["daily"],
                }
                for svc, data in service_costs.items()
            ],
            key=lambda x: x["total_cost_usd"],
            reverse=True,
        )

        total_cost = round(sum(s["total_cost_usd"] for s in by_service), 4)
        top_service = by_service[0]["service"] if by_service else "N/A"
        top_service_cost = by_service[0]["total_cost_usd"] if by_service else 0.0

        return {
            "period": {"start": start_date, "end": end_date},
            "granularity": granularity,
            "total_cost_usd": total_cost,
            "currency": "USD",
            "by_service": by_service,
            "top_service": top_service,
            "top_service_cost_usd": top_service_cost,
            "anomalies_detected": [],
        }

    except client.exceptions.BillExpirationException:
        logger.warning("Cost Explorer not enabled on this account.")
        return {
            "error": (
                "Cost Explorer not enabled on this account. "
                "Enable it in AWS Console → Billing → Cost Explorer."
            )
        }
    except Exception as e:
        error_msg = str(e)
        if "not enabled" in error_msg.lower() or "opt in" in error_msg.lower():
            return {
                "error": (
                    "Cost Explorer not enabled on this account. "
                    "Enable it in AWS Console → Billing → Cost Explorer."
                )
            }
        logger.error(f"get_cost_summary: {type(e).__name__}: {e}")
        return {
            "error": f"Failed to retrieve cost data: {type(e).__name__}: {e}"
        }


# ─── Cost Spike Detection ───────────────────────────────────────────────────


async def get_cost_spike(
    session,
    service: Optional[str] = None,
    lookback_days: int = 14,
) -> dict:
    """
    Detect cost spikes by comparing recent spend to baseline.
    Splits the lookback window in half: first half = baseline, second half = recent.
    Returns services with spike_factor >= 1.3 and severity classification.
    """
    try:
        client = _ce_client(session)

        today = date.today()
        end_date = today.strftime("%Y-%m-%d")
        mid_date = (today - timedelta(days=lookback_days // 2)).strftime("%Y-%m-%d")
        start_date = (today - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        half_days = lookback_days // 2

        # Build optional service filter
        filter_expr = None
        if service:
            filter_expr = {
                "Dimensions": {
                    "Key": "SERVICE",
                    "Values": [service],
                }
            }

        # --- Period 1: Baseline (first half) ---
        kwargs_baseline = {
            "TimePeriod": {"Start": start_date, "End": mid_date},
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }
        if filter_expr:
            kwargs_baseline["Filter"] = filter_expr

        resp_baseline = client.get_cost_and_usage(**kwargs_baseline)

        # --- Period 2: Recent (second half) ---
        kwargs_recent = {
            "TimePeriod": {"Start": mid_date, "End": end_date},
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }
        if filter_expr:
            kwargs_recent["Filter"] = filter_expr

        resp_recent = client.get_cost_and_usage(**kwargs_recent)

        # Aggregate per service for each period
        baseline_totals: dict[str, float] = {}
        for result_by_time in resp_baseline.get("ResultsByTime", []):
            for group in result_by_time.get("Groups", []):
                svc = group["Keys"][0]
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                baseline_totals[svc] = baseline_totals.get(svc, 0.0) + cost

        recent_totals: dict[str, float] = {}
        for result_by_time in resp_recent.get("ResultsByTime", []):
            for group in result_by_time.get("Groups", []):
                svc = group["Keys"][0]
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                recent_totals[svc] = recent_totals.get(svc, 0.0) + cost

        # Compute spike factor per service
        all_services = set(baseline_totals.keys()) | set(recent_totals.keys())
        spikes_detected = []

        for svc in all_services:
            baseline_total = baseline_totals.get(svc, 0.0)
            recent_total = recent_totals.get(svc, 0.0)

            baseline_daily_avg = round(baseline_total / half_days, 4) if half_days > 0 else 0.0
            recent_daily_avg = round(recent_total / half_days, 4) if half_days > 0 else 0.0

            if baseline_daily_avg > 0:
                spike_factor = round(recent_daily_avg / baseline_daily_avg, 4)
            else:
                spike_factor = 999.0 if recent_daily_avg > 0 else 0.0

            spike_usd = round(recent_daily_avg - baseline_daily_avg, 4)

            # Severity classification
            if spike_factor >= 5.0:
                severity = "CRITICAL"
            elif spike_factor >= 3.0:
                severity = "HIGH"
            elif spike_factor >= 2.0:
                severity = "MEDIUM"
            elif spike_factor >= 1.3:
                severity = "LOW"
            else:
                severity = "NONE"

            # Only include services with meaningful spikes
            if spike_factor >= 1.3:
                spikes_detected.append({
                    "service": svc,
                    "baseline_daily_avg_usd": baseline_daily_avg,
                    "recent_daily_avg_usd": recent_daily_avg,
                    "spike_factor": spike_factor,
                    "spike_usd_per_day": spike_usd,
                    "severity": severity,
                })

        # Sort by spike_factor descending
        spikes_detected.sort(key=lambda x: x["spike_factor"], reverse=True)

        highest_spike_service = spikes_detected[0]["service"] if spikes_detected else "None"
        highest_spike_factor = spikes_detected[0]["spike_factor"] if spikes_detected else 0.0

        # Human-readable summary
        if spikes_detected:
            top = spikes_detected[0]
            summary = (
                f"Detected {len(spikes_detected)} service(s) with cost spikes in the last {lookback_days} days. "
                f"Highest spike: {top['service']} at {top['spike_factor']}x baseline "
                f"(+${top['spike_usd_per_day']:.2f}/day, severity: {top['severity']})."
            )
        else:
            summary = f"No significant cost spikes detected in the last {lookback_days} days. All services within normal spend range."

        return {
            "lookback_days": lookback_days,
            "analysis_period": {"start": start_date, "end": end_date},
            "service_filter": service or "all services",
            "spikes_detected": spikes_detected,
            "highest_spike_service": highest_spike_service,
            "highest_spike_factor": highest_spike_factor,
            "summary": summary,
        }

    except Exception as e:
        error_msg = str(e)
        if "not enabled" in error_msg.lower() or "opt in" in error_msg.lower():
            return {
                "error": (
                    "Cost Explorer not enabled on this account. "
                    "Enable it in AWS Console → Billing → Cost Explorer."
                )
            }
        logger.error(f"get_cost_spike: {type(e).__name__}: {e}")
        return {
            "lookback_days": lookback_days,
            "analysis_period": {"start": "", "end": ""},
            "service_filter": service or "all services",
            "spikes_detected": [],
            "highest_spike_service": "None",
            "highest_spike_factor": 0.0,
            "summary": f"Failed to analyze cost spikes: {type(e).__name__}: {e}",
        }


# ─── Cost Anomalies ─────────────────────────────────────────────────────────


async def get_cost_anomalies(session) -> dict:
    """
    Get AWS-detected cost anomalies from Cost Anomaly Detection monitors.
    Uses AWS's own ML-based anomaly detection for high-confidence findings.
    """
    try:
        client = _ce_client(session)

        # Get anomaly monitors
        try:
            monitors_resp = client.get_anomaly_monitors(MaxResults=100)
        except Exception as monitor_err:
            error_msg = str(monitor_err)
            if "not enabled" in error_msg.lower() or "opt in" in error_msg.lower():
                return {
                    "error": (
                        "Cost Explorer not enabled on this account. "
                        "Enable it in AWS Console → Billing → Cost Explorer."
                    )
                }
            # No monitors configured — not an error, just not set up
            return {
                "total_anomalies": 0,
                "anomalies": [],
                "summary": (
                    "No AWS Cost Anomaly monitors configured. "
                    "Consider enabling Cost Anomaly Detection in "
                    "AWS Billing console for automatic spike detection."
                ),
                "highest_impact_anomaly": None,
            }

        monitors = monitors_resp.get("AnomalyMonitors", [])
        if not monitors:
            return {
                "total_anomalies": 0,
                "anomalies": [],
                "summary": (
                    "No AWS Cost Anomaly monitors configured. "
                    "Consider enabling Cost Anomaly Detection in "
                    "AWS Billing console for automatic spike detection."
                ),
                "highest_impact_anomaly": None,
            }

        # Query anomalies from each monitor (last 30 days)
        today = date.today()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        all_anomalies = []
        for monitor in monitors:
            monitor_arn = monitor.get("MonitorArn", "")
            if not monitor_arn:
                continue

            try:
                anomalies_resp = client.get_anomalies(
                    MonitorArn=monitor_arn,
                    DateInterval={"StartDate": start_date, "EndDate": end_date},
                    TotalImpact={
                        "NumericOperator": "GREATER_THAN",
                        "StartValue": 1,
                    },
                )

                for anomaly in anomalies_resp.get("Anomalies", []):
                    anomaly_id = anomaly.get("AnomalyId", "")
                    anomaly_start = anomaly.get("AnomalyStartDate", "")
                    anomaly_end = anomaly.get("AnomalyEndDate")

                    # Extract root cause service
                    root_causes = anomaly.get("RootCauses", [])
                    service_name = root_causes[0].get("Service", "Unknown") if root_causes else "Unknown"

                    # Impact
                    impact = anomaly.get("Impact", {})
                    actual_spend = round(float(impact.get("TotalActualSpend", 0)), 4)
                    expected_spend = round(float(impact.get("TotalExpectedSpend", 0)), 4)
                    impact_usd = round(actual_spend - expected_spend, 4)
                    impact_percentage = (
                        round((impact_usd / expected_spend) * 100, 2)
                        if expected_spend > 0
                        else 999.0
                    )

                    # Determine if ongoing
                    is_ongoing = anomaly_end is None or anomaly_end == ""

                    # Severity from AWS anomaly score
                    anomaly_score = anomaly.get("AnomalyScore", {})
                    max_score = float(anomaly_score.get("MaxScore", 0))
                    if max_score >= 90:
                        severity = "CRITICAL"
                    elif max_score >= 70:
                        severity = "HIGH"
                    elif max_score >= 50:
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"

                    all_anomalies.append({
                        "anomaly_id": anomaly_id,
                        "service": service_name,
                        "start_date": anomaly_start,
                        "end_date": anomaly_end if not is_ongoing else None,
                        "is_ongoing": is_ongoing,
                        "actual_spend_usd": actual_spend,
                        "expected_spend_usd": expected_spend,
                        "impact_usd": impact_usd,
                        "impact_percentage": impact_percentage,
                        "severity": severity,
                    })

            except Exception as anomaly_err:
                logger.warning(f"get_anomalies for monitor {monitor_arn}: {type(anomaly_err).__name__}")
                continue

        # Sort by impact descending
        all_anomalies.sort(key=lambda x: x["impact_usd"], reverse=True)

        highest_impact = all_anomalies[0] if all_anomalies else None

        if all_anomalies:
            ongoing_count = sum(1 for a in all_anomalies if a["is_ongoing"])
            total_impact = round(sum(a["impact_usd"] for a in all_anomalies), 2)
            summary = (
                f"Found {len(all_anomalies)} cost anomaly/anomalies in the last 30 days "
                f"with total impact of ${total_impact:.2f}. "
                f"{ongoing_count} ongoing."
            )
        else:
            summary = "No cost anomalies detected by AWS in the last 30 days."

        return {
            "total_anomalies": len(all_anomalies),
            "anomalies": all_anomalies,
            "highest_impact_anomaly": highest_impact,
            "summary": summary,
        }

    except Exception as e:
        error_msg = str(e)
        if "not enabled" in error_msg.lower() or "opt in" in error_msg.lower():
            return {
                "error": (
                    "Cost Explorer not enabled on this account. "
                    "Enable it in AWS Console → Billing → Cost Explorer."
                )
            }
        logger.error(f"get_cost_anomalies: {type(e).__name__}: {e}")
        return {
            "total_anomalies": 0,
            "anomalies": [],
            "summary": f"Failed to retrieve cost anomalies: {type(e).__name__}: {e}",
            "highest_impact_anomaly": None,
        }


# ─── Service Cost Timeline ──────────────────────────────────────────────────


async def get_service_cost_timeline(
    session,
    service: str,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Get detailed daily cost breakdown and usage types for ONE specific service.
    Shows peak spending day and what usage types drove the cost.
    """
    try:
        client = _ce_client(session)

        response = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["UnblendedCost", "UsageQuantity"],
            Filter={
                "Dimensions": {
                    "Key": "SERVICE",
                    "Values": [service],
                }
            },
            GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
        )

        daily_costs = []
        usage_type_totals: dict[str, float] = {}
        peak_day = ""
        peak_day_cost = 0.0

        for result_by_time in response.get("ResultsByTime", []):
            day_date = result_by_time["TimePeriod"]["Start"]
            day_total = 0.0
            usage_types = []

            for group in result_by_time.get("Groups", []):
                usage_type = group["Keys"][0]
                cost_val = round(float(group["Metrics"]["UnblendedCost"]["Amount"]), 4)
                day_total = round(day_total + cost_val, 4)

                if cost_val > 0:
                    usage_types.append({
                        "usage_type": usage_type,
                        "cost_usd": cost_val,
                    })

                # Accumulate for cost_drivers
                usage_type_totals[usage_type] = round(
                    usage_type_totals.get(usage_type, 0.0) + cost_val, 4
                )

            daily_costs.append({
                "date": day_date,
                "cost_usd": day_total,
                "usage_types": sorted(usage_types, key=lambda x: x["cost_usd"], reverse=True),
            })

            if day_total > peak_day_cost:
                peak_day_cost = day_total
                peak_day = day_date

        total_cost = round(sum(d["cost_usd"] for d in daily_costs), 4)

        # Top 3 usage types by total cost
        cost_drivers = sorted(
            [
                {"usage_type": ut, "total_cost_usd": round(cost, 4)}
                for ut, cost in usage_type_totals.items()
                if cost > 0
            ],
            key=lambda x: x["total_cost_usd"],
            reverse=True,
        )[:3]

        return {
            "service": service,
            "period": {"start": start_date, "end": end_date},
            "total_cost_usd": total_cost,
            "peak_day": peak_day,
            "peak_day_cost_usd": round(peak_day_cost, 4),
            "daily_costs": daily_costs,
            "cost_drivers": cost_drivers,
        }

    except Exception as e:
        error_msg = str(e)
        if "not enabled" in error_msg.lower() or "opt in" in error_msg.lower():
            return {
                "error": (
                    "Cost Explorer not enabled on this account. "
                    "Enable it in AWS Console → Billing → Cost Explorer."
                )
            }
        logger.error(f"get_service_cost_timeline ({service}): {type(e).__name__}: {e}")
        return {
            "service": service,
            "period": {"start": start_date, "end": end_date},
            "total_cost_usd": 0.0,
            "peak_day": "",
            "peak_day_cost_usd": 0.0,
            "daily_costs": [],
            "cost_drivers": [],
            "error": f"Failed to retrieve timeline: {type(e).__name__}: {e}",
        }

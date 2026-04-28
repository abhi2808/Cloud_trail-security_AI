"""
CloudWatch reader service — metrics and alarms only (no logs).
All functions take an explicit boto3 Session created from decrypted credentials.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def get_metric_data(
    session,
    namespace: str,
    metric_name: str,
    dimensions: list,
    start_time: datetime,
    end_time: datetime,
    period_seconds: int = 300,
) -> dict:
    """
    Fetch a CloudWatch metric and detect anomalies (value > 2x average).
    """
    try:
        client = session.client("cloudwatch")
        response = client.get_metric_data(
            MetricDataQueries=[{
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": metric_name,
                        "Dimensions": dimensions,
                    },
                    "Period": period_seconds,
                    "Stat": "Average",
                },
                "ReturnData": True,
            }],
            StartTime=start_time,
            EndTime=end_time,
        )

        result_data = response.get("MetricDataResults", [{}])[0]
        timestamps = result_data.get("Timestamps", [])
        values = result_data.get("Values", [])

        datapoints = [
            {"timestamp": str(ts), "value": round(val, 4), "unit": "None"}
            for ts, val in zip(timestamps, values)
        ]

        average = round(sum(values) / len(values), 4) if values else 0.0
        maximum = round(max(values), 4) if values else 0.0
        anomaly_detected = any(v > 2 * average for v in values) if average > 0 else False

        return {
            "metric": metric_name,
            "namespace": namespace,
            "datapoints": datapoints,
            "average": average,
            "max": maximum,
            "anomaly_detected": anomaly_detected,
        }
    except Exception as e:
        logger.error(f"get_metric_data ({namespace}/{metric_name}): {type(e).__name__}")
        return {
            "metric": metric_name,
            "namespace": namespace,
            "datapoints": [],
            "average": 0.0,
            "max": 0.0,
            "anomaly_detected": False,
            "error": str(e),
        }


async def describe_alarms(session, state: Optional[str] = None) -> list:
    """List CloudWatch alarms, optionally filtered by state: OK | ALARM | INSUFFICIENT_DATA."""
    try:
        client = session.client("cloudwatch")
        kwargs = {}
        if state:
            kwargs["StateValue"] = state

        paginator = client.get_paginator("describe_alarms")
        alarms = []
        for page in paginator.paginate(**kwargs):
            for alarm in page.get("MetricAlarms", []):
                alarms.append({
                    "alarm_name": alarm.get("AlarmName"),
                    "state": alarm.get("StateValue"),
                    "metric_name": alarm.get("MetricName"),
                    "namespace": alarm.get("Namespace"),
                    "threshold": alarm.get("Threshold"),
                    "comparison_operator": alarm.get("ComparisonOperator"),
                    "last_state_change": str(alarm.get("StateUpdatedTimestamp", "")),
                    "alarm_description": alarm.get("AlarmDescription", ""),
                })
        return alarms
    except Exception as e:
        logger.error(f"describe_alarms: {type(e).__name__}")
        return []


async def list_active_alarms(session) -> list:
    """Convenience wrapper — returns only alarms currently in ALARM state."""
    return await describe_alarms(session, state="ALARM")


def resolve_namespace_and_dimensions(resource_id: str, resource_type: str) -> tuple:
    """Map resource_type + resource_id to CloudWatch namespace and dimensions."""
    mapping = {
        "ec2":    ("AWS/EC2",    "InstanceId"),
        "lambda": ("AWS/Lambda", "FunctionName"),
        "s3":     ("AWS/S3",     "BucketName"),
    }
    namespace, dim_key = mapping.get(resource_type.lower(), ("AWS/EC2", "InstanceId"))
    dimensions = [{"Name": dim_key, "Value": resource_id}]
    if resource_type.lower() == "s3":
        dimensions.append({"Name": "StorageType", "Value": "AllStorageTypes"})
    return namespace, dimensions

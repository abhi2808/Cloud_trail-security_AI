"""
AWS CloudTrail service — boto3 client wrapper for LookupEvents.
Handles pagination, deduplication, retry with exponential backoff,
and client-side filtering for secondary parameters.
Supports single-region and all-region queries.
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.config import settings
from app.models.query import ExtractedIntent, CloudTrailEvent
from app.db.repositories.account_repository import account_repository
from app.core.encryption import decrypt_value

logger = logging.getLogger(__name__)

MAX_RESULTS_PER_CALL = 50
MAX_TOTAL_EVENTS = 200
MAX_RETRIES = 3
INITIAL_BACKOFF = 0.5

# All common AWS regions for "query all" mode
ALL_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1",
    "ap-south-1", "ap-southeast-1", "ap-southeast-2",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "ca-central-1", "sa-east-1",
]

def _parse_event(raw_event: dict) -> CloudTrailEvent:
    """Parse a raw CloudTrail event dict into a CloudTrailEvent Pydantic model."""
    detail = {}
    if "CloudTrailEvent" in raw_event:
        try:
            detail = json.loads(raw_event["CloudTrailEvent"])
        except (json.JSONDecodeError, TypeError):
            detail = {}

    # Extract username — try multiple locations
    username = raw_event.get("Username")
    if not username:
        user_identity = detail.get("userIdentity", {})
        username = (
            user_identity.get("userName")
            or user_identity.get("principalId", "").split(":")[-1]
            or user_identity.get("type")
        )

    # Extract user ARN
    user_identity = detail.get("userIdentity", {})
    user_arn = user_identity.get("arn")

    # Extract request parameters
    request_params = detail.get("requestParameters")

    return CloudTrailEvent(
        event_id=raw_event.get("EventId", detail.get("eventID", "unknown")),
        event_name=raw_event.get("EventName", detail.get("eventName", "unknown")),
        event_time=raw_event.get("EventTime", detail.get("eventTime", datetime.now(timezone.utc))),
        username=username,
        user_arn=user_arn,
        source_ip=detail.get("sourceIPAddress"),
        aws_region=detail.get("awsRegion"),
        error_code=detail.get("errorCode"),
        error_message=detail.get("errorMessage"),
        request_parameters=request_params,
    )


def _build_lookup_params(
    attribute_key: str,
    attribute_value: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> dict:
    """Build the parameters dict for a LookupEvents API call."""
    params = {
        "LookupAttributes": [
            {
                "AttributeKey": attribute_key,
                "AttributeValue": attribute_value,
            }
        ],
        "MaxResults": MAX_RESULTS_PER_CALL,
    }
    if start_time:
        params["StartTime"] = start_time
    if end_time:
        params["EndTime"] = end_time
    return params


def _call_lookup_with_retry(client, params: dict) -> list[dict]:
    """
    Call CloudTrail LookupEvents with pagination and exponential backoff retry.
    Returns list of raw event dicts.
    """
    all_events = []
    next_token = None

    while len(all_events) < MAX_TOTAL_EVENTS:
        call_params = {**params}
        if next_token:
            call_params["NextToken"] = next_token

        backoff = INITIAL_BACKOFF
        for attempt in range(MAX_RETRIES):
            try:
                response = client.lookup_events(**call_params)
                events = response.get("Events", [])
                all_events.extend(events)
                next_token = response.get("NextToken")
                break
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "ThrottlingException" and attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"CloudTrail throttled, retrying in {backoff}s (attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error(f"CloudTrail API error: {error_code} - {e.response['Error']['Message']}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"AWS CloudTrail error: {error_code} - {e.response['Error']['Message']}",
                    )

        if not next_token:
            break

    return all_events[:MAX_TOTAL_EVENTS]


def _query_single_region(region: str, intent: ExtractedIntent, access_key: str, secret_key: str) -> list[CloudTrailEvent]:
    """
    Query CloudTrail events for a single AWS region.
    Returns parsed CloudTrailEvent list.
    """
    client = boto3.Session(
        aws_access_key_id=access_key, 
        aws_secret_access_key=secret_key, 
        region_name=region
    ).client("cloudtrail")
    lookup_calls = []

    if intent.event_name:
        event_names = [name.strip() for name in intent.event_name.split(",")]
        for event_name in event_names:
            params = _build_lookup_params(
                "EventName", event_name, intent.start_time, intent.end_time
            )
            lookup_calls.append(("EventName", params))

    if intent.username:
        params = _build_lookup_params(
            "Username", intent.username, intent.start_time, intent.end_time
        )
        lookup_calls.append(("Username", params))

    if intent.resource_id:
        params = _build_lookup_params(
            "ResourceName", intent.resource_id, intent.start_time, intent.end_time
        )
        lookup_calls.append(("ResourceName", params))

    if not lookup_calls:
        params = {"MaxResults": MAX_RESULTS_PER_CALL}
        if intent.start_time:
            params["StartTime"] = intent.start_time
        if intent.end_time:
            params["EndTime"] = intent.end_time
        lookup_calls.append(("broad", params))

    all_raw_events = []
    seen_event_ids = set()

    for call_type, params in lookup_calls:
        try:
            raw_events = _call_lookup_with_retry(client, params)
            for event in raw_events:
                event_id = event.get("EventId", "")
                if event_id not in seen_event_ids:
                    seen_event_ids.add(event_id)
                    all_raw_events.append(event)
        except HTTPException:
            # Log and skip regions that fail (e.g. not enabled)
            logger.warning(f"Skipping region {region} due to API error on {call_type}")
            return []

    parsed_events = []
    for raw_event in all_raw_events:
        try:
            parsed_events.append(_parse_event(raw_event))
        except Exception as e:
            logger.warning(f"Failed to parse event in {region}: {e}")
            continue

    # Apply client-side filters
    if len(lookup_calls) == 1 and lookup_calls[0][0] == "Username":
        if intent.event_name:
            event_names = [name.strip() for name in intent.event_name.split(",")]
            parsed_events = [e for e in parsed_events if e.event_name in event_names]
    elif len(lookup_calls) == 1 and lookup_calls[0][0] == "ResourceName":
        if intent.event_name:
            event_names = [name.strip() for name in intent.event_name.split(",")]
            parsed_events = [e for e in parsed_events if e.event_name in event_names]
        if intent.username:
            username_lower = intent.username.lower()
            parsed_events = [
                e for e in parsed_events
                if e.username and username_lower in e.username.lower()
            ]

    return parsed_events


async def lookup_events(intent: ExtractedIntent, account_id: str, user_id: str) -> list[CloudTrailEvent]:
    """
    Main entry point: look up CloudTrail events based on extracted intent.
    
    If intent.aws_region is 'all', queries all common AWS regions in parallel and merges results.
    Otherwise queries only the specified region (defaults to account region).
    """
    try:
        account_doc = await account_repository.get_account_by_id(account_id, user_id)
        if not account_doc:
            raise HTTPException(status_code=404, detail="Account not found")

        access_key = decrypt_value(account_doc["access_key_id"])
        secret_key = decrypt_value(account_doc["secret_access_key"])
        
        region = intent.aws_region or account_doc["region"]

        if region == "all":
            logger.info(f"Querying ALL {len(ALL_REGIONS)} AWS regions in parallel")
            tasks = [
                asyncio.to_thread(_query_single_region, r, intent, access_key, secret_key)
                for r in ALL_REGIONS
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_events = []
            seen_ids = set()
            for r_name, result in zip(ALL_REGIONS, results):
                if isinstance(result, Exception):
                    logger.warning(f"Region {r_name} failed: {result}")
                    continue
                for event in result:
                    if event.event_id not in seen_ids:
                        seen_ids.add(event.event_id)
                        all_events.append(event)

            all_events.sort(key=lambda e: e.event_time, reverse=True)
            logger.info(f"All-region query returned {len(all_events)} total events")
            await account_repository.update_last_verified(account_id)
            return all_events[:MAX_TOTAL_EVENTS]

        else:
            logger.info(f"Querying CloudTrail in region: {region}")
            parsed_events = await asyncio.to_thread(_query_single_region, region, intent, access_key, secret_key)
            parsed_events.sort(key=lambda e: e.event_time, reverse=True)
            logger.info(f"CloudTrail lookup returned {len(parsed_events)} events")
            await account_repository.update_last_verified(account_id)
            return parsed_events

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in CloudTrail lookup: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query CloudTrail: {str(e)}",
        )

"""
Pydantic schemas for query request/response and CloudTrail event models.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Incoming user query request."""
    message: str = Field(..., min_length=1, max_length=500, description="User's natural language query")
    conversation_history: list[dict] = Field(
        default_factory=list, description="Previous conversation messages for context"
    )
    region: str = Field(
        default="us-east-1", description="AWS region to query, or 'all' to query all common regions"
    )
    account_id: str = Field(..., description="The ID of the AWS account to query")


class ExtractedIntent(BaseModel):
    """AI-extracted intent from user's natural language query."""
    event_name: Optional[str] = Field(None, description="AWS CloudTrail event name")
    resource_id: Optional[str] = Field(None, description="AWS resource identifier")
    username: Optional[str] = Field(None, description="IAM username to filter by")
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    query_type: Literal["resource_event", "user_activity", "general", "suspicious_activity"] = Field(
        default="general", description="Category of the query"
    )
    aws_region: Optional[str] = Field(
        None, description="AWS region to query (e.g., us-east-1, ap-south-1). None = use default"
    )
    clarification_needed: bool = Field(
        default=False, description="Whether the query needs clarification"
    )
    clarification_message: Optional[str] = Field(
        None, description="Message asking user for clarification"
    )


class CloudTrailEvent(BaseModel):
    """Parsed CloudTrail event record."""
    event_id: str = Field(..., description="Unique CloudTrail event ID")
    event_name: str = Field(..., description="AWS API action name")
    event_time: datetime = Field(..., description="Timestamp of the event")
    username: Optional[str] = Field(None, description="IAM user who performed the action")
    user_arn: Optional[str] = Field(None, description="Full ARN of the user/role")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    aws_region: Optional[str] = Field(None, description="AWS region where event occurred")
    error_code: Optional[str] = Field(None, description="Error code if the action failed")
    error_message: Optional[str] = Field(None, description="Error message if the action failed")
    request_parameters: Optional[dict] = Field(None, description="Request parameters sent with the API call")


class QueryResponse(BaseModel):
    """Response returned to the frontend."""
    answer: str = Field(..., description="AI-interpreted human-readable answer")
    events_count: int = Field(default=0, description="Number of matching CloudTrail events")
    raw_events: list[CloudTrailEvent] = Field(
        default_factory=list, description="List of parsed CloudTrail events"
    )
    # Agentic fields
    severity: Optional[str] = Field(default=None, description="NONE|LOW|MEDIUM|HIGH|CRITICAL")
    evidence: list[str] = Field(default_factory=list, description="Key findings supporting verdict")
    recommended_actions: list[str] = Field(default_factory=list, description="Specific next steps")
    steps_taken: list[dict] = Field(default_factory=list, description="Agent investigation steps")
    iterations: int = Field(default=0, description="Number of ReAct loop iterations used")


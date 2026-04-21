"""
API routes for CloudTrail AI Investigator.
POST /api/query — process natural language query against CloudTrail
GET /api/health — health check endpoint
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.models.query import QueryRequest, QueryResponse
from app.services.ai import extract_intent, interpret_results
from app.services.cloudtrail import lookup_events

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_query(query_req: QueryRequest, request: Request):
    """
    Process a natural language security query against AWS CloudTrail.
    
    Flow:
    1. Extract intent from natural language using AI
    2. If clarification needed, return early
    3. Query CloudTrail with extracted parameters
    4. Interpret results with AI
    5. Return structured response
    """
    logger.info(f"Processing query: {query_req.message[:100]}...")

    # Step 1: Extract intent from natural language
    intent = await extract_intent(query_req.message, query_req.conversation_history)

    # Step 2: If clarification needed, return early
    if intent.clarification_needed:
        logger.info("Clarification needed, returning early")
        return QueryResponse(
            answer=intent.clarification_message or "Could you please provide more details about what you're looking for?",
            events_count=0,
            raw_events=[],
        )

    # Step 3: Query CloudTrail using the account credentials
    user_id = request.state.user["sub"]
    intent.aws_region = intent.aws_region or query_req.region
    events = await lookup_events(intent, account_id=query_req.account_id, user_id=user_id)

    # Step 4: Interpret results with AI
    answer = await interpret_results(query_req.message, events)

    # Step 5: Return response
    logger.info(f"Query processed successfully: {len(events)} events found")
    return QueryResponse(
        answer=answer,
        events_count=len(events),
        raw_events=events,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint — returns status and current UTC timestamp."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "CloudTrail AI Investigator",
    }

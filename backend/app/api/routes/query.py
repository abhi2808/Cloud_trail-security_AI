"""
API routes for CloudTrail AI Investigator.
POST /api/query — process natural language query via agentic ReAct loop
GET /api/health — health check endpoint
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.models.query import QueryRequest, QueryResponse
from app.services.agent.runner import run as agent_run

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_query(query_req: QueryRequest, request: Request):
    """
    Process a natural language security query via the agentic ReAct loop.

    Flow:
    1. Agent receives user question
    2. ReAct loop: AI reasons → tool executes → memory updated → repeat
    3. Agent calls finish() with verdict + evidence
    4. Return structured response
    """
    logger.info(f"Agent query: {query_req.message[:100]}...")
    user_id = request.state.user["sub"]

    result = await agent_run(
        user_question=query_req.message,
        account_id=query_req.account_id,
        user_id=user_id,
        conversation_history=query_req.conversation_history,
        query_region=query_req.region,
    )

    logger.info(
        f"Agent completed: {result.get('iterations', 0)} iterations, "
        f"severity={result.get('severity')}"
    )

    return QueryResponse(
        answer=result["answer"],
        severity=result.get("severity"),
        evidence=result.get("evidence", []),
        recommended_actions=result.get("recommended_actions", []),
        steps_taken=result.get("steps_taken", []),
        iterations=result.get("iterations", 0),
        events_count=result.get("events_count", 0),
        raw_events=[],
    )



@router.get("/health")
async def health_check():
    """Health check endpoint — returns status and current UTC timestamp."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "CloudTrail AI Investigator",
    }

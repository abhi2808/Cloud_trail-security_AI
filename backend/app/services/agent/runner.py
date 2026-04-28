"""
ReAct loop orchestrator — the core agent runner.
Coordinates: prompt building → AI reasoning → tool execution → memory → repeat.
"""

import json
import logging

import boto3
from botocore.config import Config

from app.db.repositories.account_repository import account_repository
from app.core.encryption import decrypt_value
from app.services.agent.memory import InvestigationMemory
from app.services.agent.tools import execute_tool, TOOL_NAMES
from app.services.agent.prompts import build_agent_system_prompt
from app.services import iam_reader

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 6  # Lowered from 8 — each iteration costs ~25-43s on Groq free tier


def _make_session(access_key: str, secret_key: str, region: str):
    """Create a boto3 Session with explicit credentials. Never logs credentials."""
    return boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region or "ap-south-1",
    )


def _format_history(conversation_history: list) -> str:
    if not conversation_history:
        return "None"
    lines = []
    for msg in conversation_history[-6:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _clean_json(raw: str) -> str:
    """Strip markdown code fences from AI response before JSON parsing."""
    cleaned = raw.strip()
    for fence in ("```json", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


async def _call_agent_ai(messages: list) -> str:
    """
    Call the configured AI provider through ai.agent_think().
    Applies a sliding window to cap token usage:
      - messages[0]: system prompt (always kept)
      - messages[1]: original user question (always kept)
      - messages[-6:]: last 3 turn-pairs (tool call + result each)
    This prevents the growing context from triggering Groq 429s.
    """
    from app.services.ai import agent_think
    if len(messages) > 8:
        windowed = [messages[0], messages[1]] + messages[-6:]
    else:
        windowed = messages
    return await agent_think(windowed)


async def run(
    user_question: str,
    account_id: str,
    user_id: str,
    conversation_history: list,
    query_region: str = "all",
) -> dict:
    """
    Execute the full ReAct investigation loop.

    Returns a dict with:
      answer, severity, evidence, recommended_actions,
      steps_taken, iterations, events_count
    """
    # ── Step 1: Fetch and decrypt account credentials ─────────────────────
    account_doc = await account_repository.get_account_by_id(account_id, user_id)
    if not account_doc:
        return _error_response("Account not found or access denied.")

    try:
        access_key = decrypt_value(account_doc["access_key_id"])
        secret_key = decrypt_value(account_doc["secret_access_key"])
    except Exception:
        return _error_response("Failed to decrypt account credentials.")

    account_region = account_doc.get("region", "ap-south-1")
    if account_region == "all":
        account_region = "ap-south-1"

    session = _make_session(access_key, secret_key, account_region)

    # ── Step 2: Get caller identity (best-effort) ─────────────────────────
    identity = await iam_reader.get_caller_identity(session)
    aws_account_id = identity.get("account_id", "unknown")
    logger.info(f"Agent started for AWS account {aws_account_id}")

    # ── Step 3: Initialize memory ─────────────────────────────────────────
    memory = InvestigationMemory(user_question)

    # ── Step 4: Build initial AI messages ─────────────────────────────────
    system_prompt = build_agent_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Question: {user_question}\n\n"
                f"Previous conversation context:\n{_format_history(conversation_history)}"
            ),
        },
    ]

    finish_payload = None
    iteration = 0

    # ── Step 5: ReAct loop ────────────────────────────────────────────────
    while iteration < MAX_ITERATIONS:

        # Inject running investigation context after the first step
        if iteration > 0:
            messages.append({
                "role": "user",
                "content": memory.build_context_for_ai(),
            })

        # Call AI
        try:
            raw_response = await _call_agent_ai(messages)
        except Exception as e:
            logger.error(f"Agent AI call failed on iteration {iteration}: {e}")
            break

        # Parse JSON — retry once on failure
        parsed = None
        for attempt in range(2):
            try:
                parsed = json.loads(_clean_json(raw_response))
                break
            except json.JSONDecodeError:
                if attempt == 0:
                    logger.warning(f"JSON parse failed on iteration {iteration}, retrying...")
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON. "
                            "Respond ONLY with a single valid JSON object in FORMAT A or FORMAT B. "
                            "No markdown, no preamble."
                        ),
                    })
                    try:
                        raw_response = await _call_agent_ai(messages)
                    except Exception:
                        pass
                else:
                    logger.error(f"JSON parse failed twice at iteration {iteration}")

        if parsed is None:
            break

        response_type = parsed.get("type", "")

        # ── Finish ────────────────────────────────────────────────────────
        if response_type == "finish":
            finish_payload = parsed
            break

        # ── Tool call ─────────────────────────────────────────────────────
        if response_type == "tool_call":
            tool_name = parsed.get("tool_name", "")
            params = parsed.get("params", {})
            reasoning = parsed.get("reasoning", "")

            if tool_name not in TOOL_NAMES or tool_name == "finish":
                logger.warning(f"Agent chose unknown tool: {tool_name}")
                messages.append({
                    "role": "user",
                    "content": (
                        f"Tool '{tool_name}' does not exist. "
                        "Choose a valid tool from AVAILABLE TOOLS."
                    ),
                })
                iteration += 1
                continue

            logger.info(f"Agent iteration {iteration + 1}: calling {tool_name}")
            result = await execute_tool(
                tool_name=tool_name,
                params=params,
                session=session,
                account_id=account_id,
                user_id=user_id,
                query_region=query_region,
            )

            memory.add_step(
                tool_name=tool_name,
                params=params,
                result=result if isinstance(result, dict) else {"items": result, "count": len(result) if isinstance(result, list) else 0},
                reasoning=reasoning,
            )

            # Add result as assistant message so AI sees it
            # Cap at 2000 chars to reduce per-call token count and avoid Groq rate limits
            result_str = json.dumps(result, default=str)[:2000]
            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "type": "tool_call",
                    "reasoning": reasoning,
                    "tool_name": tool_name,
                    "params": params,
                }),
            })
            messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}:\n{result_str}",
            })

            iteration += 1
            continue

        # Unknown response type
        logger.warning(f"Unexpected agent response type: {response_type}")
        break

    # ── Step 6: Build final response ──────────────────────────────────────
    if finish_payload:
        return {
            "answer": finish_payload.get("answer", "Investigation complete."),
            "severity": finish_payload.get("severity", "NONE"),
            "evidence": finish_payload.get("evidence", []),
            "recommended_actions": finish_payload.get("recommended_actions", []),
            "steps_taken": memory.to_response_steps(),
            "iterations": iteration,
            "events_count": 0,
        }

    # Loop exhausted — ask for best-effort summary
    logger.warning(f"Agent loop exhausted after {iteration} iterations, requesting summary.")
    try:
        messages.append({
            "role": "user",
            "content": (
                "You have reached the iteration limit. "
                "Summarise the investigation so far and provide your best verdict "
                "with the available evidence. Respond in FORMAT B (finish)."
            ),
        })
        raw_final = await _call_agent_ai(messages)
        final = json.loads(_clean_json(raw_final))
        return {
            "answer": final.get("answer", "Investigation incomplete — iteration limit reached."),
            "severity": final.get("severity", "MEDIUM"),
            "evidence": final.get("evidence", []),
            "recommended_actions": final.get("recommended_actions", [
                "Review CloudTrail logs manually for the time period in question."
            ]),
            "steps_taken": memory.to_response_steps(),
            "iterations": iteration,
            "events_count": 0,
        }
    except Exception as e:
        logger.error(f"Final summary call failed: {e}")
        return {
            "answer": (
                "Investigation reached the maximum step limit. "
                f"Completed {iteration} investigation steps. "
                "Please review the steps taken for partial findings."
            ),
            "severity": "MEDIUM",
            "evidence": memory.key_findings,
            "recommended_actions": ["Review CloudTrail logs manually."],
            "steps_taken": memory.to_response_steps(),
            "iterations": iteration,
            "events_count": 0,
        }


def _error_response(message: str) -> dict:
    return {
        "answer": f"⚠️ {message}",
        "severity": "NONE",
        "evidence": [],
        "recommended_actions": [],
        "steps_taken": [],
        "iterations": 0,
        "events_count": 0,
    }

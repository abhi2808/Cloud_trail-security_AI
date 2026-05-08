"""
ReAct loop orchestrator — the core agent runner.
Coordinates: prompt building → AI reasoning → tool execution → memory → repeat.
"""

import asyncio
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

# Sweep keywords — broad account-health questions need more steps than targeted lookups
_SWEEP_KEYWORDS = {
    "safe", "secure", "security", "overview", "audit", "risk", "risks",
    "everything", "posture", "summary", "health", "check", "issues",
    "what is wrong", "any issues", "vulnerable", "exposure", "exposed",
    "hygiene", "compliance", "compliant", "overall", "account",
}


def _get_max_iterations(question: str) -> int:
    """
    Return iteration limit based on query breadth.
    Sweep queries (broad account-health or EC2 security) → 14 steps.
    Targeted queries (specific resource/user) → 8 steps.
    """
    q = question.lower()
    if any(kw in q for kw in _SWEEP_KEYWORDS):
        return 14
    return 8


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
    if len(messages) > 14:
        windowed = [messages[0], messages[1]] + messages[-12:]
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
    max_iterations = _get_max_iterations(user_question)
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

    # Prioritise the UI dropdown selection (query_region) over the stored account region.
    # When the user picks "ap-south-1" in the UI, ALL service calls (EC2, IAM, CloudWatch…)
    # must use that region — not whatever region was stored in MongoDB when the account was added.
    # Fall back to account_region only when the user selected "all" or sent no region.
    if query_region and query_region != "all":
        session_region = query_region
    else:
        session_region = account_region

    session = _make_session(access_key, secret_key, session_region)

    # ── Step 2: Get caller identity (best-effort) ─────────────────────────
    identity = await iam_reader.get_caller_identity(session)
    aws_account_id = identity.get("account_id", "unknown")
    logger.info(f"Agent started for AWS account {aws_account_id}")

    # ── Step 3: Initialize memory ─────────────────────────────────────────
    memory = InvestigationMemory(user_question)

    # ── Step 4: Build initial AI messages ─────────────────────────────────
    system_prompt = build_agent_system_prompt(max_iterations=max_iterations)
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
    while iteration < max_iterations:

        # Inject running investigation context after the first step
        if iteration > 0:
            messages.append({
                "role": "user",
                "content": memory.build_context_for_ai(),
            })

        # Warn the agent on its final allowed tool-call iteration
        if iteration == max_iterations - 1:
            messages.append({
                "role": "user",
                "content": (
                    f"⚠️ BUDGET NOTICE: This is your final allowed tool call "
                    f"({max_iterations} of {max_iterations}). "
                    "After you receive this result, you will get ONE bonus iteration "
                    "to call 'finish'. Use it to submit your verdict — no further tool calls will be accepted."
                ),
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
                            "Respond ONLY with a single valid JSON object — one of: "
                            "FORMAT A (tool_call), FORMAT A2 (tool_calls batch), or FORMAT B (finish). "
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

        # ── Parallel tool calls (fan-out) ─────────────────────────────────
        if response_type == "tool_calls":
            calls = parsed.get("calls", [])
            reasoning = parsed.get("reasoning", "")

            if not calls:
                logger.warning("Agent returned tool_calls with empty calls array — skipping.")
                iteration += 1
                continue

            # Enforce max batch size of 10
            if len(calls) > 10:
                logger.warning(f"Parallel batch of {len(calls)} exceeds cap of 10 — truncating.")
                calls = calls[:10]

            # Validate all tool names before executing anything
            invalid = [c.get("tool_name") for c in calls if c.get("tool_name") not in TOOL_NAMES]
            if invalid:
                messages.append({
                    "role": "user",
                    "content": (
                        f"Unknown tool(s) in parallel batch: {invalid}. "
                        "All tool_name values must be from AVAILABLE TOOLS."
                    ),
                })
                iteration += 1
                continue

            logger.info(
                f"Agent iteration {iteration + 1}: parallel batch of "
                f"{len(calls)} tools: {[c['tool_name'] for c in calls]}"
            )

            # Execute all calls simultaneously — one failed call must not abort the rest
            raw_results = await asyncio.gather(
                *[
                    execute_tool(
                        tool_name=c["tool_name"],
                        params=c.get("params", {}),
                        session=session,
                        account_id=account_id,
                        user_id=user_id,
                        query_region=query_region,
                    )
                    for c in calls
                ],
                return_exceptions=True,
            )

            # Normalise exceptions → error dicts so the AI sees a consistent structure
            parallel_results = []
            for i, res in enumerate(raw_results):
                if isinstance(res, Exception):
                    logger.error(f"Parallel call {calls[i]['tool_name']} failed: {res}")
                    parallel_results.append({
                        "tool": calls[i]["tool_name"],
                        "params": calls[i].get("params", {}),
                        "result": {"error": str(res)},
                    })
                else:
                    parallel_results.append({
                        "tool": calls[i]["tool_name"],
                        "params": calls[i].get("params", {}),
                        "result": res,
                    })

            # Store as ONE memory entry — AI sees all results together next iteration
            memory.add_step(
                tool_name=f"parallel_batch({len(calls)} tools)",
                params={"calls": [c["tool_name"] for c in calls]},
                result={"parallel_results": parallel_results},
                reasoning=reasoning,
            )

            # Feed all results back as a single combined assistant + user message pair
            batch_summary = json.dumps(
                {"type": "tool_calls", "reasoning": reasoning, "calls": [c["tool_name"] for c in calls]},
            )
            results_str = json.dumps({"parallel_results": parallel_results}, default=str)[:16000]
            messages.append({"role": "assistant", "content": batch_summary})
            messages.append({
                "role": "user",
                "content": f"Parallel batch results ({len(calls)} tools):\n{results_str}",
            })

            # Counts as ONE iteration — the whole point of parallelism
            iteration += 1
            continue

        # ── Single tool call ──────────────────────────────────────────────
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
            # Cap at 6000 chars — covers ~20 EC2 instances or a large IAM policy.
            # The sliding window in _call_agent_ai manages overall context size.
            result_str = json.dumps(result, default=str)[:6000]
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

    # ── Bonus iteration: force finish (tool_calls blocked) ───────────────────
    logger.warning(f"Agent loop exhausted after {iteration} iterations — granting +1 bonus finish iteration.")
    try:
        messages.append({
            "role": "user",
            "content": (
                "🛑 TOOL CALLS ARE NOW CLOSED. "
                "You have used all allowed tool-call iterations. "
                "You MUST respond in FORMAT B (finish) RIGHT NOW. "
                "Summarise all findings from the investigation so far and return your verdict. "
                "Any response that is not a 'finish' type will be discarded."
            ),
        })
        raw_final = await _call_agent_ai(messages)
        final = json.loads(_clean_json(raw_final))

        # Strictly reject any tool_call/tool_calls attempt in the bonus round
        if final.get("type") in ("tool_call", "tool_calls"):
            logger.error("Agent attempted a tool call in bonus finish iteration — forcing fallback.")
            raise ValueError("tool calls not allowed in bonus iteration")

        return {
            "answer": final.get("answer", "Investigation incomplete — iteration limit reached."),
            "severity": final.get("severity", "MEDIUM"),
            "evidence": final.get("evidence", []),
            "recommended_actions": final.get("recommended_actions", [
                "Review CloudTrail logs manually for the time period in question."
            ]),
            "steps_taken": memory.to_response_steps(),
            "iterations": iteration + 1,  # +1 for the bonus round
            "events_count": 0,
        }
    except Exception as e:
        logger.error(f"Bonus finish iteration failed: {e}")
        return {
            "answer": (
                f"Investigation reached the step limit after {iteration} tool calls. "
                "Please review the investigation steps below for partial findings."
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

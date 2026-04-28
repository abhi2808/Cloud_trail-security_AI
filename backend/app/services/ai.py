"""
AI service — Gemini/Groq client initialization, intent extraction, and result interpretation.
Handles both Step 1 (NL → CloudTrail params) and Step 2 (events → human answer).
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import settings
from app.models.query import ExtractedIntent, CloudTrailEvent
from app.services.event_taxonomy import EVENT_TAXONOMY

logger = logging.getLogger(__name__)

# ─── Client Initialization ───────────────────────────────────────────────────

_gemini_client = None
_groq_client = None


def _get_gemini_client():
    """Lazily initialize and return the Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        try:
            from google import genai
            _gemini_client = genai.Client(api_key=settings.gemini_api_key)
            logger.info("Gemini client initialized successfully (google.genai)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise HTTPException(status_code=500, detail=f"Gemini initialization failed: {str(e)}")
    return _gemini_client


def _get_groq_client():
    """Lazily initialize and return the Groq client."""
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=settings.groq_api_key)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            raise HTTPException(status_code=500, detail=f"Groq initialization failed: {str(e)}")
    return _groq_client


# ─── AI Call Dispatchers ─────────────────────────────────────────────────────

def _call_gemini(system_prompt: str, user_message: str) -> str:
    """Send a prompt to Gemini 2.0 Flash and return the text response."""
    try:
        client = _get_gemini_client()
        from google import genai
        from google.genai import types
        full_prompt = f"{system_prompt}\n\nUser Query: {user_message}"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048,
            ),
        )
        return response.text.strip()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise HTTPException(status_code=502, detail=f"Gemini API error: {str(e)}")


def _call_groq(system_prompt: str, user_message: str) -> str:
    """Send a prompt to Groq (llama-3.3-70b-versatile) and return the text response."""
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(e)}")


def _call_ai(system_prompt: str, user_message: str) -> str:
    """Route the AI call to the configured provider."""
    if settings.ai_provider == "gemini":
        return _call_gemini(system_prompt, user_message)
    elif settings.ai_provider == "groq":
        return _call_groq(system_prompt, user_message)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI provider: {settings.ai_provider}",
        )


# ─── Step 1: Extract Intent ─────────────────────────────────────────────────

def _build_extract_intent_prompt() -> str:
    """Build the system prompt for intent extraction."""
    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""You are an expert AWS CloudTrail query parser. Your job is to convert natural language security questions into structured JSON parameters for querying AWS CloudTrail LookupEvents API.

{EVENT_TAXONOMY}

CURRENT DATE AND TIME: {today_str}

INSTRUCTIONS:
1. Analyze the user's question and extract the relevant CloudTrail query parameters.
2. Map natural language to the correct AWS event names using the taxonomy above.
3. For time references like "today", "yesterday", "last week", "this month", calculate the actual datetime based on the current date provided above.
4. If the query mentions multiple event types (e.g., "security group changes"), combine them as comma-separated values in event_name.
5. If the query is too vague (no specific resource, user, event type, or time context), set clarification_needed to true and provide a helpful clarification_message.
6. For "suspicious activity" queries, set query_type to "suspicious_activity" and event_name to "ConsoleLogin" as a starting point.
7. For root user queries, set username to "root" or use event_name based on context.

You MUST return ONLY a valid JSON object with these exact fields (no markdown, no code blocks, no preamble):
{{
    "event_name": "<CloudTrail event name or comma-separated names, or null>",
    "resource_id": "<AWS resource ID like i-xxxxx, arn:aws:xxx, or null>",
    "username": "<IAM username to filter by, or null>",
    "start_time": "<ISO 8601 datetime string, or null>",
    "end_time": "<ISO 8601 datetime string, or null>",
    "query_type": "<one of: resource_event, user_activity, general, suspicious_activity>",
    "clarification_needed": <true or false>,
    "clarification_message": "<helpful message if clarification needed, or null>"
}}

Return ONLY the JSON object. No other text."""


async def extract_intent(message: str, conversation_history: list[dict]) -> ExtractedIntent:
    """
    Extract structured CloudTrail query intent from a natural language message.
    Uses the configured AI provider to parse the user's question.
    """
    system_prompt = _build_extract_intent_prompt()

    # Build user message with conversation context
    user_message = message
    if conversation_history:
        context_lines = []
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_lines.append(f"{role}: {content}")
        context_str = "\n".join(context_lines)
        user_message = f"Previous conversation:\n{context_str}\n\nCurrent question: {message}"

    try:
        raw_response = _call_ai(system_prompt, user_message)

        # Clean up response — strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Parse JSON
        intent_data = json.loads(cleaned)
        intent = ExtractedIntent(**intent_data)
        logger.info(f"Extracted intent: event_name={intent.event_name}, query_type={intent.query_type}")
        return intent

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {raw_response[:500]}")
        # Return a clarification request instead of crashing
        return ExtractedIntent(
            query_type="general",
            clarification_needed=True,
            clarification_message="I had trouble understanding your query. Could you rephrase it? Try something like 'Who terminated EC2 instances today?' or 'Show IAM user creation events this week'.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract intent from query: {str(e)}",
        )


# ─── Step 2: Interpret Results ───────────────────────────────────────────────

def _build_interpret_prompt() -> str:
    """Build the system prompt for result interpretation."""
    return """You are a senior AWS security analyst. Your job is to interpret AWS CloudTrail events and provide a clear, investigator-style answer to security questions.

INSTRUCTIONS:
1. Lead with a direct, one-sentence answer to the question.
2. List key findings with bullet points including:
   - Timestamp (converted to IST, UTC+5:30)
   - Actor/Username (Who performed the action)
   - Target Resource Affected (Extract this clearly from the 'request_parameters' object - e.g., the name of the IAM user created, the ID of the EC2 instance altered, the name of the EKS cluster, etc. Do not skip this!)
   - Source IP address
   - AWS region
3. Flag anything suspicious with a ⚠️ icon:
   - Root user activity
   - No MFA on console login
   - Source IP that looks external (NOT RFC1918: not 10.x.x.x, 172.16-31.x.x, 192.168.x.x)
   - Off-hours actions (outside 09:00-18:00 IST)
   - Error codes present (unauthorized attempts)
   - Access key creation or deletion
   - CloudTrail configuration changes
4. If ZERO events are found: clearly state no matching events were found in CloudTrail, and suggest possible reasons:
   - Wrong time range (CloudTrail retains 90 days of management events)
   - Event not captured (data events require separate trail configuration)
   - Resource ID mismatch
   - Event may have occurred in a different AWS region
5. Keep the response under 300 words.
6. End with the line: "🔍 Total matching events found: X" (replace X with actual count)
7. NEVER invent or fabricate events that are not present in the provided data.
8. Format timestamps as: DD-MMM-YYYY HH:MM:SS IST

You will receive the user's question and a JSON array of CloudTrail events. Analyze them and respond."""


async def interpret_results(question: str, events: list[CloudTrailEvent]) -> str:
    """
    Interpret CloudTrail events and generate a human-readable security analysis.
    """
    system_prompt = _build_interpret_prompt()

    # Serialize events to JSON for the AI
    events_data = []
    for event in events:
        events_data.append(event.model_dump(mode="json"))

    user_message = f"""Question: {question}

CloudTrail Events ({len(events)} found):
{json.dumps(events_data, indent=2, default=str)}"""

    try:
        answer = _call_ai(system_prompt, user_message)
        return answer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Result interpretation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to interpret CloudTrail results: {str(e)}",
        )


# ─── Agent Think: used by the ReAct loop ─────────────────────────────────────

async def agent_think(messages: list[dict], temperature: float = 0.1) -> str:
    """
    Pass a messages array to the configured AI provider and return raw text.
    The runner handles JSON parsing and retry logic.
    Temperature 0.1 for consistent JSON output.
    """
    if settings.ai_provider == "gemini":
        return _agent_think_gemini(messages, temperature)
    elif settings.ai_provider == "groq":
        return _agent_think_groq(messages, temperature)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI provider: {settings.ai_provider}",
        )


def _agent_think_gemini(messages: list[dict], temperature: float) -> str:
    """Send a messages array to Gemini. Combines system + user messages into a single prompt."""
    try:
        client = _get_gemini_client()
        from google.genai import types

        # Gemini doesn't use chat-style messages natively in this SDK — flatten to one prompt
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.insert(0, f"SYSTEM INSTRUCTIONS:\n{content}")
            elif role == "assistant":
                parts.append(f"ASSISTANT:\n{content}")
            else:
                parts.append(f"USER:\n{content}")

        full_prompt = "\n\n---\n\n".join(parts)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=4096,
            ),
        )
        return response.text.strip()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini agent_think failed: {e}")
        raise HTTPException(status_code=502, detail=f"Gemini API error: {str(e)}")


def _agent_think_groq(messages: list[dict], temperature: float) -> str:
    """Send a messages array to Groq directly (natively supports chat format)."""
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
        )
        return response.choices[0].message.content.strip()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Groq agent_think failed: {e}")
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(e)}")

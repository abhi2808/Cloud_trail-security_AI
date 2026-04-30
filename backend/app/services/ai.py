"""
AI service — Gemini/Groq client initialization and agent thought orchestration.
Handles the ReAct loop decision-making processes only.
"""

import logging
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

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


# ─── Agent Think: used by the ReAct loop ─────────────────────────────────────

def _agent_think_gemini(messages: list[dict], temperature: float) -> str:
    """Send a messages array to Gemini. Flattens to a single prompt (SDK limitation)."""
    try:
        client = _get_gemini_client()
        from google.genai import types

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


async def agent_think(messages: list[dict], temperature: float = 0.1) -> str:
    """
    Public entry point for all agent AI calls from runner.py.
    Routes to Groq or Gemini based on the configured AI_PROVIDER env variable.
    """
    provider = getattr(settings, "ai_provider", "groq").lower()
    if provider == "gemini":    
        logger.info("Using Gemini AI provider for agent_think")
        return _agent_think_gemini(messages, temperature)
    elif provider == "groq":
        logger.info("Using Groq AI provider for agent_think")
        return _agent_think_groq(messages, temperature)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI provider: {settings.ai_provider}",
        )

"""
AI service — AWS Bedrock (Claude Haiku via APAC cross-region inference).

Credential separation:
  - Bedrock client  → BEDROCK_* keys from .env  (backend-owned)
  - Customer boto3 sessions → MongoDB stored creds (never mixed in here)

Public API (signatures unchanged):
  agent_think(messages, temperature=0.1) -> str
"""

import logging
import boto3
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Module-level Bedrock client (backend creds only) ────────────────────────
# Initialized once at import time.  Uses BEDROCK_* env vars — never the
# customer credentials that are stored in MongoDB.
_client = boto3.client(
    "bedrock-runtime",
    region_name=settings.bedrock_region,
    aws_access_key_id=settings.bedrock_access_key_id,
    aws_secret_access_key=settings.bedrock_secret_access_key,
)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _to_bedrock_messages(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Convert OpenAI-style message dicts → Bedrock Converse API format.

    FROM: {"role": "system"|"user"|"assistant", "content": "text"}
    TO:   {"role": "user"|"assistant", "content": [{"text": "text"}]}

    System messages are extracted into a separate list (Bedrock's system= param).
    Consecutive messages with the same role are merged to satisfy the alternating
    user/assistant constraint imposed by the Converse API.
    """
    system_parts: list[str] = []
    bedrock_messages: list[dict] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue

        if role == "system":
            system_parts.append(content)
            continue

        # Normalize: Bedrock only accepts "user" or "assistant"
        normalized_role = "assistant" if role == "assistant" else "user"

        # Merge consecutive same-role messages (Bedrock requires strict alternation)
        if bedrock_messages and bedrock_messages[-1]["role"] == normalized_role:
            bedrock_messages[-1]["content"][0]["text"] += f"\n\n{content}"
        else:
            bedrock_messages.append({
                "role": normalized_role,
                "content": [{"text": content}],
            })

    system_blocks = [{"text": "\n\n".join(system_parts)}] if system_parts else []
    return bedrock_messages, system_blocks


def _converse(
    messages: list[dict],
    system_blocks: list[dict],
    temperature: float,
    max_tokens: int = 1000,
) -> str:
    """
    Single call to the Bedrock Converse API.
    Raises HTTPException(502) on any Bedrock error.
    """
    try:
        response = _client.converse(
            modelId=settings.bedrock_model_id,
            messages=messages,
            system=system_blocks,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        )
        return response["output"]["message"]["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Bedrock converse failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Bedrock API error: {str(e)}",
        )


# ─── Public interface (signatures identical to previous ai.py) ────────────────

async def agent_think(messages: list[dict], temperature: float = 0.1) -> str:
    """
    Primary entry point called by runner.py on every ReAct loop iteration.

    Accepts the same OpenAI-style messages list the runner builds.
    Internally converts to Bedrock Converse format and calls Claude Haiku
    via APAC cross-region inference.
    """
    logger.info(
        "agent_think → Bedrock %s (%d messages)",
        settings.bedrock_model_id,
        len(messages),
    )
    bedrock_messages, system_blocks = _to_bedrock_messages(messages)

    # Guard: Bedrock requires at least one message
    if not bedrock_messages:
        raise HTTPException(status_code=400, detail="No non-system messages to send to Bedrock.")

    return _converse(bedrock_messages, system_blocks, temperature, max_tokens=1000)

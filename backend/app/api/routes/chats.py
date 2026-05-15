"""
Chat history API routes.

GET    /api/chats                        — list all sessions for the authenticated user
POST   /api/chats                        — create a new session
GET    /api/chats/{session_id}           — get session with full message history
POST   /api/chats/{session_id}/messages  — append a message to a session
PATCH  /api/chats/{session_id}           — update session title
DELETE /api/chats/{session_id}           — delete session
DELETE /api/chats/{session_id}/messages  — clear all messages (keep session)
"""

import logging
from fastapi import APIRouter, HTTPException, Request, status

from app.models.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    AppendMessageRequest,
    ChatSessionResponse,
    ChatSessionSummary,
)
from app.db.repositories.chat_repository import chat_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_user_id(request: Request) -> str:
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return request.state.user["sub"]


# ── List sessions (sidebar) ────────────────────────────────────────
@router.get("", response_model=list[ChatSessionSummary])
async def list_sessions(request: Request):
    user_id = _get_user_id(request)
    sessions = await chat_repository.list_sessions_fast(user_id)
    return sessions


# ── Create new session ─────────────────────────────────────────────
@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(body: ChatSessionCreate, request: Request):
    user_id = _get_user_id(request)
    session = await chat_repository.create_session(
        user_id=user_id,
        title=body.title or "New Conversation",
        account_id=body.account_id,
        region=body.region or "all",
    )
    return session


# ── Get single session ─────────────────────────────────────────────
@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str, request: Request):
    user_id = _get_user_id(request)
    session = await chat_repository.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Append message ─────────────────────────────────────────────────
@router.post("/{session_id}/messages", response_model=ChatSessionResponse)
async def append_message(session_id: str, body: AppendMessageRequest, request: Request):
    user_id = _get_user_id(request)
    session = await chat_repository.append_message(
        session_id, user_id, body.message.model_dump()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Update title ───────────────────────────────────────────────────
@router.patch("/{session_id}", response_model=ChatSessionResponse)
async def update_session(session_id: str, body: ChatSessionUpdate, request: Request):
    user_id = _get_user_id(request)
    if not body.title:
        raise HTTPException(status_code=400, detail="Nothing to update")
    session = await chat_repository.update_title(session_id, user_id, body.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ── Delete session ─────────────────────────────────────────────────
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, request: Request):
    user_id = _get_user_id(request)
    deleted = await chat_repository.delete_session(session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


# ── Clear messages ─────────────────────────────────────────────────
@router.delete("/{session_id}/messages", response_model=ChatSessionResponse)
async def clear_messages(session_id: str, request: Request):
    user_id = _get_user_id(request)
    session = await chat_repository.clear_messages(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

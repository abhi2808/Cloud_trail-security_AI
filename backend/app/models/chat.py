from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str                   # "user" | "assistant"
    content: str
    timestamp: Optional[str] = None
    severity: Optional[str] = None
    evidence: Optional[List] = []
    recommended_actions: Optional[List] = []
    steps_taken: Optional[List] = []
    iterations: Optional[int] = 0
    events_count: Optional[int] = 0


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    account_id: Optional[str] = None
    region: Optional[str] = "all"


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None


class AppendMessageRequest(BaseModel):
    message: ChatMessage


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    account_id: Optional[str] = None
    region: Optional[str] = "all"
    messages: List[ChatMessage] = []
    created_at: str
    updated_at: str


class ChatSessionSummary(BaseModel):
    """Lightweight version for sidebar listing (no messages)."""
    id: str
    title: str
    account_id: Optional[str] = None
    region: Optional[str] = "all"
    message_count: int = 0
    created_at: str
    updated_at: str

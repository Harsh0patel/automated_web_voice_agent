"""
Pydantic models for the memory layer.

MemoryEntry: A single exchange in a conversation turn
SessionMemory: A full session stored in MongoDB
ConversationSummary: A summarized block of exchanges
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app import config as cfg


class MemoryEntry(BaseModel):
    """A single exchange in a conversation turn."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    action: Optional[dict] = None


class ConversationSummary(BaseModel):
    """A summary of a block of exchanges."""
    block_start: int
    block_end: int
    summary_text: str
    exchange_count: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class SessionMemory(BaseModel):
    """A session's full conversation stored in MongoDB."""
    session_id: str
    exchanges: list[MemoryEntry] = []
    exchange_count: int = 0
    summaries: list[ConversationSummary] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


MAX_EXCHANGES_BEFORE_SUMMARY: int = cfg.MEMORY_MAX_EXCHANGES
MAX_RAW_TOKENS_BEFORE_SUMMARY: int = cfg.MEMORY_MAX_TOKENS
MAX_RAW_EXCHANGES_IN_CONTEXT: int = cfg.MEMORY_MAX_RAW_IN_CONTEXT

MONGO_COLLECTION_SESSIONS: str = "sessions"
MONGO_COLLECTION_SUMMARIES: str = "session_summaries"

"""
MemoryManager - the core API for the memory layer.

Provides in-memory buffer for active session exchanges, MongoDB persistence
when the buffer reaches capacity, async summary generation, and context
injection for the LLM.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from backend.app import config as cfg
from backend.app.logger import get_logger
from backend.memory.models import (
    MAX_EXCHANGES_BEFORE_SUMMARY,
    MAX_RAW_EXCHANGES_IN_CONTEXT,
    MAX_RAW_TOKENS_BEFORE_SUMMARY,
    MONGO_COLLECTION_SESSIONS,
    MONGO_COLLECTION_SUMMARIES,
    ConversationSummary,
    MemoryEntry,
)
from backend.memory.summarizer import summarize_exchanges

logger = get_logger(__name__)


def _get_mongo_client() -> AsyncIOMotorClient | None:
    """Get MongoDB client using existing central config."""
    if not cfg.MONGO_URI:
        return None
    try:
        return AsyncIOMotorClient(cfg.MONGO_URI, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
    except Exception as e:
        logger.error("Failed to create MongoDB client for memory layer: %s", e)
        return None


def _estimate_tokens(chars: int) -> int:
    return chars // 4


class MemoryManager:
    """Manages conversation memory per session."""

    def __init__(self):
        self._buffers: dict[str, list[MemoryEntry]] = {}
        self._counters: dict[str, int] = {}
        self._session_locks: dict[str, asyncio.Lock] = {}
        self._mongo_client: AsyncIOMotorClient | None = None
        self._mongo_available: bool = False
        self._init_lock = asyncio.Lock()

    def _session_lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]

    async def _ensure_mongo(self) -> bool:
        if self._mongo_client is None:
            async with self._init_lock:
                if self._mongo_client is None:
                    client = _get_mongo_client()
                    if client is not None:
                        try:
                            await client.admin.command("ping")
                            self._mongo_client = client
                            self._mongo_available = True
                        except Exception:
                            self._mongo_available = False
                    else:
                        self._mongo_available = False
        return self._mongo_available

    def _buffer(self, session_id: str) -> list[MemoryEntry]:
        if session_id not in self._buffers:
            self._buffers[session_id] = []
            self._counters[session_id] = 0
        return self._buffers[session_id]

    def _raw_exchange_chars(self, session_id: str) -> int:
        buf = self._buffer(session_id)
        return sum(len(e.content) for e in buf)

    async def get_context(self, session_id: str) -> str:
        """Build memory context for the LLM prompt."""
        parts: list[str] = []
        async with self._session_lock(session_id):
            buf = self._buffer(session_id)

        if await self._ensure_mongo():
            try:
                db = self._mongo_client.memory
                cursor = db[MONGO_COLLECTION_SUMMARIES].find({"session_id": session_id}).sort("block_start", 1)
                summaries = []
                async for doc in cursor:
                    summaries.append(doc.get("summary_text", ""))
                if summaries:
                    parts.append("Previous conversation summary:")
                    parts.extend(f"- {s}" for s in summaries[-3:])
                    parts.append("")
            except Exception:
                pass

        if buf:
            recent = buf[-MAX_RAW_EXCHANGES_IN_CONTEXT:]
            parts.append("Recent messages:")
            for entry in recent:
                role_label = "User" if entry.role == "user" else "Assistant"
                parts.append(f"{role_label}: {entry.content}")
            parts.append("")

        return "\n".join(parts).strip()

    async def add_exchange(
        self, session_id: str, user_message: str, assistant_message: str, action: Optional[dict] = None,
    ) -> None:
        """Store a user <-> assistant exchange."""
        async with self._session_lock(session_id):
            buf = self._buffer(session_id)
            self._counters[session_id] += 1
            buf.append(MemoryEntry(role="user", content=user_message))
            buf.append(MemoryEntry(role="assistant", content=assistant_message, action=action))
            exchange_num = self._counters[session_id]
            raw_tokens = _estimate_tokens(self._raw_exchange_chars(session_id))
            should_flush = exchange_num >= MAX_EXCHANGES_BEFORE_SUMMARY or raw_tokens >= MAX_RAW_TOKENS_BEFORE_SUMMARY

        if should_flush:
            await self._flush_and_summarize(session_id)

    async def _flush_and_summarize(self, session_id: str) -> None:
        async with self._session_lock(session_id):
            buf = self._buffer(session_id)
            if not buf:
                return
            exchange_num = self._counters[session_id]

            if not await self._ensure_mongo():
                self._buffers[session_id] = []
                return

            try:
                db = self._mongo_client.memory
                exchanges_data = [e.model_dump(mode="json") for e in buf]
                set_fields = {
                    "session_id": session_id,
                    "exchange_count": exchange_num,
                    "updated_at": datetime.now(tz=timezone.utc).isoformat(),
                }
                await db[MONGO_COLLECTION_SESSIONS].update_one(
                    {"session_id": session_id},
                    {"$set": set_fields, "$push": {"exchanges": {"$each": exchanges_data}}},
                    upsert=True,
                )
                block_start = exchange_num - len(buf) // 2 + 1
                asyncio.create_task(self._generate_and_store_summary(session_id, buf, block_start, exchange_num))
                self._buffers[session_id] = []
            except Exception as e:
                logger.error("Failed to flush session %s to MongoDB: %s", session_id[:8], e)

    async def _generate_and_store_summary(self, session_id: str, exchanges: list[MemoryEntry], block_start: int, block_end: int) -> None:
        try:
            summary_text = await summarize_exchanges(exchanges)
            if not summary_text:
                return
            if not await self._ensure_mongo():
                return
            db = self._mongo_client.memory
            summary_doc = {
                "session_id": session_id, "block_start": block_start, "block_end": block_end,
                "summary_text": summary_text, "exchange_count": len(exchanges),
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            await db[MONGO_COLLECTION_SUMMARIES].insert_one(summary_doc)
        except Exception as e:
            logger.error("Failed to store summary for session %s: %s", session_id[:8], e)

    async def finalize_session(self, session_id: str) -> None:
        buf_copy: list[MemoryEntry] = []
        block_start = 0
        block_end = 0
        async with self._session_lock(session_id):
            buf = self._buffer(session_id)
            if buf:
                exchange_num = self._counters[session_id]
                block_start = exchange_num - len(buf) // 2 + 1
                block_end = exchange_num
                if await self._ensure_mongo():
                    try:
                        db = self._mongo_client.memory
                        exchanges_data = [e.model_dump(mode="json") for e in buf]
                        await db[MONGO_COLLECTION_SESSIONS].update_one(
                            {"session_id": session_id},
                            {"$set": {"updated_at": datetime.now(tz=timezone.utc).isoformat()},
                             "$push": {"exchanges": {"$each": exchanges_data}}},
                            upsert=True,
                        )
                    except Exception as e:
                        logger.warning("Failed to finalize session %s: %s", session_id[:8], e)
                buf_copy = list(buf)
            self._session_locks.pop(session_id, None)
            self._buffers.pop(session_id, None)
            self._counters.pop(session_id, None)

        if buf_copy:
            await self._generate_and_store_summary(session_id, buf_copy, block_start, block_end)

    def get_exchange_count(self, session_id: str) -> int:
        return self._counters.get(session_id, 0)

    async def clear_session(self, session_id: str) -> None:
        async with self._session_lock(session_id):
            self._buffers.pop(session_id, None)
            self._counters.pop(session_id, None)
            self._session_locks.pop(session_id, None)
            if await self._ensure_mongo():
                try:
                    db = self._mongo_client.memory
                    await db[MONGO_COLLECTION_SESSIONS].delete_one({"session_id": session_id})
                    await db[MONGO_COLLECTION_SUMMARIES].delete_many({"session_id": session_id})
                except Exception:
                    pass

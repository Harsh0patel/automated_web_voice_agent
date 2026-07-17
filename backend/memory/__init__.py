"""
Memory layer - provides persistent, session-aware conversation memory.

Components:
  - models.py: Pydantic models for memory entries
  - manager.py: Core MemoryManager with in-memory buffer + MongoDB persistence
  - summarizer.py: Async LLM call to summarize blocks of exchanges
"""
from backend.memory.manager import MemoryManager
from backend.memory.models import ConversationSummary, MemoryEntry

__all__ = ["MemoryManager", "MemoryEntry", "ConversationSummary"]

"""
Unit tests for the MemoryManager class.

Tests cover:
  - In-memory buffer management
  - Context building (with and without MongoDB)
  - Exchange storage and flush thresholds
  - MongoDB persistence (mocked)
  - Session finalization
  - Session cleanup
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.memory.models import MAX_EXCHANGES_BEFORE_SUMMARY, MemoryEntry


# ============================================================
# Helpers
# ============================================================

class AsyncIter:
    """Convert a list into an async-iterable for mocking MongoDB cursors."""
    def __init__(self, items):
        self._items = items
        self._i = 0
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self._i >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._i]
        self._i += 1
        return item


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def memory_manager():
    """
    Create a fresh MemoryManager for each test.
    Disables MONGO_URI so _get_mongo_client returns None immediately
    (no 3-second timeout waiting for MongoDB ping).
    """
    import backend.app.config as cfg
    orig_uri = cfg.MONGO_URI
    cfg.MONGO_URI = ""

    from backend.memory.manager import MemoryManager
    mm = MemoryManager()

    yield mm

    cfg.MONGO_URI = orig_uri


@pytest.fixture
def mongo_cursor():
    """
    Create a mock MongoDB cursor that supports async iteration.
    Returns a callable: mongo_cursor(items) → AsyncMock cursor
    """
    def _make_cursor(items):
        cursor = AsyncMock()
        cursor.__aiter__ = MagicMock(return_value=AsyncIter(items))
        cursor.sort = MagicMock(return_value=cursor)
        return cursor
    return _make_cursor


@pytest.fixture
def mock_summarizer():
    """Mock the summarizer to avoid actual LLM calls."""
    with patch(
        "backend.memory.manager.summarize_exchanges",
        new_callable=AsyncMock,
        return_value="User asked about doctors. AI showed them.",
    ):
        yield


class _MockDB:
    """
    Mock database that supports BOTH attribute access (db.sessions)
    AND item access (db["sessions"]) — because production code uses
    db[MONGO_COLLECTION_SESSIONS] which is item access, but MagicMock's
    attribute and item access return DIFFERENT mock objects.
    """
    def __init__(self, sessions_mock, summaries_mock):
        self._sessions = sessions_mock
        self._summaries = summaries_mock

    def __getitem__(self, key):
        if key == "sessions":
            return self._sessions
        if key == "session_summaries":
            return self._summaries
        raise KeyError(key)

    @property
    def sessions(self):
        return self._sessions

    @property
    def session_summaries(self):
        return self._summaries


@pytest.fixture
def memory_manager_with_mongo(memory_manager, mongo_cursor):
    """
    MemoryManager with MongoDB pre-initialized (no real connection needed).
    Returns (mm, mock_db) for test assertions.
    """
    mock_client = AsyncMock()
    mock_client.admin = AsyncMock()
    mock_client.admin.command = AsyncMock(return_value={"ok": 1})

    # Collection mocks
    mock_sessions = AsyncMock()
    mock_summaries = AsyncMock()
    mock_summaries.find = MagicMock()
    mock_summaries.find.return_value = mongo_cursor([])
    mock_summaries.insert_one = AsyncMock()

    # _MockDB supports both attribute and item access
    mock_db = _MockDB(mock_sessions, mock_summaries)
    mock_client.memory = mock_db

    # Inject directly into MemoryManager
    memory_manager._mongo_client = mock_client
    memory_manager._mongo_available = True

    return memory_manager, mock_db


# ============================================================
# Tests: Buffer Management
# ============================================================

class TestBufferManagement:
    """Tests for internal buffer methods."""

    def test_init_empty(self, memory_manager):
        """A new MemoryManager should have no buffers or counters."""
        assert memory_manager._buffers == {}
        assert memory_manager._counters == {}

    def test_buffer_creates_new(self, memory_manager):
        """_buffer() should create a new list for unknown session."""
        buf = memory_manager._buffer("session-1")
        assert buf == []
        assert memory_manager._buffers["session-1"] is buf
        assert memory_manager._counters["session-1"] == 0

    def test_buffer_returns_existing(self, memory_manager):
        """_buffer() should return the existing buffer for known session."""
        buf1 = memory_manager._buffer("session-1")
        buf2 = memory_manager._buffer("session-1")
        assert buf1 is buf2  # same object

    def test_buffer_multiple_sessions(self, memory_manager):
        """_buffer() should handle multiple sessions independently."""
        buf_a = memory_manager._buffer("session-a")
        buf_b = memory_manager._buffer("session-b")
        buf_a.append(MemoryEntry(role="user", content="hello"))
        assert len(buf_b) == 0
        assert len(buf_a) == 1

    def test_raw_exchange_chars(self, memory_manager):
        """_raw_exchange_chars should count total chars in buffer."""
        buf = memory_manager._buffer("s1")
        buf.append(MemoryEntry(role="user", content="hello"))
        buf.append(MemoryEntry(role="assistant", content="world"))
        assert memory_manager._raw_exchange_chars("s1") == 10

    def test_raw_exchange_chars_empty(self, memory_manager):
        """_raw_exchange_chars should return 0 for empty buffer."""
        memory_manager._buffer("s1")
        assert memory_manager._raw_exchange_chars("s1") == 0


# ============================================================
# Tests: get_context
# ============================================================

class TestGetContext:
    """Tests for get_context method."""

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_session(self, memory_manager):
        """get_context should return empty string for a session with no data."""
        context = await memory_manager.get_context("unknown-session")
        assert context == ""

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_session(self, memory_manager):
        """get_context should return empty for session with no exchanges."""
        memory_manager._buffer("empty-session")
        context = await memory_manager.get_context("empty-session")
        assert context == ""

    @pytest.mark.asyncio
    async def test_returns_recent_messages(self, memory_manager):
        """get_context should include recent user/assistant messages."""
        buf = memory_manager._buffer("s1")
        buf.append(MemoryEntry(role="user", content="Show me doctors"))
        buf.append(MemoryEntry(role="assistant", content="Here are our doctors"))

        context = await memory_manager.get_context("s1")

        assert "Recent messages:" in context
        assert "User: Show me doctors" in context
        assert "Assistant: Here are our doctors" in context

    @pytest.mark.asyncio
    async def test_includes_only_last_n_raw(self, memory_manager):
        """get_context should include at most MAX_RAW_EXCHANGES_IN_CONTEXT entries."""
        from backend.memory.models import MAX_RAW_EXCHANGES_IN_CONTEXT
        buf = memory_manager._buffer("s1")
        # Add more than MAX_RAW_EXCHANGES_IN_CONTEXT entries
        for i in range(MAX_RAW_EXCHANGES_IN_CONTEXT + 5):
            buf.append(MemoryEntry(role="user", content=f"query {i}"))
            buf.append(MemoryEntry(role="assistant", content=f"response {i}"))

        context = await memory_manager.get_context("s1")

        # Should have at most MAX_RAW_EXCHANGES_IN_CONTEXT entries (user + assistant pairs)
        # Each entry is 1 line, but User/Assistant pairs take 2 lines
        total_entries = context.count("User:") + context.count("Assistant:")
        assert total_entries == MAX_RAW_EXCHANGES_IN_CONTEXT

    @pytest.mark.asyncio
    async def test_includes_summaries_from_mongo(self, memory_manager_with_mongo, mongo_cursor):
        """get_context should include summaries from MongoDB when available."""
        mm, mock_db = memory_manager_with_mongo
        # Override cursor with one that returns a summary
        mock_db.session_summaries.find.return_value = mongo_cursor([
            {"summary_text": "User asked about doctors. AI showed them."},
        ])

        context = await mm.get_context("s1")

        assert "Previous conversation summary:" in context
        assert "User asked about doctors" in context

    @pytest.mark.asyncio
    async def test_combines_summaries_and_recent(self, memory_manager_with_mongo, mongo_cursor):
        """get_context should combine MongoDB summaries with recent raw exchanges."""
        mm, mock_db = memory_manager_with_mongo
        mock_db.session_summaries.find.return_value = mongo_cursor([
            {"summary_text": "User asked about doctors."},
        ])

        buf = mm._buffer("s1")
        buf.append(MemoryEntry(role="user", content="Show me cardiologists"))
        buf.append(MemoryEntry(role="assistant", content="Here they are"))

        context = await mm.get_context("s1")

        assert "Previous conversation summary:" in context
        assert "Recent messages:" in context
        assert "Show me cardiologists" in context

    @pytest.mark.asyncio
    async def test_handles_mongo_failure_gracefully(self, memory_manager):
        """get_context should work without MongoDB available."""
        memory_manager._buffer("s1").append(
            MemoryEntry(role="user", content="Hello")
        )
        context = await memory_manager.get_context("s1")
        assert "Recent messages:" in context
        assert "Hello" in context


# ============================================================
# Tests: add_exchange
# ============================================================

class TestAddExchange:
    """Tests for add_exchange method."""

    @pytest.mark.asyncio
    async def test_adds_user_and_assistant(self, memory_manager):
        """add_exchange should add both user and assistant entries."""
        await memory_manager.add_exchange(
            "s1",
            user_message="Show me doctors",
            assistant_message="Here are our doctors",
        )
        buf = memory_manager._buffer("s1")
        assert len(buf) == 2
        assert buf[0].role == "user"
        assert buf[0].content == "Show me doctors"
        assert buf[1].role == "assistant"
        assert buf[1].content == "Here are our doctors"

    @pytest.mark.asyncio
    async def test_increments_counter(self, memory_manager):
        """add_exchange should increment the exchange counter."""
        assert memory_manager.get_exchange_count("s1") == 0
        await memory_manager.add_exchange("s1", "hello", "hi")
        assert memory_manager.get_exchange_count("s1") == 1
        await memory_manager.add_exchange("s1", "how are you?", "good")
        assert memory_manager.get_exchange_count("s1") == 2

    @pytest.mark.asyncio
    async def test_stores_action(self, memory_manager):
        """add_exchange should store the action on the assistant entry."""
        action = {"type": "navigate", "path": "/doctors"}
        await memory_manager.add_exchange(
            "s1",
            user_message="Show me doctors",
            assistant_message="Navigating!",
            action=action,
        )
        buf = memory_manager._buffer("s1")
        assert buf[1].action == action

    @pytest.mark.asyncio
    async def test_no_action_by_default(self, memory_manager):
        """add_exchange should not set action if not provided."""
        await memory_manager.add_exchange("s1", "hello", "hi")
        buf = memory_manager._buffer("s1")
        assert buf[1].action is None

    @pytest.mark.asyncio
    async def test_triggers_flush_at_threshold(self, memory_manager_with_mongo, mongo_cursor):
        """
        add_exchange should trigger _flush_and_summarize when
        exchange count reaches MAX_EXCHANGES_BEFORE_SUMMARY.
        """
        mm, mock_db = memory_manager_with_mongo

        # Add exchanges one below threshold
        for i in range(MAX_EXCHANGES_BEFORE_SUMMARY - 1):
            await mm.add_exchange("s1", f"query {i}", f"response {i}")

        # Buffer should still have entries (not flushed yet)
        assert len(mm._buffer("s1")) > 0
        assert mm.get_exchange_count("s1") == MAX_EXCHANGES_BEFORE_SUMMARY - 1

        # This should trigger the flush
        await mm.add_exchange("s1", "trigger query", "trigger response")

        # Buffer should be cleared after flush
        assert len(mm._buffer("s1")) == 0
        assert mm.get_exchange_count("s1") == MAX_EXCHANGES_BEFORE_SUMMARY


# ============================================================
# Tests: _flush_and_summarize
# ============================================================

class TestFlushAndSummarize:
    """Tests for _flush_and_summarize method."""

    @pytest.mark.asyncio
    async def test_clears_buffer_without_mongo(self, memory_manager):
        """_flush_and_summarize should clear the buffer even without MongoDB."""
        buf = memory_manager._buffer("s1")
        buf.append(MemoryEntry(role="user", content="hello"))
        buf.append(MemoryEntry(role="assistant", content="hi"))

        await memory_manager._flush_and_summarize("s1")

        assert len(memory_manager._buffer("s1")) == 0

    @pytest.mark.asyncio
    async def test_returns_early_if_empty(self, memory_manager):
        """_flush_and_summarize should return immediately if buffer is empty."""
        memory_manager._buffer("s1")
        await memory_manager._flush_and_summarize("s1")  # should not raise

    @pytest.mark.asyncio
    async def test_writes_to_mongo(self, memory_manager_with_mongo):
        """_flush_and_summarize should write exchanges to MongoDB."""
        mm, mock_db = memory_manager_with_mongo
        buf = mm._buffer("s1")
        buf.append(MemoryEntry(role="user", content="hello"))
        buf.append(MemoryEntry(role="assistant", content="hi"))
        mm._counters["s1"] = 1

        await mm._flush_and_summarize("s1")

        # Should have called update_one on the sessions collection
        mock_db.sessions.update_one.assert_called_once()

        # Buffer should be cleared
        assert len(mm._buffer("s1")) == 0

    @pytest.mark.asyncio
    async def test_correct_update_one_syntax(self, memory_manager_with_mongo):
        """_flush_and_summarize should use correct MongoDB $push syntax."""
        mm, mock_db = memory_manager_with_mongo
        buf = mm._buffer("s1")
        buf.append(MemoryEntry(role="user", content="hello"))
        buf.append(MemoryEntry(role="assistant", content="hi"))
        mm._counters["s1"] = 1

        await mm._flush_and_summarize("s1")

        call_kwargs = mock_db.sessions.update_one.call_args[0]
        filter_arg = call_kwargs[0]
        update_arg = call_kwargs[1]

        assert filter_arg == {"session_id": "s1"}
        assert "$push" in update_arg
        # Verify $push has the correct field name (not bare $each)
        assert "exchanges" in update_arg["$push"]
        assert "$each" in update_arg["$push"]["exchanges"]


# ============================================================
# Tests: finalize_session
# ============================================================

class TestFinalizeSession:
    """Tests for finalize_session method."""

    @pytest.mark.asyncio
    async def test_cleans_up_in_memory_state(self, memory_manager):
        """finalize_session should remove buffer and counter."""
        memory_manager._buffer("s1")
        memory_manager._counters["s1"] = 5

        await memory_manager.finalize_session("s1")

        assert "s1" not in memory_manager._buffers
        assert "s1" not in memory_manager._counters

    @pytest.mark.asyncio
    async def test_flushes_remaining_to_mongo(self, memory_manager_with_mongo, mock_summarizer):
        """finalize_session should flush remaining exchanges to MongoDB."""
        mm, mock_db = memory_manager_with_mongo
        buf = mm._buffer("s1")
        buf.append(MemoryEntry(role="user", content="goodbye"))
        buf.append(MemoryEntry(role="assistant", content="bye"))
        mm._counters["s1"] = 1

        await mm.finalize_session("s1")

        # Should have called update_one
        mock_db.sessions.update_one.assert_called()

        # State cleaned up
        assert "s1" not in mm._buffers

    @pytest.mark.asyncio
    async def test_handles_empty_session(self, memory_manager):
        """finalize_session should clean up empty sessions gracefully."""
        memory_manager._buffer("empty")
        await memory_manager.finalize_session("empty")
        assert "empty" not in memory_manager._buffers
        assert "empty" not in memory_manager._counters


# ============================================================
# Tests: get_exchange_count
# ============================================================

class TestGetExchangeCount:
    """Tests for get_exchange_count method."""

    def test_returns_zero_for_unknown(self, memory_manager):
        """get_exchange_count should return 0 for unknown session."""
        assert memory_manager.get_exchange_count("unknown") == 0

    def test_returns_counter_value(self, memory_manager):
        """get_exchange_count should return the counter value."""
        memory_manager._counters["s1"] = 42
        assert memory_manager.get_exchange_count("s1") == 42


# ============================================================
# Tests: clear_session
# ============================================================

class TestClearSession:
    """Tests for clear_session method."""

    @pytest.mark.asyncio
    async def test_clears_in_memory_state(self, memory_manager):
        """clear_session should remove buffer and counter."""
        memory_manager._buffer("s1")
        memory_manager._counters["s1"] = 5

        await memory_manager.clear_session("s1")

        assert "s1" not in memory_manager._buffers
        assert "s1" not in memory_manager._counters

    @pytest.mark.asyncio
    async def test_clears_mongo_data(self, memory_manager_with_mongo):
        """clear_session should delete session data from MongoDB."""
        mm, mock_db = memory_manager_with_mongo
        mm._buffer("s1")
        await mm.clear_session("s1")

        mock_db.sessions.delete_one.assert_called_once_with({"session_id": "s1"})
        mock_db.session_summaries.delete_many.assert_called_once_with({"session_id": "s1"})


# ============================================================
# Tests: Integration-style scenarios
# ============================================================

class TestIntegrationScenarios:
    """End-to-end style tests simulating real usage patterns."""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, memory_manager_with_mongo, mock_summarizer):
        """
        Simulate a multi-turn conversation and verify context is built correctly.
        """
        mm, mock_db = memory_manager_with_mongo
        session = "integration-test"

        # Turn 1: User asks about doctors
        await mm.add_exchange(
            session, "Show me your doctors", "We have 200+ doctors!",
            action={"type": "navigate", "path": "/doctors"},
        )

        # Context should contain turn 1
        ctx1 = await mm.get_context(session)
        assert "Show me your doctors" in ctx1
        assert "We have 200+ doctors!" in ctx1
        assert mm.get_exchange_count(session) == 1

        # Turn 2: Follow-up about doctors
        await mm.add_exchange(
            session, "Show me cardiologists", "Dr. Sarah Mitchell is our cardiologist",
            action={"type": "navigate", "path": "/doctors?specialty=Cardiology"},
        )

        # Context should contain both turns
        ctx2 = await mm.get_context(session)
        assert "Show me your doctors" in ctx2
        assert "Dr. Sarah Mitchell" in ctx2
        assert mm.get_exchange_count(session) == 2

        # Finalize the session
        await mm.finalize_session(session)

        # State should be cleaned up
        assert session not in mm._buffers
        assert session not in mm._counters

    @pytest.mark.asyncio
    async def test_multiple_independent_sessions(self, memory_manager):
        """
        Verify that two sessions don't interfere with each other.
        """
        await memory_manager.add_exchange("session-a", "Hello A", "Hi A")
        await memory_manager.add_exchange("session-b", "Hello B", "Hi B")
        await memory_manager.add_exchange("session-a", "Query A2", "Response A2")

        ctx_a = await memory_manager.get_context("session-a")
        ctx_b = await memory_manager.get_context("session-b")

        assert "Hello A" in ctx_a
        assert "Query A2" in ctx_a
        assert "Hello B" in ctx_b
        assert "Query A2" not in ctx_b
        assert memory_manager.get_exchange_count("session-a") == 2
        assert memory_manager.get_exchange_count("session-b") == 1

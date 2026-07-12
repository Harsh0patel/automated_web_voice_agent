"""Unit tests for the MongoDB database module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetClient:
    """Tests for _get_client and get_db functions."""

    def test_get_client_returns_none_without_uri(self, monkeypatch):
        """Without MONGO_URI, _get_client should return None (not crash)."""
        from backend.core import database as db
        # Reset global client to force re-initialization
        db._client = None

        import backend.core.config as cfg
        original = cfg.MONGO_URI
        cfg.MONGO_URI = ""

        try:
            result = db._get_client()
            assert result is None, "Should return None when MONGO_URI is empty"
        finally:
            cfg.MONGO_URI = original

    @patch("backend.core.database.AsyncIOMotorClient")
    def test_get_client_creates_singleton(self, mock_client_cls):
        """_get_client should create and return a single client instance."""
        from backend.core import database as db

        # Ensure fresh state
        db._client = None

        client1 = db._get_client()
        client2 = db._get_client()

        assert client1 is client2, "Should return the same instance"
        mock_client_cls.assert_called_once()

    @patch("backend.core.database.AsyncIOMotorClient")
    def test_get_db_returns_scraped_data_db(self, mock_client_cls):
        """get_db should return the scraped_data database."""
        from backend.core import database as db
        db._client = None

        client = db._get_client()
        db_instance = db.get_db()

        assert db_instance is client.scraped_data

    @patch("backend.core.database._client", None)
    def test_cleanup_after_test(self):
        """Ensure global state is reset between tests."""
        from backend.core import database as db
        db._client = None
        assert db._client is None


@pytest.mark.usefixtures("mock_soniox_client")
class TestStorePage:
    """Tests for store_page function."""

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_store_inserts_one(self, mock_client_cls):
        """store_page should insert one document and return its ID."""
        from backend.core import database as db

        db._client = None
        instance = mock_client_cls.return_value
        mock_collection = instance.scraped_data.pages
        mock_collection.insert_one = AsyncMock()
        mock_collection.insert_one.return_value = MagicMock(inserted_id="abc123")
        mock_collection.create_index = AsyncMock()

        doc_id = await db.store_page(
            url="https://example.com",
            title="Example",
            content="Hello world",
        )

        assert doc_id == "abc123"
        mock_collection.insert_one.assert_awaited_once()
        inserted = mock_collection.insert_one.await_args[0][0]
        assert inserted["url"] == "https://example.com"
        assert inserted["title"] == "Example"
        assert inserted["content"] == "Hello world"
        assert inserted["metadata"] == {}

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_store_creates_text_index(self, mock_client_cls):
        """store_page should create a text index on pages collection."""
        from backend.core import database as db
        db._client = None

        instance = mock_client_cls.return_value
        mock_collection = instance.scraped_data.pages
        mock_collection.insert_one = AsyncMock()
        mock_collection.create_index = AsyncMock()

        await db.store_page(
            url="https://example.com",
            title="Test",
            content="Some content",
        )

        mock_collection.create_index.assert_awaited_once()
        args = mock_collection.create_index.await_args
        assert args is not None
        # Should create text index on content and title
        index_spec = args[0][0]
        assert ("content", "text") in index_spec
        assert ("title", "text") in index_spec

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_store_handles_index_error(self, mock_client_cls):
        """If index creation fails, store_page should not crash."""
        from backend.core import database as db
        db._client = None

        instance = mock_client_cls.return_value
        mock_collection = instance.scraped_data.pages
        mock_collection.insert_one = AsyncMock()
        mock_collection.create_index = AsyncMock(side_effect=Exception("Index error"))

        # Should not raise
        doc_id = await db.store_page(
            url="https://example.com",
            title="Test",
            content="Some content",
            metadata={"source": "test"},
        )

        assert doc_id is not None


class MockAsyncCursor:
    """Helper: simulates a MongoDB async cursor with chainable sort/limit."""
    def __init__(self, docs):
        self.docs = docs
        self.idx = 0
        self.sort = MagicMock(return_value=self)
        self.limit = MagicMock(return_value=self)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.idx >= len(self.docs):
            raise StopAsyncIteration
        doc = self.docs[self.idx]
        self.idx += 1
        return doc


class TestSearchPages:
    """Tests for search_pages function."""

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_search_returns_results(self, mock_client_cls):
        """search_pages should return matching documents."""
        from backend.core import database as db
        db._client = None

        mock_docs = [
            {"_id": type("", (), {"__str__": lambda s: "id1"})(), "url": "https://a.com", "title": "Page A",
             "content": "This is about medicine.", "score": 2.5},
            {"_id": type("", (), {"__str__": lambda s: "id2"})(), "url": "https://b.com", "title": "Page B",
             "content": "This is also about medicine.", "score": 1.5},
        ]

        mock_cursor = MockAsyncCursor(mock_docs)

        instance = mock_client_cls.return_value
        instance.scraped_data.pages.find = MagicMock(return_value=mock_cursor)

        results = await db.search_pages("medicine")

        assert len(results) == 2
        assert results[0]["url"] == "https://a.com"
        assert results[0]["score"] == 2.5
        assert results[1]["title"] == "Page B"

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_search_empty_returns_empty(self, mock_client_cls):
        """search_pages should return empty list when no matches."""
        from backend.core import database as db
        db._client = None

        mock_cursor = MockAsyncCursor([])

        instance = mock_client_cls.return_value
        instance.scraped_data.pages.find = MagicMock(return_value=mock_cursor)

        results = await db.search_pages("nonexistent")

        assert results == []

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_search_respects_limit(self, mock_client_cls):
        """search_pages should respect the limit parameter."""
        from backend.core import database as db
        db._client = None

        mock_cursor = MockAsyncCursor([])

        instance = mock_client_cls.return_value
        instance.scraped_data.pages.find = MagicMock(return_value=mock_cursor)

        await db.search_pages("test", limit=3)

        mock_cursor.sort.assert_called_once()
        # sort is called with a list of tuples
        args = mock_cursor.sort.call_args.args[0]
        assert ("score", {"$meta": "textScore"}) in args
        mock_cursor.limit.assert_called_once_with(3)


@pytest.mark.usefixtures("mock_soniox_client")
class TestGetAllPages:
    """Tests for get_all_pages function."""

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_get_all_returns_pages(self, mock_client_cls):
        """get_all_pages should return all stored pages."""
        from backend.core import database as db
        db._client = None

        class MockGetAllCursor:
            def __init__(self, docs):
                self.docs = docs
                self.idx = 0
            def __aiter__(self):
                return self
            async def __anext__(self):
                if self.idx >= len(self.docs):
                    raise StopAsyncIteration
                doc = self.docs[self.idx]
                self.idx += 1
                return doc
            def limit(self, *args, **kwargs):
                return self

        mock_docs = [
            {"_id": MagicMock(__str__=lambda x: "id1"), "url": "https://a.com",
             "title": "Page A", "content": "Long content..."},
        ]

        mock_cursor = MockGetAllCursor(mock_docs)

        instance = mock_client_cls.return_value
        instance.scraped_data.pages.find = MagicMock(return_value=mock_cursor)

        results = await db.get_all_pages()

        assert len(results) == 1
        assert results[0]["title"] == "Page A"
        assert results[0]["url"] == "https://a.com"
        assert "content_preview" in results[0]


class TestDeleteAllPages:
    """Tests for delete_all_pages function."""

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_delete_all(self, mock_client_cls):
        """delete_all_pages should delete all documents."""
        from backend.core import database as db
        db._client = None

        instance = mock_client_cls.return_value
        mock_collection = instance.scraped_data.pages
        mock_collection.delete_many = AsyncMock()
        mock_collection.delete_many.return_value = MagicMock(deleted_count=5)

        count = await db.delete_all_pages()

        assert count == 5
        mock_collection.delete_many.assert_awaited_once_with({})


class TestPing:
    """Tests for ping function."""

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_ping_success(self, mock_client_cls):
        """ping should return True when MongoDB is reachable."""
        from backend.core import database as db
        db._client = None

        instance = mock_client_cls.return_value
        instance.admin.command = AsyncMock(return_value={"ok": 1})

        result = await db.ping()
        assert result is True
        instance.admin.command.assert_awaited_once_with("ping")

    @pytest.mark.asyncio
    @patch("backend.core.database.AsyncIOMotorClient")
    async def test_ping_failure(self, mock_client_cls):
        """ping should return False when MongoDB is unreachable."""
        from backend.core import database as db
        db._client = None

        instance = mock_client_cls.return_value
        instance.admin.command = AsyncMock(side_effect=Exception("Connection refused"))

        result = await db.ping()
        assert result is False

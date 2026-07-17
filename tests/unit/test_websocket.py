"""
Unit tests for the WebSocket ConnectionManager class.
"""
from unittest.mock import AsyncMock

import pytest


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def test_init_empty_connections(self):
        """A new ConnectionManager should have no active connections."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()
        assert mgr.active_connections == []

    @pytest.mark.asyncio
    async def test_connect_adds_websocket(self, mock_websocket):
        """connect() should accept and add the websocket."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()

        await mgr.connect(mock_websocket)

        assert len(mgr.active_connections) == 1
        assert mock_websocket in mgr.active_connections
        mock_websocket.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self, mock_websocket):
        """disconnect() should remove the websocket from active connections."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()
        await mgr.connect(mock_websocket)
        assert len(mgr.active_connections) == 1

        mgr.disconnect(mock_websocket)

        assert len(mgr.active_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_does_nothing(self, mock_websocket):
        """Disconnecting a websocket not in the list should not raise."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()

        mgr.disconnect(mock_websocket)  # Should not raise
        assert len(mgr.active_connections) == 0

    @pytest.mark.asyncio
    async def test_send_json(self, mock_websocket):
        """send_json should delegate to websocket.send_json."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()
        data = {"type": "test", "key": "value"}

        await mgr.send_json(mock_websocket, data)

        mock_websocket.send_json.assert_awaited_once_with(data)

    @pytest.mark.asyncio
    async def test_connect_multiple(self, mock_websocket):
        """Multiple websockets can be connected simultaneously."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await mgr.connect(mock_websocket)
        await mgr.connect(ws2)
        await mgr.connect(ws3)

        assert len(mgr.active_connections) == 3

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        """broadcast() should send a message to all connected clients."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await mgr.connect(ws1)
        await mgr.connect(ws2)

        await mgr.broadcast("Hello everyone!")

        ws1.send_text.assert_awaited_once_with("Hello everyone!")
        ws2.send_text.assert_awaited_once_with("Hello everyone!")

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(self):
        """broadcast() should remove connections that fail to send."""
        from backend.api.routes.websocket import ConnectionManager
        mgr = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        await mgr.connect(ws1)
        await mgr.connect(ws2)

        await mgr.broadcast("Test")

        ws1.send_text.assert_awaited_once_with("Test")
        # ws2 should have been removed
        assert ws2 not in mgr.active_connections
        assert ws1 in mgr.active_connections

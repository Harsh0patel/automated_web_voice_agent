"""
Integration tests for WebSocket routes using FastAPI TestClient
with mocked external services (Soniox, OpenAI).
"""
import base64
from unittest.mock import AsyncMock

import pytest


class TestWebSocketConnection:
    """Integration tests for WebSocket connection lifecycle."""

    def test_welcome_message(self, client):
        """On connect, should receive a welcome message."""
        with client.websocket_connect("/ws") as ws:
            welcome = ws.receive_json()
            assert welcome["type"] == "connection_established"
            assert "message" in welcome
            assert "version" in welcome

    def test_welcome_has_correct_structure(self, client):
        """The welcome message should have expected fields."""
        with client.websocket_connect("/ws") as ws:
            welcome = ws.receive_json()
            assert "type" in welcome
            assert "message" in welcome
            assert "version" in welcome
            assert welcome["version"] == "1.1.0"

    def test_multiple_connections(self, client):
        """Multiple clients should all receive welcome messages."""
        with client.websocket_connect("/ws") as ws1:
            with client.websocket_connect("/ws") as ws2:
                w1 = ws1.receive_json()
                w2 = ws2.receive_json()
                assert w1["type"] == "connection_established"
                assert w2["type"] == "connection_established"


class TestWebSocketPlainText:
    """Plain text input goes through the full LLM pipeline."""

    def test_plain_text_triggers_query(self, client, mock_openai_client):
        """Sending plain text should return a query_result."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_text("Hello")

            ws.receive_json()  # processing (searching)
            ws.receive_json()  # db_lookup_skipped
            ws.receive_json()  # processing (llm)
            ws.receive_json()  # processing (tts)
            r = ws.receive_json()  # query_result
            assert r["type"] == "query_result"


class TestWebSocketJsonEcho:
    """Tests for JSON echo functionality."""

    def test_unknown_json_type_echo(self, client):
        """Sending JSON with unknown type should echo it back."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "unknown_type", "data": "test"})
            response = ws.receive_json()
            assert response["type"] == "echo"
            assert response["data"]["type"] == "unknown_type"

    def test_echo_with_custom_data(self, client):
        """Custom data should be preserved in echo."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"foo": "bar", "num": 42, "nested": {"a": 1}})
            response = ws.receive_json()
            assert response["type"] == "echo"
            assert response["data"]["foo"] == "bar"
            assert response["data"]["num"] == 42


class TestWebSocketBinaryAudio:
    """Integration tests for binary audio input."""

    def test_binary_chunk_received(self, client):
        """Sending binary data should return audio_chunk_received."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_bytes(b"test_audio_data")
            response = ws.receive_json()
            assert response["type"] == "audio_chunk_received"

    def test_multiple_binary_chunks(self, client):
        """Multiple binary chunks should accumulate in the buffer."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_bytes(b"chunk1")
            r1 = ws.receive_json()
            assert r1["total_buffer"] == 6
            ws.send_bytes(b"chunk2")
            r2 = ws.receive_json()
            assert r2["total_buffer"] == 12

    def test_process_audio_without_buffer_returns_error(self, client):
        """process_audio with no binary data should return error."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_json({"type": "process_audio", "format": "wav"})
            response = ws.receive_json()
            assert response["type"] == "error"

    def test_process_audio_pipeline_with_keys(self, client, mock_soniox_client, mock_openai_client):
        """Full audio pipeline with mocked services returns query_result."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_bytes(b"fake_wav_audio_data")
            ws.receive_json()  # chunk

            ws.send_json({"type": "process_audio", "format": "wav"})

            ws.receive_json()  # transcribing
            ws.receive_json()  # transcription
            ws.receive_json()  # searching
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()  # result
            assert r["type"] == "query_result"


class TestWebSocketAudioTranscribe:
    """Integration tests for audio_transcribe."""

    def test_audio_transcribe_empty_data_error(self, client):
        """audio_transcribe with empty data should return error."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_json({"type": "audio_transcribe", "format": "wav", "data": ""})
            r = ws.receive_json()
            assert r["type"] == "error"

    def test_audio_transcribe_invalid_base64(self, client):
        """audio_transcribe with invalid base64 should return error."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_json({"type": "audio_transcribe", "data": "not-valid-base64!!!"})
            r = ws.receive_json()
            assert r["type"] == "error"

    def test_audio_transcribe_with_valid_data(self, client, mock_soniox_client, mock_openai_client):
        """audio_transcribe with valid base64 data should process audio."""
        audio_b64 = base64.b64encode(b"fake_audio").decode()
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_json({"type": "audio_transcribe", "format": "wav", "data": audio_b64})

            ws.receive_json()  # transcribing
            ws.receive_json()  # transcription
            ws.receive_json()  # searching
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()  # query_result
            assert r["type"] == "query_result"


class TestWebSocketChat:
    """Tests for chat — now returns query_result."""

    def test_chat_without_keys_returns_error(self, client):
        """Chat without OPENAI_API_KEY should return processing_started then error."""
        import backend.core.config as cfg
        original = cfg.OPENAI_API_KEY
        cfg.OPENAI_API_KEY = ""
        try:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()  # welcome
                ws.send_json({"type": "chat", "content": "Hello"})
                ws.receive_json()  # searching
                ws.receive_json()  # db_skip
                r = ws.receive_json()  # llm processing_started
                assert r["type"] == "processing_started"
                r = ws.receive_json()  # error
                assert r["type"] == "error"
        finally:
            cfg.OPENAI_API_KEY = original

    def test_chat_with_mocked_llm(self, client, mock_openai_client):
        """Chat with mocked OpenAI should return query_result."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Hello"})

            ws.receive_json()  # searching
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()  # query_result
            assert r["type"] == "query_result"
            assert "message" in r

    def test_chat_preserves_content(self, client, mock_openai_client):
        """Chat should pass content through the pipeline."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()
            ws.send_json({"type": "chat", "content": "Testing chat"})

            ws.receive_json()  # searching
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()
            assert r["type"] == "query_result"

"""
Integration tests for WebSocket routes using FastAPI TestClient
with mocked external services (Soniox, OpenAI).
"""
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

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
            assert set(welcome.keys()) == {"type", "message", "version"}
            assert welcome["version"] == "1.0.0"

    def test_multiple_connections(self, client):
        """Multiple clients should all receive welcome messages."""
        with client.websocket_connect("/ws") as ws1:
            with client.websocket_connect("/ws") as ws2:
                w1 = ws1.receive_json()
                w2 = ws2.receive_json()
                assert w1["type"] == "connection_established"
                assert w2["type"] == "connection_established"


class TestWebSocketTextEcho:
    """Integration tests for plain text echo functionality."""

    def test_plain_text_echo(self, client):
        """Sending plain text should echo it back as a response."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_text("Hello WebSocket!")
            response = ws.receive_json()

            assert response["type"] == "response"
            assert response["input_type"] == "text"
            assert "Hello WebSocket!" in response["content"]

    def test_multiple_text_messages(self, client):
        """Multiple text messages should all be echoed correctly."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome

            for msg in ["first", "second", "third"]:
                ws.send_text(msg)
                response = ws.receive_json()
                assert msg in response["content"]


class TestWebSocketJsonEcho:
    """Integration tests for JSON echo functionality."""

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
            assert response["data"]["nested"]["a"] == 1


class TestWebSocketBinaryAudio:
    """Integration tests for binary audio input."""

    def test_binary_chunk_received(self, client):
        """Sending binary data should return audio_chunk_received."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_bytes(b"test_audio_data")
            response = ws.receive_json()

            assert response["type"] == "audio_chunk_received"
            assert response["bytes_received"] == len(b"test_audio_data")
            assert response["total_buffer"] == len(b"test_audio_data")

    def test_multiple_binary_chunks(self, client):
        """Multiple binary chunks should accumulate in the buffer."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome

            ws.send_bytes(b"chunk1")
            r1 = ws.receive_json()
            assert r1["total_buffer"] == len(b"chunk1")

            ws.send_bytes(b"chunk2")
            r2 = ws.receive_json()
            assert r2["total_buffer"] == len(b"chunk1chunk2")

            ws.send_bytes(b"chunk3")
            r3 = ws.receive_json()
            assert r3["total_buffer"] == len(b"chunk1chunk2chunk3")

    def test_process_audio_without_buffer_returns_error(self, client):
        """process_audio with no binary data should return error."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "process_audio", "format": "wav"})
            response = ws.receive_json()

            assert response["type"] == "error"
            assert "No audio data" in response["message"]

    def test_process_audio_pipeline_with_keys(self, client, mock_soniox_client, mock_openai_client):
        """Full audio pipeline with mocked Soniox + OpenAI should work."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome

            # Send binary audio
            ws.send_bytes(b"fake_wav_audio_data")
            r = ws.receive_json()
            assert r["type"] == "audio_chunk_received"

            # Process audio
            ws.send_json({"type": "process_audio", "format": "wav"})

            # Should get processing_started
            process = ws.receive_json()
            assert process["type"] == "processing_started"
            assert process["stage"] == "transcribing"

            # Should get transcription_complete
            trans = ws.receive_json()
            assert trans["type"] == "transcription_complete"
            assert "transcript" in trans

            # Should get processing_started for LLM
            llm = ws.receive_json()
            assert llm["type"] == "processing_started"
            assert llm["stage"] == "llm"

            # Should get final result
            result = ws.receive_json()
            assert result["type"] == "audio_processed"
            assert "transcript" in result
            assert "llm_response" in result
            assert result["llm_response"]["parsed"] == {
                "result": "success",
                "data": "processed",
            }


class TestWebSocketAudioTranscribe:
    """Integration tests for audio_transcribe JSON message type."""

    def test_audio_transcribe_empty_data_error(self, client):
        """audio_transcribe with empty data should return error."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "audio_transcribe", "format": "wav", "data": ""})
            response = ws.receive_json()

            assert response["type"] == "error"
            assert "No audio data" in response["message"]

    def test_audio_transcribe_invalid_base64(self, client):
        """audio_transcribe with invalid base64 should return error."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "audio_transcribe", "data": "not-valid-base64!!!"})
            response = ws.receive_json()

            assert response["type"] == "error"
            assert "Failed to decode" in response["message"]

    def test_audio_transcribe_with_valid_data(self, client, mock_soniox_client, mock_openai_client):
        """audio_transcribe with valid base64 data should process audio."""
        audio_b64 = base64.b64encode(b"fake_audio").decode()

        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "audio_transcribe", "format": "wav", "data": audio_b64})

            # Should start processing
            r = ws.receive_json()
            assert r["type"] == "processing_started"
            assert r["stage"] == "transcribing"

            # Should get transcription
            r = ws.receive_json()
            assert r["type"] == "transcription_complete"

            # Should get LLM processing
            r = ws.receive_json()
            assert r["type"] == "processing_started"
            assert r["stage"] == "llm"

            # Should get final result
            r = ws.receive_json()
            assert r["type"] == "audio_processed"


class TestWebSocketChat:
    """Integration tests for chat via LLM."""

    def test_chat_without_keys_returns_error(self, client):
        """Chat without OPENAI_API_KEY should return error."""
        import backend.core.config as cfg
        original_key = cfg.OPENAI_API_KEY
        cfg.OPENAI_API_KEY = ""

        try:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()  # welcome
                ws.send_json({"type": "chat", "content": "Hello"})
                response = ws.receive_json()
                assert response["type"] == "error"
        finally:
            cfg.OPENAI_API_KEY = original_key

    def test_chat_with_mocked_llm(self, client, mock_openai_client):
        """Chat with mocked OpenAI should return proper response."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Hello"})
            response = ws.receive_json()

            assert response["type"] == "response"
            assert "content" in response
            assert "parsed" in response
            assert "model" in response
            assert response["parsed"] == {
                "result": "success",
                "data": "processed",
            }

    def test_chat_preserves_original(self, client, mock_openai_client):
        """Chat response should include the original request."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Testing chat"})
            response = ws.receive_json()

            assert response["type"] == "response"
            assert response["original"]["content"] == "Testing chat"
            assert response["original"]["type"] == "chat"

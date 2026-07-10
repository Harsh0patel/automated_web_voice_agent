"""
End-to-end tests for the full audio → Soniox → DB Lookup → LLM → TTS pipeline.
All external services are mocked.
"""
import base64
from unittest.mock import AsyncMock, patch

import pytest


class TestFullAudioPipeline:
    """Complete end-to-end test for the audio processing pipeline."""

    def test_full_audio_transcribe_pipeline(self, client, mock_soniox_client, mock_openai_client):
        """E2E: Connect → send audio → receive query_result with TTS."""
        audio_b64 = base64.b64encode(b"fake_wav_audio_data").decode()

        with client.websocket_connect("/ws") as ws:
            welcome = ws.receive_json()
            assert welcome["type"] == "connection_established"

            ws.send_json({"type": "audio_transcribe", "format": "wav", "data": audio_b64})

            # processing_started (transcribing)
            r = ws.receive_json()
            assert r["type"] == "processing_started"
            assert r["stage"] == "transcribing"

            # transcription_complete
            r = ws.receive_json()
            assert r["type"] == "transcription_complete"

            # processing_started (searching)
            r = ws.receive_json()
            assert r["type"] == "processing_started"

            # db_lookup_skipped (no real DB running)
            r = ws.receive_json()
            assert r["type"] in ("db_lookup_skipped", "db_results_found")

            # processing_started (llm)
            r = ws.receive_json()
            assert r["type"] == "processing_started" and r["stage"] == "llm"

            # processing_started (tts)
            r = ws.receive_json()
            assert r["type"] == "processing_started" and r["stage"] == "tts"

            # query_result
            r = ws.receive_json()
            assert r["type"] == "query_result"
            assert "message" in r

    def test_full_binary_audio_pipeline(self, client, mock_soniox_client, mock_openai_client):
        """E2E: Connect → send binary audio → process_audio → receive result."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_bytes(b"RIFF chunk1 ")
            ws.receive_json()  # chunk_received
            ws.send_json({"type": "process_audio", "format": "wav"})

            ws.receive_json()   # processing_started (transcribing)
            ws.receive_json()   # transcription_complete
            ws.receive_json()   # processing_started (searching)
            ws.receive_json()   # db_lookup_skipped
            ws.receive_json()   # processing_started (llm)
            ws.receive_json()   # processing_started (tts)
            r = ws.receive_json()
            assert r["type"] == "query_result"

    def test_pipeline_error_handling(self, client, mock_soniox_client, mock_openai_client):
        """E2E: Pipeline errors should be reported via WebSocket."""
        instance = mock_soniox_client.return_value
        instance.stt.transcribe_and_wait_with_tokens = AsyncMock(
            side_effect=RuntimeError("Transcription failed")
        )
        audio_b64 = base64.b64encode(b"bad_audio").decode()

        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "audio_transcribe", "format": "wav", "data": audio_b64})

            r = ws.receive_json()  # processing_started
            assert r["type"] == "processing_started"
            r = ws.receive_json()  # error
            assert r["type"] == "error"

    def test_mixed_json_and_audio_flow(self, client, mock_soniox_client, mock_openai_client):
        """E2E: Mixed flow — text, then audio, then chat."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome

            # Text query
            ws.send_text("Hello")
            ws.receive_json()  # processing (searching)
            ws.receive_json()  # db_lookup_skipped
            ws.receive_json()  # processing (llm)
            ws.receive_json()  # processing (tts)
            r = ws.receive_json()
            assert r["type"] == "query_result"

            # Audio query
            ws.send_bytes(b"audio_data")
            ws.receive_json()  # chunk_received
            ws.send_json({"type": "process_audio", "format": "wav"})
            ws.receive_json()  # transcribing
            ws.receive_json()  # transcription
            ws.receive_json()  # searching
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()
            assert r["type"] == "query_result"

            # Chat
            ws.send_json({"type": "chat", "content": "Second request"})
            ws.receive_json()  # searching
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()
            assert r["type"] == "query_result"


class TestLLMIntegration:
    """End-to-end tests for the LLM integration."""

    def test_llm_response_format(self, client, mock_openai_client):
        """The LLM response should be a query_result with message."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Test"})

            ws.receive_json()  # db_search
            ws.receive_json()  # db_skip
            ws.receive_json()  # llm
            ws.receive_json()  # tts
            r = ws.receive_json()
            assert r["type"] == "query_result"
            assert isinstance(r.get("message", ""), str)

    def test_llm_error_propagation(self, client, mock_openai_client):
        """If the LLM fails, the error should be sent back."""
        instance = mock_openai_client.return_value
        instance.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("OpenAI API error")
        )

        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Test"})

            ws.receive_json()  # db_search
            ws.receive_json()  # db_skip
            r = ws.receive_json()  # llm processing_started
            assert r["type"] == "processing_started"

            r = ws.receive_json()  # error
            assert r["type"] == "error"
            assert "OpenAI" in r["message"]

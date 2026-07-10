"""
End-to-end tests for the full audio → Soniox → OpenAI → WebSocket pipeline.
All external services are mocked since this is a headless backend.
"""
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFullAudioPipeline:
    """Complete end-to-end test for the audio processing pipeline."""

    def test_full_audio_transcribe_pipeline(self, client, mock_soniox_client, mock_openai_client):
        """
        E2E: Connect → send audio_transcribe → receive final processed result.
        Tests the complete flow: audio → Soniox STT → OpenAI LLM → WebSocket response.
        """
        audio_b64 = base64.b64encode(b"fake_wav_audio_data").decode()

        with client.websocket_connect("/ws") as ws:
            # Step 1: Receive welcome
            welcome = ws.receive_json()
            assert welcome["type"] == "connection_established"

            # Step 2: Send audio for transcription
            ws.send_json({
                "type": "audio_transcribe",
                "format": "wav",
                "data": audio_b64,
            })

            # Step 3: Receive processing started (transcribing)
            msg1 = ws.receive_json()
            assert msg1["type"] == "processing_started"
            assert msg1["stage"] == "transcribing"

            # Step 4: Receive transcription complete
            msg2 = ws.receive_json()
            assert msg2["type"] == "transcription_complete"
            assert msg2["transcript"] == "Hello, this is a test transcription."

            # Step 5: Receive processing started (LLM)
            msg3 = ws.receive_json()
            assert msg3["type"] == "processing_started"
            assert msg3["stage"] == "llm"

            # Step 6: Receive final result
            msg4 = ws.receive_json()
            assert msg4["type"] == "audio_processed"
            assert msg4["transcript"] == "Hello, this is a test transcription."
            assert msg4["llm_response"]["parsed"] == {
                "result": "success",
                "data": "processed",
            }

    def test_full_binary_audio_pipeline(self, client, mock_soniox_client, mock_openai_client):
        """
        E2E: Connect → send binary audio → process_audio → receive result.
        Tests the binary chunk accumulation + processing flow.
        """
        with client.websocket_connect("/ws") as ws:
            # Step 1: Welcome
            ws.receive_json()

            # Step 2: Send binary audio in chunks
            ws.send_bytes(b"RIFF chunk1 ")
            r = ws.receive_json()
            assert r["type"] == "audio_chunk_received"
            assert r["total_buffer"] == 12

            ws.send_bytes(b"chunk2 data ")
            r = ws.receive_json()
            assert r["type"] == "audio_chunk_received"
            assert r["total_buffer"] == 24

            ws.send_bytes(b"final_chunk")
            r = ws.receive_json()
            assert r["type"] == "audio_chunk_received"
            assert r["total_buffer"] == 35

            # Step 3: Process the accumulated audio
            ws.send_json({"type": "process_audio", "format": "wav"})

            # Step 4-7: Receive pipeline messages
            msg1 = ws.receive_json()
            assert msg1["type"] == "processing_started"

            msg2 = ws.receive_json()
            assert msg2["type"] == "transcription_complete"

            msg3 = ws.receive_json()
            assert msg3["type"] == "processing_started"
            assert msg3["stage"] == "llm"

            msg4 = ws.receive_json()
            assert msg4["type"] == "audio_processed"

    def test_pipeline_error_handling(self, client, mock_soniox_client, mock_openai_client):
        """
        E2E: Test that pipeline errors are properly reported via WebSocket.
        """
        # Make Soniox fail
        instance = mock_soniox_client.return_value
        instance.stt.transcribe_and_wait_with_tokens = AsyncMock(
            side_effect=RuntimeError("Transcription failed")
        )

        audio_b64 = base64.b64encode(b"bad_audio").decode()

        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome

            ws.send_json({
                "type": "audio_transcribe",
                "format": "wav",
                "data": audio_b64,
            })

            # Should get processing_started
            r = ws.receive_json()
            assert r["type"] == "processing_started"

            # Then error
            r = ws.receive_json()
            assert r["type"] == "error"
            assert "Audio processing failed" in r["message"]

    def test_mixed_json_and_audio_flow(self, client, mock_soniox_client, mock_openai_client):
        """
        E2E: Mixed flow - echo, then audio, then chat, verifying context isolation.
        """
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome

            # 1. Text echo
            ws.send_text("Hello")
            r = ws.receive_json()
            assert r["type"] == "response"
            assert r["input_type"] == "text"

            # 2. Audio processing
            ws.send_bytes(b"audio_data")
            ws.receive_json()  # chunk_received

            ws.send_json({"type": "process_audio", "format": "wav"})
            ws.receive_json()  # processing_started
            ws.receive_json()  # transcription
            ws.receive_json()  # llm processing
            r = ws.receive_json()  # final result
            assert r["type"] == "audio_processed"

            # 3. Chat - should work without interference from audio buffer
            ws.send_json({"type": "chat", "content": "Second request"})
            r = ws.receive_json()
            assert r["type"] == "response"
            assert r["input_type"] == "chat"
            assert r["original"]["content"] == "Second request"


class TestLLMIntegration:
    """End-to-end tests for the LLM integration."""

    def test_llm_response_format(self, client, mock_openai_client):
        """The LLM response should always include content, parsed, and model."""
        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Test"})
            r = ws.receive_json()

            assert r["type"] == "response"
            assert isinstance(r["content"], str)
            assert isinstance(r["parsed"], dict)
            assert isinstance(r["model"], str)
            assert r["model"] == "gpt-4o-mini"

    def test_llm_error_propagation(self, client, mock_openai_client):
        """If the LLM fails, the error should be sent back."""
        instance = mock_openai_client.return_value
        instance.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("OpenAI API error")
        )

        with client.websocket_connect("/ws") as ws:
            ws.receive_json()  # welcome
            ws.send_json({"type": "chat", "content": "Test"})
            r = ws.receive_json()

            assert r["type"] == "error"
            assert "OpenAI" in r["message"]

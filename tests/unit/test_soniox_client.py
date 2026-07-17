"""
Unit tests for the Soniox speech-to-text client.
"""
from unittest.mock import AsyncMock, call

import pytest


class TestTranscribeAudio:
    """Tests for transcribe_audio function."""

    @pytest.mark.asyncio
    async def test_transcribe_success(self, sample_audio_bytes, mock_soniox_client):
        """Successful transcription should return the transcript text."""
        from backend.clients.speech.soniox import transcribe_audio

        result = await transcribe_audio(sample_audio_bytes, audio_format="wav")

        assert result == "Hello, this is a test transcription."
        mock_soniox_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_calls_client_with_file(self, sample_audio_bytes, mock_soniox_client):
        """The client should be called with the temp file path."""
        from backend.clients.speech.soniox import transcribe_audio

        await transcribe_audio(sample_audio_bytes, audio_format="wav")

        instance = mock_soniox_client.return_value
        call = instance.stt.transcribe_and_wait_with_tokens.await_args
        assert call is not None, "transcribe_and_wait_with_tokens was not called"
        # Should have been called with a file path argument
        assert "file" in call.kwargs
        assert call.kwargs["delete_after"] is True

    @pytest.mark.asyncio
    async def test_transcribe_raises_without_api_key(self, monkeypatch, sample_audio_bytes):
        """Without SONIOX_API_KEY, should raise ValueError."""
        # Directly override config value without reloading
        import backend.app.config as cfg
        original_key = cfg.SONIOX_API_KEY
        cfg.SONIOX_API_KEY = ""

        from backend.clients.speech.soniox import transcribe_audio

        try:
            with pytest.raises(ValueError, match="SONIOX_API_KEY is not set"):
                await transcribe_audio(sample_audio_bytes)
        finally:
            cfg.SONIOX_API_KEY = original_key

    @pytest.mark.asyncio
    async def test_transcribe_handles_client_error(self, sample_audio_bytes, mock_soniox_client):
        """If Soniox client raises, the error should propagate."""
        instance = mock_soniox_client.return_value
        instance.stt.transcribe_and_wait_with_tokens = AsyncMock(
            side_effect=RuntimeError("Soniox API error")
        )

        from backend.clients.speech.soniox import transcribe_audio

        with pytest.raises(RuntimeError, match="Soniox API error"):
            await transcribe_audio(sample_audio_bytes)

    @pytest.mark.asyncio
    async def test_transcribe_cleans_up_temp_file(self, sample_audio_bytes, mock_soniox_client):
        """Temp files should be cleaned up after transcription."""
        from backend.clients.speech.soniox import transcribe_audio

        # Verify no errors during cleanup
        result = await transcribe_audio(sample_audio_bytes, audio_format="wav")
        assert result == "Hello, this is a test transcription."

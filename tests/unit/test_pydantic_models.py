"""
Unit tests for pydantic data models.
"""
import pytest
from pydantic import ValidationError


class TestAudioTranscriptionRequest:
    """Tests for AudioTranscriptionRequest model."""

    def test_default_format(self):
        from backend.core.pydantic_models import AudioTranscriptionRequest
        req = AudioTranscriptionRequest()
        assert req.audio_format == "wav"

    def test_custom_format(self):
        from backend.core.pydantic_models import AudioTranscriptionRequest
        req = AudioTranscriptionRequest(audio_format="mp3")
        assert req.audio_format == "mp3"


class TestTranscriptionResult:
    """Tests for TranscriptionResult model."""

    def test_default_is_final(self):
        from backend.core.pydantic_models import TranscriptionResult
        result = TranscriptionResult(text="hello")
        assert result.text == "hello"
        assert result.is_final is True

    def test_non_final(self):
        from backend.core.pydantic_models import TranscriptionResult
        result = TranscriptionResult(text="partial", is_final=False)
        assert result.is_final is False

    def test_missing_text_raises(self):
        from backend.core.pydantic_models import TranscriptionResult
        with pytest.raises(ValidationError):
            TranscriptionResult()


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_defaults(self):
        from backend.core.pydantic_models import LLMConfig
        config = LLMConfig()
        assert config.model == "gpt-4o-mini"
        assert config.system_prompt == ""
        assert config.temperature == 0.1
        assert config.response_format is None

    def test_custom_values(self):
        from backend.core.pydantic_models import LLMConfig
        config = LLMConfig(
            model="gpt-4",
            system_prompt="Be concise",
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.5


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_minimal(self):
        from backend.core.pydantic_models import LLMResponse
        resp = LLMResponse(content='{"key": "value"}')
        assert resp.content == '{"key": "value"}'
        assert resp.raw_json is None
        assert resp.model == ""

    def test_full(self):
        from backend.core.pydantic_models import LLMResponse
        resp = LLMResponse(
            content='{"key": "value"}',
            raw_json={"key": "value"},
            model="gpt-4o-mini",
        )
        assert resp.raw_json == {"key": "value"}
        assert resp.model == "gpt-4o-mini"


class TestAudioProcessingResult:
    """Tests for AudioProcessingResult model."""

    def test_creation(self):
        from backend.core.pydantic_models import (
            AudioProcessingResult,
            LLMResponse,
        )
        result = AudioProcessingResult(
            transcript="hello world",
            llm_response=LLMResponse(
                content='{"result": "ok"}',
                model="gpt-4o-mini",
            ),
        )
        assert result.transcript == "hello world"
        assert result.llm_response.content == '{"result": "ok"}'

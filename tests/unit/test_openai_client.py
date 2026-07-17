"""
Unit tests for the OpenAI LLM client.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLoadSystemPrompt:
    """Tests for load_system_prompt function."""

    @pytest.mark.asyncio
    async def test_returns_default_prompt(self):
        """Should load the prompt from the .txt file."""
        from backend.clients.llm.openai import load_system_prompt
        from pathlib import Path
        prompt_path = Path(__file__).resolve().parent.parent.parent / "backend" / "prompts" / "default_system_prompt.txt"
        expected = prompt_path.read_text(encoding="utf-8").strip() if prompt_path.exists() else ""
        result = await load_system_prompt()
        assert result == expected

    @pytest.mark.asyncio
    async def test_default_prompt_has_required_content(self):
        """The default prompt should contain key instructions."""
        from backend.clients.llm.openai import load_system_prompt
        result = await load_system_prompt()
        assert len(result) > 100
        assert "[Site Name]" in result
        assert "navigate" in result
        assert "json" in result.lower()
        assert "message" in result


class TestGenerateJsonFromTranscript:
    """Tests for generate_json_from_transcript function."""

    @pytest.mark.asyncio
    async def test_successful_generation(self, mock_openai_client):
        """Should return a dict with content, parsed, and model."""
        from backend.clients.llm.openai import generate_json_from_transcript

        result = await generate_json_from_transcript("Hello world")

        assert "content" in result
        assert "parsed" in result
        assert "model" in result
        assert result["parsed"] == {"message": "This is a test response from the LLM."}
        assert isinstance(result["model"], str)
        assert len(result["model"]) > 0

    @pytest.mark.asyncio
    async def test_uses_system_prompt(self, mock_openai_client):
        """Should pass the system prompt as the system message."""
        from backend.clients.llm.openai import generate_json_from_transcript

        await generate_json_from_transcript("Hello")

        instance = mock_openai_client.return_value
        call = instance.chat.completions.create.await_args
        assert call is not None
        messages = call.kwargs["messages"]
        # Find the system message
        system_msgs = [m for m in messages if m.get("role") == "system"]
        assert len(system_msgs) == 1
        assert "navigate" in system_msgs[0]["content"]
        assert "message" in system_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_raises_without_api_key(self, monkeypatch):
        """Without OPENAI_API_KEY, should raise ValueError."""
        import backend.app.config as cfg
        original_key = cfg.OPENAI_API_KEY
        cfg.OPENAI_API_KEY = ""

        from backend.clients.llm.openai import generate_json_from_transcript

        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
                await generate_json_from_transcript("Hello")
        finally:
            cfg.OPENAI_API_KEY = original_key

    @pytest.mark.asyncio
    async def test_parses_json_content(self, mock_openai_client):
        """Should parse the JSON content from the API response."""
        instance = mock_openai_client.return_value
        mock_choice = MagicMock()
        mock_choice.message.content = '{"intent": "greeting", "confidence": 0.95}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        instance.chat.completions.create.return_value = mock_response

        from backend.clients.llm.openai import generate_json_from_transcript

        result = await generate_json_from_transcript("Hello")
        assert result["parsed"] == {"intent": "greeting", "confidence": 0.95}

    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(self, mock_openai_client):
        """If OpenAI returns invalid JSON, should fall back to raw_text."""
        instance = mock_openai_client.return_value
        mock_choice = MagicMock()
        mock_choice.message.content = "Not valid JSON"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        instance.chat.completions.create.return_value = mock_response

        from backend.clients.llm.openai import generate_json_from_transcript

        result = await generate_json_from_transcript("Hello")
        assert result["parsed"] == {"message": "Not valid JSON"}

    @pytest.mark.asyncio
    async def test_passes_transcript_in_user_message(self, mock_openai_client):
        """The transcript should be included in the user message."""
        from backend.clients.llm.openai import generate_json_from_transcript

        await generate_json_from_transcript("This is a test transcript.")

        instance = mock_openai_client.return_value
        call = instance.chat.completions.create.await_args
        assert call is not None
        messages = call.kwargs["messages"]
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert "This is a test transcript." in user_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_response_format_json(self, mock_openai_client):
        """Should NOT pass response_format when OPENAI_JSON_MODE is false."""
        from backend.clients.llm.openai import generate_json_from_transcript

        await generate_json_from_transcript("Hello")

        instance = mock_openai_client.return_value
        call = instance.chat.completions.create.await_args
        assert call is not None
        # json_object mode is disabled by default (OPENAI_JSON_MODE=false)
        # so response_format should NOT be in kwargs
        assert "response_format" not in call.kwargs
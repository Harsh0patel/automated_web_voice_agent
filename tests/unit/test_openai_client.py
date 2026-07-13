"""
Unit tests for the OpenAI LLM client.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLoadSystemPrompt:
    """Tests for load_system_prompt function."""

    @pytest.mark.asyncio
    async def test_loads_from_file(self, tmp_path):
        """Should load the system prompt from the prompt file."""
        import backend.core.config as cfg

        prompt_file = tmp_path / "system_prompt.txt"
        prompt_file.write_text("You are a helpful assistant.")

        original = cfg.PROMPT_FILE
        cfg.PROMPT_FILE = prompt_file

        from backend.LLM_CLIENT.openai_client import load_system_prompt
        try:
            result = await load_system_prompt()
            assert result == "You are a helpful assistant."
        finally:
            cfg.PROMPT_FILE = original

    @pytest.mark.asyncio
    async def test_returns_empty_if_file_missing(self, tmp_path):
        """Should return empty string if prompt file doesn't exist."""
        import backend.core.config as cfg

        prompt_file = tmp_path / "nonexistent.txt"
        original = cfg.PROMPT_FILE
        cfg.PROMPT_FILE = prompt_file

        from backend.LLM_CLIENT.openai_client import load_system_prompt
        try:
            result = await load_system_prompt()
            assert result == ""
        finally:
            cfg.PROMPT_FILE = original

    @pytest.mark.asyncio
    async def test_returns_empty_if_file_empty(self, tmp_path):
        """Should return empty string if prompt file is empty."""
        import backend.core.config as cfg

        prompt_file = tmp_path / "system_prompt.txt"
        prompt_file.write_text("")

        original = cfg.PROMPT_FILE
        cfg.PROMPT_FILE = prompt_file

        from backend.LLM_CLIENT.openai_client import load_system_prompt
        try:
            result = await load_system_prompt()
            assert result == ""
        finally:
            cfg.PROMPT_FILE = original


class TestGenerateJsonFromTranscript:
    """Tests for generate_json_from_transcript function."""

    @pytest.mark.asyncio
    async def test_successful_generation(self, mock_openai_client):
        """Should return a dict with content, parsed, and model."""
        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

        result = await generate_json_from_transcript("Hello world")

        assert "content" in result
        assert "parsed" in result
        assert "model" in result
        assert result["parsed"] == {"result": "success", "data": "processed"}
        assert isinstance(result["model"], str)
        assert len(result["model"]) > 0

    @pytest.mark.asyncio
    async def test_uses_system_prompt(self, mock_openai_client, tmp_path):
        """Should pass the system prompt as the system message."""
        import backend.core.config as cfg

        prompt_file = tmp_path / "system_prompt.txt"
        prompt_file.write_text("Custom prompt.")

        original = cfg.PROMPT_FILE
        cfg.PROMPT_FILE = prompt_file

        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript
        try:
            await generate_json_from_transcript("Hello")
        finally:
            cfg.PROMPT_FILE = original

        instance = mock_openai_client.return_value
        call = instance.chat.completions.create.await_args
        assert call is not None
        messages = call.kwargs["messages"]
        # Find the system message
        system_msgs = [m for m in messages if m.get("role") == "system"]
        assert len(system_msgs) == 1
        assert "Custom prompt." in system_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_raises_without_api_key(self, monkeypatch):
        """Without OPENAI_API_KEY, should raise ValueError."""
        import backend.core.config as cfg
        original_key = cfg.OPENAI_API_KEY
        cfg.OPENAI_API_KEY = ""

        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

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

        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

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

        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

        result = await generate_json_from_transcript("Hello")
        assert result["parsed"] == {"message": "Not valid JSON"}

    @pytest.mark.asyncio
    async def test_passes_transcript_in_user_message(self, mock_openai_client):
        """The transcript should be included in the user message."""
        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

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
        """Should request json_object response format."""
        from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

        await generate_json_from_transcript("Hello")

        instance = mock_openai_client.return_value
        call = instance.chat.completions.create.await_args
        assert call is not None
        assert call.kwargs["response_format"] == {"type": "json_object"}

"""
Shared pytest fixtures and configuration for the test suite.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from backend.main import app as fastapi_app


# ============================================================
# Fixtures: mock external service keys
# ============================================================

@pytest.fixture(autouse=True)
def _mock_env_vars(monkeypatch):
    """Prevent any real API key usage during tests."""
    monkeypatch.setenv("SONIOX_API_KEY", "test-soniox-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-elevenlabs-key")
    # Force reload of config module values
    import backend.core.config as cfg
    cfg.SONIOX_API_KEY = "test-soniox-key"
    cfg.OPENAI_API_KEY = "test-openai-key"
    cfg.GROQ_API_KEY = "test-groq-key"
    cfg.ELEVENLABS_API_KEY = "test-elevenlabs-key"


# ============================================================
# Fixtures: FastAPI TestClient
# ============================================================

@pytest.fixture
def app():
    """Return the FastAPI application instance."""
    return fastapi_app


@pytest.fixture
def client(app):
    """Return a FastAPI TestClient."""
    from fastapi.testclient import TestClient
    return TestClient(app)


# ============================================================
# Fixtures: mock external service clients
# ============================================================

@pytest.fixture
def mock_soniox_client():
    """Mock the AsyncSonioxClient (legacy — kept for Soniox-based tests)."""
    with patch("backend.LLM_CLIENT.soniox_client.AsyncSonioxClient") as mock:
        instance = mock.return_value
        instance.stt.transcribe_and_wait_with_tokens = AsyncMock()
        mock_transcript = MagicMock()
        mock_transcript.text = "Hello, this is a test transcription."
        instance.stt.transcribe_and_wait_with_tokens.return_value = mock_transcript
        instance.tts.generate_to_file = AsyncMock(return_value=None)
        yield mock


@pytest.fixture
def mock_groq_client():
    """Mock the Groq client (used for STT via Whisper)."""
    with patch("backend.LLM_CLIENT.groq_client.Groq") as mock:
        instance = mock.return_value
        # Mock audio.transcriptions.create to return a fake transcription
        mock_transcription = MagicMock()
        mock_transcription.text = "This is a test transcription from Groq."
        instance.audio.transcriptions.create = MagicMock(return_value=mock_transcription)
        yield mock


@pytest.fixture
def mock_elevenlabs_client():
    """Mock the ElevenLabs client (used for TTS)."""
    with patch("backend.LLM_CLIENT.elevenlabs_client.ElevenLabs") as mock:
        instance = mock.return_value
        # Mock text_to_speech.convert to return fake audio bytes
        instance.text_to_speech.convert = MagicMock(return_value=[b"fake_audio_data"])
        yield mock


# ============================================================
# Fixtures: mock OpenAI client
# ============================================================

@pytest.fixture
def mock_openai_client():
    """Mock the AsyncOpenAI client and its chat completions."""
    with patch("backend.LLM_CLIENT.openai_client.AsyncOpenAI") as mock:
        instance = mock.return_value

        # Create a mock response
        mock_choice = MagicMock()
        mock_choice.message.content = '{"message": "This is a test response from the LLM."}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        # Set up the chat completions chain
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        yield mock


# ============================================================
# Fixtures: mock WebSocket
# ============================================================

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing ConnectionManager."""
    ws = AsyncMock(spec=WebSocket)
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.receive_bytes = AsyncMock()
    ws.receive = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    return ws


# ============================================================
# Fixtures: sample data
# ============================================================

@pytest.fixture
def sample_audio_bytes():
    """Return sample audio bytes for testing."""
    return b"RIFF\x00\x00\x00\x00WAVEfmt test audio bytes"


# ============================================================
# Fixtures: disable MongoDB for tests that don't need it
# ============================================================

@pytest.fixture
def disable_mongo():
    """Make _get_client return None so DB functions degrade gracefully."""
    from unittest.mock import patch
    with patch("backend.core.database._get_client", return_value=None):
        yield


# ============================================================
# Fixtures: sample data
# ============================================================

@pytest.fixture
def sample_llm_result():
    """Return a sample LLM result dict."""
    return {
        "content": '{"result": "success", "data": "processed"}',
        "parsed": {"result": "success", "data": "processed"},
        "model": "gpt-4o-mini",
    }

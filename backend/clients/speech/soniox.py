"""
Soniox STT client fallback.

Transcribes audio using Soniox's AsyncSonioxClient REST API.
Used as a fallback when Groq transcription is unavailable.
"""
import tempfile
from pathlib import Path

from soniox import AsyncSonioxClient

from backend.app import config as cfg
from backend.app.logger import get_logger

logger = get_logger(__name__)


async def transcribe_audio(audio_data: bytes, audio_format: str = "wav") -> str:
    """Transcribe audio bytes to text using Soniox.

    Args:
        audio_data: Raw audio bytes to transcribe.
        audio_format: File extension/format (e.g. 'wav', 'mp3').

    Returns:
        The transcribed text string.
    """
    if not cfg.SONIOX_API_KEY:
        raise ValueError("SONIOX_API_KEY is not set. Set the SONIOX_API_KEY environment variable.")

    suffix = f".{audio_format.lstrip('.')}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        client = AsyncSonioxClient(api_key=cfg.SONIOX_API_KEY)
        transcript = await client.stt.transcribe_and_wait_with_tokens(
            file=tmp_path,
            delete_after=True,
        )
        return transcript.text
    finally:
        path = Path(tmp_path)
        if path.exists():
            path.unlink()

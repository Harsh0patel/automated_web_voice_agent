"""
Groq Whisper STT — transcribe audio using Groq's free Whisper API.
"""
import asyncio
import io

from groq import Groq

from backend.core import config as cfg
from backend.core.logger import get_logger

logger = get_logger(__name__)


def _transcribe_sync(audio_data: bytes, audio_format: str) -> str:
    """Synchronous Groq transcription (called via asyncio.to_thread)."""
    if not cfg.GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set")
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Set the GROQ_API_KEY environment variable."
        )

    client = Groq(api_key=cfg.GROQ_API_KEY)
    suffix = audio_format.lstrip(".")

    audio_file = io.BytesIO(audio_data)
    audio_file.name = f"audio.{suffix}"

    mime_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "m4a": "audio/mp4",
    }.get(suffix, f"audio/{suffix}")

    logger.debug("Calling Groq Whisper (%s, model=%s)...", audio_file.name, cfg.GROQ_WHISPER_MODEL)
    transcription = client.audio.transcriptions.create(
        file=(audio_file.name, audio_file, mime_type),
        model=cfg.GROQ_WHISPER_MODEL,
        response_format="json",
        language="en",
        temperature=0.0,
    )

    result = transcription.text.strip()
    logger.info("Groq STT transcribed %d bytes → %d chars", len(audio_data), len(result))
    return result


async def transcribe_audio(audio_data: bytes, audio_format: str = "wav") -> str:
    """
    Transcribe audio bytes to text using Groq Whisper API.

    Args:
        audio_data: Raw audio bytes to transcribe.
        audio_format: File extension/format of the audio (e.g. 'wav', 'webm').

    Returns:
        The transcribed text string.
    """
    # Run the synchronous Groq client in a thread pool
    return await asyncio.to_thread(_transcribe_sync, audio_data, audio_format)

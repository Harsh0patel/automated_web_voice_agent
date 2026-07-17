"""
Groq Whisper STT client.

Transcribes audio using Groq's free Whisper API. Runs the synchronous
Groq client in a thread pool to avoid blocking the async event loop.
"""
import asyncio
import io

from groq import Groq

from backend.app import config as cfg
from backend.app.logger import get_logger

logger = get_logger(__name__)


def _transcribe_sync(audio_data: bytes, audio_format: str) -> str:
    """Synchronous Groq transcription."""
    if not cfg.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Set the GROQ_API_KEY environment variable.")

    client = Groq(api_key=cfg.GROQ_API_KEY)
    suffix = audio_format.lstrip(".")
    audio_file = io.BytesIO(audio_data)
    audio_file.name = f"audio.{suffix}"

    mime_type = {
        "wav": "audio/wav", "mp3": "audio/mpeg", "webm": "audio/webm",
        "ogg": "audio/ogg", "flac": "audio/flac", "m4a": "audio/mp4",
    }.get(suffix, f"audio/{suffix}")

    transcription = client.audio.transcriptions.create(
        file=(audio_file.name, audio_file, mime_type),
        model=cfg.GROQ_WHISPER_MODEL,
        response_format="json",
        language="en",
        temperature=0.0,
    )
    return transcription.text.strip()


async def transcribe_audio(audio_data: bytes, audio_format: str = "wav") -> str:
    """Transcribe audio bytes to text using Groq Whisper API."""
    return await asyncio.to_thread(_transcribe_sync, audio_data, audio_format)

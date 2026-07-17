"""
ElevenLabs TTS client.

Synthesizes speech from text using the ElevenLabs API.
Runs the synchronous client in a thread pool to avoid blocking.
"""
import asyncio

from elevenlabs.client import ElevenLabs

from backend.app import config as cfg
from backend.app.logger import get_logger

logger = get_logger(__name__)

_FORMAT_MAP = {
    "wav": "pcm_16000",
    "mp3": "mp3_44100_128",
    "pcm": "pcm_16000",
    "ulaw": "ulaw_8000",
}


def _synthesize_sync(text: str, voice_id: str, model_id: str, audio_format: str) -> bytes:
    """Synchronous ElevenLabs TTS."""
    if not cfg.ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set. Set the ELEVENLABS_API_KEY environment variable.")

    client = ElevenLabs(api_key=cfg.ELEVENLABS_API_KEY)
    output_format = _FORMAT_MAP.get(audio_format.lstrip("."), "mp3_44100_128")

    audio_generator = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
    )
    audio_bytes = b"".join(audio_generator)
    return audio_bytes


async def synthesize_speech(
    text: str,
    voice: str | None = None,
    language: str | None = None,
    audio_format: str = "mp3",
) -> bytes:
    """Synthesize text to speech using ElevenLabs.

    Args:
        text: The text to convert to speech.
        voice: Voice ID (defaults to ELEVENLABS_VOICE_ID from config).
        language: Not used by ElevenLabs (kept for compatibility).
        audio_format: Output audio format (e.g. 'mp3', 'wav').

    Returns:
        The audio bytes.
    """
    voice_id = voice or cfg.ELEVENLABS_VOICE_ID
    model_id = cfg.ELEVENLABS_MODEL
    return await asyncio.to_thread(_synthesize_sync, text, voice_id, model_id, audio_format)

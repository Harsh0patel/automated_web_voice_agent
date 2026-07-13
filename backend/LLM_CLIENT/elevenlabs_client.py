"""
ElevenLabs TTS — synthesize speech using ElevenLabs API.
"""
import asyncio

from elevenlabs.client import ElevenLabs

from backend.core import config as cfg
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Map our generic format to ElevenLabs output_format values
_FORMAT_MAP = {
    "wav": "pcm_16000",
    "mp3": "mp3_44100_128",
    "pcm": "pcm_16000",
    "ulaw": "ulaw_8000",
}


def _synthesize_sync(text: str, voice_id: str, model_id: str, audio_format: str) -> bytes:
    """Synchronous ElevenLabs TTS (called via asyncio.to_thread)."""
    if not cfg.ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set")
        raise ValueError(
            "ELEVENLABS_API_KEY is not set. "
            "Set the ELEVENLABS_API_KEY environment variable."
        )

    client = ElevenLabs(api_key=cfg.ELEVENLABS_API_KEY)
    output_format = _FORMAT_MAP.get(audio_format.lstrip("."), "mp3_44100_128")

    logger.debug(
        "Calling ElevenLabs TTS (%d chars, voice=%s, model=%s, format=%s)",
        len(text), voice_id, model_id, output_format,
    )
    audio_generator = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
    )

    audio_bytes = b"".join(audio_generator)
    logger.info("ElevenLabs TTS generated %d bytes from %d chars", len(audio_bytes), len(text))
    return audio_bytes


async def synthesize_speech(
    text: str,
    voice: str | None = None,
    language: str | None = None,
    audio_format: str = "mp3",
) -> bytes:
    """
    Synthesize text to speech using ElevenLabs.

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

    return await asyncio.to_thread(
        _synthesize_sync, text, voice_id, model_id, audio_format,
    )

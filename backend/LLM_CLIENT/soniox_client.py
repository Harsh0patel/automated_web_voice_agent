import tempfile
from pathlib import Path

from soniox import AsyncSonioxClient

from backend.core import config as cfg
from backend.core.logger import get_logger

logger = get_logger(__name__)


async def transcribe_audio(audio_data: bytes, audio_format: str = "wav") -> str:
    """
    Transcribe audio bytes to text using Soniox AsyncSonioxClient REST API.

    Args:
        audio_data: Raw audio bytes to transcribe.
        audio_format: File extension/format of the audio (e.g. 'wav', 'mp3').

    Returns:
        The transcribed text string.
    """
    if not cfg.SONIOX_API_KEY:
        logger.error("SONIOX_API_KEY not set")
        raise ValueError(
            "SONIOX_API_KEY is not set. "
            "Set the SONIOX_API_KEY environment variable."
        )

    suffix = f".{audio_format.lstrip('.')}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    logger.debug("Saved %d bytes to temp file %s", len(audio_data), tmp_path)

    try:
        client = AsyncSonioxClient(api_key=cfg.SONIOX_API_KEY)
        logger.debug("Calling Soniox STT...")
        transcript = await client.stt.transcribe_and_wait_with_tokens(
            file=tmp_path,
            delete_after=True,
        )
        logger.info("Soniox STT transcribed %d bytes → %d chars", len(audio_data), len(transcript.text))
        return transcript.text
    finally:
        path = Path(tmp_path)
        if path.exists():
            path.unlink()
            logger.debug("Temp file %s cleaned up", tmp_path)


async def synthesize_speech(
    text: str,
    voice: str = "Adrian",
    language: str = "en",
    audio_format: str = "wav",
) -> bytes:
    """
    Synthesize text to speech using Soniox TTS.

    Args:
        text: The text to convert to speech.
        voice: Voice name (e.g. 'Adrian').
        language: Language code (e.g. 'en').
        audio_format: Output audio format (e.g. 'wav').

    Returns:
        The audio bytes.
    """
    if not cfg.SONIOX_API_KEY:
        logger.error("SONIOX_API_KEY not set")
        raise ValueError(
            "SONIOX_API_KEY is not set. "
            "Set the SONIOX_API_KEY environment variable."
        )

    client = AsyncSonioxClient(api_key=cfg.SONIOX_API_KEY)
    suffix = f".{audio_format.lstrip('.')}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        logger.debug("Calling Soniox TTS (%d chars, voice=%s, lang=%s)", len(text), voice, language)
        await client.tts.generate_to_file(
            tmp_path,
            text=text,
            model="tts-rt-v1",
            language=language,
            voice=voice,
            audio_format=audio_format,
        )
        audio_bytes = Path(tmp_path).read_bytes()
        logger.info("Soniox TTS generated %d bytes from %d chars", len(audio_bytes), len(text))
        return audio_bytes
    finally:
        path = Path(tmp_path)
        if path.exists():
            path.unlink()
            logger.debug("Temp file %s cleaned up", tmp_path)

import tempfile
from pathlib import Path

from soniox import AsyncSonioxClient

from backend.core import config as cfg


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
        raise ValueError(
            "SONIOX_API_KEY is not set. "
            "Set the SONIOX_API_KEY environment variable."
        )

    # Save bytes to a temporary file so Soniox can read it
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
        # Clean up temp file if it still exists
        path = Path(tmp_path)
        if path.exists():
            path.unlink()

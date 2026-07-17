"""
Pydantic models for request/response validation across the API.
"""
from typing import Optional

from pydantic import BaseModel


class AudioTranscriptionRequest(BaseModel):
    """Represents an audio transcription request from WebSocket."""
    audio_format: str = "wav"


class TranscriptionResult(BaseModel):
    """Result from speech-to-text transcription."""
    text: str
    is_final: bool = True


class LLMConfig(BaseModel):
    """Configuration for the LLM call."""
    model: str = "gpt-4o-mini"
    system_prompt: str = ""
    temperature: float = 0.1
    response_format: Optional[dict] = None


class LLMResponse(BaseModel):
    """Response from the OpenAI LLM."""
    content: str
    raw_json: Optional[dict] = None
    model: str = ""


class AudioProcessingResult(BaseModel):
    """Complete result of audio -> transcript -> LLM pipeline."""
    transcript: str
    llm_response: LLMResponse

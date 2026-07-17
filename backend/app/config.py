"""
Centralized application configuration.

All settings are loaded from environment variables (with .env support)
and exposed as module-level constants for easy import.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path), override=True)

# Soniox config (STT - fallback)
SONIOX_API_KEY: str = os.getenv("SONIOX_API_KEY", "")

# Groq config (STT - primary)
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_WHISPER_MODEL: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

# ElevenLabs config (TTS)
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
ELEVENLABS_MODEL: str = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")

# OpenAI / LLM config
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_JSON_MODE: bool = os.getenv("OPENAI_JSON_MODE", "true").lower() == "true"

# MongoDB config
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Memory layer config
MEMORY_ENABLED: bool = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
MEMORY_MAX_EXCHANGES: int = int(os.getenv("MEMORY_MAX_EXCHANGES", "20"))
MEMORY_MAX_TOKENS: int = int(os.getenv("MEMORY_MAX_TOKENS", "3000"))
MEMORY_MAX_RAW_IN_CONTEXT: int = int(os.getenv("MEMORY_MAX_RAW_IN_CONTEXT", "6"))

# Project root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

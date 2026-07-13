import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root (supports local development)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    # override=True ensures .env values take precedence over shell env (which may have empty vars)
    load_dotenv(dotenv_path=str(env_path), override=True)

# NOTE: Add these to your .env file:
#   GROQ_API_KEY=<your-groq-api-key>
#   ELEVENLABS_API_KEY=<your-elevenlabs-api-key>

# Soniox config (STT - keep as fallback)
SONIOX_API_KEY: str = os.getenv("SONIOX_API_KEY", "")

# Groq config (STT - primary)
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_WHISPER_MODEL: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

# ElevenLabs config (TTS)
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
ELEVENLABS_MODEL: str = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")

# OpenAI / LLM config (works with any OpenAI-compatible API)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# Some providers (Groq, OpenRouter, Gemini) don't support OpenAI's json_object mode.
# Set to "false" to rely on the system prompt to enforce JSON output instead.
OPENAI_JSON_MODE: bool = os.getenv("OPENAI_JSON_MODE", "true").lower() == "true"

# MongoDB config
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Paths
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE: Path = PROJECT_ROOT / "backend" / "core" / "prompts" / "system_prompt.txt"

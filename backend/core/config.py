import os
from pathlib import Path

# Soniox config
SONIOX_API_KEY: str = os.getenv("SONIOX_API_KEY", "")

# OpenAI config
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Paths
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE: Path = PROJECT_ROOT / "backend" / "core" / "prompts" / "system_prompt.txt"

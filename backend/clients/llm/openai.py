"""
OpenAI-compatible LLM client.

Works with any OpenAI-compatible API (OpenAI, Groq, OpenRouter, etc.)
for generating structured JSON responses from transcripts.
"""
import json
import re
from pathlib import Path

from openai import AsyncOpenAI

from backend.app import config as cfg
from backend.app.logger import get_logger

logger = get_logger(__name__)


async def load_system_prompt() -> str:
    """Load the default system prompt from prompts/default_system_prompt.txt."""
    prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "default_system_prompt.txt"
    if prompt_path.exists():
        text = prompt_path.read_text(encoding="utf-8").strip()
        logger.debug("Loaded system prompt from %s (%d chars)", prompt_path, len(text))
        return text
    logger.warning("Prompt file not found at %s", prompt_path)
    return "You are a helpful assistant. Respond in JSON format."


def _try_extract_json(text: str) -> dict | None:
    """Try multiple strategies to extract valid JSON from LLM output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    cleaned = re.sub(r"<[^>]+>", "", text).strip()
    if cleaned != text:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r'\{[^{}]*"message"[^{}]*\}', cleaned, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    depth = 0
    start = -1
    last_valid = None
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    candidate = json.loads(cleaned[start:i+1])
                    if isinstance(candidate, dict) and "message" in candidate:
                        last_valid = candidate
                except json.JSONDecodeError:
                    pass
                start = -1
    if last_valid:
        return last_valid

    return None


async def generate_json_from_transcript(
    transcript: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> dict:
    """Send a transcript to the LLM and return a structured JSON response.

    Args:
        transcript: The transcribed text from the user.
        system_prompt: Optional system prompt override.
        model: OpenAI model to use. Defaults to config.

    Returns:
        Dict with keys: content, parsed, model.
    """
    if not cfg.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Set the OPENAI_API_KEY environment variable.")

    if system_prompt is None:
        system_prompt = await load_system_prompt()

    client = AsyncOpenAI(api_key=cfg.OPENAI_API_KEY, base_url=cfg.OPENAI_BASE_URL)
    model_name = model or cfg.OPENAI_MODEL

    messages = [
        {"role": "system", "content": system_prompt or "You are a helpful assistant. Respond in JSON format."},
        {"role": "user", "content": transcript},
    ]

    kwargs = dict(model=model_name, messages=messages, temperature=0.1)
    if cfg.OPENAI_JSON_MODE:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    content_raw = response.choices[0].message.content or "{}"

    parsed_content = _try_extract_json(content_raw)
    if parsed_content is not None:
        pass
    else:
        cleaned_text = re.sub(r"<[^>]+>", "", content_raw).strip()
        parsed_content = {"message": cleaned_text or content_raw}

    return {"content": content_raw, "parsed": parsed_content, "model": model_name}

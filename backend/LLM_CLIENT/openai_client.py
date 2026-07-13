import json
import re
from pathlib import Path

from openai import AsyncOpenAI

from backend.core import config as cfg
from backend.core.logger import get_logger

logger = get_logger(__name__)


async def load_system_prompt() -> str:
    """
    Load the system prompt from the text file.
    Returns an empty string if the file is empty or doesn't exist.
    """
    prompt_path = Path(cfg.PROMPT_FILE)
    if prompt_path.exists():
        text = prompt_path.read_text(encoding="utf-8").strip()
        logger.debug("Loaded system prompt (%d chars) from %s", len(text), prompt_path)
        return text
    logger.debug("Prompt file %s not found, using empty prompt", prompt_path)
    return ""


def _try_extract_json(text: str) -> dict | None:
    """Try multiple strategies to extract valid JSON from LLM output."""
    # Strategy 1: Try parsing the full text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip XML/HTML-style tags (like <thought>...</thought>) and try again
    cleaned = re.sub(r"<[^>]+>", "", text).strip()
    if cleaned != text:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find the first { } JSON object in the text
    brace_match = re.search(r"\{[^{}]*" + '"message"' + r"[^{}]*\}", cleaned, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 4: Find ALL complete { } blocks and use the LAST one with a "message" key.
    # This handles LLM output where earlier blocks are reasoning previews
    # and the final JSON at the end is the actual response.
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
    """
    Take a transcript and send it to OpenAI to generate a structured JSON response.

    Args:
        transcript: The transcribed text from Soniox.
        system_prompt: Optional system prompt override. If None, loaded from file.
        model: OpenAI model to use. Defaults to config value.

    Returns:
        The parsed JSON response from the LLM.
    """
    if not cfg.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Set the OPENAI_API_KEY environment variable."
        )

    if system_prompt is None:
        system_prompt = await load_system_prompt()

    client = AsyncOpenAI(
        api_key=cfg.OPENAI_API_KEY,
        base_url=cfg.OPENAI_BASE_URL,
    )
    model_name = model or cfg.OPENAI_MODEL
    logger.debug("LLM client: base_url=%s, model=%s", cfg.OPENAI_BASE_URL, model_name)

    messages = [
        {"role": "system", "content": system_prompt or "You are a helpful assistant. Respond in JSON format."},
        {"role": "user", "content": transcript},
    ]

    logger.debug("Sending to LLM model=%s base_url=%s json_mode=%s (%d+%d chars)",
                 model_name, cfg.OPENAI_BASE_URL, cfg.OPENAI_JSON_MODE,
                 len(system_prompt), len(transcript))

    kwargs = dict(
        model=model_name,
        messages=messages,
        temperature=0.1,
    )
    # json_object mode is OpenAI-specific; skip it for other providers
    if cfg.OPENAI_JSON_MODE:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)

    content_raw = response.choices[0].message.content or "{}"
    logger.info("OpenAI response received (%d chars, model=%s)", len(content_raw), model_name)

    # Try multiple strategies to extract valid JSON
    parsed_content = _try_extract_json(content_raw)

    if parsed_content is not None:
        logger.debug("Successfully parsed LLM JSON response")
    else:
        # Last resort: use the raw text as a message (strip XML tags for cleanliness)
        cleaned_text = re.sub(r"<[^>]+>", "", content_raw).strip()
        parsed_content = {"message": cleaned_text or content_raw}
        logger.warning("LLM response was not valid JSON, using raw text as message")

    return {
        "content": content_raw,
        "parsed": parsed_content,
        "model": model_name,
    }

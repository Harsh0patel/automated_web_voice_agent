import json
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

    # Parse the JSON string into an actual dict for proper WebSocket delivery
    try:
        parsed_content = json.loads(content_raw)
        logger.debug("Successfully parsed LLM JSON response")
    except json.JSONDecodeError:
        parsed_content = {"raw_text": content_raw}
        logger.warning("LLM response was not valid JSON, wrapping in raw_text")

    return {
        "content": content_raw,
        "parsed": parsed_content,
        "model": model_name,
    }

import json
from pathlib import Path

from openai import AsyncOpenAI

from backend.core import config as cfg


async def load_system_prompt() -> str:
    """
    Load the system prompt from the text file.
    Returns an empty string if the file is empty or doesn't exist.
    """
    prompt_path = Path(cfg.PROMPT_FILE)
    if prompt_path.exists():
        text = prompt_path.read_text(encoding="utf-8").strip()
        return text
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
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Set the OPENAI_API_KEY environment variable."
        )

    if system_prompt is None:
        system_prompt = await load_system_prompt()

    client = AsyncOpenAI(api_key=cfg.OPENAI_API_KEY)
    model_name = model or cfg.OPENAI_MODEL

    messages = [
        {
            "role": "system",
            "content": system_prompt or "You are a helpful assistant. Respond in JSON format.",
        },
        {
            "role": "user",
            "content": f"Here is a transcript:\n\n{transcript}\n\nPlease process this and respond in JSON format.",
        },
    ]

    response = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content_raw = response.choices[0].message.content or "{}"

    # Parse the JSON string into an actual dict for proper WebSocket delivery
    try:
        parsed_content = json.loads(content_raw)
    except json.JSONDecodeError:
        parsed_content = {"raw_text": content_raw}

    return {
        "content": content_raw,
        "parsed": parsed_content,
        "model": model_name,
    }

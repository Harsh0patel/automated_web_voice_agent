"""
Summarizer - uses the configured LLM to generate concise summaries
of conversation exchange blocks for long-range memory.
"""
from __future__ import annotations
from pathlib import Path

from backend.memory.models import MemoryEntry
from backend.app.logger import get_logger
from backend.clients.llm.openai import generate_json_from_transcript

logger = get_logger(__name__)


def _load_summarize_prompt() -> str:
    """Load the summarizer prompt from prompts/summarize_prompt.txt."""
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "summarize_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    logger.warning("Summarize prompt not found at %s, using fallback", prompt_path)
    return (
        "You are a conversation summarizer. Condense a conversation "
        "between a User and an AI Assistant into 2-4 sentences. "
        "Focus on topics, information provided, actions taken, and pending requests. "
        'Respond with ONLY JSON: {"summary": "..."}'
    )


async def summarize_exchanges(exchanges: list[MemoryEntry]) -> str | None:
    """Generate a concise summary of a list of exchanges using the LLM.

    Args:
        exchanges: List of MemoryEntry objects to summarize.

    Returns:
        Summary text string, or None if summarization failed.
    """
    if not exchanges:
        return None

    lines: list[str] = []
    for entry in exchanges:
        role = "User" if entry.role == "user" else "Assistant"
        text = entry.content[:500]
        lines.append(f"{role}: {text}")
        if entry.action:
            lines.append(f"  [Action: {entry.action.get('type', 'unknown')}]")

    conversation_text = "\n".join(lines)

    try:
        result = await generate_json_from_transcript(
            transcript=(
                f"Summarize this conversation:\n\n{conversation_text}\n\n"
                f"Respond with a concise 2-4 sentence summary."
            ),
            system_prompt=_load_summarize_prompt(),
        )
        parsed = result.get("parsed", {})
        summary = parsed.get("summary", "")
        if summary:
            return summary
        else:
            return f"Conversation: {conversation_text[:300]}"
    except Exception as e:
        logger.error("Summarization failed: %s", e)
        return None

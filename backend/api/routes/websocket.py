"""
WebSocket route for voice/text queries.

Pipeline: DB lookup -> LLM (with scraped context) -> Always-TTS -> Response
"""
import asyncio
import base64
import json
import re
import traceback
import uuid
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app import config as cfg
from backend.app import database as db
from backend.app.logger import get_logger
from backend.clients.llm.groq import transcribe_audio as groq_transcribe_audio
from backend.clients.llm.openai import generate_json_from_transcript
from backend.clients.speech.elevenlabs import synthesize_speech
from backend.memory import MemoryManager
from backend.scraping.parser import format_components_for_llm
from backend.scraping.prompt_generator import build_system_prompt
from backend.scraping import site_config as scfg

memory_manager = MemoryManager()
logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._counter = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self._counter += 1

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)

    async def send_bytes(self, websocket: WebSocket, data: bytes):
        await websocket.send_bytes(data)

    async def broadcast(self, message: str):
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning("Broadcast failed: %s", e)
                self.disconnect(connection)


manager = ConnectionManager()
TTS_OUTPUT_FORMAT = "mp3"


def _get_session_id(message_data: dict | None, websocket: WebSocket) -> str:
    if not hasattr(websocket, "_session_id"):
        websocket._session_id = None
    if message_data and message_data.get("session_id"):
        sid = message_data["session_id"]
        websocket._session_id = sid
        return sid
    if websocket._session_id:
        return websocket._session_id
    sid = str(uuid.uuid4())
    websocket._session_id = sid
    return sid


def _build_dynamic_system_prompt() -> str | None:
    """Build a dynamic system prompt from site configuration."""
    try:
        site_name = scfg.get_site_name()
        nav_mappings = scfg.get_page_mappings()
        scroll_sections = scfg.get_scrollable_sections()

        mapping_lines = "\n".join(f"   - {k} -> {v}" for k, v in sorted(nav_mappings.items()))
        scroll_lines = "\n".join(f"   - {s} - {l}" for s, l in sorted(scroll_sections.items()))

        prompt = f"""You are a helpful, conversational AI assistant for {site_name}. You answer user questions using context from the site's knowledge base when relevant.

## Guidelines
- Use the provided context to answer accurately and conversationally.
- If the user sends a greeting or small talk, respond warmly and briefly.
- If the context contains relevant information, summarize it naturally.
- If no relevant context is available, say you don't have that information.
- Keep responses concise - 1-4 sentences.
- Never mention "sources" or "knowledge base".
- Use the navigation mappings to take the user where they want. NEVER say "I can't".
- For actions you truly can't perform (e.g. processing payments), explain how the user can do it themselves.

CRITICAL: Respond with ONLY a single valid JSON object, no other text, no markdown.

## Response Format
Always include a "message" field. Optionally, include an "action" (single) or "actions" (array) field.

### Single action (simple):
{{"message": "Your response", "action": {{"type": "navigate", "path": "/page-name"}}}}

### Multi-step sequence (complex):
{{"message": "Let me help you with that.", "actions": [
  {{"type": "navigate", "path": "/page-name"}},
  {{"type": "wait", "delay": 1500}},
  {{"type": "fill", "selector": "#field-id", "value": "Some value"}},
  {{"type": "submit", "selector": "#form-id"}}
]}}

### Available action types:
- {{"type": "navigate", "path": "/page-url"}} - Navigate to a page
- {{"type": "scroll", "selector": "#section-id"}} - Scroll to a section
- {{"type": "submit", "selector": "#form-id"}} - Submit a form
- {{"type": "wait", "delay": 1000}} - Wait N ms
- {{"type": "focus", "selector": "#input-id"}} - Focus an input
- {{"type": "click", "selector": ".btn"}} - Click any element
- {{"type": "fill", "selector": "input#id", "value": "text"}} - Fill a form field
- {{"type": "select", "selector": "select#id", "value": "option"}} - Select a dropdown
- {{"type": "check", "selector": "input#id", "checked": true}} - Check/uncheck a box"""

        if nav_mappings:
            prompt += f"""

### Auto-Discovered Navigation Mappings
{mapping_lines}

### Dynamic Action Rules:
1. Use page_url from context - Navigate to the page_url found in context
2. Current page awareness - Use scroll for current page, navigate for other pages
3. Query parameters from context - Add filter params from context when applicable
4. Form pre-filling - Navigate with query params to pre-fill fields using form schemas"""

        if scroll_sections:
            prompt += f"""

### Scrollable Sections
{scroll_lines}"""

        prompt += """
## Format
{"message": "Your response", "action": {"type": "navigate", "path": "/page-name"}}
"""
        return prompt
    except Exception:
        return None


def _load_default_system_prompt() -> str:
    """Load the default system prompt from prompts/default_system_prompt.txt."""
    prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "default_system_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "You are a helpful assistant for a website. Respond in JSON format."


def _get_system_prompt() -> str:
    dynamic = _build_dynamic_system_prompt()
    if dynamic:
        return dynamic
    return _load_default_system_prompt()


async def _process_query(websocket: WebSocket, text: str, session_id: str | None = None) -> None:
    """Generic query pipeline: DB lookup -> Memory -> LLM -> TTS -> Response."""
    logger.info("Processing query (%d chars): %.80s", len(text), text)

    if not session_id:
        session_id = _get_session_id(None, websocket)

    # Step 1: Component Registry lookup
    await manager.send_json(websocket, {"type": "processing_started", "stage": "searching", "message": "Searching knowledge base..."})

    db_context = ""
    components: list[dict] = []
    try:
        components = await db.search_components(text)
        if components:
            db_context = format_components_for_llm(components)
            await manager.send_json(websocket, {"type": "db_results_found", "count": len(components),
                                                "component_types": list(set(c.get("type", "") for c in components))})
        else:
            await manager.send_json(websocket, {"type": "db_lookup_skipped", "reason": "No relevant data found."})
    except Exception as exc:
        await manager.send_json(websocket, {"type": "db_lookup_skipped", "reason": str(exc)})

    # Step 2: Memory context
    memory_context = ""
    if cfg.MEMORY_ENABLED:
        try:
            memory_context = await memory_manager.get_context(session_id)
        except Exception:
            pass

    # Step 3: LLM processing
    await manager.send_json(websocket, {"type": "processing_started", "stage": "llm", "message": "Generating response..."})

    current_path = getattr(websocket, "_current_path", "/")
    augmented_parts: list[str] = []
    if db_context:
        augmented_parts.append(f"Here is relevant information from our knowledge base:\n\n{db_context}")
    if memory_context:
        augmented_parts.append(f"Previous conversation:\n{memory_context}")
    augmented_parts.append(f"Current page: {current_path}")
    augmented_parts.append(f"User query: {text}")
    augmented_parts.append("Answer the user based on the information above. Keep responses concise - 1-4 sentences.")
    augmented_text = "\n\n".join(augmented_parts)

    system_prompt = _get_system_prompt()
    llm_result = await generate_json_from_transcript(transcript=augmented_text, system_prompt=system_prompt)
    llm_parsed = llm_result.get("parsed", {})
    response_message = llm_parsed.get("message", "")
    response_action = llm_parsed.get("action")
    response_actions = llm_parsed.get("actions")

    if response_action and not response_actions:
        response_actions = [response_action]
    elif not response_actions:
        response_actions = []

    if not response_message:
        raw = llm_result.get("content", "")
        if raw and raw != "{}":
            clean_raw = re.sub(r"<[^>]+>", "", raw).strip()
            try:
                p = json.loads(clean_raw)
                if isinstance(p, dict):
                    response_message = p.get("message", clean_raw) or clean_raw
                    if not response_actions:
                        p_action = p.get("action")
                        p_actions = p.get("actions")
                        if p_actions:
                            response_actions = p_actions
                        elif p_action:
                            response_actions = [p_action]
            except (json.JSONDecodeError, TypeError):
                pass
            if not response_message:
                m = re.search(r'\{\s*"message"\s*:\s*"([^"]+)"\s*\}', clean_raw)
                if m:
                    response_message = m.group(1)
            if not response_message:
                response_message = clean_raw

    # Store in memory
    if cfg.MEMORY_ENABLED and response_message:
        try:
            asyncio.create_task(memory_manager.add_exchange(session_id, user_message=text, assistant_message=response_message, action=response_action))
        except Exception:
            pass

    logger.info("LLM response generated (%d chars)", len(response_message))

    # Step 4: TTS
    await manager.send_json(websocket, {"type": "processing_started", "stage": "tts", "message": "Generating voice response..."})
    tts_audio = None
    tts_error = None
    if response_message.strip():
        try:
            tts_audio = await synthesize_speech(response_message, audio_format=TTS_OUTPUT_FORMAT)
        except Exception as e:
            tts_error = str(e)

    if tts_audio:
        await manager.send_bytes(websocket, tts_audio)

    await manager.send_json(websocket, {
        "type": "query_result",
        "session_id": session_id,
        "message": response_message,
        "action": response_action if not response_actions else response_actions[0],
        "actions": response_actions if len(response_actions) > 0 else None,
        "llm_raw": llm_result["content"],
        "sources": [{"type": c["type"], "page": c.get("metadata", {}).get("page_title", ""), "url": c.get("metadata", {}).get("page_url", "")} for c in components[:5]] if db_context else [],
        "tts": {"size": len(tts_audio), "format": TTS_OUTPUT_FORMAT} if tts_audio else None,
        "tts_error": tts_error,
    })


async def _run_audio_pipeline(websocket: WebSocket, audio_bytes: bytes, audio_format: str = "wav", session_id: str | None = None) -> None:
    """Transcribe audio -> _process_query."""
    await manager.send_json(websocket, {"type": "processing_started", "stage": "transcribing", "message": "Transcribing audio..."})
    transcript = await groq_transcribe_audio(audio_bytes, audio_format=audio_format)
    await manager.send_json(websocket, {"type": "transcription_complete", "transcript": transcript})
    await _process_query(websocket, transcript, session_id=session_id)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    audio_buffer: list[bytes] = []
    client_addr = websocket.client

    try:
        await manager.send_json(websocket, {"type": "connection_established", "message": "Connected to AI Assistant", "version": "1.1.0"})

        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break

            if message["type"] == "websocket.receive":
                message_bytes = message.get("bytes")
                if message_bytes is not None:
                    audio_buffer.append(message_bytes)
                    await manager.send_json(websocket, {"type": "audio_chunk_received", "bytes_received": len(message_bytes), "total_buffer": sum(len(c) for c in audio_buffer)})
                    continue

            message_text = message.get("text")
            if message_text is None:
                continue

            try:
                parsed = json.loads(message_text)
            except json.JSONDecodeError:
                session_id = _get_session_id(None, websocket)
                await _process_query(websocket, message_text, session_id=session_id)
                continue

            session_id = _get_session_id(parsed, websocket)
            if parsed.get("current_path"):
                websocket._current_path = parsed["current_path"]

            msg_type = parsed.get("type", "unknown")

            if msg_type == "audio_transcribe":
                audio_format = parsed.get("format", "wav")
                audio_data_b64 = parsed.get("data", "")
                if audio_data_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_data_b64)
                        audio_buffer = [audio_bytes]
                    except Exception as e:
                        await manager.send_json(websocket, {"type": "error", "message": f"Failed to decode audio: {e}"})
                        continue
                if not audio_buffer:
                    await manager.send_json(websocket, {"type": "error", "message": "No audio data in buffer."})
                    continue
                combined = b"".join(audio_buffer)
                audio_buffer.clear()
                await _run_audio_pipeline(websocket, combined, audio_format, session_id=session_id)
                continue

            if msg_type == "process_audio":
                audio_format = parsed.get("format", "wav")
                if not audio_buffer:
                    await manager.send_json(websocket, {"type": "error", "message": "No audio data in buffer."})
                    continue
                combined = b"".join(audio_buffer)
                audio_buffer.clear()
                await _run_audio_pipeline(websocket, combined, audio_format, session_id=session_id)
                continue

            if msg_type in ("chat", "message"):
                content = parsed.get("content", message_text)
                await _process_query(websocket, content, session_id=session_id)
                continue

            await manager.send_json(websocket, {"type": "echo", "data": parsed})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if cfg.MEMORY_ENABLED:
            sid = getattr(websocket, "_session_id", None)
            if sid:
                asyncio.create_task(memory_manager.finalize_session(sid))
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        try:
            await manager.send_json(websocket, {"type": "error", "message": f"Unexpected error: {e}", "details": traceback.format_exc()})
        except Exception:
            pass
        manager.disconnect(websocket)
        if cfg.MEMORY_ENABLED:
            sid = getattr(websocket, "_session_id", None)
            if sid:
                asyncio.create_task(memory_manager.finalize_session(sid))

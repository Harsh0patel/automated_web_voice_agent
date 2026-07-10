"""
WebSocket route for voice/text queries with:
  DB lookup → LLM (with scraped context) → Always-TTS → Response
"""
import base64
import json
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.LLM_CLIENT.soniox_client import transcribe_audio, synthesize_speech
from backend.LLM_CLIENT.openai_client import generate_json_from_transcript
from backend.core import database as db
from backend.core.logger import get_logger

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
        conn_id = self._counter
        logger.info("WS client #%d connected (total: %d)", conn_id, len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WS client disconnected (total: %d)", len(self.active_connections))

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)

    async def send_bytes(self, websocket: WebSocket, data: bytes):
        await websocket.send_bytes(data)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning("Broadcast failed, removing connection: %s", e)
                self.disconnect(connection)


manager = ConnectionManager()


async def _process_query(
    websocket: WebSocket,
    text: str,
) -> None:
    """
    Generic query pipeline:
      1. Search DB for relevant scraped content
      2. Send content + query to LLM
      3. Always convert LLM response to speech (TTS)
      4. Send audio + JSON back through WebSocket
    """
    logger.info("Processing query (%d chars): %.80s", len(text), text)

    # Step 1: DB lookup
    await manager.send_json(websocket, {
        "type": "processing_started",
        "stage": "searching",
        "message": "Searching knowledge base...",
    })

    db_context = ""
    results: list[dict] = []
    try:
        results = await db.search_pages(text)
        if results:
            parts = []
            for r in results[:3]:
                parts.append(f"--- Page: {r.get('title', r['url'])} ---\n{r['content'][:2000]}")
            db_context = "\n\n".join(parts)
            logger.info("DB lookup found %d results for query", len(results))
            await manager.send_json(websocket, {
                "type": "db_results_found",
                "count": len(results),
                "sources": [{"url": r["url"], "title": r["title"]} for r in results[:3]],
            })
        else:
            logger.info("DB lookup returned 0 results for query")
    except Exception as exc:
        db_context = ""
        results = []
        logger.warning("DB lookup failed (query=%.60s): %s", text, exc)
        await manager.send_json(websocket, {
            "type": "db_lookup_skipped",
            "reason": str(exc),
        })

    # Step 2: LLM processing
    await manager.send_json(websocket, {
        "type": "processing_started",
        "stage": "llm",
        "message": "Generating response...",
    })

    augmented_text = text
    if db_context:
        augmented_text = (
            f"Here is relevant information from our knowledge base:\n\n"
            f"{db_context}\n\n"
            f"User query: {text}\n\n"
            f"Answer the user based on the information above."
        )
        logger.debug("Augmented prompt with %d chars of context", len(db_context))

    llm_result = await generate_json_from_transcript(augmented_text)
    llm_parsed = llm_result.get("parsed", {})
    response_message = llm_parsed.get("message", llm_result.get("content", ""))
    logger.info("LLM response generated (%d chars)", len(response_message))

    # Step 3: Always do TTS
    await manager.send_json(websocket, {
        "type": "processing_started",
        "stage": "tts",
        "message": "Generating voice response...",
    })

    tts_audio = None
    tts_error = None
    if response_message.strip():
        try:
            tts_audio = await synthesize_speech(response_message)
            logger.info("TTS generated: %d bytes", len(tts_audio))
        except Exception as e:
            tts_error = str(e)
            logger.error("TTS failed: %s", tts_error)
    else:
        logger.warning("Skipping TTS — empty response message")

    # Step 4: Send audio → JSON response
    if tts_audio:
        await manager.send_bytes(websocket, tts_audio)
        logger.debug("Sent %d bytes of TTS audio", len(tts_audio))

    await manager.send_json(websocket, {
        "type": "query_result",
        "message": response_message,
        "llm_raw": llm_result["content"],
        "sources": [{"url": r["url"], "title": r["title"]} for r in results[:3]] if db_context else [],
        "tts": {
            "size": len(tts_audio),
            "format": "wav",
        } if tts_audio else None,
        "tts_error": tts_error,
    })

    logger.info("Query completed — response sent to client")


async def _run_audio_pipeline(
    websocket: WebSocket,
    audio_bytes: bytes,
    audio_format: str = "wav",
) -> None:
    """Transcribe audio → _process_query."""
    logger.info("Starting audio pipeline: %d bytes, format=%s", len(audio_bytes), audio_format)
    await manager.send_json(websocket, {
        "type": "processing_started",
        "stage": "transcribing",
        "message": f"Transcribing {len(audio_bytes)} bytes of audio...",
    })
    transcript = await transcribe_audio(audio_bytes, audio_format=audio_format)
    logger.info("Transcription complete: %.100s", transcript)
    await manager.send_json(websocket, {
        "type": "transcription_complete",
        "transcript": transcript,
    })
    await _process_query(websocket, transcript)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    audio_buffer: list[bytes] = []
    client_addr = websocket.client
    logger.info("WebSocket connection opened from %s", client_addr)

    try:
        await manager.send_json(websocket, {
            "type": "connection_established",
            "message": "Connected to AI Assistant with knowledge base lookup",
            "version": "1.1.0",
        })

        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                logger.info("Client %s disconnected", client_addr)
                break

            # --- BINARY audio input ---
            if message["type"] == "websocket.receive":
                message_bytes = message.get("bytes")
                if message_bytes is not None:
                    audio_buffer.append(message_bytes)
                    total = sum(len(c) for c in audio_buffer)
                    logger.debug("Received audio chunk: %d bytes (buffer: %d)", len(message_bytes), total)
                    await manager.send_json(websocket, {
                        "type": "audio_chunk_received",
                        "bytes_received": len(message_bytes),
                        "total_buffer": total,
                    })
                    continue

            # --- TEXT / JSON input ---
            message_text = message.get("text")
            if message_text is None:
                continue

            try:
                parsed = json.loads(message_text)
            except json.JSONDecodeError:
                # Plain text → treat as query
                logger.info("Received plain text query from %s: %.60s", client_addr, message_text)
                try:
                    await _process_query(websocket, message_text)
                except Exception as e:
                    logger.error("Query processing failed: %s", e, exc_info=True)
                    await manager.send_json(websocket, {
                        "type": "error", "message": f"Processing failed: {e}",
                    })
                continue

            msg_type = parsed.get("type", "unknown")
            logger.debug("Received JSON message type=%s from %s", msg_type, client_addr)

            # --- AUDIO via base64 JSON ---
            if msg_type == "audio_transcribe":
                audio_format = parsed.get("format", "wav")
                audio_data_b64 = parsed.get("data", "")
                if audio_data_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_data_b64)
                        audio_buffer = [audio_bytes]
                        logger.info("Decoded base64 audio: %d bytes", len(audio_bytes))
                    except Exception as e:
                        logger.warning("Base64 decode failed: %s", e)
                        await manager.send_json(websocket, {
                            "type": "error", "message": f"Failed to decode audio data: {e}",
                        })
                        continue
                if not audio_buffer:
                    await manager.send_json(websocket, {
                        "type": "error", "message": "No audio data in buffer.",
                    })
                    continue
                combined = b"".join(audio_buffer)
                audio_buffer.clear()
                try:
                    await _run_audio_pipeline(websocket, combined, audio_format)
                except Exception as e:
                    logger.error("Audio pipeline failed: %s", e, exc_info=True)
                    await manager.send_json(websocket, {
                        "type": "error", "stage": "pipeline", "message": f"Audio processing failed: {e}",
                    })
                continue

            # --- PROCESS buffered binary audio ---
            if msg_type == "process_audio":
                audio_format = parsed.get("format", "wav")
                if not audio_buffer:
                    await manager.send_json(websocket, {
                        "type": "error", "message": "No audio data in buffer.",
                    })
                    continue
                combined = b"".join(audio_buffer)
                audio_buffer.clear()
                logger.info("Processing buffered audio: %d bytes", len(combined))
                try:
                    await _run_audio_pipeline(websocket, combined, audio_format)
                except Exception as e:
                    logger.error("Audio pipeline failed: %s", e, exc_info=True)
                    await manager.send_json(websocket, {
                        "type": "error", "stage": "pipeline", "message": f"Audio processing failed: {e}",
                    })
                continue

            # --- TEXT INPUT ---
            if msg_type in ("chat", "message"):
                content = parsed.get("content", message_text)
                logger.info("Chat/message from %s: %.80s", client_addr, content)
                try:
                    await _process_query(websocket, content)
                except Exception as e:
                    logger.error("Chat processing failed: %s", e, exc_info=True)
                    await manager.send_json(websocket, {
                        "type": "error", "message": f"Processing failed: {e}",
                    })
                continue

            # Fallback echo
            logger.debug("Echoing unknown JSON message type=%s", msg_type)
            await manager.send_json(websocket, {"type": "echo", "data": parsed})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("Unexpected WebSocket error from %s: %s", client_addr, e, exc_info=True)
        try:
            await manager.send_json(websocket, {
                "type": "error", "message": f"Unexpected error: {e}",
                "details": traceback.format_exc(),
            })
        except Exception:
            pass
        manager.disconnect(websocket)

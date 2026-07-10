import base64
import json
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.LLM_CLIENT.soniox_client import transcribe_audio
from backend.LLM_CLIENT.openai_client import generate_json_from_transcript

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


async def _run_audio_pipeline(
    websocket: WebSocket,
    audio_bytes: bytes,
    audio_format: str = "wav",
) -> None:
    """
    Transcribe audio through Soniox, then generate JSON via OpenAI,
    sending progress updates back through the WebSocket.
    """
    # Step 1: transcription
    await manager.send_json(websocket, {
        "type": "processing_started",
        "stage": "transcribing",
        "message": f"Transcribing {len(audio_bytes)} bytes of audio...",
    })

    transcript = await transcribe_audio(audio_bytes, audio_format=audio_format)

    await manager.send_json(websocket, {
        "type": "transcription_complete",
        "transcript": transcript,
    })

    # Step 2: LLM JSON generation
    await manager.send_json(websocket, {
        "type": "processing_started",
        "stage": "llm",
        "message": "Generating JSON response...",
    })

    llm_result = await generate_json_from_transcript(transcript)

    # Step 3: final result
    await manager.send_json(websocket, {
        "type": "audio_processed",
        "transcript": transcript,
        "llm_response": llm_result,
    })


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    audio_buffer: list[bytes] = []

    try:
        # Send a welcome message
        await manager.send_json(websocket, {
            "type": "connection_established",
            "message": "Connected to WebSocket server",
            "version": "1.0.0",
        })

        while True:
            # Use low-level receive() to handle both text and binary messages
            message = await websocket.receive()

            # Handle disconnect
            if message["type"] == "websocket.disconnect":
                break

            # --- BINARY audio input ---
            if message["type"] == "websocket.receive":
                message_bytes = message.get("bytes")
                if message_bytes is not None:
                    audio_buffer.append(message_bytes)
                    await manager.send_json(websocket, {
                        "type": "audio_chunk_received",
                        "bytes_received": len(message_bytes),
                        "total_buffer": sum(len(c) for c in audio_buffer),
                    })
                    continue

            # --- TEXT / JSON input ---
            message_text = message.get("text")
            if message_text is None:
                continue

            try:
                parsed = json.loads(message_text)
            except json.JSONDecodeError:
                # Plain text input (echo back)
                await manager.send_json(websocket, {
                    "type": "response",
                    "input_type": "text",
                    "content": f"Received: {message_text}",
                    "original": message_text,
                })
                continue

            msg_type = parsed.get("type", "unknown")

            # --- AUDIO via base64 JSON ---
            if msg_type == "audio_transcribe":
                audio_format = parsed.get("format", "wav")
                audio_data_b64 = parsed.get("data", "")

                if audio_data_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_data_b64)
                        audio_buffer = [audio_bytes]
                    except Exception as e:
                        await manager.send_json(websocket, {
                            "type": "error",
                            "message": f"Failed to decode audio data: {e}",
                        })
                        continue

                if not audio_buffer:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": "No audio data in buffer. Send audio first.",
                    })
                    continue

                combined_audio = b"".join(audio_buffer)
                audio_buffer.clear()

                try:
                    await _run_audio_pipeline(websocket, combined_audio, audio_format)
                except Exception as e:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "stage": "pipeline",
                        "message": f"Audio processing failed: {e}",
                    })
                continue

            # --- PROCESS buffered binary audio ---
            if msg_type == "process_audio":
                audio_format = parsed.get("format", "wav")

                if not audio_buffer:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": "No audio data in buffer. Send binary audio first.",
                    })
                    continue

                combined_audio = b"".join(audio_buffer)
                audio_buffer.clear()

                try:
                    await _run_audio_pipeline(websocket, combined_audio, audio_format)
                except Exception as e:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "stage": "pipeline",
                        "message": f"Audio processing failed: {e}",
                    })
                continue

            # --- TEXT INPUT via LLM ---
            if msg_type in ("chat", "message"):
                content = parsed.get("content", message_text)
                try:
                    llm_result = await generate_json_from_transcript(content)
                    await manager.send_json(websocket, {
                        "type": "response",
                        "input_type": msg_type,
                        "content": llm_result["content"],
                        "parsed": llm_result.get("parsed", {}),
                        "model": llm_result.get("model", ""),
                        "original": parsed,
                    })
                except Exception as e:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": f"OpenAI processing failed: {e}",
                    })
                continue

            # Fallback: echo the JSON
            await manager.send_json(websocket, {
                "type": "echo",
                "data": parsed,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        try:
            await manager.send_json(websocket, {
                "type": "error",
                "message": f"Unexpected error: {e}",
                "details": traceback.format_exc(),
            })
        except Exception:
            pass
        manager.disconnect(websocket)

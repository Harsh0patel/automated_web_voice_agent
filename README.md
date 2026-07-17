# Automated Web Agent — Backend

A headless FastAPI backend that accepts **audio + text input** via WebSocket, transcribes audio using **Soniox STT**, generates structured **JSON responses** via **OpenAI**, and sends the result back in real time.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Backend](#running-the-backend)
- [API Reference](#api-reference)
  - [REST Endpoints](#rest-endpoints)
  - [WebSocket Protocol](#websocket-protocol)
- [WebSocket Message Reference](#websocket-message-reference)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Continuous Integration (CI)](#continuous-integration-ci)

---

## Architecture

```
┌─────────────┐    WebSocket     ┌──────────────────────────────────────────────────┐
│             │ ◄──────────────► │                  FastAPI Backend                    │
│   Client    │                  │                                                      │
│  (Browser)  │  Text / Audio    │  ┌──────────┐   ┌──────────────┐   ┌─────────────┐ │
│             │ ───────────────► │  │  Groq    │   │   LLM (any   │   │  ElevenLabs  │ │
│             │                  │  │  STT     │──►│   OpenAI-    │──►│   TTS        │ │
│             │ ◄─────────────── │  └──────────┘   │   compatible │   └─────────────┘ │
│             │  TTS Audio +     │                  └──────────────┘                   │
│             │  JSON Response   │  + MongoDB (memory + component registry)            │
└─────────────┘                  └──────────────────────────────────────────────────┘
```

**Pipeline:**
1. Client connects to `ws://localhost:8000/ws`
2. Sends text (chat) or audio (binary chunks / base64)
3. Server searches the **Component Registry** (MongoDB) for relevant context
4. Retrieves **Conversation Memory** for the session
5. Sends everything to the **LLM** with a system prompt loaded from `backend/prompts/`
6. LLM returns a JSON response with message + optional actions (navigate, scroll, fill, submit, etc.)
7. Server synthesizes **TTS audio** via ElevenLabs
8. Sends audio bytes + JSON result back through the WebSocket

---

## Prerequisites

- **Python 3.12+**
- **uv** (Python package manager) — [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Soniox API key** — [Get one](https://soniox.com)
- **OpenAI API key** — [Get one](https://platform.openai.com/api-keys)

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd automated_web_agent

# 2. Create and activate a virtual environment
uv venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install all dependencies
uv sync

# 4. Copy and configure environment variables
cp .env.example .env
```

---

## Configuration

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI / compatible API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | LLM model name |
| `GROQ_API_KEY` | No | — | Groq Whisper STT key (audio input) |
| `ELEVENLABS_API_KEY` | No | — | ElevenLabs TTS key (voice output) |
| `MONGO_URI` | No | `mongodb://localhost:27017` | MongoDB URI (memory + components) |

### System Prompts

Prompts are stored as plain `.txt` files in `backend/prompts/`:

| File | Purpose |
|---|---|
| `default_system_prompt.txt` | Main AI assistant prompt (fallback) |
| `summarize_prompt.txt` | Conversation memory summarizer |

Edit these files to customize the assistant's behavior.

---

## Running the Backend

```bash
# Start the server (hot-reload enabled)
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`.

| Endpoint | Description |
|---|---|
| `http://localhost:8000/` | Health check / homepage |
| `http://localhost:8000/health` | Detailed health status |
| `ws://localhost:8000/ws` | WebSocket for audio/text input |

---

## API Reference

### REST Endpoints

#### `GET /`

Returns a basic welcome message.

```json
{
  "message": "this is backend homepage"
}
```

#### `GET /health`

Returns the server health status.

```json
{
  "status": "healthy",
  "api_version": "1.0.0",
  "api_status": "running"
}
```

### WebSocket Protocol

Connect to `ws://<host>:8000/ws`.

On connection, the server sends a welcome message:

```json
{
  "type": "connection_established",
  "message": "Connected to WebSocket server",
  "version": "1.0.0"
}
```

The WebSocket supports both **text** and **binary** messages.

---

## WebSocket Message Reference

### Sending Audio (Option 1 — Binary Chunks)

Send raw audio as binary WebSocket frames, then send a JSON message to process.

```python
# 1. Send audio as binary chunks (one or more)
ws.send_bytes(b"<raw audio data>")

# Server responds:
# {"type": "audio_chunk_received", "bytes_received": 1234, "total_buffer": 1234}

# 2. Trigger processing
ws.send_json({"type": "process_audio", "format": "wav"})
```

### Sending Audio (Option 2 — Base64 in JSON)

Send audio as base64-encoded data in a single JSON message.

```python
import base64

audio_b64 = base64.b64encode(audio_bytes).decode()

ws.send_json({
    "type": "audio_transcribe",
    "format": "wav",
    "data": audio_b64
})
```

### Sending Text for LLM Processing

```python
ws.send_json({
    "type": "chat",
    "content": "Your text here..."
})

# Or with type "message":
ws.send_json({
    "type": "message",
    "content": "Your text here..."
})
```

### Sending Plain Text (Echo)

```python
ws.send_text("Just a regular message")
# Server echoes: {"type": "response", "input_type": "text", "content": "Received: Just a regular message", ...}
```

### Audio Pipeline Server Responses

When processing audio, the server sends these messages in order:

| Step | Type | Fields |
|---|---|---|
| 1. Transcription starts | `processing_started` | `stage: "transcribing"`, `message` |
| 2. Transcription done | `transcription_complete` | `transcript` |
| 3. LLM starts | `processing_started` | `stage: "llm"`, `message` |
| 4. Final result | `audio_processed` | `transcript`, `llm_response` |

**`audio_processed` response example:**

```json
{
  "type": "audio_processed",
  "transcript": "Hello, how are you?",
  "llm_response": {
    "content": "{\"intent\": \"greeting\", \"sentiment\": \"positive\"}",
    "parsed": {
      "intent": "greeting",
      "sentiment": "positive"
    },
    "model": "gpt-4o-mini"
  }
}
```

### Chat / Text LLM Response

```json
{
  "type": "response",
  "input_type": "chat",
  "content": "{\"reply\": \"Hello! How can I help?\"}",
  "parsed": {"reply": "Hello! How can I help?"},
  "model": "gpt-4o-mini",
  "original": {"type": "chat", "content": "Hi"}
}
```

### Error Responses

All errors follow this format:

```json
{
  "type": "error",
  "stage": "transcription|llm|pipeline",
  "message": "Description of what went wrong"
}
```

---

## Project Structure

```
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI
│
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Environment variable config
│   │   ├── database.py        # MongoDB connection + queries
│   │   └── logger.py          # Logging configuration
│   ├── api/routes/
│   │   ├── homepage.py        # REST routes (/, /health)
│   │   ├── scrape.py          # Scraping + component endpoints
│   │   └── websocket.py       # WebSocket route (/ws)
│   ├── clients/
│   │   ├── llm/
│   │   │   ├── openai.py      # OpenAI-compatible LLM client
│   │   │   └── groq.py        # Groq Whisper STT client
│   │   └── speech/
│   │       ├── elevenlabs.py  # ElevenLabs TTS client
│   │       └── soniox.py      # Soniox STT client (fallback)
│   ├── memory/
│   │   ├── manager.py         # MemoryManager (buffer + MongoDB)
│   │   ├── models.py          # MemoryEntry, ConversationSummary
│   │   └── summarizer.py      # Async LLM call for summarization
│   ├── scraping/
│   │   ├── browser.py         # Playwright-based site scraper
│   │   ├── fetcher.py         # HTTP-based page fetcher
│   │   ├── parser.py          # Component parser (typed extraction)
│   │   ├── prompt_generator.py# Dynamic system prompt builder
│   │   └── site_config.py     # Site configuration loader
│   ├── schemas/
│   │   └── pydantic_models.py # Data models
│   └── prompts/
│       ├── default_system_prompt.txt  # Main AI assistant prompt
│       └── summarize_prompt.txt       # Memory summarizer prompt
│
├── tests/
│   ├── conftest.py            # Shared fixtures & mocks
│   ├── unit/                  # Unit tests (49 tests)
│   │   ├── test_config.py
│   │   ├── test_pydantic_models.py
│   │   ├── test_soniox_client.py
│   │   ├── test_openai_client.py
│   │   ├── test_homepage.py
│   │   └── test_websocket.py
│   ├── integration/           # Integration tests (19 tests)
│   │   ├── test_rest_routes.py
│   │   └── test_websocket_routes.py
│   └── e2e/                   # End-to-end tests (6 tests)
│       └── test_full_pipeline.py
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

---

## Testing

The project has **208 tests** across three levels.

### Running All Tests

```bash
uv run pytest tests/ -v --tb=short
```

### Running Specific Test Categories

```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# End-to-end tests only
uv run pytest tests/e2e/ -v

# Specific test file
uv run pytest tests/unit/test_openai_client.py -v
```

### Test Categories

| Level | Count | What it tests |
|---|---|---|
| **Unit** | 160 | Individual functions/classes in isolation. External APIs (Soniox, OpenAI) are mocked. |
| **Integration** | 34 | WebSocket routes with mocked external services, REST API responses. |
| **End-to-End** | 14 | Full audio pipeline, error handling, mixed text/audio flows. All external APIs mocked. |

Tests use:
- **pytest** — test runner
- **pytest-asyncio** — async test support
- **pytest-mock** — mocking external services
- **unittest.mock** — built-in mocking utilities

---

## Continuous Integration (CI)

The project uses **GitHub Actions** to automatically run the test suite on every push or pull request to the `main` branch.

### Workflow: `.github/workflows/ci.yml`

The CI pipeline:

1. **Checks out** the repository
2. **Installs Python 3.12** and **uv** (with caching for faster installs)
3. **Installs all dependencies** via `uv sync`
4. **Runs the full test suite** via `uv run pytest tests/ -v --tb=short`

### CI Status

To see CI results:
1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Select the **CI** workflow
4. Click on any run to see detailed test output

### Adding CI to a New Repository

Push the code to GitHub and the workflow will run automatically. No additional configuration needed.

### CI Badge (Optional)

Add this to your `README.md` to show the CI status:

```markdown
[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
```

---

## Quick Example (Python Client)

```python
import asyncio
import json
from fastapi.testclient import TestClient

from backend.app.main import app

async def demo():
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        # Read welcome
        welcome = ws.receive_json()
        print(f"Connected: {welcome['message']}")

        # Send text for LLM processing
        ws.send_json({"type": "chat", "content": "What's the weather like?"})

        # Read response
        response = ws.receive_json()
        if response["type"] == "response":
            print(f"LLM response: {json.dumps(response['parsed'], indent=2)}")

asyncio.run(demo())
```

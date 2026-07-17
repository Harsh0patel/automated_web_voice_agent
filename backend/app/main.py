"""
FastAPI application entry point.

Sets up logging, applies Windows asyncio fixes, includes all API routes,
and serves the frontend static files.
"""
import asyncio
import sys

if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.logger import setup_logging, get_logger
from backend.api.routes import homepage, scrape, websocket
from backend.scraping.browser import _start as _pw_start, _stop as _pw_stop

setup_logging(level="INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start Playwright on server start, shut down on stop."""
    logger.info("Starting Playwright browser...")
    try:
        await _pw_start()
        logger.info("Playwright browser ready")
    except Exception as exc:
        logger.error("Failed to start Playwright: %s", exc)
    yield
    logger.info("Shutting down Playwright...")
    await _pw_stop()


app = FastAPI(title="AI Voice Assistant API", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:8001", "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(homepage.router)
app.include_router(scrape.router)
app.include_router(websocket.router)

frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
static_dir = frontend_path / "dist"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="frontend")
elif frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
else:
    logger.warning("Frontend directory not found at %s", frontend_path)

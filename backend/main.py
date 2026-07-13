"""
FastAPI application entry point.

Sets up logging, applies Windows asyncio fixes, and
mounts the frontend static files.
"""
import asyncio
import sys

# ── Windows asyncio fix (must be BEFORE any event loop is created) ──
# Playwright needs ProactorEventLoopPolicy to spawn Chromium subprocesses
# on Windows. The default Python 3.12+ policy is correct, but uvicorn may
# override it. We set it here at import time so it takes effect before
# the event loop is started in lifespan or during requests.
if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .core.logger import setup_logging, get_logger
from .core.scraper_site import _start as _pw_start, _stop as _pw_stop
from .routes import homepage, scrape, websocket

# Initialize logging at startup
setup_logging(level="INFO")

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start up Playwright browser on server start, shut down on stop."""
    logger.info("Starting Playwright browser for site scraping ...")
    try:
        await _pw_start()
        logger.info("Playwright browser ready")
    except Exception as exc:
        logger.error("Failed to start Playwright browser: %s", exc)
    yield
    logger.info("Shutting down Playwright browser ...")
    await _pw_stop()
    logger.info("Playwright browser shut down")


app = FastAPI(
    title="AI Voice Assistant API",
    version="1.1.0",
    lifespan=lifespan,
)

# Include API routes first so they take priority over static files
app.include_router(homepage.router)
app.include_router(scrape.router)
app.include_router(websocket.router)

# Serve frontend static files at /app path (not root, to avoid route conflicts)
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
# Serve the production build (dist/) if it exists, otherwise serve the dev root
static_dir = frontend_path / "dist"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="frontend")
    logger.info("Frontend (React build) mounted at /app from %s", static_dir)
elif frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    logger.info("Frontend (dev) mounted at /app from %s", frontend_path)
else:
    logger.warning("Frontend directory not found at %s", frontend_path)

logger.info("Server started — routes: /, /health, /scrape, /ws, /app")

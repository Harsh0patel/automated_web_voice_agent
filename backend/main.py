from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .core.logger import setup_logging, get_logger
from .routes import homepage, scrape, websocket

# Initialize logging at startup
setup_logging(level="INFO")

logger = get_logger(__name__)

app = FastAPI(title="AI Voice Assistant API", version="1.1.0")

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

logger.info(
    "Server started — routes: /, /health, /scrape, /ws, /app"
)

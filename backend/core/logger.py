"""
Centralized logging configuration for the backend server.
All modules should import `get_logger` and create a module-level logger.
"""
import logging
import sys
from pathlib import Path

# Log format: timestamp | level | module:function | message
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
) -> None:
    """
    Configure root logging once at startup.

    Args:
        level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_file: Optional path to a log file. If None, logs go to stdout.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove any existing handlers (avoids duplicates on reload)
    root.handlers.clear()

    # Console handler (stdout)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(console)

    # Optional file handler
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(path), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        root.addHandler(file_handler)

    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    root.info("Logging initialised — level=%s, file=%s", level, log_file or "(stdout)")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Usage:
        logger = get_logger(__name__)
        logger.info("message")
    """
    return logging.getLogger(name)

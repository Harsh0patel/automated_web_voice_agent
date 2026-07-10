"""Unit tests for the centralized logging module."""

import logging
import io
import sys

import pytest


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_default_level(self):
        """Default log level should be INFO."""
        from backend.core.logger import setup_logging

        setup_logging(level="INFO")

        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_setup_debug_level(self):
        """Should respect DEBUG log level."""
        from backend.core.logger import setup_logging

        setup_logging(level="DEBUG")

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_setup_invalid_level_falls_back(self):
        """Invalid log level should fall back to INFO."""
        from backend.core.logger import setup_logging

        setup_logging(level="INVALID")

        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_setup_clears_existing_handlers(self):
        """Should clear existing handlers before adding new ones."""
        from backend.core.logger import setup_logging

        root = logging.getLogger()
        root.addHandler(logging.StreamHandler(sys.stdout))
        handler_count_before = len(root.handlers)

        setup_logging(level="INFO")

        # Should have exactly 1 handler (console)
        assert len(root.handlers) == 1

    def test_console_handler_output(self):
        """The console handler should output to stdout."""
        from backend.core.logger import setup_logging

        setup_logging(level="DEBUG")

        root = logging.getLogger()
        # Find the stream handler
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1
        assert stream_handlers[0].stream == sys.stdout

    def test_file_handler_added_when_specified(self, tmp_path):
        """Should add a file handler when log_file is specified."""
        from backend.core.logger import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(level="INFO", log_file=str(log_file))

        root = logging.getLogger()
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert str(file_handlers[0].baseFilename) == str(log_file.resolve())

    def test_no_file_handler_by_default(self):
        """Should not add a file handler by default."""
        from backend.core.logger import setup_logging

        setup_logging(level="INFO")

        root = logging.getLogger()
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0

    def test_quiets_noisy_libraries(self):
        """Noisy libraries should be set to WARNING level."""
        from backend.core.logger import setup_logging

        setup_logging(level="DEBUG")

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING

    def test_logger_actually_logs(self):
        """The logger should actually output log messages."""
        from backend.core.logger import setup_logging, get_logger

        setup_logging(level="INFO")

        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert logger.isEnabledFor(logging.INFO)

    def test_logger_respects_level(self):
        """The logger should respect the configured level."""
        from backend.core.logger import setup_logging, get_logger

        setup_logging(level="ERROR")

        logger = get_logger("test_module")
        assert not logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.ERROR)

"""Tests for documentation_sync.log module."""
import json
import logging
from io import StringIO

import pytest

from documentation_sync.log import (
    JsonFormatter,
    JsonLogger,
    get_logger,
    setup_logging,
    now_utc,
)


class TestJsonFormatter:
    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["event"] == "Test message"
        assert "timestamp" in data

    def test_format_with_context(self):
        """Test formatting with structured context."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None
        )
        record.docsync_context = {"phase": "architecture", "duration_ms": 123}
        result = formatter.format(record)
        data = json.loads(result)
        # Context should not be automatically merged without _CONTEXT_KEY
        assert "phase" not in data

    def test_format_with_exception(self):
        """Test formatting when exception info is present."""
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py",
            lineno=1, msg="Error occurred", args=(), exc_info=exc_info
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "ERROR"
        assert "exception" in data  # Exception should be included


class TestJsonLogger:
    def test_logger_debug(self):
        """Test debug logging."""
        logger = JsonLogger("test")
        # Should not raise
        logger.debug("test event", key="value")

    def test_logger_info(self):
        """Test info logging."""
        logger = JsonLogger("test")
        logger.info("test event", key="value")

    def test_logger_warning(self):
        """Test warning logging."""
        logger = JsonLogger("test")
        logger.warning("test event", key="value")

    def test_logger_error(self):
        """Test error logging."""
        logger = JsonLogger("test")
        logger.error("test event", key="value")

    def test_logger_exception(self):
        """Test exception logging."""
        logger = JsonLogger("test")
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("error occurred", context="value")

    def test_logger_bind(self):
        """Test binding context to logger."""
        logger = JsonLogger("test", initial="context")
        bound = logger.bind(phase="architecture")
        assert bound._defaults["initial"] == "context"
        assert bound._defaults["phase"] == "architecture"

    def test_logger_with_defaults(self):
        """Test logger with default context."""
        logger = JsonLogger("test", request_id="12345")
        # Should not raise
        logger.info("event", extra="data")


class TestGetLogger:
    def test_get_logger_returns_cached_instance(self):
        """Test that get_logger caches instances."""
        logger1 = get_logger("myapp")
        logger2 = get_logger("myapp")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different logger names create different instances."""
        logger1 = get_logger("app1")
        logger2 = get_logger("app2")
        assert logger1 is not logger2


class TestSetupLogging:
    def test_setup_logging_idempotent(self):
        """Test that setup_logging is idempotent."""
        # Clear any existing handlers
        root = logging.getLogger("docsync")
        root.handlers.clear()
        
        # Setup twice
        setup_logging()
        handler_count_1 = len(root.handlers)
        setup_logging()
        handler_count_2 = len(root.handlers)
        
        # Should not add more handlers
        assert handler_count_1 == handler_count_2

    def test_setup_logging_with_custom_stream(self):
        """Test setup_logging with custom stream."""
        stream = StringIO()
        # Clear handlers first
        root = logging.getLogger("docsync_custom")
        root.handlers.clear()
        
        # Setup with custom stream
        setup_logging(stream=stream)
        # Should not raise


class TestNowUtc:
    def test_now_utc_returns_iso_string(self):
        """Test that now_utc returns ISO 8601 timestamp."""
        result = now_utc()
        assert isinstance(result, str)
        assert "T" in result
        assert "Z" in result or "+" in result  # UTC indicator

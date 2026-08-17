"""Structured, JSON-formatted logging for observability.

Replaces ad-hoc ``print()`` calls with a ``structlog``-style key/value logger
built on the stdlib :mod:`logging` module (avoids a hard dependency on
structlog). Emits one JSON object per line with structured fields such as:

    {"event": "phase_complete", "phase": "architecture",
     "phase_latency_ms": 12, "llm_tokens_in": 310, "llm_tokens_out": 120,
     "fallback_triggered": true, "timestamp": "2026-08-13T10:00:00Z"}

Call :func:`setup_logging` once at process startup; then use :func:`get_logger`.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import sys
from typing import Any, Dict, Optional

# Fields that carry diagnostic/performance context per structured event.
_CONTEXT_KEY = "docsync.context"


class JsonFormatter(logging.Formatter):
    """Emit each record as a single JSON object on one line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        # Merge structured context bound via get_logger().bind(...).
        context = getattr(record, _CONTEXT_KEY, None)
        if isinstance(context, dict):
            payload.update(context)
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class JsonLogger:
    """Small structlog-like wrapper around a stdlib logger.

    Usage::

        log = get_logger()
        log.info("phase_complete", phase="architecture", phase_latency_ms=12)

    Produces a JSON line with the given key/value fields.
    """

    def __init__(self, name: str = "docsync", **defaults: Any) -> None:
        self._logger = logging.getLogger(name)
        self._defaults = defaults

    def bind(self, **kwargs: Any) -> "JsonLogger":
        """Return a new logger with extra context merged into every event."""
        merged = {**self._defaults, **kwargs}
        return JsonLogger(self._logger.name, **merged)

    def _emit(self, level: int, event: str, **kwargs: Any) -> None:
        context = {**self._defaults, **kwargs}
        # rate_limit tracks token/usage counts that should be visible even at
        # the warning level (they help debugging, not just diagnostics).
        if context:
            extra = {_CONTEXT_KEY: context}
        else:
            extra = None
        self._logger.log(level, event, extra=extra)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.DEBUG, event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.ERROR, event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception(event, extra={_CONTEXT_KEY: kwargs} if kwargs else None)


_loggers: Dict[str, JsonLogger] = {}


def get_logger(name: str = "docsync", **defaults: Any) -> JsonLogger:
    """Return a cached JsonLogger for *name* with the given default context."""
    key = name
    if key not in _loggers:
        _loggers[key] = JsonLogger(name, **defaults)
    return _loggers[key]


def setup_logging(
    level: str | int = "INFO",
    stream=None,
) -> None:
    """Configure the root docsync logger with a JSON formatter.

    Safe to call multiple times; idempotent after first setup.
    """
    root = logging.getLogger("docsync")
    if root.handlers:
        return
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level if isinstance(level, int) else level.upper())
    root.propagate = False


def now_utc() -> str:
    """ISO-8601 UTC timestamp used for latency/duration bookkeeping."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat()

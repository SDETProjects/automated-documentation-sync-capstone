"""Retry and backoff primitives for flaky external calls (LLM, Jira).

Implements a small, dependency-free exponential-backoff with jitter. The
design goal is a drop-in wrapper for the LLM adapters and Jira fetches so
transient 429 / 5xx failures are retried automatically without coupling the
whole codebase to ``tenacity``.
"""
from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Subclasses of these (plus our own JiraConnectorError) trigger a retry.
_TRANSIENT_EXCEPTIONS: tuple[type[Exception], ...] = ()


class RetryableError(Exception):
    """Marker exception: raise to ask the caller to retry with backoff."""


# Errors from the Anthropic SDK that are transient (rate limit / server).
_ANTHROPIC_TRANSIENT = ("RateLimitError", "APITimeoutError", "InternalServerError")
_HTTP_TRANSIENT = (429, 500, 502, 503, 504)


def _is_retryable(exc: BaseException) -> bool:
    """Return True if *exc* is a known transient failure worth retrying."""
    if isinstance(exc, RetryableError):
        return True
    # JiraConnectorError: retry only on 5xx (network blips).
    if exc.__class__.__name__ == "JiraConnectorError":
        return "timed out" in str(exc) or "Could not reach" in str(exc)
    # Anthropic SDK rate-limit/timeout/server errors.
    name = exc.__class__.__name__
    if name in _ANTHROPIC_TRANSIENT:
        return True
    # httpx/requests HTTPStatusError carrying a status_code.
    status = getattr(exc, "status_code", None)
    if status in _HTTP_TRANSIENT:
        return True
    return False


def _retry_after_from(exc: BaseException) -> float | None:
    """Parse the Retry-After header (seconds) from an exception if present."""
    # requests.Response exposes headers on the exception's .response
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) if response is not None else None
    if headers:
        retry_after = headers.get("Retry-After")
        if retry_after is not None:
            try:
                return float(retry_after)
            except (TypeError, ValueError):
                return None
    return None


def retry(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.1,
    **kwargs: Any,
) -> T:
    """Call *func* with exponential backoff on transient failures.

    Args:
        max_retries: Maximum number of *retries* (attempts = retries + 1).
        base_delay: Initial sleep between retries, seconds.
        max_delay: Cap on the backoff sleep, seconds.
        jitter: Random jitter fraction applied to each sleep.
    """
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - we re-raise non-transient
            if attempt >= max_retries or not _is_retryable(exc):
                raise
            attempt += 1
            retry_after = _retry_after_from(exc)
            if retry_after is not None:
                delay = min(retry_after, max_delay)
            else:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            # Full jitter in [-jitter, +jitter] * delay
            delay *= 1 + (random.random() * 2 - 1) * jitter
            logger.warning(
                "Retrying %s after transient failure (%d/%d) in %.2fs: %s",
                getattr(func, "__name__", func),
                attempt,
                max_retries,
                delay,
                exc,
            )
            time.sleep(max(0.0, delay))


def retrying(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator form of :func:`retry` for methods/standalone functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retry(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                **kwargs,
            )
        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        wrapper.__doc__ = getattr(func, "__doc__", None)
        return wrapper
    return decorator

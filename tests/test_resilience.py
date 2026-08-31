"""Tests for documentation_sync.resilience — retry/backoff primitives."""
import logging
from unittest.mock import MagicMock, patch

import pytest

from documentation_sync.resilience import (
    RetryableError,
    _is_retryable,
    _retry_after_from,
    retry,
    retrying,
)


# ---------------------------------------------------------------------------
# _is_retryable
# ---------------------------------------------------------------------------

def test_is_retryable_returns_true_for_retryable_error():
    assert _is_retryable(RetryableError("transient")) is True


def test_is_retryable_returns_false_for_value_error():
    assert _is_retryable(ValueError("bad input")) is False


def test_is_retryable_returns_false_for_runtime_error():
    assert _is_retryable(RuntimeError("crash")) is False


def test_is_retryable_jira_connector_error_on_timeout():
    """JiraConnectorError subclass with 'timed out' message is retryable."""
    # Create a class named exactly "JiraConnectorError" so _is_retryable
    # recognises it by __class__.__name__.
    JiraConnectorError = type("JiraConnectorError", (Exception,), {})
    err = JiraConnectorError("timed out connecting to server")
    assert _is_retryable(err) is True


def test_is_retryable_jira_connector_error_non_transient():
    """JiraConnectorError without transient message is NOT retried."""
    JiraConnectorError = type("JiraConnectorError", (Exception,), {})
    err = JiraConnectorError("invalid credentials")
    assert _is_retryable(err) is False


def test_is_retryable_checks_http_status_code():
    exc = Exception("429 rate limit")
    exc.status_code = 429
    assert _is_retryable(exc) is True


def test_is_retryable_false_for_4xx_non_429():
    exc = Exception("404 not found")
    exc.status_code = 404
    assert _is_retryable(exc) is False


def test_is_retryable_true_for_500():
    exc = Exception("500 server error")
    exc.status_code = 500
    assert _is_retryable(exc) is True


def test_is_retryable_true_for_503():
    exc = Exception("503 unavailable")
    exc.status_code = 503
    assert _is_retryable(exc) is True


# ---------------------------------------------------------------------------
# _retry_after_from
# ---------------------------------------------------------------------------

def test_retry_after_from_returns_none_for_plain_exception():
    assert _retry_after_from(ValueError("no header")) is None


def test_retry_after_from_parses_header_from_response():
    mock_response = MagicMock()
    mock_response.headers = {"Retry-After": "30"}
    exc = Exception("rate limited")
    exc.response = mock_response
    assert _retry_after_from(exc) == 30.0


def test_retry_after_from_returns_none_on_invalid_header():
    mock_response = MagicMock()
    mock_response.headers = {"Retry-After": "not-a-number"}
    exc = Exception("rate limited")
    exc.response = mock_response
    assert _retry_after_from(exc) is None


def test_retry_after_from_returns_none_when_no_response():
    exc = RetryableError("no response attr")
    assert _retry_after_from(exc) is None


# ---------------------------------------------------------------------------
# retry — success on first attempt
# ---------------------------------------------------------------------------

def test_retry_succeeds_on_first_call():
    calls = []
    def fn():
        calls.append(1)
        return "ok"
    result = retry(fn)
    assert result == "ok"
    assert len(calls) == 1


def test_retry_passes_args_and_kwargs():
    def fn(x, y=0):
        return x + y
    assert retry(fn, 3, y=4) == 7


# ---------------------------------------------------------------------------
# retry — retries on transient error then succeeds
# ---------------------------------------------------------------------------

def test_retry_retries_on_retryable_error(monkeypatch):
    monkeypatch.setattr("documentation_sync.resilience.time.sleep", lambda _: None)
    attempts = []
    def fn():
        attempts.append(1)
        if len(attempts) < 3:
            raise RetryableError("transient")
        return "done"
    result = retry(fn, max_retries=3, base_delay=0.0)
    assert result == "done"
    assert len(attempts) == 3


# ---------------------------------------------------------------------------
# retry — raises after max_retries
# ---------------------------------------------------------------------------

def test_retry_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr("documentation_sync.resilience.time.sleep", lambda _: None)
    def fn():
        raise RetryableError("always transient")
    with pytest.raises(RetryableError):
        retry(fn, max_retries=2, base_delay=0.0)


# ---------------------------------------------------------------------------
# retry — non-retryable error raised immediately
# ---------------------------------------------------------------------------

def test_retry_raises_immediately_for_non_retryable():
    def fn():
        raise ValueError("not retryable")
    with pytest.raises(ValueError):
        retry(fn, max_retries=5)


# ---------------------------------------------------------------------------
# retry — uses Retry-After header when present
# ---------------------------------------------------------------------------

def test_retry_uses_retry_after_header(monkeypatch):
    slept = []
    monkeypatch.setattr("documentation_sync.resilience.time.sleep",
                        lambda d: slept.append(d))
    attempts = []
    def fn():
        attempts.append(1)
        if len(attempts) == 1:
            exc = RetryableError("rate limited")
            mock_response = MagicMock()
            mock_response.headers = {"Retry-After": "2"}
            exc.response = mock_response
            raise exc
        return "ok"
    result = retry(fn, max_retries=2, base_delay=0.0, max_delay=60.0, jitter=0.0)
    assert result == "ok"
    assert any(s >= 1.9 for s in slept)  # Retry-After 2s (with jitter=0)


# ---------------------------------------------------------------------------
# retrying decorator
# ---------------------------------------------------------------------------

def test_retrying_decorator_wraps_function(monkeypatch):
    monkeypatch.setattr("documentation_sync.resilience.time.sleep", lambda _: None)
    calls = []

    @retrying(max_retries=2, base_delay=0.0)
    def my_func():
        calls.append(1)
        if len(calls) < 2:
            raise RetryableError("oops")
        return "wrapped ok"

    assert my_func() == "wrapped ok"
    assert len(calls) == 2


def test_retrying_preserves_function_name():
    @retrying()
    def my_named_function():
        return "x"
    assert my_named_function.__name__ == "my_named_function"


def test_retrying_raises_after_max_retries(monkeypatch):
    monkeypatch.setattr("documentation_sync.resilience.time.sleep", lambda _: None)

    @retrying(max_retries=1, base_delay=0.0)
    def always_fails():
        raise RetryableError("always")

    with pytest.raises(RetryableError):
        always_fails()

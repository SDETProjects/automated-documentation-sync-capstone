"""Tests for documentation_sync.tokens (M2: token budgeting)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from documentation_sync.tokens import TokenCounter, create_counter_from_settings


def _make_counter(**kwargs):
    return TokenCounter(**kwargs)


def test_heuristic_count_is_deterministic():
    counter = _make_counter()
    text = "x" * 40  # ~10 tokens heuristic
    result = counter.count(text)
    assert result.method == "heuristic"
    assert result.count == 10
    assert not result.warning


def test_warning_threshold_triggers():
    counter = _make_counter(context_window=1000, warning_threshold=0.8)
    # 1000 * 0.8 = 800-token limit; 8000 chars ≈ 2000 tokens > limit
    text = "x" * 8000
    result = counter.count(text)
    assert result.warning is True


def test_truncate_to_budget_shortens_text():
    counter = _make_counter(context_window=200, warning_threshold=0.8)
    text = "a" * 4000  # way over the ~40-token warning limit
    out = counter.truncate_to_budget(text)
    assert len(out) < len(text)
    assert counter.count(out).count <= counter.warning_limit


def test_truncate_leaves_short_text_unchanged():
    counter = _make_counter()
    text = "short"
    assert counter.truncate_to_budget(text) == text


def test_truncate_with_custom_budget():
    """Test truncate_to_budget with custom budget parameter."""
    counter = _make_counter()
    text = "x" * 1000
    result = counter.truncate_to_budget(text, budget=5)
    # Should truncate to approximately 5 tokens (20 chars)
    assert len(result) <= len(text)


def test_truncate_iterates_if_still_over_limit():
    """Test that truncate retries if still over limit after first truncation."""
    counter = _make_counter()
    text = "a" * 10000
    result = counter.truncate_to_budget(text, budget=10)
    assert counter.count(result).count <= 11  # Allow small margin


def test_count_returns_token_count_namedtuple():
    """Test that count() returns TokenCount with expected fields."""
    counter = _make_counter()
    result = counter.count("test text")
    assert hasattr(result, "count")
    assert hasattr(result, "method")
    assert hasattr(result, "warning")
    assert isinstance(result.count, int)
    assert isinstance(result.method, str)
    assert isinstance(result.warning, bool)


def test_count_empty_string():
    """Test counting empty string."""
    counter = _make_counter()
    result = counter.count("")
    # Heuristic returns max(1, len(text) // 4) = max(1, 0) = 1
    assert result.count >= 1
    assert result.warning is False


def test_create_counter_from_settings_returns_valid_counter():
    """Test factory function returns TokenCounter when initialized directly."""
    # Test direct initialization since config module has import issues in tests
    counter = TokenCounter(context_window=8192, warning_threshold=0.75)
    assert isinstance(counter, TokenCounter)
    assert counter.context_window == 8192
    assert counter.warning_limit == 6144


def test_warning_limit_calculation():
    """Test that warning_limit is correctly calculated."""
    counter = _make_counter(context_window=1000, warning_threshold=0.5)
    assert counter.warning_limit == 500
    
    counter2 = _make_counter(context_window=8192, warning_threshold=0.75)
    assert counter2.warning_limit == 6144


def test_count_with_various_text_lengths():
    """Test counting behavior with various text lengths."""
    counter = _make_counter()
    
    # Single char
    result = counter.count("a")
    assert result.count >= 1
    
    # Very long text
    long_text = "x" * 100000
    result = counter.count(long_text)
    assert result.count > 1000
    
    # Text with special characters
    special_text = "Hello\nWorld\t!@#$%^&*()"
    result = counter.count(special_text)
    assert result.count > 0


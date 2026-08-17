"""Tests for documentation_sync.forecast_calculator."""
import pytest

from documentation_sync.forecast_calculator import ProjectionResult, linear_extrapolate


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_linear_extrapolate_midperiod():
    """14 days elapsed of 31 — spend of 1000 → ~2214.29 projected."""
    result = linear_extrapolate(1000.0, 14, 31)
    assert isinstance(result, ProjectionResult)
    assert abs(result.projected_total - 2214.29) < 0.01


def test_linear_extrapolate_returns_exact_on_full_period():
    """When elapsed_days >= total_days the actual equals the projection."""
    result = linear_extrapolate(5000.0, 31, 31)
    assert result.projected_total == 5000.0
    assert "Full period elapsed" in result.confidence_note


def test_linear_extrapolate_zero_elapsed():
    """Day 0 — no elapsed data; projection equals spend_to_date."""
    result = linear_extrapolate(0.0, 0, 31)
    assert result.projected_total == 0.0
    assert "Day 0" in result.confidence_note


def test_linear_extrapolate_day_one():
    """First day of the month: extrapolate correctly."""
    result = linear_extrapolate(100.0, 1, 30)
    assert result.projected_total == 3000.0


def test_linear_extrapolate_confidence_note_contains_days():
    """confidence_note always references elapsed and total days."""
    result = linear_extrapolate(500.0, 10, 28)
    assert "10" in result.confidence_note
    assert "28" in result.confidence_note


def test_linear_extrapolate_rounds_to_two_decimal_places():
    """Result is rounded to 2 d.p. to avoid floating-point noise."""
    result = linear_extrapolate(1000.0, 7, 31)
    assert result.projected_total == round(1000.0 / 7 * 31, 2)


def test_linear_extrapolate_elapsed_greater_than_total():
    """elapsed_days > total_days: treated as full period elapsed."""
    result = linear_extrapolate(3000.0, 35, 31)
    assert result.projected_total == 3000.0
    assert "Full period elapsed" in result.confidence_note


def test_linear_extrapolate_zero_spend():
    """Zero spend to date → zero projection regardless of elapsed days."""
    result = linear_extrapolate(0.0, 15, 31)
    assert result.projected_total == 0.0


# ---------------------------------------------------------------------------
# Edge cases and guards
# ---------------------------------------------------------------------------

def test_linear_extrapolate_raises_on_zero_total_days():
    with pytest.raises(ValueError, match="total_days must be a positive integer"):
        linear_extrapolate(100.0, 5, 0)


def test_linear_extrapolate_raises_on_negative_total_days():
    with pytest.raises(ValueError):
        linear_extrapolate(100.0, 5, -1)


def test_linear_extrapolate_negative_elapsed_treated_as_zero():
    """Negative elapsed_days should behave as Day 0."""
    result = linear_extrapolate(100.0, -3, 31)
    assert result.projected_total == 100.0
    assert "Day 0" in result.confidence_note


def test_projection_result_dataclass_fields():
    pr = ProjectionResult(projected_total=1234.56, confidence_note="test")
    assert pr.projected_total == 1234.56
    assert pr.confidence_note == "test"

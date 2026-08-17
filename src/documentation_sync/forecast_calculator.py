"""Forecast calculation logic for projecting month-end spend totals.

Decoupled from chart rendering per NFR-4. Consumed by ForecastDataService
and SpendApiRouter; no imports from the rest of the pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectionResult:
    """The output of a spend projection calculation."""

    projected_total: float
    confidence_note: str


def linear_extrapolate(
    spend_to_date: float,
    elapsed_days: int,
    total_days: int,
) -> ProjectionResult:
    """Project the month-end total via linear extrapolation.

    Assumes a constant daily spend rate over the remaining days. Documents
    this assumption in ``confidence_note`` so callers can surface it in the UI
    (Assumption A2 from requirements).

    Args:
        spend_to_date: Total actual spend recorded so far in the period.
        elapsed_days:  Number of calendar days elapsed in the period (0-based).
        total_days:    Total calendar days in the period (e.g. 31 for August).

    Returns:
        A :class:`ProjectionResult` with the extrapolated total and a note
        describing the basis of the projection.

    Raises:
        ValueError: If ``total_days`` is not a positive integer.
    """
    if total_days <= 0:
        raise ValueError(f"total_days must be a positive integer, got {total_days!r}")

    # Guard: no data yet — cannot extrapolate; return spend as-is.
    if elapsed_days <= 0:
        return ProjectionResult(
            projected_total=round(spend_to_date, 2),
            confidence_note=f"Day 0 — no elapsed data (0 of {total_days} days)",
        )

    # Guard: period already complete — projection equals actual.
    if elapsed_days >= total_days:
        return ProjectionResult(
            projected_total=round(spend_to_date, 2),
            confidence_note=f"Full period elapsed ({elapsed_days} of {total_days} days)",
        )

    daily_rate = spend_to_date / elapsed_days
    projected = daily_rate * total_days
    return ProjectionResult(
        projected_total=round(projected, 2),
        confidence_note=(
            f"linear extrapolation, {elapsed_days} of {total_days} days elapsed"
        ),
    )

"""Risk flag evaluation logic for budget exceedance detection.

Decoupled from chart rendering per NFR-4 and the design-review policy:
no threshold comparison logic may exist in any frontend component.
Consumed by SpendApiRouter; all risk evaluation happens server-side.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskFlag:
    """The result of a risk evaluation against a budget threshold."""

    triggered: bool
    label: str


def evaluate(
    projected_total: float,
    budget: Optional[float],
    category: Optional[str] = None,
) -> Optional[RiskFlag]:
    """Evaluate whether a projected month-end total breaches a budget.

    Returns ``None`` when no budget is configured — this drives the FR-4
    graceful-degradation path (risk flags hidden when budgets are absent).

    Threshold condition is strict exceedance: ``projected_total > budget``
    (Assumption A5 from requirements).

    Args:
        projected_total: The extrapolated month-end total from
                         :func:`forecast_calculator.linear_extrapolate`.
        budget:          The configured budget threshold, or ``None`` if no
                         budget has been set.
        category:        Optional category name for the label string
                         (e.g. ``"engineering"``). When ``None``, the label
                         refers to the overall budget.

    Returns:
        - ``None`` if ``budget`` is ``None`` (no budget configured).
        - :class:`RiskFlag` with ``triggered=True`` when
          ``projected_total > budget``.
        - :class:`RiskFlag` with ``triggered=False`` when within budget.
    """
    if budget is None:
        return None

    scope = f"{category} budget" if category else "overall budget"
    triggered = projected_total > budget
    label = f"Projected spend exceeds {scope}" if triggered else ""
    return RiskFlag(triggered=triggered, label=label)

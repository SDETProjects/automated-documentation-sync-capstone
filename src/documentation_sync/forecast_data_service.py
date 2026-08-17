"""Data aggregation layer for spend records and budget configuration.

Reads from file-based JSON data stores (v1). The file paths are injected
via the constructor so unit tests can use tmp_path fixtures without touching
real data files.
"""
from __future__ import annotations

import calendar
import json
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List, Optional

from .forecast_calculator import ProjectionResult, linear_extrapolate


# Default data directory (relative to the repo root at runtime).
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"


@dataclass
class SpendRecord:
    """A single daily spend record."""

    date: str    # ISO format: YYYY-MM-DD
    amount: float


@dataclass
class BudgetConfig:
    """Budget configuration for overall and per-category spend."""

    overall: Optional[float] = None
    categories: List[dict] = field(default_factory=list)


class ForecastDataService:
    """Aggregates spend records and budget data for the forecast API.

    Args:
        data_dir: Path to the directory containing ``spend_records.json``
                  and ``budgets.json``. Defaults to the repo-level
                  ``data/`` directory. Override in tests with ``tmp_path``.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_actual_spend(self, period: str) -> List[SpendRecord]:
        """Return spend records for the given period (YYYY-MM).

        Args:
            period: Month in ``YYYY-MM`` format (e.g. ``"2026-08"``).

        Returns:
            List of :class:`SpendRecord` objects for that month, sorted by
            date ascending. Empty list if no records exist for the period.
        """
        all_records = self._load_spend_records()
        return sorted(
            [r for r in all_records if r.date.startswith(period)],
            key=lambda r: r.date,
        )

    def get_projected_month_end(
        self, period: str, category: Optional[str] = None
    ) -> ProjectionResult:
        """Compute the projected month-end total for a period.

        Delegates to :func:`forecast_calculator.linear_extrapolate` using
        actual spend-to-date and today's position in the period.

        Args:
            period:   Month in ``YYYY-MM`` format.
            category: Category ID to filter records; ``None`` for overall.

        Returns:
            A :class:`ProjectionResult` with the extrapolated total.
        """
        records = self.get_actual_spend(period)

        # Filter by category when requested (category stored in record label
        # field; plain records without a category are included in overall).
        if category:
            records = [
                r for r in records
                if getattr(r, "category", None) == category
            ]

        spend_to_date = sum(r.amount for r in records)
        today = date.today()

        try:
            year, month = int(period[:4]), int(period[5:7])
        except (ValueError, IndexError):
            # Fallback for invalid period; return spend as-is.
            return ProjectionResult(
                projected_total=round(spend_to_date, 2),
                confidence_note="invalid period format",
            )

        total_days = calendar.monthrange(year, month)[1]
        # elapsed_days = days gone by in the given month (capped to total_days).
        if today.year == year and today.month == month:
            elapsed_days = today.day
        elif date(year, month, 1) > today:
            elapsed_days = 0   # future month
        else:
            elapsed_days = total_days  # past month fully elapsed

        return linear_extrapolate(spend_to_date, elapsed_days, total_days)

    def get_budget_config(self, category: Optional[str] = None) -> Optional[float]:
        """Return the budget threshold for the given scope.

        Args:
            category: Category ID (e.g. ``"engineering"``), or ``None``
                      for the overall budget.

        Returns:
            The budget amount as a float, or ``None`` if not configured.
        """
        config = self._load_budget_config()
        if category is None:
            return config.overall

        for cat in config.categories:
            if cat.get("id") == category:
                return cat.get("budget")
        return None

    def get_all_budgets(self) -> BudgetConfig:
        """Return the full budget configuration object."""
        return self._load_budget_config()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_spend_records(self) -> List[SpendRecord]:
        spend_file = self._data_dir / "spend_records.json"
        if not spend_file.exists():
            return []
        with spend_file.open(encoding="utf-8") as f:
            raw = json.load(f)
        return [SpendRecord(date=r["date"], amount=float(r["amount"])) for r in raw]

    def _load_budget_config(self) -> BudgetConfig:
        budget_file = self._data_dir / "budgets.json"
        if not budget_file.exists():
            return BudgetConfig()
        with budget_file.open(encoding="utf-8") as f:
            raw = json.load(f)
        return BudgetConfig(
            overall=raw.get("overall"),
            categories=raw.get("categories", []),
        )

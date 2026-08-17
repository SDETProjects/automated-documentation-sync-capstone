"""Tests for documentation_sync.forecast_data_service."""
import json
from pathlib import Path

import pytest

from documentation_sync.forecast_data_service import (
    BudgetConfig,
    ForecastDataService,
    SpendRecord,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    """Populate a temporary data directory with sample JSON fixtures."""
    records = [
        {"date": "2026-08-01", "amount": 1000.00},
        {"date": "2026-08-02", "amount": 500.00},
        {"date": "2026-08-10", "amount": 750.00},
        {"date": "2026-07-15", "amount": 200.00},   # different month
    ]
    budgets = {
        "overall": 35000.00,
        "categories": [
            {"id": "engineering", "label": "Engineering", "budget": 15000.00},
            {"id": "marketing",   "label": "Marketing",   "budget": 8000.00},
        ],
    }
    (tmp_path / "spend_records.json").write_text(json.dumps(records), encoding="utf-8")
    (tmp_path / "budgets.json").write_text(json.dumps(budgets), encoding="utf-8")
    return tmp_path


@pytest.fixture
def svc(data_dir):
    return ForecastDataService(data_dir=data_dir)


@pytest.fixture
def empty_dir(tmp_path):
    """Data directory with no JSON files at all."""
    return tmp_path


# ---------------------------------------------------------------------------
# get_actual_spend
# ---------------------------------------------------------------------------

def test_get_actual_spend_filters_by_period(svc):
    records = svc.get_actual_spend("2026-08")
    assert len(records) == 3
    assert all(r.date.startswith("2026-08") for r in records)


def test_get_actual_spend_excludes_other_months(svc):
    records = svc.get_actual_spend("2026-07")
    assert len(records) == 1
    assert records[0].date == "2026-07-15"


def test_get_actual_spend_returns_empty_for_unknown_period(svc):
    records = svc.get_actual_spend("2025-01")
    assert records == []


def test_get_actual_spend_sorted_by_date(svc):
    records = svc.get_actual_spend("2026-08")
    dates = [r.date for r in records]
    assert dates == sorted(dates)


def test_get_actual_spend_returns_spend_records(svc):
    records = svc.get_actual_spend("2026-08")
    assert all(isinstance(r, SpendRecord) for r in records)


def test_get_actual_spend_empty_when_no_file(empty_dir):
    svc = ForecastDataService(data_dir=empty_dir)
    assert svc.get_actual_spend("2026-08") == []


# ---------------------------------------------------------------------------
# get_projected_month_end
# ---------------------------------------------------------------------------

def test_get_projected_month_end_returns_projection_result(svc):
    from documentation_sync.forecast_calculator import ProjectionResult
    result = svc.get_projected_month_end("2026-08")
    assert isinstance(result, ProjectionResult)


def test_get_projected_month_end_nonzero_when_records_exist(svc):
    result = svc.get_projected_month_end("2026-08")
    assert result.projected_total > 0


def test_get_projected_month_end_zero_when_no_records(svc):
    result = svc.get_projected_month_end("2025-01")
    assert result.projected_total == 0.0


def test_get_projected_month_end_invalid_period_returns_gracefully(svc):
    result = svc.get_projected_month_end("not-a-date")
    assert result.projected_total >= 0  # no exception raised


# ---------------------------------------------------------------------------
# get_budget_config
# ---------------------------------------------------------------------------

def test_get_budget_config_overall(svc):
    assert svc.get_budget_config(None) == 35000.00


def test_get_budget_config_known_category(svc):
    assert svc.get_budget_config("engineering") == 15000.00


def test_get_budget_config_marketing(svc):
    assert svc.get_budget_config("marketing") == 8000.00


def test_get_budget_config_unknown_category_returns_none(svc):
    assert svc.get_budget_config("hr") is None


def test_get_budget_config_returns_none_when_no_file(empty_dir):
    svc = ForecastDataService(data_dir=empty_dir)
    assert svc.get_budget_config(None) is None


# ---------------------------------------------------------------------------
# get_all_budgets
# ---------------------------------------------------------------------------

def test_get_all_budgets_returns_budget_config(svc):
    config = svc.get_all_budgets()
    assert isinstance(config, BudgetConfig)
    assert config.overall == 35000.00
    assert len(config.categories) == 2


def test_get_all_budgets_empty_when_no_file(empty_dir):
    svc = ForecastDataService(data_dir=empty_dir)
    config = svc.get_all_budgets()
    assert config.overall is None
    assert config.categories == []

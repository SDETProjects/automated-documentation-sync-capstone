"""Integration tests for the full forecast pipeline (Task 9).

Spins up the Flask app with a temporary data directory and exercises the
complete request path: SpendApiRouter → ForecastDataService →
ForecastCalculator + RiskFlagEvaluator → JSON response.

Mirrors the API contract specified in claude-architecture.md.
"""
import json

import pytest

pytest.importorskip("flask", reason="Flask required for integration tests")

from documentation_sync.spend_api_router import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_data_dir(tmp_path):
    """Dataset where projected total EXCEEDS the overall budget."""
    # Use a PAST month (2025-08) so elapsed_days = total_days = 31.
    # 31 days @ 1000/day → projection = 31000 > budget 28000 → should trigger flag.
    records = [{"date": f"2025-08-{i:02d}", "amount": 1000.0} for i in range(1, 32)]
    budgets = {
        "overall": 28000.00,
        "categories": [
            {"id": "engineering", "label": "Engineering", "budget": 12000.00},
        ],
    }
    (tmp_path / "spend_records.json").write_text(json.dumps(records), encoding="utf-8")
    (tmp_path / "budgets.json").write_text(json.dumps(budgets), encoding="utf-8")
    return tmp_path


@pytest.fixture
def under_budget_dir(tmp_path):
    """Dataset where projected total stays WITHIN budget."""
    records = [{"date": f"2026-08-{i:02d}", "amount": 100.0} for i in range(1, 15)]
    budgets = {"overall": 50000.00, "categories": []}
    (tmp_path / "spend_records.json").write_text(json.dumps(records), encoding="utf-8")
    (tmp_path / "budgets.json").write_text(json.dumps(budgets), encoding="utf-8")
    return tmp_path


@pytest.fixture
def no_budget_dir(tmp_path):
    """Dataset with spend records but NO budget configuration."""
    records = [{"date": "2026-08-01", "amount": 500.0}]
    (tmp_path / "spend_records.json").write_text(json.dumps(records), encoding="utf-8")
    # No budgets.json
    return tmp_path


def _client(data_dir):
    app = create_app(data_dir=data_dir)
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# Full-pipeline integration: forecast response structure
# ---------------------------------------------------------------------------

def test_integration_forecast_full_response_structure(full_data_dir):
    """Verify every field from the API contract is present."""
    with _client(full_data_dir) as c:
        resp = c.get("/api/spend/forecast?period=2025-08")
    assert resp.status_code == 200
    data = resp.get_json()

    required_keys = {"period", "category", "actual_spend", "projected_total",
                     "confidence_note", "budget", "risk_flag"}
    assert required_keys.issubset(data.keys()), (
        f"Missing keys: {required_keys - data.keys()}"
    )


def test_integration_actual_spend_records_count(full_data_dir):
    """31 records in fixture → 31 actual_spend entries."""
    with _client(full_data_dir) as c:
        data = c.get("/api/spend/forecast?period=2025-08").get_json()
    assert len(data["actual_spend"]) == 31


def test_integration_actual_spend_record_shape(full_data_dir):
    """Each actual_spend entry has 'date' and 'amount'."""
    with _client(full_data_dir) as c:
        data = c.get("/api/spend/forecast?period=2025-08").get_json()
    for rec in data["actual_spend"]:
        assert "date" in rec and "amount" in rec


# ---------------------------------------------------------------------------
# Risk flag: exceeded budget
# ---------------------------------------------------------------------------

def test_integration_risk_flag_triggered_when_projection_exceeds_budget(full_data_dir):
    """31 days * 1000/day → projection = 31000 > budget 28000 → flag triggered."""
    with _client(full_data_dir) as c:
        data = c.get("/api/spend/forecast?period=2025-08").get_json()
    assert data["risk_flag"] is not None
    assert data["risk_flag"]["triggered"] is True
    assert data["risk_flag"]["label"] != ""


# ---------------------------------------------------------------------------
# Risk flag: within budget
# ---------------------------------------------------------------------------

def test_integration_risk_flag_not_triggered_when_within_budget(under_budget_dir):
    """100/day * 14 days → projection ≈ 3100 < budget 50000 → flag not triggered."""
    with _client(under_budget_dir) as c:
        data = c.get("/api/spend/forecast?period=2026-08").get_json()
    assert data["risk_flag"] is not None
    assert data["risk_flag"]["triggered"] is False


# ---------------------------------------------------------------------------
# Risk flag: no budget (FR-4 graceful degradation)
# ---------------------------------------------------------------------------

def test_integration_risk_flag_null_when_no_budget(no_budget_dir):
    """When no budgets.json exists, risk_flag must be null."""
    with _client(no_budget_dir) as c:
        data = c.get("/api/spend/forecast?period=2026-08").get_json()
    assert data["risk_flag"] is None


# ---------------------------------------------------------------------------
# GET /api/spend/budgets integration
# ---------------------------------------------------------------------------

def test_integration_budgets_endpoint_returns_correct_structure(full_data_dir):
    with _client(full_data_dir) as c:
        data = c.get("/api/spend/budgets").get_json()
    assert data["overall"] == 28000.00
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == "engineering"


def test_integration_budgets_empty_when_no_config(no_budget_dir):
    with _client(no_budget_dir) as c:
        data = c.get("/api/spend/budgets").get_json()
    assert data["overall"] is None
    assert data["categories"] == []


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_integration_400_for_missing_period(full_data_dir):
    with _client(full_data_dir) as c:
        resp = c.get("/api/spend/forecast")
    assert resp.status_code == 400


def test_integration_400_for_invalid_period(full_data_dir):
    with _client(full_data_dir) as c:
        resp = c.get("/api/spend/forecast?period=2026/08")
    assert resp.status_code == 400


def test_integration_404_for_empty_period(no_budget_dir):
    """Period with no records → 404."""
    with _client(no_budget_dir) as c:
        resp = c.get("/api/spend/forecast?period=2025-01")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# No regressions on existing pipeline
# ---------------------------------------------------------------------------

def test_existing_models_still_importable():
    """Confirm the new modules do not break existing package imports."""
    from documentation_sync.models import JiraStory, Requirement, RequirementSet
    from documentation_sync.generator import build_requirement_set

    story = JiraStory(
        key="TEST-1",
        summary="Test",
        description="As a user I want things.",
        acceptance_criteria=["AC1"],
    )
    req_set = build_requirement_set(story)
    assert req_set.story.key == "TEST-1"

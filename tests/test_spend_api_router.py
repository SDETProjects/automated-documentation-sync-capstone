"""Tests for documentation_sync.spend_api_router (Flask test client)."""
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("flask", reason="Flask required for spend_api_router tests")

from documentation_sync.spend_api_router import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    records = [
        {"date": "2026-08-01", "amount": 1200.00},
        {"date": "2026-08-07", "amount": 980.00},
        {"date": "2026-08-14", "amount": 1050.00},
    ]
    budgets = {
        "overall": 35000.00,
        "categories": [
            {"id": "engineering", "label": "Engineering", "budget": 15000.00},
        ],
    }
    (tmp_path / "spend_records.json").write_text(json.dumps(records), encoding="utf-8")
    (tmp_path / "budgets.json").write_text(json.dumps(budgets), encoding="utf-8")
    return tmp_path


@pytest.fixture
def client(data_dir):
    app = create_app(data_dir=data_dir)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def empty_data_dir(tmp_path):
    return tmp_path


@pytest.fixture
def client_no_data(empty_data_dir):
    app = create_app(data_dir=empty_data_dir)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/spend/forecast — happy path
# ---------------------------------------------------------------------------

def test_forecast_returns_200_for_valid_period(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert resp.status_code == 200


def test_forecast_response_contains_required_fields(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    data = resp.get_json()
    for key in ("period", "actual_spend", "projected_total", "budget", "risk_flag"):
        assert key in data, f"Missing key: {key}"


def test_forecast_period_echoed_in_response(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert resp.get_json()["period"] == "2026-08"


def test_forecast_actual_spend_is_list(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert isinstance(resp.get_json()["actual_spend"], list)


def test_forecast_projected_total_positive(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert resp.get_json()["projected_total"] > 0


def test_forecast_budget_present_when_configured(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert resp.get_json()["budget"] == 35000.00


def test_forecast_confidence_note_in_response(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert "confidence_note" in resp.get_json()


# ---------------------------------------------------------------------------
# GET /api/spend/forecast — category view
# ---------------------------------------------------------------------------

def test_forecast_category_param_echoed(client):
    resp = client.get("/api/spend/forecast?period=2026-08&category=engineering")
    data = resp.get_json()
    assert data["category"] == "engineering"


def test_forecast_overall_category_null(client):
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert resp.get_json()["category"] is None


# ---------------------------------------------------------------------------
# GET /api/spend/forecast — error paths
# ---------------------------------------------------------------------------

def test_forecast_missing_period_returns_400(client):
    resp = client.get("/api/spend/forecast")
    assert resp.status_code == 400


def test_forecast_invalid_period_format_returns_400(client):
    resp = client.get("/api/spend/forecast?period=08-2026")
    assert resp.status_code == 400


def test_forecast_invalid_period_error_message(client):
    resp = client.get("/api/spend/forecast?period=invalid")
    assert "error" in resp.get_json()


def test_forecast_unknown_period_returns_404(client):
    resp = client.get("/api/spend/forecast?period=2099-01")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/spend/forecast — risk flag
# ---------------------------------------------------------------------------

def test_forecast_risk_flag_present_when_budget_configured(client):
    """risk_flag is not None when budget is configured."""
    resp = client.get("/api/spend/forecast?period=2026-08")
    data = resp.get_json()
    # budget exists → risk_flag should be a dict (not null)
    assert data["risk_flag"] is not None
    assert "triggered" in data["risk_flag"]
    assert "label" in data["risk_flag"]


def test_forecast_risk_flag_null_when_no_budget(client_no_data, tmp_path):
    """risk_flag is null when no budgets.json exists."""
    # Put only spend records, no budgets.
    records = [{"date": "2026-08-01", "amount": 500.0}]
    (tmp_path / "spend_records.json").write_text(json.dumps(records), encoding="utf-8")
    app = create_app(data_dir=tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        resp = c.get("/api/spend/forecast?period=2026-08")
        assert resp.get_json()["risk_flag"] is None


# ---------------------------------------------------------------------------
# GET /api/spend/budgets
# ---------------------------------------------------------------------------

def test_budgets_returns_200(client):
    resp = client.get("/api/spend/budgets")
    assert resp.status_code == 200


def test_budgets_response_structure(client):
    data = resp = client.get("/api/spend/budgets").get_json()
    assert "overall" in data
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_budgets_overall_value(client):
    data = client.get("/api/spend/budgets").get_json()
    assert data["overall"] == 35000.00


def test_budgets_categories_list(client):
    data = client.get("/api/spend/budgets").get_json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == "engineering"


def test_budgets_empty_when_no_file(client_no_data):
    data = client_no_data.get("/api/spend/budgets").get_json()
    assert data["overall"] is None
    assert data["categories"] == []


# ---------------------------------------------------------------------------
# Authentication (Design Review revision item 1)
# ---------------------------------------------------------------------------

def test_auth_returns_401_when_api_key_required_and_missing(data_dir, monkeypatch):
    monkeypatch.setenv("SPEND_API_KEY", "secret-key")
    app = create_app(data_dir=data_dir)
    app.config["TESTING"] = True
    with app.test_client() as c:
        resp = c.get("/api/spend/forecast?period=2026-08")
        assert resp.status_code == 401


def test_auth_returns_401_with_wrong_key(data_dir, monkeypatch):
    monkeypatch.setenv("SPEND_API_KEY", "secret-key")
    app = create_app(data_dir=data_dir)
    app.config["TESTING"] = True
    with app.test_client() as c:
        resp = c.get(
            "/api/spend/forecast?period=2026-08",
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401


def test_auth_returns_200_with_correct_key(data_dir, monkeypatch):
    monkeypatch.setenv("SPEND_API_KEY", "secret-key")
    app = create_app(data_dir=data_dir)
    app.config["TESTING"] = True
    with app.test_client() as c:
        resp = c.get(
            "/api/spend/forecast?period=2026-08",
            headers={"X-API-Key": "secret-key"},
        )
        assert resp.status_code == 200


def test_auth_skipped_when_no_env_var(client):
    """When SPEND_API_KEY is unset, requests succeed without a header."""
    # client fixture does NOT set SPEND_API_KEY — default test env.
    resp = client.get("/api/spend/forecast?period=2026-08")
    assert resp.status_code == 200


def test_auth_401_response_body(data_dir, monkeypatch):
    monkeypatch.setenv("SPEND_API_KEY", "secret-key")
    app = create_app(data_dir=data_dir)
    app.config["TESTING"] = True
    with app.test_client() as c:
        resp = c.get("/api/spend/forecast?period=2026-08")
        assert resp.get_json() == {"error": "unauthorized"}

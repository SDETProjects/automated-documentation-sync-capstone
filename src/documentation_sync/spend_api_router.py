"""REST API router for spend forecast and budget data.

Exposes two endpoints consumed by the ForecastChartComponent frontend:
  GET /api/spend/forecast  — actual spend + projected total + risk flag
  GET /api/spend/budgets   — overall + category budget configuration

Authentication (Design Review revision item 1):
  When the SPEND_API_KEY environment variable is set, every request must
  include an ``X-API-Key`` header matching that value. A 401 is returned
  otherwise.  When SPEND_API_KEY is unset the server operates in dev mode
  (no auth required; bind to 127.0.0.1 in production).

Usage:
    from documentation_sync.spend_api_router import create_app
    app = create_app()
    app.run(host="127.0.0.1", port=5050)

    # Or for tests:
    client = app.test_client()
"""
from __future__ import annotations

import os
import re
from functools import wraps
from typing import Optional

try:
    from flask import Flask, jsonify, request
    _FLASK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FLASK_AVAILABLE = False

from .forecast_data_service import ForecastDataService
from .risk_flag_evaluator import evaluate as evaluate_risk


# Valid period format: YYYY-MM
_PERIOD_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


def _validate_period(period: Optional[str]) -> Optional[str]:
    """Return an error string if period is invalid, else None."""
    if not period:
        return "period query parameter is required (format: YYYY-MM)"
    if not _PERIOD_RE.match(period):
        return f"invalid period format {period!r}; expected YYYY-MM"
    return None


def create_app(data_dir=None) -> "Flask":
    """Create and configure the Flask application.

    Args:
        data_dir: Optional path to the data directory.  Passed to
                  :class:`ForecastDataService`; useful for tests.

    Returns:
        A configured Flask :class:`~flask.Flask` instance.

    Raises:
        ImportError: If Flask is not installed.
    """
    if not _FLASK_AVAILABLE:  # pragma: no cover
        raise ImportError(
            "Flask is required for the spend API. "
            "Install it with: pip install flask"
        )

    app = Flask(__name__)
    svc = ForecastDataService(data_dir=data_dir)

    # ------------------------------------------------------------------
    # Auth middleware
    # ------------------------------------------------------------------

    def require_api_key(f):
        """Decorator: enforce X-API-Key when SPEND_API_KEY env var is set."""
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = os.environ.get("SPEND_API_KEY")
            if api_key:
                provided = request.headers.get("X-API-Key", "")
                if provided != api_key:
                    return jsonify({"error": "unauthorized"}), 401
            return f(*args, **kwargs)
        return decorated

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/api/spend/forecast", methods=["GET"])
    @require_api_key
    def get_forecast():
        """Return actual spend, projected total, and risk flag for a period.

        Query params:
            period   (required) YYYY-MM
            category (optional) category ID for per-category view
        """
        period = request.args.get("period")
        error = _validate_period(period)
        if error:
            return jsonify({"error": error}), 400

        category = request.args.get("category") or None

        records = svc.get_actual_spend(period)
        if not records:
            return jsonify({"error": f"no spend data for period {period!r}"}), 404

        projection = svc.get_projected_month_end(period, category)
        budget = svc.get_budget_config(category)
        risk_flag = evaluate_risk(projection.projected_total, budget, category)

        actual_spend = [{"date": r.date, "amount": r.amount} for r in records]
        risk_flag_payload = (
            {"triggered": risk_flag.triggered, "label": risk_flag.label}
            if risk_flag is not None
            else None
        )

        return jsonify(
            {
                "period": period,
                "category": category,
                "actual_spend": actual_spend,
                "projected_total": projection.projected_total,
                "confidence_note": projection.confidence_note,
                "budget": budget,
                "risk_flag": risk_flag_payload,
            }
        )

    @app.route("/api/spend/budgets", methods=["GET"])
    @require_api_key
    def get_budgets():
        """Return overall and per-category budget configuration."""
        config = svc.get_all_budgets()
        return jsonify(
            {
                "overall": config.overall,
                "categories": config.categories,
            }
        )

    return app


if __name__ == "__main__":  # pragma: no cover
    _app = create_app()
    _app.run(host="127.0.0.1", port=5050, debug=False)

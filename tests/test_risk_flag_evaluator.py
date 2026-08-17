"""Tests for documentation_sync.risk_flag_evaluator."""
from documentation_sync.risk_flag_evaluator import RiskFlag, evaluate


# ---------------------------------------------------------------------------
# No budget configured (FR-4 graceful degradation)
# ---------------------------------------------------------------------------

def test_evaluate_returns_none_when_no_budget():
    """When budget is None, evaluate must return None — no flags shown."""
    result = evaluate(15000.0, None)
    assert result is None


def test_evaluate_returns_none_when_no_budget_with_category():
    result = evaluate(15000.0, None, category="engineering")
    assert result is None


# ---------------------------------------------------------------------------
# Budget exceeded (FR-2: risk flag triggered)
# ---------------------------------------------------------------------------

def test_evaluate_triggers_flag_when_projection_exceeds_budget():
    result = evaluate(15001.0, 15000.0)
    assert isinstance(result, RiskFlag)
    assert result.triggered is True
    assert "overall budget" in result.label


def test_evaluate_triggers_flag_with_category_label():
    result = evaluate(8001.0, 8000.0, category="marketing")
    assert result.triggered is True
    assert "marketing" in result.label


def test_evaluate_label_mentions_budget_scope_overall():
    result = evaluate(100.0, 50.0)
    assert "overall budget" in result.label


def test_evaluate_label_mentions_category_name():
    result = evaluate(100.0, 50.0, category="operations")
    assert "operations" in result.label


# ---------------------------------------------------------------------------
# Within budget (flag exists but not triggered)
# ---------------------------------------------------------------------------

def test_evaluate_not_triggered_when_equal_to_budget():
    """Strict exceedance: equal to budget is NOT a flag (Assumption A5)."""
    result = evaluate(15000.0, 15000.0)
    assert isinstance(result, RiskFlag)
    assert result.triggered is False
    assert result.label == ""


def test_evaluate_not_triggered_when_below_budget():
    result = evaluate(14999.0, 15000.0)
    assert result.triggered is False


# ---------------------------------------------------------------------------
# Boundary values
# ---------------------------------------------------------------------------

def test_evaluate_zero_projected_zero_budget():
    """Zero projected against zero budget: not triggered (0 is not > 0)."""
    result = evaluate(0.0, 0.0)
    assert result.triggered is False


def test_evaluate_very_small_exceedance():
    """Even a 0.01 exceedance should trigger the flag."""
    result = evaluate(15000.01, 15000.0)
    assert result.triggered is True


def test_risk_flag_dataclass_fields():
    flag = RiskFlag(triggered=True, label="test label")
    assert flag.triggered is True
    assert flag.label == "test label"

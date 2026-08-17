# Tests

Test suite for the Automated Documentation Sync package. Uses **pytest** with **≥80% coverage** enforced.

## Quick Start

```bash
# Run all tests with coverage
pytest -q --cov=src/documentation_sync --cov-report=term-missing

# Run a specific test module
pytest tests/test_generator.py -v

# Run with HTML coverage report
pytest --cov=src/documentation_sync --cov-report=html
```

## Test Organization

| Test Module | Coverage Target |
|-------------|-----------------|
| `test_parser.py` | JSON/Markdown story loading, validation errors |
| `test_validator.py` | Story & requirement set validation |
| `test_generator.py` | Artifact generation, traceability enforcement |
| `test_doc_validator.py` | Document quality checks (sections, headings, traceability, parity) |
| `test_phased_generator.py` | Phased generation, checkpoints, resume, rollback |
| `test_checkpoint.py` | Checkpoint save/load/atomic writes |
| `test_input_handler.py` | Jira URL/key/text ingestion, auth, fallback |
| `test_jira_connector.py` | Jira REST client (mocked) |
| `test_jira_mcp_server.py` | MCP server tools |
| `test_llm_orchestrator.py` | Clarifying questions, feedback incorporation |
| `test_providers.py` | LLM adapters (Claude, offline heuristic) |
| `test_tokens.py` | Token counting, budget, truncation |
| `test_resilience.py` | Retry, backoff, circuit breaker |
| `test_config.py` | Settings load order, schema validation, env overrides |
| `test_forecast_calculator.py` | `linear_extrapolate()` edge cases |
| `test_forecast_data_service.py` | Spend records, budgets, projections |
| `test_risk_flag_evaluator.py` | Budget exceedance logic, None handling |
| `test_spend_api_router.py` | Flask endpoints, auth, validation |
| `test_forecast_integration.py` | End-to-end forecast flow |
| `test_integration.py` | Full CLI → artifacts → verify pipeline |
| `test_traceability.py` | Cross-artifact ID consistency |
| `test_log.py` | Structured logging output |
| `test_input_handler.py` | Input loading edge cases |

## Fixtures (conftest.py)

Common fixtures are defined in `tests/conftest.py`:

| Fixture | Purpose |
|---------|---------|
| `sample_story` | `JiraStory` from `samples/jira_story.json` |
| `temp_dir` | `tmp_path` fixture for isolated output dirs |
| `mock_jira_response` | Mocked `requests.Response` for Jira API |
| `forecast_data_service` | `ForecastDataService` with tmp data files |

## Mocking Strategy

- **External HTTP**: `responses` or `unittest.mock.patch` on `requests.get/post`
- **Jira API**: `tests/test_jira_connector.py` shows the pattern — mock `requests.Session`
- **LLM calls**: `providers.LLMManager` adapters are swappable; tests use `OfflineHeuristicAdapter`
- **Flask**: `spend_api_router.create_app(data_dir=tmp_path)` for isolated test client

## Coverage Requirements

| Metric | Threshold | Enforced By |
|--------|-----------|-------------|
| Overall coverage | ≥80% | `pyproject.toml` → `tool.coverage.report.fail_under = 80` |
| Branch coverage | Not enforced | — |

Run coverage locally:
```bash
pytest --cov=src/documentation_sync --cov-report=term-missing
```

CI runs the same command via `.github/workflows/tests.yml`.

## Test Patterns

### Happy Path
```python
def test_generate_requirements_md(sample_story):
    req_set = build_requirement_set(sample_story)
    md = generate_requirements_md(req_set)
    assert "US-1" in md
    assert "FR-1" in md
```

### Error Conditions
```python
def test_validator_rejects_missing_key():
    story = JiraStory(key="", summary="x", description="y", acceptance_criteria=[])
    with pytest.raises(ValidationError):
        ensure_valid_story(story)
```

### Parametrized
```python
@pytest.mark.parametrize("period,expected_days", [
    ("2026-01", 31), ("2026-02", 28), ("2024-02", 29),
])
def test_month_days(period, expected_days):
    assert calendar.monthrange(int(period[:4]), int(period[5:7]))[1] == expected_days
```

### Integration (CLI → artifacts → verify)
```python
def test_full_pipeline(tmp_path, sample_story):
    # Write story file
    story_file = tmp_path / "story.json"
    story_file.write_text(json.dumps(sample_story.__dict__))
    
    # Run CLI
    result = run_cli([str(story_file), "-o", str(tmp_path / "out")])
    assert result == 0
    
    # Verify
    report = validate_artifacts(tmp_path / "out", story_path=story_file)
    assert report.ok
```

## Adding Tests

1. Create `tests/test_<module>.py` following existing naming
2. Import from `src.documentation_sync` (pythonpath set in `pyproject.toml`)
3. Use `tmp_path` for filesystem isolation
4. Mock external dependencies
5. Run `pytest tests/test_<module>.py -v` to verify

## Common Issues

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: documentation_sync` | `pip install -e .` from repo root |
| `ImportError: cannot import name 'X'` | Check `__init__.py` exports; module may be private |
| Coverage <80% | Run with `--cov-report=term-missing` to find gaps; add tests for uncovered lines |
| Flaky Jira tests | Ensure `responses` or `mock` fully intercepts `requests`; no real network calls |
# documentation_sync Package

Core Python package for Automated Documentation Sync. Provides CLI, programmatic API, Jira integration, artifact generation, validation, and a spend forecast API.

## Public API

### CLI Entry Points

| Function | Module | Installed As |
|----------|--------|--------------|
| `main()` | `cli` | `docsync` |
| `main()` | `doc_validator` | `docsync-verify` |
| `create_app()` | `spend_api_router` | — (programmatic) |

### Programmatic Usage

```python
from documentation_sync import (
    load_story,
    build_requirement_set,
    write_all_artifacts,
    validate_artifacts,
    ForecastDataService,
    create_app,  # Flask app for spend API
)

# Load story from file, URL, or text
story = load_story("samples/jira_story.json")

# Build requirements (US-1, FR-n, NFR-1)
req_set = build_requirement_set(story)

# Generate all 9 artifacts
paths = write_all_artifacts(req_set, output_dir="out")

# Verify artifacts
report = validate_artifacts("out", story_path="samples/jira_story.json")
assert report.ok

# Spend forecast API
svc = ForecastDataService(data_dir="data")
projection = svc.get_projected_month_end("2026-08")
budgets = svc.get_all_budgets()

# Or run Flask server
app = create_app()
app.run(host="127.0.0.1", port=5050)
```

## Module Overview

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Argument parsing, orchestration, Jira fallback, phased generation entry |
| `config.py` | Centralized `Settings` (file → env → defaults), JSON Schema validation |
| `models.py` | `JiraStory`, `Requirement`, `RequirementSet` dataclasses |
| `parser.py` | JSON/Markdown story loading (`load_story`, `load_story_from_any_source`) |
| `validator.py` | Story & requirement set validation (`ensure_valid_story`, `ensure_valid_requirement_set`) |
| `generator.py` | One-shot artifact generation (`build_requirement_set`, `write_all_artifacts`) |
| `phased_generator.py` | Interactive 4-phase generation with checkpoints (`run_phased_generation`) |
| `checkpoint.py` | Checkpoint save/load/rollback for phased runs (`.docsync_checkpoint.json`) |
| `doc_validator.py` | Artifact quality checks (sections, headings, traceability, story parity) |
| `input_handler.py` | Jira URL/key/text ingestion with auth config, fallback to pasted text |
| `jira_connector.py` | `requests`-based Jira REST client (issue fetch, field mapping) |
| `jira_mcp_server.py` | Custom MCP server (4 tools: fetch, run_pipeline, status, validate) |
| `llm_orchestrator.py` | Clarifying question generation, feedback incorporation, user input waits |
| `providers.py` | LLM adapter pattern (Claude, Copilot placeholder, offline heuristic) |
| `tokens.py` | Token counting, budget enforcement, context truncation |
| `resilience.py` | Retry/backoff, circuit breaker for external calls |
| `forecast_calculator.py` | `linear_extrapolate()` — pure projection logic |
| `forecast_data_service.py` | `ForecastDataService` — aggregates spend records + budgets |
| `risk_flag_evaluator.py` | `evaluate()` — server-side budget exceedance logic (RiskFlag) |
| `spend_api_router.py` | Flask app with `/api/spend/forecast`, `/api/spend/budgets` (+ auth) |
| `log.py` | Structured logging setup |

## Configuration

`Settings` loads from (in precedence order):

1. Hard-coded defaults in `config.py`
2. `docsync.config.json` (validated against `docsync.config.schema.json`)
3. `DOCSYNC_*` environment variables

### Example Config

```json
{
  "jira_base_url": "https://jiraeu.epam.com",
  "llm": {
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 512,
    "max_retries": 3
  },
  "logging_level": "INFO",
  "mcp_api_key": "shared-secret",
  "mcp_rate_limit_per_minute": 60,
  "max_context_tokens": 200000
}
```

### Env Overrides

| Env Var | Maps To |
|---------|---------|
| `JIRA_BASE_URL` | `jira_base_url` |
| `DOCSYNC_LOG_LEVEL` | `logging_level` |
| `DOCSYNC_MCP_API_KEY` | `mcp_api_key` |
| `DOCSYNC_LLM_MODEL` | `llm.model` |
| `DOCSYNC_LLM_MAX_RETRIES` | `llm.max_retries` |

## Data Files (Forecast API)

The `ForecastDataService` reads two JSON files from `data_dir` (default: repo root `data/`):

### `spend_records.json`
```json
[
  { "date": "2026-08-01", "amount": 1200.00 },
  { "date": "2026-08-02", "amount": 980.50 }
]
```

### `budgets.json`
```json
{
  "overall": 35000.00,
  "categories": [
    { "id": "engineering", "label": "Engineering", "budget": 15000.00 },
    { "id": "marketing", "label": "Marketing", "budget": 8000.00 }
  ]
}
```

## Traceability Rules

- **IDs are generated from the story**: `US-1` (summary), `FR-1..n` (each acceptance criterion), `NFR-1` (doc quality)
- **IDs are immutable**: Prose may be edited; IDs must not drift
- **Generator enforces traceability**: `assert_traceable()` fails fast if an artifact cites unknown IDs
- **Verifier enforces parity**: `docsync-verify --story` ensures `FR-n` count matches acceptance criteria exactly

## Extending the Package

### Add a New Artifact Generator

1. Add a `generate_<name>_md(req_set)` function in `generator.py`
2. Add the filename + required sections to `REQUIRED_SECTIONS` in `doc_validator.py`
3. Add to `TRACEABILITY_REQUIRED` if it must cite requirement IDs
4. Add to `artifacts` dict in `write_all_artifacts()`
5. Add tests in `tests/test_generator.py` and `tests/test_doc_validator.py`

### Add a New LLM Provider

1. Implement `LLMAdapter` protocol in `providers.py`
2. Register in `LLMManager._adapters`
3. Ensure `is_available()` returns `True` when credentials exist

---

## Testing

```bash
# All tests
pytest -q --cov=src/documentation_sync --cov-report=term-missing

# Specific module
pytest tests/test_generator.py -v

# With coverage detail
pytest --cov=src/documentation_sync --cov-report=html
```

Coverage target: **≥80%** (enforced in `pyproject.toml`).
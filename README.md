# Automated Documentation Sync

**Automated Documentation Sync** turns a Jira-style story into traceable SDLC artifacts and provides verification checks to keep requirements, architecture, review notes, and release documentation aligned.

This repository supports two distinct workflows:

1. **A product workflow**: the `docsync` CLI and Python package in `src/documentation_sync/`.
2. **An authoring workflow**: GitHub Copilot Chat and Claude-based SDLC pipelines that produce reviewable artifacts.

---

## Repository Guide

| Guide | Purpose |
|-------|---------|
| `README.md` (this file) | Overall project: CLI, installation, features, output locations |
| `.github/README.md` | GitHub Copilot workflow: prompts, running steps, verification |
| `.claude/README.md` | Claude Code workflow: commands, agents, MCP, hooks |
| `docs/copilot-operating-model.md` | Deep dive on how Copilot + CLI divide labor |
| `CLAUDE.md` | Copilot pipeline rules and gates |
| `.claude/CLAUDE.md` | Claude Code pipeline rules and gates |

---

## What The Product Does

1. Accepts story input as a local JSON file, Markdown file, full Jira URL, bare Jira issue key, or pasted text.
2. Normalizes the story into a structured model with title, description, acceptance criteria, and metadata.
3. Generates SDLC artifacts with stable traceability IDs (`US-1`, `FR-n`, `NFR-n`).
4. Validates both story input and generated artifact quality.
5. **New**: Runs a Flask-based spend forecast API (`/api/spend/forecast`, `/api/spend/budgets`) with risk-flag evaluation.
6. **New**: Serves a lightweight frontend (`src/frontend/`) using uPlot for charting forecast vs budget.

---

## Project Layout

```text
src/documentation_sync/   Core CLI, parser, validator, generator, Jira integration, verifier, forecast API
tests/                    Unit and integration tests (24 modules, ≥80% coverage enforced)
.github/                  GitHub Copilot prompts, instructions, workflows
.claude/                  Claude commands, agents, skills, hooks, MCP settings
samples/                  Example local story inputs (JSON)
data/                     JSON data files for forecast API (budgets.json, spend_records.json)
docs/                     Explanatory and operating-model documentation
github-copilot-output/    Default generated output for CLI / Copilot runs (gitignored)
claude-output/            Default generated output for Claude CLI runs (gitignored)
demo_output/              Legacy demo runs (gitignored)
output_mcp/               MCP demo outputs (gitignored)
archive/                  Superseded demo runs
```

---

## Installation

```bash
pip install -e .
```

### Optional Extras

```bash
pip install -e ".[url-ingestion,mcp-tools,test]"
```

- `url-ingestion` — `requests` for live Jira URL/key fetching
- `mcp-tools` — `mcp` for the custom Jira MCP server
- `test` — pytest, pytest-cov, requests, mcp

---

## Configuration

### Local Jira Configuration

For full Jira URL input, set a token:

```bash
# Windows (PowerShell)
$env:JIRA_API_TOKEN="your-token"
# Windows (cmd)
set JIRA_API_TOKEN=your-token
# Linux/macOS
export JIRA_API_TOKEN="your-token"
```

For bare issue-key input such as `EPMCDMETST-55568`, also provide a Jira base URL:

**Option 1: Environment variable**
```bash
export JIRA_BASE_URL=https://jiraeu.epam.com
```

**Option 2: Config file** (create `docsync.config.json` from `docsync.config.example.json`)
```json
{
  "jira_base_url": "https://jiraeu.epam.com"
}
```

`docsync.config.json` is intentionally gitignored.

### Configuration System (v2)

The engine now uses a centralized, validated `Settings` object (`src/documentation_sync/config.py`):

- **Load order**: defaults → `docsync.config.json` (validated against `docsync.config.schema.json`) → `DOCSYNC_*` environment variables
- **Supported settings**:
  - `jira_base_url` — Jira instance base URL
  - `llm.model`, `llm.max_tokens`, `llm.max_retries`, `llm.retry_base_delay_s`, `llm.retry_max_delay_s`, `llm.context_window`, `llm.token_warning_threshold`
  - `logging_level` — DEBUG/INFO/WARNING/ERROR/CRITICAL
  - `mcp_api_key`, `mcp_rate_limit_per_minute`
  - `max_context_tokens`

Environment variable overrides use the `DOCSYNC_` prefix (e.g., `DOCSYNC_LOG_LEVEL=DEBUG`, `DOCSYNC_LLM_MODEL=claude-opus-5`).

---

## CLI Usage

The `docsync` command is installed as a console script (`python -m documentation_sync.cli` works equivalently).

### Basic Generation (one-shot, all artifacts)

```bash
# From a local sample story
docsync samples/jira_story.json

# From a live Jira issue key (requires JIRA_BASE_URL + JIRA_API_TOKEN)
docsync EPMCDMETST-55568 --phased --non-interactive

# From a full Jira URL
docsync https://jiraeu.epam.com/browse/EPMCDMETST-55568 --phased --non-interactive

# Choose a specific output directory
docsync samples/jira_story.json -o out
```

### Default Output Directory Behavior

| Invocation | Output Directory |
|------------|------------------|
| `docsync story.json` (no `-o`, no `--llm`) | `github-copilot-output/` |
| `docsync story.json --llm claude` (no `-o`) | `claude-output/` |
| `docsync story.json -o custom/path` | `custom/path/` (explicit always wins) |

Both default directories are gitignored.

### Phased Generation (interactive gates)

```bash
# Interactive: pauses at each phase boundary for y/N approval
docsync samples/jira_story.json --phased

# Non-interactive (CI): auto-approves all pauses
docsync samples/jira_story.json --phased --non-interactive

# With live Jira + phased
docsync "https://jira.company.com/browse/PROJ-123" --phased --non-interactive --jira-token "$JIRA_API_TOKEN"

# Resume from a specific phase after interruption
docsync samples/jira_story.json --phased --resume-from-phase architecture
```

**Phases**: `requirements` → `architecture` → `design-review` → `impl-plan` → `pr`

### Live Jira Fetch for Copilot Pipeline

The CLI writes `user-story.md` (the canonical input for the Copilot pipeline) alongside the 8 artifacts when run with `-o .`.

**Option 1 — Pre-fetch via CLI, then run Copilot:**
```bash
# One-time: set your Jira token
export JIRA_API_TOKEN="your-personal-access-token"

# Fetch live story → writes user-story.md + all 8 artifacts to current dir
docsync "https://jira.company.com/browse/EPMCDMETST-55568" \
  --jira-token "$JIRA_API_TOKEN" \
  -o . \
  --non-interactive

# Then in Copilot Chat:
/run-pipeline EPMCDMETST-55568
```

**Option 2 — One-command wrapper (recommended for teams):**
```bash
# One-time setup
chmod +x .github/scripts/fetch-and-run.sh

# Fetch and prepare in one command
export JIRA_API_TOKEN="your-token"
.github/scripts/fetch-and-run.sh EPMCDMETST-55568 "https://jira.company.com/browse/EPMCDMETST-55568"

# Then in Copilot Chat:
/run-pipeline EPMCDMETST-55568
```

**Option 3 — CI/GitHub Action (automated):**
See `.github/workflows/fetch-jira-story.yml` for a `workflow_dispatch` action that commits fresh `user-story.md` to the repo. Requires `JIRA_API_TOKEN` in repository secrets.

---

## What Happens If You Run Twice?

| Scenario | Behavior |
|----------|----------|
| **Same story, same output dir** (`-o out`) | Artifacts are **overwritten** in place. `write_all_artifacts()` opens each file with `write_text()` — no backup, no versioning. |
| **Same story, different output dir** (`-o out2`) | Fresh artifacts in `out2/`. Original `out/` untouched. |
| **Different story, same output dir** | Artifacts reflect the *new* story. Old content replaced. |
| **Phased run interrupted, then resumed** | `--resume-from-phase` loads `.docsync_checkpoint.json` from the output dir, rolls back any incomplete phase artifacts, and continues from the named phase. |
| **Phased run completed, then re-run without `--resume`** | Full regeneration from phase 1. Checkpoint file is deleted on successful completion. |

**No automatic versioning or timestamped subdirectories exist.** If you need history, commit artifacts to git or copy the output directory before re-running.

---

## Verification And Tests

### Run the full test suite

```bash
python -m pytest -q --cov=src/documentation_sync --cov-report=term-missing
```

Coverage threshold: **≥80%** (enforced by `pyproject.toml` and CI).

### Verify generated artifacts

```bash
# Verify structure, headings, traceability IDs
docsync-verify github-copilot-output --story user-story.md
```

`docsync-verify` checks:
- Required `##` sections per artifact type
- Heading discipline (single `#` title first; nothing deeper than `##`)
- Traceability — downstream artifacts cite only IDs that `requirements.md` defines
- Story parity (`--story`) — `FR-n` count matches the story's acceptance criteria exactly

---

## MCP Support

This repo ships a custom MCP server for Jira-aware operations:

| Item | Location |
|------|----------|
| Server implementation | `src/documentation_sync/jira_mcp_server.py` |
| Copilot MCP config | `.mcp.json` |
| Claude MCP config | `.claude/settings.json` |

Supported MCP tools:
1. `fetch_jira_story`
2. `run_sdlc_pipeline`
3. `get_artifact_status`
4. `validate_jira_url`

---

## Spend Forecast API (New)

A Flask-based REST API exposing spend actuals, projections, and budget risk flags.

### Start the server

```bash
# Install Flask
pip install flask

# Run (defaults to 127.0.0.1:5050)
python -m documentation_sync.spend_api_router
```

Or programmatically:
```python
from documentation_sync.spend_api_router import create_app
app = create_app()
app.run(host="127.0.0.1", port=5050)
```

### Endpoints

| Endpoint | Query Params | Response |
|----------|--------------|----------|
| `GET /api/spend/forecast` | `period` (required, `YYYY-MM`), `category` (optional) | `{ period, category, actual_spend[], projected_total, confidence_note, budget, risk_flag }` |
| `GET /api/spend/budgets` | none | `{ overall, categories[] }` |

### Authentication (optional)

Set `SPEND_API_KEY` environment variable to enable API key auth:

```bash
export SPEND_API_KEY="your-secret-key"
```

Clients must then include `X-API-Key: your-secret-key` header. When unset, the server operates in dev mode (no auth required; bind to `127.0.0.1` in production).

### Data Files

- `data/spend_records.json` — daily spend records: `[{ "date": "2026-08-01", "amount": 1200.00 }, ...]`
- `data/budgets.json` — overall + per-category budgets

Both are read by `ForecastDataService` (injected via `data_dir` for tests).

---

## Frontend (New)

A zero-build frontend in `src/frontend/` using uPlot (via CDN) for charting.

### Files

| File | Purpose |
|------|---------|
| `index.html` | Main page with chart, view toggle, period selector, refresh button |
| `ForecastChart.js` | uPlot chart component; fetches `/api/spend/forecast` |
| `view_toggle.js` | Overall/Category view switcher |
| `period_cache.js` | In-memory cache keyed by period+category |
| `risk_flag_marker.js` | Renders server-side risk flag (no threshold logic in frontend) |
| `budget_absence_notice.js` | Graceful message when no budget configured |

### Run

```bash
# Start API server first
python -m documentation_sync.spend_api_router

# Serve frontend (any static server)
npx serve src/frontend
# or
python -m http.server -d src/frontend 8080
```

Open `http://localhost:8080` (or the serve port). The chart loads `2026-08` by default.

### Architecture Notes

- **No threshold logic in frontend** — risk evaluation happens server-side (`risk_flag_evaluator.py`)
- **Cache invalidation** — Refresh button clears period cache and re-fetches
- **Graceful degradation** — If no budget configured, risk flag hidden and notice shown (FR-4)

---

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `tests.yml` | push, PR | Run pytest with coverage ≥80%, `docsync-verify` |
| `doc-sync.yml` | push to main | Verify story-to-artifact ID parity on generated artifacts |
| `release.yml` | tag push | Validate all 8 steps present, create GitHub Release |

---

## Commit-Ready Notes

Track these as **source assets** (commit to git):
1. `src/`, `tests/`, `.github/`, `.claude/`, `README.md`, `CLAUDE.md`, `.mcp.json`
2. Prompt and MCP config files
3. `docsync.config.example.json`, `docsync.config.schema.json`

Treat these as **generated output** (do not commit unless explicitly needed for review):
1. `github-copilot-output/`
2. `claude-output/`
3. Root-level `claude-*.md` files
4. Root-level phase artifacts: `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `PR.md`, `CHANGELOG.md`, `verification-report.md`, `user-story.md`

Only commit generated artifacts if they are part of the deliverable for your current branch.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: documentation_sync` | Run `pip install -e .` from repo root |
| `Jira fetch fails: 401/403` | Check `JIRA_API_TOKEN` validity and permissions; ensure `JIRA_BASE_URL` matches the Jira instance |
| `docsync-verify fails: missing sections` | Run `docsync` again to regenerate; or manually add required `##` sections |
| `docsync-verify fails: traceability IDs` | Ensure `requirements.md` defines all cited IDs; run with `--story` to check parity |
| `Flask not found` | `pip install flask` |
| `MCP server not found` | Ensure `.mcp.json` / `.claude/settings.json` have correct `PYTHONPATH=src` |
| `Tests fail: coverage <80%` | Add tests for uncovered lines; run `pytest --cov-report=term-missing` to see gaps |

---

## Key Principles

1. **No phase skipping.** Steps go 1→8 in order. Each consumes the prior artifact.
2. **Requirement IDs are immutable.** `US-1`, `FR-1`, ... `FR-n`, `NFR-1` are derived from the source story. Prose may be refined; IDs may not.
3. **Copilot is the driver for authoring.** Steps 1-5 are Copilot Chat + prompts. Steps 6-8 include CLI verification.
4. **Traceability throughout.** Every artifact cites the requirements it addresses.
5. **Human gates at 3, 6, 8.** Not all gates are blocking, but explicit approval is expected.
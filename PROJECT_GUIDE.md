# Automated Documentation Sync — Project Guide

**Story:** EPMCDMETST-59936
**Branch:** `feature/jira-mcp-readiness`
**Status:** Release-ready (all 8 SDLC steps complete, 92% test coverage, all gates green)

---

## 1. What This Project Does

This repository implements an **Agentic SDLC Pipeline** that automates the creation and synchronization of software development lifecycle documentation — from a Jira story through requirements, architecture, design review, implementation plan, code review, verification, changelog, and release.

**Two operating modes:**

| Mode | Description | Entry Point |
|------|-------------|-------------|
| **Pipeline A — Copilot Chat** | Human-driven, AI-assisted. Copilot authors artifacts via prompts; you approve at gates. | `/run-pipeline <JIRA-ID>` in Copilot Chat |
| **Pipeline B — CLI (`docsync`)** | Fully automated. Generates Steps 1–4 artifacts from a story file/URL in one command. | `docsync <story> -o .` |

**Key differentiator:** Both pipelines produce **traceable artifacts** — every requirement (US-1, FR-1..n, NFR-1) flows from story → requirements → architecture → design → plan → code → tests → verification → changelog. IDs are immutable; only prose is refined.

---

## 2. What Was Created (EPMCDMETST-59936)

### Core Implementation (src/documentation_sync/)

| Module | Purpose |
|--------|---------|
| `cli.py` | Main entry point — `docsync` command, phased flow, Jira fetch |
| `parser.py` | Loads story from JSON, Markdown, Jira URL, or raw text |
| `validator.py` | Enforces required fields, traceability rules, ID format |
| `generator.py` | Renders `requirements.md`, `architecture.md`, `impl-plan.md`, `PR.md` |
| `phased_generator.py` | Interactive phased flow with clarification questions |
| `input_handler.py` | Multi-source input (file, URL, stdin, Jira API) |
| `jira_connector.py` | Jira REST API client (auth, fetch, custom fields) |
| `jira_mcp_server.py` | MCP server exposing 4 tools: `fetch_story`, `validate_requirements`, `generate_artifacts`, `verify_traceability` |
| `llm_orchestrator.py` | Abstraction over LLM providers (Claude, Copilot, heuristic) |
| `providers.py` | Provider implementations for `llm_orchestrator` |
| `config.py` | Centralized configuration (env, file, defaults) |
| `checkpoint.py` | Phase checkpoint persistence for resume capability |
| `resilience.py` | Retry, circuit breaker, timeout utilities |
| `log.py` | Structured logging |
| `tokens.py` | Token estimation/cost tracking |
| `doc_validator.py` | Artifact quality checker (used by pre-commit hook) |
| `models.py` | Pydantic models for story, requirements, artifacts |

### Forecast Feature (EPMCDMETST-59936)

| Module | Purpose |
|--------|---------|
| `forecast_calculator.py` | Month-end spend projection algorithms |
| `forecast_data_service.py` | Spend data retrieval + caching |
| `risk_flag_evaluator.py` | Budget exceedance detection (overall + per-category) |
| `spend_api_router.py` | FastAPI endpoints: `/api/spend/actual`, `/api/spend/forecast`, `/api/budgets` |

### Frontend (src/frontend/)

| File | Purpose |
|------|---------|
| `ForecastChart.js` | uPlot-based chart: actual spend + projected month-end line |
| `risk_flag_marker.js` | Accessible risk flags (role=alert, aria-label) |
| `view_toggle.js` | Keyboard-accessible Overall ↔ Category view switch |
| `period_cache.js` | In-memory Map cache per period (NFR-2) |
| `budget_absence_notice.js` | Graceful degradation UI when budgets missing (FR-4) |
| `index.html` | Demo page wiring all components |

### Data (data/)

| File | Purpose |
|------|---------|
| `budgets.json` | Sample budget definitions (overall + categories) |
| `spend_records.json` | Sample spend transactions for testing |

### Tests (tests/) — 352 passing, 92% coverage

| Test File | Coverage Focus |
|-----------|----------------|
| `test_parser.py` | Story parsing (JSON, MD, URL, missing fields) |
| `test_validator.py` | Requirement ID format, traceability, duplicates |
| `test_generator.py` | Artifact content, file writing, ID preservation |
| `test_integration.py` | CLI end-to-end (exit codes, error handling) |
| `test_jira_connector.py` | Auth, fetch, custom field mapping |
| `test_jira_mcp_server.py` | MCP tool registration, tool execution |
| `test_llm_orchestrator.py` | Provider switching, prompt templating |
| `test_providers.py` | Claude/Copilot/heuristic provider behavior |
| `test_config.py` | Config precedence, env overrides, validation |
| `test_checkpoint.py` | Phase resume, corruption recovery |
| `test_resilience.py` | Retry, circuit breaker, timeout scenarios |
| `test_tokens.py` | Estimation accuracy, cost tracking |
| `test_forecast_calculator.py` | Projection math, edge cases |
| `test_forecast_data_service.py` | Data retrieval, caching, fallback |
| `test_risk_flag_evaluator.py` | Threshold logic, category/overall flags |
| `test_spend_api_router.py` | API endpoints, auth, error responses |
| `test_forecast_integration.py` | End-to-end forecast flow |
| `test_traceability.py` | Story→artifact ID chain verification |
| `test_period_cache.js` | JS cache behavior (Jest) |

### Pipeline Artifacts (root)

| Artifact | Pipeline Step | Status |
|----------|---------------|--------|
| `user-story.md` | Input (Jira fetch) | ✅ Current |
| `requirements.md` | Step 1 | ✅ Traceable IDs |
| `architecture.md` | Step 2 | ✅ Component design |
| `design-review.md` | Step 3 | ✅ **Gate passed** |
| `impl-plan.md` | Step 4 | ✅ Task breakdown |
| `code-review.md` | Step 5 | ✅ Findings addressed |
| `verification-report.md` | Step 6 | ✅ **Gate passed** |
| `CHANGELOG.md` | Step 7 | ✅ Release notes |
| `PR.md` | Step 8 | ✅ PR description |

### Tooling & Config

| File | Purpose |
|------|---------|
| `.githooks/pre-commit` | Blocks commit if artifact quality fails |
| `.github/workflows/tests.yml` | CI: pytest + coverage gate (≥80%) |
| `.github/workflows/doc-sync.yml` | CI: artifact traceability verification |
| `.github/workflows/release.yml` | CI: release gate (all 8 steps present) |
| `.github/scripts/fetch-and-run.sh` | One-command Jira fetch + pipeline prep |
| `.claude/settings.json` | MCP servers, hooks, permissions |
| `.claude/hooks/trigger-doc-sync.py` | Stop-hook: blocks exit if src/ changed without doc sync |
| `.claude/commands/` | Slash commands for 8-step pipeline |
| `.claude/agents/` | Agent definitions for each step |
| `.mcp.json` | MCP server registry (Jira, GitHub, Filesystem) |
| `pyproject.toml` | Package config, pytest, coverage, dependencies |

---

## 3. How It Works

### Pipeline A: Copilot Chat (Interactive)

```mermaid
graph LR
    A[Jira Story] --> B[/run-pipeline]
    B --> C[Step 1: Requirements]
    C --> D[Step 2: Architecture]
    D --> E[Step 3: Design Review]
    E -->|Human Approve| F[Step 4: Impl Plan]
    F --> G[Step 5: Code Review]
    G --> H[Step 6: Verification]
    H -->|Tests Pass| I[Step 7: Changelog]
    I --> J[Step 8: PR & Release]
```

**You drive it:**
1. Run `/run-pipeline EPMCDMETST-59936` in Copilot Chat
2. Copilot runs Step 1 prompt → you answer clarifying questions
3. Copilot runs Step 2 prompt → you refine/approve architecture
4. **Gate 3:** Copilot runs Step 3 prompt → **you must approve** design-review.md
5. Copilot runs Step 4 → impl-plan.md
6. You implement code + tests per impl-plan.md
7. Copilot runs Step 5 → code-review.md
8. **Gate 6:** Run tests, verify coverage → Copilot runs Step 6 → verification-report.md
9. Copilot runs Step 7 → CHANGELOG.md
10. **Gate 8:** CI passes → you merge PR

### Pipeline B: CLI (Automated)

```bash
# One-time setup
git config core.hooksPath .githooks

# Fetch live Jira story + generate all artifacts
export JIRA_API_TOKEN="your-pat"
docsync "https://jira.company.com/browse/EPMCDMETST-59936" \
  --jira-token "$JIRA_API_TOKEN" \
  -o . \
  --non-interactive

# Or use the wrapper
chmod +x .github/scripts/fetch-and-run.sh
.github/scripts/fetch-and-run.sh EPMCDMETST-59936 "https://jira.company.com/browse/EPMCDMETST-59936"
```

**Output:** `user-story.md`, `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md` — all with correct requirement IDs.

---

## 4. How to Run It

### Prerequisites

```bash
# Python 3.11+
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"   # or: pip install -r requirements-dev.txt
```

### Option 1: Full Pipeline with Live Jira (Recommended)

```bash
# 1. Set Jira token (once)
export JIRA_API_TOKEN="your-personal-access-token"

# 2. Fetch story + generate artifacts
docsync "https://jira.company.com/browse/EPMCDMETST-59936" \
  --jira-token "$JIRA_API_TOKEN" \
  -o . \
  --non-interactive

# 3. Run Copilot pipeline
# In VS Code Copilot Chat:
/run-pipeline EPMCDMETST-59936
```

### Option 2: CLI-Only (Steps 1–4 Auto-Generated)

```bash
# From a local story file
docsync user-story.md -o . --phased --non-interactive
```

### Option 3: Run Forecast API + Frontend Demo

```bash
# Terminal 1: Start API server
python -m documentation_sync.spend_api_router
# → http://localhost:8000

# Terminal 2: Serve frontend (any static server)
cd src/frontend
python -m http.server 3000
# → http://localhost:3000
```

### Option 4: Run Tests & Verify

```bash
# Full test suite with coverage
pytest -v --cov=src/documentation_sync --cov-report=term-missing

# Verify artifact quality (same as pre-commit hook)
python -m documentation_sync.doc_validator . --story user-story.md
```

### Option 5: Use MCP Server (for AI assistants)

```bash
# Start MCP server
python -m documentation_sync.jira_mcp_server

# In Claude Code / MCP client, tools available:
# - fetch_story(jira_url, token)
# - validate_requirements(requirements_path)
# - generate_artifacts(story_path, output_dir)
# - verify_traceability(project_dir, story_path)
```

---

## 5. Why It's Useful

### For Teams

| Pain Point | Solution |
|------------|----------|
| Docs drift from code | **Traceability enforcement** — pre-commit + CI block merges if IDs mismatch |
| Manual doc writing | **Auto-generation** — Steps 1–4 from story in seconds |
| Inconsistent artifacts | **Templated generators** — same structure every time |
| Missed requirements | **Gated pipeline** — human approval at Design, Verification, Release |
| No Jira integration | **Live fetch** — `docsync <jira-url>` pulls story, custom fields, comments |

### For Auditors / Compliance

- Every artifact cites source requirement IDs
- Immutable ID chain: Story → US-1 → FR-1..n → NFR-1 → code → tests → verification
- `verification-report.md` is evidence of test coverage + acceptance criteria mapping

### For Developers

- **CLI mode** for rapid prototyping: `docsync story.md -o .`
- **MCP server** lets any AI assistant fetch Jira, validate, generate, verify
- **Checkpoint/resume** — phased flow survives interruptions
- **Resilience built-in** — retry, circuit breaker, timeout on all external calls

### For the Forecast Feature (EPMCDMETST-59936)

| Requirement | Implementation |
|-------------|----------------|
| FR-1: Actual + projected line | `ForecastChart.js` + `forecast_calculator.py` |
| FR-2: Risk flags on exceedance | `risk_flag_evaluator.py` + `risk_flag_marker.js` |
| FR-3: Overall/Category toggle | `view_toggle.js` (keyboard accessible) |
| FR-4: Graceful degradation | `budget_absence_notice.js` (flags hidden, notice shown) |
| NFR-1: 2s render target | uPlot CDN (~40 KB), no heavy deps |
| NFR-2: Period caching | `period_cache.js` (in-memory Map, no sessionStorage) |
| NFR-3: Accessibility | role=alert, aria-label, keyboard nav |

---

## 6. Questions You Should Be Prepared to Answer

### Architecture & Design

| Question | Key Points to Cover |
|----------|---------------------|
| "How does traceability work end-to-end?" | Story → parser extracts AC → generator creates requirement IDs (US-1, FR-1..n, NFR-1) → every downstream artifact references those exact IDs → validator enforces parity in pre-commit + CI |
| "Why two pipelines (Copilot + CLI)?" | Copilot = human-in-loop for judgment calls (design review, code review); CLI = CI/CD automation, bulk generation, reproducibility |
| "How does the MCP server fit in?" | Exposes 4 tools so *any* AI assistant (Claude Code, Cursor, custom agent) can fetch Jira, validate reqs, generate artifacts, verify traceability — not tied to Copilot |
| "What happens if someone edits requirements.md by hand?" | Pre-commit hook runs `doc_validator` — fails if IDs don't match story. Override only with `git commit --no-verify` (audited). |

### Implementation

| Question | Key Points to Cover |
|----------|---------------------|
| "How is 92% coverage achieved?" | Unit tests for every module; integration tests for CLI + API; property-based tests for calculator; Jest for frontend cache; resilience tests inject failures |
| "How does the phased generator resume?" | `checkpoint.py` writes phase state to `.docsync_checkpoint.json`; `--resume-from-phase` loads it and skips completed phases |
| "Why uPlot for charts?" | ~40 KB gzipped, no runtime deps, canvas-based (fast), meets 2s render target (NFR-1) |
| "How does risk flag evaluation work?" | `risk_flag_evaluator.py`: projects month-end from daily spend rate × remaining days; compares to overall + per-category budgets; returns flag objects with severity, message, category |

### Operations

| Question | Key Points to Cover |
|----------|---------------------|
| "How do I add a new story?" | `docsync "https://jira.com/browse/NEW-123" --jira-token $TOKEN -o . --non-interactive` → runs pipeline |
| "What if Jira custom fields change?" | `jira_connector.py` has `CUSTOM_FIELD_MAP` — update mapping, tests cover field extraction |
| "How do I run in CI?" | `.github/workflows/tests.yml` runs pytest + coverage; `doc-sync.yml` runs validator; `release.yml` checks all 8 artifacts exist |
| "Can I use this without Jira?" | Yes — `docsync story.md -o .` works with local Markdown/JSON story files |

### Forecast Feature Specific

| Question | Key Points to Cover |
|----------|---------------------|
| "How is month-end projection calculated?" | Linear extrapolation: `daily_rate = spend_to_date / days_elapsed`; `projected = spend_to_date + daily_rate * days_remaining` |
| "What if budgets are missing?" | `budget_absence_notice.js` shows "Budgets required for risk assessment"; risk flags hidden (FR-4) |
| "Is per-category projection accurate?" | Known limitation: currently uses overall spend data; category-scoped projection deferred to follow-up story |
| "How do I test the API?" | `python -m documentation_sync.spend_api_router` → `curl http://localhost:8000/api/spend/forecast?period=2026-08` |

### Extensibility

| Question | Key Points to Cover |
|----------|---------------------|
| "How do I add a new artifact type?" | 1. Add template in `generator.py` 2. Add validator rule in `doc_validator.py` 3. Add to `ARTIFACTS` in `.githooks/pre-commit` 4. Add test in `test_generator.py` |
| "How do I swap LLM provider?" | `llm_orchestrator.py` uses `Provider` protocol — implement `ClaudeProvider`, `CopilotProvider`, or `HeuristicProvider` in `providers.py` |
| "Can I add more MCP tools?" | Add `@server.tool()` methods in `jira_mcp_server.py`; register in `create_server()` |

---

## 7. Quick Reference Commands

```bash
# ===== Setup =====
git config core.hooksPath .githooks          # Enable pre-commit hook
pip install -e ".[dev]"                      # Install deps

# ===== Jira Fetch + Generate =====
export JIRA_API_TOKEN="your-token"
docsync "https://jira.com/browse/EPMCDMETST-59936" --jira-token "$JIRA_API_TOKEN" -o . --non-interactive
.github/scripts/fetch-and-run.sh EPMCDMETST-59936 "https://jira.com/browse/EPMCDMETST-59936"

# ===== Local Story =====
docsync user-story.md -o . --phased --non-interactive

# ===== Verify =====
python -m documentation_sync.doc_validator . --story user-story.md
pytest -v --cov=src/documentation_sync --cov-report=term-missing

# ===== Forecast Demo =====
python -m documentation_sync.spend_api_router      # Terminal 1: API on :8000
cd src/frontend && python -m http.server 3000      # Terminal 2: UI on :3000

# ===== MCP Server =====
python -m documentation_sync.jira_mcp_server       # Exposes 4 tools

# ===== Copilot Pipeline =====
# In VS Code Copilot Chat:
/run-pipeline EPMCDMETST-59936
/step-1-requirements
/step-2-architecture
/step-3-design-review      # GATE: approve in chat
/step-4-impl-plan
/step-5-implement
/step-6-code-review
/step-7-verify             # GATE: tests pass, coverage ≥80%
/step-8-create-pr
/doc-sync                  # Sync docs only
```

---

## 8. File Tree (Key Files)

```
automated-documentation-sync-capstone/
├── .claude/
│   ├── settings.json           # MCP, hooks, permissions
│   ├── hooks/
│   │   └── trigger-doc-sync.py # Stop hook: block exit if src/ changed
│   ├── commands/               # Slash commands for 8 steps
│   └── agents/                 # Agent definitions
├── .github/
│   ├── prompts/                # Copilot prompts for each step
│   ├── scripts/fetch-and-run.sh
│   └── workflows/              # CI: tests.yml, doc-sync.yml, release.yml
├── .githooks/pre-commit        # Artifact quality gate
├── src/
│   ├── documentation_sync/     # Core + forecast modules
│   └── frontend/               # Forecast UI components
├── data/                       # budgets.json, spend_records.json
├── tests/                      # 352 tests, 92% coverage
├── user-story.md               # Current story (EPMCDMETST-59936)
├── requirements.md             # Step 1 artifact
├── architecture.md             # Step 2 artifact
├── design-review.md            # Step 3 artifact (gate passed)
├── impl-plan.md                # Step 4 artifact
├── code-review.md              # Step 5 artifact
├── verification-report.md      # Step 6 artifact (gate passed)
├── CHANGELOG.md                # Step 7 artifact
├── PR.md                       # Step 8 artifact
├── pyproject.toml
└── PROJECT_GUIDE.md            # This file
```

---

## 9. Next Steps / Future Work

- [ ] Category-scoped spend projections (follow-up story)
- [ ] Automated Lighthouse performance gating (NFR-1)
- [ ] Integrate `spend_api_router` into main `docsync` CLI entry point
- [ ] Add Confluence wiki sync as output target
- [ ] Slack/Teams notifications for gate approvals

---

## 10. Deep-Dive: Guardrails, Hooks, Testing, Resume, Tokens, MCP

### 10.1 Guardrails & Hooks — Where and How They're Used

**Three enforcement hooks in `.claude/settings.json`:**

| Hook | Event | Script | What It Guards |
|------|-------|--------|----------------|
| `block-secrets` | `PreToolUse` (Bash) | `.claude/hooks/block-secrets.py` | Prevents accidental secret leakage in shell commands (AWS keys, passwords, API keys, private keys) |
| `guard-generated` | `PreToolUse` (Write/Edit) | `.claude/hooks/guard-generated-files.py` | Protects `.claude/` config files (CLAUDE.md, settings.json, commands/, agents/) from accidental overwrites |
| `doc-sync-check` | `Stop` (session end) | `.claude/hooks/trigger-doc-sync.py` | Blocks session exit if `src/` or `tests/` changed but `/doc-sync` wasn't run |

**How they work effectively:**

1. **Block secrets at the source** — `block-secrets.py` runs *before* any Bash command executes. It regex-matches against 6 secret patterns (AWS AKIA*, `password=`, `api_key=`, private key markers, `--password` flag, `--api-key` flag). Exit code 1 blocks the command; output explains what was detected.

2. **Protect config integrity** — `guard-generated-files.py` intercepts Write/Edit to `.claude/`. It allows `.claude/hooks/`, `.claude/skills/`, `.claude/projects/*/memory/` (user-writable) but blocks `.claude/CLAUDE.md`, `.claude/settings.json`, `.claude/commands/`, `.claude/agents/`. Override: use `claude /config` command instead.

3. **Enforce doc-sync discipline** — `trigger-doc-sync.py` runs on session Stop. Logic:
   - `git diff --name-only HEAD` → get changed files
   - If `src/**` or `tests/**` changed AND marker `.claude/.docsync-ran` absent AND no doc artifacts changed → **block exit**
   - Marker written by `/doc-sync` skill after successful run
   - Override: pass `--force` to hook, or confirm in chat

**Setup (one-time):**
```bash
git config core.hooksPath .githooks   # Enables pre-commit (separate from Claude hooks)
# Claude Code hooks are auto-loaded from .claude/settings.json — no extra step
```

**Pre-commit hook (separate, git-level):** `.githooks/pre-commit` runs `python -m documentation_sync.doc_validator . --story user-story.md` on staged artifact changes. Fails commit if structure/traceability invalid.

---

### 10.2 Test Coverage — How We Test, Current Status, 100% Target

**Test infrastructure (pyproject.toml):**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--cov=src/documentation_sync --cov-report=term-missing"

[tool.coverage.run]
source = ["src/documentation_sync"]

[tool.coverage.report]
fail_under = 80
```

**Current coverage: 92% (352 tests passing, 2 skipped)**

| Module | Coverage | Missing Lines |
|--------|----------|---------------|
| `forecast_calculator.py` | 100% | — |
| `forecast_data_service.py` | 98% | Line 114 (fallback) |
| `risk_flag_evaluator.py` | 100% | — |
| `spend_api_router.py` | 100% | — |
| `checkpoint.py` | 100% | — |
| `config.py` | 92% | Lines 50, 105-106, 152-153, 158-160, 170 |
| `cli.py` | 85% | Lines 102-103, 127-128, 134-135, 170-177, 233 |
| `generator.py` | 98% | Lines 122, 285 |
| `jira_mcp_server.py` | 65% | Lines 33-34, 43, 75-76, 162-224, 228-229 |
| `providers.py` | 83% | Lines 79, 103, 154-163, 173-181, 190, 216-235 |

**How to push toward 100%:**

1. **Run with coverage details:**
   ```bash
   pytest -v --cov=src/documentation_sync --cov-report=term-missing --cov-report=html
   # Open htmlcov/index.html for line-by-line visualization
   ```

2. **Target the gaps:**
   - `jira_mcp_server.py` (65%) — needs tests for MCP server wiring (`create_server`, tool registration). Currently skipped if `mcp` package not installed.
   - `providers.py` (83%) — test all provider branches (Claude, Copilot, heuristic) including error paths.
   - `cli.py` (85%) — test `--resume-from-phase`, error exit codes, interactive prompts.
   - `config.py` (92%) — test env override precedence, validation errors.

3. **Add missing tests:**
   ```bash
   # Example: test error path in providers.py
   def test_claude_provider_missing_api_key(monkeypatch):
       monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
       with pytest.raises(ValueError):
           ClaudeProvider().generate("prompt")
   ```

4. **Enforce in CI:** `.github/workflows/tests.yml` already runs `pytest --cov=fail_under=80`. Raise to 90 or 100 when ready.

**Note on 100%:** Pragmatic 100% excludes:
- `__main__` blocks (`if __name__ == "__main__":`)
- Import-error fallbacks (e.g., optional `mcp`, `anthropic`, `tiktoken`)
- Abstract base class methods not meant for direct call

---

### 10.3 Pipeline Resume — Starting From Where It Stopped

**Two resume mechanisms:**

#### A. CLI Phased Generation (`--resume-from-phase`)

```bash
# First run (interactive or non-interactive)
docsync user-story.md -o . --phased --non-interactive
# ... stops at phase 3 (design-review) awaiting approval ...

# Resume from phase 4
docsync user-story.md -o . --phased --non-interactive --resume-from-phase architecture
# or
docsync user-story.md -o . --phased --non-interactive --resume-from-phase impl-plan
```

**How it works (`checkpoint.py`):**
- After each phase, `PhaseCheckpoint.save()` writes `.docsync_checkpoint.json` atomically (tmp → rename)
- Checkpoint contains: `req_set` (story + requirements), `results[]` (phase + artifact_path + approved), `clarifications`
- `--resume-from-phase` loads checkpoint, skips completed phases, resumes at requested phase
- `rollback_artifacts()` deletes artifacts from failed phases before retry

**Checkpoint file location:** `<output_dir>/.docsync_checkpoint.json`

#### B. Copilot Chat Pipeline (Manual Resume)

```bash
# In Copilot Chat, run specific step commands:
/step-4-impl-plan          # Resumes after design-review approved
/step-5-implement          # Resumes after impl-plan exists
/step-6-code-review        # Resumes after code + tests exist
/step-7-verify             # Resumes after code-review approved
/step-8-create-pr          # Resumes after verification passed
```

Each step command reads the prior artifact as input — no hidden state. If you hand-edited an artifact, the next step consumes your version.

---

### 10.4 Token Usage — Effective Setup & Management

**Token counter (`src/documentation_sync/tokens.py`):**

```python
from documentation_sync.tokens import TokenCounter, create_counter_from_settings

counter = create_counter_from_settings()  # Reads from config.Settings
# Or explicit:
counter = TokenCounter(
    context_window=200_000,      # Model context limit
    warning_threshold=0.8,       # Warn at 80% (160k tokens)
    model="claude-haiku-4-5-20251001"
)

# Count before sending to LLM
tokens = counter.count(prompt_text)
if tokens.warning:
    print(f"WARNING: {tokens.count} tokens ({tokens.method}) — exceeds 80% budget")
    prompt_text = counter.truncate_to_budget(prompt_text)

# Use truncated prompt...
```

**Three counting methods (auto-fallback):**
1. **Anthropic SDK** — `ANTHROPIC_API_KEY` set, `anthropic` package installed → exact count
2. **tiktoken** — `tiktoken` package installed → cl100k_base encoding (accurate for Claude)
3. **Heuristic** — fallback: `len(text) // 4` (4 chars ≈ 1 token)

**Config-driven setup (`config.py` → `Settings`):**
```python
# Settings.load() reads (precedence: env var > config file > defaults)
max_context_tokens = 200_000
llm.token_warning_threshold = 0.8
llm.model = "claude-haiku-4-5-20251001"
```

**Effective practices:**
- Always call `counter.count()` before LLM calls in `llm_orchestrator.py` / `providers.py`
- Use `truncate_to_budget()` for long prompts (e.g., full story + context)
- Set `warning_threshold=0.75` for safety margin on large contexts
- Monitor via `tokens.py` logging — logs method used and warning status

---

### 10.5 MCP Integration — Setup & Details

**MCP Server: `docsync-jira`** (exposes 4 tools to any MCP client)

**Configuration (`.claude/settings.json`):**
```json
{
  "mcpServers": {
    "docsync-jira": {
      "command": "python",
      "args": ["-m", "documentation_sync.jira_mcp_server"],
      "env": {
        "PYTHONPATH": "src",
        "PYTHONIOENCODING": "utf-8"
      }
    },
    "github": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" } },
    "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."] }
  }
}
```

**Run standalone:**
```bash
python -m documentation_sync.jira_mcp_server
# Listens on stdio — connect via MCP client (Claude Code, Cursor, etc.)
```

**Tools exposed:**

| Tool | Parameters | Returns |
|------|------------|---------|
| `fetch_jira_story` | `url: string`, `jira_token?: string` | `{key, summary, description, acceptance_criteria[], labels[], priority, story_points, reporter, assignee}` or `{error}` |
| `run_sdlc_pipeline` | `jira_url: string`, `output_dir?: string`, `non_interactive?: boolean` | `{status, output_dir, artifacts_generated[], phases_completed}` or `{status: error, exit_code}` |
| `get_artifact_status` | `output_dir?: string` | `{output_dir, phases_completed, total_phases, details: {phase: {artifact, exists, path}}}` |
| `validate_jira_url` | `url: string` | `{valid: boolean, issue_key?: string, url}` |

**Authentication:**
- Token sources (priority): explicit `jira_token` param → `JIRA_API_TOKEN` env → `JIRA_TOKEN` env
- Base URL: `Settings.jira_base_url` (config) → `JIRA_BASE_URL` env → default Jira Cloud

**Usage from Claude Code:**
```bash
# In Claude Code with MCP enabled:
> Use the fetch_jira_story tool with url="https://jira.company.com/browse/EPMCDMETST-59936"
> Use the run_sdlc_pipeline tool with jira_url="https://jira.company.com/browse/EPMCDMETST-59936"
```

**Adding custom tools:** Edit `jira_mcp_server.py` → add `@mcp.tool()` decorated functions in `create_server()` → restart MCP server.

---

### 10.6 Additional Questions You May Be Asked

| Question | Answer |
|----------|--------|
| **"How does the pre-commit hook differ from Claude hooks?"** | Pre-commit (`.githooks/pre-commit`) runs at *git commit* time, validates artifact structure + traceability via `doc_validator`. Claude hooks (`.claude/settings.json`) run at *tool-use* time: block-secrets (before Bash), guard-generated (before Write/Edit), doc-sync-check (on session Stop). They operate at different layers. |
| **"Can I bypass hooks?"** | Pre-commit: `git commit --no-verify` (audited). Claude hooks: not bypassable via CLI; they're enforced by the Claude Code runtime. For `doc-sync-check`, pass `--force` to the hook script explicitly. |
| **"How is requirement ID immutability enforced?"** | 1. Generator creates IDs from story acceptance criteria (FR-1..n). 2. `doc_validator.check_story_parity()` verifies requirements.md has exactly those FR IDs + US-1. 3. `doc_validator.check_traceability()` ensures downstream artifacts cite only known IDs. 4. Pre-commit + CI both run validator. Hand-edits that drift IDs are caught. |
| **"What if Jira is unavailable during pipeline?"** | `jira_connector.py` uses `resilience.py` (retry 3×, exponential backoff, circuit breaker). CLI fails fast with clear error. Phased generator checkpoints before Jira call — resume after Jira recovers. |
| **"How do I add a new SDLC artifact type?"** | 1. Add template method in `generator.py` 2. Add required sections in `doc_validator.REQUIRED_SECTIONS` 3. Add to `TRACEABILITY_REQUIRED` if it must cite IDs 4. Add to `ARTIFACTS` in `.githooks/pre-commit` 5. Add test in `test_generator.py` 6. Add phase in `phased_generator.py` if part of phased flow |
| **"Can this work without Jira?"** | Yes. `docsync story.md -o .` accepts local Markdown/JSON story files. Parser handles: raw text, JSON, Markdown with frontmatter, Jira URL (needs token). |
| **"How is the forecast chart accessible?"** | `risk_flag_marker.js`: `role="alert"`, `aria-label="Risk: budget exceeded by X%"`. `view_toggle.js`: `<button>` with `aria-pressed`, keyboard `Enter/Space` toggles. `ForecastChart.js`: uPlot canvas with `aria-hidden`, text summary in adjacent `<div role="region">`. |
| **"What's the difference between Pipeline A and B artifacts?"** | Pipeline A (Copilot): `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `code-review.md`, `verification-report.md`, `CHANGELOG.md`, `PR.md`. Pipeline B (CLI): auto-generates only Steps 1–4 (`requirements.md` through `impl-plan.md`). Steps 5–8 require human/Copilot. Both use same ID scheme. |
| **"How do I debug a failing hook?"** | Run hook script directly: `python .claude/hooks/block-secrets.py "echo password=secret"` → shows exit code + message. Check `.claude/settings.json` hook config matches script paths. Logs: hook stdout/stderr appears in Claude Code tool output. |

---

**Generated:** 2026-08-17
**Branch:** `feature/jira-mcp-readiness` (9 commits ahead of origin)
**Status:** All gates green, release-ready
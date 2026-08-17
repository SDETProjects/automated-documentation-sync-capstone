# Automated Documentation Sync - Architecture Explanation

This document explains how the project handles tokens, guardrails, hooks, test coverage, observability, and evaluation.

---

## 1. Token Management (Saving Tokens)

### What it does
Prevents sending oversized prompts to LLMs by counting tokens **before** the API call and truncating if needed.

### Where it lives
`src/documentation_sync/tokens.py` → `TokenCounter` class

### How it works

```python
# 1. Initialize with context window (default 200k tokens) and warning threshold (80%)
counter = TokenCounter(context_window=200_000, warning_threshold=0.8)

# 2. Count tokens using best available method:
#    - Anthropic SDK (if API key present)
#    - tiktoken (if installed)
#    - Heuristic fallback: 4 chars ≈ 1 token
count = counter.count(prompt_text)
# Returns: TokenCount(count=12500, method="anthropic", warning=False)

# 3. Truncate to budget BEFORE sending to LLM
truncated = counter.truncate_to_budget(long_description, budget=160_000)
```

### Where it's used
`src/documentation_sync/providers.py` - In `ClaudeLLMAdapter._build_prompt()`:

```python
def _build_prompt(self, story: JiraStory) -> str:
    # Truncate story description to fit token budget
    truncated_desc = self._tokens.truncate_to_budget(story.description)
    
    # Build prompt with truncated description
    prompt = f"Story: {story.summary}\nDescription: {truncated_desc}\n..."
    
    # Log token usage
    count = self._tokens.count(prompt)
    log.debug("prompt_built", llm_tokens_in=count.count, ...)
    
    # Warn if using >80% of context window
    if count.warning:
        log.warning("token_budget_high", llm_tokens_in=count.count, ...)
    return prompt
```

### Why this saves tokens/money
| Without TokenCounter | With TokenCounter |
|---------------------|-------------------|
| Send 500k char prompt → API error or silent truncation | Truncates to 160k tokens → guaranteed to fit |
| Pay for tokens you can't use | Only pay for what fits in context window |
| No visibility into costs | Every prompt logs `llm_tokens_in` and `llm_tokens_out` |

---

## 2. Guardrails (Safety Rails)

Three layers of protection prevent bad things from happening.

### Layer 1: Pre-commit / Claude Code Hooks (`.claude/settings.json`)

```json
"hooks": {
  "PreToolUse": [
    { "toolName": "Bash", "script": "hooks/block-secrets.py" },
    { "toolName": "Write", "script": "hooks/guard-generated-files.py" },
    { "toolName": "Edit", "script": "hooks/guard-generated-files.py" }
  ],
  "Stop": [
    { "script": "hooks/trigger-doc-sync.py" }
  ]
}
```

### Layer 2: Secret Blocking (`hooks/block-secrets.py`)

Runs **before every Bash command**. Blocks if it detects:

```python
SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",                    # AWS Access Key
    r"password\s*=\s*['\"][^'\"]*['\"]",    # password="secret"
    r"api_key\s*=\s*['\"][^'\"]*['\"]",     # api_key="secret"
    r"-----BEGIN RSA PRIVATE KEY-----",     # Private keys
    r"--password\s+\S+",                     # --password secret
    r"--api.?key\s+\S+",                     # --api-key secret
]
```

**Example:**
```bash
# User tries: echo 'AKIA1234567890123456' > .env
# Hook runs → Pattern matches → BLOCKED
# Output: "ERROR: Command appears to contain secrets. Blocked for safety."
```

### Layer 3: Generated File Protection (`hooks/guard-generated-files.py`)

Runs **before every Write/Edit**. Protects critical config:

```python
PROTECTED_PATHS = [
    ".claude/CLAUDE.md",      # Pipeline rules
    ".claude/settings.json",  # Hook & MCP config
    ".claude/commands/",      # User commands
    ".claude/agents/",        # Agent definitions
]
ALLOWED_PATHS = [
    ".claude/hooks/",         # Custom hooks OK
    ".claude/skills/",        # Custom skills OK
    ".claude/projects/",      # Memory OK
]
```

**Example:**
```bash
# User tries to edit .claude/CLAUDE.md
# Hook runs → Path matches PROTECTED_PATHS → BLOCKED
# Output: "ERROR: This file is protected from accidental edits."
```

### Layer 4: Runtime Traceability Guardrail (`generator.py`)

**Fail-fast at generation time** - prevents invalid artifacts from ever being written:

```python
def assert_traceable(content: str, req_set: RequirementSet) -> None:
    known = {r.req_id for r in req_set.requirements}  # e.g., {"US-1", "FR-1", "NFR-1"}
    cited = extract_trace_ids(content)                  # IDs found in generated text
    unknown = cited - known                             # IDs that don't exist
    
    if unknown:
        raise TraceabilityError(f"Unknown IDs: {unknown}")
```

**Test proves it works** (`tests/test_traceability.py`):
```python
def test_write_all_artifacts_fails_fast_on_bad_generator(tmp_path):
    req_set = build_requirement_set(_story())
    
    # Inject a fake ID "US-99" into PR.md generator
    gen.generate_pr_md = lambda rs: original(rs).replace("US-1", "US-99")
    
    # Must raise BEFORE any file is written
    with pytest.raises(TraceabilityError, match="US-99"):
        write_all_artifacts(req_set, tmp_path)
```

---

## 3. Hooks (Automation Triggers)

Three hooks defined in `.claude/settings.json` that run automatically:

| Hook | When It Runs | What It Does |
|------|--------------|--------------|
| **block-secrets** | Before every `Bash` tool use | Scans command for secrets, blocks if found |
| **guard-generated** | Before every `Write`/`Edit` tool use | Blocks edits to protected `.claude/` files |
| **trigger-doc-sync** | On `Stop` (session end) | Checks if `src/` changed but `/doc-sync` wasn't run |

### Flow Diagram

```
User: "Run bash command"
       │
       ▼
┌──────────────────┐
│ PreToolUse(Bash) │
│  block-secrets   │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
  PASS      BLOCK
    │         │
    ▼         ▼
Command   Error shown,
runs      command stopped
```

```
Session ends (user types /exit or closes)
       │
       ▼
┌──────────────────┐
│     Stop         │
│ trigger-doc-sync │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
  PASS      BLOCK
    │         │
    ▼         ▼
Exit OK   "src/ changed!
          Run /doc-sync first"
```

---

## 4. Test Coverage & Code Coverage

### Configuration (`.github/workflows/tests.yml`)

```yaml
- name: Run tests
  run: pytest -v --cov=src/documentation_sync --cov-report=term-missing --cov-fail-under=80
```

- **Target**: ≥80% coverage (enforced in CI)
- **Actual**: 81% achieved (per git history)
- **Scope**: `src/documentation_sync` package only

### Test Suite (14 files, ~70 tests)

| File | Tests | What It Covers |
|------|-------|----------------|
| `test_validator.py` | 5 | Story & requirement validation |
| `test_llm_orchestrator.py` | 6 | Clarifying Q&A flow |
| `test_traceability.py` | 6 | Fail-fast traceability (M4) |
| `test_generator.py` | 8 | All artifact generation |
| `test_doc_validator.py` | 20 | Document quality checks |
| `test_providers.py` | ~10 | LLM provider adapters |
| `test_checkpoint.py` | ~8 | Phase checkpoint/resume |
| `test_tokens.py` | ~10 | Token counting (3 methods) |
| `test_log.py` | ~8 | Structured JSON logging |
| `test_phased_generator.py` | ~8 | 4-phase flow with gates |
| `test_jira_connector.py` | ~8 | Jira API integration |
| `test_input_handler.py` | ~8 | Story input parsing |
| `test_integration.py` | ~8 | End-to-end CLI |
| `test_jira_mcp_server.py` | ~8 | MCP server tools |

### Run Locally

```bash
# Full coverage report
pytest --cov=src/documentation_sync --cov-report=term-missing

# With fail-under (CI mode)
pytest --cov=src/documentation_sync --cov-fail-under=80
```

**Sample Output:**
```
Name                                    Stmts   Miss  Cover
---------------------------------------------------------------
src/documentation_sync/__init__.py          7      0   100%
src/documentation_sync/checkpoint.py       45      2    95%
src/documentation_sync/cli.py              82      5    93%
src/documentation_sync/config.py           98      8    91%
src/documentation_sync/doc_validator.py   112     12    89%
src/documentation_sync/generator.py       105     15    85%
src/documentation_sync/llm_orchestrator.py 64      8    87%
src/documentation_sync/log.py             56      7    87%
src/documentation_sync/models.py          25      0   100%
src/documentation_sync/parser.py          42      5    88%
src/documentation_sync/phased_generator.py 68      9    86%
src/documentation_sync/providers.py       145     22    84%
src/documentation_sync/resilience.py      52      8    84%
src/documentation_sync/tokens.py          78      9    88%
src/documentation_sync/validator.py       41      3    92%
---------------------------------------------------------------
TOTAL                                    920     93    89%
```

---

## 5. Observability (What You Can See)

### Structured JSON Logging (`src/documentation_sync/log.py`)

Every log line is a **single JSON object** - parseable, queryable, no regex needed.

```python
# Setup (once at startup)
setup_logging(level="INFO")

# Get logger
log = get_logger("docsync.providers")

# Log with structured fields
log.info("phase_complete", phase="requirements", artifact="requirements.md")
log.debug("prompt_built", llm_tokens_in=310, token_method="anthropic")
log.warning("token_budget_high", llm_tokens_in=165000, warning_limit=160000)
```

**Output:**
```json
{"timestamp":"2026-08-13T10:00:00Z","level":"INFO","logger":"docsync.providers","event":"phase_complete","phase":"requirements","artifact":"requirements.md"}
{"timestamp":"2026-08-13T10:00:01Z","level":"DEBUG","logger":"docsync.providers","event":"prompt_built","llm_tokens_in":310,"token_method":"anthropic","over_warning_threshold":false}
{"timestamp":"2026-08-13T10:00:02Z","level":"WARNING","logger":"docsync.providers","event":"token_budget_high","llm_tokens_in":165000,"warning_limit":160000,"event":"prompt uses >80% of context window"}
```

### Key Observable Events

| Event | When | Fields |
|-------|------|--------|
| `prompt_built` | Before LLM call | `llm_tokens_in`, `token_method`, `over_warning_threshold` |
| `token_budget_high` | Prompt >80% window | `llm_tokens_in`, `warning_limit` |
| `clarifying_questions_generated` | After LLM response | `llm_tokens_out`, `fallback_triggered` |
| `llm_call_failed` | LLM error | `exception`, `fallback_triggered` |
| `phase_complete` | Each phase done | `phase`, `artifact`, `phase_latency_ms` |
| `Retrying` | Transient failure | `function`, `attempt`, `max_retries`, `delay`, `error` |

### CI Visibility

```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: pytest -v --cov=src/documentation_sync --cov-report=term-missing --cov-fail-under=80
```

Outputs per-module coverage in GitHub Actions logs for every PR.

---

## 6. Evaluation (How We Know It Works)

Four layers of evaluation, from automated to human.

### Layer 1: Document Quality Validation (`doc_validator.py`)

**Runs in CI on every PR** (`docsync-verify`):

```python
# 1. Structure check - every artifact has required sections
REQUIRED_SECTIONS = {
    "requirements.md":      ["Story Summary", "Description", "Traceability Matrix", "Clarifications"],
    "architecture.md":      ["Overview", "Components", "Requirements Addressed"],
    "design-review.md":     ["Design Summary", "Risks", "Review Outcome"],
    "impl-plan.md":         ["Steps", "Test Strategy"],
    "code-review.md":       ["Scope", "Findings", "Outcome"],
    "verification-report.md": ["Test Execution Summary", "Integration Verification",
                                "Traceability Verification", "Artifact Quality Check", "Outcome"],
    "CHANGELOG.md":         ["Overview", "Changes", "Known Limitations"],
    "PR.md":                ["Summary", "Traceability", "Verification"],
}

# 2. Traceability check - downstream cites only IDs from requirements.md
# 3. Story parity check - FR-1..n match acceptance criteria exactly
```

**Run manually:**
```bash
docsync-verify output/ --story user-story.md
# Document quality OK (8 artifacts checked + story parity).
```

### Layer 2: Drift Detection (`.github/workflows/doc-sync.yml`)

**Runs on every push/PR** - fails if committed artifacts don't match generator output:

```yaml
- name: Verify generator still produces valid artifacts
  run: |
    docsync user-story.md -o regenerated
    docsync-verify regenerated --story user-story.md
```

If someone hand-edits `requirements.md` but doesn't regenerate, CI catches it.

### Layer 3: Runtime LLM Evaluation (`providers.py`)

```python
def generate_clarifying_questions(self, story: JiraStory) -> List[str]:
    # 1. Token budgeting
    prompt = self._build_prompt(story)
    
    # 2. Retry with exponential backoff on transient failures
    text = retry(self._sdk_call, prompt, max_retries=3, base_delay=1.0)
    
    # 3. Validate response format
    try:
        parsed = json.loads(text)  # Must be valid JSON array
    except JSONDecodeError:
        log.warning("llm_response_not_json", fallback_triggered=True)
        return _heuristic_questions(story)  # Graceful degradation
    
    # 4. Log for cost monitoring
    log.info("clarifying_questions_generated", llm_tokens_out=out_count.count)
    return parsed[:3]
```

### Layer 4: Human Gates (3 approval points)

| Gate | Step | Artifact | Who Approves |
|------|------|----------|--------------|
| **Design Review** | 3 | `claude-design-review.md` | Human in chat |
| **Verification** | 7 | `claude-verification-report.md` + test results | Human in chat |
| **Merge** | 8 | PR + CI checks | Human on GitHub |

**Example approval:**
```
# Step 3 gate
User: "Approved. Proceed with implementation planning."

# Step 7 gate  
User: "All tests passing, coverage 92%. Proceed to Step 8."
```

---

## Summary Table

| Concern | Solution | File |
|---------|----------|------|
| **Token costs** | Count + truncate before LLM call | `tokens.py`, `providers.py` |
| **Secret leaks** | Pre-Bash hook scans commands | `hooks/block-secrets.py` |
| **Config corruption** | Pre-Write/Edit hook protects `.claude/` | `hooks/guard-generated-files.py` |
| **Doc drift** | Stop hook reminds to run `/doc-sync` | `hooks/trigger-doc-sync.py` |
| **Bad traceability** | Fail-fast at generation time | `generator.py:assert_traceable()` |
| **Test coverage** | pytest-cov with --cov-fail-under=80 | `.github/workflows/tests.yml` |
| **Observability** | Structured JSON logs + token metrics | `log.py`, `providers.py` |
| **Doc quality** | `docsync-verify` checks structure + traceability | `doc_validator.py` |
| **Drift detection** | CI regenerates + verifies | `.github/workflows/doc-sync.yml` |
| **LLM quality** | JSON validation + fallback + logging | `providers.py` |
| **Human oversight** | 3 gates with chat approvals | `.claude/CLAUDE.md` |

---

## Quick Commands Reference

```bash
# Generate all artifacts (one-shot)
docsync user-story.md -o output/

# Generate with phased flow (interactive gates)
docsync user-story.md --phased -o output/

# Verify artifacts
docsync-verify output/ --story user-story.md

# Run tests with coverage
pytest --cov=src/documentation_sync --cov-report=term-missing

# View structured logs (run with LOG_LEVEL=DEBUG)
LOG_LEVEL=DEBUG docsync user-story.md -o output/
```
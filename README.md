# Automated Documentation Sync

Automated Documentation Sync turns a Jira-style story into traceable SDLC artifacts and provides verification checks to keep requirements, architecture, review notes, and release documentation aligned.

This repository supports two distinct workflows:
1. A product workflow: the `docsync` CLI and Python package in `src/documentation_sync/`.
2. An authoring workflow: GitHub Copilot Chat and Claude-based SDLC pipelines that produce reviewable artifacts.

## Repository Guide
1. Overall project: `README.md`
2. GitHub Copilot workflow: `.github/README.md`
3. Claude workflow: `.claude/README.md`
4. Copilot operating model details: `docs/copilot-operating-model.md`
5. Claude rules and gates: `CLAUDE.md`

## What The Product Does
1. Accepts story input as a local JSON file, Markdown file, full Jira URL, bare Jira issue key, or pasted text.
2. Normalizes the story into a structured model with title, description, acceptance criteria, and metadata.
3. Generates SDLC artifacts with stable traceability IDs (`US-1`, `FR-n`, `NFR-n`).
4. Validates both story input and generated artifact quality.

## Project Layout
```text
src/documentation_sync/   Core CLI, parser, validator, generator, Jira integration, verifier
tests/                    Unit and integration tests
.github/                  GitHub Copilot prompts, instructions, workflows
.claude/                  Claude commands, agents, skills, hooks, MCP settings
samples/                  Example local story inputs
docs/                     Explanatory and operating-model documentation
github-copilot-output/    Default generated output for CLI / Copilot runs (gitignored)
claude-output/            Default generated output for Claude CLI runs (gitignored)
```

## Installation
```bash
pip install -e .
```

Optional extras:
```bash
pip install -e ".[url-ingestion,mcp-tools,test]"
```

## Local Jira Configuration
For full Jira URL input, set a token:
```bash
set JIRA_API_TOKEN=your-token
```

For bare issue-key input such as `EPMCDMETST-55568`, also provide a Jira base URL either by environment variable:
```bash
set JIRA_BASE_URL=https://jiraeu.epam.com
```

or by creating a local `docsync.config.json` file from `docsync.config.example.json`:
```json
{
	"jira_base_url": "https://jiraeu.epam.com"
}
```

`docsync.config.json` is intentionally gitignored.

## CLI Usage
Generate artifacts from a local sample story:
```bash
python -m documentation_sync.cli samples/jira_story.json
```

Generate from a live Jira issue key:
```bash
python -m documentation_sync.cli EPMCDMETST-55568 --phased --non-interactive
```

Generate from a full Jira URL:
```bash
python -m documentation_sync.cli https://jiraeu.epam.com/browse/EPMCDMETST-55568 --phased --non-interactive
```

Choose a specific output directory when needed:
```bash
python -m documentation_sync.cli samples/jira_story.json -o out
```

Default output behavior:
1. No `-o` and no `--llm claude`: `github-copilot-output`
2. No `-o` and `--llm claude`: `claude-output`
3. Explicit `-o`: always wins

## Verification And Tests
Run the full test suite:
```bash
python -m pytest -q --cov=src/documentation_sync --cov-report=term-missing
```

Verify generated artifacts:
```bash
python -m documentation_sync.doc_validator github-copilot-output --story user-story.md
```

## MCP Support
This repo ships a custom MCP server for Jira-aware operations:
1. Server implementation: `src/documentation_sync/jira_mcp_server.py`
2. Copilot MCP config: `.mcp.json`
3. Claude MCP config: `.claude/settings.json`

Supported MCP tools:
1. `fetch_jira_story`
2. `run_sdlc_pipeline`
3. `get_artifact_status`
4. `validate_jira_url`

## Commit-Ready Notes
Track these as source assets:
1. `src/`, `tests/`, `.github/`, `.claude/`, `README.md`, `CLAUDE.md`
2. Prompt and MCP config files

Treat these as generated output unless you explicitly want them versioned as review artifacts:
1. `github-copilot-output/`
2. `claude-output/`
3. Root-level `claude-*.md` files
4. Root-level phase artifacts such as `requirements.md`, `architecture.md`, and `PR.md`

Only commit generated artifacts if they are part of the deliverable for your current branch.

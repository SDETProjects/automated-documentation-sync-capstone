# Claude Workflow

This repository includes a Claude-oriented SDLC pipeline under `.claude/`. Use this README when you want to run the project through Claude Code rather than GitHub Copilot Chat.

## What Lives Under `.claude/`
1. `commands/` contains the user-facing slash commands.
2. `agents/` contains the execution agents used by those commands.
3. `skills/` contains reusable workflows.
4. `hooks/` contains local safeguards and exit checks.
5. `settings.json` registers MCP servers, permissions, and hooks.

Current tracked skills in this repository are only the ones that actually exist:
1. `requirements-elicitor`
2. `pr-generator`

## Prerequisites
1. Install Claude Code CLI.
2. Authenticate with Claude.
3. Open this repository as the current working directory.
4. Ensure Python dependencies are installed for the local MCP server and Jira access.

Example setup:
```bash
npm install -g @anthropic-ai/claude-code
claude auth login
pip install -e ".[url-ingestion,mcp-tools,test]"
```

## Main Commands
1. `/run-pipeline`
2. `/step-1-requirements`
3. `/step-2-architecture`
4. `/step-3-design-review`
5. `/step-4-impl-plan`
6. `/step-5-implement`
7. `/step-6-code-review`
8. `/step-7-verify`
9. `/step-8-create-pr`
10. `/doc-sync`

## Recommended Claude Flow
Run the full pipeline:
```text
/run-pipeline EPMCDMETST-55568
```

Or run step by step:
```text
/step-1-requirements
/step-2-architecture
/step-3-design-review
/step-4-impl-plan
/step-5-implement
/step-6-code-review
/step-7-verify
/step-8-create-pr
```

## Output Behavior
1. Claude phase artifacts use the `claude-` prefix.
2. Shared implementation still lands in `src/` and `tests/`.
3. CLI runs with `--llm claude` default to `claude-output/` when `-o` is not provided.

Expected artifact set:
1. `claude-requirements.md`
2. `claude-architecture.md`
3. `claude-design-review.md`
4. `claude-impl-plan.md`
5. `claude-code-review.md`
6. `claude-verification-report.md`
7. `claude-pr-description.md`

## MCP In Claude
Claude uses `.claude/settings.json` for MCP registration. The current setup includes:
1. `docsync-jira`
2. `github`
3. `filesystem`

The custom `docsync-jira` server is implemented in `src/documentation_sync/jira_mcp_server.py`.

## Jira Requirements For Claude Runs
For live Jira fetches you need:
1. `JIRA_API_TOKEN` or `JIRA_TOKEN`
2. `JIRA_BASE_URL` or local `docsync.config.json` for bare issue-key input
3. `JIRA_EMAIL` only when the target Jira host uses Atlassian Cloud basic auth

## Verification
Run tests:
```bash
python -m pytest -q --cov=src/documentation_sync --cov-report=term-missing
```

Run artifact verification:
```bash
python -m documentation_sync.doc_validator claude-output --story user-story.md
```

## Related Files
1. `README.md`
2. `.github/README.md`
3. `CLAUDE.md`
4. `.claude/settings.json`
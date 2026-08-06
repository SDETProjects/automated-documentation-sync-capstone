# GitHub Copilot Workflow

This repository supports GitHub Copilot as an interactive SDLC authoring workflow inside VS Code. Use this README when you want Copilot Chat to guide or execute the eight pipeline steps.

## What Copilot Is Responsible For
1. Driving the SDLC conversation step by step.
2. Drafting and refining the root-level phase artifacts.
3. Asking clarifying questions and pausing at approval gates.

## What Copilot Is Not
Copilot is not exposed here as a programmatic Python API. The CLI accepts `--llm copilot`, but that is not a true headless Copilot invocation. The supported Copilot path in this repository is VS Code Copilot Chat plus the prompt files under `.github/prompts/`.

## Required Files
1. Prompt entrypoint: `.github/prompts/run-pipeline.prompt.md`
2. Step prompts:
   - `.github/prompts/step-1-requirements.prompt.md`
   - `.github/prompts/step-2-architecture.prompt.md`
   - `.github/prompts/step-3-design-review.prompt.md`
   - `.github/prompts/step-4-impl-plan.prompt.md`
   - `.github/prompts/step-5-code-review.prompt.md`
   - `.github/prompts/step-6-pr.prompt.md`
   - `.github/prompts/step-7-verify.prompt.md`
   - `.github/prompts/step-8-create-pr.prompt.md`
3. Global Copilot rules: `.github/copilot-instructions.md`
4. Operating model: `docs/copilot-operating-model.md`

## How To Run In VS Code Copilot Chat
1. Open the repository in VS Code.
2. Open GitHub Copilot Chat.
3. Run the orchestrator prompt with a Jira issue key:
   `/run-pipeline EPMCDMETST-55568`
4. Approve or revise at the required gates.

## How Copilot Pipeline Works Here
1. Copilot reads `.github/copilot-instructions.md` automatically.
2. The orchestrator prompt loads the step prompt files in order.
3. Step 1 creates `requirements.md`.
4. Step 2 creates `architecture.md`.
5. Step 3 creates `design-review.md` and pauses for approval.
6. Step 4 creates `impl-plan.md`.
7. Step 5 creates `code-review.md`.
8. Step 6 creates `verification-report.md` and pauses for approval.
9. Step 7 covers code and tests.
10. Step 8 updates `CHANGELOG.md` and `PR.md`, then pauses for final approval.

## Verification Commands
Run tests:
```bash
python -m pytest -q --cov=src/documentation_sync --cov-report=term-missing
```

Run artifact verification:
```bash
python -m documentation_sync.doc_validator . --story user-story.md
```

## Jira Inputs In Copilot Flow
Copilot prompts may refer to a Jira issue key directly, but actual fetch support still depends on runtime configuration:
1. `JIRA_API_TOKEN` or `JIRA_TOKEN`
2. `JIRA_BASE_URL` or `docsync.config.json`

Without those, the workflow can still proceed using a local story file or pasted story text.

## Recommended Working Style
1. Use Copilot Chat for discussion, design, and gate approvals.
2. Use the CLI and verifier for deterministic generation and checks.
3. Keep generated output directories (`github-copilot-output/`) out of version control unless needed for review.

## Related Files
1. `README.md`
2. `.claude/README.md`
3. `docs/copilot-operating-model.md`
4. `.mcp.json`
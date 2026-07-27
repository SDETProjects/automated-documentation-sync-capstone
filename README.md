# Automated Documentation Sync (Capstone)

A small Python project that takes a Jira-style user story, refines it into structured requirements, and generates the supporting SDLC documentation artifacts (architecture, design review, implementation plan, and PR description) with full traceability.

## Why
Manually keeping requirements, architecture notes, and PR descriptions in sync with a Jira story is error-prone. This project demonstrates a minimal, testable engine that automates that sync from a single source of truth: the story itself.

## What It Does
1. Reads a Jira-style story from `samples/jira_story.json` (JSON or Markdown supported).
2. Converts the story into `requirements.md` with traceability IDs (`US-1`, `FR-n`, `NFR-1`).
3. Generates `architecture.md`, `design-review.md`, `impl-plan.md`, and `PR.md` from the approved requirements.
4. Validates input and reports clear errors instead of producing partial documentation.

## Project Structure
```
src/documentation_sync/   # parser, validator, generator, cli, models
tests/                    # pytest suite (parser, validator, generator, integration)
samples/                  # example Jira-style story input
docs/traceability/        # Jira story template for new inputs
evidence/                 # PR automation evidence
.github/                  # Copilot instructions, prompts, PR template, CI workflow
```

## Getting Started
```bash
pip install -e .
python -m documentation_sync.cli samples/jira_story.json -o .
```

Or, once installed as a console script:
```bash
docsync samples/jira_story.json -o .
```

## Running Tests
```bash
pytest -v
```

See `test-evidence.md` for expected results and `evidence/pr-automation-evidence.md` for PR workflow evidence.

## Source Story
Example story: [EPMCDMETST-55568](https://jiraeu.epam.com/browse/EPMCDMETST-55568), sample input in `samples/jira_story.json`.

## Generated Artifacts
`requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `code-review.md`, `PR.md`, `test-evidence.md` in the repository root demonstrate the full generated output for the sample story.

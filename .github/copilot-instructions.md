# Copilot Instructions: Automated Documentation Sync

This repository automates SDLC documentation generation from a Jira-style user story.

## Two pipelines — do not conflate them

| | Pipeline A — Process | Pipeline B — Product |
|---|---|---|
| What | The agentic SDLC we *perform* to build this repo | The `docsync` tool this repo *ships* |
| Driven by | GitHub Copilot Chat + `.github/prompts/` 01-06 | `src/documentation_sync/` |
| Artifacts | The `.md` files at repo root | Whatever the user generates into `-o <dir>` |

Root-level `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`,
`code-review.md`, `PR.md` are **Pipeline A** artifacts: they describe `docsync` itself.

## Mandatory workflow (Pipeline A)

**Quick start:** `/run-pipeline JIRA-ID` in Copilot Chat to orchestrate all 8 steps.

Or drive steps manually from `.github/prompts/` in order:

```
step-1-requirements → step-2-architecture → step-3-design-review
→ step-4-impl-plan → step-5-code-review → step-6-pr
→ step-7-verify → step-8-create-pr
```

- No skipping. Each step consumes prior artifacts.
- Do not hand-author an artifact from scratch. Refining Copilot output is expected;
  inventing artifacts outside the prompt workflow is not.
- Requirement IDs (`US-n`, `FR-n`, `NFR-n`) are immutable (derived from the source story). 
  Prose may be refined; IDs may not drift. Enforced by `docsync-verify --story user-story.md`.

## Enforcement

| Gate | Mechanism | Scope | Artifacts checked |
|---|---|---|---|
| Document quality | `.githooks/pre-commit` | Local, at commit | All 8 steps |
| Document quality | `.github/workflows/tests.yml` | CI | All 8 steps |
| Story-to-artifact parity | `.github/workflows/doc-sync.yml` | CI | Steps 1-4 (generated) |
| Code coverage >=80% | `.github/workflows/tests.yml` | CI | tests/ |

Install the local hook once per clone:

```bash
git config core.hooksPath .githooks
```

## Code conventions

- Preserve traceability IDs (`US-1`, `FR-n`, `NFR-n`) across every generated artifact.
- Reuse the exception types in `validator.py` and `parser.py` (`StoryNotFoundError`,
  `StoryParseError`, `ValidationError`) for consistent CLI exit codes:
  2 = story not found, 1 = parse/validation failure, 0 = success.
- Network access is confined to `jira_connector.py`. The core parse -> validate -> generate
  path stays file-based and offline.
- Add or update tests in `tests/` for any change to parser, validator, generator, or CLI.

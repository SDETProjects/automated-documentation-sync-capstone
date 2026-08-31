# AGENTS.md — Workspace Instructions for GitHub Copilot

This repository implements an 8-step agentic SDLC pipeline for automated documentation sync.

## Two Pipelines — Do Not Conflate

| Pipeline | Driver | Agent files | Artifact prefix |
|---|---|---|---|
| **GitHub Copilot** | `.github/agents/*.agent.md` | `@requirements-analyst`, `@sdlc-orchestrator`, etc. | None (`requirements.md`) |
| **Claude Code** | `.claude/agents/*.md` | Dispatched via `/pipeline` skill | `claude-` (`claude-requirements.md`) |

## Key Principles

1. **No phase skipping** — Steps 1→8 must run in order; each step consumes the prior artifact
2. **Requirement IDs are immutable** — `US-1`, `FR-1..n`, `NFR-1..n` are derived from the source story and must not be renumbered
3. **Human gates at steps 3, 7, and 8** — Explicit approval required before proceeding
4. **Traceability throughout** — Every artifact cites the requirement IDs it addresses

## Available Agents

| Agent | Invoke with | Purpose | Gate |
|---|---|---|---|
| `requirements-analyst` | `@requirements-analyst` | Generate `requirements.md` from story | — |
| `software-architect` | `@software-architect` | Design `architecture.md` | — |
| `design-reviewer` | `@design-reviewer` | Review design, write `design-review.md` | **Gate 1** |
| `implementation-planner` | `@implementation-planner` | Break architecture into `impl-plan.md` | — |
| `code-developer` | `@code-developer` | Implement `src/` and `tests/` | — |
| `code-reviewer` | `@code-reviewer` | Review code, write `code-review.md` | Advisory |
| `qa-verifier` | `@qa-verifier` | Verify tests, write verification report | **Gate 2** |
| `release-engineer` | `@release-engineer` | Generate `PR.md` and `CHANGELOG.md` | **Gate 3 (CI)** |
| `sdlc-orchestrator` | `@sdlc-orchestrator` | Full 8-step pipeline | All gates |

## Quick Start

Run the full pipeline from a Jira story key:

```
@sdlc-orchestrator EPMCDMETST-55568
```

Or run individual steps:

```
@requirements-analyst
@software-architect
@design-reviewer
```

## Artifact Map

| Step | Agent | Output artifact |
|---|---|---|
| 1 | `requirements-analyst` | `requirements.md` |
| 2 | `software-architect` | `architecture.md` |
| 3 | `design-reviewer` | `design-review.md` |
| 4 | `implementation-planner` | `impl-plan.md` |
| 5 | `code-developer` | `src/`, `tests/` |
| 6 | `code-reviewer` | `code-review.md` |
| 7 | `qa-verifier` | `claude-verification-report.md` |
| 8 | `release-engineer` | `PR.md`, `CHANGELOG.md` |

## Enforcement

- Pre-commit hooks: Document structure and traceability IDs (`.githooks/pre-commit`)
- CI: Coverage ≥80% and `docsync-verify` must pass (`.github/workflows/tests.yml`)
- Gate 3: CI must be green before merge is allowed

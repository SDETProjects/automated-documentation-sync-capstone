---
name: sdlc-orchestrator
description: Orchestrate the full 8-step SDLC pipeline by sequentially dispatching specialized agents with state persistence and human gates
tools:
  - editFiles
  - runCommands
  - fetch
agents:
  - requirements-analyst
  - software-architect
  - design-reviewer
  - implementation-planner
  - code-developer
  - code-reviewer
  - qa-verifier
  - release-engineer
model: claude-haiku-4-5
argument-hint: "Jira story key, URL, or path to user-story.md (e.g. EPMCDMETST-55568)"
---

# SDLC Pipeline Orchestrator

Orchestrate the full 8-step SDLC pipeline by dispatching specialized agents and managing human approval gates.

## Usage

```
@sdlc-orchestrator EPMCDMETST-55568
```

## Story Resolution (before Step 1)

1. **Jira auto-fetch** — if argument is a key/URL and `JIRA_API_TOKEN` + `JIRA_BASE_URL` are set:
   ```bash
   docsync "${JIRA_BASE_URL}/browse/${ISSUE_KEY}" --jira-token "$JIRA_API_TOKEN" -o . --non-interactive
   ```
2. **Local file** — check for `user-story.md` at repository root
3. **User paste** — prompt: *"No story found. Paste the story text and press Enter twice."*

After resolving, confirm `user-story.md` exists before proceeding.

## Agent Dispatch Order

| Step | Agent | Gate |
|---|---|---|
| 1 | `@requirements-analyst` | No |
| 2 | `@software-architect` | No |
| 3 | `@design-reviewer` | **Gate 1 — human approval** |
| 4 | `@implementation-planner` | No |
| 5 | `@code-developer` | No |
| 6 | `@code-reviewer` | No (advisory) |
| 7 | `@qa-verifier` | **Gate 2 — human approval** |
| 8 | `@release-engineer` | **Gate 3 — CI required** |

Display progress after each step: `[2/8] Architecture complete ✓`

## Gate Handling

- **Gate 1 Rejection:** Re-dispatch `@software-architect` with design-review.md feedback; repeat Step 3
- **Gate 2 Failure:** Re-dispatch `@code-developer` with failing test diagnostics; repeat Steps 5–7
- **Gate 3:** Remind user to open PR and wait for CI — do not merge until CI is green

## State Persistence

After each step, record status and artifact path in `.github/pipeline-state.json`. On restart, read this file and resume from the last incomplete step.

> **Note:** This file is exclusively owned by the GitHub Copilot pipeline. The Claude Code pipeline maintains its own independent state in `.claude/pipeline-state.json`. The two state files must not be merged — their artifact names differ (`requirements.md` vs `claude-requirements.md`) and mixing them would corrupt both pipelines.

## Rules

- No phase skipping — user cannot jump to Step 5 without completing Steps 1–4
- Requirement IDs are immutable — US-1, FR-n, NFR-n set in Step 1 must not change
- Architecture is locked after Gate 1 — no structural changes allowed in Steps 5–8

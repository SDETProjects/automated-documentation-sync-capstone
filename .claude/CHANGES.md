# Claude Pipeline Configuration — Change Log

**Date:** 2026-08-20
**Author:** GitHub Copilot (Claude Sonnet 4.6)
**Scope:** `.claude/` workspace configuration for the 8-step Agentic SDLC Pipeline

---

## Phase 1 — Configuration Cleanup (`.claude/settings.json`)

**Target file:** `.claude/settings.json`
**Status:** ✅ Complete

### Changes Made

| # | Change                                                                            | Reason                                                                    |
| - | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 1 | Removed`GITHUB_PERSONAL_ACCESS_TOKEN` env var from `github` MCP server block  | Token belongs in environment, not in checked-in config (security hygiene) |
| 2 | Replaced nested`hooks[{type,command}]` array format with flat `script` string | Anthropic's current hook schema uses`script`, not `{type,command}`    |
| 3 | Removed`Stop` hook's `matcher: ""` wrapper                                    | `Stop` event hooks do not use matcher; empty string caused a warning    |
| 4 | Removed`permissions.allowlist` block                                            | Allowlist was moved to`settings.local.json` (per-user, not committed)   |
| 5 | Reformatted`args` arrays to multi-line for readability                          | Consistency with Anthropic docs examples                                  |

### Before / After Summary

```diff
- "github": { "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" } }
+ "github": {}   // no env block — token from shell environment

- "hooks": [{ "type": "command", "command": "..." }]
+ "script": "python .claude/hooks/block-secrets.py"

- "permissions": { "allowlist": [...] }
+ (removed — moved to settings.local.json)
```

---

## Phase 2 — State Persistence File (`.claude/pipeline-state.json`)

**Target file:** `.claude/pipeline-state.json` *(new file)*
**Status:** ✅ Complete

### Changes Made

Created a new JSON state tracking file for the 8-step SDLC pipeline with:

| Field            | Purpose                                                                    |
| ---------------- | -------------------------------------------------------------------------- |
| `pipeline_id`  | Identifier for the current pipeline run                                    |
| `current_step` | Index of the active step (0 = not started)                                 |
| `status`       | Overall pipeline status (`NOT_STARTED` / `IN_PROGRESS` / `COMPLETE`) |
| `updated_at`   | ISO-8601 timestamp of last state mutation                                  |
| `steps.*`      | Per-step status, artifact path, agent name, and gate decision              |
| `history`      | Append-only log of gate decisions and rollback events                      |

### Key Design Decisions

- Steps 3 and 7 have `gate_status: "AWAITING_HUMAN_APPROVAL"` — these are blocking gates.
- `gate_decision: null` until human explicitly approves or rejects.
- `history: []` starts empty; orchestrator appends entries on gate decisions and rollbacks.
- `"$schema"` field enables JSON Schema validation in editors.

---

## Phase 3 — Subagent Specifications (`.claude/agents/*.md`)

**Target directory:** `.claude/agents/`
**Status:** ✅ Complete

### Files Created

| File                          | Role                                                         | Model      | Gate      |
| ----------------------------- | ------------------------------------------------------------ | ---------- | --------- |
| `orchestrator.md`           | Master pipeline driver; dispatches subagents; enforces gates | `opus`   | —        |
| `requirements-analyst.md`   | Step 1 — extracts US/FR/NFR IDs from story                  | `sonnet` | —        |
| `software-architect.md`     | Step 2 — designs components linked to FR IDs                | `sonnet` | —        |
| `design-reviewer.md`        | Step 3 — reviews arch for risks and security                | `sonnet` | ✋ Gate 1 |
| `implementation-planner.md` | Step 4 — task breakdown per impl plan                       | `sonnet` | —        |
| `code-developer.md`         | Step 5 — implements`src/` + `tests/` (≥80% coverage)   | `sonnet` | —        |
| `code-reviewer.md`          | Step 6 — static analysis and review findings                | `sonnet` | —        |
| `qa-verifier.md`            | Step 7 — test runner metrics and coverage                   | `sonnet` | ✋ Gate 2 |
| `release-engineer.md`       | Step 8 — CHANGELOG + PR description                         | `sonnet` | —        |

### Format Changes vs Legacy Agents

Legacy agents (`step-N-*-agent.md`) had no YAML frontmatter and used free-form markdown.
New agents use standardized YAML frontmatter:

```yaml
---
name: <agent-name>
description: <one-line description>
tools:
  - Read
  - Write
  - Glob
  - Grep
model: sonnet|opus
---
```

**Legacy files retained** (not deleted) to avoid breaking existing references in `CLAUDE.md` step table and command definitions. New files coexist.

---

## Phase 4 — User Slash Command Skill (`.claude/skills/pipeline/SKILL.md`)

**Target file:** `.claude/skills/pipeline/SKILL.md` *(new file)*
**Status:** ✅ Complete

### Changes Made

Created a `/pipeline` skill entry point under `.claude/skills/pipeline/SKILL.md` that:

1. Reads `.claude/pipeline-state.json` for current pipeline state.
2. Dispatches the `orchestrator` subagent to drive the full 8-step run.
3. Explicitly calls out human pause gates at Step 3 (Design Review) and Step 7 (Verification).

This joins the two existing skills (`pr-generator/SKILL.md`, `requirements-elicitor/SKILL.md`) and provides a single entry point for end-to-end pipeline execution.

---

## Phase 5 — Workspace Guidance (`.claude/CLAUDE.md`)

**Target file:** `.claude/CLAUDE.md`
**Status:** ✅ Complete

### Changes Made

Replaced the `Settings & Configuration` section with a richer block containing three new sections:

| Section Added                                  | Content                                                                                                              |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Custom Instructions vs Agent Prompts** | Distinguishes`CLAUDE.md` (global system context) from `.claude/agents/*.md` (per-agent role prompts)             |
| **Architecture & Handoff Model**         | Documents the Ritchie Modular Agent Architecture, orchestrator role, rollback logic, and the full agent roster table |
| **State Persistence**                    | Explains`.claude/pipeline-state.json` — step statuses, gate decisions, session resumption, and rollback triggers  |

The `Settings & Configuration` section was preserved with a simplified bullet list (removed stale reference to `Permission allowlist` since that block was removed in Phase 1).

---

## Summary of All Files Changed or Created

| Phase | File                                         | Action   |
| ----- | -------------------------------------------- | -------- |
| 1     | `.claude/settings.json`                    | Modified |
| 2     | `.claude/pipeline-state.json`              | Created  |
| 3     | `.claude/agents/orchestrator.md`           | Created  |
| 3     | `.claude/agents/requirements-analyst.md`   | Created  |
| 3     | `.claude/agents/software-architect.md`     | Created  |
| 3     | `.claude/agents/design-reviewer.md`        | Created  |
| 3     | `.claude/agents/implementation-planner.md` | Created  |
| 3     | `.claude/agents/code-developer.md`         | Created  |
| 3     | `.claude/agents/code-reviewer.md`          | Created  |
| 3     | `.claude/agents/qa-verifier.md`            | Created  |
| 3     | `.claude/agents/release-engineer.md`       | Created  |
| 4     | `.claude/skills/pipeline/SKILL.md`         | Created  |
| 5     | `.claude/CLAUDE.md`                        | Modified |

**No files were deleted.** Legacy agent files (`pipeline-orchestrator.md`, `step-N-*-agent.md`) are retained for backward compatibility.

# /doc-sync

**Sync and index all documentation artifacts.**

## Role

Documentation coordinator that generates a manifest of all SDLC artifacts.

## Task

Scan the repository for all Claude Code and Copilot Chat artifacts and generate:
- **`docs/claude-synced-output.md`:** Index of all Claude Code artifacts
- **`docs/copilot-synced-output.md`:** Index of all Copilot Chat artifacts (optional)
- Both files include artifact status (complete, in-progress, missing)

## Context

- **Input:** All artifacts in the repo (requirements, architecture, code, tests, etc.)
- **Output:** `docs/claude-synced-output.md` with manifest
- **Audience:** Pipeline orchestrators, reviewers, stakeholders
- **When to run:** After each step, or on demand

## Constraints

- Scan must be fast (under 5 seconds)
- Ignore build artifacts, cache files, `.git/`
- Only index markdown (`.md`) and source files (`src/`)

## Inputs

1. Repository structure (all files)

## Outputs / Output format

```markdown
# Claude Code Artifacts — Synced Output

**Last synced:** 2026-08-04 12:34:56 UTC

## Pipeline Status

| Step | Artifact | Status | Modified | Size |
|---|---|---|---|---|
| 1 | `claude-requirements.md` | ✓ Complete | 2026-08-04 11:22 | 2.4 KB |
| 2 | `claude-architecture.md` | ✓ Complete | 2026-08-04 11:45 | 3.1 KB |
| 3 | `claude-design-review.md` | ✓ Complete | 2026-08-04 12:02 | 2.8 KB |
| 4 | `claude-impl-plan.md` | ✓ Complete | 2026-08-04 12:15 | 1.9 KB |
| 5 | `src/` | ✓ Complete | 2026-08-04 12:22 | 12.5 KB |
| 5 | `tests/` | ✓ Complete | 2026-08-04 12:22 | 8.3 KB |
| 6 | `claude-code-review.md` | ⏳ In Progress | — | — |
| 7 | `claude-verification-report.md` | ⏳ In Progress | — | — |
| 8 | `claude-pr-description.md` | — | — | — |

## Artifact Details

### Step 1: Requirements
- **File:** `claude-requirements.md`
- **Size:** 2.4 KB
- **Content:** US-1, FR-1..3, NFR-1..2, ACs, clarifications
- **Last modified:** 2026-08-04 11:22
- **Status:** ✓ Complete

### Step 2: Architecture
- **File:** `claude-architecture.md`
- **Size:** 3.1 KB
- **Content:** Components, data flow, APIs, technology stack, risks preview
- **Last modified:** 2026-08-04 11:45
- **Status:** ✓ Complete

### Step 3: Design Review
- **File:** `claude-design-review.md`
- **Size:** 2.8 KB
- **Content:** Risk analysis, mitigations, alternatives, confidence, approval status
- **Last modified:** 2026-08-04 12:02
- **Status:** ✓ Complete

### Step 4: Implementation Plan
- **File:** `claude-impl-plan.md`
- **Size:** 1.9 KB
- **Content:** Task breakdown, dependencies, effort estimate, testing strategy
- **Last modified:** 2026-08-04 12:15
- **Status:** ✓ Complete

### Step 5: Implementation
- **Files:** `src/`, `tests/`
- **Size:** 12.5 KB (src) + 8.3 KB (tests)
- **Content:** Code + unit, integration, E2E tests
- **Last modified:** 2026-08-04 12:22
- **Status:** ✓ Complete
- **Coverage:** 92% (pytest output)

### Step 6: Code Review
- **File:** `claude-code-review.md`
- **Status:** ⏳ In Progress (not yet generated)

### Step 7: Verification
- **File:** `claude-verification-report.md`
- **Status:** ⏳ In Progress (not yet generated)

### Step 8: PR & Changelog
- **File:** `claude-pr-description.md`
- **Status:** Not yet started

## Copilot Chat Artifacts (Optional)

Same structure as above, for `requirements.md`, `architecture.md`, etc. (without `claude-` prefix).

## Summary

- **Complete:** 5/8 steps
- **In Progress:** 2/8 steps
- **Not started:** 1/8 steps
- **Overall progress:** 62.5%
- **Last update:** 2026-08-04 12:34:56

## Next Action

Continue with `/step-6-code-review` to advance the pipeline.
```

## Completion criteria

- [ ] `docs/claude-synced-output.md` exists
- [ ] All steps listed with status
- [ ] Modified timestamps included
- [ ] Size and content summary for each artifact
- [ ] Overall progress percentage shown

---

## When to Run

- **Automatically:** After `/step-N` completes
- **Manually:** On demand with `/doc-sync`
- **Periodically:** To check pipeline status

---

## See Also

- `.claude/CLAUDE.md` — Pipeline overview
- [README-CLAUDE.md](../../README-CLAUDE.md) — Quick-start guide

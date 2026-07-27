# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 8-Phase Agentic SDLC Pipeline

**Automated Documentation Sync** follows a strict 8-phase workflow. Once approved, each phase's artifacts are locked (read-only). No skipping phases. Human approval required at phases 4, 6, and 8.

### Phase 1: Parse & Validate
**Deliverable:** `requirements.md` | **Checklist:** Story loads without error; all required fields present; acceptance criteria ≥1
**Done:** Traceability IDs (US-1, FR-n, NFR-1) generated and unique

### Phase 2: Architecture
**Deliverable:** `architecture.md` | **Checklist:** Maps all FR requirements; identifies components; no implementation detail
**Done:** Design review checklist populated for Phase 4

### Phase 3: Design Review
**Deliverable:** `design-review.md` | **Checklist:** Risks identified; alternatives considered; assumptions explicit
**Approval Gate:** ⏸ Human sign-off required. No coding proceeds without approval.

### Phase 4: Implementation Plan
**Deliverable:** `impl-plan.md` | **Checklist:** Step-by-step tasks from requirements; test strategy explicit (happy path + edge cases)
**Done:** Test structure drafted; test cases listed (not yet implemented)

### Phase 5: Test Coverage
**Deliverable:** Test suite (`tests/test_*.py`) | **Checklist:** Happy path tests pass; edge case tests present; coverage ≥80%
**Done:** All tests run green; coverage report generated

### Phase 6: Code Review
**Deliverable:** `code-review.md` | **Checklist:** Style, security, performance reviewed; traceability IDs preserved; no dead code
**Approval Gate:** ⏸ Code review approval before PR creation.

### Phase 7: PR Generation
**Deliverable:** `PR.md` | **Checklist:** Title, summary, traceability, test evidence, breaking changes listed; links to all prior phases
**Done:** PR sections complete; all requirement IDs referenced

### Phase 8: Merge & Release
**Deliverable:** Merged branch + release notes | **Checklist:** CI passes; all approvals collected; tags created
**Approval Gate:** ⏸ Final sign-off before merge. Post-merge, all prior artifacts read-only.

## Critical Gotchas
- **No phase skipping.** Every phase must complete and pass its checklist before advancing.
- **Locked files.** Once approved (phases 3, 6, 8), do NOT modify requirements/architecture/design-review without re-opening the phase.
- **Edge case testing.** Phase 5 must verify both happy path (nominal flow) and edge cases (missing fields, invalid input, boundary conditions).
- **Traceability preservation.** Every artifact must reference requirement IDs and link back to the story.
- **Human gates.** Phases 3, 6, 8 are human approval points; Claude cannot auto-advance.

## Quick Commands
```bash
docsync samples/jira_story.json --phased                # Interactive 8-phase flow
docsync samples/jira_story.json --phased --non-interactive  # Auto-approve (CI use)
pytest -v --cov=src/documentation_sync tests/            # Verify test coverage
```

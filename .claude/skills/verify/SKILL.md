---
name: verify
description: Execute full test suite and artifact quality checks. Invokes qa-verifier agent, then pauses for human Gate 2 approval.
---

# Verification Skill (Gate 2)

1. Run locally: `pytest tests/ -v --cov=src/documentation_sync --cov-report=term-missing`
2. Run: `docsync-verify . --story user-story.md`
3. Dispatch `Agent(subagent_type="qa-verifier", prompt="Verify tests pass, coverage >=80%, all artifacts complete. Write claude-verification-report.md")`.
4. Present Outcome section from `claude-verification-report.md`.
5. **GATE 2 — BLOCKING:** Ask: *"Verification complete. All checks passed. Approve to proceed to PR? (yes / fix-and-retry)"*
   - `yes` → record Gate 2 approval in `.claude/pipeline-state.json`.
   - `fix-and-retry` → dispatch `code-developer` with failing test diagnostics; re-run from step 1.

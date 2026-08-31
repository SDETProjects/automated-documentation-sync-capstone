---
name: pr
description: Generate PR description and CHANGELOG. Invokes release-engineer agent to write claude-pr-description.md and update CHANGELOG.md. Requires Gate 2 approval.
---

# PR Generation Skill (Gate 3)

1. Verify Gate 2 is recorded as approved in `.claude/pipeline-state.json`; abort if not.
2. Dispatch `Agent(subagent_type="release-engineer", prompt="Summarize all pipeline outputs and write claude-pr-description.md and CHANGELOG.md")`.
3. Confirm outputs:
   - `claude-pr-description.md` — title ≤60 chars, summary, traceability matrix, test evidence, breaking changes.
   - `CHANGELOG.md` — user-facing entry, dated, linked to requirement IDs.
4. **GATE 3 — CI:** Remind user to open the PR; CI must be green before merge.

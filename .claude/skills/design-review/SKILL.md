---
name: design-review
description: Risk and gap analysis of requirements and architecture. Invokes design-reviewer agent, then pauses for human Gate 1 approval before allowing pipeline to continue.
---

# Design Review Skill (Gate 1)

1. Verify both `claude-requirements.md` and `claude-architecture.md` exist.
2. Dispatch `Agent(subagent_type="design-reviewer", prompt="Review requirements and architecture, write claude-design-review.md")`.
3. Present the Outcome section from `claude-design-review.md` to the user.
4. **GATE 1 — BLOCKING:** Ask: *"Design review complete. Do you approve? (yes / revise / reject)"*
   - `yes` → record approval in `.claude/pipeline-state.json` and continue.
   - `revise` → dispatch `software-architect` with reviewer feedback; repeat from step 2.
   - `reject` → halt pipeline; record rejection in pipeline-state.json.

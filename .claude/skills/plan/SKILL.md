---
name: plan
description: Break the approved architecture into a dependency-ordered implementation task list. Invokes implementation-planner agent to write claude-impl-plan.md.
---

# Implementation Plan Skill

1. Verify Gate 1 is recorded as approved in `.claude/pipeline-state.json`; abort if not.
2. Dispatch `Agent(subagent_type="implementation-planner", prompt="Decompose claude-architecture.md into tasks and write claude-impl-plan.md")`.
3. Confirm `claude-impl-plan.md` contains: ordered tasks, effort estimates (S/M/L), explicit dependencies, definition of done per task.
4. Identify the critical path and surface it to the user before proceeding to `/implement`.

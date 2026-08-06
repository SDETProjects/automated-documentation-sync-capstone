---
mode: agent
description: Break architecture into prioritized, dependency-ordered implementation tasks
tools: ["editFiles", "runCommands"]
---

# Prompt: Generate impl-plan.md

Using the approved requirements.md and architecture.md, produce impl-plan.md with:

1. An ordered task list to implement the requirements, each task tagged with the FR/NFR ID(s) it addresses.
2. Estimated relative effort (S/M/L) per task.
3. Dependencies between tasks, if any.
4. A definition of done referencing test coverage and documentation updates.

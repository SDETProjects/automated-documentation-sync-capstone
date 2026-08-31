---
name: pipeline
description: Run the full 8-step Agentic SDLC pipeline with state persistence and human approval gates. Orchestrates requirements → architecture → design-review → plan → implement → code-review → verify → pr in sequence.
---

# SDLC Pipeline Skill

1. Read `.claude/pipeline-state.json`; resume from the last incomplete step if a prior run exists.
2. Dispatch `Agent(subagent_type="orchestrator", prompt="Run 8-step pipeline for current story")`.
3. The orchestrator executes skills in order: `/requirements` → `/architecture` → `/design-review` → `/plan` → `/implement` → `/code-review` → `/verify` → `/pr`.
4. **Gate 1** (after `/design-review`): human must approve before `/plan` runs.
5. **Gate 2** (after `/verify`): human must approve before `/pr` runs.
6. **Gate 3** (after `/pr`): CI must pass before merge.
7. On any step failure: record failed step + error in `.claude/pipeline-state.json`, surface to user, allow retry or skip with justification.

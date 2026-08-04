---
mode: agent
description: Orchestrate the full 8-step SDLC pipeline from a Jira story ID
tools: ["codebase", "editFiles", "runCommands"]
---

# SDLC Pipeline Orchestrator

## Input

User provides a **Jira story ID** (e.g., `EPMCDMETST-57618`).

## Execution

Run the full 8-step agentic SDLC pipeline. For each step:

1. **Load the step prompt** from `.github/prompts/step-N-*.prompt.md`
2. **Execute the step** using the instructions in that prompt
3. **Commit the artifact** (when complete)
4. **Gate pause** (after steps 3, 6, 8) — ask the user for approval before proceeding
5. **Verification** — between steps, run `docsync-verify . --story user-story.md` to ensure document quality

## Steps

| Step | Artifact | Gate After? |
|---|---|---|
| 1 | requirements.md | No |
| 2 | architecture.md | No |
| 3 | design-review.md | **YES** |
| 4 | impl-plan.md | No |
| 5 | code-review.md | No |
| 6 | verification-report.md | **YES** |
| 7 | code & tests | No |
| 8 | CHANGELOG.md, PR description | **YES** |

## Key Rules

- Follow the order. Do not skip steps.
- Answer clarifying questions before writing any artifacts.
- Requirement IDs (US-n, FR-n, NFR-n) are immutable; derived from the story.
- Prose may be refined and extended; IDs may not drift.
- At each gate, wait for explicit user approval before advancing.
- All CI gates (tests, coverage, document quality, verification) must pass before final merge.

## Example invocation

```
/run-pipeline EPMCDMETST-57618
```

The orchestrator will fetch the story, initialize phase 1, and guide you through all 8 steps.

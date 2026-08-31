---
name: pipeline
description: Run the full 8-step SDLC pipeline via the sdlc-orchestrator agent
agent: sdlc-orchestrator
model: claude-haiku-4-5
argument-hint: "Jira story key or URL (e.g. EPMCDMETST-55568)"
---

Run the full 8-step SDLC pipeline for the story provided as an argument.

Resolve the story source in this order:
1. Use the Jira key/URL argument if provided
2. Fall back to `user-story.md` at repo root
3. If neither exists, ask the user to paste the story text

Then execute all pipeline steps in order, pausing for human approval at Gates 1, 2, and 3.

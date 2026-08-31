---
name: requirements
description: Elicit functional and non-functional requirements from a user story. Invokes requirements-analyst agent to parse US/FR/NFR IDs and write claude-requirements.md.
---

# Requirements Elicitation Skill

1. Locate story source: check `user-story.md` → if absent, prompt user to paste story text.
2. Dispatch `Agent(subagent_type="requirements-analyst", prompt="Parse story and write claude-requirements.md")`.
3. Confirm `claude-requirements.md` exists with immutable IDs: `US-1`, `FR-1..n`, `NFR-1..n`.
4. List any clarifying questions the agent recorded; ask the user to resolve them before proceeding to `/architecture`.

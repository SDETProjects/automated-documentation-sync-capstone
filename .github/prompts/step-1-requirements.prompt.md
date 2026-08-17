---
mode: agent
description: Elicit and document requirements from a user story with traceability IDs
tools: ["editFiles", "runCommands"]
---

# Prompt: Generate requirements.md

**Story Source (resolved by orchestrator before this step):**
1. **Auto-fetch from Jira** — If `JIRA_API_TOKEN` + `JIRA_BASE_URL` configured, runs `docsync` to fetch live story → `user-story.md`
2. **Local file** — Falls back to existing `user-story.md` at repo root
3. **User paste** — If neither above, orchestrator prompts user to paste story in chat

**This step receives:** Story text (from `user-story.md` or chat paste)

Given a Jira-style story (samples/jira_story.json or Markdown), produce requirements.md with:

1. Story summary and a link back to the Jira key.
2. US-1 user story statement.
3. Numbered functional requirements FR-1..FR-n derived from acceptance criteria, in the order the criteria appear.
4. Non-functional requirements NFR-1..NFR-n (performance, security, usability) inferred from story labels/description if present.
5. An Open Questions section listing any ambiguous or missing fields that required a clarifying assumption.

If required fields (title, description, acceptance criteria) are missing, raise a validation error instead of guessing content.

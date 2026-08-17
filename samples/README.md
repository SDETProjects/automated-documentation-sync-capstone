# Samples

Example input files for the `docsync` CLI and Copilot pipeline.

## Files

| File | Format | Description |
|------|--------|-------------|
| `jira_story.json` | JSON | Canonical sample story used by tests and demos |

## `jira_story.json` Structure

```json
{
  "key": "EPMCDMETST-55568",
  "summary": "Enable automated documentation sync for user stories",
  "description": "As a QA engineer, I want user stories to be automatically converted into structured requirements and SDLC documentation artifacts...",
  "acceptance_criteria": [
    "Given a Jira-style story file, the system parses title, description, and acceptance criteria into a structured model",
    "Given a parsed story, the system generates requirements.md with unique traceability IDs (US, FR, NFR)",
    "Given approved requirements, the system generates architecture.md, design-review.md, impl-plan.md, and PR.md",
    "Given an invalid or incomplete story, the system reports clear validation errors instead of generating partial docs"
  ],
  "labels": ["documentation", "automation", "sdlc"],
  "priority": "High",
  "story_points": 5,
  "reporter": "jane.doe@example.com",
  "assignee": "john.smith@example.com"
}
```

## Usage

```bash
# Generate artifacts from sample
docsync samples/jira_story.json -o out

# Verify with sample as source of truth
docsync-verify out --story samples/jira_story.json
```

## Creating Your Own

1. Copy `jira_story.json` to a new file
2. Update `key`, `summary`, `description`, `acceptance_criteria`
3. Optional: add `labels`, `priority`, `story_points`, `reporter`, `assignee`
4. Run `docsync your-story.json -o out`

## Supported Input Formats

The CLI accepts:
- **JSON** (above) — full fidelity, all metadata preserved
- **Markdown** — `user-story.md` format (see `generate_user_story_md` in `generator.py`)
- **Jira URL** — `https://jira.company.com/browse/PROJ-123`
- **Bare issue key** — `PROJ-123` (requires `JIRA_BASE_URL`)
- **Pasted text** — interactive fallback when Jira integration unavailable
# Copilot Instructions: Automated Documentation Sync

This repository automates SDLC documentation generation from a Jira-style user story. When assisting in this repo:

- Preserve traceability IDs (`US-1`, `FR-n`, `NFR-n`) across every generated artifact.
- Keep the pipeline file-based and simple: parse -> validate -> generate. Do not introduce network calls or databases.
- Source of truth is the story (`samples/jira_story.json` or Markdown equivalent); never hand-edit generated artifacts without updating the story first.
- Reuse the exception types in `src/documentation_sync/validator.py` and `parser.py` (`StoryNotFoundError`, `StoryParseError`, `ValidationError`) for consistent CLI exit codes.
- Add or update tests in `tests/` for any change to parser, validator, generator, or CLI behavior.
- Follow prompts in `.github/prompts/` for the documentation-generation workflow order (requirements -> architecture -> design-review -> impl-plan -> code-review -> PR).

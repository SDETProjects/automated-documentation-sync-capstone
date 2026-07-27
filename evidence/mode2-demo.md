# Mode 2 Demo Transcript — URL Input with Graceful Fallback

**Command:**

```
docsync "https://jiraeu.epam.com/browse/EPMCDMETST-55568" -o demo_output_2
```

**Terminal output:**

```
$ docsync "https://jiraeu.epam.com/browse/EPMCDMETST-55568" -o demo_output_2

WARNING: Jira integration unavailable: no authentication token provided
and the URL could not be fetched anonymously.
Jira/Confluence integration is not available. Please paste the full story
text below, then press Enter on an empty line to finish:
> {
>   "key": "EPMCDMETST-55568",
>   "summary": "Enable automated documentation sync for user stories",
>   "description": "As a QA engineer, I want user stories to be automatically
>     converted into structured requirements and SDLC documentation artifacts,
>     so that documentation stays in sync with delivered features and reviewers
>     have consistent, traceable evidence.",
>   "acceptance_criteria": [
>     "Given a Jira-style story file, the system parses title, description,
>      and acceptance criteria into a structured model",
>     "Given a parsed story, the system generates requirements.md with unique
>      traceability IDs (US, FR, NFR)",
>     "Given approved requirements, the system generates architecture.md,
>      design-review.md, impl-plan.md, and PR.md",
>     "Given an invalid or incomplete story, the system reports clear
>      validation errors instead of generating partial docs"
>   ],
>   "labels": ["documentation", "automation", "sdlc"],
>   "priority": "High"
> }
>
Generated 5 artifact(s) in C:\...\demo_output_2:
  - requirements.md
  - architecture.md
  - design-review.md
  - impl-plan.md
  - PR.md
```

**What this shows:**

- URL ingestion attempted; auth failure detected and reported clearly.
- System does NOT crash — gracefully prompts for manual story paste.
- After paste, proceeds identically to Mode 1.
- Exit code: 0

**Key design decisions visible here:**

- `IntegrationUnavailableError` surfaces a human-readable message, not a raw stack trace.
- The fallback prompt is on `stderr`; artifact generation output is on `stdout`.
- The pasted text goes through the same `load_story_from_any_source` → `ensure_valid_story` pipeline as a file input, so validation is identical.

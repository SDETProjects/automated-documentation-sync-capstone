# Python Instructions

Applies to: src/documentation_sync/**, tests/**

- Target Python 3.10+, use type hints and dataclasses (see models.py) for story/requirement structures.
- Keep modules single-purpose: parser.py (read/parse input), validator.py (business rules), generator.py (render Markdown artifacts), cli.py (orchestration and exit codes).
- Raise specific exceptions (StoryNotFoundError, StoryParseError, ValidationError) instead of generic Exception; map them to CLI exit codes 2, 1, 1 respectively.
- Every public function needs a docstring and at least one pytest covering happy path plus one covering an error path.
- No external services or network calls; all I/O is local file reads/writes under the project directory.

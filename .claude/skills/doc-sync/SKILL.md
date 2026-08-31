---
name: doc-sync
description: Scan the repository for all SDLC artifacts and generate a synced documentation manifest. Use after any src/ change to keep docs current.
---

# Documentation Sync Skill

1. Scan for all claude-*.md and pipeline artifacts at repo root.
2. For each artifact, record: path, last-modified, status (complete / in-progress / missing).
3. Write manifest to `docs/claude-synced-output.md`.
4. Run `docsync-verify . --story user-story.md` to validate traceability IDs are consistent.
5. Create marker: `.claude/.docsync-ran` with timestamp.
6. Report any missing or stale artifacts to the user.

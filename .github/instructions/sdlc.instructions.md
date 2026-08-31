---
name: SDLC Pipeline
description: Guidelines for SDLC artifacts — traceability IDs, heading structure, section requirements
applyTo: "requirements.md,architecture.md,design-review.md,impl-plan.md,code-review.md,PR.md,CHANGELOG.md,verification-report.md,claude-requirements.md,claude-architecture.md,claude-design-review.md,claude-impl-plan.md,claude-code-review.md,claude-pr-description.md,claude-verification-report.md"
---

# SDLC Pipeline Instructions

When editing or creating SDLC artifacts:

1. **Preserve traceability IDs** — `US-1`, `FR-n`, `NFR-n` must not be renumbered or removed once set
2. **Use correct heading structure** — Single `#` for title, `##` for sections, `###` for sub-sections
3. **Link to requirements** — Each component or section must reference the FR/NFR IDs it addresses
4. **Never remove `## Outcome`** — The Outcome section is required for review sign-off in design-review.md and code-review.md
5. **Regenerate on change** — When `requirements.md` changes, regenerate all downstream artifacts that reference changed IDs

## Agent Artifact Naming

| Agent | GitHub Copilot artifact | Claude Code artifact |
|---|---|---|
| `requirements-analyst` | `requirements.md` | `claude-requirements.md` |
| `software-architect` | `architecture.md` | `claude-architecture.md` |
| `design-reviewer` | `design-review.md` | `claude-design-review.md` |
| `implementation-planner` | `impl-plan.md` | `claude-impl-plan.md` |
| `code-reviewer` | `code-review.md` | `claude-code-review.md` |
| `qa-verifier` | `verification-report.md` | `claude-verification-report.md` |
| `release-engineer` | `PR.md`, `CHANGELOG.md` | `claude-pr-description.md`, `CHANGELOG.md` |

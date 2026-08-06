# SKILL: PR Generator

**Reusable workflow for generating PR description and changelog.**

## Use Cases

- Step 8: Generate PR description and changelog
- Any point: Create a PR summary for code changes

## Workflow

1. **Summarize code changes**
   - List new files added
   - List modified files (with line counts)
   - List files deleted (if any)

2. **Map requirements to code**
   - Build traceability matrix: Requirement → File → Test
   - Show that all FRs and NFRs are addressed in code

3. **Include test evidence**
   - Test count
   - Coverage percentage
   - All tests passing status

4. **Generate PR description**
   - Title (≤60 chars)
   - Summary (2-3 sentences)
   - Changes section (new/modified/deleted)
   - Traceability matrix
   - Test evidence
   - Breaking changes (if any)
   - Deployment notes (if any)

5. **Update CHANGELOG.md**
   - Added: New features
   - Changed: Enhancements
   - Fixed: Bug fixes
   - Deprecated: Deprecated features
   - Removed: Removed features
   - Security: Security fixes

## Inputs

- All prior artifacts (requirements through verification report)
- Code diff (changes in `src/`)
- Test results

## Outputs

- `claude-pr-description.md` (ready to copy-paste to GitHub)
- `CHANGELOG.md` updated with new entry

## Key Rules

- PR title ≤60 chars
- Description must include traceability
- Test evidence required
- Changelog entry must be user-facing
- No breaking changes (or list them explicitly)

---

## Implementation

Invoked by `/step-8-create-pr` command and `step-8-pr-agent`.

Use this skill's workflow when generating PR descriptions for other features.

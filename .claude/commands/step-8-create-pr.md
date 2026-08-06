# /step-8-create-pr

**Generate PR description and changelog, ready for merge.**

## Role

PR specialist that packages the implementation into a merge-ready pull request.

## Task

Generate:
- **`claude-pr-description.md`:** PR body with title, summary, traceability, test evidence
- **`CHANGELOG.md` update:** User-facing changelog entry
- Both files ready for GitHub PR creation

## Context

- **Input:** All prior approvals, code from Steps 4–7
- **Output:** `claude-pr-description.md` + `CHANGELOG.md` update
- **Gate:** No blocking gate; CI must pass after PR creation
- **Audience:** GitHub reviewers, users reading release notes

## Constraints

- PR title must be ≤60 characters
- Description must include traceability (requirements → code)
- Changelog must be user-facing (no technical jargon)
- Follow repo conventions for PR format

## Inputs

1. All prior artifacts (requirements through verification report)
2. Code diff (changes in `src/`)
3. Test results from Step 7

## Outputs / Output format

### `claude-pr-description.md`

```markdown
# PR Title: [≤60 chars summary]

## Summary

[2-3 sentence overview of what this PR does and why]

Example:
"This PR implements the Jira sync feature requested in EPMCDMETST-55568. It adds:
- Jira issue fetcher that polls for new stories
- Requirement generator that extracts FRs and NFRs
- CI/CD integration for automated artifact generation

All changes are covered by tests with 92% coverage."

## Changes

### New Files
- `src/jira_fetcher.py` — Polls Jira for new issues
- `src/requirement_extractor.py` — Extracts requirements from stories
- `tests/test_jira_fetcher.py` — Tests for fetcher

### Modified Files
- `src/pipeline.py` — Added Jira integration hook (+12 lines)

## Traceability

| Requirement | File | Tests |
|---|---|---|
| US-1 | `jira_fetcher.py` | `test_jira_fetcher.py` |
| FR-1 | `requirement_extractor.py` | `test_requirement_extractor.py` |
| FR-2 | `requirement_extractor.py` | `test_requirement_extractor.py` |
| NFR-1 | `jira_fetcher.py` | `test_jira_fetcher.py` |

## Test Evidence

```
test_jira_fetcher.py PASSED
test_requirement_extractor.py PASSED
========== 28 passed in 1.23s ==========

Coverage: 92% (target: ≥80%) ✓
```

## Breaking Changes

None.

## Deployment Notes

- No database migrations required
- No configuration changes required
- No API changes (backward compatible)

## Related Issues

Closes #EPMCDMETST-55568

## Reviewer Checklist

- [ ] Code follows repo conventions
- [ ] Tests pass locally
- [ ] No breaking changes
- [ ] Traceability clear
- [ ] Coverage ≥80%
```

### `CHANGELOG.md` entry

```markdown
## [Unreleased]

### Added
- Jira integration for automated story → requirements transformation
- Requirement extractor that generates FR/NFR/AC from stories
- CI/CD hook for automatic artifact generation

### Changed
- Pipeline now supports Jira story input (was file-only)

### Fixed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Security
- N/A
```

## Completion criteria

- [ ] `claude-pr-description.md` exists with title, summary, changes
- [ ] Traceability matrix included
- [ ] Test evidence attached
- [ ] No breaking changes listed
- [ ] `CHANGELOG.md` updated with user-facing summary
- [ ] PR ready for GitHub creation

---

## Gate

**No blocking gate.** PR is created and CI checks run. After CI passes:

1. Review `claude-pr-description.md`
2. Create PR on GitHub with that content
3. Wait for CI to pass
4. Merge PR

---

## See Also

- `/step-7-verify` — Prior step (approval required)
- `.claude/agents/step-8-pr-agent.md` — Implementation
- `.claude/skills/pr-generator/SKILL.md` — Reusable PR generation workflow

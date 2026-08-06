# /step-6-code-review

**Review implemented code for quality, security, and correctness.**

## Role

Code reviewer that assesses code quality, test coverage, and architecture alignment.

## Task

Review the code generated in Step 5 and generate `claude-code-review.md` with:
- **Quality assessment:** Correctness, readability, performance
- **Security review:** Vulnerabilities, unsafe patterns, data handling
- **Test coverage:** Are tests adequate? Coverage ≥80%?
- **Architecture alignment:** Does code match the approved design?
- **Suggestions:** Non-blocking improvements
- **Approval:** Code is ready for verification

## Context

- **Input:** Code in `src/`, tests in `tests/` (Step 5 output)
- **Output:** `claude-code-review.md`
- **Audience:** Implementation team, maintainers
- **No blocking gate.** Review is informational; Step 7 proceeds regardless.

## Constraints

- Focus on high-impact issues (security, correctness, maintainability)
- Don't nitpick style (that's linting's job)
- Praise good patterns when found
- Suggest improvements, not demands

## Inputs

1. Code in `src/`
2. Tests in `tests/`
3. Approved `claude-architecture.md` (design to verify against)

## Outputs / Output format

```markdown
# Code Review — [Story ID]

## Overview
[1-2 sentences on code quality assessment]

## Findings

### Security Issues

**Finding:** [Title]
- **Severity:** Critical | High | Medium | Low
- **Location:** `src/module.py:line_number`
- **Description:** [What's wrong]
- **Recommendation:** [How to fix]

### Correctness Issues

**Finding:** [Title]
...

### Performance Issues

**Finding:** [Title]
...

## Test Coverage

| File | Coverage | Status |
|---|---|---|
| `src/module_1.py` | 95% | ✓ Pass |
| `src/module_2.py` | 82% | ✓ Pass |
| **TOTAL** | **92%** | ✓ Pass |

Target met: ≥80% ✓

## Architecture Alignment

- [Component] matches design: ✓ Yes | ✗ No
- [Component] matches design: ✓ Yes | ✗ No
...

## Suggestions (Non-Blocking)

- Consider using [pattern] for [reason]
- [Suggestion]: [Why this improves the code]

## Approval

Code is **ready for verification** (Step 7).

## Traceability

| Requirement | Implementation | Test | Review |
|---|---|---|---|
| FR-1 | `module_1.py` | `test_module_1.py` | ✓ Verified |
| FR-2 | `module_2.py` | `test_module_2.py` | ✓ Verified |
...
```

## Completion criteria

- [ ] `claude-code-review.md` exists
- [ ] Security issues identified and recommendations given
- [ ] Test coverage ≥80% confirmed
- [ ] Architecture alignment verified
- [ ] Code quality assessment complete
- [ ] Approval status clear

---

## See Also

- `/step-5-implement` — Prior step (code reviewed here)
- `/step-7-verify` — Next step (runs tests and confirms coverage)
- `.claude/agents/step-6-code-review-agent.md` — Implementation

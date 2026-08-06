# /step-7-verify

**Verify that all tests pass, coverage meets threshold, and artifacts are complete.**

## Role

Verification specialist that confirms implementation is ready for merging.

## Task

Verify:
1. **All tests pass:** `pytest tests/ -v` exits with 0
2. **Coverage ≥80%:** `pytest --cov=src` shows ≥80% overall coverage
3. **Artifact completeness:** All 7 steps have artifacts present
4. **Traceability:** Requirements are addressable in code + tests
5. Generate `claude-verification-report.md` with summary

## Context

- **Input:** Code from Step 5, coverage report, all prior artifacts
- **Output:** `claude-verification-report.md`
- **Gate:** ✋ Tests must pass, coverage ≥80%. User approval required.
- **Pre-step:** User runs locally first:
  ```bash
  docsync-verify . --story user-story.md
  ```

## Constraints

- Tests must pass (exit code 0)
- Coverage must be ≥80% (line coverage, not branch coverage)
- All 7 prior artifacts must exist
- No artifact may be empty or malformed

## Inputs

1. **Test results** from Step 5 (from local run):
   ```bash
   pytest tests/ -v
   pytest --cov=src --cov-report=term-missing
   ```

2. **All prior artifacts:**
   - `claude-requirements.md`
   - `claude-architecture.md`
   - `claude-design-review.md`
   - `claude-impl-plan.md`
   - `src/` + `tests/`
   - `claude-code-review.md`

## Outputs / Output format

```markdown
# Verification Report — [Story ID]

## Test Results

```
test_module_1.py PASSED
test_module_2.py PASSED
test_integration.py PASSED
test_e2e.py PASSED

========== 42 passed in 3.52s ==========
```

Status: ✓ ALL PASS

## Coverage Report

```
Name                 Stmts   Miss  Cover
───────────────────────────────────────
src/module_1.py        42     2    95%
src/module_2.py        58     8    86%
src/service_1.py       35     1    97%
───────────────────────────────────────
TOTAL               135     11    92%
```

Status: ✓ 92% ≥ 80% threshold

## Artifact Completeness

| Step | Artifact | Status |
|---|---|---|
| 1 | `claude-requirements.md` | ✓ Present |
| 2 | `claude-architecture.md` | ✓ Present |
| 3 | `claude-design-review.md` | ✓ Present |
| 4 | `claude-impl-plan.md` | ✓ Present |
| 5 | `src/`, `tests/` | ✓ Present |
| 6 | `claude-code-review.md` | ✓ Present |
| 7 | This report | ✓ Present |

## Traceability Verification

| Requirement | Implementation | Tests | Coverage |
|---|---|---|---|
| US-1 | ✓ in `src/` | ✓ in `tests/` | ✓ Covered |
| FR-1 | ✓ in `src/` | ✓ in `tests/` | ✓ Covered |
| FR-2 | ✓ in `src/` | ✓ in `tests/` | ✓ Covered |
...

## Overall Status

- ✓ All tests pass
- ✓ Coverage ≥80%
- ✓ All artifacts present
- ✓ Traceability verified

**READY FOR STEP 8: PR & Changelog**

## Next Steps

1. Confirm approval in chat
2. Proceed to Step 8: Create PR
3. Review `claude-pr-description.md` and `CHANGELOG.md`
4. Merge PR after CI checks pass
```

## Completion criteria

- [ ] All tests pass (exit 0)
- [ ] Coverage ≥80% (term-missing output shows no uncovered lines in new code)
- [ ] All 7 prior artifacts exist and are valid
- [ ] `claude-verification-report.md` generated
- [ ] **Human approval gate:** User confirms "Tests passing. Proceed to PR." or similar

---

## Gate

**At this step, you must verify and approve:**

```
> Tests passing, coverage 92%. Proceed to Step 8.
```

or reject:

```
> Tests failing. Fix [issue] and re-run /step-7-verify.
```

---

## Pre-Step: Local Verification

Before invoking `/step-7-verify`, run locally:

```bash
# Verify tests pass
pytest tests/ -v

# Verify coverage
pytest --cov=src --cov-report=term-missing

# Optional: Verify artifact structure
docsync-verify . --story user-story.md
```

---

## See Also

- `/step-6-code-review` — Prior step (review precedes verification)
- `/step-8-create-pr` — Next step (locked until approval)
- `.claude/agents/step-7-verification-agent.md` — Implementation

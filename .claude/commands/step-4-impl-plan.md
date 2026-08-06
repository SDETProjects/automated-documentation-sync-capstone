# /step-4-impl-plan

**Break the design into implementable tasks with order and dependencies.**

## Role

Implementation planner that translates architecture into a task-by-task roadmap.

## Task

Read `claude-requirements.md` and `claude-architecture.md` (approved design) and generate `claude-impl-plan.md` with:
- **Task breakdown:** 1–5 day tasks, one task per file or module
- **Task order:** Dependencies and critical path
- **Acceptance criteria:** Per-task testability
- **Testing strategy:** Unit, integration, end-to-end
- **Traceability:** Each task addresses one or more requirements

## Context

- **Input:** Approved `claude-requirements.md`, `claude-architecture.md` (Steps 1–3 outputs)
- **Output:** `claude-impl-plan.md`
- **Audience:** Developers implementing Step 5
- **Assumption:** Design is locked; no architecture changes in Step 5

## Constraints

- Each task must be completable in 1–5 days
- List task dependencies (Task 3 depends on Task 1)
- Prioritize critical path (what must be done first)
- Include testing for each task

## Inputs

1. Approved `claude-requirements.md`
2. Approved `claude-architecture.md`

## Outputs / Output format

```markdown
# Implementation Plan — [Story ID]

## Overview
[1-2 sentences on approach and effort estimate]

## Task Breakdown

### Task 1: [Title]
- **Component:** [Which component]
- **Scope:** [What code/tests to write]
- **Estimate:** [1–5 days]
- **Dependencies:** None
- **Requirements:** FR-1, NFR-2
- **Acceptance Criteria:**
  - [ ] Code written for [module]
  - [ ] Unit tests pass with ≥80% coverage
  - [ ] [Component] API contract satisfied
- **Testing:** Unit tests + [integration | contract]

### Task 2: [Title]
- **Component:** [Which component]
- **Scope:** [What code/tests to write]
- **Estimate:** [1–5 days]
- **Dependencies:** Task 1
- **Requirements:** FR-2, FR-3
- **Acceptance Criteria:**
  - [ ] [Testable outcome]
  - [ ] [Testable outcome]
- **Testing:** [Test types]

### Task 3: [Title]
...

## Critical Path

```
Task 1 (2 days)
    ↓
Task 2 (1 day) ─┐
Task 3 (1 day) ─┤
               ↓
Task 4 (3 days)
    ↓
Task 5: Integration tests (2 days)

Total: ~9 days (critical path 2→1→3→2 = 6 days)
```

## Testing Strategy

| Task | Unit | Integration | E2E | Coverage |
|---|---|---|---|---|
| Task 1 | Yes | — | — | ≥80% |
| Task 2 | Yes | Yes | — | ≥80% |
| Task 3 | Yes | — | — | ≥80% |
| Task 4 | Yes | Yes | Yes | ≥80% |
| Task 5 | — | — | Yes | ≥80% |

## Effort Estimate

- **Total effort:** [X days]
- **Critical path:** [Y days]
- **Parallelizable tasks:** [1, 2, 3] (can run in parallel)

## Traceability

| Task | FR | NFR | Verification |
|---|---|---|---|
| Task 1 | FR-1 | NFR-1 | Unit test + contract test |
| Task 2 | FR-2, FR-3 | NFR-2 | Integration test |
...

## Next Steps

1. Review plan with team
2. Proceed to Step 5: Implementation
3. Execute tasks in order (or parallelized where safe)
```

## Completion criteria

- [ ] `claude-impl-plan.md` exists
- [ ] All tasks from architecture mapped to tasks
- [ ] Each task has estimate (1–5 days)
- [ ] Task dependencies clearly stated
- [ ] Critical path identified
- [ ] Testing strategy for each task specified
- [ ] Implementation team understands the roadmap

---

## See Also

- `/step-3-design-review` — Prior step (approval required)
- `/step-5-implement` — Next step (executes these tasks)
- `.claude/agents/step-4-impl-plan-agent.md` — Implementation

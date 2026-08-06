# /run-pipeline

**Orchestrate the full 8-step SDLC pipeline.**

## Role

Pipeline coordinator that walks through Steps 1–8 sequentially, waiting for human approval at gates (Steps 3, 6, 7).

## Task

Run the complete Automated Documentation Sync SDLC pipeline:
1. Requirements Elicitation
2. Architecture Design
3. Design Review + **human approval gate**
4. Implementation Plan
5. Implementation (code + tests)
6. Code Review
7. Verification + **human approval gate**
8. PR & Changelog generation

## Context

- **Story input:** `user-story.md` (user provides path or text)
- **Artifact prefix:** `claude-` (to avoid conflicts with Copilot Chat)
- **Gates:** Steps 3, 6, 7 require explicit human approval in chat
- **MCP:** Uses `docsync-jira` for JIRA integration, `filesystem` for file I/O
- **Memory:** Stores decisions and blockers in `.claude/projects/*/memory/`

## Constraints

- **No phase skipping.** Steps execute 1→8 in order.
- **Requirement IDs are immutable.** `US-1`, `FR-1`, …, `NFR-1` match the source story.
- **Each step consumes the prior artifact.** E.g., Step 2 reads `claude-requirements.md`.
- **Traceability required.** Every artifact must link back to requirements.
- **Coverage target ≥80%.** Step 7 gate blocks until tests pass with ≥80% coverage.

## Inputs

1. **Story source** (one of):
   - Path to `user-story.md`: `/run-pipeline`
   - JIRA story ID: `/run-pipeline EPMCDMETST-55568`
   - Text pasted into chat (prompted if not provided)

2. **Approvals at gates:**
   - Step 3: "Approved. Proceed." or similar
   - Step 7: "Tests passing. Proceed to PR." or similar

## Outputs / Output format

### Artifacts
- `claude-requirements.md` — Step 1 output
- `claude-architecture.md` — Step 2 output
- `claude-design-review.md` — Step 3 output
- `claude-impl-plan.md` — Step 4 output
- `src/` + `tests/` — Step 5 output
- `claude-code-review.md` — Step 6 output
- `claude-verification-report.md` — Step 7 output
- `claude-pr-description.md` + `CHANGELOG.md` — Step 8 output

### Progress
- Display: `[1/8] Requirements` → `[8/8] PR & Changelog`
- Each step shows: input, processing, output location
- Gates show: approval request, context for decision

## Completion criteria

- [ ] Step 1: `claude-requirements.md` exists with US-1, FR-1..n, NFR-1
- [ ] Step 2: `claude-architecture.md` exists with component design
- [ ] Step 3: Design review complete; human approval recorded
- [ ] Step 4: `claude-impl-plan.md` exists with task breakdown
- [ ] Step 5: Code in `src/`, tests in `tests/`, coverage ≥80%
- [ ] Step 6: `claude-code-review.md` exists with findings
- [ ] Step 7: All tests passing; human approval recorded
- [ ] Step 8: `claude-pr-description.md` and `CHANGELOG.md` ready for merge

---

## Implementation

This command invokes the `pipeline-orchestrator` agent with `run_mode=full_pipeline`.

### Pseudocode

```
1. Prompt user for story source (file, JIRA ID, or text)
2. Invoke /step-1-requirements
   → Wait for Step 1 output
3. Invoke /step-2-architecture
   → Wait for Step 2 output
4. Invoke /step-3-design-review
   → Display: "Review complete. Do you approve? Reply 'Approved' or describe revisions."
   → **GATE: Wait for human approval**
5. Invoke /step-4-impl-plan
   → Wait for Step 4 output
6. Invoke /step-5-implement
   → Wait for Step 5 output (code + tests)
7. Invoke /step-6-code-review
   → Wait for Step 6 output
8. Display: "Tests required. Run: docsync-verify . --story user-story.md"
   → Invoke /step-7-verify
   → **GATE: Wait for human verification approval**
9. Invoke /step-8-create-pr
   → Display: "Pipeline complete! PR artifacts ready. Review claude-pr-description.md and CHANGELOG.md"
10. Record completion in memory

Done.
```

---

## See Also

- `.claude/agents/pipeline-orchestrator.md` — Implementation agent
- `.claude/CLAUDE.md` — Pipeline rules and gates
- [README-CLAUDE.md](../../README-CLAUDE.md) — Quick-start guide

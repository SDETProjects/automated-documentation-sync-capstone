# CLAUDE.md — Claude Code SDLC Pipeline

Guidance for the **Claude Code implementation** of the 8-step Agentic SDLC Pipeline for Automated Documentation Sync.

This complements the [Copilot Chat pipeline](../CLAUDE.md) documented in `.github/prompts/`. Both pipelines are independent and produce separate artifacts with the `claude-` prefix for Claude Code.

---

## Operating Model

Claude Code drives the 8-step pipeline via:

- **Commands** (`.claude/commands/`) — User entrypoints  
- **Agents** (`.claude/agents/`) — Execution workers  
- **Skills** (`.claude/skills/`) — Reusable workflows  
- **Hooks** (`.claude/settings.json` + `.claude/hooks/`) — Validation gates  
- **MCP Servers** (`.mcp.json`) — JIRA, GitHub, filesystem integration

---

## The 8 Steps

### Step 1: Requirements Elicitation

**Command:** `/step-1-requirements`  
**Agent:** `step-1-requirements-agent.md`  
**Input:** `user-story.md`  
**Output:** `claude-requirements.md` (US-1, FR-1..n, NFR-1, ACs)

Tasks:
- Parse story or elicit via clarifying questions
- Extract functional requirements (FR-1, FR-2, …)
- Extract non-functional requirements (NFR-1, NFR-2, …)
- Document acceptance criteria
- Mark traceability: `US-1 → {FR-n, NFR-n}`

**Gate after:** No

---

### Step 2: Architecture Design

**Command:** `/step-2-architecture`  
**Agent:** `step-2-architecture-agent.md`  
**Input:** `claude-requirements.md`  
**Output:** `claude-architecture.md`

Tasks:
- Design component structure
- Sketch data flow and APIs
- Identify integration points
- List deployment topology
- Map requirements to components (traceability)

**Gate after:** No

---

### Step 3: Design Review

**Command:** `/step-3-design-review`  
**Agent:** `step-3-design-review-agent.md`  
**Input:** `claude-requirements.md`, `claude-architecture.md`  
**Output:** `claude-design-review.md`

Tasks:
- Identify risks (security, performance, maintainability, scalability)
- Propose mitigations for each risk
- Suggest alternatives and trade-offs
- Rate confidence in design
- Seek human approval before proceeding

**Gate after:** ✋ **YES — You must approve in chat to unlock Step 4**

Example approval response in chat:
```
Approved. Proceed with implementation planning.
```

---

### Step 4: Implementation Plan

**Command:** `/step-4-impl-plan`  
**Agent:** `step-4-impl-plan-agent.md`  
**Input:** Approved `claude-requirements.md`, `claude-architecture.md`  
**Output:** `claude-impl-plan.md`

Tasks:
- Break architecture into implementable tasks (1–5 day estimates)
- Define task order and dependencies
- Identify testing strategy
- List acceptance criteria per task
- Map to requirements (traceability)

**Gate after:** No

---

### Step 5: Implementation

**Command:** `/step-5-implement`  
**Agent:** `step-5-implementation-agent.md`  
**Input:** `claude-impl-plan.md`  
**Output:** Code in `src/`, tests in `tests/`

Tasks:
- Generate code for each task in the plan
- Write unit tests (target ≥80% coverage)
- Follow repo coding standards
- Integrate with existing code
- Ask for clarifications if blocked

**Gate after:** No  
**Coverage target:** ≥80% (enforced at Step 7 gate)

---

### Step 6: Code Review

**Command:** `/step-6-code-review`  
**Agent:** `step-6-code-review-agent.md`  
**Input:** Implemented code + test results  
**Output:** `claude-code-review.md`

Tasks:
- Review code for correctness, security, performance
- Check test coverage and quality
- Verify architecture alignment
- Suggest improvements (not blocking)
- Sign off on code quality

**Gate after:** No (informational)

---

### Step 7: Verification

**Command:** `/step-7-verify`  
**Agent:** `step-7-verification-agent.md`  
**Input:** Test results, coverage report, artifacts  
**Output:** `claude-verification-report.md`

**Pre-step (manual):**
```bash
# You run this locally
docsync-verify . --story user-story.md
```

Tasks:
- Summarize test results (pass/fail count, execution time)
- Confirm coverage ≥80%
- Validate artifact completeness (all 8 steps present)
- Verify traceability (requirements → code → tests)
- Require human sign-off if tests fail

**Gate after:** ✋ **YES — Tests must pass, coverage ≥80%, all checks green**

Example approval:
```
All tests passing, coverage 92%. Proceed to Step 8.
```

---

### Step 8: PR & Changelog

**Command:** `/step-8-create-pr`  
**Agent:** `step-8-pr-agent.md`  
**Input:** All prior approvals  
**Output:** `claude-pr-description.md`, `CHANGELOG.md` update

Tasks:
- Draft PR title (≤60 chars)
- Generate PR description with:
  - Summary of changes
  - Traceability matrix (requirements → code)
  - Test evidence
  - Screenshots/demos (if applicable)
- Update `CHANGELOG.md` with user-facing summary
- Format for GitHub PR merge

**Gate after:** CI (GitHub Actions) — human execution

---

## Artifact Naming Convention

All Claude Code artifacts use the `claude-` prefix to avoid conflicts with Copilot Chat:

| Step | Artifact | Purpose |
|---|---|---|
| 1 | `claude-requirements.md` | Functional & non-functional requirements |
| 2 | `claude-architecture.md` | Design and component structure |
| 3 | `claude-design-review.md` | Risk analysis and approval gate |
| 4 | `claude-impl-plan.md` | Task breakdown and order |
| 5 | `src/`, `tests/` | Implementation (shared with Copilot) |
| 6 | `claude-code-review.md` | Code quality assessment |
| 7 | `claude-verification-report.md` | Test results and coverage |
| 8 | `claude-pr-description.md`, `CHANGELOG.md` | PR package (changelog shared) |

---

## Memory System

Claude Code sessions leverage persistent memory at:

```
.claude/projects/C--Users-UjjalSaha-Documents-Capstone-Projects-automated-documentation-sync-capstone/memory/
```

Memory tracks:
- Custom MCP server setup and configuration
- Known issues and workarounds
- Lessons from prior pipeline runs
- Project context (deadlines, stakeholders, constraints)

---

## MCP Servers

Configured in `.mcp.json` and `.claude/settings.json`:

| Server | Purpose | Type |
|---|---|---|
| `docsync-jira` | Fetch JIRA story, validate requirements | Custom Python |
| `github` | Create/update PRs, read workflows | Standard |
| `filesystem` | Read/write project files | Standard |

---

## Hooks & Validation

Three hooks enforce integrity:

| Hook | Event | Script | Purpose |
|---|---|---|---|
| `block-secrets` | PreToolUse (Bash) | `block-secrets.py` | Deny commands with secret patterns |
| `guard-generated` | PreToolUse (Write\|Edit) | `guard-generated-files.py` | Protect `.claude/` from accidental overwrites |
| `doc-sync-check` | Stop | `trigger-doc-sync.py` | Block session exit if `src/` changed but docs not synced |

---

## Human Gates (3 approval points)

1. **After Step 3 (Design Review)**  
   Chat approval required to proceed to implementation planning.
   
2. **After Step 7 (Verification)**  
   Tests must pass, coverage ≥80%, all checks green.
   
3. **After Step 8 (PR merge)**  
   CI must be green; human clicks merge button on GitHub.

---

## Key Rules

1. **No phase skipping.** Steps go 1→8 in order. Each step consumes the prior artifact.

2. **Requirement ID immutability.** `US-1`, `FR-1`, … `FR-n`, `NFR-1` are derived from the source story. Prose may be refined; IDs may not.

3. **Traceability throughout.** Every artifact links back to requirements:
   ```
   User Story → Requirements → Architecture → Design Review → Impl Plan → Code → Tests → Verification
   ```

4. **Separate Claude artifacts.** Use `claude-*` prefix to run both pipelines independently.

5. **Memory persistence.** Use `.claude/projects/*/memory/` to record insights, blockers, and decisions.

---

## Running the Pipeline

### Full Pipeline (Recommended)

```bash
claude
> /run-pipeline
```

Walks Steps 1–8 sequentially, pausing at gates (3, 6, 7) for approval.

### Step-by-Step (Manual Control)

```bash
claude
> /step-1-requirements
> /step-2-architecture
> /step-3-design-review     # Gate: approve in chat
> /step-4-impl-plan
> /step-5-implement
> /step-6-code-review
> /step-7-verify            # Gate: approve after tests pass
> /step-8-create-pr
```

### Sync Documentation

```bash
claude
> /doc-sync
```

---

## Settings & Configuration

See `.claude/settings.json` for:
- MCP server definitions
- Hook configuration
- Permission allowlist
- Environment variables

---

## Troubleshooting

**Q: Step X failed with "MCP server not found"**  
A: Ensure `.mcp.json` includes the custom server and Python environment is set up.

**Q: How do I reject a design and go back to Step 2?**  
A: In chat at Step 3 gate, respond: "Design not approved. Revise architecture for [reason]." Step 5+ locks once locked, revert Step 5 code and re-run /step-5-implement.

**Q: Tests fail at Step 7. What now?**  
A: Fix code in `src/` or `tests/`, re-run `/step-7-verify` to validate. Step 7 gate blocks until passing.

**Q: Can I use the same artifact files as Copilot Chat?**  
A: No—use the `claude-*` prefix. This lets both pipelines coexist. After both complete, compare and merge the best version.

---

## Comparison with Copilot Chat

| Aspect | Claude Code | Copilot Chat |
|---|---|---|
| Entry point | `/run-pipeline` CLI command | `/run-pipeline JIRA-ID` in chat |
| Agents | `.claude/agents/*.md` | Inline in Copilot Chat |
| Memory | `.claude/projects/*/memory/` | Not supported |
| Hooks | `.claude/settings.json` + `.claude/hooks/` | Not supported |
| MCP servers | `.claude/settings.json` | `.mcp.json` (GitHub Copilot style) |
| Artifact prefix | `claude-*` | (none) |

---

## Next Steps

1. Read [README-CLAUDE.md](../README-CLAUDE.md) for quick-start instructions.
2. Run `/run-pipeline` to start the full pipeline.
3. Approve designs at Step 3 gate.
4. Verify tests at Step 7 gate.
5. Review and merge PR from Step 8.

---

## See Also

- [CLAUDE.md](../CLAUDE.md) — Copilot Chat pipeline
- [README-CLAUDE.md](../README-CLAUDE.md) — Quick-start guide
- [.claude/commands/](commands/) — Command definitions
- [.claude/agents/](agents/) — Agent implementations

# CLAUDE.md

Guidance for working with the Automated Documentation Sync capstone project.

## The 8-Step Agentic SDLC Pipeline

This repository implements an **agentic SDLC** with independent GitHub Copilot and Claude Code pipelines, plus CLI tools for verification and artifact generation.

### Two operating modes

| Mode | Steps 1-4 | Steps 5-8 | Demo entry point |
|---|---|---|---|
| **GitHub Copilot (Pipeline A)** | Specialist agents in `.github/agents/` | Requirements through PR workflow | `@sdlc-orchestrator JIRA-ID` |
| **Claude Code (Pipeline B)** | Specialist agents in `.claude/agents/` and skills in `.claude/skills/` | Requirements through release workflow | `/pipeline` |
| **CLI generation** | Auto-generates requirements through plan artifacts | Not applicable | `docsync <story> -o . --phased` |

**Key rule:** Steps 1–4 artifacts may be hand-refined, but their requirement IDs (US-n, FR-n, NFR-n) must match the source story exactly. Steps 5–8 are prose and implementation; IDs still matter for traceability but prose is free-form.

---

## The 8 Steps

Use `@sdlc-orchestrator EPMCDMETST-55568` for the GitHub Copilot pipeline or `/pipeline` for Claude Code. Both dispatch the same stages in order, while keeping their artifact names and pipeline-state files separate.

| Step | Stage | Copilot artifact | Claude artifact | Gate |
|---|---|---|---|---|
| 1 | Requirements | `requirements.md` | `claude-requirements.md` | No |
| 2 | Architecture | `architecture.md` | `claude-architecture.md` | No |
| 3 | Design review | `design-review.md` | `claude-design-review.md` | Human approval |
| 4 | Implementation plan | `impl-plan.md` | `claude-impl-plan.md` | No |
| 5 | Implementation | `src/`, `tests/` | `src/`, `tests/` | No |
| 6 | Code review | `code-review.md` | `claude-code-review.md` | Advisory |
| 7 | Verification | `verification-report.md` | `claude-verification-report.md` | Human approval |
| 8 | PR and release | `PR.md`, `CHANGELOG.md` | `claude-pr-description.md`, `CHANGELOG.md` | CI before merge |

---

## Enforcement

| What | Where | Enforced by |
|---|---|---|
| Document structure + traceability | Root artifacts | `.githooks/pre-commit` (local) + `tests.yml` (CI) |
| Story-to-artifact ID parity (steps 1-4) | Generated artifacts | `doc-sync.yml` (CI) |
| Code coverage ≥80% | `tests/` | `tests.yml` (CI) |
| All 8 steps present | Merge time | `release.yml` (on tag push) |

---

## Quick Start

**To run the full pipeline with live Jira fetch:**

```bash
git config core.hooksPath .githooks  # One-time setup

# 1. Set Jira token (one-time)
export JIRA_API_TOKEN="your-personal-access-token"

# 2. Fetch live story and generate user-story.md + all artifacts
docsync "https://jira.company.com/browse/EPMCDMETST-55568" \
  --jira-token "$JIRA_API_TOKEN" \
  -o . \
  --non-interactive

# 3. Run the GitHub Copilot pipeline on the fresh user-story.md
# Then, in Copilot Chat:
@sdlc-orchestrator EPMCDMETST-55568
```

**Or use the one-command wrapper:**

```bash
# One-time setup
chmod +x .github/scripts/fetch-and-run.sh

# Fetch and prepare
export JIRA_API_TOKEN="your-token"
.github/scripts/fetch-and-run.sh EPMCDMETST-55568 "https://jira.company.com/browse/EPMCDMETST-55568"

# Then in Copilot Chat:
@sdlc-orchestrator EPMCDMETST-55568
```

**To verify a step output locally:**

```bash
docsync-verify . --story user-story.md
```

**To auto-generate steps 1-4 from a story (CLI mode):**

```bash
docsync user-story.md -o . --phased --non-interactive
```

---

## Artifact Locations

| Step | Artifact | Author | Locked after approval? |
|---|---|---|---|
| 1 | `requirements.md` | Copilot requirements agent | Step 3 gate |
| 2 | `architecture.md` | Copilot architecture agent | Step 3 gate |
| 3 | `design-review.md` | Copilot design-review agent | Step 3 gate |
| 4 | `impl-plan.md` | Copilot implementation-planner agent | No |
| 5 | `code-review.md` | Copilot code-review agent | Advisory |
| 6 | `verification-report.md` | Copilot QA-verifier agent | Step 7 gate |
| 7 | `CHANGELOG.md` | Copilot release-engineer agent | No |
| 8 | PR + release | CI + human | After merge |

---

## Key Principles

1. **No phase skipping.** Steps go 1→8 in order. Each consumes the prior artifact.
2. **Requirement IDs are immutable.** `US-1`, `FR-1`, ... `FR-n`, `NFR-1` are derived from the source story. Prose may be refined; IDs may not.
3. **Agents are the drivers.** GitHub Copilot uses `.github/agents/`; Claude Code uses `.claude/agents/` with `.claude/skills/`.
4. **Traceability throughout.** Every artifact cites the requirements it addresses.
5. **Human gates at 3, 6, 8.** Not all gates are blocking, but explicit approval is expected.

See `.github/copilot-instructions.md` and `docs/copilot-operating-model.md` for implementation details.

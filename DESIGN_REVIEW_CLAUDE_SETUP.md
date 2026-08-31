# Design Review: Claude Code Setup Issues & Ideal Mechanisms

> **Historical design review:** The issues and examples below describe the retired command-based setup. The current agent-and-skill implementation is documented in `.claude/CLAUDE.md`; do not treat deleted `.claude/commands/` paths as active instructions.

**Reviewer:** AI/LLM Expert (Claude Code + GitHub Copilot)
**Date:** 2026-08-18
**Scope:** `.claude/` directory structure, commands, agents, skills, hooks, MCP, and prompts

---

## Executive Summary

The project has a functional 8-step SDLC pipeline with both Claude Code and Copilot Chat pipelines. However, the Claude Code setup has **7 significant design issues** that deviate from Claude Code's intended architecture. Most stem from conflating Claude Code concepts (commands, agents, skills) that should be distinct, and from duplicating prompt content across multiple layers.

---

## Issue 1: Redundant 1:1 Command→Agent Mapping

**What exists:**
Every step has a command file AND a separate agent file with nearly identical content:

| Command (`.claude/commands/step-N*.md`) | Agent (`.claude/agents/step-N*-agent.md`) |
|---|---|
| `step-1-requirements.md` | `step-1-requirements-agent.md` |
| `step-2-architecture.md` | `step-2-architecture-agent.md` |
| `step-3-design-review.md` | `step-3-design-review-agent.md` |
| ... (8 pairs) | ... |

**The problem:**
- Claude Code **commands** and **agents** are not the same thing (see section below), but this project treats them as duplicate copies of the same content.
- The command files contain the full prompt, task description, context, constraints, and output format. The agent files contain nearly the same thing rephrased.
- This creates **drift risk** — if you update one, the other gets stale. It also **bloats context** since both load into the session.

**What Claude Code actually defines:**

| Concept | What it is | How it works |
|---|---|---|
| **Command** (`.claude/commands/*.md`) | A user-invocable slash command (`/step-1-requirements`) | Loads the markdown as the prompt. The file IS the instruction. No separate agent needed for single-command tasks. |
| **Agent** (`.claude/agents/*.md`) | A reusable sub-agent definition that can be spawned by the `Agent` tool or from a command | Used when a command needs to delegate work to a background or parallel sub-agent. Has frontmatter (`model`, `tools`). |
| **Skill** (`.claude/skills/*/SKILL.md`) | A reusable workflow pattern that can be invoked via the `Skill` tool | Cross-cutting concern — used by multiple commands/agents. Not pipeline-step-specific. |

**Ideal approach:**
- Commands should be **thin wrappers** that reference an agent or skill, NOT duplicate the full prompt.
- Agents should only exist where a **sub-agent is actually spawned** (e.g., the orchestrator calling step agents).
- Most step commands should be commands only (no agent) — the command's markdown IS the full instruction.

**Example fix — thin command:**
```markdown
# /step-1-requirements

Elicit functional and non-functional requirements from the story at `user-story.md`.

Use the requirements-elicitor skill workflow. Write output to `claude-requirements.md`.

**Artifact format:** Follow the template in `.claude/skills/requirements-elicitor/SKILL.md`.
```

This is ~5 lines instead of ~95 lines. The skill holds the reusable workflow; the command just invokes it.

---

## Issue 2: No YAML Frontmatter in Commands or Agents

**What exists:**
All `.claude/commands/*.md` and `.claude/agents/*.md` files are **plain markdown** — no frontmatter block.

**Compare with Copilot prompts (`.github/prompts/*.prompt.md`):**
```yaml
---
mode: agent
description: Elicit and document requirements from a user story with traceability IDs
tools: ["editFiles", "runCommands"]
---
```

Copilot prompts correctly use YAML frontmatter for metadata. Claude Code commands and agents support a similar mechanism.

**What Claude Code expects:**

For **commands**, the entire file IS the prompt — no special frontmatter required, but you can use `$ARGUMENTS` placeholder for dynamic input:
```markdown
# /step-1-requirements

Parse the story from: $ARGUMENTS
If no argument given, read `user-story.md`.
```

For **agents**, frontmatter controls model and tools:
```markdown
---
model: sonnet
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
---

You are the Architecture Specialist...
```

**The problem:**
- Agents have **no frontmatter** — they inherit the parent model and all tools, which is wasteful for tasks that only need Read/Write.
- Commands don't use `$ARGUMENTS` — the `/run-pipeline` command describes accepting a Jira ID but doesn't wire it to `$ARGUMENTS`.
- Without `description` in agent frontmatter, Claude Code can't display what each agent does in the UI.

**Ideal approach:**
```yaml
# .claude/agents/step-2-architecture-agent.md
---
model: sonnet
tools: ["Read", "Write", "Glob", "Grep"]
description: "Design system architecture from requirements"
---

You are the Architecture Specialist...
```

---

## Issue 3: Orchestration Failure Handling is Absent

**What exists:**
The `pipeline-orchestrator.md` describes sequential step execution with gates, but has **zero error handling**:

```
1. Calls /step-1-requirements → captures output
2. Calls /step-2-architecture → captures output
...
```

No mention of:
- What happens if a step **fails** (tool error, LLM timeout, validation error)
- What happens if a step produces **invalid output** (missing required sections, broken traceability)
- What happens if the **user rejects** at a gate (the agent mentions "loop back" but doesn't define HOW)
- What happens if an **MCP server is down** (Jira unreachable, filesystem server crashed)
- **Checkpoint/resume** — if the session dies mid-pipeline, there's no way to resume from the last successful step

**Compare with what the CLI already implements:**
- `checkpoint.py` — atomic checkpoint after each phase
- `resilience.py` — retry, circuit breaker, timeout
- `rollback_artifacts()` — clean up partial output on failure

**The Claude Code pipeline has NONE of this.**

**Ideal approach — add to orchestrator:**

```markdown
## Error Handling

### Step Failure
If any step agent returns an error or produces invalid output:
1. Log the error: `Memory: "Step N failed: [error]"`
2. Ask user: "Step N failed. Retry / Skip / Abort?"
3. On retry: re-invoke the same step agent (max 2 retries)
4. On skip: record skip reason, continue to next step (flag in final report)
5. On abort: clean up partial artifacts, exit

### Gate Rejection
If user rejects at a gate (Steps 3, 6, 7):
1. Record rejection reason in memory
2. Route back to the appropriate step:
   - Step 3 rejected → re-run Step 2 (architecture) or Step 3 (review)
   - Step 6 rejected → re-run Step 5 (implementation fixes)
   - Step 7 rejected → re-run Step 5 (test fixes) or Step 6 (re-review)
3. After 3 rejections on same step: escalate to user with summary

### MCP Server Unavailable
If docsync-jira MCP fails:
1. Fall back to local user-story.md
2. If no local file: prompt user to paste story
3. Log: "Jira unavailable, using fallback"

### Session Recovery
After session restart, orchestrator should:
1. Check for `.docsync_checkpoint.json` (from CLI pipeline)
2. Check for existing `claude-*.md` artifacts
3. Ask: "Pipeline partially complete. Resume from Step N?"
```

---

## Issue 4: Command Names Are Not Meaningful or Short

**What exists:**
```
/step-1-requirements
/step-2-architecture
/step-3-design-review
/step-4-impl-plan
/step-5-implement
/step-6-code-review
/step-7-verify
/step-8-create-pr
/doc-sync
/run-pipeline
```

**Problems:**
1. **`/step-N-` prefix is noise** — users don't think in step numbers, they think in tasks. Nobody says "run step 4." They say "plan implementation" or "create a PR."
2. **Inconsistent naming** — `/step-4-impl-plan` (noun) vs `/step-5-implement` (verb) vs `/step-7-verify` (verb) vs `/step-8-create-pr` (verb phrase)
3. **Too long** — `/step-1-requirements` is 21 chars. Claude Code commands should be short, memorable.
4. **The step numbers leak an implementation detail** — if you reorder steps, all command names break.

**Ideal approach — task-based, short names:**

```
/elicitarereqs       # or /reqs
/design
/review
/plan
/implement
/codereview          # or /reviewcode
/verify
/release             # or /pr
/sync                # replaces /doc-sync
/pipeline            # replaces /run-pipeline
```

If step numbers are needed for documentation, put them in the command description, not the name:
```yaml
---
description: "Step 1/8: Elicit and structure requirements from a user story"
---
```

---

## Issue 5: Prompt Files Are Plain Markdown (No YAML Structure)

**What exists (Copilot prompts):**
```yaml
---
mode: agent
description: Elicit and document requirements from a user story with traceability IDs
tools: ["editFiles", "runCommands"]
---
```

**What exists (Claude Code commands):**
```markdown
# /step-1-requirements

**Elicit functional and non-functional requirements from a user story.**

## Role
...
## Task
...
```

**The problem:**
The Copilot `.github/prompts/*.prompt.md` files correctly use YAML frontmatter with `mode`, `description`, and `tools`. The Claude Code `.claude/commands/*.md` files have **no structured metadata at all** — everything is prose.

This means:
- Claude Code can't auto-discover what tools each command needs
- No `description` for UI display
- No way to distinguish `mode: agent` (background) from interactive commands
- The `tools` field in Copilot prompts constrains what the agent can do — Claude Code commands have no equivalent, so they get ALL tools (wasteful, potential security issue)

**Ideal approach for Claude Code:**
Commands don't require frontmatter (they're simpler than Copilot prompts), but agents SHOULD have it:

```yaml
# .claude/agents/step-5-implementation-agent.md
---
model: sonnet
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
description: "Implement code and tests per the implementation plan"
---

You are the Implementation Specialist...
```

---

## Issue 6: Skills Are Misused as Step-Specific Workflows

**What exists:**
```
.claude/skills/
├── requirements-elicitor/SKILL.md    # Only used by Step 1
└── pr-generator/SKILL.md             # Only used by Step 8
```

**The problem:**
Per Claude Code's design, **skills are cross-cutting, reusable workflows** — not step-specific implementations. The `requirements-elicitor` skill is only ever called from `/step-1-requirements`. The `pr-generator` skill is only ever called from `/step-8-create-pr`. These aren't "skills" — they're step implementations disguised as skills.

A skill should be something like:
- "code-review" — used by Step 6 code review AND ad-hoc reviews
- "test-runner" — used by Step 7 verification AND manual test runs
- "doc-generator" — used by multiple steps that produce markdown

**What's actually happening:**
Each step command references its "skill" but the skill content is nearly identical to the command content. Three layers of duplication:

```
command/step-1-requirements.md    →  95 lines
agent/step-1-requirements-agent.md →  60 lines
skill/requirements-elicitor/SKILL.md → 55 lines
```

All three say the same thing.

**Ideal approach:**
1. **Keep skills only for truly reusable workflows** — "code-review" could be a skill (used by `/codereview` command AND by the orchestrator agent)
2. **Move step-specific logic into commands** — the command IS the prompt
3. **Use agents only for background delegation** — if a command spawns a sub-agent, THAT needs an agent file

---

## Issue 7: Custom Instructions vs Prompts — Conflated

**What exists:**
The project has THREE layers of instructions:
1. `.claude/CLAUDE.md` — project-level custom instructions (always loaded)
2. `.claude/commands/*.md` — user-invocable commands (loaded on `/command`)
3. `.claude/agents/*.md` — agent definitions (loaded when agent is spawned)

**The confusion:**
The `.claude/CLAUDE.md` contains BOTH:
- **Always-on rules** (requirement ID immutability, traceability, phase order) — these are correct custom instructions
- **Step-by-step pipeline instructions** — these should be in the orchestrator command, not in the always-on context

**What Claude Code defines:**

| Concept | When loaded | Purpose |
|---|---|---|
| **Custom Instructions** (`CLAUDE.md`, `.claude/CLAUDE.md`) | Every session, always in context | Project-wide rules, conventions, constraints. Should be SHORT — they consume context on every turn. |
| **Prompts/Commands** (`.claude/commands/*.md`) | On `/command` invocation only | Task-specific instructions. Loaded once, full detail. |
| **Agent Definitions** (`.claude/agents/*.md`) | When agent is spawned | Sub-agent system prompt. Only loaded for that agent's context. |

**The problem:**
- `.claude/CLAUDE.md` is ~160 lines of detailed step-by-step instructions that should NOT be in always-on context. This wastes tokens on every conversation turn.
- The step instructions are duplicated between CLAUDE.md, commands, and agents.
- Memory files (`.claude/projects/*/memory/`) are not being used for session-specific decisions — everything is hardcoded in CLAUDE.md.

**Ideal `.claude/CLAUDE.md` — keep it lean:**
```markdown
# CLAUDE.md — Project Rules

## Pipeline Rules
- 8-step SDLC: Steps 1→8 in order, no skipping
- Requirement IDs (US-1, FR-1..n, NFR-1) are immutable
- Every artifact must trace back to source requirements
- Human gates at: design review (3), verification (7), release (8)
- Artifact prefix: `claude-` for Claude Code pipeline

## Conventions
- Use `.claude/skills/` for reusable workflows
- Store decisions in `.claude/projects/*/memory/`
- MCP servers: `docsync-jira` (Jira), `github` (PRs), `filesystem` (I/O)
```

That's ~15 lines. The remaining 145 lines should move to commands/agents.

---

## Additional Issues Found

### Issue 8: Duplicate Prompt Content Across Pipelines

The `.github/prompts/` (Copilot) and `.claude/commands/` (Claude Code) contain near-identical step logic. If the requirements extraction logic changes, you must update BOTH locations. Consider:
- A single source of truth for each step's logic
- Pipeline-specific wrappers that reference shared content

### Issue 9: MCP Tools Underutilized

The `docsync-jira` MCP server exposes 4 tools, but the Claude Code commands don't reference MCP tools explicitly. The commands rely on the agent "reading files" instead of calling `fetch_jira_story` MCP tool directly. This means:
- No programmatic Jira integration in the Claude Code pipeline
- The MCP server is only useful if you manually invoke it

### Issue 10: Hooks Don't Cover All Failure Modes

Current hooks:
- `block-secrets` — PreToolUse (Bash)
- `guard-generated` — PreToolUse (Write/Edit)
- `doc-sync-check` — Stop

Missing hooks that would improve the pipeline:
- **PreToolUse (Write)**: Validate that artifact files match expected format before writing
- **PostToolUse (Bash)**: If test command ran, check coverage threshold
- **Stop**: Check that all 8 artifacts exist before allowing session end

---

## Recommended Refactored Structure

```
.claude/
├── CLAUDE.md                          # ~20 lines: rules only, no step details
├── settings.json                      # MCP, hooks, permissions (keep as-is)
├── commands/
│   ├── reqs.md                        # Short name, thin wrapper
│   ├── design.md
│   ├── review.md
│   ├── plan.md
│   ├── implement.md
│   ├── codereview.md
│   ├── verify.md
│   ├── release.md
│   ├── sync.md                        # replaces doc-sync
│   └── pipeline.md                    # replaces run-pipeline
├── agents/
│   ├── orchestrator.md                # ONLY agent that spawns sub-agents
│   ├── architect.md                   # model: sonnet, tools: [Read, Write, Glob]
│   └── implementer.md                 # model: sonnet, tools: [Read, Write, Edit, Bash]
├── skills/
│   ├── code-review.md                 # Truly reusable: ad-hoc + Step 6
│   ├── test-runner.md                 # Truly reusable: Step 7 + manual
│   └── traceability.md                # Used by multiple steps
└── hooks/                             # Keep as-is
```

**Key changes:**
1. Commands → short names, thin (5-10 lines each)
2. Agents → only where sub-agent spawning is needed, with frontmatter
3. Skills → only cross-cutting reusable workflows
4. CLAUDE.md → rules only, no step instructions
5. YAML frontmatter on agents for model/tools/description

---

## Summary Table

| # | Issue | Severity | Effort to Fix |
|---|---|---|---|
| 1 | Redundant 1:1 command→agent mapping | High | Medium — merge or thin out |
| 2 | No YAML frontmatter on agents | Medium | Low — add 4 lines per agent |
| 3 | No orchestration failure handling | High | High — rewrite orchestrator |
| 4 | Command names not meaningful/short | Medium | Low — rename files + update refs |
| 5 | No YAML in prompts (vs Copilot) | Low | Low — agents get frontmatter |
| 6 | Skills misused as step-specific | Medium | Medium — restructure skills |
| 7 | CLAUDE.md has too much detail | High | Low — trim to rules only |
| 8 | Duplicate content across pipelines | Medium | High — single source of truth |
| 9 | MCP tools underutilized | Medium | Medium — wire MCP into commands |
| 10 | Hooks don't cover all failure modes | Low | Medium — add PostToolUse hooks |

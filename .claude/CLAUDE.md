# CLAUDE.md — Claude Code SDLC Pipeline

Guidance for the **Claude Code implementation** of the 8-step Agentic SDLC Pipeline for Automated Documentation Sync.

This complements the [Copilot Chat pipeline](../CLAUDE.md) documented in `.github/prompts/`. Both pipelines are independent and produce separate artifacts with the `claude-` prefix for Claude Code.

---

## The 8 Steps (Commands + Agents)

| Step | Command | Agent | Input | Output | Gate |
|---|---|---|---|---|---|
| 1 | `/step-1-requirements` | `step-1-requirements-agent.md` | `user-story.md` | `claude-requirements.md` | No |
| 2 | `/step-2-architecture` | `step-2-architecture-agent.md` | `claude-requirements.md` | `claude-architecture.md` | No |
| 3 | `/step-3-design-review` | `step-3-design-review-agent.md` | req + arch | `claude-design-review.md` | ✋ **YES** |
| 4 | `/step-4-impl-plan` | `step-4-impl-plan-agent.md` | approved req + arch | `claude-impl-plan.md` | No |
| 5 | `/step-5-implement` | `step-5-implementation-agent.md` | `claude-impl-plan.md` | `src/`, `tests/` | No |
| 6 | `/step-6-code-review` | `step-6-code-review-agent.md` | code + tests | `claude-code-review.md` | No |
| 7 | `/step-7-verify` | `step-7-verification-agent.md` | tests + artifacts | `claude-verification-report.md` | ✋ **YES** |
| 8 | `/step-8-create-pr` | `step-8-pr-agent.md` | all approvals | `claude-pr-description.md`, `CHANGELOG.md` | CI |

**Additional:** `/doc-sync` (skill) — sync documentation; `/run-pipeline` — full 8-step walk.

---

## Artifact Naming

All Claude Code artifacts use `claude-` prefix:

| Step | Artifact |
|---|---|
| 1 | `claude-requirements.md` |
| 2 | `claude-architecture.md` |
| 3 | `claude-design-review.md` |
| 4 | `claude-impl-plan.md` |
| 6 | `claude-code-review.md` |
| 7 | `claude-verification-report.md` |
| 8 | `claude-pr-description.md`, `CHANGELOG.md` |

---

## MCP Servers (`.mcp.json` + `.claude/settings.json`)

| Server | Purpose | Command |
|---|---|---|
| `docsync-jira` | Fetch JIRA story, validate reqs | `python -m documentation_sync.jira_mcp_server` |
| `github` | PRs, workflows | `npx -y @modelcontextprotocol/server-github` |
| `filesystem` | File access | `npx -y @modelcontextprotocol/server-filesystem .` |

---

## Hooks (`.claude/settings.json` + `.claude/hooks/`)

| Hook | Event | Script | Purpose |
|---|---|---|---|
| `block-secrets` | PreToolUse (Bash) | `block-secrets.py` | Deny secret patterns |
| `guard-generated` | PreToolUse (Write/Edit) | `guard-generated-files.py` | Protect `.claude/` |
| `doc-sync-check` | Stop | `trigger-doc-sync.py` | Block exit if src/ changed |

---

## Human Gates (3 approvals)

1. **After Step 3** — Design review approval in chat
2. **After Step 7** — Tests pass, coverage ≥80%, all green
3. **After Step 8** — CI green, human merges PR

---

## Key Rules

1. **No phase skipping** — Steps 1→8 in order
2. **Requirement ID immutability** — `US-1`, `FR-1..n`, `NFR-1` from source story
3. **Traceability** — Every artifact links back: Story → Reqs → Arch → Design → Plan → Code → Tests → Verify
4. **Separate artifacts** — Use `claude-*` prefix for coexistence
5. **Memory persistence** — `.claude/projects/*/memory/` for decisions, blockers, lessons

---

## Running the Pipeline

```bash
claude
> /run-pipeline                    # Full 8-step, pauses at gates
> /step-1-requirements             # Individual step
> /step-2-architecture
> /step-3-design-review            # Gate: approve in chat
> /step-4-impl-plan
> /step-5-implement
> /step-6-code-review
> /step-7-verify                   # Gate: approve after tests
> /step-8-create-pr
> /doc-sync                        # Just sync docs
```

### Live Jira Fetch for Copilot Pipeline

While Claude Code uses its own `claude-requirements.md` artifacts, the Copilot pipeline needs `user-story.md`. Use the CLI to fetch live data:

```bash
# One-time: set Jira token
export JIRA_API_TOKEN="your-personal-access-token"

# Fetch live story → writes user-story.md at repo root
docsync "https://jira.company.com/browse/EPMCDMETST-55568" \
  --jira-token "$JIRA_API_TOKEN" \
  -o . \
  --non-interactive

# Then run Copilot pipeline:
/run-pipeline EPMCDMETST-55568
```

Or use the wrapper script:
```bash
chmod +x .github/scripts/fetch-and-run.sh
export JIRA_API_TOKEN="your-token"
.github/scripts/fetch-and-run.sh EPMCDMETST-55568 "https://jira.company.com/browse/EPMCDMETST-55568"
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

- **MCP server not found:** Ensure `.mcp.json` includes custom server, Python env set up
- **Reject design:** At Step 3, respond: "Design not approved. Revise for [reason]."
- **Tests fail at Step 7:** Fix `src/` or `tests/`, re-run `/step-7-verify`
- **Artifact conflicts:** Use `claude-*` prefix — both pipelines coexist

---

## See Also

- [CLAUDE.md](../CLAUDE.md) — Copilot Chat pipeline
- [README-CLAUDE.md](../README-CLAUDE.md) — Quick-start guide
- [.claude/commands/](commands/) — Command definitions
- [.claude/agents/](agents/) — Agent implementations
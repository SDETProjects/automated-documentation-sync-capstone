---
mode: agent
description: Orchestrate the full 8-step SDLC pipeline from a Jira story ID
tools: ["codebase", "editFiles", "runCommands"]
---

# SDLC Pipeline Orchestrator

## Input

User provides a **Jira story ID** (e.g., `EPMCDMETST-57618`).

## Execution

Run the full 8-step agentic SDLC pipeline. For each step:

1. **Load the step prompt** from `.github/prompts/step-N-*.prompt.md`
2. **Execute the step** using the instructions in that prompt
3. **Commit the artifact** (when complete)
4. **Gate pause** (after steps 3, 6, 8) — ask the user for approval before proceeding
5. **Verification** — between steps, run `docsync-verify . --story user-story.md` to ensure document quality

## Steps

| Step | Artifact | Gate After? |
|---|---|---|
| 1 | requirements.md | No |
| 2 | architecture.md | No |
| 3 | design-review.md | **YES** |
| 4 | impl-plan.md | No |
| 5 | code-review.md | No |
| 6 | verification-report.md | **YES** |
| 7 | code & tests | No |
| 8 | CHANGELOG.md, PR description | **YES** |

## Key Rules

- Follow the order. Do not skip steps.
- Answer clarifying questions before writing any artifacts.
- Requirement IDs (US-n, FR-n, NFR-n) are immutable; derived from the story.
- Prose may be refined and extended; IDs may not drift.
- At each gate, wait for explicit user approval before advancing.
- All CI gates (tests, coverage, document quality, verification) must pass before final merge.

## Smart Story Resolution (Auto-Fetch → Local File → User Paste)

**Before Step 1, the orchestrator MUST resolve the story source in this priority order:**

### Priority 1: Auto-Fetch from Jira (if token available)
```bash
# Check if JIRA_API_TOKEN is set
if [ -n "$JIRA_API_TOKEN" ]; then
  # Try to construct URL from issue key (requires JIRA_BASE_URL or config)
  JIRA_BASE="${JIRA_BASE_URL:-}"
  if [ -z "$JIRA_BASE" ] && [ -f "docsync.config.json" ]; then
    JIRA_BASE=$(cat docsync.config.json | grep -o '"jira_base_url"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
  fi
  if [ -n "$JIRA_BASE" ]; then
    JIRA_URL="${JIRA_BASE}/browse/${ISSUE_KEY}"
    # Run docsync to fetch and generate user-story.md
    docsync "$JIRA_URL" --jira-token "$JIRA_API_TOKEN" -o . --non-interactive
    echo "��� Fetched live Jira story → user-story.md"
  else
    echo "������ JIRA_BASE_URL not set; skipping auto-fetch"
  fi
else
  echo "������ JIRA_API_TOKEN not set; skipping auto-fetch"
fi
```

### Priority 2: Local `user-story.md` File
```bash
# If auto-fetch didn't run or failed, check for existing file
if [ -f "user-story.md" ]; then
  echo "���� Using existing user-story.md"
else
  echo "���� No user-story.md found"
fi
```

### Priority 3: Ask User to Paste Story Text
If neither Priority 1 nor 2 yields a story, **prompt the user in chat**:
> "I couldn't find a live Jira story (no token/base URL) or local `user-story.md`.  
> Please paste the story text below (Jira key, summary, description, acceptance criteria).  
> Press Enter twice when done."

## Example Invocation

```
/run-pipeline EPMCDMETST-57618
```

## Orchestrator Behavior

1. **Extract issue key** from user message (e.g., `EPMCDMETST-55568`)
2. **Run auto-fetch logic** via `runCommands` (see above)
3. **Verify `user-story.md` exists** at repo root
4. **If missing after auto-fetch**, ask user to paste story in chat
5. **Once story is available**, load Step 1 prompt and begin pipeline
6. **Between steps**, run `docsync-verify . --story user-story.md`

## Manual Pre-Fetch Options (Still Supported)

If you prefer to fetch manually before running the pipeline:

### Option 1: Pre-fetch via CLI
```bash
export JIRA_API_TOKEN="your-personal-access-token"
docsync "https://jira.company.com/browse/EPMCDMETST-55568" \
  --jira-token "$JIRA_API_TOKEN" \
  -o . \
  --non-interactive
/run-pipeline EPMCDMETST-55568
```

### Option 2: One-Command Wrapper
```bash
chmod +x .github/scripts/fetch-and-run.sh
export JIRA_API_TOKEN="your-token"
.github/scripts/fetch-and-run.sh EPMCDMETST-55568 "https://jira.company.com/browse/EPMCDMETST-55568"
/run-pipeline EPMCDMETST-55568
```

### Option 3: CI/GitHub Action
See `.github/workflows/fetch-jira-story.yml` (requires `JIRA_API_TOKEN` secret).

---

The orchestrator will auto-fetch from Jira (if configured), fall back to local `user-story.md`, or ask you to paste the story — then guide you through all 8 steps.

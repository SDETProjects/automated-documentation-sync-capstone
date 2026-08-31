---
name: code-review
description: Static analysis and quality check of src/ and tests/. Invokes code-reviewer agent to write claude-code-review.md. Non-blocking — findings inform fixes but do not halt the pipeline.
---

# Code Review Skill

1. Dispatch `Agent(subagent_type="code-reviewer", prompt="Review src/ and tests/ for correctness, security, coverage, and architecture alignment. Write claude-code-review.md")`.
2. Present findings grouped by severity: Critical / High / Medium / Low.
3. For Critical or High findings: ask the user whether to fix now or log as tech debt before `/verify`.
4. This gate is **non-blocking** — the pipeline continues regardless, but findings are persisted.

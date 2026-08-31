---
name: implement
description: Write source code and tests following claude-impl-plan.md. Invokes code-developer agent targeting >=80% test coverage.
---

# Implementation Skill

1. Verify `claude-impl-plan.md` exists; abort if missing.
2. Dispatch `Agent(subagent_type="code-developer", prompt="Implement tasks from claude-impl-plan.md into src/ and tests/, target >=80% coverage")`.
3. After the agent completes, run: `pytest tests/ --cov=src/documentation_sync --cov-report=term-missing`
4. If coverage < 80%, dispatch `code-developer` again with the coverage gap report as context.
5. Confirm all tests pass (exit code 0) before proceeding to `/code-review`.

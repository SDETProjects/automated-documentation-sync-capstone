---
mode: agent
description: Prepare release artifacts including changelog and merge evidence
tools: ["editFiles", "runCommands"]
---

# Prompt: Generate CHANGELOG.md and PR description

After verification passes, produce CHANGELOG.md and prepare for merge with:

1. CHANGELOG.md: Document all changes in user-facing language. Include:
   - What changed (features, fixes, breaking changes)
   - Why it changed (linked to requirements)
   - Migration guide if there are breaking changes
   - Any known limitations or deferred items

2. PR Summary: comprehensive PR description covering:
   - What was built (2-3 sentence summary linked to the story key)
   - Traceability: which US/FR/NFR are covered
   - Changes made: list of files added/modified with brief rationale
   - Test evidence: summary of test results and coverage
   - Known limitations: anything explicitly NOT in scope
   - Merge checklist: confirm all gates passed (tests, code review, verification)

3. Release readiness: confirm this is ready for tag and release (vs. draft/experimental).

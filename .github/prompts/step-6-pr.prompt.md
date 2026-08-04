---
mode: agent
description: Generate comprehensive PR description with full traceability and verification evidence
tools: ["editFiles", "runCommands"]
---

# Prompt: Generate PR.md

Using all approved artifacts (requirements.md, architecture.md, design-review.md, impl-plan.md, code-review.md, test-evidence.md), produce PR.md following .github/pull_request_template.md structure:

1. A concise summary of the change and the Jira story it implements.
2. Traceability IDs covered (US, FR, NFR).
3. A checklist of artifacts updated.
4. Verification steps (how to run tests locally and confirm CI passes).
5. Notes on any clarifying assumptions made during requirements generation.

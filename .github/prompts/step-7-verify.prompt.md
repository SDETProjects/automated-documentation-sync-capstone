---
mode: agent
description: Execute verification suite and document test evidence and artifact quality
tools: ["editFiles", "runCommands"]
---

# Prompt: Generate verification-report.md

After implementation and code review approval, produce verification-report.md with:

1. Test Execution Summary: which test suites ran, how many tests passed, coverage percentage.
2. Integration Verification: verify the implemented features work end-to-end (happy path + edge cases).
3. Traceability Verification: confirm all FR/NFR requirements are covered by tests; map requirements to test cases.
4. Artifact Quality Check: run `docsync-verify` to confirm document structure and ID parity.
5. An Outcome section: Pass, Pass with caveats, or Fail. List any test failures or coverage gaps that must be resolved before merge.

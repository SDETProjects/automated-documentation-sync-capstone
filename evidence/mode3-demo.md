# Mode 3 Demo Transcript — Interactive Phased Generation with LLM Clarifications

**Command:**
```
docsync samples/jira_story.json -o demo_output_3 --phased --llm claude
```

**Terminal output:**
```
$ docsync samples/jira_story.json -o demo_output_3 --phased --llm claude

LLM provider: Claude (Anthropic SDK)

=== Phase 1: Requirements ===

[Clarification needed] Are there any edge cases (errors, empty states,
concurrent access) not covered by the 4 acceptance criteria listed?
> The tool should handle partial JSON (missing optional fields) gracefully
  and continue with defaults rather than failing hard.

[Clarification needed] The story is labeled ['documentation', 'automation',
'sdlc']. Should any of these labels map to a specific measurable NFR
(e.g. a latency target)?
> No latency target. The NFR is traceability: every generated artifact must
  link back to the originating story ID.

[Clarification needed] Who is the primary reviewer/approver for the
generated requirements before architecture work begins?
> The QA lead reviews requirements; the tech lead reviews architecture.

Requirements locked in. Proceed to architecture? [y/N] y

Architecture drafted. Proceed to design review? [y/N] y

Design review recorded. Proceed to implementation planning? [y/N] y

Phased run complete: 5 artifact(s) in C:\...\demo_output_3:
  - [requirements] requirements.md
  - [architecture] architecture.md
  - [design-review] design-review.md
  - [impl-plan] impl-plan.md
  - [pr] PR.md
```

**What this shows:**

1. **LLM adapter detection**: Claude (Anthropic SDK) is selected automatically
   because `ANTHROPIC_API_KEY` is set in the environment.

2. **Phase 1 — Clarifying Questions**: Three questions generated (by LLM if
   available, heuristic fallback if not). User answers are collected
   interactively via CLI prompts and incorporated into the enriched story
   before requirements are locked.

3. **Phase 2 — Architecture Gate**: Execution pauses. Human explicitly
   approves before architecture work proceeds.

4. **Phase 3 — Design Review Gate**: Execution pauses again. Human confirms
   design decisions are acceptable before implementation planning begins.

5. **Phase 4 — Implementation**: impl-plan.md and PR.md generated after
   all prior phases are approved.

**Key capstone differentiator visible here:**
- The tool is an **orchestrator**, not a static generator.
- Human judgment is embedded at three points: Q&A, architecture approval,
  design-review approval.
- LLM generates the questions; the human provides the answers.
- Each phase writes its artifact to disk immediately, so a partially-approved
  run still leaves reviewable output behind.

---

**Fallback demo (Copilot unavailable):**
```
$ docsync samples/jira_story.json -o demo_output_3b --phased --llm copilot

WARNING: No LLM adapter available.
  - Set ANTHROPIC_API_KEY for the Claude SDK path
  - Or install the Claude CLI and ensure 'claude --version' works
  - Or omit --llm to use the offline heuristic question generator
Continuing with offline heuristic questions.

=== Phase 1: Requirements ===

[Clarification needed] Are there any edge cases (errors, empty states,
concurrent access) not covered by the 4 acceptance criteria listed?
> ...
```

**What this shows**: `--llm copilot` is architecturally wired; when unavailable,
the system falls back to heuristic questions with a clear warning rather than
crashing — the human-in-the-loop flow continues uninterrupted.

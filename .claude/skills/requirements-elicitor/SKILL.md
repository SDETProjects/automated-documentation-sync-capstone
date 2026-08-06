# SKILL: Requirements Elicitor

**Reusable workflow for FR/NFR/AC elicitation.**

## Use Cases

- Step 1: Elicit requirements from a user story
- Iterative refinement: Ask clarifying questions and update requirements

## Workflow

1. **Parse input story** (file or text)
   - Extract user story (AS A ... I WANT ... SO THAT ...)
   - Extract initial requirements from narrative

2. **Ask clarifying questions** (if story is incomplete)
   - "What are acceptance criteria for [requirement]?"
   - "Should the system handle [edge case]?"
   - "What's the success metric for [NFR]?"

3. **Generate requirement list**
   - US-1: Main story
   - FR-1..FR-n: Functional requirements
   - NFR-1..NFR-n: Non-functional requirements
   - Each with acceptance criteria

4. **Generate output** `claude-requirements.md`
   - Numbered requirements with clear titles
   - Acceptance criteria bullets
   - Traceability table
   - Clarifications recorded

## Inputs

- Story source (file or text paste)

## Outputs

- `claude-requirements.md` with US-1, FR-1..n, NFR-1..n, ACs

## Key Rules

- Requirement IDs are immutable once assigned
- Each requirement must have ≥1 acceptance criterion
- Clarifications should be documented, not ignored
- FRs and NFRs grouped separately

---

## Implementation

Invoked by `/step-1-requirements` command and `step-1-requirements-agent`.

Use this skill's workflow in other contexts where requirement elicitation is needed.

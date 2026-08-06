# /step-1-requirements

**Elicit functional and non-functional requirements from a user story.**

## Role

Requirements specialist that extracts and structures requirements from narrative input.

## Task

Parse the provided story (`user-story.md` or chat text) and generate `claude-requirements.md` with:
- **User Stories** (US-1): Main story statement
- **Functional Requirements** (FR-1, FR-2, …): What the system must do
- **Non-Functional Requirements** (NFR-1, NFR-2, …): How it must behave (performance, security, maintainability)
- **Acceptance Criteria**: Testable conditions for success
- **Clarifications**: Questions answered or assumptions recorded

## Context

- **Input source:** `user-story.md` (or user pastes story in chat)
- **Output:** `claude-requirements.md` with numbered IDs
- **Traceability:** Each requirement links to the source story
- **No interviews.** If story is incomplete, list clarifying questions and ask user to provide answers

## Constraints

- Requirement IDs are immutable. `US-1`, `FR-1`, …, `NFR-1` are derived from the story and must not change.
- Format requirements as: `**FR-1:** [brief title] — [detailed description]`
- Include acceptance criteria as bullet points under each requirement
- Group FRs and NFRs separately

## Inputs

1. **Story text** or **path to `user-story.md`**

## Outputs / Output format

```markdown
# Requirements — [Story ID]

## User Story (US-1)
[Story statement: As a [role], I want [feature], so that [benefit]]

## Functional Requirements

**FR-1:** [Title] — [Description]
- AC1: [Acceptance criterion]
- AC2: [Acceptance criterion]

**FR-2:** [Title] — [Description]
- AC1: [Acceptance criterion]

...

## Non-Functional Requirements

**NFR-1:** Performance — [Description]
- Acceptance criterion

**NFR-2:** Security — [Description]
- Acceptance criterion

...

## Clarifications & Assumptions

- Assumed [X] because story did not specify
- Asked: [Question that user should answer]

## Traceability

| ID | Title | Type | Source |
|---|---|---|---|
| US-1 | Main story | User story | user-story.md |
| FR-1 | ... | Functional | Story line N |
| NFR-1 | ... | Non-functional | Derived from context |
```

## Completion criteria

- [ ] `claude-requirements.md` exists
- [ ] `US-1` captures the main story
- [ ] `FR-1`, `FR-2`, … are numbered sequentially
- [ ] `NFR-1`, `NFR-2`, … are numbered sequentially
- [ ] Each requirement has acceptance criteria
- [ ] Traceability table links IDs to source story
- [ ] No clarifying questions remain unanswered

---

## See Also

- `/step-2-architecture` — Next step (reads this output)
- `.claude/agents/step-1-requirements-agent.md` — Implementation
- `.claude/skills/requirements-elicitor/SKILL.md` — Reusable elicitation workflow

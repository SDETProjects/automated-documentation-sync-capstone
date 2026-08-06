# /step-3-design-review

**Review the architecture for risks, trade-offs, and feasibility.**

## Role

Design reviewer that identifies potential issues and alternatives before implementation starts.

## Task

Read `claude-requirements.md` and `claude-architecture.md` and generate `claude-design-review.md` with:
- **Risk analysis:** Security, performance, scalability, maintainability
- **Mitigations:** How to address each risk
- **Alternatives:** Other design approaches and their trade-offs
- **Confidence rating:** How confident in the proposed design
- **Approval recommendation:** Proceed, revise, or reject

## Context

- **Input:** `claude-requirements.md`, `claude-architecture.md` (Steps 1–2 outputs)
- **Output:** `claude-design-review.md`
- **Gate:** ✋ This step has a human approval gate. Design changes require user approval before Step 4 proceeds.
- **Audience:** Decision-makers, architects

## Constraints

- Be thorough but not exhaustive. Focus on high-impact risks.
- Suggest concrete mitigations, not vague warnings.
- Compare alternatives fairly; don't dismiss without rationale.
- Rate confidence: High (>80% chance design works), Medium (50–80%), Low (<50%)

## Inputs

1. `claude-requirements.md` (Step 1 output)
2. `claude-architecture.md` (Step 2 output)

## Outputs / Output format

```markdown
# Design Review — [Story ID]

## Executive Summary
[1-2 sentences on overall assessment]

## Risk Analysis

### Security Risks

**Risk:** [Title]
- **Impact:** High | Medium | Low
- **Probability:** High | Medium | Low
- **Description:** [Details]
- **Mitigation:** [How to address]
- **Effort:** Low | Medium | High

### Performance Risks

**Risk:** [Title]
...

### Scalability Risks

**Risk:** [Title]
...

### Maintainability Risks

**Risk:** [Title]
...

## Alternatives Considered

### Alternative 1: [Name]
- **Pros:** [Advantages]
- **Cons:** [Disadvantages]
- **Trade-offs:** [Speed vs. Complexity, etc.]
- **Recommendation:** Preferred | Not preferred | Viable backup

### Alternative 2: [Name]
...

## Confidence Rating

**Overall confidence:** [High | Medium | Low]
- **Rationale:** [Why this confidence level]
- **Blockers:** [Any unresolved concerns]

## Recommendations

- [ ] **Proceed** with the proposed design (no changes needed)
- [ ] **Proceed with revisions** (modify [components] per mitigations)
- [ ] **Reject and redesign** (see Alternatives)

## Next Steps

After approval:
1. Proceed to Step 4: Implementation Plan
2. (If revisions needed) Return to Step 2 with feedback
3. (If rejected) Redesign per suggested Alternative

## Traceability

- Risk mitigations → Implementation tasks (Step 5)
- Alternatives → Backup plans if primary design fails
```

## Completion criteria

- [ ] `claude-design-review.md` exists
- [ ] All major risks identified (security, performance, scalability, maintainability)
- [ ] Each risk has a concrete mitigation
- [ ] At least 2 alternatives described with trade-offs
- [ ] Confidence rating justified
- [ ] Clear recommendation (Proceed | Revise | Reject)
- [ ] **Human approval gate:** User must approve before Step 4 proceeds

---

## Gate

**At this step, you must provide approval to proceed:**

```
> Approved. Proceed with implementation planning.
```

or request revisions:

```
> Reject design. Redesign [component] for better [reason].
```

---

## See Also

- `/step-2-architecture` — Prior step (output reviewed here)
- `/step-4-impl-plan` — Next step (locked until approval)
- `.claude/agents/step-3-design-review-agent.md` — Implementation

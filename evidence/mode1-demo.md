# Mode 1 Demo Transcript — File-Based (One-Shot)

**Command:**

```
docsync samples/jira_story.json -o demo_output_1
```

**Terminal output:**

```
$ docsync samples/jira_story.json -o demo_output_1

Generated 5 artifact(s) in C:\...\demo_output_1:
  - requirements.md
  - architecture.md
  - design-review.md
  - impl-plan.md
  - PR.md
```

**What this shows:**

- Local JSON file parsed and validated without errors.
- All five SDLC artifacts generated in a single shot.
- No LLM or network access required.
- Exit code: 0

**Artifacts produced:**

| File                 | Content                                               |
| -------------------- | ----------------------------------------------------- |
| `requirements.md`  | Traceability matrix with US-1, FR-1..FR-4, NFR-1      |
| `architecture.md`  | Component overview, data-flow, requirements addressed |
| `design-review.md` | Error handling, extensibility, testing checklist      |
| `impl-plan.md`     | Phased roadmap tied to FR/NFR IDs                     |
| `PR.md`            | PR title, summary, test plan, traceability footer     |

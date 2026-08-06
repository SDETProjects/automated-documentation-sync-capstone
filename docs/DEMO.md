# Demo: 8-Step Agentic SDLC Pipeline

This document walks a reviewer through a complete end-to-end demo of the Automated Documentation Sync capstone.

**Estimated time:** 15 minutes (A) + 5 minutes (B) = 20 minutes total

---

## Demo A: The Agentic Workflow (Copilot Chat)

**What you're demonstrating:** The human-driven SDLC using Copilot as a pair programmer.

**What the reviewer will see:** A conversation transcript where Copilot asks clarifying questions, designs architecture, conducts reviews, and verifies implementation. The *process* is the deliverable here.

### Setup (1 min)

1. Clone the repo
2. Open `.github/copilot-instructions.md` — shows the global contract loaded into every Copilot Chat
3. Open `.github/prompts/` — show the 8 step prompts (step-1 through step-8)
4. Explain: "Copilot loads these automatically; they guide the conversation"

### Run the orchestrator (10 min)

In VS Code Copilot Chat, type:

```
/run-pipeline EPMCDMETST-55568
```

Copilot will:
1. Fetch the story from `user-story.md`
2. Run step 1, ask clarifying questions
3. Generate `requirements.md`
4. Pause for human approval
5. Continue through steps 2–8, pausing at gates (steps 3, 6, 8)

**What to note for the reviewer:**
- Copilot asks questions about the story; you answer them
- The conversation *is* the evidence of the agentic workflow
- Gates are enforced (you must approve before proceeding)
- IDs are preserved across all artifacts
- The final artifacts link back to requirements

### Commit the outputs (1 min)

```bash
git add *.md
git commit -m "SDLC Pipeline: all 8 steps completed"
```

The pre-commit hook runs:

```bash
docsync-verify . --story user-story.md
```

Explains what it checks: structure, sections, traceability IDs.

**Evidence for the reviewer:** Git history shows artifacts were generated in order, with commit messages tying each to a step.

---

## Demo B: The Verification & CI (CLI)

**What you're demonstrating:** The tooling that enforces the pipeline — tests, coverage, artifact quality, release workflow.

**What the reviewer will see:** Deterministic gates that prevent bad artifacts and incomplete coverage from reaching prod.

### 1. Document quality verification (2 min)

```bash
docsync-verify . --story user-story.md
```

Output:
```
Document quality OK (8 artifacts checked + story parity).
```

Explains what it verified:
- All 8 artifacts present
- Required sections in each artifact
- Heading discipline (max level 2)
- Traceability IDs (US-1, FR-1..FR-n, NFR-1 present in all downstream artifacts)
- **Story parity:** `FR-1..FR-n` count matches the story's acceptance criteria exactly

### 2. Test suite & coverage (1 min)

```bash
pytest -q --cov=src/documentation_sync tests/
```

Output: `152 passed in 18s`, `85% coverage` (green, above 80% gate)

Explains:
- All tests pass (happy path + edge cases)
- Coverage is 85% (above the 80% gate)
- `doc_validator.py` is 99% covered (the new module from this capstone)

### 3. Show the workflows (1 min)

Open `.github/workflows/`:

- **tests.yml** — runs on every push/PR
  - Installs dependencies
  - Runs pytest with coverage gate
  - Runs `docsync-verify` as a separate gate
  - Two independent signals: coverage ≥80% AND doc quality pass

- **doc-sync.yml** — verifies no drift
  - Regenerates artifacts from the source story
  - Verifies they match committed artifacts (for steps 1-4)
  - Catches hand-edits that break traceability

- **release.yml** — triggered on tag push
  - Re-verifies everything (tests, coverage, doc quality, all 8 artifacts present)
  - Creates a GitHub Release with RELEASE-NOTES.md

### 4. Show the hook (30 sec)

```bash
git log --oneline -5
```

Show the recent commits. Each one passed:

```bash
cat .githooks/pre-commit | head -20
```

Explains: "This hook ran locally before each commit, catching artifact drift before it hit CI."

### 5. Map the story to code (1 min)

Show how a requirement flows through the codebase:

```bash
grep -n "US-1" *.md                  # Cited in all artifacts
grep -rn "FR-1" src/documentation_sync  # Addressed in code
```

**Evidence for the reviewer:** Requirement IDs are preserved end-to-end. A human can trace any feature request back to code, tests, and documentation.

---

## Reviewer Checklist

At the end of the demo, the reviewer verifies:

- [ ] Copilot Chat workflow is clear and runnable (`/run-pipeline`)
- [ ] 8 steps are all present, in order, with prompts in `.github/prompts/`
- [ ] All 8 artifacts are generated (steps 1-4 auto, steps 5-8 stub/authored)
- [ ] Requirement IDs (US-n, FR-n, NFR-n) are preserved across all artifacts
- [ ] Tests pass, coverage ≥80%, document quality checks pass
- [ ] Pre-commit hook enforces artifact quality
- [ ] Three CI workflows (tests, doc-sync, release) are configured
- [ ] RELEASE-NOTES.md and release.yml exist (not yet tagged)
- [ ] CLAUDE.md and operating-model.md explain the two-pipeline design
- [ ] README and docs are up-to-date

---

## Troubleshooting

**If `/run-pipeline` doesn't work:** Copilot doesn't recognize the prompt file. Confirm:
- Prompts are in `.github/prompts/`
- Each has YAML frontmatter with `mode: agent`

**If `docsync-verify` fails:** An artifact is missing a required section. Check:
- All 8 artifact files exist at repo root
- Heading structure is flat (max `##`, no `###`)
- Traceability IDs are cited in downstream artifacts

**If tests fail:** Something broke during the refactor. Run:
```bash
pytest -v tests/test_doc_validator.py tests/test_generator.py
```
to isolate the issue.

---

## Files Changed in This Capstone

| File | Change | Reason |
|---|---|---|
| `.github/prompts/` | Renamed 01-06 → step-1-6, added step-7-8, created orchestrator | 8-step visibility |
| `.github/prompts/run-pipeline.prompt.md` | New | Orchestrator entry point |
| `.github/copilot-instructions.md` | Updated | Reference 8 steps, not 6 |
| `src/documentation_sync/doc_validator.py` | Extended | Validate 8 artifacts, not 5 |
| `src/documentation_sync/generator.py` | Extended | Generate steps 5-8 stubs |
| `tests/test_doc_validator.py` | Extended | Test new validators |
| `tests/test_generator.py` | Extended | Test new generators |
| `CLAUDE.md` | Rewritten | Explain 8-step pipeline |
| `docs/copilot-operating-model.md` | Rewritten | Detail CLI limitation, two pipelines |
| `.github/copilot-instructions.md` | Updated | Reference 8 steps |
| `user-story.md` | New | Input file at root (START HERE) |
| `code-review.md`, `verification-report.md`, `CHANGELOG.md` | New | Steps 5-8 artifacts |
| `RELEASE-NOTES.md` | New | v1.0.0 release notes |
| `.github/workflows/release.yml` | New | Tag push → release |
| `.githooks/pre-commit` | Updated | Reference new artifact paths |

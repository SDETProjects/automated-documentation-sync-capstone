# Copilot Operating Model

How this repository uses GitHub Copilot, what Copilot cannot do, and the approved
workaround. Read alongside `.github/copilot-instructions.md`.

---

## 1. The constraint

GitHub Copilot has **no programmatic API callable from Python**. It runs as an IDE
extension driven by an interactive chat session. There is no `copilot -p "<prompt>"`
equivalent to Claude Code's headless mode.

This is visible in the code. `CopilotLLMAdapter.is_available()` in
`src/documentation_sync/providers.py` returns `False` unconditionally:

```python
def is_available(self) -> bool:
    return False
```

The adapter exists to keep the `--llm copilot` flag and the adapter pattern
demonstrable. **It is inert at runtime.** Passing `--llm copilot` causes `LLMManager`
to fall back to Claude (if configured) or to the offline heuristic generator.

## 2. The approved operating model

Copilot drives the *authoring* of SDLC artifacts. The CLI drives *generation and
verification*. They meet at the artifact files.

```
  YOU + Copilot Chat                    docsync CLI
  (.github/prompts/ 01-06)              (src/documentation_sync/)
          |                                    |
          |  authors & refines                 |  generates & verifies
          v                                    v
     +-----------------------------------------------+
     |  requirements.md  architecture.md              |
     |  design-review.md impl-plan.md  PR.md          |
     +-----------------------------------------------+
                          |
                          v
          .githooks/pre-commit  +  CI workflows
             (enforce structure & ID parity)
```

Division of labour:

| Concern | Owner |
|---|---|
| Clarifying questions, judgement, prose quality | Copilot Chat |
| Deterministic scaffolding from a Jira story | `docsync` |
| Structure + traceability enforcement | `docsync-verify` |

## 3. Running Pipeline A — Copilot Chat

This is how the capstone's 8 steps are actually performed.

**Setup (once):**

```bash
git config core.hooksPath .githooks
```

**Per phase**, in VS Code:

1. Open Copilot Chat (`Ctrl+Alt+I`).
2. Attach the phase prompt with `#file`, plus the prior artifact. For phase 1:

   ```
   #file:.github/prompts/01-requirements.prompt.md
   #file:samples/jira_story.json

   Generate requirements.md following the attached prompt.
   Ask me clarifying questions before writing anything.
   ```

3. Answer Copilot's questions. This dialogue *is* the deliverable for the capstone's
   "let Copilot ask or clarify questions" requirement.
4. Save the result to the artifact file.
5. Verify and commit:

   ```bash
   docsync-verify . --story samples/jira_story.json
   git add requirements.md && git commit -m "Phase 1: requirements"
   ```

Then repeat for `02-architecture` through `06-pr`, attaching the previous artifact each
time. `.github/copilot-instructions.md` is loaded automatically into every Chat turn —
you do not attach it.

Note: `.github/instructions/python.instructions.md` and `docs.instructions.md` are
path-scoped and apply automatically when Copilot touches matching files.

## 4. Running Pipeline B — the CLI

Independent of Copilot. Generates artifacts for *any* story.

```bash
docsync samples/jira_story.json -o out                        # local story
docsync "https://jiraeu.epam.com/browse/EPMCDMETST-57618" -o out   # live Jira
docsync samples/jira_story.json -o out --phased               # interactive gates
docsync-verify out --story samples/jira_story.json            # verify output
```

Live Jira requires a token:

```bash
export JIRA_API_TOKEN="your-personal-access-token"
```

`--llm copilot` is accepted but never dispatches to Copilot — see §1.

## 5. Verification

`docsync-verify` checks generated documents, which unit tests do not cover:

- required `##` sections per artifact type
- heading discipline (single `#` title first; nothing deeper than `##`)
- traceability — downstream artifacts cite only IDs that `requirements.md` defines
- story parity (`--story`) — `FR-n` count matches the story's acceptance criteria exactly

Parity checks **IDs, not prose**, which is what allows Copilot-refined wording to pass
while still catching a dropped or invented requirement.

| Gate | Command | Enforced by |
|---|---|---|
| Coverage >=80% | `pytest --cov-fail-under=80` | `tests.yml` |
| Document quality | `docsync-verify . --story samples/jira_story.json` | `tests.yml`, pre-commit |
| Story parity | same, with `--story` | `doc-sync.yml` |

Coverage and document quality are **separate gates** by design: a broken artifact
should not read as a coverage regression.

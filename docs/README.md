# Documentation

Explanatory and operating-model documentation for the Automated Documentation Sync project.

## Contents

| File | Purpose |
|------|---------|
| `copilot-operating-model.md` | How GitHub Copilot + CLI divide labor; running Pipeline A |
| `traceability/jira-story-template.md` | Expected Jira story structure for traceability |

## Cross-References

| If you're looking for... | Go to |
|--------------------------|-------|
| Project overview, CLI usage, installation | `../README.md` |
| GitHub Copilot workflow | `../.github/README.md` |
| Claude Code workflow | `../.claude/README.md` |
| Package API reference | `../src/documentation_sync/README.md` |
| Test organization | `../tests/README.md` |
| Frontend (ForecastChart) | `../src/frontend/README.md` |
| Sample story format | `../samples/README.md` |
| Forecast data format | `../data/README.md` |

## Contributing

Documentation changes should:
1. Reflect actual code behavior (not aspirational)
2. Cross-reference rather than duplicate
3. Include runnable examples
4. Note version-specific behavior where relevant
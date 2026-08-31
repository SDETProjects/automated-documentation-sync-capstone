#!/usr/bin/env python3
"""
Hook: trigger-doc-sync
Event: Stop (session end)
Purpose: Block session exit if src/ changed but docs not synced

This hook checks:
1. Did src/ or tests/ change in this session (via git diff)?
2. Was /doc-sync (or docsync CLI) run during this session?
3. If source changed but docs not synced, block exit and suggest running it

Allows exit if:
- src/ did not change since last commit
- A doc-sync was run in this session (tracked via marker file)
- SKIP_DOC_SYNC=1 is set in the environment (replaces the --force argv flag,
  which is unreachable when invoked as a Claude Code Stop hook)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Artifacts that doc-sync produces; if none exist in the repo root, we assume
# docs have not yet been generated for the current source state.
EXPECTED_DOC_ARTIFACTS = [
    "requirements.md",
    "architecture.md",
    "design-review.md",
    "impl-plan.md",
    "PR.md",
    "CHANGELOG.md",
    "verification-report.md",
]

# Marker written by /doc-sync skill after a successful run this session.
DOC_SYNC_MARKER = ".claude/.docsync-ran"


def _git_diff_names() -> set[str]:
    """Return set of file paths changed (staged + unstaged) vs HEAD."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except (subprocess.SubprocessError, OSError):
        return set()


def _source_changed(diff_names: set[str]) -> bool:
    """True if any src/ or tests/ file changed."""
    return any(
        name.startswith("src/") or name.startswith("tests/")
        for name in diff_names
    )


def _docs_changed(diff_names: set[str]) -> bool:
    """True if any documentation artifact changed this session."""
    return any(name in EXPECTED_DOC_ARTIFACTS for name in diff_names)


def _doc_sync_ran_this_session() -> bool:
    """True if /doc-sync was invoked this session (marker file present)."""
    return Path(DOC_SYNC_MARKER).exists()


def check_doc_sync_needed() -> bool:
    """Return True if doc-sync should be required before exit.

    Logic:
        - If SKIP_DOC_SYNC=1 env var is set: return False (allow exit).
        - If no source changes: return False (nothing to sync).
        - If doc-sync ran this session: return False (just synced).
        - If docs already changed alongside source: return False (synced by hand).
        - Otherwise: return True (block and require /doc-sync).

    To bypass from the terminal: export SKIP_DOC_SYNC=1
    """
    if os.environ.get("SKIP_DOC_SYNC") == "1":
        return False

    diff_names = _git_diff_names()
    if not diff_names:
        return False

    if not _source_changed(diff_names):
        return False

    if _doc_sync_ran_this_session():
        return False

    if _docs_changed(diff_names):
        return False

    return True


def main() -> int:
    if check_doc_sync_needed():
        print("⚠️  src/ or tests/ changed but documentation is not in sync.")
        print("")
        print("To sync documentation, run one of:")
        print("  1. claude  →  /doc-sync")
        print("  2. docsync <story-file-or-url> -o . --phased --non-interactive")
        print("  3. python -m documentation_sync.cli <story> -o . --phased")
        print("")
        print("Or skip this check:")
        print("  export SKIP_DOC_SYNC=1  (set before starting the session)")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

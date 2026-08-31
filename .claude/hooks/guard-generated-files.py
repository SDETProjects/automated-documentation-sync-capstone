#!/usr/bin/env python3
"""
Hook: guard-generated-files
Event: PreToolUse (Write, Edit)
Purpose: Protect .claude/ configuration files from accidental overwrites

Claude Code passes tool input as JSON on stdin. This hook reads that payload,
extracts the file path, and blocks writes to protected paths.

Decision output (stdout JSON):
  {"decision": "block", "reason": "..."}  — deny the tool call
  {"decision": "approve"}                 — allow the tool call

Protected (blocked):
  .claude/CLAUDE.md
  .claude/settings.json
  .claude/commands/*
  .claude/agents/*

Allowed even within .claude/:
  .claude/hooks/*
  .claude/skills/*
  .claude/projects/*  (memory system)
"""

import json
import sys
from pathlib import Path

PROTECTED_PATHS = [
    ".claude/CLAUDE.md",
    ".claude/settings.json",
    ".claude/commands/",
    ".claude/agents/",
]

ALLOWED_PATHS = [
    ".claude/hooks/",
    ".claude/skills/",
    ".claude/projects/",
]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _repository_relative_path(filepath: str) -> str:
    """Normalize a supplied path to a repository-relative POSIX path."""
    supplied_path = Path(filepath)
    resolved_path = (
        supplied_path.resolve()
        if supplied_path.is_absolute()
        else (REPOSITORY_ROOT / supplied_path).resolve()
    )
    try:
        return resolved_path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return ""


def is_protected(filepath: str) -> bool:
    """Return True if the filepath should be blocked."""
    filepath = _repository_relative_path(filepath)
    if not filepath:
        return False

    for protected in PROTECTED_PATHS:
        if filepath == protected or filepath.startswith(protected.rstrip("/") + "/"):
            for allowed in ALLOWED_PATHS:
                if filepath.startswith(allowed):
                    return False
            return True

    return False


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
        tool_input = payload.get("tool_input", {})
        # Write uses "file_path"; Edit uses "file_path" too
        filepath = tool_input.get("file_path", "")
    except (json.JSONDecodeError, AttributeError):
        print(json.dumps({"decision": "approve"}))
        return

    if not filepath:
        print(json.dumps({"decision": "approve"}))
        return

    if is_protected(filepath):
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"'{filepath}' is a protected configuration file. "
                "To modify .claude/ configuration use: claude /config"
            ),
        }))
    else:
        print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hook: guard-generated-files
Event: PreToolUse (Write, Edit)
Purpose: Protect .claude/ configuration files from accidental overwrites

This hook blocks writes to critical .claude/ files:
- .claude/CLAUDE.md (pipeline rules)
- .claude/settings.json (MCP server config)
- .claude/commands/* (user shouldn't edit these)
- .claude/agents/* (user shouldn't edit these)

Allows writes to:
- .claude/hooks/* (user can add custom hooks)
- .claude/skills/* (user can add custom skills)
- .claude/projects/*/memory/* (user memory system)
"""

import sys
import os

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

def is_protected(filepath: str) -> bool:
    """Check if filepath is protected. Return True if it should be blocked."""
    filepath = filepath.replace("\\", "/")  # Normalize to forward slashes

    for protected in PROTECTED_PATHS:
        if filepath == protected or filepath.startswith(protected.rstrip("/") + "/"):
            # Check if it's in an allowed override path
            for allowed in ALLOWED_PATHS:
                if filepath.startswith(allowed):
                    return False
            return True

    return False

if __name__ == "__main__":
    # Get the filepath from tool input
    # For simplicity, check sys.argv[1] if provided

    filepath = sys.argv[1] if len(sys.argv) > 1 else ""

    if not filepath:
        # No filepath provided, allow it
        sys.exit(0)

    if is_protected(filepath):
        # Protected file, block it
        print("ERROR: This file is protected from accidental edits.")
        print(f"File: {filepath}")
        print("\nIf you need to modify .claude/ configuration, use:")
        print("  claude /config")
        sys.exit(1)
    else:
        # Safe to write, allow it
        sys.exit(0)

#!/usr/bin/env python3
"""
Hook: trigger-doc-sync
Event: Stop (session end)
Purpose: Block session exit if src/ changed but docs not synced

This hook checks:
1. Did src/ or tests/ change in this session?
2. Was /doc-sync run during this session?
3. If src changed but /doc-sync was not run, block exit and suggest running it

Allows exit if:
- src/ did not change
- /doc-sync was already run
- User explicitly confirms they want to skip doc-sync
"""

import os
import sys

def check_doc_sync_needed():
    """
    Check if doc-sync is needed.
    Return True if it should be run before exit.
    """
    # This is a placeholder implementation.
    # In a real hook, this would:
    # 1. Check git diff to see if src/ changed
    # 2. Check session memory to see if /doc-sync was run
    # 3. Return True if sync is needed

    # For now, assume sync is needed if src/ exists
    if os.path.isdir("src"):
        # Could add more sophisticated logic here
        # e.g., check git diff --name-only for src/ changes
        return False  # For now, don't block (can enable later)

    return False

if __name__ == "__main__":
    if check_doc_sync_needed():
        print("⚠️  src/ has changed. Consider running /doc-sync to update documentation.")
        print("")
        print("Options:")
        print("  1. Run: claude")
        print("     > /doc-sync")
        print("")
        print("  2. Or, skip doc-sync and continue:")
        print("     [Confirm in chat to proceed without doc-sync]")
        print("")
        sys.exit(1)
    else:
        sys.exit(0)

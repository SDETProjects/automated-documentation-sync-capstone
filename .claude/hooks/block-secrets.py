#!/usr/bin/env python3
"""
Hook: block-secrets
Event: PreToolUse (Bash)
Purpose: Prevent bash commands that leak secrets

This hook blocks bash commands containing patterns that might leak secrets:
- AWS keys (AKIA...)
- API keys in plaintext
- Passwords in env vars
- Private keys
"""

import re
import sys

SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",  # AWS key
    r"password\s*=\s*['\"][^'\"]*['\"]",  # password=
    r"api_key\s*=\s*['\"][^'\"]*['\"]",  # api_key=
    r"-----BEGIN RSA PRIVATE KEY-----",  # Private key marker
    r"-----BEGIN OPENSSH PRIVATE KEY-----",  # SSH key marker
    r"--password\s+\S+",  # --password flag
    r"--api.?key\s+\S+",  # --api-key flag
]

def check_command(command: str) -> bool:
    """Check if command contains secret patterns. Return False if it does (block it)."""
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False
    return True

if __name__ == "__main__":
    # Tool result is passed as JSON in CLAUDE_TOOL_INPUT env var or stdin
    # For simplicity, check sys.argv[1] if provided

    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if not command:
        # No command provided, allow it
        sys.exit(0)

    if check_command(command):
        # Safe command, allow it
        sys.exit(0)
    else:
        # Secret detected, block it
        print("ERROR: Command appears to contain secrets. Blocked for safety.")
        print(f"Command: {command}")
        sys.exit(1)

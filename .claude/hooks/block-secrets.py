#!/usr/bin/env python3
"""
Hook: block-secrets
Event: PreToolUse (Bash)
Purpose: Prevent bash commands that leak secrets

Claude Code passes tool input as JSON on stdin. This hook reads that payload,
extracts the command string, and blocks execution if secret patterns are found.

Decision output (stdout JSON):
  {"decision": "block", "reason": "..."}  — deny the tool call
  {"decision": "approve"}                 — allow the tool call
"""

import json
import re
import sys

SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",                    # AWS access key
    r"password\s*=\s*['\"][^'\"]*['\"]",    # password=
    r"api_key\s*=\s*['\"][^'\"]*['\"]",     # api_key=
    r"-----BEGIN RSA PRIVATE KEY-----",      # RSA private key
    r"-----BEGIN OPENSSH PRIVATE KEY-----",  # SSH private key
    r"--password\s+\S+",                     # --password flag
    r"--api[-_]key\s+\S+",                  # --api-key / --api_key flag
]


def check_command(command: str) -> tuple[bool, str]:
    """Return (is_safe, reason). is_safe=False means block."""
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command matches secret pattern: {pattern}"
    return True, ""


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
        command = payload.get("tool_input", {}).get("command", "")
    except (json.JSONDecodeError, AttributeError):
        # If we can't parse the payload, allow the call — don't block on our own error
        print(json.dumps({"decision": "approve"}))
        return

    if not command:
        print(json.dumps({"decision": "approve"}))
        return

    is_safe, reason = check_command(command)
    if is_safe:
        print(json.dumps({"decision": "approve"}))
    else:
        print(json.dumps({"decision": "block", "reason": f"Secret detected — {reason}"}))


if __name__ == "__main__":
    main()

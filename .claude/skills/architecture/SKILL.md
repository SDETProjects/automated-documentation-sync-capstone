---
name: architecture
description: Design system components and data flow. Invokes software-architect agent to produce claude-architecture.md from approved requirements.
---

# Architecture Design Skill

1. Verify `claude-requirements.md` exists; abort with a message if missing.
2. Dispatch `Agent(subagent_type="software-architect", prompt="Design architecture from claude-requirements.md and write claude-architecture.md")`.
3. Confirm `claude-architecture.md` covers every FR and NFR with a traceability note.
4. Surface any open design decisions to the user before proceeding to `/design-review`.

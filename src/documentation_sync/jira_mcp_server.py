"""MCP server exposing docsync SDLC pipeline tools for Jira integration.

Exposes four tools to Claude Code:
  - fetch_jira_story     : fetch + parse a Jira issue into structured fields
  - run_sdlc_pipeline    : run the full 8-phase SDLC pipeline for a story
  - get_artifact_status  : check which phase artifacts exist in an output dir
  - validate_jira_url    : validate a URL points to a Jira issue
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Tool logic — plain functions, no MCP dependency, fully testable.
# ---------------------------------------------------------------------------

def _tool_fetch_jira_story(url: str, jira_token: str | None = None) -> Dict[str, Any]:
    """Fetch and parse a Jira issue URL into structured story fields."""
    from .jira_connector import fetch_issue_raw, JiraConnectorError
    from .input_handler import _issue_key_to_url, _looks_like_issue_key
    from .input_handler import _story_from_raw_json

    if not url.startswith("http"):
        if _looks_like_issue_key(url):
            try:
                url = _issue_key_to_url(url, jira_base_url=os.environ.get("JIRA_BASE_URL"))
            except Exception as exc:  # noqa: BLE001
                return {"error": str(exc)}
        else:
            return {
                "error": (
                    f"Provide a Jira issue key (e.g. PROJ-123) or full Jira URL "
                    f"(e.g. https://jira.host/browse/{url})."
                )
            }

    token = jira_token or os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")
    if not token:
        return {
            "error": (
                "No Jira API token found. Set the JIRA_API_TOKEN environment variable "
                "or pass jira_token to this tool."
            )
        }

    try:
        raw = fetch_issue_raw(url, api_token=token)
        story = _story_from_raw_json(raw)
        return {
            "key": story.key,
            "summary": story.summary,
            "description": story.description,
            "acceptance_criteria": story.acceptance_criteria,
            "labels": story.labels or [],
            "priority": story.priority,
            "story_points": story.story_points,
            "reporter": story.reporter,
            "assignee": story.assignee,
        }
    except JiraConnectorError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Unexpected error fetching story: {exc}"}


def _tool_run_sdlc_pipeline(
    jira_url: str,
    output_dir: str = ".",
    non_interactive: bool = True,
) -> Dict[str, Any]:
    """Run the full 8-phase SDLC pipeline for a Jira story URL."""
    from .cli import run

    token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")
    exit_code = run(
        story_input=jira_url,
        output_dir=output_dir,
        jira_token=token,
        phased=True,
        non_interactive=non_interactive,
    )

    if exit_code == 0:
        _ARTIFACT_NAMES = {
            "requirements.md", "architecture.md",
            "design-review.md", "impl-plan.md", "PR.md",
        }
        out = Path(output_dir)
        artifacts = sorted(
            f.name for f in out.glob("*.md") if f.name in _ARTIFACT_NAMES
        )
        return {
            "status": "success",
            "output_dir": str(out.resolve()),
            "artifacts_generated": artifacts,
            "phases_completed": len(artifacts),
        }

    return {"status": "error", "exit_code": exit_code, "output_dir": output_dir}


def _tool_get_artifact_status(output_dir: str = ".") -> Dict[str, Any]:
    """Check which SDLC phase artifacts exist in output_dir."""
    _PHASES = [
        ("Phase 1 — Requirements",       "requirements.md"),
        ("Phase 2 — Architecture",        "architecture.md"),
        ("Phase 3 — Design Review",       "design-review.md"),
        ("Phase 4 — Implementation Plan", "impl-plan.md"),
        ("Phase 7 — PR",                  "PR.md"),
    ]
    out = Path(output_dir)
    details: Dict[str, Any] = {}
    for phase_name, filename in _PHASES:
        path = out / filename
        details[phase_name] = {
            "artifact": filename,
            "exists": path.exists(),
            "path": str(path.resolve()) if path.exists() else None,
        }

    completed = sum(1 for v in details.values() if v["exists"])
    return {
        "output_dir": str(out.resolve()) if out.exists() else str(out),
        "phases_completed": completed,
        "total_phases": len(_PHASES),
        "details": details,
    }


def _tool_validate_jira_url(url: str) -> Dict[str, Any]:
    """Validate whether a URL points to a Jira issue and extract its key."""
    from .jira_connector import validate_jira_url, extract_issue_key

    is_valid = validate_jira_url(url)
    issue_key = extract_issue_key(url) if is_valid else None
    return {
        "valid": is_valid,
        "issue_key": issue_key,
        "url": url,
    }


# ---------------------------------------------------------------------------
# MCP server wiring — wraps the functions above as registered tools.
# ---------------------------------------------------------------------------

def create_server():
    """Build and return the MCPServer instance (importable for testing)."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:
        raise ImportError(
            "The 'mcp' package is required to run the MCP server. "
            "Install with: pip install mcp"
        ) from exc

    mcp = MCPServer(
        name="docsync-jira",
        description=(
            "SDLC pipeline tools: fetch Jira stories, run the 8-phase docsync "
            "pipeline, and check artifact status."
        ),
    )

    @mcp.tool(
        description=(
            "Fetch a Jira issue by URL and return its structured fields: key, summary, "
            "description, acceptance criteria, labels, priority, story points. "
            "Requires JIRA_API_TOKEN environment variable or explicit jira_token."
        )
    )
    def fetch_jira_story(url: str, jira_token: str = "") -> str:
        result = _tool_fetch_jira_story(url, jira_token or None)
        return json.dumps(result, indent=2)

    @mcp.tool(
        description=(
            "Run the full 8-phase SDLC documentation pipeline for a Jira story URL. "
            "Generates requirements.md, architecture.md, design-review.md, impl-plan.md, "
            "and PR.md into output_dir. Set non_interactive=true for CI/auto-approve mode."
        )
    )
    def run_sdlc_pipeline(
        jira_url: str,
        output_dir: str = ".",
        non_interactive: bool = True,
    ) -> str:
        result = _tool_run_sdlc_pipeline(jira_url, output_dir, non_interactive)
        return json.dumps(result, indent=2)

    @mcp.tool(
        description=(
            "Check which SDLC phase artifacts have been generated in output_dir. "
            "Returns per-phase status (exists/missing) and a count of completed phases."
        )
    )
    def get_artifact_status(output_dir: str = ".") -> str:
        result = _tool_get_artifact_status(output_dir)
        return json.dumps(result, indent=2)

    @mcp.tool(
        description=(
            "Validate whether a URL points to a Jira issue. "
            "Returns {valid, issue_key, url}."
        )
    )
    def validate_jira_url(url: str) -> str:
        result = _tool_validate_jira_url(url)
        return json.dumps(result, indent=2)

    return mcp


if __name__ == "__main__":
    server = create_server()
    asyncio.run(server.run_stdio_async())

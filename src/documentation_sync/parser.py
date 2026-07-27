"""Parsing utilities for Jira-style story inputs (JSON or Markdown)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .models import JiraStory

REQUIRED_FIELDS = ("key", "summary", "description")


class StoryParseError(Exception):
    """Raised when a story input file cannot be parsed into a JiraStory."""


class StoryNotFoundError(Exception):
    """Raised when the requested story input file does not exist."""


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StoryParseError(f"Invalid JSON in {path}: {exc}") from exc


def _read_markdown(path: Path) -> Dict[str, Any]:
    """Very small Markdown convention:

    # <key>: <summary>
    ## Description
    <free text>
    ## Acceptance Criteria
    - item
    - item
    """
    text = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.splitlines()]

    data: Dict[str, Any] = {"acceptance_criteria": []}
    section = None
    description_lines = []

    for line in lines:
        if line.startswith("# "):
            header = line[2:].strip()
            if ":" in header:
                key, summary = header.split(":", 1)
                data["key"] = key.strip()
                data["summary"] = summary.strip()
            else:
                data["summary"] = header
        elif line.lower().startswith("## description"):
            section = "description"
        elif line.lower().startswith("## acceptance criteria"):
            section = "acceptance_criteria"
        elif line.startswith("- ") and section == "acceptance_criteria":
            data["acceptance_criteria"].append(line[2:].strip())
        elif section == "description" and line.strip():
            description_lines.append(line.strip())

    data["description"] = " ".join(description_lines).strip()
    return data


def load_story(path: str | Path) -> JiraStory:
    """Load a Jira-style story from a JSON or Markdown file.

    Raises:
        StoryNotFoundError: if the file does not exist.
        StoryParseError: if required fields are missing or content is invalid.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise StoryNotFoundError(f"Story input file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".json":
        data = _read_json(file_path)
    elif suffix in (".md", ".markdown"):
        data = _read_markdown(file_path)
    else:
        raise StoryParseError(f"Unsupported story file type: {suffix}")

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        raise StoryParseError(
            f"Story input {file_path} is missing required fields: {', '.join(missing)}"
        )

    return JiraStory(
        key=data["key"],
        summary=data["summary"],
        description=data["description"],
        acceptance_criteria=list(data.get("acceptance_criteria", [])),
        labels=list(data.get("labels", [])),
        priority=data.get("priority"),
        story_points=data.get("story_points"),
        reporter=data.get("reporter"),
        assignee=data.get("assignee"),
    )

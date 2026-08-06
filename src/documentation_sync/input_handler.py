"""Input layer: detect and load a Jira/Confluence story from file, URL, or raw text."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .models import JiraStory
from .parser import StoryParseError, load_story

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
ISSUE_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
REPO_CONFIG_FILENAME = "docsync.config.json"


class IntegrationUnavailableError(Exception):
    """Raised when a Jira/Confluence URL cannot be fetched automatically.

    Callers should catch this and fall back to asking the user to paste the
    story text manually; this pipeline never blocks on a missing integration.
    """


def detect_input_type(input_str: str) -> str:
    """Classify a CLI input string as "file", "url", or "text".

    - "url": starts with http:// or https://
    - "file": path has a known story file extension (.json/.md/.markdown),
              OR the path exists on disk (handles extension-less paths)
    - "text": anything else (raw pasted story content)
    """
    candidate = input_str.strip()
    if URL_PATTERN.match(candidate):
        return "url"
    p = Path(candidate)
    if p.suffix.lower() in (".json", ".md", ".markdown") or p.exists():
        return "file"
    return "text"


def _looks_like_jira(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "atlassian.net" in host or "jira" in host


def _looks_like_confluence(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "confluence" in host or "wiki" in host


def _to_jira_rest_url(url: str) -> str:
    """Convert a Jira browse URL to its REST API equivalent.

    Delegates to jira_connector.to_rest_url so the conversion lives in one place.
    """
    from .jira_connector import to_rest_url

    return to_rest_url(url)


def _looks_like_issue_key(value: str) -> bool:
    """Return True when value is a bare Jira issue key (for example PROJ-123)."""
    return bool(ISSUE_KEY_PATTERN.match(value.strip()))


def _read_repo_jira_base_url() -> Optional[str]:
    """Read Jira base URL from a repository config file if present.

    The expected file is `docsync.config.json` and can define either:
      - {"jira_base_url": "https://jira.company.com"}
      - {"jira": {"base_url": "https://jira.company.com"}}
    """
    start = Path.cwd().resolve()
    for directory in [start, *start.parents]:
        config_path = directory / REPO_CONFIG_FILENAME
        if not config_path.exists():
            continue

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise IntegrationUnavailableError(
                f"Invalid JSON in {config_path}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise IntegrationUnavailableError(
                f"Invalid config format in {config_path}: expected a JSON object"
            )

        root_value = data.get("jira_base_url")
        if isinstance(root_value, str) and root_value.strip():
            return root_value.strip()

        jira_section = data.get("jira")
        if isinstance(jira_section, dict):
            nested_value = jira_section.get("base_url")
            if isinstance(nested_value, str) and nested_value.strip():
                return nested_value.strip()

        return None

    return None


def _issue_key_to_url(issue_key: str, jira_base_url: Optional[str]) -> str:
    """Resolve a Jira issue key into a browse URL using jira_base_url.

    jira_base_url can be provided by caller configuration or environment.
    """
    import os

    base = (
        jira_base_url
        or os.environ.get("JIRA_BASE_URL")
        or _read_repo_jira_base_url()
        or ""
    ).strip()
    if not base:
        raise IntegrationUnavailableError(
            "Received a Jira issue key but no Jira base URL is configured. Set JIRA_BASE_URL, "
            "or create docsync.config.json with jira_base_url, or pass a full Jira URL."
        )

    base = base.rstrip("/")
    if not URL_PATTERN.match(base):
        raise IntegrationUnavailableError(
            f"Configured JIRA_BASE_URL '{base}' is invalid. Use an absolute URL like https://jira.company.com"
        )
    return f"{base}/browse/{issue_key.strip()}"


def fetch_from_url(url: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
    """Attempt to fetch story data from a Jira or Confluence REST API.

    Accepts both browser URLs (/browse/PROJ-123) and REST API URLs; browser
    URLs are converted to the REST endpoint automatically.

    Requires the `requests` package and a valid `auth_token` (Jira/Confluence
    personal access token). If the integration is not configured (no token,
    network/auth failure, unsupported host), raises IntegrationUnavailableError
    so the caller can fall back to asking the user to paste the story manually.
    """
    import os
    from .jira_connector import fetch_issue_raw, JiraConnectorError

    # Try provided token, then environment variables
    token = auth_token or os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")

    if not token:
        raise IntegrationUnavailableError(
            "No Jira/Confluence auth token configured. Set via:\n"
            "  --jira-token <token>\n"
            "  JIRA_API_TOKEN environment variable\n"
            "  JIRA_TOKEN environment variable\n"
            "Or paste the story text manually."
        )

    try:
        import requests
    except ImportError as exc:
        raise IntegrationUnavailableError(
            "The 'requests' package is not installed; cannot fetch from "
            "Jira/Confluence automatically. Run: pip install requests"
        ) from exc

    if not (_looks_like_jira(url) or _looks_like_confluence(url)):
        raise IntegrationUnavailableError(
            f"URL '{url}' does not look like a Jira or Confluence host. "
            "Please paste the story text manually."
        )

    try:
        return fetch_issue_raw(url, api_token=token)
    except JiraConnectorError as exc:
        raise IntegrationUnavailableError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - any network/auth failure triggers fallback
        raise IntegrationUnavailableError(
            f"Could not fetch story from '{url}': {exc}. "
            "Please paste the story text manually."
        ) from exc


_AC_CUSTOM_FIELDS = [
    "acceptance_criteria",    # local/sample JSON convention
    "customfield_10014",      # common EPAM/Atlassian AC field
    "customfield_10034",      # alternate AC field
    "customfield_10500",      # another common variant
]

_SP_CUSTOM_FIELDS = [
    "story_points",
    "customfield_10016",      # Story Points (most common)
    "customfield_10028",      # alternate story-points field
]


def _extract_ac_from_description(description: str) -> List[str]:
    """Parse acceptance criteria items from a description that embeds them
    as a section (e.g., '\\nAcceptance Criteria\\n1. Given ...').
    """
    criteria: List[str] = []
    in_ac = False
    for line in description.splitlines():
        low = line.lower().strip()
        if re.match(r"acceptance\s+criteria", low):
            in_ac = True
            continue
        if in_ac:
            if re.match(r"(notes?|context|background|references?|scenario)\b", low):
                break
            item = re.match(r"^(\d+[\.\)]\s*|-\s*|\*\s*)(.*)", line.strip())
            if item:
                criteria.append(item.group(2).strip())
            elif low.startswith("given "):
                criteria.append(line.strip())
    return criteria


def _story_from_raw_json(data: Dict[str, Any]) -> JiraStory:
    """Build a JiraStory from a raw Jira REST API or sample JSON payload.

    Acceptance criteria are looked up across known custom fields first; if
    none are found the description field is scanned for an embedded AC section.
    """
    fields = data.get("fields", data)

    description = fields.get("description") or ""
    # Jira REST v2 returns description as Atlassian Document Format (dict) for
    # cloud instances; extract plain text if that is the case.
    if isinstance(description, dict):
        description = _flatten_adf(description)

    # Acceptance criteria: try custom fields, then parse from description.
    ac: List[str] = []
    for cf in _AC_CUSTOM_FIELDS:
        raw = fields.get(cf)
        if raw:
            if isinstance(raw, list):
                ac = [str(item).strip() for item in raw if item]
            elif isinstance(raw, str):
                ac = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            break
    if not ac and description:
        ac = _extract_ac_from_description(description)

    # Story points: try custom fields.
    story_points = None
    for sp_cf in _SP_CUSTOM_FIELDS:
        val = fields.get(sp_cf)
        if val is not None:
            try:
                story_points = int(val)
            except (TypeError, ValueError):
                pass
            break

    # Priority and assignee may be dicts in the Jira REST response.
    priority_raw = fields.get("priority")
    priority = priority_raw.get("name") if isinstance(priority_raw, dict) else priority_raw

    reporter_raw = fields.get("reporter")
    reporter = (
        reporter_raw.get("emailAddress") or reporter_raw.get("displayName")
        if isinstance(reporter_raw, dict) else reporter_raw
    )

    assignee_raw = fields.get("assignee")
    assignee = (
        assignee_raw.get("emailAddress") or assignee_raw.get("displayName")
        if isinstance(assignee_raw, dict) else assignee_raw
    )

    labels_raw = fields.get("labels", [])
    labels = [
        (lbl.get("name") if isinstance(lbl, dict) else lbl)
        for lbl in labels_raw
    ]

    return JiraStory(
        key=data.get("key", fields.get("key", "UNKNOWN-0")),
        summary=fields.get("summary", ""),
        description=description,
        acceptance_criteria=ac,
        labels=labels,
        priority=priority,
        story_points=story_points,
        reporter=reporter,
        assignee=assignee,
    )


def _flatten_adf(node: Any, sep: str = "\n") -> str:
    """Recursively extract plain text from an Atlassian Document Format node."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        text = node.get("text", "")
        children = node.get("content", [])
        parts = ([text] if text else []) + [_flatten_adf(c) for c in children]
        return sep.join(p for p in parts if p)
    if isinstance(node, list):
        return sep.join(_flatten_adf(item) for item in node if item)
    return ""


def _normalize_freetext(text: str) -> str:
    """Insert newlines at logical boundaries so single-line pastes parse correctly.

    Handles the common case where text is copied from a browser or chat
    tool and arrives as one long line with no newlines.
    """
    # Insert newline before numbered list items (1. / 2. / etc.)
    text = re.sub(r"(?<!\n)(\d+\.\s+)", r"\n\1", text)
    # Insert newline before recognisable section headers
    text = re.sub(
        r"(?<!\n)(Acceptance\s+Criteria|Notes?|Context\s*Repo|Background|References?)",
        r"\n\1\n",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _extract_freetext_story(text: str) -> JiraStory:
    """Best-effort extraction of story fields from free-form pasted text.

    Handles natural language story descriptions that don't follow the
    structured JSON or Markdown conventions. Extracts:
      - key: first JIRA-style token (WORD-NNN) found, else "MANUAL-001"
      - summary: first "I want to ..." clause, or the first sentence
      - description: full pasted text
      - acceptance_criteria: numbered/bulleted items under a criteria section
    """
    text = _normalize_freetext(text)
    lines = [l.rstrip() for l in text.splitlines()]

    # Key: look for JIRA-style token anywhere in text
    key_match = re.search(r"\b([A-Z][A-Z0-9]+-\d+)\b", text)
    key = key_match.group(1) if key_match else "MANUAL-001"

    # Summary: prefer "I want to ..." clause, else first non-empty line
    want_match = re.search(r"I want to ([^,\.]+)", text, re.IGNORECASE)
    if want_match:
        summary = want_match.group(0).strip().rstrip(".")
    else:
        summary = next((l.strip() for l in lines if l.strip()), text[:120].strip())

    # Acceptance criteria: collect numbered or bulleted items after a
    # "Acceptance Criteria" or "Given/When/Then" section header
    criteria: list[str] = []
    in_criteria = False
    for line in lines:
        low = line.lower().strip()
        if re.match(r"acceptance criteria|given.+when.+then", low):
            in_criteria = True
            continue
        if in_criteria:
            # Stop collecting at the next section header (Notes, Context, etc.)
            if re.match(r"(notes?|context|background|references?)\b", low):
                in_criteria = False
                continue
            item_match = re.match(r"^(\d+[\.\)]\s*|-\s*|\*\s*)(.*)", line.strip())
            if item_match:
                criteria.append(item_match.group(2).strip())
            elif low.startswith("given "):
                criteria.append(line.strip())

    return JiraStory(
        key=key,
        summary=summary,
        description=text.strip(),
        acceptance_criteria=criteria,
    )


def _story_from_text(text: str) -> JiraStory:
    """Parse a raw pasted story: try the structured Markdown convention first,
    then fall back to free-form extraction so natural language pastes work too.
    """
    from .parser import _read_markdown  # local import to avoid circular typing noise
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)

    try:
        data = _read_markdown(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    missing = [f for f in ("key", "summary", "description") if not data.get(f)]
    if not missing:
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

    # Markdown parse missing required fields — try free-form extraction instead.
    return _extract_freetext_story(text)


def load_story_from_any_source(
    input_str: str, auth_config: Optional[Dict[str, str]] = None
) -> JiraStory:
    """Route a CLI input string to the file loader, URL fetcher, or text parser.

    auth_config may contain {"jira_token": "..."} for URL ingestion. If URL
    ingestion fails for any reason, IntegrationUnavailableError propagates to
    the caller (cli.py), which should prompt the user to paste the story
    manually rather than crashing.
    """
    auth_config = auth_config or {}
    input_type = detect_input_type(input_str)

    if input_type == "file":
        return load_story(input_str)

    if input_type == "url":
        raw = fetch_from_url(input_str, auth_token=auth_config.get("jira_token"))
        return _story_from_raw_json(raw)

    stripped = input_str.strip()

    # Bare Jira issue key support (for example EPMCDMETST-55568): resolve to URL,
    # then reuse the URL fetch + parse flow.
    if _looks_like_issue_key(stripped):
        issue_url = _issue_key_to_url(
            stripped,
            jira_base_url=auth_config.get("jira_base_url"),
        )
        raw = fetch_from_url(issue_url, auth_token=auth_config.get("jira_token"))
        return _story_from_raw_json(raw)

    # "text": try JSON first, then fall back to the Markdown convention.
    if stripped.startswith("{"):
        try:
            return _story_from_raw_json(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise StoryParseError(f"Pasted text looks like JSON but failed to parse: {exc}") from exc

    return _story_from_text(stripped)

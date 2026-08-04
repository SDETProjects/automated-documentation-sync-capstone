"""Jira integration utilities: token management and direct issue fetching."""
from __future__ import annotations

import base64
import os
import re
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None


class JiraConnectorError(Exception):
    """Raised when Jira operations fail."""


def get_api_token_from_env() -> Optional[str]:
    """Retrieve Jira API token from environment variables.

    Checks multiple common conventions:
    - JIRA_API_TOKEN (CLI convention)
    - JIRA_TOKEN (shorter form)
    - ATLASSIAN_TOKEN (platform-wide)
    """
    return (
        os.environ.get("JIRA_API_TOKEN")
        or os.environ.get("JIRA_TOKEN")
        or os.environ.get("ATLASSIAN_TOKEN")
    )


def detect_jira_host(url: str) -> str:
    """Extract the Jira host from a URL.

    Examples:
        https://jiraeu.epam.com/browse/PROJ-123  →  https://jiraeu.epam.com
        https://mycompany.atlassian.net/browse/P-1  →  https://mycompany.atlassian.net
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def build_auth_headers(jira_url: str, token: str, email: Optional[str] = None) -> dict:
    """Build the correct Authorization header for the target Jira deployment.

    Jira Cloud (*.atlassian.net) requires HTTP Basic with `email:api_token`.
    Jira Server/Data Center (e.g. jiraeu.epam.com) uses a Bearer PAT.
    """
    headers = {"Accept": "application/json"}
    host = urlparse(jira_url).netloc.lower()

    if "atlassian.net" in host:
        account_email = email or os.environ.get("JIRA_EMAIL")
        if not account_email:
            raise JiraConnectorError(
                "Jira Cloud requires an account email alongside the API token. "
                "Set JIRA_EMAIL or pass email=..."
            )
        basic = base64.b64encode(f"{account_email}:{token}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    else:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def to_rest_url(jira_url: str) -> str:
    """Convert a /browse/KEY URL to its REST API equivalent.

    Already-REST URLs are returned unchanged.
    """
    parsed = urlparse(jira_url)
    browse_match = re.match(r"^/browse/([^/?#]+)", parsed.path)
    if not browse_match:
        return jira_url
    issue_key = browse_match.group(1)
    return f"{detect_jira_host(jira_url)}/rest/api/2/issue/{issue_key}"


def fetch_issue_raw(
    jira_url: str, api_token: Optional[str] = None, email: Optional[str] = None
) -> dict:
    """Fetch a raw Jira issue from a browser or API URL.

    Handles both /browse/KEY and /rest/api/2/issue/KEY URLs.
    Falls back to environment token if not provided.

    Args:
        jira_url: Browser URL (/browse/PROJ-123) or REST URL
        api_token: Personal access token. If None, tries environment.
        email: Atlassian account email, required for Jira Cloud Basic auth.

    Returns:
        The raw Jira REST response (dict).

    Raises:
        JiraConnectorError: If the fetch fails.
    """
    if not requests:
        raise JiraConnectorError(
            "Jira integration requires 'requests' package. "
            "Install with: pip install requests"
        )

    token = api_token or get_api_token_from_env()
    if not token:
        raise JiraConnectorError(
            "No Jira API token provided. Set via --jira-token, "
            "JIRA_API_TOKEN, or JIRA_TOKEN environment variable."
        )

    rest_url = to_rest_url(jira_url)
    headers = build_auth_headers(jira_url, token, email)

    try:
        response = requests.get(rest_url, headers=headers, timeout=10)
    except requests.Timeout as exc:
        raise JiraConnectorError(f"Jira request timed out: {rest_url}") from exc
    except requests.RequestException as exc:
        raise JiraConnectorError(f"Could not reach Jira at {rest_url}: {exc}") from exc

    if response.status_code in (401, 403):
        raise JiraConnectorError(
            f"Jira authentication failed (HTTP {response.status_code}). "
            "Verify your API token is valid and has access to this issue."
        )
    if response.status_code == 404:
        raise JiraConnectorError(f"Jira issue not found: {rest_url}")
    if not response.ok:
        raise JiraConnectorError(
            f"Jira returned HTTP {response.status_code} for {rest_url}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise JiraConnectorError(
            f"Jira returned a non-JSON response for {rest_url} "
            "(this often means an SSO/login page was served instead)."
        ) from exc


def validate_jira_url(url: str) -> bool:
    """Check if a URL looks like a valid Jira instance."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    return (
        ("atlassian.net" in host or "jira" in host)
        and ("/browse/" in path or "/rest/api" in path)
    )


def extract_issue_key(url: str) -> Optional[str]:
    """Extract the issue key from a Jira URL.

    Examples:
        https://jiraeu.epam.com/browse/EPMCDMETST-55568  →  EPMCDMETST-55568
        https://jira.company.com/rest/api/2/issue/PROJ-123  →  PROJ-123
    """
    # Try /browse/ pattern first
    browse_match = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", url)
    if browse_match:
        return browse_match.group(1)

    # Try /rest/api path pattern
    rest_match = re.search(r"/issue/([A-Z][A-Z0-9]+-\d+)", url)
    if rest_match:
        return rest_match.group(1)

    return None

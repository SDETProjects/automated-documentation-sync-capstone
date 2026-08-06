"""Tests for Jira connector utilities."""
import base64

import pytest
from unittest.mock import patch, MagicMock

from documentation_sync.jira_connector import (
    get_api_token_from_env,
    detect_jira_host,
    extract_issue_key,
    validate_jira_url,
    fetch_issue_raw,
    build_auth_headers,
    to_rest_url,
    JiraConnectorError,
)


class TestGetApiTokenFromEnv:
    """Test environment variable resolution."""

    def test_prefers_jira_api_token(self, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "token1")
        monkeypatch.setenv("JIRA_TOKEN", "token2")
        assert get_api_token_from_env() == "token1"

    def test_falls_back_to_jira_token(self, monkeypatch):
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.setenv("JIRA_TOKEN", "token2")
        assert get_api_token_from_env() == "token2"

    def test_falls_back_to_atlassian_token(self, monkeypatch):
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)
        monkeypatch.setenv("ATLASSIAN_TOKEN", "token3")
        assert get_api_token_from_env() == "token3"

    def test_returns_none_when_no_token(self, monkeypatch):
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)
        monkeypatch.delenv("ATLASSIAN_TOKEN", raising=False)
        assert get_api_token_from_env() is None


class TestDetectJiraHost:
    """Test host detection."""

    def test_extract_from_browse_url(self):
        url = "https://jiraeu.epam.com/browse/PROJ-123"
        assert detect_jira_host(url) == "https://jiraeu.epam.com"

    def test_extract_from_atlassian_cloud(self):
        url = "https://mycompany.atlassian.net/browse/KEY-999"
        assert detect_jira_host(url) == "https://mycompany.atlassian.net"

    def test_extract_from_rest_url(self):
        url = "https://jira.internal.com/rest/api/2/issue/BUG-42"
        assert detect_jira_host(url) == "https://jira.internal.com"


class TestExtractIssueKey:
    """Test issue key extraction."""

    def test_extract_from_browse_url(self):
        url = "https://jiraeu.epam.com/browse/EPMCDMETST-55568"
        assert extract_issue_key(url) == "EPMCDMETST-55568"

    def test_extract_from_rest_url(self):
        url = "https://jira.company.com/rest/api/2/issue/PROJ-123"
        assert extract_issue_key(url) == "PROJ-123"

    def test_returns_none_for_invalid_url(self):
        url = "https://example.com/something"
        assert extract_issue_key(url) is None


class TestValidateJiraUrl:
    """Test Jira URL validation."""

    def test_valid_browse_url(self):
        assert validate_jira_url("https://jiraeu.epam.com/browse/PROJ-123")

    def test_valid_atlassian_cloud_url(self):
        assert validate_jira_url("https://company.atlassian.net/browse/KEY-999")

    def test_valid_rest_url(self):
        assert validate_jira_url("https://jira.internal.com/rest/api/2/issue/BUG-1")

    def test_invalid_host(self):
        assert not validate_jira_url("https://example.com/browse/PROJ-123")

    def test_invalid_path(self):
        assert not validate_jira_url("https://jira.company.com/issues/PROJ-123")


class TestFetchIssueRaw:
    """Test Jira API fetching."""

    @patch("documentation_sync.jira_connector.requests")
    def test_successful_fetch(self, mock_requests, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "PROJ-123", "fields": {"summary": "Test"}}
        mock_requests.get.return_value = mock_response

        result = fetch_issue_raw("https://jira.company.com/browse/PROJ-123")

        assert result["key"] == "PROJ-123"
        assert result["fields"]["summary"] == "Test"
        mock_requests.get.assert_called_once()

    def test_no_token_raises_error(self, monkeypatch):
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)
        monkeypatch.delenv("ATLASSIAN_TOKEN", raising=False)

        with pytest.raises(JiraConnectorError, match="No Jira API token"):
            fetch_issue_raw("https://jira.company.com/browse/PROJ-123")

    @patch("documentation_sync.jira_connector.requests")
    def test_http_401_error(self, mock_requests, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "invalid_token")
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_requests.get.return_value = mock_response

        with pytest.raises(JiraConnectorError, match="authentication failed"):
            fetch_issue_raw("https://jira.company.com/browse/PROJ-123")

    @patch("documentation_sync.jira_connector.requests")
    def test_http_404_error(self, mock_requests, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_requests.get.return_value = mock_response

        with pytest.raises(JiraConnectorError, match="not found"):
            fetch_issue_raw("https://jira.company.com/browse/UNKNOWN-999")

    def test_missing_requests_package(self, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
        # Simulate requests not being available
        with patch("documentation_sync.jira_connector.requests", None):
            with pytest.raises(JiraConnectorError, match="requests"):
                fetch_issue_raw("https://jira.company.com/browse/PROJ-123")

    def test_connection_failure_reports_cause_not_nameerror(self, monkeypatch):
        """Regression: when requests.get itself raises, the error handler used to
        reference an unassigned `response` and mask the real cause with NameError."""
        monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
        import requests as real_requests

        mock_requests = MagicMock()
        mock_requests.get.side_effect = real_requests.ConnectionError("dns failure")
        mock_requests.Timeout = real_requests.Timeout
        mock_requests.RequestException = real_requests.RequestException

        with patch("documentation_sync.jira_connector.requests", mock_requests):
            with pytest.raises(JiraConnectorError, match="Could not reach Jira"):
                fetch_issue_raw("https://jira.company.com/browse/PROJ-123")

    def test_timeout_is_reported_as_timeout(self, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
        import requests as real_requests

        mock_requests = MagicMock()
        mock_requests.get.side_effect = real_requests.Timeout("too slow")
        mock_requests.Timeout = real_requests.Timeout
        mock_requests.RequestException = real_requests.RequestException

        with patch("documentation_sync.jira_connector.requests", mock_requests):
            with pytest.raises(JiraConnectorError, match="timed out"):
                fetch_issue_raw("https://jira.company.com/browse/PROJ-123")

    @patch("documentation_sync.jira_connector.requests")
    def test_html_login_page_reports_sso_hint(self, mock_requests, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("not json")
        mock_requests.get.return_value = mock_response

        with pytest.raises(JiraConnectorError, match="non-JSON"):
            fetch_issue_raw("https://jira.company.com/browse/PROJ-123")


class TestBuildAuthHeaders:
    """Jira Cloud needs Basic auth; Server/Data Center needs Bearer."""

    def test_server_uses_bearer(self):
        headers = build_auth_headers("https://jiraeu.epam.com/browse/AB-1", "tok")
        assert headers["Authorization"] == "Bearer tok"

    def test_cloud_uses_basic_with_email(self):
        headers = build_auth_headers(
            "https://acme.atlassian.net/browse/AB-1", "tok", email="a@b.com"
        )
        assert headers["Authorization"].startswith("Basic ")
        decoded = base64.b64decode(headers["Authorization"].split()[1]).decode()
        assert decoded == "a@b.com:tok"

    def test_cloud_falls_back_to_jira_email_env(self, monkeypatch):
        monkeypatch.setenv("JIRA_EMAIL", "env@b.com")
        headers = build_auth_headers("https://acme.atlassian.net/browse/AB-1", "tok")
        decoded = base64.b64decode(headers["Authorization"].split()[1]).decode()
        assert decoded == "env@b.com:tok"

    def test_cloud_without_email_raises(self, monkeypatch):
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        with pytest.raises(JiraConnectorError, match="account email"):
            build_auth_headers("https://acme.atlassian.net/browse/AB-1", "tok")


class TestToRestUrl:
    def test_converts_browse_url(self):
        assert (
            to_rest_url("https://jiraeu.epam.com/browse/EPMCDMETST-55568")
            == "https://jiraeu.epam.com/rest/api/2/issue/EPMCDMETST-55568"
        )

    def test_leaves_rest_url_unchanged(self):
        url = "https://jiraeu.epam.com/rest/api/2/issue/AB-1"
        assert to_rest_url(url) == url

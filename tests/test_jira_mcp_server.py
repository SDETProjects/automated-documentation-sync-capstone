"""Tests for jira_mcp_server tool handler functions.

Tests call the private _tool_* functions directly — no MCP protocol layer
needed — so they run fast and stay independent of network or Jira access.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from documentation_sync.jira_mcp_server import (
    _tool_fetch_jira_story,
    _tool_get_artifact_status,
    _tool_run_sdlc_pipeline,
    _tool_validate_jira_url,
    create_server,
)


# ---------------------------------------------------------------------------
# validate_jira_url
# ---------------------------------------------------------------------------

class TestValidateJiraUrl:
    def test_valid_epam_url(self):
        result = _tool_validate_jira_url(
            "https://jiraeu.epam.com/browse/EPMCDMETST-55568"
        )
        assert result["valid"] is True
        assert result["issue_key"] == "EPMCDMETST-55568"

    def test_valid_atlassian_cloud_url(self):
        result = _tool_validate_jira_url(
            "https://mycompany.atlassian.net/browse/PROJ-123"
        )
        assert result["valid"] is True
        assert result["issue_key"] == "PROJ-123"

    def test_invalid_github_url(self):
        result = _tool_validate_jira_url("https://github.com/org/repo/issues/42")
        assert result["valid"] is False
        assert result["issue_key"] is None

    def test_invalid_plain_string(self):
        result = _tool_validate_jira_url("not-a-url")
        assert result["valid"] is False

    def test_url_preserved_in_result(self):
        url = "https://jiraeu.epam.com/browse/TEST-1"
        result = _tool_validate_jira_url(url)
        assert result["url"] == url


# ---------------------------------------------------------------------------
# get_artifact_status
# ---------------------------------------------------------------------------

class TestGetArtifactStatus:
    def test_empty_dir_all_missing(self, tmp_path):
        result = _tool_get_artifact_status(str(tmp_path))
        assert result["phases_completed"] == 0
        assert result["total_phases"] == 5
        for detail in result["details"].values():
            assert detail["exists"] is False
            assert detail["path"] is None

    def test_partial_artifacts(self, tmp_path):
        (tmp_path / "requirements.md").write_text("# Requirements")
        (tmp_path / "architecture.md").write_text("# Architecture")
        result = _tool_get_artifact_status(str(tmp_path))
        assert result["phases_completed"] == 2
        assert result["total_phases"] == 5

    def test_all_artifacts_present(self, tmp_path):
        for name in ["requirements.md", "architecture.md", "design-review.md",
                     "impl-plan.md", "PR.md"]:
            (tmp_path / name).write_text(f"# {name}")
        result = _tool_get_artifact_status(str(tmp_path))
        assert result["phases_completed"] == 5

    def test_detail_keys_present(self, tmp_path):
        result = _tool_get_artifact_status(str(tmp_path))
        # Must have one entry per tracked phase
        assert len(result["details"]) == 5
        for detail in result["details"].values():
            assert "artifact" in detail
            assert "exists" in detail
            assert "path" in detail

    def test_existing_artifact_has_path(self, tmp_path):
        req = tmp_path / "requirements.md"
        req.write_text("# Requirements")
        result = _tool_get_artifact_status(str(tmp_path))
        phase_key = next(k for k in result["details"] if "Requirements" in k)
        assert result["details"][phase_key]["exists"] is True
        assert result["details"][phase_key]["path"] is not None

    def test_default_dir_does_not_crash(self):
        result = _tool_get_artifact_status(".")
        assert "phases_completed" in result
        assert "total_phases" in result


# ---------------------------------------------------------------------------
# fetch_jira_story — no network calls; mocked at jira_connector boundary
# ---------------------------------------------------------------------------

class TestFetchJiraStory:
    def test_bare_key_without_base_url_returns_error(self, monkeypatch):
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        result = _tool_fetch_jira_story("PROJ-123")
        assert "error" in result
        assert "JIRA_BASE_URL" in result["error"]

    def test_bare_key_with_base_url_fetches(self, monkeypatch):
        monkeypatch.setenv("JIRA_BASE_URL", "https://jiraeu.epam.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        mock_raw = {
            "key": "PROJ-123",
            "fields": {
                "summary": "Key lookup story",
                "description": "desc",
                "acceptance_criteria": ["ac"],
            },
        }
        with patch(
            "documentation_sync.jira_connector.fetch_issue_raw",
            return_value=mock_raw,
        ):
            result = _tool_fetch_jira_story("PROJ-123")

        assert "error" not in result
        assert result["key"] == "PROJ-123"

    def test_no_token_returns_error(self, monkeypatch):
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)
        result = _tool_fetch_jira_story(
            "https://jiraeu.epam.com/browse/PROJ-1", jira_token=None
        )
        assert "error" in result
        assert "token" in result["error"].lower()

    def test_explicit_token_overrides_env(self, monkeypatch):
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)
        mock_raw = {
            "key": "PROJ-1",
            "fields": {
                "summary": "Test story",
                "description": "A description",
                "acceptance_criteria": ["AC 1"],
            },
        }
        # Patch at source module because _tool_fetch_jira_story uses lazy import
        with patch(
            "documentation_sync.jira_connector.fetch_issue_raw",
            return_value=mock_raw,
        ):
            result = _tool_fetch_jira_story(
                "https://jiraeu.epam.com/browse/PROJ-1",
                jira_token="mytoken",
            )
        assert "error" not in result
        assert result["key"] == "PROJ-1"
        assert result["summary"] == "Test story"

    def test_connector_error_returned_as_error_dict(self, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        from documentation_sync.jira_connector import JiraConnectorError
        with patch(
            "documentation_sync.jira_connector.fetch_issue_raw",
            side_effect=JiraConnectorError("Auth failed"),
        ):
            result = _tool_fetch_jira_story(
                "https://jiraeu.epam.com/browse/PROJ-1"
            )
        assert "error" in result
        assert "Auth failed" in result["error"]

    def test_returned_fields_complete(self, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        mock_raw = {
            "key": "TEST-42",
            "fields": {
                "summary": "My story",
                "description": "Desc",
                "customfield_10014": "AC 1\nAC 2",
                "priority": {"name": "High"},
                "customfield_10016": 5,
                "reporter": {"emailAddress": "dev@example.com"},
                "assignee": {"displayName": "Jane"},
                "labels": ["backend"],
            },
        }
        with patch(
            "documentation_sync.jira_connector.fetch_issue_raw",
            return_value=mock_raw,
        ):
            result = _tool_fetch_jira_story(
                "https://jiraeu.epam.com/browse/TEST-42"
            )
        assert result["key"] == "TEST-42"
        assert result["priority"] == "High"
        assert result["story_points"] == 5
        assert result["reporter"] == "dev@example.com"
        assert result["assignee"] == "Jane"
        assert result["labels"] == ["backend"]


# ---------------------------------------------------------------------------
# run_sdlc_pipeline — cli.run mocked
# ---------------------------------------------------------------------------

class TestRunSdlcPipeline:
    def test_success_returns_artifacts(self, tmp_path, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        for name in ["requirements.md", "architecture.md", "design-review.md",
                     "impl-plan.md", "PR.md"]:
            (tmp_path / name).write_text(f"# {name}")

        with patch("documentation_sync.cli.run", return_value=0):
            result = _tool_run_sdlc_pipeline(
                "https://jiraeu.epam.com/browse/PROJ-1",
                output_dir=str(tmp_path),
            )

        assert result["status"] == "success"
        assert result["phases_completed"] == 5
        assert "requirements.md" in result["artifacts_generated"]
        assert "PR.md" in result["artifacts_generated"]

    def test_cli_error_returns_error_dict(self, tmp_path, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        with patch("documentation_sync.cli.run", return_value=1):
            result = _tool_run_sdlc_pipeline(
                "https://jiraeu.epam.com/browse/PROJ-1",
                output_dir=str(tmp_path),
            )
        assert result["status"] == "error"
        assert result["exit_code"] == 1

    def test_passes_non_interactive_true_by_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        with patch("documentation_sync.cli.run", return_value=0) as mock_run:
            _tool_run_sdlc_pipeline(
                "https://jiraeu.epam.com/browse/PROJ-1",
                output_dir=str(tmp_path),
            )
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("non_interactive") is True

    def test_passes_token_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("JIRA_API_TOKEN", "my-secret-token")
        with patch("documentation_sync.cli.run", return_value=0) as mock_run:
            _tool_run_sdlc_pipeline(
                "https://jiraeu.epam.com/browse/PROJ-1",
                output_dir=str(tmp_path),
            )
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("jira_token") == "my-secret-token"


# ---------------------------------------------------------------------------
# create_server — smoke test: server instantiation and tool registration
# ---------------------------------------------------------------------------

class TestCreateServer:
    def test_server_creates_without_error(self):
        pytest.importorskip("mcp", reason="optional extra: pip install -e '.[mcp-tools]'")
        server = create_server()
        assert server is not None

    def test_four_tools_registered(self):
        pytest.importorskip("mcp", reason="optional extra: pip install -e '.[mcp-tools]'")
        from mcp.server.mcpserver import MCPServer
        server = create_server()
        assert isinstance(server, MCPServer)
        # Access the tool manager to count registered tools
        tool_names = {t.name for t in server._tool_manager.list_tools()}
        assert "fetch_jira_story" in tool_names
        assert "run_sdlc_pipeline" in tool_names
        assert "get_artifact_status" in tool_names
        assert "validate_jira_url" in tool_names

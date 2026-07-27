"""Offline, fully-mocked tests for LLM provider adapters (providers.py).

All tests are designed to run without network access, without a real
ANTHROPIC_API_KEY, and without the Claude CLI installed, consistent with
the capstone's offline-testable design philosophy.
"""
from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from documentation_sync.models import JiraStory
from documentation_sync.providers import (
    ClaudeLLMAdapter,
    CopilotLLMAdapter,
    LLMManager,
)


def _sample_story() -> JiraStory:
    return JiraStory(
        key="ABC-1",
        summary="Sync docs automatically",
        description="Keep SDLC docs in sync with Jira stories.",
        acceptance_criteria=["Given a story, when parsed, then docs generate"],
        labels=["automation"],
    )


# ---------------------------------------------------------------------------
# ClaudeLLMAdapter — availability
# ---------------------------------------------------------------------------

class TestClaudeLLMAdapterAvailability:
    def test_available_when_api_key_set(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        adapter = ClaudeLLMAdapter()
        assert adapter.is_available() is True

    def test_available_when_cli_installed_and_no_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            adapter = ClaudeLLMAdapter()
            assert adapter.is_available() is True

    def test_unavailable_when_no_key_and_no_cli(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            adapter = ClaudeLLMAdapter()
            assert adapter.is_available() is False

    def test_unavailable_when_cli_returns_nonzero(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "claude"),
        ):
            adapter = ClaudeLLMAdapter()
            assert adapter.is_available() is False

    def test_name(self):
        assert "Claude" in ClaudeLLMAdapter().name()


# ---------------------------------------------------------------------------
# ClaudeLLMAdapter — question generation via SDK
# ---------------------------------------------------------------------------

class TestClaudeLLMAdapterSDKPath:
    def test_generate_questions_via_sdk(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        questions = ["Q1?", "Q2?", "Q3?"]

        mock_content = MagicMock()
        mock_content.text = json.dumps(questions)
        mock_message = MagicMock()
        mock_message.content = [mock_content]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch("documentation_sync.providers.Anthropic", return_value=mock_client):
            # Patch the import inside the method
            import documentation_sync.providers as p
            original = getattr(p, "Anthropic", None)
            p.Anthropic = lambda: mock_client  # type: ignore[attr-defined]

            try:
                adapter = ClaudeLLMAdapter()
                result = adapter.generate_clarifying_questions(_sample_story())
            finally:
                if original is not None:
                    p.Anthropic = original  # type: ignore[attr-defined]

        assert isinstance(result, list)
        assert len(result) <= 3

    def test_generate_questions_via_sdk_mocked_import(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        questions = ["Edge case Q1?", "Missing detail Q2?", "Ambiguity Q3?"]

        mock_content = MagicMock()
        mock_content.text = json.dumps(questions)
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.dict("sys.modules", {"anthropic": MagicMock(Anthropic=lambda: mock_client)}):
            adapter = ClaudeLLMAdapter()
            result = adapter.generate_clarifying_questions(_sample_story())

        assert len(result) == 3
        assert result[0] == "Edge case Q1?"


# ---------------------------------------------------------------------------
# ClaudeLLMAdapter — question generation via CLI fallback
# ---------------------------------------------------------------------------

class TestClaudeLLMAdapterCLIPath:
    def test_generate_questions_via_cli(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        questions = ["CLI Q1?", "CLI Q2?", "CLI Q3?"]

        mock_result = MagicMock()
        mock_result.stdout = json.dumps(questions)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            adapter = ClaudeLLMAdapter()
            result = adapter.generate_clarifying_questions(_sample_story())

        assert result == questions
        # Verify claude -p was called
        call_args = mock_run.call_args_list[-1]
        cmd = call_args[0][0]
        assert cmd[0] == "claude"
        assert cmd[1] == "-p"

    def test_generate_questions_truncates_to_three(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        many_questions = [f"Q{i}?" for i in range(10)]

        mock_result = MagicMock()
        mock_result.stdout = json.dumps(many_questions)

        with patch("subprocess.run", return_value=mock_result):
            adapter = ClaudeLLMAdapter()
            result = adapter.generate_clarifying_questions(_sample_story())

        assert len(result) == 3


# ---------------------------------------------------------------------------
# ClaudeLLMAdapter — as_llm_call
# ---------------------------------------------------------------------------

class TestClaudeLLMAdapterAsLLMCall:
    def test_as_llm_call_returns_callable(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        adapter = ClaudeLLMAdapter()
        llm_call = adapter.as_llm_call()
        assert callable(llm_call)

    def test_as_llm_call_cli_returns_callable_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        adapter = ClaudeLLMAdapter()
        llm_call = adapter.as_llm_call()
        assert callable(llm_call)

    def test_as_llm_call_cli_invokes_subprocess(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        mock_result = MagicMock()
        mock_result.stdout = "some response text"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            adapter = ClaudeLLMAdapter()
            llm_call = adapter.as_llm_call()
            output = llm_call("test prompt")

        assert output == "some response text"
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "claude"
        assert cmd[1] == "-p"


# ---------------------------------------------------------------------------
# CopilotLLMAdapter
# ---------------------------------------------------------------------------

class TestCopilotLLMAdapter:
    def test_is_not_available(self):
        adapter = CopilotLLMAdapter()
        assert adapter.is_available() is False

    def test_name_mentions_unavailable(self):
        assert "unavailable" in CopilotLLMAdapter().name().lower()

    def test_generate_questions_raises(self):
        adapter = CopilotLLMAdapter()
        with pytest.raises(RuntimeError, match="Copilot"):
            adapter.generate_clarifying_questions(_sample_story())

    def test_as_llm_call_raises(self):
        adapter = CopilotLLMAdapter()
        with pytest.raises(RuntimeError, match="Copilot"):
            adapter.as_llm_call()


# ---------------------------------------------------------------------------
# LLMManager
# ---------------------------------------------------------------------------

class TestLLMManager:
    def test_returns_claude_when_available(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        manager = LLMManager(preferred="claude")
        adapter = manager.get_adapter()
        assert isinstance(adapter, ClaudeLLMAdapter)

    def test_falls_back_to_claude_when_copilot_preferred_but_unavailable(
        self, monkeypatch
    ):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        manager = LLMManager(preferred="copilot")
        adapter = manager.get_adapter()
        # Falls back to Claude since Copilot is always unavailable
        assert isinstance(adapter, ClaudeLLMAdapter)

    def test_raises_when_no_adapter_available(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            manager = LLMManager(preferred="claude")
            with pytest.raises(RuntimeError, match="No LLM adapter available"):
                manager.get_adapter()

    def test_as_llm_call_returns_callable_when_claude_available(
        self, monkeypatch
    ):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        manager = LLMManager(preferred="claude")
        llm_call = manager.as_llm_call()
        assert callable(llm_call)

    def test_unknown_preferred_falls_back_to_first_available(
        self, monkeypatch
    ):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        manager = LLMManager(preferred="unknown_provider")
        # Should still find Claude
        adapter = manager.get_adapter()
        assert isinstance(adapter, ClaudeLLMAdapter)

"""LLM provider adapters for interactive clarification (Phase 1 of the
phased generation flow). Supports Claude (Anthropic SDK or CLI fallback)
and a stubbed GitHub Copilot adapter for architectural completeness.

Design goal: keep this module fully offline-testable. Adapters expose
`is_available()` so LLMManager can select a working provider and fail
loudly (not silently) when none is available.
"""
from __future__ import annotations

import json
import os
import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional

from .log import get_logger
from .models import JiraStory
from .resilience import retry
from .tokens import TokenCounter

log = get_logger("docsync.providers")


class LLMAdapter(ABC):
    """Common interface for pluggable LLM providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this adapter can be used right now."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name for logging."""

    @abstractmethod
    def generate_clarifying_questions(self, story: JiraStory) -> List[str]:
        """Return exactly up to 3 clarifying questions for the story."""


class ClaudeLLMAdapter(LLMAdapter):
    """Claude adapter. Prefers the Anthropic SDK (ANTHROPIC_API_KEY env
    var); falls back to shelling out to the `claude` CLI in -p (print)
    mode if the SDK path is unavailable but the CLI is installed.
    """

    MODEL = "claude-haiku-4-5-20251001"

    def __init__(
        self,
        token_counter: Optional[TokenCounter] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        self._tokens = token_counter or TokenCounter()
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

    def is_available(self) -> bool:
        # Treat API key presence as availability for manager selection.
        # The SDK import itself is resolved lazily at call time.
        if os.getenv("ANTHROPIC_API_KEY"):
            return True
        try:
            subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return False

    def name(self) -> str:
        if self._sdk_available():
            return "Claude (Anthropic SDK)"
        return "Claude (CLI via claude -p)"

    def _build_prompt(self, story: JiraStory) -> str:
        # M2: budget the description against the context window before sending.
        truncated_desc = self._tokens.truncate_to_budget(story.description)
        criteria = "\n".join(f"- {ac}" for ac in story.acceptance_criteria)
        prompt = (
            "Analyze this user story and generate exactly 3 clarifying "
            "questions about edge cases, missing details, or ambiguities.\n\n"
            f"Story:\nTitle: {story.summary}\nDescription: {truncated_desc}\n"
            f"Acceptance Criteria:\n{criteria}\n\n"
            'Return ONLY a JSON array of exactly 3 strings, nothing else.\n'
            'Example: ["Q1?", "Q2?", "Q3?"]'
        )
        # Emit a structured warning if we're close to blowing the window.
        count = self._tokens.count(prompt)
        log.debug(
            "prompt_built",
            llm_tokens_in=count.count,
            token_method=count.method,
            over_warning_threshold=count.warning,
        )
        if count.warning:
            log.warning(
                "token_budget_high",
                llm_tokens_in=count.count,
                warning_limit=self._tokens.warning_limit,
                event="prompt uses >80% of context window",
            )
        return prompt

    def _sdk_call(self, prompt: str) -> str:
        from anthropic import Anthropic  # optional dep; imported lazily

        client = Anthropic()
        message = client.messages.create(
            model=self.MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def _cli_call(self, prompt: str) -> str:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def generate_clarifying_questions(self, story: JiraStory) -> List[str]:
        prompt = self._build_prompt(story)

        # M3: wrap the call in exponential backoff on transient failures.
        try:
            if os.getenv("ANTHROPIC_API_KEY"):
                text = retry(
                    self._sdk_call,
                    prompt,
                    max_retries=self._max_retries,
                    base_delay=self._base_delay,
                    max_delay=self._max_delay,
                )
                fallback = False
            else:
                text = retry(
                    self._cli_call,
                    prompt,
                    max_retries=self._max_retries,
                    base_delay=self._base_delay,
                    max_delay=self._max_delay,
                )
                fallback = False
        except Exception as exc:  # noqa: BLE001 - LLM failure falls back
            log.warning(
                "llm_call_failed",
                event="falling back to heuristic questions",
                exception=str(exc),
                fallback_triggered=True,
            )
            from .llm_orchestrator import _heuristic_questions

            return _heuristic_questions(story)[:3]

        out_count = self._tokens.count(text)
        log.info(
            "clarifying_questions_generated",
            llm_tokens_out=out_count.count,
            fallback_triggered=fallback,
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            log.warning(
                "llm_response_not_json",
                event="returning heuristic questions",
                fallback_triggered=True,
            )
            from .llm_orchestrator import _heuristic_questions

            return _heuristic_questions(story)[:3]
        return parsed[:3]

    def _sdk_available(self) -> bool:
        """True only when both API key and the anthropic package are present."""
        if not os.getenv("ANTHROPIC_API_KEY"):
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False

    def as_llm_call(self):
        """Return a callable matching LLMCallable: (prompt: str) -> str.

        Tries the Anthropic SDK first (when ANTHROPIC_API_KEY + package are
        present), then falls back to the `claude -p` CLI subprocess on any
        SDK failure — handles CodeMie environments where the API key is a
        proxy token that the standard SDK cannot use against api.anthropic.com.
        """
        model = self.MODEL

        def _cli_call(prompt: str) -> str:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

        if not self._sdk_available():
            return _cli_call

        def _sdk_call(prompt: str) -> str:
            from anthropic import Anthropic

            client = Anthropic()
            message = client.messages.create(
                model=model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()

        def _sdk_with_cli_fallback(prompt: str) -> str:
            try:
                return _sdk_call(prompt)
            except Exception:
                # SDK failed (e.g. CodeMie proxy key can't reach api.anthropic.com
                # directly); transparently fall back to the CLI subprocess path.
                return _cli_call(prompt)

        return _sdk_with_cli_fallback


class CopilotLLMAdapter(LLMAdapter):
    """GitHub Copilot adapter — architecturally wired as an extension point.

    GitHub Copilot operates as a VS Code extension and does not expose a
    programmatic REST API callable from Python. The interactive clarification
    workflow is available via Copilot Chat in VS Code using the prompt files
    in .github/prompts/. This adapter preserves the --llm copilot flag in
    the CLI so the adapter pattern is demonstrable; at runtime it falls back
    to the offline heuristic question generator via LLMManager.
    """

    def is_available(self) -> bool:
        return False

    def name(self) -> str:
        return "GitHub Copilot (VS Code Chat only - CLI unavailable, see .github/prompts/)"

    def generate_clarifying_questions(self, story: JiraStory) -> List[str]:
        raise RuntimeError(self._unavailable_msg())

    def as_llm_call(self):
        raise RuntimeError(self._unavailable_msg())

    def _unavailable_msg(self) -> str:
        return (
            "GitHub Copilot does not expose a CLI-callable API.\n"
            "  To use Copilot for requirements clarification:\n"
            "    1. Open this project in VS Code with the Copilot extension active.\n"
            "    2. Open Copilot Chat and run: .github/prompts/01-requirements.prompt.md\n"
            "    3. Copilot will read .github/copilot-instructions.md automatically.\n"
            "  For the CLI phased flow, run with --llm claude instead."
        )


class LLMManager:
    """Selects a working LLM adapter, preferring the caller's choice but
    gracefully falling back to any other available adapter.
    """

    def __init__(self, preferred: str = "claude") -> None:
        self.preferred = preferred
        self.adapters: dict[str, LLMAdapter] = {
            "claude": ClaudeLLMAdapter(),
            "copilot": CopilotLLMAdapter(),
        }

    def get_adapter(self) -> LLMAdapter:
        preferred = self.adapters.get(self.preferred)
        if preferred and preferred.is_available():
            return preferred

        for name, adapter in self.adapters.items():
            if adapter.is_available():
                print(
                    f"WARNING: '{self.preferred}' unavailable; "
                    f"falling back to '{name}'"
                )
                return adapter

        raise RuntimeError(
            "No LLM adapter available.\n"
            "  - Set ANTHROPIC_API_KEY for the Claude SDK path\n"
            "  - Or install the Claude CLI and ensure 'claude --version' works\n"
            "  - Or omit --llm to use the offline heuristic question generator"
        )

    def as_llm_call(self):
        """Return an LLMCallable from the best available adapter.

        Passes straight into run_phased_generation(llm_call=...) without
        any changes to llm_orchestrator.py.
        """
        adapter = self.get_adapter()
        return adapter.as_llm_call()

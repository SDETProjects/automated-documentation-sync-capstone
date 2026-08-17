"""Token counting and context-window management for LLM calls.

Provides a :class:`TokenCounter` that can count tokens with the Anthropic SDK
when available, and falls back to a deterministic tiktoken / heuristic estimate
otherwise. This keeps the module fully offline-testable.

All call sites that send prompts to an LLM should pass their text through
``TokenCounter.count()`` and check ``TokenCounter.warning_threshold`` before
the call so that prompts exceeding ~80 % of the context window are truncated
or at least flagged.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

# Heuristic: ~4 chars/token for English; works well enough for truncation.
_HEURISTIC_CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class TokenCount:
    """Result of a token-count operation."""

    count: int
    method: str  # "anthropic" | "tiktoken" | "heuristic"
    warning: bool  # True if count > threshold % of the context window


class TokenCounter:
    """Count tokens with SDK when possible, fallback to heuristic otherwise."""

    def __init__(
        self,
        context_window: int = 200_000,
        warning_threshold: float = 0.8,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        self.context_window = context_window
        self.warning_threshold = warning_threshold
        self.model = model
        self._anthropic_client: Optional[object] = None

    @property
    def warning_limit(self) -> int:
        return int(self.context_window * self.warning_threshold)

    def _ensure_anthropic(self) -> bool:
        if self._anthropic_client is not None:
            return True
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return False
        try:
            import anthropic

            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
            return True
        except ImportError:
            return False

    def count(self, text: str) -> TokenCount:
        """Return a TokenCount for *text* using the best available method."""
        if self._ensure_anthropic():
            try:
                # Anthropic's count_tokens is sync in the current SDK.
                resp = self._anthropic_client.count_tokens(
                    model=self.model, messages=[{"role": "user", "content": text}]
                )
                return TokenCount(
                    count=resp.input_tokens,
                    method="anthropic",
                    warning=resp.input_tokens > self.warning_limit,
                )
            except Exception:
                # Any SDK failure -> fall through to heuristic
                pass

        # Fallback: tiktoken cl100k_base if installed, else heuristic
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return TokenCount(
                count=len(enc.encode(text)),
                method="tiktoken",
                warning=len(enc.encode(text)) > self.warning_limit,
            )
        except ImportError:
            # Deterministic heuristic: 4 chars ≈ 1 token
            heuristic_count = max(1, len(text) // _HEURISTIC_CHARS_PER_TOKEN)
            return TokenCount(
                count=heuristic_count,
                method="heuristic",
                warning=heuristic_count > self.warning_limit,
            )

    def truncate_to_budget(
        self, text: str, budget: Optional[int] = None
    ) -> str:
        """Truncate *text* so its token count ≤ *budget* (default: warning_limit)."""
        limit = budget or self.warning_limit
        tokens = self.count(text)
        if tokens.count <= limit:
            return text
        # Simple character-proportional truncation (good enough for heuristics)
        ratio = limit / tokens.count
        cut = int(len(text) * ratio)
        truncated = text[:cut]
        # Re-count and iterate once if still over
        if self.count(truncated).count > limit:
            truncated = truncated[: int(len(truncated) * 0.9)]
        return truncated


def create_counter_from_settings() -> TokenCounter:
    """Factory that reads env vars or falls back to defaults."""
    try:
        from .config import Settings
    except ImportError:
        Settings = None  # type: ignore[assignment]

    if Settings:
        try:
            settings = Settings.load()
            return TokenCounter(
                context_window=settings.max_context_tokens,
                warning_threshold=settings.llm.token_warning_threshold,
                model=settings.llm.model,
            )
        except Exception:
            pass
    # Fallback defaults match TokenCounter.__init__
    return TokenCounter()
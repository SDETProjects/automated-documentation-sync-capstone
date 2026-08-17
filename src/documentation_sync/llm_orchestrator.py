"""LLM integration layer: clarifying questions, interactive pause points,
and merging user feedback back into the story before requirements lock-in.

This module is provider-agnostic. If no LLM client is configured (no
ANTHROPIC_API_KEY / no Copilot runtime available), it falls back to a
deterministic heuristic question generator so the CLI flow still works
end-to-end without any network access, which keeps this capstone testable.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .models import JiraStory
from .tokens import TokenCounter, create_counter_from_settings


@dataclass
class EnrichedStory:
    """A JiraStory augmented with clarifying Q&A collected from the user."""

    story: JiraStory
    clarifications: Dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return self.story.key


# Type alias for a pluggable LLM call: (prompt) -> raw text response.
LLMCallable = Callable[[str], str]


def _heuristic_questions(story: JiraStory) -> List[str]:
    """Deterministic fallback question generator (no LLM required)."""
    questions: List[str] = []

    if not story.acceptance_criteria:
        questions.append(
            f"'{story.key}' has no acceptance criteria. What are the key "
            "Given/When/Then scenarios that define 'done'?"
        )
    else:
        questions.append(
            "Are there any edge cases (errors, empty states, concurrent "
            f"access) not covered by the {len(story.acceptance_criteria)} "
            "acceptance criteria listed?"
        )
    if not story.labels:
        questions.append(
            "Are there any non-functional requirements (performance, "
            "security, accessibility) that should be captured for this story?"
        )
    else:
        questions.append(
            f"The story is labeled {story.labels}. Should any of these "
            "labels map to a specific measurable NFR (e.g. a latency target)?"
        )
    questions.append(
        "Who is the primary reviewer/approver for the generated requirements "
        "before architecture work begins?"
    )
    return questions[:3]


def generate_clarifying_questions(
    story: JiraStory,
    llm_call: Optional[LLMCallable] = None,
    token_counter: Optional[TokenCounter] = None,
) -> List[str]:
    """Generate 2-3 clarifying questions about edge cases/ambiguities in a story.

    If `llm_call` is provided (e.g. a wrapper around the Claude API or a
    Copilot chat call), it is used to draft the questions from a prompt
    built from the story. Otherwise falls back to `_heuristic_questions` so
    the flow remains fully offline-testable.

    If `token_counter` is provided, the story description will be truncated
    to fit within the token budget before building the prompt.
    """
    if llm_call is None:
        return _heuristic_questions(story)

    # Initialize token counter if not provided
    if token_counter is None:
        token_counter = create_counter_from_settings()

    # M2: budget the description against the context window before sending.
    truncated_desc = token_counter.truncate_to_budget(story.description)

    prompt = (
        "You are reviewing a Jira user story before it is turned into "
        "formal requirements. Ask 2-3 short, specific clarifying questions "
        "about ambiguities or edge cases. Return ONLY the questions, one "
        "per line, no numbering.\n\n"
        f"Key: {story.key}\n"
        f"Summary: {story.summary}\n"
        f"Description: {truncated_desc}\n"
        f"Acceptance Criteria: {story.acceptance_criteria}\n"
        f"Labels: {story.labels}\n"
    )

    # Emit a structured warning if we're close to blowing the window.
    count = token_counter.count(prompt)
    if count.warning:
        import sys
        print(
            f"WARNING: Prompt uses {count.count} tokens (>{token_counter.warning_limit} limit); "
            "truncation may have occurred.",
            file=sys.stderr,
        )

    try:
        raw = llm_call(prompt)
    except Exception as exc:  # noqa: BLE001 - any LLM failure falls back to heuristics
        import sys
        print(
            f"WARNING: LLM call failed ({exc}); using heuristic questions instead.",
            file=sys.stderr,
        )
        return _heuristic_questions(story)

    questions = [line.strip(" -\t") for line in raw.splitlines() if line.strip()]
    return questions[:3] if questions else _heuristic_questions(story)


def wait_for_user_input(questions: List[str], input_func: Callable[[str], str] = input) -> Dict[str, str]:
    """CLI pause point: present each question and collect the user's answer.

    `input_func` is injectable for testing (defaults to the builtin `input`).
    An empty answer is recorded as "No response provided." rather than
    blocking the pipeline indefinitely.
    """
    answers: Dict[str, str] = {}
    for question in questions:
        print(f"\n[Clarification needed] {question}")
        response = input_func("> ").strip()
        answers[question] = response or "No response provided."
    return answers


def incorporate_feedback(story: JiraStory, answers: Dict[str, str]) -> EnrichedStory:
    """Merge clarifying Q&A back into the story as an EnrichedStory.

    The original JiraStory is left untouched (immutability keeps traceability
    predictable); the Q&A is carried alongside it and surfaced in the
    generated requirements.md "Open Questions" / "Clarifications" section.
    """
    return EnrichedStory(story=story, clarifications=dict(answers))


def is_llm_configured() -> bool:
    """Best-effort detection of whether a real LLM backend is available.

    Checked env vars are provider-agnostic placeholders; callers may pass
    their own `llm_call` to `generate_clarifying_questions` regardless.
    """
    return bool(
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("COPILOT_API_TOKEN")
    )

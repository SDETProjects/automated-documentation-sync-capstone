"""Tests for documentation_sync.llm_orchestrator."""
from documentation_sync.llm_orchestrator import (
    EnrichedStory,
    generate_clarifying_questions,
    incorporate_feedback,
    wait_for_user_input,
)
from documentation_sync.models import JiraStory


def _story(**overrides):
    defaults = dict(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z"],
        labels=[],
    )
    defaults.update(overrides)
    return JiraStory(**defaults)


def test_generate_clarifying_questions_heuristic_no_llm():
    questions = generate_clarifying_questions(_story())
    assert 1 <= len(questions) <= 3
    assert all(isinstance(q, str) and q for q in questions)


def test_generate_clarifying_questions_flags_missing_acceptance_criteria():
    story = _story(acceptance_criteria=[])
    questions = generate_clarifying_questions(story)
    assert any("acceptance criteria" in q.lower() for q in questions)


def test_generate_clarifying_questions_uses_llm_call_when_provided():
    def fake_llm(prompt: str) -> str:
        assert "ABC-1" in prompt
        return "Question one?\nQuestion two?\nQuestion three?\n"

    questions = generate_clarifying_questions(_story(), llm_call=fake_llm)
    assert questions == ["Question one?", "Question two?", "Question three?"]


def test_generate_clarifying_questions_falls_back_on_llm_failure():
    def failing_llm(prompt: str) -> str:
        raise RuntimeError("LLM unavailable")

    questions = generate_clarifying_questions(_story(), llm_call=failing_llm)
    assert questions  # falls back to heuristic questions, never empty


def test_wait_for_user_input_collects_answers():
    questions = ["Q1?", "Q2?"]
    responses = iter(["Answer 1", "Answer 2"])

    answers = wait_for_user_input(questions, input_func=lambda _: next(responses))
    assert answers == {"Q1?": "Answer 1", "Q2?": "Answer 2"}


def test_wait_for_user_input_records_blank_response():
    answers = wait_for_user_input(["Q1?"], input_func=lambda _: "")
    assert answers["Q1?"] == "No response provided."


def test_incorporate_feedback_returns_enriched_story():
    story = _story()
    answers = {"Q1?": "A1"}
    enriched = incorporate_feedback(story, answers)

    assert isinstance(enriched, EnrichedStory)
    assert enriched.story is story
    assert enriched.clarifications == answers
    assert enriched.key == "ABC-1"

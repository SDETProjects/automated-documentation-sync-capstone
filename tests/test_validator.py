"""Tests for documentation_sync.validator."""
import pytest

from documentation_sync.models import JiraStory, Requirement, RequirementSet
from documentation_sync.validator import (
    ValidationError,
    ensure_valid_requirement_set,
    ensure_valid_story,
    validate_requirement_set,
    validate_story,
)


def _valid_story() -> JiraStory:
    return JiraStory(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z"],
    )


def test_validate_story_happy_path():
    story = _valid_story()
    assert validate_story(story) == []
    ensure_valid_story(story)  # should not raise


def test_validate_story_missing_fields():
    story = JiraStory(key="", summary="", description="", acceptance_criteria=[])
    issues = validate_story(story)
    assert len(issues) == 4

    with pytest.raises(ValidationError):
        ensure_valid_story(story)


def test_validate_requirement_set_happy_path():
    story = _valid_story()
    req_set = RequirementSet(
        story=story,
        requirements=[
            Requirement("US-1", "US", "Do the thing (ABC-1)", "ABC-1"),
            Requirement("FR-1", "FR", "Given X, when Y, then Z", "ABC-1"),
        ],
    )
    assert validate_requirement_set(req_set) == []
    ensure_valid_requirement_set(req_set)  # should not raise


def test_validate_requirement_set_duplicate_ids():
    story = _valid_story()
    req_set = RequirementSet(
        story=story,
        requirements=[
            Requirement("FR-1", "FR", "text one", "ABC-1"),
            Requirement("FR-1", "FR", "text two", "ABC-1"),
        ],
    )
    issues = validate_requirement_set(req_set)
    assert any("Duplicate" in issue for issue in issues)


def test_validate_requirement_set_empty():
    story = _valid_story()
    req_set = RequirementSet(story=story, requirements=[])

    with pytest.raises(ValidationError):
        ensure_valid_requirement_set(req_set)

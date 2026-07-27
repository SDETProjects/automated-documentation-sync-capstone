"""Tests for documentation_sync.parser."""
import json

import pytest

from documentation_sync.parser import (
    StoryNotFoundError,
    StoryParseError,
    load_story,
)


def _write_json(tmp_path, data):
    path = tmp_path / "story.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_story_happy_path(tmp_path):
    data = {
        "key": "ABC-1",
        "summary": "Do the thing",
        "description": "As a user I want the thing.",
        "acceptance_criteria": ["Given X, when Y, then Z"],
    }
    path = _write_json(tmp_path, data)

    story = load_story(path)

    assert story.key == "ABC-1"
    assert story.summary == "Do the thing"
    assert story.acceptance_criteria == ["Given X, when Y, then Z"]


def test_load_story_missing_required_fields(tmp_path):
    data = {"key": "ABC-2"}
    path = _write_json(tmp_path, data)

    with pytest.raises(StoryParseError):
        load_story(path)


def test_load_story_invalid_json(tmp_path):
    path = tmp_path / "story.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(StoryParseError):
        load_story(path)


def test_load_story_not_found(tmp_path):
    missing = tmp_path / "does_not_exist.json"

    with pytest.raises(StoryNotFoundError):
        load_story(missing)


def test_load_story_unsupported_extension(tmp_path):
    path = tmp_path / "story.txt"
    path.write_text("irrelevant", encoding="utf-8")

    with pytest.raises(StoryParseError):
        load_story(path)


def test_load_story_from_markdown(tmp_path):
    md = (
        "# ABC-3: Enable feature X\n\n"
        "## Description\n"
        "As a user I want feature X to work.\n\n"
        "## Acceptance Criteria\n"
        "- Given A, when B, then C\n"
        "- Given D, when E, then F\n"
    )
    path = tmp_path / "story.md"
    path.write_text(md, encoding="utf-8")

    story = load_story(path)

    assert story.key == "ABC-3"
    assert story.summary == "Enable feature X"
    assert len(story.acceptance_criteria) == 2

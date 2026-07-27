"""Tests for documentation_sync.input_handler."""
import json

import pytest

from documentation_sync.input_handler import (
    IntegrationUnavailableError,
    detect_input_type,
    fetch_from_url,
    load_story_from_any_source,
)
from documentation_sync.parser import StoryParseError


def _write_json(tmp_path, data):
    path = tmp_path / "story.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_detect_input_type_url():
    assert detect_input_type("https://mycompany.atlassian.net/browse/ABC-1") == "url"
    assert detect_input_type("http://confluence.mycompany.com/page") == "url"


def test_detect_input_type_file(tmp_path):
    data = {"key": "ABC-1", "summary": "S", "description": "D", "acceptance_criteria": ["x"]}
    path = _write_json(tmp_path, data)
    assert detect_input_type(str(path)) == "file"


def test_detect_input_type_text():
    assert detect_input_type("Key: ABC-1\nTitle: Something") == "text"


def test_fetch_from_url_without_token_raises():
    with pytest.raises(IntegrationUnavailableError):
        fetch_from_url("https://mycompany.atlassian.net/browse/ABC-1", auth_token=None)


def test_fetch_from_url_unsupported_host_raises():
    with pytest.raises(IntegrationUnavailableError):
        fetch_from_url("https://example.com/not-jira", auth_token="dummy-token")


def test_load_story_from_any_source_file(tmp_path):
    data = {
        "key": "ABC-1",
        "summary": "Do the thing",
        "description": "As a user I want the thing.",
        "acceptance_criteria": ["Given X, when Y, then Z"],
    }
    path = _write_json(tmp_path, data)
    story = load_story_from_any_source(str(path))
    assert story.key == "ABC-1"
    assert story.summary == "Do the thing"


def test_load_story_from_any_source_raw_json_text():
    raw = json.dumps(
        {
            "key": "ABC-2",
            "summary": "Pasted story",
            "description": "As a user I want pasted input to work.",
            "acceptance_criteria": ["Given a paste, when parsed, then it works"],
        }
    )
    story = load_story_from_any_source(raw)
    assert story.key == "ABC-2"
    assert story.summary == "Pasted story"


def test_load_story_from_any_source_url_without_token_raises():
    with pytest.raises(IntegrationUnavailableError):
        load_story_from_any_source(
            "https://mycompany.atlassian.net/browse/ABC-1", auth_config={}
        )


def test_load_story_from_any_source_markdown_text():
    text = (
        "# ABC-3: A pasted markdown story\n"
        "## Description\n"
        "As a user I want markdown paste support.\n"
        "## Acceptance Criteria\n"
        "- Given a markdown paste, when parsed, then it works\n"
    )
    story = load_story_from_any_source(text)
    assert story.key == "ABC-3"
    assert story.acceptance_criteria


def test_load_story_from_any_source_invalid_json_text_raises():
    with pytest.raises(StoryParseError):
        load_story_from_any_source("{not valid json")

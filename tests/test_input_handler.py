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


def test_detect_input_type_issue_key_remains_text():
    # Issue key routing is handled by load_story_from_any_source for backward
    # compatibility with detect_input_type return values.
    assert detect_input_type("EPMCDMETST-55568") == "text"


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


def test_load_story_from_any_source_issue_key_without_base_url_raises():
    with pytest.raises(IntegrationUnavailableError, match="JIRA_BASE_URL"):
        load_story_from_any_source("EPMCDMETST-55568", auth_config={"jira_token": "tok"})


def test_load_story_from_any_source_issue_key_uses_repo_config(monkeypatch, tmp_path):
    from documentation_sync import input_handler as ih

    config = tmp_path / "docsync.config.json"
    config.write_text(
        json.dumps({"jira_base_url": "https://jiraeu.epam.com"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    captured = {}

    def fake_fetch(url, auth_token=None):
        captured["url"] = url
        return {
            "key": "EPMCDMETST-55568",
            "fields": {
                "summary": "Resolved from config",
                "description": "desc",
                "acceptance_criteria": ["ac"],
            },
        }

    monkeypatch.setattr(ih, "fetch_from_url", fake_fetch)

    story = load_story_from_any_source(
        "EPMCDMETST-55568",
        auth_config={"jira_token": "tok"},
    )

    assert captured["url"] == "https://jiraeu.epam.com/browse/EPMCDMETST-55568"
    assert story.key == "EPMCDMETST-55568"


def test_load_story_from_any_source_issue_key_invalid_repo_config_raises(monkeypatch, tmp_path):
    config = tmp_path / "docsync.config.json"
    config.write_text("{not-json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(IntegrationUnavailableError, match="Invalid JSON"):
        load_story_from_any_source("EPMCDMETST-55568", auth_config={"jira_token": "tok"})


def test_load_story_from_any_source_issue_key_resolves_and_fetches(monkeypatch):
    from documentation_sync import input_handler as ih

    captured = {}

    def fake_fetch(url, auth_token=None):
        captured["url"] = url
        captured["token"] = auth_token
        return {
            "key": "EPMCDMETST-55568",
            "fields": {
                "summary": "Resolved from key",
                "description": "As a user I want key lookup.",
                "acceptance_criteria": ["Given a key, when resolved, then story loads"],
            },
        }

    monkeypatch.setattr(ih, "fetch_from_url", fake_fetch)
    story = load_story_from_any_source(
        "EPMCDMETST-55568",
        auth_config={"jira_token": "tok", "jira_base_url": "https://jiraeu.epam.com"},
    )

    assert captured["url"] == "https://jiraeu.epam.com/browse/EPMCDMETST-55568"
    assert captured["token"] == "tok"
    assert story.key == "EPMCDMETST-55568"


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


# ── _extract_ac_from_description ──────────────────────────────────────────────

def test_extract_ac_from_description_numbered_items():
    from documentation_sync.input_handler import _extract_ac_from_description

    desc = (
        "Some preamble.\n"
        "Acceptance Criteria\n"
        "1. Given A, when B, then C\n"
        "2. Given D, when E, then F\n"
    )
    ac = _extract_ac_from_description(desc)
    assert ac == ["Given A, when B, then C", "Given D, when E, then F"]


def test_extract_ac_from_description_stops_at_notes_section():
    from documentation_sync.input_handler import _extract_ac_from_description

    desc = (
        "Acceptance Criteria\n"
        "1. First criterion\n"
        "Notes\n"
        "2. This should not be included\n"
    )
    ac = _extract_ac_from_description(desc)
    assert len(ac) == 1
    assert ac[0] == "First criterion"


def test_extract_ac_from_description_given_prefix():
    from documentation_sync.input_handler import _extract_ac_from_description

    desc = "Acceptance Criteria\nGiven X, when Y, then Z"
    ac = _extract_ac_from_description(desc)
    assert "Given X, when Y, then Z" in ac


# ── _flatten_adf ──────────────────────────────────────────────────────────────

def test_flatten_adf_plain_string():
    from documentation_sync.input_handler import _flatten_adf

    assert _flatten_adf("hello") == "hello"


def test_flatten_adf_dict_with_text():
    from documentation_sync.input_handler import _flatten_adf

    node = {"type": "text", "text": "hello world"}
    assert _flatten_adf(node) == "hello world"


def test_flatten_adf_dict_with_children():
    from documentation_sync.input_handler import _flatten_adf

    node = {
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "foo"},
            {"type": "text", "text": "bar"},
        ],
    }
    result = _flatten_adf(node)
    assert "foo" in result
    assert "bar" in result


def test_flatten_adf_list():
    from documentation_sync.input_handler import _flatten_adf

    nodes = [{"text": "a"}, {"text": "b"}]
    result = _flatten_adf(nodes)
    assert "a" in result
    assert "b" in result


# ── _normalize_freetext ───────────────────────────────────────────────────────

def test_normalize_freetext_inserts_newlines_before_numbered_items():
    from documentation_sync.input_handler import _normalize_freetext

    text = "Preamble 1. First item 2. Second item"
    result = _normalize_freetext(text)
    assert "\n1." in result
    assert "\n2." in result


def test_normalize_freetext_inserts_newlines_before_headers():
    from documentation_sync.input_handler import _normalize_freetext

    text = "Some text Acceptance Criteria 1. Item"
    result = _normalize_freetext(text)
    assert "\nAcceptance Criteria\n" in result


# ── _extract_freetext_story ───────────────────────────────────────────────────

def test_extract_freetext_story_finds_jira_key():
    from documentation_sync.input_handler import _extract_freetext_story

    text = "ABC-42: As a user I want feature X.\nAcceptance Criteria\n1. Given X, then Y"
    story = _extract_freetext_story(text)
    assert story.key == "ABC-42"


def test_extract_freetext_story_falls_back_to_manual_key():
    from documentation_sync.input_handler import _extract_freetext_story

    text = "I want to build something nice.\nAcceptance Criteria\n1. Given A, then B"
    story = _extract_freetext_story(text)
    assert story.key == "MANUAL-001"


def test_extract_freetext_story_extracts_i_want_summary():
    from documentation_sync.input_handler import _extract_freetext_story

    text = "As a user I want to enable feature X so that things work"
    story = _extract_freetext_story(text)
    assert "I want to enable feature X" in story.summary


def test_extract_freetext_story_collects_ac_items():
    from documentation_sync.input_handler import _extract_freetext_story

    text = (
        "ABC-10: Story\n"
        "Acceptance Criteria\n"
        "- Given A, when B, then C\n"
        "- Given D, when E, then F\n"
    )
    story = _extract_freetext_story(text)
    assert len(story.acceptance_criteria) == 2


# ── _story_from_raw_json with ADF description ─────────────────────────────────

def test_story_from_raw_json_with_adf_description():
    from documentation_sync.input_handler import _story_from_raw_json

    data = {
        "key": "ADF-1",
        "fields": {
            "summary": "ADF story",
            "description": {
                "type": "doc",
                "content": [{"type": "text", "text": "As a user I want ADF support."}],
            },
            "acceptance_criteria": ["Given ADF, then it works"],
        },
    }
    story = _story_from_raw_json(data)
    assert story.key == "ADF-1"
    assert "ADF support" in story.description


def test_story_from_raw_json_ac_extracted_from_description():
    from documentation_sync.input_handler import _story_from_raw_json

    data = {
        "key": "EXTR-1",
        "fields": {
            "summary": "Extract AC",
            "description": (
                "Background text.\nAcceptance Criteria\n1. Given X, when Y, then Z"
            ),
        },
    }
    story = _story_from_raw_json(data)
    assert story.acceptance_criteria


def test_story_from_raw_json_story_points_bad_value_ignored():
    from documentation_sync.input_handler import _story_from_raw_json

    data = {
        "key": "SP-1",
        "fields": {
            "summary": "Story points test",
            "description": "desc",
            "story_points": "not-a-number",
        },
    }
    story = _story_from_raw_json(data)
    assert story.story_points is None


# ── fetch_from_url: requests ImportError path ─────────────────────────────────

def test_fetch_from_url_requests_import_error_raises(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("mocked missing requests")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    with pytest.raises(IntegrationUnavailableError, match="requests"):
        fetch_from_url("https://mycompany.atlassian.net/browse/ABC-1", auth_token="token")

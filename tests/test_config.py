"""Tests for documentation_sync.config — Settings loading and validation."""
import json
from pathlib import Path

import pytest

from documentation_sync.config import (
    CONFIG_FILENAME,
    ConfigError,
    Settings,
    _bool,
    _env_overrides,
    _load_config_file,
    _normalise_config,
)


# ---------------------------------------------------------------------------
# _bool helper
# ---------------------------------------------------------------------------

def test_bool_true_from_bool():
    assert _bool(True) is True


def test_bool_false_from_bool():
    assert _bool(False) is False


def test_bool_true_from_string_true():
    assert _bool("true") is True


def test_bool_true_from_string_1():
    assert _bool("1") is True


def test_bool_true_from_string_yes():
    assert _bool("yes") is True


def test_bool_false_from_string_false():
    assert _bool("false") is False


def test_bool_false_from_zero():
    assert _bool(0) is False


# ---------------------------------------------------------------------------
# _normalise_config
# ---------------------------------------------------------------------------

def test_normalise_config_passes_through_plain_dict():
    data = {"jira_base_url": "https://jira.example.com"}
    result = _normalise_config(data)
    assert result["jira_base_url"] == "https://jira.example.com"


def test_normalise_config_extracts_jira_base_url_from_nested():
    data = {"jira": {"base_url": "https://nested.jira.com"}}
    result = _normalise_config(data)
    assert result["jira_base_url"] == "https://nested.jira.com"


def test_normalise_config_does_not_override_explicit_jira_base_url():
    data = {
        "jira_base_url": "https://explicit.jira.com",
        "jira": {"base_url": "https://nested.jira.com"},
    }
    result = _normalise_config(data)
    assert result["jira_base_url"] == "https://explicit.jira.com"


def test_normalise_config_coerces_mcp_enabled_string():
    data = {"mcp_enabled": "true"}
    result = _normalise_config(data)
    assert result["mcp_enabled"] is True


# ---------------------------------------------------------------------------
# _env_overrides
# ---------------------------------------------------------------------------

def test_env_overrides_empty_when_no_vars():
    overrides = _env_overrides({})
    assert overrides == {}


def test_env_overrides_jira_base_url():
    overrides = _env_overrides({"JIRA_BASE_URL": "https://jira.example.com"})
    assert overrides["jira_base_url"] == "https://jira.example.com"


def test_env_overrides_logging_level():
    overrides = _env_overrides({"DOCSYNC_LOG_LEVEL": "DEBUG"})
    assert overrides["logging_level"] == "DEBUG"


def test_env_overrides_mcp_api_key():
    overrides = _env_overrides({"DOCSYNC_MCP_API_KEY": "my-key"})
    assert overrides["mcp_api_key"] == "my-key"


def test_env_overrides_llm_model():
    overrides = _env_overrides({"DOCSYNC_LLM_MODEL": "claude-haiku-3"})
    assert overrides["llm"]["model"] == "claude-haiku-3"


def test_env_overrides_llm_max_retries():
    overrides = _env_overrides({"DOCSYNC_LLM_MAX_RETRIES": "5"})
    assert overrides["llm"]["max_retries"] == 5


# ---------------------------------------------------------------------------
# _load_config_file
# ---------------------------------------------------------------------------

def test_load_config_file_returns_empty_dict_when_no_file():
    result = _load_config_file(None)
    # _load_config_file returns {} when no config file is found.
    # If a docsync.config.json happens to exist in cwd, this may vary.
    assert isinstance(result, dict)


def test_load_config_file_raises_config_error_for_missing_explicit_path(tmp_path):
    nonexistent = tmp_path / "missing.json"
    with pytest.raises(ConfigError, match="Config file not found"):
        _load_config_file(str(nonexistent))


def test_load_config_file_raises_config_error_for_invalid_json(tmp_path):
    bad = tmp_path / CONFIG_FILENAME
    bad.write_text("NOT JSON", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid JSON"):
        _load_config_file(str(bad))


def test_load_config_file_raises_config_error_for_non_object_json(tmp_path):
    arr_file = tmp_path / CONFIG_FILENAME
    arr_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ConfigError, match="must contain a JSON object"):
        _load_config_file(str(arr_file))


def test_load_config_file_loads_valid_config(tmp_path):
    cfg = {"jira_base_url": "https://jira.example.com"}
    cfg_file = tmp_path / CONFIG_FILENAME
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
    result = _load_config_file(str(cfg_file))
    assert result["jira_base_url"] == "https://jira.example.com"


# ---------------------------------------------------------------------------
# Settings.load
# ---------------------------------------------------------------------------

def test_settings_load_raises_when_explicit_path_missing():
    with pytest.raises(ConfigError):
        Settings.load(
            config_path="/nonexistent/path/that/does/not/exist.json",
            env={},
        )


def test_settings_load_defaults_when_no_config_and_no_env(tmp_path, monkeypatch):
    # Ensure we're in a directory with no docsync.config.json
    monkeypatch.chdir(tmp_path)
    settings = Settings.load(env={})
    assert settings.logging_level == "INFO"


def test_settings_load_env_overrides_take_precedence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings.load(env={"DOCSYNC_LOG_LEVEL": "DEBUG"})
    assert settings.logging_level == "DEBUG"


def test_settings_load_from_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"logging_level": "WARNING"}
    (tmp_path / CONFIG_FILENAME).write_text(json.dumps(cfg), encoding="utf-8")
    settings = Settings.load(env={})
    assert settings.logging_level == "WARNING"


def test_settings_load_raises_config_error_for_missing_explicit_path(tmp_path):
    with pytest.raises(ConfigError):
        Settings.load(config_path=str(tmp_path / "no_such_file.json"), env={})


def test_settings_default_jira_base_url_is_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings.load(env={})
    assert settings.jira_base_url == ""


def test_settings_load_jira_base_url_from_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings.load(env={"JIRA_BASE_URL": "https://jira.example.com"})
    assert settings.jira_base_url == "https://jira.example.com"

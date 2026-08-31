"""Centralised, validated configuration for the docsync engine.

Loads a single :class:`Settings` object from, in increasing precedence:

    1. defaults (hard-coded in the model)
    2. a config file  (``docsync.config.json``, optionally with an explicit
       path override) validated against ``docsync.config.schema.json``
    3. environment variables (``DOCSYNC_*``)

A single source of truth removes the configuration chaos that previously
scattered env reads and ad-hoc ``docsync.config.json`` parsing across
``input_handler.py``, ``providers.py``, ``jira_connector.py`` and the CLI.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from pydantic import BaseModel, Field, ValidationError
except ImportError:  # pragma: no cover - pydantic is a core dependency
    # In test environments without pydantic, provide minimal shims
    class _BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    BaseModel = _BaseModel

    def Field(default=None, default_factory=None, **kwargs):  # noqa: N802
        if default_factory is not None:
            return default_factory()
        return default

    class ValidationError(Exception):
        pass

SCHEMA_FILENAME = "docsync.config.schema.json"
CONFIG_FILENAME = "docsync.config.json"
_ENV_PREFIX = "DOCSYNC_"


class ConfigError(Exception):
    """Raised when configuration cannot be loaded or validated."""


def _env(name: str) -> Optional[str]:
    """Read an environment variable honouring the DOCSYNC_ prefix."""
    return os.environ.get(f"{_ENV_PREFIX}{name}")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


class LLMSettings(BaseModel):
    """LLM provider and token-budget knobs."""

    model: str = "claude-haiku-4-5-20251001"
    max_tokens: int = 512
    max_retries: int = 3
    retry_base_delay_s: float = 1.0
    retry_max_delay_s: float = 60.0
    context_window: int = 200_000
    token_warning_threshold: float = 0.8


class Settings(BaseModel):
    """Full engine configuration, loaded once at startup."""

    jira_base_url: str = ""
    llm: LLMSettings = Field(default_factory=LLMSettings)
    logging_level: str = "INFO"
    mcp_api_key: str = ""
    mcp_rate_limit_per_minute: int = 60
    max_context_tokens: int = 200_000

    # -- Loading ------------------------------------------------------------

    @classmethod
    def load(
        cls,
        config_path: Optional[str | Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> "Settings":
        """Load settings from file -> env -> defaults, in that precedence.

        ``env`` is an injectable mapping for tests; when omitted the real
        process environment is read. ``config_path`` overrides the default
        ``docsync.config.json`` search.
        """
        data = _load_config_file(config_path)

        # Apply env overrides (DOCSYNC_*) on top of the file, then defaults.
        overrides = _env_overrides(env)
        data.update(overrides)

        try:
            return cls(**data)
        except ValidationError as exc:
            raise ConfigError(f"Invalid configuration: {exc}") from exc


def _discover_config_path() -> Optional[Path]:
    """Return the first docsync.config.json found from cwd up to the root."""
    start = Path.cwd().resolve()
    for directory in [start, *start.parents]:
        candidate = directory / CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return None


def _load_config_file(config_path: Optional[str | Path]) -> Dict[str, Any]:
    """Read and JSON-validate the config file (if any)."""
    path: Optional[Path] = None
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
    else:
        path = _discover_config_path()
    if path is None:
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"Config file {path} must contain a JSON object.")

    validate_against_schema(raw, path)
    return _normalise_config(raw)


def validate_against_schema(
    data: Dict[str, Any], config_path: Optional[str | Path] = None
) -> None:
    """Validate a config dict against docsync.config.schema.json.

    Uses :mod:`jsonschema` when available; otherwise falls back to pydantic
    field validation so the check still runs.
    """
    try:
        import jsonschema
    except ImportError:
        return  # pydantic field validation is the backstop

    schema = _load_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        location = f" in {config_path}" if config_path else ""
        raise ConfigError(f"Config{location} fails JSON Schema: {exc.message}") from exc


def _load_schema() -> Dict[str, Any]:
    """Locate and parse docsync.config.schema.json shipped with the package."""
    here = Path(__file__).resolve().parent
    candidates = [here / SCHEMA_FILENAME, here.parent.parent / SCHEMA_FILENAME]
    for candidate in candidates:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    raise ConfigError(
        f"Cannot locate {SCHEMA_FILENAME} next to the package. "
        f"Searched: {', '.join(str(c) for c in candidates)}"
    )


def _normalise_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map legacy/loose config keys onto the Settings model fields."""
    result = dict(data)

    # Support both {"jira_base_url": "..."} and {"jira": {"base_url": "..."}}.
    if "jira_base_url" not in result:
        jira = data.get("jira")
        if isinstance(jira, dict) and jira.get("base_url"):
            result["jira_base_url"] = jira["base_url"]

    # Coerce boolean-ish values so legacy configs parse cleanly.
    for key in ("mcp_enabled",):
        if key in result:
            result[key] = _bool(result[key])
    return result


def _env_overrides(env: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Translate DOCSYNC_* env vars into flat Settings fields."""
    source = os.environ if env is None else env
    overrides: Dict[str, Any] = {}

    jira_base_url = source.get("JIRA_BASE_URL")
    if jira_base_url:
        overrides["jira_base_url"] = jira_base_url

    logging_level = source.get("DOCSYNC_LOG_LEVEL")
    if logging_level:
        overrides["logging_level"] = logging_level

    mcp_api_key = source.get("DOCSYNC_MCP_API_KEY")
    if mcp_api_key:
        overrides["mcp_api_key"] = mcp_api_key

    llm_model = source.get("DOCSYNC_LLM_MODEL")
    if llm_model:
        overrides.setdefault("llm", {})["model"] = llm_model

    max_retries = source.get("DOCSYNC_LLM_MAX_RETRIES")
    if max_retries:
        overrides.setdefault("llm", {})["max_retries"] = int(max_retries)

    return overrides

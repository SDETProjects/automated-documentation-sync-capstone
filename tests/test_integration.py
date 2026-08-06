"""End-to-end integration tests for the Automated Documentation Sync CLI flow."""
import json

import pytest

from documentation_sync.cli import build_arg_parser, main, run


def _write_story(tmp_path, data):
    path = tmp_path / "story.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_end_to_end_happy_path(tmp_path):
    story_path = _write_story(
        tmp_path,
        {
            "key": "EPMCDMETST-55568",
            "summary": "Enable automated documentation sync",
            "description": "As a QA engineer I want docs to sync automatically.",
            "acceptance_criteria": [
                "Given a story file, the system parses it",
                "Given requirements, the system generates docs",
            ],
        },
    )
    output_dir = tmp_path / "out"

    exit_code = run(str(story_path), str(output_dir))

    assert exit_code == 0
    for filename in (
        "requirements.md",
        "architecture.md",
        "design-review.md",
        "impl-plan.md",
        "PR.md",
    ):
        generated = output_dir / filename
        assert generated.exists()
        assert generated.read_text(encoding="utf-8").strip() != ""


def test_end_to_end_missing_fields_returns_error(tmp_path):
    story_path = _write_story(tmp_path, {"key": "EPMCDMETST-1"})
    output_dir = tmp_path / "out"

    exit_code = run(str(story_path), str(output_dir))

    assert exit_code == 1
    assert not output_dir.exists() or list(output_dir.iterdir()) == []


def test_end_to_end_invalid_json_returns_error(tmp_path):
    story_path = tmp_path / "story.json"
    story_path.write_text("{invalid", encoding="utf-8")
    output_dir = tmp_path / "out"

    exit_code = run(str(story_path), str(output_dir))

    assert exit_code == 1


def test_end_to_end_story_not_found_returns_error(tmp_path):
    missing_path = tmp_path / "missing.json"
    output_dir = tmp_path / "out"

    exit_code = run(str(missing_path), str(output_dir))

    assert exit_code == 2


def test_end_to_end_no_acceptance_criteria_fails_validation(tmp_path):
    story_path = _write_story(
        tmp_path,
        {
            "key": "EPMCDMETST-2",
            "summary": "Story without acceptance criteria",
            "description": "Some description.",
            "acceptance_criteria": [],
        },
    )
    output_dir = tmp_path / "out"

    exit_code = run(str(story_path), str(output_dir))

    assert exit_code == 1


def test_run_with_explicit_jira_token_emits_warning(tmp_path, capsys):
    story_path = _write_story(
        tmp_path,
        {
            "key": "WARN-1",
            "summary": "Token warning test",
            "description": "Check that explicit jira-token triggers a warning.",
            "acceptance_criteria": ["Given a token, warn the user"],
        },
    )
    out = tmp_path / "out"

    exit_code = run(str(story_path), str(out), jira_token="fake-token-abc")

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "JIRA_API_TOKEN" in captured.err


class TestArgParser:
    def test_defaults(self):
        args = build_arg_parser().parse_args(["story.json"])
        assert args.story_input == "story.json"
        assert args.output_dir is None
        assert args.phased is False
        assert args.non_interactive is False
        assert args.llm is None

    def test_all_flags(self):
        args = build_arg_parser().parse_args(
            ["story.json", "-o", "out", "--phased", "--non-interactive", "--llm", "claude"]
        )
        assert args.output_dir == "out"
        assert args.phased is True
        assert args.non_interactive is True
        assert args.llm == "claude"


def test_run_defaults_to_github_copilot_output(tmp_path, monkeypatch):
    story_path = _write_story(
        tmp_path,
        {
            "key": "DEF-1",
            "summary": "Default output dir",
            "description": "As a user I want a stable default output path.",
            "acceptance_criteria": ["Given no -o, artifacts go to default folder"],
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = run(str(story_path))

    assert exit_code == 0
    assert (tmp_path / "github-copilot-output" / "requirements.md").exists()


def test_run_defaults_to_claude_output_when_llm_claude(tmp_path, monkeypatch):
    story_path = _write_story(
        tmp_path,
        {
            "key": "DEF-2",
            "summary": "Claude default output dir",
            "description": "As a user I want claude outputs separated.",
            "acceptance_criteria": ["Given llm claude and no -o, artifacts go to claude-output"],
        },
    )
    monkeypatch.chdir(tmp_path)

    exit_code = run(str(story_path), llm="claude")

    assert exit_code == 0
    assert (tmp_path / "claude-output" / "requirements.md").exists()

    def test_rejects_unknown_llm(self):
        with pytest.raises(SystemExit):
            build_arg_parser().parse_args(["story.json", "--llm", "gpt4"])


def test_run_fallback_paste_when_integration_unavailable(tmp_path, monkeypatch):
    """When IntegrationUnavailableError is raised, _load_story_with_fallback
    prompts the user to paste the story; simulate pasting via monkeypatching input()."""
    import documentation_sync.cli as cli_module
    from documentation_sync.input_handler import IntegrationUnavailableError
    from documentation_sync import input_handler as ih_module

    out = tmp_path / "out"

    pasted_lines = [
        "# PASTE-1: Pasted story",
        "## Description",
        "As a user I want the fallback paste path to work.",
        "## Acceptance Criteria",
        "- Given a paste, when parsed, then it works",
        "",
    ]
    line_iter = iter(pasted_lines)
    call_count = {"n": 0}

    real_load = ih_module.load_story_from_any_source

    def fake_load(input_str, auth_config=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise IntegrationUnavailableError("no token")
        return real_load(input_str, auth_config=auth_config)

    monkeypatch.setattr("documentation_sync.cli.load_story_from_any_source", fake_load)
    monkeypatch.setattr("builtins.input", lambda *_: next(line_iter, ""))

    exit_code = cli_module.run(
        "https://fake.jira.com/browse/PASTE-1",
        str(out),
    )
    assert exit_code == 0


class TestMain:
    def test_main_happy_path_returns_zero(self, tmp_path):
        story_path = _write_story(
            tmp_path,
            {
                "key": "MAIN-1",
                "summary": "Main entry point works",
                "description": "As a user I want the CLI entry point to work.",
                "acceptance_criteria": ["Given argv, when main runs, then exit code is 0"],
            },
        )
        out = tmp_path / "out"

        assert main([str(story_path), "-o", str(out)]) == 0
        assert (out / "requirements.md").exists()

    def test_main_phased_non_interactive(self, tmp_path):
        story_path = _write_story(
            tmp_path,
            {
                "key": "MAIN-2",
                "summary": "Phased flow via main",
                "description": "As a user I want the phased flow from the CLI.",
                "acceptance_criteria": ["Given --phased, when main runs, then artifacts exist"],
            },
        )
        out = tmp_path / "out"

        exit_code = main([str(story_path), "-o", str(out), "--phased", "--non-interactive"])

        assert exit_code == 0
        for filename in ("requirements.md", "architecture.md", "PR.md"):
            assert (out / filename).exists()

    def test_main_missing_file_returns_two(self, tmp_path):
        assert main([str(tmp_path / "nope.json"), "-o", str(tmp_path / "out")]) == 2

    def test_unicode_story_content_does_not_crash(self, tmp_path):
        """Regression: Jira content contains characters (e.g. "50 -> 0.5" with an
        arrow glyph) that a cp1252 Windows console cannot encode."""
        story_path = _write_story(
            tmp_path,
            {
                "key": "UNI-1",
                "summary": "Percentage button: 50 → 0.5",
                "description": "Values convert → like this — always.",
                "acceptance_criteria": ["Given 50, when % pressed, then 50 → 0.5"],
            },
        )
        out = tmp_path / "out"

        assert main([str(story_path), "-o", str(out)]) == 0
        content = (out / "requirements.md").read_text(encoding="utf-8")
        assert "→" in content

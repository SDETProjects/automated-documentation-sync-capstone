"""End-to-end integration tests for the Automated Documentation Sync CLI flow."""
import json

from documentation_sync.cli import run


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

"""Tests for generated-document quality verification (Phase 7)."""
from __future__ import annotations

import json

import pytest

from documentation_sync.doc_validator import (
    check_document,
    check_story_parity,
    check_traceability,
    extract_trace_ids,
    main,
    validate_artifacts,
)
from documentation_sync.generator import build_requirement_set, write_all_artifacts
from documentation_sync.models import JiraStory


@pytest.fixture
def story() -> JiraStory:
    return JiraStory(
        key="TEST-1",
        summary="Sync documentation automatically",
        description="As a developer I want docs generated from the story.",
        acceptance_criteria=[
            "Artifacts are generated from the story",
            "Traceability IDs are preserved",
        ],
    )


@pytest.fixture
def generated_dir(tmp_path, story):
    write_all_artifacts(build_requirement_set(story), tmp_path)
    return tmp_path


# --- Happy path -------------------------------------------------------------


def test_real_generated_artifacts_pass(generated_dir):
    report = validate_artifacts(generated_dir)
    assert report.ok, [str(i) for i in report.issues]
    assert len(report.checked) == 8  # All 8 steps now


def test_main_returns_zero_on_valid_output(generated_dir, capsys):
    assert main([str(generated_dir)]) == 0
    assert "Document quality OK" in capsys.readouterr().out


def test_extract_trace_ids_finds_all_categories():
    assert extract_trace_ids("US-1 and FR-12 plus NFR-3") == {"US-1", "FR-12", "NFR-3"}


def test_extract_trace_ids_ignores_non_ids():
    assert extract_trace_ids("VERSION-1 and FRAGMENT-2") == set()


# --- Edge cases: structure --------------------------------------------------


def test_empty_document_reported():
    issues = check_document("PR.md", "   \n")
    assert len(issues) == 1
    assert "empty" in issues[0].message


def test_missing_level_one_title():
    issues = check_document("impl-plan.md", "## Steps\n## Test Strategy\n")
    assert any("missing level-1 title" in i.message for i in issues)


def test_title_not_first_line():
    text = "Preamble text\n\n# Implementation Plan\n\n## Steps\n\n## Test Strategy\n"
    issues = check_document("impl-plan.md", text)
    assert any("must be the first line" in i.message for i in issues)


def test_heading_deeper_than_level_two_rejected():
    text = "# Impl\n\n## Steps\n\n### Substep\n\n## Test Strategy\n"
    issues = check_document("impl-plan.md", text)
    assert any("deeper than level 2" in i.message for i in issues)


def test_missing_required_section():
    text = "# Impl\n\n## Steps\n- do the thing\n"
    issues = check_document("impl-plan.md", text)
    assert any("Test Strategy" in i.message for i in issues)


def test_unknown_filename_has_no_section_requirements():
    assert check_document("notes.md", "# Notes\n\n## Anything\n") == []


# --- Edge cases: traceability ----------------------------------------------


def test_traceability_missing_requirements_file():
    issues = check_traceability({"PR.md": "# PR\n\nFR-1\n"})
    assert any("cannot verify traceability" in i.message for i in issues)


def test_traceability_requirements_defines_no_ids():
    issues = check_traceability({"requirements.md": "# Requirements\n\nNo IDs here.\n"})
    assert any("defines no traceability IDs" in i.message for i in issues)


def test_traceability_downstream_cites_nothing():
    artifacts = {
        "requirements.md": "# R\n\nUS-1 FR-1 NFR-1\n",
        "PR.md": "# PR\n\nNo identifiers at all.\n",
    }
    issues = check_traceability(artifacts)
    assert any(i.filename == "PR.md" and "cites no" in i.message for i in issues)


def test_traceability_downstream_cites_unknown_id():
    artifacts = {
        "requirements.md": "# R\n\nUS-1 FR-1 NFR-1\n",
        "PR.md": "# PR\n\nCovers FR-1 and FR-99.\n",
    }
    issues = check_traceability(artifacts)
    assert any("FR-99" in i.message for i in issues)


def test_traceability_skips_absent_optional_artifacts():
    artifacts = {"requirements.md": "# R\n\nUS-1 FR-1\n"}
    assert check_traceability(artifacts) == []


# --- Edge cases: directory --------------------------------------------------


def test_missing_artifacts_reported(tmp_path):
    report = validate_artifacts(tmp_path)
    assert not report.ok
    assert report.checked == []
    assert any("not found" in i.message for i in report.issues)


def test_drifted_artifact_fails_and_main_returns_one(generated_dir, capsys):
    (generated_dir / "impl-plan.md").write_text("# Impl\n\n## Steps\n", encoding="utf-8")
    assert main([str(generated_dir)]) == 1
    err = capsys.readouterr().err
    assert "Document quality FAILED" in err
    assert "Test Strategy" in err


# --- Story parity -----------------------------------------------------------


def test_parity_passes_for_generated_artifacts(generated_dir, story):
    text = (generated_dir / "requirements.md").read_text(encoding="utf-8")
    assert check_story_parity(story, text) == []


def test_parity_allows_refined_prose(story):
    """Hand-refined wording is fine as long as the IDs match the story."""
    text = (
        "# Requirements: TEST-1\n\n"
        "US-1 as a developer...\n"
        "FR-1 completely rewritten by a human in Copilot Chat\n"
        "FR-2 also rewritten with much richer detail\n"
        "NFR-1 traceability\n"
    )
    assert check_story_parity(story, text) == []


def test_parity_detects_missing_fr(story):
    text = "# Requirements: TEST-1\n\nUS-1\nFR-1 only\n"
    issues = check_story_parity(story, text)
    assert any("FR-2 missing" in i.message for i in issues)


def test_parity_detects_invented_fr(story):
    text = "# Requirements: TEST-1\n\nUS-1\nFR-1\nFR-2\nFR-3 invented\n"
    issues = check_story_parity(story, text)
    assert any("FR-3" in i.message and "no matching" in i.message for i in issues)


def test_parity_detects_missing_us1(story):
    text = "# Requirements: TEST-1\n\nFR-1\nFR-2\n"
    issues = check_story_parity(story, text)
    assert any("US-1 missing" in i.message for i in issues)


def test_parity_detects_missing_story_key(story):
    text = "# Requirements\n\nUS-1\nFR-1\nFR-2\n"
    issues = check_story_parity(story, text)
    assert any("does not reference story key TEST-1" in i.message for i in issues)


def test_validate_artifacts_with_story_path(tmp_path, story, generated_dir):
    story_file = tmp_path / "story.json"
    story_file.write_text(
        json.dumps(
            {
                "key": story.key,
                "summary": story.summary,
                "description": story.description,
                "acceptance_criteria": story.acceptance_criteria,
            }
        ),
        encoding="utf-8",
    )
    report = validate_artifacts(generated_dir, story_file)
    assert report.ok, [str(i) for i in report.issues]


def test_main_accepts_story_flag(tmp_path, story, generated_dir, capsys):
    story_file = tmp_path / "story.json"
    story_file.write_text(
        json.dumps(
            {
                "key": story.key,
                "summary": story.summary,
                "description": story.description,
                "acceptance_criteria": story.acceptance_criteria,
            }
        ),
        encoding="utf-8",
    )
    assert main([str(generated_dir), "--story", str(story_file)]) == 0
    assert "story parity" in capsys.readouterr().out


def test_validate_8_steps_artifacts(generated_dir):
    """Verify that all 8 step artifacts are checked."""
    report = validate_artifacts(generated_dir)
    expected_8 = {
        "requirements.md",
        "architecture.md",
        "design-review.md",
        "impl-plan.md",
        "code-review.md",
        "verification-report.md",
        "CHANGELOG.md",
        "PR.md",
    }
    assert set(report.checked) == expected_8


def test_verification_report_missing_required_section(tmp_path, story, generated_dir):
    """Verify that verification-report.md must have required sections."""
    (generated_dir / "verification-report.md").write_text(
        "# Verification Report\n\n## Test Summary\nNot the right heading.\n",
        encoding="utf-8"
    )
    report = validate_artifacts(generated_dir)
    assert not report.ok
    assert any("Test Execution Summary" in i.message for i in report.issues)


def test_changelog_missing_required_section(tmp_path, story, generated_dir):
    """Verify that CHANGELOG.md must have required sections."""
    (generated_dir / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Updates\nNo required sections.\n",
        encoding="utf-8"
    )
    report = validate_artifacts(generated_dir)
    assert not report.ok
    assert any("Overview" in i.message for i in report.issues)

"""Tests for documentation_sync.generator."""
from documentation_sync.generator import (
    build_requirement_set,
    generate_architecture_md,
    generate_changelog_md,
    generate_code_review_md,
    generate_impl_plan_md,
    generate_pr_md,
    generate_requirements_md,
    generate_user_story_md,
    generate_verification_report_md,
    write_all_artifacts,
)
from documentation_sync.models import JiraStory


def _story() -> JiraStory:
    return JiraStory(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z", "Given A, when B, then C"],
    )


def test_build_requirement_set_creates_expected_ids():
    req_set = build_requirement_set(_story())
    ids = [r.req_id for r in req_set.requirements]

    assert ids[0] == "US-1"
    assert "FR-1" in ids
    assert "FR-2" in ids
    assert ids[-1] == "NFR-1"


def test_generate_requirements_md_contains_traceability():
    req_set = build_requirement_set(_story())
    content = generate_requirements_md(req_set)

    assert "US-1" in content
    assert "FR-1" in content
    assert "NFR-1" in content
    assert "ABC-1" in content


def test_generate_architecture_md_lists_functional_requirements():
    req_set = build_requirement_set(_story())
    content = generate_architecture_md(req_set)

    assert "FR-1" in content
    assert "FR-2" in content


def test_generate_impl_plan_md_has_steps_for_each_fr():
    req_set = build_requirement_set(_story())
    content = generate_impl_plan_md(req_set)

    assert "FR-1" in content
    assert "FR-2" in content


def test_generate_pr_md_references_all_requirement_ids():
    req_set = build_requirement_set(_story())
    content = generate_pr_md(req_set)

    for req in req_set.requirements:
        assert req.req_id in content


def test_write_all_artifacts_creates_files(tmp_path):
    req_set = build_requirement_set(_story())
    written = write_all_artifacts(req_set, tmp_path)

    expected_names = {
        "user-story.md",
        "requirements.md",
        "architecture.md",
        "design-review.md",
        "impl-plan.md",
        "code-review.md",
        "verification-report.md",
        "CHANGELOG.md",
        "PR.md",
    }
    assert {p.name for p in written} == expected_names
    for path in written:
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip() != ""


def test_generate_user_story_md_round_trips_through_parser(tmp_path):
    """user-story.md must parse back into the same JiraStory it was generated from."""
    from documentation_sync.parser import load_story

    story = JiraStory(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z", "Given A, when B, then C"],
        labels=["capstone"],
        priority="High",
        story_points=3,
        reporter="alice@example.com",
        assignee="bob@example.com",
    )
    req_set = build_requirement_set(story)
    content = generate_user_story_md(req_set)

    story_path = tmp_path / "user-story.md"
    story_path.write_text(content, encoding="utf-8")
    reparsed = load_story(story_path)

    assert reparsed.key == story.key
    assert reparsed.summary == story.summary
    assert reparsed.description == story.description
    assert reparsed.acceptance_criteria == story.acceptance_criteria


def test_generate_user_story_md_renders_metadata(tmp_path):
    story = JiraStory(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z"],
        labels=["capstone"],
        priority="High",
        story_points=3,
    )
    content = generate_user_story_md(build_requirement_set(story))

    assert "# ABC-1: Do the thing" in content
    assert "## Acceptance Criteria" in content
    assert "- Given X, when Y, then Z" in content
    assert "## Metadata" in content
    assert "| Labels | capstone |" in content
    assert "| Priority | High |" in content
    assert "| Story Points | 3 |" in content


def test_generate_verification_report_md_has_required_sections():
    req_set = build_requirement_set(_story())
    content = generate_verification_report_md(req_set)

    assert "Test Execution Summary" in content
    assert "Integration Verification" in content
    assert "Traceability Verification" in content
    assert "Artifact Quality Check" in content
    assert "Outcome" in content


def test_generate_changelog_md_has_required_sections():
    req_set = build_requirement_set(_story())
    content = generate_changelog_md(req_set)

    assert "Overview" in content
    assert "Changes" in content
    assert "Known Limitations" in content

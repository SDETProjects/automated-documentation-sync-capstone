"""Tests for documentation_sync.generator."""
from documentation_sync.generator import (
    build_requirement_set,
    generate_architecture_md,
    generate_impl_plan_md,
    generate_pr_md,
    generate_requirements_md,
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
        "requirements.md",
        "architecture.md",
        "design-review.md",
        "impl-plan.md",
        "PR.md",
    }
    assert {p.name for p in written} == expected_names
    for path in written:
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip() != ""

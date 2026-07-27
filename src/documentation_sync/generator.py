"""Generators that turn requirements into SDLC documentation artifacts."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

from .models import JiraStory, Requirement, RequirementSet


def build_requirement_set(story: JiraStory) -> RequirementSet:
    """Convert a parsed story into a traceable set of requirements.

    - One US requirement summarizing the story itself.
    - One FR requirement per acceptance criterion.
    - One baseline NFR requirement (documentation/traceability quality).
    """
    requirements: List[Requirement] = []

    requirements.append(
        Requirement(
            req_id="US-1",
            category="US",
            text=f"{story.summary} ({story.key})",
            source_key=story.key,
        )
    )

    for idx, criterion in enumerate(story.acceptance_criteria, start=1):
        requirements.append(
            Requirement(
                req_id=f"FR-{idx}",
                category="FR",
                text=criterion,
                source_key=story.key,
            )
        )

    requirements.append(
        Requirement(
            req_id="NFR-1",
            category="NFR",
            text=(
                "Every generated artifact must retain traceability back to the "
                f"originating story {story.key} via requirement IDs."
            ),
            source_key=story.key,
        )
    )

    return RequirementSet(story=story, requirements=requirements)


def _traceability_table(req_set: RequirementSet) -> str:
    rows = ["| ID | Category | Requirement | Source |", "|----|----------|-------------|--------|"]
    for req in req_set.requirements:
        rows.append(f"| {req.req_id} | {req.category} | {req.text} | {req.source_key} |")
    return "\n".join(rows)


def generate_requirements_md(req_set: RequirementSet) -> str:
    story = req_set.story
    today = date.today().isoformat()
    lines = [
        f"# Requirements: {story.key}",
        "",
        f"_Generated: {today}_",
        "",
        "## Story Summary",
        story.summary,
        "",
        "## Description",
        story.description,
        "",
        "## Traceability Matrix",
        _traceability_table(req_set),
        "",
        "## Clarifications Needed",
        (
            "None identified."
            if story.acceptance_criteria
            else "Acceptance criteria were missing; please clarify expected behavior."
        ),
    ]
    return "\n".join(lines) + "\n"


def generate_architecture_md(req_set: RequirementSet) -> str:
    story = req_set.story
    fr_list = "\n".join(f"- {r.req_id}: {r.text}" for r in req_set.by_category("FR"))
    return (
        f"# Architecture: {story.key}\n\n"
        "## Overview\n"
        "A file-based Python engine reads a story, builds structured requirements, "
        "and renders Markdown documentation artifacts via templated generators.\n\n"
        "## Components\n"
        "- `parser`: loads JSON/Markdown story input\n"
        "- `validator`: enforces required fields and traceability rules\n"
        "- `generator`: builds requirements and downstream docs\n"
        "- `cli`: orchestrates the end-to-end flow\n\n"
        "## Requirements Addressed\n"
        f"{fr_list}\n"
    )


def generate_design_review_md(req_set: RequirementSet) -> str:
    story = req_set.story
    return (
        f"# Design Review: {story.key}\n\n"
        "## Design Summary\n"
        "File-based pipeline: story -> requirements -> generated docs, kept "
        "intentionally simple and testable for the capstone scope.\n\n"
        "## Risks\n"
        "- Limited Jira integration (file-based only for v1)\n"
        "- Simple heuristic-based Markdown parsing\n\n"
        "## Review Outcome\n"
        "Approved for implementation pending sign-off on requirements.md.\n"
    )


def generate_impl_plan_md(req_set: RequirementSet) -> str:
    story = req_set.story
    steps = "\n".join(
        f"{i}. Implement and test {r.req_id}: {r.text}"
        for i, r in enumerate(req_set.by_category("FR"), start=1)
    )
    return (
        f"# Implementation Plan: {story.key}\n\n"
        "## Steps\n"
        f"{steps}\n\n"
        "## Test Strategy\n"
        "Pytest coverage for happy path, missing fields, invalid input, and "
        "not-found scenarios.\n"
    )


def generate_pr_md(req_set: RequirementSet) -> str:
    story = req_set.story
    req_ids = ", ".join(r.req_id for r in req_set.requirements)
    return (
        f"# PR: {story.key} - {story.summary}\n\n"
        "## Summary\n"
        f"Implements automated documentation sync for {story.key}.\n\n"
        "## Traceability\n"
        f"Addresses requirements: {req_ids}\n\n"
        "## Verification\n"
        "See test-evidence.md and evidence/pr-automation-evidence.md for "
        "local execution results.\n"
    )


def write_all_artifacts(req_set: RequirementSet, output_dir: str | Path = ".") -> List[Path]:
    """Render and write all documentation artifacts to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "requirements.md": generate_requirements_md(req_set),
        "architecture.md": generate_architecture_md(req_set),
        "design-review.md": generate_design_review_md(req_set),
        "impl-plan.md": generate_impl_plan_md(req_set),
        "PR.md": generate_pr_md(req_set),
    }

    written: List[Path] = []
    for filename, content in artifacts.items():
        path = out / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)

    return written

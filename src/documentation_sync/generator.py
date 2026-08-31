"""Generators that turn requirements into SDLC documentation artifacts."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import JiraStory, Requirement, RequirementSet

TRACE_ID_PATTERN = re.compile(r"\b(?:US|FR|NFR)-\d+\b")


class TraceabilityError(Exception):
    """Raised when a generator emits a traceability ID absent from req_set.

    This enforces traceability at generation time (fail fast) rather than
    deferring the check to docsync-verify (M4).
    """


def _known_ids(req_set: RequirementSet) -> Set[str]:
    """The set of requirement IDs the generator is allowed to cite."""
    return {r.req_id for r in req_set.requirements}


def extract_trace_ids(text: str) -> Set[str]:
    """Return the set of US/FR/NFR-<n> IDs cited in *text*."""
    return set(TRACE_ID_PATTERN.findall(text))


def assert_traceable(content: str, req_set: RequirementSet) -> None:
    """Fail fast if *content* cites an ID not defined in *req_set*."""
    known = _known_ids(req_set)
    cited = extract_trace_ids(content)
    unknown = sorted(cited - known)
    if unknown:
        raise TraceabilityError(
            f"Artifact cites requirement IDs absent from requirements.md: "
            f"{', '.join(unknown)}. Known IDs: {', '.join(sorted(known)) or '(none)'}"
        )


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


def generate_requirements_md(
    req_set: RequirementSet, clarifications: Optional[Dict[str, str]] = None
) -> str:
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
        "## Clarifications",
    ]

    if clarifications:
        for idx, (question, answer) in enumerate(clarifications.items(), start=1):
            lines.extend([f"{idx}. **{question}**", f"   - {answer}", ""])
    elif story.acceptance_criteria:
        lines.append("None identified.")
    else:
        lines.append("Acceptance criteria were missing; please clarify expected behavior.")

    return "\n".join(lines).rstrip() + "\n"


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


def generate_verification_report_md(req_set: RequirementSet) -> str:
    story = req_set.story
    fr_count = len(req_set.by_category("FR"))
    return (
        f"# Verification Report: {story.key}\n\n"
        "## Test Execution Summary\n"
        f"Running test suite for {story.key}...\n"
        f"Required test coverage for {fr_count} functional requirements.\n\n"
        "## Integration Verification\n"
        "Verify the implementation satisfies the acceptance criteria:\n"
        + "\n".join(f"- [ ] {criterion}" for criterion in story.acceptance_criteria) + "\n\n"
        "## Traceability Verification\n"
        "Map each requirement to test coverage:\n"
        + "\n".join(
            f"- {r.req_id}: test coverage TBD" for r in req_set.by_category("FR")
        )
        + "\n\n"
        "## Artifact Quality Check\n"
        "Run: `docsync-verify . --story user-story.md`\n\n"
        "## Outcome\n"
        "[ ] Pass\n"
        "[ ] Pass with caveats (describe)\n"
        "[ ] Fail (blocking issue to resolve)\n"
    )


def generate_code_review_md(req_set: RequirementSet) -> str:
    story = req_set.story
    req_ids = ", ".join(r.req_id for r in req_set.requirements)
    fr_list = "\n".join(f"- {r.req_id}: {r.text}" for r in req_set.by_category("FR"))
    return (
        f"# Code Review: {story.key}\n\n"
        "## Scope\n"
        "Review scope: source code, test suite, and implementation against requirements.\n"
        f"Requirements addressed: {req_ids}\n\n"
        "## Functional Requirements\n"
        f"{fr_list}\n\n"
        "## Findings\n"
        "Correctness: Verify each component behaves as specified in requirements.md.\n\n"
        "Code Quality: Check separation of concerns, error handling, and traceability.\n\n"
        "Testing: Verify tests cover happy path and edge cases (missing fields, not found).\n\n"
        "## Outcome\n"
        "[ ] Approved\n"
        "[ ] Approved with comments\n"
        "[ ] Changes requested (describe)\n"
    )


def generate_changelog_md(req_set: RequirementSet) -> str:
    story = req_set.story
    today = date.today().isoformat()
    return (
        f"# Changelog: {story.key}\n\n"
        f"_Generated: {today}_\n\n"
        "## Overview\n"
        f"{story.summary}\n\n"
        "## Changes\n"
        f"Implements {story.key}.\n\n"
        "- [ ] Feature 1: (describe the change)\n"
        "- [ ] Feature 2: (describe the change)\n"
        "- [ ] Bugfix: (if applicable)\n\n"
        "## Known Limitations\n"
        "- Out of scope for this release:\n"
        "- Deferred to v1.1:\n"
    )


def generate_user_story_md(req_set: RequirementSet) -> str:
    """Render the source story as a Markdown input file (user-story.md).

    This captures the live Jira fetch (key, summary, description, acceptance
    criteria) into the canonical input file the Copilot pipeline reads in
    `/run-pipeline`. It uses the exact Markdown convention `_read_markdown`
    parses, so the round-trip through `docsync-verify --story user-story.md`
    preserves story-to-requirement ID parity.

    Metadata (labels, priority, story points, reporter, assignee) is appended
    as a `## Metadata` section so a downstream fetch never loses Jira context.
    """
    story = req_set.story
    today = date.today().isoformat()
    lines = [
        f"# {story.key}: {story.summary}",
        "",
        f"_Fetched: {today}_",
        "",
        "## Description",
        story.description or "(no description provided)",
        "",
        "## Acceptance Criteria",
    ]
    if story.acceptance_criteria:
        lines.extend(f"- {criterion}" for criterion in story.acceptance_criteria)
    else:
        lines.append("(none provided)")

    metadata: Dict[str, str] = {}
    if story.labels:
        metadata["Labels"] = ", ".join(str(lbl) for lbl in story.labels)
    if story.priority:
        metadata["Priority"] = str(story.priority)
    if story.story_points is not None:
        metadata["Story Points"] = str(story.story_points)
    if story.reporter:
        metadata["Reporter"] = str(story.reporter)
    if story.assignee:
        metadata["Assignee"] = str(story.assignee)

    if metadata:
        lines.append("")
        lines.append("## Metadata")
        # Use table format to avoid parser confusion with acceptance criteria bullets
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        for key, value in metadata.items():
            lines.append(f"| {key} | {value} |")

    return "\n".join(lines).rstrip() + "\n"


def write_all_artifacts(
    req_set: RequirementSet,
    output_dir: str | Path = ".",
    clarifications: Optional[Dict[str, str]] = None,
) -> List[Path]:
    """Render and write all documentation artifacts to output_dir.

    Writes steps 1-4 (fully generated) and stub templates for steps 5-8
    (Copilot Chat-authored). Steps 1-4 are deterministic; steps 5-8 are
    meant to be manually refined.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "user-story.md": generate_user_story_md(req_set),
        "requirements.md": generate_requirements_md(req_set, clarifications),
        "architecture.md": generate_architecture_md(req_set),
        "design-review.md": generate_design_review_md(req_set),
        "impl-plan.md": generate_impl_plan_md(req_set),
        "code-review.md": generate_code_review_md(req_set),
        "verification-report.md": generate_verification_report_md(req_set),
        "CHANGELOG.md": generate_changelog_md(req_set),
        "PR.md": generate_pr_md(req_set),
    }

    # M4: fail fast — validate every artifact cites only known IDs *before*
    # any file is written, so a traceability violation never lands on disk.
    for filename, content in artifacts.items():
        assert_traceable(content, req_set)

    written: List[Path] = []
    for filename, content in artifacts.items():
        path = out / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)

    return written

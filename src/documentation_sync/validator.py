"""Validation logic for parsed Jira stories and generated requirement sets."""
from __future__ import annotations

from typing import List

from .models import JiraStory, RequirementSet


class ValidationError(Exception):
    """Raised when a story or requirement set fails validation."""


def validate_story(story: JiraStory) -> List[str]:
    """Return a list of validation issues (empty list means valid)."""
    issues: List[str] = []

    if not story.key or not story.key.strip():
        issues.append("Story key is required.")
    if not story.summary or not story.summary.strip():
        issues.append("Story summary is required.")
    if not story.description or not story.description.strip():
        issues.append("Story description is required.")
    if not story.acceptance_criteria:
        issues.append(
            "Story has no acceptance criteria; at least one is required for requirement generation."
        )

    return issues


def ensure_valid_story(story: JiraStory) -> None:
    """Raise ValidationError if the story is invalid."""
    issues = validate_story(story)
    if issues:
        raise ValidationError(
            "Story failed validation: " + "; ".join(issues)
        )


def validate_requirement_set(req_set: RequirementSet) -> List[str]:
    """Validate that a requirement set has unique, well-formed traceability IDs."""
    issues: List[str] = []
    seen_ids = set()

    if not req_set.requirements:
        issues.append("Requirement set contains no requirements.")

    for req in req_set.requirements:
        if req.req_id in seen_ids:
            issues.append(f"Duplicate requirement ID detected: {req.req_id}")
        seen_ids.add(req.req_id)

        if req.category not in ("US", "FR", "NFR"):
            issues.append(
                f"Requirement {req.req_id} has invalid category '{req.category}'."
            )
        if not req.text or not req.text.strip():
            issues.append(f"Requirement {req.req_id} has empty text.")

    return issues


def ensure_valid_requirement_set(req_set: RequirementSet) -> None:
    issues = validate_requirement_set(req_set)
    if issues:
        raise ValidationError(
            "Requirement set failed validation: " + "; ".join(issues)
        )

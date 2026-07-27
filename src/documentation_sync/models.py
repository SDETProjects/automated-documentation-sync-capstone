"""Data models for Jira stories and generated requirement sets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JiraStory:
    """A parsed Jira-style user story."""

    key: str
    summary: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    priority: Optional[str] = None
    story_points: Optional[int] = None
    reporter: Optional[str] = None
    assignee: Optional[str] = None


@dataclass
class Requirement:
    """A single traceable requirement derived from a story."""

    req_id: str
    category: str
    text: str
    source_key: str


@dataclass
class RequirementSet:
    """The full set of requirements generated for one story."""

    story: JiraStory
    requirements: List[Requirement] = field(default_factory=list)

    def by_category(self, category: str) -> List[Requirement]:
        """Return requirements filtered by category (US, FR, or NFR)."""
        return [r for r in self.requirements if r.category == category]


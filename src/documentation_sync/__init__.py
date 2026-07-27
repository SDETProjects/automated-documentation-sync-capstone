"""Automated Documentation Sync package.

Parses a Jira-style story, validates it, and generates SDLC documentation
artifacts (requirements, architecture, design review, implementation plan,
code review, test evidence, and PR description) with full traceability.
"""
from .models import JiraStory, Requirement, RequirementSet

__all__ = [
    "JiraStory",
    "Requirement",
    "RequirementSet",
]

__version__ = "0.1.0"

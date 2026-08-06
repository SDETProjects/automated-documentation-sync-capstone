"""Quality checks for generated SDLC documentation artifacts.

Verifies the *output* documents rather than the code that produced them:
required sections are present, heading levels are consistent, and
traceability IDs survive from requirements.md into every downstream artifact.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

TRACE_ID_PATTERN = re.compile(r"\b(?:US|FR|NFR)-\d+\b")

REQUIRED_SECTIONS: Dict[str, List[str]] = {
    "requirements.md": [
        "Story Summary",
        "Description",
        "Traceability Matrix",
        "Clarifications",
    ],
    "architecture.md": ["Overview", "Components", "Requirements Addressed"],
    "design-review.md": ["Design Summary", "Risks", "Review Outcome"],
    "impl-plan.md": ["Steps", "Test Strategy"],
    "code-review.md": ["Scope", "Findings", "Outcome"],
    "verification-report.md": [
        "Test Execution Summary",
        "Integration Verification",
        "Traceability Verification",
        "Artifact Quality Check",
        "Outcome",
    ],
    "CHANGELOG.md": ["Overview", "Changes", "Known Limitations"],
    "PR.md": ["Summary", "Traceability", "Verification"],
}

# Artifacts that must cite at least one requirement ID from requirements.md.
# Steps 1-4 are generated; steps 5-8 are Copilot Chat-authored but still cite traceability IDs.
TRACEABILITY_REQUIRED = [
    "architecture.md",
    "impl-plan.md",
    "code-review.md",
    "verification-report.md",
    "PR.md",
]


@dataclass
class DocIssue:
    filename: str
    message: str

    def __str__(self) -> str:
        return f"{self.filename}: {self.message}"


@dataclass
class DocQualityReport:
    issues: List[DocIssue] = field(default_factory=list)
    checked: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def extract_trace_ids(text: str) -> Set[str]:
    return set(TRACE_ID_PATTERN.findall(text))


def _headings(text: str) -> List[str]:
    return [line for line in text.splitlines() if line.startswith("#")]


def check_document(filename: str, text: str) -> List[DocIssue]:
    """Validate a single artifact's structure and required sections."""
    issues: List[DocIssue] = []

    if not text.strip():
        return [DocIssue(filename, "file is empty")]

    headings = _headings(text)
    titles = [h for h in headings if h.startswith("# ")]
    if not titles:
        issues.append(DocIssue(filename, "missing level-1 title (`# ...`)"))
    elif not text.lstrip().startswith("# "):
        issues.append(DocIssue(filename, "level-1 title must be the first line"))

    for heading in headings:
        level = len(heading) - len(heading.lstrip("#"))
        if level > 2:
            issues.append(
                DocIssue(filename, f"heading deeper than level 2 not allowed: {heading!r}")
            )

    section_titles = {h.lstrip("# ").strip() for h in headings if h.startswith("## ")}
    for required in REQUIRED_SECTIONS.get(filename, []):
        if required not in section_titles:
            issues.append(DocIssue(filename, f"missing required section '## {required}'"))

    return issues


def check_traceability(artifacts: Dict[str, str]) -> List[DocIssue]:
    """Ensure downstream artifacts cite IDs that requirements.md actually defines."""
    issues: List[DocIssue] = []
    requirements = artifacts.get("requirements.md")
    if requirements is None:
        return [DocIssue("requirements.md", "missing; cannot verify traceability")]

    known = extract_trace_ids(requirements)
    if not known:
        issues.append(DocIssue("requirements.md", "defines no traceability IDs"))
        return issues

    for filename in TRACEABILITY_REQUIRED:
        text = artifacts.get(filename)
        if text is None:
            continue
        cited = extract_trace_ids(text)
        if not cited:
            issues.append(DocIssue(filename, "cites no traceability IDs"))
            continue
        unknown = sorted(cited - known)
        if unknown:
            issues.append(
                DocIssue(
                    filename,
                    f"cites IDs absent from requirements.md: {', '.join(unknown)}",
                )
            )

    return issues


def check_story_parity(story, requirements_text: str) -> List[DocIssue]:
    """Ensure requirements.md covers exactly the story's acceptance criteria.

    Artifact prose may be refined by hand (that is the Copilot Chat workflow);
    the requirement *IDs* may not drift from the source story.
    """
    issues: List[DocIssue] = []
    cited = extract_trace_ids(requirements_text)

    expected_fr = {f"FR-{i}" for i in range(1, len(story.acceptance_criteria) + 1)}
    actual_fr = {i for i in cited if i.startswith("FR-")}

    for missing in sorted(expected_fr - actual_fr):
        issues.append(
            DocIssue("requirements.md", f"{missing} missing; story defines that criterion")
        )
    for extra in sorted(actual_fr - expected_fr):
        issues.append(
            DocIssue("requirements.md", f"{extra} has no matching acceptance criterion in the story")
        )
    if "US-1" not in cited:
        issues.append(DocIssue("requirements.md", "US-1 missing"))
    if story.key not in requirements_text:
        issues.append(DocIssue("requirements.md", f"does not reference story key {story.key}"))

    return issues


def validate_artifacts(
    output_dir: str | Path = ".", story_path: str | Path | None = None
) -> DocQualityReport:
    """Validate every known artifact present in output_dir.

    When story_path is given, additionally verify requirement-ID parity
    between the source story and requirements.md.
    """
    out = Path(output_dir)
    report = DocQualityReport()
    artifacts: Dict[str, str] = {}

    for filename in REQUIRED_SECTIONS:
        path = out / filename
        if not path.exists():
            report.issues.append(DocIssue(filename, "expected artifact not found"))
            continue
        text = path.read_text(encoding="utf-8")
        artifacts[filename] = text
        report.checked.append(filename)
        report.issues.extend(check_document(filename, text))

    report.issues.extend(check_traceability(artifacts))

    if story_path is not None and "requirements.md" in artifacts:
        from .parser import load_story

        story = load_story(story_path)
        report.issues.extend(check_story_parity(story, artifacts["requirements.md"]))

    return report


def main(argv: List[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="docsync-verify",
        description="Verify generated SDLC documentation artifacts.",
    )
    parser.add_argument("output_dir", nargs="?", default=".")
    parser.add_argument(
        "--story",
        help="Source story file; enables requirement-ID parity checking.",
    )
    args = parser.parse_args(argv)

    report = validate_artifacts(args.output_dir, args.story)

    if report.ok:
        suffix = " + story parity" if args.story else ""
        print(f"Document quality OK ({len(report.checked)} artifacts checked{suffix}).")
        return 0

    print(f"Document quality FAILED ({len(report.issues)} issue(s)):", file=sys.stderr)
    for issue in report.issues:
        print(f"  - {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

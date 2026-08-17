"""Checkpoint / resume support for the phased generation pipeline (M1).

Provides :class:`PhaseCheckpoint` to serialise a :class:`PhasedRunReport`
after every phase, and a small helper to roll back artifacts written during
a failed phase. The CLI uses :func:`load_checkpoint` to implement
``--resume-from-phase``.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import JiraStory, Requirement, RequirementSet

if TYPE_CHECKING:
    from .phased_generator import PhaseResult, PhasedRunReport


CHECKPOINT_FILENAME = ".docsync_checkpoint.json"


def _requirement_to_dict(req: Requirement) -> Dict[str, Any]:
    return {
        "req_id": req.req_id,
        "category": req.category,
        "text": req.text,
        "source_key": req.source_key,
    }


def _requirement_set_to_dict(rs: RequirementSet) -> Dict[str, Any]:
    return {
        "story": {
            "key": rs.story.key,
            "summary": rs.story.summary,
            "description": rs.story.description,
            "acceptance_criteria": rs.story.acceptance_criteria,
            "labels": rs.story.labels,
            "priority": rs.story.priority,
            "story_points": rs.story.story_points,
            "reporter": rs.story.reporter,
            "assignee": rs.story.assignee,
        },
        "requirements": [_requirement_to_dict(r) for r in rs.requirements],
    }


def _requirement_set_from_dict(data: Dict[str, Any]) -> RequirementSet:
    story_data = data["story"]
    story = JiraStory(
        key=story_data["key"],
        summary=story_data["summary"],
        description=story_data["description"],
        acceptance_criteria=story_data.get("acceptance_criteria", []),
        labels=story_data.get("labels", []),
        priority=story_data.get("priority"),
        story_points=story_data.get("story_points"),
        reporter=story_data.get("reporter"),
        assignee=story_data.get("assignee"),
    )
    requirements = [
        Requirement(
            req_id=r["req_id"],
            category=r["category"],
            text=r["text"],
            source_key=r["source_key"],
        )
        for r in data["requirements"]
    ]
    return RequirementSet(story=story, requirements=requirements)


def _phase_result_to_dict(pr: "PhaseResult") -> Dict[str, Any]:
    return {
        "phase": pr.phase,
        "artifact_path": str(pr.artifact_path),
        "approved": pr.approved,
    }


def _phase_result_from_dict(data: Dict[str, Any]) -> "PhaseResult":
    from .phased_generator import PhaseResult
    return PhaseResult(
        phase=data["phase"],
        artifact_path=Path(data["artifact_path"]),
        approved=data.get("approved", True),
    )


class PhaseCheckpoint:
    """Serialises / deserialises a PhasedRunReport to a JSON file.

    The checkpoint is written atomically (write to .tmp then rename) so
    partially-written files never corrupt the resume state.
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.path = Path(output_dir) / CHECKPOINT_FILENAME

    def save(self, report: PhasedRunReport) -> None:
        """Persist *report* to the checkpoint file."""
        payload = {
            "req_set": _requirement_set_to_dict(report.req_set),
            "results": [_phase_result_to_dict(r) for r in report.results],
            "clarifications": report.clarifications,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def load(self) -> Optional["PhasedRunReport"]:
        """Load a checkpoint, or return None if no valid checkpoint exists."""
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        try:
            req_set = _requirement_set_from_dict(data["req_set"])
            results = [_phase_result_from_dict(r) for r in data.get("results", [])]
            clarifications = data.get("clarifications", {})
            from .phased_generator import PhasedRunReport
            return PhasedRunReport(
                req_set=req_set, results=results, clarifications=clarifications
            )
        except (KeyError, TypeError):
            return None

    def delete(self) -> None:
        """Remove the checkpoint file (called on successful completion)."""
        if self.path.exists():
            self.path.unlink()


def rollback_artifacts(report: "PhasedRunReport", keep_phases: List[str]) -> None:
    """Delete artifact files for phases not in *keep_phases*.

    Used when a phase fails and we want to undo its artifacts before
    resuming or aborting.
    """
    keep = set(keep_phases)
    for result in report.results:
        if result.phase not in keep:
            path = result.artifact_path
            if path.exists():
                path.unlink(missing_ok=True)


def load_checkpoint(output_dir: str | Path) -> Optional["PhasedRunReport"]:
    """Convenience helper for CLI resume logic."""
    return PhaseCheckpoint(output_dir).load()


def checkpoint_after_phase(
    report: "PhasedRunReport", output_dir: str | Path
) -> None:
    """Hook called by run_phased_generation after each successful phase."""
    PhaseCheckpoint(output_dir).save(report)
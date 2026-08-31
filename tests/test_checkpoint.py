"""Tests for checkpoint module."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from src.documentation_sync.checkpoint import (
    PhaseCheckpoint,
    checkpoint_after_phase,
    load_checkpoint,
    rollback_artifacts,
)
from src.documentation_sync.models import JiraStory, Requirement, RequirementSet
from src.documentation_sync.phased_generator import PhaseResult, PhasedRunReport


@pytest.fixture
def sample_story():
    return JiraStory(
        key="PROJ-123",
        summary="Test story",
        description="Test description",
        acceptance_criteria=["AC1", "AC2"],
        labels=["bug", "urgent"],
        priority="High",
        story_points=5,
        reporter="alice@example.com",
        assignee="bob@example.com",
    )


@pytest.fixture
def sample_requirement_set(sample_story):
    return RequirementSet(
        story=sample_story,
        requirements=[
            Requirement(
                req_id="US-1",
                category="user_story",
                text="As a user, I want...",
                source_key="PROJ-123",
            ),
            Requirement(
                req_id="FR-1",
                category="functional",
                text="System shall parse input",
                source_key="PROJ-123",
            ),
        ],
    )


@pytest.fixture
def sample_phased_report(sample_requirement_set):
    return PhasedRunReport(
        req_set=sample_requirement_set,
        results=[
            PhaseResult(
                phase="requirements",
                artifact_path=Path("./requirements.md"),
                approved=True,
            ),
            PhaseResult(
                phase="architecture",
                artifact_path=Path("./architecture.md"),
                approved=False,
            ),
        ],
        clarifications={"q1": "answer1"},
    )


class TestPhaseCheckpoint:
    def test_save_and_load(self, sample_phased_report, tmp_path):
        """Test saving and loading a checkpoint."""
        checkpoint = PhaseCheckpoint(tmp_path)
        checkpoint.save(sample_phased_report)
        
        loaded = checkpoint.load()
        assert loaded is not None
        assert loaded.req_set.story.key == "PROJ-123"
        assert len(loaded.results) == 2
        assert loaded.results[0].phase == "requirements"
        assert loaded.results[0].approved is True
        assert loaded.results[1].approved is False
        assert loaded.clarifications == {"q1": "answer1"}

    def test_load_nonexistent_returns_none(self, tmp_path):
        """Test that loading a nonexistent checkpoint returns None."""
        checkpoint = PhaseCheckpoint(tmp_path)
        assert checkpoint.load() is None

    def test_load_corrupted_json_returns_none(self, tmp_path):
        """Test that loading corrupted JSON returns None."""
        checkpoint_file = tmp_path / ".docsync_checkpoint.json"
        checkpoint_file.write_text("{ invalid json }", encoding="utf-8")
        
        checkpoint = PhaseCheckpoint(tmp_path)
        assert checkpoint.load() is None

    def test_load_missing_required_fields_returns_none(self, tmp_path):
        """Test that loading JSON missing required fields returns None."""
        checkpoint_file = tmp_path / ".docsync_checkpoint.json"
        checkpoint_file.write_text(json.dumps({"incomplete": "data"}), encoding="utf-8")
        
        checkpoint = PhaseCheckpoint(tmp_path)
        assert checkpoint.load() is None

    def test_delete_removes_checkpoint_file(self, sample_phased_report, tmp_path):
        """Test that delete() removes the checkpoint file."""
        checkpoint = PhaseCheckpoint(tmp_path)
        checkpoint.save(sample_phased_report)
        
        assert checkpoint.path.exists()
        checkpoint.delete()
        assert not checkpoint.path.exists()

    def test_delete_on_nonexistent_file(self, tmp_path):
        """Test that delete() on nonexistent file doesn't raise error."""
        checkpoint = PhaseCheckpoint(tmp_path)
        checkpoint.delete()  # Should not raise

    def test_atomic_write(self, sample_phased_report, tmp_path):
        """Test that checkpoint write is atomic."""
        checkpoint = PhaseCheckpoint(tmp_path)
        checkpoint.save(sample_phased_report)
        
        # Verify .tmp file is cleaned up
        tmp_file = tmp_path / ".docsync_checkpoint.tmp"
        assert not tmp_file.exists()
        
        # Verify .json file exists
        assert checkpoint.path.exists()

    def test_preservation_of_optional_fields(self, tmp_path):
        """Test that optional story fields are preserved."""
        story = JiraStory(
            key="PROJ-456",
            summary="Story with all fields",
            description="Full description",
            acceptance_criteria=["AC1"],
            labels=["label1"],
            priority="Medium",
            story_points=3,
            reporter="reporter@example.com",
            assignee="assignee@example.com",
        )
        req_set = RequirementSet(story=story, requirements=[])
        report = PhasedRunReport(
            req_set=req_set, results=[], clarifications={}
        )
        
        checkpoint = PhaseCheckpoint(tmp_path)
        checkpoint.save(report)
        loaded = checkpoint.load()
        
        assert loaded.req_set.story.labels == ["label1"]
        assert loaded.req_set.story.priority == "Medium"
        assert loaded.req_set.story.story_points == 3
        assert loaded.req_set.story.reporter == "reporter@example.com"
        assert loaded.req_set.story.assignee == "assignee@example.com"


class TestRollbackArtifacts:
    def test_rollback_removes_unfinished_artifacts(self, sample_phased_report):
        """Test that rollback deletes artifacts for phases not in keep list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create artifact files
            req_file = tmpdir_path / "requirements.md"
            arch_file = tmpdir_path / "architecture.md"
            design_file = tmpdir_path / "design-review.md"
            
            req_file.touch()
            arch_file.touch()
            design_file.touch()
            
            # Create report with different artifact paths
            report = PhasedRunReport(
                req_set=sample_phased_report.req_set,
                results=[
                    PhaseResult(phase="requirements", artifact_path=req_file, approved=True),
                    PhaseResult(phase="architecture", artifact_path=arch_file, approved=True),
                    PhaseResult(phase="design-review", artifact_path=design_file, approved=False),
                ],
                clarifications={},
            )
            
            # Keep only requirements
            rollback_artifacts(report, ["requirements"])
            
            assert req_file.exists()
            assert not arch_file.exists()
            assert not design_file.exists()

    def test_rollback_handles_missing_files(self, sample_phased_report):
        """Test that rollback doesn't fail if artifact files are missing."""
        report = PhasedRunReport(
            req_set=sample_phased_report.req_set,
            results=[
                PhaseResult(
                    phase="requirements",
                    artifact_path=Path("/nonexistent/file.md"),
                    approved=True,
                ),
            ],
            clarifications={},
        )
        
        # Should not raise
        rollback_artifacts(report, [])


class TestCheckpointHelpers:
    def test_load_checkpoint_returns_none_if_no_checkpoint(self, tmp_path):
        """Test load_checkpoint convenience function."""
        result = load_checkpoint(tmp_path)
        assert result is None

    def test_load_checkpoint_delegates_to_phase_checkpoint(self, sample_phased_report, tmp_path):
        """Test that load_checkpoint uses PhaseCheckpoint.load()."""
        checkpoint = PhaseCheckpoint(tmp_path)
        checkpoint.save(sample_phased_report)
        
        loaded = load_checkpoint(tmp_path)
        assert loaded is not None
        assert loaded.req_set.story.key == "PROJ-123"

    def test_checkpoint_after_phase_saves(self, sample_phased_report, tmp_path):
        """Test checkpoint_after_phase hook."""
        checkpoint_after_phase(sample_phased_report, tmp_path)
        
        # Verify it was saved
        checkpoint = PhaseCheckpoint(tmp_path)
        loaded = checkpoint.load()
        assert loaded is not None
        assert loaded.req_set.story.key == "PROJ-123"

"""Tests for documentation_sync.phased_generator."""
from documentation_sync.models import JiraStory
from documentation_sync.phased_generator import PhasedRunReport, run_phased_generation


def _story(**overrides):
    defaults = dict(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z"],
        labels=["performance"],
    )
    defaults.update(overrides)
    return JiraStory(**defaults)


def test_run_phased_generation_non_interactive_writes_all_artifacts(tmp_path):
    report = run_phased_generation(
        _story(), output_dir=str(tmp_path), non_interactive=True
    )

    assert isinstance(report, PhasedRunReport)
    phases = [r.phase for r in report.results]
    assert phases == ["requirements", "architecture", "design-review", "impl-plan", "pr"]

    for result in report.results:
        assert result.artifact_path.exists()
        assert result.artifact_path.read_text(encoding="utf-8").strip()


def test_run_phased_generation_stops_when_user_rejects_a_gate(tmp_path):
    # First input_func call answers the single clarifying question, the
    # second call (the y/n gate after Phase 1) rejects continuation.
    responses = iter(["An answer.", "n"])

    report = run_phased_generation(
        _story(),
        output_dir=str(tmp_path),
        input_func=lambda _: next(responses),
        non_interactive=False,
    )

    phases = [r.phase for r in report.results]
    assert phases == ["requirements"]
    assert (tmp_path / "requirements.md").exists()
    assert not (tmp_path / "architecture.md").exists()


def test_run_phased_generation_uses_provided_llm_call(tmp_path):
    calls = []

    def fake_llm(prompt: str) -> str:
        calls.append(prompt)
        return "Only one question?"

    report = run_phased_generation(
        _story(),
        output_dir=str(tmp_path),
        llm_call=fake_llm,
        non_interactive=True,
    )

    assert calls  # the LLM callable was actually invoked
    assert report.results[0].phase == "requirements"

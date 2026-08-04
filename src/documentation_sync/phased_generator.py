"""Phased documentation generation with interactive approval gates.

Phase 1 (Requirements): clarify ambiguities with the user, then lock in
    requirements.md.
Phase 2 (Architecture): generate architecture.md from the locked
    requirements, then pause for design review approval.
Phase 3 (Design Review): generate design-review.md, then pause for
    approval before implementation planning begins.
Phase 4 (Implementation): generate impl-plan.md, PR.md, and (via the
    existing test suite) verification evidence.

Each phase writes its artifact to disk immediately so a partially-completed
run still leaves reviewable output behind.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .generator import (
    build_requirement_set,
    generate_architecture_md,
    generate_design_review_md,
    generate_impl_plan_md,
    generate_pr_md,
    generate_requirements_md,
)
from .llm_orchestrator import (
    LLMCallable,
    generate_clarifying_questions,
    incorporate_feedback,
    wait_for_user_input,
)
from .models import JiraStory, RequirementSet
from .validator import ensure_valid_story


@dataclass
class PhaseResult:
    """Record of one phase's output path and approval status."""

    phase: str
    artifact_path: Path
    approved: bool = True


@dataclass
class PhasedRunReport:
    """Full record of a phased run, for evidence/PR purposes."""

    req_set: RequirementSet
    results: List[PhaseResult] = field(default_factory=list)
    clarifications: Dict[str, str] = field(default_factory=dict)


def _confirm(prompt: str, input_func: Callable[[str], str] = input) -> bool:
    """Interactive CLI pause point requiring y/n approval to proceed."""
    answer = input_func(f"{prompt} [y/N] ").strip().lower()
    return answer in ("y", "yes")


def run_phased_generation(
    story: JiraStory,
    output_dir: str = ".",
    llm_call: Optional[LLMCallable] = None,
    input_func: Callable[[str], str] = input,
    non_interactive: bool = False,
) -> PhasedRunReport:
    """Run the four-phase generation flow with pauses between phases.

    If `non_interactive` is True, all pauses are auto-approved (useful for
    CI/tests); otherwise each phase boundary asks for explicit confirmation
    via `input_func` before continuing.
    """
    ensure_valid_story(story)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = PhasedRunReport(req_set=build_requirement_set(story))

    # Phase 1: Requirements -- clarify, then lock in.
    questions = generate_clarifying_questions(story, llm_call=llm_call)
    if non_interactive:
        answers = {q: "Auto-approved (non-interactive run)." for q in questions}
    else:
        print("\n=== Phase 1: Requirements ===")
        answers = wait_for_user_input(questions, input_func=input_func)
    enriched = incorporate_feedback(story, answers)
    report.clarifications = enriched.clarifications

    req_path = out / "requirements.md"
    req_path.write_text(
        generate_requirements_md(report.req_set, enriched.clarifications), encoding="utf-8"
    )
    report.results.append(PhaseResult("requirements", req_path))

    if not non_interactive and not _confirm(
        "Requirements locked in. Proceed to architecture?", input_func
    ):
        return report

    # Phase 2: Architecture.
    arch_path = out / "architecture.md"
    arch_path.write_text(generate_architecture_md(report.req_set), encoding="utf-8")
    report.results.append(PhaseResult("architecture", arch_path))

    if not non_interactive and not _confirm(
        "Architecture drafted. Proceed to design review?", input_func
    ):
        return report

    # Phase 3: Design Review.
    design_path = out / "design-review.md"
    design_path.write_text(generate_design_review_md(report.req_set), encoding="utf-8")
    report.results.append(PhaseResult("design-review", design_path))

    if not non_interactive and not _confirm(
        "Design review recorded. Proceed to implementation planning?", input_func
    ):
        return report

    # Phase 4: Implementation (impl-plan.md + PR.md).
    impl_path = out / "impl-plan.md"
    impl_path.write_text(generate_impl_plan_md(report.req_set), encoding="utf-8")
    report.results.append(PhaseResult("impl-plan", impl_path))

    pr_path = out / "PR.md"
    pr_path.write_text(generate_pr_md(report.req_set), encoding="utf-8")
    report.results.append(PhaseResult("pr", pr_path))

    return report

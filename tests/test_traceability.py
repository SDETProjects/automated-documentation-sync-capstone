"""Tests for M4 — fail-fast traceability enforcement in generator.py."""
from __future__ import annotations

import pytest

from documentation_sync.generator import (
    TraceabilityError,
    assert_traceable,
    build_requirement_set,
    extract_trace_ids,
    write_all_artifacts,
)
from documentation_sync.models import JiraStory


def _story() -> JiraStory:
    return JiraStory(
        key="ABC-1",
        summary="Do the thing",
        description="As a user I want the thing.",
        acceptance_criteria=["Given X, when Y, then Z"],
    )


def test_extract_trace_ids_finds_all_categories():
    assert extract_trace_ids("US-1 and FR-12 plus NFR-3") == {"US-1", "FR-12", "NFR-3"}


def test_assert_traceable_passes_for_known_ids():
    req_set = build_requirement_set(_story())
    # Should not raise for known IDs.
    assert_traceable("US-1 FR-1 NFR-1", req_set)


def test_assert_traceable_raises_on_unknown_id():
    req_set = build_requirement_set(_story())
    with pytest.raises(TraceabilityError, match="FR-99"):
        assert_traceable("FR-99 is invented", req_set)


def test_assert_traceable_reports_all_unknown_ids():
    req_set = build_requirement_set(_story())
    with pytest.raises(TraceabilityError) as excinfo:
        assert_traceable("FR-99 and NFR-7", req_set)
    assert "FR-99" in str(excinfo.value)
    assert "NFR-7" in str(excinfo.value)


def test_write_all_artifacts_fails_fast_on_bad_generator(tmp_path):
    """A generator that emits a bogus ID must fail before writing any file."""
    req_set = build_requirement_set(_story())

    # Monkeypatch generate_pr_md to emit an unknown ID.
    import documentation_sync.generator as gen

    original = gen.generate_pr_md

    def bad_pr(req_set):
        content = original(req_set)
        return content.replace("US-1", "US-99")  # inject an unknown ID

    gen.generate_pr_md = bad_pr
    try:
        with pytest.raises(TraceabilityError, match="US-99"):
            write_all_artifacts(req_set, tmp_path)
    finally:
        gen.generate_pr_md = original


def test_known_ids_are_exactly_the_requirements():
    req_set = build_requirement_set(_story())
    ids = {r.req_id for r in req_set.requirements}
    assert ids == {"US-1", "FR-1", "NFR-1"}

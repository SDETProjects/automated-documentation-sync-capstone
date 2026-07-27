"""Command-line interface for the Automated Documentation Sync engine."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import build_requirement_set, write_all_artifacts
from .input_handler import IntegrationUnavailableError, load_story_from_any_source
from .parser import StoryNotFoundError, StoryParseError
from .phased_generator import run_phased_generation
from .validator import ValidationError, ensure_valid_requirement_set, ensure_valid_story


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docsync",
        description="Convert a Jira/Confluence story into synced SDLC documentation artifacts.",
    )
    parser.add_argument(
        "story_input",
        help=(
            "Path to a story file (.json/.md), a Jira/Confluence URL, or "
            "raw pasted story text (wrap in quotes)."
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory to write generated artifacts into (default: current directory)",
    )
    parser.add_argument(
        "--jira-token",
        default=None,
        help=(
            "Jira/Confluence API token for URL ingestion. If omitted, falls "
            "back to the JIRA_API_TOKEN environment variable, then to asking "
            "you to paste the story manually if the URL cannot be fetched."
        ),
    )
    parser.add_argument(
        "--phased",
        action="store_true",
        help=(
            "Run the interactive phased flow (clarifying questions + "
            "approval gates between requirements/architecture/design-review/"
            "implementation) instead of generating all artifacts in one shot."
        ),
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="With --phased, auto-approve every pause point (useful for CI).",
    )
    parser.add_argument(
        "--llm",
        choices=["claude", "copilot"],
        default=None,
        help=(
            "LLM provider for interactive clarifying questions in --phased "
            "mode. If omitted, falls back to the offline heuristic "
            "question generator."
        ),
    )
    return parser


def _load_story_with_fallback(story_input: str, jira_token: str | None):
    """Load a story from file/URL/text; on integration failure, prompt for paste."""
    import os

    auth_config = {"jira_token": jira_token or os.environ.get("JIRA_API_TOKEN")}
    try:
        return load_story_from_any_source(story_input, auth_config=auth_config)
    except IntegrationUnavailableError as exc:
        print(f"WARNING: {exc}", file=sys.stderr)
        print(
            "Jira/Confluence integration is not available. Please paste the "
            "full story text below, then press Enter on an empty line to finish:",
            file=sys.stderr,
        )
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        pasted = "\n".join(lines)
        return load_story_from_any_source(pasted)


def run(
    story_input: str,
    output_dir: str = ".",
    jira_token: str | None = None,
    phased: bool = False,
    non_interactive: bool = False,
    llm: str | None = None,
) -> int:
    try:
        story = _load_story_with_fallback(story_input, jira_token)
        ensure_valid_story(story)

        if phased:
            llm_call = None
            if llm:
                from .providers import LLMManager

                try:
                    llm_call = LLMManager(preferred=llm).as_llm_call()
                    print(f"LLM provider: {LLMManager(preferred=llm).get_adapter().name()}")
                except RuntimeError as exc:
                    print(f"WARNING: {exc}", file=sys.stderr)
                    print(
                        "Continuing with offline heuristic questions.",
                        file=sys.stderr,
                    )

            report = run_phased_generation(
                story,
                output_dir=output_dir,
                non_interactive=non_interactive,
                llm_call=llm_call,
            )
            print(
                f"Phased run complete: {len(report.results)} artifact(s) in "
                f"{Path(output_dir).resolve()}:"
            )
            for result in report.results:
                print(f"  - [{result.phase}] {result.artifact_path.name}")
            return 0

        req_set = build_requirement_set(story)
        ensure_valid_requirement_set(req_set)
        written = write_all_artifacts(req_set, output_dir)
    except StoryNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (StoryParseError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {len(written)} artifact(s) in {Path(output_dir).resolve()}:")
    for path in written:
        print(f"  - {path.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    return run(
        args.story_input,
        args.output_dir,
        jira_token=args.jira_token,
        phased=args.phased,
        non_interactive=args.non_interactive,
        llm=args.llm,
    )


if __name__ == "__main__":
    raise SystemExit(main())

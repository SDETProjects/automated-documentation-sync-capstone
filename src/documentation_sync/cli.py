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
        epilog=(
            "JIRA INTEGRATION:\n"
            "  To fetch stories directly from Jira URLs, provide an API token via:\n"
            "    --jira-token <your-token>\n"
            "    JIRA_API_TOKEN environment variable\n"
            "    JIRA_TOKEN environment variable\n"
            "  Example: docsync 'https://jira.company.com/browse/PROJ-123' "
            "--jira-token abc123xyz\n"
            "  Or: export JIRA_API_TOKEN=abc123xyz && docsync "
            "'https://jira.company.com/browse/PROJ-123'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        nargs="?",
        const=None,
        help=(
            "Jira/Confluence API token for URL ingestion. If omitted, falls "
            "back to the JIRA_API_TOKEN or JIRA_TOKEN environment variable."
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

    auth_config = {"jira_token": jira_token or os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")}
    try:
        return load_story_from_any_source(story_input, auth_config=auth_config)
    except IntegrationUnavailableError as exc:
        print(f"WARNING: {exc}", file=sys.stderr)
        print(
            "\nTo use Jira integration, set your API token:\n"
            "  export JIRA_API_TOKEN='your-token'  # or JIRA_TOKEN\n"
            "  docsync <url> --phased --jira-token 'your-token'\n"
            "\nOtherwise, paste the story text below (press Enter on empty line to finish):",
            file=sys.stderr,
        )
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                break
            lines.append(line)
        pasted = "\n".join(lines)
        if not pasted.strip():
            print("ERROR: No story text was provided.", file=sys.stderr)
            raise SystemExit(1)
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
    # Windows consoles default to cp1252, which cannot encode characters that
    # routinely appear in Jira content (e.g. "50 → 0.5") and would crash on print.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

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

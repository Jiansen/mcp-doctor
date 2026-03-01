"""CLI entry point for mcp-doctor."""

from __future__ import annotations

import argparse
import sys

from mcp_doctor import __version__


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="mcp-doctor",
        description="Check and improve the contract quality of any MCP server.",
    )
    parser.add_argument("--version", action="version", version=f"mcp-doctor {__version__}")

    sub = parser.add_subparsers(dest="command")

    check_p = sub.add_parser("check", help="Run contract quality checks on an MCP server")
    check_p.add_argument("path", help="Path to the MCP server repository directory")
    check_p.add_argument(
        "--format",
        choices=["terminal", "json", "markdown"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    check_p.add_argument(
        "--mode",
        choices=["rule", "ai"],
        default="rule",
        help="Evaluation mode: rule (deterministic, default) or ai (LLM-enhanced)",
    )
    check_p.add_argument(
        "--model",
        default=None,
        help="LLM model name for AI mode (default: $MCP_DOCTOR_MODEL or gpt-4o-mini)",
    )

    args = parser.parse_args(argv)

    if args.command == "check":
        _run_check(args.path, args.format, args.mode, args.model)
    else:
        parser.print_help()
        sys.exit(1)


def _run_check(path: str, fmt: str, mode: str = "rule", model: str | None = None) -> None:
    from mcp_doctor.checks import overall_grade, run_all_checks
    from mcp_doctor.loader import load_from_path
    from mcp_doctor.report import format_json, format_markdown, format_terminal

    try:
        info = load_from_path(path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    results = run_all_checks(info)
    grade = overall_grade(results)

    ai_review = None
    if mode == "ai":
        from mcp_doctor.checks.ai_review import run_ai_review

        ai_review = run_ai_review(info, results, model=model)
        if ai_review.error:
            print(f"AI review warning: {ai_review.error}", file=sys.stderr)

    formatters = {
        "terminal": format_terminal,
        "json": format_json,
        "markdown": format_markdown,
    }
    output = formatters[fmt](info, results, grade, ai_review=ai_review)
    print(output)

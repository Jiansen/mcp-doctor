"""Format check results for terminal, JSON, or Markdown output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_doctor.checks import CheckResult
    from mcp_doctor.loader import ServerInfo


def format_terminal(info: ServerInfo, results: list[CheckResult], overall: str) -> str:
    w = 52
    lines: list[str] = []
    lines.append("+" + "-" * w + "+")
    lines.append("|" + " MCP Doctor — Contract Quality Report".ljust(w) + "|")
    lines.append("+" + "=" * w + "+")
    lines.append("|" + f"  Server:  {info.name or '(unnamed)'}".ljust(w) + "|")
    lines.append("|" + f"  Version: {info.version or '(unknown)'}".ljust(w) + "|")
    lines.append("|" + f"  Tools:   {len(info.tools)}".ljust(w) + "|")
    lines.append("|" + f"  Source:  {_truncate(info.source_path, 38)}".ljust(w) + "|")
    lines.append("+" + "-" * w + "+")

    for r in results:
        label = f"  {r.dimension}:"
        grade_str = f"{r.grade} ({r.score})"
        padding = w - len(label) - len(grade_str)
        lines.append("|" + label + " " * max(padding, 1) + grade_str + "|")

    lines.append("|" + "-" * w + "|")
    label = "  Overall:"
    grade_str = f"{overall}"
    padding = w - len(label) - len(grade_str)
    lines.append("|" + label + " " * max(padding, 1) + grade_str + "|")
    lines.append("+" + "-" * w + "+")

    all_recs = []
    for r in results:
        all_recs.extend(r.recommendations)

    if all_recs:
        lines.append("")
        lines.append("Top Recommendations:")
        for i, rec in enumerate(all_recs[:5], 1):
            lines.append(f"  {i}. {rec}")

    all_findings = []
    for r in results:
        all_findings.extend(r.findings)
    if all_findings:
        lines.append("")
        lines.append("Findings:")
        for f in all_findings:
            lines.append(f"  - {f}")

    return "\n".join(lines)


def format_json(info: ServerInfo, results: list[CheckResult], overall: str) -> str:
    data = {
        "server": {
            "name": info.name,
            "version": info.version,
            "tools": len(info.tools),
            "source": info.source_path,
        },
        "overall_grade": overall,
        "overall_score": (round(sum(r.score for r in results) / len(results)) if results else 0),
        "dimensions": [
            {
                "name": r.dimension,
                "grade": r.grade,
                "score": r.score,
                "findings": r.findings,
                "recommendations": r.recommendations,
            }
            for r in results
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_markdown(info: ServerInfo, results: list[CheckResult], overall: str) -> str:
    lines: list[str] = []
    lines.append(f"# MCP Doctor Report: {info.name or '(unnamed)'}")
    lines.append("")
    lines.append(f"- **Version**: {info.version or '(unknown)'}")
    lines.append(f"- **Tools**: {len(info.tools)}")
    lines.append(f"- **Overall Grade**: **{overall}**")
    lines.append("")
    lines.append("| Dimension | Grade | Score |")
    lines.append("|-----------|-------|-------|")
    for r in results:
        lines.append(f"| {r.dimension} | {r.grade} | {r.score} |")
    lines.append("")

    all_recs = []
    for r in results:
        all_recs.extend(r.recommendations)
    if all_recs:
        lines.append("## Recommendations")
        lines.append("")
        for i, rec in enumerate(all_recs[:10], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    for r in results:
        if r.findings:
            lines.append(f"### {r.dimension}")
            lines.append("")
            for f in r.findings:
                lines.append(f"- {f}")
            lines.append("")

    return "\n".join(lines)


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return "..." + s[-(max_len - 3) :]

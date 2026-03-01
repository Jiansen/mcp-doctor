"""Format check results for terminal, JSON, or Markdown output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_doctor.checks import CheckResult
    from mcp_doctor.checks.ai_review import AIReviewResult
    from mcp_doctor.loader import ServerInfo


def format_terminal(
    info: ServerInfo,
    results: list[CheckResult],
    overall: str,
    ai_review: AIReviewResult | None = None,
) -> str:
    w = 52
    lines: list[str] = []
    lines.append("+" + "-" * w + "+")
    lines.append("|" + " MCP Doctor — Contract Quality Report".ljust(w) + "|")
    lines.append("+" + "=" * w + "+")
    lines.append("|" + f"  Server:  {info.name or '(unnamed)'}".ljust(w) + "|")
    lines.append("|" + f"  Version: {info.version or '(unknown)'}".ljust(w) + "|")
    lines.append("|" + f"  Tools:   {len(info.tools)}".ljust(w) + "|")
    lines.append("|" + f"  Source:  {_truncate(info.source_path, 38)}".ljust(w) + "|")

    mode_str = "rule-based"
    if ai_review and not ai_review.error:
        mode_str = f"ai ({ai_review.model_name})"
    lines.append("|" + f"  Mode:    {_truncate(mode_str, 38)}".ljust(w) + "|")
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

    _append_ai_section(lines, ai_review)

    return "\n".join(lines)


def format_json(
    info: ServerInfo,
    results: list[CheckResult],
    overall: str,
    ai_review: AIReviewResult | None = None,
) -> str:
    eval_meta: dict = {"mode": "rule-based"}
    if ai_review and not ai_review.error:
        eval_meta = {
            "mode": "ai",
            "model_name": ai_review.model_name,
            "model_version": ai_review.model_version,
        }

    data: dict = {
        "server": {
            "name": info.name,
            "version": info.version,
            "tools": len(info.tools),
            "source": info.source_path,
        },
        "evaluation": eval_meta,
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

    if ai_review and not ai_review.error:
        data["ai_review"] = {
            "summary": ai_review.review_summary,
            "dimension_reviews": ai_review.dimension_reviews,
        }
    elif ai_review and ai_review.error:
        data["ai_review"] = {"error": ai_review.error}

    return json.dumps(data, indent=2, ensure_ascii=False)


def format_markdown(
    info: ServerInfo,
    results: list[CheckResult],
    overall: str,
    ai_review: AIReviewResult | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"# MCP Doctor Report: {info.name or '(unnamed)'}")
    lines.append("")
    lines.append(f"- **Version**: {info.version or '(unknown)'}")
    lines.append(f"- **Tools**: {len(info.tools)}")
    lines.append(f"- **Overall Grade**: **{overall}**")

    if ai_review and not ai_review.error:
        lines.append(
            f"- **Evaluation Mode**: ai"
            f" (model: `{ai_review.model_name}`,"
            f" version: `{ai_review.model_version}`)"
        )
    else:
        lines.append("- **Evaluation Mode**: rule-based")

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

    _append_ai_section_md(lines, ai_review)

    return "\n".join(lines)


def _append_ai_section(lines: list[str], ai_review: AIReviewResult | None) -> None:
    if ai_review is None:
        return
    lines.append("")
    if ai_review.error:
        lines.append(f"AI Review: {ai_review.error}")
        return
    lines.append(f"AI Review (model: {ai_review.model_name}):")
    if ai_review.review_summary:
        lines.append(f"  Summary: {ai_review.review_summary}")
    for dim, review in ai_review.dimension_reviews.items():
        lines.append(f"  [{dim}] {review}")


def _append_ai_section_md(lines: list[str], ai_review: AIReviewResult | None) -> None:
    if ai_review is None:
        return
    if ai_review.error:
        lines.append(f"> **AI Review Error**: {ai_review.error}")
        lines.append("")
        return
    lines.append("## AI Review")
    lines.append("")
    lines.append(f"*Model: `{ai_review.model_name}` (version: `{ai_review.model_version}`)*")
    lines.append("")
    if ai_review.review_summary:
        lines.append(f"**Summary**: {ai_review.review_summary}")
        lines.append("")
    for dim, review in ai_review.dimension_reviews.items():
        lines.append(f"- **{dim}**: {review}")
    lines.append("")


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return "..." + s[-(max_len - 3) :]

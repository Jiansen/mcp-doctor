"""Check 4: Token Efficiency — Will tool responses fit an agent's context budget?"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_doctor.checks import CheckResult, score_to_grade

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo


def check_token_efficiency(info: ServerInfo) -> CheckResult:
    findings: list[str] = []
    recommendations: list[str] = []
    score = 0

    total = len(info.tools)
    if total == 0:
        findings.append("No tools found")
        return CheckResult("Token Efficiency", "D", 10, findings, recommendations)

    if total <= 8:
        score += 30
        findings.append(f"Tool count is lean ({total} tools)")
    elif total <= 15:
        score += 20
        findings.append(f"Tool count is reasonable ({total} tools)")
    elif total <= 30:
        score += 10
        findings.append(f"Tool count is high ({total} tools) — may cause tool selection confusion")
        recommendations.append(
            "Consider grouping tools into toolsets or reducing to <15 "
            "high-impact tools to improve agent tool selection accuracy"
        )
    else:
        score += 5
        findings.append(f"Tool count is very high ({total} tools) — likely causes agent confusion")
        recommendations.append(
            "Strongly recommend implementing toolsets (like GitHub MCP) "
            "to let agents load only what they need"
        )

    combined_text = info.readme_text.lower() + " " + info.description.lower()
    for t in info.tools:
        combined_text += " " + t.description.lower()

    response_format_signals = [
        "response_format",
        "concise",
        "detailed",
        "verbose",
        "format",
        "summary",
        "brief",
    ]
    has_response_format = any(s in combined_text for s in response_format_signals)
    if has_response_format:
        score += 25
        findings.append("Response format control (concise/detailed) found")
    else:
        score += 5
        recommendations.append(
            "Add a response_format parameter (concise/detailed) to data-heavy tools "
            "so agents can control response verbosity and save context"
        )

    pagination_signals = [
        "pagination",
        "paginate",
        "page_size",
        "per_page",
        "limit",
        "offset",
        "cursor",
        "next_page",
        "max_results",
    ]
    has_pagination = any(s in combined_text for s in pagination_signals)
    if has_pagination:
        score += 25
        findings.append("Pagination or result limiting supported")
    else:
        score += 5
        recommendations.append(
            "Add pagination or result limiting to tools that can return large datasets"
        )

    truncation_signals = [
        "truncat",
        "max_token",
        "max_length",
        "token_limit",
        "character_limit",
    ]
    has_truncation = any(s in combined_text for s in truncation_signals)
    if has_truncation:
        score += 20
        findings.append("Response truncation mechanism found")
    else:
        score += 10

    score = min(score, 100)
    return CheckResult("Token Efficiency", score_to_grade(score), score, findings, recommendations)

"""Check 3: Interface Quality — Are tools well-named, well-described, and well-typed?"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from mcp_doctor.checks import CheckResult, score_to_grade

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def check_interface_quality(info: ServerInfo) -> CheckResult:
    findings: list[str] = []
    recommendations: list[str] = []
    score = 0

    if not info.tools:
        findings.append("No tools found")
        return CheckResult("Interface Quality", "D", 10, findings, recommendations)

    total = len(info.tools)

    snake_count = sum(1 for t in info.tools if SNAKE_CASE_RE.match(t.name))
    if snake_count == total:
        score += 20
        findings.append("All tool names use consistent snake_case")
    elif snake_count > total * 0.5:
        score += 10
        findings.append(f"{snake_count}/{total} tools use snake_case")
        recommendations.append("Use consistent snake_case for all tool names")
    else:
        score += 5
        non_snake = [t.name for t in info.tools if not SNAKE_CASE_RE.match(t.name)]
        findings.append(f"Inconsistent naming: {non_snake[:3]}")
        recommendations.append(
            "Standardize all tool names to snake_case (e.g. get_status, not getStatus)"
        )

    prefixes = set()
    for t in info.tools:
        parts = t.name.split("_")
        if len(parts) >= 2:
            prefixes.add(parts[0])
    if len(prefixes) <= 2 and total > 1:
        score += 10
        findings.append(f"Consistent namespace prefix(es): {prefixes}")
    elif total > 3:
        score += 5
        recommendations.append(
            "Consider using a consistent prefix for tool names "
            "(e.g. db_query, db_schema, db_optimize)"
        )
    else:
        score += 8

    desc_scores: list[int] = []
    for t in info.tools:
        d = t.description
        if not d:
            desc_scores.append(0)
            continue
        s = 0
        if len(d) >= 20:
            s += 3
        if len(d) <= 500:
            s += 2
        d_lower = d.lower()
        if any(w in d_lower for w in ["returns", "return", "output"]):
            s += 2
        if any(w in d_lower for w in ["args", "param", "input", "takes"]):
            s += 1
        if any(w in d_lower for w in ["use this", "use when", "for", "helps"]):
            s += 2
        desc_scores.append(min(s, 10))

    if desc_scores:
        avg_desc = sum(desc_scores) / len(desc_scores)
        desc_pct = int(avg_desc * 10)
        score += min(desc_pct * 30 // 100, 30)
        if avg_desc >= 7:
            findings.append("Tool descriptions are detailed and agent-friendly")
        elif avg_desc >= 4:
            findings.append("Tool descriptions are adequate but could be more agent-oriented")
            recommendations.append(
                "Enhance tool descriptions: explain what each tool returns, "
                "when to use it, and any side effects"
            )
        else:
            findings.append("Tool descriptions are minimal")
            recommendations.append(
                "Rewrite tool descriptions as if explaining to a new team member: "
                "what it does, when to use it, what it returns"
            )

    tools_with_schema = sum(
        1 for t in info.tools if t.input_schema and t.input_schema.get("properties")
    )
    schema_ratio = tools_with_schema / total if total else 0
    if schema_ratio >= 0.8:
        score += 20
        findings.append(f"{tools_with_schema}/{total} tools have detailed inputSchema")
    elif schema_ratio > 0:
        score += 10
        findings.append(f"{tools_with_schema}/{total} tools have inputSchema")
        recommendations.append("Add detailed inputSchema with property descriptions to all tools")
    else:
        score += 5
        recommendations.append("Define inputSchema with typed properties for each tool")

    tools_with_output = sum(
        1
        for t in info.tools
        if t.output_schema
        and t.output_schema.get("properties")
        and not t.output_schema.get("additionalProperties", False)
    )
    if tools_with_output == total and total > 0:
        score += 20
        findings.append("All tools have well-defined outputSchema")
    elif tools_with_output > 0:
        score += 10
        findings.append(f"{tools_with_output}/{total} tools have specific outputSchema")
        recommendations.append("Tighten outputSchema: avoid additionalProperties: true")
    else:
        score += 5
        recommendations.append(
            "Define outputSchema for each tool so agents know the response structure"
        )

    score = min(score, 100)
    return CheckResult("Interface Quality", score_to_grade(score), score, findings, recommendations)

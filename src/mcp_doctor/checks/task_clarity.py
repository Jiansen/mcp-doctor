"""Check 1: Task Clarity — Is the server's purpose immediately clear?"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_doctor.checks import CheckResult, score_to_grade

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo

ACTION_VERBS = {
    "diagnose",
    "search",
    "create",
    "manage",
    "query",
    "analyze",
    "monitor",
    "generate",
    "update",
    "build",
    "deploy",
    "test",
    "review",
    "automate",
    "connect",
    "integrate",
    "sync",
    "fetch",
    "read",
    "write",
    "execute",
    "check",
    "validate",
    "verify",
    "inspect",
    "scan",
    "discover",
    "browse",
    "navigate",
    "control",
    "transform",
    "convert",
    "extract",
    "parse",
    "schedule",
    "notify",
    "alert",
    "publish",
    "submit",
    "help",
    "provide",
    "enable",
    "access",
    "retrieve",
    "send",
    "list",
    "get",
    "run",
    "find",
}

WHEN_TO_USE_SIGNALS = [
    "use this when",
    "use this to",
    "use when",
    "useful for",
    "helps you",
    "designed for",
    "built for",
    "ideal for",
    "best for",
    "run this",
]


def check_task_clarity(info: ServerInfo) -> CheckResult:
    findings: list[str] = []
    recommendations: list[str] = []
    score = 0

    desc = info.description.strip()

    if not desc:
        findings.append("No server description found")
        recommendations.append("Add a description to server.json or tool metadata")
        return CheckResult("Task Clarity", "D", 0, findings, recommendations)

    score += 25
    findings.append(f"Description present ({len(desc)} chars)")

    if len(desc) <= 200:
        score += 20
        findings.append("Description fits platform card limit (<=200 chars)")
    else:
        score += 10
        findings.append(f"Description is {len(desc)} chars (>200, will be truncated on platforms)")
        recommendations.append(
            "Shorten description to <=200 characters for platform card compatibility"
        )

    desc_lower = desc.lower()
    has_verb = any(verb in desc_lower.split() for verb in ACTION_VERBS)
    if has_verb:
        score += 20
        findings.append("Description contains action verb(s)")
    else:
        recommendations.append(
            "Start description with an action verb (e.g. 'Diagnose...', 'Search...', 'Manage...')"
        )

    has_when = any(signal in desc_lower for signal in WHEN_TO_USE_SIGNALS)
    tool_descs = " ".join(t.description.lower() for t in info.tools)
    has_when_in_tools = any(signal in tool_descs for signal in WHEN_TO_USE_SIGNALS)

    if has_when or has_when_in_tools:
        score += 20
        findings.append("'When to use' guidance found in descriptions")
    else:
        score += 5
        recommendations.append(
            "Add 'Use this when...' guidance to server or tool descriptions "
            "so agents know when to invoke your tools"
        )

    if info.has_readme and len(info.readme_text) > 100:
        score += 15
        findings.append("README with substantive content present")
    elif info.has_readme:
        score += 5
        findings.append("README present but minimal")
        recommendations.append("Expand README with use cases and examples")
    else:
        recommendations.append("Add a README.md with use cases and examples")

    score = min(score, 100)
    return CheckResult("Task Clarity", score_to_grade(score), score, findings, recommendations)

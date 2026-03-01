"""Contract quality checks for MCP servers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo

GRADES = ("A", "B", "C", "D")


@dataclass
class CheckResult:
    dimension: str
    grade: str  # A, B, C, D
    score: int  # 0-100
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def overall_grade(results: list[CheckResult]) -> str:
    if not results:
        return "D"
    avg = sum(r.score for r in results) / len(results)
    if avg >= 85:
        return "A"
    if avg >= 70:
        return "B"
    if avg >= 50:
        return "C"
    return "D"


def score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def run_all_checks(info: ServerInfo) -> list[CheckResult]:
    from mcp_doctor.checks.cross_platform import check_cross_platform
    from mcp_doctor.checks.install_friction import check_install_friction
    from mcp_doctor.checks.interface_quality import check_interface_quality
    from mcp_doctor.checks.task_clarity import check_task_clarity
    from mcp_doctor.checks.token_efficiency import check_token_efficiency
    from mcp_doctor.checks.trust_safety import check_trust_safety

    return [
        check_task_clarity(info),
        check_trust_safety(info),
        check_interface_quality(info),
        check_token_efficiency(info),
        check_install_friction(info),
        check_cross_platform(info),
    ]

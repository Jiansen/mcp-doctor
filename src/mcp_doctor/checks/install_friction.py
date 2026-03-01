"""Check 5: Install Friction — How fast can someone go from discovery to first use?"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_doctor.checks import CheckResult, score_to_grade

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo


def check_install_friction(info: ServerInfo) -> CheckResult:
    findings: list[str] = []
    recommendations: list[str] = []
    score = 0

    if info.has_server_json:
        score += 25
        findings.append("server.json present and parseable")
    else:
        findings.append("No server.json found")
        recommendations.append(
            "Create a server.json following the official MCP Registry schema "
            "— required for official Registry and consumed by all major platforms"
        )

    methods = info.install_methods
    if len(methods) >= 3:
        score += 25
        findings.append(f"Multiple install methods: {', '.join(methods)}")
    elif len(methods) >= 1:
        score += 15
        findings.append(f"Install method(s): {', '.join(methods)}")
        recommendations.append("Add more install options (Docker, Homebrew, npx) to lower friction")
    else:
        findings.append("No standard install method detected")
        recommendations.append("Add pip/npm/Docker install support")

    if info.has_remote:
        score += 25
        findings.append("Remote/hosted deployment available")
    else:
        score += 5
        recommendations.append(
            "Consider adding remote server support (streamable-http) "
            "— platforms increasingly favor zero-install hosted servers"
        )

    readme_lower = info.readme_text.lower()
    one_click_signals = [
        "one-click",
        "one click",
        "install button",
        "quick install",
        "curl ",
        "npx ",
        "pip install",
        "brew install",
        "docker run",
    ]
    has_quick = any(s in readme_lower for s in one_click_signals)
    if has_quick:
        score += 15
        findings.append("Quick install instructions found in README")
    else:
        score += 5
        recommendations.append("Add a one-liner install command at the top of your README")

    if info.has_readme and (
        "## install" in readme_lower
        or "## getting started" in readme_lower
        or "## setup" in readme_lower
        or "## usage" in readme_lower
        or "## quickstart" in readme_lower
    ):
        score += 10
        findings.append("Dedicated install/setup section in README")
    elif info.has_readme:
        score += 5
        recommendations.append("Add a dedicated '## Installation' section to README")

    score = min(score, 100)
    return CheckResult("Install Friction", score_to_grade(score), score, findings, recommendations)

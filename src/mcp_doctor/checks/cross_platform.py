"""Check 6: Cross-platform Readiness — Is metadata complete for all major distribution platforms?"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_doctor.checks import CheckResult, score_to_grade

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo


REQUIRED_SERVER_JSON_FIELDS = ["name", "description", "version", "repository"]
OPTIONAL_SERVER_JSON_FIELDS = ["packages", "remotes", "title"]
VALID_SCHEMAS = [
    "https://static.modelcontextprotocol.io/schemas/",
]


def check_cross_platform(info: ServerInfo) -> CheckResult:
    findings: list[str] = []
    recommendations: list[str] = []
    score = 0

    sj = info.server_json
    if not sj:
        findings.append("No server.json — cannot assess cross-platform readiness")
        recommendations.append("Create server.json to enable distribution on all MCP platforms")
        return CheckResult("Cross-platform Readiness", "D", 5, findings, recommendations)

    schema = sj.get("$schema", "")
    if any(schema.startswith(v) for v in VALID_SCHEMAS):
        score += 10
        findings.append("server.json uses official schema")
    else:
        score += 5
        recommendations.append(
            "Set $schema to an official MCP Registry schema URL "
            "(e.g. https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json)"
        )

    present = [f for f in REQUIRED_SERVER_JSON_FIELDS if sj.get(f)]
    missing = [f for f in REQUIRED_SERVER_JSON_FIELDS if not sj.get(f)]
    if not missing:
        score += 20
        findings.append("All required server.json fields present")
    else:
        ratio = len(present) / len(REQUIRED_SERVER_JSON_FIELDS)
        score += int(20 * ratio)
        findings.append(f"Missing server.json fields: {missing}")
        recommendations.append(f"Add missing fields to server.json: {', '.join(missing)}")

    repo = sj.get("repository", {})
    if isinstance(repo, dict) and repo.get("url"):
        score += 10
        findings.append("Repository URL present")
    else:
        recommendations.append("Add repository.url to server.json for platform discovery")

    name = sj.get("name", "")
    if "." in name and "/" in name:
        score += 15
        findings.append(f"Name uses reverse-DNS format: {name}")
    elif name:
        score += 5
        findings.append(f"Name present but not reverse-DNS: {name}")
        recommendations.append(
            "Use reverse-DNS naming (e.g. io.github.user/server) "
            "for official Registry namespace verification"
        )
    else:
        recommendations.append("Add a name field in reverse-DNS format to server.json")

    packages = sj.get("packages", [])
    if packages:
        score += 15
        registries = [p.get("registryType", "unknown") for p in packages]
        findings.append(f"Package registries: {', '.join(registries)}")
    else:
        score += 5
        recommendations.append("Add packages section to server.json with registry type and version")

    if info.has_license:
        score += 10
        findings.append("LICENSE file present")
    else:
        recommendations.append("Add a LICENSE file — required by Glama for license score")

    desc = info.description
    if desc and len(desc) <= 200:
        score += 10
        findings.append("Description fits platform card limit")
    elif desc:
        score += 5
        recommendations.append("Shorten description to <=200 chars for platform cards")

    if info.has_remote:
        score += 10
        findings.append("Remote deployment available (Smithery/Glama preferred)")
    else:
        score += 5

    score = min(score, 100)
    return CheckResult(
        "Cross-platform Readiness", score_to_grade(score), score, findings, recommendations
    )

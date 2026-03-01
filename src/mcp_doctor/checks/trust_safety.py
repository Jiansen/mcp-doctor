"""Check 2: Trust & Safety — Are side effects, permissions, and safety boundaries clear?"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_doctor.checks import CheckResult, score_to_grade

if TYPE_CHECKING:
    from mcp_doctor.loader import ServerInfo


def check_trust_safety(info: ServerInfo) -> CheckResult:
    findings: list[str] = []
    recommendations: list[str] = []
    score = 0

    if not info.tools:
        findings.append("No tools found — cannot assess trust properties")
        return CheckResult("Trust & Safety", "D", 10, findings, recommendations)

    tools_with_annotations = sum(1 for t in info.tools if t.annotations)
    total = len(info.tools)
    annotation_ratio = tools_with_annotations / total if total else 0

    if annotation_ratio >= 0.8:
        score += 35
        findings.append(f"{tools_with_annotations}/{total} tools have annotations")
    elif annotation_ratio > 0:
        score += 15
        findings.append(f"Only {tools_with_annotations}/{total} tools have annotations")
        recommendations.append("Add annotations (readOnlyHint, destructiveHint) to all tools")
    else:
        findings.append("No tool annotations found")
        recommendations.append(
            "Add tool annotations: readOnlyHint, destructiveHint, idempotentHint "
            "— agents need these to assess risk before calling"
        )

    has_readonly = any(t.annotations.get("readOnlyHint") for t in info.tools)
    has_destructive = any(t.annotations.get("destructiveHint") for t in info.tools)

    if has_readonly:
        score += 15
        findings.append("readOnlyHint annotation present")
    if has_destructive is False and total > 0:
        pass

    desc_lower = info.description.lower()
    readme_lower = info.readme_text.lower()
    combined = desc_lower + " " + readme_lower

    read_only_signals = ["read-only", "read only", "readonly", "no side effect", "no write"]
    has_readonly_mode = any(s in combined for s in read_only_signals)
    if has_readonly_mode:
        score += 20
        findings.append("Read-only mode or no-side-effect guarantee mentioned")
    else:
        score += 5
        recommendations.append(
            "Document whether the server supports a read-only mode "
            "or declare which tools have side effects"
        )

    permission_signals = [
        "permission",
        "scope",
        "oauth",
        "token",
        "api key",
        "auth",
        "credential",
        "access control",
        "approval",
    ]
    has_permission_info = any(s in combined for s in permission_signals)
    if has_permission_info:
        score += 15
        findings.append("Permission/auth requirements documented")
    else:
        score += 5
        recommendations.append("Document what permissions or auth the server requires")

    confirmation_signals = ["confirm", "approval", "approve", "human-in-the-loop", "interactive"]
    has_confirmation = any(s in combined for s in confirmation_signals)
    if has_confirmation:
        score += 15
        findings.append("Confirmation/approval flow for dangerous operations mentioned")
    else:
        score += 5

    score = min(score, 100)
    return CheckResult("Trust & Safety", score_to_grade(score), score, findings, recommendations)

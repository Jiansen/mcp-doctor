"""AI-powered qualitative review using OpenAI-compatible API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_doctor.checks import CheckResult
    from mcp_doctor.loader import ServerInfo


@dataclass
class AIReviewResult:
    """Result of an AI-powered qualitative review."""

    mode: str = "ai"
    model_name: str = ""
    model_version: str = ""
    review_summary: str = ""
    dimension_reviews: dict[str, str] = None  # type: ignore[assignment]
    error: str | None = None

    def __post_init__(self) -> None:
        if self.dimension_reviews is None:
            self.dimension_reviews = {}


def get_model_info() -> tuple[str, str]:
    """Return (model_name, base_url) from environment or defaults."""
    model = os.environ.get("MCP_DOCTOR_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    return model, base_url


def _build_prompt(info: ServerInfo, results: list[CheckResult]) -> str:
    lines = [
        "You are an expert MCP (Model Context Protocol) server reviewer.",
        "Evaluate the following MCP server's contract quality.",
        "Provide concise, actionable feedback for each dimension.",
        "",
        f"Server name: {info.name or '(unnamed)'}",
        f"Description: {info.description or '(none)'}",
        f"Version: {info.version or '(unknown)'}",
        f"Tools: {len(info.tools)}",
        f"Has server.json: {info.has_server_json}",
        f"Has README: {info.has_readme}",
        f"Has LICENSE: {info.has_license}",
        f"Install methods: {', '.join(info.install_methods) or 'none detected'}",
        "",
    ]

    if info.tools:
        lines.append("Tool definitions:")
        for t in info.tools:
            ann_str = ""
            if t.annotations:
                ann_str = f" [annotations: {t.annotations}]"
            lines.append(f"  - {t.name}: {t.description or '(no description)'}{ann_str}")
        lines.append("")

    if info.readme_text:
        readme_preview = info.readme_text[:2000]
        if len(info.readme_text) > 2000:
            readme_preview += "\n... (truncated)"
        lines.append("README (preview):")
        lines.append(readme_preview)
        lines.append("")

    lines.append("Rule-based scores:")
    for r in results:
        lines.append(f"  {r.dimension}: {r.grade} ({r.score}/100)")
        if r.findings:
            for f in r.findings[:3]:
                lines.append(f"    - {f}")
        if r.recommendations:
            for rec in r.recommendations[:2]:
                lines.append(f"    * Rec: {rec}")
    lines.append("")

    lines.append(
        "For each of the 6 dimensions, provide a 1-2 sentence qualitative review "
        "that adds insight beyond the rule-based score. Focus on what the rules "
        "cannot detect: naming quality, description clarity, README persuasiveness, "
        "trust signal effectiveness, etc."
    )
    lines.append("")
    lines.append(
        "Also provide an overall summary (2-3 sentences) of the server's "
        "contract quality and the single most impactful improvement."
    )
    lines.append("")
    lines.append("Format your response EXACTLY as follows (keep the markers):")
    lines.append("[SUMMARY]")
    lines.append("Your overall summary here.")
    lines.append("[Task Clarity]")
    lines.append("Your review of task clarity.")
    lines.append("[Trust & Safety]")
    lines.append("Your review of trust & safety.")
    lines.append("[Interface Quality]")
    lines.append("Your review of interface quality.")
    lines.append("[Token Efficiency]")
    lines.append("Your review of token efficiency.")
    lines.append("[Install Friction]")
    lines.append("Your review of install friction.")
    lines.append("[Cross-platform Readiness]")
    lines.append("Your review of cross-platform readiness.")

    return "\n".join(lines)


def _parse_response(text: str) -> tuple[str, dict[str, str]]:
    """Parse the structured AI response into summary + per-dimension reviews."""
    sections: dict[str, str] = {}
    current_key = ""
    current_lines: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current_key and current_lines:
                sections[current_key] = " ".join(current_lines).strip()
            current_key = stripped[1:-1]
            current_lines = []
        else:
            current_lines.append(stripped)

    if current_key and current_lines:
        sections[current_key] = " ".join(current_lines).strip()

    summary = sections.pop("SUMMARY", "")
    return summary, sections


def run_ai_review(
    info: ServerInfo,
    results: list[CheckResult],
    model: str | None = None,
) -> AIReviewResult:
    """Run AI-powered qualitative review. Requires openai package and API key."""
    try:
        import openai
    except ImportError:
        return AIReviewResult(
            error=("openai package not installed. Install with: pip install mcp-doctor[ai]"),
        )

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return AIReviewResult(
            error=(
                "OPENAI_API_KEY environment variable not set. Set it to use AI evaluation mode."
            ),
        )

    model_name, base_url = get_model_info()
    if model:
        model_name = model

    client_kwargs: dict = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    prompt = _build_prompt(info, results)

    try:
        client = openai.OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
    except Exception as exc:
        return AIReviewResult(
            model_name=model_name,
            error=f"AI API call failed: {exc}",
        )

    reply = response.choices[0].message.content or ""
    resp_model = getattr(response, "model", model_name)

    summary, dimension_reviews = _parse_response(reply)

    return AIReviewResult(
        mode="ai",
        model_name=resp_model,
        model_version=model_name,
        review_summary=summary,
        dimension_reviews=dimension_reviews,
    )

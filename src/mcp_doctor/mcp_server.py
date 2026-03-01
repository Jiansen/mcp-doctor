"""MCP server for mcp-doctor — lets agents check any MCP server's contract quality."""

from __future__ import annotations

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment, misc]

if FastMCP is not None:
    _INSTRUCTIONS = """\
TRUST MODEL: In rule-based mode (default), mcp-doctor is fully offline and \
read-only — it only reads files from the local filesystem. No network calls, \
no LLM, no API keys, no data sent anywhere.

In AI mode (mode="ai"), mcp-doctor sends a summary of the server metadata to \
an OpenAI-compatible API for qualitative review. This requires OPENAI_API_KEY \
to be set. No source code is sent — only metadata, tool definitions, and a \
README preview.

WORKFLOW:
1. Use check_server(path) for rule-based evaluation (default, deterministic)
2. Use check_server(path, mode="ai") for AI-enhanced qualitative review
3. Review the 6 dimension scores (A/B/C/D)
4. Focus on lowest-scoring dimensions first
5. Follow the recommendations to improve the server

If check_server fails, verify the path points to a valid directory.

FEEDBACK: Report issues at https://github.com/Jiansen/mcp-doctor/issues
"""

    mcp = FastMCP(
        "mcp-doctor",
        instructions=_INSTRUCTIONS,
        description=(
            "Check the contract quality of any MCP server. "
            "Use this when you want to evaluate whether an MCP server "
            "is well-designed for agents, humans, and distribution platforms."
        ),
    )

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    def check_server(
        path: str,
        format: str = "json",
        mode: str = "rule",
        model: str | None = None,
    ) -> dict:
        """Run contract quality checks on an MCP server at the given path.

        Use this to evaluate any MCP server's readiness for agents,
        distribution platforms, and human users.

        Args:
            path: Absolute path to the MCP server repository directory.
            format: Output format — "json" for structured data (default),
                    "markdown" for human-readable report.
            mode: "rule" for deterministic rule-based evaluation (default),
                  "ai" for LLM-enhanced qualitative review (requires
                  OPENAI_API_KEY environment variable).
            model: LLM model name for AI mode. Defaults to
                   $MCP_DOCTOR_MODEL env var or "gpt-4o-mini".

        Returns a structured report with:
        - evaluation: {mode, model_name, model_version} (if AI mode)
        - overall_grade: A/B/C/D
        - dimensions: 6 check results with grade, score, findings
        - ai_review: qualitative AI feedback (if AI mode)
        """
        import json as json_mod

        from mcp_doctor.checks import overall_grade, run_all_checks
        from mcp_doctor.loader import load_from_path
        from mcp_doctor.report import format_json, format_markdown

        try:
            info = load_from_path(path)
        except FileNotFoundError as exc:
            return {
                "error": str(exc),
                "hint": "Provide an absolute path to an MCP server repo.",
            }
        except Exception as exc:
            return {"error": f"Failed to load server: {exc}"}

        results = run_all_checks(info)
        grade = overall_grade(results)

        ai_review = None
        if mode == "ai":
            from mcp_doctor.checks.ai_review import run_ai_review

            ai_review = run_ai_review(info, results, model=model)

        if format == "markdown":
            return {"report": format_markdown(info, results, grade, ai_review=ai_review)}

        raw = format_json(info, results, grade, ai_review=ai_review)
        return json_mod.loads(raw)

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    def list_dimensions() -> dict:
        """List the 6 contract quality dimensions that mcp-doctor checks.

        Use this to understand what mcp-doctor evaluates before running a check.

        Returns a list of dimension names with brief descriptions.
        """
        return {
            "dimensions": [
                {
                    "name": "Task Clarity",
                    "description": (
                        "Is the server's purpose immediately clear to humans and agents?"
                    ),
                },
                {
                    "name": "Trust & Safety",
                    "description": "Are side effects, permissions, and safety boundaries declared?",
                },
                {
                    "name": "Interface Quality",
                    "description": "Are tools well-named, well-described, and well-typed?",
                },
                {
                    "name": "Token Efficiency",
                    "description": "Will tool responses fit an agent's context budget?",
                },
                {
                    "name": "Install Friction",
                    "description": "How fast can someone go from discovery to first use?",
                },
                {
                    "name": "Cross-platform Readiness",
                    "description": "Is metadata complete for all major MCP distribution platforms?",
                },
            ]
        }

else:
    mcp = None  # type: ignore[assignment]

"""MCP server for mcp-doctor — lets agents check any MCP server's contract quality."""

from __future__ import annotations

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment, misc]

if FastMCP is not None:
    _INSTRUCTIONS = """\
TRUST MODEL: mcp-doctor is read-only. It only reads files from the local \
filesystem. No network calls, no LLM, no API keys, no data sent anywhere.

WORKFLOW:
1. Use check_server(path) to evaluate any MCP server repo
2. Review the 6 dimension scores (A/B/C/D)
3. Focus on lowest-scoring dimensions first
4. Follow the recommendations to improve the server

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
    def check_server(path: str, format: str = "json") -> dict:
        """Run contract quality checks on an MCP server at the given path.

        Use this to evaluate any MCP server's readiness for agents,
        distribution platforms, and human users.

        Args:
            path: Absolute path to the MCP server repository directory.
            format: Output format — "json" for structured data (default),
                    "markdown" for human-readable report.

        Returns a structured report with:
        - overall_grade: A/B/C/D
        - dimensions: list of 6 check results with grade, score, findings, recommendations
        """
        import json as json_mod

        from mcp_doctor.checks import overall_grade, run_all_checks
        from mcp_doctor.loader import load_from_path
        from mcp_doctor.report import format_json, format_markdown

        try:
            info = load_from_path(path)
        except FileNotFoundError as exc:
            return {"error": str(exc), "hint": "Provide an absolute path to an MCP server repo."}
        except Exception as exc:
            return {"error": f"Failed to load server: {exc}"}

        results = run_all_checks(info)
        grade = overall_grade(results)

        if format == "markdown":
            return {"report": format_markdown(info, results, grade)}

        return json_mod.loads(format_json(info, results, grade))

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

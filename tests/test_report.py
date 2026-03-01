"""Tests for the report module."""

import json
from unittest import TestCase

from mcp_doctor.checks import CheckResult
from mcp_doctor.loader import ServerInfo, ToolInfo
from mcp_doctor.report import format_json, format_markdown, format_terminal


def _sample_info() -> ServerInfo:
    return ServerInfo(
        name="io.github.test/sample",
        version="1.0.0",
        tools=[ToolInfo(name="test_tool", description="A test tool")],
        source_path="/tmp/sample",
    )


def _sample_results() -> list[CheckResult]:
    return [
        CheckResult("Task Clarity", "A", 92, ["Description present"], []),
        CheckResult("Trust & Safety", "B", 78, ["Some annotations"], ["Add readOnlyHint"]),
    ]


class TestFormatTerminal(TestCase):
    def test_contains_server_name(self):
        out = format_terminal(_sample_info(), _sample_results(), "B")
        self.assertIn("io.github.test/sample", out)
        self.assertIn("Task Clarity", out)
        self.assertIn("Overall", out)

    def test_contains_recommendations(self):
        out = format_terminal(_sample_info(), _sample_results(), "B")
        self.assertIn("readOnlyHint", out)


class TestFormatJson(TestCase):
    def test_valid_json(self):
        out = format_json(_sample_info(), _sample_results(), "B")
        data = json.loads(out)
        self.assertEqual(data["overall_grade"], "B")
        self.assertEqual(len(data["dimensions"]), 2)

    def test_scores_present(self):
        out = format_json(_sample_info(), _sample_results(), "B")
        data = json.loads(out)
        self.assertIn("overall_score", data)


class TestFormatMarkdown(TestCase):
    def test_contains_header(self):
        out = format_markdown(_sample_info(), _sample_results(), "B")
        self.assertIn("# MCP Doctor Report", out)
        self.assertIn("| Task Clarity |", out)

    def test_contains_recommendations(self):
        out = format_markdown(_sample_info(), _sample_results(), "B")
        self.assertIn("Recommendations", out)

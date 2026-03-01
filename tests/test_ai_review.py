"""Tests for the AI review module."""

import json
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from mcp_doctor.checks import CheckResult
from mcp_doctor.checks.ai_review import (
    AIReviewResult,
    _build_prompt,
    _parse_response,
    get_model_info,
    run_ai_review,
)
from mcp_doctor.loader import ServerInfo, ToolInfo


def _sample_info() -> ServerInfo:
    return ServerInfo(
        name="io.github.test/sample",
        description="A test server",
        version="1.0.0",
        tools=[ToolInfo(name="test_tool", description="A test tool")],
        source_path="/tmp/sample",
        has_readme=True,
        readme_text="# Sample\nA sample MCP server.",
    )


def _sample_results() -> list[CheckResult]:
    return [
        CheckResult("Task Clarity", "A", 92, ["Good"], []),
        CheckResult("Trust & Safety", "C", 60, ["Missing annotations"], ["Add readOnlyHint"]),
    ]


class TestGetModelInfo(TestCase):
    def test_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            model, base_url = get_model_info()
            self.assertEqual(model, "gpt-4o-mini")
            self.assertEqual(base_url, "")

    def test_custom_model(self):
        with patch.dict(os.environ, {"MCP_DOCTOR_MODEL": "claude-3-haiku"}):
            model, _ = get_model_info()
            self.assertEqual(model, "claude-3-haiku")

    def test_custom_base_url(self):
        with patch.dict(os.environ, {"OPENAI_BASE_URL": "http://localhost:11434/v1"}):
            _, base_url = get_model_info()
            self.assertEqual(base_url, "http://localhost:11434/v1")


class TestBuildPrompt(TestCase):
    def test_includes_server_info(self):
        prompt = _build_prompt(_sample_info(), _sample_results())
        self.assertIn("io.github.test/sample", prompt)
        self.assertIn("test_tool", prompt)

    def test_includes_scores(self):
        prompt = _build_prompt(_sample_info(), _sample_results())
        self.assertIn("Task Clarity: A (92/100)", prompt)
        self.assertIn("Trust & Safety: C (60/100)", prompt)

    def test_includes_readme(self):
        prompt = _build_prompt(_sample_info(), _sample_results())
        self.assertIn("# Sample", prompt)


class TestParseResponse(TestCase):
    def test_parses_structured_response(self):
        text = (
            "[SUMMARY]\n"
            "This server is well-built.\n"
            "[Task Clarity]\n"
            "Clear naming and docs.\n"
            "[Trust & Safety]\n"
            "Needs annotations.\n"
        )
        summary, dims = _parse_response(text)
        self.assertIn("well-built", summary)
        self.assertIn("Task Clarity", dims)
        self.assertIn("Trust & Safety", dims)

    def test_empty_response(self):
        summary, dims = _parse_response("")
        self.assertEqual(summary, "")
        self.assertEqual(dims, {})


class TestRunAiReview(TestCase):
    def test_no_openai_package(self):
        with patch.dict("sys.modules", {"openai": None}):
            result = run_ai_review(_sample_info(), _sample_results())
            self.assertIsNotNone(result.error)
            self.assertIn("openai", result.error)

    def test_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = run_ai_review(_sample_info(), _sample_results())
            self.assertIsNotNone(result.error)
            self.assertIn("OPENAI_API_KEY", result.error)

    def test_successful_review(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "[SUMMARY]\nGreat server.\n[Task Clarity]\nClear.\n"
        mock_response.model = "gpt-4o-mini-2025-07-18"
        mock_client.chat.completions.create.return_value = mock_response

        mock_openai = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch.dict("sys.modules", {"openai": mock_openai}),
        ):
            import importlib

            import mcp_doctor.checks.ai_review as ai_mod

            importlib.reload(ai_mod)
            result = ai_mod.run_ai_review(_sample_info(), _sample_results())

        self.assertIsNone(result.error)
        self.assertEqual(result.mode, "ai")
        self.assertIn("Great server", result.review_summary)

    def test_model_override(self):
        with patch.dict(os.environ, {}, clear=True):
            result = run_ai_review(_sample_info(), _sample_results(), model="custom-model")
            self.assertIsNotNone(result.error)


class TestReportWithAiReview(TestCase):
    """Verify that report formatters handle ai_review parameter."""

    def test_json_with_ai_review(self):
        from mcp_doctor.report import format_json

        ai = AIReviewResult(
            model_name="gpt-4o-mini",
            model_version="gpt-4o-mini",
            review_summary="Solid server.",
            dimension_reviews={"Task Clarity": "Well done."},
        )
        out = format_json(_sample_info(), _sample_results(), "B", ai_review=ai)
        data = json.loads(out)
        self.assertEqual(data["evaluation"]["mode"], "ai")
        self.assertEqual(data["evaluation"]["model_name"], "gpt-4o-mini")
        self.assertIn("ai_review", data)

    def test_json_without_ai_review(self):
        from mcp_doctor.report import format_json

        out = format_json(_sample_info(), _sample_results(), "B")
        data = json.loads(out)
        self.assertEqual(data["evaluation"]["mode"], "rule-based")
        self.assertNotIn("ai_review", data)

    def test_terminal_with_ai_mode(self):
        from mcp_doctor.report import format_terminal

        ai = AIReviewResult(
            model_name="gpt-4o-mini",
            model_version="gpt-4o-mini",
            review_summary="Good.",
            dimension_reviews={},
        )
        out = format_terminal(_sample_info(), _sample_results(), "B", ai_review=ai)
        self.assertIn("ai (gpt-4o-mini)", out)

    def test_terminal_rule_mode(self):
        from mcp_doctor.report import format_terminal

        out = format_terminal(_sample_info(), _sample_results(), "B")
        self.assertIn("rule-based", out)

    def test_markdown_with_ai(self):
        from mcp_doctor.report import format_markdown

        ai = AIReviewResult(
            model_name="gpt-4o-mini",
            model_version="gpt-4o-mini",
            review_summary="Quality server.",
            dimension_reviews={"Task Clarity": "Excellent."},
        )
        out = format_markdown(_sample_info(), _sample_results(), "B", ai_review=ai)
        self.assertIn("Evaluation Mode", out)
        self.assertIn("AI Review", out)

    def test_markdown_rule_mode(self):
        from mcp_doctor.report import format_markdown

        out = format_markdown(_sample_info(), _sample_results(), "B")
        self.assertIn("rule-based", out)

    def test_ai_error_in_json(self):
        from mcp_doctor.report import format_json

        ai = AIReviewResult(error="API key missing")
        out = format_json(_sample_info(), _sample_results(), "B", ai_review=ai)
        data = json.loads(out)
        self.assertEqual(data["evaluation"]["mode"], "rule-based")
        self.assertIn("error", data["ai_review"])

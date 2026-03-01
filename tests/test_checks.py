"""Tests for all 6 check dimensions."""

from unittest import TestCase

from mcp_doctor.checks import overall_grade, run_all_checks
from mcp_doctor.checks.cross_platform import check_cross_platform
from mcp_doctor.checks.install_friction import check_install_friction
from mcp_doctor.checks.interface_quality import check_interface_quality
from mcp_doctor.checks.task_clarity import check_task_clarity
from mcp_doctor.checks.token_efficiency import check_token_efficiency
from mcp_doctor.checks.trust_safety import check_trust_safety
from mcp_doctor.loader import ServerInfo, ToolInfo


def _make_good_server() -> ServerInfo:
    return ServerInfo(
        name="io.github.test/good-server",
        description="Diagnose network issues for AI coding tools. Use this when connections fail.",
        version="1.0.0",
        repo_url="https://github.com/test/good-server",
        tools=[
            ToolInfo(
                name="diagnose_network",
                description=(
                    "Run a full network diagnostic. Use this when the editor "
                    "cannot connect. Returns status, diagnosis, and fixes."
                ),
                input_schema={
                    "type": "object",
                    "properties": {"editor": {"type": "string", "description": "Editor name"}},
                },
                output_schema={
                    "type": "object",
                    "properties": {"status": {"type": "string"}},
                },
                annotations={"readOnlyHint": True, "destructiveHint": False},
            ),
            ToolInfo(
                name="list_fixes",
                description="Get recommended fixes. Use this after diagnose returns unhealthy.",
                input_schema={
                    "type": "object",
                    "properties": {"editor": {"type": "string"}},
                },
                output_schema={
                    "type": "object",
                    "properties": {"fixes": {"type": "array"}},
                },
                annotations={"readOnlyHint": True},
            ),
        ],
        has_server_json=True,
        server_json={
            "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
            "name": "io.github.test/good-server",
            "description": (
                "Diagnose network issues for AI coding tools. Use this when connections fail."
            ),
            "version": "1.0.0",
            "repository": {"url": "https://github.com/test/good-server", "source": "github"},
            "packages": [
                {
                    "registryType": "pypi",
                    "identifier": "good-server",
                    "version": "1.0.0",
                    "transport": {"type": "stdio"},
                }
            ],
        },
        has_readme=True,
        readme_text=(
            "# Good Server\n\nDiagnose network issues.\n\n"
            "## Installation\n\npip install good-server\nbrew install good-server\n"
            "docker run good-server\n\n"
            "All tools are read-only. No side effects. Auth via API key.\n"
            "Supports pagination via limit parameter.\n"
        ),
        has_license=True,
        install_methods=["pip", "homebrew", "docker"],
        has_remote=False,
    )


def _make_bad_server() -> ServerInfo:
    return ServerInfo(
        name="",
        description="",
        tools=[ToolInfo(name="doStuff", description="")],
        has_server_json=False,
        has_readme=False,
    )


class TestTaskClarity(TestCase):
    def test_good_server(self):
        r = check_task_clarity(_make_good_server())
        self.assertIn(r.grade, ("A", "B"))
        self.assertGreaterEqual(r.score, 75)

    def test_bad_server(self):
        r = check_task_clarity(_make_bad_server())
        self.assertEqual(r.grade, "D")


class TestTrustSafety(TestCase):
    def test_good_server(self):
        r = check_trust_safety(_make_good_server())
        self.assertIn(r.grade, ("A", "B"))

    def test_no_annotations(self):
        s = _make_bad_server()
        r = check_trust_safety(s)
        self.assertIn(r.grade, ("C", "D"))


class TestInterfaceQuality(TestCase):
    def test_good_server(self):
        r = check_interface_quality(_make_good_server())
        self.assertIn(r.grade, ("A", "B"))

    def test_bad_naming(self):
        r = check_interface_quality(_make_bad_server())
        self.assertIn(r.grade, ("C", "D"))


class TestTokenEfficiency(TestCase):
    def test_lean_tools(self):
        r = check_token_efficiency(_make_good_server())
        self.assertIn(r.grade, ("A", "B", "C"))
        self.assertGreaterEqual(r.score, 50)

    def test_no_tools(self):
        s = ServerInfo()
        r = check_token_efficiency(s)
        self.assertEqual(r.grade, "D")


class TestInstallFriction(TestCase):
    def test_good_server(self):
        r = check_install_friction(_make_good_server())
        self.assertIn(r.grade, ("A", "B"))

    def test_no_server_json(self):
        r = check_install_friction(_make_bad_server())
        self.assertIn(r.grade, ("C", "D"))


class TestCrossPlatform(TestCase):
    def test_good_server(self):
        r = check_cross_platform(_make_good_server())
        self.assertIn(r.grade, ("A", "B"))

    def test_no_metadata(self):
        r = check_cross_platform(_make_bad_server())
        self.assertEqual(r.grade, "D")


class TestRunAllChecks(TestCase):
    def test_returns_6_results(self):
        results = run_all_checks(_make_good_server())
        self.assertEqual(len(results), 6)

    def test_overall_grade(self):
        results = run_all_checks(_make_good_server())
        grade = overall_grade(results)
        self.assertIn(grade, ("A", "B", "C", "D"))

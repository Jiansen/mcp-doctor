"""Tests for the loader module."""

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from mcp_doctor.loader import load_from_path


class TestLoadFromPath(TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = load_from_path(tmp)
            self.assertEqual(info.name, "")
            self.assertFalse(info.has_server_json)
            self.assertFalse(info.has_readme)
            self.assertEqual(info.tools, [])

    def test_with_server_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            sj = {
                "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
                "name": "io.github.test/my-server",
                "description": "A test MCP server for unit testing",
                "version": "1.0.0",
                "repository": {"url": "https://github.com/test/my-server", "source": "github"},
                "packages": [
                    {
                        "registryType": "pypi",
                        "identifier": "my-server",
                        "version": "1.0.0",
                        "transport": {"type": "stdio"},
                    }
                ],
            }
            Path(tmp, "server.json").write_text(json.dumps(sj))
            Path(tmp, "README.md").write_text(
                "# My Server\n\n## Installation\n\npip install my-server\n"
            )
            Path(tmp, "LICENSE").write_text("MIT")

            info = load_from_path(tmp)
            self.assertEqual(info.name, "io.github.test/my-server")
            self.assertEqual(info.version, "1.0.0")
            self.assertTrue(info.has_server_json)
            self.assertTrue(info.has_readme)
            self.assertTrue(info.has_license)

    def test_with_tool_json_descriptors(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools_dir = Path(tmp, "tools")
            tools_dir.mkdir()
            tool = {
                "name": "my_tool",
                "description": "Does something useful. Use this when you need X.",
                "arguments": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                },
            }
            (tools_dir / "my_tool.json").write_text(json.dumps(tool))

            info = load_from_path(tmp)
            self.assertEqual(len(info.tools), 1)
            self.assertEqual(info.tools[0].name, "my_tool")
            self.assertIn("useful", info.tools[0].description)

    def test_nonexistent_path(self):
        with self.assertRaises(FileNotFoundError):
            load_from_path("/nonexistent/path/xyz")

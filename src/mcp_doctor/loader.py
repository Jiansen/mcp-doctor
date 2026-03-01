"""Load MCP server metadata from local repo path, stdio connection, or registry."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolInfo:
    name: str
    description: str = ""
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    annotations: dict = field(default_factory=dict)


@dataclass
class ServerInfo:
    """Unified representation of an MCP server's metadata for checking."""

    name: str = ""
    description: str = ""
    version: str = ""
    repo_url: str = ""
    tools: list[ToolInfo] = field(default_factory=list)
    server_json: dict | None = None
    readme_text: str = ""
    has_server_json: bool = False
    has_readme: bool = False
    has_license: bool = False
    install_methods: list[str] = field(default_factory=list)
    has_remote: bool = False
    source_path: str = ""
    packages: list[dict] = field(default_factory=list)


def load_from_path(path: str | Path) -> ServerInfo:
    """Load server metadata from a local repo directory."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")

    info = ServerInfo(source_path=str(root))

    _load_server_json(root, info)
    _load_readme(root, info)
    _load_license(root, info)
    _load_tools_from_source(root, info)
    _detect_install_methods(root, info)

    return info


def _load_server_json(root: Path, info: ServerInfo) -> None:
    sj = root / "server.json"
    if not sj.exists():
        return
    try:
        data = json.loads(sj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    info.has_server_json = True
    info.server_json = data
    info.name = data.get("name", "")
    info.description = data.get("description", "")
    info.version = data.get("version", "")
    repo = data.get("repository", {})
    info.repo_url = repo.get("url", "") if isinstance(repo, dict) else ""
    info.packages = data.get("packages", [])

    remotes = data.get("remotes", [])
    if remotes:
        info.has_remote = True


def _load_readme(root: Path, info: ServerInfo) -> None:
    for name in ("README.md", "readme.md", "README.rst", "README.txt", "README"):
        p = root / name
        if p.exists():
            info.has_readme = True
            try:
                info.readme_text = p.read_text(encoding="utf-8")
            except OSError:
                pass
            return


def _load_license(root: Path, info: ServerInfo) -> None:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"):
        if (root / name).exists():
            info.has_license = True
            return


_TOOL_DECORATOR_RE = re.compile(
    r"@\w+\.tool\b[^)]*\)\s*(?:async\s+)?def\s+(\w+)",
    re.DOTALL,
)

_TOOL_NAME_RE = re.compile(r'name\s*=\s*["\']([^"\']+)["\']')
_TOOL_DESC_RE = re.compile(r'description\s*=\s*["\']([^"\']+)["\']')


def _load_tools_from_source(root: Path, info: ServerInfo) -> None:
    """Best-effort extraction of tool definitions from Python source files."""
    tool_names_seen: set[str] = set()

    for py_file in root.rglob("*.py"):
        try:
            src = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if "@" not in src or "tool" not in src:
            continue

        for match in _TOOL_DECORATOR_RE.finditer(src):
            func_name = match.group(1)
            if func_name in tool_names_seen:
                continue
            tool_names_seen.add(func_name)

            decorator_text = src[match.start() : match.end()]
            desc = ""
            annotations: dict = {}

            desc_match = _TOOL_DESC_RE.search(decorator_text)
            if desc_match:
                desc = desc_match.group(1)

            func_end = match.end()
            body_start = src.find(":", func_end)
            if body_start != -1:
                docstring_start = src.find('"""', body_start, body_start + 100)
                if docstring_start == -1:
                    docstring_start = src.find("'''", body_start, body_start + 100)
                if docstring_start != -1:
                    quote = src[docstring_start : docstring_start + 3]
                    docstring_end = src.find(quote, docstring_start + 3)
                    if docstring_end != -1 and not desc:
                        desc = src[docstring_start + 3 : docstring_end].strip()

            if "readOnlyHint" in decorator_text or "read_only" in decorator_text.lower():
                annotations["readOnlyHint"] = True
            if "destructiveHint" in decorator_text:
                annotations["destructiveHint"] = True
            if "idempotentHint" in decorator_text:
                annotations["idempotentHint"] = True

            info.tools.append(
                ToolInfo(
                    name=func_name,
                    description=desc,
                    annotations=annotations,
                )
            )

    _load_tools_from_json_descriptors(root, info, tool_names_seen)


def _load_tools_from_json_descriptors(root: Path, info: ServerInfo, seen: set[str]) -> None:
    """Load tool definitions from JSON descriptor files (e.g. Cursor MCP format)."""
    for json_file in root.rglob("*.json"):
        if json_file.name == "server.json" or json_file.name == "package.json":
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict) or "name" not in data:
            continue
        if "description" not in data and "arguments" not in data:
            continue
        name = data["name"]
        if name in seen:
            continue
        seen.add(name)
        info.tools.append(
            ToolInfo(
                name=name,
                description=data.get("description", ""),
                input_schema=data.get("arguments", data.get("inputSchema", {})),
                output_schema=data.get("outputSchema", {}),
                annotations=data.get("annotations", {}),
            )
        )


def _detect_install_methods(root: Path, info: ServerInfo) -> None:
    methods: list[str] = []

    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        methods.append("pip")
    if (root / "package.json").exists():
        methods.append("npm")
    if (root / "Dockerfile").exists():
        methods.append("docker")

    readme_lower = info.readme_text.lower()
    if "homebrew" in readme_lower or "brew install" in readme_lower:
        methods.append("homebrew")
    if "npx " in readme_lower:
        methods.append("npx")

    for pkg in info.packages:
        if pkg.get("transport", {}).get("type") in ("streamable-http", "sse"):
            info.has_remote = True
            if "remote" not in methods:
                methods.append("remote")

    if info.has_remote and "remote" not in methods:
        methods.append("remote")

    info.install_methods = methods

<!-- mcp-name: io.github.Jiansen/mcp-doctor -->

<p align="center">
  <img src="assets/avatar-512.png" width="120" alt="mcp-doctor logo">
</p>

<h1 align="center">MCP Doctor</h1>

<p align="center">
  <a href="https://pypi.org/project/mcp-doctor/"><img src="https://img.shields.io/pypi/v/mcp-doctor" alt="PyPI"></a>
  <a href="https://github.com/Jiansen/mcp-doctor/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <a href="https://pypi.org/project/mcp-doctor/"><img src="https://img.shields.io/pypi/pyversions/mcp-doctor" alt="Python"></a>
  <a href="https://github.com/Jiansen/mcp-doctor/stargazers"><img src="https://img.shields.io/github/stars/Jiansen/mcp-doctor?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">Check and improve the contract quality of any MCP server — for humans, agents, and platforms.</p>

## Problem

Most MCP servers are built with only one audience in mind (usually human developers reading a README). But a successful MCP server needs to satisfy three audiences simultaneously:

- **Distribution platforms** (Registry, Smithery, PulseMCP, Glama) need structured metadata
- **Human users** need clear purpose, trust signals, and low install friction
- **AI agents** need unambiguous tool descriptions, declared side effects, and token-efficient responses

MCP Doctor checks all six dimensions of "contract quality" and gives you actionable recommendations.

## Quick Start

```bash
pip install mcp-doctor
mcp-doctor check /path/to/your-mcp-server
```

## What It Checks

| Dimension | Question |
|-----------|----------|
| **Task Clarity** | Is the server's purpose immediately clear? |
| **Trust & Safety** | Are side effects, permissions, and safety boundaries declared? |
| **Interface Quality** | Are tools well-named, well-described, and well-typed? |
| **Token Efficiency** | Will tool responses fit an agent's context budget? |
| **Install Friction** | How fast can someone go from discovery to first use? |
| **Cross-platform Readiness** | Is metadata complete for Registry, Smithery, PulseMCP, Glama? |

## Usage

### CLI

```bash
# Terminal output (default)
mcp-doctor check /path/to/server

# JSON output (for CI/CD)
mcp-doctor check /path/to/server --format json

# Markdown output (for README badges or reports)
mcp-doctor check /path/to/server --format markdown
```

### As an MCP Server

MCP Doctor is also an MCP server, so AI agents can use it to check other servers:

```json
{
  "mcpServers": {
    "mcp-doctor": {
      "command": "python",
      "args": ["-m", "mcp_doctor.mcp_server"]
    }
  }
}
```

Tools:
- `check_server(path, format)` — Run all 6 checks on a server at the given path
- `list_dimensions()` — List what MCP Doctor evaluates

### For AI Agents: Quick Install

**One-liner** (paste this to your AI agent):

> Install mcp-doctor (`pip install mcp-doctor`) and add it to your MCP config with command `python -m mcp_doctor.mcp_server`. Then use the `check_server` tool to check any MCP server's quality.

**Step by step:**

1. Install: `pip install mcp-doctor`
2. Add to your MCP configuration:
   ```json
   {
     "mcpServers": {
       "mcp-doctor": {
         "command": "python",
         "args": ["-m", "mcp_doctor.mcp_server"]
       }
     }
   }
   ```
3. Use the `check_server` tool with a path to any MCP server repo
4. If MCP is not available, fall back to CLI: `mcp-doctor check /path/to/server --format json`

**Agent workflow:** check server -> review scores -> identify lowest dimensions -> follow recommendations

## Scoring

Each dimension is scored 0-100 and graded A/B/C/D:

- **A** (90+): Exemplary
- **B** (75-89): Good, minor gaps
- **C** (55-74): Adequate, notable gaps
- **D** (<55): Needs significant improvement

## Theoretical Foundation

MCP Doctor is based on the **Contract Quality Framework** — the principle that a successful MCP product's promises (what it does, what it costs, what risks it carries) should be equally parseable by platforms, humans, and agents.

The framework draws from:
- Anthropic's "Writing effective tools for agents" (tool description engineering, namespacing, token efficiency)
- Official MCP Registry requirements (server.json schema, namespace verification)
- Cross-platform analysis of Smithery, PulseMCP, Glama ranking signals

## Trust & Permissions

MCP Doctor is **read-only by default**. It only reads files from the filesystem — it never modifies, deletes, or creates files.

| What it accesses | Why |
|-----------------|-----|
| `server.json` | Parse MCP metadata |
| `README.md` | Check documentation quality |
| `LICENSE` | Verify license presence |
| `*.py`, `*.json` in `src/` | Detect tool definitions |

- No network calls — all checks run locally
- No LLM or AI — scoring is deterministic and rule-based
- No API keys or secrets required
- No data sent anywhere

All MCP tools have `readOnlyHint: true` and `destructiveHint: false` annotations.

## Feedback

Found a bug? Have a suggestion? We'd love to hear from you:

- **GitHub Issues**: https://github.com/Jiansen/mcp-doctor/issues
- **Quick report** (if you have `gh` CLI):
  ```bash
  gh issue create --repo Jiansen/mcp-doctor --title "Bug: ..." --body "..."
  ```

If you're an agent, include the JSON output of `check_server` in your report for context.

## Contributing

```bash
git clone https://github.com/Jiansen/mcp-doctor.git
cd mcp-doctor
pip install -e ".[dev]"
ruff check src/ tests/
pytest tests/ -v
```

---

If MCP Doctor helped you improve your server, consider giving it a star on GitHub — it helps others discover the tool.

[![Star on GitHub](https://img.shields.io/github/stars/Jiansen/mcp-doctor?style=social)](https://github.com/Jiansen/mcp-doctor)

## License

MIT

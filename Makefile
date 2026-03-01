
.PHONY: help lint test check self-check install

help:
	@echo "mcp-doctor — MCP server contract quality checker"
	@echo ""
	@echo "  make install     Install in editable mode"
	@echo "  make lint        Run ruff linter"
	@echo "  make test        Run tests"
	@echo "  make check       Check a server (usage: make check PATH=/path/to/server)"
	@echo "  make self-check  Check mcp-doctor itself"

install:
	pip install -e ".[dev,mcp]"

lint:
	python3 -m ruff check src/ tests/
	python3 -m ruff format --check src/ tests/

test:
	python3 -m pytest tests/ -v

check:
	@if [ -z "$(PATH_ARG)" ]; then echo "Usage: make check PATH_ARG=/path/to/server"; exit 1; fi
	python3 -m mcp_doctor check $(PATH_ARG)

self-check:
	python3 -m mcp_doctor check .

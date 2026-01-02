# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project integrates the Claude Agent SDK with E2B (Execution to Binary) sandboxes to enable secure, isolated Python code execution for AI agents. The core pattern is building custom MCP tools that execute code in E2B cloud sandboxes rather than locally.

## Commands

### Install Dependencies
```bash
pip install -e .              # Install project with dependencies
pip install -e ".[dev]"       # Install with dev dependencies (pytest, mypy, ruff)
```

### Run the Agent
```bash
python main.py
```

### Testing
```bash
pytest                                    # Run all tests
pytest tests/unit                         # Run unit tests only
pytest -m "not integration"               # Skip integration tests
pytest tests/path/to/test.py::test_name   # Run single test
```

### Linting & Type Checking
```bash
ruff check .          # Lint
ruff format .         # Format
mypy src              # Type check
```

## Architecture

### Core Pattern: Custom E2B Tools for Claude Agent SDK

The project creates MCP (Model Context Protocol) tools that wrap E2B sandbox operations:

1. **Tool Definition** (`@tool` decorator) - Defines name, description, and input schema
2. **Sandbox Management** - Global or session-scoped `Sandbox` instances
3. **MCP Server Creation** - `create_sdk_mcp_server()` bundles tools
4. **Agent Query** - `query()` runs the agent loop with tools available via `mcp_servers` option

### Key Integration Points

```
Claude Agent SDK query()
    → ClaudeAgentOptions(mcp_servers={"e2b-sandbox": server})
        → Tool handler calls E2B Sandbox API
            → Code executes in isolated cloud VM
```

### Tool Naming Convention

MCP tools are accessed as `mcp__<server-name>__<tool-name>`:
- `mcp__e2b-sandbox__execute_python`

## Environment Variables

Required in `.env`:
- `ANTHROPIC_API_KEY` - Claude API key
- `E2B_API_KEY` - E2B sandbox API key

## Key Dependencies

- `claude-agent-sdk` - Agent loop and tool framework
- `e2b-code-interpreter` - Sandbox code execution
- `python-dotenv` - Environment variable loading

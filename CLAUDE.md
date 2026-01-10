# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ralph-On-Shelf (ROS)** - Autonomous AI agents running in secure E2B cloud sandboxes with self-referential iteration loops.

Key components:
- **E2B Sandboxes** - Isolated cloud VMs for safe code execution
- **Ralph Loop** - Self-referential feedback loop that re-feeds prompts until completion
- **MCP Connectors** - Connect to external services (search, databases, APIs) via Model Context Protocol
- **Claude Code Plugin** - `/ros`, `/ros-mcp`, and `/cancel-ros` commands

## Commands

### Development
```bash
pip install -e .              # Install project
pip install -e ".[dev]"       # Install with dev dependencies
```

### ROS Commands (in Claude Code)
```bash
/ros "<prompt>" --max-iterations N --completion-promise "TEXT" --output-dir "./output" --mcp auto
/ros-mcp                                                          # List available MCP servers
/cancel-ros                                                       # Cancel loop
```

MCP modes:
- `--mcp auto` (default) - Auto-select MCP servers based on prompt keywords
- `--mcp none` - Disable MCP, use classic SDK mode
- `--mcp exa-search,aws-knowledge` - Explicitly specify servers

All files created in the sandbox workspace are automatically downloaded to `--output-dir` (default: `./ralph_output`) when the loop completes.

### Testing & Linting
```bash
pytest                        # Run all tests
ruff check .                  # Lint
ruff format .                 # Format (line-length: 100)
mypy src                      # Type check (strict mode)
```

## Architecture

### ROS Loop Flow
```
/ros "task" → Create Sandbox → Work in /home/user/workspace → Check Completion → Repeat
                    ↓                         ↓                        ↓
              E2B Cloud VM            Files saved here         Until COMPLETE or max iterations
                                             ↓
                                    Download to local output_dir
```

### Key Files
| File | Purpose |
|------|---------|
| `main.py` | Direct E2B sandbox execution with MCP support |
| `mcp_registry.py` | MCP server definitions and metadata |
| `mcp_selector.py` | Auto-selection logic for MCP servers |
| `.claude-plugins/ralph-on-shelf/commands/ros.md` | /ros command definition |
| `.claude-plugins/ralph-on-shelf/commands/ros-mcp.md` | /ros-mcp command (list servers) |
| `.claude-plugins/ralph-on-shelf/hooks/stop.py` | Stop hook - re-feeds prompt |

### State File
ROS tracks loop state in `.claude-plugins/ralph-on-shelf/.ros-state.json`:
```json
{
  "active": true,
  "prompt": "...",
  "max_iterations": 10,
  "current_iteration": 3,
  "sandbox_id": "...",
  "completion_promise": "COMPLETE"
}
```

## E2B Sandbox Usage

```python
from e2b_code_interpreter import Sandbox

# Create and use sandbox
with Sandbox() as sbx:
    result = sbx.run_code('print("Hello")')
    stdout = "".join(result.logs.stdout)

    # File operations
    sbx.files.write("/path/file.txt", content)
    content = sbx.files.read("/path/file.txt")
```

### Sandbox Manager (Plugin)
```python
from lib.sandbox_manager import execute_python, manager

result = execute_python('print("test")')
# Returns: {"success": True, "output": "...", "results": [...]}

manager.write_file("/path", content)
manager.read_file("/path")
manager.kill()  # Cleanup
```

## MCP (Model Context Protocol) Integration

ROS can connect to remote MCP servers, giving the sandbox agent access to external tools and services.

### Available MCP Servers

| Server | Auth | Description |
|--------|------|-------------|
| `exa-search` | Open | Web search and research |
| `aws-knowledge` | Open | AWS documentation and cloud knowledge |
| `zapier` | API Key | Automation with 5000+ apps |
| `stripe` | API Key | Payment processing |
| `github` | OAuth | Repository management |
| `notion` | OAuth | Workspace management |
| `linear` | OAuth | Issue tracking |

### Usage

```python
from main import launch_ralph

# Auto-select MCP servers based on prompt
result = launch_ralph(
    prompt="Search the web for Python 3.13 features",
    mcp="auto"  # Will select exa-search
)

# Explicitly specify servers
result = launch_ralph(
    prompt="Any task",
    mcp="exa-search,aws-knowledge"
)

# Disable MCP (use classic SDK mode)
result = launch_ralph(
    prompt="Any task",
    mcp="none"
)
```

### Adding New MCP Servers

Edit `mcp_registry.py` to add servers:
```python
MCP_SERVERS["new-server"] = MCPServer(
    name="new-server",
    url="https://mcp.example.com/sse",
    auth_type="open",  # or "api_key" or "oauth"
    description="Description",
    categories=["category"],
    keywords=["keyword1", "keyword2"],
    auth_env_var="MCP_NEW_SERVER_API_KEY"  # if auth_type == "api_key"
)
```

## Environment Variables

Required in `.env`:
- `ANTHROPIC_API_KEY` - Claude API key
- `E2B_API_KEY` - E2B sandbox API key

Optional MCP API keys:
- `MCP_ZAPIER_API_KEY` - For Zapier MCP server
- `MCP_STRIPE_API_KEY` - For Stripe MCP server

## Key Dependencies

- `e2b-code-interpreter` >= 1.0.0 - Sandbox execution
- `anthropic` >= 0.40.0 - MCP connector support
- `python-dotenv` - Environment loading

Requires Python 3.11+

## Plugin Development

Commands go in `.claude-plugins/ralph-on-shelf/commands/*.md`
Hooks go in `.claude-plugins/ralph-on-shelf/hooks/*.py`
Shared code in `.claude-plugins/ralph-on-shelf/lib/`

## Roadmap

- [x] **MCP Connector Integration** - Connect to external services via Model Context Protocol
- [ ] **Central Wiggum Orchestrator** - A persistent "master" Ralph that stays alive and spawns child E2B sandboxes to perform tasks in parallel. The orchestrator would:
  - Maintain state across sessions
  - Dispatch tasks to worker sandboxes
  - Aggregate results from multiple parallel executions
  - Enable complex multi-agent workflows
- [ ] OAuth token management for MCP servers (GitHub, Notion, etc.)
- [ ] Sandbox templates (pre-configured environments)
- [ ] Progress streaming (real-time output)
- [ ] Checkpoint/resume (pause and continue loops)

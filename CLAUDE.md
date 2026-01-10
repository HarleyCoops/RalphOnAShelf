# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ralph-On-Shelf (ROS)** - Autonomous AI agents running in secure E2B cloud sandboxes with Wiggum planning and MCP tool integration.

**Architecture:**
```
User Task → [Wiggum Planner] → [Ralph Loop in Sandbox] → Results
               (local)              (E2B cloud)
```

Key components:
- **Wiggum Planner** - Analyzes tasks, creates todos, assigns MCPs (runs locally)
- **Ralph Loop** - Self-referential iteration loop (runs inside E2B sandbox)
- **MCP Connectors** - 13+ external services (search, databases, APIs)
- **Local Tools** - File operations inside sandbox (write_file, read_file, execute_python)
- **Claude Code Plugin** - `/ros`, `/ros-mcp`, and `/cancel-ros` commands

## Commands

### Development
```bash
pip install -e .              # Install project
pip install -e ".[dev]"       # Install with dev dependencies
```

### ROS Commands (in Claude Code)
```bash
/ros "<prompt>" --max-iterations N --completion-promise "TEXT" --output-dir "./output"
/ros-mcp                                                          # List available MCP servers
/cancel-ros                                                       # Cancel loop
```

### Python API
```python
from main import launch_ralph

result = launch_ralph(
    prompt="Search for Python 3.13 features and summarize",
    max_iterations=5,
    use_wiggum=True,  # Enable Wiggum planning (default)
)
```

All files created in the sandbox workspace are automatically downloaded to `--output-dir` (default: `./ralph_output`).

### Testing & Linting
```bash
pytest                        # Run all tests
ruff check .                  # Lint
ruff format .                 # Format (line-length: 100)
mypy src                      # Type check (strict mode)
```

## Architecture

### Wiggum + Ralph Flow
```
/ros "task" → Wiggum Plans → Create Sandbox → Ralph Loop → Download Files
                  ↓               ↓              ↓             ↓
            Break into       E2B Cloud     Iterate until   Results to
            todos + MCPs        VM          COMPLETE      output_dir
```

### Key Files
| File | Purpose |
|------|---------|
| `main.py` | WiggumPlanner + RalphLoop + AGENT_CODE_MCP |
| `mcp_registry.py` | MCP server definitions (13+ servers) |
| `mcp_selector.py` | Auto-selection logic for MCP servers |
| `.claude-plugins/ralph-on-shelf/commands/ros.md` | /ros command definition |
| `.claude-plugins/ralph-on-shelf/commands/ros-mcp.md` | /ros-mcp command |
| `.claude-plugins/ralph-on-shelf/hooks/stop.py` | Stop hook for plugin mode |

### Wiggum Planner
The `WiggumPlanner` class runs locally and:
1. Analyzes the task with Claude
2. Breaks it into 1-5 subtasks (todos)
3. Assigns only needed MCPs to each subtask
4. Shows the plan before execution

```python
plan = {
    "todos": [
        {"task": "Search for info", "mcps": ["exa-search", "tavily"]},
        {"task": "Process data", "mcps": []},
        {"task": "Store in DB", "mcps": ["pinecone"]}
    ]
}
```

### Ralph Loop (Inside Sandbox)
The `ralph_loop()` function in AGENT_CODE_MCP:
- Runs entirely inside E2B sandbox
- Uses stop-hook pattern (same as official ralph-wiggum plugin)
- Has access to MCP tools + local tools
- Iterates until completion promise or max iterations

### Local Tools (Sandbox)
```python
LOCAL_TOOLS = [
    "write_file",      # Write to workspace
    "read_file",       # Read from workspace
    "list_files",      # List workspace contents
    "execute_python"   # Run Python code
]
```

## MCP Servers

### Available Servers (13+)

| Server | Auth | Description |
|--------|------|-------------|
| `exa-search` | Open | Web search |
| `aws-knowledge` | Open | AWS docs |
| `tavily` | API Key | AI search |
| `stripe` | API Key | Payments |
| `github` | OAuth | Repos |
| `notion` | OAuth | Workspace |
| `linear` | OAuth | Issues |
| `pinecone` | API Key | Vector DB |
| `huggingface` | API Key | ML models |
| `firecrawl` | API Key | Web scraping |
| `sentry` | API Key | Error tracking |
| `posthog` | API Key | Analytics |
| `wandb` | API Key | ML experiments |

### Adding New MCP Servers

Edit `mcp_registry.py`:
```python
MCP_SERVERS["new-server"] = MCPServer(
    name="new-server",
    url="https://mcp.example.com/sse",
    auth_type="api_key",
    description="Description",
    categories=["category"],
    keywords=["keyword1", "keyword2"],
    auth_env_var="NEW_SERVER_API_KEY"
)
```

## Environment Variables

Required in `.env`:
- `ANTHROPIC_API_KEY` - Claude API key
- `E2B_API_KEY` - E2B sandbox API key

Optional MCP API keys (use exact names):
- `TAVILY_API_KEY`
- `GITHUB_TOKEN` or `GH_TOKEN`
- `NOTION_TOKEN`
- `LINEAR_API_KEY`
- `STRIPE_API_KEY`
- `PINECONE_API_KEY`
- `HF_TOKEN`
- `FIRECRAWL_API_KEY`
- `SENTRY_API_KEY`
- `POSTHOG_API_KEY`
- `WANDB_API`

## State Files

- **Sandbox**: `/home/user/ralph_state.json` - iteration history
- **Plugin**: `.claude-plugins/ralph-on-shelf/.ros-state.json` - loop status

## Key Dependencies

- `e2b-code-interpreter` >= 1.0.0 - Sandbox execution
- `anthropic` >= 0.40.0 - MCP connector support
- `python-dotenv` - Environment loading

Requires Python 3.11+

## Plugin Development

Commands: `.claude-plugins/ralph-on-shelf/commands/*.md`
Hooks: `.claude-plugins/ralph-on-shelf/hooks/*.py`
Agents: `.claude-plugins/ralph-on-shelf/agents/*.md`

## Roadmap

- [x] **Wiggum Planning** - Local planning with MCP assignment
- [x] **Loop Inside Sandbox** - Full stop-hook pattern in E2B
- [x] **Local Tools** - File ops, code execution
- [x] **13+ MCP Servers** - Search, databases, APIs
- [ ] **Multi-Sandbox** - Parallel execution (one per todo)
- [ ] **Wiggum Orchestrator** - Spawn multiple Ralphs
- [ ] **Progress Streaming** - Real-time output
- [ ] **Checkpoint/Resume** - Pause and continue loops

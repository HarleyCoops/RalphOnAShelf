<div align="center">

# Ralph-On-Shelf (ROS)

![Ralph On A Shelf](RalphOnAShelf.jpeg)

Autonomous AI agents running in secure E2B sandboxes with MCP tool integration.

Ralph says: "I'm helping!" He just does it from inside a sandbox.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![E2B](https://img.shields.io/badge/sandbox-E2B-orange.svg)](https://e2b.dev)
[![Claude Code](https://img.shields.io/badge/cli-Claude%20Code-purple.svg)](https://claude.ai/code)
[![MCP](https://img.shields.io/badge/tools-MCP-green.svg)](https://modelcontextprotocol.io)

</div>

---

## What is Ralph-On-Shelf?

Ralph-On-Shelf (ROS) is an autonomous agent system that combines **Wiggum planning** with **Ralph execution**:

1. **Wiggum** (local) analyzes your task, breaks it into todos, and assigns the right MCP tools
2. **Ralph** (in E2B sandbox) executes the plan autonomously with self-referential iteration

Think of it as Chief Wiggum dispatching Ralph to do the actual work - earnest, persistent, and quietly effective.

## Architecture

```
                    LOCAL                          E2B CLOUD SANDBOX
                      |                                   |
User Task -----> [Wiggum Planner] -----> [Ralph Loop] -----> Results
                      |                       |
                 Creates todos           Iterates until
                 Assigns MCPs            completion or
                 Shows plan              max iterations
                      |                       |
                      v                       v
              "Search needs exa-search"   "I'm helping!"
              "File ops need nothing"     *uses tools*
                                          *writes files*
                                          *downloads output*
```

## Key Features

### Wiggum Planning (Local)
- Analyzes task complexity and breaks into 1-5 subtasks
- Assigns only the MCP tools each subtask actually needs
- Shows you the plan before execution begins
- Adjusts iteration count based on estimated complexity

### Ralph Execution (Sandbox)
- Runs entirely inside isolated E2B cloud VM
- Self-referential loop (stop-hook pattern) - iterates until complete
- Access to 13+ MCP servers for external tools
- Local tools for file operations (write_file, read_file, execute_python)
- Ralph Wiggum quotes in terminal output

### Available MCP Servers

| Server | Type | Use Case |
|--------|------|----------|
| exa-search | open | Web search and research |
| tavily | api_key | AI-optimized search |
| aws-knowledge | open | AWS documentation |
| github | oauth | Repository management |
| notion | oauth | Workspace and docs |
| linear | oauth | Issue tracking |
| stripe | api_key | Payment processing |
| pinecone | api_key | Vector database |
| huggingface | api_key | ML models |
| firecrawl | api_key | Web scraping |
| sentry | api_key | Error tracking |
| posthog | api_key | Analytics |
| wandb | api_key | ML experiments |

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key
- E2B API key
- Optional: API keys for MCP servers you want to use

### Install

```bash
pip install -e .
```

### Configure

Create `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...

# Optional MCP API keys
TAVILY_API_KEY=tvly-...
GITHUB_TOKEN=ghp_...
STRIPE_API_KEY=sk_...
PINECONE_API_KEY=...
```

### Run Directly (Python)

```python
from main import launch_ralph

result = launch_ralph(
    prompt="Search for Python 3.13 features and create a summary file",
    max_iterations=5,
    use_wiggum=True  # Enable Wiggum planning (default)
)
```

### Use with Claude Code (Plugin)

ROS integrates with Claude Code as a native plugin:

```bash
# Start an autonomous task
/ros "Build a REST API with tests. Output COMPLETE when done." --max-iterations 10

# List available MCP servers
/ros-mcp

# Cancel a running loop
/cancel-ros
```

The `/ros` command triggers the full Wiggum + Ralph workflow inside Claude Code.

## Example Output

```
[wiggum] Analyzing task...

============================================================
  WIGGUM EXECUTION PLAN
============================================================

Analysis: Search for news and write summary to file.
Estimated iterations: 3

Todos:
  1. Search the web for latest Claude AI news
     MCPs: exa-search, tavily

  2. Analyze results and create summary
     MCPs: (no external tools)

  3. Write summary to file
     MCPs: (no external tools)

============================================================

[ralph] launching autonomous sandbox agent
[ralph] MCP servers: exa-search, tavily

============================================================
  RALPH LOOP - ITERATION 1/3
============================================================

    [Ralph] I'm learnding!

[mcp] tavily/tavily_search: {"query": "Claude AI news"...}
[mcp-result] {"results": [...]}

[tool] write_file: {"path": "summary.txt", "content": "..."}
[result] Successfully wrote 500 characters to summary.txt

COMPLETE

[ralph] Completion signal detected!
    [Ralph] I found a moon rock in my nose!

[ralph] downloading 1 file(s) to ./ralph_output
[ralph] downloaded: summary.txt
```

## How It Works

### Wiggum Planner (Local)

```python
class WiggumPlanner:
    def plan(self, prompt: str) -> dict:
        # 1. Analyze task with Claude
        # 2. Break into subtasks (todos)
        # 3. Assign MCPs to each subtask
        # 4. Return structured plan
```

The planner sees all available MCP servers and their auth status, then assigns only what's needed:

```json
{
  "todos": [
    {"task": "Search for info", "mcps": ["exa-search"]},
    {"task": "Process data", "mcps": []},
    {"task": "Store in vector DB", "mcps": ["pinecone"]}
  ]
}
```

### Ralph Loop (Sandbox)

The entire iteration loop runs inside the E2B sandbox:

```python
def ralph_loop():
    while iteration < max_iterations:
        result = run_single_iteration(...)

        if completion_promise in result:
            return "completed"  # Stop-hook exit

        # Re-feed prompt (stop-hook pattern)
        continue
```

This is the same pattern as the official `ralph-wiggum` plugin, but running inside an isolated cloud VM.

### Tool Architecture

Ralph has access to two types of tools:

1. **MCP Tools** (external) - Search, databases, APIs
   - Handled by Anthropic API's MCP connector
   - Connected via SSE/HTTP to remote servers

2. **Local Tools** (sandbox) - File operations
   - `write_file` - Create files in workspace
   - `read_file` - Read file contents
   - `list_files` - List workspace files
   - `execute_python` - Run Python code

## State Files

- **Sandbox state**: `/home/user/ralph_state.json` - iteration history
- **Plugin state**: `.claude-plugins/ralph-on-shelf/.ros-state.json` - loop status

## Project Layout

```
RalphOnAShelf/
  main.py              # Core: WiggumPlanner + RalphLoop
  mcp_registry.py      # MCP server definitions
  mcp_selector.py      # Auto-selection logic
  .env                 # API keys
  ralph_output/        # Downloaded files land here
  .claude-plugins/
    ralph-on-shelf/
      plugin.json
      commands/
        ros.md         # /ros command
        ros-mcp.md     # /ros-mcp command
        cancel-ros.md  # /cancel-ros command
      hooks/
        stop.py        # Stop hook for iteration
      agents/
        sandbox-executor.md
```

## Relationship to Official Plugins

ROS builds on the same concepts as the official [ralph-wiggum](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) plugin:

| Feature | ralph-wiggum | Ralph-On-Shelf |
|---------|--------------|----------------|
| Loop location | Local (Claude Code) | E2B Sandbox |
| Stop-hook pattern | Yes | Yes |
| MCP integration | No | Yes (13+ servers) |
| File isolation | No | Yes (sandbox) |
| Wiggum planning | No | Yes |

ROS is designed for tasks that need:
- Isolated execution environment
- External tool access (search, APIs)
- File operations without local system access

## Roadmap

- [x] Wiggum planning with MCP assignment
- [x] Full loop inside sandbox (stop-hook pattern)
- [x] Local tools (file ops, code execution)
- [ ] Multi-sandbox parallel execution (one per todo)
- [ ] Wiggum orchestrator spawning multiple Ralphs
- [ ] Progress streaming
- [ ] Checkpoint/resume
- [ ] Cost tracking

## License

MIT License. See LICENSE for details.

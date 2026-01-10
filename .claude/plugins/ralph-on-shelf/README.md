# Ralph-On-Shelf Plugin

Autonomous AI agents running in E2B cloud sandboxes with self-referential iteration loops.

## Overview

Ralph-On-Shelf (ROS) enables Claude to launch autonomous agent loops that run inside isolated E2B cloud sandboxes. The agent works on your task iteratively until completion, with full access to Python, bash, and file operations in a safe environment.

**Key Features:**
- **Autonomous Execution** - Agent runs independently until task completion
- **E2B Sandboxes** - Isolated Linux VMs for safe code execution
- **Self-Referential Loop** - Continues working across iterations until done
- **Configurable Limits** - Set max iterations and completion signals

## Installation

### Prerequisites

1. **E2B API Key** - Get one at [e2b.dev](https://e2b.dev)
2. **Anthropic API Key** - For Claude Agent SDK

Add to your `.env` file:
```bash
E2B_API_KEY=your_e2b_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### Install Plugin

**Option 1: From GitHub Marketplace**
```bash
/plugin marketplace add HarleyCoops/RalphOnAShelf
/plugin install ralph-on-shelf@ralph-tools
```

**Option 2: Local Development**
```bash
claude --plugin-dir ./.claude-plugins/ralph-on-shelf
```

## Commands

### `/ros <prompt> [options]`

Start an autonomous Ralph loop.

**Arguments:**
- `prompt` (required) - The task for the agent to work on
- `--max-iterations N` - Maximum iterations before stopping (default: 10)
- `--completion-promise TEXT` - Text that signals completion (default: "COMPLETE")

**Examples:**
```bash
# Simple task
/ros "Create a Python script that calculates prime numbers"

# Complex task with higher iteration limit
/ros "Build a REST API with tests. Output COMPLETE when done." --max-iterations 20

# Custom completion signal
/ros "Analyze this dataset and generate a report" --completion-promise "ANALYSIS DONE"
```

### `/cancel-ros`

Cancel an active ROS loop and clean up the sandbox.

```bash
/cancel-ros
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. /ros "task"                                                 │
│     │                                                           │
│     ▼                                                           │
│  2. Create E2B Sandbox (isolated Linux VM)                      │
│     │                                                           │
│     ▼                                                           │
│  3. Claude Agent SDK runs inside sandbox                        │
│     │                                                           │
│     ▼                                                           │
│  4. Agent works on task (code, files, bash)                     │
│     │                                                           │
│     ▼                                                           │
│  5. Check for completion signal                                 │
│     │                                                           │
│     ├──→ Found "COMPLETE" → Done, cleanup sandbox               │
│     │                                                           │
│     └──→ Not found → Increment iteration, re-run from step 4    │
│                                                                 │
│  6. Max iterations reached → Stop, cleanup sandbox              │
└─────────────────────────────────────────────────────────────────┘
```

## Components

| Component | File | Purpose |
|-----------|------|---------|
| `/ros` command | `commands/ros.md` | Start autonomous loop |
| `/cancel-ros` command | `commands/cancel-ros.md` | Cancel active loop |
| Sandbox executor agent | `agents/sandbox-executor.md` | Execute code in E2B |
| Stop hook | `hooks/stop.md` | Re-feed prompt on iteration |

## State Management

ROS tracks loop state in `.ros-state.json`:

```json
{
  "active": true,
  "prompt": "Your task...",
  "max_iterations": 10,
  "completion_promise": "COMPLETE",
  "current_iteration": 3,
  "sandbox_id": "abc123",
  "status": "running"
}
```

## Agent Capabilities

Inside the E2B sandbox, the agent can:

- **Execute Python code** - Full Python 3.11+ environment
- **Run bash commands** - Git, curl, system tools
- **Read/write files** - Persistent within the sandbox session
- **Install packages** - Via pip
- **Access the network** - HTTP requests, API calls

## Requirements

- Python 3.11+
- `e2b-code-interpreter` >= 1.0.0
- `claude-agent-sdk`
- `python-dotenv`

## Roadmap

- [ ] **Ralph Orchestrator** - Launch multiple sandboxes in parallel
- [ ] **Sandbox templates** - Pre-configured environments (Node, Rust, etc.)
- [ ] **Progress streaming** - Real-time output from sandbox
- [ ] **Checkpoint/resume** - Save state across sessions

## License

MIT

<div align="center">

# Ralph-On-Shelf (ROS)

![Ralph On A Shelf](RalphOnAShelf.jpeg)

Autonomous AI agents running in secure E2B sandboxes.

Ralph says: "I'm helping." He just does it from inside a sandbox.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![E2B](https://img.shields.io/badge/sandbox-E2B-orange.svg)](https://e2b.dev)
[![Claude Code](https://img.shields.io/badge/cli-Claude%20Code-purple.svg)](https://claude.ai/code)

</div>

---

## What is Ralph-On-Shelf?

Ralph-On-Shelf (ROS) is a self-referential agent loop that runs Claude Agent SDK inside
an E2B sandbox. It keeps iterating until a completion promise is found, while preserving
files and context inside the sandbox.

If Ralph Wiggum had a dev environment, this is it: earnest, persistent, and quietly
effective.

## Wiggum in a sandbox (implementation)

There are two layers to the loop: a host controller and a sandboxed agent.

Host controller (outside the sandbox):
- `main.py` creates an E2B sandbox and installs `claude-agent-sdk` and `nest_asyncio`.
- It formats the per-iteration prompt and injects `AGENT_CODE` into the sandbox.
- After each run, it checks for the completion promise and decides to continue.

Sandboxed agent (inside the sandbox):
- `AGENT_CODE` runs Claude Agent SDK with the current prompt and iteration info.
- It reads `/home/user/ralph_state.json` to pull in the last few results.
- It writes updated history back to `/home/user/ralph_state.json` so the next
  iteration can reference it.

Claude Code plugin loop (optional):
- `/ros` writes `.claude-plugins/ralph-on-shelf/.ros-state.json` and starts the sandbox.
- `hooks/stop.py` intercepts exit, increments the iteration, and re-feeds the prompt
  until complete.

This is the Wiggum pattern in practice: a self-referential loop that keeps showing up,
re-reads its own homework, and tries again until the task is done.

## Quick start

### Prerequisites

- Python 3.11+
- Anthropic API key
- E2B API key

### Install

```bash
pip install -e .
```

For dev tools:

```bash
pip install -e ".[dev]"
```

### Configure

Create `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...
```

### Run locally

```bash
python main.py
```

### Use with Claude Code (plugin)

```bash
/ros "Build a REST API with tests. Output COMPLETE when done." --max-iterations 20
/cancel-ros
```

## Completion signals

ROS stops when the completion promise appears in the output (default: `COMPLETE`) or
when max iterations are reached. Use explicit completion criteria in your prompts.

Example:

```bash
/ros "Generate primes up to 1000 and save to primes.txt. Output COMPLETE when done."
```

## State files

- Local runner: `/home/user/ralph_state.json` inside the sandbox keeps the last few
  iteration outputs.
- Claude Code plugin: `.claude-plugins/ralph-on-shelf/.ros-state.json` tracks iteration
  count, sandbox id, and status.

## Project layout

```
RalphOnAShelf/
  main.py
  README.md
  pyproject.toml
  requirements.txt
  .env
  .claude-plugins/
    ralph-on-shelf/
      plugin.json
      README.md
      commands/
        ros.md
        cancel-ros.md
      hooks/
        stop.py
        stop.md
      agents/
        sandbox-executor.md
```

## Testing and linting

```bash
pytest
ruff check .
ruff format .
mypy src
```

## Roadmap

- Ralph Orchestrator: multi-sandbox parallel execution
- Sandbox templates
- Progress streaming
- Checkpoint/resume
- Cost tracking

## License

MIT License. See LICENSE for details.

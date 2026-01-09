# Ralph-On-Shelf (ROS)

A self-referential autonomous agent loop running in E2B sandboxes.

## Overview

Ralph-On-Shelf combines:
- **E2B Sandboxes** - Isolated cloud VMs for safe code execution
- **Ralph Loop Pattern** - Self-referential feedback loop for autonomous iteration

Named after Ralph Wiggum, but now he's on a shelf watching your code run safely in the cloud.

## Commands

### `/ros <prompt> [--max-iterations N] [--completion-promise TEXT]`

Start an autonomous loop.

```bash
/ros "Build a REST API with tests. Output COMPLETE when done." --max-iterations 20
```

**Options:**
- `--max-iterations` - Safety limit (default: 10)
- `--completion-promise` - Completion signal text (default: "COMPLETE")

### `/cancel-ros`

Cancel an active loop and clean up the sandbox.

## How It Works

1. `/ros` creates a state file and spins up an E2B sandbox
2. Claude works on the task, executing code in the sandbox
3. When Claude tries to exit, the Stop hook intercepts
4. If not complete, the hook re-feeds the prompt for another iteration
5. Loop continues until completion promise is found or max iterations reached
6. Sandbox is cleaned up on completion/cancellation

## State File

Located at `.ros-state.json`:

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

## Requirements

- E2B API key in `.env` as `E2B_API_KEY`
- Python 3.11+
- e2b-code-interpreter package

## TODO

- [ ] Ralph Orchestrator - launch multiple sandboxes in parallel
- [ ] Sandbox templates - pre-configured environments
- [ ] Progress streaming - real-time output from sandbox
- [ ] Checkpoint/resume - save state across sessions

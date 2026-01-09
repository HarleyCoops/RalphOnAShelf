---
name: ros
description: Start a Ralph-On-Shelf autonomous loop in an E2B sandbox
arguments:
  - name: prompt
    description: The task prompt for the agent to work on
    required: true
  - name: max-iterations
    description: Maximum number of iterations before stopping (default 10)
    required: false
  - name: completion-promise
    description: Text that signals successful completion
    required: false
---

# Ralph-On-Shelf (ROS) - Autonomous E2B Agent Loop

You are starting a **Ralph-On-Shelf** autonomous loop. This creates a self-referential feedback loop where you work on a task inside an E2B sandbox, iterating until completion.

## Setup Instructions

1. **Create the ROS state file** at `${CLAUDE_PLUGIN_ROOT}/.ros-state.json`:

```json
{
  "active": true,
  "prompt": "{{prompt}}",
  "max_iterations": {{max-iterations | default: 10}},
  "completion_promise": "{{completion-promise | default: "COMPLETE"}}",
  "current_iteration": 0,
  "sandbox_id": null,
  "started_at": "<current ISO timestamp>",
  "status": "running"
}
```

2. **Spin up an E2B sandbox** using the project's E2B integration:
   - Use the `execute_python` tool via MCP or direct E2B API
   - Store the sandbox_id in the state file

3. **Begin working on the task** inside the sandbox:
   - Read the prompt: `{{prompt}}`
   - Execute code in the E2B sandbox to accomplish the task
   - Track progress in files within the sandbox

## Iteration Rules

- Each iteration, increment `current_iteration` in the state file
- Check if `current_iteration >= max_iterations` - if so, stop and report
- Check if your output contains the completion promise `{{completion-promise | default: "COMPLETE"}}` - if so, mark complete
- Otherwise, the Stop hook will re-feed this prompt for the next iteration

## Your Task

**Prompt:** {{prompt}}

**Max Iterations:** {{max-iterations | default: 10}}
**Completion Signal:** Output `{{completion-promise | default: "COMPLETE"}}` when done

## Working Guidelines

1. **Use the E2B sandbox** for all code execution - it's isolated and safe
2. **Persist state in files** - write progress to files so you can read them in next iteration
3. **Be incremental** - each iteration should make measurable progress
4. **Signal completion** - output the completion promise when the task is done
5. **Document blockers** - if stuck, document what's blocking in a file

## Begin

Start working on the task now. Create the state file first, then begin executing in the sandbox.

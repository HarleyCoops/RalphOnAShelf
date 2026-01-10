---
name: ros-stop-hook
event: Stop
description: Intercepts session stop to continue Ralph-On-Shelf loop
---

# Ralph-On-Shelf Stop Hook

This hook intercepts when Claude tries to stop/exit and continues the autonomous loop if ROS is active.

## Check ROS State

1. Read the state file at `${CLAUDE_PLUGIN_ROOT}/.ros-state.json`
2. If the file doesn't exist or `active` is false, allow normal exit
3. If active, check the conditions below

## Continuation Logic

When ROS is active, check these conditions:

### Stop Conditions (allow exit)
- `current_iteration >= max_iterations` - max iterations reached
- `status` is "completed" - completion promise was found
- `status` is "cancelled" - user cancelled via /cancel-ros

If any stop condition is met:
- Set `active: false` in state file
- Report final status to user
- Allow normal exit

### Continue Conditions (block exit and re-feed)
If none of the stop conditions are met:

1. **Increment iteration counter** in state file
2. **Block the exit** by outputting a continuation message
3. **Re-feed the original prompt** to continue the loop

## Re-feed Message Template

When continuing the loop, output:

```
---
ROS ITERATION {{current_iteration + 1}} / {{max_iterations}}
---

Continuing Ralph-On-Shelf loop...

Original task: {{prompt}}

Instructions:
- Review any files you created in previous iterations
- Continue working toward the completion criteria
- Output "{{completion_promise}}" when the task is complete
- You have {{max_iterations - current_iteration}} iterations remaining

Resume working on the task now.
```

## Implementation

Read the state file and make decisions:

```python
import json
from pathlib import Path

state_path = Path("${CLAUDE_PLUGIN_ROOT}/.ros-state.json")

if state_path.exists():
    state = json.loads(state_path.read_text())

    if state.get("active"):
        current = state.get("current_iteration", 0)
        max_iter = state.get("max_iterations", 10)

        if current >= max_iter or state.get("status") in ["completed", "cancelled"]:
            # Allow exit
            state["active"] = False
            state_path.write_text(json.dumps(state, indent=2))
        else:
            # Continue loop - increment and re-feed
            state["current_iteration"] = current + 1
            state_path.write_text(json.dumps(state, indent=2))
            # Output continuation message (hook should block exit)
```

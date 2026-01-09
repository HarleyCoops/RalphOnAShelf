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
    description: Text that signals successful completion (default COMPLETE)
    required: false
---

# Ralph-On-Shelf (ROS)

Launch an autonomous Claude Agent SDK loop inside an E2B cloud sandbox.

## Execute

Run the following Python code to start the Ralph loop:

```bash
cd {{cwd}} && python -c "
from main import launch_ralph

result = launch_ralph(
    prompt='''{{prompt}}''',
    max_iterations={{max-iterations | default: 10}},
    completion_promise='{{completion-promise | default: COMPLETE}}',
    timeout=600
)

print(f'[ralph] final status: {result[\"status\"]}')
print(f'[ralph] total iterations: {result[\"iterations\"]}/{result[\"max_iterations\"]}')
"
```

The agent will run autonomously in the E2B sandbox until:
- The completion promise appears in the output
- Max iterations is reached

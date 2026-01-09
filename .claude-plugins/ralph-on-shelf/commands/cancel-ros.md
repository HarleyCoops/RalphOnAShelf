---
name: cancel-ros
description: Cancel an active Ralph-On-Shelf loop
---

# Cancel Ralph-On-Shelf

This command cancels any active ROS loop.

## Instructions

1. **Read the state file** at `${CLAUDE_PLUGIN_ROOT}/.ros-state.json`

2. **If no active loop**, report:
   ```
   No active Ralph-On-Shelf loop to cancel.
   ```

3. **If active loop exists**, update the state:
   ```json
   {
     "active": false,
     "status": "cancelled",
     "cancelled_at": "<current ISO timestamp>",
     "final_iteration": <current_iteration>
   }
   ```

4. **Kill the E2B sandbox** if one is running:
   - Read the `sandbox_id` from state
   - Call sandbox.kill() to clean up

5. **Report cancellation**:
   ```
   Ralph-On-Shelf loop cancelled.
   - Completed iterations: {{final_iteration}}
   - Original prompt: {{prompt}}
   - Sandbox cleaned up: {{sandbox_id}}
   ```

## Execute

Cancel the ROS loop now by updating the state file and cleaning up resources.

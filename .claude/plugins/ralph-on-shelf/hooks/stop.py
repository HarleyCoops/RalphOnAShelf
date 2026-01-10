#!/usr/bin/env python3
"""
Ralph-On-Shelf Stop Hook

Intercepts session stop to continue the autonomous loop if ROS is active.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# State file location - relative to plugin root
PLUGIN_ROOT = Path(__file__).parent.parent
STATE_FILE = PLUGIN_ROOT / ".ros-state.json"


def load_state() -> dict | None:
    """Load ROS state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return None
    return None


def save_state(state: dict) -> None:
    """Save ROS state to file."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    state = load_state()

    # No state or not active - allow normal exit
    if not state or not state.get("active"):
        sys.exit(0)

    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 10)
    status = state.get("status", "running")
    prompt = state.get("prompt", "")
    completion_promise = state.get("completion_promise", "COMPLETE")

    # Check stop conditions
    if current_iteration >= max_iterations:
        state["active"] = False
        state["status"] = "max_iterations_reached"
        state["ended_at"] = datetime.now().isoformat()
        save_state(state)
        print(f"\n[ROS] Max iterations ({max_iterations}) reached. Loop ended.")
        sys.exit(0)

    if status in ["completed", "cancelled"]:
        state["active"] = False
        state["ended_at"] = datetime.now().isoformat()
        save_state(state)
        print(f"\n[ROS] Loop {status}.")
        sys.exit(0)

    # Continue the loop - increment and re-feed
    state["current_iteration"] = current_iteration + 1
    save_state(state)

    # Output continuation message - this blocks exit and re-feeds
    remaining = max_iterations - current_iteration - 1
    print(f"""
================================================================================
ROS ITERATION {current_iteration + 1} / {max_iterations}
================================================================================

Continuing Ralph-On-Shelf loop...

**Original task:** {prompt}

**Instructions:**
- Review any files you created in previous iterations
- Check the E2B sandbox for your work so far
- Continue working toward the completion criteria
- Output "{completion_promise}" when the task is complete
- You have {remaining} iterations remaining

Resume working on the task now.
""")

    # Exit with non-zero to block the stop (hook behavior)
    sys.exit(1)


if __name__ == "__main__":
    main()

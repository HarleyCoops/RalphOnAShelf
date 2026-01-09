# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ralph-On-Shelf (ROS)** - Autonomous AI agents running in secure E2B cloud sandboxes with self-referential iteration loops.

Key components:
- **E2B Sandboxes** - Isolated cloud VMs for safe code execution
- **Ralph Loop** - Self-referential feedback loop that re-feeds prompts until completion
- **Claude Code Plugin** - `/ros` and `/cancel-ros` commands

## Commands

### Development
```bash
pip install -e .              # Install project
pip install -e ".[dev]"       # Install with dev dependencies
```

### ROS Commands (in Claude Code)
```bash
/ros "<prompt>" --max-iterations N --completion-promise "TEXT"   # Start loop
/cancel-ros                                                       # Cancel loop
```

### Testing & Linting
```bash
pytest                        # Run all tests
ruff check .                  # Lint
ruff format .                 # Format (line-length: 100)
mypy src                      # Type check (strict mode)
```

## Architecture

### ROS Loop Flow
```
/ros "task" → Create Sandbox → Work on Task → Stop Hook → Re-feed Prompt → Repeat
                    ↓                              ↓
              E2B Cloud VM                  Until COMPLETE or max iterations
```

### Key Files
| File | Purpose |
|------|---------|
| `main.py` | Direct E2B sandbox execution |
| `.claude-plugins/ralph-on-shelf/commands/ros.md` | /ros command definition |
| `.claude-plugins/ralph-on-shelf/hooks/stop.py` | Stop hook - re-feeds prompt |
| `.claude-plugins/ralph-on-shelf/lib/sandbox_manager.py` | E2B sandbox utilities |

### State File
ROS tracks loop state in `.claude-plugins/ralph-on-shelf/.ros-state.json`:
```json
{
  "active": true,
  "prompt": "...",
  "max_iterations": 10,
  "current_iteration": 3,
  "sandbox_id": "...",
  "completion_promise": "COMPLETE"
}
```

## E2B Sandbox Usage

```python
from e2b_code_interpreter import Sandbox

# Create and use sandbox
with Sandbox() as sbx:
    result = sbx.run_code('print("Hello")')
    stdout = "".join(result.logs.stdout)

    # File operations
    sbx.files.write("/path/file.txt", content)
    content = sbx.files.read("/path/file.txt")
```

### Sandbox Manager (Plugin)
```python
from lib.sandbox_manager import execute_python, manager

result = execute_python('print("test")')
# Returns: {"success": True, "output": "...", "results": [...]}

manager.write_file("/path", content)
manager.read_file("/path")
manager.kill()  # Cleanup
```

## Environment Variables

Required in `.env`:
- `ANTHROPIC_API_KEY` - Claude API key
- `E2B_API_KEY` - E2B sandbox API key

## Key Dependencies

- `e2b-code-interpreter` >= 1.0.0 - Sandbox execution
- `python-dotenv` - Environment loading

Requires Python 3.11+

## Plugin Development

Commands go in `.claude-plugins/ralph-on-shelf/commands/*.md`
Hooks go in `.claude-plugins/ralph-on-shelf/hooks/*.py`
Shared code in `.claude-plugins/ralph-on-shelf/lib/`

## Roadmap

- [ ] Ralph Orchestrator - multi-sandbox parallel execution
- [ ] Sandbox templates
- [ ] Progress streaming
- [ ] Checkpoint/resume

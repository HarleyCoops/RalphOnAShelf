---
name: ros
description: Start a Ralph-On-Shelf autonomous loop in an E2B sandbox with MCP tools
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
  - name: output-dir
    description: Local directory to save workspace files (default ./ralph_output)
    required: false
  - name: mcp
    description: MCP mode - "auto" (select based on prompt), "none", or comma-separated server names like "exa-search,aws-knowledge"
    required: false
---

# Ralph-On-Shelf (ROS)

Launch an autonomous Claude agent inside an E2B cloud sandbox with MCP connector support.

## MCP Servers

When `mcp=auto` (default), Ralph analyzes your prompt and automatically connects to relevant MCP servers:
- **exa-search**: Web search and research (keywords: search, find, research, web)
- **aws-knowledge**: AWS documentation and cloud knowledge (keywords: aws, cloud, lambda, s3)

Use `mcp=none` to disable MCP and use the classic SDK mode.
Use `mcp=exa-search,aws-knowledge` to explicitly specify servers.

## Execute

Run the following Python code to start the Ralph loop:

```bash
cd {{cwd}} && python -c "
from main import launch_ralph

result = launch_ralph(
    prompt='''{{prompt}}''',
    max_iterations={{max-iterations | default: 10}},
    completion_promise='{{completion-promise | default: COMPLETE}}',
    output_dir='{{output-dir | default: ralph_output}}',
    mcp='{{mcp | default: auto}}',
    timeout=600
)

print(f'[ralph] final status: {result[\"status\"]}')
print(f'[ralph] total iterations: {result[\"iterations\"]}/{result[\"max_iterations\"]}')
print(f'[ralph] MCP servers: {result.get(\"mcp_servers\", [])}')
if result.get('downloaded_files'):
    print(f'[ralph] files saved to: {result[\"output_dir\"]}')
    for f in result['downloaded_files']:
        print(f'  - {f}')
"
```

The agent will run autonomously in the E2B sandbox until:
- The completion promise appears in the output
- Max iterations is reached
